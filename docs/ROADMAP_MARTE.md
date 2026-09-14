# Marte na linha Core — plano de execução

> Escrito em 2026-09-14, depois de ler `docs/PROJETO_MARTE.md` inteiro e
> de **medir** a dependência que ele não explicita.
>
> O estudo do NanoClone está fechado (§14.3 de lá): 20 arquivos, 16
> bitmaps medidos, `.cfg`/`.sbs`/`.wps` decodificados tag a tag, fonte
> com o cabeçalho fechando byte a byte e os pixels decodificados em §15.
> **Este documento não re-estuda nada. Ele diz em que ordem construir.**

---

## 1. O fato que define a ordem

**Marte M1 — inverter a paleta, 12 bytes — é o passo de maior efeito e
menor risco do projeto inteiro. E ele não pode ser o primeiro.**

M1 escreve seis campos da **tabela de tema do Saturno**, em `0x001A5400`.
Na Core 1.0.1 essa tabela **não existe**:

```
Core 1.0.1              FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
linha interface (v101)  00 00 08 82 31 C7 FF FF FF FF 05 FA 11 10 13 00 00 01 00
```

A tabela vem do Saturno, que é **revestimento** sobre as rotinas do
`patch_chrome_padrao`, que por sua vez pressupõe a home em lista.

### Isto foi medido, não deduzido

Apliquei a cadeia de carcaça direto sobre a Core 1.0.1. O segundo passo
recusou, e com um motivo concreto:

```
2. fix_status_bar.py   FALHOU
     indice de paleta 2 esta EM USO na folha — nao pode ser redefinido
     indice de paleta 3 esta EM USO na folha — nao pode ser redefinido
     ...
     os tons da barra do V016 aparecem FORA da faixa superior;
     repintar mudaria outra coisa
```

A folha de imagem da home de fábrica usa os índices de paleta que a faixa
precisaria. Quem libera esses índices é o `make_list_home`.

> **A camada de interface é um bloco interdependente, não um cardápio.**
> É por isso que a receita `interface` existe com aquela ordem: ela é o
> resultado de descobrir essas dependências uma a uma, e não uma
> preferência.

---

## 2. O plano

| versão | o que entra | tamanho | risco |
|---|---|---|---|
| **Core 2.0** | **a carcaça** — receita `interface` inteira | 39 setores | médio |
| **Core 2.1** | **Marte M1** — inverter a paleta | **12 bytes** | baixo |
| **Core 2.2** | correções da carcaça (vão de 5 px, faixa clara) | pequeno | baixo |
| **Core 2.3** | **M2/M3** — degradê na faixa e na seleção | rotina nova | médio |
| **Core 2.4** | **M4** — ícones de estado na faixa | médio | médio |
| **Core 2.5** | **M5** — a fonte do nano | ver §11/§15 do estudo | médio |
| **Core 3.x** | **M6** — Tocando Agora (W1..W5) | grande | W5 alto |

### Por que a 2.0 e a 2.1 são versões separadas

Poderiam sair juntas — a tabela já nasceria com os valores do nano. Mas
aí, se algo ficar errado na tela, não dá para saber se foi a carcaça ou a
paleta. **Separadas, a 2.1 é reversível em 12 bytes** e responde uma
pergunta só: *o tema claro do nano agrada neste aparelho?*

É a mesma lógica que fez a Core 1.0 ser pequena.

---

## 3. Core 2.0 — a carcaça

```
receita     tools/build.py --receita interface
base        Core 1.0.1 (STABLE)
diff        8.925 bytes em 39 setores, menor offset 0x04867C
validacao   21 OK + a falha de CRC da R1; guardas todas OK
```

O que ela traz: home em lista, barra de seleção, rolagem escondida,
faixa superior com a string "OpenPod", título próprio em 37 telas,
as rotinas de chrome e a **tabela de tema** do Saturno (S1–S12).

### O que ela traz de defeito, e é preciso dizer antes

A linha `interface` carrega quatro defeitos abertos, herdados da 2.1/2.2:

| # | defeito | situação |
|---|---|---|
| 1 | faixa clara vazia sob o título | causa provável identificada; hipótese do fundo branco **derrubada pelo aparelho** |
| 2 | título colide com o contador na lista de Música | contador **não localizado** |
| 5 | vão de 5 px nas 14 telas sem lista | **diagnosticado, correção pronta** — 12 dos 15 contêineres aceitam a correção direta |
| 6 | barra da home no descanso de tela | não há página de descanso |

**Nenhum deles é regressão nova: são o estado conhecido dessa camada.**
Entram na 2.0 porque a carcaça é indivisível, e saem na 2.2 — o #5 já tem
o conserto escrito.

> O **Extras continua fora**. Três patches empilhados, os seis itens não
> abrem. Nada na receita finge funcionar.

---

## 4. Core 2.1 — Marte M1, os 12 bytes

Os valores, já com o `LV_COLOR_16_SWAP` aplicado (a tabela guarda
pré-invertido):

| campo | hoje | Marte (RGB565) | grava |
|---|---|---|---|
| `cor_tela` | `0x0000` preto | `0xFFFF` branco | `0xFFFF` |
| `cor_faixa` | `0x8208` | `0xBE39` | `0x39BE` |
| `cor_separador` | `0xC731` | `0x5B0D` | `0x0D5B` |
| `cor_texto` | `0xFFFF` | `0x0000` | `0x0000` |
| `cor_texto_sel` | `0xFFFF` | `0xFFFF` | `0xFFFF` |
| `cor_selecao` | `0xFA05` ciano | `0x2B3B` azul | `0x3B2B` |

**O iPod nano é tema CLARO** — `foreground 000000`, `background FFFFFF`
no `.cfg`. O OpenPod foi para o escuro. Marte não é ajuste de cor: é
inverter o tema inteiro. E, pela tabela do Saturno, isso custa **seis
campos, doze bytes, zero bytes de código**.

Ferramenta a escrever: `tools/patch_marte_paleta.py`, que lê a tabela,
confere que ela existe e está na forma esperada, e troca os seis campos.

---

## 5. O que já convergiu com o nano sem a gente saber

Três coisas que o estudo achou e que **não custam nada**, porque já estão
feitas:

```
sem icones nas listas      o .cfg do nano traz `show icons: off`;
                           o nosso S7 fez igual
sem barra de rolagem       `scrollbar: off` no .cfg;
                           o CRIA_CONT ja faz clear_flag(SCROLLABLE)
geometria da faixa         conteudo comeca em y=20 no nano, y=19 no nosso;
                           faixa de 18 px contra 17+separador
```

E uma em que **somos melhores que o tema original**: o título do nano é
**pintado no bitmap** — `NanoClone.bmp` tem a palavra "iPod" desenhada
dentro da barra, e por isso ela é igual em toda tela de menu. O nosso
`patch_titulos` desenha texto de verdade, por página, vindo de uma
tabela. **Marte não deve copiar isso.**

---

## 6. O que continua em aberto, e não vamos fingir que não

Do estudo (§13.5 e §15.5), sem promessa:

1. **Se o nosso LVGL honra `BG_GRAD_DIR`/`BG_GRAD_COLOR`** — decide o
   M2/M3. Indício forte a favor: o setter de `BG_GRAD` (prop 38) existe
   em `0x0014D0C4`, e o despachante aceita qualquer número de
   propriedade. **PROVÁVEL, não confirmado.** Só o aparelho responde.
   Plano B: cor chapada na média do degradê, `0xDF1C`.
2. **Converter a fonte `RB12` para o formato do LVGL** — e saber se o
   nosso LVGL foi compilado com fonte de 4 bpp. A fonte **cabe**: tinta
   real de 16 px na nossa linha de 16, e nenhum dos 15 itens de menu
   estoura os 124 px úteis.
3. **De onde vem a fonte atual da interface** — é `.data` copiada da
   FIRM para `0x00819xxx`; não existe partição FONT. Se o `dsc` apontar
   para a flash, trocar a fonte é **um ponteiro**.
4. **A capa do álbum é recurso novo**, não adaptação: o firmware lê tags
   ID3 mas não extrai o frame `APIC`. O decodificador JPEG existe (23
   referências), que é a metade difícil. Fase 3, não Fase 1.

---

## 7. A amarra que é fácil esquecer

Os ícones do NanoClone **não têm transparência** e o degradê da barra
está **assado dentro deles**: a linha 0 do `battery.bmp` é exatamente a
cor do degradê em `y=2`. Eles só compõem certo **naquela posição
vertical**.

Nossa faixa tem 17 px de degradê + 1 de separador, igual à dele — então
`y=2` funciona sem ajuste. **Mas se um dia mudarmos `altura_faixa`, os
ícones importados abrem emenda.** Anotado aqui para não ser redescoberto
na tela.

---

## 8. Licença

Os bitmaps do NanoClone são **CC BY-SA 3.0**, de Billy Blair. Usá-los
obriga a creditar, indicar que houve alteração, e licenciar os derivados
sob a mesma licença. Está em `ATRIBUICAO.md`, e **falta repetir na tela
Sobre** quando Marte entrar no aparelho — pendência da versão que
importar o primeiro bitmap dele.

A alternativa mais barata existe e está registrada: o Font Awesome do
próprio firmware já tem play, pause, anterior, próxima, aleatório,
volume e configurações. É monocromático — os do nano são coloridos e com
brilho. **A escolha é de design, e o mantenedor já escolheu os bitmaps.**
