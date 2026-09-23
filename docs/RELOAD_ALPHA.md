# OpenPod Reload Alpha — reset limpo

> Criado 2026-09-23. Base: `GN438_original.bin` sha `b7cd5eb9...`

## Filosofia
Reset no ORIGINAL, 3 features só. Sem carregar acoplamento da linha Core (Saturno, chrome, Marte). Cada patch independente.

## Receita `reload_alpha` (`tools/build.py:274`)

| # | Ferramenta | O que faz | Bytes | Setores |
|---|---|---|---|---|
| 1 | `patch_update_sd.py` | `Configurar → Atualizar por SD` (`0x00CF6CA0` + gancho `0x001092C0`) | ~72 B + 8 B string | `0x053000`, `0x109000`, `0x1A3000` |
| 2 | `patch_fundo_display.py` | `disp->bg_color` branco→preto (`0x001567F6 FF→00`) | 1 B | `0x156000` |
| 3 | `patch_fundo_abertura.py` | Fundo abertura preto (2 bytes `0x0012285C/0x001228E6`) | 2 B | `0x122000` |
| 4 | `patch_fundo_preto.py` | Paleta Tocando Agora preta (`0x000C73B8`) | 1024 B | `0x0C7000` |
| 5 | `patch_nome_faixa.py --em 0x1A3040` | `OpenPod` na barra centro (`0x001226F4` → `0x00DA3040`) | 8 B + 10 B NOP | `0x122000`, `0x1A3000` |

Total: 867 bytes em 6 setores, `0x053000` a `0x1A3000`. Nada abaixo `0x00D000` (R1 OK).

## Barra principal — Data | OpenPod | Bateria
- Esq: data/hora nativa do firmware (relógio do topo, já existe)
- Centro: `patch_nome_faixa` — rotina `0x00D226AC` (2 chamadores `0x00D23898`/`0x00D23E9C`)
- Dir: bateria nativa (ícone da bateria, já existe). Verde/prata fica para Alpha 0.2

Perda: ícone de SD presente some (vira texto fixo). Verificar com/sem cartão.

## Fundo preto
`docs/ARQUITETURA.md §12` provou que fresta branca é `disp->bg_color = 0xFFFFFF` em `lv_disp_drv_register:0x00D567F6`. 1 byte resolve global. Os outros 2 patches fecham abertura e Tocando Agora.

## Build
```sh
python3 tools/build.py --receita reload_alpha --saida firmware/WORKING/GN438_reload_alpha_v001.bin
python3 tools/validate_firmware.py firmware/WORKING/GN438_reload_alpha_v001.bin
# FIRM CRC FAIL é ESPERADO (R1) — build já reclassifica como OK
python3 tools/gera_up.py --in firmware/WORKING/GN438_reload_alpha_v001.bin --out firmware/WORKING/GN438_reload_alpha_v001.up
python3 tools/make_update_up.py --in firmware/WORKING/GN438_reload_alpha_v001.bin --verify-only firmware/WORKING/GN438_reload_alpha_v001.up
```

Imagens:
- `6e1bddb20501d08ad63da40666f38f44632552b9f755cf64c52d97509903be33` bin
- `e40f29ddda809d7615065f593a9d291063e55e4a00f20013de4f6bf67d171961` up

## Próximos passos (Alpha 0.2+)
- Bateria verde/prata (`patch_bateria_verde.py`)
- Versão em Info (`patch_versao.py --texto "Reload Alpha 0.1"`)
- Logo OpenPod (`patch_logo.py` + `patch_fundo_abertura`)
