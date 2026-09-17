# ANDROMEDA — RESEARCH

## Metodologia e status geral da pesquisa

---

## 1. Base de dados

| Fonte | O quê | Como foi usada |
|---|---|---|
| `firmware/ORIGINAL/GN438_original.bin` | Dump completo de 2 MiB | Análise estática, disassembly, extração de strings |
| `docs/FIRMWARE_ANALYSIS.md` | 23 perguntas respondidas sobre o firmware | Ponto de partida |
| `docs/FIRMWARE_MAP.md` | Mapa real da flash | Entender layout e áreas livres |
| `docs/SDUPDATE_ANALYSIS.md` | Disassembly da rotina `boot sdupdate` | Base para SD Boot |
| `docs/UPDATE_MECHANISM.md` | Mecanismo de atualização por SD confirmado | Contexto de risco |
| `docs/BUTTON_ANALYSIS.md` | Entrada (botões, ADC, LVGL) | Mapeamento de input |
| `docs/GUI_ANALYSIS.md` | LVGL, display, fontes, imagens | Mapeamento de output |
| `docs/EXTERNAL_RESEARCH.md` | Pesquisa sobre YP3/SL6801/Smartlink | Contexto externo |
| `tools/disasm.py` | Disassembly ARM Thumb-2 | Análise do bootloader |
| `tools/firmware_info.py` | Informações gerais do binário | Validação de estrutura |
| `tools/validate_firmware.py` | Validação de CRC e layout | Confiança nos dados |
| `tools/extract_strings.py` | Extração de strings | Evidências textuais |

---

## 2. Convenção de confiança

Toda afirmação relevante é classificada:

- **CONFIRMADO** — evidência direta no firmware, no hardware (observação) ou em documentação confiável.
- **PROVÁVEL** — várias evidências convergentes, mas sem confirmação direta.
- **HIPÓTESE** — explicação plausível, ainda não comprovada.
- **NÃO RESOLVIDO** — investigado e não determinado.

---

## 3. Linha do tempo

| Data | Evento |
|---|---|
| 2026-09-11 | Dump do firmware original confirmado (SHA-256: `b7cd5eb9…4b36f`) |
| 2026-09-11 | `docs/FIRMWARE_ANALYSIS.md` — estrutura geral do firmware |
| 2026-09-12 | `docs/SDUPDATE_ANALYSIS.md` — rotina `boot sdupdate` desmontada |
| 2026-09-12 | `docs/UPDATE_MECHANISM.md` — mecanismo de update por SD confirmado |
| 2026-09-12 | `docs/PSMP_FORMAT.md` — formato da partição de configuração |
| 2026-09-14 | Core 1.0.1 instalada no aparelho via SD (`docs/ESTADO_ATUAL.md`) |
| 2026-09-15 | Início do ANDROMEDA — criação da pasta e leitura da documentação existente |

---

## 4. Descobertas já consolidadas (relevantes para ANDROMEDA)

### 4.1 CPU e arquitetura

- **ARMv7-M, Thumb-2, com FPU** — CONFIRMADO.
- Instruções VFP (`vldr`, `vstr`, etc.) em `0x00E030`–`0x018A90`.
- Instruções Thumb-2 de 32 bits (`mov.w`, `tbb`) descartam Cortex-M0/M0+.
- Núcleo exato (M4F / M7 / M33) — **NÃO IDENTIFICADO**.

### 4.2 Flash e partições

- 2 MiB, 3 partições: `FIRM`, `TONE`, `PSMP`.
- Bootloader ocupa `0x000000`–`0x000D000` (protegido no `sdupdate`).
- Área livre: 364.488 bytes (`0x001A3038`–`0x001FBFFF`).

### 4.3 Bootloader

- Carrega 4 KiB da FIRM para `0x00804C00` e salta para `0x00804C01`.
- Restante da FIRM executa em XIP a partir de `0x00C00000`.
- Contém rotina `sdupdate` que lê `0:\update.up` e grava na flash.
- Primitivas FatFs (`f_mount`, `f_open`, `f_read`, `f_lseek`) presentes.

### 4.4 SD Boot

- **Não existe caminho pronto** no bootloader para carregar código do SD para RAM e executar.
- As primitivas necessárias existem.
- Um patch no bootloader seria teoricamente possível, mas de alto risco.

### 4.5 Rockbox

- Nenhum porte conhecido para SL6801/YP3.
- SDK/documentação do chip inexistentes publicamente.
- Precedente: firmware YP3 já foi modificado com sucesso (`bunkaich`), mas não há publicação técnica.

---

## 5. Lacunas que orientam a pesquisa

| # | Lacuna | Impacto | Prioridade |
|---|---|---|---|
| 1 | Tamanho total da SRAM | Define o tamanho máximo de um sistema carregado do SD | P0 |
| 2 | Mapa de memória completo (RAM, periféricos, DMA) | Base para qualquer sistema alternativo | P0 |
| 3 | Se o bootloader pode ser modificado para SD Boot | Determina a arquitetura | P0 |
| 4 | Identidade exata do SoC / CPU | Necessária para toolchain e drivers | P1 |
| 5 | Drivers de áudio, LCD, SD, botões | Necessários para Rockbox | P1 |
| 6 | Tamanho mínimo de um Rockbox funcional | Determina viabilidade de RAM | P1 |
| 7 | Stack e heap do firmware atual | Determina RAM disponível | P1 |
| 8 | Bluetooth, FM, USB | Não bloqueiam a primeira avaliação | P2/P3 |

---

## 6. Proibições desta fase

- Nenhuma gravação no dispositivo.
- Nenhuma modificação em `firmware/ORIGINAL/`.
- Nenhum código de produção.
- Nenhuma operação destrutiva.

Toda a pesquisa é **offline** e **baseada em evidência**.
