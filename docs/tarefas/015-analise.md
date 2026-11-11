# 015 — análise: a capa sem engasgar a música

Base: B6b exato (`5f5020b3…`, carimbado `542ecbb8…`). Toda afirmação foi
lida no binário e conferida no emulador; o que não foi provado está marcado.

## 1. A função de dormir da fábrica

**CONFIRMADO: `0xD2436E` não é sleep.** É o caminho do tipo `0x11` do handler
`0xD242B4` (`0xD242D0`), que faz `b.w 0x811700` com `r0` = ponteiro da
mensagem. `0x811700` tem uma única referência e é **PROVÁVEL** limpeza/free,
não uma pausa de tarefa. A afirmação antiga da `008-analise` está errada.

- **CONFIRMADO:** `0xD7DADE` chama a recepção bloqueante de fila em `0xB372`.
  O argumento de timeout é passado adiante; a unidade (ticks ou ms) **não**
  está provada.
- **PROVÁVEL:** `0x80D580` é uma espera/delay em ms; o corpo está em RAM,
  fora do dump.
- **PROVÁVEL:** `0xC43634` é o `vPortYield`/PendSV: `cbz r0`; grava
  `0x10000000` em `0xE000ED04`; `dsb`/`isb`; não tem xrefs.
- O período do tick e o SysTick estão na mask ROM (`0x0000B5A9`), fora do
  dump. **Não dá para provar** a unidade do timeout nem o período.

**Seguro na PreTask?** Sim para o yield escolhido. No ponto de pausa a
PreTask não segura o mutex do banco (`0x80DB48`/`0x80DB6E` não aparecem no
`carrega_capa`) e o FatFs já soltou a trava: `f_read` (`0xD76854`) chama
lock `0xD7533E` e unlock `0xD75328` dentro da própria chamada; o caminho de
skip usa `f_lseek` (`0xD76C0B`). O callback de saída só escreve pixels.

**Qual deixa a MediaTask rodar?** As duas tarefas têm prioridade 3. O yield
entrega a vez imediatamente; o sleep também, mas acrescenta atraso e depende
do tick. **Escolhido: yield, sem sleep.**

## 2. Onde pausar

Os callbacks reais do TJpgDec no `carrega_capa 0xDAA256` são:

| Papel | Ponteiro | Rotina | Onde é passado |
|---|---|---|---|
| entrada | `0xDAA405` | `0xDAA404` | `0xDAA30A adr r1,#0xf8` → `0xDAA30C orr r1,#1`; `0xDAA31E blx` `jd_prepare 0xD10B20` |
| saída | `0xDAA477` | `0xDAA476` | `0xDAA372 addw r1,pc,#0x102` → `0xDAA376 orr r1,#1`; `0xDAA384 blx` `jd_decomp 0xD11090` |

A ficha dizia “perto de `0xDAA9B6`/`0xDAA8E0`”: essas duas são rotinas de
ID3/APIC (varredura/leitura do marcador JPEG), **não** os callbacks. O
emulador confirma `r1 = 0xDAA405` em `jd_prepare` e `0xDAA477` em
`jd_decomp`.

Contagem de chamadas no emulador:

| Capa | B6b entrada/saída | B7a entrada/saída |
|---|---:|---:|
| 300×300 | 34 / 361 | 34 / 361 |
| 500×500 | 77 / 1024 | 77 / 961 |
| 1000×1000 | 164 / 3969 | 164 / 3969 |
| 48×48 | 21 / 0 (falha) | 21 / 0 (falha) |
| 56×56 | 21 / 0 (falha) | 24 / 16 (s=0) |

Nenhuma trava fica presa: a entrada chama `f_read`/`f_lseek`, que adquirem e
liberam a trava do FatFs internamente; a saída só escreve no `tmp`. O
emulador termina sem erro e sem arquivo aberto.

## 3. Quanto pausar

**Escolhido: N=1, yield depois de cada callback; sem sleep.**

- O maior trecho sem pausa é **um** callback: uma leitura de até 512 B ou
  um bloco de saída do TJpgDec, seguido imediatamente do yield. Não há
  trecho de vários callbacks sem ponto de scheduler.
- Número de pausas = entrada + saída:
  - 300: `34 + 361 = 395`;
  - 500: `77 + 961 = 1038`;
  - 1000: `164 + 3969 = 4133`;
  - 56: `24 + 16 = 40`.
- Custo do wrapper + yield: ~20 instruções por callback (push/movw/movt/blx
  + `0xC43634`). Em 500 são ~21 mil instruções, muito abaixo de 500 ms mesmo
  a 48 MHz; a troca de contexto real não é medida no emulador e fica para o
  aparelho. **Não há sleep**, então o atraso não cresce com ticks.
- Pilha medida no B7b para 500: **368 B usados** (inclui o frame de 16 B do
  wrapper); com o pior baseline de 152 B sobram **1528 B** (> 512 B).
  O `vPortYield` real salva contexto no stack da tarefa; a folga cobre isso.

## 4. O que foi construído

### B7a — só a escala

B6b exato + quatro bytes `0x40` → `0x38` em `0x1AA32C`, `0x1AA330`,
`0x1AA346`, `0x1AA34E`. 500×500 passa a s=3; 300×300 continua s=2;
1000×1000 continua s=3; <56 → cinza.

- Instruções próprias do `carrega_capa` (hook só no intervalo
  `0xDAA256..0xDAA403`): B6b/B7a = **158/158** (300), **158/162** (500),
  **162/162** (1000).
- Não carimbado: `6e1cb9c6…`; carimbado: `09147526…`; `.up` CRC `0x4609`,
  sha `bf18ca70…`.
- Contra o B6b carimbado: **6 bytes** (2 do texto “B7a” + 4 da escala).

### B7b — escala + pausas + guarda da view

B7a +:

1. Ponteiros de entrada/saída trocados por `ldr.w r1,[pc,#...]`
   (`0x1AA30C`/`0x1AA376`), literais em `0xDAAE50`/`0xDAAE54`;
2. wrappers `0xDAAE00`/`0xDAAE20` + comum `0xDAAE30`, N=1;
3. guarda do tipo 6: o `cmp.w r3,#0x1c00` em `0xDAAABC` vira
   `b.w 0xDAAE60`; a guarda exige `[r4,#0xA] == 0x408`, refaz o cmp do
   offset e volta para a cópia em `0xDAAAC2`; se falhar, vai ao epílogo
   `0xDAAAFA`.

Não carimbado: `26ffa272…`; carimbado: `d7951433…`; `.up` CRC `0xEAC9`,
sha `bd14f18e…`. Contra o B6b carimbado: **107 bytes**.

O resultado em pixels do B7b é idêntico ao B7a; o número de yields é
exatamente entrada+saída; a primeira pausa ocorre depois de `f_open` e
`f_read`; a guarda rejeita `msg+0xA != 0x408` sem copiar.

## 5. O que não dá para saber

- O período real do tick e a unidade do timeout de `0xD7DADE`.
- O corpo de `0x80D580` (RAM, fora do dump).
- O custo real da troca de contexto do `vPortYield` e o tempo de
  `f_read`/TJpgDec no aparelho; o emulador não mede ms.
- Se o aparelho real se comporta como o emulador; o decisor testa B7a
  primeiro e só usa B7b se ainda engasgar.

## 6. Testes

`tests/test_diag_trava.py`, classe `B7` (115–124): construção, reprodutível,
diff exato, recusas, premissas, emulação B7a (300/500/1000/48), emulação
B7b (pixels, yields, primeira pausa), guarda da view e pilha. `sh tools/ci.sh`
continua sem rodar `test_diag_trava.py`; a classe foi rodada à mão.

## Resultado no aparelho (decisor, 2026-11-11)

- **B7b gravado: a engasgada sumiu e a capa aparece rápido.** Toca normalmente.
- **CONFIRMADO no aparelho:** ceder a vez (`0xC43634`, r0=1) a cada callback do TJpgDec resolve a disputa com a MediaTask.
- O B7a (só a escala) não foi testado. O B7b inclui a escala do B7a.
