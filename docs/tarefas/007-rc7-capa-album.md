# 007 — Reload 1.0 RC7: capa do álbum (ID3v2 APIC) na Tocando Agora

- Tipo: Risco + Pesada (código novo na área livre, ganchos na Tocando Agora)
- Desenvolvedor: MiniMax M3 (opencode.json do worktree)
- Analista: gpt-6-sol high (R0 e 1ª análise do diff), gpt-6-astra medium (final)
- Depende de: RC6 (catraca `af3a2b6d…`), análise `docs/tarefas/003-rc5-analise-capa.md` (E1/E2 feitos), D05, D08
- Status: **RASCUNHO — Fase A parcial** (2026-10-30). Ficha ainda não escrita; testes vermelhos ainda não escritos.

## Fase A — achados no ORIGINAL até aqui (desmontagem, capstone)

| # | Achado | Endereço | Confiança |
|---|---|---|---|
| A1 | **P10 — caminho da faixa atual:** `pstr_audio_get_path` = `0xCFEFC4(src, índice, buf)`; devolve `1` e copia até `0xFF` bytes (`strncpy` `0xD9FD54`, sem terminador garantido → buffer de 256 B zerado). Uso canônico da fábrica: `src = ldrb [0x81BC84]` (`0xCFF1A8`), `índice = ldr [0x81BC84+0x20]` (`0xCFF0FC`), `buf = 0xCF780C(0xFF)` (malloc), libera `0xCF7884`. Mesmo padrão em `0xCFF0A8`, `0xCFF354`, `0xD016A6`, `0xD017AA` | `0xCFEFC4` | CONFIRMADO (estático) |
| A2 | Caminho do banco aceito direto pelo `f_open` `0xD777CC` | — | PROVÁVEL (falta conferir um chamador que passe o caminho do `get_path` ao `f_open`) |
| A3 | **Título no presenter:** `0xD08448` pega o índice (`0xCFF0FC`), `calloc(1,0xFF)`, `0xCFEE60(src, índice, buf, 1)` e manda a mensagem tipo 3 / rótulo 1 (`0xD0D818` + `0xD0D880`). Chamado na abertura da página (`0xD09014`) e nas trocas de faixa (ex.: `0xD08BE2`) → ponto natural para "faixa mudou" | `0xD08448` | CONFIRMADO (chamadores a listar todos) |
| A4 | **View:** `page_music_play_create` `0xD31E7C`: struct `malloc(0x30)` (`0xD31E84`) zerada; tela-pai em `sl` = `0xD21690()` (`0xD31EB0`); fundo `lv_img_create` `0xD5D850` + `lv_img_set_src` `0xD5D868`; `lv_obj_align(obj, alinh, x, y)` = `0xD4A3A2` (alinh 2 = topo-centro). Campos: `[0]` contador "1/253" y0 · `[4]` título y22 h22 · `[8]` rótulo 118×60 em **y45** · `[0x10]` btnmatrix (ícones) y110 · `[0x14]`/`[0x18]` tempos · `[0x1C]` barra y152 · `[0x24]` objeto de `0xD5B890`. Ponteiro da view em `[[0x81CE2C]+0xAC]` | `0xD31E7C` | CONFIRMADO |
| A5 | **Rótulo `[8]` ocupa y45..105, o mesmo vão da capa (y42..106).** Recebe o texto do índice 2 da mensagem tipo 3. Há strings de letra (`-lrc found: %s`, `reader.lrc`, `-time is: %d, lrc: %s`): o rótulo `[8]` **pode ser a letra (.lrc)** e ficaria sob/sobre a capa | `0xD32204` | HIPÓTESE — decidir antes da ficha |
| A6 | Mensagens à view: `0xD32204` (tipo 3: `set_text` 0xD5ED94 nos campos `[0]`,`[4]`,`[8]`,`[0x14]`,`[0x18]`; tipo 4 índice 5: barra `0xD5B738`) | `0xD32204` | CONFIRMADO |
| A7 | **JPEG da fábrica (fotos):** `0xD103D4(caminho, in, out)` usa **um contexto global único** em `[0x81CDE8]` e recusa se já houver um; `calloc(1,0x4180)`; FIL em `ctx+0x3E08`; `jd_prepare(ctx+0x4064, 0xD1036D, ctx+0x3000, 0xE00, ctx)`; repete após `f_lseek(0)` se `[ctx+0x4114]==1`. Libera em `0xD10498` (`f_close`, `free`, zera o global). `0xD104B8` chama `jd_decomp(ctx+0x4064, 0xD10229, escala)`. **Consequência:** nossa rotina não deve usar esse global (ou deve respeitá-lo) para não colidir com o visualizador de fotos | `0xD103D4` | CONFIRMADO |

## Falta na Fase A
- A2 (caminho → `f_open`), A5 (o que vai no rótulo `[8]`), todos os chamadores de `0xD08448`, onde liberar o buffer (destruição da página 4), leitor `0xD1036D` e as convenções de `jd_prepare`/`jd_decomp` desta build, espaço livre (lotes no `MAPA`: livre de `0x1A7050` a `0x1A8000` ≈ 4 KiB dentro de `AREA_FIM`).
