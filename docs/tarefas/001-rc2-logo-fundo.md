# 001 — Reload 1.0 RC2: logo do OpenPod na abertura + fundo preto

- Tipo: Risco (imagem que vai para o aparelho)
- Desenvolvedor: MiniMax M3 (opencode.json do worktree)
- Analista: gpt-6-astra, esforço high
- Depende de: RC1 (aprovada no aparelho em 2026-10-21)
- Status: revisada (astra R0 incorporada) — aguardando aprovação do decisor

## Objetivo
O aparelho liga mostrando a logo do OpenPod sobre fundo preto, e as telas
deixam de ter fundo branco. A Tocando Agora perde o papel de parede azul e
fica preta. Tudo o que a RC1 entregou (update por SD) continua igual.

## Escopo
- Inclui: receita `reload_1.0_rc2` em `tools/build.py` = os passos da
  `reload_1.0_rc1` + **exatamente duas ferramentas novas**, com estes nomes:
  - `tools/fab_logo.py` — item 1 (lê `assets/OpenLogo.png`);
  - `tools/fab_fundo_preto.py` — itens 2, 3 e 4.
  Interface das duas: `--in <bin> --out <bin> [--dry-run]`, padrão de `tools/`.
- **Recusa antes de escrever (D3):** cada ferramenta lê a entrada, confere
  TODAS as premissas abaixo (tamanho 2 MiB; cabeçalhos e ponteiros XIP dos
  descritores; bytes de fábrica dos `bl`, de `0x1567F6` e das funções
  `0xD21384`/`0xD2138A`) e, se qualquer uma falhar, sai com código ≠ 0
  **sem criar o arquivo de saída** e sem tocar a entrada.
- Não inclui: barra "OpenPod", degradê, ícones, bateria, textos (RC3/RC4);
  carimbo de versão e kit (o engenheiro faz).
- **Proibido**: usar, importar ou copiar `patch_logo.py`,
  `patch_fundo_display.py`, `patch_fundo_abertura.py`, `patch_fundo_preto.py`
  ou qualquer ferramenta listada em `PROIBIDAS` de `tests/test_rc2.py`.
  Decisão do mantenedor: só o firmware de fábrica é fonte.

## Evidência no ORIGINAL (verificada pelo engenheiro em 2026-10-21)
Base XIP `0x00C00000`. Thumb-2, little-endian. Endereços abaixo = offset no arquivo.

1. **Logo da abertura** — `lv_img_dsc` em `0x0CC7C4`: header `0x0462000A`
   (cf=10 INDEXED_8, 128×35), data_size 5504, ptr `0x00CCC7D0`. Paleta
   256×BGRA em `0x0CC7D0`, pixels 1 B/px em `0x0CCBD0..0x0CDD50`.
   Referenciada nas duas rotinas da abertura (pools em `0x12289C`, `0x122924`).
   Imagem nova: `assets/OpenLogo.png` (128×35).
2. **Fundo da abertura** — nas duas rotinas: `bl 0xD21384` em `0x12285A` e
   `0x1228E4`, cujo retorno vai para `0xD4D092` (estilo bg). `0xD21384` =
   `mov.w r0,#-1; bx lr` (branco). A fábrica tem ao lado `0xD2138A` =
   `mov.w r0,#0; bx lr` (preto). Trocar o alvo dos dois `bl` para `0xD2138A`.
3. **Fundo do display** — `0x1567F6`: `ff 23` = `movs r3,#0xff`, seguido de
   três `strb.w r3,[r4,#0x29/0x2a/0x2b]` (cor de fundo do display, RGB).
   Trocar o imediato para 0: `00 23`.
4. **Papel de parede da Tocando Agora** — `lv_img_dsc` em `0x0C73B8`
   (INDEXED_8 128×160, ptr `0x00CC73C4`), referenciado em `0x13217C`.
   Deixar as **256** cores da paleta pretas (B=G=R=0), alfa como na
   fábrica. Só a paleta (`0x0C73C4..0x0C77C4`) muda: cabeçalho e pixels
   intocados.

## Critérios de aceite (todos em `tests/test_rc2.py`)
- [ ] C0 `reload_1.0_rc2` constrói e passa a validação do `build.py`
- [ ] C1 a RC1 continua reprodutível (sha `a427c62e…`) e a RC2 contém todos os bytes dela
- [ ] C2 a receita começa por `patch_update_sd.py` e não usa ferramenta proibida
- [ ] C3 cabeçalho da logo intocado; logo decodificada ≈ `OpenLogo.png` (erro médio ≤ 2, máx ≤ 64), alfa 255
- [ ] C4 os dois `bl` da abertura chamam `0xD2138A`; a função preta continua intocada
- [ ] C5 `0x1567F6` = `00 23`
- [ ] C6 papel de parede: cabeçalho e pixels intocados; as 256 cores pretas; alfa de fábrica
- [ ] D3 as duas ferramentas existem, aceitam o ORIGINAL e recusam entrada truncada ou adulterada sem criar saída
- [ ] C7 nenhum byte fora do permitido; nada abaixo de `0xE000`; PSMP intocada

## Danos possíveis (equivalente dos casos de abuso)
| # | Dano | Comportamento esperado | Teste |
|---|---|---|---|
| D1 | `bl` mal codificado → salto para lugar errado → trava na abertura | alvo decodificado == `0xD2138A` | C4 |
| D2 | ferramenta escreve fora do slot (ex.: cabeçalho, imagem vizinha) | só bytes permitidos mudam | C3, C6, C7 |
| D3 | aplicada sobre imagem que não é a esperada → corrompe outra coisa | a ferramenta confere a premissa (bytes de fábrica) e **recusa** se não bater | revisão do diff |
| D4 | quebra a RC1 (update por SD) | RC1 intacta dentro da RC2 | C1 |
| D5 | código de projeto antigo entra escondido | receita e fontes sem nomes proibidos | C2 |
| D6 | bootloader / setor `0xD000` / PSMP tocados | build e teste recusam | C7 |
| D7 | `.up` com payload errado, CRC errado ou alcançando a PSMP | o engenheiro só entrega com `gera_versao` [4/4] OK (CRC, cobertura, PSMP fora, setores = imagem) e registra no pacote | pacote |
| D8 | fundo preto deixa texto ou seleção ilegível, inclusive no caminho do update por SD | roteiro obrigatório no aparelho antes de aprovar | roteiro |
| D9 | código antigo copiado e renomeado | o analista confere a procedência no diff (só fábrica + Pillow + stdlib) | revisão do diff |

## Roteiro no aparelho (decisor, antes de aprovar)
| Fluxo | Passos | ✔/✘ |
|---|---|---|
| Abertura | ligar → logo OpenPod, fundo preto; repetir após reset | |
| Navegação | home → cada item → voltar; textos e seleção legíveis | |
| Tocando Agora | tocar uma música → fundo preto, tempos e título legíveis | |
| Configurar | Informações = "Reload 1.0 RC2"; "Atualizar por SD" legível | |
| Update por SD | `update.up` da RC2 no cartão → Atualizar por SD → volta normal → apagar `update.up` | |

## Bytes permitidos
Além dos da RC1: `0x0CC7D0..0x0CDD50`, `0x0C73C4..0x0C77C4` (só a paleta),
`0x12285A..0x12285E`, `0x1228E4..0x1228E8`, `0x1567F6..0x1567F8`.

## Arquivos de teste protegidos
- `tests/test_rc2.py`, `tools/ci.sh` (hash em `tests/PROTEGIDOS.sha256`)

## Revisão da ficha (Codex)
R0 — gpt-6-astra high, 2026-10-21: REPROVADO (2 ALTA, 3 MÉDIA, 1 BAIXA).
Incorporado: recusa testada com 7 entradas adulteradas (D3); papel de
parede limitado à paleta, 256 entradas; hash e tamanho do PNG fixados;
conferência do `.up` pelo engenheiro (D7); roteiro no aparelho (D8);
procedência no diff (D9).

## Entrega (preenchida pelo desenvolvedor)
- O que foi feito:
- Decisões tomadas:
- Pendências / limitações:
- Danos notados e não cobertos:

## Rodadas
