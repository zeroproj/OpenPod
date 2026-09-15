# EXTRAS — o plano, e o aviso honesto

> Aberto em 2026-09-14, depois da Core 2.2. Decisão do mantenedor: a home
> passa a seguir o modelo do **iPod nano 2G**, com poucos itens, e o resto
> vai para um submenu **Extras**.
>
> **Nada aqui foi implementado.** É plano.

---

## 1. O alvo, decidido

```
HOME                    EXTRAS
  Musica                  Gravacao
  Video                   Radio
  Extras      ->          Livro digital
  Configurar              Imagem
                          Bluetooth
                          Pastas
```

Quatro itens na home, seis no Extras. Total 9 destinos + 1 item novo.

### O que isso destrava

A padronização de geometria, que hoje é **aritmeticamente impossível**:

```
hoje      22 + 9 x 16 = 166   nao cabe em 160
com 4     22 + 4 x 16 =  86   sobra folga
```

Com quatro itens, a home passa a começar em `y=22` como todas as outras
telas, com linhas de 16 px. **Geometria idêntica, sem preço.**

---

## 2. ⚠️ O AVISO — este é o único patch que nunca funcionou

O submenu Extras foi tentado **três vezes** neste projeto:
`patch_extras`, `patch_extras_fix`, `patch_extras_fix2`. Três patches
empilhados no mesmo ponto. **Os itens nunca abriram no aparelho.** As três
ferramentas foram apagadas na limpeza de 2026-09-14.

A causa está medida: esticar a contagem de itens de uma página existente
mexe em **alocação e aritmética de ponteiro**, e corrupção de heap **não
aparece na verificação byte a byte pós-gravação**.

> **É a única classe de defeito deste projeto que passa por todos os
> nossos testes e só quebra no aparelho.**

### Por que hoje é diferente — e não é otimismo, são dois fatos

**1. Nós reescrevemos o `create` da home do zero, e funcionou.** A Core
2.0.2 provou que dá para substituir um laço de desenho inteiro no lugar,
sem tocar em alocação. A tela Extras pode nascer assim, em vez de esticar
a contagem de uma página de fábrica — que foi o que quebrou antes.

**2. Sabemos onde mora a estrutura de cada página e quanta folga tem.**
Foi isso que tornou a conversão da home segura: `malloc 0x54` intocado,
zero aritmética de ponteiro (`CARCACA_PADRAO.md` §4.3).

---

## 3. O que já foi medido sobre o ROTEAMENTO

É a parte que derrubou as tentativas anteriores, e é a que menos se
conhece.

### O enter da home

```
00D2EA62  ldr  r3, =0x00823D83     o indice selecionado
00D2EA64  ldrb r2, [r3]
00D2EA66  cmp  r2, #8              indice > 8 -> ignora
00D2EA6C  movs r3, #4
00D2EA6E  movs r1, #2
00D2EA70  movs r0, #1
00D2EA76  b.w  0xD23510            despacha, com o INDICE em r2
```

### O despachante

`0x00D23510` monta uma **mensagem** na pilha e a envia:

```
sp+0x04 = r7 = 1
sp+0x06 = r6 = 2
sp+0x08 = r5 = O INDICE        <- e este campo que seleciona o destino
sp+0x0a = 1
sp+0x0e = 2
```

**O mapeamento índice → página acontece depois**, em `page1_process`, que
vive na região BAIXA da flash (fora do XIP). As tentativas antigas
registraram endereços dessa área (`0x00100F66`, `0x00100FB2`,
`0x00101036`) e descreveram um `tbh` — tabela de desvio.

### ✅ Passo 1, PARCIAL — medido em 2026-09-15

**Primeiro: os endereços dos relatórios antigos NÃO BATEM com mapa
nenhum.** `0x00100F66` está abaixo da base do mapa `boot` (`0x0081FB60`)
e fora do XIP (`0x00C00000`). Não há como localizá-los. Bom que o plano
os marcou como não medidos — construir em cima deles teria sido chute.

**O despacho NÃO é chamada direta: é uma FILA.**

```
0x00D23510   monta a mensagem na pilha, com o INDICE em sp+0x08
0x00D234AC   pega um buffer (0x00D6AE38) e ENFILEIRA
```

A mensagem é consumida depois, noutro contexto. Logo **não existe tabela
inline para remapear** no caminho do enter.

**Quem consome é o `page1_process`, e os destinos têm nome próprio:**

```
0x00D00D6C  page1_build_cb          0x00D00E28  page1_music_build_cb
0x00D00DA0  page1_record_build_cb   0x00D00E84  page1_video_build_cb
0x00D00DE0  page1_folder_build_cb   0x00D00EE0  page1_ebook_build_cb
```

**Cada um aparece exatamente UMA vez, e sempre em POOL LITERAL**
(`0x00D01250`…`0x00D01308`) — nunca como `bl` direto.

> **Consequência, e é a que decide o custo:** o mapeamento índice →
> destino está no **CÓDIGO** de `page1_process`, como um switch que
> carrega o ponteiro certo por literal. **Não é tabela de dados que se
> reescreva.** Remapear exige editar o switch — o terreno exato onde as
> três tentativas anteriores morreram.

### ✅ E o switch é `TBH` — o melhor caso

```
00D00FB2  ldrh r3, [r4, #0xc]     o indice, vindo da mensagem
00D00FB4  cmp  r3, #0xb           limite: 12 entradas (0..11)
00D00FBA  tbh  [pc, r3, lsl #1]
```

**A tabela é DADO PURO** — 12 halfwords em `0x00D00FBE`, 24 bytes:

```
 0 -> 0x00D00FD6     4 -> 0x00D01162     8 -> 0x00D0128C
 1 -> 0x00D01066     5 -> 0x00D011AE     9 -> 0x00D012E2
 2 -> 0x00D010F6     6 -> 0x00D012D6    10 -> 0x00D01202
 3 -> 0x00D0113C     7 -> 0x00D0123A    11 -> 0x00D012DC
```

**Trocar o destino de um item é trocar UM HALFWORD.** Sem mexer em
código, sem mudar tamanho, sem realocar. É o caso mais barato que podia
sair.

### ⚠️ MAS o TBH tem alcance limitado — e isso molda a solução

```
destino = pc + 2*halfword,  pc = 0x00D00FBE
o halfword e SEM SINAL, 16 bits  ->  no maximo +131.070 bytes
alcance:  0x00D00FBE .. 0x00D20FBC

a AREA LIVRE do projeto:  0x00DA3040     FORA DO ALCANCE
```

**Uma entrada do TBH não consegue apontar para código novo na área
livre.** O destino tem de morar nos ~128 KB seguintes à tabela.

### O que isso implica para o Extras — e muda a abordagem

Escrever um `page1_extras_build_cb` novo na área livre e apontar o TBH
para ele **não funciona**. Sobram dois caminhos:

**A — reaproveitar uma página que já existe.** O `page_home_menu`
(página `0x53`, `0x00D2F0A0`) já monta uma lista com os helpers da
carcaça, e já tem despacho próprio. O item "Extras" da home apontaria
para ela, e o `create` dela seria reescrito com 6 itens — exatamente a
técnica que funcionou na home (Core 2.0.2), e que **não mexe em
alocação**.

**B — um trampolim perto da tabela.** Apontar o TBH para um trecho morto
dentro do alcance, que faz um `b.w` para a área livre. Depende de achar
espaço morto ali, e acrescenta um salto.

**O caminho A é o recomendado**: usa o que já existe, já foi provado
nesta linha, e não depende de achar espaço.

---

## 3-bis. A página `0x53` medida — o custo real do caminho A

> Medido em 2026-09-15. É a mesma medição que tornou a conversão da home
> segura, feita agora para a página que virará o Extras.

### A estrutura

```
page_home_menu_create  0x00D2F0A0
  00D2F0A4  movs r0, #0x28      aloca 40 bytes
  00D2F0C2  movs r2, #0x28      memset

  r8 = r7 - 4 ;  no laco  r8 = r7 + 4i

  str   r4, [r8, #0x04]!   -> +0x00   array A  = a LINHA
  str.w sb, [r8, #0x0C]    -> +0x0C   array B
  str.w sl, [r8, #0x18]    -> +0x18   array C

  3 arrays x 3 itens x 4 = 0x24        folga: 4 bytes
  laco: `cmp r6, #3`  em 0x00D2F2DA
```

**São TRÊS arrays**, não dois: ela guarda ícone além de linha e texto.

### Quem toca nos deslocamentos — só três pontos

```
0x00D2F2DC  str.w +0x0C   escreve array B
0x00D2F2E0  str.w +0x18   escreve array C
0x00D2F2FA  ldr   +0x0C   le array B
```

Isso é pouco, e é a boa notícia: a aritmética de ponteiro está
concentrada, não espalhada.

### O custo para 6 itens

| o que | de | para | bytes |
|---|---|---|---|
| `malloc` / `memset` | `0x28` | `0x4C` | 2 |
| array B | `+0x0C` | `+0x18` | 2 pontos |
| array C | `+0x18` | `+0x30` | 1 ponto |
| limite do laço | `cmp r6,#3` | `#6` | 1 |
| tabela de ids | 3 entradas | 6 entradas | nova tabela |

### ⚠️ E o ponto que ainda incomoda — a cópia para a pilha

```
00D2F0A6  sub sp, #0x1c              28 bytes de pilha
00D2F20C  ldr r3, =0x00C486E8        a tabela de 3 ids
00D2F20E  ldm.w r3, {r0, r1, r2}     le TRES palavras
00D2F214  stm.w r3, {r0, r1, r2}     copia para sp+0xC
```

Para 6 ids seriam 24 bytes a partir de `sp+0xC` → `sp+0x24`, e a pilha
só tem `0x1C`. **Transbordaria.**

**Saída limpa, e ela simplifica em vez de complicar:** o laço já lê o id
com `ldr r0, [r3, r6, lsl #2]`. Basta **apontar `r3` para a própria
tabela** em vez da cópia na pilha, e a cópia inteira deixa de existir.
Menos código, não mais.

### Veredito honesto

O caminho A é **tratável e medido**, mas ele **É** aritmética de
alocação — a classe que quebrou as três tentativas antigas, e a única
que não aparece na verificação byte a byte.

A diferença em relação àquelas tentativas não é coragem: é que agora
cada número está medido, a aritmética está em **3 pontos** e não
espalhada, e a cópia para a pilha — que seria o transbordo silencioso —
foi **encontrada antes**, não depois de gravar.

**Recomendação:** fazer o Extras numa versão isolada, sem nenhuma outra
mudança junto, e testar entrando em cada um dos seis itens antes de
seguir para a home de 4 itens.

---

## 4. A ORDEM — e errar ela apaga funções do aparelho

```
1. MEDIR a tabela de despacho indice -> pagina     (so medicao)
2. a string "Extras"                               (ferramenta ja existe)
3. a tela EXTRAS, funcionando e testada
4. a home com 4 itens
5. padronizar a geometria                          (ai sem preco)
```

**O passo 5 não pode vir antes do 4**, e o 4 não pode vir antes do 3.

Se a geometria for padronizada com os 9 itens ainda na home, os itens
além do oitavo saem da área visível — e a navegação da home é por índice
e **não rola**. Ficariam inalcançáveis.

Se a home for reduzida antes de o Extras funcionar, Gravação, Rádio,
Livro digital, Imagem, Bluetooth e Pastas ficam **sem nenhum caminho de
acesso**.

---

## 5. O que muda na home, em detalhe

| | hoje | depois |
|---|---|---|
| itens | 9 | 4 |
| tabela de ids | `0x00C486C4`, 9 entradas | 4 entradas |
| limite da navegação | `cmp r1,#8` (4 pontos) | `cmp r1,#3` |
| limite do enter | `cmp r2,#8` | `cmp r2,#3` |
| `N_ITENS` no nosso laço | 9 | 4 |
| `TOPO` | 16 | 22, igual às outras |

O item **Extras** é novo: precisa de id de texto e de destino. O
`relocate_lang_table.py --add Extras` já existe e já criou o id 216 no
passado — está na ferramenta, sem uso hoje.

---

## 6. Alternativa mais barata, se o roteamento se mostrar caro

Se a medição do passo 1 mostrar que remapear o despacho é arriscado, há
um caminho intermediário que entrega **quase tudo** sem tocar em
roteamento:

**Manter os 9 destinos e só reordenar a home**, deixando os quatro
primeiros visíveis e os cinco últimos alcançáveis por rolagem — mas isso
exige fazer a navegação rolar, que hoje ela não faz.

**Ou**: aceitar a home com 8 itens em vez de 9, movendo só "Pastas" para
dentro de uma tela que já exista. `22 + 8 x 16 = 150`, cabe.

Nenhuma das duas é o alvo do nano. São saídas, não o plano.

---

## 7. Recomendação de sequência

O **M-c** (faixa superior da home) é pequeno, não toca em roteamento e
deixa a home visualmente igual às outras. Vale fazer **antes**, enquanto
o Extras é medido — assim há entrega segura no meio do caminho.

---

## 8. A RECEITA DO EXTRAS — medida byte a byte, 2026-09-15

> Tudo aqui está **medido**, não estimado. Falta **uma** peça, declarada
> em §9, e sem ela a versão não é testável.

### 8.1 A tabela de ids — pronta

A home usa `0x00C486C4`, nove entradas:

```
0 Musica  id 1     3 Radio          id 6     6 Bluetooth  id 9
1 Video   id 3     4 Livro digital  id 2     7 Configurar id 10
2 Gravacao id 5    5 Imagem         id 4     8 Pastas     id 8
```

A tabela do Extras são os índices 2,3,4,5,6,8 — **24 bytes na área livre**:

```
ids = [5, 6, 2, 4, 9, 8]
       Gravacao, Radio, Livro digital, Imagem, Bluetooth, Pastas
```

### 8.2 As nove edições na página `0x53`

| # | onde | de | para | o que é |
|---|---|---|---|---|
| 1 | `0x0012F0A4` | `0x28` | `0x4C` | `malloc` |
| 2 | `0x0012F0C2` | `0x28` | `0x4C` | `memset` |
| 3 | `0x0012F2DC` | `+0x0C` | `+0x18` | escreve array B |
| 4 | `0x0012F2FA` | `+0x0C` | `+0x18` | lê array B |
| 5 | `0x0012F37A` `0x0012F40E` `0x0012F43E` `0x0012F486` | `+0x0C` | `+0x18` | lê array B (4 pontos) |
| 6 | `0x0012F2E0` | `+0x18` | `+0x30` | escreve array C |
| 7 | `0x0012F414` | `+0x18` | `+0x30` | lê array C |
| 8 | `0x0012F2DA` | `cmp r6,#3` | `#6` | limite do laço |
| 9 | `0x0012F246` | `cmp r6,#2` | `#5` | o último item (borda) |
| 10 | `0x0012F3E2` `0x0012F406` | `cmp r3,#2` | `#5` | limites de navegação |

**Ordem obrigatória:** o novo offset do array B (`+0x18`) colide com o
offset antigo do array C. A ferramenta calcula todas as posições
**antes** de escrever qualquer byte.

### 8.3 A cópia para a pilha — o transbordo, contornado

```
00D2F0A6  sub sp, #0x1c            28 bytes de pilha
00D2F20E  ldm.w r3,{r0,r1,r2}      copia TRES ids para sp+0xC
00D2F2B6  add r3, sp, #0xc         o laco recarrega o ponteiro aqui
00D2F2B8  ldr.w r0, [r3, r6, lsl #2]
```

Crescer a cópia para 6 ids transbordaria a pilha. **A saída é melhor:**
trocar o `add r3,sp,#0xc` por um `ldr` do pool, e apontar o pool para a
tabela nova. A cópia continua acontecendo, fica inofensiva, e **nada
transborda**.

```
0x0012F2B6   03 ab   add r3,sp,#0xc   ->   1b 4b   ldr r3,[pc,#108]
0x0012F324   o pool: 0x00C486E8       ->   a tabela nova na area livre
```

Conferido: o pool fica a 108 bytes do `pc` alinhado — dentro dos 1020 do
`ldr` de 16 bits.

---

## 9. ⚠️ O QUE FALTA, e sem isso a versão NÃO É TESTÁVEL

**A página `0x53` está MORTA no firmware de fábrica.** Nada chega nela.
Expandir para 6 itens e gravar produziria uma tela que não abre por
lugar nenhum — e um teste que não testa.

Falta **rotear** algo até ela. O caminho natural, já medido em §3:

```
a tabela TBH em 0x00D00FBE, 12 halfwords
  indice 2 (Gravacao) -> 0x00D010F6
```

Apontar o índice 2 para a página `0x53` tornaria a versão testável de
imediato: o item "Gravação" da home abriria a lista de seis. O rótulo
ficaria errado por enquanto — e **Gravação continua acessível, de dentro
do Extras**.

**O que precisa ser medido antes:** para onde um destino do TBH tem de
apontar para abrir a página `0x53`. Os alvos da tabela são trechos de
código dentro do `page1_process`, não endereços de página — é preciso
ler um deles e entender o que ele faz.

### ✅ MEDIDO — e a receita está completa

**Como um destino do TBH abre uma página.** Os destinos curtos setam
registradores e caem numa cauda comum:

```
00D011EA  movs r3, #0x15        <- O NUMERO DA PAGINA
00D011EC  movs r2, #0
00D011EE  movs r1, #2
00D011F0  movs r0, #1
00D011F2  pop.w {r4,r5,r6,r7,r8,lr}
00D011F6  b.w  0xD0DAE0         <- a troca de pagina
```

**Confirmação cruzada:** o destino do índice **7** (Configurar) seta
`r3 = 0x28`, e `PAGINAS.md` registra que a página **40 = 0x28** é o
`page_set_menu` — o Configurar. `r3` é o número da página.

### ⚠️ CORREÇÃO — a página NÃO é a `0x53`. É a `0x52`.

Este documento, e os relatórios antigos, vinham dizendo `0x53`. **Está
errado por um.** Medido na tabela `TBB` do `view_page_create`
(`0x00D23B34`):

```
pagina 0x51 (81)  -> bl 0x00D3CAA8
pagina 0x52 (82)  -> bl 0x00D2F0A0    <- page_home_menu_create
pagina 0x53 (83)  -> 0x00D23B38       outra coisa
```

**Usar `0x53` abriria a página errada.** Toda referência a "página 0x53"
neste projeto deve ser lida como **`0x52`**.

### A peça que faltava, pronta

Reescrever o começo do destino do índice 2 (hoje Gravação,
`0x00D010F6`) com 10 bytes:

```
0x001010F6  52 23   movs r3, #0x52      a pagina do Extras
0x001010F8  00 22   movs r2, #0
0x001010FA  02 21   movs r1, #2
0x001010FC  01 20   movs r0, #1
0x001010FE  78 E0   b 0x00D011F2        a cauda comum
```

O resto do destino antigo vira código morto — só era alcançável pela
entrada 2 do TBH.

**Efeito:** o item "Gravação" da home passa a abrir a lista de seis. O
rótulo fica errado até a home ser reduzida, e **Gravação continua
acessível de dentro do Extras**. A versão vira testável.
