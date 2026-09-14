# OpenPod — FIRMWARE_MAP

Mapa real do dump `GN438_original.bin` (yp3_2.0.43).

- **Arquivo:** 2.097.152 bytes (2 MiB), `0x00000000`–`0x001FFFFF`
- **SHA-256:** `b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f`
- **Base XIP da flash em memória:** `0x00C00000` — CONFIRMADO
  (ponteiros de `lv_img_dsc_t` satisfazem `ptr - 0x00C00000 == offset no arquivo`,
  em 8 de 8 casos; reconfirmado pelo ponteiro de cmap `0x00CC1150` → `0x000C1150`)

---

## 1. Mapa de alto nível

```text
0x00000000 ┌──────────────────────────────────────────────┐
           │ Cabeçalho de boot  "HLKJ"          0x60 B    │  CONFIRMADO
0x00000060 ├──────────────────────────────────────────────┤
           │ Bootloader — código ARM Thumb-2              │  CONFIRMADO
           │ payload 0xC8EC B, CRC16 0x759D  OK           │
0x0000C94C ├──────────────────────────────────────────────┤
           │ padding 0x00                                 │
0x0000D000 ├──────────────────────────────────────────────┤
           │ TABELA DE PARTIÇÕES  (3 entradas)            │  CONFIRMADO
0x0000D040 ├──────────────────────────────────────────────┤
           │ padding 0x00                                 │
0x0000E000 ├──────────────────────────────────────────────┤
           │ ███ PARTIÇÃO  FIRM  ███  1.647.984 B         │  CONFIRMADO
           │     CRC16 0x49A6  OK                         │
0x001A0570 ├──────────────────────────────────────────────┤
           │ lacuna — 2.704 B de 0x00                     │
0x001A1000 ├──────────────────────────────────────────────┤
           │ ███ PARTIÇÃO  TONE  ███  8.248 B             │  CONFIRMADO
           │     CRC16 0x9177  OK                         │
0x001A3038 ├──────────────────────────────────────────────┤
           │ ÁREA LIVRE — 364.488 B de 0xFF (apagada)     │  CONFIRMADO
           │   em uso pelo OpenPod (ver 1.1 abaixo)       │
0x001FC000 ├──────────────────────────────────────────────┤
           │ ███ PARTIÇÃO  PSMP  ███  16.384 B            │  CONFIRMADO
           │     CRC16 gravado = 0x0000 (não verificada)  │
0x00200000 └──────────────────────────────────────────────┘
```

**Espaço livre disponível: 364.488 bytes (356 KiB, 17,4 % da flash).**
Relevante para o OpenPod: há folga real para novos recursos gráficos.

### 1.1 O que o OpenPod já pôs na área livre

Esta área é **fora de todas as partições**, logo fora de qualquer CRC.
Leitura por XIP em `0x00C00000 + offset` foi CONFIRMADA no V017;
**execução** de código, no V020.

| Offset | XIP | Tamanho | O quê | Desde |
|---|---|---|---|---|
| `0x001A3038` | `0x00DA3038` | 8 B | string `"OpenPod"` (título da home) | V016/V017 |
| `0x001A3054` | `0x00DA3054` | 868 B | **ponteiros da tabela de strings do português, realocada**: 217 ids, o 216 é `Extras` | V021 |
| `0x001A33B8` | `0x00DA33B8` | 24 B | tabela de destinos do Extras: `3 5 6 2 9 8` | V029 |
| `0x001A33D0` | `0x00DA33D0` | ~145 B | módulo de roteamento do Extras (Thumb-2) | V029 |
| `0x001A3464` | `0x00DA3464` | ~3,3 KiB | os textos do português, revisados | V021+ |
| `0x001A5000` | `0x00DA5000` | 88 B | **rotina do título da barra superior** (Thumb-2) | V054 |
| `0x001A5058` | `0x00DA5058` | 76 B | tabela `página → id de string`, 37 telas | V054 |

Último byte em uso: `0x001A4197`, depois `0x001A5000..0x001A50A3`.

> ⚠️ **A tabela de strings que vale é a da área livre.** Editar a
> original em `0x00C53B84` não tem efeito nenhum desde o V021. Está
> repetido aqui porque é o tipo de coisa que custa uma sessão inteira.

Primeiro setor ainda virgem depois disso: **`0x001A6000`**.

---

## 2. Cabeçalho de boot `HLKJ` @ `0x00000000`

Os nomes dos campos **não são inventados**: vêm de uma string de depuração
do próprio bootloader em `0x0000A061`:

```text
boot--->firmware_header_len 0x%x;timestamp 0x%x;loadToRam 0x%x;
        runFromRam 0x%x;loadLength 0x%x;loadCrc 0x%x
```

| Offset | Tipo | Campo | Valor | Status |
|---|---|---|---|---|
| +0x00 | char[4] | magic | `HLKJ` | CONFIRMADO |
| +0x04 | u32 | loadToRam | `0x0081FBC0` | CONFIRMADO |
| +0x08 | u32 | runFromRam | `0x00820001` (Thumb) | CONFIRMADO |
| +0x0C | u32 | firmware_header_len | `0x60` | CONFIRMADO |
| +0x10 | u32 | loadLength | `0xC8EC` | CONFIRMADO |
| +0x14 | u16/u32 | loadCrc | `0x759D` | CONFIRMADO (CRC validado) |
| +0x18 | u32 | ? | `0x00000009` | **NÃO IDENTIFICADO** |
| +0x1C | u32 | ? | `0x00000400` | **NÃO IDENTIFICADO** |
| +0x20 | u32 | offset da tabela de partições | `0x0000D000` | PROVÁVEL (aponta exatamente para a tabela) |
| +0x24 | u32 | ? | `0x00000000` | **NÃO IDENTIFICADO** |

O `timestamp` do formato genérico não aparece neste header — é possível que
o cabeçalho `HLKJ` (lido pela mask ROM) e o cabeçalho de partição (lido pelo
bootloader) sejam **variantes diferentes** do mesmo formato. Ver seção 4.

---

## 3. Tabela de partições @ `0x0000D000`

```text
+0x00  u32   número de entradas          = 3
+0x04  u32   número de entradas (cópia)  = 3
+0x08  u32   0
+0x0C  u32   0
+0x10  entradas de 16 bytes:
         +0x00  char[4]  nome
         +0x04  u32      offset na flash
         +0x08  u32      tamanho em bytes
         +0x0C  u32      CRC-16/CCITT-FALSE (nos 16 bits baixos)
```

| Nome | Offset | Tamanho | Fim | CRC gravado | CRC calculado |
|---|---|---|---|---|---|
| `FIRM` | 0x0000E000 | 0x00192570 | 0x001A0570 | 0x49A6 | **0x49A6 OK** |
| `TONE` | 0x001A1000 | 0x00002038 | 0x001A3038 | 0x9177 | **0x9177 OK** |
| `PSMP` | 0x001FC000 | 0x00004000 | 0x00200000 | 0x0000 | 0x5684 (não verificada) |

Os limites declarados coincidem **exatamente** com as fronteiras de
preenchimento observadas de forma independente no mapa de entropia
(`0x001A0570` início de zeros, `0x001A3038` início de 0xFF). Isto é
evidência cruzada, não coincidência.

---

## 4. Cabeçalho da partição FIRM @ `0x0000E000`

| Offset | Campo | Valor | Status |
|---|---|---|---|
| +0x00 | firmware_header_len | `0x30` | CONFIRMADO |
| +0x04 | timestamp | `0x8F20F1C2` | PROVÁVEL (nome vem da string de debug; epoch desconhecido) |
| +0x08 | — | `0` | reservado |
| +0x0C | — | `0` | reservado |
| +0x10 | loadToRam | `0x00804C00` | CONFIRMADO |
| +0x14 | runFromRam | `0x00804C01` (Thumb) | CONFIRMADO |
| +0x18 | loadLength | `0x1000` (4 KiB) | CONFIRMADO |
| +0x1C | loadCrc | `0x68E1` | **CONFIRMADO — CRC16 de FIRM[0x30:0x1030] confere** |

### Consequência arquitetural importante

`loadLength` é apenas **4 KiB**. O bootloader copia somente os primeiros
4096 bytes da FIRM para a RAM em `0x00804C00` e salta para lá. Os outros
~1,6 MB **não cabem em RAM e não são copiados**: executam em XIP
diretamente da flash mapeada em `0x00C00000`.

Isso explica por que recursos (fontes, ícones, imagens) são referenciados
por ponteiro absoluto `0x00Cxxxxx` — eles são lidos direto da flash.

**Para o OpenPod isto é excelente:** alterar um ícone ou uma fonte não
exige recalcular layout de RAM. Basta reescrever os bytes na flash e
corrigir o CRC da partição FIRM.

---

## 5. Layout interno da partição FIRM

Fronteiras derivadas de densidade de opcodes Thumb, entropia e das
estruturas de dados identificadas.

| Faixa | Conteúdo | Status |
|---|---|---|
| `0x00E000`–`0x00E030` | cabeçalho FIRM | CONFIRMADO |
| `0x00E030`–`0x00F030` | estágio carregado em RAM (4 KiB) | CONFIRMADO |
| `0x00F030`–`0x018A90` | código Thumb-2 com uso intenso de VFP (matemática / DSP de áudio) | PROVÁVEL |
| `0x019000`–`0x03946F` | **131.072 B de 0x00** — lacuna interna | CONFIRMADO (conteúdo), propósito NÃO IDENTIFICADO |
| `0x039470`–`0x048000` | código Thumb-2 | PROVÁVEL |
| `0x048000`–`0x05E7E0` | código + dados; registradores MMIO em `0x4008xxxx` | PROVÁVEL |
| `0x05E7E0`–`0x086C32` | **blob de bitmaps da fonte de texto** (164.946 B) | CONFIRMADO |
| `0x086C44`–`0x0A27E4` | **tabela de glifos da fonte** (7098 × 16 B) | CONFIRMADO |
| `0x0A27E6`–`0x0A5F70` | **cmap da fonte** (7098 × u16) | CONFIRMADO |
| `0x0A5F71`–`0x0A6568` | blob do conjunto `icons_small` (4bpp) | PROVÁVEL |
| `0x0A6568`–`0x0A66E8` | tabela de `icons_small` (24 glifos) | CONFIRMADO |
| `0x0B0DC4`–`0x0BE720` | **blob de bitmaps dos ícones** 4bpp (55.644 B) | CONFIRMADO |
| `0x0BE720`–`0x0C1150` | **tabela de ícones** (675 × 16 B) | CONFIRMADO |
| `0x0C1150`–`0x0C1CC6` | **cmap dos ícones** (U+F000…) | CONFIRMADO |
| `0x0C235C`–`0x0C71BC` | 4 imagens `TRUE_COLOR_CHROMA` 50×50 (RGB565) | CONFIRMADO |
| `0x0C71AC`–`0x0C73B8` | 1 imagem `TRUE_COLOR_CHROMA` 16×16 | CONFIRMADO |
| `0x0C73B8`–`0x0CC7C4` | imagem `INDEXED_8` 128×160 (papel de parede) | CONFIRMADO |
| `0x0CC7C4`–`0x0CDD50` | imagem `INDEXED_8` 128×35 (logotipo **GENAI**) | CONFIRMADO |
| `0x0CDD50`–`0x0D315C` | imagem `INDEXED_8` 128×160 (**folha de ícones do menu principal**) | CONFIRMADO |
| `0x0D3000`–`0x0F4000` | strings de UI (8 idiomas), paths de código, mensagens de debug | CONFIRMADO |
| `0x0F4000`–`0x1A0570` | **corpo principal do código** — maior densidade de Thumb-2 do dump | PROVÁVEL |

### Mapa de strings dentro da FIRM

| Faixa | Conteúdo |
|---|---|
| `0x04A000`–`0x053000` | mensagens de debug do gerenciador (`-yp3 mgr ...`, `watch_key_*`) |
| `0x053000`–`0x05E000` | **textos de interface nos 8 idiomas** |
| `0x0D9000`–`0x0E1000` | asserts do LVGL + paths `F:\pen133_yp3_mp\spark2\src\gui8\lvgl\...` |
| `0x0E2000`–`0x0E5000` | drivers (`gc9106_lcd_init`, USB, SD, áudio) |

---

## 6. TONE @ `0x001A1000` (8.248 B)

Contém uma assinatura `ID3` em `0x001A1400`. Consistente com um ou mais
sons de sistema em MP3. **NÃO CONFIRMADO** — não foi extraído nem decodificado
nesta fase.

## 7. PSMP @ `0x001FC000` (16.384 B)

Dados apenas em `0x001FC000`–`0x001FC82F` (2.096 B); o restante é `0xFF`.
CRC gravado é `0x0000`, isto é, **não verificado pelo boot**.

Estar no fim da flash, ter baixa entropia, ser parcialmente apagado e não
ter CRC são quatro indícios convergentes de **área de configuração /
parâmetros persistentes gravada em runtime**.

> ✅ **CONFIRMADO em 2026-09-12 por observação.** Uma releitura do aparelho
> mostrou que a `PSMP` — e **somente** ela — mudou sozinha entre dois
> dumps. O formato foi decodificado: armazenamento append-only
> chave-valor, sem apagamento. Ver `docs/PSMP_FORMAT.md`.

> Consequência prática: PSMP é a única região que o dispositivo
> provavelmente reescreve sozinho. Não usar essa área para código.
