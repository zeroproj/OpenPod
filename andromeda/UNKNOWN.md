# ANDROMEDA — UNKNOWN

## Hipóteses abertas e como confirmar

---

## 1. P0 — bloqueiam a arquitetura

### 1.1 Tamanho total da SRAM ✅ RESOLVIDO

- **Pergunta:** Quantos KiB de RAM física o GN-438 possui?
- **Resposta:** 512 KiB (`0x00800000`–`0x00880000`), hipótese forte baseada no heap LVGL terminando em `0x00880000`.
- **Status:** Movido para `MEMORY.md` como PROVÁVEL.

### 1.2 Método seguro de SD Boot

- **Pergunta:** É possível implementar SD Boot sem modificar o bootloader?
- **Hipótese:** Sim, via hook na FIRM que verifica SD e salta para código carregado.
- **Evidência:** A FIRM pode executar código arbitrário; pode desativar interrupções e saltar.
- **Contra-evidência:** Não testado; depende de reinicialização completa do hardware.
- **Como confirmar:**
  - Criar um pequeno payload de prova.
  - Carregar via FIRM modificada e observar execução.
- **Impacto:** Determina risco de brick.

### 1.3 Se o bootloader pode ser estendido

- **Pergunta:** Existe espaço no bootloader para adicionar código?
- **Hipótese:** Não há espaço significativo; o bootloader vai até `0x0000C94C` e depois há padding até `0x0000D000` (~1.700 bytes).
- **Evidência:** Mapa da flash.
- **Contra-evidência:** O padding pode ser utilizável.
- **Como confirmar:** Verificar se o bootloader lê/executa código na faixa de padding.
- **Impacto:** Se não houver espaço, patch no bootloader exigiria redimensionamento.

---

## 2. P1 — importantes, mas não bloqueantes

### 2.1 Identidade do chip ✅ RESOLVIDO

- **Pergunta:** Qual é o SoC real do GN-438?
- **Resposta:** Marcação física `Jointbees MP3 V57J21B6A0`; firmware identifica como `SL6801`; fabricante Shenzhen Shenju Technology.
- **Status:** Movido para `SOC.md` como CONFIRMADO/PROVÁVEL.

### 2.2 Núcleo Cortex-M exato

- **Pergunta:** É Cortex-M4F, M7, M33 ou outro?
- **Hipótese:** Cortex-M4F (FPU + Thumb-2 + frequência típica de players).
- **Evidência:** Instruções VFP, Thumb-2, ausência de TrustZone óbvia.
- **Como confirmar:** Ler registrador `CPUID` (endereço `0xE000ED00`) via payload ou encontrar no código.
- **Impacto:** Toolchain e flags de compilação.

### 2.3 Frequência de clock

- **Pergunta:** Qual a frequência do CPU?
- **Hipótese:** 100–400 MHz (típico de SoCs de áudio).
- **Como confirmar:** Analisar configuração de PLL no bootloader; medir via timer.
- **Impacto:** Performance de áudio e UI.

### 2.4 Codec e interface de áudio

- **Pergunta:** Qual o codec e como ele é conectado (I2S, PWM, DAC interno)?
- **Hipótese:** I2S para codec externo ou DAC interno do SL6801.
- **Evidência:** Strings `audio_crab`, paths de compilação, suporte a múltiplos formatos.
- **Como confirmar:** RE do driver de áudio; identificar registradores I2S/DAC.
- **Impacto:** Maior desafio de um porte Rockbox.

### 2.5 Driver do LCD

- **Pergunta:** GC9106 ou ST7789S?
- **Hipótese:** Ambos existem no binário; GC9106 é usado pela FIRM, ST7789S pelo bootloader (ou vice-versa).
- **Evidência:** Strings `gc9106_lcd_init` e `st7789s_lcd_init`.
- **Como confirmar:** Testar comandos de init em hardware; rastrear chamadas no bootloader.
- **Impacto:** Driver de display para Rockbox.

### 2.6 SD controller físico

- **Pergunta:** Qual o controller de SD/MMC e seu endereço base?
- **Hipótese:** Controller SDIO proprietário do SL6801, acessado pela camada FatFs.
- **Evidência:** Strings de erro `sdio(e):`, `HAL_SD_Init_new`, FatFs.
- **Como confirmar:** RE das funções `f_read`/`f_open` até os registradores físicos.
- **Impacto:** Essencial para drivers próprios; não crítico se reaproveitar o bootloader.

### 2.7 Identidade do codec/DAC

- **Pergunta:** Qual o chip codec/DAC e como é controlado?
- **Hipótese:** Codec integrado ao SoC SL6801; controlado por registradores internos.
- **Evidência:** Ausência de nomes de codec externos; strings `audio_crab`, `AMIC1_GAIN`, `spk wire volume`.
- **Como confirmar:** RE do driver `/dev/audio0` e mapear registradores de áudio.
- **Impacto:** Essencial para qualquer sistema alternativo; não necessário para redesign OpenPod.

### 2.8 Resolução do display

- **Pergunta:** Qual a resolução exata do painel?
- **Hipótese:** 240×320 (ST7789S) ou 128×160 (GC9106).
- **Evidência:** Strings `st7789s_lcd_init` e `gc9106_lcd_init`; formato RGB565.
- **Como confirmar:** Analisar comandos de init; inspecionar estrutura `lv_disp_drv_t` em RAM.
- **Impacto:** Importante para adaptar o Design System.

---

## 3. P2/P3 — funcionalidades futuras

### 3.1 Bluetooth

- **Pergunta:** Qual chip e stack Bluetooth?
- **Hipótese:** Stack proprietário do SoC; chip possivelmente integrado.
- **Impacto:** P2 — não bloqueia primeira avaliação.

### 3.2 FM

- **Pergunta:** Qual sintonizador FM?
- **Hipótese:** Chip não identificado.
- **Impacto:** P2/P3.

### 3.3 USB

- **Pergunta:** O modo "update from pc" enumera corretamente?
- **Hipótese:** Sim, derivado do código.
- **Como confirmar:** Testar somente leitura.
- **Impacto:** Rede de segurança.

---

## 4. Como priorizar

A ordem de investigação recomendada:

1. ✅ **Identidade do chip** — resolvido (Jointbees MP3 V57J21B6A0 / SL6801).
2. ✅ **Tamanho da RAM** — resolvido (512 KiB, PROVÁVEL).
3. **Método de SD Boot seguro** — P0.
4. **Núcleo Cortex-M exato** — P1.
5. **Resolução do display** — P1 (importante para OpenPod).
6. **SD controller físico** — P1 (para drivers próprios).
7. **Áudio (codec/I2S)** — P1 (para sistemas alternativos).
8. Bluetooth, FM, USB — P2/P3.

---

## 5. Registro de hipóteses para não perder

Toda hipótese acima deve ser:
- Testada.
- Confirmada/refutada.
- Movida para o documento apropriado (`MEMORY.md`, `BOOT.md`, etc.) com a classe correta.
- Se não resolvida, permanecer aqui com plano de confirmação.
