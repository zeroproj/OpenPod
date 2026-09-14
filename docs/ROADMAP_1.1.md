# OpenPod 1.1 — o que o mantenedor pediu depois de usar a 1.0

> Lista feita em 2026-09-13, com o aparelho na mão e a 1.0 gravada.
> Cada item tem o que **já foi investigado** e o que **falta**, para a
> próxima sessão não recomeçar do zero.

---

## 1. Tela Informação ilegível — ✅ RESOLVIDO na 1.3/1.4

**A causa era número de linhas, não espaçamento.** Com três mensagens
(título + versão + base) elas se atropelavam; com duas, o layout se
comporta sozinho.

```
1.2  título encurtado (190 px -> 95 px)   resolveu o transbordo horizontal
1.3  versão em UMA linha                  resolveu a sobreposição
1.4  ícone U+F00C removido                tirou o ≡ da frente
```

O ícone estava em `0x00122B14`, pool da função `0x00D229F0` na camada
VIEW — **um único ponto carrega esse literal**, então as outras 18 telas
que usam o mesmo glifo ficaram intactas.

> **Limite prático: duas linhas.** Quem for acrescentar informação nessa
> tela (modelo, capacidade, nº de músicas) vai esbarrar nisso, e a
> solução será o trabalho de layout abaixo — não mais uma string.

### O que ficou por fazer

A função que desenha é `0x00D229F0`: recebe o texto em `[r5,#0x14]`,
cria um rótulo para o ícone e outro para o texto. Quem quiser mais de
duas linhas precisa achar ali a altura de linha e o tamanho do contêiner.

### O registro do caminho errado

Passei um bom tempo procurando altura de linha na camada VIEW enquanto a
evidência estava na foto: cada encurtamento melhorava um pouco, e o que
resolveu foi **remover uma linha inteira**. Testar a hipótese barata
antes de caçar a causa profunda teria economizado uma versão.

## 1b. (histórico) o diagnóstico inicial

**O que já sei.** `page_info` (0x00D0A4C8) monta só duas coisas: o título
(`get_string(43)`) e a versão, que vem de um literal — não da tabela de
idiomas. Os ids 44 (`Número da versão`) e 156 (`TP version:`) são
**strings mortas**, nunca buscadas.

O texto vai para uma caixa via `0x00D0D818` / `0x00D0D880`, com
`strlen + 9` guardado em `[r4,#0xa]`.

**O que falta.** Descobrir a geometria dessa caixa — largura, quebra de
linha, espaçamento. O amontoado provavelmente é falta de `pad` e de
altura de linha, os mesmos parâmetros que resolvemos nas listas.

**Custo estimado.** Baixo se for questão de estilo (pad/line-height);
médio se for preciso recriar a caixa.

---

## 2. Navegação dos botões — ⚠️ NÃO É DEFEITO (fechada na 1.8)

> **O item estava mal formulado.** `0x81` é o **VOL** e `0xA0` é o **M**
> — respondido pelo aparelho. Nas subtelas o VOL volta e o M não faz
> nada, e **isso é o padrão do produto**: censo no firmware de fábrica
> dá 41 de 49 telas para cada um.
>
> A 1.7 inverteu os dois (M volta, VOL desce) e o mantenedor preferiu o
> original. **Revertido na 1.8.**
>
> O que sobrou de valioso: o mapa de teclas, e a descoberta de que
> `0x00D47654` (`lv_group_send_data`) é um **ponto único** por onde passa
> toda tecla de toda tela — 1 gancho muda o mapeamento inteiro.
> `tools/patch_navegacao.py` fica no repositório, desaplicado.
>
> **O que continua verdadeiro:** na home o VOL navega, nas subtelas ele
> volta. O mesmo botão, dois significados. Alinhar exige mexer na
> **home**, e tiraria dela dois botões que hoje funcionam — decisão do
> mantenedor.
>
> Detalhe em `docs/BUTTON_ANALYSIS.md` §8 e §9.

### O diagnóstico antigo, preservado


**O que já sei.** São `btn_process` diferentes. A home usa o da página 1;
Extras e Configurar usam os seus. A home tem o comportamento que o
mantenedor aprovou: M e Vol pulam 3, Voltar e Passar pulam 1, Play entra.

**O que falta.** Comparar os três `btn_process` lado a lado e listar onde
divergem. É leitura de código, não tentativa.

**Custo estimado.** Médio. Provavelmente trocas de constante, como foi
com os divisores — mas pode haver ramos de tecla que simplesmente não
existem nas outras telas.

---

## 3. Cor da seleção — ✅ COMPLETA na 1.6 (V055)

> A cor saiu na 1.1; **o raio saiu na 1.6, em 1 byte.**
>
> O diagnóstico abaixo (*"o arredondamento vem do tema por um caminho que
> não é chamada de setter"*) **estava errado**. Vem de chamada de setter,
> sim: `0x00D4D064`, propriedade **96**. As duas tentativas usaram a
> propriedade `0x0B`, que na LVGL v8 é `TRANSFORM_HEIGHT`.
>
> A frase *"a propriedade 0x0B nunca é usada como estilo no firmware"*
> era um fato verdadeiro que levou à conclusão errada: ela não é usada
> porque **não é o raio**, não porque o raio viesse de outro lugar.
>
> Tabela completa de propriedades em `docs/GUI_ANALYSIS.md`.

### O diagnóstico antigo, preservado


**A cor foi unificada** (1.1): uma rotina no criador de linha
compartilhado aplica `palette_main(7)` no estado `FOCUS_KEY`, e as 39
telas passaram a usar a cor da home.

**O raio NÃO.** A seleção da home é quadrada; a das listas continua
arredondada. Duas tentativas falharam:

```
patch_raio_selecao.py   chamou o despachante com prop 0x0B  ->  sem efeito
```

**O que a varredura provou:** a propriedade `0x0B` (`LV_STYLE_RADIUS`)
**nunca é usada como estilo** no firmware inteiro. As 14 ocorrências de
`movs r1,#0xb` são `ctrl_id`, coisa diferente.

**Conclusão:** o arredondamento vem do tema da LVGL por um caminho que
não é chamada de setter — provavelmente uma tabela de estilo em flash.
Achar exige desmontar a inicialização do tema.

> **Não tentar de novo por dedução.** Já custou uma versão. A propriedade
> `0x000B` foi deduzida do padrão dos outros setters e estava errada, ou
> o caminho não passa pelo despachante.

## 3b. (histórico) o diagnóstico original

**O que já sei, e é a parte boa:**

```asm
home        00D2EB42  movs r0, #7   ; bl palette_main  (navegação)
            00D2EDB2  movs r0, #7   ; bl palette_main  (criação)
listas      nada — a cor vem do TEMA da LVGL
```

A home **pinta explicitamente** com a paleta 7. O criador de linha
compartilhado (`0x00D21764`) só define fundo preto e cor de borda
(paleta 0x12); a cor do estado selecionado nunca é definida, então cai no
padrão do tema.

Existe o seletor de estado, e o firmware já o usa em 5 lugares:

```
seletor 0x00000004 = LV_STATE_FOCUS_KEY
ex. 0x00D21D44: palette_main(5) -> set_style_bg_color(obj, cor, 4)
```

**O desenho.** Acrescentar ao criador de linha compartilhado uma chamada
`set_style_bg_color(linha, palette_main(7), 0x04)`. **Uma rotina na área
livre, um gancho — e as 39 telas passam a usar a cor da home.**

**Custo estimado.** Baixo. É o mesmo padrão da barra de rolagem: gancho
numa chamada existente de `0x00D21764` + rotina na área livre.

---

## 4. Barra superior em todas as telas — ✅ FEITA na 1.6 (V054)

> **A estimativa abaixo estava errada, e vale a pena saber por quê.**
> Ela dizia *"a única dos quatro que exige criar objeto"* e previa custo
> alto. Não exige: o criador do rótulo do título (`0x00D226AC`) já existe
> desde o V017, e `view_icon_create` já tem o número da página corrente
> na mão quando roda. O trabalho real foi **1 gancho de 30 bytes** e uma
> rotina de tabela de 88 bytes na área livre — 37 telas de uma vez, e
> 2 bytes por tela nova daqui em diante.
>
> O erro de estimativa veio de olhar o problema **pela camada da página**
> (onde de fato seria preciso criar objeto em cada uma) em vez de pela
> **camada view**, que já desenha a bateria em todas elas. Detalhe
> completo em `docs/STATUS_BAR.md` §14.
>
> O desenho original, preservado abaixo, previa `tabela + rotina + gancho
> por tela`. Acertou a forma e errou a quantidade de ganchos: **um só**.

### O diagnóstico original



**Sim, e o caminho está claro.** Mas é a única dos quatro que exige
**criar objeto**, não ajustar constante.

**O que já sei.**

- Os textos dos títulos **já existem**: id 216 `Extras`, id 10
  `Configurar`, id 3 `Vídeo`, id 6 `Rádio`, id 8 `Pastas`...
- A home já tem a barra: relógio, título e separador, documentados em
  `docs/STATUS_BAR.md`.
- As telas do sistema têm uma faixa no topo, mas só com a bateria.

**O desenho que eu proporia.**

```
tabela  página -> id do título     (na área livre)
rotina  compartilhada: cria o rótulo, busca o texto, posiciona
gancho  em cada tela, apontando para a rotina
```

Uma rotina serve todas — é o mesmo padrão do módulo de roteamento da
V029, que funcionou. O custo por tela vira **4 bytes de gancho**.

**Custo estimado.** Alto para a primeira tela (criar a rotina, achar onde
pendurar, acertar a geometria), baixo para as seguintes.

**Risco.** Criar objeto mexe com `malloc`. É o aviso da `MENU_LISTA.md`
§14: **corrupção de heap não aparece na verificação byte a byte.** Montar
inteiro, validar por disassembly, e ter o kit de reversão pronto.

Hoje isso é muito menos assustador que antes: se quebrar, `Volume↓ +
Reset` recupera, e a partir da 1.0 o cartão SD também.

---

## Ordem sugerida

```
3. cor da seleção      barato, muito visível, uma rotina serve 39 telas
1. tela Informação     barato ou médio, incomoda todo dia
2. navegação           médio, é leitura de código
4. barra superior      caro, mas é o que fecha o visual do nano
```

Fazer o 3 primeiro dá o maior ganho pelo menor risco — e exercita de novo
o padrão "gancho + rotina na área livre" antes do item 4, que é o
difícil.
