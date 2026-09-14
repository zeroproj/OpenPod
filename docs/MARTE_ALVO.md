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
| **M-d** | barra de rolagem | **não existe** | existe, à direita | **VISTO NA TELA** | ⚠️ gancho (§2-bis) |
| **M-e** | ícones de linha | **não existem** | existem (engrenagens) | **VISTO NA TELA** | ⚠️ 38 pontos ou gancho |
| **M-f** | seleção | degradê **AZUL** RGB(41,101,222) = RGB565 `0x2B3B` | **CIANO chapado**, já de borda a borda | **VISTO NA TELA** | ⚠️ origem NÃO LOCALIZADA (§2-bis) |
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

### M-d — a barra de rolagem NÃO é configurada pelo firmware

`CRIA_CONTEINER` (`0x00D21690`) termina chamando `0x00D215FA` e
`0x00D215E0` — desmontados: são **setters de padding**
(`0xD4D01C/028/034/040/04C/058`), não de rolagem.

**Ninguém desliga a barra.** Ela é o padrão da LVGL (`AUTO`). Existem 14
pontos que usam `LV_PART_SCROLLBAR` (`0x010000`), mas são páginas
individuais, não a carcaça.

Para as 59 telas de contêiner, isso exige **inserir uma chamada** em
`CRIA_CONTEINER` — e a função é justa, sem espaço. Ou seja: **gancho para
uma rotina na área livre.**

### M-e — a fonte de ícones é referenciada em 38 pontos

```
0x00CA671C  em pool literal:  38 pontos
```

Não é "um ponto". Ou se mexe em 38, ou se cria um gancho.

### M-f — a origem do ciano NÃO foi localizada

Eliminados, por medição:

```
tabela de paletas 0x00CDF078   UNICO leitor e a propria palette_main
palette_main(7) = CYAN         chamada UMA vez, e e a pagina 0x18
CRIA_LINHA                     nao seta cor de estado nenhum
0xD51704 / 0xD516B4            setters de geometria, nao de cor
os 22 bg_color com estado      FOCUS_KEY/CHECKED, nenhum na carcaca
```

**Conclusão: o ciano vem do tema interno da LVGL**, aplicado por classe
de objeto, não por chamada explícita do firmware. Achá-lo é engenharia
reversa do tema — trabalho de verdade, não um patch.

> **Alvo, para quando for atacado:** azul do Marte RGB(41,101,222) =
> RGB565 `0x2B3B`, pré-invertido `0x3B2B` (`selecao_base` do
> `nanoclone.json`). Decidido pelo mantenedor em 14/09.

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
