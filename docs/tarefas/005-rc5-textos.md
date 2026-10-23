# 005 — Reload 1.0 RC5: textos em português revisados + nomes curtos na home

- Tipo: Risco (imagem que vai para o aparelho)
- Desenvolvedor: MiniMax M3 (opencode.json do worktree)
- Analista: gpt-6-astra, esforço high
- Depende de: RC4 (rodando no aparelho, foto de 2026-10-23; vira catraca `74e8cb31…`)
- Status: revisão R0 incorporada; liberada para implementação. Decisor: "Faz a RC4.1 e 5 tudo junto" (2026-10-23)

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
`assets/textos_pt.tsv` (sha `c9cc64bd…`): `id<TAB>texto`, `\n` = quebra.
180 ids: os 175 da revisão (menos 40 e 91, da RC1) + os 8 da home. Total
~2,9 KB.

## Escopo — receita `reload_1.0_rc5` = `reload_1.0_rc4` + `fab_textos.py`
- Lê `--textos` (padrão `assets/textos_pt.tsv`); recusa se o sha não for o
  fixado, se um id estiver fora de 0..215, for 40/91 ou repetir.
- Grava as strings UTF-8 com NUL no lote `0x1A5000..0x1A6000` (novo no
  `MAPA`, sem cruzar ninguém) e reaponta só as entradas da tabela dos ids
  da lista. Nunca edita string de fábrica no lugar.
- Premissas (recusa antes de escrever): **sha256 da entrada = RC4
  `74e8cb31…`** (revisão R0: RC1–RC3 passariam nas outras premissas); 2 MiB; literal `0x121104` =
  `0x00C53B84`; cada id da lista aponta para a string de FÁBRICA (ponteiro
  igual ao ORIGINAL); ids 40 e 91 com os ponteiros da RC1 (≠ fábrica, na
  área livre); lote todo `0xFF`; cmap e tabela de avanços iguais ao
  ORIGINAL; todo caractere com glifo; especificadores `%` iguais aos de
  fábrica; ids da home ≤ 40 px; cada linha ≤ 113 px ou não mais larga que
  a de fábrica.
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
| D5 | texto novo grande demais para a tela | home ≤ 40 px; demais: cada linha ≤ 113 px ou ≤ a largura de fábrica (C4); roteiro |
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
R0 — gpt-6-astra high, 2026-10-23: REPROVADO (1 ALTA, 1 MÉDIA). Incorporado:
- ALTA: entrada tem de ser a RC4 exata (sha); teste recusa a RC3.
- MÉDIA: 3 textos ficavam mais largos que os de fábrica (52, 154, 161) e
  foram encurtados ("Nenhum arquivo", "Lendo arquivos.\nNão desligue.",
  "Carregue 10 min\nantes de usar"); teste novo: nenhuma linha passa de
  113 px a não ser que a de fábrica já passasse (avisos longos de fábrica
  quebram no widget; o novo nunca é mais largo).

## Entrega (preenchida pelo desenvolvedor)

### O que foi feito
- **`tools/fab_textos.py`** (739 linhas): a receita `reload_1.0_rc5`. Le a RC4,
  grava as 180 strings novas em UTF-8 com NUL no lote `0x1A5000..0x1A6000`
  (2799 bytes; 1297 sobram em 0xFF) e reponta **só** as 180 entradas da tabela
  (`0x053B84 + 4·id`) que a lista manda. Nenhuma string de fábrica é editada no
  lugar, nenhum outro id muda, nada fora dos bytes da ficha é tocado.
- **`tools/build.py`**: `RELOAD_1_0_RC5 = RELOAD_1_0_RC4 + [fab_textos.py]` e o
  lote `(0x001A5000, 0x1000)` no `MAPA`. O comentário do `MAPA` sobre o
  0x1A5000 (reserva do `patch_titulos`, ferramenta removida em 2026-09-14) foi
  corrigido: o lote agora é da ficha 005, e continua sem cruzar nenhum lote
  declarado.
- Nenhum teste, `tools/ci.sh` ou `assets/textos_pt.tsv` tocado.
  `sh tools/ci.sh`: **verde** (19 + 30 + 18 + 20 testes, `CI OK`).

### Imagem
    receita   reload_1.0_rc5  (RC4 catraca 74e8cb31... + fab_textos.py)
    sha256    f9f2e05990adb5d3882bbf093a6251673139004571af7698f3514b02f1e08f50
    2 MiB, validate_firmware: 21 OK + a falha esperada da regra R1 (CRC da FIRM)
    binary diff vs ORIGINAL: 30684 bytes, menor offset 0x053B88, 17 setores;
      o passo novo sozinho mexe 3337 bytes em 2 setores (0x053000, 0x1A5000)
    PSMP intacta, setor 0x00D000 intacto, nada abaixo de 0x00E000

### Decisões
- **Entrada pela premissa do sha256 da RC4 exata** (revisão R0). Ela é o que
  recusa a RC3 e a segunda passagem; as outras dez premissas continuam todas no
  código e todas nomeadas — só que, com o sha em cima, elas servem para dizer
  *o que* está errado, não apenas *que* está.
- **A tabela é comparada pelo sha256, não entrada a entrada.** Colar 216
  ponteiros no fonte seria ruído. O truque é comparar o sha da tabela com os
  ids 40 e 91 restaurados para fábrica: isso prova de uma vez que **todo** id da
  lista aponta para a string de fábrica dele (D4), e os dois ids da RC1 são
  conferidos à parte, nomeados, para a recusa dizer qual deles divergiu.
- **A string de fábrica é lida da própria entrada**, não do ORIGINAL: o sha da
  entrada já garante que a imagem *é* a RC4, e a RC1–RC4 não tocaram em string
  de fábrica. Assim a ferramenta não precisa abrir `firmware/ORIGINAL/`.
- **Todas as premissas rodam e todas as falhas voltam juntas** (inclusive as da
  fonte, que vêm antes das medidas de largura: medir com fonte adulterada daria
  um número bonito e falso).
- **Nada de alinhamento no lote.** O aparelho lê pelo ponteiro até o NUL; 4 KiB
  para 2,8 KB não pedem byte gasto.

### Por que o lote, e não a string no lugar (achado novo, não previsto)
Em fábrica **três strings são compartilhadas por dois ids cada**, e em cada par
o parceiro está **fora** da lista:

    0x00C54440  ids 40 e 90   → o 40 é o "Atualizar por SD" da RC1
    0x00C547E0  ids 78 e 155  → o 155 não é da RC5
    0x00C550B4  ids  9 e  29   → o 29 não é da RC5

Escrever no lugar mudaria três ids que a ficha manda deixar como estão — um
deles o "Atualizar por SD". Isso confirma, com nome e número, o D4 da ficha, e
vale para qualquer texto novo que vier na RC6.

### Pendências / não coberto
- **Nada foi gravado no aparelho**: o roteiro da ficha continua inteiro. A
  conferência das medidas (40 px, 113 px, glifos, `%`) é estática e está no
  `test_rc5.py`; se algum texto ficar estranho em contexto, isso só aparece na
  foto.
- O lote `0x1A5000` fica na **área livre**, fora de FIRM/TONE/PSMP — como todo
  código das RC1–RC4. O `make_install_kit` deriva os setores do diff, então o
  setor `0x1A5000` entra sozinho no kit; nenhuma ação extra é preciso do kit.
- **Sugestão (fora do escopo, não fiz)**: o `MANIFEST.sha256` da raiz parou na
  linha Core 2.4 (não cita `tools/`, `assets/` nem as RCs) e hoje não confere
  nada. Bastaria um utilitário que varresse a árvore e reescrevesse o arquivo.
- **Sugestão**: o `docs/TEXTOS_REVISAO.md` é a fonte do conteúdo, mas o
  `.tsv` + o sha fixado são a verdade; a revisão R1 da ficha (`RC5.1`) vai
  exigir um sha novo na ficha e na ferramenta — o caminho já existe.

### Danos notados
- Nenhum dano causado. `firmware/ORIGINAL/` intacto (sha confere no ci.sh),
  nada gravado no aparelho, nenhum arquivo protegido tocado, nenhum byte fora
  dos 180×4 + 4 KiB do lote.
- Dano **possível** herdado da ficha (D7, aceito pelo decisor): interromper a
  gravação entre `0x053000` e `0x1A5000` deixa textos apontando para lixo.
  Como a área livre vem por último na ordem de endereços, o caminho mais seguro
  é o mesmo das RCs anteriores: gravar tudo e conferir por cabo.

## Rodadas
