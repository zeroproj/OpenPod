# 005 — Reload 1.0 RC5: textos em português revisados + nomes curtos na home

- Tipo: Risco (imagem que vai para o aparelho)
- Desenvolvedor: MiniMax M3 (opencode.json do worktree)
- Analista: gpt-6-astra, esforço high
- Depende de: RC4 (rodando no aparelho, foto de 2026-10-23; vira catraca `74e8cb31…`)
- Status: ficha escrita — aguardando revisão astra. Decisor: "Faz a RC4.1 e 5 tudo junto" (2026-10-23)

## Objetivo
1. Os nomes da home cabem nos 40 px do rótulo, sem corte nem rolagem:
   Música, Livros, Vídeo (V maiúsculo), Fotos, Gravar, Pastas, BT, Config.
2. Os textos em português do sistema saem da revisão `docs/TEXTOS_REVISAO.md`
   (traduções erradas, "ecrã"/"ficheiro", textos que não cabem).

Fora: outros idiomas, fontes, tamanho dos rótulos, capa do álbum (RC6).

## Evidência no ORIGINAL (CONFIRMADO, desmontagem)
- `0xD2108C(id)`: idioma atual por `0xD0E2B8` (0..8, `tbb`); cada idioma é
  uma tabela de 216 ponteiros XIP. Português = idioma 8, tabela em
  `0xC53B84` (arquivo `0x053B84..0x053EE4`), literal em `0x121104`.
  Conferido: id 1 "Música", 3 "vídeo", 8 "Ver pastas".
- Home: rótulo de cada ícone criado em `0xD2ED24` com texto
  `0xD2108C(id)`, tamanho `40×15` (`0xD2ED5C/5E`), modo longo 0 e 3 (rola)
  no selecionado — por isso "Gravaç", "Blueto", "onfigur:".
- A RC1 repontou os ids 40 e 91 ("Atualizar por SD"). Nesta RC eles não
  mudam.
- Fonte dos menus: cmap de 7098 `u16` em `0x0A27E6`, avanço do glifo em
  `0x086C44 + g·16 + 4`. Todos os caracteres dos textos novos existem.
- Único texto com `%`: id 96, mantém `%%` (string de formato).

## Conteúdo
`assets/textos_pt.tsv` (sha `44e82c41…`): `id<TAB>texto`, `\n` = quebra.
180 ids: os 175 da revisão (menos 40 e 91, da RC1) + os 8 da home. Total
~2,9 KB.

## Escopo — receita `reload_1.0_rc5` = `reload_1.0_rc4` + `fab_textos.py`
- Lê `--textos` (padrão `assets/textos_pt.tsv`); recusa se o sha não for o
  fixado, se um id estiver fora de 0..215, for 40/91 ou repetir.
- Grava as strings UTF-8 com NUL no lote `0x1A5000..0x1A6000` (novo no
  `MAPA`, sem cruzar ninguém) e reaponta só as entradas da tabela dos ids
  da lista. Nunca edita string de fábrica no lugar.
- Premissas (recusa antes de escrever): 2 MiB; literal `0x121104` =
  `0x00C53B84`; cada id da lista aponta para a string de FÁBRICA (ponteiro
  igual ao ORIGINAL); ids 40 e 91 com os ponteiros da RC1 (≠ fábrica, na
  área livre); lote todo `0xFF`; cmap e tabela de avanços iguais ao
  ORIGINAL; todo caractere com glifo; especificadores `%` iguais aos de
  fábrica; ids da home ≤ 40 px.
- `--in/--out/--dry-run/--textos`; recusa `--out` igual/symlink/hardlink de
  `--in` e 2ª passagem. Não usa nem copia código de `aplica_textos.py`,
  `patch_menu_text.py`, `relocate_lang_table.py`, `propoe_textos.py`.

## Critérios de aceite (`tests/test_rc5.py`)
- [ ] C0 constrói · C1 catraca RC4
- [ ] C2 receita = RC4 + `fab_textos.py`; lote no `MAPA` sem cruzar; conteúdo com o sha fixado
- [ ] C3 cada id → string nova no lote; demais ids e strings de fábrica intocados
- [ ] C4 glifos, `%` iguais, home ≤ 40 px, nomes da home
- [ ] C5 só tabela (ids da lista) + lote; nada abaixo de `0xE000`; PSMP
- [ ] D3 recusas

## Danos possíveis
| # | Dano | Coberto por |
|---|---|---|
| D1 | `%` diferente → printf lê lixo / trava | C4 formato |
| D2 | caractere sem glifo → quadrado ou texto cortado | C4 glifos |
| D3 | ponteiro para fora / string sem NUL | C3 (lê pelo ponteiro até o NUL dentro do lote) |
| D4 | desfaz a RC1 ("Atualizar por SD") | ids 40/91 fora da lista e como premissa |
| D5 | texto novo grande demais para a tela | home testada (40 px); demais medidos na revisão (113 px), roteiro |
| D6 | outro idioma afetado | só a tabela 8 muda (C5) |
| D7 | gravação interrompida entre `0x053000` e `0x1A5000` → textos lixo | risco aceito (mesmo da RC1–RC4); recuperação pelo cartão/cabo |

## Riscos aceitos (decisor)
- "BT" e "Config" na home (e nos títulos das telas). "Ajustes" mede 41 px,
  não cabe.
- Textos dos menus mudam em todo o sistema; algum pode ficar estranho em
  contexto — o roteiro pede foto das telas principais.

## Roteiro no aparelho
| Fluxo | Passos | ✔/✘ |
|---|---|---|
| Home | nomes inteiros: Música, Vídeo, Gravar, Rádio, Livros, Fotos, BT, Config, Pastas | |
| Música | "Todas as músicas", "Artistas", "Álbuns", "Favoritas", "Tocando agora" | |
| Config | itens legíveis, "Atualizar por SD" continua e funciona | |
| Bateria fraca | (se der) mensagem "Bateria abaixo de 10%" | |
| Sem arquivos | abrir Vídeo/Fotos sem arquivos → "Nenhum vídeo/imagem encontrado" | |
| Idioma | trocar para English e voltar: inglês intacto | |

## Bytes permitidos
Além dos da RC4: as entradas `0x053B84 + 4·id` dos ids da lista e
`0x1A5000..0x1A6000`.

## Arquivos de teste protegidos
- `tests/test_rc2.py` … `tests/test_rc5.py`, `tools/ci.sh`

## Revisão da ficha (Codex)
(pendente)

## Entrega (preenchida pelo desenvolvedor)

## Rodadas
