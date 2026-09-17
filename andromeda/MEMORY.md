# ANDROMEDA — MEMORY

## Mapa de memória do GN-438

---

## 1. Resumo executivo

| Região | Endereço | Tamanho conhecido | Status |
|---|---|---|---|
| Flash interna (XIP) | `0x00C00000` | 2 MiB mapeados | CONFIRMADO |
| RAM total | `0x00800000`–`0x00880000` | **512 KiB (hipótese forte)** | PROVÁVEL |
| Payload carregável | `0x00820000` | 64 KiB (smartlink_flash) | CONFIRMADO |
| Heap LVGL | `0x00876000` | 40 KiB (`0xA000`) | CONFIRMADO |
| Stack top (bootloader) | `0x0083BE90` | — | CONFIRMADO |
| Stack bottom aprox. | `0x0083BA90` | — | PROVÁVEL |
| Área de dados do bootloader | `0x0082C4AC` em diante | — | PROVÁVEL |
| Carga da FIRM stage | `0x00804C00` | 4 KiB | CONFIRMADO |
| Entry point da FIRM stage | `0x00804C01` | — | CONFIRMADO |
| PSMP (configuração) | `0x001FC000` (flash) | 16 KiB | CONFIRMADO |

---

## 2. Flash interna

### 2.1 Layout

```text
0x00000000 ┌──────────────────────────────────────────────┐
           │ Cabeçalho HLKJ                      0x60 B   │
           │  · load_addr  0x0081FBC0                     │
           │  · entry      0x00820001                     │
           │  · payload_len 0xC8EC                        │
           │  · payload_crc 0x759D (CRC-16/CCITT-FALSE)   │
0x00000060 ├──────────────────────────────────────────────┤
           │ Bootloader — código ARM Thumb-2              │
           │ payload 0xC8EC B, CRC16 0x759D               │
0x0000C94C ├──────────────────────────────────────────────┤
           │ padding                                      │
0x0000D000 ├──────────────────────────────────────────────┤
           │ Tabela de partições (3 entradas ativas)      │
           │ cada entrada: nome(4) + off(4) + size(4)     │
           │              + crc16(4)                      │
0x0000D040 ├──────────────────────────────────────────────┤
           │ padding                                      │
0x0000E000 ├──────────────────────────────────────────────┤
           │ Partição FIRM — 1.647.984 B                  │
           │ CRC-16/CCITT-FALSE = 0x49A6                  │
0x001A0570 ├──────────────────────────────────────────────┤
           │ padding                                      │
0x001A1000 ├──────────────────────────────────────────────┤
           │ Partição TONE — 8.248 B                      │
           │ CRC-16/CCITT-FALSE = 0x9177                  │
0x001A3038 ├──────────────────────────────────────────────┤
           │ ÁREA LIVRE — 364.488 B (0xFF)                │
0x001FC000 ├──────────────────────────────────────────────┤
           │ Partição PSMP — 16.384 B                     │
           │ CRC declarado 0x0000 (não verificado?)       │
0x00200000 └──────────────────────────────────────────────┘
```

### 2.2 XIP (eXecute In Place)

- A flash é mapeada em `0x00C00000`.
- Ponteiros absolutos no código seguem o padrão `0x00Cxxxxx`.
- Apenas os primeiros 4 KiB da FIRM são copiados para RAM; o resto executa diretamente da flash.

---

## 3. RAM

### 3.1 O que sabemos

O bootloader é carregado para `0x0081FBC0`. O stack pointer inicial é `0x0083BE90`.

No reset handler:

```asm
00820028  ldr r0, [pc, #0x18]  ; = 0x0083BE90
0082002A  mov sp, r0
0082002C  ldr r2, [pc, #0x18]  ; = 0x0082C4AC
...
00820036  ldr r3, [pc, #0x14]  ; = 0x0083BA90
00820038  cmp r2, r3
0082003A  blo #0x820030
```

O loop zera a memória de `0x0082C4AC` até `0x0083BA90`. Isso sugere:

- **Stack top**: `0x0083BE90`
- **Stack bottom aproximado**: `0x0083BA90` (área de `0x400` bytes = 1 KiB acima do .bss?)
- **Área .bss do bootloader**: `0x0082C4AC`–`0x0083BA90` (~62 KiB)

### 3.2 Endereços observados na FIRM

A FIRM é carregada em `0x00804C00` (4 KiB). Strings e estruturas de dados da aplicação aparecem em:

```text
0x0081BBC0  — buffer circular de mensagens (MVP)
0x00819C78  — tabelas de fontes em RAM
0x00823D84  — estado de navegação
```

Isso indica que a RAM é usada tanto pelo bootloader quanto pela FIRM.

### 3.3 Tamanho total da RAM — HIPÓTESE FORTE: 512 KiB

A descoberta do heap LVGL forneceu a melhor evidência até agora.

#### 3.3.1 Heap LVGL

Em `lv_mem_init` (`0x00D58100`), o firmware chama:

```asm
00D58102  mov.w r1, #0xa000      ; r1 = 40 KiB
00D58106  ldr   r0, [pc, #0xc]   ; r0 = 0x00876000
00D58108  bl    #0xd59908        ; lv_tlsf_create(heap, size)
```

Isso significa:

- **Heap LVGL inicia em `0x00876000`.**
- **Heap LVGL tem `0xA000` bytes = 40 KiB.**
- **Heap LVGL termina em `0x00880000`.**

#### 3.3.2 Inferência do tamanho total

O heap LVGL termina exatamente em `0x00880000`. Isso sugere fortemente que `0x00880000` é o **topo da RAM física**, pois o heap foi posicionado para usar o final da RAM.

Se o início da RAM é `0x00800000` e o topo é `0x00880000`, o tamanho total é:

> **0x00880000 - 0x00800000 = 0x80000 bytes = 512 KiB**

#### 3.3.3 Evidências de suporte

- Não há referências por `LDR literal` a endereços RAM na faixa `0x00880000`–`0x00900000`.
- O histograma de endereços `0x008xxxxx` mostra concentração abaixo de `0x00880000`.
- Endereços `0x20xxxxxx` e `0x008Fxxxx` encontrados em dados são, na maioria, constantes (tabelas, coeficientes, máscaras), não referências de código a RAM.

#### 3.3.4 Ressalvas

- Não há **prova direta** do tamanho da SRAM (nenhum registrador de controle de memória foi identificado).
- Pode haver RAM adicional mapeada em outra faixa (ex: `0x20000000` padrão Cortex-M) que não foi confirmada.
- O heap LVGL pode ter sido posicionado em `0x00876000` por alinhamento, não porque ocupa o topo.

| Tamanho | Plausibilidade | Observação |
|---|---|---|
| 256 KiB | Possível | Stack top em `0x0083BE90` caberia, mas o heap LVGL em `0x00876000` estaria fora |
| **512 KiB** | **Provável** | Heap LVGL termina em `0x00880000`; sem referências acima |
| 1 MiB | Possível | Requer RAM adicional não mapeada em `0x008xxxxx` |

### 3.4 RAM disponível para um sistema externo

Se um SD loader copiasse um binário para RAM, ele precisaria de:

- Espaço para o binário.
- Stack para o próprio loader.
- Stack para o sistema carregado.
- Heap/buffers.

Com 512 KiB de RAM total e o heap LVGL ocupando 40 KiB no topo, o espaço **teoricamente** disponível para um sistema carregado seria da ordem de centenas de KiB, mas com restrições:

- A região `0x00820000`–`0x0083BE90` é usada pelo bootloader (não pode ser sobrescrita enquanto o bootloader estiver ativo).
- A FIRM stage ocupa `0x00804C00`–`0x00805C00` (4 KiB).
- O heap LVGL ocupa `0x00876000`–`0x00880000` (40 KiB).

Um sistema SD Boot precisaria:
1. Carregar para uma região livre (ex: `0x00840000`–`0x00876000` = 216 KiB, ou após `0x00880000` se houver mais RAM).
2. Configurar seu próprio stack.
3. Evitar colisão com o bootloader até tomar controle total.

---

## 4. Periféricos (endereços parciais)

| Periférico | Endereço | Evidência | Confiança |
|---|---|---|---|
| GPIO/pinmux | `0x40085000` | 313 acessos em 65 funções (bootloader + FIRM) | PROVÁVEL |
| Clock/Reset | `0x40080000`, `0x40081000` | uso massivo no `startup_main_begin` | PROVÁVEL |
| PMU/System Control | `0x40070000` | acessado no bootloader init | PROVÁVEL |
| SPI Flash controller | `0x40027000` | usado por `flash_read`/`flash_write` | PROVÁVEL |
| SDIO/SD host | `0x40020000`, `0x40030000`, `0x40038000` | strings `sdio(i):...` / `sdio(e):...` | PROVÁVEL |
| LCDC | `0x400D0000`, `0x400D1000`, `0x400403xx` | `gc9106_lcd_init`, `/dev/lcd` | PROVÁVEL |
| ADC (teclas) | `0x40095000`, `0x40096000` | `/dev/kadc_ch0`..`/dev/kadc_ch5` | PROVÁVEL |
| PWM | `0x40010000`, `0x40010100`, `0x40010200`, `0x40011000` | `/dev/pwm_ch0`..`/dev/pwm_ch5` | PROVÁVEL |
| UART/SPI debug | `0x40009000` | alto tráfego, possível debug serial | PROVÁVEL |
| Audio I2S/DAC | `0x40090000`, `0x40240000`, `0x40300000` | `audio_crab`, I2S strings | PROVÁVEL |
| USB device | `0x40A00000`, `0x40C00000` | `/dev/usbd`, `usb_status` | PROVÁVEL |
| USB host/otg | `0x41100000` | `/dev/usb` | PROVÁVEL |
| Timer/watchdog | `0x40001000`, `0x40003000` | funções de timer | PROVÁVEL |
| PMU | registrador `0x23` | `HAL_pmu_sd_update_flag_set` (`docs/UPDATE_MECHANISM.md`) | PROVÁVEL |

Detalhes completos no arquivo `andromeda/PERIPHERAL_REGISTER_SCAN.md`.

---

## 5. Mapa conceitual

```text
┌─────────────────────────────────────┐
│  0x00880000  ← topo da RAM (?)*     │
│  0x00876000  ← heap LVGL (40 KiB)   │
├─────────────────────────────────────┤
│  região livre / buffers (~216 KiB)  │
├─────────────────────────────────────┤
│  0x0083BE90  ← stack top (boot)     │
├─────────────────────────────────────┤
│  .bss / heap do bootloader          │
├─────────────────────────────────────┤
│  0x0081FBC0  ← bootloader em RAM    │
├─────────────────────────────────────┤
│  buffers / filas / estado           │
├─────────────────────────────────────┤
│  0x00804C00  ← FIRM stage (4 KiB)   │
├─────────────────────────────────────┤
│  0x00800000  ← início da RAM        │
└─────────────────────────────────────┘

* topo da RAM = hipótese baseada no heap LVGL terminar em 0x00880000

┌─────────────────────────────────────┐
│  0x00D00000  ← flash XIP (topo)     │
├─────────────────────────────────────┤
│  ...                                │
├─────────────────────────────────────┤
│  0x00C00000  ← flash XIP (base)     │
└─────────────────────────────────────┘
```

---

## 6. Lacunas críticas

| Pergunta | Status | Impacto |
|---|---|---|
| Tamanho total da SRAM | PROVÁVEL (512 KiB) | Define tamanho máximo do sistema SD |
| Endereço final da RAM | PROVÁVEL (`0x00880000`) | Necessário para linker de um novo sistema |
| Regiões reservadas pelo bootloader | PROVÁVEL | Pode colidir com sistema carregado |
| Mapeamento de periféricos | PARCIAL | Necessário para drivers |
| DMA / buffers de áudio | NÃO RESOLVIDO | Afeta RAM disponível |
| RAM extra fora de `0x008xxxxx` | NÃO RESOLVIDO | Pode haver SRAM em `0x20000000` ou outra faixa |

---

## 7. Classificação

| Afirmação | Classe |
|---|---|
| Flash é 2 MiB | CONFIRMADO |
| Flash mapeada em XIP a partir de `0x00C00000` | CONFIRMADO |
| FIRM stage carregado em `0x00804C00` | CONFIRMADO |
| Stack top do bootloader em `0x0083BE90` | CONFIRMADO |
| Heap LVGL em `0x00876000`, 40 KiB | CONFIRMADO |
| Tamanho total da RAM = 512 KiB | PROVÁVEL |
| RAM disponível para sistema externo | PROVÁVEL (com restrições) |
