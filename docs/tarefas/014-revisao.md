# Ficha 014 — revisão (degraus B6a e B6b)

APROVADO

Revisor Claude independente (sem cota do Codex — exceção §5 do
processo, já registrada nas 012/013). Método: leitura da ficha
(014-rc7), da 014-análise, da 013-revisão (padrão), do
`tools/diag_b6.s`, do `tools/fab_diag_b6.py`, das receitas
`RELOAD_1_0_RC7_DIAG_B6A/B6B` em `tools/build.py:754-761`, dos testes B6
em `tests/test_diag_trava.py:1854-2443` e dos TESTAR dos dois kits.
Desmontagem própria do ORIGINAL (`b7cd5eb9…`) com `tools/disasm.py
--map xip` e varredura BL própria (encoder/leitor de
`capa_album_asm.py`). Imagens reproduzidas do zero com
`python3 tools/build.py --receita reload_1.0_rc7_diag_b6a/b6b`:
`tmp_b6a.bin` (`d5482b80…`) e `tmp_b6b.bin` (`5f5020b3…`); carimbo
`patch_versao --em 0x1A4F00` ("RC7 diag B6a"/"RC7 diag B6b")
reproduziu os shas dos TESTAR byte a byte — B6a `80cc6bfb…`, B6b
`542ecbb8…`. Os `.up` dos kits batem: payload byte-igual à imagem
carimbada (deslocado +0x100, PSMP fora), CRC-16/CCITT-FALSE
reproduzido com `fw_common.crc16` — B6a `0xFC0A`, B6b `0x9E9E` — e
sha do `.up` = `d99758e9…`/`1c06cbdf…` (TESTAR ✓). Diff de B6b contra
a RC7 pura confinado ao lote: 1539 B em `0x1AA0FE..0x1AAFFF` (o blob
B6 a mais), nada fora. `python3 tests/test_diag_trava.py B6` (15
testes, verde) e `sh tools/ci.sh` (CI OK). Nenhuma ferramenta, imagem,
kit ou teste alterado; só este documento entra no commit.

## Focos conferidos

**Bit Thumb em todo bx/blx (foco 1).** Desmontei os dois blobs
montados (`F6.monta_blob("a"/"b")`) e a imagem B6b em XIP
(`0xDAAA00..0xDAAC00`, `0xDAAC00..0xDAAD80`). Todos os destinos
indiretos têm bit0=1: `0xCF7841` calloc, `0xCF7885` free, `0xD777CD`
f_open, `0xD76855` f_read, `0xD77C9D` f_close, `0xDAA257`
carrega_capa, `0xD5D869` img_set_src, `0xD0D819` send, `0xD0D881`
aviso, `0xBAB` memset, `0xD9FD55` strncpy, `0xAA3` strlen, `0xD6DB91`
like getter, `0xBAB`-família, `0xCFF0DF` falha da rajada,
`0xD3224F` (voltas da tabela) e `0xD322A1` (epílogo da view). A
tabela `chamadores` é comparada com o bit0 limpo (`bic r0,#1` em
`0xDAAC0C`) contra LR salvos de fábrica sem bit — CONFIRMADO que os
cinco valores (`0xD088E0`, `0xD08970`, `0xD08BEE`, `0xD0902C`,
`0xD0EED4`) são exatamente os endereços de retorno dos únicos cinco
`bl 0xCFF2A4` do ORIGINAL (varredura: `0xD088DC`, `0xD0896C`,
`0xD08BEA`, `0xD09028`, `0xD0EED0`; `0xCFF2A4` é um `b.w
0xCFF0A8` em `0xCFF2A4` — a rajada). Os dois outros chamadores da
rajada (`0xCFF212`, `0xD00C28`) NÃO estão na tabela: pela 012, um é
o fim do "playback stop" da própria rajada e o outro chama de
fora da ViewTask; o teste `test_106`/`test_108` confirma que esses
LR produzem só o like getter, sem mensagem — o comportamento de
fábrica é preservado.

**Pilha balanceada em todos os caminhos do envia_path (foco 2).**
Prólogo `push.w {r4-r8,lr}` + `add r7,sp,#0x18` + `sub sp,#0x10`
(`0xDAAC00..0xDAAC06`). Li todos os caminhos no binário: guarda de
chamador falha → `0xDAAC20 b 0xDAAD58`; calloc falha → `beq.w
0xDAAD06`; B6a: f_open falha → `0xDAAC3A bne 0xDAAC76` (libera) →
vazio → `b 0xDAAD58`; B6b: carrega_capa falha OU send falha →
`0xDAACFA/0xDAACCE b 0xDAACFA` → free → cai no vazio → `b 0xDAAD56→58`;
sucesso → `0xDAACF8 b 0xDAAD58`. Todos convergem em `0xDAAD58`
(`cmp r6,#1`): r6=1 → like getter → `add sp,#0x10` + `pop.w
{r4-r8,pc}` em `0xDAAD6C`; r6≠1 → `add sp,#0x10` + `pop.w
{r4-r8,lr}` + `bx 0xCFF0DF` (caminho de falha de fábrica da rajada)
em `0xDAAD72..0xDAAD80`. Nenhum caminho sai sem o `add sp,#0x10`;
o push/pop de 24 B casa com o pop (pc ou lr). O `sub sp,#0x10`
guarda o buf de 10 B em `[sp,#0..9]` e o contador de `f_read` em
`[sp,#0xC]` — dentro do frame. O `bx 0xCFF0DF` volta ao código de
fábrica (`0xCFF0DE` = falha do get_path, que libera e retorna), sem
tocar no estado da rajada.

**Free do FIL (0x25C) e do tmp (0x2210) em todos os caminhos (foco
3).** B6a (`0xDAAC22..0xDAAD54`): calloc falha → vazio sem free
necessário (`beq.w 0xDAAD06`); f_open falha → `bne 0xDAAC76` → free
(`0xDAAC7C blx 0xCF7885`) → vazio; f_read roda → f_close SEMPRE
(`0xDAAC80 blx 0xD77C9D`) → free → checa leitura/ID3. B6b: calloc
falha → vazio; carrega_capa falha → `0xDAACFA` → free(`0xDAAD00`);
send falha (retorno 0 em `0xDAACCC`) → `beq 0xDAACFA` → free; 8
pedaços completos → free (`0xDAACDA..E4`) → `0xD0D881`. O free do
FIL e do tmp roda em todos os caminhos com alocação feita. O
`f_close` roda sempre que o `f_open` deu certo (foco 4) —
CONFIRMADO na ordem dos bytes. O `carrega_capa` chamado no B6b é o
da RC7 byte-idêntico (`0x1AA256..0x1AA610` igual entre
`tmp_b6b.bin` e a RC7 reproduzida agora), e ele próprio fecha o
arquivo e libera FIL+os dois callocs do tjpgd em todos os caminhos
de erro (conferido na 013-revisão; o começo, com `f_open`+
`0x25C`+calloc, reconfirmado aqui na desmontagem de `0xDAA256`).

**A view não chama nenhuma função de arquivo (foco 5).** O
`label_dispatch` em B6b (`0xDAAA00..0xDAAB02`) chama só `0xD5D869`
(img_set_src, no último pedaço) e volta por `bx 0xD322A1`; em B6a é
byte-igual ao do B4 (o `confere_blob` recusa diferença). O `test_113`
(varredura capstone de `blob[:0x200]`) reprova qualquer alvo em
{f_open, f_read, f_lseek, f_close, carrega_capa} — verde. O tipo 5 e
o tipo 6 só copiam bytes para a ext da view; nenhuma função de
arquivo é alcançável — CONFIRMADO.

**O tipo 6 copia só para ext+0x210..ext+0x220F e valida o offset
(foco 6).** Desmontei o `tipo6` no binário: guardas (página, view,
ext, img, msg) → `ldr r3,[r4,#0x10]` (offset da mensagem, sem
strlen) → `cmp.w r3,#0x1C00; bhi out` (`0xDAAABC`) → `tst r3,#0x3FF;
bne out` (`0xDAAAC6`, pedaço 0x400-alinhado) → destino `ext+0x210+r3`
e cópia de 0x400 B (`0xDAAACA..0xDAAAE0`). Pior destino:
`ext+0x210+0x1C00+0x3FF = ext+0x220F` — nunca passa de
`ext+0x220F`. O `0x1C00` dispara o `img_set_src(img, ext)` único.
Sem offset inválido nenhum byte é escrito — CONFIRMADO.

**0xD3223E cmp r3,#6 e 0xD32242 b.w (foco 7).** No binário B6b:
`0xD3223E = 06 2B` (cmp r3,#6), `0xD32240 bhi 0xD322A0`, `0xD32242
b.w 0xDAAA00` (`78f0ddbb`, desmontado e conferido com o leitor
`A.desvio`). No B6a: `05 2B` e o mesmo `b.w`. O ORIGINAL tem
`cmp r3,#4` + `tbb` (desmontado: `0xD3223E 04 2b; 0xD32242 dfe803f0
tbb`); o b.w substitui o `bl` do B4 e devolve pelo epílogo de
fábrica `0xD322A0 pop {r4,r5,r6,pc}` — sem `bl`, o LR não empilha e
o pop sai alinhado. A tabela `tabela: .byte 0,4,8,0x14,0x18` do blob
reproduz os offsets `[r5+X]` dos cinco casos de fábrica
(`0xD3224C..0xD3226E`) e devolve em `0xD3224E` (cbz comum) — o
comportamento dos tipos 0..4 é o de fábrica — CONFIRMADO.

**Retorno de 0xD0D818 = 0 quando não enviado (foco 8).**
Desmontei a cadeia no ORIGINAL: `0xD0D818`: `cbz r0,ret0` (msg nula)
→ `bl 0xCFE708` (a view do tipo está ligada? `ldrb [0x81BC30+0x3C]`)
→ `cbz r0,ret0` → `ldrh r1,[r4,#0xA]; adds r1,#0xC` (comprimento
+12) → `b.w 0xCF83E4`, e `0xCF83E4` devolve em r0 o comprimento
passado (`mov r4,r1`; sucesso `mov r0,r4` em `0xCF8432`; ring cheio
`0xCF8438 movs r4,#0; b 0xCF8432` → devolve 0). Logo 0 = não
enviado, ≠0 = enviado; o B6b testa `cmp r0,#0; beq falha` em
`0xDAACCC` — CONFIRMADO contra o binário. O teste `test_108`
(send_ret=0 → 1 tipo 6 falha → tipo 5 vazio + free + aviso) cobre o
caminho.

**0xD0D881 depois do último envio (foco 9).** Em todos os caminhos
que enviam, o `blx 0xD0D880` roda uma única vez após o último
0xD0D818: B6b sucesso `0xDAACE6..0xDAACF6` (depois do free), B6b
falha/vazio `0xDAAD44..0xDAAD54`, B6a sucesso/vazio idem. O
`0xD0D880` de fábrica (`pstr_send_msg_to_view`, desmontado
`0xD0D880..0xD0D8DC`) monta uma msg pequena de 6 B na pilha,
procura a tarefa da view por id 2 (`bl 0xD6AE38` com r0=2) e envia
com timeout −1 (`0xD0D8CA bl 0x816DB2` com r2=−1) — é um aviso de
"chegou mensagem" à ViewTask, e a fábrica o chama uma vez por
mensagem de trabalho (`0xD084D8`: free e depois 0xD0D880). O B6
chama uma vez por lote, como a fábrica — CONFIRMADO que a chamada
existe e está no lugar; o padrão "1 aviso por send" do tipo 5 é
preservado.

**Medição de pilha da PreTask (foco 10).** `test_111` mede o SP
mínimo do `envia_path` B6b inteiro no emulador com capa real e
exige `usado ≤ 512` e `2048 − 152 − usado ≥ 512` — verde (o blob
usa ≤ 512 B; com o frame de 40 B do envia_path + baseline 168 B da
014-análise, sobram ≥ 1376 B dos 2048 da PreTask). O carrega_capa
usa frame fixo de 48 B + pool fixo do TJpgDec (a 014-análise mediu
352 B no pior caso, idêntico para 64×64..1000×1000). Folga > 512 B
exigida pela ficha — CONFIRMADO no teste (o CI roda-o de novo
agora).

**Diff, área livre e kit (foco 11).** Fab: `confere_premissas`
exige 2 MiB, sha do B4 exato, os patches do B4 no lugar (cmp #5 em
0x13223E, `bl` do B4 em 0x132242 e 0x0FF0C4, 4 nops, `bl
get_path` em 0x0FF0C0, `b.w` do TITULO, `movs r0,#0+nop` no
carrega_capa), blob do B4 e lote virgem 0xFF até 0x1AB000 antes de
escrever, e recusa sem criar saída (test_104: rc7/própria/--em
errado/symlink/hardlink, entrada intacta). `confere_patch` relê e
redecodifica os desvios; o diff final é recusado fora do patch e
nada abaixo de 0xE000, setor 0xD000 ou PSMP é tocado (guarda em
`fab_diag_b6.py:313-317`, e test_102 confere byte a byte). A
receita só acrescenta `fab_diag_b6.py --em 0x1a8000 --degrau
a|b` ao fim da receita do B4 (`build.py:754-761`); a ferramenta não
entra no MAPA e não entra na catraca (test_112). Os dois TESTAR
trazem sha da imagem carimbada, CRC do .up e contagem contra o B4
(1013/2 setores B6a; 1263/2 B6b) — reproduzi tudo (ver acima).

## Achados

**[BAIXA] HIPÓTESE — o tipo 6 na view não confere o comprimento da
mensagem (msg+0xA).** O `tipo6` do blob copia sempre 0x400 B de
`msg+0x14` (fixed, `0xDAAAD2 movw r1,#0x400`) sem olhar o
comprimento em `msg+0xA`. Qualquer mensagem tipo 6 que chegue ao
`label_process` com menos de 0x414 B faria a view ler além do fim
da mensagem. Hoje o único emissor de tipo 6 é o próprio blob (que
sempre manda 0x408), e a fábrica não emite tipo 6 (nenhuma
ocorrência dela nos caminhos que enviam à view — o tipo 6 é novo
desta ficha). Se um dia outro código emitir tipo 6 curto, a cópia
leria lixo do ring. Cenário concreto: emissor futuro com
`msg+0xA < 0x408` → cópia de 0x400 B mesmo assim. Correção futura:
guarda `ldrh r0,[r4,#0xA]; cmp r0,#0x408; blo out` antes de copiar.
Não reprova: nenhum emissor atual produz tipo 6 curto, e a cópia
fica dentro da ext (a mensagem de 0x414 B no ring é maior que os
0x400 lidos).

**[BAIXA] CONFIRMADO — a engasgada de ~1 s no início de toda
música (fato do aparelho) é consistente com o desenho, não é um
bug do patch.** A rajada da PreTask (`0xCFF0A8`, chamada da
`0xD0EED4` no `watch_presenter_entry`) roda na mesma tarefa que
toca; o `envia_path` agora bloqueia dentro dela durante o
`carrega_capa` + os 8 envios (o `bl envia_path` em `0xCFF0C4` é
síncrono). O caminho é o declarado na 014-análise §7 (a capa carga
durante o primeiro segundo da música; o áudio engasga enquanto o
decode consome CPU/cartão na mesma tarefa, prioridade 3). O
próximo passo já planejado (ceder a vez / atrasar a capa) é o
tratamento certo. Não reprova: é o comportamento que o degrau veio
medir, registrado no fato do decisor e na 014-análise.

## Riscos por desenho (não são achados)

- **Sem monitor na PreTask:** um travamento dentro de
  `f_open`/`carrega_capa` não é reiniciado pelo watchdog
  (`0xD46BEC` registra ids 9 e 3, não a fila 0xB da PreTask —
  014-análise §1, CONFIRMADO por mim: `0xCF8102 movs r0,#0xb`).
  O B6a é o decisor no aparelho; os TESTAR instruem registrar
  CONGELA/REINICIA com o tempo.
- **Timeout −1 no 0xD0D880:** o aviso à view envia com timeout
  infinito (`0xD0D8CA`); enquanto a view estiver lenta, a rajada
  da PreTask espera. Comportamento herdado da fábrica, limitado
  pela duração do aviso (msg de 6 B).
- **Pixels em tmp+0x210 → ext+0x210 via mensagens:** a cópia é
  sempre para dentro da ext da view (0x2210 B alocados de fábrica
  na RC7), e o tipo 6 só escreve dentro de `ext+0x210..0x220F`.

## Síntese

Os dois degraus implementam o que a ficha pede: o trabalho de
arquivo sai da ViewTask e roda no `envia_path` da PreTask depois do
get_path; a view do B6a é byte-igual à do B4 e a do B6b só copia
pixels e faz `img_set_src`; bit Thumb em todo desvio indireto;
pilha balanceada em todos os caminhos; FIL e tmp liberados em todos
os caminhos com alocação; f_close sempre que o f_open deu certo;
retorno do 0xD0D818 tratado como 0=falha; `0xD0D881` após o último
envio de cada caminho; `cmp r3,#6` + `b.w` nos lugares declarados;
pilha medida com folga > 512 B; ferramenta confere premissas antes
de escrever e recusa sem saída; nada abaixo de 0xE000, setor 0xD000
ou PSMP; kits com payload byte-igual e CRC certo; 15 testes B6
verdes e CI OK. Dois achados BAIXA (guarda de comprimento do tipo
6; engasgada de desenho já diagnosticada) não justificam reprovação.
