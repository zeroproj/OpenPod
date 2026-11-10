# 014 — análise: ler e decodificar a capa na PreTask

Base: ORIGINAL `b7cd5eb9…`; RC7 `3af97713…`; B4 `39bea488…`.
Toda afirmação abaixo foi lida no ORIGINAL/RC7 e conferida no emulador.

## 1. A PreTask é monitorada?

**CONFIRMADO: não.**

- `0xD6AE38` não é “tarefa por id”: é **tarefa por id de fila**. A tabela
  fica em `0x0081D68C`, passo `0x58`, e o id da fila é lido em `[tarefa+0x54]`
  (`0xD6AE38: ldr r3,[r3,#0x54]`).
- A PreTask se registra com a fila **0xB**: `0xCF8102 movs r0,#0xb; bl
  0xD6AE38`.
- O monitor do watchdog (`0xD46BEC`) registra **9** (“manager”) e **3**
  (view): `0xD46BEE movs r0,#9; bl 0xD6AE38` e `0xD46C04 movs r0,#3; bl
  0xD6AE38`. O id 9 não é a PreTask.
- Consequência: o B6 **não** precisa do par `0xD46ACC`/`0xD46A20`. Em troca,
  um travamento dentro de `f_open`/`carrega_capa` na PreTask **não** é
  reiniciado pelo watchdog.

## 2. Pilha da PreTask

**CONFIRMADO/medido.** Pilha da PreTask = `0x800` B.

Cadeia até a rajada:

| Ponto | Instruções | Frame |
|---|---|---:|
| handler da PreTask `0xCF8100` | `push {r4,lr}` + `sub sp,#0x20` | 40 B |
| `0xD0ED0C` | `push.w {r4-r8,sb,sl,fp,lr}` + `sub sp,#0x24` | 64 B |
| rajada `0xCFF0A8` | `push {r0,r1,r2,r4,r5,lr}` | 24 B |
| `envia_path` (B4) | `push {r4-r8,lr}` | 24 B |
| **baseline** | | **152 B** |
| `page4_media_cb` `0xD088B4` | `push {r4,lr}` | +8 B |
| pior outro chamador | | +16 B |
| **pior baseline** | | **168 B** |

`carrega_capa` (`0xDAA256`) abre com `push.w {r4-r8,sb,sl,fp,lr}` +
`sub sp,#0xc` = **48 B**. No emulador, o SP mínimo com MP3 + APIC foi
**352 B** para capas 64×64, 500×500 e 1000×1000 (idêntico; o pool do TJpgDec
é fixo).

O `envia_path` do B6b usa 40 B; total medido no pior caso:

```
168 (baseline) + 40 (envia_path B6b) + 352 (carrega_capa) = 560 B
2048 - 560 = 1488 B livres  (> 512 B exigidos)
```

O B6a usa 40 B e não chama `carrega_capa`; sobra muito mais.

## 3. Por que a fábrica para a música para abrir foto

**CONFIRMADO que a fábrica para a música por decisão de produto.**
`0xC5CFC7` = `"Music would be stopped if you open the picture, continue?"`.
O caminho é `_pic_proc_` (`0xC4FD59`) e as strings `JpegDec*` (`0xC4FCAD`).

**NÃO DÁ PARA SABER** se o `JpegDec`/`_pic_proc_` disputa memória ou
hardware com o decodificador de áudio. Não há prova no binário. O TJpgDec da
RC7 (`0xD10B20`/`0xD11090`) é outro decodificador; o B6b o usa na PreTask e
o teste de emulação mostra que ele não toca no estado do áudio.

## 4. Entrega dos pixels à view

**ESCOLHIDO: (i) mensagens em pedaços.** O (ii) foi descartado: sem prova de
liberação em todos os caminhos (inclusive página que não é o player ou
mensagem que não chega ao `label_process`), é proibido.

- 8 mensagens classe 3, tipo 6, de 1024 B de pixels (64×64×2 = 8192 B).
- `msg+0xA = 0x408` (comprimento sem `strlen`); tamanho da mensagem =
  `0x408 + 0xC = 0x414` B; 8 × `0x414` = **8352 B**.
- O offset vai em `msg+0x10`; os pixels em `msg+0x14`.
- A view copia para `ext+0x210+offset`; no último pedaço
  (`offset == 0x1C00`) faz `img_set_src(img, ext)`.
- O ring da view (`0x0081BBC0`, 15360 B) cabe as 8 mensagens com folga.

## 5. O que foi construído

- **B6a** (`reload_1.0_rc7_diag_b6a`): B4 exato; no `envia_path` da PreTask
  (`0xDAAC00`), depois do `get_path`: `calloc(1,0x25C)`, `f_open(caminho,1)`,
  `f_read` de 10 B, `f_close`, `free`. `"ID3"` → tipo 5 com o caminho e
  `0xD0D881`; qualquer falha → tipo 5 vazio (cinza) e `0xD0D881`. A view
  mantém a lógica do B4 (tipo 5); só o desvio para o `label_dispatch` muda
  de `bl` para `b.w` (item 7).
- **B6b** (`reload_1.0_rc7_diag_b6b`): `calloc(1,0x2210)`, caminho em
  `tmp+0x110`, `carrega_capa(tmp)` (`0xDAA256`) intacto. Sucesso → 8 tipos 6,
  `free(tmp)` e `0xD0D881`; falha → tipo 5 vazio, `free(tmp)` e `0xD0D881`.
  A view só copia pixels e faz `img_set_src`; nenhuma função de arquivo é
  alcançável dela (teste estático em `tests/test_diag_trava.py`, classe
  `B6`).

## 6. O que não dá para saber

- Se o `JpegDec` da fábrica compartilha hardware/memória com o áudio (item 3).
- Se o aparelho real se comporta como o emulador em todos os tempos de
  `f_open`/`carrega_capa`; o B6a é o decisor no aparelho.

## 7. Correções da revisão (B6a/B6b)

- **Tipo 6 na view (crítico).** O `label_process` começa em `0xD32204`
  (`ldr r3,[pc,#0x9c]`; `ldrh r2,[r0,#6]`; `cmp r2,#3`; `push` em
  `0xD3220C`; `ldr r5,[r3,#0xac]`). O B4 deixou `cmp r3,#5` em `0xD3223E`;
  sem o B6b trocar para `cmp r3,#6`, o tipo 6 cai em `bhi 0xD322A0` e nunca
  chega ao `label_dispatch`.
- **Desvio `b.w`, não `bl`.** O epílogo `0xD322A0 pop {r4,r5,r6,pc}` espera
  a pilha do prólogo. Um `bl` empilha o LR e o `pop` sai 4 B deslocado; o
  patch em `0x00132242` tem de ser `b.w label_dispatch`.
- **Retorno do `0xD0D818`.** `0xD0D818` devolve 0 quando a mensagem é nula
  ou `0xCFE708` devolve 0; `0xCF83E4` devolve o comprimento (não zero) no
  sucesso e 0 no ring cheio. Logo **0 = falha, != 0 = sucesso**; o B6b usa
  `beq` para o caminho de falha.
- **`0xD0D881` restaurado.** O aviso da view é chamado depois do último send
  de cada caminho (tipo 5 do B6a, 8º tipo 6 do B6b e tipo 5 vazio), como a
  fábrica em `0xD084D8` (free e depois `0xD0D880`).
- **Imagens carimbadas novas.** B6a `80cc6bfb…` (1013 B contra o B4
  carimbado, 2 setores de patch); B6b `542ecbb8…` (1263 B, 2 setores).
  `.up` B6a CRC `0xFC0A`, sha `d99758e9…`; B6b CRC `0x9E9E`, sha
  `1c06cbdf…`.

## Resultado do B6b no aparelho (decisor, 2026-11-10)

- **A capa apareceu** na Tocando Agora, com o B6b corrigido (`a78a169`, `.up` `1c06cbdf…`, CRC `0x9E9E`).
- **CONFIRMADO no aparelho:** ler e decodificar a capa na PreTask e entregar os pixels à view em 8 mensagens tipo 6 funciona.
- Observação: o decisor gravou antes da conferência final da coordenação e da revisão GLM. Ainda falta registrar a impressão dele.
