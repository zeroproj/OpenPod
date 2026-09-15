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

> ⚠️ **Isto ainda NÃO foi medido nesta linha.** Os endereços vêm dos
> relatórios das tentativas antigas, não de medição minha. O mapa `boot`
> do `disasm.py` usa outra base e eu não completei a leitura.
>
> **Medir essa tabela é o passo 1, e é pré-requisito de tudo.**

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
