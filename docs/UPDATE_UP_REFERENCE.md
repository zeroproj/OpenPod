# OpenPod — UPDATE_UP_REFERENCE

Busca por um pacote `update.up` real da família YP3 / SL6801 e
reconciliação do formato.

| | |
|---|---|
| **Data** | 2026-09-12 |
| **Objetivo** | obter referência estrutural para o formato `update.up` |
| **Pacote binário real encontrado** | **NÃO** |
| **Especificação autoritativa encontrada** | **SIM** — código-fonte do conversor oficialmente reconhecido |
| **Hardware** | nenhuma operação; nenhum flash |
| **`update.up` criado** | **NÃO** — conforme instruído |
| **Firmware original** | intocado, SHA-256 confere |

---

## 0. ⚠️ Correções a documentos anteriores

### 0.1 A rejeição por timestamp NÃO é previsível (2026-09-12)

`docs/SDUPDATE_ANALYSIS.md` §6 e a §5 deste documento afirmam que um
pacote gerado do rebuild byte-a-byte **seria rejeitado com `0xFC`** por ter
timestamp igual ao instalado.

**Essa afirmação não se sustenta.** Ela pressupõe que o valor comparado
pelo bootloader é, de fato, o timestamp instalado. A análise byte a byte
do §12 mostra que a origem dos dois valores comparados **não está
resolvida** — e que, sob a leitura mais provável, ambos são valores
espúrios.

| Situação | Antes | Agora |
|---|---|---|
| Estrutura do desvio (`beq` → `0xFC`) | CONFIRMADO | **CONFIRMADO** (inalterado) |
| O valor comparado é o timestamp | afirmado | **NÃO RESOLVIDO** |
| Um rebuild idêntico seria rejeitado | afirmado | **NÃO RESOLVIDO** |

**Consequência prática:** trocar o timestamp continua sendo o mais
prudente, mas **não é garantia de aceitação** — e tampouco se pode
garantir que um pacote idêntico seria recusado. Ver §12.3.

### 0.2 Precedente de patch bem-sucedido (2026-09-12)

A §7 afirmava que ninguém havia gravado firmware modificado nesta família.
**Errado** — ver `docs/EXTERNAL_RESEARCH.md` §5.1.

---

## 1. Resultado

**Não localizei nenhum arquivo `update.up` publicado.** As buscas estão
documentadas no §6.

Em compensação, encontrei algo de valor superior para o objetivo declarado
("referência estrutural"): **o código-fonte do utilitário que gera esse
formato**, escrito pelo mesmo autor que fez a engenharia reversa do chip.

```text
smartlink_flash/fwhelper/main.c
commit 49d51d17e825afbbbc2be7d91d6367674543c2e3   (já travado na sessão 3)
```

`fwhelper/README.md`:

```text
Converts a flash dump into a firmware update file:
    ./fwhelper flash.bin dump2fw update.up
Prints info about a dump or update file:
    ./fwhelper flash.bin scan
```

E o autor confirma, na issue #3 do repositório, para que serve:

> "there is a utility in the `fwhelper` folder that converts the raw dump
> to a format recognized by **official flashing tools**. So you can flash
> the firmware that way."

> **Uma amostra binária mostraria um exemplo do formato. O código-fonte
> mostra o formato inteiro, incluindo os campos que uma amostra específica
> deixaria com valor zero ou ambíguo.** Para o objetivo declarado, isto é
> estritamente melhor.

O repositório já estava travado por hash em
`tools/external/smartlink_flash.lock` desde a sessão 3 — ou seja, a
proveniência e a integridade desta referência já estão registradas.

---

## 2. O formato `update.up` — especificação completa

De `dump2fw()`, `fwhelper/main.c` linhas 138–153:

```c
uint8_t buf[0x100];
memset(buf, 0, 0x100);
memcpy(buf, "CONFIG", 6);                      // +0x00
WRITE32_LE(buf + 6, 0x100);                    // +0x06
WRITE32_LE(buf + 0x10, fw_size);               // +0x10
WRITE16_LE(buf + 0x14, crc16(mem, fw_size));   // +0x14
strcpy((char*)buf + 0x16, chip_name);          // +0x16
buf[0xfe] = 0x55;                              // +0xFE
buf[0xff] = 0xaa;                              // +0xFF
fwrite(buf, 1, 0x100, fo);
fwrite(mem, 1, fw_size, fo);                   // imagem da flash, de 0 a fw_size
```

### Cabeçalho CONFIG (0x100 bytes)

| Offset | Tam. | Campo | Valor | Origem |
|---|---|---|---|---|
| `0x00` | 6 | magic | `"CONFIG"` | fwhelper |
| `0x06` | 4 | tamanho do cabeçalho | `0x100` | fwhelper |
| `0x0A` | 6 | zeros | `0` | `memset` |
| `0x10` | 4 | `fw_size` — tamanho do payload | calculado | fwhelper |
| `0x14` | 2 | CRC-16 do payload | calculado | fwhelper |
| `0x16` | 10 | nome do chip | `"SL6801"` / `"SL6806"` | fwhelper |
| `0x20`–`0xFD` | — | zeros | `0` | `memset` |
| `0xFE` | 1 | assinatura | `0x55` | fwhelper |
| `0xFF` | 1 | assinatura | `0xAA` | fwhelper |

### Payload

Cópia literal da imagem de flash, de `0x00000000` até `fw_size`.

`fw_size` = maior `offset + tamanho` entre as partições, **ignorando
`PSMP`**. Ou seja, o pacote **não inclui** a área de configuração
persistente do aparelho — ela não é sobrescrita.

### Seleção do nome do chip

```c
n = READ32_LE(p); ver = READ32_LE(p + 8);
...
if (ver >= 0x30) chip_name = "SL6806";   /* senão, SL6801 */
```

O terceiro word do cabeçalho da tabela de partições é uma **versão**.
Campo que na Fase 0 eu havia registrado apenas como "zero".

---

## 3. Reconciliação com o disassembly

Comparação campo a campo entre o que o bootloader **lê** (sessão 4,
`docs/SDUPDATE_ANALYSIS.md`) e o que o `fwhelper` **escreve**.

| Campo | Disassembly do bootloader | fwhelper | Veredito |
|---|---|---|---|
| `+0x00` magic | `memcmp(buf, "CONFIG", 5)` | escreve `"CONFIG"` (6 B) | **BATE** — o bootloader só confere 5 dos 6 bytes |
| `+0x06` | u32 `codeOffsetInByte`, usado em `f_lseek` | `0x100` = tamanho do cabeçalho | **BATE — e resolve o significado** (§3.1) |
| `+0x10` | não lido no caminho analisado | `fw_size` | fwhelper preenche; bootloader (sdupdate) não usa |
| `+0x14` | não lido no caminho analisado | CRC-16 do payload | idem — ver §3.2 |
| `+0x16` | `memcmp(buf+0x16, "SL6801", 6)` | `strcpy(chip_name)` | **BATE exatamente** |
| `+0xFE/FF` | não lido | `0x55 0xAA` | fwhelper preenche; bootloader não usa |
| Tamanho | — | `0x100` | consistente com `codeOffsetInByte` |

### 3.1 `codeOffsetInByte` resolvido — CONFIRMADO por duas fontes

Na sessão 4 eu havia registrado `codeOffsetInByte` como "existe e é usado
em `f_lseek`, mas o valor correto não é derivável". Agora fecha:

```text
codeOffsetInByte = 0x100 = tamanho do cabeçalho CONFIG

bootloader:  f_lseek(fil, parition_start + codeOffsetInByte)
             = 0xD000 + 0x100
             = 0xD100  (posição NO ARQUIVO)

arquivo:     payload começa em 0x100
             file 0xD100  ->  flash 0xD000  =  tabela de partições  ✓
```

**É o deslocamento que converte offset de flash em offset de arquivo.**
Duas análises independentes — disassembly do bootloader e código do
gerador — chegam ao mesmo valor. Sai de NÃO RESOLVIDO para **CONFIRMADO**.

### 3.2 O CRC do pacote: uma discrepância real

O `fwhelper` grava em `+0x14` o CRC-16 de todo o payload, e o `scan_fw`
verifica esse campo. Mas **no caminho de `sdupdate` que desmontei, esse
campo não é lido antes da gravação**.

Duas explicações possíveis, **nenhuma comprovada**:

1. o campo é consumido pela ferramenta **oficial de gravação por USB**
   (o README do fwhelper diz "official flashing tools", no plural), e não
   pelo caminho de cartão SD;
2. o bootloader verifica em algum trecho fora da função que analisei.

Consequência prática: **não se deve contar com esse CRC como proteção**.
Preencha-o corretamente de qualquer forma.

### 3.3 Uma leitura minha que não fecha — registrada como aberta

No disassembly, após ler `0x80` bytes na posição da tabela de partições,
o bootloader faz `ldr r2, [r5, #0x10]` e usa esse valor em `f_lseek`.
Com o layout confirmado pelo `fwhelper` (entradas começam em `ptable+0x10`,
com o **nome** nos primeiros 4 bytes), esse `+0x10` corresponde ao nome
`"FIRM"` (`0x4D524946`) — que não é um offset válido.

Verifiquei a codificação da instrução (`0x692A` → `LDR r2,[r5,#0x10]`) e
ela está correta. Portanto, ou há uma precondição do caminho que não
estabeleci, ou algum registrador foi mal identificado na minha leitura.

**NÃO RESOLVIDO.** Registro em vez de inventar explicação. Não bloqueia a
construção do pacote, porque o formato autoritativo é conhecido.

---

## 4. Validação cruzada com o nosso dump

Compilei o `fwhelper` e rodei **apenas** o comando `scan` (somente leitura)
contra o firmware original:

```console
$ ./fwhelper GN438_original.bin scan
0x0: HLKJ, base = 0x81fbc0, entry = 0x820001, off = 0x60, size = 0xc8ec
0xd000: partition table (items = 3, ver = 0x0)
partition "FIRM", off = 0xe000, size = 0x192570
0xe000: FIRM, timestamp = 2401300930
partition "TONE", off = 0x1a1000, size = 0x2038
partition "PSMP", off = 0x1fc000, size = 0x4000
```

**Nenhuma mensagem de divergência de checksum.** Uma implementação de
terceiros, escrita sem conhecimento deste projeto, valida os mesmos CRCs
que `tools/validate_firmware.py`. Confirmação independente do trabalho das
sessões 2 e 3.

### Concordâncias adicionais

| Item | Nosso resultado | fwhelper | |
|---|---|---|---|
| CRC | CRC-16/CCITT-FALSE, init `0xFFFF`, poly `0x1021` | idêntico (`0x11021`, init `0xffff`) | ✅ |
| Campo `+0x20` do HLKJ | offset da tabela de partições | `READ32_LE(mem + 0x20)` | ✅ |
| CRC da entrada em `+0x0C` | posição usada | `p + (ver >= 0x30 ? 14 : 12)` → `12` p/ ver 0 | ✅ |
| `PSMP` sem CRC | política `PARTICOES_SEM_CRC` | `if (!memcmp(p,"PSMP",4)) continue;` | ✅ |
| Chip | SL6801 | `ver = 0x0` → `SL6801` | ✅ |

> A política `PARTICOES_SEM_CRC = {b"PSMP"}` que criei na sessão 2 — depois
> do defeito que o teste T2 encontrou — é **exatamente** o que o upstream
> faz. Boa notícia para a correção daquela sessão.

---

## 5. O timestamp decodificado — CONFIRMADO

`fwhelper` imprime o timestamp em decimal, e isso revela o formato:

```text
timestamp = 0x8F20F1C2 = 2401300930
                         │ │ │ │ └─ MM  minuto  30
                         │ │ │ └─── HH  hora    09
                         │ │ └───── DD  dia     30
                         │ └─────── MM  mês     01
                         └───────── YY  ano     24

            ->  2024-01-30 09:30
```

Data plausível de build, e coerente com a versão `yp3_2.0.43`.

**Não é epoch Unix — é um decimal codificado `YYMMDDHHMM`.**

### Por que isso importa mais do que parece

A sessão 4 confirmou que o bootloader **rejeita** (código `0xFC`) um
pacote cujo timestamp seja **igual** ao instalado. Agora sabemos o formato
exato do campo, então sabemos como satisfazer a verificação:

```text
campo em FIRM + 0x04, u32 little-endian
valor decimal YYMMDDHHMM, maior que 2401300930
```

Junto: **o último bloqueio conhecido para montar um pacote aceitável está
tecnicamente resolvido.** Falta apenas o gatilho do `sdupdate`.

---

## 6. Buscas realizadas

Todas em 2026-09-12.

| # | Consulta / alvo | Resultado |
|---|---|---|
| 1 | `"update.up" firmware YP3 SL6801 MP3 player Smartlink` | apenas `smartlink_flash`; nenhum pacote |
| 2 | `Jointbees MP3 yp3 firmware update Shenzhen Shenju SL6801 SL6806` | nenhum pacote |
| 3 | `github SL6801 yp3 firmware update.up ... 云P3` (restrito a github/gitlab/gitee) | apenas `smartlink_flash` |
| 4 | `MP3 player SD card firmware update "update.up" copy to card root` | procedimentos genéricos de outras marcas |
| 5 | `"6801_intel_flash.bin" OR "SL6801" official flash tool download` | poluída por "Intel"; nada |
| 6 | `mechen.com.cn/firmwareupgrade` e `/M30` | páginas renderizadas por JS; sem links legíveis |
| 7 | Issues e PRs de `ilyakurdyukov/smartlink_flash` | **valiosas** — ver §7 |

### Conclusão da busca

Não há, publicamente indexado, nenhum `update.up` desta família. O
ecossistema YP3/SL6801 é pequeno: essencialmente um único repositório e
uma discussão com três ou quatro participantes.

Caminhos ainda não esgotados, se um binário real for necessário no futuro:

- fóruns chineses (Baidu Tieba, 52pojie) com o termo `云P3`;
- solicitar diretamente ao fabricante (um usuário tentou; sem resposta
  registrada);
- comprar um aparelho da família que venha com atualização oficial
  publicada.

---

## 7. Inteligência da comunidade — e dois avisos sérios

Da issue #3 do repositório upstream, com respostas do próprio autor da
ferramenta. **Isto altera a avaliação de risco do projeto.**

### Aviso 1 — a flash não se comporta como flash normal

> *ilyakurdyukov:* "The on-chip flash is acting strange, it can't clear
> bits one by one. It's probably not SLC flash."
>
> "All is fine with 1 → 0, but flash can somehow restore 0 → 1 with **90 %
> efficiency** without erasing."

Escrever `1` sobre `0` **não deveria funcionar** sem apagar antes, e aqui
funciona — de forma aparentemente **aleatória**, em cerca de 90 % dos
casos. Isso significa que uma gravação pode deixar bits incorretos de
maneira não determinística.

**Implicação direta:** qualquer gravação precisa ser **verificada por
releitura**. Felizmente o `sdupdate` já faz exatamente isso (o CRC
arquivo × releitura descrito em `SDUPDATE_ANALYSIS.md` §7) — o que agora
parece ser uma resposta deliberada a essa característica do silício.

### Aviso 2 — brick além do bootloader é documentado

> *ilyakurdyukov:* "There are cases where devices no longer boot, **even in
> bootloader mode**, if you erase the entire flash or if there's invalid
> content. I don't know how unbreakable these chips are."

**Isto qualifica a conclusão da sessão 4.** Eu havia registrado que o
`sdupdate` nunca toca em `0x0`–`0xD000` e que, portanto, o bootloader
sobrevive a uma atualização falha. Isso continua verdadeiro **para o
caminho do cartão SD**. Mas gravação por **USB** pode atingir o
bootloader, e há casos relatados de aparelhos que não voltam nem em modo
bootloader.

Ajuste da avaliação de risco:

| Caminho | Risco | Observação |
|---|---|---|
| `sdupdate` (cartão) | **menor** | bootloader não é tocado |
| `write_flash` por USB | **alto** | brick irrecuperável documentado |

### Estado da arte da comunidade

- O autor da ferramenta **nunca modificou** um firmware:
  "No, I haven't tried changing the firmware."
- Ele testou escrita apenas em 64 KB de espaço livre no fim da flash, só
  em SL6801.
- Outro usuário (`altoensodio`) tenta CFW para SL6801; sem resultado
  publicado.
- Um usuário (`Dogolitesnap`, issue #4) gravou **sem ter feito dump antes**
  e ficou sem firmware; pedido sem resposta.
- Porte do Rockbox foi considerado inviável sem SDK vazado.

> ⚠️ **CORRIGIDO em 2026-09-12.** A versão original desta seção afirmava
> que ninguém havia gravado firmware modificado com sucesso. **Está
> errado.** Lendo os 25 comentários da issue #3 (eu havia lido só os
> primeiros), aparece um precedente confirmado pelo próprio autor da
> ferramenta: o desenvolvedor **bunkaich** corrigiu o Bluetooth e
> **remapeou os botões** de um aparelho desta família. Detalhes e citações
> em **`docs/EXTERNAL_RESEARCH.md` §5.1**.
>
> O que continua verdadeiro: **não existe rede de segurança pública** —
> nenhum guia, nenhum procedimento de recuperação testado, e o patch do
> bunkaich não foi publicado como código.
>
> O `GN438_original.bin` deste projeto — verificado, com round-trip
> byte-a-byte provado — vale mais do que parece: é a única garantia de
> recuperação que existe.

---

## 8. Como seria o pacote do nosso aparelho

Calculado analiticamente a partir do formato. **Nenhum arquivo foi
criado** — conforme instruído.

```text
fw_size          = 0x1A3038   (1.716.280 bytes)
                   = fim da TONE; PSMP excluída
crc16(payload)   = 0x77F5
chip_name        = "SL6801"   (ver = 0x0 < 0x30)
tamanho total    = 0x100 + 0x1A3038 = 1.716.536 bytes

cabeçalho CONFIG:
  +0x00  "CONFIG"
  +0x06  0x00000100
  +0x10  0x001A3038
  +0x14  0x77F5
  +0x16  "SL6801"
  +0xFE  0x55
  +0xFF  0xAA
```

**Atenção:** um pacote gerado a partir do dump original **sem alterar o
timestamp** seria rejeitado pelo bootloader com código `0xFC`, porque o
timestamp seria idêntico ao instalado (`SDUPDATE_ANALYSIS.md` §6). Isto
é uma limitação real de `dump2fw` para regravar um dump inalterado —
não um defeito do nosso entendimento.

---

## 9. Lacunas resolvidas e remanescentes

### Resolvidas nesta sessão

| Lacuna | Antes | Agora |
|---|---|---|
| Bytes `0x0A`–`0x15` e `0x1C`+ do cabeçalho | NÃO RESOLVIDO | **CONFIRMADO** — zeros, salvo `fw_size`, CRC e `0x55AA` |
| `codeOffsetInByte` | valor não derivável | **CONFIRMADO** = `0x100` |
| Semântica do timestamp | desconhecida | **CONFIRMADO** — decimal `YYMMDDHHMM` |
| Versão da tabela de partições | registrada como zero | **CONFIRMADO** — campo de versão; `≥0x30` ⇒ SL6806 |
| Polinômio do CRC do updater | PROVÁVEL | **CONFIRMADO** por implementação independente |

### Remanescentes

| # | Lacuna | Impacto |
|---|---|---|
| 1 | **Como o `sdupdate` é disparado** | **ALTO** — único bloqueio real restante |
| 2 | O `+0x14` (CRC do pacote) é verificado por quem? | médio |
| 3 | O `ldr r2,[r5,#0x10]` que não fecha (§3.3) | médio |
| 4 | Confiabilidade da gravação, dada a anomalia 0→1 | **ALTO** — risco, não desconhecimento |
| 5 | Serigrafia → `key_id` | ALTO, mas independente disto |

---

## 10. Recomendação

O formato do `update.up` está **suficientemente comprovado** para montar
um pacote. O que ainda **não** está resolvido é o **gatilho** e o
**risco de gravação**.

Ordem sugerida, do mais seguro para o menos:

1. **Fase 1 sem gravação** — trocar ícone / logo / papel de parede na
   imagem, reconstruir, validar com `validate_firmware.py` **e** com o
   `fwhelper scan` de terceiros. Prova o pipeline inteiro sem tocar no
   aparelho.
2. Determinar o gatilho do `sdupdate` (análise estática, sem risco).
3. Capturar a UART de depuração — resolve o mapeamento de botões **e**
   permite observar o `sdupdate` em execução.
4. Só então considerar uma gravação real, e **pelo cartão SD**, nunca por
   USB.

> Enquanto o item 2 não estiver resolvido, não há como gravar mesmo que o
> pacote esteja perfeito. Não há pressa.

---
# PARTE II — Especificação reproduzível do `update.up`

Análise de `fwhelper/main.c` (commit `49d51d17`, SHA-256 do arquivo
`a66ed2dc…a300b`, verificado contra `tools/external/smartlink_flash.lock`)
confrontada instrução a instrução com `docs/SDUPDATE_ANALYSIS.md`.

> **Nenhum arquivo `update.up` foi criado.** Todos os valores desta parte
> foram calculados **em memória**. Nenhuma operação em hardware.

---

## 11. Estrutura completa — CONFIRMADO

```text
update.up
├── 0x00000000  cabeçalho CONFIG          0x100 bytes
└── 0x00000100  payload                   fw_size bytes
                └── cópia literal de flash[0 .. fw_size]
                    ├── 0x000000  cabeçalho HLKJ + bootloader
                    ├── 0x00D000  tabela de partições
                    ├── 0x00E000  FIRM
                    └── 0x1A1000  TONE
                    (PSMP fica de fora — ver §11.2)

tamanho total = 0x100 + fw_size
```

### 11.1 Cálculo de `fw_size` — CONFIRMADO

```c
for (i = 0; i < n; i++) {
    p += 16;
    if (!memcmp(p, "PSMP", 4)) continue;
    off = READ32_LE(p + 4);
    len = READ32_LE(p + 8);
    len += off;
    if (fw_size < len) fw_size = len;
}
```

`fw_size` = **maior `offset + tamanho`** entre as partições, **excluindo
`PSMP`**. Para o nosso aparelho:

| Partição | off | len | off+len |
|---|---|---|---|
| FIRM | `0x00E000` | `0x192570` | `0x1A0570` |
| TONE | `0x1A1000` | `0x002038` | **`0x1A3038`** ← máximo |
| PSMP | `0x1FC000` | `0x004000` | *excluída* |

**`fw_size = 0x1A3038`** (1.716.280 bytes) · pacote = **1.716.536 bytes**.

### 11.2 Por que `PSMP` fica de fora — PROVÁVEL

`PSMP` é a área de configuração persistente (`FIRMWARE_MAP.md` §7).
Excluí-la significa que **a atualização não apaga as preferências do
usuário**. Coerente com o campo de CRC zerado dessa partição e com a
política `fw_common.PARTICOES_SEM_CRC`.

---

## 12. Todos os campos do cabeçalho — CONFIRMADO

Bytes reais calculados para o nosso firmware:

```text
0000: 43 4F 4E 46 49 47 00 01 00 00 00 00 00 00 00 00  |CONFIG..........|
0010: 38 30 1A 00 F5 77 53 4C 36 38 30 31 00 00 00 00  |80...wSL6801....|
...   (zeros)
00F0: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 55 AA  |..............U.|
```

| Offset | Tam. | Campo | Valor | Escrito por | Lido pelo boot | Status |
|---|---|---|---|---|---|---|
| `0x00` | 6 | magic | `"CONFIG"` | `memcpy` | **sim** — só 5 bytes | CONFIRMADO |
| `0x06` | 4 | `codeOffsetInByte` | `0x00000100` | `WRITE32_LE` | **sim** | CONFIRMADO |
| `0x0A` | 6 | — | zeros | `memset` | não | CONFIRMADO |
| `0x10` | 4 | `fw_size` | `0x001A3038` | `WRITE32_LE` | **não** | CONFIRMADO |
| `0x14` | 2 | CRC-16 do payload | `0x77F5` | `WRITE16_LE` | **não** | CONFIRMADO |
| `0x16` | ≤10 | nome do chip | `"SL6801\0"` | `strcpy` | **sim** — 6 bytes | CONFIRMADO |
| `0x20`–`0xFD` | — | — | zeros | `memset` | não | CONFIRMADO |
| `0xFE` | 1 | assinatura | `0x55` | direto | **não** | CONFIRMADO |
| `0xFF` | 1 | assinatura | `0xAA` | direto | **não** | CONFIRMADO |

### 12.1 Confronto campo a campo com o disassembly

| Offset | Bootloader (`SDUPDATE_ANALYSIS.md`) | fwhelper | Veredito |
|---|---|---|---|
| `0x00` | `memcmp(buf, "CONFIG", 5)` — **5** bytes | escreve 6 | **BATE**; o 6º byte (`G`) não é verificado |
| `0x06` | `ldr.w sb,[r5,#6]` — u32 desalinhado | `0x100` | **BATE** |
| `0x10` | não lido | `fw_size` | fwhelper preenche; sdupdate ignora |
| `0x14` | não lido | CRC payload | fwhelper preenche; sdupdate ignora |
| `0x16` | `memcmp(buf+0x16, "SL6801", 6)` | `strcpy` | **BATE exatamente** |
| `0xFE/FF` | não lido | `0x55 0xAA` | fwhelper preenche; sdupdate ignora |

> Três campos que o `fwhelper` escreve **não são lidos** pelo caminho do
> cartão SD. **PROVÁVEL:** são consumidos pela ferramenta oficial de
> gravação por USB — o README do `fwhelper` diz "official flashing
> tool**s**", no plural. **NÃO CONFIRMADO.**

### 12.2 `codeOffsetInByte` — CONFIRMADO por duas fontes independentes

```text
fwhelper:    WRITE32_LE(buf + 6, 0x100)        <- tamanho do cabeçalho
bootloader:  f_lseek(fil, parition_start + codeOffsetInByte)
             = 0xD000 + 0x100 = 0xD100

no arquivo o payload começa em 0x100, logo:
             file[0xD100] = flash[0xD000] = tabela de partições  ✓
```

**`codeOffsetInByte` é o deslocamento que converte offset de flash em
offset dentro do arquivo.** Numericamente verificado.

### 12.3 ⚠️ `fileStamp`: o ponto que não fecha — NÃO RESOLVIDO

**`fwhelper` não gera `fileStamp`.** Ele não existe no cabeçalho CONFIG:
está **dentro do payload**, em `FIRM + 0x04`, e `dump2fw` copia a imagem
literalmente. Portanto o timestamp de um pacote é o que já estava no dump.

O bootloader, porém, faz:

```asm
00827934  ldr r2, [r5, #0x10]   ; buf[0x10] do bloco lido na ptable
0082793C  blx r1                ; f_lseek(fil, r2)
0082794A  blx r6                ; f_read(fil, buf, 0x80)
0082794E  ldr r6, [r5, #4]      ; fileStamp = buf[4]
00827956  bl  flash_read(&A,   parition_start + 0x10, 4)
00827962  bl  flash_read(&len, parition_start + 0x18, 4)
0082796E  bl  flash_read(&cur, A + 4, 4)
00827986  cmp r3, r6            ; cur == fileStamp ?
00827988  beq -> 0xFC           ; iguais: ABORTA
```

Conteúdo real da tabela de partições lida:

| buf+ | valor | interpretação |
|---|---|---|
| `0x10` | `0x4D524946` = `"FIRM"` | **usado como offset de seek** |
| `0x18` | `0x00192570` | tamanho da FIRM — **bate** com `firmwareStartLen` |

Duas leituras possíveis, **nenhuma fecha os dois campos**:

| Leitura | `+0x10` | `+0x18` |
|---|---|---|
| **A** — entradas em `ptable+0x10` (layout real, confirmado pelo fwhelper) | `"FIRM"` — não é offset ✗ | tamanho ✓ |
| **B** — se o boot assumisse entradas em `ptable+0x0C` | `0xE000`, e `+4` = timestamp ✓ | seria o CRC ✗ |

**Consequência, sob a leitura A:**

```text
A = 0x4D524946  ->  flash_read(0x4D52494A)  : fora da faixa de 2 MiB
f_lseek(0x4D524946)  ->  além do fim do arquivo
2º f_read retorna 0 bytes; buf permanece com a ptable
fileStamp = buf[4] = 0x00000003  (a contagem de partições)

Os DOIS lados da comparação seriam valores espúrios.
```

**HIPÓTESE:** nesse cenário a igualdade quase nunca ocorre e a verificação
de timestamp **sempre passa** — ou seja, o retorno `0xFC` talvez nunca
dispare neste aparelho.

**O que continua CONFIRMADO:** a estrutura do desvio (`beq` → `0xFC`).
**O que é NÃO RESOLVIDO:** se ele chega a disparar, e sobre quais valores.

> **Isto é o item nº 1 a resolver antes de qualquer gravação.** Não porque
> impeça o pacote, mas porque significa que **não sabemos prever a decisão
> do bootloader**. Uma verificação que opera sobre lixo pode tanto aceitar
> um pacote ruim quanto recusar um bom.

---

## 13. CRCs: quais, sobre o quê — CONFIRMADO

Algoritmo único em todo o sistema: **CRC-16/CCITT-FALSE**
(`poly=0x1021`, `init=0xFFFF`, sem reflexão, `xorout=0`).

Implementação do `fwhelper` (forma tabelada de `0x11021`) verificada
equivalente à nossa `fw_common.crc16`.

| # | CRC | Região coberta | Onde fica | Quem escreve | Quem verifica |
|---|---|---|---|---|---|
| 1 | headerCrc | `flash[0x00:0x5C]` | HLKJ `+0x5C` | nosso rebuild | boot (não observado no sdupdate) |
| 2 | loadCrc boot | `flash[0x60 : 0x60+0xC8EC]` | HLKJ `+0x14` | nosso rebuild | `scan_fw` |
| 3 | loadCrc FIRM | `FIRM[0x30 : 0x1030]` | FIRM `+0x1C` | nosso rebuild | boot |
| 4 | CRC FIRM | `flash[0xE000 : 0x1A0570]` | ptable `+0x0C` | nosso rebuild | `dump2fw` **aborta** se errado |
| 5 | CRC TONE | `flash[0x1A1000 : 0x1A3038]` | ptable `+0x0C` | nosso rebuild | `dump2fw` **aborta** se errado |
| 6 | CRC PSMP | — | zerado | — | **ninguém** |
| 7 | **CRC do payload** | `flash[0 : fw_size]` | **CONFIG `+0x14`** | `dump2fw` | `scan_fw`; sdupdate **não** |
| 8 | verificação de escrita | arquivo × releitura da flash | — | — | sdupdate, **pós-gravação** |

> O CRC **nº 7** é novo para nós — é o único que o `fwhelper` calcula e que
> não existe na imagem de flash. Os 1–6 já são produzidos corretamente por
> `tools/rebuild_firmware.py`.

### Posição do CRC de partição depende da versão — CONFIRMADO

```c
chk2 = READ16_LE(p + (ver >= 0x30 ? 14 : 12));
```

`ver` = terceiro word do cabeçalho da ptable (`ptable+0x08`).
Nosso `ver = 0` ⇒ CRC em `+0x0C`, e `chip_name = "SL6801"`.

---

## 14. Como o `fwhelper` constrói o pacote — CONFIRMADO

Sequência exata de `dump2fw()`:

```text
1. exige flash[0:4] == "HLKJ", senão aborta
2. off = READ32_LE(flash + 0x20)              -> tabela de partições
3. exige pelo menos 0x100 bytes a partir de off
4. n = ptable[0]; ver = ptable[8]; exige n <= 15
5. para cada partição:
      pula PSMP
      VERIFICA o CRC; diverge -> ABORTA (não recalcula)
      fw_size = max(fw_size, off + len)
6. ver >= 0x30 -> chip "SL6806", senão "SL6801"
7. fw_size == 0 -> aborta
8. monta o cabeçalho de 0x100 bytes (§12)
9. grava cabeçalho, depois flash[0 : fw_size]
```

**Detalhe importante:** o passo 5 **verifica e aborta**, nunca corrige.
`dump2fw` só aceita uma imagem já íntegra. Ou seja:

```text
  editar a imagem  ->  tools/rebuild_firmware.py  (corrige CRCs 1–6)
                   ->  fwhelper dump2fw           (valida e empacota)
```

O nosso rebuilder é **pré-requisito** do `dump2fw`, não alternativa.

---

## 15. Podemos gerar um pacote a partir do nosso rebuild?

### Estruturalmente: **SIM** — CONFIRMADO

`GN438_rebuilt_original.bin` é byte-idêntico ao original e passa em todas
as verificações de `dump2fw`, comprovado pela réplica em memória:

```text
[1] HLKJ ok · ptable off = 0xD000
[2] n = 3  ver = 0x0  -> SL6801
    FIRM off=0x00E000 len=0x192570 crc=0x49a6 vs 0x49a6 OK
    TONE off=0x1A1000 len=0x002038 crc=0x9177 vs 0x9177 OK
    PSMP -> continue
[3] fw_size = 0x1A3038
[4] crc16(payload) = 0x77F5
```

### Seria aceito pelo aparelho: **NÃO RESOLVIDO**

Três incógnitas, nenhuma delas do formato:

| # | Incógnita | Status |
|---|---|---|
| 1 | Como o `sdupdate` é disparado | **NÃO RESOLVIDO** |
| 2 | Se a verificação de timestamp dispara (§12.3) | **NÃO RESOLVIDO** |
| 3 | Confiabilidade da gravação (flash anômala) | **RISCO conhecido** |

### Se optarmos por trocar o timestamp

Campo `FIRM + 0x04`, u32 LE, decimal `YYMMDDHHMM`. Exemplo calculado para
`2609121200` (2026-09-12 12:00):

| Campo | Antes | Depois |
|---|---|---|
| timestamp (`0x00E004`) | `2401300930` | `2609121200` |
| CRC FIRM (`0x00D01C`) | `0x49A6` | `0x38EA` |
| CRC payload (CONFIG `+0x14`) | `0x77F5` | `0x9775` |
| loadCrc FIRM (`0x00E01C`) | `0x68E1` | **inalterado** |
| headerCrc (`0x00005C`) | `0x34DB` | **inalterado** |

Os dois últimos não mudam porque o timestamp está no **cabeçalho** da
partição, fora dos 4 KiB cobertos por `loadCrc` e fora do cabeçalho HLKJ.

**Apenas 3 campos.** `tools/rebuild_firmware.py` já cuida dos dois
primeiros; o terceiro é do `dump2fw`.

---

## 16. Classificação das conclusões

| # | Conclusão | Classificação |
|---|---|---|
| 1 | Pacote = cabeçalho `0x100` + `flash[0:fw_size]` | **CONFIRMADO** |
| 2 | Magic `"CONFIG"`, verificado em 5 bytes | **CONFIRMADO** |
| 3 | `codeOffsetInByte` = `0x100` = deslocamento flash→arquivo | **CONFIRMADO** (2 fontes) |
| 4 | `fw_size` exclui `PSMP` | **CONFIRMADO** |
| 5 | `PSMP` excluída para preservar configurações | **PROVÁVEL** |
| 6 | Marca do chip em `+0x16`, de `ver` da ptable | **CONFIRMADO** |
| 7 | CRC-16/CCITT-FALSE em todos os campos | **CONFIRMADO** |
| 8 | CRC do payload em `+0x14` cobre `flash[0:fw_size]` | **CONFIRMADO** |
| 9 | `dump2fw` valida e aborta, nunca corrige CRCs | **CONFIRMADO** |
| 10 | `fileStamp` não é gerado pelo fwhelper; vem do payload | **CONFIRMADO** |
| 11 | Timestamp é decimal `YYMMDDHHMM` | **CONFIRMADO** |
| 12 | `+0x10`, `+0x14`, `+0xFE/FF` são para a ferramenta USB | **PROVÁVEL** |
| 13 | Nosso rebuild produz um pacote estruturalmente válido | **CONFIRMADO** |
| 14 | O que o bootloader compara na verificação de timestamp | **NÃO RESOLVIDO** |
| 15 | Se o retorno `0xFC` chega a disparar | **NÃO RESOLVIDO** |
| 16 | A verificação de timestamp sempre passa (lixo × lixo) | **HIPÓTESE** |
| 17 | Como o `sdupdate` é disparado | **NÃO RESOLVIDO** |

---

## 17. Especificação reproduzível — resumo operacional

```text
PARA PRODUZIR UM update.up (quando autorizado):

 1. partir de firmware/ORIGINAL/GN438_original.bin  (nunca editá-lo)
 2. editar a cópia de trabalho
 3. se alterar o timestamp: FIRM+0x04, decimal YYMMDDHHMM
 4. tools/rebuild_firmware.py  -> corrige headerCrc, loadCrc boot,
                                  loadCrc FIRM, CRC FIRM, CRC TONE
 5. tools/validate_firmware.py -> 26 verificações
 6. fwhelper <img> scan        -> confirmação independente
 7. fwhelper <img> dump2fw     -> gera o pacote
 8. fwhelper <pacote> scan     -> valida o pacote pronto

PRÉ-REQUISITOS AINDA NÃO ATENDIDOS:
 · como disparar o sdupdate                    NÃO RESOLVIDO
 · previsibilidade da verificação de timestamp NÃO RESOLVIDO
 · gravação não determinística (0→1)           RISCO
```

> **Enquanto os dois primeiros não forem resolvidos, gerar o pacote não
> traz benefício e não deve ser feito.** A especificação está pronta; a
> autorização para usá-la, não.


---

## 18. Referências cruzadas

| Assunto | Documento |
|---|---|
| Disassembly do `sdupdate` | `docs/SDUPDATE_ANALYSIS.md` |
| Round-trip do rebuild | `docs/REBUILD_VALIDATION.md` |
| Layout da flash | `docs/FIRMWARE_MAP.md` |
| Obtenção do firmware | `docs/FIRMWARE_DUMP.md` |
| Versão travada da ferramenta | `tools/external/smartlink_flash.lock` |

**Fontes externas:**

- [ilyakurdyukov/smartlink_flash](https://github.com/ilyakurdyukov/smartlink_flash) — ferramenta, `fwhelper` e discussões

**Dossiê completo da pesquisa externa:** `docs/EXTERNAL_RESEARCH.md`
