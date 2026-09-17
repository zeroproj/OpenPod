# ANDROMEDA — PERIPHERAL REGISTER SCAN

## Mapeamento automatizado de acessos a periféricos no GN-438

---

## 1. Metodologia

- Base de análise: `firmware/ORIGINAL/GN438_original.bin` (2 MiB, base de flash `0x00C00000`).
- Usada lista de inícios de função de `analysis/funcmap.json` (3.365 entradas).
- Cada função foi desmontada com Capstone em modo Thumb-2 por até 2 KiB.
- Foram coletados todos os `LDR Rn, [PC, #imm]` cujo literal aponta para a faixa `0x40000000..0x4FFFFFFF` (periféricos AHB/APB) ou `0xE0000000..0xE00FFFFF` (registradores internos Cortex-M).
- O endereço do literal foi lido como little-endian word e agrupado por função.

> **Cuidado**: a tabela abaixo contém endereços que ainda precisam de confirmação. Valores alinhados a 0x1000/0x100 e com múltiplas referências são os mais confiáveis.

---

## 2. Registradores internos do Cortex-M (confirmados)

| Endereço | Registrador ARMv7-M | Evidência | Confiança |
|---|---|---|---|
| `0xE000E010` | SysTick CSR | acessado no bootloader | CONFIRMADO |
| `0xE000E100` | NVIC ISER0 | acessado no bootloader | CONFIRMADO |
| `0xE000ED00` | SCB base / CPUID | referência base para fault status | CONFIRMADO |
| `0xE000ED04` | ICSR | usado em rotinas de sistema | CONFIRMADO |
| `0xE000ED14` | CCR | usado no bootloader | CONFIRMADO |
| `0xE000ED88` | CPACR (habilita CP10/CP11) | setado com `0xF00000` em `0x00CF5B66` | CONFIRMADO |

A escrita em `0xE000ED88` com bits 20-23 (`CP10/CP11 = 0b11`) prova que o firmware habilita a FPU VFP. Isso reforça a classificação do núcleo como **Cortex-M4F** (ver `CPU.md`).

---

## 3. Bases de periféricos detectados (0x40000000..0x4FFFFFFF)

A tabela lista endereços base alinhados a 0x1000 ou 0x100, com pelo menos 2 funções referenciando.

| Base | #refs | #funcs | Hipótese | Motivação |
|---|---|---|---|---|
| `0x40000060` | 6 | 6 | — | acesso muito baixo, possivelmente flag/proxy |
| `0x40001000` | 6 | 6 | Timer / watchdog | faixa típica de timers |
| `0x40003000` | 12 | 12 | Timer secundário | usado por funções de timer em `0x00C41xxx` |
| `0x40009000` | 565 | 55 | **UART/SPI mestre** | alto tráfego, debug provável |
| `0x40009100` | 7 | 3 | Extensão do `0x40009000` | mesmo cluster |
| `0x40009400` | 4 | 4 | Extensão do `0x40009000` | mesmo cluster |
| `0x40009600` | 4 | 4 | Extensão do `0x40009000` | mesmo cluster |
| `0x40010000` | 51 | 43 | **Timer / PWM** | muitas funções, possivelmente PWM |
| `0x40010100` | 9 | 9 | Timer/PWM secundário | próximo a `0x40010000` |
| `0x40010200` | 9 | 9 | Timer/PWM secundário | próximo a `0x40010000` |
| `0x40011000` | 20 | 15 | **Timer/PWM terciário** | cluster PWM (`/dev/pwm_ch*`) |
| `0x40020000` | 24 | 21 | **DMA / SD host** | usado por funções de SDIO em `0x00D80xxx` |
| `0x40027000` | 17 | 17 | **Flash/Quad-SPI controller** | usado por `flash_*` em `0x00C43xxx` |
| `0x40030000` | 24 | 18 | **SDIO / DMA** | próximo a `0x40020000`, usado por SDIO |
| `0x40038000` | 4 | 4 | Extensão de DMA/SD | funções `0x00D80xxx` |
| `0x40040300` | 3 | 3 | — | usado por `0x00D64Exx` (LCD?) |
| `0x40070000` | 13 | 7 | **PMU / System Control** | acessado no bootloader init |
| `0x40080000` | 150 | 41 | **Clock / Reset / SCU** | muito usado no bootloader init |
| `0x40081000` | 30 | 30 | **Clock / Reset secundário** | mesmo cluster de `0x40080000` |
| `0x40085000` | 313 | 65 | **GPIO / pinmux** | o maior cluster de pinos |
| `0x40089000` | 12 | 12 | I2C/SPI/aux | usado por funções de baixo nível |
| `0x4008A000` | 11 | 11 | I2C/SPI/aux | próximo a `0x40089000` |
| `0x40090000` | 34 | 17 | **I2S / Audio DAC** | usado por `0x00D9FCxx` (áudio) |
| `0x40092000` | 12 | 12 | I2S/aux | próximo a `0x40090000` |
| `0x40095000` | 9 | 9 | **ADC** | usado por `0x00D7C1xx` (kadc?) |
| `0x40096000` | 7 | 7 | **ADC** | próximo a `0x40095000` |
| `0x40099000` | 21 | 21 | I2C/SPI/aux | usado por `0x00CF6Fxx` |
| `0x4009B000` | 36 | 14 | I2C/SPI/aux | usado por `0x00D7C6xx` |
| `0x400D0000` | 117 | 27 | **LCD controller** | usado por funções de display |
| `0x400D1000` | 64 | 21 | **LCD controller extensão** | próximo a `0x400D0000` |
| `0x40240000` | 30 | 15 | **Audio / I2S** | usado por `0x00D6B1xx` |
| `0x40300000` | 57 | 16 | **Audio / I2S** | usado por `0x00D9FCxx` / `0x00D9FDxx` |
| `0x40A00000` | 22 | 22 | **USB device** | usado por `0x00D407xx` (usbd) |
| `0x40C00000` | 43 | 22 | **USB device / PHY** | próximo a `0x40A00000` |
| `0x40FE0000` | 19 | 19 | **ADC / misc** | usado por `0x00D7CDxx` |
| `0x41100000` | 44 | 22 | **USB host/otg** | usado por `0x00D407xx` |

> **Nota**: os endereços `0x43500000` e `0x40FE0000` aparecem com poucas funções e podem ser constantes de máscara; foram mantidos por alinhamento.

---

## 4. Identificações mais fortes

### 4.1 GPIO — `0x40085000`

- É o periférico mais referenciado do firmware (313 acessos, 65 funções).
- Aparece tanto no bootloader quanto na FIRM.
- Inclui acessos com offsets como `0x40085074`, `0x40085084`, etc.
- Provável base do controlador de GPIO/pinmux do SL6801.

### 4.2 Clock/Reset — `0x40080000` e `0x40081000`

- `0x40080000` é o segundo mais referenciado (150 acessos).
- Usado intensivamente durante o `startup_main_begin` do bootloader.
- Inclui offsets `0x40080030`, `0x40080064`, `0x40080074`, `0x400800E8`.
- `0x40081000` provavelmente é um segundo bloco de clock/reset.

### 4.3 SDIO — `0x40020000`, `0x40030000`, `0x40038000`

- Usado pelas funções que contêm strings `sdio(i):...` e `sdio(e):...`.
- `0x40020000` e `0x40030000` são candidatos ao host controller SDIO/SDMMC.
- `0x40038000` pode ser DMA associado ao SD.

### 4.4 Display/LCDC — `0x400D0000` e `0x400D1000`

- Funções de display e `gc9106_lcd_init` acessam esta faixa.
- `0x40040300`/`0x40040304`/`0x40040308` também aparecem em funções de LCD.

### 4.5 ADC (teclas) — `0x40095000`/`0x40096000`

- O firmware cria dispositivos `/dev/kadc_ch0`..`/dev/kadc_ch5`.
- As funções em `0x00D7C1xx`/`0x00D7C6xx` acessam `0x40095000` e `0x40096000`.
- Forte candidato ao ADC usado pelo teclado resistivo.

### 4.6 PWM — `0x40010000`..`0x40011000`

- O firmware abre `/dev/pwm_ch0`..`/dev/pwm_ch5`.
- As faixas `0x40010000`, `0x40010100`, `0x40010200`, `0x40011000` são típicas de timers/PWM.

### 4.7 USB — `0x40A00000`, `0x40C00000`, `0x41100000`

- Usado por funções que contêm strings `usbd`, `usb_in`, `usb_status`.
- `0x40A00000` provavelmente é a base do USB device controller.

### 4.8 Audio — `0x40090000`, `0x40240000`, `0x40300000`

- `0x40090000` e `0x40300000` são acessados por funções do driver `audio_crab`.
- `0x40240000` também está no caminho de áudio.

---

## 5. Mapeamento de offsets dentro das bases (2026-09-16)

Para as bases mais promissoras, foram rastreados os **offsets específicos**
acessados pelo firmware. O rastreamento é conservador: detecta acessos via
`LDR [PC, #imm]` (literal pool) e acessos relativos a um registrador que
carregou a própria base. Acessos que copiam a base para outro registrador
antes de usar offsets podem não aparecer.

### 5.1 GPIO / pinmux — base `0x40085000`

Offsets acessados:

| Offset | Tipo | #refs | #funcs | Observação |
|---|---|---|---|---|
| `+0x000` | leitura (literal) | 33 | 22 | base carregada diretamente |
| `+0x060` | escrita relativa | 2 | 2 | |
| `+0x070` | leitura relativa | 3 | 1 | |
| `+0x074` | leitura/escrita | 5 | 3 | também carregado via literal |
| `+0x078` | leitura/escrita | 2 | 1 | |
| `+0x080` | leitura/escrita | 3 | 1 | |
| `+0x084` | leitura (forte) | 11 | 4 | |
| `+0x088` | leitura | 1 | 1 | |
| `+0x098` | leitura/escrita | 21 | 4 | |
| `+0x0A0` | leitura/escrita | 2 | 1 | |
| `+0x0A4` | leitura/escrita | 13 | 1 | |
| `+0x0AC` | escrita | 1 | 1 | |
| `+0x0B0` | escrita | 1 | 1 | |
| `+0x0B4` | escrita | 1 | 1 | |
| `+0x0B8` | escrita | 1 | 1 | |
| `+0x0BC` | escrita | 2 | 2 | |
| `+0x0C0` | escrita | 1 | 1 | |
| `+0x0D0` | leitura/escrita | 11 | 2 | |
| `+0x0D4` | leitura/escrita | 3 | 1 | |
| `+0x0D8` | leitura/escrita | 6 | 3 | |
| `+0x0DC` | escrita | 1 | 1 | |
| `+0x0E0` | escrita | 1 | 1 | |
| `+0x0E4` | escrita | 1 | 1 | |
| `+0x0E8` | leitura/escrita | 3 | 1 | |
| `+0x0EC` | leitura/escrita | 3 | 2 | |
| `+0x100` | leitura/escrita | 4 | 1 | |
| `+0x104` | leitura/escrita | 8 | 2 | |
| `+0x108` | escrita | 1 | 1 | |
| `+0x10C` | leitura | 1 | 1 | |
| `+0x110` | leitura | 1 | 1 | |

> **Padrão observado:** os offsets estão agrupados em blocos de 0x10/0x20
> bytes, sugerindo registradores de 32 bits com espaçamento regular. Os
> offsets baixos (`0x00`–`0x0C`) não aparecem no rastreamento, o que pode
> indicar que o acesso a esses registradores é feito por outro mecanismo
> (ex: copiando a base para outro registrador) ou que eles não são usados.

### 5.2 Clock / reset — bases `0x40080000` e `0x40081000`

`0x40080000`:

| Offset | Tipo | #refs | #funcs |
|---|---|---|---|
| `+0x000` | leitura/escrita | 18 | 5 |
| `+0x010` | leitura/escrita | 2 | 1 |
| `+0x014` | leitura/escrita | 5 | 1 |
| `+0x030` | leitura (literal) | 4 | 3 |
| `+0x040` | leitura/escrita | 17 | 4 |
| `+0x048` | leitura/escrita | 4 | 2 |
| `+0x064` | leitura (literal) | 2 | 2 |
| `+0x074` | leitura (literal) | 2 | 2 |
| `+0x0E8` | leitura (literal) | 2 | 2 |

`0x40081000`:

| Offset | Tipo | #refs | #funcs |
|---|---|---|---|
| `+0x000` | leitura/escrita | 4 | 2 |
| `+0x024` | leitura/escrita | 2 | 1 |
| `+0x02C` | leitura/escrita | 2 | 1 |
| `+0x404` | leitura (literal) | 1 | 1 | usado por função em `0x00D7C6A4` |

### 5.3 LCDC — bases `0x400D0000` e `0x400D1000`

`0x400D0000`:

| Offset | Tipo | #refs | #funcs |
|---|---|---|---|
| `+0x000` | leitura/escrita | 10 | 4 |
| `+0x008` | leitura/escrita | 9 | 3 |
| `+0x00C` | leitura/escrita | 5 | 4 |
| `+0x020` | leitura (literal) | 2 | 2 |
| `+0x040` | leitura (literal) | 1 | 1 |
| `+0x060` | leitura (literal) | 1 | 1 |

`0x400D1000`:

| Offset | Tipo | #refs | #funcs |
|---|---|---|---|
| `+0x000` | leitura/escrita | 14 | 8 |
| `+0x008` | leitura/escrita | 4 | 2 |
| `+0x00C` | leitura/escrita | 4 | 2 |
| `+0x010` | leitura | 3 | 1 |
| `+0x014` | leitura | 1 | 1 |
| `+0x018` | leitura | 1 | 1 |
| `+0x020` | leitura | 1 | 1 |
| `+0x024` | leitura | 1 | 1 |
| `+0x028` | leitura | 1 | 1 |
| `+0x02C` | leitura | 1 | 1 |
| `+0x040` | leitura/escrita | 4 | 4 |
| `+0x044` | leitura | 1 | 1 |
| `+0x050` | leitura | 1 | 1 |
| `+0x05C` | leitura | 1 | 1 |

### 5.4 ADC — bases `0x40095000` e `0x40096000`

O rastreamento simples só encontrou a própria base sendo carregada em
registradores (`0x00D7C660` carrega `0x40095000`; `0x00D7C564` carrega
`0x40096000`). Os registradores internos do ADC são acessados através de
estruturas copiadas por `memcpy`/loop, então os offsets individuais ainda
não foram mapeados. Ver `andromeda/INPUT.md` §8.

### 5.5 SDIO — bases `0x40020000`, `0x40030000`, `0x40038000`

`0x40020000`:

| Offset | Tipo | #refs | #funcs |
|---|---|---|---|
| `+0x000` | leitura/escrita | 27 | 4 |
| `+0x00C` | leitura (literal) | 3 | 3 |
| `+0x010` | leitura (literal) | 1 | 1 |
| `+0x018` | leitura (literal) | 5 | 1 |
| `+0x01C` | leitura (literal) | 3 | 3 |
| `+0x020` | leitura (literal) | 3 | 3 |
| `+0x030` | leitura (literal) | 4 | 4 |
| `+0x040` | leitura (literal) | 1 | 1 |
| `+0x044` | leitura (literal) | 1 | 1 |
| `+0x080` | leitura (literal) | 1 | 1 |
| `+0x0C0` | leitura (literal) | 1 | 1 |
| `+0x1B0` | leitura (literal) | 1 | 1 |
| `+0x1E4` | leitura (literal) | 1 | 1 |

`0x40030000`:

| Offset | Tipo | #refs | #funcs |
|---|---|---|---|
| `+0x000` | leitura/escrita | 10 | 4 |
| `+0x020` | leitura (literal) | 4 | 3 |
| `+0x2B0` | leitura (literal) | 12 | 4 |
| `+0x2FC` | leitura (literal) | 1 | 1 |
| `+0x304` | leitura (literal) | 2 | 2 |
| `+0x534` | leitura (literal) | 1 | 1 |
| `+0xEB8` | leitura (literal) | 1 | 1 |

`0x40038000`:

| Offset | Tipo | #refs | #funcs |
|---|---|---|---|
| `+0x000` | leitura (literal) | 1 | 1 |

> **Observação:** `0x40030000` possui acesso pesado em `+0x2B0`, sugerindo
> registrador de controle de dados/interrupção. `0x40038000` pode ser uma
> porta de DMA ligada ao SD.

### 5.6 Timer / PWM — bases `0x40010000`, `0x40010100`, `0x40010200`, `0x40011000`

`0x40010000` (faixa total acessada: `0x40010000`..`0x4001030C`):

| Offset | Tipo | #refs | #funcs |
|---|---|---|---|
| `+0x000` | leitura/escrita | 12 | 4 |
| `+0x100` | leitura (literal) | 1 | 1 |
| `+0x108` | leitura (literal) | 1 | 1 |
| `+0x120` | leitura (literal) | 3 | 3 |
| `+0x200` | leitura (literal) | 1 | 1 |
| `+0x21C` | leitura (literal) | 1 | 1 |
| `+0x228` | leitura (literal) | 1 | 1 |
| `+0x290` | leitura (literal) | 1 | 1 |
| `+0x298` | leitura (literal) | 1 | 1 |
| `+0x2C8` | leitura (literal) | 1 | 1 |
| `+0x2F0` | leitura (literal) | 1 | 1 |
| `+0x30C` | leitura (literal) | 1 | 1 |

`0x40010100` e `0x40010200` apresentam padrão semelhante, com acessos a
offsets até `+0x30C`. Além disso, ambas as bases também acessam a região
`0x40011000` com offsets grandes (`+0xF00`..`+0xFE4`), o que indica que o
firmware trata `0x40011000` como extensão do mesmo cluster de timers ou
como um quarto timer/PWM.

`0x40011000`:

| Offset | Tipo | #refs | #funcs |
|---|---|---|---|
| `+0x000` | leitura/escrita | 6 | 2 |
| `+0x004` | leitura (literal) | 4 | 4 |
| `+0x008` | leitura (literal) | 3 | 2 |
| `+0x00C` | leitura (literal) | 2 | 2 |
| `+0x010` | leitura (literal) | 1 | 1 |
| `+0x020` | leitura (literal) | 1 | 1 |
| `+0x024` | leitura (literal) | 1 | 1 |
| `+0x02C` | leitura (literal) | 1 | 1 |
| `+0x040` | leitura (literal) | 3 | 3 |
| `+0x044` | leitura (literal) | 1 | 1 |
| `+0x060` | leitura (literal) | 2 | 2 |
| `+0x064` | leitura (literal) | 5 | 5 |
| `+0x080` | leitura (literal) | 3 | 3 |
| `+0x084` | leitura (literal) | 8 | 8 |
| `+0x088` | leitura (literal) | 4 | 4 |
| `+0x0A0` | leitura (literal) | 4 | 4 |
| `+0x0A4` | leitura (literal) | 1 | 1 |
| `+0x0AC` | leitura (literal) | 11 | 11 |
| `+0x0B0` | leitura (literal) | 2 | 2 |
| `+0x0B4` | leitura (literal) | 3 | 3 |
| `+0x0B8` | leitura (literal) | 1 | 1 |
| `+0x0BC` | leitura (literal) | 1 | 1 |
| `+0x0C0` | leitura (literal) | 3 | 3 |
| `+0x0C4` | leitura (literal) | 1 | 1 |
| `+0x0CC` | leitura (literal) | 1 | 1 |
| `+0x0D0` | leitura (literal) | 1 | 1 |
| `+0x0E4` | leitura (literal) | 1 | 1 |

> **Padrão observado:** os blocos `0x40010000`/`0x40010100`/`0x40010200`
> parecem ter registradores espaçados a cada 0x100 bytes, enquanto
> `0x40011000` tem registradores densos a cada 0x04/0x08 bytes. Isso pode
> indicar dois tipos de controlador: timers genéricos (`0x40010x00`) e um
> PWM dedicado (`0x40011000`).

### 5.7 Debug de clock — função `0x00D65840`

Uma função de debug localizada em `0x00D65840` imprime a string:

```text
core pll:%u, cpu pll:%u, cpu0:%u, cpu1:%u, ahb:%u, norf:%u\n
```

Chamadas observadas:

| Endereço chamado | r0 | Uso provável |
|---|---|---|
| `0x008051B0` | 3,4,5 | stub / no-op |
| `0x008051E0` | 3,4,2,0x2A,6,0x2B | leitura/escrita de registradores de clock |
| `0x0080D6CC` | 3,4,5 | conversão/leitura de frequência (código em RAM, não visível estaticamente) |
| `0x00CF7294` | 3,4,5 | leitura de configuração de PLL |

A função calcula ao menos duas frequências por divisão de valores de
ponto flutuante. Os valores `cpu0`, `cpu1`, `ahb` e `norf` vêm diretamente
de `0x008051E0` com índices fixos. Isso confirma que o firmware tem acesso
a leituras de clock e que `0x008051E0` é um helper de acesso a
registradores de clock/SCU.

---

## 6. Falsos positivos conhecidos

- Muitos valores entre `0x46000000` e `0x47FFFFFF` são instruções Thumb-2 (ex: `0x46016823`, `0x47706093`) usadas como máscaras ou constantes, não endereços de periféricos.
- Valores não alinhados a palavra (ímpares) foram descartados.
- Constantes ASCII como `0x424C4154` ('BLAT') aparecem em pools de literais e foram filtradas.

---

## 7. Próximos passos

1. Refinar o rastreamento de registradores para capturar acessos indiretos
   (quando a base é copiada para outro registrador antes do acesso),
   especialmente para ADC.
2. Cruzar offsets de GPIO/clock com as funções de init do bootloader para
   inferir o papel de cada registrador.
3. Cruzar com strings de debug (`/dev/uart*`, `/dev/pwm*`, `/dev/kadc*`,
   `/dev/rtc`, `/dev/lcd`, etc.).
4. Mapear uso dos pinos GPIO para os botões físicos e backlight.
5. Determinar se é possível executar código próprio no ANDROMEDA com este
   mapa de periféricos.
6. Investigar a falha do OpenPod Core 3.1.2 usando este mapa (sem gerar
   novo patch antes da causa raiz ser identificada).

---

## 8. Classificação

| Afirmação | Classe |
|---|---|
| Bases de periféricos em `0x400xxxxx` existem e são acessadas pelo código | CONFIRMADO |
| `0x40085000` é GPIO/pinmux | PROVÁVEL |
| `0x40080000`/`0x40081000` são clock/reset | PROVÁVEL |
| `0x40020000`/`0x40030000` são SDIO/SD host | PROVÁVEL |
| `0x400D0000`/`0x400D1000` são LCDC | PROVÁVEL |
| `0x40095000`/`0x40096000` são ADC | PROVÁVEL |
| `0x40010000`..`0x40011000` são timers/PWM | PROVÁVEL |
| `0x40A00000`/`0x40C00000`/`0x41100000` são USB | PROVÁVEL |
| `0x40090000`/`0x40240000`/`0x40300000` são áudio/I2S | PROVÁVEL |
| Offsets específicos de GPIO (`0x400850xx`) acessados | CONFIRMADO |
| Offsets específicos de clock (`0x400800xx`, `0x400810xx`) acessados | CONFIRMADO |
| Offsets específicos de LCDC (`0x400D00xx`, `0x400D10xx`) acessados | CONFIRMADO |
| Offsets específicos de SDIO (`0x400200xx`, `0x400300xx`) acessados | CONFIRMADO |
| Offsets específicos de PWM/timer (`0x40010xxx`, `0x400110xx`) acessados | CONFIRMADO |
| Função de debug de PLL `0x00D65840` identificada | CONFIRMADO |
| Significado funcional de cada offset | NÃO RESOLVIDO |
| Registradores internos Cortex-M mapeados corretamente | CONFIRMADO |
