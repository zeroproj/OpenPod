# OpenPod Core 2.3 — o texto branco fixo passa a ler a tabela

```
Base       OpenPod Core 2.2
Gerada     2026-09-14
Status     EXPERIMENTAL
Diff       36 bytes em 3 setores
```

---

## 1. De onde veio

O diagnóstico de cores mostrou: com `cor_texto = AZUL` na tabela, os
dígitos do relógio saíram **brancos**. Não é cor herdada — é branco
escrito no código. No tema claro `cor_tela` é branco, e **branco sobre
branco some**.

Era essa a *"tela que às vezes fica branca"*. Não era falha de redesenho:
é um elemento que desaparece.

---

## 2. O censo, antes de consertar

`set_style_text_color` tem **50 chamadas**:

```
constante/desconhecida ............ 24
getter claro (ja le cor_texto) .... 10
BRANCO FIXO (mov.w r1,#-1) ........  8   <- esta versao
palette_main ......................  6
getter de PRETO ...................  1
getter da home (ja le cor_texto) ..  1
```

Os oito, todos com **r1** como destino:

```
0x00123686  0x001236B0  0x001236CA  0x001238E8  0x00123912
    view_set_icon_bat        (o icone de bateria da faixa)
0x00128DD0  0x00128F14  0x00128FBA
    page_bt_menu_scr_process (o menu Bluetooth)
```

---

## 3. O conserto

`mov.w r1,#-1` ocupa 4 bytes. Um `bl` também. Cada ponto vira chamada a
uma rotina de 12 bytes:

```
00DA6000   ldr  r1, [pc, #4]   ; = 0x00DA5400
00DA6002   ldrh r1, [r1, #6]   ; cor_texto
00DA6004   bx   lr
```

Desmontada da imagem construída, não suposta.

**Sobre o `lr`, que é o risco real:** a rotina escreve em `r1` e `lr`. E
`lr` já está comprometido nesses pontos — a instrução seguinte a cada um
é o próprio `bl set_style_text_color`. Se a função não tivesse salvo
`lr`, já estaria quebrada antes de nós.

**Sobre `r0` e `r2`:** conferido no desassemble de um ponto — `r0` é
carregado **depois** do nosso `bl`, e `r2` antes. A rotina não toca em
nenhum dos dois.

---

## 4. O que esta versão **NÃO** conserta — dito antes, não depois

**Os dígitos do relógio não estão entre os oito.** Eles vêm de um dos 24
pontos de origem não identificada. **A tela de relógio continua com o
defeito.**

Também ficam de fora os 6 pontos de `palette_main` e os 24 desconhecidos.

E o **"cinza" atrás do texto** continua aberto: o diagnóstico provou que
não é a tabela, e eu não escolhi uma causa sem evidência.

---

## 5. A bateria — interino declarado

Cinco dos oito são o ícone de bateria da faixa. Hoje ele é branco sobre a
faixa clara, quase invisível. Lendo `cor_texto`, fica preto e legível.

**Não é o alvo.** `marte/mockups/marte_completo.png` mostra a bateria
**colorida, em verde**, desenhada — e os bitmaps estão em
`marte/adaptado/icones/battery_0*.png`. Isso é o M4.

Preto é a forma legível até lá, e fica registrado como **interino**, não
como pronto. Regra de `MARTE_ALVO.md` §0: onde não se segue a referência,
o desvio é escrito com o motivo.

---

## 6. Validação

```
validate_firmware   21 OK + a falha de CRC da R1
diff contra a 2.2   36 bytes em 3 setores, menor offset 0x123686
OK  nada abaixo de 0x00D000   OK  0x00D000 intocado   OK  PSMP intocada
imagem  f2399318849a0d684c2844c81aa9034a4ceeb0e1ca50d2739485e1d1788ee0ef
kit     4 setores, 16 KiB
```

---

## 7. O que olhar

1. **O ícone de bateria na faixa** — apareceu? Antes era branco sobre
   claro, quase invisível.
2. **O menu Bluetooth** — os textos que sumiam voltaram?
3. **A tela de relógio continua branca?** Deve continuar — não é esta
   versão que a conserta, e se tiver mudado eu errei o censo.
4. Alguma tela que **piorou**? Os oito pontos eram brancos por algum
   motivo; se algum deles estava sobre fundo escuro, agora fica preto
   sobre escuro.

O item 4 é o risco desta versão, e eu não consigo prevê-lo estaticamente:
não sei o fundo de cada um dos oito.
