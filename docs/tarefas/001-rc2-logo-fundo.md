# 001 — Reload 1.0 RC2: logo do OpenPod na abertura + fundo preto

- Tipo: Risco (imagem que vai para o aparelho)
- Desenvolvedor: MiniMax M3 (opencode.json do worktree)
- Analista: gpt-6-astra, esforço high
- Depende de: RC1 (aprovada no aparelho em 2026-10-21)
- Status: rascunho

## Objetivo
O aparelho liga mostrando a logo do OpenPod sobre fundo preto, e as telas
deixam de ter fundo branco. A Tocando Agora perde o papel de parede azul e
fica preta. Tudo o que a RC1 entregou (update por SD) continua igual.

## Escopo
- Inclui: receita `reload_1.0_rc2` em `tools/build.py` = os passos da
  `reload_1.0_rc1` + ferramentas NOVAS para os quatro itens abaixo.
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
   Deixar todas as 256 cores da paleta pretas (B=G=R=0), alfa 255.
   Cabeçalho intocado.

## Critérios de aceite (todos em `tests/test_rc2.py`)
- [ ] C0 `reload_1.0_rc2` constrói e passa a validação do `build.py`
- [ ] C1 a RC1 continua reprodutível (sha `a427c62e…`) e a RC2 contém todos os bytes dela
- [ ] C2 a receita começa por `patch_update_sd.py` e não usa ferramenta proibida
- [ ] C3 cabeçalho da logo intocado; logo decodificada ≈ `OpenLogo.png` (erro médio ≤ 2, máx ≤ 64), alfa 255
- [ ] C4 os dois `bl` da abertura chamam `0xD2138A`; a função preta continua intocada
- [ ] C5 `0x1567F6` = `00 23`
- [ ] C6 papel de parede: cabeçalho intocado, todos os pixels pretos, alfa 255
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

## Bytes permitidos
Além dos da RC1: `0x0CC7D0..0x0CDD50`, `0x0C73C4..0x0CC7C4`,
`0x12285A..0x12285E`, `0x1228E4..0x1228E8`, `0x1567F6..0x1567F8`.

## Arquivos de teste protegidos
- `tests/test_rc2.py`, `tools/ci.sh` (hash em `tests/PROTEGIDOS.sha256`)

## Revisão da ficha (Codex)
<pendente>

## Entrega (preenchida pelo desenvolvedor)
- O que foi feito:
- Decisões tomadas:
- Pendências / limitações:
- Danos notados e não cobertos:

## Rodadas
