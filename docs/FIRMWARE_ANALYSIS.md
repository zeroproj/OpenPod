# OpenPod — FIRMWARE_ANALYSIS

Análise forense inicial de `GN438_original.bin` (Iigenai GN-438, yp3_2.0.43).

| | |
|---|---|
| Arquivo | `firmware/ORIGINAL/GN438_original.bin` |
| Tamanho | 2.097.152 bytes (2 MiB) |
| SHA-256 | `b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f` — **confere** |
| Cópia de trabalho | `firmware/WORKING/GN438_analysis.bin` (hash idêntico) |
| Data da análise | 2026-09-11 |
| Escopo | somente leitura; nenhuma operação em hardware |

### Convenção de confiança

- **CONFIRMADO** — evidência direta e verificável no binário.
- **PROVÁVEL** — vários indícios convergentes, sem prova direta.
- **HIPÓTESE** — ainda precisa ser comprovado.
- **NÃO IDENTIFICADO** — investigado e não resolvido.

---

## Respostas às 23 perguntas

### 1. Qual é a CPU?

**ARM Cortex-M com unidade de ponto flutuante (FPU).** — CONFIRMADO quanto
à família; o núcleo exato (M4F / M7 / M33) é **NÃO IDENTIFICADO**.

Evidências:
- Tabela de vetores no estilo Cortex-M: em `0x00000060` o primeiro word é
  `0x0083BE90` (ponteiro de pilha inicial) e o segundo é `0x00820001`
  (reset handler com bit Thumb ligado), exatamente igual ao campo
  `runFromRam` do cabeçalho.
- Instruções VFP densas em `0x00E030`–`0x018A90`: prefixos `0xEC`, `0xED`,
  `0xEE` (`vldr`, `vstr`, operações de coprocessador).
- Instruções Thumb-2 de 32 bits: `4F F0 FF 30` (`mov.w`), `DF E8 00 F0`
  (`tbb`) — ambas exclusivas de ARMv7-M ou superior. Descartam Cortex-M0/M0+.

A string `SL6801` aparece em `0x0000C184`, dentro do bootloader, junto de
`CONFIG`. É um **indício forte** do SoC, mas uma string não prova o
silício — pode ser um identificador de build ou de compatibilidade.
Classificação: **PROVÁVEL**. O `CLAUDE.md` pede explicitamente que isso
não seja assumido, e não está sendo.

### 2. Qual é a arquitetura?

**ARMv7-M, conjunto de instruções Thumb-2.** — CONFIRMADO
(ver evidências da pergunta 1).

### 3. Qual é o endianness?

**Little-endian.** — CONFIRMADO. Todos os campos de cabeçalho, ponteiros e
tabelas decodificam de forma coerente em LE, e os CRCs conferem sob essa
interpretação. Em big-endian nada fecha.

### 4. Qual é o tamanho da flash?

**2 MiB (2.097.152 bytes).** — CONFIRMADO pelo dump, pela tabela de
partições (que termina exatamente em `0x00200000`) e pelo `README.txt` do
dump original.

Ocupação real: **1.732.664 bytes usados (82,6 %)**, **364.488 bytes
livres (17,4 %)** apagados com `0xFF` entre `0x001A3038` e `0x001FBFFF`.

### 5. Como o firmware está organizado?

```text
0x000000  cabeçalho HLKJ (0x60 B)
0x000060  bootloader Thumb-2, 51.436 B, CRC16 0x759D
0x00D000  tabela de partições (3 entradas)
0x00E000  FIRM — aplicação, 1.647.984 B, CRC16 0x49A6
0x1A1000  TONE — 8.248 B, CRC16 0x9177
0x1FC000  PSMP — 16.384 B, sem CRC
```

Detalhamento completo em `docs/FIRMWARE_MAP.md`.

**Mecanismo de boot — CONFIRMADO.** O bootloader copia apenas os primeiros
**4 KiB** da FIRM para a RAM em `0x00804C00` e salta para `0x00804C01`.
O restante (~1,6 MB) executa em **XIP** a partir da flash mapeada em
`0x00C00000`.

### 6. Existem partições?

**Sim, três, confirmadas por tabela explícita em `0x0000D000`.** —
CONFIRMADO.

| Nome | Offset | Tamanho | CRC16 gravado | CRC16 calculado |
|---|---|---|---|---|
| `FIRM` | 0x0000E000 | 1.647.984 B | 0x49A6 | **0x49A6 OK** |
| `TONE` | 0x001A1000 | 8.248 B | 0x9177 | **0x9177 OK** |
| `PSMP` | 0x001FC000 | 16.384 B | 0x0000 | não verificada |

O `CLAUDE.md` citava `FIRM / PICS / FONT / TONE / PSMP` como nomes de
*outros* aparelhos. Neste dispositivo existem **apenas FIRM, TONE e PSMP**.
Não há partição `PICS` nem `FONT` — as fontes e imagens vivem **dentro**
da FIRM.

### 7. Onde está o código?

- Bootloader: `0x000060`–`0x00C94C` — CONFIRMADO.
- FIRM, estágio em RAM: `0x00E030`–`0x00F030` — CONFIRMADO.
- FIRM, código XIP: principalmente `0x0F4000`–`0x1A0570` (maior densidade
  de prólogos/epílogos Thumb do dump: 2.395 `push {…,lr}` e 875 `bx lr`)
  e `0x039470`–`0x05E000` — PROVÁVEL.

### 8. Onde estão os dados?

- Strings de UI (8 idiomas): `0x053000`–`0x05E000` — CONFIRMADO.
- Mensagens de debug: `0x04A000`–`0x053000` e `0x0D9000`–`0x0E5000`.
- Recursos gráficos: `0x05E7E0`–`0x0D3000` — CONFIRMADO.
- Lacuna interna de 128 KiB zerada em `0x019000`–`0x03946F`: propósito
  **NÃO IDENTIFICADO**.

### 9. Onde estão os gráficos?

CONFIRMADO. Duas categorias:

**Ícones (fontes de símbolo, 4 bpp com alfa):**
- `icons_main`: 675 ícones. Tabela `0x0BE720`, blob `0x0B0DC4`, cmap `0x0C1150` (U+F000…).
- `icons_small`: 24 ícones. Tabela `0x0A6568`, blob `0x0A5F71`.

**Imagens (`lv_img_dsc_t`), 8 no total:**
- 5 × `TRUE_COLOR_CHROMA` (RGB565): quatro 50×50 e uma 16×16.
- 3 × `INDEXED_8` (paleta BGRA de 256 entradas): 128×160 papel de parede,
  128×35 logotipo GENAI, 128×160 folha de ícones do menu principal.

**699 arquivos PNG extraídos** para `extracted/`.

### 10. Onde estão as fontes?

CONFIRMADO e totalmente decodificado.

| Bloco | Faixa |
|---|---|
| Blob de bitmaps | `0x05E7E0` – `0x086C32` (164.946 B) |
| Tabela de glifos | `0x086C44` – `0x0A27E4` (7.098 × 16 B) |
| cmap | `0x0A27E6` – `0x0A5F70` |

Formato `lv_font_fmt_txt` (LVGL v8, `LV_FONT_FMT_TXT_LARGE = 1`),
**1 bpp**, altura **12 px**, 95 glifos ASCII (8 px de largura) e 6.763
glifos CJK (16 px). Validado por renderização de `A`, `a`, `g`, `p`, `5`
e `中`.

### 11. Onde estão os textos?

`0x053000`–`0x05E000` — CONFIRMADO. Oito idiomas: Deutsch, English,
Español, Français, Italiano, Nederlands, **Português**, 中文.

### 12. Como a GUI funciona?

**LVGL v8** sobre display **128×160 RGB565**, controlador **GC9106**.
Interface organizada em **61 páginas numeradas** (`page1`–`page84`) com
padrão MVP. Detalhes completos em `docs/GUI_ANALYSIS.md`.

### 13. Como os botões funcionam?

Parcialmente mapeado. Entrada via `/dev/key_onoff`, `/dev/key_io` e seis
canais `/dev/kadc_ch0-5` (teclas por ADC). Apenas **onoff, volume_up e
volume_down** têm tratamento nomeado; os botões M, ◀◀, ▶▶ e ▶Ⅱ
**não foram localizados**. Há suporte confirmado a *short press*,
*long press* e auto-repetição. Detalhes e lacunas em
`docs/BUTTON_ANALYSIS.md`.

### 14. Qual filesystem é utilizado?

**FatFs** sobre cartão microSD, com **FAT32 e exFAT** — CONFIRMADO
(`f_mount`, `f_open`, `f_findnext`, `create_fatfs_stream`, strings
literais `FAT32   ` e `EXFAT   `).

A **flash interna não usa filesystem**: é dividida pela tabela de
partições em `0x0000D000` e os recursos são endereçados por offset
absoluto. Isto responde à distinção pedida no `CLAUDE.md` entre
*firmware filesystem* e *microSD filesystem* — só o segundo existe.

Há também uma string `r://60`, indicando um driver `lv_fs` registrado com
a letra `r` que resolve recursos por ID numérico. Mecanismo
**NÃO IDENTIFICADO** (ocorrência única).

### 15. Quais codecs existem?

CONFIRMADO por strings:

| Domínio | Evidência |
|---|---|
| **JPEG** | `JpegDecInit`, `JpegDecDecoder`, `JpegDecRelease`, `Start Of Frame 0x%02x: width=%u, height=%u`, `Bogus JPEG colorspace`, `Wrong JPEG library version` — derivado de **libjpeg** |
| **BMP** | `BmpDecDecoder` |
| **AVI** | `avi_init`, `avi_head`, `read avi buffer failed`, `avi channel is not 2!` |
| **WAV / PCM / ADPCM** | `wav save to pcm`, `wav save to adpcm, bytes_per_sec: %d` (gravação) |
| **FLAC** | extensão `.flac` reconhecida |
| **MP3** | assinaturas `ID3` na partição TONE |

Nomes de decodificadores MP3/WMA/AAC **não aparecem** nas strings —
provavelmente estão em blobs sem mensagens de debug. **NÃO CONFIRMADO.**

### 16. Como Bluetooth funciona?

CONFIRMADO quanto aos perfis, **NÃO IDENTIFICADO** quanto ao stack.

Perfis e camadas presentes: **A2DP source e sink** (`a2dp src open`,
`a2dp snk open`), **AVRCP** (`avrcp btn 0x%x`), **HFP** (`hf_open`,
`hf codec 0x%x`), **L2CAP**, **RFCOMM**, pareamento (`dev_pairing`).

A2DP em *source* **e** *sink* significa que o aparelho pode tanto enviar
áudio para um fone quanto receber de um telefone.

Não há strings de BTstack, Zephyr ou BlueZ — provavelmente stack
proprietário do SoC. A UI correspondente é `page35`
(`_paired_list_process`, `_search_list_process`, `_show_bt_option`).

### 17. Como FM funciona?

Parcialmente. Existe `/dev/fm` e `fm_init`, além de
`pstr_fm_preset_init` (persistência de estações pré-sintonizadas).
O **chip sintonizador não foi identificado**. NÃO IDENTIFICADO.

### 18. Como vídeo funciona?

Contêiner **AVI** com quadros decodificados pelo decodificador **JPEG**
(ou seja, **MJPEG**) — PROVÁVEL, baseado na coexistência de `avi_init`
com `JpegDecDecoder` e na ausência de qualquer string de H.264/MPEG-4.
A UI é `page20` (`_show_video`, `_video_process`, `_deinit`).
A string `-avi channel is not 2!` sugere exigência de áudio estéreo.

### 19. Como o firmware verifica integridade?

**CONFIRMADO — esta é a descoberta mais importante para o projeto.**

Algoritmo: **CRC-16/CCITT-FALSE**

```text
polinômio : 0x1021
init      : 0xFFFF
refin     : não
refout    : não
xorout    : 0x0000
```

Descoberto por força bruta sobre sete variantes de CRC-16 e validado
independentemente em **quatro** regiões distintas:

| Região | Intervalo | CRC gravado | Calculado |
|---|---|---|---|
| Payload do bootloader | `0x000060`–`0x00C94C` | 0x759D | **0x759D** |
| Estágio RAM da FIRM | `0x00E030`–`0x00F030` | 0x68E1 | **0x68E1** |
| Partição FIRM | `0x00E000`–`0x1A0570` | 0x49A6 | **0x49A6** |
| Partição TONE | `0x1A1000`–`0x1A3038` | 0x9177 | **0x9177** |

Os nomes dos campos de cabeçalho **não foram inferidos**: o próprio
bootloader os imprime, em `0x0000A061`:

```text
boot--->firmware_header_len 0x%x;timestamp 0x%x;loadToRam 0x%x;
        runFromRam 0x%x;loadLength 0x%x;loadCrc 0x%x
```

Não há evidência de assinatura criptográfica, AES, DES ou XOR de
ofuscação. A entropia global é **5,94 bits/byte** e nenhuma região passa
de ~7,0 — compatível com código ARM compilado, **não** com dados cifrados
ou comprimidos. **O firmware está em claro.**

### 20. Como podemos reconstruí-lo?

**Viável.** Procedimento derivado das estruturas já confirmadas:

```text
1. copiar GN438_original.bin              (nunca editar o original)
2. alterar bytes DENTRO da partição alvo  (preferencialmente sem mudar tamanhos)
3. recalcular CRC-16/CCITT-FALSE da partição
4. gravar o CRC no campo +0x0C da entrada em 0x0000D000
5. se a alteração tocar os primeiros 4 KiB da FIRM,
   recalcular também loadCrc em 0x0000E01C
6. validar com tools/find_partitions.py  → todos os CRCs devem dar OK
7. comparar tamanho: deve permanecer exatamente 2.097.152 bytes
```

**Ainda não implementado.** O passo seguinte do projeto é escrever
`tools/rebuild_firmware.py` e `tools/validate_firmware.py`.

Riscos conhecidos e não resolvidos: os campos `+0x18` e `+0x1C` do
cabeçalho `HLKJ` seguem **NÃO IDENTIFICADOS**, e não se sabe se o
bootloader verifica algo além dos CRCs.

### 21. Quais partes são fáceis de modificar?

Em ordem crescente de risco:

1. **Folha de ícones do menu principal** (`0x000CDD50`, 128×160 INDEXED_8) —
   substituir pixels mantendo a paleta e o tamanho. Nenhum offset muda.
2. **Papel de parede** (`0x000C73B8`) e **logotipo de boot** (`0x000CC7C4`).
3. **Ícones 4bpp individuais** em `icons_main` — mantendo `box_w`/`box_h`,
   o blob não muda de tamanho e nenhum ponteiro precisa ser recalculado.
4. **Textos de UI** — reescrever in-place, respeitando o comprimento original.
5. **Bitmaps de glifos da fonte** — mesmo princípio dos ícones.

Todos dependem apenas de: reescrever bytes + recalcular dois CRCs.

### 22. Quais são perigosas?

- **Bootloader** (`0x000000`–`0x00D000`) — é o único caminho de
  recuperação conhecido. Nunca tocar nesta fase.
- **Primeiros 4 KiB da FIRM** — carregados em RAM e verificados por
  `loadCrc` próprio; um erro aqui impede o boot.
- **PSMP** (`0x1FC000`) — provável área reescrita pelo dispositivo em
  runtime. Qualquer coisa gravada ali pode ser sobrescrita.
- **Mudar tamanhos** de qualquer recurso — deslocaria offsets e
  invalidaria ponteiros absolutos `0x00Cxxxxx` espalhados pelo código.
- **Entrada / botões** — enquanto a tabela de `key_id` não for
  desmontada, alterar isso pode produzir um aparelho que liga mas não
  navega.

### 23. Qual deve ser o primeiro patch?

**Proposta: substituir um único ícone 4bpp de `icons_main`, mantendo
exatamente as mesmas dimensões.**

Justificativa:
- altera algumas dezenas de bytes;
- não muda nenhum offset, tamanho ou ponteiro;
- exige recalcular apenas o CRC da partição FIRM;
- não toca o bootloader nem os 4 KiB do estágio em RAM;
- é visualmente verificável no aparelho em um segundo;
- e, principalmente, **prova o ciclo completo
  extrair → modificar → reconstruir → validar** com o menor risco possível.

Alternativa de impacto visual maior e risco equivalente: a folha de
ícones do menu principal em `0x000CDD50`.

> Antes de qualquer gravação, é obrigatório resolver o método de flash e
> de recuperação. Existe uma rotina `boot sdupdate` no bootloader (ver
> abaixo), que é a pista mais promissora.

---

## Descobertas adicionais relevantes

### Sistema operacional — CONFIRMADO

**FreeRTOS**, com uma camada de abstração própria (`OAL_`).

Evidências: `[osfreertos]: Error creating thread: %s, stack size: %d`,
`[osfreertos]: Error creating exitSem`, `[osfreertos]: Error creating joinSem`,
`task:%s stack overflow, stack start addr:0x%x, stack top addr:0x%x`,
`OAL_mutex_create`, `MainTaskTimer`, `_dev_service_task_`.

O modelo de dispositivos é do tipo Unix (`/dev/...` com `open`), o que
sugere uma camada de driver padronizada sobre o FreeRTOS.

### Atualização por cartão SD — CONFIRMADO

O bootloader contém uma rotina de atualização via cartão SD, com
verificação em etapas:

```text
boot sdupdate--->header pass
boot sdupdate--->mark pass
boot sdupdate--->file length %d
boot sdupdate--->parition_start= %x
boot sdupdate--->codeOffsetInByte + parition_start= %x
boot sdupdate--->succeed get update buff
UPDATE_LACK_OF_MEMORY
```

**Isto é potencialmente o caminho de gravação mais seguro do projeto**:
não depende de USB e o bootloader valida cabeçalho e marca antes de
gravar. O formato do arquivo de atualização **ainda não foi determinado**
— é a próxima peça de engenharia reversa de maior valor.

### Origem do SDK

Caminhos de compilação preservados no binário:

```text
F:\pen133_yp3_mp\spark2\src\gui8\lvgl\...
F:\pen133_yp3_mp\spark2\src\middleware\audio_crab\core\crab_pin.c
```

O SDK se chama **spark2**, com um middleware de áudio chamado
**audio_crab**. Módulos identificados: `gui8` (LVGL) e `middleware`.

### Cardreader USB

`SMTLINK CARDREADER      1.00` em `0x00046FBF`, além de
`usbd_msc_cardreader_init` e `driver_usbd_msc_param_init` — o aparelho se
apresenta como dispositivo de armazenamento em massa, coerente com o
VID:PID `301a:2801` observado.

---

## Estado atual e lacunas

### Resolvido nesta fase

- Layout completo da flash e tabela de partições.
- Algoritmo e localização de **todos** os checksums.
- Formato dos dois cabeçalhos de imagem, com nomes de campo vindos do
  próprio firmware.
- Base de mapeamento XIP da flash (`0x00C00000`).
- Arquitetura da CPU e do RTOS.
- Framework de GUI, resolução e profundidade de cor.
- Formato completo de fontes e ícones, com extração funcionando.
- Mapa das 61 telas.

### Não resolvido

| Item | Impacto |
|---|---|
| Campos `+0x18` e `+0x1C` do cabeçalho `HLKJ` | médio — pode afetar rebuild |
| Formato do pacote de `boot sdupdate` | **alto** — é o caminho de gravação |
| Tabela de `key_id` e demais botões | **alto** — bloqueia Fase 2 |
| `/dev/tp` é real ou código morto? | médio |
| ST7789S vs GC9106: qual roda? | médio |
| Lacuna zerada de 128 KiB em `0x019000` | baixo |
| Driver `lv_fs` "r://" | baixo |
| Conteúdo da partição TONE | baixo |
| Núcleo Cortex-M exato | baixo |

### Próximos passos recomendados

1. Escrever `tools/rebuild_firmware.py` + `tools/validate_firmware.py`.
2. Fazer um rebuild **idêntico ao original** (round-trip byte a byte) e
   confirmar SHA-256 igual — prova que o processo não corrompe nada.
3. Desmontar a rotina `boot sdupdate` e determinar o formato do pacote.
4. Desmontar o handler de `key_id`.
5. Só então produzir `GN438_openpod_v001.bin` com um único ícone alterado.
