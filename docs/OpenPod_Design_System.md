# OpenPod — Design System

## Referência visual

**Base de design:** iPod nano (2ª geração)

O OpenPod utilizará como referência visual principal a interface do iPod nano de 2ª geração, adaptando seus princípios para o hardware, resolução de tela e controles físicos disponíveis no player YP3/GN-438.

> **Princípio:** não copiar o sistema da Apple. Recriar a experiência visual clássica do Nano 2 usando os recursos disponíveis no firmware YP3.

---

## 1. Objetivo do design

Criar uma interface:

- simples;
- rápida;
- legível em uma tela pequena;
- orientada a navegação por botões;
- visualmente inspirada no iPod nano 2;
- leve o suficiente para as limitações do hardware YP3.

A interface deve priorizar **usabilidade e desempenho**, evitando elementos gráficos desnecessários.

---

## 2. Características do iPod nano 2 utilizadas como referência

### Estrutura

- menus em listas verticais;
- cabeçalho superior;
- item selecionado claramente destacado;
- navegação hierárquica;
- telas com poucos elementos;
- ícones simples;
- informações essenciais sempre visíveis;
- foco na reprodução de música.

### Linguagem visual

- aparência limpa e minimalista;
- alto contraste;
- tipografia pequena e legível;
- elementos alinhados;
- pouca decoração;
- utilização econômica de espaço.

---

## 3. Adaptação ao OpenPod

O OpenPod **não assumirá que possui os mesmos recursos gráficos do Nano 2**.

Devemos utilizar somente aquilo que o firmware/hardware YP3 disponibilizar.

Prioridade:

1. recursos existentes no firmware;
2. recursos que possam ser modificados com segurança;
3. novos recursos somente quando forem tecnicamente viáveis.

---

## 4. Navegação

A interface será projetada para controles físicos.

Conceito:

```text
UP / DOWN
    ↓
Navegação entre itens

OK / PLAY
    ↓
Selecionar / executar

BACK
    ↓
Voltar

NEXT / PREVIOUS
    ↓
Navegação ou controle de reprodução
```

O mapeamento definitivo dos botões será determinado após a análise do firmware original.

---

## 5. Estrutura principal

A estrutura inicial proposta:

```text
OpenPod
│
├── Music
│   ├── Artists
│   ├── Albums
│   ├── Songs
│   ├── Genres
│   └── Now Playing
│
├── Videos
├── Radio
├── Bluetooth
├── Photos
├── Files
└── Settings
```

A estrutura final deverá respeitar os recursos efetivamente existentes no YP3.

---

## 6. Tela principal

Conceito visual:

```text
┌──────────────────┐
│ Music        🔋  │
├──────────────────┤
│ ▶ Music          │
│   Videos         │
│   Radio          │
│   Bluetooth      │
│   Photos         │
│   Settings       │
└──────────────────┘
```

### Regras

- título no topo;
- lista vertical;
- item selecionado destacado;
- indicador de posição quando necessário;
- ícones somente quando contribuírem para a navegação.

---

## 7. Tela de reprodução

A tela Now Playing deve priorizar:

- capa, quando suportada;
- título;
- artista;
- álbum;
- tempo atual;
- duração;
- progresso;
- estado de reprodução.

Conceito:

```text
┌──────────────────┐
│ Now Playing  🔋 │
│                  │
│     ┌──────┐     │
│     │COVER │     │
│     └──────┘     │
│                  │
│ Artist           │
│ Song Title       │
│                  │
│ 1:42 ━━━●━━ 3:48 │
│   ◀   ▶   ▶▶     │
└──────────────────┘
```

Se a capacidade gráfica do YP3 não suportar determinada informação, ela deverá ser removida ou simplificada.

---

## 8. Cores

A referência deve seguir a estética clássica do Nano 2, mas sem depender de uma reprodução exata de cores.

Paleta inicial:

- fundo claro ou neutro;
- texto escuro;
- seleção em tom contrastante;
- elementos secundários em cinza;
- ícones simples.

A paleta definitiva dependerá das capacidades do display e do framebuffer encontrados no firmware.

---

## 9. Tipografia

Prioridades:

1. legibilidade;
2. baixo consumo de memória;
3. compatibilidade com o mecanismo de fontes existente;
4. aparência próxima da interface clássica do Nano.

Não substituir fontes do firmware até identificarmos:

- formato da fonte;
- tamanho;
- encoding;
- mecanismo de renderização;
- espaço disponível no firmware.

---

## 10. Ícones

Os ícones devem seguir uma estética:

- simples;
- monocromática ou com poucas cores;
- pequena;
- facilmente reconhecível;
- compatível com a resolução do display.

Antes de criar novos ícones, devemos identificar os recursos gráficos existentes na partição de imagens do firmware.

---

## 11. Animações

Animações serão tratadas como **opcionais**.

A prioridade é:

```text
Resposta rápida
      >
Animação
```

Somente adicionar animações se o hardware e o firmware demonstrarem capacidade suficiente sem prejudicar a experiência.

---

## 12. Restrições de engenharia

O design deve respeitar:

- memória disponível;
- armazenamento da firmware;
- resolução do display;
- profundidade de cor;
- framebuffer;
- mecanismo gráfico existente;
- sistema de arquivos;
- formato das imagens;
- formato das fontes;
- sistema de eventos dos botões.

Nenhuma decisão visual deve exigir a substituição completa do sistema gráfico sem necessidade.

---

## 13. Regra fundamental do OpenPod

> **Usar o que o YP3 já entrega. Melhorar antes de substituir.**

O OpenPod será desenvolvido progressivamente sobre o firmware original.

```text
Firmware YP3
     ↓
Análise
     ↓
Interface OpenPod
     ↓
Melhorias
     ↓
Novos recursos
```

---

## 14. Direção estética

O resultado desejado é:

**iPod nano 2ª geração na filosofia de interface + capacidades reais do YP3 + melhorias do OpenPod.**

Não buscamos transformar o GN-438 em uma cópia moderna de um smartphone.

Buscamos criar um **player dedicado, simples, rápido e agradável de usar**.

---

## 15. Regra para futuras alterações

Toda alteração visual deverá ser avaliada em três pontos:

### Compatibilidade
Funciona com o hardware e firmware existentes?

### Desempenho
Mantém a interface rápida e estável?

### Consistência
Continua seguindo a linguagem visual definida pelo OpenPod?

Se a resposta for negativa, a alteração deve ser simplificada.

---

## 16. Status

**Projeto:** OpenPod  
**Design base:** iPod nano — 2ª geração  
**Hardware inicial:** Iigenai GN-438  
**Plataforma alvo:** YP3 / Smartlink  
**Estratégia:** modificar progressivamente o firmware original


---

# PADRÃO — Realce de seleção (decidido em 2026-09-13)

> **A linha selecionada é uma BARRA de fundo, não uma cor de texto.**
> Vale para **todos** os menus do OpenPod, não só a tela inicial.

## A regra

```text
item selecionado    fundo  = paleta 7 (#00BCD4)   texto = branco
item nao selecionado fundo = preto (getter do tema) texto = branco
```

O texto **não muda de cor**. Quem muda é o fundo.

## Como se faz, neste firmware

A seleção original chamava `lv_obj_set_style_text_color`. Basta trocar o
alvo da chamada — a assinatura é a mesma `(obj, cor, seletor)`:

| Função | Endereço | Propriedade |
|---|---|---|
| `set_style_bg_color` | `0x00D4D092` | 0x20 |
| `set_style_bg_opa` | `0x00D4D0B4` | 0x21 |
| `set_style_text_color` | `0x00D4D10A` | 0x37 |

**Um rótulo nasce com fundo transparente**, então `bg_opa = 255` tem de
ser ligado uma vez, na criação. Sem isso a cor de fundo não aparece.

> ⚠️ **E não basta ligar a opacidade.** Ao ligar `bg_opa`, o rótulo passa
> a mostrar a cor de fundo **padrão do tema — que é BRANCA**. É preciso
> pintar de preto **na mesma hora**:
>
> ```text
> na criacao:  bg_color = 0x0000 (preto)  E  bg_opa = 255
> ```
>
> O V027 ligou só a opacidade. O resultado: as linhas que ainda não
> tinham sido desselecionadas apareciam **brancas**, e sumiam uma a uma
> conforme o usuário passava por cima delas. O sintoma era claro e o
> padrão denunciava a causa — mas custou uma gravação.
>
> **Lição:** ao ligar uma propriedade que revela outra, as duas têm de
> ser definidas juntas. Ligar a visibilidade de algo cujo valor você não
> definiu é confiar num padrão que você não escolheu.

Getters de cor do tema:

| | Endereço | Devolve |
|---|---|---|
| texto | `0x00D21384` | `0xFFFF` branco |
| fundo | `0x00D2138A` | `0x0000` preto |

## Geometria

A barra é o retângulo do próprio rótulo. Na home: `x = 6`, largura
**116** → barra de 6 a 122, simétrica, cobrindo o chevron da linha ativa.

> **A largura é 1 byte** (`0x0012ED5E`). Mudar de simétrica para colada
> nas bordas, ou deixar o chevron de fora, é um byte e um setor.

## Onde ainda não vale

As telas de lista do sistema (`page_set_menu`, `page_home_menu`) já têm
barra nativa, com botões de largura total — **e a cor delas vem da
paleta `0x12`, não da 7.** Unificar as duas paletas é o próximo passo do
padrão, e é mais 1 byte por tela.

---

# PADRÃO DE MENU EM LISTA — a regra

> Escrito em 2026-09-13, a pedido do mantenedor: *"tem que ter uma regra
> de design para esse menu, pois quando precisarmos criar temos ele"*.
>
> Esta seção é **normativa**. Todo menu em lista do OpenPod segue isto.
> Os endereços são do `GN438_openpod_v040.bin`; se o firmware mudar,
> reconferir antes de usar.

## 1. A aparência

```
┌────────────────────────────┐
│ 08:06  OpenPod        [==] │  barra:  y 0..15, texto y_ofs 1
├────────────────────────────┤  separador: y 16, 1 px
│                            │  respiro:   y 17..18
│██Música█████████████████ > │  linha selecionada: barra azul + chevron
│  Imagem                  > │  linha normal: fundo preto
│  Extras                  > │
│  Configurar              > │
│                            │
└────────────────────────────┘
```

| elemento | valor | por quê |
|---|---|---|
| fundo da linha | **preto opaco** | sem isso o tema entrega branco |
| linha selecionada | **paleta 7**, barra de fundo | nunca cor de texto |
| texto | branco, 12 px, fonte única do firmware | |
| altura da linha | **16 px** | `ver_res / 10` |
| barra de seleção | **x = 6..115** (110 px) | deixa a coluna do chevron livre |
| chevron | **x = 116..121**, 4×7, traço 1 px | desenhado na folha de fundo |
| margens | 6 px à esquerda, 6 px à direita | simétricas |
| **separador entre itens** | **NÃO EXISTE** | a barra já delimita a linha |
| **ícone por item** | **NÃO EXISTE** | engrenagem repetida não informa nada |
| **barra de rolagem** | **NÃO EXISTE** | `LV_PART_SCROLLBAR` com `bg_opa = 0` |

## 2. As três regras que já custaram versão

**R-L1 — Seleção é barra de fundo, nunca cor de texto.**
São **três** caminhos de código que pintam a seleção, e é preciso
corrigir os três: **seleção** (navegação), **desseleção** (um ramo por
tecla) e **criação** (o índice restaurado ao abrir a tela). A V027
corrigiu dois e esqueceu o terceiro; a V031 fechou. Antes de dar por
pronto, contar todas as chamadas a `set_style_text_color` da página.

**R-L2 — Fundo opaco esconde o que está na folha.**
Ligar `bg_opa` no rótulo faz ele pintar por cima do desenho de fundo na
área que ocupa. Foi assim que a V028b apagou os chevrons. **A largura da
barra e a posição do chevron são uma decisão só.**

**R-L3 — Cada tela de lista é um código diferente.**
Extras e Configurar *parecem* a mesma tela e **não são**:

```
Configurar   page_set_menu_create   0x00D3A638   10 itens
Extras       (função irmã)          0x00D2F0A0    6 itens
Home         page_home_menu_create  0x00D2EBB8    9 objetos, 4 visíveis
```

Semelhança visual **não** é evidência de código compartilhado. Provar
com patch ou com desmontagem antes de afirmar.

## 3. Os pontos de controle, por tela

### Compartilhado — criador da linha `0x00D21764`

```asm
00D2179E  movs r1, #N  ; bl 0xD4D0F4  border_width   N=0 -> sem separador
00D217A8  movs r1, #N  ; bl 0xD4D100  border_side    1 = BOTTOM
```

Vale para **todas** as listas do sistema. Largura 0 torna o lado
irrelevante, inclusive os overrides por item.

### Home — `page_home_menu_create` (0x00D2EBB8)

```
0x000486A0   tabela de coordenadas dos rótulos  (x=6, y da linha)
0x0004867C   tabela de coordenadas dos chevrons (x=116, y+3)
0x0012ED5E   largura do rótulo = largura da barra  (0x6E = 110)
0x0012ED5C   altura do rótulo (0x0F = 15)
0x0012EDBC   bl set_bg_color  — a seleção na CRIAÇÃO
0x0012EB4C   bl set_bg_color  — a seleção na NAVEGAÇÃO
0x000CE15C   folha de fundo 128×160: barra, separador do topo, chevrons
```

### Configurar — `page_set_menu_create` (0x00D3A638)

```
0x0013A7BA   divisor da altura da linha   (10 -> 16 px)
0x0013A8BC   literal do ícone             (-> string vazia)
0x00C4879C   tabela de ids dos 10 itens
```

### Extras — função irmã (0x00D2F0A0)

```
0x0012F0EC   divisor do contêiner (altura e y)
0x0012F22E   divisor da altura da linha
0x0012F330   literal do ícone
0x00DA33B8   tabela de ids dos 6 itens  (na área livre)
0x0012F23E   border_side por item = 2 (TOP)
0x0012F24C   border_side do último  = 3 (TOP|BOTTOM)
```

## 4. Constantes da LVGL, confirmadas NESTE binário

Não deduzidas da documentação — encontradas varrendo o firmware.

```
LV_PART_SCROLLBAR   0x00010000     LV_PART_INDICATOR  0x00020000
LV_PART_SELECTED    0x00040000     LV_PART_ITEMS      0x00050000

LV_BORDER_SIDE  NONE 0  BOTTOM 1  TOP 2  LEFT 4  RIGHT 8

lv_obj_add_flag             0x00D49204   (orrs  [r4,#0x1c])
lv_obj_clear_flag           0x00D4924A   (bic.w [r4,#0x1c])
LV_OBJ_FLAG_SCROLLABLE      0x10

set_style_bg_color     0x00D4D092   prop 0x20
set_style_bg_opa       0x00D4D0B4   prop 0x21
set_style_border_color 0x00D4D0D6   prop 0x30
set_style_border_opa   0x00D4D0EA   prop 0x31
set_style_border_width 0x00D4D0F4   prop 0x32
set_style_border_side  0x00D4D100   prop 0x33
set_style_text_color   0x00D4D10A   prop 0x37
lv_disp_get_ver_res    0x00D568CC
```

## 5. Como criar um menu novo seguindo o padrão

1. Copiar a estrutura da função irmã mais próxima em número de itens.
2. Tabela de ids na área livre (`0x001A3038+`), como o Extras faz.
3. Divisor = 10. Ícone = string vazia. Separador já vem desligado.
4. Seleção: barra de fundo nos **três** caminhos (R-L1).
5. Chevron na folha, fora da barra (R-L2).
6. Conferir no aparelho antes de considerar pronto — prévia em ASCII
   prova correção, não estética.

---

# CHROME PADRÃO — a faixa superior e o início da lista

> Escrito em 2026-09-14, depois de o mantenedor apontar o problema de
> raiz: *"eu quero um padrão de design, tudo tem que parecer com a home
> (…) senão vai ficar sempre tudo aleatório"*.
>
> **Esta seção é NORMATIVA.** Ela não descreve o que o firmware faz:
> descreve o que toda tela do OpenPod tem de fazer. Os números saíram de
> medição da home, pixel a pixel, não de gosto.

## 1. A régua — a home, medida

```text
y  0.. 4   RGB( 20, 22, 26)   topo
y  5.. 9   RGB( 14, 16, 19)   meio
y 10..15   RGB(  9, 10, 12)   base
y 16       RGB( 52, 56, 62)   SEPARADOR, 1 px
y 17..18   preto              respiro, 2 px
y 19..     lista
```

```text
altura da faixa    16 px          separador  1 px em y16
respiro             2 px          lista comeca em y19
texto da faixa     y_ofs 1, ocupa y 1..13  (ascendente 13 com acentos)
```

## 2. O que estava errado, medido

A faixa das subtelas **não** é pintada na folha: é um objeto LVGL cuja
altura é `160 / divisor`, e o divisor é uma constante **por tela**.

```text
divisor  7 -> faixa 22 px  :  50 telas
divisor  8 -> faixa 20 px  :   1 tela
divisor 10 -> faixa 16 px  :   1 tela (Extras, mudada na V040)
```

**51 das 52 telas divergem da home.** Essa é a origem do "aleatório" —
não é descuido de desenho, é uma constante espalhada por 52 funções.

### ⚠️ Por que NÃO se corrige trocando o divisor

O mesmo divisor alimenta um segundo cálculo, o espaçador inferior:

```text
altura_do_espacador = 160 - 7 * (160/divisor)
   divisor  7 -> 160 - 154 =  6 px     (o resto da divisao)
   divisor 10 -> 160 - 112 = 48 px     <- cobriria a lista
```

Trocar 1 byte por tela pareceria certo e quebraria as 51. **Registrado
aqui porque é exatamente o erro que este documento existe para evitar.**

## 3. A regra

Toda tela de lista do OpenPod aplica, sem exceção:

| elemento | valor | como |
|---|---|---|
| altura da faixa | **17 px** (16 de banda + 1 de separador) | forçada no `set_size` da faixa |
| fundo da faixa | `RGB(14,16,19)` = `0x0882` | no criador compartilhado `0x00D216F0` |
| separador | `RGB(52,56,62)` = `0x31C7`, borda 1 px BOTTOM | idem |
| início da lista | **y = 19** | forçado no `align` do contêiner |
| respiro | 2 px, consequência dos dois acima | — |

A faixa vira **cor sólida** no tom do meio, não degradê de três faixas.
Entre `RGB(20,22,26)` e `RGB(9,10,12)` a diferença é imperceptível neste
LCD; o degradê da home fica porque ela é imagem e não custa nada.
**Isto é uma simplificação assumida, não um descuido.**

## 4. Como se aplica

Nunca tela a tela. Uma ferramenta varre os pontos, confere a forma de
cada um e **recusa tudo se um só divergir**:

```text
1. localiza cada `bl 0x00D216F0`            (criador da faixa)
2. acha o `bl 0x00D4A21A` seguinte           (set_size da faixa)
3. redireciona para uma rotina que ignora a altura calculada
4. localiza cada `bl 0x00D21690`            (criador do conteiner)
5. acha o `bl 0x00D4A3A2` seguinte com align=2
6. redireciona para uma rotina que forca y_ofs = 20
```

`y_ofs = 20` e não 19 porque as linhas são alinhadas em `16*i - 1`: a
linha 0 cai em `20 - 1 = 19`.

## 5. A regra de ouro

> **A home é a régua.** Quando uma tela discordar dela, a tela muda — e a
> mudança entra por uma varredura que atinge todas as telas, nunca por um
> ajuste naquela tela. Se o ajuste não puder ser expresso como regra
> aplicável a todas, ele não entra.

## 6. Implementação — `tools/patch_chrome_padrao.py` (V060 / 2.0)

```text
telas de lista (faixa + linhas)              36   TODAS cobertas
  altura da faixa   24 via set_height   14 via set_size
  altura do conteiner                   30
  align do conteiner                     8   (as demais: set_align BOTTOM_MID)
  telas que nao mexem no conteiner       6   -> pegam o padrao do criador
```

### 6.1 O que foi preciso para chegar às 36

O primeiro reconhecedor casava padrão de instruções e achava **14 de
36**: as telas não usam a mesma sequência de chamadas. Trocado por
**rastreamento de registrador** — segue o objeto devolvido por
`0x00D216F0` / `0x00D21690`, acompanha as cópias entre registradores, e
registra toda chamada em que ele é o 1º argumento. Subiu para 30.

As **6 restantes** não redimensionam nem alinham o contêiner: deixam como
o criador entregou. Em vez de caçar um gancho inexistente, o padrão virou
**default do criador compartilhado** — e as 30 que sobrescrevem passam
pelos thunks que normalizam. Cobertura: 36/36, sem exceção.

### 6.2 A forma do patch

```text
0x001A5300   76 B   6 rotinas (thunks de 6 B + a base do conteiner)
     24 ganchos -> forca altura 17 na faixa   (set_height)
     14 ganchos -> forca altura 17 na faixa   (set_size)
     30 ganchos -> forca altura 141 no conteiner
      8 ganchos -> forca y_ofs 19 no conteiner
      1 gancho  -> cor de fundo da faixa      (criador compartilhado)
      1 gancho  -> cor do separador           (criador compartilhado)
      1 gancho  -> default do conteiner       (criador compartilhado)
```

**270 bytes, 25 setores.** Setores muitos porque os ganchos estão
espalhados pelas funções de criação de tela — irrelevante pelo cartão SD,
que reescreve a imagem inteira.

> **A lição:** a especificação foi barata (uma medição da home). O caro é
> a **aplicação uniforme**, porque o firmware não é uniforme. Foi por isso
> que o projeto foi escorregando para ajustes por tela. A ferramenta
> **recusa tudo** se uma tela não casar — é o que impede a recaída.
