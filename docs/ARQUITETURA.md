# ARQUITETURA — como o firmware está organizado

Escrito em 2026-09-14 a partir de `docs/SIMBOLOS.md`, que recuperou 412
nomes de função do próprio binário. Base: **`GN438_original.bin`**, de
fábrica — não a nossa imagem de trabalho.

---

## 1. O firmware é MVP, e ele mesmo diz isso

Três nomes que atravessam camadas provam a estrutura:

```
0x000FC4D4  keyManager_send_alarm_msg_to_presenter
0x000FFF2C  dshow_send_oper_msg_to_view
0x00123E50  view_page_msg_analysis
```

**`keyManager` → `presenter` → `view`.** É Model-View-Presenter clássico.

E isso decifra o prefixo mais comum do firmware:

> **`pstr_` = PreSenTeR.** São 121 nomes `pstr_*`. Eu vinha tratando isso
> como uma abreviação opaca por semanas.

---

## 2. As quatro camadas, por faixa de endereço

| faixa | camada | símbolos | como os nomes são formados |
|---|---|---|---|
| `0x0F0000`–`0x100000` | **sistema / tarefas** | 18 | `watch_view_task`, `keyManager_*`, `usbd_cb` |
| `0x100000`–`0x110000` | **PRESENTER** | 112 | `pageNN_*`, `pstr_pageNN_*` — por **número** |
| `0x120000`–`0x140000` | **VIEW** | 200 | `page_<nome>_create`, `view_*` — por **nome** |
| `0x140000`+ | **LVGL / infra** | 82 | `lv_*`, `get_local_style` |

A tabela completa das 61 páginas — número, presenter, view e nome — está
em **`docs/PAGINAS.md`**.

A descoberta que organiza tudo:

> **O presenter identifica as telas por NÚMERO (`page4`, `page84`); a view
> as identifica por NOME (`page_music_play_create`).** São dois
> vocabulários para a mesma tela, em camadas diferentes.

O firmware cita números de página de **1 a 84**; 61 aparecem por nome (as
23 restantes têm presenter sem log).

---

## 3. O caminho de uma tecla até a tela

```
   tecla física
        |
   keyManager                      0x000FC4D4  (camada de sistema)
        |  send_alarm_msg_to_presenter
        v
   PRESENTER  pstr_pageNN_process  0x10xxxx
        |     decide O QUE acontece: valida cartao, volume,
        |     indice sujo; escolhe a proxima pagina
        |
        |  dshow_send_oper_msg_to_view   0x000FFF2C
        v
   VIEW   view_page_msg_analysis   0x00123E50
        |  roteia a mensagem para a pagina
        v
   page_<nome>_create              0x12xxxx / 0x13xxxx
        |  monta os objetos LVGL
        v
   LVGL  get_local_style, lv_obj_*  0x14xxxx
```

Os nossos ganchos do Saturno entram **entre a view e o LVGL** — por isso
mudam aparência sem tocar em comportamento. Foi acidental, mas está certo.

---

## 4. Os nossos dois acidentes, agora explicados

Ambos aconteceram em funções que até hoje eram **blocos anônimos**.

### 4.1 O tratador de cartão SD (`patch_titulos`)

Neutralizamos uma guarda em `0x00123E8A`. O mapa mostra onde isso fica:

```
0x00123E50  view_page_msg_analysis   <- inicio da funcao
0x00123E8A  ................. +0x3A  <- a guarda que mexemos
```

**Está dentro de `view_page_msg_analysis`** — a função que roteia *toda*
mensagem de página para a view.

### Correção: eu superestimei este risco

Escrevi acima que "mexer ali afeta o caminho de todas as páginas". **Fui
verificar e não é isso.** A função despacha por subtipo:

```
0x00123E5C  ldrb r1,[r0,#0x0c]
0x00123E5E  cmp  r1,#6
0x00123E62  tbb  [pc,r1]        <- 7 ramos
```

Decodificando a tabela `tbb`:

| subtipo | destino | |
|---|---|---|
| 0 | `0x123E6E` | |
| **1** | **`0x123E76`** | **o ramo que cortamos** |
| 2..6 | `0x123EB2`..`0x123EFA` | intocados |

Nosso corte fica **dentro do ramo 1, de 7**, e vai de `0x123E8A` até o
`pop` da função. O que esse ramo fazia:

```
se a pagina corrente e 1 (home) ou 0x51:
    se msg[0x0d] == 0  -> apaga o objeto em r6[0x14]
    senao, se vazio    -> cria com bl 0x00D226AC   (o criador de titulo)
```

Ou seja: era **o tratador de insercao/remocao de cartao SD** decidindo
criar ou apagar o icone do cartao — o mesmo slot que reaproveitamos para
o titulo. Cortar ali faz exatamente o que a 1.5 queria: tirar o cartao
deixa de apagar o titulo.

**Alcance real: 1 ramo de 7, dentro de um tipo de mensagem.** Os outros
seis continuam intactos. O risco é muito menor do que o que eu registrei
— e registrar errado para o lado do medo tambem e registrar errado.

### 4.2 O Extras (`patch_extras`)

`0x0010CC0C` = `pstr_page84_process` — **presenter**. E a mensagem morria
numa guarda de `page1_img_process` (`0x00100F3C`), também presenter.

Ou seja: os dois acidentes foram em camadas que sabíamos *usar* mas não
sabíamos **nomear**. O mapa não teria evitado o bug, mas teria mostrado
de cara que estávamos mexendo no roteador e no despachante.

### 4.3 Correções de nomenclatura nossa

| chamávamos | nome real do firmware |
|---|---|
| `page1_process` | **`page1_img_process`** |
| `pstr_page84_process` | confirmado, idêntico |

---

## 5. Cobertura: 80%

Dos 511 endereços que citamos em `docs/` e `tools/` dentro da faixa de
código, **409 (80%) caem dentro de uma função agora nomeada**.

As funções onde mais mexemos:

| citações | função |
|---|---|
| 46 | `page_home_event_cb` |
| 45 | `page_home_menu_event_cb` |
| 39 | `page1_img_process` |
| 34 | `view_option_callback` |
| 33 | `get_local_style` |
| 32 | `ebook_auto_play` |
| 23 | `volume_bar_key_event_cb` |

`get_local_style` é o despachante de estilo do LVGL — o alicerce do
Saturno. `page_home_*_event_cb` é a home, que é a régua do design.

---

## 6. O que NÃO tem nome, e por quê

Os criadores compartilhados que o Saturno mais usa **não aparecem** no
mapa:

```
0x001216F0  cria FAIXA        sem nome
0x00121690  cria CONTEINER    sem nome
0x00121764  cria LINHA        sem nome
0x001226AC  cria TITULO       sem nome
0x00123740  view_icon_create  sem nome
```

Motivo: **só funções que registram log têm nome**. Esses são auxiliares
pequenos, chamados de dentro das páginas, e não logam nada.

**`docs/AUXILIARES.md`** ataca isso por outro caminho: grafo de chamadas
sobre 3.210 funções e 11.283 arestas, ranqueando as **2.798 anônimas**
por número de chamadores. Não inventa nome — entrega evidência.

Resultados desta varredura:

| endereço | chamadores | confiança | o que é |
|---|---|---|---|
| `0x0010D818` | **173** | HIPÓTESE | primitiva de mensagem do presenter — a mais chamada da camada |
| `0x0010D880` | 88 | HIPÓTESE | monta struct de mensagem de 0x24 B |
| `0x000F780C` | 82 | PROVÁVEL | alocador (confere limite, loga, aloca) |

E a validação do método: os criadores do Saturno aparecem com **59, 51 e
36 chamadores** — contêiner, faixa e linha — batendo com o que já
tínhamos contado por outro caminho.

**O limite que essa varredura expôs:** 13 dos 29 auxiliares conhecidos
**não têm prólogo `push`** e escapam da detecção — incluindo todos os
setters de estilo e o despachante. São thunks de cauda. Ou seja, o
método erra sistematicamente na camada onde o Saturno mais trabalha.

---

## 7. Limites deste mapa

1. **`BAIXA` é pista, não fato.** 51 dos 412 símbolos são de funções que
   citam vários nomes — podem estar logando nomes alheios.
2. **Só 12 têm validação independente** (aparecem na tabela de páginas
   `0x00D23B38`). Os outros 349 `MEDIA` valem pela regra "cita um único
   nome", que é forte mas não é prova.
3. ~~**Numeração de página** ainda não conferida.~~ **RESOLVIDO** —
   `docs/PAGINAS.md` e `tools/mapa_paginas.py`. A ligação é
   `0x0010EF64[N-1]` → stub de 6 B em `0x0010F0B0` → presenter. O **ID da
   página é a autoridade** (duas tabelas independentes concordam); o
   número **no nome** do presenter bate até a 70 e fica **+1** da 75 em
   diante, por histórico de renumeração. `page84` e a página 0x53 são a
   mesma tela.
4. Nada disto substitui teste no aparelho: o mapa é estrutura, e os dois
   defeitos que nos custaram versões eram **comportamento em execução**.

---

## 8. O transporte entre presenter e view — a cadeia fechada

> **Correção.** A primeira versão desta seção chamava isto de "canal de
> diagnóstico / trace binário". **Errado.** Rastreando até o consumidor,
> é o **transporte de mensagens do MVP** — o caminho por onde toda
> mensagem do presenter chega à tela. Ver §8.5.

### 8.1 O escritor: moldura `0x55AA`

```
0x0010D818   se flag_global[0x3c] == 0: retorna
             r1 = msg[0x0a] + 0x0c          (tamanho + cabecalho)
             tail-call 0x00CF83E4

0x00CF83E4   trava
             confere espaco no buffer circular  (0x0081BBC0, RAM)
             grava cabecalho  0x55AA + tamanho(16 bits)
             grava o corpo
             destrava
```

Escreve registros emoldurados num buffer circular em RAM, sob trava,
gated por um flag global.

### 8.2 O canal de TEXTO, separado deste: `0x000002B0`

O padrão `ldr r0,=formato ; mov r1,arg ; bl 0x2b0` aparece **2.808
vezes** no código. As strings de formato são visíveis
(`"-%s mbox failed !!!"`, `"-%s no code:%d"`).

`0x000002B0` **não está no dump**. A flash é XIP em `0xC00000`, e o
arquivo começa com o cabeçalho **`HLKJ`** (`0x4A4B4C48`) — não é tabela
de vetores. Logo `0x2b0` é **mask ROM do SoC**, fora do nosso alcance.

Classificação: **PROVÁVEL** que seja um `printf` de depuração;
**HIPÓTESE** que produza saída neste hardware.

### 8.3 O consumidor — achado, e muda tudo

O leitor é `0x000F8444` (começa **antes** do `push`: carrega `r3` primeiro,
por isso a busca por prólogo errava o endereço). Ele lê 4 bytes, confere
o magic `0x55AA`, aloca um buffer do tamanho declarado e devolve o
registro.

Quem o chama, duas vezes, é **`watch_view_rec_analysis`** em `0x00124340`
— **camada VIEW**. E o laço é este:

```
124340  bl 0x00CF8444        le um registro
124344  mov r4, r0
124346  cbz r0, fim          buffer vazio -> sai
124348  bl 0x00D23E50        view_page_msg_analysis(msg)
12434C  mov r0, r4
12434E  bl 0x00D5811C        free(msg)
124352  b  0x00124340        repete
```

### 8.4 A cadeia completa, ponta a ponta

```
   tecla -> keyManager -> PRESENTER  pstr_pageNN_process
                              |
                              v
                          0x0010D818   (173 chamadores)
                              |
                              v
                          0x00CF83E4   moldura 0x55AA + tamanho
                              |
                              v
              [ buffer circular 0x0081BBC0, em RAM ]
                              |
                              v
   VIEW task  watch_view_rec_analysis  -> 0x00CF8444  (le e aloca)
                              |
                              v
                     view_page_msg_analysis   0x00D23E50
                              |
                              v
                     tbb de 7 ramos -> a tela
```

**É por aqui que passa tudo.** Inclusive a mensagem do Extras, e
inclusive o ramo cujo `ldrb` nós substituímos por um `b` (§4.1).

### 8.5 O que eu tinha concluído errado

Escrevi que `0x0010D818` era um "emissor de trace binário" e que o
buffer era um "canal de diagnóstico". A pista que me enganou foi boa: um
flag global que liga/desliga, moldura com magic, buffer circular — tudo
isso **parece** telemetria.

Mas é o **transporte de IPC** do MVP. O erro veio de parar antes do
consumidor: eu tinha o escritor e inventei o propósito. Com o leitor na
mão, o propósito se impôs sozinho.

Lição registrada: **um escritor sem consumidor não determina propósito.**

### 8.6 O que continua valendo como diagnóstico

O canal de TEXTO, sim: **2.808 chamadas a `0x000002B0`** com formato e
argumento, e as strings visíveis no binário. Esse permanece
`PROVÁVEL printf`, e permanece fora de alcance — `0x2b0` é mask ROM,
fora do dump (o arquivo começa com o cabeçalho `HLKJ`, não com tabela de
vetores).

### 8.4 Retratação

Eu havia escrito que `0x0010D818` "lê `msg[0x0a]`, **o mesmo campo da
guarda que matava o Extras**", insinuando ligação.

**Provavelmente errado.** Ali `msg[0x0a]` é somado a `0x0c` e usado como
**tamanho de registro**. No Extras, `msg[0x0a]` é comparado com 1, 2 e 4
e repassado ao abrir a página — é discriminador, não tamanho. São
**structs diferentes** que por acaso usam o mesmo deslocamento.

Coincidência de offset não é evidência de nada, e eu apresentei como se
fosse.

---

## 9. As configurações persistentes (NV) — subsistema identificado

Veio de investigar os símbolos `BAIXA`. Quatro funções citavam o mesmo
punhado de nomes (`authorization_code`, `bt_name`, `restore_factory`…) e
eu tinha marcado como "despachante ambíguo". **Não são nomes de função:
são CHAVES de configuração.**

### 9.1 A tabela de chaves — `0x000D85BB`

```
freq_drift      speaker_ctr   batlevel     usb_status    language
bright          offscr        scr_clock    voltage       profile
bt_info         alarm         btrlk        bt_name       bt_addr
pass            restore_factory            audio_volume
authorization_code           authorization_code_length
```

São exatamente os ajustes que aparecem na interface: brilho, tempo de
tela, idioma, volume, senha, nome Bluetooth.

### 9.2 Os acessadores

`0x00144EBC` abre com:

```
subs r0,#1 ; cmp r0,#0x19 ; bhi ; tbb [pc,r0]
```

Um `tbb` de **26 ramos** despachando por ID de chave (1..26). Cada ramo
carrega o ponteiro da string e chama um primitivo com
(chave, buffer, tamanho).

| função | primitivo | chamadas | provável papel |
|---|---|---|---|
| `0x00144EBC` | `0x0016B6A8` + `0x0016B694` | 1 + 1 | grava uma chave |
| `0x00145064` | `0x0016B694` | 13 | grava (variante) |
| `0x001452C6` | `0x0016B6BC` | 23 | **lê** |
| `0x001453B8` | `0x0016B6BC` | 22 | lê (com tratamento extra) |

E os primitivos são finos:

```
0x0016B6A8   ldr r0,[handle] ; b.w 0x00D6CEA4    GRAVA
0x0016B6BC   ldr r0,[handle] ; b.w 0x00D6CBDE    LE
```

Classificação: **PROVÁVEL**. A divisão leitura/escrita vem da assinatura
e da contagem de chamadas, não de rastrear o armazenamento até o fim.

### 9.3 Por que isto interessa ao OpenPod

Hoje o tema do Saturno vive numa **tabela de 19 bytes na flash**: mudar
exige gravar o aparelho. Este subsistema é o caminho para um dia o tema
ser **ajustável pelo usuário e persistente** — a Fase 2 do `CLAUDE.md`.

Não é para agora. Mas deixa de ser um desconhecido.

### 9.4 Efeito na qualidade do mapa de símbolos

Isto veio junto de uma correção de método. A primeira versão marcava como
`BAIXA` toda função que citasse mais de um nome. Mas
`page10_mbox_process` e `page10_scr_process` são a **mesma função** com
dois pontos de log — não ambiguidade.

Perguntar "quantos nomes?" era a pergunta errada. A certa é "**os nomes
concordam?**":

| | antes | depois |
|---|---|---|
| ALTA | 12 | 12 |
| MEDIA | 349 | **392** |
| BAIXA | **51** | **8** |

Os 8 que sobraram são ambiguidade real — e quatro deles eram justamente
este subsistema NV, que agora está identificado.

---

## 10. Como o texto traduzido chega à tela

Descoberto ao conferir um número meu que estava errado.

### 10.1 O caminho

```
presenter:   get_lang_str(id)                    163 chamadas
                 |
                 v
             pstr_cmd_view(ctrl, texto)          63 delas
                 |  zera um buffer de 0x414 B
                 |  cabecalho: [0]=0x48  [2]=0x0f  [4]=2  [6]=3
                 |  [0x0c] = ctrl            <- o MESMO campo do Extras
                 |  [0x14] = o texto, ate 1023 B (strncpy)
                 v
view:        recebe por mensagem e poe no rotulo
```

**O texto traduzido viaja dentro da mensagem**, copiado inteiro — não é
um id que a view resolve depois.

E isto fecha o layout da struct de mensagem, que até agora conhecíamos
só por pedaços, todos vindos do caso do Extras:

| offset | o que é | onde aprendemos |
|---|---|---|
| `0x00` | tipo (`0x48` aqui, `6` no caso do Extras) | §4.2 |
| `0x08` | página de origem | cauda `0x00101036` |
| `0x0a` | discriminador (1, 2, 4) | a guarda que matava o Extras |
| `0x0c` | **ctrl_id / parâmetro** | o que o nosso patch escreve |
| `0x14` | corpo (texto, até 1023 B) | **aqui** |

### 10.2 O erro que isto corrigiu

Eu havia varrido `lv_label_set_text` na camada VIEW e concluído: *"das
243 chamadas, só 35 vêm da tabela de idiomas"* — sugerindo que quase
nada é traduzível.

**Enganoso.** A varredura só via o que chega ao rótulo **direto**, dentro
da view. O caminho principal é o de cima, e por isso as 82 chamadas que
classifiquei como "origem não determinada" são, em boa parte, **texto
traduzido chegando por mensagem**.

O erro foi de método: medi uma camada e falei da tela. Num firmware MVP,
olhar só a view responde metade da pergunta.

O que **continua sólido** da varredura é a lista de **literais** em
`docs/TEXTOS_FIXOS.md` — `Time's up!`, `OK`, `yes`, `no` são texto em
inglês fixo no binário, e nenhuma tradução os alcança.

---

## 11. As 14 telas sem lista — por que elas divergem

Vale registrar porque explica um defeito e revela um padrão do firmware.

Essas telas **não usam a tabela de tema para nada geométrico**. Elas
calculam tudo a partir da altura da tela, dividida por uma constante que
fica num registrador:

```
0x001334E2   set_size(faixa, w, 160/r7)      r7 = 7  ->  22
0x00133504   CRIA_CONT
0x0013351C   r0 = 160/r7                            ->  22
0x00133520   r1 = 160 - r0                          -> 138
0x00133526   set_h(cont, 138)
0x0013352E   set_align(cont, 5)               BOTTOM -> topo em y=22
```

Ou seja: **o número 22 nunca é escrito** — ele nasce de `tela/7`. Por
isso a busca por imediatos nunca o encontrava, e por isso o S9 conseguiu
mudar a faixa sem que nada mais acompanhasse.

É o mesmo padrão das 10 telas de lista que calculam `tela/10` = 16 para a
altura da linha (§ do S11). **O firmware usa divisores da altura da tela
como unidade de layout**, não constantes.

Divisores observados:

| divisor | resultado | usado para |
|---|---|---|
| `tela/7` | 22 | faixa e contêiner das 14 telas sem lista |
| `tela/10` | 16 | altura de linha em 10 telas de lista |

Anotado porque muda como procurar: **um valor de layout pode não existir
como número no binário.**

---

## 12. O fundo do display é branco — a causa provável da faixa clara

Defeito aberto desde a 2.0: uma faixa clara sob o título, que não se move
e à qual não se consegue navegar. Eu já havia descartado herança de tema,
linha vazia e barra de rolagem.

### 12.1 A evidência

Em `lv_disp_drv_register`, imediatamente antes de criar as telas:

```
0x001567F6   movs   r3, #0xff
0x001567F8   strb.w r3, [r4, #0x29]
0x001567FC   strb.w r3, [r4, #0x2a]
0x00156800   strb.w r3, [r4, #0x2b]
0x00156804   movs   r0, #0
0x00156806   bl     0x00D491EC        <- cria a tela
```

Três bytes `0xFF` seguidos num `lv_disp_t`, logo antes das telas. É o
padrão do LVGL v8:

```c
disp->bg_color = lv_color_white();
disp->bg_opa   = LV_OPA_COVER;
```

**O fundo do display é branco.**

### 12.2 E ninguém pinta por cima

Varri as telas: **nenhuma página pinta o fundo do objeto de tela**. Quem
pinta são a faixa (`cor_faixa`) e o contêiner (preto, do getter
`0x0012138A`).

Então qualquer região que esses dois não cubram mostra o **branco do
display**. Nas listas, é a fresta entre o fim da faixa (`y=17`) e o
começo do contêiner (`y=19`).

Classificação: **PROVÁVEL**. Deduzi o campo pelo padrão do LVGL, não por
rastrear o renderizador — tentei e caiu em ruído. Parei.

### 12.3 A descoberta colateral, e ela é grave

**`cor_tela` da tabela do Saturno tem UM único leitor**: o thunk do S12,
que serve só a página 0x18. Fora dele, ninguém lê o campo.

Consequência direta: o **`DIAGNOSTICO cores/update.up`** que eu montei
para identificar a faixa **não consegue testar este defeito**. Ele muda
`cor_tela` para vermelho, e isso não pinta nada além da 0x18. Gravar
aquela imagem teria queimado uma sessão de teste para não responder nada.

Registro isso porque o erro foi meu e do tipo que se repete: **montei um
instrumento sem verificar se o que ele mede está ligado em algo.**

### 12.4 O teste certo — 1 byte

```
0x001567F6   movs r3, #0xff   ->   movs r3, #0x00
```

Fundo do display preto. Se a faixa clara sumir, está provado. Se ficar,
a causa é outra e a hipótese cai — o que também é resposta.

### 12.5 A correção definitiva, se confirmar

Não é pintar de preto: é fazer o fundo do display **ler `cor_tela`** da
tabela. Aí o campo deixa de ser morto, e o tema claro do Projeto Marte
(§ `PROJETO_MARTE.md`) passa a mudar o fundo do aparelho inteiro pelo
mesmo caminho — que é o que o Saturno existe para fazer.
