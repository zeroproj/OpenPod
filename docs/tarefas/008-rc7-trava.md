# Ficha 008 — RC7 trava ao tocar (diagnóstico)

Tipo: **Risco** (a Tocando Agora do aparelho). Base: `privado-completo` com a RC7
(imagem `3af97713…`, ficha 007). Quem conduz: sessão GLM (D10/D12, a pedido do decisor:
"aqui a gente só coordena"). Desenvolvedor: `minimax/MiniMax-M3`.

## Sintoma (decisor, aparelho, 2026-11-01)
"quando eu coloco para tocar ele trava. Às vezes ele abre o player só que não toca a
música, mas também não mostra a capa." → CONFIRMADO no aparelho. O decisor volta à RC6.

Leitura: a ViewTask (ou o sistema inteiro) para **dentro do TITULO, antes do `set_src` da
capa**, e o áudio também não começa. O arnês (`tests/emu_rc7.py`) passa porque troca por
stubs exatamente o que não foi exercitado de verdade: heap, FatFs, `get_path` e LVGL.

## Hipóteses (nenhuma confirmada; classificar ao investigar)
- **H1 — trava entre tarefas (HIPÓTESE, a mais forte).** O TITULO roda na ViewTask e chama
  `get_path` `0xCFEFC4` → `0xD6D1B4`, que **pega um mutex do banco** (`[[pc+0x3c]]+0x5C` via
  `0x80DB48`, solta em `0x80DB6E`, código em RAM) e depois o FatFs (`fs+0x14`). Na fábrica
  quem chama `get_path` é a MainTask (presenter). Se a MainTask/tarefa do áudio segura esse
  mutex (ou o do FatFs, ou a trava da LVGL) e espera a ViewTask → ABBA. Conferir: quem pega
  `+0x5C`, se `0x80DB48` espera para sempre, se a MainTask manda a mensagem do título e espera
  a ViewTask (envio síncrono), e a ordem de travas da fábrica.
- **H2 — pilha da ViewTask (HIPÓTESE).** Os 392 B medidos não contam o `get_path` real
  (quadro `0x238` + `0xD6F138`…) nem o `f_open` real (LFN). Somar a profundidade real no
  ponto do `label_process`.
- **H3 — falha de CPU (HIPÓTESE).** A fábrica tem zero `udiv` em 1,75 MiB → o núcleo pode
  não ser ARMv7-M comum (ex.: v7-A/R) e checar alinhamento. Procurar acesso desalinhado e
  qualquer instrução do lote que a fábrica nunca usa.
- **H4 — interface real diferente do stub (HIPÓTESE).** Tamanho do FIL (≤ `0x25C` era
  PROVÁVEL), `f_lseek` 64 bits em `r2:r3`, formato do caminho, retorno de `get_path`.

## O que entregar
1. Análise estática (só leitura do ORIGINAL) de H1..H4 com CONFIRMADO/PROVÁVEL/HIPÓTESE.
2. **Imagens de bisseção pelo cartão**, cada uma com um degrau a mais, a partir da RC7, sem tocar
   nada fora dos bytes da RC7, cada uma com `.up` (via `gera_versao`) e carimbo próprio
   (`patch_versao --em 0x1A4F00`, "RC7 diag A" etc.):
   - **A:** TITULO só faz o `set_text` (CRIA fica: quadrado cinza);
   - **B:** A + `get_path` (sem arquivo);
   - **C:** B + `f_open`/`f_close`;
   - **D:** a RC7 inteira (já existe).
   Se a análise confirmar a causa antes, propor direto a correção (ex.: tirar `get_path`/FatFs
   da ViewTask) em vez da bisseção, e perguntar ao decisor.
3. Roteiro curto para o decisor gravar A→B→C e dizer onde trava.
4. Nada de mexer nos testes protegidos; receitas novas são de diagnóstico (não entram na
   catraca). Ferramentas novas ≤ 350 linhas. `sh tools/ci.sh` verde.

## Entrega (preenchida pelo desenvolvedor — MiniMax M3, 2026-11-01)

### O que foi feito

Três **imagens de bisseção** (A, B e C) a partir da **RC7 exata** (sha
`3af97713…`), mais o D que já existia. As três são **patches cirúrgicos no
lote já montado** — nada foi remontado, nada fora dos bytes da RC7 foi
tocado:

| degrau | o que muda | bytes | onde |
|---|---|---|---|
| **A** | a entrada `TITULO` da tabela do lote passa a apontar para o `lv_label_set_text` da fábrica (`0x00D5ED94`) | **4** | `0x1AA014` |
| **B** | o `blx` da **única** chamada externa ao `f_open` (`0x00D777CD`) vira `movs r0, #1` | **2** | `0x1AA294` |
| **C** | o `blx` da **única** chamada externa ao `jd_prepare` (`0x00D10B21`) vira `movs r0, #1` | **2** | `0x1AA31E` |

- **`tools/fab_diag_trava.py`** (323 linhas) — a ferramenta da receita:
  `--in/--out/--nivel a|b|c/--em/--dry-run`, premissas nomeadas conferidas
  **antes** de escrever, recusa sem criar saída, conferência do resultado
  (decodifica o `b.w` novo de volta) e **diff final** contra a entrada
  (tem de ser exatamente 4/2/2 bytes, nos lugares certos).
- **`tools/diag_trava_asm.py`** (133 linhas) — o módulo com o layout do lote
  e o **scanner Thumb-2** que acha o par `movw/movt` que carrega um
  endereço (com o bit do Thumb) e o `blx` que o usa; usa o
  `tools/capa_album_asm.py` (o mesmo par encoder/leitor do `test_rc7.py`).
- **`tools/build.py`** — três receitas novas: `reload_1.0_rc7_diag_a`,
  `_b` e `_c` (= `reload_1.0_rc7` + `fab_diag_trava.py`), em `RECEITAS`.
  `AREA_FIM` **não muda** (`0x1AB000`).
- **`tests/test_diag_trava.py`** (novo, **não** protegido) — 24 testes.
- **Nenhum teste protegido, `tools/ci.sh`, `firmware/ORIGINAL/` ou
  ferramenta da receita RC7 foi tocado.** `sh tools/ci.sh`: **verde**
  (`CI OK`).

### Imagem

| | receita | sha256 (sem carimbo) | sha256 (carimbada) | sha256 do `.up` | CRC |
|---|---|---|---|---|---|
| **A** | `reload_1.0_rc7_diag_a` | `66c678b59e47808921e546b8666613cb3dc9b7f8046ad9c1af7bb77aed3ca7f4` | `cceb3edb39939a0ca3e5a42fd4fcc84788dd375a26cee0942b0978027d027209` | `91fcb645f0d7beab2e73c518b664b01ed6fb3466913705ebd72dd49d853d1295` | `0x58EE` |
| **B** | `reload_1.0_rc7_diag_b` | `a2979126c8b18896d364f753570f06dcf676be32c5cb0ff0d2f65b5861efa402` | `20598de38d93f72292e717858255b35ac40fb7d033272e3e30d83f79d8ba814f` | `3a98b9917aff906c45b1ee83f898eec0ad13cbb124354fefebd358fea5b1d660` | `0x4478` |
| **C** | `reload_1.0_rc7_diag_c` | `c51ec6e0d73684a7f249eb968a331d8ddcb77d2afc3f162b710b532230261fbb` | `88d1ddb1204ca05d78e593569bba8a2e087fbcda4e3853e21e3478975441c25d` | `c1046cee3767a1e52972ec4c65f12e71a72c0d3ec9140311a3abe3b9e78a6a26` | `0x6D8D` |

- RC7 (o degrau **D**, já existia): `3af97713c9d8e28c2b36b872fd5883d18af9e65bff443c5e99ab645678237d9e`.
- **RC7 → diag:** exatamente os bytes da tabela acima e **nada mais**:
  A = 4 bytes em `0x1AA014`; B = 2 bytes em `0x1AA294`; C = 2 bytes em `0x1AA31E`.
- **Carimbo:** `patch_versao --em 0x1A4F00` com o texto `RC7 diag A/B/C`
  (11 B de texto no slot + 4 B do literal em `0x10A59C`; a string de
  fábrica fica intacta). O nome que aparece em Config → Informações é
  `RC7 diag A` / `RC7 diag B` / `RC7 diag C`.
- **Kits** (pelo `gera_versao`, que confere CRC, payload byte a byte, PSMP
  fora e bootloader intocado):
  - `firmware/RELEASE/OpenPod Reload 1.0 RC7 Diag A|B|C/` (setores + `.up`
    + `diag.sh` + `flash_*.sh` + `recovery_check_linux.sh` + `LEIA-ME.txt`)
  - `release/OpenPod-Reload-1.0-RC7-Diag-A|B|C/` (o pacote público, com o
    `.up` e `cabo/setores/`).
- Nada abaixo de `0x00E000`; setor `0x00D000` e PSMP (`0x1FC000+`)
  intocados; build reprodutível (duas execuções, o mesmo sha).

### Decisões

- **A entrada é a RC7 pelo sha256** (`3af97713…`), como a ficha manda: é a
  premissa única e as outras conferências (a tabela de entradas no lugar,
  a chamada alvo aparecendo **exatamente uma vez** no código do lote, a
  região não estar já patcheada) continuam no código, nomeadas, para dizer
  *o que* está errado.
- **A chamada é achada pelo código, não por endereço fixo.** O scanner
  procura, no código do lote (`0x1AA01C` até o fim, os `0xFF` marmam o
  fim), o par `movw/movt` que carrega o alvo **com o bit do Thumb** e o
  `blx` logo depois; a tool recusa se aparecer ≠ 1 vez. Os `blx` são de 2
  bytes (`blx r12` = `0x47E0`), então "desligar a chamada" são 2 bytes
  (`01 20` = `movs r0, #1`) — e é isso que a RC7 gasta.
- **O `movs r0, #1` no lugar do `blx` é seguro quanto ao `lr`:** o
  `blx` é o que grava o `lr` de retorno, e a sua ausência foi conferida no
  código desmontado — o caminho de erro termina em `CHAMAR FREE` (que
  grava o `lr`) antes do `pop {…, pc}` de cada rotina. Nos três degraus o
  retorno é o certo (conferido no emulador: `m.erros == []`).
- **A ferramenta nova NÃO entra no `MAPA`** (desvio do despacho, com
  motivo): o `tests/test_rc7.py` **protegido** (C2) recusa qualquer lote
  do `MAPA` que cruze o lote da RC7
  (`assertFalse(ini < LOTE + LOTE_TAM and LOTE < ini + tam)`), e o despacho
  pedia `MAPA["fab_diag_trava.py"] = (0x001A8000, 0x3000)` — o **mesmo**
  lote da capa. Com a entrada no `MAPA`, o `ci.sh` fica **vermelho**
  (`lote cruza fab_diag_trava.py`) e o teste protegido não pode ser
  mexido. Como a ferramenta **não aloca nada** (só patcha 4/2/2 bytes
  dentro do lote que a RC7 já montou), o endereço do lote passou a viajar
  **na receita** (`--em 0x1a8000`), e a ferramenta recusa qualquer outro
  `--em` — o mesmo padrão que `patch_nome_faixa.py` e
  `patch_faixa_degrade.py` já usam. Se o arquiteto preferir a entrada no
  `MAPA`, é **uma linha** no teste protegido (aceitar uma segunda
  ferramenta no mesmo lote) e a entrada volta.
- **As receitas de diagnóstico não entram na catraca** e não mexem em
  teste nenhum (`tests/test_catraca.py` continua com a RC6; verificado
  pelo `test_18`).

### Verificações feitas

- **O comportamento de cada degrau, no arnês de emulação** (unicorn, o
  `tests/emu_rc7.py` — só heap, FatFs, caminho da faixa e LVGL são stubs;
  cada stub registra a chamada):
  - **A**: a sequência é **só** `label_set_text` — nenhum `get_path`,
    nenhum `f_open`. É o comportamento de fábrica.
  - **B**: `label_set_text`, `get_path` (o de verdade), `img_set_src` (o
    quadrado cinza), `calloc` (o FIL) e 3 `free` — **nenhum `f_open`**,
    nenhum `f_read`, nenhum `f_close`.
  - **C**: `label_set_text`, `get_path`, `calloc` ×3 (FIL, JDEC, pool),
    `f_open` **real**, as leituras da tag (`f_read`/`f_lseek`), `f_close`
    **real** — e **nenhum JPEG**: o `jd_prepare` não roda (o único `src`
    é o quadrado cinza).
  - **D** (a RC7, para contraste): o mesmo caminho com a capa no fim (o
    último `img_set_src` **não** é o quadrado cinza).
- **O diff RC7 → diag** é conferido byte a byte pelo teste (4/2/2 bytes e
  nada mais) e a **decodificação de volta**: o `b.w` novo da entrada
  `TITULO` é lido e aponta para `0x00D5ED94`; os 2 bytes novos são
  `01 20` e decodificam como `movs r0, #1`.
- **`tests/test_diag_trava.py`** (24 testes, rodado a mao — o `ci.sh`
  protegido roda só a lista fixa dele):
  - a RC7 exata e as três receitas constroem;
  - **build reprodutível**: duas execuções de cada receita, o mesmo sha;
  - o diff exato e nada fora do lote;
  - as recusas: RC6, **RC6 carimbada**, RC7 truncada, RC7 com o lote
    mexido, RC7 com o `movw` do `f_open` mexido, `--dry-run` (não grava),
    `--out` igual/symlink/hardlink da entrada, `--em` errado e o
    reprocessamento de uma saída — **nenhuma** delas cria arquivo;
  - as premissas, uma por uma (inclusive "já patcheada" e "a chamada não
    existe"), no branco sobre preto.
- **`sh tools/ci.sh`: verde** (`CI OK`) — round-trip + RC2..RC7 + a
  regressão da RC7 (`test_rc7_trava.py`) + a catraca.

### Pendências / não coberto

- **Nada foi gravado no aparelho**: o roteiro abaixo continua inteiro. Toda
  a conferência aqui é de emulação (e os stubs do arnês trocam justamente o
  heap, o FatFs e o LVGL — o **tempo real** de cada degrau não foi
  medido).
- **O `free(NULL)` do degrau B.** No B o `f_open` "falha" e o caminho de
  erro libera o JDEC e o pool, que **nunca foram alocados** → dois
  `free(NULL)`. O `free` da fábrica (`0xCF7884`) desvia para a **ROM
  baixa** (`0x9E3C`), que **não está no dump**: não dá para saber se ela
  tolera ponteiro nulo. Se não tolerar, a imagem **B reinicia o aparelho**
  no primeiro título (e não trava) — o que é distinguível na hora (veja o
  roteiro). O mesmo `free(NULL)` já existia na RC7 (caminho "sem memória"),
  então não é novidade do patch.
- **A bisseção mede a LENTIDÃO, não um sim/não.** H1 (PROVÁVEL) diz que o
  ring enche porque o TITULO ficou lento (dezenas de ms por título). A, B e
  C são degraus de lentidão crescente; **se B e C não travarem, isso não
  refuta H1** — pode ser que só o D (o JPEG inteiro) encha o ring. O que
  interessa é o **primeiro degrau que trava**.
- **O `MAPA` da ferramenta ficou de fora** (motivo acima): pendência para
  o arquiteto decidir se prefere a entrada no `MAPA` (e amendar o C2
  protegido) ou o `--em` na receita como está.
- **Os kits não foram publicados** (sem `push`, sem `publica_release.py`):
  a publicação é da coordenação, depois do `PRONTO-008`.

### Danos notados

- **Nenhum dano novo** no firmware: os três degraus só desligam trabalho
  (o `f_open` no B, o `jd_prepare` no C) ou devolvem o TITULO ao da
  fábrica (no A). Nada é escrito fora do lote, nada muda o comportamento
  de outra tela, e o **D14** (pausa na tela ao decodificar) e o **D13**
  (gravação interrompida) seguem como na RC7.
- **O único risco novo é o `free(NULL)` do degrau B** (acima): no pior
  caso, um reinício do aparelho em vez de um travamento — e é justamente
  no degrau B, o que pode ser lido errado como "B travou".

### Roteiro para o decisor (A → B → C → D)

Grava pelo cartão (o `.up` de cada um, em `firmware/RELEASE/OpenPod Reload
1.0 RC7 Diag A|B|C/`). Antes de cada degrau, anota o que o aparelho mostra
em Config → Informações (é `RC7 diag A`, `RC7 diag B`, `RC7 diag C`; no D
é a RC7). Depois de gravar: **Config → Atualizar por SD**, reiniciar,
abrir a **Tocando Agora** e **tocar** uma faixa (o `01_capa_v23.mp3` de
`tests/assets/rc7/` é o melhor caso: tem capa). Repete com **trocar de
faixa** (`>>|`).

Anota, para cada degrau: **(1)** o player abre? **(2)** a música toca?
**(3)** a capa aparece (ou fica o quadrado cinza)? **(4)** o aparelho
**trava** (tela viva, relógio/medidor parado, não volta — só desligando),
**reinicia** (volta sozinho ao logo), ou **continua normal**?

| degrau | o que ele mede | se TRAVAR | se REINICIAR | se ficar NORMAL |
|---|---|---|---|---|
| **A** | o TITULO é o de fábrica (nem `get_path`, nem FatFs) | H1 e o `get_path`/banco **não** são a causa: a lentidão do banco não é o gatilho | idem A | o degrau é rápido demais: **vá para B** |
| **B** | `get_path` de verdade (mutex do banco + FatFs do db), **sem** abrir o MP3 | o **banco/mutex** (`0x81DC00+0x5C`) ou o FatFs **é** a causa | provavelmente o `free(NULL)` do B (veja "Danos notados") | vá para **C** |
| **C** | `f_open`/`f_close` reais, **sem** JPEG | o **FatFs** (abrir/fechar o arquivo do usuário) é a causa | idem C | vá para **D** |
| **D** | a RC7 inteira (o degrau que trava hoje) | a causa está **depois** do `jd_prepare` (o JPEG, a reescala, o `jd_decomp`) | idem D | a trava **não** é da capa: oculpado é outro (H1-ring, que é tempo, não a capa) |

- Se **A** já travar, o problema **não** é a capa: é o ring de mensagens
  (H1) exposto por **qualquer** mensagem de título, e a correção muda
  (tirar o `get_path`/FatFs da ViewTask é a via da ficha 008).
- Se só o **D** travar, a causa está no JPEG (e aí o conserto é outro:
  cachear a capa, ou procurar o APIC no presenter).
- Congelamento com a tela viva que **não volta** = o deadlock do ring
  (H1). **Reinício** no B = o `free(NULL)`. **Normal** até o D = outra
  coisa.
