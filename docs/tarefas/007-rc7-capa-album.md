# 007 — Reload 1.0 RC7: capa do álbum (ID3v2 APIC) na Tocando Agora

- Tipo: **Risco + Pesada** (código novo na área livre, ganchos na Tocando Agora, leitura de arquivo do usuário)
- Engenheiro (análise, ficha, testes): Claude Opus 5.5 — só Fases A e B (D10)
- Sessão da ficha (Fases C e D): **glm-5.3** no OpenCode (`opencode-go/glm-5.3`, D10)
- Desenvolvedor: **MiniMax M3** (`opencode-go/minimax-m3`, opencode.json do worktree, skip-worktree)
- Analista: Codex **gpt-6-sol high** (R0 e 1ª análise do diff), **gpt-6-astra medium** (conferência final)
- Depende de: RC6 (catraca `af3a2b6d…`), `docs/tarefas/003-rc5-analise-capa.md` (E1/E2 feitos), D05, D08, D10, D11
- Status: **ficha + testes vermelhos prontos (2026-10-30)**; falta R0

## Objetivo
Na Tocando Agora, mostrar a capa do álbum lida **de dentro do MP3** (ID3v2 `APIC`,
JPEG baseline) em **64×64 centralizada** (x 32..96, y 42..106), sem mudar mais nada
da tela (`docs/img/rc7_tocando_modelo.png`). Sem capa, capa progressiva, PNG,
imagem menor que 64×64, tag inválida ou falta de memória: **quadrado cinza
(52,52,52) com nota musical (150,150,150)**, tirado do modelo aprovado.

Fora: qualquer outra tela; a letra (`.lrc`) continua onde está e é desenhada
**por cima** da capa (D11); `cover.jpg` da pasta (D05); leitor de ID3 da biblioteca.

## Evidência no ORIGINAL (desmontagem capstone + emulação unicorn do código de fábrica)

| # | Achado | Endereço | Confiança |
|---|---|---|---|
| A1 | **P10 — caminho da faixa atual:** `pstr_audio_get_path` = `0xCFEFC4(origem, índice, buf)` → `1` e copia até `0xFF` bytes (`strncpy` `0xD9FD54`: sem terminador se o caminho tiver ≥255 → buffer de 256 B zerado). Origem = `ldrb [0x81BC84]` (`0xCFF1A8`), índice = `ldr [0x81BC84+0x20]` (`0xCFF0FC`). Mesmo padrão em `0xCFF0A8`, `0xCFF354`, `0xD016A6`, `0xD017AA` | `0xCFEFC4` | CONFIRMADO |
| A2 | O caminho do banco é o que a fábrica usou para abrir o arquivo ao montar a biblioteca (`0xD71E42`) | — | PROVÁVEL (sem `f_open` direto após `get_path` na fábrica) |
| A3 | **Título:** presenter `0xD08448` (índice `0xCFF0FC`, `0xCFEE60(src, idx, buf, 1)`) manda a mensagem tipo 3 / rótulo 1. Chamado na abertura da página (`0xD09014`) e nas trocas de faixa (`0xD088E8`, `0xD089A0` = `page4_media_cb`, `0xD08BE2`) | `0xD08448` | CONFIRMADO |
| A4 | **View** `page_music_play_create` `0xD31E7C`: struct `lv_mem_alloc(0x30)` (`movs r0,#0x30` em `0xD31E80`) zerada por `memset(...,0x30)` (`movs r2,#0x30` em `0xD31E9E`); `r5` = struct até o fim; tela em `r0` no `bl lv_img_create` do **fundo** em `0xD31EB6` (o papel de parede é o 1º objeto). Campos: `[0]` contador · `[4]` **título** · `[8]` rótulo 118×60 em y45 (letra) · `[0x10]` ícones · `[0x14]`/`[0x18]` tempos · `[0x1C]` barra · `[0x24]`. Ponteiro da view em `[[0x81CE2C]+0xAC]` (slot `0x9C+4·página`) | `0xD31E7C` | CONFIRMADO |
| A5 | O rótulo `[8]` recebe o texto do índice 2 (`0xD084F8`: `"  "` quando não há letra) vindo de `page4_media_cb`; strings `-lrc found: %s`, `-time is: %d, lrc: %s` → é a **letra** | `0xD084F8` | PROVÁVEL |
| A6 | `page_music_play_label_process` `0xD32204`: tipo 3 → `set_text` nos campos `[0]`,`[4]`,`[8]`,`[0x14]`,`[0x18]` por **um único** `b.w 0xD5ED94` em `0xD3225E` (r0 = rótulo, r1 = texto) | `0xD3225E` | CONFIRMADO |
| A7 | A struct da view é liberada por `view_clean_all_objs` (`lv_mem_free` `0xD5811C` em `0xD23A7C`) **depois** de apagar os objetos (`0xD23A62`); a página 4 não tem destrutor próprio | `0xD23A60` | CONFIRMADO |
| A8 | `lv_obj_del` manda **`LV_EVENT_DELETE = 0x21`** (`movs r1,#0x21; bl lv_event_send 0xD46FF0` em `0xD4D264`). `lv_event_t`: `+0` alvo, `+8` código (byte), `+0xC` user_data, `+0x10` param (acessores `0xD47030..0xD4703C`). `lv_obj_add_event_cb(obj, cb, filtro, user_data)` = `0xD47064` (usado assim em `0xD320F0`) | `0xD4D264` | CONFIRMADO |
| A9 | LVGL: `lv_img_create(pai)` `0xD5D850`, `lv_img_set_src(obj, src)` `0xD5D868`, `lv_obj_align(obj, alinh, x, y)` `0xD4A3A2` (alinh 2 = topo-centro), `lv_label_set_text` `0xD5ED94` | — | CONFIRMADO (uso na view) |
| A10 | **Cor:** `LV_COLOR_16_SWAP = 1` (`docs/COLOR_SOURCE.md` §9, aparelho). `lv_img_dsc_t` = header (`cf` 5 bits, `always_zero` 3, `reserved` 2, `w` 11, `h` 11) + `data_size` + `data`; TRUE_COLOR = cf 4 (o papel de parede `0x0C73B8` decodifica com cf 10 = INDEXED_8 nessa numeração) | — | CONFIRMADO |
| A11 | **TJpgDec da fábrica** (emulado): `jd_prepare(jd, entrada, pool, 0xE00, dev)` `0xD10B20` (5º arg na pilha; zera `0x118` B do `JDEC`); `jd_decomp(jd, saída, escala)` `0xD11090`; largura/altura em **`jd+0x1C`/`jd+0x1E`** (u16); saída em **RGB565 little-endian** (vermelho = `00 F8`) → **trocar bytes** para a LVGL; retângulo `JRECT {left,right,top,bottom}` u16; dimensão reduzida = `w >> s` | `0xD10B20` | CONFIRMADO (emulação) |
| A12 | **O `jd_prepare` desta build ACEITA JPEG progressivo** (SOF2) e decodifica lixo → a recusa do progressivo é **nossa** (procurar SOF0 antes) | `0xD10B20` | CONFIRMADO (emulação, `test_a1`) |
| A13 | Uso da fábrica (fotos): contexto **global único** `[0x81CDE8]` (`calloc(1,0x4180)`; FIL em `+0x3E08`, JDEC em `+0x4064`, pool `+0x3000`) — **não usar esse global** (colidiria com o visualizador de fotos). Leitor `0xD1036D`: `f_read` ou, para pular, `f_lseek(fptr+n)` com **`fptr` (64 bits) em `FIL+0x38`**; `f_lseek(fil, ofs)` recebe o offset de 64 bits em **`r2:r3`** (`0xD10456`) | `0xD103D4` | CONFIRMADO |
| A14 | FatFs **reentrante** (`validate` → `ff_req_grant` `0xD77EA4` com o objeto de sincronização em `fs+0x14`; `unlock_fs` `0xD75328`); LFN no heap (`ff_memalloc` = `0xCF780C`). `f_open(fil, caminho, modo)` `0xD777CC`, `f_read(fil, buf, n, &lidos)` `0xD76854`, `f_close(fil)` `0xD77C9C`. FIL ≤ `0x25C` B (vão entre FIL e JDEC na fábrica) | — | CONFIRMADO (FIL: PROVÁVEL) |
| A15 | Tarefas: `ViewTask` (onde rodam view e mensagens) com pilha `0x1000`; `MainTask` (presenter, que já chama `get_path` com quadro de `0x238`) com `0x400` | `0xCF83A0` | CONFIRMADO o valor; pilha suficiente: PROVÁVEL |
| A16 | Heap: `calloc(n, tam)` `0xCF7840` (confere o livre e devolve 0 se faltar), `malloc` `0xCF780C`, `free` `0xCF7884`. E1: 16,4 KiB de contexto JPEG cabem com música tocando | — | CONFIRMADO |
| A17 | Área livre `0xFF` de `0x1A7048` a `0x1FC000` (RC6); `AREA_FIM` do `build.py` hoje = `0x1A8000` | — | CONFIRMADO |

## Escopo — receita `reload_1.0_rc7` = `reload_1.0_rc6` + `fab_capa_album.py`
Uma ferramenta só; exige **sha256 da entrada = RC6 `af3a2b6d…`** (premissa única que
cobre tudo; as outras conferências continuam para dizer *o que* está errado).

### Bytes (únicos permitidos além da RC6)
| Arquivo | Fábrica | Novo | O quê |
|---|---|---|---|
| `0x131E80` | `30 20` | `34 20` | `lv_mem_alloc(0x30)` → `0x34` (campo novo `[view+0x30]` = EXT) |
| `0x131E9E` | `30 22` | `34 22` | `memset(view, 0, 0x30)` → `0x34` |
| `0x131EB6` | `bl 0xD5D850` | `bl 0xDAA010` | criação do fundo → **CRIA** |
| `0x13225E` | `b.w 0xD5ED94` | `b.w 0xDAA014` | `set_text` das mensagens → **TITULO** |
| `0x1A8000..0x1AB000` | `FF` | lote | dsc + placeholder + tabela + código |

### Lote `0x1A8000` (`0x3000`, XIP `0xDA8000`) — layout FIXO
```
0x1A8000  lv_img_dsc_t do quadrado cinza: header 0x08010004 (TRUE_COLOR 64x64), data_size 8192, data 0x00DA8010
0x1A800C  FF FF FF FF
0x1A8010  8192 B = tests/assets/rc7/placeholder_64x64.rgb565swap (do modelo aprovado, bytes já trocados)
0x1AA010  b.w CRIA_impl      ; ENTRA_CRIA   0xDAA010
0x1AA014  b.w TITULO_impl    ; ENTRA_TITULO 0xDAA014
0x1AA018  b.w APAGA_impl     ; ENTRA_APAGA  0xDAA018 (cb do LV_EVENT_DELETE, registrado como 0xDAA019)
0x1AA01C  código (até 0x1AB000); o que sobrar fica 0xFF
```
`MAPA["fab_capa_album.py"] = (0x1A8000, 0x3000)` e `AREA_FIM` passa a `0x1AB000`
(o vigia do pipeline passa a cobrir o lote). O código é **assembly** (Thumb-2,
`tools/asm.py`/clang; pode ficar num `tools/capa_album.s` lido pela ferramenta); **sem
compilador C** (a saída mudaria com a versão e quebraria a catraca).

### Contratos (o que os testes rodam no unicorn)
Funções de fora que o código pode chamar: **só** `0xCF7840` calloc, `0xCF780C` malloc,
`0xCF7884` free, `0xCFEFC4` get_path, `0xD777CC` f_open, `0xD76854` f_read,
`0xD76C0A` f_lseek, `0xD77C9C` f_close, `0xD10B20` jd_prepare, `0xD11090` jd_decomp,
`0xD5D850` lv_img_create, `0xD5D868` lv_img_set_src, `0xD4A3A2` lv_obj_align,
`0xD47064` lv_obj_add_event_cb, `0xD5ED94` lv_label_set_text, `0xBAA` memset.
Qualquer outra (strcmp, memcpy, strncpy…) → escreva o laço. Não tocar nos objetos LVGL
por dentro. Registradores `r4..r11` preservados; pilha balanceada.

1. **CRIA** (`bl` em `0x131EB6`; `r0` = tela, `r5` = view já zerada):
   `fundo = lv_img_create(tela)` (sempre o 1º, para a capa ficar acima do papel de parede);
   `ext = calloc(1, EXT)` com `EXT ≤ 0x2400` (dsc 12 B + pixels 8192 + último caminho 256);
   `img = lv_img_create(tela)`; se `img == 0`: `free(ext)`, `[view+0x30] = 0`, devolve `fundo`.
   `lv_img_set_src(img, 0xDA8000)`; `lv_obj_align(img, 2, 0, 42)`;
   se `ext`: guarda `img` no ext, `[view+0x30] = ext`, `lv_obj_add_event_cb(img, 0xDAA019, 0x21, ext)`;
   sem `ext` (sem memória): fica o quadrado cinza, `[view+0x30] = 0`. **Devolve `r0 = fundo`.**
2. **TITULO** (`b.w` em `0x13225E`; `r0` = rótulo, `r1` = texto; volta direto a quem chamou o label_process):
   `lv_label_set_text(r0, r1)` **primeiro e uma vez só**. Depois, só se `view = [[0x81CE2C]+0xAC]` ≠ 0,
   `r0 == [view+4]` (título) e `ext = [view+0x30]` ≠ 0:
   `get_path(ldrb [0x81BC84], [0x81BC84+0x20], buf256)`; falhou → último caminho = vazio e quadrado
   cinza; **mesmo caminho do último → não faz nada** (nem arquivo, nem `set_src`);
   caminho novo → guarda; `lv_img_set_src(img, 0xDA8000)`; tenta a capa; **só se tudo der certo**
   `lv_img_set_src(img, &ext->dsc)` com header `0x08010004`, `data_size 8192`, `data` = pixels do ext.
3. **A capa** (contexto próprio `calloc`, **≤ 0x1800 B vivos a mais** no pico; tudo liberado e
   arquivo fechado na volta, inclusive nos erros):
   - `f_open(fil, caminho, 1)`; ID3v2 no início: `"ID3"`, versão **3 ou 4** (resto → cinza);
     flags do tag: `0x80` (unsync) → cinza; `0x40` → pular cabeçalho estendido (v2.3: 4 + tamanho BE32;
     v2.4: tamanho synchsafe, que já o inclui); tamanho do tag **synchsafe** (byte ≥ `0x80` → cinza).
   - Quadros a partir do fim do cabeçalho enquanto couber um cabeçalho de 10 B no tag; id começando
     com `00` = padding → fim. Tamanho do quadro: v2.3 **BE32 normal**, v2.4 **synchsafe**; quadro que
     passa do fim do tag → cinza. **Antes de avançar**, conferir `tam ≤ resto do tag − 10` (sem somar `10 + tam` em 32 bits); v2.4 com byte ≥ `0x80` no tamanho do quadro → cinza (R0 glm-5.3, MÉDIA: `0xFFFFFFF6` dava a volta e laçava; casos `v23_quadro_wrap`, `v23_tit2_wrap_antes`, `v24_quadro_synchsafe_invalido`). **Só o 1º `APIC` conta.** Flags do APIC: v2.3 `flags[1] & 0xE0`
     (comprimido/cifrado/grupo) ≠ 0 → cinza; v2.4 `flags[1] & 0x4F` ≠ 0 → cinza.
   - Corpo: codificação (0..3; outra → cinza), MIME até `00` (ignorado), tipo (1 B), descrição até
     `00` (codificação 0/3) ou `00 00` em pares (1/2). Imagem = resto do quadro; tem de começar com
     `FF D8` (PNG etc. → cinza). **Nunca ler além do quadro.**
   - **Só baseline:** percorrer os marcadores até o 1º SOF: `C0` aceita; `C1..CF` exceto `C4`,`C8`,`CC`
     → cinza; `D9`/`DA` antes de SOF → cinza.
   - Decodificar com o TJpgDec da fábrica, leitor **nosso** limitado ao tamanho do JPEG (pular =
     `f_lseek(fptr+n)`, `fptr` em `FIL+0x38`), pool `0xE00`. `jd_prepare` ≠ 0 → cinza.
     `w = jd+0x1C`, `h = jd+0x1E`; `w < 64` ou `h < 64` → cinza. `s` = maior de 0..3 com `w>>s ≥ 64`
     e `h>>s ≥ 64`; `W = w>>s`, `H = h>>s`. `jd_decomp(jd, saída, s)` ≠ 0 → cinza.
   - **Saída:** pixel `(ox, oy)` da capa = pixel `(ox·W/64, oy·H/64)` (divisão inteira) da imagem
     reduzida, com os **bytes trocados** (`LV_COLOR_16_SWAP`). Imagem não quadrada é esticada.
     Pixels fora de `W×H` ignorados. A saída devolve 1.
4. **APAGA** (cb do `LV_EVENT_DELETE` do `img`; `r0` = evento): se código `[e+8] == 0x21`:
   `ext = [e+0xC]`; se a view atual tiver `[view+0x30] == ext` → zera; `free(ext)`.

## Critérios de aceite (`tests/test_rc7.py` + `tests/emu_rc7.py`, protegidos)
- [x] **Arnês** (verde já na RC6): ativos por sha, TJpgDec da fábrica emulado (inclui A12), guarda de execução
- [ ] C0 constrói · C1 catraca RC6 · C2 receita/`MAPA`/`AREA_FIM`/proibidas
- [ ] C3 ganchos (premissa de fábrica + alvo novo), tamanho `0x34`, dsc + placeholder byte a byte, tabela de `b.w`
- [ ] C5 só os bytes acima mudam sobre a RC6; nada abaixo de `0xE000`; PSMP intacta
- [ ] D1 CRIA: fundo devolvido, img com quadrado cinza em (2, 0, 42), evento `0x21` com o ext; sem memória; sem objeto
- [ ] D2 capas com **pixels exatos** (erro máximo 0 contra o TJpgDec da fábrica + a regra acima): v2.3, v2.4 UTF-16, v2.4 e v2.3 com cabeçalho estendido, v2.3 grande (BE32 com byte ≥ 0x80), MIME errado
- [ ] D3 recusas → só quadrado cinza: progressiva, PNG, sem capa, sem tag, v2.2, unsync, APIC comprimido/cifrado/DLI, codificação inválida, 48×48, JPEG truncado, quadro maior que o tag, synchsafe inválido, 1º APIC PNG, arquivo vazio, `get_path` falha, arquivo ausente, sem memória
- [ ] D4 só o título dispara; sem view → só `set_text`; mesma faixa → nada; troca capa → cinza → capa
- [ ] D5 APAGA libera o ext e zera `[view+0x30]`
- [ ] Em todos: `set_text` primeiro, arquivo fechado, nenhum vazamento, pico ≤ `0x1800`, nada fora da lista
- [ ] D6 ferramenta: recusa RC5/truncado/bytes trocados, `--dry-run`, saída igual/symlink/hardlink

## Danos possíveis
| # | Dano | Coberto por |
|---|---|---|
| D1 | `bl`/`b.w` para lugar errado → reinicia ao abrir a Tocando Agora | C3 + D1/D2 rodando pelas entradas fixas |
| D2 | `set_text` deixa de ser chamado ou chamado 2× → título/tempos/letra somem | D2–D4 (`set_text` primeiro, uma vez, todos os rótulos) |
| D3 | `r5`/`r4..r11` destruídos na criação → view corrompida → reinício | arnês confere `r4..r11` e pilha em toda chamada |
| D4 | tag hostil (tamanhos falsos, truncado) → laço infinito, leitura fora do quadro, travamento | D3 (tempo limite 60 s, recusas), leitor limitado |
| D5 | JPEG progressivo decodificado como baseline → lixo na tela | A12 + D3 `progressiva` |
| D6 | vazamento de memória a cada troca de faixa → falta de memória depois de horas | D2–D5 (`vivos` igual antes/depois; APAGA) |
| D7 | uso depois de liberar (ext liberado com o img vivo, ou o contrário) | APAGA no DELETE do próprio img; arnês pinta `0xDD` no que foi liberado |
| D8 | arquivo fica aberto → FatFs esgota FIL/LFN | D2–D3 (`abertos == {}`) |
| D9 | memória: contexto + ext > o que sobra com música | pico ≤ `0x1800` + ext ≤ `0x2400` (< 16,4 KiB do E1); calloc 0 → cinza |
| D10 | cores trocadas (sem swap) | D2 pixel exato com bytes trocados |
| D11 | colisão com o visualizador de fotos (global `0x81CDE8`) | contrato: contexto próprio; arnês proíbe as rotinas de fotos |
| D12 | escrita fora dos bytes / no bootloader / PSMP | C5 |
| D13 | gravação interrompida entre `0x131000` e `0x1A8000` → Tocando Agora reinicia | risco aceito (igual RC1–RC6); só a página 4 depende dos ganchos |
| D14 | trava da GUI enquanto decodifica (capa grande) | risco aceito; roteiro mede |

## Riscos aceitos (decisor)
- Letra `.lrc` desenhada por cima da capa (D11).
- Capa não quadrada é esticada; só o 1º `APIC` conta; capas menores que 64×64 ficam cinza.
- Breve pausa na tela ao trocar de faixa com capa grande (decodificação na ViewTask).
- `get_path` e FatFs chamados da ViewTask (A14/A15: PROVÁVEL seguro; a fábrica faz isso no presenter).
- Gravação interrompida: Tocando Agora reinicia até regravar (recuperação por cabo/cartão).

## Roteiro no aparelho (decisor) — MP3 em `tests/assets/rc7/` (6 s, tom de 440 Hz baixo)
Copie os 7 MP3 para uma pasta do cartão e toque um por um (pela pasta/Arquivos).
| Arquivo | Esperado | ✔/✘ |
|---|---|---|
| `01_capa_v23.mp3` | capa rosa/roxa com disco escuro e centro amarelo, 64×64 no meio | |
| `02_capa_v24.mp3` | capa azul com anéis laranja e faixa branca à esquerda | |
| `03_capa_v24_cabecalho_estendido.mp3` | listras verdes e creme (imagem 200×120 esticada) | |
| `04_capa_progressiva.mp3` | quadrado cinza com nota | |
| `05_capa_png.mp3` | quadrado cinza com nota | |
| `06_sem_capa.mp3` | quadrado cinza com nota | |
| `07_sem_tag.mp3` | quadrado cinza com nota | |
| Trocar de faixa com `>>|` e `|<<` entre 01→04→02 | capa troca certo; título, tempos, ícones e barra iguais à RC6 | |
| Sair (M → Voltar ao início) e voltar à música 10× | sem reinício, capa volta | |
| Abrir Fotos com música tocando (E1) | abre como antes | |
| Música com `.lrc` (se tiver) | letra aparece por cima da capa | |
| Config | Informações = "Reload 1.0 RC7"; Atualizar por SD funciona | |

## Bytes permitidos
Além dos da RC6: `0x131E80..0x131E82`, `0x131E9E..0x131EA0`, `0x131EB6..0x131EBA`,
`0x13225E..0x132262`, `0x1A8000..0x1AB000`.

## Arquivos protegidos (NÃO ALTERAR sem o arquiteto)
`tests/test_rc2.py` … `tests/test_rc7.py`, `tests/emu_rc7.py`, `tests/test_catraca.py`,
`tests/LIMITE_EXCECOES.txt`, `tools/ci.sh` (hashes em `tests/PROTEGIDOS.sha256`); os ativos
de `tests/assets/rc7/` são presos pelo sha dentro do `test_rc7.py`.
Dependência nova: `unicorn` (`python3 -m pip install --user unicorn`; o `ci.sh` avisa).

## Para a sessão glm-5.3 (Fases C e D)
1. R0 desta ficha pelo Codex Sol high (`codex exec -s read-only`, 1ª linha APROVADO/REPROVADO);
   achado → teste novo protegido + linha em `docs/seguranca.md` (protegido = pedir ao arquiteto).
2. Despacho do MiniMax M3 neste worktree (§16; `opencode.json` com `opencode-go/minimax-m3`,
   skip-worktree; `DESPACHO-007.md`; mensagem terminando em `FIM-007` sozinho numa linha).
3. `sh tools/ci.sh` verde; 1ª análise do diff (Sol high, `privado-completo...HEAD`); correções R1/R2
   revisadas só no diff; conferência final Astra medium; 2 reprovações com MÉDIA → `ESCALADA-007`.
4. Pacote nesta ficha + linha em `docs/metricas.md` + commit; `PRONTO-007`.
Se um teste protegido parecer errado: **PERGUNTA-DECISOR 007** (não alterar).

## Revisão da ficha (Codex)
(a preencher — R0)

## Entrega (preenchida pelo desenvolvedor)

### O que foi feito
- **Três arquivos novos** (a regra do projeto é 350 linhas por ferramenta, D06):
  - **`tools/fab_capa_album.py`** (322 linhas) — a ferramenta da receita:
    as premissas, a escrita, a conferência do resultado e a linha de
    comando (`--in/--out/--em/--dry-run`);
  - **`tools/capa_album_asm.py`** (161 linhas) — o módulo do layout do
    lote, dos encoders do Thumb-2 (o mesmo par encoder/leitor que o
    `test_rc7.py` usa), da montagem do `.text` e da conferência dele;
  - **`tools/capa_album.s`** (assembly Thumb-2, montado pelo clang via
    `tools/asm.py`). **Sem compilador C**: a saída muda com a versão do
    compilador e a catraca quebraria.
- **`tools/build.py`**: `RELOAD_1_0_RC7 = RELOAD_1_0_RC6 + [fab_capa_album.py]`,
  `RECEITAS["reload_1.0_rc7"]`, `MAPA["fab_capa_album.py"] = (0x001A8000,
  0x3000)` e `AREA_FIM` de `0x001A8000` para `0x001AB000` (o vigia do
  pipeline passa a cobrir o lote novo). O lote não cruza nenhum lote
  declarado acima (o `fab_home_moldura` termina em 0x001A6480).
- **O que o código novo faz** (as três rotinas do lote, em
  `tools/capa_album.s`):
  - `CRIA` (0x00DAA01C): cria o fundo (o 1º `lv_img`, para a capa ficar
    acima do papel de parede), o contexto (`calloc(1, 0x2210)` = dsc 12 B +
    img 4 B + dois caminhos de 256 B + 8192 B de pixels; a ficha limita a
    0x2400), a imagem da capa, `lv_img_set_src(img, 0x00DA8000)`,
    `lv_obj_align(img, 2, 0, 42)` e o `lv_obj_add_event_cb(img, 0x00DAA019,
    0x21, ext)`. Sem memória ou sem objeto: o quadrado cinza e
    `[view+0x30] = 0`. Devolve `r0 = fundo`.
  - `TITULO` (0x00DAA020): `lv_label_set_text` **primeiro e uma vez só**;
    depois, se a view existir, se o rótulo for o do título (`[view+4]`) e
    se o contexto existir, `get_path(origem, índice, buf)`; caminho igual
    ao último → nada; caminho novo → guarda, mostra o quadrado cinza e
    tenta a capa; só se tudo der certo é que a imagem passa a ser a do
    contexto.
  - `APAGA` (0x00DAA024): cb do `LV_EVENT_DELETE`; se a view atual ainda
    aponta para o contexto, zera `[view+0x30]` e libera o contexto.
  - A capa: `f_open` (só leitura), tag ID3v2 v3/v4 (unsync recusado,
    cabeçalho estendido pulado, tamanho synchsafe), laço de quadros com a
    **regra do R0** (o tamanho é comparado com o que resta da tag **antes**
    de qualquer avanço; nada de `10 + tam` em 32 bits), corpo do APIC
    (codificação, MIME, tipo, descrição), só JPEG **baseline** (o SOF0
    é procurado marcador a marcador; `C1..CF` menos `C4/C8/CC` e
    `D9/DA` antes do SOF → cinza), decodificação com o **TJpgDec da
    fábrica** e leitor próprio (limitado ao fim do quadro; pular =
    `f_lseek`), escala `s` = maior de 0..3 com `w>>s ≥ 64` e `h>>s ≥ 64`,
    e a saída 64×64 com o pixel `(ox,oy)` = `(ox·W/64, oy·H/64)` da
    imagem reduzida e **os bytes trocados** (`LV_COLOR_16_SWAP`).
- **Nenhum teste, `tools/ci.sh` ou arquivo protegido tocado.**
  `sh tools/ci.sh`: **verde** (round-trip + RC2..RC7 + catraca, `CI OK`).

### Imagem
    receita   reload_1.0_rc7  (RC6 catraca af3a2b6d... + fab_capa_album.py)
    sha256    a74d3386abd3301a0c695f5fc9ed72e55228ca4c15370c39a0e96adb18ad1971
    2 MiB; build reprodutível: duas execuções seguidas, o mesmo sha
    RC6 → RC7: 10645 bytes, menor offset 0x131E80, maior 0x1AA995
      0x131E80..0x131E82  o tamanho da view (0x30 -> 0x34)
      0x131E9E..0x131EA0  o memset da view (0x30 -> 0x34)
      0x131EB6..0x131EBA  o `bl` do lv_img_create -> CRIA
      0x13225E..0x132262  o `b.w` do lv_label_set_text -> TITULO
      0x1A8000..0x1AA996  o lote: dsc, placeholder, tabela e código
                           (o resto do lote, 0x1AA997..0x1AB000, fica 0xFF)
    nada abaixo de 0x00E000; setor 0x00D000 e PSMP (0x1FC000+) intocados

### Decisões
- **A entrada é a RC6 pelo sha256** (`af3a2b6d…`), como a ficha manda: é a
  premissa única, e as outras conferências (os bytes de fábrica dos
  ganchos e dos tamanhos, o lote virgem, o TJpgDec intacto, o sha do
  quadrado cinza e a conferência do `.text` montado) continuam todas no
  código, nomeadas, para dizer *o que* está errado.
- **O código é assembly e não C** (a ficha): o `.text` é montado pelo
  clang, que só faz o Thumb-2; sem linkador, toda chamada para fora é
  `movw/movt + blx` (o bit do Thumb no endereço) e toda chamada interna
  é um `bl` relativo, resolvido pelo montador.
- **O `.text` começa pelos três trampolins** (`CRIA`, `TITULO`, `APAGA`)
  em endereços fixos (0x00DAA01C/20/24) e a **tabela de entradas** do
  lote (0x00DAA010/14/18) aponta para eles com `b.w`. O cb do
  `LV_EVENT_DELETE` é registrado como **0x00DAA019** — a entrada da
  tabela, como a ficha diz — e não o trampolim.
- **O contexto tem dois caminhos** (o guardado e o novo, 256 B cada):
  o `get_path` pode não terminar a string (o `strncpy` da fábrica
  copia até 0xFF bytes sem o `0`), e a comparação "é a mesma faixa?"
  precisa do caminho novo separado do guardado. 8720 B no total, contra
  o teto de 0x2400 da ficha.
- **O descritor do quadrado cinza** fica em 0x001A8000 com o `data`
  apontando para os pixels (0x00DA8010), e os pixels são os 8192 bytes
  do modelo aprovado, byte a byte.
- **A decodificação acontece no contexto, não no global**: o `JDEC` (0x138
  B = o `JDEC` da fábrica 0x118 + 0x20 do nosso contexto), o pool (0xE00,
  como a ficha) e o `FIL` (0x25C) são alocados e liberados em volta da
  chamada; o global 0x81CDE8 do visualizador de fotos não aparece no
  código (D11).
- **O leitor do TJpgDec é nosso e limitado**: ele guarda a posição e o
  fim da imagem no contexto e nunca lê depois do fim do quadro; o
  arquivo é reposicionado no começo da imagem antes do `jd_prepare`,
  porque o TJpgDec lê o cabeçalho desde o FFD8.

### Verificações feitas (além dos testes protegidos)
- **As únicas funções de fábrica chamadas são as 15 da ficha**
  (calloc, free, get_path, f_open, f_read, f_lseek, f_close, jd_prepare,
  jd_decomp, lv_img_create, lv_img_set_src, lv_obj_align,
  lv_obj_add_event_cb, lv_label_set_text, memset) — conferido no `.s`.
- **Pilha**: a maior descida do SP medida no emulador do arnês
  (`tests/emu_rc7.py`, com um hook por instrução por cima) durante o
  `TITULO` com capa foi de **384 bytes (0x180)**, contando as rotinas da
  fábrica (jd_prepare/jd_decomp). A pilha da ViewTask é de 0x1000 (4096):
  9% dela. É a medição que o R0 pediu (BAIXA): o **arnês** continua não
  medindo (protegido, não tocado).
- **Memória**: o pico vivo durante a busca da capa é de 4500 B
  (FIL 604 + JDEC/contexto 312 + pool 3584), contra o teto de 0x1800
  da ficha; e o contexto tem 8720 B, contra o teto de 0x2400.
- **Os pixels batem byte a byte** com o TJpgDec da fábrica emulado
  (erro máximo 0 por pixel) nos seis casos de capa do `test_d2_capas`.

### Pendências / não coberto
- **Nada foi gravado no aparelho**: o roteiro da ficha continua inteiro
  (os 7 MP3, a troca de faixa, as 10 entradas e saídas, o E1 com a
  música tocando). Toda a conferência aqui é de emulação.
- **D14 (trava da GUI enquanto decodifica)**: o risco é aceito pela
  ficha, mas o código novo roda na ViewTask e o tempo de decodificação
  de uma capa grande (500×500, escala 2) **não foi medido** — o roteiro
  mede.
- **A BAIXA do R0 sobre a RAM sem vigia de escrita** continua em pé como
  vigia: o código não toca o global 0x81CDE8 (nem o cita), e o
  contexto é próprio, mas isso é contrato + revisão do diff, não
  medição.
- **Sugestão (fora do escopo, não implementada)**: na troca de faixa o
  `lv_img_set_src` do quadrado cinza é chamado **duas** vezes (uma antes
  de tentar a capa, outra só se a capa falhar; no caminho feliz a capa
  entra no mesmo instante, sem redesenho intermediário). A ordem é a que
  a ficha descreve ("caminho novo → guarda; `lv_img_set_src(img,
  0xDA8000)`; tenta a capa"), e por isso fica como está; se quem mantiver
  a ficha quiser o set_src só no fracasso, é uma linha a menos.

### Danos notados
- **Nenhum dano novo** encontrado: o que o rascunho anterior tinha
  (ver Rodadas) era defeito de implementação, não de projeto — e
  nenhum deles chegou a ser gravado em aparelho.
- **D13 (gravação interrompida)** e **D14 (pausa na tela)**: inalterados
  (riscos aceitos pela ficha). O lote novo é o mais alto da RC7: se a
  gravação parar entre 0x132000 e 0x1A8000, a Tocando Agora reinicia
  (como nas RCs anteriores).

## Rodadas
- **Rodada 1 (retomada, 2026-10-31, MiniMax M3)**: o trabalho começou
  de um **rascunho sem commit** (`tools/fab_capa_album.py` com 419 linhas,
  acima do limite de 350, e `tools/capa_album.s` com 1105). O rascunho
  **não foi aproveitado como está**: conferido contra a ficha, ele tinha
  **onze defeitos**, todos corrigidos aqui (e nenhum deles apareceu num
  aparelho, porque nada foi gravado):
  1. `get_path` era chamado com **quatro** argumentos
     (`AUDIO, origem, índice, buf`) em vez de `(origem, índice, buf)`: a
     origem virava o endereço da struct e o índice, a origem;
  2. o descritor do quadrado cinza apontava o `data` para **o próprio
     descritor** (0x00DA8000) em vez dos pixels (0x00DA8010);
  3. o cb do `LV_EVENT_DELETE` era registrado como 0x00DAA025 (o
     trampolim) em vez de **0x00DAA019** (a entrada da tabela), como a
     ficha e o teste pedem;
  4. o **leitor do TJpgDec deixava a pilha desbalanceada em 8 bytes** no
     caminho de "pular" (o `sub sp` do contador do `f_read` não era
     desfeito): o `pop` trazia lixo e o PC saltava para dentro do JPEG
     (0xFFD8) — trava na hora de decodificar;
  5. a varredura dos marcadores do JPEG começava **2 bytes antes** da
     posição real do arquivo: cada salto de segmento caía 2 bytes antes
     e o SOF nunca era achado (nenhuma capa aparecia);
  6. ao pular um quadro que não é APIC, **só o contador andava**: o
     ponteiro do arquivo ficava no corpo do quadro e a leitura seguinte
     era do lugar errado (a tag ficava ilegível);
  7. o arquivo **não voltava para o começo da imagem** antes do
     `jd_prepare`: o TJpgDec lia do meio do JPEG;
  8. em `saida`, o destino **não somava `ox_lo*2`**: todos os blocos do
     TJpgDec escreviam no começo da linha (só 4 dos 64 pixels de cada
     linha saíam, e o resto, zero);
  9. em `saida`, `ox_lo`/`ox_hi` eram calculados com **H no lugar de
     W** (imagem não quadrada saía errada);
  10. a conferência do código montado lia a tabela de entradas no
      deslocamento errado — ela jamais teria passado;
  11. sem memória, `[view+0x30]` não era zerado (a ficha pede).
- **Rodada 1 — resultado**: `sh tools/ci.sh` **verde** (23 testes da RC7,
  erro máximo 0 por pixel nos seis casos de capa; as 18 recusas do D3
  viram quadrado cinza, sem laço, sem arquivo aberto, sem vazamento e
  com o pico de memória medido).

## Pacote — Ficha 007 / Reload 1.0 RC7
(a preencher)

## Revisão da ficha (R0, glm-5.3 — D12)
REPROVADO (1 MÉDIA, 2 BAIXAS), `docs/tarefas/007-revisao-r0.md`. Decisor escolheu a opção A
(2026-10-30): o arquiteto acrescentou os casos hostis de tamanho de quadro (wrap em 32 bits e
synchsafe inválido no quadro) ao `test_d3_recusas` e a regra explícita no laço de quadros.
BAIXAS registradas, sem bloquear: pilha da ViewTask não medida pelo arnês (A15 segue PROVÁVEL; o
E1 no aparelho é evidência parcial); RAM sem vigia de escrita no arnês (D11, global `0x81CDE8`).

