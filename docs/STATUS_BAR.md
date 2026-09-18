# OpenPod — A faixa superior: relógio, bateria e ícones de estado

> Pergunta do mantenedor em 2026-09-12: *"a parte superior, onde fica a
> bateria, o relógio e o chip do SD — aquilo ali é viável mudar?"*
>
> **Veredito: VIÁVEL, e quase tudo é da mesma classe de patch que já
> fizemos — imediato de 1 byte ou ponteiro de pool.** Só o título
> centralizado ao estilo do nano custa mais, e o motivo é curioso.

---

## 1. Por que ela sobreviveu ao V014

A faixa não está na folha de imagem `0x000CDD50`. São **objetos LVGL
próprios**, guardados na estrutura global da view (`0x0081CE2C → [.]`) e
criados por funções da camada view, não da página. Por isso o V014
redesenhou a folha inteira e a faixa continuou lá. **CONFIRMADO** — foi
observado na tela.

---

## 2. Mapa dos elementos

| Elemento | Slot | Criado em | Chamado de |
|---|---|---|---|
| Relógio | `view_p[0x20]` | helper `0x00D217B4` | `0x00D238CA` |
| Bateria | `view_p[0x10]` | `0x00D225B0` | `0x00D237B6` (`view_icon_create`) |
| Ícone BT | `view_p[0x0C]` | `0x00D22744` | `view_icon_create` |
| Ícone SD / gravação | `view_p[0x18]` | `0x00D226F8` | `0x00D238AE` |

Funções de manutenção: `view_icon_create` (`0x00D23740`),
`view_set_icon_bat` (`0x00D2361C`), `view_set_icon_bt` (`0x00D2354C`).

---

## 3. Relógio — `0x00D217B4`

```asm
0x00D217BE   bl   #0xd5e2e8      ; cria label
0x00D217C4   bl   #0xd21384      ; cor do texto = getter do tema (branco)
0x00D217D6   movs r3, #2         ; y_ofs = 2
0x00D217D8   movs r2, #3         ; x_ofs = 3
0x00D217D2   movs r1, #1         ; align = 1  (canto superior esquerdo)
0x00D217DA   bl   #0xd4a3a2      ; align(obj, 1, 3, 2)
0x00D217DE   ldr  r1, [pc, #0xc] ; = 0x00C5D61C  "14:00"   (texto inicial)
0x00D217E2   bl   #0xd5ed94      ; set_text
```

O valor real é escrito depois com
`label_set_text_fmt(obj, "%02d:%02d", h, m)`, formato em `0x00C4CD5D`.

| Mudança | Custo |
|---|---|
| mover na horizontal | **1 byte** (`0x0012_17D8`) |
| mover na vertical | **1 byte** (`0x0012_17D6`) |
| trocar o canto de ancoragem | 1 byte (`0x0012_17D2`) |
| trocar o texto inicial "14:00" | ponteiro de pool, 4 B |

---

## 4. Bateria — `0x00D225B0`

É um **label com a fonte de ícones** mais um `lv_bar` filho que desenha o
nível:

```asm
0x00D2260A   bl   #0xd5e2e8          ; cria o label
0x00D22612   movs r1, #0x6b          ; x = 107
0x00D22614   bl   #0xd4a2d4          ; set_pos(obj, 107, 0)
0x00D2261A   ldr  r1, [pc, #0x84]    ; = 0x00CACFE4   fonte de ícones
0x00D22632   ldr  r1, [pc, #0x70]    ; = 0x00C5D60C   glifo U+E626
0x00D22642   bl   #0xd5b720          ; cria a barra (filho)
0x00D22654   movs r1, #0xd           ; largura 13
0x00D22652   movs r2, #6             ; altura 6
0x00D22662   movs r1, #9 / mvn r2,#2 ; align(9, -3, 0)
0x00D22682   movw r1, #0xcf5d        ; cor de fundo da barra
```

| Mudança | Custo |
|---|---|
| mover na horizontal | **1 byte** (`0x0012_2612`) |
| tamanho da barra | **2 bytes** (`0x0012_2654`, `0x0012_2652`) |
| cor da barra | **4 bytes** (`0x0012_2682`) — **pré-inverter**, `COLOR_SOURCE.md` §9 |
| trocar o glifo | 4 B no pool `0x0012_2632` |

> A cor de bateria fraca é `0x00F8` em `view_set_icon_bat`
> (`0x00D23666`), que **pré-invertida** é `0xF800` = vermelho puro.
> Confirma de novo a regra do `LV_COLOR_16_SWAP`.

---

## 5. O título estilo nano — o detalhe curioso

O nano põe **"iPod" centralizado** no lugar onde aqui fica o relógio.
A tentação é editar a string `"%02d:%02d"` em `0x00C4CD5D` e pronto.

**Não faça isso.** Ela é a **cauda de uma string maior**:

```text
0x00C4CD55   "%02d. %02d:%02d:%02d"
                     ^
                     0x00C4CD5D  aponta AQUI, no meio
```

Sobrescrever os bytes quebraria a string longa, usada em outro lugar para
data/hora completa. É exatamente o tipo de armadilha que o projeto já
pagou caro para aprender: **o dado parecia isolado e não era.**

### A forma limpa

Repontar os **dois** ponteiros de pool que carregam esse formato:

```text
0x0012_3994   pool de view_icon_create        -> string nova
0x0012_4390   pool de watch_view_rec_analysis -> string nova
```

4 bytes cada, mais a string nova gravada em área livre (`0x1A3038`, 364
KiB de `0xFF`, fora da partição FIRM, logo fora do CRC da FIRM).

Com isso o relógio vira um rótulo fixo — *"OpenPod"*, por exemplo — sem
uma linha de código novo. **Custo: 8 bytes + a string.**

> Note a troca: **o relógio some.** Ter título **e** relógio exige um
> objeto novo, e aí é código.

---

## 6. Resumo de viabilidade

| O que | Classe | Custo |
|---|---|---|
| Mover relógio / bateria | dado | 1 byte cada |
| Redimensionar a barra da bateria | dado | 2 bytes |
| Recolorir a barra da bateria | dado | 4 bytes |
| Trocar glifo da bateria | dado | 4 bytes |
| Esconder um elemento | dado | 1 byte (mover para fora da tela) |
| **Trocar o relógio por um título fixo** | dado | 8 bytes + string |
| Título **além** do relógio | **código** | objeto novo |
| Reposicionar os ícones de estado (BT/SD) | dado | a medir em `view_icon_create` |

> **Recomendação:** esconder por deslocamento, nunca por remoção. Mover um
> objeto para fora da tela é 1 byte e reversível em 1 byte; tirar a
> chamada que o cria mexe em fluxo e pode deixar um ponteiro nulo que
> outra função vai desreferenciar. `view_set_icon_bat` já faz
> `cbz r0, sai`, mas nem toda função tem essa guarda — e não conferi
> todas.

---

## 7. Classificação

| Afirmação | Classe |
|---|---|
| A faixa superior são objetos LVGL da camada view, não a folha de imagem | **CONFIRMADO** (disassembly + sobreviveu ao V014 na tela) |
| Relógio em `view_p[0x20]`, `align(1, 3, 2)` | **CONFIRMADO** |
| Bateria em `view_p[0x10]`, `set_pos(107, 0)`, barra 13×6 | **CONFIRMADO** |
| `0x00C4CD5D` é cauda de `"%02d. %02d:%02d:%02d"` | **CONFIRMADO** (leitura direta dos bytes) |
| `0x00CACFE4` é a fonte de ícones da faixa | **PROVÁVEL** |
| `0xCF5D` é a cor da barra, pré-invertida | **PROVÁVEL** — bate com a regra do §9 do `COLOR_SOURCE`, não foi testado na tela |
| Código/strings em `0x1A3038` executam e são lidos por XIP | **PROVÁVEL** — o layout confirma, nunca foi usado |

---

## 8. V016 — o acabamento montado

Decisão do mantenedor: **título E relógio**, reaproveitando o label do
ícone do SD; mais a barra com "leve mudança de cor para mostrar que é uma
barra", como no nano.

### 8.1 O que foi alterado

```text
0x001A3038   8 B  string "OpenPod\0"                    <- ÁREA LIVRE
0x00122740   4 B  ponteiro do texto  0x00C5D608 -> 0x00DA3038
0x00122714   4 B  bl set_style_text_font -> 2x NOP      (usa a fonte padrão)
0x00122708   1 B  align  1 (TOP_LEFT) -> 2 (TOP_MID)
0x00122706   1 B  x_ofs  0x28 (40)    -> 0x04
0x00122702   1 B  y_ofs  0x00         -> 0x02
0x000CE15C   px   linhas 0..15 da folha: degradê, separador e respiro
0x00D00C     2 B  CRC-16 da FIRM  0x7567 -> 0x1A7D
```

**1 812 bytes, 4 setores.** Ferramenta: `tools/patch_status_bar.py`.

### 8.2 Por que a fonte virou NOP em vez de outro ponteiro

Para o label do SD virar texto, ele precisa deixar a fonte de ícones
(`0x00CACFE4`) e usar a fonte de texto. **Eu não sabia o endereço da fonte
padrão** — e em vez de procurar, apaguei a chamada:

```text
0x00122714   bl lv_obj_set_style_text_font   ->   NOP ; NOP
```

Sem estilo de fonte, o objeto herda a do tema — é exatamente o que o
label do relógio (`0x00D217B4`) faz, e ele mostra dígitos corretamente.
**Não descobrir o endereço saiu mais barato e mais seguro do que
descobrir.** A instrução anterior que carregava o ponteiro vira código
morto inofensivo.

### 8.3 A barra, em pixels da folha

```text
y  0.. 3   índice 234  (46,50,55)   topo mais claro
y  4.. 8   índice  33  (31,35,41)
y  9..12   índice  84  (28,32,38)   base mais escura
y 13       índice 181  (61,65,70)   separador
y 14..15   índice   1  (0,0,0)      respiro
y 16..     lista
```

A primeira tentativa usou o índice 181 no topo e o separador em y=15.
Na prévia a barra ficou clara demais e a linha colava na palavra
"Música". **Foi a prévia renderizada que pegou isso, não o aparelho** —
é para isso que `tools/preview_home.py` existe.

### 8.4 Geometria conferida na fonte do firmware

```text
relógio  "88:88"    31 px   x   3 ..  34
título   "OpenPod"  52 px   x  42 ..  94     folga  8 px / 13 px
bateria                     x 107 ..
```

A ferramenta **recusa** um título que encoste no relógio ou na bateria.

### 8.5 O que este patch prova para o V017

A string foi para `0x001A3038` — os 364 KiB de `0xFF` fora de todas as
partições, que o `FIRMWARE_MAP.md` chama de *"espaço para o OpenPod"*.

> **É a primeira vez que o projeto grava e lê algo dessa região.** O V017
> pretende pôr **código** lá. Se o ponteiro funcionar e o título aparecer
> na tela, fica provado, com um patch de dado e risco visual, que a área
> livre é endereçável por XIP — a premissa em que o V017 inteiro se apoia.
>
> Estava classificada como **PROVÁVEL** em `MENU_HIERARQUIA.md` §7. Uma
> gravação de 8 bytes resolve isso antes de qualquer linha de Thumb-2 ser
> escrita.

### 8.6 O que se perde

O **ícone do cartão SD** deixa de aparecer. A informação de cartão
presente/ausente some da faixa — o label que a mostrava virou o título.
Reversível em 4 setores pelo kit.

---

## 9. ⚠️ O V016 no aparelho: dois defeitos, e o que eles ensinam

Gravado pelo mantenedor em 2026-09-13. **A barra ficou visível demais e o
título não apareceu.** Foto no relatório de sessão.

### 9.1 Defeito 1 — patchei o label errado

A faixa tem **dois** labels de ícone parecidos, e eu tratei os dois como
se fossem um:

| Slot | Criado em | Glifo | Condição | Aparece? |
|---|---|---|---|---|
| `view_p[0x14]` | `0x00D226AC` | **U+F0C7** (disquete) | `0xCFE714 != 0` — cartão presente | ✅ **é o da tela** |
| `view_p[0x18]` | `0x00D226F8` | U+E647 | flag em RAM `0x008238EB != 0` | ❌ nunca, na home |

```asm
0x00D238A6   bl   #0xcfe9e8      ; le a flag 0x008238EB
0x00D238AA   cbz  r0, #0xd238b4  ; se 0, NAO cria o label
0x00D238AE   bl   #0xd226f8      ; view_p[0x18]
```

**O patch do V016 estava byte a byte correto e simplesmente nunca
executou.** O disassembly do V016 mostra o ponteiro resolvendo para
`"OpenPod"` em `0x00DA3038` — o defeito não estava no patch, estava na
**escolha do alvo**.

> **Lição de método.** Eu confirmei que o patch estava aplicado — e tratei
> isso como se confirmasse que ele funcionaria. São coisas diferentes:
> *"o byte certo está no lugar certo"* não é *"este código roda"*.
> É a mesma família do erro da Sessão 25 (`WRITE_FLASH_SEMANTICS.md` §3):
> um teste que passa sem provar o que se queria provar.
>
> O que faltou foi uma pergunta de uma linha: **este objeto chega a ser
> criado nesta tela?** A resposta estava a duas instruções de distância.

### 9.2 Defeito 2 — a barra ficou clara demais

O degradê usou os cinzas **que já existiam** na paleta da folha, e o mais
escuro disponível era `(28,32,38)`. Na tela ficou proeminente.

A folha, depois do V014, usa **6 dos 256 índices**. Havia 250 livres —
dava para **definir o tom exato** em vez de garimpar o mais próximo.
Eu tinha escrito na própria ferramenta *"não altera a paleta"* como se
fosse uma regra de segurança, quando era só uma limitação que eu mesmo
tinha imposto.

### 9.3 A correção — V017

**A.** Reverte os 5 pontos do V016 em `0x00D226F8`. Sem isso, se aquela
flag algum dia ficasse `!= 0`, o título apareceria no meio da tela por
cima de outra coisa. **Um patch morto não é inofensivo: é uma armadilha
adormecida.**

**B.** Aplica o título em `0x00D226AC`, o label que aparece:

```text
0x001226BA   mvn r2,#0x1d (x=-30)   -> movs r2,#4 ; nop
0x001226BE   movs r1,#3 (TOP_RIGHT) -> movs r1,#2 (TOP_MID)
0x001226CA   bl set_style_text_font -> 2x NOP
0x001226F4   ponteiro do texto      -> 0x00DA3038
```

**C.** Define 4 entradas de paleta novas e repinta:

| idx | antes | depois |
|---|---|---|
| 2 | (170,174,178) | **(20,22,26)** topo |
| 3 | (150,154,159) | **(14,16,19)** meio |
| 4 | (127,131,136) | **(9,10,12)** base |
| 5 | (102,106,111) | **(52,56,62)** separador |

A ferramenta **recusa** redefinir um índice que esteja em uso nos pixels,
e recusa repintar se os tons da barra do V016 aparecerem fora da faixa.

**1 828 bytes, 4 setores.** `tools/fix_status_bar.py`.

### 9.4 Ressalva que continua valendo

O título é criado **só com cartão presente**. Sem cartão, não aparece.
Não existe label incondicional na faixa além do relógio — e usar o
relógio significaria perdê-lo.

### 9.5 O que ainda NÃO foi provado

> A premissa da área livre (`0x001A3038` legível por XIP) **continua
> NÃO TESTADA**. O V016 deveria tê-la testado, mas o label nunca foi
> criado, então o ponteiro nunca foi lido. O V017 é que vai responder.
>
> Isso importa: é a premissa em que o **V018 (Extras)** se apoia para pôr
> código na área livre. Registrado aqui para não se perder.

---

## 10. ✅ V017 no aparelho — e a premissa da área livre, PROVADA

Gravado em 2026-09-13. **O título "OpenPod" apareceu**, ao lado do
relógio, com a bateria à direita.

| Previsto | Observado | Classe |
|---|---|---|
| o label `view_p[0x14]` é o que aparece | ✅ virou o título | **CONFIRMADO** |
| `align=2` centraliza na tela | ✅ | **CONFIRMADO** |
| apagar o `bl` da fonte faz herdar a do tema | ✅ texto legível | **CONFIRMADO** |
| paleta redefinida deixa a barra discreta | ✅ | **CONFIRMADO** |
| **string em `0x001A3038` legível por XIP** | ✅ **"OpenPod" na tela** | **CONFIRMADO** |

> ### A premissa da área livre está provada
>
> `MENU_HIERARQUIA.md` §7 classificava como **PROVÁVEL** que dados em
> `0x001A3038` fossem endereçáveis por XIP em `0x00DA3038`. **Agora é
> CONFIRMADO**, e custou 8 bytes de string.
>
> É a premissa em que o **Extras** se apoia para pôr código na área
> livre. Sai da lista de riscos.
>
> Ressalva honesta do alcance: isto prova **leitura de dado** por XIP.
> **Não prova execução de código** de lá. São coisas diferentes — o
> mesmo tipo de distinção que me custou o V016.

---

## 11. V018 — a barra tinha altura errada, e dava para medir

O mantenedor observou que a faixa ficou apertada. **Não era impressão, e
a régua estava no próprio firmware:**

```text
fonte de texto   ascendente 12, descendente 0  -> altura 12
y_ofs do texto   2                             -> ocupa y  2 .. 14
barra do V017    banda y 0..12, separador y13
```

**O texto estourava a barra em 1 px e cruzava o separador.** Nenhum dos
patches anteriores tinha medido isso; eu escolhi a altura da barra por
aparência na prévia, não pela métrica da fonte.

### A correção — e um segundo ajuste, também medido

A primeira tentativa foi barra `y0..16`, separador `y17`, lista de `y18`.
Na prévia o mantenedor viu que **o separador encostava no topo de
"Música"**. Medido: **0 px de folga** — o texto do rótulo começa
exatamente na linha seguinte ao separador.

A saída foi subir o texto da barra em 1 px, o que libera 2 px embaixo:

```text
texto da barra   y_ofs 2 -> 1,  ocupa y  1 .. 13
barra            y  0 .. 15
separador        y 16
respiro          y 17 .. 18        2 px
lista            y 19 ..159        141 px para 9 linhas
linhas           19  35  50  66  82  97  113  129  144
espaçamento          16  15  16  16  15  16  16  15
```

As 9 linhas não cabem em espaçamento inteiro (142 / 9 = 15,8), então
alternam 16 e 15 px. **A diferença de 1 px é invisível com fonte de
12 px, e é melhor que sobrar espaço morto no rodapé ou cortar a última
linha.** A última termina exatamente em 159.

A bateria desce de `y=0` para `y=2` para centralizar na barra nova.

**`tools/patch_bar_height.py`.** Com a maiúscula do "Vídeo" junto, o
V018 fecha em **1 227 bytes, 11 setores**.

> **Lição, reforçada duas vezes na mesma sessão:** havia uma métrica
> exata disponível — a ascendente da fonte, a 3 linhas de Python — e eu
> escolhi por olho. Errei a altura da barra, e depois errei o respiro.
> Nos dois casos bastou **medir a folga em pixels** em vez de olhar a
> imagem. Quando o número existe no próprio artefato, a prévia é
> conferência, não substituto.

---

## 12. Nota: "vídeo" → "Vídeo", e a segunda armadilha de string

Pedido do mantenedor: o item do menu estava em minúscula, fora de padrão
com os outros oito.

**A correção óbvia — trocar 1 byte — estava errada.** A string do
português é a **cauda** de outra:

```text
0x00C55370   "...odução de vídeo\0"
                          ↑ 0x00C5537C  é para onde pt id 3 aponta
```

Capitalizar no lugar transformaria `"Reprodução de vídeo"` em
`"Reprodução de Vídeo"`. **Segunda vez que um ponteiro de string aponta
para o meio de outra** — a primeira foi `"%02d:%02d"` dentro de
`"%02d. %02d:%02d:%02d"` (§5).

> **Regra derivada:** neste firmware, **nunca edite uma string no lugar**.
> Sempre grave uma nova na área livre e reaponte o ponteiro. Custa 4 bytes
> a mais e remove a classe inteira de erro, em vez de evitá-la caso a
> caso. Mesmo raciocínio do `write_flash` com offset 0 por arquivo
> (`WRITE_FLASH_SEMANTICS.md` §5).

Ferramenta: `tools/patch_menu_text.py`, que faz exatamente isso e
**recusa** texto com caractere fora da fonte. Ela também serve para o
"Extras" do V019.

Nos outros sete idiomas o item já começa com maiúscula (`Video`,
`Vidéo`, `视频`), e nenhum compartilha o ponteiro do português — logo a
mudança é exclusiva do pt.

---

## 13. Defeito no renderizador de prévia — acentos fora da caixa

Encontrado pelo mantenedor olhando a prévia da barra de seleção: o "ú" de
"Música" ficava **fora** da barra azul.

**Era defeito da prévia, não do desenho.** Medido na fonte do firmware:

```text
ascendente só com ASCII (0x21..0x7E)   12
ascendente incluindo á ã í ú           13   <- +1 px
descendente                             0
altura total do texto                  13 px
altura do rótulo                       15 px
```

O `preview_home.py` e o `preview_selecao.py` calculavam a linha de base
com **apenas caracteres ASCII**. Como os acentos sobem 1 px acima do
maior glifo ASCII, eles eram desenhados **acima** da caixa do rótulo.

Na tela isso não acontece: a LVGL posiciona a linha dentro da área de
conteúdo do rótulo, e 13 px cabem em 15.

**Corrigido:** a ascendente passa a ser calculada sobre a faixa ASCII
**mais** os acentuados (`0xC0..0xFF`).

> **Lição:** a prévia é ferramenta de decisão, então um erro nela custa
> uma decisão errada. Esta quase me fez mudar a altura da barra para
> resolver um problema que não existia no aparelho. **Quem sugere uma
> mudança a partir de uma imagem tem de conferir a imagem antes.**
>
> É a terceira vez nesta sessão que a resposta estava numa métrica do
> próprio firmware e eu tinha chegado nela pelo olho.

---

## 14. V054 — o título em 37 telas, e por que saiu barato

Pedido do mantenedor depois de gravar a 1.5: *"vamos fazer a barra
superior"*, com **título e bateria** nas subtelas (sem relógio) e o texto
vindo de `get_string`, traduzido.

O `ROADMAP_1.1.md` §4 classificava isto como **a única pendência que cria
objeto** e estimava custo alto. **A estimativa estava errada, e o motivo
é instrutivo: o objeto já existia.**

### 14.1 As três descobertas que derrubaram o custo

**A. O id da página está disponível na camada view, e o criador do
título também.**

```asm
0x00D23D0E   ldr r3,[r4] ; strb r5,[r3]   ; view_p[0] = numero da pagina
0x00D23D12   bl  0xd23740                 ; view_icon_create, logo depois
```

Dentro de `view_icon_create` tudo é decidido por esse byte. O bloco do
título ocupa `0x00D23880..0x00D2389D` — **30 bytes** — e diz:

```text
se pagina == 1 ou 0x51, e ha cartao SD, e view_p[0x14] e nulo:
    view_p[0x14] = 0x00D226AC()      ; o criador do rotulo, ja posicionado
```

Ou seja: faltava só decidir **para quais páginas** roda e **qual texto**
recebe. Trocar os 30 bytes por um `bl` para uma rotina de tabela resolve
as duas coisas de uma vez. **Custo por tela nova, daqui em diante:
2 bytes.**

**B. O relógio não é page-gated na atualização.**

```asm
0x00D2430A   ldr r0,[r3,#0x20] ; cbz r0, pula
```

Se o objeto existir, ele é atualizado. Não foi preciso nesta versão — o
mantenedor optou por título e bateria — mas fica registrado: habilitar o
relógio em outra tela é só criar o objeto, nada mais.

**C. Cada tela de lista JÁ TEM faixa superior com um rótulo de título
centralizado — vazio.**

```text
page_home_menu_create  0x00D2F0D4   faixa 128x16  (divisor 10)
page_set_menu_create   0x00D3A66C   faixa 128x22  (divisor  7)
   ambas: rotulo centralizado (align 9), texto = 0x00C4F981
```

E `0x00C4F981` é **um espaço**. Lendo os bytes: `0x00C4F97C` é
`"id \r\n \0"`, então `0x00C4F981` = `" "` e `0x00C4F982` = `""` — esta
última é a que a V039 usou para apagar a engrenagem.

> Não usei esse rótulo (é um por tela, e a posição varia com o divisor da
> faixa), mas ele confirma que a faixa foi **projetada** para ter título.
> O firmware original simplesmente nunca preencheu.

### 14.2 O inventário, por critério objetivo

Em vez de escolher telas pelo que "parece" lista, contei quem chama os
dois helpers:

```text
0x00D216F0   cria a faixa superior      -> 50 paginas
0x00D21764   cria a linha de lista      -> 34 dessas 50 tambem
```

O nome de cada página veio das strings de depuração do próprio firmware
(cada `_create` carrega o literal do próprio nome para a mensagem de
`malloc failed`). Nada foi adivinhado.

As 16 que têm faixa mas **não** têm linhas são seletores de hora, leitura
de e-book, entrada de senha e afins — ficaram de fora.

### 14.3 Geometria: o título das subtelas não é centrado na tela

Sem relógio, o espaço útil vai de x=0 até a bateria em x=107. A rotina
realinha o rótulo para `TOP_MID` com **x_ofs = -12**, isto é, centro em
**x=52** — o centro óptico da área livre.

```text
largura maxima = 2 x min(52-4, 107-4-52) = 96 px
```

A ferramenta **mede na fonte do próprio firmware e recusa** qualquer
título acima disso. O mais largo que passou: `Sobre o aparelho`, 95 px.

> Sem esse deslocamento o orçamento cairia para 80 px e cinco telas
> ficariam sem título. **Um byte de x_ofs comprou cinco telas** — e
> evitou ter que inventar strings novas, que só existiriam em português.

A home e a `0x51` levam o id sentinela `0xFF`: mantêm `"OpenPod"` e o
alinhamento original (`x_ofs +4`), porque ali **há** relógio à esquerda.

### 14.4 ⚠️ Um defeito da 1.5, encontrado no caminho

Procurando quem mais mexe em `view_p[0x14]`, apareceu um segundo ponto:

```asm
0x00D23E86   r6 = view_p
0x00D23E8A   se pagina == 1 ou 0x51:
0x00D23E94       se o cartao SAIU:   lv_obj_del(view_p[0x14]); slot = 0
                 se o cartao ENTROU: recria
```

**Na 1.5, remover o cartão SD na home apaga o título "OpenPod".** É
herança de quando aquele slot era o ícone do cartão (V017, §9). Nunca foi
notado porque ninguém remove o cartão com a home na tela.

Com o título desacoplado do cartão, esse bloco vira armadilha adormecida
— exatamente o que a §9.3 diz sobre patch morto. Desviado com 2 bytes:

```text
0x00123E8A   ldrb r2,[r6]  ->  b 0x00D23EA2     (o pop da funcao)
```

> **Lição de método, pela positiva desta vez.** A §9.1 me custou uma
> versão por patchar o rótulo errado sem perguntar *"este objeto chega a
> ser criado nesta tela?"*. Desta vez a pergunta foi *"quem mais escreve
> neste slot?"* — uma varredura de `ldr/str [rX,#0x14]` na camada view,
> 30 segundos — e ela achou um defeito que já estava no aparelho.

### 14.5 O CRC: a ferramenta estava prestes a repetir o erro de 2026-09-12

A primeira versão do `patch_titulos.py` recalculava o CRC da FIRM, como
fazem o `patch_status_bar.py` e os outros tools antigos. Isso teria posto
**o setor `0x00D000` na lista de gravação** — o setor que guarda o
ponteiro de boot e que matou o primeiro GN-438 (`INCIDENTE_V028.md`).

A regra **R1** já tinha resolvido isso: o CRC da FIRM não é verificado
por nada, o campo fica desatualizado de propósito, e `0x00D000` saiu do
projeto. A prova de que a 1.5 já vive assim:

```text
GN438_original.bin              FIRM crc  0x49A6
GN438_openpod_v053_carimbado    FIRM crc  0x49A6   (conteudo real 0x4D67)
```

A ferramenta agora **não toca no campo** e tem uma trava dura: recusa
gerar qualquer diferença abaixo de `0x00E000`.

> O `tools/validate_firmware.py` reporta `[FALHA] FIRM: CRC` tanto na
> V053 quanto na V054 — **é o estado esperado desde a R1**, não uma
> regressão. O validador ainda não foi ensinado a regra; fica anotado.

### 14.6 O patch

```text
0x001A5000   88 B   rotina (Thumb-2), XIP 0x00DA5000   <- AREA LIVRE
0x001A5058   76 B   tabela pagina -> id de string, 37 entradas
0x00123880   30 B   bloco do titulo  ->  bl 0x00DA5000 + 13 NOPs
0x00123E8A    2 B   ldrb r2,[r6]     ->  b 0x00D23EA2
0x0010A000          carimbo de versao (gerador de kit, regra R7)
```

**193 bytes, 3 setores.** `tools/patch_titulos.py`.

Ordem de gravação (**R2**), passada explicitamente ao gerador:

```text
0x1A5000   a rotina           <- primeiro: o alvo tem que existir
0x10A000   o carimbo
0x123000   o gancho           <- por ultimo: e ele que ATIVA tudo
```

Todo estado intermediário continua bootável: antes do último setor a
rotina está lá, mas ninguém a chama.

### 14.7 O que está provado e o que não está

| Afirmação | Classe |
|---|---|
| `view_p[0]` é o número da página, escrito antes de `view_icon_create` | **CONFIRMADO** (disassembly, `0x00D23D0E`) |
| As 50 páginas com faixa e as 34 com linhas de lista | **CONFIRMADO** (varredura de chamadas aos dois helpers) |
| O nome de cada página | **CONFIRMADO** (literal de depuração da própria função) |
| A rotina montada faz o que o comentário diz | **CONFIRMADO** (remontada e desmontada instrução por instrução) |
| Código na área livre executa | **CONFIRMADO** desde o V020 |
| `0x00C4F981` é `" "`, cauda de `"id \r\n "` | **CONFIRMADO** (leitura dos bytes) |
| Remover o cartão apaga o título na 1.5 | **PROVÁVEL** — o código diz isso com clareza, **não foi reproduzido no aparelho** |
| Os 37 títulos são os certos | **ESCOLHA EDITORIAL**, não descoberta. Revisar em `TITULOS` dentro da ferramenta |
| A aparência da faixa com título nas 37 telas | **NÃO TESTADO** — o aparelho é o único juiz (§13) |

### 14.8 As duas ressalvas honestas

1. **`Música` aparece duas vezes** — na página 2 (menu de música) e na 3
   (lista de faixas). O id natural da 3 seria o 12, `Todas as músicas`,
   que tem **103 px** e não cabe nos 96. Preferi repetir a palavra a
   inventar string nova.

2. **A página 23 (`page_record_time`) ficou sem título.** Ela tem faixa e
   linhas, mas os literais que carrega são glifos de ícone, não texto —
   não consegui dizer com confiança o que a tela é. **Melhor sem título
   do que com título errado**, e são 2 bytes para acrescentar depois.

---

## 15. V059 / OpenPod 1.9 — o respiro sob a faixa nas subtelas

Foto do mantenedor com a 1.8: na home a faixa tem traço e 2 px de
respiro antes da lista; **no Configurar a barra de seleção encosta no
título.**

### 15.1 Não era falta de separador — era sobreposição de 1 px

A faixa **já desenha um traço**: `0x00D216F0` define `border_width = 1`
e `border_side = 1` (BOTTOM), na cor da paleta `0x12`.

O problema é onde a lista começa:

```text
Configurar   faixa    y 0..21        (altura = 160/7 = 22)
             conteiner y 22          (alinhado TOP_MID com o MESMO valor)
             linha i   y_ofs = passo*i - 1
             linha 0   -> 22 + (0 - 1) = 21
```

**A linha 0 começa em y=21, exatamente onde a faixa desenha o traço.** A
barra azul de seleção cobre o traço e encosta no título. O `- 1` existia
para as linhas de 22 px do desenho original, onde ele fundia bordas
vizinhas; com as linhas de 16 px da V039/V040 virou colisão.

### 15.2 O ponto único

O contêiner da lista **não** é criado por cada tela: sai de um helper
compartilhado.

```text
0x00D21690   criador de conteiner   -> 58 paginas
0x00D216F0   criador da faixa       -> 50 paginas
0x00D21764   criador da linha       -> 36 paginas
```

Dar `pad_top` ao contêiner empurra o conteúdo em todas de uma vez, porque
`lv_obj_align` posiciona pelo **content area** do pai — a área já
descontada do padding.

```text
0x001216CC   bl set_style_radius  ->  bl 0x00DA5220
0x001A5220   rotina 18 B: faz o radius que ja fazia + pad_top = 3
```

**4 bytes de gancho.** A propriedade `PAD_TOP` é a 16, wrapper
`0x00D4D01C` (`GUI_ANALYSIS.md`), e a ferramenta confere isso na imagem
antes de gravar.

### 15.3 Os 3 px saíram da geometria, não do gosto

```text
Configurar   faixa 0..21, traco em 21 -> linha 0 em 22+3-1 = 24  -> respiro 2 px
Extras       faixa 0..15, traco em 15 -> lista em 16+3    = 19   -> respiro 3 px
```

2 px é exatamente o respiro da home (§11). O Extras fica com 3 px porque
suas linhas não usam o `-1` — elas são empilhadas pelo layout do
contêiner, não alinhadas uma a uma.

### 15.4 Ressalva honesta sobre o alcance

O helper serve **58 páginas** e eu **não conferi as 58**. Telas que não
sejam lista também ganham 3 px de padding no contêiner. É reversível em
4 bytes, mas o alcance é maior que o defeito relatado — e isso precisa
ser olhado no aparelho, não deduzido.


---

# FECHADO — o "OpenPod" some sem cartão SD (2026-09-18)

A pendência aberta na Core 2.3, em 15/09:

> *"Se a rotina `0x00D226AC` for chamada só quando há cartão, o
> 'OpenPod' vai sumir junto com ele — e aí o texto estaria fazendo papel
> de indicador de cartão, o que é PIOR que o ícone original. Não dá para
> responder isso pelo binário sem ler os dois chamadores."*

**Respondida por observação no aparelho:** o mantenedor tirou o cartão e
o "OpenPod" **some** da faixa.

Ou seja: a hipótese estava certa. O título ocupa o slot do ícone de SD e
herda a condição de existência dele.

## A decisão

**Do mantenedor: fica assim.** *"Tá ótimo, não tem problema."*

Então o comportamento é **aceito, não corrigido**. Quem mexer nisso
depois precisa saber que é escolha, não descuido:

- o "OpenPod" na faixa é **indicador de cartão** na prática;
- separar as duas coisas exige um objeto novo — é código, não dado
  (ver §6 desta página);
- e a rotina de título por página (V054, `0x001A5000`) **nunca foi
  testada no aparelho** e não existe nesta linha de firmware.

| Afirmação | Classe |
|---|---|
| O título some sem cartão | **CONFIRMADO** (observado na tela) |
| É o slot do ícone de SD | CONFIRMADO |
| Separar exige objeto novo | PROVÁVEL (§6) |
| Comportamento aceito pelo mantenedor | decisão, 2026-09-18 |


---

# A altura da faixa — padronizada em 16 px (Core 5.4)

## O defeito, medido em 2026-09-18

As **53 telas** que criam a faixa não concordavam sobre a altura dela:

```text
divisor 10  ->  160/10 = 16 px      25 telas
divisor  7  ->  160/7  = 22 px      23 telas   <- o desvio
altura fixa 16                       1 tela    <- a home (Core 2.0)
sem divisor identificado              4 telas
```

A Core 2.2 padronizou as **linhas** de 7 para 10, em 54 pontos, e deixou
a **faixa** dessas 23 telas no 7.

## Por que isso desalinhava a bateria

A bateria é posicionada **fixa em `y = 0`**:

```asm
0x00D22612   movs r1, #0x6b      ; x = 107
0x00D22614   bl   #0x00D4A2D4    ; set_pos(obj, 107, 0)
```

Numa faixa de 16 px, o glifo de 13 px fica quase centrado. Numa de
22 px, sobram 9 px embaixo e ele fica colado no topo.

> Mantenedor: *"a barra degradê tá diferente do menu iniciar para o
> restante das páginas, e no restante das páginas tá muito desalinhado o
> ícone da bateria. Ou afina tudo igual da home ou coloca a da home
> igual do restante."*

**Escolhido: afinar tudo para 16 px.** É o que a home já usa, o que o
resto do sistema calcula, e o mais perto do `faixa_altura_px = 18` do
`nanoclone.json`.

## A armadilha da medição

A altura chega por **duas** funções diferentes, e procurar só uma dá
zero resultado:

| | |
|---|---|
| `0x00D4A1EA` | `set_height(obj, h)` |
| `0x00D4A21A` | `set_size(obj, w, h)` ← as telas de faixa usam esta |

E a janela de busca precisa de `0x40` bytes: com `0x24` a chamada de
`set_size` do Configurar cai **um byte** fora e o sítio some.

`tools/patch_faixa_16px.py` — 23 bytes, 1 por tela. Dado, não código.
