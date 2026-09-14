# OpenPod — INPUT_MAP_COMPLETE

Mapeamento do sistema de entrada do GN-438.

| | |
|---|---|
| **Data** | 2026-09-12 |
| **Alvo** | partição FIRM, `firmware/WORKING/GN438_analysis.bin` |
| **Método** | disassembly ARM Thumb-2 (capstone), `tools/disasm.py` |
| **Hardware** | **nenhuma operação** — análise estática |
| **Firmware** | **não alterado** |

### Convenção de confiança

- **CONFIRMADO** — lido no disassembly, instrução por instrução.
- **PROVÁVEL** — inferido de assinatura de chamada ou de literal.
- **HIPÓTESE** — plausível, não comprovado.
- **NÃO RESOLVIDO** — investigado e não determinado.

### Mapeamento de endereços

```text
FIRM (XIP):  addr = offset_no_arquivo + 0x00C00000
```

Validado: 7 de 7 strings de entrada testadas têm xrefs em pool literal
exatamente nesse endereço.

---

## 1. Resposta direta: os botões físicos

> **Leia esta seção inteira antes de usar a tabela.**

O firmware **não nomeia** os botões como `M`, `◀◀`, `▶▶`, `▶Ⅱ`. Ele
trabalha com um espaço de `key_id` numéricos e nomes **funcionais**
(`enter`, `left`, `right`, `back`, `record`, `onoff`, `power`,
`volume_up`, `volume_down`).

A tradução entre a **serigrafia do aparelho** e o `key_id` depende da
tabela de descritores do driver, que é montada em **RAM** (`0x00819BCC`)
e **não existe na flash de forma estática**. Procurei por ela: varri toda
a FIRM por janelas contendo 6+ dos `key_id` conhecidos e as 1682
ocorrências candidatas eram todas instruções VFP ou código comum —
**nenhuma tabela de descritores**.

| Botão físico | key_id provável | Nome no firmware | Confiança | Base |
|---|---|---|---|---|
| **▶Ⅱ** | `0x21` | `enter` | **HIPÓTESE** | `enter` é a tecla de confirmação; nesta classe de player o play/pause acumula a função de selecionar |
| **◀◀** | `0x42` | `left` | **HIPÓTESE** | correspondência direcional |
| **▶▶** | `0x43` | `right` | **HIPÓTESE** | correspondência direcional |
| **M** | `0x45` | `back` | **HIPÓTESE** | `M` costuma ser menu/voltar; `back` é o único candidato de navegação restante |
| **VOL +** | `0x24` | `volume_up` | **PROVÁVEL** | nome funcional inequívoco |
| **VOL −** | `0x23` | `volume_down` | **PROVÁVEL** | nome funcional inequívoco |
| chave liga/desliga | `0x37` / `0x47` | `onoff` / `power` | **CONFIRMADO** | `/dev/key_onoff` é aberto com exatamente esses dois ids (§4) |

> **Não trate as linhas marcadas HIPÓTESE como mapeamento.** Elas são a
> correspondência mais razoável entre nomes funcionais e serigrafia, não
> uma leitura do binário. O §9 descreve o teste de 10 minutos que
> converte todas elas em CONFIRMADO sem risco nenhum para o aparelho.

Além disso, existem **quatro `key_id` sem nome** (`0x20`, `0x22`, `0x25`,
`0x38`) que são tratados pelo firmware mas nunca impressos com rótulo.
Se o aparelho tiver ↑/↓ separados de ◀◀/▶▶, eles provavelmente estão aí.

---

## 2. Tabela de `key_id` — CONFIRMADO

Extraída da cadeia de comparações em `0x00CFC862`–`0x00CFC8F2`.

| `key_id` | Nome | String de depuração | Endereço do `ldr` |
|---|---|---|---|
| `0x20` | **sem nome** | — | tratado em `0x00CFC91A` |
| `0x21` | `enter` | `"- enter key "` | `0x00CFC8E8` |
| `0x22` | **sem nome** | — | tratado em `0x00CFC91E` |
| `0x23` | `volume_down` | `"- volume_down key "` | `0x00CFC8D8` |
| `0x24` | `volume_up` | `"- volume_up key "` | `0x00CFC8D0` |
| `0x25` | **sem nome** | — | tratado em `0x00CFC974` |
| `0x34` | `record` | `"- record key "` | `0x00CFC88E` |
| `0x37` | `onoff` | `"- onoff key "` | `0x00CFC8B8` |
| `0x38` | **sem nome** | — | tratado em `0x00CFC97E` |
| `0x42` | `left` | `"- left key "` | `0x00CFC8A0` |
| `0x43` | `right` | `"- right key "` | `0x00CFC8E0` |
| `0x45` | `back` | `"- back key "` | `0x00CFC8F0` |
| `0x47` | `power` | `"- power key "` | `0x00CFC8B0` |
| qualquer outro | — | `"- default key %x "` | `0x00CFC87A` |

### Estrutura do switch (CONFIRMADO)

```asm
00CFC862  cmp  r6, #0x37
00CFC866  beq  #0xcfc8b4        ; onoff
00CFC868  bhi  #0xcfc892        ; ramo 0x42/0x43/0x45/0x47
00CFC86A  cmp  r6, #0x23
00CFC86C  beq  #0xcfc8d4        ; volume_down
00CFC86E  bhi  #0xcfc882        ; ramo 0x24/0x34
00CFC870  cmp  r6, #0x21
00CFC872  beq  #0xcfc8e4        ; enter
00CFC874  ...                   ; default
```

> Os `key_id` se agrupam por faixa: `0x2x` (6 ids), `0x3x` (3 ids),
> `0x4x` (4 ids). **HIPÓTESE:** o nibble alto identifica a origem
> (controlador/porta) e o baixo, o índice da tecla. Coerente com haver
> três dispositivos de entrada (§4), mas não comprovado.

---

## 3. Códigos de evento — CONFIRMADO

Derivados da cadeia de despacho da tecla `onoff` (`0x37`), a única cujos
cinco eventos têm string própria.

| Código | Evento | String | Endereço |
|---|---|---|---|
| `0x10` | **press** — pressionar | `"-onoff key press ! "` | `0x00CFC9D2` |
| `0x30` | **short release** — toque curto | `"-onoff key short release status to backlight "` | `0x00CFCA42` |
| `0x40` | **long start** — início do longo | `"-onoff key long start  "` | `0x00CFCA52` |
| `0x50` | **long release** — soltar após longo | `"-onoff key long release  "` | `0x00CFCA62` |
| `0x60` | **long press** — longo sustentado | `"-onoff key long press  "` | `0x00CFE148` |

Despacho (CONFIRMADO), em `0x00CFC9A6` e `0x00CFE134`:

```asm
00CFC9A6  cmp  r4, #0x40   ; long start
00CFC9AE  cmp  r4, #0x10   ; press
00CFE134  cmp  r4, #0x50   ; long release
00CFE13A  cmp  r4, #0x60   ; long press
```

> Os cinco eventos estão disponíveis para **todas** as teclas — o
> despacho por evento é independente do `key_id`. É o firmware original
> que já fornece pressionar, toque curto, longo e sustentado. O OpenPod
> não precisa implementar isso.

---

## 4. Driver de entrada — CONFIRMADO

Função de inicialização: **`0x00CFC378`** (offset `0x0FC378`).

Abre três dispositivos via `open(path, 0, params)` em `0x00D636F0`:

| Dispositivo | Endereço do `ldr` | Parâmetros |
|---|---|---|
| `/dev/kadc_ch1` | `0x00CFC388` | `0x10` + callback `0x00CFC7A9` |
| `/dev/key_onoff` | `0x00CFC3C4` | **`0x37`, `0x47`** + callback |
| `/dev/key_io` | `0x00CFC3E4` | `2`, tabela em RAM `0x00819BCC` + callback |

### A prova mais forte do documento

```asm
00CFC3B8  movs r2, #0x37
00CFC3BA  movs r3, #0x47
00CFC3BC  strd r2, r3, [sp]
00CFC3C4  ldr  r0, ... "/dev/key_onoff"
00CFC3C8  bl   #0xd636f0            ; open(path, 0, {0x37, 0x47})
```

`/dev/key_onoff` é aberto declarando literalmente os `key_id` **`0x37`** e
**`0x47`** — os mesmos que o switch nomeia `onoff` e `power`.
**CONFIRMADO sem ambiguidade.**

Os demais `key_id` vêm de `/dev/key_io` (GPIO) e `/dev/kadc_ch1` (ADC). A
tabela de `key_io` está em `0x00819BCC`, que é **RAM** — inicializada em
tempo de execução, portanto **não legível estaticamente**. É exatamente
essa tabela que faria a ligação serigrafia → `key_id`.

**NÃO RESOLVIDO:** limiares do canal ADC e pinos GPIO.

---

## 5. Callback e formato do evento — CONFIRMADO

Callback registrado pelos três dispositivos: **`0x00CFC7A8`**
(ponteiro Thumb `0x00CFC7A9`).

### Empacotamento da palavra de evento

```asm
00CFC7CA  bic  r3, r3, #0x80000000   ; limpa bit 31
00CFC83C  uxtb r6, r1                ; key_id  = bits [7:0]
00CFC83E  ubfx r4, r1, #0x10, #8     ; evento  = bits [23:16]
```

```text
 31              23        16 15         8 7          0
┌──┬──────────────┬───────────┬────────────┬───────────┐
│F │   (não usado)│  evento   │ (não usado)│  key_id   │
└──┴──────────────┴───────────┴────────────┴───────────┘
 bit 31 = flag; quando ligado e a luz está acesa, o evento é descartado
          ("-========== light oN, ingore!", 0x00CFC7C0)
```

### Eventos sintéticos — CONFIRMADO

Valores pequenos vindos do driver são convertidos em pares fixos:

| Valor bruto | Vira | Endereço |
|---|---|---|
| `1` | `key_id=0x21` (enter), evento `0x10` | `0x00CFC7F0` |
| `2` | `key_id=0x21` (enter), evento `0x30` | `0x00CFC844` |
| `4` | `key_id=0x47` (power), evento `0x10` | `0x00CFC7F6` |

---

## 6. Máquina de estados — CONFIRMADO

Despacho por **tabela de salto TBH** em `0x00CFC828`, com **8 estados**:

```asm
00CFC820  ldrb  r1, [r7]
00CFC822  cmp   r1, #7
00CFC824  bhi.w #0xcfe05a        ; estado inválido
00CFC828  tbh   [pc, r1, lsl #1]
```

Tabela em `0x00CFC82C` (halfwords): `0x000E, 0x0064, 0x035A, 0x063A,
0x08A1, 0x0A1E, 0x0B4E, 0x0C0D`.

| Estado | Handler | Identificação |
|---|---|---|
| 0 | `0x00CFC848` | **idle** — `"-key status is idle "` |
| 1 | `0x00CFC8F4` | **work** — `"-key status is work "` / `watch_key_work_process` |
| 2 | `0x00CFCEE0` | PROVÁVEL: backlight off |
| 3 | `0x00CFD4A0` | PROVÁVEL: sync |
| 4 | `0x00CFD96E` | PROVÁVEL: sleep wait |
| 5 | `0x00CFDC68` | PROVÁVEL: sleep |
| 6 | `0x00CFDEC8` | PROVÁVEL: wake up |
| 7 | `0x00CFE046` | NÃO RESOLVIDO |

Os nomes dos estados 2–6 vêm das strings `watch_key_back_light_off_process`,
`watch_key_pv_sync_process`, `watch_key_sleep_wait_process`,
`watch_key_sleep_process`, `watch_key_wake_up_process` — a **ordem** não
foi confirmada contra a tabela TBH.

> **Consequência para o OpenPod:** a mesma tecla faz coisas diferentes
> conforme o estado. Qualquer remapeamento precisa considerar os 8
> caminhos, não só o `work`.

---

## 7. Camada LVGL e navegação — CONFIRMADO

O caminho completo do evento:

```text
GPIO / ADC / chave
   ↓
/dev/key_io · /dev/kadc_ch1 · /dev/key_onoff
   ↓  callback 0x00CFC7A8
desempacota (key_id, evento)
   ↓  tbh por estado  (0x00CFC828)
handler do estado (ex.: work, 0x00CFC8F4)
   ↓  bl 0x00D21374(key_id, evento)
fila de mensagens
   ↓
pstr_pageNN_process   (ex.: page4, 0x00D08A90)
   ↓
LVGL: grupo → widget focado → ctrl_id
   ↓
ação
```

### Tipos de clique na camada de apresentação — CONFIRMADO

| String | Endereço | Significado |
|---|---|---|
| `"-short click "` | `0x00D08B64` | toque curto |
| `"-long pressed "` | `0x00D08E12` | pressionar longo |
| `"-long pressed repeat "` | `0x00D08E8E` | repetição automática |
| `"-released "` | `0x00D08F20` | soltar |

### Estrutura da mensagem de UI — CONFIRMADO

Lida em `pstr_page4_process` (`0x00D08A90`):

| Offset | Campo | Valores observados |
|---|---|---|
| `+0x02` | `cmd` | deve ser `6`, senão `"no msgp->cmd"` |
| `+0x08` | página atual | comparado com a página ativa |
| `+0x0A` | `ctrl_grp` | `1`, `4`, `5` |
| `+0x0E` | `type` | `1` |
| `+0x14` | `sta` | `4` etc. |
| `+0x0C` (r4) | `ctrl_id` | `0`–`7` |

### Descoberta: `page4` é a tela Now Playing — CONFIRMADO

`pstr_page4_process` contém as ações do reprodutor:

| `ctrl_id` | Ação | String |
|---|---|---|
| — | play/pause | `"- play "` (`0x00D08C1C`) |
| `2` | próxima | `"- next "` (`0x00D08C66`) |
| `4` | anterior / repetir | `"- pre "` (`0x00D08BA4`) |
| — | velocidade | `"- speed "` (`0x00D08CEC`) |
| — | repetir | `"- repeat "` (`0x00D08D04`) |
| — | loop | `"- loop "` (`0x00D08D26`) |
| — | favorito | `"- love "` (`0x00D08D92`) |

> **Correção a `docs/GUI_ANALYSIS.md` §5.** Na Fase 0 levantei `page34`
> como candidato mais forte a Now Playing. Está **errado**: `page4` é a
> tela do reprodutor, agora confirmada por disassembly. O documento de GUI
> será corrigido.

### O ponto arquitetural mais importante

A ação **não** é função do botão físico. É função do **`ctrl_id` do widget
focado** no momento. O mesmo `◀◀` faz "anterior" no Now Playing e
"esquerda" numa lista.

Para o OpenPod isso é uma boa notícia: **mudar navegação é mudar foco e
`ctrl_id` na camada LVGL**, não mexer no driver.

---

## 8. Combinações de teclas

**Nenhuma evidência encontrada.** Procurei por:

- comparações de dois `key_id` no mesmo bloco;
- máscaras de bits de teclas simultâneas;
- strings com "combo", "combi", "hold", "simultaneous".

O despacho é estritamente **um `key_id` por evento**. A única coisa
parecida com combinação é a sequência temporal de uma tecla só
(`press → long start → long press → long release`).

Status: **NÃO EXISTE, até onde a análise alcançou.** Ausência de evidência
num despacho tão linear é um argumento forte, mas não é prova.

---

## 9. Como transformar as HIPÓTESES do §1 em fatos

O firmware já imprime tudo o que é necessário, em `0x00CFC85C`:

```text
"-key id: %x ,"                     a cada tecla
"-key %x id = %02x, event = %02x"   id + evento
```

Essas mensagens saem pela UART de depuração. O gate é o byte em
`0x00823EB0` (nível de log): a maioria exige `== 8`, a camada de
apresentação exige `== 0x0A`.

**Procedimento (somente leitura, sem risco):**

1. Localizar os pinos de UART de depuração na placa.
2. Conectar um adaptador USB-serial (3,3 V) e capturar a saída.
3. Pressionar cada botão uma vez e anotar o `key_id` impresso.
4. Repetir com pressionar longo para observar `0x40`/`0x60`.

Isso resolve `M`, `◀◀`, `▶▶`, `▶Ⅱ` e os quatro ids sem nome de uma vez.
Nenhuma gravação, nenhum risco de brick.

> Se o nível de log padrão não for 8, a saída não aparece. Nesse caso o
> caminho alternativo é localizar a escrita em `0x00823EB0` e o valor
> gravado no boot — análise estática, também sem risco.

---

## 10. Endereços — referência rápida

| Função / dado | Endereço XIP | Offset | Confiança |
|---|---|---|---|
| Init do driver de entrada | `0x00CFC378` | `0x0FC378` | CONFIRMADO |
| Callback de evento | `0x00CFC7A8` | `0x0FC7A8` | CONFIRMADO |
| Despacho TBH por estado | `0x00CFC828` | `0x0FC828` | CONFIRMADO |
| Tabela de saltos TBH | `0x00CFC82C` | `0x0FC82C` | CONFIRMADO |
| Switch de `key_id` (idle) | `0x00CFC862` | `0x0FC862` | CONFIRMADO |
| Handler do estado `work` | `0x00CFC8F4` | `0x0FC8F4` | CONFIRMADO |
| Despacho de evento (onoff) | `0x00CFC9A6` | `0x0FC9A6` | CONFIRMADO |
| Eventos `0x50`/`0x60` | `0x00CFE134` | `0x0FE134` | CONFIRMADO |
| `bl` para a fila de mensagens | `0x00D21374` | `0x121374` | PROVÁVEL |
| `pstr_page4_process` (Now Playing) | `0x00D08A90` | `0x108A90` | CONFIRMADO |
| `open()` de dispositivo | `0x00D636F0` | `0x1636F0` | PROVÁVEL |
| Nível de log global | `0x00823EB0` (RAM) | — | CONFIRMADO |
| Tabela de descritores de `key_io` | `0x00819BCC` (RAM) | — | NÃO RESOLVIDO |

---

## 11. Lacunas

| # | Lacuna | Impacto |
|---|---|---|
| 1 | Serigrafia → `key_id` (M, ◀◀, ▶▶, ▶Ⅱ) | **ALTO** — resolve com §9 |
| 2 | Os 4 `key_id` sem nome (`0x20`,`0x22`,`0x25`,`0x38`) | **ALTO** — resolve com §9 |
| 3 | Tabela de descritores em `0x00819BCC` (RAM) | médio |
| 4 | Limiares do ADC em `/dev/kadc_ch1` | médio |
| 5 | Ponte `key_id` → `LV_KEY_*` | médio — as conversões achadas (`0x00D366F8`, `0x00D3CEFA`) são internas do LVGL, não a ponte da aplicação |
| 6 | Ordem real dos estados 2–7 na tabela TBH | baixo |

---

## 12. O que isto significa para o OpenPod

**Bom:**
- os cinco tipos de evento já existem — não há o que implementar;
- a repetição automática em pressionar longo já funciona;
- navegação é definida por foco/`ctrl_id` no LVGL, não pelo driver:
  **redesenhar navegação não exige tocar no driver de entrada**.

**Cuidado:**
- a tabela que liga hardware a `key_id` está em RAM e não foi localizada;
- 8 estados de energia despacham teclas de forma diferente.

**Recomendação:** não alterar nada de entrada até o §9 estar feito.
A Fase 1 (ícones, imagens, textos) não depende disto e pode prosseguir.

---

## 13. Referências cruzadas

| Assunto | Documento |
|---|---|
| Análise preliminar de botões (Fase 0) | `docs/BUTTON_ANALYSIS.md` |
| GUI, telas e LVGL | `docs/GUI_ANALYSIS.md` |
| Layout da flash | `docs/FIRMWARE_MAP.md` |
| Ferramenta de disassembly | `tools/disasm.py` |


---

# PARTE II — Estrutura dos drivers de entrada (2026-09-12)

## 14. Quantas teclas vêm de cada dispositivo — CONFIRMED

Os parâmetros passados em cada `open()` revelam a distribuição:

| Dispositivo | Parâmetros | Interpretação |
|---|---|---|
| `/dev/key_onoff` | `strd {0x37, 0x47}` inline | **2 teclas**, ids explícitos |
| `/dev/key_io` | `strb #2` + ponteiro `0x00819BCC` + callback | **2 teclas**, via tabela em RAM |
| `/dev/kadc_ch1` | `str #0x10` + 2 bytes zerados + callback | **até 16 níveis** de ADC |

```asm
00CFC3DC  movs r3, #2                     ; key_io: 2 teclas
00CFC3DE  strb.w r3, [sp, #0xc]
00CFC3E2  ldr  r3, = 0x00819BCC           ; tabela em RAM
00CFC3EA  strd r3, r5, [sp, #0x10]        ; tabela + callback
```

### O que isso significa

```text
13 key_id conhecidos
 ├─  2  de /dev/key_onoff   (0x37 onoff, 0x47 power)   CONFIRMED
 ├─  2  de /dev/key_io      (GPIO)                     ids UNKNOWN
 └─  9  restantes           -> /dev/kadc_ch1 (ADC)     PROBABLE
```

> **A maioria dos botões do GN-438 é lida por ADC**, não por GPIO
> dedicado. Isso confirma a suspeita da §1 de uma **escada resistiva**:
> vários botões em um canal analógico, discriminados por faixa de tensão.
>
> Consequência prática para o OpenPod: remapear um botão nesse esquema é
> alterar **limiares numéricos**, não fiação — mais fácil do que parecia.
> Mas os limiares não estão na flash de forma localizável (§15).

---

## 15. Drivers localizados — CONFIRMED

Funções de inicialização de cada driver, identificadas pelos pools
literais que referenciam os nomes de dispositivo:

| Driver | Endereço | Offset |
|---|---|---|
| `/dev/kadc_ch1` | `0x00D63DC0` | `0x163DC0` |
| `/dev/key_io` | `0x00D64014` | `0x164014` |
| `/dev/key_onoff` | `0x00D642C8` | `0x1642C8` |
| `/dev/lcd` | `0x00D64404` | `0x164404` |

Strings próximas confirmam o domínio: `"sleep channel %d ok."`,
`"wakeup channel %d ok."`, `"param err."`.

---

## 16. Tentativas de resolver a tabela hardware → key_id

| Tentativa | Resultado |
|---|---|
| Varredura da FIRM por janelas com 6+ `key_id` | 1682 candidatas, **todas** instruções VFP ou código comum |
| xrefs para a tabela em RAM `0x00819BCC` | **1 só** — o próprio `open()`. Não há inicializador localizável |
| Busca por `mov rX, #<key_id>` na região dos drivers | 5 ocorrências, nenhuma em contexto de atribuição de id |
| Busca por `mov rX, #<key_id>` no gerenciador de teclas | 7 ocorrências, todas já explicadas (§5 sintéticos e `open`) |

### Conclusão — UNKNOWN

> A tabela que liga pino/limiar a `key_id` **não é derivável estaticamente**
> com os métodos aplicados. Ela é montada em runtime em `0x00819BCC`
> (GPIO) e provavelmente dentro do driver de ADC.
>
> O mapeamento de **M, ◀◀, ▶▶ e ▶Ⅱ** permanece **HYPOTHESIS** — como
> registrado na §1. **Não foi inventado.**

O caminho da §9 (capturar a UART de depuração) continua sendo o
procedimento correto, e agora com um ganho: sabendo que o grosso vem do
ADC, o log deve mostrar os ids em faixas contíguas conforme a escada.
