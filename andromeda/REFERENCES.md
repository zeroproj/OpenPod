# ANDROMEDA — REFERENCES

## Fontes internas e externas

---

## 1. Fontes primárias

### 1.1 Firmware original do GN-438

| | |
|---|---|
| Arquivo | `firmware/ORIGINAL/GN438_original.bin` |
| Tamanho | 2.097.152 bytes |
| SHA-256 | `b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f` |
| Tipo | Análise estática, disassembly, extração de strings |
| Relevância | Base de toda a pesquisa |
| Confiança | ALTA (direto do dispositivo) |

### 1.2 Inspeção física do hardware

| | |
|---|---|
| Marcação do chip | `Jointbees MP3 V57J21B6A0` |
| Marcação da placa | `Modelo: JLR-80852`, `Código de fábrica: F004226`, `Código do lote: 6/26` |
| Método | Leitura direta do silício com dispositivo aberto |
| Relevância | Confirma fabricante e linha de produto |
| Confiança | ALTA

### 1.3 Documentação interna do OpenPod

| Documento | Tema | Relevância |
|---|---|---|
| `docs/FIRMWARE_ANALYSIS.md` | 23 perguntas sobre o firmware | ALTA |
| `docs/FIRMWARE_MAP.md` | Mapa real dos 2 MiB | ALTA |
| `docs/SDUPDATE_ANALYSIS.md` | Disassembly do `boot sdupdate` | ALTA |
| `docs/UPDATE_MECHANISM.md` | Mecanismo de update por SD | ALTA |
| `docs/BUTTON_ANALYSIS.md` | Sistema de entrada | MÉDIA |
| `docs/GUI_ANALYSIS.md` | LVGL, display, fontes | MÉDIA |
| `docs/EXTERNAL_RESEARCH.md` | Pesquisa externa sobre YP3/SL6801 | ALTA |
| `docs/PSMP_FORMAT.md` | Formato da partição de configuração | MÉDIA |
| `docs/REBUILD_VALIDATION.md` | Validação do rebuild | MÉDIA |

### 1.4 smartlink_flash

| | |
|---|---|
| URL | https://github.com/ilyakurdyukov/smartlink_flash |
| Autor | Ilya Kurdyukov |
| Commit travado | `49d51d17e825afbbbc2be7d91d6367674543c2e3` |
| Licença | Nenhuma explícita (AS IS) |
| Relevância | Única ferramenta pública; especificação do `update.up`; opcodes do boot ROM |
| Confiança | ALTA para formato de update; MÉDIA para comportamento de flash |

---

## 2. Fontes externas sobre SD Boot em Cortex-M

| # | Fonte | Autor | Informação | Relevância |
|---|---|---|---|---|
| 2.1 | STMicroelectronics AN — "External memory code execution on STM32F7x0/H750/H7B0/H730" | ST | BootROM model: copia binário de SD/SPI-NOR para RAM e executa | ALTA — prova padrão arquitetural |
| 2.2 | NXP Application Note AN12107 — "How to Enable Boot from Octal SPI Flash and SD Card" | NXP | i.MX RT boot from SD card | ALTA — precedente i.MX RT |
| 2.3 | MCU on Eclipse — "Tutorial: Booting the NXP i.MX RT from Micro SD Card" | Erich Styger | Passo a passo de SD boot em i.MX RT | MÉDIA — método prático |
| 2.4 | NXP/ZLG AN13113 — "A kind of SD card based 2nd bootloader on LPC54600 MCU" | NXP | Segundo bootloader que carrega imagem de SD para SRAM e executa | ALTA — modelo direto de SD loader |
| 2.5 | Stack Exchange — "External code execution on ARM Cortex M" | Comunidade | Cortex-M permite execução de RAM/flash externa | MÉDIA — confirma arquitetural |
| 2.6 | ST Community — "Best way to create SD card → RAM bootloader" | ST Community | Discussão sobre STM32H7R/S | MÉDIA — padrão atual |

---

## 3. Fontes externas sobre Rockbox

| # | Fonte | Informação | Relevância |
|---|---|---|---|
| 3.1 | https://www.rockbox.org/wiki/AgptekRocker.html | AGPtEK Rocker — Ingenic X1000, 32 MB RAM, SD, Bluetooth, LCD SPI | MÉDIA — target com SD e pouca RAM |
| 3.2 | https://git.rockbox.org/cgit/rockbox.git/tree/firmware/export/config/fiiom3k.h | FiiO M3K — X1000, 240×320, SD, codec AK4376 | MÉDIA — target similar em arquitetura |
| 3.3 | https://www.rockbox.org/wiki/CowonD2Info | Cowon D2 — SD como armazenamento principal | MÉDIA — precedente de SD como drive principal |
| 3.4 | Rockbox `tools/configure` | Suporte a Cortex-M7 e configuração de targets | MÉDIA — indica que toolchain ARM é suportada |

---

## 4. Fontes sobre SoCs similares

| # | Fonte | Informação | Relevância |
|---|---|---|---|
| 4.1 | Rockchip RKnanoC datasheet | Cortex-M3, 224 KB SRAM, SD/MMC, LCD, I2S, DAC — perfil muito similar | ALTA — evidência indireta de arquitetura possível |
| 4.2 | ISD9300 datasheet | Cortex-M0, 16 KB SRAM, audio — exemplo de player com pouca RAM | BAIXA — serve como contraste |

---

## 5. Resultados negativos

| Item | Busca | Resultado |
|---|---|---|
| Datasheet SL6801 | múltiplas | Não encontrado |
| SDK SL6801/SL6806 | múltiplas | Não encontrado |
| Firmware oficial YP3 público | múltiplas | Não encontrado |
| Pacote `update.up` público | múltiplas | Não encontrado |
| Porte Rockbox para SL6801/YP3 | múltiplas | Não encontrado |
| Repositório do patch `bunkaich` | GitHub/X | Não encontrado |

---

## 6. Classificação das fontes

| Fonte | Tipo | Confiança |
|---|---|---|
| Firmware original | PRIMÁRIA | ALTA |
| Documentação OpenPod | PRIMÁRIA/SECUNDÁRIA | ALTA |
| smartlink_flash | PRIMÁRIA (código-fonte) | ALTA |
| Datasheets de SoCs similares | PRIMÁRIA | MÉDIA (indireta) |
| Rockbox wiki/git | PRIMÁRIA | ALTA |
| Fóruns e comunidades | SECUNDÁRIA | MÉDIA |
| Busca sem resultado | RESULTADO NEGATIVO | ÚTIL |

---

## 7. Notas

- Nenhuma fonte externa contradiz a análise interna.
- A ausência de SDK/datasheet do SL6801 é o maior gargalo documentado.
- Os precedentes de SD Boot em Cortex-M (ST, NXP) mostram que o padrão arquitetural é viável, mas cada SoC exige implementação específica.
