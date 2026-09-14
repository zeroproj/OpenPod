# OpenPod Core 2.2 — a lista limpa do nano

```
Base       OpenPod Core 2.1.1
Receita    tools/build.py --receita marte
Gerada     2026-09-14
Status     EXPERIMENTAL
Diff       1 byte
```

**Um byte.** É o menor patch da história do projeto, e fecha a lista do
mockup.

---

## 1. O que a 2.1.1 provou no aparelho

```
Configurar   os rotulos VOLTARAM, todos legiveis          OK
home         9 itens, fundo branco, texto preto           OK
selecao      barra azul com texto BRANCO, nas duas telas  OK
```

O conserto de 8 bytes funcionou. **E o tema claro do nano está de pé.**

> **Correção de leitura minha:** eu disse, olhando a foto da 2.1, que o
> texto do item selecionado na home estava escuro. Na foto da 2.1.1 ele
> está branco, como nas listas. Provavelmente eu li mal a foto anterior —
> o item que eu havia aberto como defeito (b) não existe.

---

## 2. O que falta para o alvo, e o que esta versão tira

Comparando com `marte/mockups/marte_completo.png`:

```
fundo branco, texto preto        ✅
selecao azul, texto branco       ✅
sem icones de linha              ✅
sem barra de rolagem             ✅
SEM TRACO ENTRE OS ITENS         <- esta versao
degrade da faixa e da selecao    falta (M2/M3)
titulo centralizado              falta
bateria colorida                 falta (M4)
```

---

## 3. O byte

```
00D2178A   movs r0, #0x12
00D2178C   bl   palette_main            <- a cor vem da PALETA da LVGL
00D21796   bl   set_style_border_color
00D2179E   movs r1, #1   ->   #0        <- ESTE
00D217A0   bl   set_style_border_width
```

A cor da borda da linha nunca teve campo na tabela — **oitava vez** que
um valor de aparência mora fora dela. Zerando a largura, a cor deixa de
importar.

### O setter, conferido e não suposto

```
0x00D4D0F4   movw r1, #0x1032 ; b.w 0xD4CAC4
             0x32 = 50 = LV_STYLE_BORDER_WIDTH   (LVGL v8)
```

Desmontei o wrapper e li o número da propriedade, em vez de confiar no
nome.

### O traço da faixa FICA

Os dois são objetos diferentes, e a ferramenta confere os dois:

```
0x0012174C   CRIA_FAIXA   border_width = 1   <- FICA, e o y=17 do nano
0x001217A0   CRIA_LINHA   border_width = 1   <- vai a ZERO
```

> **A confusão que eu já tinha feito:** `faixa_separador`, no
> `nanoclone.json`, é a linha **embaixo da barra**, não entre os itens.
> Se eu tivesse "consertado" por ali, teria tirado o traço certo e
> deixado o errado.

---

## 4. Validação

```
validate_firmware   21 OK + a falha de CRC da R1
diff contra a 2.1.1  1 byte, 1 setor, offset 0x12179E
OK  nada abaixo de 0x00D000   OK  0x00D000 intocado   OK  PSMP intocada
imagem  92e9590de62b9c34393b4c6e5610daa8d26f875f58edeaf9f5bffbb723734ebb
kit     2 setores, 8 KiB
```

---

## 5. O que olhar

1. **As listas ficaram limpas?** Sem traço entre os itens, como no
   mockup.
2. **O traço embaixo da faixa continua lá?** É o único que deve
   sobreviver.
3. Comparando a tela com `marte/mockups/marte_completo.png` lado a lado:
   **o que ainda destoa, além do degradê e da bateria?**

O item 3 é o que vale mais. A partir daqui a pergunta deixa de ser "ficou
bom?" e passa a ser "bate com o alvo?".
