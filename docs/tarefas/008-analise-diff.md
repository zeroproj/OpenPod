REPROVADO
ANÁLISE 008 — MODO: DIFF — MODELO: glm-5.3
Diff revisado: a47e157…3751817 (commit do desenvolvedor). Verificado de novo
por esta sessão: build das 3 receitas (shas batem), carimbos (batem), os três
`.up` commitados (payload == imagem carimbada byte a byte, CRCs 0x58EE/
0x4478/0x6D8D, cobertura 0x1AB000) e `sh tools/ci.sh` → **CI OK**. Fora do
achado abaixo, o desenho (patches cirúrgicos de 4/2/2 bytes, premissas
nomeadas, diff final exato, scanner movw/movt+blx com conferência de
registrador) e o desvio do MAPA (o C2 protegido realmente recusa lote que
cruze o da RC7; o `--em` viaja na receita e a ferramenta recusa qualquer
outro — padrão já usado por `patch_nome_faixa.py`) estão **aprovados**.

[MÉDIA] tools/fab_diag_trava.py:67 (`NIVEL["b"] = F_OPEN`) +
docs/tarefas/008-rc7-trava.md:227 (coluna "se TRAVAR" do degrau B) — **o
degrau B não mede só o `get_path`: ele arrasta `calloc(FIL)` + `free(FIL)` +
dois `free(NULL)`** (o `capa_falha` do `.s` libera o JDEC e o pool, que no
nível B nunca foram alocados — tools/capa_album.s:491-497). O `free` real da
fábrica (`0xCF7884`) desvia para `0x9E3C`, **ROM fora do dump** (conferido
por esta sessão): é indecidível se ele tolera `NULL`. Cenário concreto: o
decisor grava o B, toca, e o `free(NULL)` dá **UsageFault** — num firmware
sem handler dedicado, fault é **loop mortal (congela)**, não reinicia; a
tabela do roteiro diria "o banco/mutex É a causa" — **falso positivo** no
degrau exato que a análise (H1) apontou como o mais provável de revelar a
causa. A ficha 008 pede "B: A + get_path (**sem arquivo**)" e o desenho
entrega "get_path + heap + free(NULL)×2".
**Correção (R1):** redesenhar o nível B para desligar o **`bl carrega_capa`**
do `corpo_titulo` (tools/capa_album.s:267) em vez do `f_open`: o `bl`
interno (4 bytes) vira `movs r0, #0` + `nop` (`00 20 00 BF`) — o `cmp r0,#0;
beq fim_titulo` que já existe termina o TITULO depois do `get_path`, da
comparação, do guardado e do quadrado cinza: **sem calloc, sem free, sem
arquivo** — "A + get_path, sem arquivo" literal. Como achar: o `carrega_capa`
é a **única** rotina do `.s` cujo prólogo é `push {r4-r11,lr}` + `sub
sp,#12` (`2D E9 4F F0 8C B0`; as outras seis com `push` de 9 registros usam
`sub sp,#4` — conferido) — o scanner decodifica os `bl` internos do lote e
exige exatamente 1 cujo alvo comece com essa assinatura (decodificar o `bl`
de volta antes de escrever; diff final do B passa a ser 4 bytes). O C fica
como está. Regenerar o kit do B (A e C não mudam). Atualizar o teste do
comportamento do B (a sequência fica `label_set_text`, `get_path`,
`img_set_src` cinza — **nada mais**) e a Entrega/roteiro: a coluna do B
perde a ressalva do `free(NULL)`; o `free(NULL)` da RC7 (caminho "sem
capa"/erro, ferramenta 007) passa a ser coberto pelo **roteiro**: tocar
também um MP3 **sem capa** (`06_sem_capa.mp3` do kit 007) no C e no D —
se C/D travarem só sem capa, a causa é o `free(NULL)` (achado novo, H5), não
o tempo do JPEG.

[BAIXA] docs/tarefas/008-rc7-trava.md:229 — "oculpado é outro" (typo; o
roteiro vai ser reescrito por esta sessão de qualquer forma).

Teste sugerido: no `tests/test_diag_trava.py`, o teste do comportamento do B
deve afirmar a sequência **exata** de chamadas (`label_set_text`, `get_path`,
`img_set_src` do cinza) com **zero** `calloc`/`free`/`f_open`, e o teste de
recusa deve incluir uma RC7 com o `bl carrega_capa` já patcheado.

---

## Conferência final (R1) — glm-5.3, 2026-11-01

APROVADO — só o diff desde a 1ª análise (`3751817…cec68a1`), e reconferido
por esta sessão de forma independente (build das receitas, carimbos e
payloads dos `.up` recomputados, `ci.sh` e o teste do dev reexecutados):

- o nível B agora corta o **`bl` interno** do `carrega_capa` (4 bytes em
  `0x1AA188`, `00 20 00 BF` = `movs r0,#0` + `nop`), achado pela
  **assinatura única** do prólogo (`push {r4-r11,lr}` + `sub sp,#12` =
  `2D E9 4F F0 83 B0` — conferido no `.s` e no lote montado; `sub sp,#12`
  é `0xB083` porque o imediato do encoding T1 é múltiplo de 4) e pelo
  `bl` decodificado de volta (alvo `0x00DAA256`, o prólogo);
- o diff real RC7→B são **3 bytes** (`0x1AA189..0x1AA18B`) — o primeiro
  byte do `bl` já era `00` e não muda; a ferramenta passou a conferir
  "nenhum byte fora da região do patch", que é o correto para esse caso;
- **sem** `calloc`/`free`/`f_open`/`f_read`/`f_close` no B (o teste exige
  a sequência exata `label_set_text`, `get_path`, `img_set_src` do
  cinza); o `free(NULL)` saiu do degrau B e ficou coberto pelo **roteiro**
  (MP3 sem capa no C e no D — o achado **H5** sobre a própria RC7, com o
  `free` real na ROM fora do dump, registrado na ficha e no Pacote);
- imagens reconferidas: A `66c678b5…`, B `952c79fb…` (carimbada
  `eab560c9…`), C `c51ec6e0…` (carimbada `88d1ddb1…`); os três `.up`
  commitados (A `91fcb645…`, B `3986e741…`, C `c1046cee…`) têm o payload
  igual à imagem carimbada **byte a byte** (CRC 0x58EE / 0x3768 /
  0x6D8D), cobertura `0x1AB000`, bootloader e setor 0xD000 iguais aos de
  fábrica, PSMP fora;
- `tests/test_diag_trava.py`: **26 testes OK** (reexecutado por esta
  sessão); `sh tools/ci.sh`: **CI OK** (rodado por esta sessão antes e
  depois da R1); nenhum arquivo protegido mudou (o hash de
  `tests/PROTEGIDOS.sha256` é conferido pelo próprio `ci.sh`).

Sem achados novos.
