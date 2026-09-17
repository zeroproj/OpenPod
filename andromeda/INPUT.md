# ANDROMEDA — INPUT

## Subsistema de botões e entrada do GN-438

---

## 1. Resumo executivo

| Propriedade | Valor | Confiança |
|---|---|---|
| Dispositivo de teclas gerais | `/dev/key_io` | CONFIRMADO |
| Dispositivo de tecla liga/desliga | `/dev/key_onoff` | CONFIRMADO |
| Framework de teclas | `watch_key_*` | CONFIRMADO |
| Leitura de teclas | `keyad` (ADC-based) | PROVÁVEL |
| Estados da máquina de teclas | idle / work / backlight off / sync / sleep wait / sleep / wake up / poweroff | CONFIRMADO |
| Botões detectados | power, onoff, volume_up, volume_down, left, right, enter, back, record, sd_detect, sleep, pvsync | CONFIRMADO |
| Mapeamento físico GPIO/ADC | Não determinado | NÃO RESOLVIDO |
| Integração LVGL | `lv_indev_drv_register` | CONFIRMADO |

---

## 2. Dispositivos de entrada

O firmware abre dois dispositivos de entrada:

```text
/dev/key_onoff
/dev/key_io
```

Possíveis papéis:

- `/dev/key_onoff`: tecla de power/sleep dedicada.
- `/dev/key_io`: matriz ou ADC das teclas restantes.

---

## 3. Botões identificados

### Pelo sistema `watch_key`

Strings de debug revelam os seguintes `key_id`:

```text
- onoff key
- power key
- volume_up key
- volume_down key
- left key
- right key
- enter key
- back key
- record key
- sd_detect key
- sleep key
- pvsync key
- key light
```

### Pelo sistema `keyad`

Strings de erro de leitura indicam botões conectados a um ADC (`keyad`):

```text
-keyad read key left, evt %x error!
-keyad read key right, evt %x error!
-keyad read key back, evt %x error!
-keyad read key up, evt %x error!
-keyad read key down, evt %x error!
-keyad read key mode, evt %x error!
-keyad read key record, evt %x error!
```

Isso sugere um esquema de **teclado resistivo com ADC**: vários botões compartilham uma linha de ADC e geram tensões diferentes.

---

## 4. Máquina de estados

As strings indicam múltiplos estados de processamento de teclas:

```textn-idle
work
back light off
sync
sleep wait
sleep
wake up
poweroff
```

Cada estado tem handlers específicos para os eventos de tecla.

---

## 5. Eventos de tecla

Para cada botão, o firmware reconhece:

- press
- short release
- long start
- long release
- long press / long press repeat

Exemplo para volume_up:

```text
-volume_up key press Vol+
-volume_up key short release Vol+
-volume_up key long en Vol+
-volume_up key long press Vol+
```

---

## 6. Integração com LVGL

O LVGL 8 é usado, com `lv_indev_drv_register` para registrar dispositivos de entrada. As teclas físicas são mapeadas para teclas LVGL:

```text
LV_KEY_LP_ENTER
LV_KEY_LR_ENTER
```

---

## 7. Rastreamento do `keyad_read` e do despacho de teclas

> Descoberto em 2026-09-16. Os endereços abaixo são endereços XIP
> (`0x00C00000` + offset do arquivo).

### 7.1 Callback principal registrado nos drivers

A inicialização de dispositivos em `0x00CFC378` abre `/dev/kadc_ch1`,
`/dev/key_onoff` e `/dev/key_io`, registrando o **mesmo callback**:

| Dispositivo | Endereço do callback registrado | IDs passadas na configuração |
|---|---|---|
| `/dev/kadc_ch1` | `0x00CFC7A9` | — (tabela em RAM `0x00819B0C`) |
| `/dev/key_onoff` | `0x00CFC7A9` | `0x37` (onoff), `0x47` (power) |
| `/dev/key_io` | `0x00CFC7A9` | tabela em RAM `0x00819BCC` |

A função em `0x00CFC7A8` é o despachador de eventos de tecla (o próprio
`watch_key_*_process`). Ela recebe `(r0 = handle do dispositivo, r1 = evento)`
e, para a maioria das teclas, chama `0x00D21374(r0=key_id, r1=event_type)`
para escrever no buffer `0x00823D7A`.

### 7.2 Buffer de evento de tecla

Escritor: `0x00D21374`:

```asm
00D21374  ldr  r3, =0x00823D7A
00D21376  movs r2, #1
00D21378  strb r0, [r3]       ; key_id
00D2137A  strb r1, [r3, #1]   ; event_type
00D2137C  strb r2, [r3, #2]   ; flag "novo evento"
00D2137E  bx   lr
```

Leitor: `keyad_read` em `0x00D21110`:

```asm
00D21110  push {r4, r5}
00D21112  ldr  r5, =0x00823D7A
00D21114  ldrb r2, [r5, #2]
00D21116  cmp  r2, #1
00D2111A  bne  exit            ; só processa se flag == 1
00D2111C  ldrb r1, [r5, #1]   ; event_type
00D2111E  ldrb r0, [r5]       ; key_id
00D21122  orr.w r0, r0, r1, lsl #16
00D21126  strb r4, [r5, #2]   ; limpa flag
```

### 7.3 Eventos de tecla reconhecidos

O firmware usa cinco códigos de evento:

| Código | Significado provável |
|---|---|
| `0x10` | press / short press |
| `0x30` | short release |
| `0x40` | long start |
| `0x50` | long press |
| `0x60` | long release |

### 7.4 Tabela de conversão do `keyad_read`

A função `keyad_read` (`0x00D21110`) converte `(key_id, event_type)` em um
código que é enviado à camada LVGL. A tabela abaixo lista os códigos de
saída para cada combinação. Códigos entre `0x00` e `0x1B` são valores
`LV_KEY_*` da LVGL v8. Códigos bit-alto (`0x80`–`0xA3`) são variantes
próprias do firmware (provavelmente pressionamento longo/long release).

| key_id | Nome na string de debug | `0x10` | `0x30` | `0x40` | `0x50` | `0x60` |
|---|---|---|---|---|---|---|
| `0x20` | `keyad read key down` | `0x12` (DOWN) | `0x12` | `0x99` | `0x9A` | `0x9B` |
| `0x21` | `keyad read key back` | `0x0A` (ENTER) | `0x0A` | `0x8B` | `0x8C` | `0x8D` |
| `0x22` | `keyad read key up` | `0x11` (UP) | `0x11` | `0x96` | `0x97` | `0x98` |
| `0x25` | `keyad read key mode` | `0xA0` | `0xA0` | `0xA1` | `0xA2` | `0xA3` |
| `0x34` | `keyad read key record` | `0x92` | `0x92` | `0x93` | `0x94` | `0x95` |
| `0x42` | `keyad read key left` | `0x14` (LEFT) | `0x14` | `0x85` | `0x86` | `0x87` |
| `0x43` | `keyad read key right` | `0x81` | `0x81` | `0x88` | `0x89` | `0x8A` |
| `0x45` | *(usa string right)* | `0x81` | `0x81` | `0x82` | `0x83` | `0x84` |

> **Atenção:** os códigos `0x81`/`0xA0` que chegam na UI já foram
> observados no aparelho (`BUTTON_ANALYSIS.md` §8): `0x81` = VOL e
> `0xA0` = M. A tabela acima mostra de onde eles podem surgir, mas
> ainda não sabemos qual botão físico gera qual `key_id`.

### 7.5 Nomes dados pelo `watch_key_work_process`

Na função `0x00CFC7A8` (estado `work`), as strings de debug identificam
os `key_id` da seguinte forma:

| key_id | Nome atribuído |
|---|---|
| `0x21` | `enter key` |
| `0x24` | `volume_up key` |
| `0x25` | *(passa pelo keyad_read; nome não exibido)* |
| `0x34` | `record key` |
| `0x37` | `onoff key` |
| `0x38` | *(estado sleep/wake)* |
| `0x42` | `left key` |
| `0x43` | `volume_down key` |
| `0x45` | `back key` |
| `0x47` | `power key` |

Isso mostra que **um mesmo `key_id` pode ter nomes diferentes conforme o
dispositivo de origem**: no `keyad_read` o `0x43` é tratado como "right",
mas no `watch_key_work_process` ele é identificado como
`volume_down key`. A explicação é que o `keyad_read` provavelmente só
recebe eventos do `/dev/kadc_ch1`, enquanto o `0x43` do estado `work`
vem de outro dispositivo (`/dev/key_io`).

## 8. Drivers de ADC

As funções que acessam as bases `0x40095000` e `0x40096000` foram
localizadas:

| Função | Endereço | Base usada | Papel provável |
|---|---|---|---|
| init ADC secundário | `0x00D7C564` | `0x40096000` | configuração do ADC |
| init ADC principal | `0x00D7C660` | `0x40095000` | configuração do ADC |
| open genérico | `0x00D636F0` | — | procura driver por nome e chama `open` |

A função `0x00D63ED8` (init de `/dev/kadc_ch1`?) chama `0x00D7C564`.
A função `0x00D64590` (init de `/dev/key_io`?) chama `0x00D7C660`.

## 9. Não resolvido

Ainda não foi determinado:

- Qual GPIO/ADC é usado para cada tecla física.
- O conteúdo das tabelas de limiar em RAM `0x00819B0C` (`/dev/kadc_ch1`) e
  `0x00819BCC` (`/dev/key_io`). Sem acesso runtime, os limiares não podem
  ser lidos.
- Se `/dev/kadc_ch0`..`/dev/kadc_ch5` são realmente usados (apenas
  `/dev/kadc_ch1` é aberto na inicialização observada).
- Se `/dev/tp` é usado em runtime ou é código morto.
- O papel exato dos códigos bit-alto (`0x80`–`0xA3`) no `keyad_read`.

## 10. Candidatos de hardware para botões

O scan de registradores encontrou:

| Função | Candidato a base | Confiança |
|---|---|---|
| GPIO/pinmux | `0x40085000` | PROVÁVEL |
| ADC (teclado resistivo) | `0x40095000`, `0x40096000` | PROVÁVEL |
| PWM (backlight?) | `0x40010000`..`0x40011000` | PROVÁVEL |

A investigação desses pontos exigiria análise das funções `keyad_read` e do driver `/dev/key_io`.

---

## 11. Implicação para OpenPod

Para a Fase 1 (interface), a navegação pode ser adaptada sem reescrever o driver de input:

- Manter o mapeamento físico atual.
- Reconfigurar a interpretação das teclas em cada tela.
- Mapear left/right/up/down/enter/back para navegação estilo iPod.

Se o layout de botões do GN-438 for:

```text
             M (menu?)
             ↑
      |<<   ← ● →   >>|
             ↓
            VOL
             ▶Ⅱ
```

Podemos mapear:
- ↑ / ↓: navegar itens.
- → / |>>: próximo / enter.
- ← / <<|: voltar.
- ▶Ⅱ: play/pause.
- M: menu.
- VOL: volume.

---

## 12. Classificação

| Afirmação | Classe |
|---|---|
| Dispositivos `/dev/key_io` e `/dev/key_onoff` existem | CONFIRMADO |
| Callback de tecla registrado em `0x00CFC7A9` | CONFIRMADO |
| Buffer de evento em `0x00823D7A` | CONFIRMADO |
| Função `keyad_read` em `0x00D21110` | CONFIRMADO |
| Tabela de conversão `key_id` → `LV_KEY_*` | CONFIRMADO |
| Botões power/vol/left/right/enter/back/record identificados por strings | CONFIRMADO |
| Bases dos registradores ADC (`0x40095000`/`0x40096000`) | PROVÁVEL |
| Leitura via ADC (`keyad`) | PROVÁVEL |
| Estados da máquina de teclas identificados | CONFIRMADO |
| LVGL gerencia input | CONFIRMADO |
| GPIO/ADC mapeado para cada botão físico | NÃO RESOLVIDO |
| Conteúdo das tabelas de limiar em RAM | NÃO RESOLVIDO |

---

## Referências

- `docs/BUTTON_ANALYSIS.md`
- `docs/GUI_ANALYSIS.md`
- `andromeda/DISPLAY.md`
