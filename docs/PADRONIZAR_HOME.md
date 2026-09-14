# Padronizar a home — a medição, antes de prometer

> 2026-09-14. Decisão do mantenedor, depois de ver duas seleções na tela:
> *"Quero padronizado, é mais fácil. Não quero herdar nada da criação
> anterior que está bugado. A base é o Marte, vamos usar o padrão e nos
> adaptar."*
>
> Este documento mede, não propõe de memória.

---

## 1. A home não usa o caminho das outras telas — CONFIRMADO

```
page_home_event_cb       0x12E950   1.212 B   70 chamadas, 39 alvos
    helpers usados:  NENHUM

page_home_menu_event_cb  0x12EF60     992 B   76 chamadas, 42 alvos
    helpers usados:  CRIA_LINHA, CRIA_CONTEINER, CRIA_FAIXA
```

Varredura de `BL` por padrão de bits, não disassembly linear.

**A página 0x53 é uma lista montada do jeito certo, dentro do firmware de
fábrica, a 992 bytes de distância da home.** Existe molde.

### Por que isso é a causa, e não um detalhe

Todo ajuste de aparência precisa ser feito **duas vezes**: uma no caminho
compartilhado (36 telas) e outra na home. Quando uma das duas é
esquecida, nasce um defeito. Já nasceram cinco:

```
V016 · V027 · V031 · a barra de rolagem · a segunda selecao
```

O Saturno escreveu o princípio **P3 — "um caminho de desenho"** e nunca o
cumpriu: o S4 levou a *geometria* e a *faixa* da home para a tabela; o
desenho da lista continuou separado.

---

## 2. O caminho padrão sem nenhum remendo da home — MEDIDO

Rodei os 16 passos do caminho padrão sobre a Core 1.0.1 limpa:

```
14 aplicaram

 2 recusaram, e as recusas dizem coisas diferentes:
    patch_titulos      "id 216 aponta fora da imagem"
                       -> nao e home: falta `relocate --add Extras`. RESOLVIDO
    patch_saturno_s5   "as linhas 0..16 contem indices fora da faixa"
                       -> E home: mexe na folha de imagem dela. SAI
```

Resultado, como receita `core2.2`:

```
1.776 bytes em 30 setores sobre a Core 1.0.1
     (a carcaca herdada eram 8.875 em 36)
validate_firmware  21 OK + a falha da R1
guardas            todas OK
audita_chrome      1 DIVERGENCIA: "home fora da carcaca"  <- de proposito
```

### Os 17 bytes que ainda caem dentro da home

Não escondo: dois passos do caminho padrão alcançam a home.

```
patch_scrollbar3    2 B   0x12EC82        esconde a rolagem
patch_saturno_s6   15 B   5 pontos, entre eles 0x12EB42 e 0x12EDB2
```

Os dois pontos do S6 são **exatamente os dois que pintam a seleção**. Ele
troca a *fonte da cor* — de `palette_main(7)` para a tabela de tema — mas
não mexe em **qual** propriedade é pintada.

**Consequência boa:** sem o `patch_barra_selecao`, os dois pontos voltam
a pintar a mesma coisa (cor de letra), que é o comportamento de fábrica.
**A segunda seleção não existe nesta receita** — ela nascia justamente de
um ponto pintar fundo e o outro, letra.

A home fica com o realce de fábrica, na cor do nano. Feio? Diferente das
outras. Bugado, não.

---

## 3. A leitura lado a lado — o que ela achou

### 3.1 O molde da 0x53, decodificado

```
r6 = 0
laco:
    r4 = CRIA_LINHA(conteiner)                    0xd21764
    altura = tela/7 ; set_height(r4)              0xd4a1ea
    border_side(r4, 2)  e, se r6==2, border_side(r4, 3)
    add_event_cb(r4, handler, 0x0D)               0xd47064
    sl = CRIA_ROTULO(r4)                          0xd5e2e8   <- icone
         set_style_text_font(sl, 0x00CA671C)      0xd4d12e
         set_text(sl, ...)                        0xd5ed94
    sb = CRIA_ROTULO(r4)                          0xd5e2e8   <- texto
         set_width / set_long_mode(sb, 4)         0xd4a1ba / 0xd5ef04
         id = tabela[r6] ; set_text(sb, get_string(id))
    r6 += 1
```

Um laço, uma tabela de ids, três helpers. É o desenho certo, e está
pronto no firmware de fábrica.

### 3.2 A home, ao lado

```
chamadas aos helpers .......... NENHUMA
set_style_text_color .......... 7x
setters de padding na mao ..... 6  (0xD4D01C 028 034 040 04C 058)
funcoes de imagem ............. 0xD55FCC 0xD55FF4 0xD56000 0xD5615C
palette_main .................. 2x
```

São **duas implementações diferentes do mesmo conceito**, não uma
variação da outra.

### 3.3 O fato que muda a recomendação

A página 0x53 tem **três** itens de fábrica. O `make_extras_menu` a
esticou para seis, e a docstring dele diz o que isso custou:

```
Esquema confirmado em page_set_menu (10 itens): rotulos = N*4,
icones = 2*N*4.   botoes 0x00  rotulos 0x18  icones 0x30  malloc 0x4C

⚠️ Este e o unico patch do projeto que mexe em ALOCACAO e aritmetica
de ponteiro. Errar um offset corrompe a heap, e corrupcao de heap NAO
aparece na verificacao byte a byte pos-gravacao.
```

**E é justamente esse o único patch da história do projeto cujo resultado
nunca funcionou no aparelho** — os seis itens do Extras não abrem, depois
de três tentativas empilhadas.

Converter a home para uma lista de **nove** itens por esse molde cai
exatamente nessa classe: alocação e aritmética de ponteiro, com falha que
não aparece na verificação pós-gravação.

---

## 4. Então padronizar tem dois níveis, e eles têm preços muito diferentes

### Nível 1 — padronizar os VALORES  (pequeno, seguro)

A home continua com desenho próprio, mas **todos os seus pontos de cor
leem a nossa tabela**. Medido na Core 2.2:

```
a home tira cor de 7 pontos
   2 ja leem a tabela   (0x12EB42, 0x12EDB2 — o S6 redirecionou)
   5 ainda chamam o getter do TEMA da LVGL
        0x12E9C0  0x12EA1C  0x12EAB0  0x12EB08  0x12ED3C
```

Redirecionar os cinco é **o mesmo gesto que o S6 já fez duas vezes**: 4
bytes por ponto, com guarda. Sem alocação, sem ponteiro, sem heap.

**O que isso resolve:** a classe "mudei a cor e esqueci um caminho" — a
que produziu V016, V027, V031, a barra de rolagem e a segunda seleção.
Passa a existir **um lugar** para mudar cor, e a home obedece.

**O que não resolve:** um recurso *estrutural* novo — uma coluna, um
ícone à direita, uma segunda linha por item — ainda precisaria ser feito
duas vezes.

### Nível 2 — padronizar o CAMINHO  (grande, e na classe que já falhou)

A home desenha pelos helpers, como a 0x53. Resolve tudo, inclusive
estrutura. E entra na aritmética de alocação descrita em §3.3.

---

## 5. Recomendação

**Nível 1 na 2.2, agora.** Entrega o que foi pedido — um lugar só para
mudar, e a home obedecendo — pelo gesto que este projeto já executou com
sucesso duas vezes, e sem encostar na classe que nunca funcionou.

**Nível 2 depois, com os olhos abertos**, e com um teste que a verificação
byte a byte não dá: corrupção de heap só aparece usando o aparelho.

> Não é recuo. É escolher o caminho em que o projeto tem **precedente de
> sucesso** em vez daquele em que tem precedente de fracasso — e a
> diferença entre os dois está medida acima, não suposta.

---

## 6. O preço de converter a home

Reescrever o desenho de `page_home_event_cb` para montar a lista com
`CRIA_CONTEINER` + `CRIA_LINHA`, como a página 0x53 faz.

| | |
|---|---|
| o que muda | só o **desenho**. O roteamento dos 9 itens fica em `page1_process`, intocado |
| molde | `page_home_menu_event_cb`, 992 B, no próprio firmware |
| tamanho provável | a maior rotina que o projeto já escreveu na área livre |
| o que some junto | a classe inteira de defeito "um caminho corrigido, outro esquecido" |
| classe | **HIPÓTESE de viabilidade.** Ninguém ainda leu as 70 chamadas da home uma a uma |

**Não prometo o tamanho.** O passo antes de escrever qualquer byte é ler
as duas funções lado a lado e listar o que a home faz que a 0x53 não faz
— ícones, chevrons, contagem variável, o que for.

---

## 4. A ordem proposta

| versão | o que | estado |
|---|---|---|
| **2.2** | o **caminho padrão** + Marte M1, sem remendo da home | **construída e validada** |
| **2.3** | a home passa a desenhar pelo caminho padrão | precisa da leitura da §3 |

A 2.2 é degrau, e o degrau é honesto: as 36 telas ficam no padrão e com o
tema do nano; a home continua a grade de fábrica, escura. **Vai ficar
visivelmente inconsistente** — é o preço de não herdar o que estava
bugado, e dura uma versão.

Alternativa, se a inconsistência incomodar mais que a espera: segurar a
2.2 e soltar as duas juntas, quando a home estiver convertida.


---

## 7. Duas medições que derrubaram o plano da §5 — 2026-09-14

### 7.1 O Nível 1 já estava feito

Fui redirecionar os cinco pontos de cor da home e olhei o getter antes:

```
ORIGINAL    0x00D2E948   mov.w r0,#-1 ; bx lr        branco fixo
Core 2.2    0x00D2E948   b.w 0xDA5980
            0x00DA5980   ldr  r0,=0x00DA5400
                         ldrh r0,[r0,#6]    <- cor_texto DA TABELA
                         bx   lr
```

**O S10 já tinha redirecionado esse getter.** Os cinco pontos da home
passam por ele, logo já leem a nossa tabela. Eu os rotulei como "getter
do TEMA" na §4 e quase escrevi um patch para algo pronto.

Corrigido: na Core 2.2 a home tira cor de **7 pontos, e os 7 leem a nossa
tabela** — 5 via o getter (`cor_texto`), 2 via a rotina do S6
(`cor_selecao`).

### 7.2 O tema claro e a home de fábrica são incompatíveis

Com a home de fábrica, Marte M1 põe `cor_texto` em **preto**. E a folha
de imagem da home é escura:

```
folha da home  0x0CDD50   128x160 INDEXED_8
   indice   1   13.640 px   RGB(0,0,0)      67% da tela, PRETO PURO
   indice   0      995 px   RGB(254,254,254)
```

**Texto preto sobre preto.** A home ficaria ilegível.

Para a home clarear é preciso que a folha escura saia do caminho — e quem
faz isso é o `make_list_home` + `S5`, que são do desenho próprio da home.

> **Consequência dura:** não existe versão que mostre o tema claro **e**
> evite o caminho próprio da home. As duas coisas estão amarradas.

### 7.3 E a variante que eu propus não compra o que eu achei

Montei a variante "home vira lista, mas sem os dois patches que criaram
a segunda seleção" (sem `patch_barra_selecao`, sem `patch_status_bar`).
Aplicou inteira, e o `audita_chrome` deu **SEM DIVERGÊNCIAS**. Mas:

```
A  variante                          8.806 bytes, 35 setores
B  Core 2.1 (carcaca + fix + Marte)  8.876 bytes, 36 setores
```

São a mesma coisa. A variante **continua levando** `make_list_home`, S4 e
S5 — o desenho próprio da home. Ela só tira a barra de seleção e a string
da faixa. Troca consistência visual por nada.

**Descartada.** A medição matou a ideia, e é melhor assim do que
descobrir na tela.

---

## 8. Onde isso deixa o projeto — honestamente

| caminho | o que entrega | o que custa |
|---|---|---|
| **Core 2.1**, como está | o tema do nano na tela, tudo consistente, o defeito das duas seleções corrigido | carrega o desenho próprio da home, que é a causa da classe |
| **Nível 2** primeiro | a causa resolvida | aritmética de alocação, a classe que nunca funcionou; e nenhuma tela nova até lá |

**Recomendação: usar a Core 2.1 como instrumento, não como baseline.**

Gravá-la responde uma pergunta que só o aparelho responde — *o tema claro
do nano funciona neste display?* — e essa resposta **não depende** de qual
caminho desenha a home. Marcada EXPERIMENTAL, nunca STABLE.

E o Nível 2 segue como o trabalho de verdade, com o molde da 0x53 já
decodificado (§3.1) e o risco já nomeado (§3.3).
