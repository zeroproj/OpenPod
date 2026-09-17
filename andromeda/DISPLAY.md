# ANDROMEDA — DISPLAY

## Subsistema de display do GN-438

---

## 1. Resumo executivo

| Propriedade | Valor | Confiança |
|---|---|---|
| Dispositivo | `/dev/lcd` | CONFIRMADO |
| Drivers de LCD detectados | `st7789s_lcd_init`, `gc9106_lcd_init` | CONFIRMADO |
| Formato de cor | RGB565 | CONFIRMADO |
| Framework gráfico | LVGL 8 | CONFIRMADO |
| Resolução | **128×160** (GC9106) | PROVÁVEL |
| Interface do LCD | SPI | PROVÁVEL |
| Controlador LCDC | Presente | CONFIRMADO |
| Framebuffer | Não mapeado | NÃO RESOLVIDO |
| Driver ativo no GN-438 | GC9106 | PROVÁVEL |

---

## 2. Evidências de display

Strings encontradas:

```text
---------------lcd_init_begin---------------
/dev/lcd
---------------lcd_init_end---------------
RGB565 lcdc_read color:0x%x
lcd_enter_sleep
lcd_exit_sleep
st7789s_lcd_init
gc9106_lcd_init
```

O formato RGB565 indica 16 bits por pixel.

A string `RGB565 lcdc_read color` indica a existência de um **LCDC (LCD Controller)** no SoC.

---

## 3. Drivers de LCD

Foram identificadas duas rotinas de inicialização:

| Função | Driver |
|---|---|
| `st7789s_lcd_init` | ST7789S |
| `gc9106_lcd_init` | GC9106 |

Isso sugere que o firmware pode suportar múltiplos painéis ou que diferentes revisões de hardware usam controladores diferentes.

### ST7789S

- Resolução típica: 240×320 (QVGA/2.0") ou 240×240 (1.3").
- Interface: SPI ou paralelo 8/16 bits.

### GC9106

- Resolução típica: 128×160 (1.77").
- Interface: SPI.

O GN-438 visualmente parece ter uma tela de aproximadamente 1.8"–2.0". A análise do firmware indica que o GN-438 provavelmente usa o **GC9106** em **128×160**.

### Endereços das rotinas (flash, base 0x00C00000)

| Função | Endereço | Descrição |
|---|---|---|
| `gc9106_lcd_init` | `0x00D6481C` | Inicialização completa do GC9106 |
| `st7789s_lcd_init` | não mapeada nesta análise | Driver alternativo não ativo no dump |
| LVGL display init | `0x00CF8210` | Prepara `lv_disp_drv_t` e chama `lv_disp_drv_register` |
| `lv_disp_drv_register` caller | `0x00D626C4` | Recebe estrutura de configuração em RAM |

### Sequência GC9106 observada

A rotina `gc9106_lcd_init` envia comandos SPI típicos do GC9106:

```text
0xFE, 0xFE, 0xEF, 0xAF  ; ativação de registradores estendidos
0x80, 0xB3, 0x03, 0xB6, ...
0x21, 0x36, 0xD0, 0x3A, 0x05, 0xB4, ...
0x11 (SLPOUT), 0x29 (DISPON), 0x2C (RAMWR)
```

O envio é feito por `bl #0x8152cc` (comando) e `bl #0x8152d8` (dado), funções residentes em RAM.

### Estruturas de configuração em RAM

| Endereço | Uso |
|---|---|
| `0x0081BBD0` | Estrutura `disp_drv` / configuração primária |
| `0x0081BBC0` | Estrutura de configuração passada para `lv_disp_drv_register` |
| `0x0081D68C` | Tabela de drivers de display (15 entradas × 0x58 bytes) |

### Indicação de resolução 128×160

Em `0x0F8368` (flash) existe o dado:

```text
0x00A00080  →  halfwords little-endian: 0x0080 (128), 0x00A0 (160)
```

Esse padrão é o único candidato claro a dimensão de display no firmware do GN-438. Não foram encontrados imediatos `240`, `320`, `128` ou `160` hardcoded em instruções, sugerindo que as dimensões são carregadas de tabela.

> **Confiança: PROVÁVEL** — ainda não foi confirmado que `0x0F8368` é efetivamente copiado para `lv_disp_drv_t.hor_res/ver_res`, mas é o único valor plausível encontrado.

---

## 4. LVGL 8

O firmware usa LVGL 8. Evidências:

```text
lv_disp_drv_register
full_refresh requires at least screen sized draw buffer(s)
_lv_disp_refr_timer
lv_disp_get_scr_act
lv_disp_get_layer_top
lv_disp_get_layer_sys
lv_indev_drv_register: no display registered hence can't attach the indev to a display
F:\pen133_yp3_mp\spark2\src\gui8\lvgl\src\core\lv_disp.c
```

Isso é importante para o OpenPod: podemos reutilizar a infraestrutura LVGL existente.

---

## 5. Resolvido nesta análise

- Driver ativo: **GC9106** (endereço `0x00D6481C`).
- Interface: **SPI** (comandos/dados enviados via funções em RAM).
- Resolução provável: **128×160**.
- Formato: **RGB565**.
- Estruturas LVGL mapeadas em RAM.

## 6. Ainda não resolvido

Ainda falta determinar:

- Endereço base do LCDC. *(candidatos: `0x400D0000`, `0x400D1000`, `0x400403xx` — ver `andromeda/PERIPHERAL_REGISTER_SCAN.md`)*
- Endereço do framebuffer.
- Pinos GPIO envolvidos.
- Confirmação definitiva de que `0x0F8368` é a resolução ativa.
- Offset exato de `hor_res`/`ver_res` dentro de `lv_disp_drv_t` para este build.

Próximos passos:

1. Confirmar que a tabela em `0x0F8368` é copiada para `0x0081BBC0+0x30`/`0x32`.
2. Mapear os registradores do LCDC.
3. Inspecionar o heap LVGL em runtime.

---

## 7. Implicação para OpenPod

Para a Fase 1 (interface), não precisamos reprogramar o driver de LCD. Basta:

- Manter `/dev/lcd` e o driver LVGL.
- Modificar temas, cores, fontes, ícones e layouts LVGL.

Se a resolução for **128×160** (provável), o Design System do iPod nano 2nd gen precisará ser fortemente simplificado:

- Fontes pequenas (8–12 px).
- Ícones 16×16 ou 24×24.
- Poucos elementos por tela.
- Scroll obrigatório para listas longas.

Se porventura a resolução for 240×320 (improvável para este dump), haveria mais espaço, mas ainda assim menos que um iPod nano original (320×240).

---

## 7. Classificação

| Afirmação | Classe |
|---|---|
| Dispositivo `/dev/lcd` existe | CONFIRMADO |
| Drivers ST7789S/GC9106 presentes | CONFIRMADO |
| Formato RGB565 | CONFIRMADO |
| LVGL 8 em uso | CONFIRMADO |
| Resolução exata | PROVÁVEL (128×160) |
| Driver ativo | PROVÁVEL (GC9106) |
| Interface SPI/paralela | PROVÁVEL (SPI) |
| Framebuffer mapeado | NÃO RESOLVIDO |

---

## Referências

- `docs/OpenPod_Design_System.md`
- `docs/GUI_ANALYSIS.md`
- `andromeda/MEMORY.md`
