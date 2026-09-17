# ANDROMEDA

## Estudo de viabilidade de SD Boot e possível compatibilidade com Rockbox no GN-438 / YP3

**Projeto:** OpenPod  
**Papel:** Pesquisa técnica independente — não é implementação.  
**Data de início:** 2026-09-15  
**Responsabilidade:** determinar, por evidência, se o GN-438 pode ser transformado em uma plataforma capaz de inicializar um sistema alternativo a partir do microSD.

---

## 1. O que é ANDROMEDA

ANDROMEDA é uma linha de investigação paralela ao OpenPod/MARTE:

| | MARTE | ANDROMEDA |
|---|---|---|
| **Objetivo** | Modificar o firmware original para criar a experiência OpenPod | Determinar se é possível executar um sistema alternativo (ex: Rockbox) carregado do microSD |
| **Base** | Firmware YP3 existente | Hardware + bootloader + reverse engineering |
| **Entrega** | Firmware modificado, patches, releases | Documentação de viabilidade e mapa de incertezas |
| **Risco aceito** | Apenas modificações reversíveis na FIRM | Nenhuma gravação no dispositivo nesta fase |

A pergunta central do ANDROMEDA é:

> **O GN-438 consegue inicializar um sistema alternativo a partir do microSD, em vez de precisar que todo o sistema caiba nos 2 MiB de flash interna?**

---

## 2. Hierarquia de prioridade da pesquisa

A investigação segue esta ordem lógica:

```text
1. SD Boot          ← decisão mais impactante
2. RAM / Bootloader
3. Hardware (SoC, CPU, periféricos)
4. Rockbox
5. Viabilidade final
```

Se o SD Boot for impossível, a limitação de 2 MiB de flash torna o Rockbox inviável. Se for possível, o projeto muda de escopo.

---

## 3. Estrutura da pasta

| Arquivo | Conteúdo |
|---|---|
| `README.md` | este documento |
| `RESEARCH.md` | metodologia, fontes, status geral |
| `SOC.md` | identificação e investigação do SoC |
| `CPU.md` | arquitetura, núcleo, endianness, ABI |
| `MEMORY.md` | mapa de memória: flash, SRAM, periféricos, XIP |
| `BOOT.md` | análise do bootloader |
| `SD_BOOT_FEASIBILITY.md` | análise central do SD Boot |
| `DISPLAY.md` | display e LCD controller |
| `INPUT.md` | botões e entrada |
| `STORAGE.md` | SD controller e filesystem |
| `AUDIO.md` | áudio, codec, I2S, DMA |
| `POWER.md` | PMU, bateria, sleep/wake |
| `USB.md` | USB e modos de boot |
| `BLUETOOTH.md` | Bluetooth (chip, stack, perfis) |
| `FM.md` | rádio FM |
| `ROCKBOX.md` | arquitetura do Rockbox relevante |
| `ROCKBOX_TARGETS.md` | targets semelhantes do Rockbox |
| `ROCKBOX_MATRIX.md` | matriz de compatibilidade GN-438 × Rockbox |
| `UNKNOWN.md` | hipóteses abertas e como confirmar |
| `RISKS.md` | riscos técnicos e classificação |
| `REFERENCES.md` | fontes internas e externas |
| `INTEGRITY.md` | checksum/CRC e validação do firmware |
| `FEASIBILITY.md` | relatório final com veredito |

---

## 4. Regras desta pesquisa

- **NÃO modificar** `firmware/ORIGINAL/GN438_original.bin`.
- **NÃO gravar** no dispositivo.
- **NÃO executar** operações destrutivas (`erase`, `write_flash`, `write_mem`, `exec`).
- **NÃO escrever código de produção** — apenas ferramentas de análise, se necessário.
- **NÃO apresentar hipótese como fato**.
- Classificar toda descoberta como **CONFIRMADO**, **PROVÁVEL**, **HIPÓTESE** ou **NÃO RESOLVIDO**.

---

## 5. Estado resumido (atual)

| Pergunta | Resposta preliminar | Confiança |
|---|---|---|
| CPU | ARMv7-M, Thumb-2, com FPU | PROVÁVEL (família); núcleo exato NÃO IDENTIFICADO |
| SoC | Jointbees MP3 V57J21B6A0; internamente SL6801 (VID:PID `301a:2801`) | CONFIRMADO (físico) / PROVÁVEL (SL6801) |
| Flash interna | 2 MiB | CONFIRMADO |
| RAM total | **512 KiB** (`0x00800000`–`0x00880000`) | PROVÁVEL |
| Bootloader | Carrega 4 KiB da FIRM para RAM e salta; tem rotina `sdupdate` | PROVÁVEL |
| SD update | Existe, lê `update.up` do cartão e grava na flash | CONFIRMADO |
| SD Boot (carregar para RAM e executar) | **NÃO existe caminho pronto no bootloader** | PROVÁVEL |
| Primitivas para SD Boot | `f_mount`, `f_open`, `f_read`, `f_lseek` existem no bootloader | CONFIRMADO |
| Possibilidade de patch na FIRM stage | Possível e mais segura que substituir bootloader | HIPÓTESE |
| Rockbox completo | **Inviável** — RAM 512 KiB << menor target Rockbox documentado (2 MB); drivers inexistentes | PROVÁVEL |
| Rockbox subset | Possível, mas requer RE de codec/DMA/GPIO | HIPÓTESE |
| GUI original | LVGL 8 | CONFIRMADO |
| Display | GC9106 ativo, RGB565, **128×160** (provável) | PROVÁVEL |
| Áudio | `audio_crab`, codec provavelmente integrado, ASRC/EQ | PROVÁVEL |
| Bluetooth | A2DP src/snk, AVRCP, HFP | CONFIRMADO |
| USB | Device MSC (card reader), detecção VBUS via PMU | CONFIRMADO |
| FM | Presets, bandas, antena via fone, tuner não identificado | PROVÁVEL |

**Veredito preliminar:** SD Boot é 🟡 viável com engenharia reversa; Rockbox completo é 🔴 inviável. Ver `FEASIBILITY.md`.

---

## 5.1 Documentos concluídos

- `README.md`
- `RESEARCH.md`
- `SOC.md`
- `CPU.md`
- `MEMORY.md`
- `BOOT.md`
- `SD_BOOT_FEASIBILITY.md`
- `DISPLAY.md`
- `INPUT.md`
- `STORAGE.md`
- `AUDIO.md`
- `POWER.md`
- `USB.md`
- `BLUETOOTH.md`
- `FM.md`
- `RISKS.md`
- `UNKNOWN.md`
- `REFERENCES.md`
- `ROCKBOX.md`
- `ROCKBOX_TARGETS.md`
- `ROCKBOX_MATRIX.md`
- `INTEGRITY.md`
- `FEASIBILITY.md`

Todos os documentos planejados foram escritos; `INTEGRITY.md` e `DISPLAY.md` foram atualizados com novas descobertas.


---

## 6. Principais documentos de entrada

- `docs/FIRMWARE_ANALYSIS.md`
- `docs/FIRMWARE_MAP.md`
- `docs/SDUPDATE_ANALYSIS.md`
- `docs/UPDATE_MECHANISM.md`
- `docs/BUTTON_ANALYSIS.md`
- `docs/GUI_ANALYSIS.md`
- `docs/EXTERNAL_RESEARCH.md`
- `firmware/ORIGINAL/GN438_original.bin` (SHA-256: `b7cd5eb9…4b36f`)

---

## 7. Resultado esperado

Ao final, ANDROMEDA deve entregar:

1. Uma resposta clara para as 10 perguntas do veredito (ver `FEASIBILITY.md`).
2. Uma classificação final: 🟢 / 🟡 / 🟠 / 🔴.
3. Um mapa de incertezas para o engenheiro que assumir a implementação.
4. Nenhuma modificação no firmware original.
