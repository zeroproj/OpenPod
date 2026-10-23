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

MiniMax M3 (opencode.json do worktree), 2026-10-23. `sh tools/ci.sh` **verde**
(1 ORIGINAL, 2 protegidos, 3 sintaxe, 4 testes: round-trip OK, autoteste OK,
rc2 19 + rc3 30 + rc4 18 OK, 5 gitleaks).

### O que foi feito

- `tools/fab_barra_centro.py` (item 1). Três bytes, um em cada `y`:
  `0x1217D6` (relógio), `0x1226B6` (título) e `0x12260E` (bateria), todos
  `02 -> 00`. Nada mais na imagem muda — nem a CRIA_FAIXA, nem o rótulo, nem o
  degradê.
- `tools/fab_icones_home.py` (item 2). Reescreve `0x0CDD5C..0x0D315C`: as 1024
  bytes da paleta e os 20480 bytes dos pixels da folha da home. Cabeçalho
  intocado. 21229 bytes em 7 setores (0x0CD000 a 0x0D3000).
- `tools/build.py`: a receita `reload_1.0_rc4` = `reload_1.0_rc3` +
  `fab_barra_centro.py` + `fab_icones_home.py`, nessa ordem, sem `MAPA` (as
  duas não alocam nada).
- Resultado: `reload_1.0_rc4` =
  `74e8cb315958b053f9e36e366a32f103ba995f7a18316c1c01e3de89e3f3b6d4`
  (reprodutível: duas execuções, mesmo sha). A RC3.1 continua
  `286e8ba8…` e a RC4 contém todos os bytes dela — 21232 bytes de diferença,
  3 em código e os outros na folha, nenhum fora dos bytes permitidos.
  Validação estrutural e binary diff do build: OK, menor offset 0x053C24,
  nada abaixo de 0xE000, setor 0xD000 e PSMP intocados.

Nada fora disso foi tocado: `firmware/ORIGINAL/` intacto (sha conferido pelo
ci), nenhuma ferramenta da lista de proibidas usada, importada ou citada nas
fontes novas, sem USB, sem gravação no aparelho. `DESPACHO-004.md` e
`opencode.json` seguem fora do commit.

### Decisões

1. **As entradas 0..15 da paleta são as 16 cores do degradê, exatas.** A
   RC3 escolhia, para cada linha, o índice mais próximo entre as 256 cores que
   já existiam, e por isso o topo da barra da home ficava em (66,76,81) e as
   pontas ganhavam matiz (erro máximo 10). Aqui a paleta é reescrita, então
   cada linha tem uma cor só, igual à conta dos menus: `topo + (base - topo) *
   y / 15`, arredondado — a mesma fórmula de `alvo_linha()` do critério C4,
   escrita aqui como fonte única e reconferida na leitura final. O dano D4
   (a barra da home perder o degradê) fica sem chão.
2. **A quantização é corte mediano com peso de população, escrito na
   ferramenta** — e não `Image.quantize()` como no `fab_logo.py`. Motivo: são
   240 entradas exatas (não 256), o preto (0,0,0) tem de ser uma entrada
   exata, e o resultado não pode depender da versão do Pillow. Está no fonte
   porque é onde dá para ler. Resultado no PNG aprovado: erro médio **1,13**
   por canal e máximo **36** (limites 2,0 e 64). O Pillow daria 1,51 e 58 —
   passa, mas com a metade da folga; a ficha já esperava "máx. 58" da
   quantização simples.
3. **O índice do pixel é o mais próximo da paleta INTEIRA (256 entradas)**, não
   só das 240 dos ícones. É o que o critério C4 mede, e evita que um pixel
   perto de uma cor da barra caia num índice de ícone e apareça com a cor
   errada. O preto do PNG cai no (0,0,0) exato da entrada 16.
4. **Métrica de distância: Chebyshev (o máximo por canal), desempate pelo menor
   índice**, com cache por cor distinta (o PNG tem 2974 cores em 18432 pixels).
   Determinístico entre execuções.
5. **Premissas presas por sha256, bytes crus para o que a ficha nomeia.** Na
   `fab_barra_centro` a cobertura pedida na R0 (título inteiro da RC3) virou
   sha256 de três regiões — o `align` do relógio (0x1217D0..0x1217DE), a
   função da bateria (0x1225B0..0x1226AC) e o rótulo do título
   (0x1226AC..0x1226F8) — mais os cinco "fatos" legíveis (`0121`, `0322`,
   `062200bf`, `0221`, `6b21`), os três `bl` lidos por **alvo** e o lote do
   texto. Na `fab_icones_home`: cabeçalho (palavra por palavra, como no
   `fab_logo`) + paleta por sha, as 144 linhas dos ícones por sha, e as 16
   linhas da barra apenas **uniformes** — assim a ferramenta aceita o ORIGINAL
   e a RC3, como a ficha pede, e recusa assim que a paleta não for a de
   fábrica (2ª passagem).
6. **Conferência de saída nas duas ferramentas**: relê do binário o que
   escreveu (bytes, alvos de `bl`, paleta, pixels) e compara com a entrada e
   com o PNG; depois confere que nada saiu da lista de bytes permitidos e
   recusa sem gravar se sair.
7. **`--out` = `--in` por qualquer via** (`os.path.samefile`), herdado da RC2;
   a recusa sai com código 2, antes de ler a entrada.

### Pendências (fora do escopo desta tarefa)

- Roteiro no aparelho (a tabela da ficha), inclusive o corte do texto no topo
  (dano D5) e a bateria nos menus (dano D6).
- Kit e carimbo: é do engenheiro. O `gera_versao` monta os setores em ordem
  crescente de endereço; nesta RC os setores novos são os de código
  (0x121000, 0x122000) e os da folha da home (0x0CD000..0x0D3000), e nenhum
  deles é lido pelo bootloader. **Ponto para o `[4/4]`:** a folha da home é
  um bloco só de 7 setores, e os setores 0x121000/0x122000 (o y do relógio,
  do título e da bateria) entram **antes** dele. Se a gravação parar no meio,
  sobra uma home com ícones novos e a barra ainda na altura da RC3 — que é o
  inverso do risco da RC3 (lá o gancho podia ficar apontando para o 0xFF do
  lote). Boot, recuperação por cabo e as outras telas não dependem de nenhum
  dos dois blocos.
- Docs (`docs/CHANGELOG.md`, `docs/RELOAD_1_0.md`): como na RC2/RC3, ficam
  para depois de a RC4 ser aprovada no aparelho.

### Danos notados e não cobertos

- **As linhas 14 e 15 do PNG são perdidas.** O approved tem 63 pixels de
  conteúdo na linha 14 e 12 na 15 (franja de antialiasing, cores como
  `(4,1,1)`), e a ficha manda que a barra sejam as linhas 0..15. Como a RC3
  já pinta ali o degradê, essa franja é descartada de qualquer modo — mas é a
  única arte do PNG que não chega à tela. Nenhum glifo é afetado (a grade
  começa em y=16).
- **A paleta nova invalida qualquer código que escolhesse cor por índice.** A
  navegação da home é por tecla e por índice e a seleção pinta o rótulo pelo
  array B (`docs/PLANO_HOME.md` §1.2 e §1.3), então hoje não há problema; e a
  troca de paleta inteira da V002 (CHANGELOG) prova que nada no firmware
  prende um índice. Se um dia existir leitura de índice de paleta para a home,
  essa leitura passa a estar errada — não há teste que pegue isso.
- **O home fica com 240 cores em vez de 2974.** É o que a folha
  INDEXED_8 permite; o erro máximo por pixel é 36 num canal. A verificação é
  numérica (média e máximo), não visual — conferi a folha renderizada contra
  o PNG e a grade 3×3 cai nas mesmas posições da de fábrica, na mesma ordem.
- **O deslocamento do y vale para todas as telas**, não só para a home: as
  duas rotinas que posicionam relógio e bateria são compartilhadas (é o mesmo
  `view_icon_create` da R1 da ficha 002). Nas telas com outros elementos na
  faixa o deslocamento é o de 2 px que a foto pediu, mas o único lugar onde dá
  para ver o resultado é a home.
- **Sem `unicorn` não há teste semântico** do que o aparelho faz com esses 6
  bytes: o que se confere é que os bytes são os da ficha.

## Rodadas
