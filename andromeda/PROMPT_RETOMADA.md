# Prompt de retomada — OpenPod / ANDROMEDA + INPUT

Use este prompt ao reabrir o projeto em outro terminal/opencode para continuar de onde parou.

---

## Contexto geral

Projeto **OpenPod** — reimaginar a interface do player **Iigenai GN-438** (família YP3 / Smartlink / Jointbees, SoC provável **SL6801**).

Firmware original sagrado:

```text
firmware/ORIGINAL/GN438_original.bin
SHA-256: b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f
```

> **Regra absoluta**: nunca modificar, sobrescrever ou apagar o firmware original.

---

## O que já foi concluído

### Firmware / OpenPod Core

- Identificada a causa estrutural da falha do menu **Extras**:
  - O firmware entrega mensagens pelo **número da página corrente**, não pela página que a mensagem diz.
  - `OpenPod Core 3.1.2` tentou corrigir isso com módulo na área livre (`0x00DA5920`) e handler no slot 9 da home, mas **ainda não funcionou no aparelho**.
- **Nenhum patch novo deve ser gerado** até entender exatamente por que a 3.1.2 falhou.

### ANDROMEDA — pesquisa de hardware

Documentos já criados/atualizados:

- `andromeda/README.md` — visão geral e prioridades.
- `andromeda/CPU.md` — CPU provavelmente **ARM Cortex-M4F** (ARMv7-M, Thumb-2, FPU VFP, CPACR `0xE000ED88`).
- `andromeda/MEMORY.md` — flash 2 MiB, bootloader em `0x0081FBC0`, FIRM stage em `0x00804C00`, heap LVGL em `0x00876000`, RAM provavelmente 512 KiB (`0x00800000`–`0x00880000`).
- `andromeda/BOOT.md` — fluxo de boot, `sdupdate`, carregamento da FIRM.
- `andromeda/SOC.md` — chip marcado `Jointbees MP3 V57J21B6A0`, SL6801 provável, sem SDK público.
- `andromeda/DISPLAY.md` — LVGL 8, driver GC9106, resolução provável 128×160, RGB565.
- `andromeda/STORAGE.md` — microSD via SDIO, FatFs no bootloader, rotina `sdupdate` documentada.
- `andromeda/INPUT.md` — `/dev/key_io`, `/dev/key_onoff`, `/dev/kadc_ch*`, máquina de estados, teclas identificadas por strings.
- `andromeda/PERIPHERAL_REGISTER_SCAN.md` — scan automatizado de acessos a periféricos. Bases prováveis mapeadas, offsets específicos de GPIO, clock, LCDC, SDIO, PWM e debug de PLL documentados:
  - GPIO/pinmux: `0x40085000`
  - Clock/Reset: `0x40080000`, `0x40081000`
  - PMU/System Control: `0x40070000`
  - SDIO/SD host: `0x40020000`, `0x40030000`, `0x40038000`
  - LCDC: `0x400D0000`, `0x400D1000`
  - ADC (teclas): `0x40095000`, `0x40096000`
  - PWM: `0x40010000`..`0x40011000`
  - USB device: `0x40A00000`, `0x40C00000`
  - USB host/otg: `0x41100000`
   - Áudio I2S/DAC: `0x40090000`, `0x40240000`, `0x40300000`
   - SPI Flash controller: `0x40027000`
- `andromeda/headers/` — headers C provisórios gerados para GPIO, clock/reset, LCDC, ADC, SDIO e PWM.

---

## Missões pendentes (prioridade)

### 1. INPUT / BOTÕES — alta prioridade

Objetivo: mapear como cada botão físico chega ao firmware.

**Concluído:**

- `keyad_read` localizada em `0x00D21110` (entry point real; função simbólica
  anterior começa em `0x00D2108C`).
- Buffer de evento de tecla em `0x00823D7A` (escritor `0x00D21374`).
- Tabela de conversão `(key_id, event_type)` → código LVGL mapeada
  (`andromeda/INPUT.md` §7.4 e `docs/BUTTON_ANALYSIS.md` §10).
- Inicialização confirmada em `0x00CFC378` registrando callback `0x00CFC7A9`
  para `/dev/kadc_ch1`, `/dev/key_onoff` e `/dev/key_io`.
- Drivers de ADC localizados: `0x00D7C660` (base `0x40095000`) e
  `0x00D7C564` (base `0x40096000`).

**Ainda não resolvido:**

- Qual botão físico gera qual `key_id`.
- Limiares de tensão do teclado ADC (tabelas em RAM `0x00819B0C` e
  `0x00819BCC`, só acessíveis em runtime).
- Se `/dev/kadc_ch0`..`ch5` são todos usados (apenas `ch1` é aberto na
  inicialização observada).

Tarefas pendentes:

1. ✅ Encontrar a função `keyad_read`.
2. ✅ Entender a tabela de conversão `key_id` → código.
3. Identificar quais canais ADC (`/dev/kadc_ch0`..`ch5`) são usados e para quê.
4. Mapear GPIO/ADC para cada botão físico do GN-438.
5. ✅ Documentar em `andromeda/INPUT.md` e `docs/BUTTON_ANALYSIS.md`.

### 2. ANDROMEDA — continuidade obrigatória

Não pare a pesquisa do ANDROMEDA. Próximos alvos:

| Área | % atual | Próximos passos |
|---|---|---|
| CPU | 80% | Confirmar leitura de `CPUID`, frequência/PLL, MPU, `MVFR0`/`MVFR1` |
| MEMORY | 70% | Confirmar tamanho total da RAM, mapear regiões reservadas, buffers de áudio/DMA |
| BOOT | 80% | Detalhar hardware init, caminhos de recuperação, viabilidade real de SD Boot |
| SOC | 80% | Continuar busca por SDK/datasheet/documentação vazada |
| DISPLAY | 65% | Confirmar base do LCDC, encontrar framebuffer, confirmar resolução 128×160 |
| STORAGE | 80% | Bases SDIO/SDMMC e offsets mapeados; falta inferir significado dos registradores |
| INPUT | 70% | `keyad_read` mapeado; falta mapeamento físico e limiares ADC |
| PERIPHERAL REGISTER SCAN | 85% | Offsets de GPIO/clock/LCDC/SDIO/PWM mapeados; headers gerados; falta significado funcional |
| UI / Navegação | 65% | ViewTask identificada como task de UI; 249 páginas listadas; falta mapear tabela de páginas e processamento da ViewTask |
| USB | 45% | Mapear endpoints, DMA e stack USB device/host |
| Áudio | 40% | Mapear I2S/DAC, codec, mixer, buffers |
| Bluetooth | 35% | Mapear stack, profiles, storage de pareamento |
| FM / Vídeo / Fotos | 30% | Apenas strings e UI mapeadas |

Tarefas gerais do ANDROMEDA:

1. ✅ Confirmar offsets dos registradores dentro das bases detectadas
   (GPIO, clock, LCDC, SDIO, PWM feitos; ADC ainda pendente devido a
   acessos indiretos).
2. Cruzar cada base com strings de driver (`/dev/uart*`, `/dev/kadc*`,
   `/dev/pwm*`, `/dev/rtc`, `/dev/lcd`, `/dev/usbd`, `/dev/usb`, `/dev/sd*`).
3. ✅ Gerar headers C provisórios para GPIO, clock/reset, LCDC, ADC, SDIO e PWM
   (`andromeda/headers/`).
4. ✅ Investigar a string de debug `core pll:%u, cpu pll:%u, cpu0:%u, cpu1:%u, ahb:%u, norf:%u` (função em `0x00D65840`); estrutura mapeada, valores só em runtime.
5. Mapear significado funcional dos offsets (especialmente GPIO, clock e SDIO).

---

## Regras absolutas

1. **Nunca modificar** `firmware/ORIGINAL/GN438_original.bin`.
2. **Nunca executar** `erase`, `write_flash`, `write_mem`, `exec` ou equivalentes no hardware sem autorização explícita.
3. Todo trabalho destrutivo ou experimental deve ser feito em cópias em `firmware/WORKING/`.
4. Documentar toda descoberta importante em `andromeda/` ou `docs/`.
5. Diferenciar **CONFIRMADO**, **PROVÁVEL** e **HIPÓTESE**.
6. Não apresentar hipótese como fato.

---

## Arquivos obrigatórios de referência

- `andromeda/PERIPHERAL_REGISTER_SCAN.md`
- `andromeda/CPU.md`
- `andromeda/MEMORY.md`
- `andromeda/BOOT.md`
- `andromeda/SOC.md`
- `andromeda/DISPLAY.md`
- `andromeda/STORAGE.md`
- `andromeda/INPUT.md`
- `docs/BUTTON_ANALYSIS.md`
- `docs/GUI_ANALYSIS.md`
- `analysis/ui/UI_TASK_ARCHITECTURE.md`
- `analysis/ui/page_list.txt`
- `docs/CHANGELOG.md`
- `analysis/funcmap.json`
- `firmware/ORIGINAL/GN438_original.bin`

---

## Primeira ação ao retomar

1. Verificar se `firmware/ORIGINAL/GN438_original.bin` ainda tem o hash correto.
2. Ler este arquivo (`andromeda/PROMPT_RETOMADA.md`) e os documentos de referência.
3. Próximos alvos sugeridos:
   - **UI:** mapear a tabela de páginas consultada pela `ViewTask`
     (`0x00CFE708`) e entender como o índice do menu home se transforma
     em `page_*_create`.
   - **INPUT físico:** rastrear uso dos pinos GPIO/ADC para botões e backlight.
   - **ANDROMEDA:** inferir significado dos offsets de GPIO/clock/SDIO cruzando
     com funções de init do bootloader.
   - **ANDROMEDA:** melhorar rastreamento para capturar acessos indiretos do ADC.

---

*Última atualização: 2026-09-16*
