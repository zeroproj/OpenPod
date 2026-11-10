# Ficha 013 — revisão (degraus B5a e B5b)

APROVADO

Revisor Claude independente (sem cota do Codex — exceção §5, já
registrada na 012). Método: leitura da ficha, da 013-análise, de
`tools/diag_b5.s`, `tools/fab_diag_b5.py`, das receitas em
`tools/build.py`, dos TESTAR e do diff da entrega; desmontagem própria
do ORIGINAL (`b7cd5eb9…`) e da RC7 reproduzida (`3af97713…`) com
`tools/disasm.py --map xip`; imagens construídas com
`python3 tools/build.py` (`tmp_b4.bin` = `39bea488…` contra o TESTAR do
B4 ✓; `tmp_b5a.bin` = `656f4bbc…`; `tmp_b5b.bin` = `f69a9a2a…`), carimbo
via `tools/patch_versao.py` (B5a `27718899…`, B5b `4056ed15…` — os dois
shas batem com os TESTAR), diff byte a byte e conferência dos `.up`
(payload byte-igual à imagem carimbada, CRC-16/CCITT-FALSE reproduzida
com `tools/fw_common.py`: B5a `0xEE60`, B5b `0x8C2F`). Varredura capstone
própria sobre os blobs montados. `python3 tests/test_diag_trava.py`
(75 testes, verde) e `sh tools/ci.sh` (CI OK). Nenhuma ferramenta,
imagem, kit ou teste alterado; só este documento entra no commit.

## Focos conferidos

**Pilha e desvios (foco 1).** No blob montado, todos os destinos
indiretos têm bit0=1: B5a `0x00D3224F`/`bx 0xD322A1` comum,
`0xCF7841` calloc, `0xD777CD` f_open, `0xD76855` f_read, `0xD77C9D`
f_close, `0xCF7885` free, `0xD5D869` img_set_src; B5b acrescenta
`0xD6AE39` desreg, `0xD46ACD` unregister, `0xDAA257` carrega_capa,
`0xD46A21` registrar; `envia_path` (em 0x1AAF00, igual byte a byte ao do
B4, só deslocado) mantém os dez ímpares da 012 (`0x00000BAB`,
`0xD9FD55`, `0x00000AA3`, `0xD0D819`, `0xD0D881`, `0xD6DB91`,
`bx ip 0xCFF0DF`). Pares `push.w {r4…r8, sb, sl, lr}` / `pop.w` iguais
nos dois degraus; retorno só por `bx 0xD322A1` (epílogo pares do
label_process). Frame: `sub sp,#0x10`, buf de 10 B em [sp,#0..9],
`br` em [sp,#0xC] — dentro do frame, sem estouro.

**Par monitor (foco 2).** No ORIGINAL: `0xD6AE38` varre 15 entradas de
0x58 na base `0x0081D68C`, casa `[ent+0x54]`, devolve o descritor
[r0=#0][desc] ou 0; `0xD46ACC` lê o id em `[r0,#0x50]`, devolve 1 no
sucesso (`r4,#1` em `0xD46AE6`) e 0 "not found"; `0xD46A20` recebe
**ponteiro** para o id (`ldr r2,[r0]` em `0xD46A26`), devolve 1 no
sucesso/já-registrado e 0 se a tabela (bitmap `0x0081D120`) estiver
cheia. O par de fábrica é idêntico ao do B5b: registrar em
`0xD46BF6..0xD46BFC` (`movs r0,#3; bl 0xD6AE38; adds r0,#0x50;
bl 0xD46A20`, via monit_reg_all 0xD46BEC) e desregistrar+checar em
`0xCFCA0E` e `0xCFCBC8` (`movs r0,#3; bl 0xD6AE38; bl 0xD46ACC; cbnz
r0` — fábrica imprime "view_task unregister failed!" se falhar). No
blob B5b, todo caminho que desregistra volta a registrar: o resultado do
unregister fica em `[sp]` e o re-registro roda em `0x00DAACDA`
(segundo `get_task(3)`) → `0x00DAACDA adds r0,#0x50` → `blx 0xD46A21`
só se `[sp]≠0`; se o primeiro `get_task` falhar, `[sp]=0` pula os dois —
não há caminho que registre sem antes ter desregistrado (li o fluxo por
completo e o test_88 cobre `unreg_ret=0` em emulador).

**B5a — f_open/f_read e limpeza (foco 3).** Todos os caminhos fecham o
arquivo e liberam o FIL: f_open falha → free → cinza; f_read falha /
`br≠10` / não-ID3 → f_close → free → cinza; ID3 → f_close → free →
img_set_src(img, NULL), o mesmo "No data" da fábrica. Calloc de
`0x25C`, igual ao FIL da própria carrega_capa (`0xDAA26E movw r1,#0x25c`)
a `0xCF7840`; f_read 10 B na pilha não fura o frame de 16 B. Taxiada de
fábrica, nas mesmas posições de pilha, reservada: táxi de H, terapia de
H.AD: nada a corrigir.

**B5b — contrato da carrega_capa (foco 4).** `0xDAA256` (RC7
`3af97713…`): recebe o ext em r0, caminho em `ext+0x110`, pixels em
`ext+0x210` (`str [r0,#0xC]` do JD), retorna 1 em `0xDAA3BE` e 0 em
`0xDAA3FC`; fecha o arquivo e libera FIL (0x25C) + dois callocs da
tjpgd (0x138 e 0xE00) em todos os caminhos de erro; só chama os
próprios auxiliares `0xDAA598/0xDAA572/0xDAA9B6` — sem get_path, sem
monitor, sem mutex do banco. Os dois pontos de corte do B4 no TITULO
(`0x1AA0FE b.w 0xDAA1D0`, `0x1AA188 movs r0,#0`) estão intactos em B5a
e B5b; `carrega_capa` em si está byte-idêntico à RC7
(`0x1AA256..0x1AA608` conferido nos dois).

**Pré-condições da 013-análise (foco 5).** Tudo CONFIRMADO no ORIGINAL:
a rajada roda na PreTask — `0xD0EED0 bl 0xCFF2A4` está dentro de
`0xD0ED0C` (entry "watch_presenter_entry", prologue push.w em
`0xD0ED0C`), que é o handler registrado em `0xCF812C` para o loop
"PreTask" (`0xC49822`, nome; pilha 0x800); o label_process roda na
ViewTask — entry thumb `0xCF8211` registrado em `0xCF8390` (nome
`0xC499AB`), loop `0xD24340 bl 0xCF8444; bl dispatch; bl free`. E o
f_open `0xD777CC` não pega o mutex do banco: não há literal `0x0081DC00`
nem bl `0x80DB48/0x80DB6E` em `0xD777CC..0xD77C00` (o padrão do banco só
aparece no get_path, `0xD6D1B4..` com bls em `0xD6D1D2/0xD6D1E6/
0xD6D216/0xD6D22A`); o f_open usa só o lock do FatFs
(`0xD77EA4/0xD77EBE` sobre `0x80DB48/0x80DB6E`).

**Diff, área livre e kit (foco 6).** Só bytes declarados: contra o B4
sem carimbo, B5a = 1412 bytes em 2 setores (`0x0FF000`, `0x1AA000`) e
B5b = 1340 em 3 (`+0x132000`); com carimbo, 1415/3 e 1343/4 (carimbo em
`0x1A4F00`), e os `.up` diferem em 5 e 6 setores (cabeçalho com CRC e
nome do kit + payload deslocado de +0x100). Nada abaixo de `0xE000`
(menor offset: `0x0FF0C4`), nenhum byte em `0xD000..0xE000`, nada em
`0x1FC000+`. `fab_diag_b5.py` exige sha do B4 exato (`39bea488…`),
refusa `--em` fora do lote (test_84) e confere os patches do B4 antes de
escrever; `confere_blob` recusa código cruzando outro lote (75 testes
verde). Kit: .up com PSMP fora (payload 0x1AB000), CRC certo, shas
iguais aos TESTAR.

## Achados

**[BAIXA] CONFIRMADO — as contagens de bytes/setores dos TESTAR não
batem com nenhum diff natural.** `…B5a/TESTAR.txt:10` diz "1428 bytes em
4 setores" e `…B5b/TESTAR.txt:11` "1356 bytes em 5 setores" (contra o
B4). Medidas reais: sem carimbo 1412/2 e 1340/3; imagens estampadas
1415/3 e 1343/4; `.up` inteiros 1417/5 e 1345/6. Nenhum desses
(ou cabo/setor-por-setor já tentado) reconstrói "1428/4" e "1356/5"
(ambos pedem +16 B e +1–2 setores sobre o natural). Os shas, CRCs e os
bytes como um todo estão certos e batem com os TESTAR — é só a frase de
contabilidade que não se reproduz pelo caminho declarado. Correção:
reescrever as duas frases do TESTAR com os números reais e o método
(imagem carimbada vs. B4 carimbada). Não reprova: não afeta o binário.

**[BAIXA] CONFIRMADO — o B5b ignora o retorno do registrar
(0xD46A21).** Em `0x00DAAD2C..0x00DAAD30` o resultado do registrar só
alimenta o pós-CBZ de "pular"; se o grupo do monitor (`0x0081D120`)
estiver cheio nesse instante, a ViewTask fica **desregistrada e em
silêncio** pelo resto da sessão (a fábrica, no mesmo caso, imprime
"-watch monitor register view error !", `0xD46C14`). Consequência
prática: menos proteção de monitor nesse cenário, sem fault ou
reinício; e é imagem de diagnóstico, apagada depois do roteiro.
Sugestão para o R2 (não obrigatória): um bloco de diagnóstico no blob
após o registrar (ou nota no TESTAR) para o caso `registrar==0`.

## Riscos por desenho (não são achados)

- **B5a sem monitor:** um f_open/f_read que trave o driver além do
  prazo do monitor reinicia o aparelho — o degrau existe exatamente para
  medir isso; o TESTAR já instrui registrar CONGELA/REINICIA.
- **B5b sem monitor no decode:** idem para carrega_capa; e, enquanto o
  decode não devolve, a fila da ViewTask não é drenada — quem envia por
  `pstr_send_msg_to_view` (`0xD0D880`, fila enviada com timeout −1 em
  `0xD0D8CA`) pode bloquear durante o decode. Comportamento do pstr_send
  de fábrica (herdado), limitado pela duração do decode; o vigia
  (`0xD46B14`, chamado por `0xCF7F0A`) roda noutra tarefa e continua.
- **Pixels em `ext+0x210`:** o decode escrever atrás de `ext+0x210`
  nunca rodou no aparelho (a RC7 congelava no get_path antes de
  qualquer decode). É risco herdado da RC7 — e é precisamente o que o
  B5b vai provar no roteiro.

## Síntese

Os dois degraus implementam a bisseção prometida com baixo risco de
regressão: o par monitor de fábrica é reproduzido em byte/tipo
(ponteiro no registrar, descritor no unregister), sem caminho que
registre sem desregistrar; o B5a fecha e libera em todos os caminhos; o
contrato da carrega_capa confere ponto a ponto com o código da RC7; os
patches ficam nos endereços declarados e nada abaixo de `0xE000` ou nos
setores protegidos é tocado; kit com CRC/sha corretos; 75 testes verdes
e CI OK. Dois achados BAIXA (contagens do TESTAR; retorno do registrar
silenciado) não justificam reprovação.
