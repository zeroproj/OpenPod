# PROJETO MARTE — o visual do iPod nano, a partir do tema NanoClone

> **Estado: ESTUDO. Nada implementado, nada gravado.**
>
> **Decisões do mantenedor (2026-09-14):** seguir o padrão do NanoClone
> **por completo**; os pixels dele **podem** entrar no projeto; creditar
> como inspiração. Registradas em `ATRIBUICAO.md`.
> Marte só começa quando o mantenedor disser. O Saturno ainda tem
> defeitos abertos (faixa clara, contador da Música, vão de 5 px,
> barra no descanso) e a 2.2 ainda não foi testada no aparelho.

Documento escrito em 2026-09-14, a partir do material em
`assets/referencia/NanoClone/` e do firmware de fábrica.

---

## 1. O que é o NanoClone

| | |
|---|---|
| nome | NanoClone 5.2 |
| autor | Billy Blair |
| licença | **CC-BY-SA 3.0** |
| alvo | Rockbox em **iPod Nano, 176×132×16** |
| atualizado | 03/2015 |

Arquivos: um `.cfg` (tema), um `.sbs` (moldura/status), um `.wps`
(tela Tocando Agora), 16 bitmaps e uma fonte `.fnt`.

### 1.1 A licença não é detalhe

CC-BY-SA 3.0 obriga a **atribuir** o autor e a licenciar derivados sob a
**mesma licença**. Se qualquer pixel dele for parar no OpenPod, isso tem
de constar no repositório e no aparelho (tela Sobre, por exemplo).

**DECIDIDO: usar os bitmaps.** O mantenedor autorizou, com crédito.

A obrigação prática, registrada em `ATRIBUICAO.md` e a repetir na tela
Sobre: creditar Billy Blair, apontar a licença, indicar que houve
alteração — e o **share-alike**, que faz os ativos derivados (e o que os
incorpore) saírem sob CC BY-SA 3.0.

---

## 2. O obstáculo que decide tudo: a tela é outra

```
iPod Nano (alvo do NanoClone)   176 x 132   paisagem
GN-438   (nosso)                128 x 160   retrato
```

Não é escala, é **proporção invertida**. 48 px a menos de largura e
28 px a mais de altura.

Mas o estrago é **muito menor do que eu previ no primeiro estudo**.
Medindo quadro a quadro em vez de olhar o tamanho do arquivo:

| bitmap | strip | quadro | cabe em 128 px? |
|---|---|---|---|
| `battery.bmp` | 21×130 | 21×13 (10) | **sim** |
| `playbtns.bmp` | 15×65 | 15×13 (5) | **sim** |
| `hdd.bmp` | 16×96 | 16×16 (6) | **sim** |
| `repeat.bmp` | 16×48 | 16×12 (4) | **sim** |
| `shuffle.bmp` | 16×12 | 16×12 | **sim** |
| `hold.bmp` | 13×13 | 13×13 | **sim** |
| `volume.bmp` | 120×11 | 120×11 | **sim** |
| `vol-l/r.bmp` | 82×24 | 82×24 | **sim** |
| `progress.bmp` | 162×11 | 162×11 | não (sobram 34) |
| `bg-176x132x16.bmp` | 176×132 | — | não (é a tela toda) |

**Nove dos dez cabem.** Os ícones do Rockbox são pequenos por natureza —
quem não cabe é só o que ocupa a largura inteira.

E há um detalhe que barateia mais: **o degradê da faixa é puramente
vertical**. Cada linha é de uma cor só. Esticar de 176 para 128 px na
horizontal é **sem perda nenhuma** — não é redimensionar, é repetir.

Sobram dois itens de verdade:
- `progress.bmp` → remontado em três fatias (tampa esquerda, miolo
  esticado, tampa direita) em `marte/adaptado/progress_114x11.png`;
- o fundo `176×132` → não se adapta, mas também não é preciso: ele é
  branco liso com a faixa no topo, que já temos separada.

> **O que Marte continua NÃO sendo:** instalar o NanoClone no GN-438.
> O aparelho não roda Rockbox e não interpreta `.wps`. Marte é
> reproduzir a aparência — agora com os pixels dele, não só com as
> medidas.

---

## 3. O que É aproveitável: a paleta

Extraída dos bitmaps, linha a linha, não suposta.
Arquivo: `marte/paleta/nanoclone.json`.

| elemento | RGB | RGB565 |
|---|---|---|
| faixa, topo do degradê | (246,246,255) | `0xF7BF` |
| faixa, base do degradê | (189,198,205) | `0xBE39` |
| separador sob a faixa | (90,97,106) | `0x5B0D` |
| fundo do conteúdo | (255,255,255) | `0xFFFF` |
| texto | (0,0,0) | `0x0000` |
| seleção, topo | (99,156,227) | `0x64FC` |
| seleção, base | (40,102,221) | `0x2B3B` |
| texto selecionado | (255,255,255) | `0xFFFF` |

### 3.1 A descoberta que inverte o projeto

**O iPod nano é tema CLARO.** `foreground color: 000000`,
`background color: FFFFFF` no `.cfg`. Texto preto sobre branco, com
barra de seleção azul em degradê.

O OpenPod foi para o **escuro** (fundo preto, texto branco, seleção
ciano). Marte não é um ajuste de cor — é **inverter o tema inteiro**.

Comparação renderizada na nossa tela real: `marte/mockups/comparacao.png`.

### 3.2 E é aqui que o Saturno se paga

Pela tabela de 19 bytes em `0x001A5400`, a inversão é:

| campo | hoje | Marte |
|---|---|---|
| `cor_tela` | `0x0000` preto | `0xFFFF` branco |
| `cor_faixa` | `0x8208` | `0xBE39` (ou degradê) |
| `cor_separador` | `0xC731` | `0x5B0D` |
| `cor_texto` | `0xFFFF` | `0x0000` |
| `cor_texto_sel` | `0xFFFF` | `0xFFFF` |
| `cor_selecao` | `0xFA05` ciano | `0x2B3B` azul |

**Seis campos. Doze bytes. Zero bytes de código.**

> Atenção ao `LV_COLOR_16_SWAP`: a tabela guarda os valores
> **pré-invertidos** (byte-swapped). `0xBE39` vira `0x39BE` gravado.
> Os valores da tabela acima são RGB565 puro e precisam do swap.

---

## 4. O que exige código novo

### 4.1 O degradê da faixa

A faixa do nano tem 18 px: 17 de degradê vertical mais 1 de separador —
quase a nossa `altura_faixa` = 17. Mas a nossa é **cor chapada**.

Evidência sobre a viabilidade, tirada do firmware de fábrica:

| propriedade LVGL v8 | nº | setter no firmware |
|---|---|---|
| `BG_COLOR` | 32 | presente (`0x0014D0B0`, `0x0014D092`) |
| `BG_OPA` | 33 | presente (`0x0014D0BA`) |
| `BG_GRAD_COLOR` | 34 | **sem atalho** |
| `BG_GRAD_DIR` | 35 | **sem atalho** |
| `BG_GRAD` | 38 | **presente** (`0x0014D0C4`) |

`BG_GRAD` recebe um descritor de degradê inteiro. A existência desse
setter é indício forte de que o caminho de degradê **está compilado** —
o LVGL só o gera quando a propriedade existe, e quem a consome é o
desenhador de retângulo.

E a ausência de atalho para 34/35 não impede nada: o despachante
`lv_obj_set_local_style_prop(obj, prop, valor, seletor)` em `0x00D4CAC4`
aceita **qualquer** número de propriedade — é assim que o Saturno já
define raio, borda e padding.

**Classificação: PROVÁVEL, não CONFIRMADO.** Só o aparelho decide.
Teste barato, no mesmo espírito do `DIAGNOSTICO cores`: definir 34 e 35
na faixa e olhar. Se não pintar, a alternativa é cor chapada na média do
degradê, `0xDF1C` — RGB(222,226,230) — que a olho nu quase não difere.

### 4.2 A fonte

| | altura | 
|---|---|
| nossa | 12 px |
| `14-MyriadPro-Semibold.fnt` | **18 px** (ascent 14, largura máx. 17) |

Uma fonte de 18 px **não cabe** na nossa linha de 16 px. Trocar a fonte
implicaria subir `altura_linha` para ~20, o que derruba de 8 para 7 os
itens visíveis. Formato também difere: Rockbox `RB12` contra o formato
de fonte do LVGL.

> **Revisto em §15.2.** A tinta real da fonte tem **16 px**, não 18 — ela
> **cabe** na nossa linha de 16 sem mudar `altura_linha`. O que resta é
> converter `RB12` para o formato do LVGL (§15.5).

---

## 5. A tela Tocando Agora — estudo pedido em 2026-09-14

### 5.1 A nossa

`page_music_play_create`, **página 0x04**, em `0x00131E7C` (2272 B).
É enxuta: **6 rótulos e 1 objeto**, posicionados com `TOP_MID`:

| y | altura | o que é (provável) |
|---|---|---|
| 0 | — | título |
| 22 | 7 | linha de estado |
| 45 | 60 | bloco de texto (título/artista/álbum) |
| 45 | 3 | elemento fino — barra de progresso? |
| 110 | 7 | tempo |
| 152 | — | rodapé |

### 5.2 A do NanoClone

Treze elementos, com lógica condicional — o `.wps` é uma linguagem
interpretada, não um layout fixo:

| elemento | posição (176×132) | tamanho |
|---|---|---|
| ícone de reprodução | 5,2 | 15×13 |
| bloqueio | 19,2 | 13×13 |
| bateria | 153,2 | 21×13 |
| posição na lista | 6,23 | 70×14 |
| repetição | 137,22 | 16×12 |
| aleatório | 153,22 | 16×12 |
| capa do álbum | 7,42 | 45×45 |
| info **com** capa | 58,38 | 112×53 |
| info **sem** capa | 7,38 | 162×53 |
| barra de progresso | 7,100 | 162×11 |
| tempo decorrido/restante | 7,110 | 162×16 |
| barra de volume | 24,111 | 120×11 |
| alto-falantes | 6,100 e 88,100 | 82×24 |

### 5.3 Cabe? Cabe — e melhor do que parecia

O medo era a largura: 176 → 128. Medindo a **tinta real** em vez do
canvas, o susto passa:

| ativo | canvas | tinta | solução |
|---|---|---|---|
| `vol-l.bmp` | 82×24 | **8×15** | recortar o padding |
| `vol-r.bmp` | 82×24 | **17×15** | recortar o padding |
| `volume.bmp` | 120×11 | 120×11 | remontar em 3 fatias → 90 px |
| `progress.bmp` | 162×11 | 162×11 | remontar em 3 fatias → 114 px |

Os canvas largos dos alto-falantes eram só **posicionamento** do Rockbox.

E ganhamos 28 px de altura (132 → 160), que sobram para o bloco de texto
e o rodapé respirarem.

Mockup: `marte/mockups/marte_tocando_agora.png`.

> **Corrigido em §13.2:** a barra de volume **substitui** a de progresso
> por 2 s (`%?mv(2.0)`); elas não convivem. O mockup mostra os dois
> estados.

### 5.4 O que realmente custa — e não é o desenho

Reposicionar ativos é barato. O caro é que **a nossa tela tem 6 rótulos
e a dele tem 13 elementos com condicional**: com capa ou sem, disco
ativo, bloqueio, cinco modos de reprodução, quatro de repetição, volume
que aparece por cima ao mexer.

Isso é **objeto novo e código novo** na página 0x04 — não é mexer na
tabela do Saturno. É a diferença entre Marte M1 (12 bytes) e isto.

### 5.5 A capa do álbum: recurso novo, não adaptação

Varri o firmware de fábrica:

```
APIC       0      <- frame de imagem do ID3
albumart   0
ID3        4      <- lê tags (título/artista/álbum)
JPEG      23      <- decodificador existe (visualizador de fotos)
```

**O firmware lê tags mas não extrai capa.** O decodificador JPEG já está
lá, que é a metade difícil — falta extrair o frame `APIC` do ID3 e
ligá-lo ao decodificador.

Classificação: **HIPÓTESE de viabilidade**, não confirmado. É Fase 3 do
projeto (recurso novo), não Fase 1 (interface). O mockup mostra a capa
como espaço reservado, honestamente — hoje ela não existe.

### 5.6 Fatiamento sugerido

| passo | o que | risco |
|---|---|---|
| **W1** | paleta clara + faixa na 0x04, como no resto | baixo |
| **W2** | barra de progresso e tempo com os ativos dele | médio |
| **W3** | ícones de estado (reprodução, repetição, aleatório, bateria) | médio |
| **W4** | barra de volume sobreposta | médio |
| **W5** | capa do álbum (extrair APIC) | **alto — recurso novo** |

W1 sai junto de Marte M1, de graça: a página 0x04 tem faixa e herda a
tabela como as outras.

---

## 6. Proposta de fatiamento

| fase | o que | custo | risco |
|---|---|---|---|
| **M1** | inverter a paleta pela tabela (6 campos) | 12 bytes | baixo |
| **M2** | degradê na faixa (props 34/35 ou 38) | rotina nova | médio |
| **M3** | degradê na seleção | rotina nova | médio |
| **M4** | ícones de estado na faixa (§9, §10) | reusar Font Awesome | baixo |
| **M5** | fonte maior + `altura_linha` (§11) | ver §11.3 | médio |
| **M6** | tela Tocando Agora (ver §5, fases W1..W5) | ver §5.6 | W1 baixo, W5 alto |

**M1 sozinho já muda o aparelho inteiro de cara** e é reversível em
12 bytes. É o melhor primeiro passo: máximo efeito visível, mínimo risco,
e testa se o tema claro agrada antes de investir em degradê.

---

## 7. Perguntas — respondidas em 2026-09-14

1. **Tema claro?** SIM — seguir o padrão do NanoClone por completo.
2. **Ciano ou azul do nano?** Azul do nano (`0x64FC` → `0x2B3B`).
3. **Creditar?** SIM, como inspiração. Feito em `ATRIBUICAO.md`;
   falta repetir na tela Sobre quando Marte for implementado.

### Ainda em aberto

- a tela **Tocando Agora** foi estudada (§5): os ativos **cabem**, o
  custo real é código para os 13 elementos condicionais, e a **capa do
  álbum é recurso novo** (o firmware não extrai `APIC`);
- a **fonte**: estudada em §11. Já existe uma de 18 px na flash; o que
  falta é achar de onde vem a fonte atual da interface (§11.3).

---

## 8. Pasta

```
marte/
├── referencia/   os 16 bitmaps convertidos para PNG (visualizáveis)
├── paleta/       nanoclone.json — cores extraídas, com RGB565
├── adaptado/     ATIVOS JA NA NOSSA MEDIDA
│   ├── faixa_128x18.png       degrade da faixa, adaptado sem perda
│   ├── selecao_128x16.png     degrade azul da selecao
│   ├── progress_114x11.png    barra remontada em 3 fatias
│   └── icones/                30 quadros extraidos dos strips
└── mockups/      comparacao.png, marte_completo.png
```

`marte/mockups/marte_completo.png` usa os pixels dele de verdade — a
faixa e a bateria saíram do tema, adaptadas.

Os originais ficam intocados em `assets/referencia/NanoClone/`.

---

## 9. A moldura — o `.sbs`

O `.sbs` é o *statusbar skin*: o que o Rockbox desenha em **todas** as
telas, por baixo de qualquer menu. É o equivalente direto da nossa faixa.

### 9.1 O que a moldura dele carrega

| elemento | posição (176×132) | tamanho |
|---|---|---|
| ícone do modo de reprodução | 5,2 | 15×13 (5 quadros) |
| bloqueio de teclas | 19,2 | 13×13 |
| atividade de disco | 4,0 | 16×16 (6 quadros, animado) |
| bateria | 153,2 | 21×13 (10 níveis) |
| repetição | 137,22 | 16×12 (4 estados) |
| aleatório | 153,22 | 16×12 |
| **viewport do conteúdo** | 5,20 | 166×112 |

### 9.2 A comparação que interessa

| | NanoClone | OpenPod 2.2 |
|---|---|---|
| conteúdo começa em | y = **20** | y = **19** |
| altura da faixa | 18 (17 + 1 separador) | 17 + separador |
| título | sim | sim, `TOP_MID` |
| **bateria na faixa** | **sim, em toda tela** | **não** |
| **modo de reprodução** | **sim** | **não** |
| **bloqueio** | **sim** | **não** |
| repetição / aleatório | sim | não |

A geometria **já bate** — 19 contra 20, 17 contra 18. Não foi de
propósito, mas é uma sorte que barateia tudo.

O que falta é **conteúdo**: a nossa faixa é só título.

Confirmei por varredura que os dois auxiliares de rótulo à direita da
faixa (`0x001226F8` e `0x0012274C`) existem no código e têm
**zero chamadores** nas telas — o desenho está lá, ninguém usa.

### 9.3 Correção de uma afirmação minha

Eu disse no chat que isso **"conflita com o S7"**. Não conflita.

O S7 escondeu os ícones cuja fonte é `0x00CA671C` — os ícones **de linha
de lista**, 44 pontos em 32 telas. Os rótulos da faixa usam outras
fontes (`0x00CACFE4` e `0x00CAF5EC`). São conjuntos disjuntos: pôr
bateria na faixa não reacende ícone nenhum das listas.

---

## 10. Os ícones que já temos — e não precisamos importar

### 10.1 A descoberta

Os glifos da fonte de ícones do firmware estão na faixa privada, e
decodificando as strings apareceu o padrão:

```
0x000D49EB   "#1E90FF " + U+E625     <- recolorização LVGL
0x000D49F7   "#1E90FF " + U+E617
...          20 ícones da home, todos em #1E90FF (DodgerBlue)
0x000D4AE8   "#54FF9F " + U+E623     <- variante verde, estado ligado
```

E na faixa `F0xx` aparecem codepoints do **Font Awesome** — que é o
conjunto de símbolos padrão do LVGL (`LV_SYMBOL_*`).

### 10.2 Inventário do que está PROVADO que renderiza

| símbolo | código | símbolo | código |
|---|---|---|---|
| AUDIO | F001 | SHUFFLE | F074 |
| VIDEO | F008 | DOWN | F078 |
| OK | F00C | CALL | F095 |
| CLOSE | F00D | SAVE | F0C7 |
| SETTINGS | F013 | BARS | F0C9 |
| VOLUME_MAX | F028 | KEYBOARD | F11C |
| PREV | F048 | BACKSPACE | F55A |
| PLAY | F04B | NEW_LINE | F8A2 |
| PAUSE | F04C | LEFT | F053 |
| NEXT | F051 | RIGHT | F054 |

**Play, pause, anterior, próxima, aleatório, volume e configurações já
existem no firmware** como glifos.

> **Corrigido em §12.3:** eu concluí daqui que "não precisamos de um
> único bitmap do NanoClone". É forte demais. Os ícones dele são
> **coloridos e com brilho**; Font Awesome é monocromático. A escolha é
> de design, não de conveniência — veja a tabela em §12.3.

### 10.3 O limite honesto desta medição

Isto mede **uso**, não **disponibilidade**. A tabela de glifos da fonte
de ícones está em RAM (`dsc` = `0x00819C90`), então não dá para listar
estaticamente o que a fonte *contém* — só o que alguma string já pede.

Símbolos como `BLUETOOTH` (F293) e as **baterias** (F240–F244) não
aparecem em nenhuma string. Isso **não prova** que faltam na fonte. E no
caso da bateria há pista contrária: a faixa desenha bateria com glifos
próprios da área privada (U+E605, U+E647), não com o Font Awesome.

---

## 11. As fontes

### 11.1 O que existe na flash

| endereço | `line_height` | 1ª faixa do cmap | o que é |
|---|---|---|---|
| `0x00CA671C` | 13 | *(dsc em RAM)* | ícones de lista (44 usos) |
| `0x00CACFE4` | 16 | U+E601, 12 chars | ícones da faixa |
| `0x00CC19B8` | 12 | U+002D, **14 chars** | **relógio** (`-./0-9:`) |
| `0x00CDED88` | **18** | U+0020, **95 chars** | **texto, ASCII completo** |
| `0x00CAF5EC` | 23 | — | ícones grandes |
| `0x00CA7E6C` | 61 | — | dígitos gigantes |
| `0x00CAA8A8` | 81 | — | dígitos gigantes |

### 11.2 Duas correções ao meu estudo anterior

1. Eu escrevi que "a nossa fonte tem 12 px". **Errado.** A de 12 px tem
   só 14 caracteres — é a do relógio. Não é a fonte da interface.
2. Eu escrevi que a fonte de 18 px do NanoClone "não cabe e exigiria
   converter `RB12` para o formato do LVGL". **Já existe uma fonte de
   18 px na flash**, `0x00CDED88`, com ASCII completo e 5 referências no
   código. Se 18 px for o alvo, pode não ser preciso converter nada.

### 11.3 Onde está a fonte real da interface — fio solto

A fonte que desenha os menus não é nenhuma das acima: os menus mostram
acentos (Música, Álbuns) e a de 18 px só cobre ASCII.

As fontes mais usadas estão em `0x00819C78`, `0x00819CC8`, `0x00819D00`,
`0x00819D38`, `0x00819D70` — **RAM**.

E a tabela de partições tem só três entradas:

```
FIRM   0x00E000   TONE   0x1A1000   PSMP   0x1FC000
```

**Não existe partição FONT.** Logo essas fontes são `.data`: os bytes
estão dentro da FIRM e o boot os copia para a RAM.

**Próximo passo concreto**, quando M5 chegar: achar a região de
inicialização de `.data` (o trecho da FIRM que alimenta `0x00819xxx`) e
verificar se o `dsc` dessas fontes aponta para RAM ou para a flash. Se
apontar para a flash, trocar a fonte da interface é **um ponteiro**.

### 11.4 Consequência para o M5

> **Corrigido em §15.2.** Não há preço de tela: a tinta real são 16 px e
> cabe na linha atual. A lista **continua com 8 itens**. O que resta do
> M5 é a conversão de formato (§15.5).

---

## 12. Revisão de manhã (2026-09-14) — o que eu tinha medido mas não OLHADO

O estudo da noite mediu os bitmaps (dimensões, caixa de tinta, cores)
mas só **abriu um** deles. Abertos todos, apareceram quatro coisas que a
medição não pega — e três delas **corrigem** o que eu havia escrito.

### 12.1 O título do nano é PINTADO no bitmap

`NanoClone.bmp` traz a palavra **"iPod"** desenhada dentro da barra.
`bg-176x132x16.bmp` traz **"Now Playing"**. Não é texto renderizado: é
imagem. Os dois diferem só em `(74,2)–(102,13)` — exatamente a caixa do
título — e `NanoClone_blank.bmp` é a mesma coisa com a barra vazia.

Consequência boa: **a nossa barra é melhor que a do tema original.**
O `patch_titulos` desenha texto de verdade, por página, vindo de uma
tabela. O nano repete "iPod" em toda tela de menu porque não tem como
fazer diferente.

**Marte não deve copiar isso.** Mantemos o título dinâmico.

### 12.2 O sulco da barra de progresso vem do fundo

Eu adaptei `progress.bmp` achando que era a barra inteira. É só o
**preenchimento**. O **sulco** (a calha vazia) está embutido no
`bg-176x132x16.bmp`, em `(6,100)`, 164×11.

Sem o fundo, a barra flutuaria sem calha. Extraído e adaptado:
`marte/adaptado/progress_sulco_114x11.png`.

### 12.3 Os ícones dele são COLORIDOS e com brilho

Esta é a correção que mais muda o plano.

Eu escrevi em §10 que, tendo Font Awesome no firmware, "não precisamos
de um único bitmap do NanoClone". **Isso é forte demais.**

Olhando: os botões de reprodução são **azuis com gradiente e brilho**, a
bateria é **verde sobre cinza metálico**, o disco é uma animação de seis
quadros. São ícones no estilo Apple de 2006, coloridos.

Font Awesome no LVGL é **glifo monocromático de uma cor só**. Dá para
recolorir (é o que a home faz com `#1E90FF`), mas **não dá brilho nem
duas cores no mesmo ícone**.

Então a escolha é real, e é de design:

| | Font Awesome (já temos) | bitmaps do NanoClone |
|---|---|---|
| custo | zero | embutir imagens |
| licença | livre | **CC BY-SA** |
| aparência | chapado, uma cor | colorido, com brilho |
| fidelidade ao nano | média | alta |

Como você decidiu *"seguir o padrão dele por completo"*, o caminho é os
**bitmaps** — mas registro que a alternativa existe e era mais barata.

### 12.4 O nano também não mostra ícones nas listas

O `.cfg` traz `show icons: off`, e a linha do conjunto de ícones está
comentada — com o nome `nanoclone_no_icons_6x12.bmp`. O autor
deliberadamente desligou os ícones das listas.

É **exatamente** o que o nosso S7 fez (`icones = 0`). Convergimos com o
padrão do nano sem saber.

### 12.5 A fonte, agora lida de verdade

O cabeçalho `RB12` fecha byte a byte:

```
36 (cabecalho) + 56088 (bits) + 64229x2 (offsets) + 64229 (larguras)
= 248811 = tamanho do arquivo
```

| campo | valor |
|---|---|
| maxwidth | 17 |
| height | **18** |
| ascent | 14 |
| depth | 1 = **antisserrilhada, 4 bpp** (ver §15.1) |
| slots declarados | 64229 |
| **glifos reais** | **834** |

Os 63.395 slots restantes apontam todos para o offset 0 — o glifo
padrão. A cobertura real são **76 blocos**:

```
U+0021..U+007E   ASCII
U+00A0..U+017E   Latin-1 + Latin Extended-A
U+0384..U+03CE   grego
U+0401..U+045F   cirilico
U+1EA0..U+1EF9   vietnamita
U+2010..U+25CA   pontuacao e simbolos
```

**Português: coberto inteiro.** Testei Á Â Ã À É Ê Í Ó Ô Õ Ú Ç e as
minúsculas, mais º e °. Nenhum ausente.

> Ressalva: meu renderizador de glifo saiu embaralhado — errei a ordem
> dos bits no formato Rockbox. A conclusão acima **não depende dele**:
> vem da contagem de offsets distintos, que é independente do desenho.

### 12.6 Nada ficou por ler

O `.zip` tem 27 entradas: **20 arquivos e 7 pastas**, e os 20 estão
extraídos. Duas pastas vêm **vazias** (`backdrops/`, `icons/`) porque as
linhas que as usariam estão comentadas no `.cfg`.

---

## 13. Varredura final — o que ainda faltava mapear

Pergunta do mantenedor: *"leu tudo? não tem mais nada a mapear?"*
Fui conferir em vez de responder de memória. Faltavam três coisas.

### 13.1 Nenhum ícone tem transparência — e o degradê está ASSADO neles

O Rockbox usa magenta `(255,0,255)` como cor transparente. **Nenhum dos
16 bitmaps usa magenta.** Todos são opacos, 24 bpp.

Isso levantou a dúvida certa: a bateria é desenhada em `(153,2)`, dentro
da barra em degradê. Se o fundo dela fosse branco, abriria um buraco
branco no degradê. Medi:

| ícone | linha 0 do quadro | degradê em y=2 | |
|---|---|---|---|
| `battery.bmp` | (238,242,246) | (238,242,246) | **idêntico** |
| `playbtns.bmp` | (238,242,246) | (238,242,246) | **idêntico** |
| `hold.bmp` | (238,242,246) | (238,242,246) | **idêntico** |

**O degradê da barra está pintado dentro dos próprios ícones.** Eles não
são recortes: são pedaços da barra com o desenho por cima.

**Consequência para Marte:** esses ícones só compõem certo **naquela
posição vertical**. Colar a bateria em outro `y` deixa uma emenda
visível. Nossa barra tem 17 px de degradê + 1 de separador, igual à
dele — então `y=2` funciona sem ajuste. Mas é uma amarra a respeitar, e
ela some se um dia mudarmos `altura_faixa`.

### 13.2 A barra de volume SUBSTITUI a de progresso

Duas linhas do `.wps` que eu tinha lido mas não interpretado:

```
%?mv(2.0)<%Vd(f)%xd(J)%xd(K)|%Vd(d)>     volume mexido ha 2s? VOLUME : PROGRESSO
%?mv(2.0)<|%al%pc%ar-%pr>                volume mexido? esconde os tempos
```

`%mv(N)` = "o volume mudou nos últimos N segundos?". Então, ao mexer no
volume, a barra de progresso e os tempos **somem** e dão lugar à barra de
volume com os alto-falantes, por 2 segundos.

É esse o "**with Volume Control**" que o nome do tema anuncia.

**Eu tinha desenhado as duas ao mesmo tempo no mockup — errado.**
Corrigido: `marte/mockups/marte_tocando_agora.png` mostra os dois estados.

Outros dois pares do mesmo tipo, agora explícitos:

```
%?C<%Vd(a)|%Vd(b)>       com capa: texto estreito | sem capa: texto largo
%?lh<%Vd(c)|%Vd(e)>      disco ativo: animacao | parado: icone de modo
```

O ícone de disco e o de modo de reprodução **dividem o mesmo canto**.

### 13.3 Inventário de tags: nada sem mapear

Decodifiquei **todas** as tags ativas (ignorando linhas comentadas):

| arquivo | linhas ativas | tags distintas | sem mapear |
|---|---|---|---|
| `NanoClone.wps` | 44 | 45 | **0** |
| `NanoClone.sbs` | 12 | 13 | **0** |

### 13.4 O `.cfg`, linha a linha

| linha | situação |
|---|---|
| `wps` / `sbs` / `font` | §1, §5, §11 |
| `statusbar: off` | a barra é do tema, não do Rockbox |
| `show icons: off` | §12.4 — igual ao nosso S7 |
| **`scrollbar: off`** | **convergência nova:** `CRIA_CONT` já faz `clear_flag(SCROLLABLE)` |
| `line selector *` | §3 — azul em degradê |
| `selector type: bar (gradient)` | §4.1 |
| `foreground` / `background` | §3.1 — tema claro |
| `filetype colours: -` / `ui viewport: -` | desligados pelo autor |
| `hold_lr_for_scroll`, `contrast`, `time format`, `bidir limit`, `scroll speed/delay/step` | **comentados** — não valem |

Três convergências não planejadas com o que já fizemos: sem ícones de
lista (S7), sem barra de rolagem, e a geometria da faixa (§9.2).

### 13.5 O que continua fora de alcance da análise estática

Honestamente, e sem promessa:

1. **A codificação dos pixels da fonte.** Cinco layouts tentados, todos
   falharam — ver §14.2, que registra o que ficou estabelecido e o
   caminho certo (ler `firmware/font.c` do Rockbox). **Ainda não vi a
   fonte desenhada.** Não bloqueia nada.
2. **Se o nosso LVGL honra `BG_GRAD_DIR`/`BG_GRAD_COLOR`.** §4.1 —
   só o aparelho responde.
3. **De onde vem a fonte da interface.** §11.3 — `.data` copiada da
   FIRM, ainda não localizada.

Fora isso, o NanoClone está mapeado: 20 arquivos, 16 bitmaps abertos e
medidos, 3 arquivos de texto decodificados tag a tag, 1 fonte com o
cabeçalho fechando byte a byte.

---

## 14. "Tudo está lido?" — resposta com prova

Terceira vez que o mantenedor pergunta. Em vez de responder de memória,
verifiquei byte a byte.

### 14.1 Nenhum arquivo tem conteúdo escondido

Para cada BMP, conferi se `offset_dos_pixels + linhas_alinhadas × altura`
bate com o tamanho do arquivo:

| resultado | arquivos |
|---|---|
| fecha exato | 3 (`AA Bottom`, `AA Left`, `AA Right`) |
| sobram **2 bytes** | 13 |

Os 2 bytes são `00 00` — padding zero no fim. O `NanoClone.bmp` chega a
declarar `biSizeImage = 69698` contra 69696 reais: o padding está contado
no próprio cabeçalho. É quirk da ferramenta que salvou, não dado.

A fonte fecha **exata**: `36 + 56088 + 64229×2 + 64229 = 248811`.

Nenhum arquivo oculto (`.DS_Store`, `._*`, `__MACOSX`): zero.

**Todo byte de todo arquivo está explicado.**

### 14.2 A exceção honesta: os 56.088 bytes de glifos

Um bloco continua **não decodificado**: a região `bits` da fonte.

O que ficou **estabelecido** (e não depende de desenhar o glifo):

- os offsets são em **bytes**, não em palavras — o maior é 55.980,
  abaixo de `nbits` = 56.088;
- `offset 0` é compartilhado por 63.395 slots — é o glifo padrão, e a
  região começa com 33 bytes `0xFF` seguidos, consistente com um bloco
  sólido de "caractere ausente";
- restam **834 glifos reais**, e a cobertura por bloco (§12.5) sai da
  tabela de offsets, não dos pixels.

O que **falhou**: cinco tentativas de layout — linhas em bytes e em
palavras, bits MSB e LSB, faixas verticais de 8 pixels (o formato nativo
de LCD do Rockbox), e offsets interpretados como palavras. Nenhuma
produziu um 'A' com densidade plausível; todas saem quase sólidas.

Parei por decisão, não por falta de ideia: o campo `depth` pode não
significar 1 bpp, e seguir chutando layout é o tipo de buraco que este
projeto já pagou caro.

> **RESOLVIDO em §15.** O formato foi lido em `firmware/font.c` do
> Rockbox: `depth=1` significa **antisserrilhada 4 bpp**, não 1 bpp. A
> fonte está decodificada e desenhada.

**Se um dia precisar:** o caminho certo não é adivinhar, é ler
`firmware/font.c` do Rockbox, que define o formato.

### 14.3 Situação final

| material | situação |
|---|---|
| `NanoClone.cfg` | lido, linha a linha (§13.4) |
| `NanoClone.sbs` | lido, tag a tag — 13 tags, 0 sem mapear |
| `NanoClone.wps` | lido, tag a tag — 45 tags, 0 sem mapear |
| 16 bitmaps | abertos, medidos, compostos; todo byte explicado |
| fonte — cabeçalho | lido, fecha byte a byte |
| fonte — offsets/larguras | lidos; 834 glifos reais, português completo |
| **fonte — pixels** | **NÃO decodificado** (§14.2) |
| pastas `backdrops/`, `icons/` | vazias no pacote |

---

## 15. A fonte, decodificada — e três correções minhas

O mantenedor mandou fechar o NanoClone antes de voltar ao OpenPod. O que
faltava eram os 56.088 bytes de pixels da fonte. Fui ler o formato no
lugar certo — `firmware/font.c` do Rockbox — em vez de continuar
adivinhando.

### 15.1 O erro era meu, e era de leitura

```
depth = 0  ->  1 bit por pixel,  width * ((height+7)/8) bytes por glifo
depth = 1  ->  ANTISSERRILHADA,  (height*width + 1)/2   bytes por glifo
```

Nossa fonte tem `depth = 1`. Eu li isso como "1 bit por pixel". **É o
oposto:** `depth=1` significa antisserrilhada, **4 bits por pixel**, um
nibble por pixel, nibble baixo primeiro, e o valor é **invertido**
(0 = tinta, 15 = fundo).

Eu estava decodificando 4 bpp como 1 bpp — por isso saía sólido nas
cinco tentativas. Não era layout exótico: era um campo mal lido.

**Correção 1:** a fonte **não é monocromática** (§12.5). É
antisserrilhada de 16 níveis.

### 15.2 A correção que muda o plano

Eu repeti várias vezes que "18 px não cabe numa linha de 16, logo
`altura_linha` iria a 20 e a lista cairia de 8 para 7 itens".

Medi a **tinta real** de 92 glifos (ASCII, acentos, `g j p q y Ç`):

| | |
|---|---|
| `line_height` declarado | 18 |
| `ascent` declarado | 14 |
| **tinta real** | **y = 1 .. 16 → 16 px** |

A linha 0 e a linha 17 são **vazias em todo glifo**.

**Correção 2: a fonte cabe exatamente na nossa linha de 16 px.** O M5
não precisa mexer em `altura_linha`, e a lista **continua com 8 itens**.

Ressalva honesta: cabe **sem folga nenhuma**. `Á` começa na linha 1;
`g`, `j` e o cedilha do `Ç` terminam na linha 16. Os dois extremos
aparecem em português. Qualquer `pad_topo` acima de 0 corta.

### 15.3 A largura também não é problema

Larguras renderizadas dos itens de menu reais, contra os 124 px úteis:

| item | px | | item | px |
|---|---|---|---|---|
| Música | 48 | | Estações salvas | 109 |
| Configurar | 75 | | Armazenamento | 115 |
| Despertador | 87 | | Desligar sozinho | 116 |
| Livro digital | 85 | | Sobre o aparelho | **118** |

**Nenhum dos 15 estoura.** O mais largo sobra 6 px.

**Correção 3:** eu havia tratado a fonte como inviável. Ela é viável em
altura e em largura.

### 15.4 Provas

- `marte/referencia/fonte_14MyriadPro_amostra.png` — a fonte desenhada
  a partir do arquivo, com acentos;
- `marte/mockups/marte_fonte_real.png` — menu em 128×160 com a fonte de
  verdade, comparando linha de 20 px e de 16 px.

### 15.5 O que ainda não sei sobre usá-la

Decodificar não é portar. Continua em aberto:

1. **converter `RB12` → formato de fonte do LVGL** — o firmware espera
   `lv_font_t` com `cmap`/`glyph_dsc`, não o formato do Rockbox;
2. **se o nosso LVGL foi compilado com fonte de 4 bpp** — LVGL aceita
   1/2/4/8 bpp, mas depende de `LV_FONT_FMT_TXT` e do que está ligado.
   A fonte de ícones do firmware tem `dsc` em RAM, o que não ajuda a
   responder estaticamente;
3. **onde a fonte atual da interface mora** (§11.3).

Ou seja: a fonte deixou de ser um **desconhecido** e virou um **item de
trabalho com passos nomeados**.
