# OpenPod — Avaliação de viabilidade e roadmap por camadas

> Escrito em 2026-09-12, **depois** de duas gravações bem-sucedidas
> (V001 e V002). Não é especulação: cada classificação abaixo cita a
> evidência que a sustenta.

---

## 1. Veredito

**O Design System é viável** — como *direção*, que é exatamente o que ele
próprio diz ser (§13: *"Usar o que o YP3 já entrega. Melhorar antes de
substituir"*; §12: proíbe *"substituição completa do sistema gráfico sem
necessidade"*).

Com **uma ressalva geométrica** que muda a referência visual, tratada na
§3 deste documento.

---

## 2. Viabilidade por camada

| Camada | Situação | Evidência |
|---|---|---|
| **1. Cor via paleta** | ✅ **PROVADO** | V002 rodando: 255 entradas reescritas, 9 ícones de uma vez |
| **2. Pixels de imagem** | ✅ **PROVADO** | V001 rodando |
| **3. Textos e rótulos** | 🟢 provável | bloco de 8 idiomas mapeado em `0x053000`–`0x05E000` |
| **4. Tipografia** | 🟡 plausível | formato decodificado, 7.098 glifos extraídos; limite é o tamanho da tabela (`0x086C44`–`0x0A27E4`) |
| **5. Posições, tamanhos, destaque** | ✅ **PROVADO** (V004) | patch Thumb-2 em imediatos — `movw`/`movs` trocados, 8 bytes |
| **6. Estrutura: telas novas, navegação** | 🔴 caro | exige escrever código ARM novo em flash livre |

**Recursos disponíveis para a camada 6, se chegarmos lá:** 364 KB de
flash apagada (`0x1A3038`–`0x1FC000`), sem assinatura, sem criptografia,
base XIP conhecida (`0x00C00000`), e recuperação por USB testada em
condições reais.

---

## 3. ⚠️ A descoberta geométrica — qual nano usar como referência

O `CLAUDE.md` e o Design System dizem **iPod nano 2ª geração**. Medindo:

| Modelo | Resolução | Ratio | Orientação | Distância do GN-438 |
|---|---|---|---|---|
| **GN-438** | 128×160 | 0,800 | **retrato** | — |
| nano 1G/2G | 176×132 | 1,333 | paisagem | **0,53 — o pior de todos** |
| nano 3G | 320×240 | 1,333 | paisagem | 0,53 |
| **nano 4G/5G** | 240×376 | 0,638 | retrato | **0,16 — o melhor** |
| nano 6G | 240×240 | 1,000 | quadrado | 0,20 |
| nano 7G | 240×432 | 0,556 | retrato | 0,24 |

> *Resoluções dos nanos anotadas de memória. Confiança alta na do 2G
> (176×132, paisagem), que é a que sustenta a conclusão. Conferir as
> demais antes de usá-las para layout fino.*

**O nano 2G é o único nano deitado, e o GN-438 é em pé.** A assinatura
visual do 2G — lista à esquerda, capa à direita — **depende** de ser mais
largo que alto. Em 128×160 essa divisão não cabe.

### Consequência 1 — a grade 3×3 deixa de ser dívida

**O nano 6G tinha a home em grade de ícones.** A grade do GN-438 não é
"não-iPod": é o idioma de um iPod *posterior*.

O item que eu havia classificado como o mais caro do projeto — converter
a home de grade para lista (§6 do Design System) — **deixa de ser
obrigatório**. Passa a ser uma opção estética, não uma correção.

### Consequência 2 — a referência se divide em duas

| O que herdar | De onde | Por quê |
|---|---|---|
| **Filosofia** | **nano 2G** | simplicidade, hierarquia, foco em música, contenção visual — é o que o `CLAUDE.md` §1 pede de fato ("reproduzir conceitos", não copiar) |
| **Soluções de layout em retrato** | **nano 4G/5G** | mesma orientação; resolvem lista, título e Now Playing em tela alta |
| **Legitimidade da grade** | **nano 6G** | home em grade de ícones é precedente Apple |

### Decisão do mantenedor — 2026-09-12: sem faixa de capas

A tira de capas de álbum do nano 4G/5G **fica fora do escopo**. Dois
motivos independentes, ambos suficientes:

1. **O nano 2G não a tinha.** Seu menu principal era lista pura: barra de
   título e itens, nada mais. A tira apareceu em modelos posteriores.
   Portanto "menu como o do 2G" não abre mão de nada — é o que o 2G era.
2. **Seria o item mais caro da interface**, para enfeite: decodificação
   JPEG em runtime, três imagens simultâneas, com RAM nunca medida.

> Consequência prática: **o menu segue o 2G** (lista pura). O 4G/5G entra
> só para proporções em tela vertical. Isso mantém o elemento mais caro
> do projeto fora do caminho crítico, sem custo estético — o resultado
> continua sendo um nano legítimo.

**Nada disso contraria a decisão original.** O `CLAUDE.md` §1 é explícito:
o objetivo é reproduzir *conceitos* — simplicidade, navegação, hierarquia,
legibilidade, minimalismo — não geometria. A filosofia continua sendo a
do 2G.

---

## 4. A inversão estratégica

**A home é 1 tela de 61.** A maior parte do uso real — navegar músicas,
pastas, configurações — **já acontece em listas verticais**.

**Evidência:** `lv_list` **não existe** no binário (0 ocorrências — a
LVGL foi compilada sem o widget). Mas há dezenas de telas de lista
montadas à mão com `lv_label` e `lv_obj`: `page_folder_list_create`,
`page_ebook_list_create`, `page_music_song_create`,
`page_bt_menu_paired_list_process`, `page_set_menu_create`.

> **A estética de lista do nano já está no aparelho.** Ela aparece toda
> vez que se entra em Arquivos, Livro ou Configurações. Não precisa ser
> inventada — precisa ser vestida.

**Portanto: atacar as listas primeiro, a home por último.** Isso dá
"parece um iPod" na maior parte do uso usando apenas as camadas 1–4, sem
uma linha de código ARM. E quando chegarmos na camada 5, já teremos
aprendido a patchar código nas telas pequenas, onde errar é barato.

---

## 5. Roadmap

### Fase 1.1 — Identidade visual *(camadas 1–2, PROVADAS)*

| | Alvo | Custo estimado |
|---|---|---|
| ✅ V001 | ícone Música azul | 3 setores — **feito** |
| ✅ V002 | 9 ícones monocromáticos pela paleta | 4 setores — **feito** |
| V003 | calibrar luminosidade (o display renderiza mais claro que o preview) | 3 setores |
| V004 | papel de parede e logo de boot | a medir |

### Fase 1.2 — As listas *(camadas 3–4)* — EM ANDAMENTO

**Feito:** Configurações alinhada ao tema (V006). Descoberto o tema
central de duas funções (`COLOR_SOURCE.md` §10) — o que torna mudanças de
cor de texto/fundo **globais por 4 bytes**, não por tela.

**Removido do escopo:** encurtar rótulos truncados. O firmware **rola** o
rótulo selecionado; o truncamento não é defeito.

**Em aberto:** inverter para tema claro (nano 2G). Depende de mapear
quais telas usam o tema — parcialmente feito (Configurações e menu
principal: sim; Arquivos, Livro, Música, Now Playing e barra de status:
**não verificados**).



O grosso do ganho. Alvos, na ordem de uso:

1. **Configurações** (`page_set_menu_create`) — a lista mais usada
2. **Arquivos** (`page_folder_list_create`)
3. **Músicas / Artistas / Álbuns** (`page_music_*_create`)

Trabalho: cor do destaque de seleção, cor de fundo, tipografia, rótulos.

### Fase 1.3 — Now Playing *(camadas 4–5)*

`page_music_play_create`. A tela que mais define um player. Provavelmente
o primeiro lugar onde vamos precisar mexer em posições — e portanto o
primeiro teste real da camada 5.

### Fase 1.4 — A home *(camada 5, opcional)*

Com o precedente do nano 6G, a grade **pode ficar**. Melhorias possíveis
sem reescrever a tela: espaçamento, destaque do item selecionado,
tipografia dos rótulos.

Converter para lista continua possível, mas passa a ser **escolha
estética**, avaliada pela §15 do Design System (compatibilidade,
desempenho, consistência) — não uma pendência.

---

## 6. O que este roadmap NÃO promete

- **Não promete a camada 5.** Patch Thumb-2 em `page_*_create` é
  plausível, não provado. A primeira tentativa dirá.
- **Não promete telas novas.** Camada 6 depende de escrever código ARM em
  flash livre — possível em princípio, nunca tentado aqui.
- **Não promete capa de álbum** (Design System §7). Depende de decodificar
  JPEG em runtime e de RAM que ainda não foi medida.

> Cada um desses vira **PROVADO** ou **NÃO DETERMINADO** por experimento,
> nunca por otimismo.

---

## 7. Classificação

| Afirmação | Classe |
|---|---|
| Camadas 1 e 2 funcionam no aparelho | **CONFIRMADO** (V001, V002) |
| `lv_list` não está compilado no firmware | **CONFIRMADO** (0 ocorrências) |
| O firmware desenha listas verticais à mão | **CONFIRMADO** (nomes de função + observação na tela) |
| nano 2G é paisagem; GN-438 é retrato | **CONFIRMADO** |
| A grade 3×3 tem precedente Apple (nano 6G) | **PROVÁVEL** (de memória; não verificado em fonte) |
| Camada 5 (patch de layout) é viável | **NÃO DETERMINADO** |
| Camada 6 (código novo) é viável | **NÃO DETERMINADO** |

---

# PROJETOS NOMEADOS — 2026-09-14

> Nomes dados pelo mantenedor. **Regra de processo instituída na mesma
> conversa: NENHUMA versão nova é gerada sem ele pedir "gerar nova
> versão".** Corrige-se, valida-se, e só então se empacota.

## 🪐 PROJETO SATURNO — a carcaça de design (ATUAL)

**O problema, em uma frase:** a home e as 36 telas de lista são **dois
mundos de desenho diferentes**, e ajustar um para imitar o outro por foto
é um ciclo sem fim.

```text
HOME (pagina 1)                 TELAS DE LISTA (36)
  imagem 128x160 indexada         framework de widgets
  faixa = PIXELS na imagem        faixa = objeto (0xD216F0)
  linhas = tabela de coords       linhas = helper (0xD21764)
  selecao = fundo do rotulo       conteiner = helper (0xD21690)
  cores = paleta da imagem        cores = tema da LVGL
```

**CONFIRMADO:** `page_home_create` não chama nenhum dos três helpers
compartilhados.

### Defeitos que o Saturno tem de matar

| origem | defeito | estado |
|---|---|---|
| fotos 2,3,4,5 | faixa clara vazia entre o título e o 1º item | **não investigado** |
| foto 3 vs 4 vs 2 | ícones `≡`, `♪` e nenhum, conforme a tela | conhecido (V039 só tratou `page_set_menu`) |
| foto 4 | título colide com um contador que a tela desenha | conhecido |
| foto 5 | Now Playing sem título nem bateria | fora das 36 |
| foto 6 | a barra da home aparece no descanso de tela | **não investigado** |

### As duas direções, e a recomendação CORRIGIDA

| | o quê | custo | risco |
|---|---|---|---|
| **A** | a home passa a usar o framework | reescrever `page_home_create` | alto — mexe na única tela que hoje está boa |
| **B** | tabela de tema + ganchos nos getters e nos 3 helpers | médio | baixo |

**Recomendo a A.** Registrando que eu havia recomendado a B, e por um
motivo ruim: *"os getters já são ponto único"* é um argumento sobre o que
é fácil de implementar, não sobre o que resolve o problema.

**A B não resolve.** Sob ela a home continua imagem e as outras continuam
widget; a tabela harmoniza as cores e a faixa da home continua sendo
pixels assados — altura, degradê e separador fora do alcance. O fosso
permanece, e o ciclo de fotos recomeça.

A A é menos arriscada do que parece: **o projeto já fez esse movimento
uma vez.** A página `0x53` teve o `create` desviado com um `bl` de 4
bytes para código nosso (V022–V026). A home é o mesmo movimento.

### O que o Saturno é, reformulado

```text
1. A carcaca JA EXISTE:
     0xD216F0  faixa      -> 50 telas
     0xD21690  conteiner  -> 58 telas
     0xD21764  linha      -> 36 telas
2. Ela nao manda: cada tela sobrescreve depois.
   A 2.0 neutralizou isso com 77 ganchos — funciona, e forca bruta.
3. A home nao participa dela.   <- o buraco de verdade
```

**Saturno = fazer a carcaça mandar + trazer a home para dentro dela.**
Aí os números moram num lugar só e a 2.0 vira consequência, não remendo.

**Pergunta em aberto, e ela decide o desenho:** a home pode deixar de ser
imagem? Sob a A ela precisa — a faixa vira objeto e o degradê de três
tons vira sólido ou dois tons. Se o degradê for inegociável, a carcaça
tem de saber desenhar faixa com imagem, e o custo sobe.

## 🔴 PROJETO MARTE — o NanoClone (DEPOIS do Saturno)

Tema Rockbox `NanoClone` (iPod Nano 2G, 176x132), em
`assets/referencia/NanoClone/`. Já extraído e lido em parte:

```text
.cfg   fonte 14-MyriadPro-Semibold; icones OFF; scrollbar OFF
       selecao: gradiente 639CE3 -> 2866DD, texto FFFFFF
       fundo FFFFFF, texto 000000          <- TEMA CLARO
.sbs   viewport da lista: %Vi(-,5,20,166,112,1)
       -> chrome ocupa y 0..19 (20 px), margem lateral 5 px
.wps   Now Playing: capa 45x45 em (7,42); texto em (58,38,112,53);
       progresso 162x11 em (7,100); "%pp of %pe" em (6,23)
```

**Validações que ele já deu:** ícones off, scrollbar off e seleção de
largura total — as três decisões que o OpenPod tomou por conta própria.

**A bifurcação:** o NanoClone é **tema claro**; o OpenPod é escuro por
decisão do mantenedor (V009–V013). Transferir estrutura, não paleta — ou
reabrir a decisão.

**Só começa quando o Saturno estiver estável.**

## Ordem acordada com o mantenedor

```text
1. SATURNO    carcaca de design
2. EXTRAS     os itens que nao abrem  (funcional, ja diagnosticado
              em MENU_HIERARQUIA.md 23.7 — NAO e problema de design)
3. VERSAO     so quando o mantenedor pedir "gerar nova versao"
4. MARTE      NanoClone
```

## Projeto Marte — estudo concluído (2026-09-14)

Análise do NanoClone feita e documentada em `docs/PROJETO_MARTE.md`;
material em `marte/`. **Nada implementado** — Marte aguarda o Saturno.

Resumo do que o estudo achou:
- o tema é para **176×132**; nossa tela é **128×160**. Os bitmaps não
  se reaproveitam. Marte é reproduzir a aparência, não portar o tema;
- o iPod nano é **tema claro** (preto no branco, seleção azul); o
  OpenPod é escuro. Marte **inverte o tema**;
- pela tabela do Saturno, essa inversão são **12 bytes** (fase M1);
- degradê da faixa: **PROVÁVEL** — o setter `BG_GRAD` (prop 38) existe
  no firmware, mas 34/35 não têm atalho. Só o aparelho confirma;
- a fonte do tema tem 18 px e **não cabe** na linha de 16 px. Fica fora;
- licença **CC-BY-SA 3.0** — atribuição e share-alike se usarmos arte.

### Marte — decisões do mantenedor (2026-09-14)

- seguir o padrão do NanoClone **por completo**;
- os **pixels dele podem** entrar no projeto, com crédito;
- tema **claro**, seleção **azul** do nano.

Registrado em `ATRIBUICAO.md` (CC BY-SA 3.0, Billy Blair). Share-alike
vale para os derivados. **Pendência de implementação:** repetir a
atribuição na tela Sobre.

Reavaliação após a permissão: **9 dos 10 bitmaps cabem em 128 px** — o
estudo inicial superestimou o problema ao olhar o tamanho do strip em
vez do quadro. Ativos já adaptados em `marte/adaptado/`.

### Marte — tela Tocando Agora estudada (2026-09-14)

Nossa: `page_music_play_create`, pagina **0x04**, `0x00131E7C`, 6 rotulos.
Dele: 13 elementos condicionais no `.wps`.

- os ativos **cabem** em 128 px: os canvas largos de `vol-l`/`vol-r` eram
  so padding do Rockbox (tinta de 8x15 e 17x15). Volume remontado em
  90 px, progresso em 114 px;
- o custo real nao e desenho, e **codigo**: 6 rotulos contra 13 elementos
  com condicional (com/sem capa, disco, bloqueio, modos);
- **capa do album e recurso novo**: sem `APIC`/`albumart` no firmware,
  mas o decodificador **JPEG existe**. HIPOTESE de viabilidade, Fase 3;
- fatiado em W1..W5 em `docs/PROJETO_MARTE.md` §5.6. W1 (paleta e faixa)
  sai de graca junto do M1.

### Marte — estudo COMPLETO (2026-09-14)

Fechados os tres itens que faltavam (`docs/PROJETO_MARTE.md` §9, §10, §11):

- **§9 a moldura (`.sbs`)**: a geometria **ja bate** (conteudo em y=19
  contra 20; faixa 17 contra 18). Falta CONTEUDO — a faixa do nano
  carrega bateria, modo de reproducao e bloqueio em toda tela; a nossa e
  so titulo. Os auxiliares de rotulo a direita da faixa existem no codigo
  com **zero chamadores**;
- **§10 os icones**: o firmware ja tem **Font Awesome** (conjunto padrao
  do LVGL). PLAY, PAUSE, PREV, NEXT, SHUFFLE, VOLUME, SETTINGS e mais 13
  estao PROVADOS em uso. Nao precisam vir do NanoClone — ficam fora do
  share-alike. Ressalva: isso mede USO, nao disponibilidade (o cmap da
  fonte de icones esta em RAM);
- **§11 as fontes**: existe uma fonte de **18 px na flash** (`0x00CDED88`,
  ASCII completo) — o M5 pode nao exigir conversao. Fio solto: a fonte
  real da interface esta em RAM (`0x00819Cxx`) e **nao ha particao FONT**
  (so FIRM/TONE/PSMP), logo e `.data` copiada da FIRM no boot.

Correcoes ao estudo anterior: a fonte de 12 px **nao** e a da interface
(tem 14 caracteres, e o relogio); e por em a faixa icones de estado
**nao conflita com o S7** (conjuntos de fonte disjuntos).

### Marte — varredura final (2026-09-14)

`docs/PROJETO_MARTE.md` §12 e §13. Fechado.

Achados que mudam implementacao:
- **os icones tem o degrade da barra ASSADO no fundo** (nenhum usa
  magenta/transparencia). So compoem certo em y=2. Nossa faixa de 17 px
  + separador bate com a dele, entao funciona — mas amarra `altura_faixa`;
- **a barra de volume SUBSTITUI a de progresso** por 2 s (`%?mv(2.0)`).
  E o "with Volume Control" do nome. O mockup anterior estava errado;
- **o titulo do nano e pintado no bitmap** ("iPod"/"Now Playing"). A nossa
  barra, com titulo dinamico por pagina, e MELHOR. Nao copiar;
- **o sulco da barra de progresso vem do fundo**, nao do `progress.bmp`;
- **os icones dele sao coloridos e com brilho**; Font Awesome e
  monocromatico. A escolha e de design (§12.3), nao de conveniencia.

Tres convergencias nao planejadas com o que ja fizemos: sem icones de
lista (S7), sem barra de rolagem, e a geometria da faixa.

Fonte: 834 glifos reais (de 64229 slots), **portugues coberto inteiro**.

### Marte — verificacao "tudo lido?" (2026-09-14)

`docs/PROJETO_MARTE.md` §14. Conferido byte a byte:
- todo byte de todo arquivo explicado (os +2 bytes em 13 BMPs sao padding
  zero; a fonte fecha exata);
- nenhum arquivo oculto;
- `.cfg`/`.sbs`/`.wps` lidos linha a linha e tag a tag, 0 sem mapear.

**UNICA pendencia real:** os 56088 bytes de pixels da fonte NAO foram
decodificados (5 layouts tentados). Nao bloqueia nada — nenhuma conclusao
depende disso e §11.2 indica que nao usaremos essa fonte. Caminho certo
se precisar: ler `firmware/font.c` do Rockbox em vez de adivinhar.

### Marte — fonte decodificada, 100% lido (2026-09-14)

`docs/PROJETO_MARTE.md` §15. O NanoClone esta **100% compreendido**.

O bloco que faltava caiu lendo `firmware/font.c` do Rockbox: `depth=1`
significa **antisserrilhada 4 bpp**, nao 1 bpp. Eu vinha decodificando
4 bpp como 1 bpp.

TRES CORRECOES minhas:
1. a fonte **nao e monocromatica** — e antisserrilhada de 16 niveis;
2. **a tinta real tem 16 px**, nao 18 (linhas 0 e 17 sao vazias em todo
   glifo). Ela **cabe na nossa linha de 16** — o M5 NAO precisa mexer em
   `altura_linha` e a lista **continua com 8 itens**. Eu vinha repetindo
   o contrario desde ontem, medindo `line_height` em vez de tinta;
3. a largura tambem cabe: nenhum dos 15 itens de menu reais estoura os
   124 px uteis (o maior, "Sobre o aparelho", sobra 6 px).

Resta do M5 apenas converter `RB12` -> formato de fonte do LVGL e
confirmar se o firmware aceita fonte de 4 bpp (§15.5).

### Mapa do firmware — partes A e B (2026-09-14)

Sobre a **ORIGINAL**, nao sobre a nossa imagem (77 ganchos poluiriam).

| documento | o que traz |
|---|---|
| `docs/SIMBOLOS.md` | 412 funcoes nomeadas, recuperadas do binario |
| `docs/ARQUITETURA.md` | MVP, 4 camadas, caminho da tecla, nossos 2 acidentes |
| `docs/PAGINAS.md` | as 61 paginas: numero <-> presenter <-> view |
| `docs/AUXILIARES.md` | grafo de chamadas; as 2.798 anonimas ranqueadas |
| `docs/COBERTURA.md` | quanto do firmware sabemos, medido |

Achados que mudam entendimento:
- o firmware e **MVP** e diz isso (`keyManager_send_alarm_msg_to_presenter`,
  `dshow_send_oper_msg_to_view`). **`pstr_` = PreSenTeR**;
- presenter identifica tela por NUMERO, view por NOME;
- a guarda de cartao SD que neutralizamos esta dentro de
  **`view_page_msg_analysis`** — o roteador de TODA mensagem de pagina.
  Risco maior do que eu havia registrado;
- `page1_process` na verdade e **`page1_img_process`**;
- numeracao: o ID da pagina e a autoridade; o numero no NOME do presenter
  bate ate a 70 e fica +1 da 75 em diante (historico). `page84` = 0x53.

Limites registrados: A cobre 12,8% das funcoes (teto do metodo e 14,8% —
so 475 logam nome); o grafo nao ve callbacks nem thunks sem prologo.

**Parte C (fronteiras do que nao sabemos) adiada a pedido do mantenedor.**

### Pipeline — resultado (2026-09-14)

`tools/build.py`. Roda 6 dos 20 passos e **para por motivo estrutural**,
nao por falta de passo.

CAUSA DE FUNDO: ~12 ferramentas escolhem o endereco da propria rotina com
um ALOCADOR INCREMENTAL (varrem a area livre e se encaixam apos o ultimo
byte ocupado). O endereco **emerge da ordem historica**; os patches
seguintes o fixam no codigo.

Medida: apos 6 passos da receita a area livre comeca em `0x001A4041`,
mas `patch_cor_texto_lista` exige a rotina em `0x001A3518` — 2.857 bytes
antes. Na historia aquele patch rodou mais cedo.

**A corrente so compoe na ordem historica exata, patches mortos incluidos.**

Achados de contabilidade, pelo caminho:
- `patch_home_keys.py` nao constava nem na receita nem nos excluidos;
- `patch_chrome_padrao.py` e **pre-requisito** do Saturno, nao superado —
  a tabela de tema e revestimento sobre ele, nao fundacao;
- `patch_cor_texto_lista.py`, idem para o S10.

CAMINHO PARA A 3.0: tirar dos patches a decisao de onde morar. Cada
ferramenta que aloca recebe `--em <endereco>`; a receita declara o mapa da
area livre. Sao ~12 ferramentas. So depois disso uma reconstrucao limpa a
partir do ORIGINAL e possivel.

### Pipeline CONCLUIDO (2026-09-14)

`tools/build.py` reconstroi a imagem do **ORIGINAL** em **24 passos
declarados**, com endereco explicito para quem aloca na area livre.

O QUE FOI PRECISO MUDAR

- **7 ferramentas** ganharam `--em <endereco>`: antes escolhiam sozinhas
  (alocador incremental) e o endereco emergia da ordem;
- `build.py` declara o MAPA da area livre e **confere apos cada passo**
  que a ferramenta nao escreveu fora dos lotes declarados;
- `patch_menu_text.py` passou a **seguir a tabela de idioma viva**
  (ponteiro em `0x00121104`) em vez de supor o endereco de fabrica. Sem
  isso ele escrevia numa copia que ninguem le e "funcionava" sem efeito.

ORDEM: descobertas que nao eram preferencia, eram requisito

- `patch_titulos` ANTES do chrome: exige 4 KiB virgens em `0x001A5000`;
- `relocate_lang_table --add Extras` ANTES do submenu: a tabela pt tem
  216 ids e emenda direto na do espanhol; sem realocar, um id 216 leria
  "Español";
- `patch_menu_text` DEPOIS do `aplica_textos`, que reescreve a tabela
  inteira e reverteria a edicao;
- `patch_chrome_padrao` e `patch_cor_texto_lista` sao **pre-requisitos**
  do Saturno, nao superados por ele.

O BUG QUE ELE ACHOU — e e da classe que ja matou um aparelho

**9 ferramentas gravavam o CRC da FIRM em `0x00D01C`**, dentro do setor
`0x00D000` — a tabela de particoes. A regra R1 diz que esse setor NUNCA
deve ser escrito. Ninguem tinha percebido porque a cadeia nunca fora
reconstruida do zero para comparacao.

Todas neutralizadas. O setor `0x00D000` agora fica intocado pela
construcao inteira.

VALIDACAO

`validate_firmware.py` na imagem construida: 21 OK, 1 falha — **a mesma
falha da v073 que boota** (CRC da FIRM, que a R1 manda nao regravar).
`audita_chrome.py`: sem divergencias.

Diferenca para a v073: 12.312 bytes em 38 setores, concentrados na area
livre (enderecos agora declarados) e na regiao de textos. **Nao e
byte-identica de proposito** — a receita coloca as coisas onde nos
mandamos, nao onde a historia calhou.

PENDENTE antes de gravar: a imagem do `build.py` **nunca foi testada no
aparelho**. Ela e equivalente a 2.2 em conteudo, nao as correcoes 2.3/2.4.

### Receita consolidada — 22 passos (2026-09-14)

Duas decisoes do mantenedor, aplicadas:

**1. O EXTRAS SAIU DA RECEITA.** `patch_extras` + `_fix` + `_fix2` sao
tres patches empilhados no mesmo ponto e os seis itens continuam sem
abrir. Sem eles o Extras volta ao comportamento de fabrica: os tres
primeiros itens abrem, os outros tres nao fazem nada. Pior em funcao,
melhor em honestidade — **nada na receita finge funcionar**. Fica em
`FORA` com o motivo escrito, nao esquecido.

**2. `patch_titulo_orfao` foi INCORPORADO ao `patch_titulos`.** Era um
segundo patch que realocava a rotina para `0x001A5C00` porque a logica
nova nao cabia. Agora e um patch so, no lugar certo, sem realocacao.

De quebra, a rotina deixou de ser codificada A MAO e passou a ser montada
pelo clang (`tools/asm.py`). Os dois piores bugs de encoding do projeto
vieram de montar a mao E escrever o verificador a partir da mesma
suposicao errada.

ARMADILHA ENCONTRADA NA CONSOLIDACAO: duas passadas de montagem nao
bastam. O tamanho do codigo muda conforme os enderecos entram no pool de
literais, o que move o slot, o que muda o codigo de novo. Com duas
passadas os literais apontavam para o layout da passada anterior — o slot
caia dentro do pool e a tabela comecava 4 bytes cedo. Agora itera ate
convergir, e **falha alto** se nao convergir em 8 voltas.

ESTADO DA RECEITA

    22 passos, do ORIGINAL a imagem final
    21 ferramentas fora, cada uma com o motivo declarado
    validate_firmware: 21 OK, 1 falha — a MESMA da v073 que boota
    audita_chrome: sem divergencias
    setor 0x00D000: INTOCADO; menor offset alterado 0x04867C (R1 ok)

NAO TESTADA NO APARELHO.
