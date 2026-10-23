# 006 — Reload 1.0 RC6: home sem nomes, grade centralizada, moldura no selecionado

- Tipo: Risco + Pesada (código novo enganchado na navegação da home)
- Desenvolvedor: MiniMax M3 (opencode.json do worktree)
- Analista: gpt-6-astra, esforço high
- Depende de: RC5 (rodando no aparelho, foto 2026-10-23; catraca `f9f2e059…`)
- Status: revisão R0 incorporada; liberada para implementação. Decisor: "tirar o texto…
  os ícones já falam", "deixar … mais centralizado", "a moldura vai ficar
  legal" (2026-10-23)

## Objetivo
Na home: sem os nomes sob os ícones; as 3 fileiras de ícones (mesmo
tamanho) distribuídas por igual entre a barra e o fim da tela; o ícone
selecionado ganha uma moldura branca arredondada que anda com os botões.

Fora: tamanho dos ícones, navegação (continua a de fábrica), outras telas,
textos (a tabela da RC5 fica como está).

## Evidência no ORIGINAL (CONFIRMADO, desmontagem)
- Criação da home, laço de 9 itens `0xD2ECEE..0xD2ED8E`: por item, um
  `lv_img` sem imagem (`0xD5D850`, foco/evento) em `(x,y)` da tabela
  `0x04867C`, e um rótulo `0xD5E2E8` (`r6`): texto `0xD2108C(id)` (bl em
  `0x12ED30`), cor normal `0xD2E948()` via `0xD4D10A` (bl em `0x12ED46`),
  modo longo 0, `size(40,15)` (`0x12ED5C movs r2,#0xf`, `0x12ED5E movs
  r1,#0x28`), posição da tabela `0x0486A0` (copiada para a pilha em
  `0xD2EC5E`; só esta referência ao literal, em `0x12EDF0`). Rótulos ficam
  em `view[+0x24+4·i]`.
- Seleção inicial: `0x12EDBC` `bl 0xD4D10A` com cor `0xD57B48(0xC)`
  (amarelo) e modo longo 3.
- Navegação (`0xD2E9B8..0xD2EB60`): o item que perde a seleção volta à cor
  normal por `bl 0xD4D10A` em `0x12E9CA`, `0x12EA26`, `0x12EABA`,
  `0x12EB12`; o novo selecionado recebe o amarelo em `0x12EB4C`. São os
  únicos `bl 0xD4D10A` sobre rótulos da home (varredura `0x12E000..0x130000`).
- Estilo: `0xD4CAC4(obj, prop, valor, seletor)`; IDs pelos wrappers de
  fábrica: `0x30` cor da borda, `0x31` opacidade da borda, `0x1032`
  largura da borda, `0x60` raio.
- Folha da home (RC4): ícones 31×31 em x 7/48/89, y 16/64/112, sombra 2
  linhas acima e 3 abaixo; fundo índice 16 = `(0,0,0)`.

## Escopo — receita `reload_1.0_rc6` = `reload_1.0_rc5` + `fab_home_moldura.py`
Uma ferramenta só; exige **sha256 da entrada = RC5 `f9f2e059…`**.

1. **Grade**: linhas 16..159 da folha viram índice preto; as três faixas
   (topo antigo, altura → topo novo) `(16,34→29)`, `(62,36→70)`,
   `(110,36→114)` são copiadas como estão (só índices; paleta intocada).
   Ícones passam a y 29, 72, 116 (vãos 13/12/13/13).
2. **Molduras**: tabela `0x0486A0` → `(5,27) (46,27) (87,27) (5,70) (46,70)
   (87,70) (5,114) (46,114) (87,114)`; tamanho `0x12ED5C` → `23 22`,
   `0x12ED5E` → `23 21` (35×35, 2 px fora do ícone).
3. **Rotinas** em `0x1A6400` (lote `0x80` no `MAPA`), exatamente:
   ```
   DESEL 0xDA6400: movs r1,#0x31; movs r2,#0;    movs r3,#0; b.w 0xD4CAC4   ; borda apagada
   SEL   0xDA640A: movs r1,#0x31; movs r2,#0xff; movs r3,#0; b.w 0xD4CAC4   ; borda acesa
   CRIA  0xDA6414: push {r4,lr}
                   mov r0,r6; movw r1,#0x1032; movs r2,#2; movs r3,#0; bl 0xD4CAC4  ; largura 2
                   mov r0,r6; movs r1,#0x60;   movs r2,#8; movs r3,#0; bl 0xD4CAC4  ; raio 8
                   mov r0,r6; movs r1,#0x30; movw r2,#0xffff; movs r3,#0; bl 0xD4CAC4 ; branca
                   movw r0,#0x6448; movt r0,#0xda; pop {r4,pc}   ; devolve "" (0xDA6448)
   0xDA6448: 00 ; resto do lote 0xFF
   ```
   `CRIA` substitui `0xD2108C` em `0x12ED30`: usa o rótulo que já está em
   `r6` (posto em `0x12ED2C`) e devolve o texto vazio que vai para
   `set_text`. `DESEL`/`SEL` têm a assinatura de `0xD4D10A` e ignoram a cor.
4. **Ganchos** (`bl` → alvo novo): `0x12ED30`→CRIA; `0x12ED46`, `0x12E9CA`,
   `0x12EA26`, `0x12EABA`, `0x12EB12`→DESEL; `0x12EB4C`, `0x12EDBC`→SEL.

Premissas: sha da entrada; antes de escrever, confere cada `bl` de fábrica,
os dois `movs` de tamanho, a tabela de posições de fábrica, a função
`0xD4CAC4` (0x40 B), lote todo `0xFF`, fundo preto na paleta. `--in/--out/
--dry-run`; recusa saída igual/link da entrada. Não usa nem copia
`patch_icones_home.py`, `patch_cor_selecao.py`, `patch_home_barra.py`.

## Critérios de aceite (`tests/test_rc6.py`)
- [ ] C0 constrói · C1 catraca RC5 · C2 receita/lote
- [ ] C3 folha = RC5 com as faixas movidas, paleta intocada
- [ ] C4 posições, tamanho, 8 ganchos, rotinas exatas, `0xD4CAC4` intocada
- [ ] C5 só bytes permitidos; nada abaixo de `0xE000`; PSMP
- [ ] D3 recusas (RC4, truncado, bordas), `--dry-run`, links

## Danos possíveis
| # | Dano | Coberto por |
|---|---|---|
| D1 | `bl` para rotina inexistente → trava ao abrir a home | ganchos e rotinas testados; rotina no mesmo kit |
| D2 | `r6` não é o rótulo em `0x12ED30` → estilo em objeto errado | evidência (`mov r6,r0` em `0x12ED2C`, `r6` não muda até `0x12ED38`); roteiro |
| D3 | algum caminho de seleção não passa pelos ganchos → moldura some/duplica | varredura de `bl 0xD4D10A` na região; roteiro: todas as direções e voltas |
| D4 | moldura fora do ícone | posições derivadas das faixas; prévia; roteiro |
| D5 | ícones cortados ao mover | C3 (faixas incluem sombra; nenhuma linha com conteúdo fora delas) |
| D6 | nomes somem também em outras telas | só os rótulos da home mudam; tabela de textos intocada (C5) |
| D7 | gravação interrompida entre `0x12E000` e `0x1A6000` → home trava | risco aceito, igual RC1–RC5; recuperação pelo cartão/cabo |

## Riscos aceitos (decisor)
- Sem nome, a home depende só do desenho dos ícones.
- A moldura é branca e fixa (2 px, raio 8).

## Roteiro no aparelho
| Fluxo | Passos | ✔/✘ |
|---|---|---|
| Home | sem nomes; grade centralizada; moldura no ícone inicial | |
| Navegação | ←/→/↑/↓ e voltas pelas bordas: moldura sempre num ícone só | |
| Abrir/voltar | abrir cada app e voltar: moldura no ícone certo | |
| Outras telas | títulos e menus com texto normal | |
| Config | Informações = "Reload 1.0 RC6"; Atualizar por SD funciona | |

## Bytes permitidos
Além dos da RC5: `0x0CE95C..0x0D315C` (linhas 16..159 da folha),
`0x0486A0..0x0486C4`, `0x12ED5C..0x12ED60`, os 8 ganchos (4 B cada),
`0x1A6400..0x1A6480`.

## Arquivos de teste protegidos
- `tests/test_rc2.py` … `tests/test_rc6.py`, `tools/ci.sh`

## Revisão da ficha (Codex)
R0 — gpt-6-astra high, 2026-10-23: APROVADO COM RESSALVAS (1 ALTA). Incorporado
(kit, do engenheiro): `gera_versao.py` agora exige payload do `.up` igual à
imagem pedida byte a byte e cobertura até a última mudança (já conferia
CRC, cabeçalho, setores do cabo, bootloader, `0xD000` e PSMP).

## Entrega (preenchida pelo desenvolvedor)

### O que foi feito
- **`tools/fab_home_moldura.py`** (nova, 1 ferramenta): a receita
  `reload_1.0_rc6 = reload_1.0_rc5 + fab_home_moldura.py`. Exige a **RC5
  exata** (sha256 `f9f2e059…`) na entrada e faz as três coisas da ficha:
  1. **Grade** — as três faixas de ícones da folha (128×160 INDEXED_8)
     saem de `16..49 / 62..97 / 110..145` para `29..62 / 70..105 / 114..149`;
     o resto das linhas 16..159 vira o índice **preto exato** da paleta. Só
     os índices dos pixels mudam: a paleta (`0x0CDD5C..0x0CE15C`) é
     intocada. Os glifos passam a y 29, 72 e 116 (vãos 13/12/13/13).
  2. **Nomes** — o texto dos nove rótulos vira a string vazia: o `bl`
     `0x00D2108C` (texto do rótulo) em `0x0012ED30` passa a chamar a rotina
     `CRIA`, que devolve `""` (0x00DA6448) em vez do nome.
  3. **Moldura** — o rótulo (que era o nome) passa a ser um retângulo de
     borda **branca, 2 px, raio 8** em volta do ícone selecionado. Os oito
     `bl 0x00D4D10A` (a função que pintava a cor do texto) viram
     `DESEL` (borda apagada) e `SEL` (borda acesa), e a moldura **anda** com
     a seleção porque os pontos de "perde a seleção" e "ganha a seleção" são
     exatamente os oito que a ficha mediu.
- **Tabela de posições** `0x0486A0` → `(5,27) (46,27) (87,27) (5,70)
  (46,70) (87,70) (5,114) (46,114) (87,114)`; **tamanho** do rótulo
  `0x12ED5C`/`0x12ED5E` → 35×35 (era 40×15), isto é, 2 px de cada lado do
  glifo de 31 px.
- **Rotinas** no lote `0x001A6400` (0x80 B), montadas pela ferramenta e
  conferidas contra um literal de 72 bytes: `DESEL` 0x00DA6400, `SEL`
  0x00DA640A, `CRIA` 0x00DA6414, string vazia em 0x00DA6448 (um `0x00`) e o
  resto do lote em `0xFF`.
- **`tools/build.py`**: `RELOAD_1_0_RC6 = RELOAD_1_0_RC5 + [fab_home_moldura.py]`
  e o lote `(0x001A6400, 0x0080)` no `MAPA` (não cruza nenhum lote declarado:
  o `make_extras_menu` termina em 0x001A6400 e o degradê começa em
  0x001A7000).
- Nenhum teste, `tools/ci.sh` ou arquivo protegido tocado.
  `sh tools/ci.sh`: **verde** (round-trip + 19 (RC2) + 30 (RC3) + 18 (RC4)
  + 20 (RC5) + 14 (RC6) testes, `CI OK`).

### Imagem
    receita   reload_1.0_rc6  (RC5 catraca f9f2e059... + fab_home_moldura.py)
    sha256    af3a2b6d8aaa1bf9d709c20e3ccd8d3f1aeb37cc6843a6070938e122488f4bc8
    2 MiB, validate_firmware: 21 OK + a falha esperada da regra R1 (CRC da FIRM)
    binary diff vs ORIGINAL: 30800 bytes, menor offset 0x0486A0, 20 setores
    o passo novo sozinho mexe 11408 bytes em 8 setores:
      0x048000 (tabela de posicoes, 18 B)   0x0CE000..0x0D2000 (folha, 11292 B)
      0x12E000 (os 8 ganchos + o tamanho, 27 B)   0x1A6000 (as rotinas, 71 B)
    PSMP intacta, setor 0x00D000 intacto, nada abaixo de 0x00E000
    build reprodutível: duas execuções seguidas, o mesmo sha

### Decisões
- **A entrada é a RC5 pelo sha256**, e não por "a imagem parece a RC5". A
  receita da RC6 é a RC5 mais esta ferramenta; qualquer outra imagem é
  recusada antes de qualquer escrita (e a segunda passagem também, porque o
  sha já não bate e o lote já não está virgem).
- **As outras sete premissas continuam todas no código e todas nomeadas**
  (os 8 ganchos lidos **por alvo**, os dois `movs` de tamanho, a tabela de
  posições de fábrica, a função de estilo `0x00D4CAC4` presa por sha256, o
  lote virgem, o preto exato na paleta). Com o sha em cima elas servem para
  dizer *o que* está errado, não apenas *que* está.
- **A folha é movida por cópia de faixa**, não redesenhada: as três faixas
  são copiadas como estão (só os índices andam de lugar) e o resto fica no
  índice preto. Assim a paleta — que é o que dá a cor de cada pixel — não
  é tocada e nenhum pixel é reinterpretado.
- **A moldura reusa o rótulo em vez de criar um objeto novo.** Não há
  alocação, não há objeto na pilha do LVGL, e o gancho continua sendo o
  `bl` de 4 bytes: só muda o *alvo*. A assinatura de `DESEL`/`SEL` é a de
  `0x00D4D10A` (r0 = o rótulo) e elas ignoram a cor — é o que a ficha pede.
- **A string vazia mora no fim do lote** (0x00DA6448, um byte `0x00`) e o
  resto do lote fica em `0xFF`: se a gravação for interrompida no meio do
  lote, sobra `0xFF` — que o Thumb-2 não executa como código — em vez de
  lixo.
- **`CRIA` devolve a string vazia, e não a pinta.** O texto do rótulo é
  trocado por `""` no gancho do `set_text`, e é por isso que o nome some
  **sem** que a tabela de textos da RC5 seja tocada (dano D6 fechado).

### Verificações feitas sobre o ORIGINAL (CONFIRMADO, não presumido)
- **A CPU é ARM Thumb-2 e a folha é INDEXED_8**: os ids de propriedade
  (`0x30` cor da borda, `0x31` opacidade, `0x1032` largura, `0x60` raio)
  foram lidos **nos wrappers de fábrica** (`0x00D4D0D6`, `0x00D4D0EA`,
  `0x00D4D0F8`, `0x00D4D068`), que são os que chamam `0x00D4CAC4`. Não são
  ids de manual: saíram do binário.
- **A cor da borda é um valor de 16 bits** (RGB565), como o da cor do texto:
  o wrapper `0x00D4D10A` monta o valor como `(cor<<16)|cor` no caso do
  texto e `0xFFFF` (branco) é o mesmo branco nos dois.
- **O rótulo nasce com fundo transparente**: `docs/OpenPod_Design_System.md`
  (`Um rótulo nasce com fundo transparente`) e o fato de a fábrica pintar o
  nome **sobre** a folha. Se o fundo fosse opaco, a moldura viraria um
  retângulo preto por cima do ícone — e o `bg_opa` do rótulo da home
  continua no padrão (o `0x00D4D13A` de `0x0012ED58` é o `text_align` da
  fábrica; o patch que ligava `bg_opa=255` aqui foi revertido).
- **A geometria confere com a folha**: na RC5 os glifos (31 px) ocupam
  x 7..37 / 48..78 / 89..119 e y 16..46 / 64..94 / 112..142, com a sombra
  formando blocos de 35 px (x 5..39 / 46..80 / 87..121). Depois do passo os
  glifos estão em y 29 / 72 / 116 e as molduras 35×35 em (5,27) (46,27)
  (87,27) (5,70) (46,70) (87,70) (5,114) (46,114) (87,114) — 2 px de
  margem em volta de cada glifo, sem exceção.
- **Os oito ganchos são os únicos**: a varredura de `bl 0x00D4D10A` na
  região `0x12E000..0x130000` da RC5 devolve exatamente os oito pontos da
  ficha (4 de "perde a seleção", 1 de "ganha", 1 de criação, 1 de criação
  com cor normal). Não sobrou nenhum caminho de seleção por fora deles
  (dano D3).
- **A sequência de criação foi lida**: `mov r6, r0` em `0x0012ED2C`, e `r6`
  não muda até `0x0012ED38` — o `CRIA` usa `r6` (o rótulo) com segurança
  (dano D2).

### Pendências / não coberto
- **Nada foi gravado no aparelho**: o roteiro da ficha continua inteiro. A
  conferência toda aqui é estática (bytes, alvos, disassembly); o que só a
  foto mostra é se a moldura aparece, se o glifo fica visível dentro dela e
  se o rótulo aceita o tamanho fixo 35×35 com texto vazio.
- **Duas coisas que a análise não fecha, e que a foto fecha:**
  1. se o LVGL desta build aceita o tamanho fixo de um `lv_label` com texto
     vazio (a fábrica já grava o texto **antes** do tamanho, então a ordem
     é a boa; mas se o `lv_label_set_text` re-encolher o objeto, a
     moldura sai com 0×0);
  2. se o rótulo da home tem fundo transparente nesta build — a
     documentação do projeto diz que sim, e a folha da RC5 confirma que o
     nome é desenhado por cima do ícone sem caixa.
- **A posição do `lv_img` da home (tabela `0x04867C`) NÃO foi mexida** — os
  bytes da ficha não a liberam. Como o `lv_img` é criado *sem imagem* (o
  glifo vem da folha), ele não desenha nada: a posição dele só importa para
  o foco/evento. A ficha assume que isso não aparece (o foco da fábrica
  também não aparece). **Se a foto mostrar um retângulo de foco por cima do
  ícone, a correção é mexer na `0x04867C` — e isso é uma nova rodada, com
  bytes novos.**
- **Sugestão (fora do escopo, não fiz)**: o `MANIFEST.sha256` da raiz
  parou na linha Core 2.4 e hoje não confere nada (já apontado na entrega
  da 005). Continua valendo.
- **Sugestão**: a receita da RC6 é a última que cabe em uma ferramenta só.
  A RC7 (se vier) vai mexer na navegação ou no desenho dos ícones: nesse
  caso a tabela `0x04867C` e o `lv_img` (hoje sem imagem) merecem uma
  leitura de verdade, e não mais um remendo de 4 bytes.

### Danos notados
- Nenhum dano causado. `firmware/ORIGINAL/` intacto (sha confere no
  `ci.sh`), nada gravado no aparelho, nenhum arquivo protegido tocado
  (`tests/test_rc2..6.py` e `tools/ci.sh`), nenhum byte fora dos liberados
  (o `test_c5_so_regioes_permitidas` confere byte a byte), nada abaixo de
  `0x00E000`, setor `0x00D000` e PSMP intactos.
- Dano **possível** herdado da ficha (D7, aceito pelo decisor): interromper
  a gravação entre `0x0D3000` e `0x1A6000` deixa a home sem moldura (se
  parar antes dos ganchos) ou com a moldura parada (se parar no meio do
  lote). O caminho é o mesmo das RC1–RC5: gravar tudo e conferir por
  cabo.
- Dano **possível** novo, e é o que a foto tem de dizer: se o rótulo da
  home tiver fundo opaco nesta build, a moldura tapa o glifo. Não tem como
  ser resolvido por análise estática do binário sem descer até o tema do
  LVGL — e a documentação do projeto diz que o fundo é transparente.

## Rodadas
- **R0 (2026-10-23, MiniMax M3)** — implementação da ficha 006.
  `tools/fab_home_moldura.py` nova; `tools/build.py` com a receita
  `reload_1.0_rc6` e o lote `(0x001A6400, 0x0080)`.
  `sh tools/ci.sh` **verde**: round-trip + 19 (RC2) + 30 (RC3) + 18 (RC4) +
  20 (RC5) + 14 (RC6) testes, `CI OK`.
  Imagem `reload_1.0_rc6`: sha256 `af3a2b6d…`, 2 MiB, reprodutível.

