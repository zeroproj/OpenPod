# 002 — Reload 1.0 RC3: "OpenPod" na barra superior + degradê

- Tipo: Risco (imagem que vai para o aparelho; primeira rotina na área livre da Reload)
- Desenvolvedor: MiniMax M3 (opencode.json do worktree)
- Analista: gpt-6-astra, esforço high
- Depende de: RC2 (aprovada no aparelho em 2026-10-21)
- Status: ficha escrita — aguardando revisão astra e aprovação do decisor

## Objetivo
A barra superior ganha um degradê vertical (cinza-azulado no topo → quase
preto embaixo) na home e nas 52 telas de menu/lista, e a home passa a
mostrar "OpenPod" centralizado entre o relógio e a bateria. Tudo o que a
RC1 e a RC2 entregaram continua igual.

## Escopo
- Inclui: receita `reload_1.0_rc3` em `tools/build.py` = os passos da
  `reload_1.0_rc2` + **exatamente duas ferramentas novas**, nesta ordem:
  - `tools/fab_barra_degrade.py` — itens 1 e 2;
  - `tools/fab_barra_titulo.py` — item 3.
  Interface: `--in <bin> --out <bin> [--dry-run] [--em <hex>]`. Com
  `--dry-run`, confere tudo e imprime o que faria, **sem criar a saída**.
  `--em`, se vier, tem de ser igual ao endereço fixo da ferramenta (abaixo);
  outro valor → recusa.
- Entradas no `MAPA` do `build.py`: `"fab_barra_degrade.py": (0x001A7000, 0x0040)`
  e `"fab_barra_titulo.py": (0x001A7040, 0x0010)`.
- **Recusa antes de escrever (D3):** cada ferramenta confere TODAS as suas
  premissas (lista em "Evidência") e, se qualquer uma falhar, sai com código
  ≠ 0 **sem criar o arquivo de saída** e sem tocar a entrada. `--out` que
  seja a própria entrada por qualquer via (caminho, symlink, hardlink) →
  recusa. Segunda passagem → recusa (a premissa de fábrica já não existe).
- Não inclui: ícones, bateria (RC4); degradê na Tocando Agora (o papel de
  parede é imagem própria, fica preto como na RC2); carimbo e kit (engenheiro).
- **Proibido**: usar, importar ou copiar qualquer ferramenta listada em
  `PROIBIDAS` de `tests/test_rc3.py` — inclui `patch_nome_faixa`,
  `patch_faixa_degrade`, `patch_status_bar`, `fix_status_bar`,
  `patch_titulos`. Thumb-2 e `bl` codificados dentro de cada ferramenta,
  só stdlib.

## Evidência no ORIGINAL (verificada pelo engenheiro em 2026-10-21)
Base XIP `0x00C00000`. Thumb-2, little-endian. Endereços sem `0xC` = offset no arquivo.
LVGL 8.0/8.1: caminhos de fonte `gui8\lvgl\src\draw\lv_draw_blend.c` (antes
do `draw/sw/` da 8.2); IDs de propriedade batem com a 8.1.

1. **Faixa das telas — `CRIA_FAIXA` `0xD216F0`** (52 chamadores, todos
   `page_*_create`, ex.: `page_music_menu_create`, `page_set_menu_create`,
   `page_folder_list_create`). Cria o objeto, largura = tela, e aplica:
   ```
   0xD2171A bl 0xD2138A        ; r0 = 0x0000 (preto)
   0xD2171E movs r2,#0 ; mov r1,r0 ; mov r0,r4
   0xD21724 bl 0xD4D092        ; set_style_bg_color(obj, cor, 0)   <- GANCHO
   0xD21728 bl 0xD21384 ...    ; texto branco, borda, etc. (segue intacto)
   ```
   A altura vem do chamador (160/7 = 22 px na maioria, 16 px em uma).
   - `0xD4D092` = wrapper de `BG_COLOR` (prop `0x20`): monta o valor e faz
     `b.w 0xD4CAC4` com `r1=0x20, r2=cor, r3=seletor`.
   - `0xD4CAC4` = `lv_obj_set_local_style_prop(obj, prop, valor, seletor)`:
     todos os wrappers (`0x20, 0x21, 0x26, 0x30, 0x33, 0x60, 0x1032, 0x457`)
     terminam nele com esse contrato. CONFIRMADO.
   - Não há wrapper para `BG_GRAD_COLOR`/`BG_GRAD_DIR` (o linker tirou), mas
     o desenho lê as duas: `lv_obj_init_draw_rect_dsc` em `0xD49B9C` busca
     `0x21` (opa), `0x4020` (cor), **`0x23` (direção, 3 bits)**,
     **`0x4022` (cor do degradê)**, `0x24`, `0x25`. CONFIRMADO.
2. **Home — folha `0x0CDD50`** (INDEXED_8 128×160, cabeçalho `0x1402000A`,
   paleta `0x0CDD5C`, pixels `0x0CE15C`). A home **não** usa a `CRIA_FAIXA`;
   relógio e bateria ficam sobre a folha. Linhas y=0..15 são todas índice 1
   (preto); os ícones começam em y=16. As 256 entradas da paleta estão em
   uso → o degradê usa as cores que já existem (mais próximas), sem mexer na
   paleta.
3. **Rótulo do cartão — `0xD226AC`** (`view_p[0x14]`), criado em `0xD23898`
   só na página 1 (home) ou `0x51`, e só com cartão presente (`0xCFE714`).
   Ao remover o cartão, `0xD23EA8` apaga o rótulo; ao inserir, recria.
   Nenhum outro código troca o texto dele (varredura de `[rX,#0x14]` na
   camada view). Bytes de fábrica:
   ```
   0x1226BA 6ff01d02  mvn r2,#0x1d        ; x_ofs = -30
   0x1226BE 0321      movs r1,#3          ; TOP_RIGHT  (y_ofs r3 = 2)
   0x1226CA 2af030fd  bl 0xD4D12E         ; set_style_text_font(fonte de ícones 0x819D00)
   0x1226F4 14d6c500  pool: texto = 0x00C5D614 (glifo)
   ```
   O relógio (`0xD217B4`) não define fonte e mostra texto com a fonte do tema.

## O que cada ferramenta escreve

### `fab_barra_degrade.py`
- **Rotina em `0x1A7000`** (XIP `0xDA7000`), exatamente esta, 44 bytes, o
  resto do lote fica `0xFF`:
  ```
  push  {r4, lr}
  mov   r4, r0
  movw  r1, #0x2A42      ; topo  RGB(64,70,82)  pré-invertido (LV_COLOR_16_SWAP)
  movs  r2, #0
  bl    0xD4D092         ; bg_color = topo
  mov   r0, r4
  movs  r1, #0x22        ; BG_GRAD_COLOR
  movw  r2, #0x8208      ; base  RGB(14,16,19)  pré-invertido
  movs  r3, #0
  bl    0xD4CAC4
  mov   r0, r4
  movs  r1, #0x23        ; BG_GRAD_DIR
  movs  r2, #1           ; LV_GRAD_DIR_VER
  movs  r3, #0
  pop.w {r4, lr}
  b.w   0xD4CAC4         ; chamada de cauda: volta direto para 0xD21728
  ```
- **Gancho:** `0x121724` `bl 0xD4D092` → `bl 0xDA7000`. O `r1` (preto) que
  chega é ignorado; `r4` é preservado; quem chama não usa `r0..r3` depois.
- **Home:** cada linha y=0..15 da folha recebe um único índice: a cor de
  paleta (alfa 255) mais próxima de `topo + (base − topo)·y/15`. Erro máximo
  por canal ≤ 12; a luminância nunca sobe de uma linha para a seguinte.
- Premissas: tamanho 2 MiB; `CRIA_FAIXA` `0x1216F0..0x121764` igual à
  fábrica (o `bl` do gancho decodifica para `0xD4D092`); `0xD4D092..0xD4D0B4`
  e `0xD4CAC4..0xD4CB04` iguais à fábrica; lote `0x1A7000..0x1A7040` todo
  `0xFF`; cabeçalho + paleta da folha iguais à fábrica; linhas 0..15 todas
  índice 1.

### `fab_barra_titulo.py`
- Texto `b"OpenPod\0"` em `0x1A7040` (XIP `0xDA7040`), resto do lote `0xFF`.
- `0x1226BA` → `00 22 00 bf` (`movs r2,#0 ; nop`, centro exato);
  `0x1226BE` → `02 21` (TOP_MID); `0x1226CA` → `00 bf 00 bf` (sem fonte de
  ícones: herda a do tema, como o relógio); `0x1226F4` → `0x00DA7040`.
- Premissas: tamanho 2 MiB; `0x1226AC..0x1226F8` igual à fábrica (inclui os
  quatro pontos acima e o `bl` da fonte decodificando para `0xD4D12E`);
  `0x123898` `bl 0xD226AC`; lote `0x1A7040..0x1A7050` todo `0xFF`.

Ordem de escrita (R2) no kit: setor `0x1A7000` (rotina/texto) antes dos
setores dos ganchos (`0x121000`, `0x122000`). O engenheiro confere no
`gera_versao`.

## Critérios de aceite (todos em `tests/test_rc3.py`)
- [ ] C0 `reload_1.0_rc3` constrói e passa a validação do `build.py`
- [ ] C1 a RC2 continua reprodutível (`fcca5fdc…`) e a RC3 contém todos os bytes dela
- [ ] C2 receita = RC2 + as duas ferramentas, nessa ordem; sem ferramenta proibida; lotes no `MAPA` sem cruzar ninguém
- [ ] C3 o gancho chama `0xDA7000`; o resto da `CRIA_FAIXA` intocado; a rotina é a da ficha; cores pré-invertidas; funções chamadas intocadas
- [ ] C4 home: cabeçalho, paleta e ícones intocados; linhas 0..15 uniformes, perto do alvo, luminância descendo
- [ ] C5 título: os quatro pontos, o texto `OpenPod`, o resto do rótulo intocado
- [ ] C6 nenhum byte fora do permitido; nada abaixo de `0xE000`; PSMP intocada
- [ ] D3 recusa: entrada truncada, gancho/faixa/wrappers adulterados, lote ocupado, folha adulterada, pontos do título adulterados, chamador adulterado, `--em` errado, saída por link, segunda passagem; `--dry-run` não cria saída; aceita o ORIGINAL

## Danos possíveis
| # | Dano | Comportamento esperado | Teste |
|---|---|---|---|
| D1 | `bl` do gancho ou da rotina mal codificado → trava ao abrir qualquer menu | alvos decodificados == `0xDA7000`, `0xD4D092`, `0xD4CAC4` | C3 |
| D2 | rotina estraga registrador ou pilha → trava ou faixa errada | rotina exata da ficha (`r4` salvo, pilha par, cauda para a função de fábrica) | C3 |
| D3 | aplicada sobre imagem diferente da esperada | confere premissa e recusa | Recusa |
| D4 | escreve fora (folha, rotina vizinha, lote de outro) | só bytes permitidos | C4, C5, C6 |
| D5 | desfaz RC1/RC2 | RC3 contém a RC2 | C1 |
| D6 | código antigo entra escondido | receita e fontes sem nomes proibidos; procedência no diff | C2, revisão |
| D7 | bootloader / `0xD000` / PSMP | build e teste recusam | C6 |
| D8 | cor trocada por falta de pré-inversão (sai verde/rosa) | valores `0x2A42`/`0x8208` conferidos | C3 |
| D9 | degradê ilegível ou sobre o texto | roteiro no aparelho | roteiro |
| D10 | `.up` errado ou ordem de setores que deixa estado intermediário quebrado | `gera_versao` [4/4] OK; rotina antes do gancho | pacote |
| D11 | título some sem cartão / ao tirar o cartão | **comportamento de fábrica do rótulo, aceito** (ver Riscos) | roteiro |

## Riscos aceitos (decisor)
- "OpenPod" só aparece na home e **com cartão**; sem cartão, a home fica sem
  título (é o rótulo do ícone do cartão, que deixa de existir).
- Se o tema não der opacidade ao fundo da faixa, o degradê não aparece nas
  telas (nada quebra). PROVÁVEL que apareça: a faixa da fábrica pinta preto
  com o mesmo mecanismo.
- A Tocando Agora fica sem degradê nesta RC.

## Roteiro no aparelho (decisor, antes de aprovar)
| Fluxo | Passos | ✔/✘ |
|---|---|---|
| Abertura | liga com logo OpenPod sobre preto (RC2) | |
| Home | "OpenPod" no centro da barra, relógio à esquerda, bateria à direita; barra com degradê | |
| Menus | Música, Configurar, Pastas, Rádio, Gravador: faixa com degradê; títulos e seleção legíveis | |
| Cartão | tirar o cartão na home → título some; recolocar → volta | |
| Tocando Agora | toca normal, fundo preto | |
| Configurar | Informações = "Reload 1.0 RC3"; "Atualizar por SD" funciona | |

## Bytes permitidos
Além dos da RC2: `0x121724..0x121728`, `0x1A7000..0x1A7050`,
`0x0CE15C..0x0CE95C`, `0x1226BA..0x1226C0`, `0x1226CA..0x1226CE`,
`0x1226F4..0x1226F8`.

## Arquivos de teste protegidos
- `tests/test_rc2.py`, `tests/test_rc3.py`, `tools/ci.sh` (hash em `tests/PROTEGIDOS.sha256`)

## Revisão da ficha (Codex)
(pendente)

## Entrega (preenchida pelo desenvolvedor)

## Rodadas
