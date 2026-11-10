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
  `f_read` de 10 B, `f_close`, `free`. `"ID3"` → tipo 5 com o caminho;
  qualquer falha → tipo 5 vazio (cinza). A view é byte a byte a do B4.
- **B6b** (`reload_1.0_rc7_diag_b6b`): `calloc(1,0x2210)`, caminho em
  `tmp+0x110`, `carrega_capa(tmp)` (`0xDAA256`) intacto. Sucesso → 8 tipos 6
  e `free(tmp)`; falha → tipo 5 vazio e `free(tmp)`. A view só copia pixels
  e faz `img_set_src`; nenhuma função de arquivo é alcançável dela (teste
  estático em `tests/test_diag_trava.py`, classe `B6`).

## 6. O que não dá para saber

- Se o `JpegDec` da fábrica compartilha hardware/memória com o áudio (item 3).
- Se o aparelho real se comporta como o emulador em todos os tempos de
  `f_open`/`carrega_capa`; o B6a é o decisor no aparelho.
