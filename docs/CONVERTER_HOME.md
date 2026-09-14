# Converter a home para o caminho padrão — a análise antes do código

> 2026-09-14. Autorizado pelo mantenedor: *"vamos iniciar. Único; quando
> resolvermos as cores e o espaço fazemos o submenu Extras."*
>
> **Decisão registrada: a home convertida fica com os nove itens numa
> lista única.** O submenu vem depois.

---

## 1. Primeiro, um erro meu, corrigido

Adiei esta conversão três vezes alegando **risco de aritmética de
alocação**, por analogia com o `make_extras_menu`. Medido:

```
page_home_event_cb        NENHUMA chamada de alocacao
page_home_menu_event_cb   NENHUMA chamada de alocacao
```

O `make_extras_menu` precisou de ponteiro porque **mudou a quantidade de
itens** da página 0x53 (3 → 6), e o buffer é dimensionado pela contagem.
A home já tem nove itens e já tem o espaço deles.

**A conversão não encosta em alocação.** O argumento que me fez adiar era
falso, e a medição custou dois comandos.

---

## 2. O que a home faz hoje — o laço, decodificado

`0x00D2ECEE` … `0x00D2ED8E`, com `r5` como índice em bytes:
`adds r5,#4` e `cmp r5,#0x24` → **9 voltas**.

Por item:

```
bl get_string                        texto do item
bl label_set_text(r6, texto)
bl 0xD2E948 -> cor_texto             set_style_text_color(r6, cor, 0)
bl label_set_long_mode(r6, 0)
bl 0xDA3040                          nossa rotina (bg_opa do rotulo)
movs r2,#0xF ; movs r1,#0x74
bl 0xDA5780                          nossa rotina (altura_linha)
mov.w r1,#0x8000 ; bl 0xD49204       flag do objeto
ldrsh r1,[sp+0x28 + r5]              x  da tabela de coordenadas
ldrsh r2,[sp+0x28 + r5 + 2]          y  idem
bl 0xDA5760                          nossa rotina (posiciona)
str sb,[sl,#4]!                      guarda o ponteiro (array 1)
str.w r6,[sl,#0x24]                  guarda o ponteiro (array 2)
```

**A home cria NOVE RÓTULOS SOLTOS**, posicionados por coordenada
absoluta. Não existe objeto de linha, nem contêiner.

### É por isso que ela não obedece a tabela

- **não há linha para pintar** → `cor_tela` não a alcança, e o fundo dela
  é o fundo do display;
- **a seleção precisa pintar o fundo do próprio rótulo** → daí os dois
  pontos que produziram a "segunda seleção";
- **o espaçamento vem da tabela de coordenadas**, não de `PAD_ROW`.

Três queixas do mantenedor, uma causa só.

### 2.1 O laço inteiro — corrigido depois de ler o miolo

A primeira leitura viu um rótulo por item. **São dois objetos por item.**

```
r7 = conteiner            <- criado antes; recebe PAD_ROW e PAD_COLUMN = 0
fp = tabela de coordenadas
sp+0x4C = tabela de ids de texto

laco, r5 = 0 ate 0x24 de 4 em 4        (9 voltas)

    sb = 0xD5D850(r7)                  objeto 1 — o icone/quadro
    flag(sb, 2) ; add_event_cb(sb, ...) ; flag(sb, 0x8000)
    x = ldrsh[fp+r5] ; y = ldrsh[fp+r5+2]
    0xDA5760(sb, x, y)                 posiciona por COORDENADA ABSOLUTA

    r6 = lv_label_create(r7)           objeto 2 — o rotulo, IRMAO do 1o
    texto = get_string(tabela[r5])
    label_set_text(r6, texto)
    set_style_text_color(r6, cor_texto, 0)
    label_set_long_mode(r6, 0)
    0xDA3040(r6, 0, 0)                 nossa rotina: bg_opa do rotulo
    0xDA5780(r6, 0x74, 0xF)            nossa rotina: largura/altura
    flag(r6, 0x8000)
    0xDA5760(r6, x, y)                 posiciona tambem por coordenada

    guarda os dois ponteiros nos arrays
```

**Os dois são irmãos, filhos do contêiner, posicionados um sobre o outro
por coordenada.** Não há linha: o "fundo" de um item é o objeto `sb`, e o
texto é um objeto separado por cima.

> Isto fecha a última dúvida sobre o cinza da home: o que parece fundo de
> item é `sb`, pintado por conta própria; o `cor_tela` nunca teve onde
> pegar.

---

## 3. O molde, do próprio firmware

`page_home_menu_event_cb` (página 0x53) monta a lista do jeito certo, e
já está decodificado em `docs/PADRONIZAR_HOME.md` §3.1:

```
CRIA_CONTEINER uma vez
laco por item:
    r4 = CRIA_LINHA(conteiner)
    altura, borda, add_event_cb
    rotulo = CRIA_ROTULO(r4)        <- o rotulo mora DENTRO da linha
    largura, long_mode, texto
```

---

## 4. O plano

Trocar o corpo do laço. O que sai e o que entra:

| hoje | depois |
|---|---|
| `sb` = objeto solto + rótulo IRMÃO | `sb` = `CRIA_LINHA(conteiner)`, rótulo **dentro** de `sb` |
| os dois posicionados por coordenada | as linhas se empilham pelo layout do contêiner |
| `bg_opa` no rótulo para a seleção | estado da linha, como nas 36 telas |
| altura por `0xDA5780` | `altura_linha` da tabela, pelo helper |

### O ponto que ainda não sei

O contêiner `r7` é criado por `0xD5D850`, **não** por `CRIA_CONTEINER`.
Para as linhas se empilharem sozinhas ele precisa do **layout** que o
`CRIA_CONTEINER` configura — no molde da 0x53 nada posiciona as linhas, o
que só funciona se o contêiner tiver layout.

**Então a conversão provavelmente precisa trocar `r7` por
`CRIA_CONTEINER` também.** É mais um gancho, e é a parte que eu ainda
não confirmei. Se o layout não vier, as nove linhas empilham em cima umas
das outras — falha visível na hora.

**Os ponteiros continuam sendo guardados** nos mesmos dois arrays — a
navegação não muda. É o objeto guardado que passa a ser a linha.

### Pontos de gancho, todos já nomeados

```
0x0012ECEE..0x0012ED8E   o corpo do laco     <- rotina nova
0x0012EB42               selecao, navegacao  <- passa a ser estado
0x0012EDB2               selecao, criacao    <- idem
```

Mais um ponto novo, antes do laço, para criar o contêiner uma vez.

### O que pode dar errado

**A home não desenhar.** É visível na hora, e o `.up` da 2.3 desfaz.
Não há risco de heap — medido na §1.

O que exige cuidado é que os dois arrays de ponteiro continuem coerentes:
a navegação lê deles para mover a seleção. Se guardarmos a linha num e o
rótulo no outro, a seleção pinta o objeto errado.

### Como será escrito

Com o **clang**, por `tools/asm.py`, iterando até convergir — nunca à mão.
Os dois piores bugs deste projeto vieram de montar Thumb-2 na mão **e**
escrever o verificador a partir da mesma suposição errada.

---

## 5. O que esta conversão NÃO resolve

- os **84 pontos** que pintam fundo fora da tabela (censo de 14/09);
- os **24 pontos** de cor de texto com origem não identificada;
- os dígitos do relógio;
- o "cinza" atrás do texto.

A conversão resolve a **classe da home** — que é a que reapareceu quatro
vezes — e nada mais. Dizer o contrário seria repetir o erro de hoje.
