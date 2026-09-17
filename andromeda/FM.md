# ANDROMEDA — FM RADIO

## Subsistema de rádio FM do GN-438

---

## 1. Resumo executivo

| Propriedade | Valor | Confiança |
|---|---|---|
| Middleware | `fm_*` APIs | CONFIRMADO |
| Recursos | presets, bandas, busca, sintonia manual | CONFIRMADO |
| Bandas | Japão / Europa / Geral | CONFIRMADO |
| Antena | Fone de ouvido | CONFIRMADO |
| Tuner físico | Não identificado | NÃO RESOLVIDO |
| Interface de controle | Provavelmente I2C | HIPÓTESE |

---

## 2. Evidências

### Inicialização e handlers

```text
?fm_init
--- %s : %d, fm_handle: %d
```

### Presets

```text
pstr_fm_preset_init
-fm station %d error!!
-fm_tag NULL error!!!!!
-set fm station %d error!!
Preset FM Stations
Delete the Presets
Clear All Preset FM
The preset station is empty
```

### Bandas

```text
Radio Bands
Japanse frequentieband
Europese frequentieband
Algemene frequentieband
```

### Interface

```text
Radio Searching
Radiofrequentie
Station
```

### Antena

```text
Please Insert Earphone as FM Antenna.
The radio needs to be plugged in as an antenna
```

### Telas LVGL

```text
page_fm_band_event_cb
page_fm_play_event_cb
page_fm_preset_event_cb
page_fm_set_event_cb
```

---

## 3. Tuner físico

Não foi identificado o chip tuner (RDA5807, TEA5767, SI4703, etc.).

A comunicação com o tuner provavelmente é via I2C, mas sem strings ou endereços I2C visíveis.

---

## 4. Implicação para OpenPod

A rádio FM pode ser mantida inalterada na Fase 1. Melhorias futuras:

- Interface de presets mais limpa.
- RDS (se suportado pelo tuner).
- Navegação por frequência estilo iPod.

---

## Classificação

| Afirmação | Classe |
|---|---|
| FM com presets e bandas | CONFIRMADO |
| Antena via fone de ouvido | CONFIRMADO |
| Telas LVGL existem | CONFIRMADO |
| Tuner identificado | NÃO ENCONTRADO |
| Interface I2C confirmada | NÃO RESOLVIDO |

---

## Referências

- `docs/FIRMWARE_ANALYSIS.md`
- `andromeda/AUDIO.md`
- `andromeda/DISPLAY.md`
