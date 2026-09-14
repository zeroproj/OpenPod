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

## 3. O preço de converter a home

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
