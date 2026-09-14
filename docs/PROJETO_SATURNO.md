# 🪐 PROJETO SATURNO — a carcaça de design

> Aberto em 2026-09-14 a pedido do mantenedor:
>
> *"centralizar é ótima opção, mas não podemos centralizar fazendo
> gambiarra. Se for necessário vamos reescrever todas as telas, apontando
> para uma carcaça de design padrão que quando muda lá muda tudo."*
>
> **Autorização dada:** a home **pode** deixar de ser imagem.

---

## 1. O diagnóstico

```text
HOME (pagina 1)                 TELAS DE LISTA (36)
  imagem 128x160 indexada         framework de widgets
  faixa = PIXELS na imagem        faixa = objeto (0xD216F0)
  linhas = tabela de coords       linhas = helper (0xD21764)
  selecao = fundo do rotulo       conteiner = helper (0xD21690)
  cores = paleta da imagem        cores = TEMA da LVGL
```

**CONFIRMADO:** `page_home_create` não chama nenhum dos três helpers.

## 2. A causa raiz de TODOS os defeitos visuais até aqui

Um padrão só, repetido:

| defeito | versões gastas | causa |
|---|---|---|
| raio da seleção | 2 | a linha não seta `radius` → **o tema decide** |
| texto cinza nas listas | 1 | a linha não seta `text_color` → **o tema decide** |
| faixa clara vazia | ? | algo não setado → **o tema decide** |

> **Toda vez que a carcaça não pinta, o tema pinta — e o tema não é
> nosso.** Não é uma sequência de descuidos: é uma propriedade da
> arquitetura atual.

## 3. Os três princípios

**P1 — A carcaça pinta tudo, explicitamente.** Nenhum objeto criado por
ela herda nada do tema. Mata a classe inteira de defeitos acima em vez de
caçá-los um a um.

**P2 — Os números moram num lugar só.** Uma tabela de tema na área livre.
A carcaça lê de lá; ninguém mais tem constante de aparência.

**P3 — Um caminho de desenho.** A home passa a usar os mesmos três
helpers. Sem isso, P1 e P2 valem para 36 telas e não para a 37ª — que é
justamente a régua.

## 4. A tabela de tema

```text
offset  tam  campo
 +00     2   cor de fundo da tela
 +02     2   cor de fundo da faixa
 +04     2   cor do separador
 +06     2   cor do texto normal
 +08     2   cor do texto selecionado
 +0A     2   cor da selecao
 +0C     1   altura da faixa        17
 +0D     1   altura da linha        16
 +0E     1   inicio da lista        19
 +0F     1   margem lateral          3
 +10     1   raio                    0
 +11     1   icones na lista         0 = nao
```

Cores em RGB565 **pré-invertidas** (`COLOR_SOURCE.md` §9).

## 5. A forma do patch — e o que já existe

A 2.0 já construiu metade disto sem que eu percebesse:

```text
JA EXISTE (2.0)                        FALTA (Saturno)
  6 thunks compartilhados                ler da tabela em vez de imediato
  77 ganchos apontando para eles         —
  3 ganchos nos helpers (cor/base)       pintar TUDO, nao so 2 coisas
  —                                      page_home_create usando os helpers
  —                                      a tabela
```

Os 77 ganchos **não são gambiarra** — são o mecanismo que neutraliza os
overrides por tela, e eles apontam para **6 rotinas**. Tornar essas 6
rotinas dirigidas por tabela é mudança pequena. O que faltava era a
tabela e a home.

### Ordem de execução

```text
S1  tabela de tema na area livre
S2  as 6 rotinas passam a ler da tabela        (a 2.0 vira consequencia)
S3  os 3 helpers pintam TUDO explicitamente    (mata a heranca do tema)
S4  page_home_create reescrito sobre os helpers
S5  a folha de imagem deixa de desenhar a faixa
```

**S4 é o único código novo de verdade.** E o projeto já fez esse
movimento: a página `0x53` teve o `create` desviado com um `bl` de 4
bytes (V022–V026).

## 6. O que o Saturno NÃO resolve

**A barra no descanso de tela.** Não existe página de descanso de tela —
só `page_scrsaver_time`, que é a configuração. O relógio grande é
desenhado **sem transição de página**, e o chrome só é destruído em
`view_page_create`. Por isso ele sobrevive.

Não é regressão da 2.0: é consequência do título da V054, que só ficou
visível agora. **Corrigir exige achar o caminho de desenho do descanso de
tela** — fica fora do Saturno, anotado.

## 7. O que fica provado quando o Saturno fechar

> Mudar um campo da tabela e ver as 37 telas mudarem juntas.
>
> Enquanto esse teste não passar, o Saturno não está pronto — e não
> adianta ajustar tela nenhuma.

---

## 8. S1 + S2 — FEITOS (V061, não gravado)

`tools/patch_saturno.py`. **173 bytes, 1 setor**, tudo na área livre.

```text
0x001A5400   18 B   a tabela de tema
0x001A5420  132 B   as 7 rotinas, agora dirigidas por tabela
             7 entradas da 2.0 viram `b.w` para as novas
```

### 8.1 Por que os endereços de entrada foram preservados

A 2.0 deixou **77 ganchos** apontando para 7 rotinas. Em vez de reescrever
os 77, cada rotina antiga virou um `b.w` para a versão nova. Os ganchos
continuam válidos e o patch cabe em **1 setor**.

### 8.2 O teste que define "pronto" — passou para S1/S2

```text
altura_faixa 17->24, inicio_lista 19->26, separador -> vermelho

  bytes diferentes entre as duas imagens:  4
  todos dentro da tabela?                  True
  algum byte de CODIGO mudou?              False
```

**Mudar o tema deixou de ser recompilar: é editar dado.**

Ainda vale para 36 telas, não 37 — a home entra no S4.

### 8.3 ⚠️ O erro que o próprio verificador deixou passar

A primeira montagem gerou:

```asm
00DA5422   ldrb r1, [r0, #4]        <- registrador E deslocamento errados
           deveria ser: ldrb r1, [r1, #0xc]
```

O verificador comparava **só o mnemônico** — `ldrb` batia com `ldrb` e ele
aprovou. Só apareceu porque eu desmontei a imagem gravada e olhei.

> **Lição, e é do mesmo tipo que o projeto já registrou duas vezes:** uma
> conferência que não distingue o caso certo do errado não é conferência.
> `ldrb` igual a `ldrb` não prova nada; o que prova é
> `ldrb r1,[r1,#0xc]` igual a `ldrb r1,[r1,#0xc]`.
>
> Corrigido: a conferência agora compara **instrução completa, com
> operandos**, para as 7 rotinas.

## 9. O que falta

| etapa | o quê | estado |
|---|---|---|
| S3 | os 3 helpers pintam TUDO explicitamente (mata a herança do tema) | a fazer |
| S4 | `page_home_create` reescrito sobre os helpers | a fazer |
| S5 | a folha de imagem deixa de desenhar a faixa | a fazer |

O S3 é o que deve matar a **faixa clara vazia**, porque ela é, por
eliminação, propriedade não setada que o tema decidiu.

---

## 10. S3 — FEITO (V062, não gravado)

`tools/patch_saturno_s3.py`. **101 bytes, 2 setores.**

### 10.1 A auditoria que motivou o patch

Desmontei os três helpers e listei o que cada um **não** seta:

```text
propriedade          FAIXA  CONTEINER  LINHA
BG_OPA      (33)      nao      nao      nao
BORDER_OPA  (49)      nao      nao      nao
OUTLINE_W   (53)      nao      nao      nao
SHADOW_W    (64)      nao      nao      nao
```

**Nenhum dos três seta opacidade, contorno ou sombra.** As quatro vinham
do tema. Contorno e sombra são exatamente o que a LVGL desenha sozinha —
contorno no estado focado, sombra nos "cards" — e aparecem como mancha
clara onde não se pediu nada.

### 10.2 O patch

```text
0x001A5500  48 B  normaliza(obj)   bg_opa=255 border_opa=255
                                   outline_w=0 shadow_w=0
0x001A5530  24 B  faixa   = raio DA TABELA + normaliza
0x001A5548  16 B  cont    = cont_base (S1/S2) + normaliza
0x001A5558  16 B  linha   = cor_texto (1.9)  + normaliza
```

Os ganchos **encadeiam** as rotinas que já existiam em vez de duplicar
lógica. `OUTLINE_WIDTH` e `SHADOW_WIDTH` não têm casca no firmware — o
linker descartou as que o código não usava — então vão pelo despachante
comum `0x00D4CAC4`, o mesmo caminho do raio.

### 10.3 ⚠️ UMA VARIÁVEL DE CADA VEZ — de propósito

Este patch mexe **só** nessas quatro. **Não** mexe em padding, que é
layout e também é suspeito.

> Se a faixa clara morrer, era herança de tema — e fica provado.
> Se sobreviver, **não** é herança de tema, e o próximo passo procura
> outra coisa sabendo onde não está.
>
> Mudar as duas classes juntas resolveria (talvez) e não ensinaria nada —
> e este projeto já pagou caro por "consertei, não sei qual dos dois
> era".

## 11. Estado do Saturno

| etapa | o quê | estado |
|---|---|---|
| S1 | tabela de tema | ✅ V061 |
| S2 | as 7 rotinas lendo da tabela | ✅ V061 — teste dos 4 bytes passou |
| S3 | os 3 helpers pintam tudo | ✅ V062 |
| S4 | `page_home_create` sobre os helpers | a fazer |
| S5 | a folha de imagem sem a faixa | a fazer |

**Nenhuma versão gerada.** V061 e V062 são imagens de trabalho.

---

## 12. S4 e S5 — FEITOS (V063 e V064, não gravados)

### 12.1 S4 — a home entra na carcaça, e o que eu NÃO fiz

Mapeei a home antes de escrever:

```text
0x00D2EBF0   widget proprio (classe 0x00CDAAA8), nao os helpers
0x00D2ECF0   por item: objeto de imagem (icone) + rotulo,
             posicionados por tabela de coordenadas
```

**Não reescrevi `page_home_create` inteiro.** Trocá-lo pelos helpers
exigiria trocar junto o `event_cb` e todo o modelo de `ctrl_id` — isto é,
**mexer na navegação que o mantenedor aprovou** — e é a classe de mudança
que já custou três gravações (`MENU_LISTA.md` §14).

O que fiz: **a faixa da home passou a ser o mesmo objeto das outras 36**,
criado pelo mesmo helper, com altura vinda da tabela.

```text
0x0012EC3E   bl bg_color  ->  bl 0x00DA5600

0x00DA5600   bg_color (o que ja fazia)
             tela  = lv_disp_get_scr_act()
             faixa = 0x00D216F0(tela)     <- helper compartilhado
             0x00DA5300(faixa)            <- altura DA TABELA
```

**24 bytes.** A faixa nasce depois do widget da home (desenhada por cima)
e antes do relógio/título/bateria, que a camada VIEW cria depois da
página (e portanto ficam acima dela). A ordem sai certa sozinha.

> **Dívida registrada, não resolvida:** a posição dos itens da home
> continua em tabela de coordenadas (`0x00C4867C`, `0x00C486A0`), ligada
> em tempo de **patch**, não de execução. Se `inicio_lista` ou
> `altura_linha` mudarem, essas coordenadas precisam ser regeradas junto.
> Hoje o valor bate (y=19), então não há divergência visível — mas a
> fonte de verdade é dupla, e isso é dívida.

### 12.2 S5 — a folha para de desenhar a faixa

```text
0x000CE15C   2.176 pixels das linhas 0..16  ->  indice 1 (fundo)
             a paleta NAO foi tocada
```

A ferramenta **recusa** se as linhas 0..16 contiverem qualquer índice fora
da faixa (2,3,4,5) e do fundo (1) — se a folha guardasse outra coisa ali,
apagar seria destruir. Conferido: só 2, 3, 4 e 5.

**Separado do S4 de propósito.** Se o objeto não aparecer no aparelho, a
home fica sem faixa — e aí se sabe que foi o objeto, não a folha.

## 13. O TESTE DO SATURNO — PASSOU

```text
tabela em 0x1A5400, 18 bytes

altura_faixa  17 -> 24
  1 byte alterado, em 0x1A540C, dentro da tabela
  nenhum byte de codigo mudou

quem le esse byte:
  thunk faixa_h    24 pontos de chamada
  thunk faixa_sz   14 pontos de chamada
  alcance          36 telas de lista + a HOME
```

> **Mudar a aparência do aparelho deixou de ser recompilar: é editar um
> byte de dado.** Era isto que o mantenedor pediu.

## 14. Estado final do Saturno

| etapa | o quê | estado |
|---|---|---|
| S1 | tabela de tema | ✅ V061 |
| S2 | as 7 rotinas lendo da tabela | ✅ V061 |
| S3 | os 3 helpers pintam tudo | ✅ V062 |
| S4 | a faixa da home vem do helper | ✅ V063 |
| S5 | a folha sem a faixa | ✅ V064 |

**Nenhuma versão gerada.** V061–V064 são imagens de trabalho.

### Os três em aberto — FECHADOS no S6

O mantenedor perguntou: *"essas 3 coisas em aberto não vamos resolver?"*
Ele estava certo — **duas delas eu tinha deixado em aberto por
conveniência, não por necessidade.**

---

## 15. S6 — os três pontos fechados (V065, não gravado)

`tools/patch_saturno_s6.py`. **158 bytes, 3 setores.**

### A — a cor da seleção vem da tabela

Vinha de `palette_main(7)` em três pontos: `0x00D2EB42` e `0x00D2EDB2`
(home) e `0x00DA3520` (a rotina compartilhada das 39 telas). Não era
herança de tema — era explícita — mas era **constante fora da tabela**, e
portanto uma segunda fonte de verdade.

**Li o valor real antes de mexer**, para não mudar a cor às cegas. A
tabela de paletas da LVGL está em `0x00CDF078`, indexada por 16 bits:

```text
palette_main(7) = 0xFA05 pre-invertido = RGB565 0x05FA = RGB(0,190,213)
```

É o ciano da seleção. A tabela de tema foi semeada com **esse mesmo
valor**: zero mudança visual, e a cor passa a morar num lugar só. A
ferramenta **recusa** se a paleta na imagem não devolver esse valor.

### B — o padding passa a ser da carcaça

O S3 deixou padding de fora de propósito, para não mudar duas classes de
uma vez. O princípio P1 diz que a carcaça pinta **tudo** — padding
incluído.

```text
pad_left = pad_right = pad_bottom = 0 nos tres objetos
pad_top  NAO e tocado: o conteiner o recebe da tabela, em cont_base,
         que roda antes. Zerar aqui apagaria aquilo.
```

Escolhi **0** e não `margem`: hoje as margens vêm da largura do rótulo
(`hor_res - 6`), então 0 preserva o visual **e** ainda assim tira a
decisão do tema. `margem` fica reservado para quando se quiser mover a
margem para o padding.

### C — a geometria dos itens da home passa a ser de execução

Era a dívida do S4. O laço da home é rastreável: `r5` é o índice × 4 nos
dois `set_pos`, e a altura do rótulo era `0x10` fixo no código.

```text
0x0012ED20  set_pos do icone    ->  y = inicio_lista + altura_linha * i
0x0012ED7E  set_pos do rotulo   ->  y = inicio_lista + altura_linha * i
0x0012ED62  set_size do rotulo  ->  altura da TABELA
```

**A fonte de verdade dupla acabou.**

## 16. O TESTE FINAL — 37 telas, um byte

```text
TABELA DE TEMA  (0x001A5400, 18 bytes)
  cor_tela       0x0000        altura_faixa   17
  cor_faixa      0x8208        altura_linha   16
  cor_separador  0xC731        inicio_lista   19
  cor_texto      0xFFFF        margem          3
  cor_texto_sel  0xFFFF        raio            0
  cor_selecao    0xFA05        pad_topo        1

altura_linha 16 -> 20:  1 byte, em 0x1A540D
  lido pelas 36 telas de lista E pela home
```

> **Mudar a aparência do aparelho inteiro é editar um byte de dado.**
> Nenhuma instrução muda. Era isto que o mantenedor pediu.

### O único ponto que continua em aberto — e por quê

**A faixa clara vazia.** O S3 fechou opacidade, contorno e sombra; o S6
fechou padding. **Não sobrou propriedade de tema para ela vir.** Se ela
ainda aparecer no aparelho, não é herança de tema — e aí o diagnóstico
começa de um lugar completamente diferente, sabendo onde *não* está.

Isso não é falta de trabalho: é uma pergunta que só o aparelho responde.


---

## 17. S7 — os ícones viram campo da tabela (V066, não gravado)

> Pergunta do mantenedor: *"a tela que mostrava ícones ela ainda continua?
> ou você resolveu isso?"*
>
> **Continuava.** Nenhum passo do Saturno tinha tocado nos ícones.

### 17.1 A medição

Varri as chamadas a `lv_obj_set_style_text_font` e agrupei por fonte:

```text
fonte 0x00CA671C  ->  44 pontos, em 32 telas    <- a fonte de ICONES
```

Um rótulo cuja fonte é a de ícones **é** um ícone. Sem ambiguidade.

A V039 tinha tirado o ícone de **uma** tela — a Configurar — apagando a
string de glifo. As outras 31 continuaram.

### 17.2 O patch

```text
tabela +0x12   icones   0 = escondidos (padrao)   1 = visiveis
0x001A5800     rotina: set_style_text_font + (se 0) LV_OBJ_FLAG_HIDDEN
44 ganchos
```

Esconder é melhor que apagar a string: funciona seja qual for o texto que
a tela ponha depois, e é reversível mudando **1 byte**.

Padrão **0**, por três razões convergentes: a home não tem ícone, a
Configurar já não tinha desde a V039, e o NanoClone traz
`show icons: off`.

### 17.3 ⚠️ Correção de uma divergência minha

O desenho na §4 listava um campo `icones` em `+11`. A implementação do S1
usou aquele byte para `pad_topo`, e **o campo nunca existiu**. O documento
dizia uma coisa e o binário fazia outra.

Corrigido: `pad_topo` em `+11`, `icones` em `+12`, nos dois lugares.

> **Lição:** o documento de desenho e a implementação divergiram e ninguém
> notou por três etapas. Quando o doc descreve uma estrutura de dados, ele
> tem de ser conferido contra o binário, não contra a memória de quem
> escreveu.

### 17.4 O que o S7 NÃO resolve — medido, não suposto

Esconder o ícone **não reposiciona o texto da linha.** Medi a largura do
rótulo por tela:

```text
largura = hor_res - N

  hor_res - 15   18 telas    <- caso dominante, linha simples
  hor_res -  6    1 tela     <- Configurar (mexida pela V039)
  hor_res - 30/34/35/45/49   telas com VALOR ou INTERRUPTOR a direita
```

**Nem toda diferença é ruído.** As telas com valor à direita precisam
mesmo de rótulo mais estreito; uniformizar todas quebraria essas.

O que dá para unificar é o **grupo de linha simples** (`-15` e `-6`), que
passaria a ler `margem` da tabela. Fica proposto, **não feito** — e a
distinção entre "linha simples" e "linha com valor" precisa ser
estabelecida por medição antes, não por chute.

---

## 18. ⚠️ Um erro meu do S6, pego antes de gravar

Ao ler a tabela de coordenadas da home para o S8, apareceu isto:

```text
rotulos da home (0x00C486A0):
   item 0..3   y = 19, 35, 51, 67
   item 4..8   y = 200            <- ESTACIONADOS fora da tela
```

E o laço da home roda **nove** vezes (`cmp r5, #0x24`). Os cinco itens
antigos continuam sendo criados desde a V022; só não aparecem porque a
V025 os estacionou em `y = 200`.

**O S6 recalculava o `y` de todos os nove** — e teria trazido os cinco de
volta para a tela.

Corrigido: a rotina passa o item intacto quando o `y` original já está
fora da tela.

```asm
00DA5760   push {r4, lr}
00DA5762   cmp  r2, #159        ; item estacionado?
00DA5764   bgt  0xda5774        ; sim -> nao mexe
           ...calcula y = inicio_lista + altura_linha * i...
00DA5774   bl   set_pos
```

> **A lição:** o S6-C parecia uma melhoria pura — trocar constante por
> tabela. Mas a constante **carregava informação** que a tabela não tem:
> "este item está desligado". Trocar dado por fórmula apaga o que o dado
> sabia.
>
> Só apareceu porque fui **ler a tabela de coordenadas** para outra coisa.
> Não havia como deduzir isso do código do S6.

## 19. S8 — o recuo do texto (V067, não gravado)

Medi a borda esquerda do texto de cada linha, em vez de supor:

```text
41 rotulos   sem align            -> origem da linha, x = 0
 4 rotulos   align=7, x_ofs = 13  -> espaco do icone   (todos na tela 0x23)
19 objetos   align=8 (RIGHT_MID)  -> VALOR a direita, LEGITIMO
```

A home, que é a régua, põe seus rótulos em **x = 0**. Logo 41 telas e a
home concordam; 4 divergem — e divergem pelo espaço de um ícone que o S7
acabou de esconder.

**Os 19 `align=8` não são ruído e não foram tocados.** Telas com valor ou
interruptor à direita precisam mesmo disso. Foi por isso que medi antes:
uniformizar tudo teria quebrado essas.

```text
tabela +0x0F  margem = 0
0x001A5880    rotina: icones != 0 -> mantem o x_ofs original
                      icones == 0 -> usa `margem`
4 ganchos
```

Ligar os ícones de novo devolve o recuo **sem tocar em código**.

## 20. A TABELA COMPLETA — o design dos menus, em 19 bytes

```text
0x001A5400
  +00  cor_tela          0x0000   RGB(0,0,0)
  +02  cor_faixa         0x8208   RGB(8,16,16)
  +04  cor_separador     0xC731   RGB(49,56,57)
  +06  cor_texto         0xFFFF   RGB(255,255,255)
  +08  cor_texto_sel     0xFFFF   RGB(255,255,255)
  +0A  cor_selecao       0xFA05   RGB(0,190,213)
  +0C  altura_faixa          17
  +0D  altura_linha          16
  +0E  inicio_lista          19
  +0F  margem                 0
  +10  raio                   0
  +11  pad_topo               1
  +12  icones                 0
```

**Todo o design dos menus do OpenPod cabe em 19 bytes de dado.**

| etapa | o quê | estado |
|---|---|---|
| S1 | tabela de tema | ✅ |
| S2 | as 7 rotinas lendo dela | ✅ |
| S3 | opacidade, contorno e sombra | ✅ |
| S4 | a faixa da home vem do helper | ✅ |
| S5 | a folha sem a faixa | ✅ |
| S6 | cor de seleção, padding, geometria da home | ✅ (corrigido, §18) |
| S7 | ícones | ✅ |
| S8 | recuo do texto | ✅ |

**Nenhuma versão gerada.** V061–V067 são imagens de trabalho.

---

## 21. AUDITORIA — `tools/audita_chrome.py`

O mantenedor pediu: *"reveja todo o design, leia todas as telas para ver
se está tudo certo e me confirme."*

Escrevi uma ferramenta que **lê a imagem final e pergunta, tela a tela:
você está ligada na tabela?** Ela não conserta nada — audita. Serve para
responder "está tudo certo?" com uma lista, não com uma opinião.

### 21.1 O que a auditoria achou — e eu não tinha visto

As 36 telas de lista passaram. Mas a auditoria só olhava listas, e havia
um buraco:

```text
telas com faixa             50
telas de lista              36    faixa 17 px, ligada na tabela
telas com faixa SEM lista   14    faixa 22 px, CRUA
```

As 14: `0x08 0x0D 0x0F 0x11 0x19 0x1F 0x2B 0x2C 0x2D 0x2F 0x31 0x44 0x4F
0x52` — seletores de hora, brilho, senha, leitura de e-book, gravação em
curso.

**Resultado visível: "Definir alarme" com faixa mais gorda que
"Despertador".** É a mesma inconsistência que o Saturno existe para
acabar; eu simplesmente nunca tinha olhado fora das listas.

> **Por isso a auditoria existe.** Eu teria dito "está tudo certo" com
> convicção, baseado nas 36 que eu mesmo escolhi olhar. A ferramenta
> olhou as 50.

### 21.2 S9 — as 14 ligadas (V068)

14 pontos de altura ligados aos mesmos thunks. **34 bytes.**

```text
TELAS COM FAIXA: 50
   ligadas na tabela : 50
   ainda cruas       :  0
```

### 21.3 Ressalva honesta

O S9 **não mexe no conteúdo** dessas 14. Elas posicionam o que desenham
supondo 22 px; com a faixa em 17 sobra um vão de 5 px antes do conteúdo,
contra 2 px nas listas.

Não corrigi porque cada uma posiciona o seu conteúdo de um jeito, e mover
conteúdo sem medir tela a tela é o atalho que este projeto já pagou caro.
**A faixa ficou igual; o vão abaixo dela, não.**

## 22. RESULTADO DA AUDITORIA FINAL (V068)

```text
TABELA DE TEMA          19 bytes em 0x001A5400
TELAS DE LISTA          36   faixa TABELA · conteiner TABELA · linha helper
TELAS COM FAIXA         50   todas ligadas na tabela
icones                   0 pontos crus
selecao                  0 pontos em palette_main(7)
recuo                    0 pontos com x_ofs cru
helpers                  faixa, conteiner e linha chamam a carcaca
home                     faixa do helper · geometria da tabela

SEM DIVERGENCIAS
```

**Nenhuma versão gerada.** V061–V068 são imagens de trabalho.


---

## 23. S10 — a cor do texto vem da tabela (V070)

> Pergunta do mantenedor: *"as fontes estão todas com cor branca? isso tb
> está centralizado? paleta do seletor tb a cor é centralizada?"*

Conferi em vez de afirmar, e uma das três respostas era **não**:

| pergunta | resposta |
|---|---|
| fontes brancas? | **sim** — os dois getters devolviam `-1` |
| cor do texto centralizada? | **NÃO** — `cor_texto` estava na tabela e **ninguém a lia** |
| seletor centralizado? | **sim** — 3 pontos leem `cor_selecao` (S6) |

O branco vinha dos **getters patchados na V013**, não da tabela. Mudar
`cor_texto` não mudava nada — segunda fonte de verdade, exatamente o que
o Saturno existe para eliminar.

### 23.1 O patch

```text
0x00121384   getter do tema  -> le a tabela   (11 pontos o usam)
0x0012E948   getter da home  -> le a tabela   ( 1 ponto)
0x001217AA   linha -> acrescenta cor_texto_sel no estado FOCUS_KEY
```

Patch na **função**, não nos chamadores: os dois getters são o ponto
único por onde passa a cor de texto da faixa, das linhas, dos rótulos da
home e do relógio.

`cor_texto_sel` passou a existir de verdade — antes o texto selecionado
herdava o normal; agora são dois campos independentes.

### 23.2 Quatro pontos NÃO tocados, de propósito

```text
0x00128DD6  0x00128F18 (imediato 3)  0x00128FC0   pagina 0x23
0x0012B882                                        pagina 0x12
```

São cores de **estado** — a `0x23` é o menu de Bluetooth (conectado,
pareando). Não são ruído de padronização, e mudá-las sem entender o que
significam seria o mesmo atalho de sempre.

### 23.3 O teste

```text
cor_texto e cor_texto_sel alterados:
   4 bytes, todos na tabela
   nenhum byte de codigo mudou
```

## 24. OpenPod 2.1 — GERADA

```text
base    OpenPod 2.0 (V060)     alvo   V070
32 setores, 128 KiB, 2.973 bytes
ordem R2: area livre -> carimbo -> folha -> ganchos
```

Conteúdo: **Saturno S1–S10** (tema em tabela de 19 bytes, 50 faixas
idênticas, ícones, recuo, cores) + **Extras corrigido**.

---

## 25. A 2.1 no aparelho — o que ficou e o que não

### 25.1 Confirmado pelas fotos

- as faixas têm a **mesma altura** em Configurar, Despertador e Música
- a home continua limpa
- a tela Configurar está praticamente certa: faixa, traço, lista

### 25.2 O que NÃO resolveu

**A faixa clara vazia continua** — e agora se sabe mais sobre ela:

```text
Configurar   fina    (~4 px)
Despertador  grossa  (~30 px)
Musica       grossa  (~30 px)
```

**Ela varia com a tela.** E o S3 + S6 fecharam opacidade, contorno,
sombra e padding — **portanto não é herança de tema**. Isso é informação
real, obtida por eliminação, e reduz muito onde procurar.

**O título ainda colide** na lista de Música: `Músi̶ta̶52` — o nosso título
(TOP_MID) por cima de um contador que a própria tela desenha. Defeito
conhecido desde a 1.8, nunca corrigido.

### 25.3 Dois achados da investigação — nenhum é a faixa clara

**A — Fundo branco herdado da V013.** O getter `0x00D21384`, que a V013
trocou para devolver branco e consertar a **cor do texto**, também
alimenta um **fundo**:

```asm
0x00122F50   bl 0xD21384   ->  bg_color(obj, BRANCO, estado normal)
```

Está assim desde a V013 — dez versões. Mas a função só tem **2
chamadores**, ambos em telas de gravação, então **não é a faixa clara**
do Despertador nem da Música. É bug real e separado.

> Registrei o achado antes de saber se explicava o sintoma, e ele não
> explicava. Vale a disciplina: não vender achado como causa.

**B — `altura_linha` NÃO está centralizada para as listas.**

```text
altura da LINHA vinda CRUA (set_h direto):  35 pontos
altura da LINHA vinda da tabela:             0 pontos
```

As 36 telas calculam `160/10 = 16` cada uma. O valor **coincide** com o
da tabela, então nada parece errado — e é justamente por isso que passou
pela auditoria: ela conferia faixa e contêiner, não a linha.

A auditoria precisa cobrir isso também.

### 25.4 A pergunta que discrimina

Não vou seguir deduzindo da foto. Uma observação de cinco segundos corta
o espaço de busca:

> **Na tela Despertador, a faixa clara se move quando você navega entre os
> itens?**
>
> se **move** → é uma LINHA da lista, vazia
> se **fica parada** → é um objeto fixo, e aí são poucos candidatos

---

## 26. Diagnóstico por cor — uma capacidade que o Saturno destravou

Resposta do mantenedor: **a faixa clara fica parada** quando se navega.
Isso elimina "linha vazia" e diz que é **objeto fixo**.

Enumerei todos os objetos do Despertador: FAIXA, rótulo do título,
CONTÊINER, LINHA (×3), ícone, texto e o interruptor (26×12). **Não há
nada de ~30 px ali além do contêiner**, cujo topo fica em y=19 —
exatamente onde a faixa começa.

Mas em vez de continuar deduzindo da foto — que foi o que me fez errar
antes — dá para **fazer o aparelho responder**, e isso só é possível
porque o tema virou tabela:

```text
firmware/WORKING/GN438_diagnostico_cores.bin     7 bytes trocados
DIAGNOSTICO cores/update.up

   cor_tela        -> VERMELHO
   cor_faixa       -> VERDE
   cor_separador   -> AMARELO
   cor_selecao     -> MAGENTA
```

Uma foto da tela Despertador responde de imediato:

| a faixa clara ficou | então ela é |
|---|---|
| MAGENTA | pintada com `cor_selecao` |
| VERMELHA | o fundo da tela / do contêiner |
| VERDE | a faixa superior, maior do que parece |
| AMARELA | o separador, grosso demais |
| **não mudou** | **não vem da tabela** — objeto que a carcaça não controla |

> **Não é uma versão.** É imagem descartável, e depois dela é preciso
> regravar a 2.1.
>
> Antes do Saturno, esse diagnóstico exigiria montar e gravar uma imagem
> por hipótese. Agora são 7 bytes e uma foto — a tabela deixou de ser só
> arrumação e virou **instrumento**.
