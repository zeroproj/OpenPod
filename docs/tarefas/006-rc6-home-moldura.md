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

## Rodadas
