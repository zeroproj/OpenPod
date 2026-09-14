# OpenPod — UPDATE_TRIGGER

Como colocar o GN-438 em modo de atualização. Resultado de uma
investigação que corrigiu duas conclusões erradas anteriores.

| | |
|---|---|
| **Data** | 2026-09-12 |
| **Método** | disassembly + menu real relatado pelo mantenedor |
| **Hardware** | nenhuma operação |

---

## 1. Resultado — os dois flags não são equivalentes

Existem **dois** flags de atualização no PMU (registrador `0x23`). Eles
têm caminhos de acionamento **completamente diferentes**:

| Flag | Caminho na interface | Classe |
|---|---|---|
| **SD** (`bits[2:0] == 6`) | **NENHUM** — só pelo console de depuração | **CONFIRMADO** |
| **PC** | **gatilho escondido na tela de versão** — §3 | **CONFIRMADO** |

> **Não existe caminho pela interface para o update por cartão SD neste
> firmware.** É isso que explica por que o item de menu nunca foi
> encontrado: ele não existe nesta build.

---

## 2. A busca que resolveu

Varredura por **padrão de bits** das instruções `BL` (não por disassembly
linear, que dá falso negativo em pools literais), procurando todos os
chamadores dos gravadores de flag:

| Função | Chamadores encontrados |
|---|---|
| `set_flag_SD` (`0x00D78252`) | **1** — `0x00CF9D68`, dentro do comando de console |
| `set_flag_PC` (`0x00D7824C`) | **2** — `0x00CF9D4A` (console) e **`0x00D0A62E`** |

O segundo chamador do flag de PC é o achado.

> **Nota de método:** a varredura por disassembly linear reportou
> **0 chamadas** para ambos. A varredura por padrão de bits achou as três.
> Conclusões de ausência exigem o método certo — foi o terceiro falso
> negativo do mesmo tipo neste projeto.

---

## 3. O gatilho escondido — CONFIRMADO

Em `pstr_page51_process`:

```asm
00D0A614  ldrh r2, [r3, #0xc]      ; ctrl_id
00D0A616  cmp  r2, #2              ; exige ctrl_id == 2
00D0A618  bne  #0xd0a658
00D0A61A  ldr  r2, = 0x008238F0    ; contador em RAM (1 byte)
00D0A61C  ldrb r3, [r2]
00D0A61E  adds r3, #1              ; incrementa
00D0A622  cmp  r3, #0xe            ; 14
00D0A624  bhi  #0xd0a62a           ; passou de 14 -> dispara
00D0A626  strb r3, [r2]            ; senao, so guarda
00D0A628  pop  {r3, pc}

00D0A62A  movs r3, #0
00D0A62C  strb r3, [r2]            ; zera o contador
00D0A62E  bl   #0xd7824c           ; GRAVA O FLAG DE UPDATE POR PC
00D0A636  b.w  #0x80cf9e           ; REINICIA
```

E o ramo que **limpa** o contador (`sta == 8`, `ctrl_id == 2`):

```asm
00D0A640  ldr  r3, = 0x008238F0
00D0A644  strb r2, [r3]            ; contador = 0
00D0A64E  ldr  r0, = "-repeat_cnt clean"
```

### Em português — **é SEGURAR, não tocar**

Os valores de `sta` correspondem ao enum `lv_event_code_t` do LVGL v8:

| Valor | Evento LVGL | Papel no gatilho |
|---|---|---|
| `6` | `LV_EVENT_LONG_PRESSED_REPEAT` | **incrementa** o contador |
| `8` | `LV_EVENT_RELEASED` | **zera** o contador |

> Na tela `page51`, **manter pressionado** o controle de `ctrl_id = 2`.
> A repetição automática dispara o evento `6` seguidamente; ao chegar na
> **15ª repetição**, o firmware grava o flag de atualização por PC e
> reinicia o aparelho.
>
> **Soltar o botão zera o contador** (`repeat_cnt clean`) e recomeça do
> zero. Não adianta tocar 15 vezes — tem de ser **um toque longo, sem
> soltar**.

A repetição automática do firmware já foi documentada em
`INPUT_MAP_COMPLETE.md` §3 (evento `0x60`, *long press* sustentado).
O intervalo entre repetições **não foi medido** — na prática, espere
alguns segundos segurando.

| Afirmação | Classe |
|---|---|
| `sta` é `lv_event_code_t` do LVGL v8 | **PROVÁVEL** (valores batem exatamente) |
| `6` = repetição de toque longo, `8` = soltar | **PROVÁVEL** |
| O gatilho exige manter pressionado | **PROVÁVEL** — decorre do acima |

### Que tela é `page51`

O ponteiro para a string `yp3_2.0.43` (a versão do firmware) está em
`0x10A59C` — **no mesmo pool literal** de `pstr_page51_process`
(`0x10A5B4`). São adjacentes.

| Afirmação | Classe |
|---|---|
| O gatilho existe, com esta lógica exata | **CONFIRMADO** |
| Está em `page51` | **CONFIRMADO** |
| `page51` é a tela que exibe `yp3_2.0.43` | **CONFIRMADO** (mesmo pool) |
| `page51` é o item **"Número da versão"** do menu | **PROVÁVEL** |
| Qual botão físico corresponde a `ctrl_id = 2` | **NÃO DETERMINADO** |

---

## 4. O menu real deste aparelho

Relatado pelo mantenedor, em Configurações:

```text
Despertador · Língua · Hora e data · Brilho · Configuração do Ecrã ·
Desligamento sem carga · Informações · Estado de Armazenamento ·
Configuração de fábrica · Atualização da Lista de Reprodução
```

**Não há "Opções de actualização".** As strings existem no firmware, mas
a tela não está exposta nesta build.

> Isto também explica a confusão anterior: a mensagem *"Não foram
> detectados dispositivos de armazenamento"* vem de **Estado de
> Armazenamento** (`page_storage_info_create`), não de uma tela de
> atualização.

---

## 5. O que fazer com isso

### Caminho A — gatilho escondido → modo PC → gravação por USB

```text
Informações → Número da versão
   └─ acionar 15x seguidas
        └─ o aparelho reinicia em modo de atualização por PC
             └─ gravar com smtlink_dump pelo Ubuntu
```

**Vantagens:** disponível agora, sem abrir o aparelho, sem UART. E dá um
jeito confiável de entrar em modo bootloader sem caçar a tecla de boot.

**Cuidado:** este caminho usa `write_flash`, que aceita qualquer endereço
— inclusive o do bootloader. A proteção estrutural do `sdupdate`
(`FLASH_POLICY.md` §2) **não se aplica aqui**.

> **Mitigação:** gravar **a partir de `0x00D000`**, nunca de `0`. Isso
> reproduz exatamente o que o `sdupdate` faria, preservando o bootloader:
>
> ```text
> write_flash 0xD000 0xD000 <tamanho> GN438_openpod_v001.bin
> ```
>
> Assim mantemos a propriedade de segurança por **escolha explícita**, em
> vez de por construção.

### Caminho B — console UART → `update sd`

Usa o mecanismo do cartão, com a proteção estrutural intacta. Exige
localizar os pinos de UART e um adaptador 3,3 V.

**PROVÁVEL** que funcione; não exercitado.

---

## 6. Recomendação

**Caminho A, com gravação a partir de `0x00D000`.**

Motivos: está disponível agora; a escrita por USB **já foi validada**
(`WRITE_TEST_RESULT.md`); e a propriedade de segurança que importa — não
tocar o bootloader — é mantida por escolha de endereço.

O Caminho B continua preferível a longo prazo, e vale buscar a UART de
qualquer forma: ela também resolve o mapeamento de botões
(`INPUT_MAP_COMPLETE.md` §9).

---

## 7. Antes de usar o gatilho

| # | Passo | Por quê |
|---|---|---|
| 1 | Confirmar que `page51` é mesmo "Número da versão" | é PROVÁVEL, não confirmado |
| 2 | Descobrir qual botão é `ctrl_id = 2` | por tentativa, na tela |
| 3 | Confirmar que o aparelho reinicia e enumera como `301a:2800` | prova que o modo entrou |
| 4 | **Só então** gravar | |

Os passos 1–3 **não escrevem nada**. Se o aparelho entrar em modo PC e
você não gravar, basta desligar e ligar: o flag é limpo pelo bootloader
antes de agir (`UPDATE_MECHANISM.md` §1).
