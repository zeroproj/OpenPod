# O alvo do produto — `marte/mockups/marte_completo.png`

> Definido pelo mantenedor em 2026-09-14: *"lá tem o marte completo, como
> nosso produto deve ficar"*.
>
> **Esta imagem é a especificação visual do OpenPod.** Quando houver
> dúvida sobre aparência, ela decide. O `OpenPod_Design_System.md`
> continua valendo como filosofia; o mockup é o alvo concreto.

---

## 0. A REGRA — decidida pelo mantenedor em 2026-09-14

> *"Sempre usar o Marte como referência, ou usar os próprios objetos
> deles."*

Toda decisão visual do OpenPod se resolve por uma destas duas vias, nesta
ordem:

1. **A referência** — `marte/mockups/marte_completo.png` e o
   `marte/paleta/nanoclone.json`. Medida, não impressão.
2. **Os próprios objetos do NanoClone** — `marte/adaptado/`, já cortados
   na nossa medida, e `marte/referencia/` com os 16 bitmaps originais.

**Não inventar.** Se uma cor, uma altura, um espaçamento ou um ícone não
estiver na referência nem nos ativos, a pergunta é *"o que o nano faz
aqui?"* — e a resposta se procura no material, não se decide por gosto.

### Por que a regra existe

Este projeto já gastou versão inventando aparência. A referência elimina
a classe inteira de discussão: em vez de *"ficou bom?"*, a pergunta vira
*"bate com o alvo?"* — que tem resposta objetiva.

E tem um efeito colateral que já apareceu: ao comparar com o mockup,
**dois erros meus caíram no mesmo dia** (o uso errado de `cor_separador`
e a suposição de que o degradê dependia de `BG_GRAD`). A referência não
só orienta — ela **corrige**.

### O que a regra obriga

- Usar os pixels do NanoClone implica **CC BY-SA 3.0**: crédito a Billy
  Blair, indicação de alteração, e share-alike nos derivados. Está em
  `ATRIBUICAO.md`, e **falta pôr na tela Sobre** quando o primeiro
  bitpixel dele entrar no firmware.
- Onde o hardware não permitir seguir a referência, o desvio é
  **registrado com o motivo** — não silencioso.

---

## 0-bis. O TEMA CLARO NÃO SERVE NESTE PAINEL — 2026-09-14

**Decisão do mantenedor, e não é preferência: é limitação de hardware
medida.**

Com o tema claro, aparecem **faixas horizontais** na área de conteúdo,
visíveis a olho nu — não é artefato de foto. A causa foi isolada por
eliminação, um variável por vez (trabalho feito em paralelo, em
`OpenPod GPT/`):

```
BG_GRAD = 0 nas linhas normais   ->  faixas IGUAIS
                                     o degrade herdado do tema: DESCARTADO

cores chapadas inconfundiveis    ->  linhas vermelhas, e as faixas
                                     PERSISTIRAM DENTRO DO VERMELHO
                                     composicao LVGL e tabela: DESCARTADAS
```

Sobra o **caminho global de exibição** — driver, controlador ou o próprio
painel. As faixas aparecem sobre fundo claro e somem sobre escuro.

### Consequência para a regra §0

A referência diz **claro**; o painel diz **escuro**. Pela própria regra,
o desvio fica registrado com o motivo:

> **O OpenPod segue o Marte em tudo — geometria, ausência de traço entre
> itens, ausência de ícones de linha, barra de seleção de borda a borda,
> tipografia — EXCETO na luminância, que é invertida: fundo preto, texto
> branco.**

Não é escolha estética e **não deve ser revisitada** sem que alguém
primeiro resolva as faixas no nível do driver do LCD.

### O que NÃO fazer

**Nenhum patch de estilo para esse defeito.** Cor, opacidade, borda,
degradê e geometria já foram eliminados por experimento. O próximo
estudo, se algum dia for autorizado, é do **driver/gamma do LCD** — outra
camada, outro projeto.

---

## 1. O que o alvo tem, item a item

```
faixa superior    degrade vertical claro, 17 px, + 1 px de separador escuro
titulo            "Menu", CENTRALIZADO, texto escuro
bateria           icone COLORIDO (verde), a direita da faixa
lista             fundo BRANCO, texto PRETO, alinhado a esquerda
selecao           barra AZUL EM DEGRADE, de borda a borda, texto BRANCO
separadores       NAO EXISTEM entre os itens
icones de linha   NAO EXISTEM
barra de rolagem  NAO EXISTE
area vazia        branca, igual ao resto da lista
```

---

## 2. 🎯 A DISTÂNCIA ATÉ O ALVO — a tabela de trabalho

> **Refeita em 2026-09-14, contra a OpenPod Core 1.0.1.**
>
> A versão anterior desta seção comparava o alvo com a **Core 2.1.1** e
> dizia "seis de seis cores exatas". **Aquela linha foi apagada no mesmo
> dia** (ver `ESTADO_ATUAL.md` §3). Comparar com ela induziria ao erro que
> a limpeza existe para acabar. A tabela abaixo é contra o que está **no
> aparelho**.

Cada linha carrega classe de confiança, conforme a regra §7 do
`CLAUDE.md`. `CONFIRMADO` quer dizer evidência direta, citada.

| # | item do alvo | Marte quer | Core 1.0.1 tem | classe | custo |
|---|---|---|---|---|---|
| ~~**M-a**~~ | separador entre itens | **não existe** | ✅ **FEITO — Core 1.1** | **VISTO NA TELA** | 1 byte |
| **M-b** | home | **lista** | grade 3×3 de fábrica | **CONFIRMADO** | código novo |
| **M-c** | título na faixa | "Menu", centralizado | faixa vazia, só a bateria | **VISTO NA TELA** | rotina + tabela |
| ~~**M-d**~~ | barra de rolagem | **não existe** | ✅ **FEITO — Core 1.3** | — | **1 byte** |
| **M-e** | ícones de linha | **não existem** | existem (engrenagens) | **VISTO NA TELA** | ⚠️ **SEM PORTÃO** — 37 pontos ou gancho (§2-ter) |
| ~~**M-f**~~ cor | seleção | AZUL RGB(41,101,222) | ✅ **FEITO — Core 1.2**, 2 bytes | **PROVADO POR DIAGNÓSTICO** | falta só o degradê (= M-h) |
| **M-g** | bateria | ícone colorido | glifo monocromático | PROVÁVEL | bitmap + M4 |
| **M-h** | degradê da faixa | 19 linhas, `nanoclone.json` | faixa lisa | **CONFIRMADO** | rotina nova |
| **M-i** | cores dos 6 campos | ver `nanoclone.json` | tema de fábrica | **A MEDIR** | — |
| **M-j** | luminância | claro | escuro | **DESVIO ACEITO** | — não fazer |

### ✅ M-a — FEITO, e confirmado na tela em 2026-09-14

Gravada como **OpenPod Core 1.1**, pelo cartão. Foto do aparelho, tela
Configurar: os seis itens sem traço entre eles.

**E a distinção que eu já havia errado antes ficou provada na prática:**
o traço de 1 px **embaixo da faixa** CONTINUA lá, como o alvo pede. São
objetos diferentes — borda da FAIXA fica, borda da LINHA sai.

> **A tese da carcaça está provada em hardware.** Um byte dentro de
> `CRIA_LINHA` mudou a tela. Não é mais dedução: é observação.

### O que a mesma foto mediu, de graça

| item | o que a tela mostra |
|---|---|
| **M-f** | a seleção **já é de borda a borda** — a geometria está certa. Falta a COR: está **ciano chapado**, `palette_main(7)` = RGB(0,190,213). O alvo é **azul** RGB(41,101,222), em degradê |
| **M-d** | a barra de rolagem aparece, fina, à direita da lista |
| **M-e** | os ícones de engrenagem estão em toda linha. O nano não tem ícone de linha |
| **M-c** | a faixa está vazia — só a bateria, à direita. Sem título |
| **M-j** | tema escuro, como decidido. Sem faixas horizontais — o painel se comporta |

---

## 2-bis. ⚠️ OS CUSTOS DE M-d, M-e E M-f ESTAVAM ERRADOS — medido em 2026-09-14

> A coluna "custo" da tabela herdou estimativas da **linha 2.x**, quando
> existia infraestrutura de gancho na área livre. Ela foi removida na
> limpeza. Medido sobre o firmware **de fábrica**, os três custam mais.
>
> Registrado aqui em vez de corrigido em silêncio, porque muda a decisão.

### ✅ M-d — RESOLVIDO em 1 byte. Core 1.3

**Eu havia dito que este item exigia gancho na área livre. Errado de
novo — e pelo mesmo vício: parei de procurar cedo demais.**

O que estava certo: `CRIA_CONTEINER` (`0x00D21690`) termina em
`0x00D215FA` e `0x00D215E0`, que são **setters de padding**, não de
rolagem. Ninguém *configura* a barra.

O que eu não vi: ela não é configurada porque é **desenhada** pelo
tratador de evento compartilhado do `lv_obj`, no evento
`LV_EVENT_DRAW_POST` (24 = `0x18`) — como na LVGL v8:

```c
else if(code == LV_EVENT_DRAW_POST) {
    draw_scrollbar(obj, draw_ctx);
}
```

No binário:

```
00D4967E  182f      cmp   r7, #0x18     <- o evento
00D49680  7ff46cae  bne.w 0xD4935C      <- nao e? RETORNA (epilogo)
00D49684  ...                           <- e? desenha a barra
```

`0xD4935C` é o **epílogo** (`add sp,#0x48; pop {...,pc}`), e todas as
leituras de estilo do bloco são de `LV_PART_SCROLLBAR`.

**O conserto:**

```
0x0014967E   18 -> FF     cmp r7,#0x18  ->  cmp r7,#0xFF
```

Códigos de evento vão até ~35; `r7` nunca vale `0xFF`. O desvio passa a
ser sempre tomado. **Para todos os outros eventos o comportamento é
idêntico** — o desvio já era tomado antes.

A rolagem continua funcionando; some só o indicador.

### M-e — procurei o portão e ele NÃO existe. Medido.

Depois que o M-f (2 bytes numa tabela) e o M-d (1 byte num comparador)
desmentiram minhas estimativas de "precisa de gancho", procurei o mesmo
tipo de ponto único aqui. **Não há.** E isso é resultado, não desistência.

**Candidato 1 — a fonte de ícones.** `0x00CA671C` aparece em 38 pools
literais, espalhados por **37 funções distintas**: uma por página. Não
existe helper compartilhado que atribua a fonte.

**Candidato 2 — as strings de glifo.** São glifos **diferentes** por
página: engrenagem `U+F013` no Configurar, e `U+F130` microfone,
`U+F04A/4C/4E` mídia, `U+F028` volume, `U+F294` bluetooth. Apagar todas
mataria os ícones de mídia, que **o Marte quer**.

**Candidato 3 — um glifo compartilhado.** `U+F0C9` (`0x00CD3261`) tem 38
referências, o mesmo número da fonte — parecia promissor. Medido:

```
funcoes que citam a FONTE de icones : 37
funcoes que citam U+F0C9            : 37
interseccao                         : 21     <- so 21 das 37
```

Apagar `U+F0C9` removeria ícone de **21 telas** e deixaria **16** com
ícone. Inconsistente, e pior do que não fazer.

**Candidato 4 — `0x00D51704`**, chamado por linha (40 chamadas, contra
39 de `CRIA_LINHA`). É compartilhado, mas recebe **a linha**, não o
ícone. Esconder um filho dali exige código novo.

### Conclusão honesta

**M-e custa 37 pontos, ou um gancho.** Diferente do M-f e do M-d, aqui a
busca pelo portão foi feita e deu negativo — o firmware simplesmente não
centraliza esta decisão.

### ✅ M-f (a cor) — RESOLVIDO em 2 bytes. Core 1.2

**Eu havia declarado este item "origem não localizada". Estava errado, e
por um erro de raciocínio que vale registrar.**

Eliminei candidatos e, ao ver que `palette_main(7)` (CYAN) tinha **uma
única** chamada, concluí que *"mexer na tabela de paletas não muda a
seleção"*. Generalizei do índice 7 para a tabela inteira. O índice **5**
(BLUE) é chamado **12 vezes**.

Também errei a cor: pela foto eu li "ciano". O mantenedor corrigiu —
*"eu vejo azul"* — e a medição do decil menos estourado da foto,
`RGB(53,163,240)`, bate com o BLUE da paleta `RGB(32,149,246)`, não com
o CYAN `RGB(0,190,213)`.

**Quem pinta a seleção:**

```
0x00D219D4   helper COMPARTILHADO, 10 chamadores
             um deles, 0x00D3AA94, esta DENTRO do Configurar
             pinta bg_color no estado FOCUS_KEY com palette_main(5)
             nos pontos 0x00D21B08 e 0x00D21B92
```

**O conserto — 2 bytes, na tabela, não em código:**

```
0x000DF082   24 BE  ->  2B 3B     paleta[5] = LV_PALETTE_BLUE

  0xBE24 invertido = 0x24BE = RGB( 32,149,246)   Material da LVGL
  0x3B2B invertido = 0x2B3B = RGB( 41,101,222)   Marte, selecao_base
```

**Alcance medido** — os 12 pontos que usam paleta[5]:

```
9x  bg_color estado FOCUS_KEY   <- as barras de selecao
1x  bg_color estado CHECKED
1x  bg_color estado normal
1x  consumidor nao identificado
```

Os três últimos passam a usar o **mesmo** azul. É consistência, não
regressão.

> **Falta o degradê.** O alvo pede `selecao_topo` RGB(99,156,227) →
> `selecao_base` RGB(41,101,222). A Core 1.2 entrega o tom de baixo,
> chapado. O degradê é o M-h, e é rotina nova.

### Como isto foi PROVADO — e os dois erros meus no caminho

A Core 1.2 foi gravada e a tela pareceu não mudar. Daí vieram dois
enganos meus, em sequência:

**Erro 1 — identifiquei a função errada.** Apontei `0x00D219D4` como
"pintor de seleção compartilhado". Ela é `view_mbox_create` — o nome
está no próprio log de erro dela. Cria **caixas de mensagem**.

**Erro 2, e foi o pior — a super-correção.** Do erro 1 eu concluí que
`paleta[5]` não governava a seleção, e cheguei a dizer que a Core 1.2
não tinha efeito. **Errado.** `view_mbox_create` é mesmo um criador de
caixas, mas a seleção é pintada por **outro** dos pontos que usam
`paleta[5]` — e paleta[5] governa a barra, sim.

**O diagnóstico que encerrou a discussão:** `paleta[5]` → vermelho puro
(`0xF800`), gravado no aparelho. **A barra ficou vermelha.**

```
foto medida: 21.016 pixels vermelhos, RGB(227,123,101)
```

> **A lição de método, e ela custou duas gravações:** eu tratei foto
> sobre-exposta como medida, duas vezes. Uma diferença sutil de cor não
> se julga por foto — **cor inconfundível resolve em uma gravação** o que
> a discussão não resolvia. Era o método que este projeto já tinha usado
> em `§0-bis`, e eu demorei a lembrar.
>
> E: quando o aparelho contraria a previsão, a primeira hipótese a
> testar é **erro meu**, não defeito de hardware. O mantenedor chegou a
> suspeitar do LCD por causa da minha confusão.

### O que isso significa para a ordem de trabalho

Os três pedem **código na área livre com gancho** — que é exatamente a
infraestrutura que a linha 2.x tinha e que foi removida por acoplar tudo.

**Reconstruí-la é decisão do mantenedor, não minha.** Se for reconstruída,
a regra é: **um gancho por item, independente**, nunca um pré-requisito
de outro. Foi o encadeamento que matou a 2.x, não o gancho em si.

---

### A evidência de cada CONFIRMADO

**M-a — o separador.** Desmontado no ORIGINAL, dentro de `CRIA_LINHA`
(`0x00D21764`, usada por **39 telas**):

```
00D2179E  0121      movs  r1, #1        <- a LARGURA da borda
00D217A0  2bf0a8fc  bl    0xD4D0F4      <- set_style_border_width (prop 50)
00D217A4  2046      mov   r0, r4
00D217A6  0022      movs  r2, #0
00D217A8  0121      movs  r1, #1
00D217AA  2bf0a9fc  bl    0xD4D100      <- set_style_border_side  (prop 51)
```

Patch: arquivo `0x0012179E`, `01` → `00`.

> ⚠️ **Não confundir com o traço da faixa.** O `faixa_separador` do
> `nanoclone.json` (y=17) é a borda da **FAIXA** e **FICA**. São objetos
> diferentes. Este item mexe só na borda da **LINHA**.

**M-b — a home é grade.** Declarado no relatório da versão: *"Consequência
aceita: a Core 1.0 tem a home em grade 3×3 de fábrica."*
(`docs/releases/OpenPod_Core_1.0.1.md`). O laço que a desenha está
decodificado em `GUI_ANALYSIS.md` PARTE IV §20.

**M-c, M-d, M-e — por construção.** As ferramentas que produziam título
(`patch_titulos`), escondiam a rolagem (`patch_scrollbar3`) e tiravam os
ícones de linha (Saturno S7) foram **removidas** em 14/09. Logo o
firmware voltou ao comportamento de fábrica nesses três pontos. O molde
de fábrica em `page_home_menu_event_cb` mostra o ícone sendo criado
explicitamente (`GUI_ANALYSIS.md` PARTE IV §21), o que confirma M-e.

**M-h — a faixa é lisa.** O degradê nunca esteve no firmware de fábrica;
veio do `nanoclone.json`, linha a linha, e dos pixels já cortados em
`marte/adaptado/faixa_128x18.png`.

**M-j — o desvio.** Registrado em §0-bis: as faixas horizontais do tema
claro são do **painel**, isoladas por eliminação. **Não revisitar** sem
antes resolver no nível do driver do LCD.

---

## 3. Ordem de trabalho — e por que esta ordem

> A ordem sugerida antes (a→e) foi escrita quando existia a tabela de tema
> do Saturno. **Ela não vale mais**: três daqueles passos eram baratos
> *porque* a infraestrutura existia, e ela foi removida. Esta é a ordem
> refeita sobre o que o firmware de fábrica oferece.

| passo | item | por que agora | custo |
|---|---|---|---|
| **1** | **M-a** separador | único item do alvo que mexe em código **de fábrica** — não dependia de nada que foi apagado. Verificável na tela em segundos | **1 byte** |
| **2** | **M-d** + **M-e** rolagem e ícones de linha | mesma classe: tirar coisa, não criar. Um ponto cada | 2 pontos |
| **3** | **M-f** + **M-i** medir a seleção e as 6 cores de fábrica | não dá para mirar sem saber de onde se parte. É medição, não patch | — |
| **4** | **M-b** a home vira lista | **o marco de verdade** — é o que faz o aparelho *parecer* o Marte | código novo |
| **5** | **M-c** título na faixa | depende da faixa estar resolvida | rotina + tabela |
| **6** | **M-h** degradê | deixou de ser aposta: as 19 cores e os pixels já existem | rotina nova |
| **7** | **M-g** bateria colorida | primeiro pixel do NanoClone no firmware → **obriga o crédito na tela Sobre** | bitmap |

### O passo 4 tem molde pronto — e um pré-requisito medido

**A carcaça existe no firmware de fábrica**, e Configurar já a usa:
`CRIA_FAIXA` (52 chamadas), `CRIA_CONTEINER` (59) e `CRIA_LINHA` (39).
A home não usa nenhuma das três. O molde inteiro, decodificado, está em
**`docs/CARCACA_PADRAO.md`**.

⚠️ **Pré-requisito:** adotar o molde na home exige um **terceiro array de
ponteiros** (a linha também é guardada), o que muda a alocação de
`page_home_create` — `movs r0,#0x54` em `0x00D2EBBC`. É risco localizado
e barato (dois imediatos), **mas os 12 bytes restantes da estrutura
precisam ser mapeados antes**. Ver `CARCACA_PADRAO.md` §4.

### A regra que vale para todos os passos

**Um passo por vez, gravado e visto na tela, sem nada de carona.** Se um
passo parecer exigir outro, isso é dito e o mantenedor decide — não se
empacota os dois. Ver `ESTADO_ATUAL.md` §3.

---

## 4. Correções que este documento faz a estudos anteriores

1. **`cor_separador` não é o traço entre as linhas.** É o traço de 1 px
   embaixo da faixa (`y=17` no JSON). O traço entre linhas vem de
   `palette_main(0x12)` e não tem campo na tabela.
2. **O degradê não depende de `BG_GRAD`** (§4.1 do estudo). O JSON traz
   as cores linha a linha e o `adaptado/` traz os pixels prontos.
3. **O alvo do produto é `marte_completo.png`**, e não a descrição em
   prosa espalhada pelos documentos.
4. **A comparação "seis de seis cores exatas" era contra a Core 2.1.1**,
   removida em 2026-09-14. A §2 agora compara com a **Core 1.0.1**, que é
   o que está no aparelho. Nenhuma afirmação sobre distância até o alvo
   deve citar uma versão que não existe.
