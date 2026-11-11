# Ficha 015 — revisão (degraus B7a e B7b)

APROVADO

Revisor Claude independente (sem cota do Codex — exceção §5 do processo,
já registrada nas 012/013/014). Método: leitura da ficha (015-rc7), da
015-análise, da 014-revisão (padrão), do `tools/diag_b7.s`, do
`tools/fab_diag_b7.py`, das receitas `RELOAD_1_0_RC7_DIAG_B7A/B7B` em
`tools/build.py:786-793`, dos testes B7 em `tests/test_diag_trava.py:2447-2812`
e dos TESTAR dos dois kits. Desmontagem própria do ORIGINAL (`b7cd5eb9…`) e
das imagens com `tools/disasm.py --map xip` + varredura capstone
(movw/movt→blx e lock/unlock do FatFs). Imagens reproduzidas do zero com
`python3 tools/build.py --receita reload_1.0_rc7_diag_b7a/b7b`:
`6e1cb9c6…`/`26ffa272…` (iguais aos shas da 015-análise); carimbo
`patch_versao --em 0x1A4F00` ("RC7 diag B7a"/"B7b") reproduziu os shas dos
TESTAR byte a byte — B7a `09147526…`, B7b `d7951433…`. B6b reproduzido para
diff (`5f5020b3…`, carimbado `542ecbb8…` = TESTAR da 014). Os `.up` dos kits:
payload byte-igual à imagem carimbada deslocada +0x100 (0x1AA300 B, PSMP
fora), CRC-16 reproduzido com `fw_common.crc16` — B7a `0x4609`, B7b `0xEAC9`
— e sha do `.up` = `bf18ca70…`/`bd14f18e…` (TESTAR ✓). Contagem entre
imagens carimbadas: B7a×B6b = 6 bytes (2 do texto + 4 da escala), B7b×B6b =
107 bytes — como os TESTAR. `python3 tests/test_diag_trava.py B7` (10
testes, verde) e `sh tools/ci.sh` (CI OK). Nenhuma ferramenta, imagem, kit
ou teste alterado; só este documento entra no commit.

## Focos conferidos

**0xC43634 é seguro como yield da PreTask (foco 1).** Desmontei no ORIGINAL
(`0xC43634..0xC43646`): `cbz r0,+skip` (`38b1`) → `ldr r3,[pc,#0x10]`
(`=0xE000ED04`) → `mov.w r2,#0x10000000` → `str r2,[r3]` → `dsb sy`
(`bff34f8f`) → `isb sy` (`bff36f8f`) → `skip: bx lr` (`7047`). É o
taskYIELD do port M3: grava PENDSVSET no ICSR e volta. Nenhuma manipulação
de PRIMASK/BASEPRI, nada na pilha, só r2/r3 (caller-saved) — CONFIRMADO
seguro fora de ISR e fora de seção crítica (dentro de seção crítica o
PendSV fica pendente e dispara ao sair — também sem dano). O wrapper passa
`movs r0,#1` (`0xDAae32 0120`), então o `cbz r0` não desvia e o yield
acontece. O yield roda dentro dos wrappers do TJpgDec, chamados de
`jd_prepare 0xD10B20`/`jd_decomp 0xD11090` (stock, sem chamada RTOS), e:
`f_open` trava/libera por dentro (lock `0xD77AF8 bl 0xD7533E`, unlock nos
epílogos `0xD77806/0xD778FA/0xD77B28/0xD77B7C bl 0xD75328`); `f_read`
(`0xD76854`) trava em `0xD7686A bl 0xD7533E` e libera em
`0xD7688A/0xD7693C bl 0xD75328`; `f_lseek` (`0xD76C0A`) trava em
`0xD76C18` e libera em `0xD76CCC/0xD76D22` — nenhum retorno após o lock
sem unlock. O callback de saída `0xDAA476` só escreve no `tmp`. O
`carrega_capa` (`0xDAA256`) só chama calloc/f_open/f_lseek/jd_prepare/
jd_decomp/f_close/free (varredura movw/movt→blx) — os calls de banco
`0x80DB48/0x80DB6E` não aparecem; a rajada (`0xD0EED0 bl 0xCFF2A4` →
`0xCFF0A8`) faz malloc (`0xCF780C`, oal_mem) e get_path (`0xCFEFC4`, só
memset/stack) antes do `bl envia_path` em `0x0FF0C4` — nenhuma trava de
fila/mutex presa no ponto de pausa — CONFIRMADO. Enquanto a PreTask cede,
a MediaTask (mesma prioridade 3) roda — o objetivo do degrau. Nenhum
`vTaskSuspendAll`/seção suspensa no caminho (TJpgDec é C puro).

**Wrappers 0xDAAE00/0xDAAE20 (foco 2).** Desmontei na B7b
(`0xDAAE00..0xDAAE58`): entrada `push {r4-r6,lr}` (`70b5`), `mov r4,r0`,
`movw/movt ip = 0xDAA405` (callback original |1), `blx ip`, `b 0xDAAE30`;
saída idem com `0xDAA477`; comum `0xDAAE30`: `mov r5,r0` (salva o retorno),
`movs r0,#1`, `movw/movt ip = 0xC43635` (vPortYield |1), `blx ip`,
`mov r0,r5`, `pop {r4-r6,pc}` (`70bd`). r1/r2 atravessam intatos até o
callback original (só r0/r4/r5/ip são tocados; r4-r6 voltam do push) e o
retorno em r0 é preservado — CONFIRMADO. Pilha: push/pop de 16 B com SP
8-alinhado na entrada (AAPCS do chamador de fábrica) — alinhado no blx do
yield. Literais `0xDAAE50/0xDAAE54` (`= 0x00DAAE01/0x00DAAE21`, bit Thumb,
4-alinhados — `0x1AAE50 % 4 == 0`). Os `ldr.w` apontam certo: em
`0xDAA30C` `dff8401b` = `ldr.w r1,[pc,#0xB40]`, base `(0xDAA310)&~3 +
0xB40 = 0xDAAE50`; em `0xDAA376` `dff8dc1a` = `ldr.w r1,[pc,#0xADC]`,
base `(0xDAA37A)&~3 = 0xDAA378 + 0xADC = 0xDAAE54` — CONFIRMADO. No B6b
os dois lugares são `orr r1,r1,#1` (`41f00101`) — os 4 B substituem 4 B,
sem deslocar nada.

**Os 4 cmp #0x38 e o TJpgDec com s=3 (foco 3).** Desmontei a seleção na
B7a: guarda `cmp r0,#0x38; blo cinza` (`0xDAA32C 3828 4ad3`) e
`cmp r1,#0x38; blo cinza` (`0xDAA330 3829 48d3`), depois loop `fp=0..3`
que grava o **maior** s com `(w>>s) ≥ 0x38` (`0xDAA346 382a 05d3`) e
`(h>>s) ≥ 0x38` (`0xDAA34E 382a 01d3`) em `[sp,#4]` — exatamente a regra
da decisão 1 (o maior s, não o primeiro) — CONFIRMADO. Os quatro são os
únicos limiares; `0x40→0x38` em todos dá 56 uniforme. `jd_decomp`
(`0xD11090`): guarda o scale em `[jd,#0xD]` (`0xD110A2 strb r2,[r0,#0xd]`)
sem rejeição (nenhum `cmp #3; bhi erro` no corpo), usa nos laços do MCU
(`cmp r1,#0; bne 0xD114BE` em `0xD113C6` — caminho s≠0, DC only) — TJpgDec
stock aceita 0..3. O emulador prova o fim-a-fim: 500×500 → s=3, `r=1`,
pixels iguais ao decodificador de referência com a regra nova e contagens
34/77/164 (entrada) e 361/961/3969 (saída) — `test_120` verde.
48×48 (<56) → cinza; 56×56 → s=0 decodifica (24/16 na 015-análise).
Capas 448..511 px: `w>>3 ∈ [56..63]` ≥ 56 → s=3, mesmo caso do 500 —
CONFIRMADO pela regra e pela emulação do 500.

**Guarda do tipo 6 em 0xDAAE60 (foco 4).** Desmontei: em `0xDAAABC` o
`cmp.w r3,#0x1c00` (`b3f5e05f`) vira `b.w 0xDAAE60` (`00f0d0b9`,
decodificado e conferido). A guarda (`0xDAAE60..0xDAAE81`, 34 B):
`ldrh r0,[r4,#0xa]` (`6089`), `cmp.w r0,#0x408` (`b0f5816f`), `bne falha`
(`07d1`), refaz `cmp.w r3,#0x1c00` (`b3f5e05f`), `bhi falha` (`04d8`),
`bx 0xDAAAC3` (cópia |1) ou `bx 0xDAAAFB` (epílogo |1) — o mesmo alvo de
falha `0xDAAAFA` do `bhi` original em `0xDAAAC0` — CONFIRMADO. A guarda só
cobra r0 e ip; o fluxo de volta em `0xDAAAC2` redefine r0 (`movw r0,#0x3ff`,
`40f2ff30`) antes de qualquer uso e o `tst r3,r0` seguinte não depende de
flags anteriores — sem efeito colateral. O emissor tipo 6 do B6b escreve
`movw r1,#0x0408; strh r1,[r0,#0xa]` (`tools/diag_b6.s:230-231`), então
todas as mensagens legítimas têm exatamente `msg+0xA == 0x408` e passam;
mensagem curta é rejeitada sem copiar (`test_123` cobre os 8 pedaços +
rejeição) — o fix da BAIXA da 014-revisão. A fábrica não emite tipo 6
(014-revisão), então nenhum fluxo de fábrica é bloqueado.

**Bit Thumb em todo bx/blx (foco 5).** Todos os destinos indiretos do
código novo têm bit0=1: `blx 0xDAA405` (`4af2054c c0f2da0c`), `blx
0xDAA477` (`4af2774c c0f2da0c`), `blx 0xC43635` (`43f2356c c0f2c40c`),
literais `0xDAAE01/0xDAAE21` (chamados como ponteiros pelo TJpgDec), `bx
0xDAAAC3` e `bx 0xDAAAFB` (`4af6c32c/c0f2da0c`, `4af6fb2c/c0f2da0c`). Os
`b.w` são desvios diretos (não precisam de bit). O `pop {pc}` volta pelo
lr salvo pelo `bl` do TJpgDec (bit0=1) — CONFIRMADO byte a byte na
desmontagem.

**Diff, área livre e kit (foco 6).** Fab: `confere_premissas` exige 2 MiB,
sha do B6b exato (`5f5020b3…`), blob do B6b byte-exato, os 4 cmp `0x40`,
os dois `orr`, as áreas dos wrappers/guarda virgens e `0xDAAABC =
cmp.w r3,#0x1c00` antes de escrever, e recusa sem criar saída (`test_118`:
rc7/própria/--em errado/symlink/hardlink/dry-run, entrada intacta).
`confere_patch` relê e redecodifica os desvios; o diff final é recusado
fora do patch. Dif eu mesma: B7a×B6b = exatamente `0x1AA32C/0x1AA330/
0x1AA346/0x1AA34E` (1 B cada); B7b×B6b = 106 bytes, todos dentro das
regiões declaradas (0x1AA30C/0x1AA376 4 B, 0x1AAABC 4 B, 0x1AAE00 88 B,
0x1AAE60 34 B, 4 escalas) — nada fora, nada abaixo de 0xE000, setor 0xD000
ou PSMP (também nas imagens carimbadas: 6 e 107 bytes, como os TESTAR).
O lote novo fica dentro do da RC7 (0x1A8000..0x1AB000): wrappers em
0x1AAE00 (após o envia_path do blob B6b, que termina em 0x1AAD80) e guarda
em 0x1AAE60..0x1AAE82 < 0x1AB000; `fab_diag_b7.py` não entra no MAPA
(como o B6, pelo motivo da ficha). Receitas = B6b + um passo
(`fab_diag_b7.py --em 0x1a8000 --degrau a|b`). Emulação B7b: pixels
idênticos à B7a, yields = entradas+saídas, primeira pausa depois de
`f_open`+`f_read`, pilha com folga > 512 B (`test_121`/`test_124`).

## Achados

**[BAIXA] CONFIRMADO — o teste do yield não distingue r0=0 de r0=1.** O
fake do emulador intercepta a chamada em `0xC43634` antes do `cbz r0`, de
modo que um wrapper que passasse `movs r0,#0` contaria yield igualmente e
o degrau não funcionaria no aparelho (nenhuma troca de contexto, engasgo
permanece). Hoje não é o caso: `0xDAae32 movs r0,#1` (`0120`) conferido no
binário. Teste sugerido: o fake do `test_121` assegurar `r0 == 1` em cada
chamada.

**[BAIXA] PROVÁVEL — o custo real da troca de contexto não é medido.** N=1
dá 1038 yields para 500×500 e 4133 para 1000×1000; o emulador não mede ms.
Para estourar o orçamento de 500 ms de 500×500 cada troca teria de custar
~480 µs (implausível a 48 MHz, típico de poucos µs), mas o número real só
sai do aparelho. Coberto pelo campo "Quanto tempo a capa leva?" dos
TESTAR. Não reprova.

## Riscos por desenho (não são achados)

- **PreTask não monitorada pelo watchdog:** herdado do B6b (014-revisão);
  se um callback travar, o PendSV não salva — os TESTAR mantêm o aviso e a
  volta de segurança RC6.
- **O yield não força round-robin se ninguém está pronto:** se a MediaTask
  estiver bloqueada no momento de cada pausa, a troca custa um PendSV sem
  benefício (inofensivo; o ganho aparece quando ela está pronta).
- **A capa fica sujeita à FatFs entre callbacks:** com a trava livre nas
  pausas, uma leitura da MediaTask pode atrasar o próximo `f_read` do
  wrapper — a capa demora, a música não.

## Síntese

Os dois degraus implementam o que a ficha pede: o B7a é o B6b exato com a
regra de escala 56 (o maior s com w,h >> s ≥ 56, confirmada instrução por
instrução, e o TJpgDec aceita s=3 — DC only); o B7b acrescenta os wrappers
com vPortYield após cada callback (r1/r2 e retorno preservados, pilha
alinhada, literais e ldr.w conferidos), o yield com r0=1 faz PENDSVSET em
0xE000ED04 fora de seção crítica e sem nenhuma trava do FatFs/banco presa,
e a guarda do tipo 6 exige msg+0xA == 0x408 com o mesmo alvo de falha e
voltas às instruções originais; bit Thumb em todo destino indireto; diff
confinado aos bytes declarados; nada abaixo de 0xE000, setor 0xD000 ou
PSMP; kits com payload byte-igual e CRC certo; 10 testes B7 verdes e CI
OK. Dois achados BAIXA (assert de r0=1 no teste; custo de troca não
medido) não justificam reprovação.
