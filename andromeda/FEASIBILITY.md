# ANDROMEDA — FEASIBILITY

## Veredicto preliminar de viabilidade

**Data:** 2026-09-15  
**Autor:** OpenPod / Claude  
**Status:** FINAL — RAM mapeada e subsistemas documentados

---

## 1. Resumo executivo

| Pergunta | Resposta |
|---|---|
| O GN-438 pode fazer SD Boot? | **Provavelmente sim, com engenharia reversa** — o bootloader já lê arquivos do SD (`0:\update.up`) e sabe saltar para código em RAM. |
| O GN-438 pode rodar Rockbox? | **Não** — RAM é 512 KiB, abaixo do menor target conhecido do Rockbox (Archos Jukebox com 2 MB). Drivers inexistentes. |
| Qual é o primeiro passo prático? | **Patch seguro do FIRM stage** para carregar payload do SD, se a linha ANDROMEDA continuar. |
| Qual é o risco mais alto? | **Brick** ao modificar o bootloader; perda de funcionalidade ao substituir firmware. |

---

## 2. Respostas às 10 perguntas do ANDROMEDA

### 2.1 CPU

- **Qual é a CPU?**  
  ARM Cortex-M, arquitetura ARMv7-M Thumb-2, com FPU.
- **Evidência:** vetores Cortex-M no início do bootloader; instruções Thumb-2 de 32 bits; instruções VFP; o repositório `smartlink_flash` compila payloads para `.arch armv7-m`.
- **Confiança:** CONFIRMADO (ARMv7-M); PROVÁVEL (FPU).

### 2.2 SoC

- **Qual é o chip?**  
  Marcação física: **Jointbees MP3 V57J21B6A0**. Internamente identificado pelo firmware como **SL6801**.
- **Evidência:** string `SL6801` no bootloader em `0x0000C184`; VID:PID `301a:2801` e inquiry `SMTLINK CARDREADER 1.00` correspondem exatamente ao SL6801 documentado no `smartlink_flash`; fabricante é Shenzhen Shenju Technology (Jointbees).
- **Confiança:** CONFIRMADO (Jointbees MP3 V57J21B6A0); PROVÁVEL (SL6801).

### 2.3 RAM

- **Quanta RAM existe?**  
  **512 KiB.** O heap LVGL foi encontrado em `0x00876000` com tamanho de 40 KiB (`0xA000`), terminando exatamente em `0x00880000`. Não há referências de código a endereços RAM acima de `0x00880000`. O vetor de reset e a FIRM stage usam a região `0x00800000–0x00804FFF`.
- **Impacto:** Rockbox precisa de RAM comparável aos targets existentes; o menor documentado possui 2 MB. Com 512 KiB, Rockbox completo é inviável. Espaço livre estimado para um payload de SD Boot: ~216 KiB (descontando stack/heap do sistema).
- **Confiança:** PROVÁVEL — evidência indireta sólida, mas sem confirmação direta de registrador de memória.

### 2.4 Flash

- **Quanta flash interna?**  
  2 MiB (0x00000000–0x001FFFFF), confirmado pelo dump.
- **Como é organizada?**  
  - `0x00000000–0x00007FFF`: Bootloader (≈32 KB).
  - `0x00008000–0x0000BFFF`: FIRM stage (≈16 KB).
  - `0x0000C000–0x001FFFFF`: Firmware principal, recursos, fontes, imagens.
- **Confiança:** PROVÁVEL.

### 2.5 Bootloader

- **Como o bootloader funciona?**  
  Lê 4 KiB do setor 0 da flash para `0x00800000` (FIRM stage), verifica algo e executa com `blx r6` apontando para `0x00804C01`.
- **Pode carregar do SD?**  
  Sim, para o arquivo `0:\update.up`, via função em `0x00827850`.
- **Pode carregar um sistema alternativo do SD?**  
  Não nativamente. Seria necessário um patch no FIRM stage ou no bootloader.
- **Confiança:** PROVÁVEL.

### 2.6 SD Boot (carregar kernel do SD)

- **É possível?**  
  Tecnicamente sim. Existem duas abordagens:
  1. **Patch FIRM stage:** modificar o stage intermédio para carregar um binário maior do SD para RAM e saltar.
  2. **Patch bootloader:** substituir o bootloader por um custom loader que lê o SD.
- **Qual é mais segura?**  
  Patch FIRM stage — o bootloader original permanece intacto como fallback.
- **Risco:** brick se o stage modificado estiver corrompido, mas recovery via USB/ISP pode existir.
- **Confiança:** PROVÁVEL (com engenharia reversa adicional).

### 2.7 Rockbox

- **O hardware atende aos requisitos mínimos do Rockbox?**  
  CPU: sim. RAM: **não** (512 KiB << 2 MB do menor target conhecido). Flash: sim para um build mínimo. Drivers: inexistentes.
- **Porte completo é viável?**  
  **Não.** Mesmo que seja possível carregar código do SD, a RAM insuficiente impede execução do Rockbox completo.
- **Subset do Rockbox é viável?**  
  Teoricamente possível, mas exige reescrever drivers de áudio/DMA/display/botões do zero sem datasheet. Não justificável frente ao redesign do firmware original.
- **Confiança:** PROVÁVEL.

### 2.8 Áudio

- **Qual é o codec / DAC?**  
  Nome do chip não identificado. Forte evidência de codec/DAC integrado ao SoC SL6801. Middleware proprietário `audio_crab` gerencia play/record/EQ/ASRC.
- **É possível portar sem reescrever o codec?**  
  Não — Rockbox precisa de driver próprio. Sem datasheet do codec, isso exige engenharia reversa extensiva.
- **Confiança:** PROVÁVEL (integração) / NÃO RESOLVIDO (identidade do chip).

### 2.9 Display

- **Qual é o controlador?**  
  Detectados `st7789s_lcd_init` e `gc9106_lcd_init`. Formato RGB565. O firmware usa LVGL 8. Resolução exata não determinada.
- **É portável?**  
  Sim, driver SPI pode ser adaptado de outras plataformas, mas a interface física ainda não foi mapeada.
- **Confiança:** PROVÁVEL.

### 2.10 Botões

- **Como funcionam?**  
  Dispositivos `/dev/key_io` e `/dev/key_onoff`. Framework `watch_key_*` gerencia estados (idle, work, sleep, wake, poweroff). Leitura provavelmente via ADC (`keyad`). Botões identificados: power, onoff, volume_up, volume_down, left, right, enter, back, record.
- **É portável?**  
  Sim, requer apenas mapeamento de GPIO/ADC.
- **Confiança:** PROVÁVEL.

### 2.11 Riscos de brick

- **O que pode brickar o dispositivo?**  
  - Escrever bootloader corrompido.
  - Firmware com tamanho/offset errado.
  - Perda de energia durante flash.
  - Checksum inválido se houver validação.
- **Existe recovery?**  
  USB recovery foi usado para o dump (`flash_id`, `read_flash`). Método de recovery do fabricante pode existir mas não está documentado.
- **Confiança:** PROVÁVEL.

---

## 3. Veredicto por iniciativa

| Iniciativa | Viabilidade | Justificativa |
|---|---|---|
| **SD Boot de firmware customizado** | 🟡 **Viável com engenharia reversa** | Primitivas existem; patch no FIRM stage é o caminho mais seguro. Payload limitado a ~216 KiB de RAM livre. |
| **Rockbox completo** | 🔴 **Inviável** | RAM é 512 KiB, abaixo do menor target conhecido do Rockbox (2 MB). Drivers inexistentes. |
| **Subset Rockbox (motor de áudio + UI mínima)** | 🟠 **Altamente improvável** | Requer RE completa de codec/DMA/display/botões sem datasheet; RAM ainda é gargalo. |
| **OpenPod como redesign do firmware original** | 🟢 **Mais viável** | Preserva drivers existentes; altera apenas recursos, GUI e fluxos de navegação. |

---

## 4. Decisões pendentes

Antes de prosseguir com qualquer patch ou PoC de SD Boot, é necessário resolver:

1. ✅ **Tamanho total da SRAM** — resolvido para 512 KiB (PROVÁVEL).
2. **Mapeamento do controlador SD / DMA** — não crítico se reaproveitar as funções FatFs do bootloader, mas necessário para drivers próprios.
3. **Codec/DAC e I2S** — essencial para qualquer sistema alternativo; não necessário para redesign OpenPod.
4. **Método de recovery do dispositivo** — essencial para mitigar risco de brick.
5. **Resolução exata do display** — importante para adaptar o Design System.

---

## 5. Recomendação

A recomendação deste estudo é:

1. **Não prosseguir com porte completo do Rockbox** — inviável por RAM insuficiente.
2. **Manter o OpenPod focado em redesign do firmware YP3 original** para Fase 1.
3. **Prosseguir com SD Boot via patch do FIRM stage** apenas como linha de pesquisa paralela de baixo risco, começando com um payload mínimo (ex: piscar LED / mostrar tela colorida).
4. **Documentar as descobertas** para que engenheiros futuros possam retomar a investigação sem refazer o trabalho.

---

## 6. Glossário de confiança

| Termo | Significado |
|---|---|
| **CONFIRMADO** | Evidência direta no firmware ou hardware. |
| **PROVÁVEL** | Múltiplas evidências convergentes, mas sem confirmação final. |
| **HIPÓTESE** | Plausível, requer mais investigação. |
| **NÃO RESOLVIDO** | Sem dados suficientes. |

---

## Referências

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
- `ROCKBOX.md`
- `ROCKBOX_MATRIX.md`
- `UNKNOWN.md`
