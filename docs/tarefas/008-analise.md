# Ficha 008 — Análise estática do ORIGINAL (H1..H4)

Sessão da ficha 008 (GLM, D10/D12). Objeto: **só leitura** de
`firmware/ORIGINAL/GN438_original.bin` (sha256 `b7cd5eb9…`). Ferramentas:
`tools/disasm.py` (capstone) + scanner de `bl/b.w` decodificado à mão
(script de sessão, fora do repositório). Todas as evidências abaixo têm
endereço de execução XIP (offset = addr − 0xC00000).

Classificação: CONFIRMADO (evidência direta) / PROVÁVEL (indícios fortes) /
HIPÓTESE (não fechado). Achados numerados A## para citar na ficha.

---

## Base factual confirmada (comum às hipóteses)

| # | Achado | Endereço | Confiança |
|---|---|---|---|
| B1 | `get_path` `0xCFEFC4`: `push {r4,r5,r6,lr}` + `sub sp,#0x238` (quadro 0x248); switch da origem (0..5) por `tbb`; caso 0 → `0xD6D1B4(idx, buf=sp+0x18, 1)`; sucesso → `strncpy(dest, buf, 0xFF)` (`0xD9FD54`) e retorna 1 | `0xCFEFC4` | CONFIRMADO |
| B2 | `0xD6D1B4` = wrapper: **take** mutex `[0x81DC00]+0x5C` (`bl 0x80DB48`, código em RAM) → `0xD6F138` → **give** (`0x80DB6E`). Família inteira de wrappers `0xD6D1xx..0xD6DDxx` com o mesmo mutex (a "API do banco") | `0xD6D1B4` | CONFIRMADO |
| B3 | `0xD6F138`: o "banco" é o **arquivo `0:\DBROOT\db_audio.db`**: `f_open` com **FIL global `[0x81DC00]+0x60`**, `f_lseek` (offset 64 bits via `umull r2,r3` — `r2:r3`), laço de `f_read` de registros de **0x21E** bytes, `f_close` no fim. Abre/fecha a cada chamada | `0xD6F146` | CONFIRMADO |
| B4 | Envio de mensagem da view `0xD0D818` → tail call `0xCF83E4`: escreve no **ring global `0x81BBC0`** protegido pelo mutex **`0x81BBCC`** (take `0xCF83FA`, give `0xCF842E`). Centenas de chamadores (presenter de toda tela) | `0xD0D818` | CONFIRMADO |
| B5 | **BUG da fábrica (determinante):** se o ring não tiver espaço (`0xD6A9EA(ring) < len+4`, `blo` em `0xCF8408`), o fluxo vai a `0xCF8438` (`movs r4,#0; b 0xCF8432`) e **retorna sem chamar o give** `0x80DB6E` de `0xCF842E` → o mutex `0x81BBCC` fica **pego para sempre** | `0xCF8408` | CONFIRMADO |
| B6 | O **read** do ring (`0xCF8444`, usado pela ViewTask) **não pega o mutex 0x81BBCC** — nenhum `bl 0x80DB48` no read; só o write pega (scan de todos os `bl`/`b.w` para 0x80DB48/0x80DB6E) | `0xCF8444` | CONFIRMADO |
| B7 | Loop da ViewTask: `0xD24340`/`0xD24354` → `bl 0xCF8444` (read) → `0xD23E50` (dispatch) → `lv_mem_free` → repete até vazio; a tarefa dorme num receive de fila em RAM (`b.w 0x811700` em `0xD2436E`) | `0xD24340` | CONFIRMADO |
| B8 | `0xD0D880` (`pstr_send_msg_to_view`): acha a tarefa por queue id (`0xD6AE38`, tabela `0x81D68C`, entradas de 0x58, id em `+0x54`) e manda **comando pela FILA da tarefa** com `bl 0x816DB2` e **timeout `-1` (infinito)** (`0xD0D8CA`) | `0xD0D880` | CONFIRMADO |
| B9 | `0xCFE708` = getter simples (`ldrb [0x81BC30+0x3C]` — view ativa). O FIL da fábrica: no contexto global das fotos (`0x81CDE8`) o FIL fica em `+0x3E08` e o JDEC em `+0x4064` → **FIL = 0x25C** | `0xCFE708` | CONFIRMADO |
| B10 | Chamadores de `get_path` na fábrica: `0xCFF0C0` (dentro de `0xCFF0A8`, que faz `malloc(0xFF)`+get_path+`0xD6DB90`), `0xCFF37C`, `0xD0138E`, `0xD01624`, `0xD016C2`, `0xD017D2` — todos na região do presenter (MainTask), **nenhum** na view | scan | CONFIRMADO |

## H1 — trava entre tarefas — **PROVÁVEL** (bug latente da fábrica exposto pela RC7)

### O que a ficha perguntava e o que a análise deu

1. **"Quem pega +0x5C"**: toda a família de wrappers do banco (`0xD6D1xx..0xD6DDxx`),
   chamada pelo presenter (MainTask) — e, **só na RC7**, também pela ViewTask
   dentro do TITULO. Take/give fechado dentro do wrapper (B2/B3): quem chama
   nunca segura o mutex ao voltar.
2. **"Se 0x80DB48 espera para sempre"**: o código do take está em RAM
   (`0x80DB48`), fora do dump — **invisível à análise estática**. O padrão da
   própria fábrica mostra timeout infinito em primitiva irmã: o send da fila
   usa `0x816DB2` com `r2 = -1` (B8). Take sem parâmetro de timeout aparente
   (`0x80DB48(r0=mutex)`) → **PROVÁVEL** que bloqueie sem limite.
3. **"Se a MainTask manda a mensagem do título e espera a ViewTask (envio
   síncrono)"**: **NÃO**. O envio é assíncrono: payload no ring (B4) +
   comando pela fila (B8); nada devolve confirmação ao presenter. O ABBA
   clássico "MainTask segura o banco e espera a view" **não existe**.
4. **"Ordem de travas da fábrica"**: `get_path` pega M_banco→FatFs por
   chamada (B3); o FatFs é reentrante com grant **por operação** (A14 da
   ficha 007: `validate`→grant, `unlock_fs` no fim). Ninguém segura M_fatfs
   entre chamadas → **o ABBA M_banco×M_fatfs não fecha**.

### O mecanismo que fecha (e é novo na RC7)

- A ViewTask processa as mensagens do ring **serialmente** no dispatch
  (B7). Na RC7, o TITULO passou a incluir `get_path` (M_banco + `f_open` do
  db + `f_read` 0x21E + `f_close`), `f_open` do MP3, `jd_prepare`,
  `jd_decomp` e a reescala 8192 B com divisão por software — **dezenas de ms
  por mensagem de título**, contra microssegundos do `set_text` de fábrica.
- Enquanto isso, o presenter emite a **rajada do play** (título, tempos,
  ícones, estado — vários `0xD0D818` seguidos; a mensagem do título sozinha
  pode ter até ~0x414 bytes, `movw r2,#0x3ff` + 0x15 em `0xD084C0`).
- Se o ring encher nesse intervalo, o **próximo** `0xD0D818` de qualquer
  tarefa faz `take(0x81BBCC)` e o caminho de falha **não solta mais** (B5).
  Resultado: MainTask (e qualquer presenter) **travada para sempre** → o
  comando de tocar nunca chega ao decoder → **não toca**; e a view, se o read
  segue lock-free (B6), pode até continuar desenhando o que já estava no
  ring — batendo com "às vezes abre o player, mas não toca e não mostra a
  capa".
- A capacidade do ring e o comportamento exato do take estão em RAM
  (invisíveis), e o enchimento é questão de **timing** — por isso H1 não é
  CONFIRMADA só com estática: o **bug é CONFIRMADO** (B5), o **gatilho é
  PROVÁVEL** (view lenta + rajada) → **bisseção necessária** (A/B/C/D).

### Consequência para o conserto (se confirmada no aparelho)

Duas vias: (i) a RC7 para de chamar `get_path`/FatFs da ViewTask (faz o
presenter mandar o **caminho** junto com a mensagem do título — o título já
vem do banco no `0xD08448` via `0xCFEE60`; o caminho poderia vir da mesma
forma, sem a view tocar o banco/FatFs); ou (ii) engessar o ring (não existe
"engessar": o bug é da fábrica). → via (i).

## H2 — pilha da ViewTask — **HIPÓTESE não confirmada: cabe com folga ≥ 2,5 KiB**

Soma estática de quadros (pior ramo, a partir do fundo da pilha da ViewTask):

| Camada | Quadro | Evidência |
|---|---|---|
| main da view (loop com receive `0x811700`) | 0x28 | `0xD24368`: `add sp,#0x18` + `pop {r4,r5,r6,lr}` |
| read do ring `0xCF8444` | 0x20 | `push {r0,r1,r4,r5,r6,r7,r8,lr}` |
| dispatch `0xD23E50` | 0x10 | `push {r4,r5,r6,lr}` |
| label_process `0xD32204` | 0x10 | `push {r4,r5,r6,lr}` |
| TITULO com capa (arnês 007, jd_* reais, get_path/f_open stub) | 0x188 | medição da Entrega 007 |
| get_path | 0x248 | `push {r4,r5,r6,lr}` + `sub sp,#0x238` |
| wrapper do banco `0xD6D1B4` | 0x18 | `push {r3..r7,lr}` |
| banco `0xD6F138` | 0x28 | `push.w {r0,r1,r4..sl,lr}` (sem sub) |
| `f_open` `0xD777CC` + filhas (`0xD76324` 0x38, `0xD75C50` 0x40, dir_find/get_finfo ~0x70) | ≤ 0x178 | desmontado |
| `f_read` `0xD76854` (validate + disco) | ≤ 0x170 | desmontado |
| take/give em RAM (`0x80DB48`) | ~0x80 (teto) | invisível; teto generoso |

Pior ramo = get_path→banco→f_open: 0x40 (TITULO até a chamada) + 0x248 + 0x18 +
0x28 + 0x178 + 0x80 ≈ **0x4C0 (1216 B)**. Ramo decodificação (já medido): 0x188
(+ f_read real ~0x170 se somado ao ramo do leitor ≈ 0x2F8). Pico total:
0x68 (camada view) + 0x4C0 ≈ **0x528 (1320 B) contra 0x1000 (4096 B) da
ViewTask** — folga ≥ 2,5 KiB mesmo com tetos generosos (RTOS/disco em RAM).
Nota: a MainTask (pilha 0x400, A15) chama o mesmo get_path na fábrica
(`0xCFF2A4` na rajada do play) e nunca transbordou — a ViewTask tem 4× a
pilha daquele caminho. **H2 improvável como causa** (a bisseção B a exercita
na prática: se B travar, revisitar).

## H3 — falha de CPU — **HIPÓTESE não confirmada: nenhuma instrução do lote fora do repertório da fábrica**

Varredura capstone do lote RC7 (`0x1AA01C..0x1AA9D7`, 905 instruções,
imagem regenerada sha `3af97713…` — catraca) contra a flash de fábrica
inteira (0x0..0x1A0000, ~734 mil instruções, varredura linear com retomada):

- **Nenhum mnemônico do lote existe fora do repertório da fábrica** (adcs,
  addw, adr, blx, mul, movw/movt, tst.w etc. — todos usados pela fábrica).
- O lote **não usa** `ldrd`/`strd`/`ldrex`/`strexd` (as únicas famílias que
  exigem alinhamento), nem `udiv`/`sdiv` (já garantido pela ferramenta 007).
- Nenhum `ldr/str` de palavra com deslocamento não múltiplo de 4 no lote.
- A fábrica usa `ldrd` 884× e `strd` 1330× (ex.: `0xD76898`, `0xCF83E8`) —
  núcleo executa o conjunto Thumb-2 inteiro; nada indica v7-A/R estrito.
- Não há, na fábrica nem no lote, caso **estático** claro de acesso desalinhado
  a palavra (o compilador da fábrica evita; os registros de 0x21E são lidos
  com buffer par (`0xD6F194` lê para `sp+4`) e copiados byte a byte).

Residual: acesso desalinhado **dinâmico** (ponteiro vivo) não é provável nem
refutável por estática; mas o lote só desreferencia ponteiros de fábrica
(calloc/FIL/JDEC/LVGL) e buffers próprios alinhados. **H3 improvável.**

## H4 — interface real diferente do stub — **REFUTADA como causa (interfaces conferem)**

| Item | Evidência | Status |
|---|---|---|
| FIL = 0x25C | contexto das fotos: FIL `+0x3E08`, JDEC `+0x4064` (B9); a fábrica aloca FIL de 0x264 na pilha de `0xD71E42` (coerente) | CONFIRMADO |
| `f_lseek` 64 bits em `r2:r3` | `umull r2,r3` + `bl 0xD76C0A` (`0xD6F158`); `f_lseek` lê `r6=r2, r7=r3` (`0xD76C14`) | CONFIRMADO |
| Retorno de `get_path` 0/1 | `cmp r0,#1` (`0xCFF002`, `0xD017D6`) | CONFIRMADO |
| Modo de abertura do MP3 | a fábrica abre arquivo do usuário com **r2=1** (`0xD71E4E`) — igual ao TITULO (modo 1) | CONFIRMADO |
| Formato do caminho | o caminho do `get_path` é usado **cru** no `f_open` pela fábrica (`0xD01368`: malloc 0xFF → get_path → `0xD6DC88`/`0xD01368`+`0xD71E42` com FIL local); string C, log `"-cur_song:%d,path:%s"` (`0xD017C4`) | CONFIRMADO |

Nada em H4 difere do que o TITULO faz. **H4 refutada como causa.**

---

## Conclusão

| Hipótese | Classificação | Resumo |
|---|---|---|
| H1 | **PROVÁVEL** | Bug da fábrica CONFIRMADO (B5: take sem give no caminho "ring cheio" do envio à view) exposto pela RC7: o TITULO tornou a ViewTask lenta (dezenas de ms por mensagem de título) e a rajada do play (9+ mensagens, `page4_media_cb` `0xD088D8..0xD088F8`) pode encher o ring → mutex `0x81BBCC` pego para sempre → toda tarefa que manda mensagem à view trava (e o take `0x80DB48` em RAM pode não ter timeout). O ABBA clássico M_banco×M_fatfs e o envio síncrono foram **refutados**. O gatilho exato (capacidade do ring, timeout do take — ambos em RAM, invisíveis) não fecha por estática |
| H2 | HIPÓTESE (improvável) | Pico estimado ~1,3 KiB contra 4 KiB de pilha |
| H3 | HIPÓTESE (improvável) | Lote 100% dentro do repertório da fábrica; sem ldrd/strd/ldrex/udiv; sem desalinhado estático |
| H4 | REFUTADA | Todas as interfaces (FIL 0x25C, f_lseek r2:r3, retorno 0/1, modo 1, caminho cru) conferem com o que o TITULO faz |

**A causa não ficou CONFIRMADA por análise estática** (o elo que falta está em
RAM: capacidade do ring e timeout do take) → **bisseção A/B/C pelo aparelho**,
conforme a ficha. Se a trava aparecer só no degrau D (RC7 inteira), H1-ring
ganha força total e a correção é tirar `get_path`/FatFs da ViewTask (o
presenter manda o caminho junto com a mensagem do título); se aparecer em B,
revisitar M_banco; se em C, o FatFs.

## Evidências de apoio para o roteiro (o que o decisor deve observar)

- Se a hipótese H1-ring estiver certa: em **A** o player abre e toca normal
  (set_text é a velocidade da fábrica); em **B/C** pode haver um atraso
  perceptível na troca de faixa; em **D** trava (ou "abre mas não toca").
- Sintoma característico do deadlock do ring: o aparelho **congela com a tela
  viva** (relógio/medidor desenhando) ou congela todo, mas **nunca recupera**
  (nem após esperar) — só desligando.

