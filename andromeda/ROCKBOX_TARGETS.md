# ANDROMEDA — ROCKBOX_TARGETS

## Targets Rockbox com características próximas ao GN-438

---

## 1. Critérios de comparação

Um target Rockbox serve como referência arquitetural quando compartilha:

- Arquitetura ARM (preferencialmente Cortex).
- Pouca RAM (relativamente).
- LCD pequeno.
- SD/microSD como storage.
- Áudio via I2S/DAC.

---

## 2. Targets relevantes

### 2.1 AGPtEK Rocker / Benjie BJ-T6

| Propriedade | Valor |
|---|---|
| SoC | Ingenic X1000 |
| CPU | MIPS XBurst |
| RAM | 32 MB (integrada) |
| Flash | SPI NAND |
| Display | 1.8" TFT |
| Storage | microSDXC |
| Bluetooth | CSR 8811 |
| Codec | Cirrus 42L51C |
| PMU | AXP192 |

**Relevância:** Média. É um player compacto com SD, mas usa MIPS e tem 32 MB de RAM — muito acima do GN-438.

### 2.2 FiiO M3K

| Propriedade | Valor |
|---|---|
| SoC | Ingenic X1000 |
| CPU | MIPS XBurst |
| RAM | 32 MB |
| Display | 240×320 |
| Storage | microSD |
| Codec | AK4376 |

**Relevância:** Média. Native port, mas MIPS e muita RAM.

### 2.3 Cowon D2

| Propriedade | Valor |
|---|---|
| CPU | Telechips TCC7801 (ARM) |
| RAM | 32 MB |
| Display | 320×240 touchscreen |
| Storage | NAND interno + SD |
| Codec | Wolfson WM8985 |

**Relevância:** Média. Usa SD como storage principal, mas tem 32 MB de RAM.

### 2.4 RCA RC3000A

| Propriedade | Valor |
|---|---|
| CPU | Telechips TCC760 (ARM) |
| RAM | DRAM externa |
| Storage | NAND interno + SD |

**Relevância:** Média. Exemplo de porte com RE significativa, mas hardware mais antigo.

### 2.5 Archos Jukebox / Ondio

| Propriedade | Valor |
|---|---|
| CPU | SH-1 |
| RAM | 2 MB |
| Display | Monocromático |

**Relevância:** Baixa. Pouca RAM, mas monocromático e arquitetura diferente.

### 2.6 Sansa Clip / Clip+ / Clip Zip

| Propriedade | Valor |
|---|---|
| CPU | AMS AS3525 (ARM) |
| RAM | ~8 MB |
| Display | 96×64 / 128×64 |
| Storage | flash interna + microSD |

**Relevância:** Média. Player compacto com SD, mas ainda tem mais RAM que o provável GN-438.

---

## 3. Comparativo

| Target | CPU | RAM | Display | SD | Áudio | Relevância |
|---|---|---|---|---|---|---|
| GN-438 (hipótese) | ARM Cortex-M | ~256 KB? | 128×160 RGB565 | sim | desconhecido | — |
| AGPtEK Rocker | MIPS | 32 MB | 1.8" TFT | sim | Cirrus 42L51C | Média |
| FiiO M3K | MIPS | 32 MB | 240×320 | sim | AK4376 | Média |
| Cowon D2 | ARM (TCC7801) | 32 MB | 320×240 | sim | WM8985 | Média |
| Sansa Clip+ | ARM | ~8 MB | 128×64 | sim | AS3525 | Média |
| Archos Jukebox | SH-1 | 2 MB | mono | não | — | Baixa |

---

## 4. Conclusão

Não existe um target Rockbox conhecido com:
- ARM Cortex-M;
- ~256 KB de RAM;
- display colorido 128×160;
- SD/microSD.

O GN-438 estaria em uma classe de RAM **inferior** aos targets existentes. Isso não impede um porte, mas significa que **não há modelo direto para copiar**.

A referência mais útil seria o **Cowon D2** pelo uso de SD como storage principal e o **RCA RC3000A** pelo processo de RE documentado.
