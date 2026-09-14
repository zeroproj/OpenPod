# GN-438 Update Mechanism

Análise do mecanismo oficial de atualização por microSD, e avaliação de
risco para o primeiro teste em hardware.

| | |
|---|---|
| **Data** | 2026-09-12 |
| **Método** | análise estática (disassembly ARM Thumb-2) + geração offline |
| **Hardware** | **nenhuma operação** — nenhum `write_flash`, `erase_flash`, `write_mem`, `exec` |
| **Pacote gerado** | `firmware/WORKING/update_v001.up` — **arquivo local, não instalado** |
| **Original** | intocado, `b7cd5eb9…4b36f`, permissão 444 |

### Convenção

**CONFIRMADO** · **PROVÁVEL** · **HIPÓTESE** · **NÃO DETERMINADO**

> **A hipótese de partida era que o SD update fosse mais seguro que a
> gravação direta por USB. A análise a confirma — mas por um motivo
> específico e verificável, não por ser "o método oficial". Ver §6.**

---

## 1. Boot/update flow

Fluxo completo do bootloader, rastreado instrução a instrução.

```text
reset
  │
  ├─ main do bootloader           0x008204EC
  │    ├─ lê flag de update por PC   bl 0x00827C02
  │    │     └─ se ligada: "update from pc" → 0x00820448
  │    └─ lê flag de update por SD   bl 0x00827C0A
  │          │
  │          ├─ DESLIGADA ──→ 0x00820610  boot normal
  │          │                  ├─ init de hardware      0x00820418
  │          │                  ├─ carrega a FIRM        0x00820470
  │          │                  ├─ sucesso → salta para runFromRam
  │          │                  └─ FALHA   → 0x00820512 "update from pc"
  │          │
  │          └─ LIGADA ────→ 0x00820520
  │                           ├─ LIMPA a flag           0x00827BFC
  │                           ├─ init de hardware       0x00820418
  │                           ├─ exibe "Finding file..."
  │                           ├─ delay 1000 ms
  │                           ├─ bl 0x00823CA0 ─ monta vtable de I/O
  │                           │     └─ bl 0x00827850  ← SDUPDATE
  │                           └─ exibe "Update finish!"
```

| Item | Conclusão | Classe |
|---|---|---|
| A flag é limpa **antes** de atualizar | evita laço infinito se falhar | **CONFIRMADO** |
| Boot normal cai em "update from pc" se a FIRM não carregar | `0x00820626 → 0x00820512` | **CONFIRMADO** |

---

## 2. sdupdate trigger

### Como o firmware detecta que deve entrar no modo — CONFIRMADO

```asm
008284C0  push {r3, lr}
008284C2  bl   #0x828490        ; lê registrador 0x23 do PMU
008284C6  and  r0, r0, #7       ; bits [2:0]
008284CA  subs r3, r0, #6
008284CC  rsbs r0, r3, #0
008284CE  adcs r0, r3           ; retorna (valor & 7) == 6
```

### Papel do PMU reg 0x23, bits [2:0] == 6 — CONFIRMADO

O registrador `0x23` do PMU é **memória persistente que sobrevive ao
reset**. Os bits [2:0] carregam o modo de boot solicitado; o valor **6**
significa "entrar em atualização por cartão SD".

Escrita: `HAL_pmu_sd_update_flag_set` em `0x0082844C`, usando
`0x00820BD0` (ler registrador do PMU) e `0x00820B68` (escrever).

### Quem liga a flag — CONFIRMADO

Existe um caminho **na própria aplicação**, em `0x00CF9D3C`:

```asm
00CF9D40  ldr r1, = "pc"    → strcmp → set flag PC → "update set pc and restart ...." → restart
00CF9D5C  ldr r1, = "sd"    → strcmp → set flag SD → "update set sd and restart ...." → restart
```

A função recebe `"sd"` ou `"pc"`, liga a flag correspondente e reinicia.

| Item | Conclusão | Classe |
|---|---|---|
| O gatilho é um flag persistente no PMU, não combinação de teclas | | **CONFIRMADO** |
| A aplicação consegue ligá-lo sem USB | função `0x00CF9D3C` aceita `"sd"` | **CONFIRMADO** |
| Qual item de menu chama essa função com `"sd"` | ⚠️ **NÃO DETERMINADO** — o item não foi localizado no aparelho. Ver §2.1 | **NÃO DETERMINADO** |
| Existe também uma tabela de comandos de console | `cpu`, `reboot`, `update`, `sleep`, `hello`, `tp`, `sd` — em `0x049F80` | **CONFIRMADO** |
| Existe outra forma de ligar a flag | | **NÃO DETERMINADO** |

### 2.1 ⚠️ O item de menu — NÃO LOCALIZADO no aparelho

**Estado atual: NÃO DETERMINADO.** O mantenedor verificou o aparelho e o
caminho `Configurações → Opções de actualização → Actualização do cartão
SD` **não existe** no menu — com ou sem cartão inserido.

| Afirmação | Classe |
|---|---|
| As strings existem, em 8 idiomas, no bloco de idioma | **CONFIRMADO** |
| A função `0x00CF9D3C` grava o flag ao receber `"sd"` | **CONFIRMADO** |
| Ela está numa **tabela de comandos de console** (`0x049F80`) | **CONFIRMADO** |
| Existe item de menu na GUI que a aciona | **NÃO DETERMINADO** |
| O `sdupdate` é acionável sem UART | **NÃO DETERMINADO** |

#### ⚠️ Duas classificações indevidas, registradas

Esta linha foi promovida a CONFIRMADO **duas vezes**, ambas sem base:

1. **Primeira:** a partir de as strings existirem no firmware. String
   existir não prova tela exposta.
2. **Segunda:** a partir de uma frase ambígua do mantenedor, que eu li
   como confirmação sem checar se tinha entendido.

**Regras derivadas, agora explícitas:**

- só é CONFIRMADO o que foi **lido no disassembly** ou **observado de
  forma inequívoca no aparelho**;
- relato do mantenedor só vale como observação depois de **confirmado o
  entendimento** — frase ambígua não é evidência;
- na dúvida, **perguntar antes de classificar**.

#### O que a evidência realmente sugere

`cpu (clk)`, `reboot`, `update`, `sleep`, `hello`, `tp`, `sd` não são
nomes de itens de menu — são comandos de **console de depuração**, quase
certamente sobre UART. É **PROVÁVEL** que esse seja o caminho real, e que
as strings de menu pertençam a uma tela não exposta nesta build.

#### Hipóteses abertas

Na sessão de 2026-09-12 afirmei **CONFIRMADO** que o gatilho seria
`Configurações → Opções de actualização → Actualização do cartão SD`.

**A afirmação era indevida.** Ela se apoiava apenas em as strings
existirem no firmware — e **string existir não significa item exposto na
interface**. O mantenedor verificou no aparelho: **essa opção não aparece
no menu de configurações.**

| Afirmação | Classe correta |
|---|---|
| As strings `Opções de actualização`, `Actualização do PC` e `Actualização do cartão SD` existem, em 8 idiomas | **CONFIRMADO** |
| Existe função que grava o flag do PMU ao receber `"sd"` (`0x00CF9D3C`) | **CONFIRMADO** |
| Essa função está numa **tabela de comandos de console** em `0x049F80` (`cpu`, `reboot`, `update`, `sleep`, `hello`, `tp`, `sd`) | **CONFIRMADO** |
| Existe item de menu na GUI que a aciona | **NÃO DETERMINADO** |
| O `sdupdate` é acionável sem UART | **NÃO DETERMINADO** |

#### O que a tabela de comandos sugere

`cpu (clk)`, `reboot`, `update`, `sleep`, `hello`, `tp`, `sd` não são
nomes de itens de menu — são **comandos de um console de depuração**,
quase certamente sobre UART. É **PROVÁVEL** que `update sd` seja o caminho
real, e que as strings de menu pertençam a uma tela não exposta nesta
build ou neste modelo.

#### Hipóteses ainda abertas

| # | Hipótese | Como testar |
|---|---|---|
| 1 | O item só aparece **com cartão inserido** | inserir o cartão e reabrir o menu |
| 2 | O item está em outro menu, não em Configurações | percorrer todos os menus |
| 3 | A tela existe mas não está ligada nesta build | disassembly da montagem do menu |
| 4 | O caminho real é o console UART (`update sd`) | localizar os pinos de UART |

> **Lição de método, registrada:** foi o mesmo erro de duas sessões atrás —
> inferir de artefato estático e classificar como CONFIRMADO sem
> observação. A regra da §8 do relatório cobre documentar julgamentos;
> falta a ela cobrir **o rigor da classificação**. Só é CONFIRMADO o que
> foi lido no disassembly **ou** observado no aparelho.

---

## 3. update.up format

### Onde o arquivo é procurado — CONFIRMADO

```asm
00823B30  bl  #0x826ab8         ; f_mount(0)         volume 0 = microSD
00823B66  bl  #0x8263e2         ; f_stat("0:\update.up", &finfo)
00823B82  movs r2, #1           ; modo = 1 = somente leitura
00823B88  bl  #0x826464         ; f_open(fil, "0:\update.up", FA_READ)
```

| Item | Valor | Classe |
|---|---|---|
| Caminho literal | `0:\update.up` — **raiz** do cartão | **CONFIRMADO** |
| Nome e extensão | fixos; sem varredura de diretório | **CONFIRMADO** |
| Modo de abertura | `1` = somente leitura — o bootloader **nunca escreve no cartão** | **CONFIRMADO** |
| Filesystem | FatFs; FAT32 ou exFAT | **CONFIRMADO** |

### Estrutura do cabeçalho

```text
0x0000  "CONFIG"        6 bytes
0x0006  uint32  0x100   codeOffsetInByte = deslocamento flash → arquivo
0x0010  uint32  fw_size
0x0014  uint16  CRC-16/CCITT-FALSE do payload
0x0016  char[]  "SL6801" ou "SL6806", terminado em NUL
0x00FE  0x55
0x00FF  0xAA
0x0100  payload = cópia literal de flash[0 : fw_size]
```

### Quais campos o bootloader REALMENTE lê — CONFIRMADO

Varredura de **todos** os acessos ao buffer do cabeçalho dentro do
`sdupdate` (`0x00827850`–`0x00827BD4`):

| Offset | Campo | Lido pelo `sdupdate`? | Como |
|---|---|---|---|
| `0x00` | magic | **SIM** | `memcmp(buf, "CONFIG", 5)` — só **5** bytes |
| `0x06` | `codeOffsetInByte` | **SIM** | `ldr.w sb, [r5, #6]` |
| `0x10` | `fw_size` | **NÃO** | nunca lido do cabeçalho |
| `0x14` | CRC do payload | **NÃO** | nunca lido |
| `0x16` | chip | **SIM** | `memcmp(buf+0x16, "SL6801", 6)` |
| `0xFE/FF` | `0x55 0xAA` | **NÃO** | nunca lido |

> Os três acessos a `[r5, #0x10]`, `[r5, #4]` que aparecem mais adiante na
> função ocorrem **depois** que o buffer foi sobrescrito por leituras
> seguintes — **não** leem o cabeçalho CONFIG. Verificado por ordem de
> execução.

**Conclusão — CONFIRMADO:** `fw_size`, o CRC do payload e a assinatura
`0x55AA` são **metadados**, do ponto de vista do caminho por cartão SD.
São **PROVÁVEL** que sirvam à ferramenta oficial de gravação por USB (o
README do `fwhelper` fala em "official flashing tool**s**", no plural) —
**NÃO DETERMINADO**.

### Como o tamanho a gravar é determinado — CONFIRMADO

**Não** por `fw_size`. Pelo **tamanho real do arquivo**, obtido via a
tabela de operações de I/O:

```asm
008278D2  ldr r3, [r3, #0x10]   ; vtable +0x10 = função "tamanho"
008278D4  blx r3                ; r8 = tamanho do arquivo
```

A função é `0x00823A74`: `ldrd r0, r1, [r0, #0x10]` — lê o campo de
tamanho de 64 bits do objeto FatFs.

### fw_size inclui o quê — CONFIRMADO

```c
for (cada particao) {
    if (nome == "PSMP") continue;      /* EXCLUIDA */
    fw_size = max(fw_size, offset + tamanho);
}
```

| Partição | off | len | fim | incluída |
|---|---|---|---|---|
| FIRM | `0x00E000` | `0x192570` | `0x1A0570` | sim |
| TONE | `0x1A1000` | `0x002038` | **`0x1A3038`** | sim — define `fw_size` |
| PSMP | `0x1FC000` | `0x004000` | `0x200000` | **NÃO** |

`fw_size = 0x1A3038`. Excluir `PSMP` significa que a atualização **não
apaga a configuração do usuário** — **PROVÁVEL** que seja intencional.

### Validação do timestamp — reavaliada

O `sdupdate` compara dois valores e aborta com `0xFC` se forem **iguais**.
A estrutura do desvio é **CONFIRMADA**. Porém a origem dos valores **não
está resolvida**: o código lê `ptable+0x10` e usa como offset de `lseek`,
mas nesse campo a imagem real contém o **nome** `"FIRM"` (`0x4D524946`).

Detalhe completo em `docs/SDUPDATE_ANALYSIS.md` §17.

| Item | Classe |
|---|---|
| Existe um desvio que retorna `0xFC` quando dois valores são iguais | **CONFIRMADO** |
| O valor comparado é o timestamp instalado | **NÃO DETERMINADO** |
| O layout de ptable esperado difere do da imagem | **PROVÁVEL** |
| A verificação está inerte neste aparelho | **HIPÓTESE** |

> Como o próprio timestamp **não é lido do cabeçalho CONFIG** (ele vive em
> `FIRM+0x04`, dentro do payload), e o `fwhelper` o copia sem alterar, um
> pacote gerado da imagem original carrega o mesmo timestamp do firmware
> instalado. **Se** a verificação estiver ativa, ela recusaria. Se estiver
> inerte, prosseguiria. Não é possível prever estaticamente.

---

## 4. Validation performed

Tudo o que o `sdupdate` verifica, em ordem, e o que faz ao falhar:

| # | Verificação | Onde | Falha → retorno |
|---|---|---|---|
| 1 | alocação do objeto de arquivo | `0x0082786A` | `0xFF` |
| 2 | alocação do buffer de 512 B | `0x00827882` | `0xFF` |
| 3 | `memcmp(buf, "CONFIG", 5)` | `0x008278A4` | **`0xFE`** |
| 4 | `memcmp(buf+0x16, "SL6801", 6)` | `0x008278BC` | **`0xFA`** |
| 5 | comparação de dois valores (timestamp?) | `0x00827986` | **`0xFC`** se iguais |
| 6 | comparação de tamanho | `0x008279A2` | nenhuma — só muda o dimensionamento do apagamento |
| 7 | CRC arquivo × releitura da flash | `0x00827A36` | nenhum retorno distinto |

**O que NÃO é verificado — CONFIRMADO:**

- **não há assinatura criptográfica**;
- **o CRC do payload (CONFIG+0x14) não é conferido antes de gravar**;
- não há verificação de versão, modelo além do nome do chip, nem de
  tamanho mínimo/máximo do arquivo.

### Ao falhar

Em todos os casos 1–5, o fluxo é idêntico (`0x00827BBA`): **fecha o
arquivo, libera o buffer e retorna o código de erro — antes de qualquer
apagamento ou gravação**. **CONFIRMADO.**

> **Consequência importante:** qualquer recusa do pacote é inofensiva. O
> aparelho continua com o firmware atual. Não existe caminho em que uma
> validação reprovada cause dano.

---

## 5. Flash write sequence

### Endereço de destino — CONFIRMADO

```asm
008278E8  movs r1, #0x20
008278EE  bl   #0x820a64        ; parition_start = flash_read32(0x20)
00827904  cbnz r3, ...          ; se 0, assume 0x3000
```

`parition_start` vem do campo `+0x20` do cabeçalho `HLKJ` da **flash
instalada** = `0x0000D000`. É onde a gravação começa.

### Apagamento — CONFIRMADO

```asm
008279AE  sub.w r6, r8, r6      ; delta = tamanho_do_arquivo - parition_start
008279B2  lsrs  r6, r6, #0xc    ; / 4096
008279B4  adds  r6, #1          ; + 1 setor
00827A68  ldr   r0, [sp, #0x18]
00827A6C  add.w r0, r0, r7, lsl #12
00827A70  bl    #0x8220e0       ; erase_sector(parition_start + n*4096)
```

Setores de **4 KiB**, a partir de `parition_start`, subindo.

### Gravação — CONFIRMADO

```asm
008279D6  lsr.w r3, r8, #9      ; blocos = delta / 512
00827AFE  blx   r6              ; f_read(fil, buf, 0x200)
00827B0A  bl    #0x821f84       ; crc_arquivo = crc_acc(crc, buf, 0x200)
00827B2C  bl    #0x821ffc       ; flash_write(buf, parition_start + n*512, 0x100)
00827B4? bl    #0x821ffc       ; segunda página de 256 bytes
```

Lê **512 bytes** do arquivo por vez; grava como **duas páginas de 256**.

### Geometria concreta para o nosso pacote

```text
tamanho do arquivo = 0x100 + 0x1A3038 = 0x1A3138
parition_start     = 0x00D000
delta              = 0x196138

APAGA   (0x196138 >> 12) + 1 = 407 setores
        0x00D000 .. 0x1A4000     (1.667.072 bytes)

GRAVA   0x196138 >> 9 = 3248 blocos de 512
        0x00D000 .. 0x1A3000     (1.662.976 bytes)
        origem: arquivo 0x00D100 .. 0x1A3100
```

### ⚠️ Consequência descoberta nesta análise — CONFIRMADO (aritmética)

```text
apagado mas NÃO gravado: 0x1A3000 .. 0x1A4000   (4096 bytes → 0xFF)
TONE ocupa             : 0x1A1000 .. 0x1A3038
→ os últimos 56 bytes da TONE ficariam apagados
→ o CRC gravado da TONE (0x9177) deixaria de conferir
```

O contador de blocos **trunca** (divisão inteira por 512), enquanto o de
setores **arredonda para cima e soma 1**. A janela entre os dois fica
apagada e não reescrita.

| Item | Classe |
|---|---|
| A aritmética acima segue do disassembly | **CONFIRMADO** |
| A TONE perderia 56 bytes | **PROVÁVEL** (depende de qual ramo de `0x008279A2` é tomado) |
| Algo verifica o CRC da TONE em runtime | **NÃO DETERMINADO** |
| Impacto real (TONE = sons de sistema, 8 KiB) | provavelmente cosmético — **HIPÓTESE** |

> Isto **não é um defeito do nosso pacote**: é comportamento do próprio
> mecanismo do fabricante, e qualquer atualização oficial com este
> `fw_size` teria o mesmo efeito.

### Verify após a escrita — CONFIRMADO

```asm
00827B98  ldr r1, [sp, #0x18]
00827B9E  add.w r1, r1, r3, lsl #9
00827BA4  bl  #0x820a64         ; RELÊ da flash
00827BB0  bl  #0x821f84         ; crc_flash = crc_acc(crc, buf, 0x200)
00827A30  ldr r0, ... "crc cmp %x %x"
00827A36  cmp r8, r6            ; crc_arquivo vs crc_flash
00827A38  bne #0x827a50         ; divergiu → termina sem a etapa final
```

Ambos os acumuladores começam em `0xFFFF`. É **verificação de gravação**
(arquivo × releitura), não validação do pacote.

### Erro durante a gravação — CONFIRMADO

```asm
00827B10  cmp r6, #0            ; resultado do f_read
00827B12  bne #0x827bba         ; erro de leitura → aborta e retorna
```

Se o CRC de verificação divergir, o código simplesmente **não executa a
etapa final** (progresso 100% + `0x00822F7C`) e retorna. **Não tenta de
novo, não desfaz, não sinaliza erro distinto.**

### Rollback — CONFIRMADO: **NÃO EXISTE**

Nenhuma cópia de segurança, nenhuma partição A/B, nenhuma reversão. A
gravação é destrutiva e de sentido único.

### O bootloader permanece intacto? — CONFIRMADO: **SIM**

Apagamento e gravação começam em `parition_start` = `0x00D000` e sobem.
A faixa `0x000000`–`0x00D000` — cabeçalho `HLKJ` e payload inteiro do
bootloader — **nunca é tocada** por este caminho.

---

## 6. SD vs USB comparison

| Característica | **SD update** | **USB write** |
|---|---|---|
| Quem controla a gravação | o **bootloader do próprio aparelho** | o **PC**, via comandos crus do boot ROM |
| Validação do pacote | magic + chip + comparação de timestamp | **nenhuma** — grava o que mandarem |
| Validação de CRC | CRC do payload **não** é conferido; só verify pós-escrita | **nenhuma** |
| Região do bootloader protegida? | **SIM** — grava só a partir de `0xD000` | **NÃO** — `write_flash 0 …` atinge `0x0` |
| Erro de gravação tratado? | detectado por releitura; **sem retry nem rollback** | **não tratado** |
| Verify após escrita | **SIM** — CRC arquivo × flash | **não**, salvo se o operador fizer |
| Possibilidade de brick | **baixa** — bootloader sobrevive | **alta** — bricks documentados na comunidade |
| Recuperação | reexecutar o update; ou cair em "update from pc" | só se o bootloader tiver sobrevivido |

### Veredito sobre a hipótese inicial — **CONFIRMADA, com motivo preciso**

O SD update **é** mais seguro que o USB write. Mas **não** porque valide
melhor o pacote — a validação dele é fraca (sem assinatura, sem conferir o
CRC do payload antes de gravar).

É mais seguro por **uma razão estrutural verificável**:

> **O `sdupdate` nunca apaga nem grava a faixa `0x0`–`0xD000`.**
> O bootloader — que é o único caminho de recuperação — fica fora do
> alcance da operação, por construção.

O `write_flash` por USB não tem essa limitação: aceita qualquer endereço,
inclusive `0`.

---

## 7. Brick risks

### O risco da flash anômala se aplica ao `sdupdate`? — análise

`docs/EXTERNAL_RESEARCH.md` §5.2 registra, do autor da `smartlink_flash`:

> *"All is fine with 1 → 0, but flash can somehow restore 0 → 1 with 90 %
> efficiency without erasing."*

| Pergunta | Resposta | Classe |
|---|---|---|
| O `sdupdate` faz erase antes do write? | **SIM** | **CONFIRMADO** |
| Em quais setores? | 4 KiB, de `0xD000` até `0xD000 + ((delta>>12)+1)*0x1000` | **CONFIRMADO** |
| Faz verify? | **SIM**, por releitura + CRC | **CONFIRMADO** |
| Escreve o bootloader? | **NÃO** | **CONFIRMADO** |
| Pula regiões? | **SIM** — `PSMP` fora do pacote; janela final apagada e não gravada (§5) | **CONFIRMADO** |
| Existe fallback? | **SIM** — "update from pc" se a FIRM não carregar | **CONFIRMADO** |
| Um firmware inválido pode deixar sem boot? | **Sem boot do APP, sim. Sem bootloader, não.** | **CONFIRMADO** |

### Por que a anomalia da flash é menos grave aqui

O `sdupdate` **apaga antes de gravar**, que é exatamente o procedimento
correto. A anomalia relatada diz respeito a gravar **sem** apagar — que é
o que o `smtlink_dump` faz por USB, não o que o `sdupdate` faz.

Ainda assim, se uma gravação sair errada, o `sdupdate` **detecta** (CRC de
releitura) mas **não corrige**. O resultado seria uma FIRM corrompida.

### Pior caso realista

```text
FIRM corrompida
   ↓
boot normal tenta carregar        0x00820470
   ↓ falha
boot cai em "update from pc"      0x00820512
   ↓
aparelho enumera por USB para regravação
```

O aparelho **liga em modo de recuperação em vez do app**. Chato,
recuperável. **Não é tijolo** — desde que o bootloader esteja íntegro, o
que o `sdupdate` garante por construção.

> **O que brica de verdade**, segundo os relatos da comunidade: apagar a
> flash inteira, ou `write_flash` por USB atingindo `0x0`–`0xD000`, ou
> gravar sem ter feito dump antes. **Nada disso está neste caminho.**

---

### 7.1 Calibragem: quanto preocupar-se com cada bloqueador

Os dois bloqueadores registrados no projeto têm **naturezas diferentes** e
não devem receber o mesmo peso. Distingui-los importa mais do que a lista
de fatos acima.

#### Bloqueador 1 — verificação de timestamp imprevisível: **NÃO é preocupante**

| | |
|---|---|
| Pior desfecho | **recusa** do pacote |
| Quando ocorre | **antes** de qualquer apagamento ou gravação (§4) |
| Dano possível | **nenhum** — o aparelho segue com o firmware atual |
| Falso "não" | custa uma tentativa |
| Falso "sim" | a atualização prossegue, que é o que se quer |

**Não existe cenário em que esta verificação danifique o aparelho.**
É imprevisibilidade, não risco. Classificar os dois como "bloqueadores"
no mesmo nível foi um erro de enquadramento — corrigido aqui.

#### Bloqueador 2 — gravação não determinística: **moderado, e contido**

Real, mas cercado por três barreiras **confirmadas por disassembly**:

| Barreira | Evidência |
|---|---|
| O `sdupdate` só apaga/grava de `0xD000` para cima | laço de erase em `0x00827A68` |
| O bootloader (`0x0`–`0xD000`) nunca é tocado | mesma análise |
| Se a FIRM não carregar, o boot cai em "update from pc" | `0x00820626 → 0x00820512` |

Ressalva honesta: o verify por releitura **detecta** uma gravação ruim mas
**não desfaz nem tenta de novo** (§5). É barreira de **diagnóstico**, não
de proteção.

Atenuante relevante: a anomalia relatada (`0 → 1` sem apagar) diz respeito
a gravar **sem apagar**. O `sdupdate` **apaga antes de gravar** — o
procedimento correto. Quem grava sem apagar é o `smtlink_dump` por USB.

#### Veredito calibrado

> **Risco baixo-moderado pelo caminho SD — e menor do que o enquadramento
> anterior deste projeto sugeria.**
>
> Perder o aparelho de forma irrecuperável pelo cartão SD é **pouco
> provável**. Levar um susto — ligar em recuperação e ter de regravar — é
> **plausível**, e deve-se estar preparado para isso.
>
> A incerteza que realmente importa não é nenhum dos dois bloqueadores:
> **é se o V001 inicializa**, o que nenhum método estático responde.

#### Registro de correção

Sessões anteriores encerraram com a frase *"os bloqueadores de gravação
seguem de pé"*, tratando os dois como equivalentes. **Isso deu ao
bloqueador 1 um peso que ele não tem.** A calibragem correta é a desta
seção.

---

## 8. Recovery possibilities

| # | Pergunta | Resposta | Classe |
|---|---|---|---|
| 1 | Ainda entra em bootloader após update malsucedido? | Sim — o bootloader não é tocado | **CONFIRMADO** (por não-gravação) |
| 2 | O bootloader fica preservado? | Sim | **CONFIRMADO** |
| 3 | Pode ser restaurado via SD? | Provável — basta outro `update.up`; depende de a flag poder ser religada sem o app | **PROVÁVEL** |
| 4 | Pode ser restaurado via USB? | O modo "update from pc" existe e é acionado automaticamente ao falhar o load da FIRM | **PROVÁVEL** |
| 5 | Qual o procedimento de recuperação? | ver abaixo | **PROVÁVEL** |
| 6 | Qual o pior caso? | ver abaixo | |

### Procedimento de recuperação — **PROVÁVEL, NUNCA EXERCITADO**

```text
1. se o aparelho liga e mostra a UI      → nada a fazer
2. se não carrega o app                  → cai sozinho em "update from pc"
3. conectar por USB; confirmar enumeração (301a:2800 ou 301a:2801)
4. regravar a partir de firmware/ORIGINAL/GN438_original.bin
```

> **Esta sequência é derivada do código, não testada.** O passo 3 depende
> de o modo de recuperação enumerar de fato — **NÃO DETERMINADO**.
>
> **Não invente etapas além destas.** Se o aparelho não enumerar, não há
> procedimento conhecido.

### Pior caso possível

| Cenário | Probabilidade | Consequência |
|---|---|---|
| Pacote recusado na validação | média | nada acontece |
| FIRM corrompida, boot cai em recuperação | baixa | regravar por USB |
| Bootloader corrompido | **muito baixa** pelo caminho SD | irrecuperável — **NÃO DETERMINADO** se existe saída |

---

## 9. V001 package validation

### A imagem

| | ORIGINAL | V001 |
|---|---|---|
| Tamanho | 2.097.152 | 2.097.152 — **idêntico** |
| SHA-256 | `b7cd5eb9…4b36f` | `9dc755ee…9215c` |
| CRC FIRM | `0x49A6` | **`0x583A`** |
| CRC TONE | `0x9177` | `0x9177` |
| `loadCrc` boot | `0x759D` | `0x759D` |
| `headerCrc` | `0x34DB` | `0x34DB` |
| `loadCrc` FIRM | `0x68E1` | `0x68E1` |

Regiões alteradas: **718 bytes em 43 faixas** — 716 de pixels
(`0x0CE96C`–`0x0CF878`, ícone Música da folha do menu) + 2 do CRC da FIRM
(`0x00D01C`). Estrutura da flash inalterada; nenhuma partição mudou de
offset ou tamanho.

### O pacote

| | |
|---|---|
| Arquivo | `firmware/WORKING/update_v001.up` |
| Tamanho | 1.716.536 bytes = `0x100` + `0x1A3038` |
| SHA-256 | `b45bcf6d5f20f3836b935692f52fb35302536feb2b90edfa5345b8c0224ec314` |
| Magic | `"CONFIG"` |
| `codeOffsetInByte` | `0x100` |
| `fw_size` | `0x1A3038` |
| CRC do payload | `0xE662` |
| Chip | `SL6801` |
| Assinatura | `0x55 0xAA` |
| Instalado no aparelho | **NÃO** |

### Validações executadas

```text
[OK] tamanho minimo                               1716536 bytes
[OK] magic "CONFIG"
[OK] codeOffsetInByte == 0x100
[OK] fw_size coerente com o arquivo
[OK] CRC-16 do payload                            0xE662 == calculado
[OK] chip id                                      SL6801
[OK] assinatura 0x55 0xAA
[OK] resto do cabecalho zerado
[OK] payload comeca com HLKJ
[OK] payload identico a flash[0:fw_size] da V001   1716280 bytes
[OK] bytes divergentes no payload = 0
                                       11 OK, 0 falhas
```

### Validação cruzada — a prova mais forte

O pacote foi comparado com o produzido pela **implementação de
referência** (`fwhelper dump2fw`, upstream, commit `49d51d17`):

```console
$ cmp update_v001.up ref_v001.up
  IDENTICOS
b45bcf6d…c314  update_v001.up
b45bcf6d…c314  ref_v001.up        (fwhelper)
```

**Byte a byte idêntico.** E `fwhelper scan` sobre o pacote não reporta
nenhuma divergência de checksum.

---

## 10. Known unknowns

| # | Incógnita | Classe | Bloqueia? |
|---|---|---|---|
| 1 | **O V001 inicializa no aparelho?** | **NÃO DETERMINADO** — não é determinável estaticamente | é a questão do teste |
| 2 | A verificação de timestamp dispara? | **NÃO DETERMINADO** | pode recusar o pacote (inofensivo) |
| 3 | Qual item de menu chama `"sd"` | **PROVÁVEL** | prático |
| 4 | A TONE perde 56 bytes? Alguém verifica seu CRC? | **PROVÁVEL** / **NÃO DETERMINADO** | provavelmente cosmético |
| 5 | O modo "update from pc" enumera de fato? | **NÃO DETERMINADO** | **é a rede de segurança — crítico** |
| 6 | Confiabilidade da gravação (anomalia 0→1) | risco conhecido, não quantificado | — |
| 7 | Para que servem `fw_size` e o CRC do payload | **PROVÁVEL**: ferramenta USB | não |

---

## 11. Recommendation for first hardware test

### Pré-requisitos, em ordem — todos sem risco

1. **Confirmar a recuperação ANTES de precisar dela.** Conectar o GN-438
   por USB, verificar que enumera, e fazer um `read_flash` de teste com o
   `smtlink_dump`. **Somente leitura.** Se isso não funcionar, **não
   prosseguir** — a rede de segurança não existe.
2. **Capturar a UART de depuração.** Passivo. Mostra `"header pass"`,
   `"mark pass"`, `"fileStamp %x f s:%x"` e `"crc cmp %x %x"` — isto
   resolve as incógnitas 2 e 4 **observando**, sem adivinhar.
3. **Localizar o item de menu** que chama `"sd"` (análise estática).
4. **Ter o `GN438_original.bin` e um `update_原.up` de restauração prontos**
   antes de qualquer gravação.

### Só então

5. Copiar `update_v001.up` para a raiz do cartão, acionar a atualização
   pelo menu, e acompanhar pela UART.

---

## Podemos testar o V001 via SD?

# SIM, COM RESSALVAS

### Por que SIM

- O **caminho está identificado e confirmado** por disassembly, do gatilho
  no PMU até o laço de gravação.
- O **pacote é byte a byte idêntico** ao da implementação de referência —
  não é uma reconstrução nossa "parecida", é exatamente o formato.
- O **bootloader está fora do alcance** da operação, por construção — e é
  isso, não a qualidade da validação, que torna o caminho SD mais seguro.
- Existe **fallback automático** para "update from pc" se a FIRM não
  carregar.
- Temos o **original preservado**, com round-trip byte-a-byte provado.
- Há **precedente** de firmware modificado gravado com sucesso nesta
  família (`EXTERNAL_RESEARCH.md` §5.1).

### As ressalvas — e elas são reais

1. **Não sabemos se o V001 inicializa.** Nenhuma análise estática responde
   isso. É exatamente o que o teste vai descobrir.
2. **A rede de segurança nunca foi exercitada.** O modo "update from pc"
   existe no código, mas não sabemos se enumera na prática. **Este é o
   único pré-requisito que eu consideraria bloqueante** — é o item 1 do
   §11, e é somente leitura.
3. **A verificação de timestamp é imprevisível.** Pode recusar o pacote.
   Inofensivo, mas confuso se acontecer sem explicação.
4. **A gravação não é determinística** e o `sdupdate` detecta mas não
   corrige. Um erro deixaria a FIRM corrompida — recuperável, mas chato.
5. **A TONE provavelmente perde 56 bytes.** Comportamento do mecanismo do
   fabricante, não do nosso pacote.

### O que eu faria

Resolver o **item 1 do §11** primeiro — confirmar que o aparelho enumera e
lê por USB. É leitura pura, leva minutos, e é a diferença entre um
experimento e uma aposta. Com isso feito, o teste do V001 passa de
"SIM, COM RESSALVAS" para um risco que eu chamaria de aceitável.

Sem isso, seria gravar sem saber se existe volta.
