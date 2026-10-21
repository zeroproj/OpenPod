# 001 — Reload 1.0 RC2: logo do OpenPod na abertura + fundo preto

- Tipo: Risco (imagem que vai para o aparelho)
- Desenvolvedor: MiniMax M3 (opencode.json do worktree)
- Analista: gpt-6-astra, esforço high
- Depende de: RC1 (aprovada no aparelho em 2026-10-21)
- Status: merged (aprovada no aparelho em 2026-10-21)

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
  - `tools/fab_logo.py` (item 1): `assets/OpenLogo.png` na `lv_img_dsc` de
    128×35 da abertura. Escreve **só** os 5504 B de `0x0CC7D0..0x0CDD50`
    (1024 de paleta BGRA + 4480 de índices); o cabeçalho `0x0CC7C4` fica
    intocado. Quantiza por median cut do Pillow, alfa 255 nas 256 entradas
    e confere o resultado lendo de volta pelo cabeçalho: erro médio 0,07
    (limite 2,0), máximo 6 (limite 64), alfa 255 em todos os pixels.
  - `tools/fab_fundo_preto.py` (itens 2, 3 e 4): os dois `bl` da abertura
    passam a chamar `0x00D2138A` (a função preta da própria fábrica, que
    fica intacta); `0x1567F6` vira `00 23`; as 256 cores da paleta do papel
    de parede (0x0C73C4..0x0C77C4) viram preto com o alfa de fábrica.
    Cabeçalho e pixels do papel de parede intocados.
  - Receita `reload_1.0_rc2` em `tools/build.py` = `reload_1.0_rc1` +
    `fab_logo.py` + `fab_fundo_preto.py`, nessa ordem. Sem entrada no
    `MAPA`: nenhuma das duas aloca, e a conferência de "escreveu só no
    próprio lote" do pipeline não se aplica a elas.
  - Recusa (D3) nas duas ferramentas: tamanho 2 MiB, os **dois**
    descritores INDEXED_8 conferidos **inteiros** (os 32 bits do cabeçalho
    palavra por palavra — cf, `always_zero`, bits reservados e
    largura/altura embutidas —, mais data_size e ponteiro XIP), os bytes de
    fábrica dos dois `bl`, de `0x1567F6` e das funções
    `0x00D21384`/`0x00D2138A`, e no `fab_logo` o sha256 e o tamanho do PNG.
    Recusa sai com código ≠ 0 sem criar a saída e sem tocar na entrada.
  - `--out` recusado quando aponta para a própria entrada por qualquer via:
    mesmo caminho, symlink ou hardlink (`os.path.samefile`, recusa 2).
  - `sh tools/ci.sh`: **tudo verde**, `CI OK` (passos 1 a 5). A pendência 1
    da R0 foi resolvida pelo merge: o `ci.sh` do ramo principal trocou `-q`
    por `--log-level error`, e o gitleaks 8.30.1 roda.
  - Imagem da RC2, para o pacote: `fcca5fdc99b828fb135cae77f5915c42cfddf1a537eb0a619f0c135313ccd123`
    (reprodutível: dois builds seguidos deram o mesmo sha). Setores tocados
    contra o ORIGINAL, além dos da RC1: `0x0C7000`, `0x0CC000`, `0x0CD000`,
    `0x122000`, `0x156000`. A R1 **não muda a imagem**: o sha acima é o
    mesmo antes e depois (a correção é só de premissa e recusa).
- Decisões tomadas:
  - As duas ferramentas são **auto-suficientes** (só stdlib; `fab_logo` usa
    também Pillow). Thumb-2 `bl` é codificado e decodificado dentro de
    cada uma, sem importar de outra ferramenta: a premissa dos `bl` é
    sobre o *alvo* do salto, e comparar bytes crus não diz para onde o
    aparelho vai.
  - Cada uma confere as premissas **inteiras**, inclusive as dos itens que
    não escreve (é o que a ficha pede: "cada ferramenta confere TODAS as
    premissas"). Só o que muda é a lista de erros que cada recusa imprime.
  - O `fab_logo` grava alfa 255 nas 256 entradas da paleta, inclusive nas
    que nenhum pixel usa. A de fábrica deixa as não usadas com alfa 0, mas
    elas não aparecem na tela: o índice nunca as referencia.
  - Segunda passagem é recusada por construção (o `bl` e o imediato já não
    são os de fábrica). É o comportamento certo para ferramenta de receita,
    e está escrito na seção LIMITACOES das duas.
  - Nenhuma linha em `docs/` além desta Entrega: CHANGELOG, `RELOAD_1_0.md`
    e `docs/metricas.md` são do engenheiro (processo-padrao §2/§11).
- Pendências / limitações:
  1. **Resolvido na R1.** `tools/ci.sh` passo 5 não rodava aqui por versão
     do gitleaks: a linha usava `-q`, que o gitleaks 8.30.1 removeu. O
     merge do ramo principal trocou por `--log-level error` e o porteiro
     fecha verde, `CI OK`. Não é mais pendência.
  2. A imagem não foi testada no aparelho — é o roteiro do decisor (D8).
     Em especial: com o fundo do display preto em todas as telas, texto
     cinza-claro e seleção precisam continuar legíveis.
  3. A paleta depende da versão do Pillow (median cut). Com o sha256 do PNG
     fixado pela ficha, é reproduzível na mesma máquina; o que garante a
     imagem não é o algoritmo, e sim a conferência de erro que a
     ferramenta roda antes de gravar.
  4. Se `assets/OpenLogo.png` mudar, `fab_logo.py` recusa até alguém
     atualizar a constante `SHA_PNG`. É o que a ficha pediu (hash fixado),
     e é uma trava de duas mãos: quem quiser outra logo tem de passar por
     ficha nova.
- Danos notados e não cobertos:
  - **D8 (legibilidade sobre preto)** continua aberto: nenhum teste
    neste repositório vê texto nem seleção. Só o roteiro no aparelho fecha.
  - **D7 (`.up`)** continua com o engenheiro: `gera_versao` tem de dar
    [4/4] OK com esta imagem. Não gero kit, não carimbo versão.
  - **D2** é coberto pela conferência de cada ferramenta (ela aborta se
    escrever fora do próprio lote) e pelo C7; **D1** pela conferência do
    alvo decodificado depois de escrever.
  - Observação de fundo (não é dano, é para o registro): a logo nova é
    **opaca**, com o preto do PNG virando cor de paleta, não alfa 0. Sobre
    o fundo preto do item 2 o resultado é o mesmo; se um dia o fundo da
    abertura deixar de ser preto, a logo apareceria com um retângulo preto
    em volta. A ferramenta recusa PNG com alfa em vez de adivinhar.
  - **Falta o mesmo `--out` por link nas ferramentas mais antigas.**
    `patch_update_sd.py` (o passo 1 da receita) compara só
    `os.path.abspath(src) == os.path.abspath(dst)`, como eu fazia na R0:
    um symlink passaria. Não corrigi — é ferramenta já aprovada no aparelho
    (D02) e mexer nela é fora do escopo desta ficha. Sugestão para o
    engenheiro: puxar a ideia para o padrão de `tools/` numa ficha própria.

## Rodadas

### R1 — gpt-6-astra, análise do diff (códigos em `docs/seguranca.md`)
Achados: **1 MÉDIA + 1 BAIXA**, ambos da minha entrega.

| # | Sev. | Achado | Causa | Correção |
|---|---|---|---|---|
| 1 | MÉDIA | D3 ignorava `always_zero` e os bits reservados (5–9) do cabeçalho dos descritores | `confere_descritor()` comparava campo por campo: só `cf` (`header & 0x1F`), largura e altura. Bits 5–9 nunca eram lidos, e a ficha diz que o **descritor** é premissa, não o campo útil | As duas ferramentas comparam agora a **palavra de 32 bits inteira** com o valor de fábrica (`0x0462000A` na logo, `0x1402000A` no papel), e o erro passa a imprimir os dois valores em hex |
| 2 | BAIXA | `--out` que é symlink/hardlink da entrada sobrescrevia a entrada | Só havia `os.path.abspath(src) == os.path.abspath(dst)`, que compara **nome de caminho**, não arquivo. Um link com outro nome passa e a gravação vai dentro da entrada | Função `mesma_entrada()` nas duas: caminho igual **ou** `os.path.samefile` quando `--out` existe (`lexists`, com `OSError` → não é a mesma). Recusa 2, antes de qualquer leitura ou escrita |

Achado lateral que a correção do #1 expôs: minha constante do cabeçalho do
papel estava escrita `0x0140200A` (zero a mais) e só não apareceu antes
porque a conferência por campo comparava só `cf`. A conferida agora é a
palavra inteira, e a constante foi corrigida para `0x1402000A` (valor lido
no ORIGINAL). Sem isso, o `fab_logo` recusaria a própria imagem de fábrica —
que é o que a correction do #1 fez aparecer logo no primeiro build.

Verificação: `tests/test_rc2.py` **18/18** (16 da R0 + os 2 novos da R1),
`sh tools/ci.sh` **verde, `CI OK`** (passos 1 a 5, com o `ci.sh` corrigido
pelo merge). conferi ainda à mão: symlink e hardlink recusados pelas duas
ferramentas (rc=2, entrada intacta), `--dry-run` também recusa link, e um
bit reservado aceso no cabeçalho da **logo** é recusado pelo
`fab_fundo_preto` (a checagem é cruzada, como a R0 já pedia). A imagem da
RC2 **não mudou**: `fcca5fdc…` antes e depois, porque as duas correções são
de premissa e recusa, não de escrita.
