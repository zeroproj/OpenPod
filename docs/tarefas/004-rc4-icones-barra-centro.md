# 004 — Reload 1.0 RC4: ícones novos na home + barra centralizada

- Tipo: Risco (imagem que vai para o aparelho)
- Desenvolvedor: MiniMax M3 (opencode.json do worktree)
- Analista: gpt-6-astra, esforço high
- Depende de: RC3.1 (gravada 2026-10-23: "Ficou alinhado"; vira catraca, sha `286e8ba8…`)
- Status: revisão R0 incorporada; liberada para implementação (decisor: "ja faz também a alteração dos icones")

## Objetivo
1. Relógio, "OpenPod" e bateria sobem 2 px e ficam no meio da barra
   (pedido do decisor na foto da RC3.1: "poderia subir um pouquinho…
   no meio da barra superior").
2. Os nove ícones da home viram os do estilo aprovado em 2026-09-24
   ("Apple-like moderno", `assets/IconesHome.png`), fundo preto, mantendo
   o degradê da barra da RC3.

Fora: bateria prata/verde (fica para a próxima RC), textos sob os ícones,
navegação.

## Evidência no ORIGINAL (CONFIRMADO, desmontagem)
- Relógio `0xD217B4`: `0x1217D2 movs r1,#1` · `0x1217D6 movs r3,#2` (y) ·
  `0x1217D8 movs r2,#3` (x) · `0x1217DA bl 0xD4A3A2` (`lv_obj_align`).
- Título (rótulo do cartão, RC3): `0x1226B6 movs r3,#2` (y) ·
  `0x1226BA movs r2,#6; nop` (RC3.1) · `0x1226BE movs r1,#2` ·
  `0x1226C0 bl 0xD4A3A2`.
- Bateria `0xD225B0`: `0x12260E movs r2,#y` (fábrica 0, RC3.1 2) ·
  `0x122612 movs r1,#0x6b` · `0x122614 bl 0xD4A2D4` (`set_pos`).
- Medido na foto da RC3.1: texto ocupa y≈4..14 numa barra 0..15 → centro
  9 contra 7,5. Subir 2 → y 2..12.
- Folha da home: `lv_img_dsc` INDEXED_8 128×160, cabeçalho `0x0CDD50`
  (12 B), paleta 256×BGRA `0x0CDD5C` (sem pré-inversão: entrada 1 de
  fábrica = `00 00 00 ff`, preto), pixels `0x0CE15C..0x0D315C`. Linhas
  0..15 são a barra (RC3 pinta o degradê nelas). Navegação por índice,
  não pelo desenho (`docs/PLANO_HOME.md` §1.2).
- `assets/IconesHome.png`: 128×160 RGB, sha `fbdd1dc7…`, ícones nas
  mesmas posições dos de fábrica, fundo `(0,0,0)`.

## Escopo — receita `reload_1.0_rc4` = `reload_1.0_rc3` + exatamente, nesta ordem:

### `fab_barra_centro.py`
- `0x1217D6` `02 23` → `00 23`; `0x1226B6` `02 23` → `00 23`;
  `0x12260E` `02 22` → `00 22`.
- Premissas (recusa se não bater): 2 MiB; os três pontos com os bytes da
  RC3 acima; `0x1217D2`=`0121`, `0x1217D8`=`0322`, `0x1217DA` = `bl 0xD4A3A2`;
  `0x1226BA`=`062200bf`, `0x1226BE`=`0221`, `0x1226C0` = `bl 0xD4A3A2`;
  `0x122612`=`6b21`, `0x122614` = `bl 0xD4A2D4`; título da RC3 inteiro:
  `0x1226CA`=`00bf00bf`, `0x1226F4` = `0x00DA7040`, `0x1A7040` =
  `"OpenPod\0"`. Recusa o ORIGINAL.

### `fab_icones_home.py`
- Lê `--png` (padrão `assets/IconesHome.png`); recusa se o sha não for
  `fbdd1dc7…` ou o tamanho não for 128×160.
- Paleta: entradas 0..15 = cor EXATA da linha y do degradê
  (`topo (64,70,82) + (base (14,16,19) − topo)·y/15`, arredondado), as
  outras 240 = quantização das linhas 16..159 do PNG, com `(0,0,0)` exato
  presente. Todas com alfa 255. Formato BGRA.
- Pixels: linha y (0..15) toda índice y; linhas 16..159 = índice da cor
  mais próxima; pixel `(0,0,0)` do PNG → entrada `(0,0,0)`. Erro médio
  ≤ 2,0 por canal **e nenhum pixel com erro > 64 num canal** (pega glifo
  apagado; quantização simples dá máx. 58).
- Cabeçalho intocado. Escreve só `0x0CDD5C..0x0D315C`.
- Premissas: 2 MiB; cabeçalho e paleta iguais à fábrica; linhas 16..159
  iguais à fábrica; cada linha 0..15 uniforme (aceita ORIGINAL e RC3).

Ambas: `--in/--out/--dry-run`; recusam antes de escrever (sem criar
saída), `--out` igual/symlink/hardlink de `--in`, 2ª passagem. Docstring
no padrão de `tools/`. Nenhuma ferramenta proibida (lista em
`tests/test_rc4.py`, inclui `patch_icones_home.py`), nem código copiado
delas.

## Critérios de aceite (`tests/test_rc4.py`)
- [ ] C0 receita constrói, 2 MiB
- [ ] C1 RC3.1 reprodutível (catraca `286e8ba8…`)
- [ ] C2 receita = RC3 + as duas ferramentas; sem proibidas; PNG com o sha aprovado
- [ ] C3 os três pontos da barra
- [ ] C4 cabeçalho intocado; paleta alfa 255 e degradê exato nas 0..15; barra em índice y; ícones fiéis ao PNG, fundo preto exato
- [ ] C5 só bytes permitidos; nada abaixo de `0xE000`; PSMP intocada
- [ ] D3 recusas (bordas, ORIGINAL no centro, PNG adulterado, links, 2ª passagem, `--dry-run`)

## Danos possíveis
| # | Dano | Coberto por |
|---|---|---|
| D1 | ícone na posição errada → navegação parece trocada | PNG aprovado, mesmas posições; roteiro |
| D2 | paleta com alfa ≠ 255 → buracos/transparência | C4 |
| D3 | ferramenta escreve sobre imagem diferente da esperada | premissas + testes de recusa |
| D4 | barra da home perde o degradê | C4 (entradas 0..15 exatas) |
| D5 | texto da barra cortado no topo (y=0) | fonte de 12 px em barra de 16; roteiro |
| D6 | bateria sobe nos menus e encosta no topo | volta ao y de fábrica (0); roteiro |
| D7 | escrita fora do permitido / bootloader / PSMP | C5 |
| D8 | `.up` errado | `gera_versao` [4/4] |

## Riscos aceitos (decisor)
- A home fica com fundo preto (o PNG aprovado é preto), não mais o
  cinza-azulado de fábrica.
- Tocando Agora e Livro continuam os dois laranja (aprovado em 2026-09-24).

## Roteiro no aparelho
| Fluxo | Passos | ✔/✘ |
|---|---|---|
| Home | ícones novos, fundo preto, barra com degradê | |
| Barra | relógio, "OpenPod" e bateria no meio da barra, mesma altura | |
| Navegação | cada ícone abre a tela certa (Música, Vídeo, Gravação, Rádio, Livro, Imagem, Bluetooth, Configurar, Pastas) | |
| Seleção | o destaque do ícone selecionado aparece e anda certo | |
| Menus | bateria sem cortar no topo | |
| Configurar | Informações = "Reload 1.0 RC4"; Atualizar por SD funciona | |

## Bytes permitidos
Além dos da RC3: `0x1217D6..0x1217D8`, `0x1226B6..0x1226B8`,
`0x12260E..0x122610`, `0x0CDD5C..0x0D315C`.

## Arquivos de teste protegidos
- `tests/test_rc2.py`, `tests/test_rc3.py`, `tests/test_rc4.py`, `tools/ci.sh`

## Revisão da ficha (Codex)
R0 — gpt-6-astra high, 2026-10-23: REPROVADO (1 ALTA, 2 MÉDIA). Incorporado:
- ALTA (kit, fora das ferramentas da ficha): `gera_versao.py` agora para se
  a imagem ou o `.up` mexerem no setor `0xD000` (antes só conferia o
  bootloader até `0xD000`) e se a imagem tocar na PSMP. Feito pelo
  engenheiro, que é dono do kit.
- MÉDIA: premissas do `fab_barra_centro` cobrem o título inteiro da RC3
  (fonte, ponteiro, texto) — testes de recusa em `0x1226CA`, `0x1226F4`,
  `0x1A7040`.
- MÉDIA: erro máximo por pixel ≤ 64 (microfone apagado passaria só com a
  média).

## Entrega (preenchida pelo desenvolvedor)

## Rodadas
