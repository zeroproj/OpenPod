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

## 2. O que já está feito

Conferido contra `marte/paleta/nanoclone.json`, campo a campo:

| | alvo | Core 2.1.1 |
|---|---|---|
| fundo do conteúdo | RGB(255,255,255) | ✅ igual |
| cor da faixa | RGB(189,198,205) | ✅ igual |
| separador da faixa | RGB(90,97,106) | ✅ igual |
| texto | RGB(0,0,0) | ✅ igual |
| texto selecionado | RGB(255,255,255) | ✅ igual |
| seleção | RGB(41,101,222) | ✅ igual |
| sem ícones de linha | — | ✅ (S7) |
| sem barra de rolagem | — | ✅ |

**As cores estão exatas. Seis de seis.**

---

## 3. O que falta, com o custo medido

### 3.1 Texto do item selecionado, na home — ✗

No mockup, "Extras" é **branco** sobre o azul. Nas fotos do aparelho:

```
Configurar   "Despertador", "Tempo de tela"   BRANCO   correto
home         "Musica"                         ESCURO   errado
```

As listas leem `cor_texto_sel` (a rotina `0x00DA598C`, gancho do
`patch_cor_selecao` dentro de `CRIA_LINHA`). **A home não** — ela pinta
o próprio realce.

Sétima ocorrência do mesmo padrão. Custo: um ponto na home, do mesmo
feitio dos anteriores.

### 3.2 Separadores entre os itens — ✗

O nano **não tem**. Nós temos, e a origem está medida:

```
00D2178A   movs r0, #0x12
00D2178C   bl   palette_main       <- a cor vem da PALETA da LVGL
00D21796   bl   set_style_border_color
00D2179E   movs r1, #1
00D217A0   bl   set_style_border_width      <- largura 1
```

A cor da borda da linha **não vem da nossa tabela** — vem de
`palette_main(0x12)`. Oitava ocorrência.

Para chegar ao alvo, a largura vai a **zero**: `0x0012179E`, o imediato
`#1` → `#0`. **Um byte.**

> **Não confundir com o traço da faixa.** O `faixa_separador` do
> `nanoclone.json` é a linha **y=17**, embaixo da barra — e essa
> **fica**. São objetos diferentes: a borda da FAIXA e a borda da LINHA.
> Eu estava usando `cor_separador` para a coisa errada.

### 3.3 Degradê da faixa e da seleção — ✗

E aqui o alvo **barateia** o que eu tinha marcado como incerto.

`marte/paleta/nanoclone.json` traz o degradê **linha a linha**: as 19
cores, de `y=0` a `y=18`. E `marte/adaptado/` já tem os pixels **na nossa
largura**:

```
faixa_128x18.png      o degrade da faixa, 128x18
selecao_128x16.png    o degrade da selecao, 128x16
```

**Logo o M2/M3 não dependem de o nosso LVGL honrar `BG_GRAD_DIR`** — a
incerteza registrada em `PROJETO_MARTE.md` §4.1 como "PROVÁVEL, só o
aparelho responde". Dá para pintar 17 linhas de 1 px, ou usar o bitmap
pronto.

**O degradê deixou de ser aposta.** Continua sendo código novo — mas de
risco conhecido, não de viabilidade duvidosa.

### 3.4 Título centralizado — ✗

Alvo: "Menu", centralizado. Hoje: `09:30 OpenPod`, à esquerda, com o
relógio.

Decisão de produto pendente: manter o relógio (útil) ou seguir o nano
(limpo). O mockup diz nano.

### 3.5 Bateria colorida — ✗

Alvo: ícone verde, desenhado. Hoje: glifo monocromático da fonte de
ícones. `marte/adaptado/icones/battery_00..09.png` já estão em 21×13.

É M4, e é onde o share-alike do CC BY-SA entra de verdade — o primeiro
pixel do NanoClone dentro do firmware.

---

## 4. Ordem sugerida

| passo | o que | custo |
|---|---|---|
| **a** | separadores somem | **1 byte** |
| **b** | texto selecionado branco na home | 1 ponto |
| **c** | degradê da faixa e da seleção | rotina nova, sem `BG_GRAD` |
| **d** | título centralizado | decisão + posição |
| **e** | bateria colorida | M4, primeiro bitmap do nano |

**a** e **b** chegam muito perto do mockup por dois pontos de código. Só
depois vale abrir o **c**.

---

## 5. Correções que este documento faz a estudos anteriores

1. **`cor_separador` não é o traço entre as linhas.** É o traço de 1 px
   embaixo da faixa (`y=17` no JSON). O traço entre linhas vem de
   `palette_main(0x12)` e não tem campo na tabela.
2. **O degradê não depende de `BG_GRAD`** (§4.1 do estudo). O JSON traz
   as cores linha a linha e o `adaptado/` traz os pixels prontos.
3. **O alvo do produto é `marte_completo.png`**, e não a descrição em
   prosa espalhada pelos documentos.
