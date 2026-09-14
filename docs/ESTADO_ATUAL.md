# Estado atual — leia isto primeiro

> Atualizado em 2026-09-13, depois da barra superior, do raio e da
> navegação.
> **Este é o documento de entrada.** Depois dele: `CLAUDE.md` (regras do
> projeto), `PROTOCOLO_GRAVACAO.md` (como gravar), `MODO_DOWNLOAD.md`
> (como recuperar), `ROADMAP_1.1.md` (o que falta).

## Onde o aparelho está

```
OpenPod 3.0        (interno V100)   <- RECONSTRUIDA do ORIGINAL, aguardando teste
                                      primeira imagem gerada por receita declarada
                                      (tools/build.py, 22 passos). SEM o Extras.
OpenPod 2.4        (interno V077)   <- gravada; melhor versao testada ate agora
OpenPod 2.2        (interno V073)   <- gravada antes
OpenPod 2.1        (interno V070)   <- gravada antes; defeitos 1,2,5,6 seguem abertos
kit e .up em       OpenPod 3.0/
anterior           OpenPod 2.0       (interno V060)
releases antigas   historico/releases/
```

> **Regra de processo (mantenedor, 2026-09-14):** nenhuma versão nova é
> gerada sem ele pedir. Corrige-se, valida-se, e só então se empacota.
> A próxima será a **2.2**.

> Arquitetura do firmware (MVP, camadas, caminho da tecla): `docs/ARQUITETURA.md`
> Tabela de simbolos recuperada (412 funcoes): `docs/SIMBOLOS.md`
> Cobertura medida do firmware (o que sabemos e o que não): `docs/COBERTURA.md`

## 🔴 DEFEITOS ABERTOS DA 2.1

| # | defeito | o que já se sabe |
|---|---|---|
| 1 | **faixa clara vazia** sob o título | **CAUSA PROVÁVEL ENCONTRADA — ver `ARQUITETURA.md` §12.** O fundo do display é **BRANCO**: `lv_disp_drv_register` escreve `0xFF` em três bytes consecutivos do `lv_disp_t` (`0x001567F6`) logo antes de criar as telas — o padrão de `disp->bg_color = branco; bg_opa = COVER` do LVGL v8. E **nenhuma página pinta o fundo da tela**. Logo, tudo que a faixa e o contêiner não cobrem aparece branco. Nas listas isso é a fresta entre o fim da faixa (`y=17`) e o início do contêiner (`y=19`). **Descoberta colateral grave: `cor_tela` da nossa tabela tem UM único leitor** (o thunk do S12, página 0x18) — ela é praticamente morta, e por isso o `DIAGNOSTICO cores/update.up` **não consegue testar este defeito**. Gravá-lo teria sido perda de tempo. **Teste certo, de 1 byte:** trocar `movs r3,#0xff` por `movs r3,#0x00` em `0x001567F6` e ver se a faixa fica preta |
| 2 | **título colide** com contador na lista de Música (`Músi̶ta̶52`) | nosso título é `TOP_MID x_ofs=+4` (`0x001226AC`). A faixa também desenha rótulos em `TOP_LEFT x=40` e `TOP_RIGHT x=−45`, que juntos ocupam x 40..83 — o centro. **Mas esses dois são ícones** (glifos U+E6xx/U+F2xx da fonte de ícones), não o contador: o contador em si **ainda não foi localizado**; a página 0x03 (`page_music_song`) só faz um `align(CENTER)` e um `set_width`. Não corrigido: mover o título sem saber o que colide seria chute |
| 3 | ~~**fundo branco** na página 0x18 (Gravação)~~ **CORRIGIDO (S12, V072)** | `0x00122F5A` pinta `BG_COLOR` do estado normal com o getter de **texto** (`0x00D21384`). **Correção de registro: não é bug nosso.** No firmware de fábrica esse getter já era `mov.w r0,#-1` (branco) — a V013 não mudou nada aqui. São 2 objetos, ambos da página 0x18, com três estados: normal branco, `LV_PART_SELECTED` = `palette(7)`, foco = `palette(0xE)`. A correção não foi pintar de preto: foi fazer o fundo ler `cor_tela` (+0x00), o campo que existe para isso. Os outros dois estados (`LV_PART_SELECTED`, foco) são estado e não padronização — ficam intocados |
| 4 | ~~**altura da linha não centralizada**~~ | **CORRIGIDO (S11, V071).** E era pior do que eu havia anotado: não eram 35 pontos com valor coincidente — eram **38 pontos com DUAS alturas**. 28 usavam o imediato **10 px**; 10 calculavam `160/10` = **16 px**. A tabela e a home dizem 16, então as 28 é que divergiam: listas mais apertadas e seleção 6 px mais baixa que a da home. Os 38 agora leem `altura_linha` (+0x0D). `audita_chrome.py` passou a conferir a linha — e o novo teste **acusa a V070 e aprova a V071**, que é a prova de que o ponto cego fechou |
| 5 | **vão de 5 px** abaixo da faixa nas 14 telas sem lista | **DIAGNOSTICADO, correção pronta para aplicar.** A causa exata: essas telas calculam a própria geometria a partir de `tela/7`. Com `r7=7`: faixa = `160/7` = **22**, contêiner = `160−22` = **138**, alinhado ao RODAPÉ → topo em `y=22`. O S9 baixou a faixa para 17 e **não tocou no contêiner**, então sobra o vão de 22−17 = **5 px**. A correção é desviar o `set_h` do contêiner para o thunk `cont_h` (`0x00DA530C`), que faz `160 − inicio_lista` = **141**; como o alinhamento é ao rodapé, o topo cai exatamente em `y=19`, igual às listas. **12 dos 15 contêineres** têm o padrão uniforme (`set_h` + `align` BOTTOM=5) e aceitam a correção direta: páginas 0x08 0x0F 0x11 0x1F 0x2B 0x2C 0x2D 0x2F 0x31 0x44 0x4F 0x52. **Três precisam de exame individual:** 0x0D (`0x0012B9AE`, sem align no rastro) e os dois contêineres da 0x19 (`0x001359F2` sem align; `0x00135FF2` sem set_h) |
| 7 | ~~**Extras: clicar nao leva a nada**~~ | **CORRIGIDO (patch_extras_fix, V073).** O `patch_extras` da 2.1 mandava a mensagem para a **entrada** de `page1_process`, que exige `msg[0x0a]==2`; o Extras chega com `==4` e ela morria em `0x00100F66`, antes do `tbh`. Tabela, mapa e rotina estavam certos — o trajeto e que nao era. **A correcao obvia (escrever 2 no campo) seria um bug silencioso**: a cauda `0x00101036` le `[0x0a]` e o repassa junto com `[0x08]`, e e isso que faz o "voltar" retornar ao Extras em vez da home. A rotina agora entra em `0x00100FB2` (direto no despacho, depois de guardas que `pstr_page84_process` ja fez identicas) e monta `r6` com o global `0x00823D05`, que a cauda `0x0010101C` **le antes de escrever**. Simulacao estatica: os seis indices caem nos seis handlers certos |
| 6 | **barra da home no descanso de tela** | não existe página de descanso; o chrome sobrevive porque não há transição de página |

### O que a 2.1 ACERTOU, confirmado na tela

```
as 50 faixas com a mesma altura        home limpa
Configurar praticamente correta        tema em tabela de 19 bytes
```

**Não confirmado ainda:** se os seis itens do Extras abrem as telas certas.

O mantenedor atualiza **pelo cartão SD**, não por cabo. O `.up` sai junto
de todo kit, automaticamente.

## Como gravar

```
1. copie  OpenPod 1.8/OpenPod 1.8.up  para a raiz do cartão como  update.up
2. Configurar → Atualizar por SD → Sim
3. o aparelho reinicia e se atualiza sozinho
4. APAGUE o update.up do cartão
```

O `.up` **não confere estado** — reescreve a imagem inteira, então
funciona a partir de qualquer versão. Não existe "gravar o kit errado".

## Como recuperar, se quebrar

```
USB conectado  ->  segure VOLUME ↓  ->  aperte RESET
```

O aparelho enumera como `301a:2800` e a flash fica toda acessível, mesmo
com o firmware destruído. Foi assim que o primeiro aparelho voltou depois
do incidente da V028. Material em `historico/recuperacao/`.

**Este hardware é recuperável por software, sempre.** A ROM de máscara
roda antes de qualquer coisa que a gente escreva.

## O que foi feito

| | |
|---|---|
| home | lista estilo nano, barra de seleção de borda a borda, sem chevron |
| Extras e Configurar | mesma altura de linha, sem engrenagem, sem separador, mesma cor |
| todas as listas | rolagem escondida (59 telas), largura de texto igual |
| textos | 175 revisados; cabem em 113 px: 124 → 176 |
| tela Sobre | título curto, versão em uma linha, sem ícone |
| atualização por SD | `Configurar → Atualizar por SD` arma o flag e reinicia |
| carimbo de versão | automático no gerador de kit (regra R7) |
| **barra superior** | **título em 37 telas, vindo de `get_string` (1.6)** |
| **raio da seleção** | **barra quadrada nas 39 telas, como a home (1.6)** |
| navegação | ~~M volta, VOL desce (1.7)~~ — **revertida na 1.8**, era o padrão do produto |

## O que falta

**1. Acabamento da barra nas subtelas** — o título está lá, mas a faixa
em si continua preta e lisa, com altura diferente por tela (16 px onde o
divisor é 10, 22 px onde é 7). A home tem degradê e separador, pintados
na folha de imagem. Unificar exige mexer no objeto da faixa
(`0x00D216F0`), não na folha. Só depois de ver a 1.7 no aparelho.

**2. ESC morto nas subtelas** — a tecla `0x1B` cai num `pop` puro. Não
foi tocada pela 1.7. Só importa se algum botão emitir `0x1B`; hoje não
se sabe se algum emite.

**3. As 28 telas fora da tabela de navegação** — não tratam `0x12` como
"próximo", então continuam com VOL = voltar e M morto. Entre elas o
**Now Playing**. Cada uma exige olhar o que o `0x12` faz lá.

**4. Página 23 (`page_record_time`) sem título** — tem faixa e linhas,
mas só carrega glifos de ícone; não identifiquei a tela. São 2 bytes na
tabela `TITULOS` quando alguém souber o que ela é.

## O que a 1.7 já confirmou no aparelho

```
barra superior com titulo   OK   nas telas de lista
alturas de linha            OK   "todos no tamanho certo"
codigo na area livre        OK   a rotina do titulo executou
```

Isso fecha a última reserva sobre a área livre: o V017 provou **leitura**
de dado por XIP, o V020 provou **execução**, e agora uma rotina nossa de
verdade roda em produção.

## O que ainda não foi visto na tela

- se alguma das 37 telas ficou com título errado ou sobreposto;
- se a barra de seleção ficou quadrada (o raio entrou junto, na 1.6/1.7);
- se remover o cartão SD na home ainda apaga o título (era defeito da
  1.5; a correção nunca foi reproduzida no aparelho, só no código).

## Onde estão as coisas

```
tools/           20+ ferramentas, cada uma com o porquê no cabeçalho
docs/            30 documentos
firmware/
  ORIGINAL/      GN438_original.bin — sagrado, sha b7cd5eb9...
  WORKING/       a cadeia V001..V053
  VENDOR/        Flashloader SL-DEV oficial da Shenju
historico/
  kits/          82 kits antigos
  releases/      OpenPod 1.0 .. 1.4
  recuperacao/   o que salvou o aparelho
```

## As regras que custaram versão

Estão em `PROTOCOLO_GRAVACAO.md` (R0–R7) e em
`OpenPod_Design_System.md` (R-L1 a R-L3). As três que mais se repetiram:

- **Um caminho corrigido, outro esquecido.** V016, V027, V031, e a barra
  de rolagem. Quando um patch muda a aparência de um objeto, enumerar
  **todos** os pontos que criam ou repintam aquele objeto.
- **Semelhança visual não é evidência de código compartilhado.** Extras e
  Configurar *parecem* a mesma tela e são funções diferentes.
- **Prévia em ASCII prova correção, não estética.** Para decisão visual,
  o aparelho é o único juiz.
