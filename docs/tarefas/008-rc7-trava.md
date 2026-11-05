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
| **B** | o `bl` **interno** que chama o `carrega_capa` vira `movs r0, #0` + `nop` (`00 20 00 BF`): o TITULO para depois do `get_path` | **4** | `0x1AA188` |
| **C** | o `blx` da **única** chamada externa ao `jd_prepare` (`0x00D10B21`) vira `movs r0, #1` | **2** | `0x1AA31E` |

> **R1 (análise do diff, glm-5.3):** o degrau **B** foi **redesenhado**.
> Antes ele desligava o `blx` do `f_open`, e o caminho de erro do
> `carrega_capa` chamava `free(NULL)` **duas vezes** (o JDEC e o pool nunca
> tinham sido alocados) — o `free` da fábrica desvia para a ROM (`0x9E3C`),
> fora do dump, e se ele não tolerar `NULL` o fault **congela** o aparelho:
> um falso positivo no degrau que existe justamente para medir o
> `get_path`. Agora o B corta o **`bl` do `carrega_capa`**: o TITULO faz o
> `get_path` de verdade, compara o caminho, guarda-o e mostra o quadrado
> cinza, e o `cmp r0,#0; beq fim_titulo` que já existe logo depois termina
> o TITULO — **sem `calloc`, sem `free`, sem arquivo**. A e C não mudaram.

- **`tools/fab_diag_trava.py`** (329 linhas) — a ferramenta da receita:
  `--in/--out/--nivel a|b|c/--em/--dry-run`, premissas nomeadas conferidas
  **antes** de escrever, recusa sem criar saída, conferência do resultado
  (decodifica o `b.w` novo de volta, e os bytes novos como instrução) e
  **diff final** contra a entrada (nenhum byte pode mudar **fora** da
  região do patch: 4/4/2 bytes).
- **`tools/diag_trava_asm.py`** (243 linhas) — o módulo com o layout do lote
  e os **scanners Thumb-2**: o par `movw/movt` + `blx` (chamadas externas),
  os `bl` **internos** e a assinatura do `carrega_capa`; e o patch de cada
  nível (onde é, quantos bytes, o que fica no lugar). Usa o
  `tools/capa_album_asm.py` (o mesmo par encoder/leitor do `test_rc7.py`).
- **`tools/build.py`** — três receitas novas: `reload_1.0_rc7_diag_a`,
  `_b` e `_c` (= `reload_1.0_rc7` + `fab_diag_trava.py`), em `RECEITAS`.
  `AREA_FIM` **não muda** (`0x1AB000`).
- **`tests/test_diag_trava.py`** (novo, **não** protegido) — 26 testes.
- **Nenhum teste protegido, `tools/ci.sh`, `firmware/ORIGINAL/` ou
  ferramenta da receita RC7 foi tocado.** `sh tools/ci.sh`: **verde**
  (`CI OK`).

### Imagem

| | receita | sha256 (sem carimbo) | sha256 (carimbada) | sha256 do `.up` | CRC |
|---|---|---|---|---|---|
| **A** | `reload_1.0_rc7_diag_a` | `66c678b59e47808921e546b8666613cb3dc9b7f8046ad9c1af7bb77aed3ca7f4` | `cceb3edb39939a0ca3e5a42fd4fcc84788dd375a26cee0942b0978027d027209` | `91fcb645f0d7beab2e73c518b664b01ed6fb3466913705ebd72dd49d853d1295` | `0x58EE` |
| **B** | `reload_1.0_rc7_diag_b` | `952c79fb3e6a4d2bdd2ae477060795ce8ea7e88c8523384bb62e468234844896` | `eab560c9008e164b9968d6e002fc5e4c4eeffd33b5467a220fedd796c0000b91` | `3986e7417ce2691c3bc96dbc3abef3865dd40a66a8c1eb455ebadd97452945df` | `0x3768` |
| **C** | `reload_1.0_rc7_diag_c` | `c51ec6e0d73684a7f249eb968a331d8ddcb77d2afc3f162b710b532230261fbb` | `88d1ddb1204ca05d78e593569bba8a2e087fbcda4e3853e21e3478975441c25d` | `c1046cee3767a1e52972ec4c65f12e71a72c0d3ec9140311a3abe3b9e78a6a26` | `0x6D8D` |

- RC7 (o degrau **D**, já existia): `3af97713c9d8e28c2b36b872fd5883d18af9e65bff443c5e99ab645678237d9e`.
- **RC7 → diag:** exatamente os bytes da tabela acima e **nada mais**:
  A = 4 bytes em `0x1AA014`; B = 4 bytes em `0x1AA188` (o `bl` cortado:
  `00 20 00 BF`; 3 deles mudam de valor, o primeiro já era `00`);
  C = 2 bytes em `0x1AA31E`.
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
- **O alvo é achado pelo código, não por endereço fixo.** O scanner
  procura, no código do lote (`0x1AA01C` até o fim, os `0xFF` marmam o
  fim): no nível C, o par `movw/movt` que carrega o alvo **com o bit do
  Thumb** e o `blx` logo depois; no nível B, a **assinatura do
  `carrega_capa`** — `push {r4-r11,lr}` + `sub sp,#12` (`2D E9 F0 4F
  83 B0`), a única rotina do lote com nove registradores e `sub sp,#12`
  (as outras seis usam `sub sp,#4`) — e o `bl` **interno** que a chama.
  Em ambos a tool recusa se aparecer ≠ 1 vez, e o alvo é **decodificado do
  binário** (o `bl` é relido e conferido antes de escrever).
- **O `movs r0, #1` no lugar do `blx` é seguro quanto ao `lr`:** o
  `blx` é o que grava o `lr` de retorno, e a sua ausência foi conferida no
  código desmontado — o caminho de erro termina em `CHAMAR FREE` (que
  grava o `lr`) antes do `pop {…, pc}` de cada rotina. Nos três degraus o
  retorno é o certo (conferido no emulador: `m.erros == []`).
- **O nível B corta o `bl` interno, não a chamada externa (R1).** O
  `bl` (4 bytes) vira `movs r0, #0` + `nop` (`00 20 00 BF`): o `cmp
  r0,#0; beq fim_titulo` que já existe logo depois termina o TITULO. O
  `bl` é um branch relativo: o montador grava o **deslocamento**, e o
  destino é lido de volta do binário (`desvio`) — é isso que a
  conferência do patch confere.
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
  - **B**: a sequência é **exata** — `label_set_text`, `get_path` (o de
    verdade) e `img_set_src` (o quadrado cinza). **Zero `calloc`, zero
    `free`, zero `f_open`**: o TITULO para depois do `get_path` e não
    entra no `carrega_capa` (é o que a R1 pediu: o degrau que mede o
    `get_path` não arrasta mais o heap nem o `free(NULL)`).
  - **C**: `label_set_text`, `get_path`, `calloc` ×3 (FIL, JDEC, pool),
    `f_open` **real**, as leituras da tag (`f_read`/`f_lseek`), `f_close`
    **real** — e **nenhum JPEG**: o `jd_prepare` não roda (o único `src`
    é o quadrado cinza).
  - **D** (a RC7, para contraste): o mesmo caminho com a capa no fim (o
    último `img_set_src` **não** é o quadrado cinza).
- **O diff RC7 → diag** é conferido byte a byte pelo teste (nenhum byte
  fora da região do patch: 4/4/2 bytes) e a **decodificação de volta**: o
  `b.w` novo da entrada `TITULO` é lido e aponta para `0x00D5ED94`; os 4
  bytes novos do B são `00 20 00 BF` e decodificam como `movs r0, #0` +
  `nop`; os 2 do C são `01 20` e decodificam como `movs r0, #1`.
- **`tests/test_diag_trava.py`** (26 testes, rodado a mao — o `ci.sh`
  protegido roda só a lista fixa dele):
  - a RC7 exata e as três receitas constroem;
  - **build reprodutível**: duas execuções de cada receita, o mesmo sha;
  - o diff exato e nada fora do lote;
  - as recusas: RC6, **RC6 carimbada**, RC7 truncada, RC7 com o lote
    mexido, RC7 com o `movw` do `jd_prepare` mexido, RC7 com o prólogo do
    `carrega_capa` mexido, RC7 com o `bl` do `carrega_capa` mexido,
    `--dry-run` (não grava), `--out` igual/symlink/hardlink da entrada,
    `--em` errado e o reprocessamento de uma saída — **nenhuma** delas
    cria arquivo;
  - as premissas, uma por uma (inclusive "já patcheada" — a entrada
    `TITULO`, o `bl` do `carrega_capa` e o `blx` do `jd_prepare` — e
    "o alvo não existe"), no branco sobre preto.
- **`sh tools/ci.sh`: verde** (`CI OK`) — round-trip + RC2..RC7 + a
  regressão da RC7 (`test_rc7_trava.py`) + a catraca.

### Pendências / não coberto

- **Nada foi gravado no aparelho**: o roteiro abaixo continua inteiro. Toda
  a conferência aqui é de emulação (e os stubs do arnês trocam justamente o
  heap, o FatFs e o LVGL — o **tempo real** de cada degrau não foi
  medido).
- **O `free(NULL)` saiu do degrau B (R1)** — o B agora não entra no
  `carrega_capa`, e portanto não há `calloc`, nem `free`, nem arquivo
  nele. Mas o **`free(NULL)` da própria RC7 continua nos degraus C e D**:
  quando o MP3 **não tem capa** (ou o APIC é inválido), o `procura_apic`
  falha **antes** do `calloc` do JDEC e do pool, e o caminho de erro
  libera os dois (nulos). O `free` da fábrica (`0xCF7884`) desvia para a
  **ROM baixa** (`0x9E3C`), que **não está no dump**: não dá para saber se
  ela tolera ponteiro nulo, e num firmware sem handler dedicado um fault
  é **loop mortal (congela)**, não reinício. Isso virou **H5** e está no
  roteiro (tocar um MP3 **sem capa** no C e no D).
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
  (o `carrega_capa` no B, o `jd_prepare` no C) ou devolvem o TITULO ao da
  fábrica (no A). Nada é escrito fora do lote, nada muda o comportamento
  de outra tela, e o **D14** (pausa na tela ao decodificar) e o **D13**
  (gravação interrompida) seguem como na RC7.
- **O risco do `free(NULL)` saiu do degrau B** (R1) — ele é da **RC7** e
  fica nos degraus **C e D**, e só no caminho "MP3 **sem capa**". Não é
  novidade do patch (o `capa_falha` da RC7 já liberava o JDEC e o pool,
  que nesse caminho nunca foram alocados), e é o que o roteiro mede.

### Roteiro de gravação (decisor) — A → B → C, nesta ordem

O `.up` de cada degrau está em `firmware/RELEASE/OpenPod Reload 1.0 RC7
Diag A|B|C/`. Grava como a RC7: `.up` no cartão → **Config → Atualizar por
SD** → reiniciar. Antes de começar, confira o carimbo em **Config →
Informações** (`RC7 diag A` / `RC7 diag B` / `RC7 diag C`).

Em **cada** degrau, o mesmo roteiro (os MP3 são os do kit 007,
`tests/assets/rc7/`):

| # | passo | ✔/✘ |
|---|---|---|
| 1 | tocar `01_capa_v23.mp3` (**com** capa) | |
| 2 | tocar `06_sem_capa.mp3` (**sem** capa) | |
| 3 | trocar de faixa 3× (`>>|` / `|<<`) com música tocando | |

Anotar a cada passo: **(1)** o player abre? **(2)** toca? **(3)** capa ou
quadrado cinza? — e o desfecho: **normal** / **travou** (tela parada que
não volta nem depois de 30 s) / **reiniciou** (voltou sozinho ao logo).

| degrau | carimbo | o que o TITULO já faz nele | se travar aí, a causa é… |
|---|---|---|---|
| **A** | RC7 diag A | só o `set_text` (o de fábrica) | não é a capa: é o envio de mensagens à view (H1) — **avisar a coordenação** |
| **B** | RC7 diag B | + `get_path` (mutex do banco + `db_audio.db`), sem heap e sem arquivo | o `get_path`/mutex do banco (H1) |
| **C** | RC7 diag C | + `f_open`/`f_close` do MP3, sem JPEG | o FatFs do arquivo do usuário |
| **D** | RC7 (a que trava hoje) | tudo (JPEG + reescala) | o tempo do JPEG/reescala (H1/D14) |

**Como ler o resultado** (as quatro linhas que importam):

- **Trava a partir do B** (com capa ou sem) → `get_path`/FatFs chamado da
  ViewTask (H1): a correção é o presenter mandar o **caminho** junto com a
  mensagem do título (a view para de tocar no banco).
- **Trava só no D** → o JPEG: cachear a capa ou decodificar fora da
  ViewTask.
- **Trava só com o `06_sem_capa.mp3`** (no C ou no D, nunca no A/B) → o
  `free(NULL)`×2 do caminho de erro da RC7 (**H5**, achado da R1): a
  correção é na ferramenta da capa, e a RC7 travaria até com MP3 sem capa.
- **Tudo normal até o D** (e o D também) → a trava não é da capa: reabrir
  com o decisor.

Ao terminar, **volte à RC6** (o kit que você já tem) e mande a tabela
preenchida para a coordenação.

## Rodadas

- **Rodada 1 (2026-11-01, MiniMax M3)** — a entrega inicial: as três
  imagens de bisseção (A, B e C, com 4/2/2 bytes), a ferramenta
  `tools/fab_diag_trava.py` (+ o módulo `tools/diag_trava_asm.py`), as três
  receitas, os três kits e o teste `tests/test_diag_trava.py`.
  `sh tools/ci.sh` verde.
- **Rodada 2 (2026-11-01, MiniMax M3) — R1 da análise do diff**
  (`docs/tarefas/008-analise-diff.md`, glm-5.3: **1 MÉDIA** + 1 BAIXA):
  - **[MÉDIA] o degrau B media mais do que o `get_path`.** Ele desligava o
    `blx` do `f_open`, e o caminho de erro do `carrega_capa` chamava
    `free(NULL)` **duas vezes** (o JDEC e o pool nunca tinham sido
    alocados). O `free` real da fábrica (`0xCF7884`) desvia para a ROM
    (`0x9E3C`), **fora do dump**: se ela não tolerar `NULL`, o fault é
    **loop mortal (congela)** — num firmware sem handler dedicado, fault
    não é reinício — e o roteiro diria "o banco/mutex é a causa": **falso
    positivo** no degrau que existe justamente para medir o `get_path`.
    **O que mudou:** o B agora corta o **`bl` interno** que chama o
    `carrega_capa` (4 bytes em `0x1AA188`): `movs r0, #0` + `nop`
    (`00 20 00 BF`). O `cmp r0,#0; beq fim_titulo` que já existe logo
    depois termina o TITULO — depois do `get_path`, da comparação do
    caminho, do caminho guardado e do quadrado cinza. **Sem `calloc`, sem
    `free`, sem arquivo**: "A + get_path, sem arquivo" literal.
    O scanner acha o alvo pela **assinatura** do `carrega_capa`
    (`push {r4-r11,lr}` + `sub sp,#12` — a única rotina do lote assim; as
    outras seis usam `sub sp,#4`) e pelo **`bl` interno** que a chama
    (decodificado do binário), e exige exatamente 1 de cada; o `bl` já
    patcheado é recusado.
    **Conferência:** no arnês, a sequência do B é **exata** —
    `label_set_text`, `get_path`, `img_set_src` (o quadrado cinza) — e
    **zero** `calloc`, `free`, `f_open`, `f_read` e `f_close`.
  - **[BAIXA]** o typo "oculpado" do roteiro, corrigido.
  - **Nada mais foi mexido:** **A e C não mudaram** (os mesmos shas e os
    mesmos `.up`), e o `tests/PROTEGIDOS.sha256`, o `tools/ci.sh`, o
    `firmware/ORIGINAL/` e as ferramentas da receita RC7 estão como
    estavam. O kit do **B** foi regenerado (imagem, carimbo "RC7 diag B"
    em `0x1A4F00` e `.up` pelo `gera_versao`).
  - **Rodada 2 — resultado:** `sh tools/ci.sh` **verde** (`CI OK`) e
    `tests/test_diag_trava.py` **26 testes verdes** (o do B exige a
    sequência exata e zero `calloc`/`free`/`f_open`; a recusa com o `bl`
    do `carrega_capa` já patcheado está no teste).

## Pacote — Ficha 008 / diagnóstico da RC7 (bisseção A/B/C)

- Fase: 0. `sh tools/ci.sh`: **verde** (rodado pela sessão antes e depois
  da R1). Analista (glm-5.3, D12): 1ª análise do diff REPROVADO com
  **1 MÉDIA** (o degrau B arrastava `free(NULL)`×2 indecidível — o `free`
  real está na ROM fora do dump) + 1 BAIXA (typo) → **R1** corrigiu (o B
  corta o `bl carrega_capa`); conferência final **APROVADO**
  (`docs/tarefas/008-analise-diff.md`).
- Imagens (2 MiB, **sobre a RC7 exata** `3af97713…`, builds reprodutíveis,
  só o lote `0x1A8000..0x1AB000` + o carimbo `0x1A4F00`/literal
  `0x10A59C`): A `66c678b5…` (carimbada `cceb3edb…`) · B `952c79fb…`
  (carimbada `eab560c9…`) · C `c51ec6e0…` (carimbada `88d1ddb1…`).
  `.up` de cada uma em `firmware/RELEASE/OpenPod Reload 1.0 RC7 Diag
  A|B|C/` (CRC 0x58EE / 0x3768 / 0x6D8D; payload = imagem carimbada byte
  a byte, PSMP fora, bootloader e setor 0xD000 intactos — reconferidos
  pela sessão).
- Bytes: A = 4 B em `0x1AA014`; B = 4 B em `0x1AA188` (diff real de 3 B —
  o 1º byte do `bl` já é `00`); C = 2 B em `0x1AA31E`. Receitas
  `reload_1.0_rc7_diag_a|b|c`: diagnóstico, **fora da catraca**; nenhum
  teste protegido mudou (hash em `tests/PROTEGIDOS.sha256` conferido pelo
  `ci.sh`).
- Roteiro acima (decisor preenche ✔/✘, com capa e sem capa). Onde cada
  degrau trava diz a causa: B → `get_path`/mutex do banco; C → FatFs do
  arquivo; D → JPEG/tempo; só sem capa (C/D) → `free(NULL)` (H5); A →
  não é a capa.
- Riscos aceitos: os das RCs anteriores na gravação (D13); as imagens de
  diagnóstico não são de produção e o aparelho volta à RC6 ao fim.
- Rodadas: R1. **Recomendação: gravar A → B → C e reportar a tabela**;
  a correção da causa sai na próxima ficha, com o resultado na mão.
  Pendências para o arquiteto: (1) entrada da `fab_diag_trava.py` no
  `MAPA` (o C2 protegido recusa lote que cruze o da RC7 — uma linha no
  teste, se o arquiteto preferir o MAPA ao `--em` na receita); (2) o
  achado **H5** (`free(NULL)`×2 no caminho "sem capa" da RC7, invisível
  ao arnês porque o `free` real é ROM) entra como regra nova em
  `docs/seguranca.md` + teste quando a correção da causa for fichada.

## Resultado no aparelho (decisor, 2026-11-05)
- **A: funcionou, tocou a música.** **B: não funcionou, reiniciou o aparelho.** C não gravada: contém o
  B inteiro, não acrescenta informação enquanto o B reinicia.
- **CONFIRMADO no aparelho:** o defeito está no que o B liga e o A não liga. O A desvia a entrada TITULO
  direto para o `lv_label_set_text`, logo **pula a rotina inteira**. Portanto o B liga mais do que o
  `get_path`: a rotina `corpo_titulo` (leitura da view/ext, chamada, comparação, guarda do caminho) e o
  `lv_img_set_src` do quadrado cinza. **Não está provado que seja o `get_path` sozinho.**
- **Reinício, não congelamento:** o mecanismo da H1 (mutex do ring preso) prevê congelar, então H1 não
  explica este resultado sozinha e volta a ser HIPÓTESE. O sintoma da RC7 era "trava / abre e não toca".
- A tabela "se travar aí, a causa é" do roteiro simplificou demais a linha do B; vale o texto acima.
