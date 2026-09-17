# ANDROMEDA — ROCKBOX_MATRIX

## Matriz de compatibilidade GN-438 × Rockbox

---

## 1. Legenda

| Status | Significado |
|---|---|
| ✅ SIM | Evidência direta de compatibilidade |
| 🟡 PROVÁVEL | Várias evidências convergentes |
| ⚠️ HIPÓTESE | Plausível, mas não comprovado |
| ❓ NÃO RESOLVIDO | Não investigado ou sem dados |
| ❌ NÃO | Evidência de incompatibilidade |

---

## 2. Matriz

| Requisito | Rockbox precisa | GN-438 tem | Evidência | Status | Dificuldade |
|---|---|---|---|---|---|
| **CPU** | ARM/MIPS 32-bit | ARMv7-M Thumb-2 + FPU | Instruções no firmware | ✅ SIM | Baixa |
| **RAM mínima** | 2 MB (menor target documentado: Archos Jukebox), ~4 MB+ (targets modernos) | **hipótese forte: 512 KiB** | Heap LVGL em `0x00876000`–`0x00880000` | 🟡 PROVÁVEL | **CRÍTICA** |
| **Bootloader** | Carrega Rockbox para RAM | Carrega 4 KiB da FIRM para RAM; não do SD | Disassembly | 🟡 PROVÁVEL (com patch) | Alta |
| **SD Boot** | Carregar binário do SD | Primitivas FatFs presentes | `f_mount`, `f_open`, `f_read` | 🟡 PROVÁVEL | Alta |
| **Interrupções / timers** | Systick, IRQs | Cortex-M tem NVIC | Arquitetura | ⚠️ HIPÓTESE | Média |
| **LCD** | Driver 128×160 RGB565 | GC9106 (FIRM) / ST7789S (boot) | Strings no binário | 🟡 PROVÁVEL | Média |
| **Buttons** | Mapeamento de botões | Parcialmente mapeado via LVGL | `BUTTON_ANALYSIS.md` | 🟡 PROVÁVEL | Média |
| **Storage** | Driver SD + filesystem | FatFs presente; camada física não mapeada | Strings e sdupdate | 🟡 PROVÁVEL | Alta |
| **Áudio / codec** | I2S/DAC + codec | `audio_crab`, múltiplos formatos | Strings e paths | ❓ NÃO RESOLVIDO | **CRÍTICA** |
| **DMA** | Para áudio/SD/LCD | Não mapeado | — | ❓ NÃO RESOLVIDO | Alta |
| **Power / PMU** | Bateria, sleep, wake | PMU reg `0x23` usado para flag | Disassembly | ⚠️ HIPÓTESE | Média |
| **RTC** | Relógio | Não confirmado | — | ❓ NÃO RESOLVIDO | Média |
| **USB** | Stack USB | Modo recovery/documentado | `smartlink_flash` | 🟡 PROVÁVEL | Média |
| **Bluetooth** | Stack + chip | Perfis A2DP/AVRCP/HFP identificados | Strings | ❓ NÃO RESOLVIDO | Alta |
| **FM** | Sintonizador | `/dev/fm`, `fm_init` | Strings | ❓ NÃO RESOLVIDO | Média |
| **Threading** | Scheduler próprio ou RTOS | FreeRTOS no firmware original | Strings | ⚠️ HIPÓTESE | Alta |
| **Framebuffer** | Acesso direto ou via driver | 128×160 RGB565 | Imagens no binário | ✅ SIM | Baixa |

---

## 3. Itens críticos

Os itens que mais impactam a viabilidade:

1. **RAM** — se confirmado 512 KiB, Rockbox completo é inviável (menor target documentado: 2 MB).
2. **Áudio / codec** — sem áudio, não é player.
3. **SD controller físico** — sem leitura de SD, não há SD Boot.
4. **DMA** — essencial para áudio fluido.

---

## 4. Viabilidade por subsistema

| Subsistema | Viabilidade | Nota |
|---|---|---|
| CPU / boot | 🟢 Viável | ARM compatível |
| SD Boot (técnico) | 🟡 Viável com engenharia reversa | Primitivas existem |
| LCD | 🟡 Viável com engenharia reversa | Driver provável |
| Botões | 🟡 Viável | Mapeamento parcial |
| Áudio | ❓ Indeterminado | Maior desafio |
| Rockbox completo | 🔴 Inviável | RAM 512 KiB abaixo do menor target documentado (2 MB); drivers inexistentes |
| Subset do Rockbox (motor de áudio) | 🟡 Talvez viável | Depende de codec/DMA |

---

## 5. Conclusão da matriz

O GN-438 é compatível com a **CPU** do Rockbox, mas a **RAM** e a **ausência de drivers** são gargalos intransponíveis. Com a hipótese forte de **512 KiB**, um porte completo do Rockbox é **inviável** — o menor target documentado possui 2 MB. Um subset focado em reprodução de áudio pode ser viável, mas exigiria engenharia reversa extensiva do codec/DMA.
