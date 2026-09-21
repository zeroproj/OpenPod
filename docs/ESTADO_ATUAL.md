# Estado atual — leia isto primeiro

> Atualizado em **2026-09-17**, depois do incidente da 3.1.2.
>
> **Este é o documento de entrada.** Depois dele: `CLAUDE.md` (regras do
> projeto), `PROTOCOLO_GRAVACAO.md` (como gravar), `MODO_DOWNLOAD.md`
> (como recuperar).

---

## ONDE PARAMOS — 2026-09-20

**No aparelho:** Beta 13, funcionando (= Beta 12 + salto no-op).
**No ar (GitHub Pages):** Beta 7. Nada publicado depois disso.
**Pronta para testar:** **Beta 14** — o conserto do índice do Extras,
escrito e validado estaticamente em 2026-09-21. Ver
`release/OpenPod-Core-5.7-Public-Beta-14/TESTAR.txt`.

### As versões que existem

| | |
|---|---|
| `release/OpenPod-Core-5.7-Public-Beta-12/` | **a boa.** Extras abre, música toca |
| `release/OpenPod-Core-5.7-Public-Beta-13/` | um teste, não uma versão |
| `release/OpenPod-Fabrica/` | o firmware de fábrica, para comparar |

### O que a Beta 12 entrega

listas de 9 linhas · Bluetooth e Hora e data com linha de 16 px ·
tempos em `mm:ss` · contador `7 - 152` · fundo preto na Tocando Agora ·
bateria prateada com miolo verde · Extras com seis itens

### A pergunta que trava tudo — RESPONDIDA 2026-09-21

A **Beta 10** aplicou um conserto que passou em **toda** verificação
estática disponível — e quebrou os seis itens do Extras.

A **Beta 13** isolou a variável: mesmo salto, destino fazendo exatamente
o que a cauda original fazia. **Resultado no aparelho: os seis itens
abrem** (relato do mantenedor: Livro abre e escaneia, Imagem abre vazia,
BT abre e ativa). **Resultado (a): o salto e a área livre estão bons;
o erro da Beta 10 estava na lógica** (`cmp r5,#4` / `r1=2,r2=6`).

**O conserto do índice do Extras (`docs/EXTRAS_INDICE.md`) está
LIBERADO para escrita.** Ele não usa `r5` nem toca `r1`/`r2` na cauda:
reescreve `[r4,#0xc]` antes da preparação, valendo para os dois
caminhos de abertura.

### Aberto

| | onde | estado |
|---|---|---|
| Bluetooth reinicia | despacho do Extras | **causa conhecida**: `docs/EXTRAS_INDICE.md` |
| Imagem e Livro sem biblioteca | despacho do Extras | **mesma causa** |
| Pastas só volta depois de entrar | Extras | aberto, duas tentativas refutadas |
| título mostra o nome do arquivo | tela de música | `r3=2` refutado — reinicia. Ler o construtor `0x00D6DB3C` antes de tentar outro valor |
| ícone do BT sobre "OpenPod" | faixa superior | **decisão de projeto**: o texto tem 52 px, o vão tem 23. Não cabe |
| tempo restante `-3:55` | tela de música | retirado na Beta 12 — era suspeito de travar a música |

### Três lições que custaram caro

1. **Varredura por forma sempre perde alguém e não avisa.** Bateria: 4
   de 7 escritores. Altura de linha: 1 de 6 sítios. Varrer por
   **significado** — desmontar e procurar o padrão.
2. **Verificação estática não basta neste firmware.** A Beta 10 provou.
3. **Conclusão larga de teste estreito.** A Beta 9 reverteu "a região do
   Bluetooth" — que continha seis páginas diferentes — e eu concluí "não
   é nosso". Era.


## 1. Onde o aparelho está

```
OpenPod Core 5.0     <- O PONTO ESTAVEL. A tela inicial e
                        Musica | Video | Extras | Configurar.
                        firmware/RELEASE/OpenPod Core 5.0/

OpenPod Core 4.7     <- o ponto estavel anterior. Extras completo, voltar certo,
                        M e VOL inertes. firmware/RELEASE/OpenPod Core 4.7/

OpenPod Core 4.6     <- o voltar retorna ao Extras.
                        firmware/RELEASE/OpenPod Core 4.6/

OpenPod Core 4.2     <- o ponto estavel anterior. O Extras fechado: os seis
                        itens abrem, o Radio sintoniza, Imagem e Livro
                        digital varrem o cartao, e o item da home se
                        chama "Extras" nos nove idiomas.
                        firmware/RELEASE/OpenPod Core 4.2/

OpenPod Core 3.7     <- o ponto estavel anterior.

OpenPod Core 3.6     <- o passo atras.
                        Os seis itens do Extras abrem, e o Radio
                        sintoniza. Confirmada na tela em 17/09.
                        firmware/RELEASE/OpenPod Core 3.6/

OpenPod Core 3.4     <- o passo atras. Tudo abre, Radio nao sintoniza.
                        firmware/RELEASE/OpenPod Core 3.4/

OpenPod Core 3.3     <- metade LVGL, tambem confirmada. O passo atras.

OpenPod Core 3.0.1   <- a base sa de onde a 3.3/3.4 sairam.

OpenPod Core 1.0.1   <- A BASELINE reproduzivel byte a byte.
                        tools/build.py --receita core1.0
                        sha 7312fbd066b1a31e508a51c9c44c5e20...
```

### O estado de cada linha

| Versão | Confirmada na tela | Observação |
|---|---|---|
| 1.0.1 | ✅ | baseline, única receita que existe |
| 1.1 | ✅ | *"Excelente"* |
| 1.4 | ✅ | fim da linha Marte (M-a…M-e) |
| 2.0 – 2.2 | — | sem registro de teste |
| 2.3 | ⚠️ em parte | só a faixa com "OpenPod" |
| **2.4** | — | **declarada a última estável** (LEIA-ME da 3.1.2) |
| 3.0 / 3.0.1 | — | primeira tela Extras |
| 3.1 | ❌ | apagou a saída do handler (`0x00D2F01A`) |
| 3.1.1 | ❌ | só trocou 6 bytes de tabela; não corrigiu |
| 3.1.2 | ❌ | apagou 5 destinos de desvio |
| **3.2** | ❌ | **TRAVOU o aparelho.** Chamava navegação do callback do LVGL. OBSOLETA |
| **3.3** | ✅ | metade LVGL. Confirmada: nada travou, itens 4-6 inertes |
| **3.4** | ✅ | os seis itens abrem. **Rádio abre mas não sintoniza** |
| **3.5** | ❌ | quebrou os menus: saltava para casos da home. OBSOLETA |
| **3.6** | ✅ | Rádio sintoniza |
| **3.7** | ✅ | **O PONTO ESTÁVEL.** Tudo funciona no Extras |
| **3.8** | ⚠️ | equivale à 3.7 |
| **3.9** | ✅ | experimento: Livro digital varre. Mecanismo provado |
| **4.0** | ❌ | Imagem travava tudo depois (origem fixa = home) |
| **4.1** | ✅ | rótulo "Extras" nos nove idiomas |
| **4.2** | ✅ | o Extras fechado |
| **4.3** | ❌ | réplica da Pastas: nem abria. OBSOLETA |
| **4.4** | ✅ | = 4.2; o voltar não foi resolvido |
| **4.5** | ❌ | **TRAVOU o aparelho**: `bx lr` sem desfazer o push. OBSOLETA |
| **4.6** | ✅ | o voltar retorna ao Extras |
| **4.7** | ✅ | **A ÚLTIMA BOA.** M e VOL inertes na tela inicial |
| **4.8** | ⚠️ | home com 4 itens, mas **Configurar não abre** |
| **4.9** | ⚠️ | idem; acrescentou `movs r0,#1`, não resolveu |
| DIAG 6 | 🔍 | índice 3 abre o Extras ⇒ o código executa |
| DIAG 7 | ✅ | o `sub` era o culpado |
| **5.0** | ✅ | a tela inicial do OpenPod |
| **5.1** | ⚠️ | contexto da Pastas — não resolveu. `docs/PASTAS_ABERTO.md` |
| 5.2 – 5.6 | ✅ | faixa 16 px, alinhamento, cores da bateria |
| **5.7** | ✅ | **NO APARELHO = PUBLIC BETA 2.** Bateria com casca prateada e miolo verde do Marte: `docs/BATERIA_VERDE.md`. Na tela Informação: `OpenPod 5.7 Beta 2` — o nome completo não cabe nos 113 px |

> ⚠️ **Não tente consertar a 3.1.2 com mais um patch.** Seriam quatro
> remendos em cima do mesmo código danificado. Volte para a 2.4.

### Antes de empacotar qualquer imagem nova

```
python3 tools/check_branch_targets.py \
    firmware/ORIGINAL/GN438_original.bin \
    firmware/WORKING/<nova>.bin \
    --baseline firmware/WORKING/GN438_core_2.4.bin
```

Tem que sair **APROVADO**. Essa checagem teria barrado a 3.1 e a 3.1.2.

---

## 2. O que a 1.0.1 entrega

| | |
|---|---|
| textos | 175 revisados em português do Brasil; cabem em 113 px |
| tela de abertura | logo do OpenPod sobre preto, sem moldura clara |
| tela Sobre | título curto, versão em uma linha, sem sobreposição |
| atualização por SD | `Configurar → Atualizar por SD` arma o flag e reinicia |

**O que ela deliberadamente NÃO faz:** a home continua a **grade 3×3 de
fábrica**. Não há home em lista, faixa superior com título, tabela de
tema, submenu Extras nem cor de seleção. Isso é escolha, não pendência:
a 1.0 existe para ser uma fundação em que um defeito tenha causa óbvia.

---

## 3. Por que a linha 2.x foi removida — 2026-09-14

> ⚠️ **Esta seção é histórica.** A linha 2.x foi removida em 14/09 e
> **reconstruída depois**, do zero, sem o acoplamento da barra superior.
> A Core 2.0–2.4 que existe hoje em `firmware/RELEASE/` é a linha nova, e
> a 2.4 é a última estável. O que segue explica por que a linha *velha*
> morreu — a lição continua valendo, o veredito sobre as versões não.


Pedido do mantenedor, nas palavras dele:

> *"realmente você está pegando códigos e problemas de versões anteriores
> bugadas. Pedi para você mudar só o menu, você veio com um update 2.4 com
> alteração da barra superior que não pedi."*

Procede, e **a causa era estrutural, não desatenção.** As receitas 2.x
encadeavam até 31 passos em que o `patch_chrome_padrao` — a barra
superior — era **pré-requisito declarado** dos doze passos do Saturno.
Mexer em qualquer item da lista arrastava a barra junto, porque a receita
não permitia separar. O acoplamento estava na receita, não no firmware.

**Agravante medido:** havia duas coisas chamadas "OpenPod 1.0" no mesmo
repositório — `historico/releases/OpenPod 1.0` (linha morta) e
`firmware/RELEASE/OpenPod Core 1.0.1` (linha viva). Isso dava margem para
buscar referência na errada.

### O que sobreviveu, e onde está

As **medições sobre o firmware de fábrica** foram extraídas antes de
apagar os planos, e estão em **`docs/GUI_ANALYSIS.md` PARTE IV**:

- os dois caminhos de desenho do firmware (home × as 36 telas de lista);
- o laço da home decodificado — são **dois objetos por item**;
- o molde certo, que já existe de fábrica em `page_home_menu_event_cb`;
- o perigo medido da alocação na página `0x53`;
- os pontos de cor e fonte.

> ⚠️ **Cuidado com endereços `0x001A5xxx`.** Aquela faixa era onde os
> patches da 2.x escreviam. Ela **não existe no firmware de fábrica**. Se
> um documento citar `0x1A5400` como se fosse do firmware, é engano.

### A regra que fica

**Volta um passo por vez, testado no aparelho, e nunca empacotado com
algo que não foi pedido.**

---

## 4. Como gravar

Pelo cartão SD, que é como o mantenedor atualiza:

```
1. copie  firmware/RELEASE/OpenPod Core 1.0.1/OpenPod_Core_1.0.1.up
   para a RAIZ do cartao, com o nome  update.up
2. no aparelho: Configurar -> Atualizar por SD -> Sim
3. ele reinicia e se atualiza
4. APAGUE o update.up do cartao
```

O `.up` **não confere estado** — reescreve a imagem inteira, então
funciona a partir de qualquer versão.

> **A primeira instalação sobre o firmware de FÁBRICA tem de ser por
> cabo.** O firmware de fábrica não tem caminho de interface para o
> update por SD — o item "Atualizar por SD" é justamente uma das coisas
> que a Core 1.0 traz. Depois disso, o cartão resolve.

> ⚠️ O kit por cabo da 1.0.1 é **diferencial** (2 setores) e **recusa** se
> o aparelho não estiver na Core 1.0. O kit da Core 1.0 foi removido na
> limpeza. Para ir de fábrica até a 1.0.1 hoje: gere a imagem completa com
> `tools/build.py --receita core1.0` e grave por `recovery/`.

---

## 5. Como recuperar, se quebrar

```
USB conectado  ->  segure VOLUME ↓  ->  aperte RESET
```

O aparelho enumera como `301a:2800` e a flash fica toda acessível, mesmo
com o firmware destruído. Foi assim que o primeiro aparelho voltou depois
do incidente da V028.

```
recovery/                  o caminho de volta, com SHA256SUMS
recovery/modo_download/    smtlink_dump, firmware de fabrica, ptable 0xD000
recovery/imagens/          GN438_original.bin, OpenPod_Core_1.0.1.bin,
                           ptable_D000_original.bin, restaura_original.up
```

**Este hardware é recuperável por software, sempre.** A ROM de máscara
roda antes de qualquer coisa que a gente escreva.

---

## 6. Onde estão as coisas

```
firmware/
  ORIGINAL/      GN438_original.bin — SAGRADO, sha b7cd5eb9...
  RELEASE/       so  OpenPod Core 1.0.1/
  WORKING/       analysis, core_1.0.1, rebuilt_original, restore.up
  VENDOR/        Flashloader SL-DEV oficial da Shenju
  READBACK/      leituras do aparelho

recovery/        caminho de volta + modo_download
marte/           a BASE VISUAL — mockups e paleta de referencia
analysis/        a engenharia reversa
extracted/       recursos extraidos do firmware
tools/           ferramentas; cada uma com o porque no cabecalho
docs/            o entendimento do firmware
```

### Por onde começar a entender o firmware

```
FIRMWARE_ANALYSIS.md   as 23 perguntas respondidas
FIRMWARE_MAP.md        o mapa real dos 2 MiB
ARQUITETURA.md         MVP, camadas, caminho da tecla
GUI_ANALYSIS.md        a GUI — e a PARTE IV, as medicoes herdadas
SIMBOLOS.md            412 funcoes recuperadas
COBERTURA.md           o que sabemos e o que NAO sabemos
MARTE_ALVO.md          a especificacao visual do produto
```

---

## 7. O próximo passo — a tabela de trabalho do Marte

**A base visual é o `marte/`**, e o alvo concreto é
`marte/mockups/marte_completo.png`.

A distância entre o que está no aparelho e esse alvo está medida item a
item em **`docs/MARTE_ALVO.md` §2**, na tabela **M-a … M-j**, cada linha
com classe de confiança e evidência citada. A ordem de trabalho está na
**§3**.

Resumo da distância, hoje:

```
M-a  separador entre itens    FEITO  Core 1.1, visto na tela
M-b  home                     grade 3x3, deveria ser LISTA        codigo novo
M-c  faixa na home            FEITO  Core 2.3
M-d  barra de rolagem         existe, deveria sumir               1 ponto
M-e  icones de linha          existem, deveriam sumir             1 ponto
M-f  selecao                  FEITO  Core 1.2, 2 bytes (cor)
                              falta so o DEGRADE, que e o M-h
M-g  bateria                  glifo mono, deveria ser colorida    bitmap
M-h  degrade da faixa         faixa lisa                          rotina
M-i  as 6 cores               A MEDIR
M-j  luminancia               DESVIO ACEITO — nao fazer (§0-bis)
```

~~**O passo 1 é o M-a**~~ ✅ **FEITO** — Core 1.1, confirmada na tela em
14/09. Ver `docs/releases/OpenPod_Core_1.1.md`.

**O passo seguinte** é o M-b, a home. O pré-requisito dele (mapear a
estrutura de `page_home_create`) foi fechado no mesmo dia —
`CARCACA_PADRAO.md` §4.3.

**O marco de verdade é o M-b** — a home virar lista é o que faz o
aparelho *parecer* o Marte. E o que travava esse passo caiu por medição:
converter a home **não encosta em alocação**.

---

## 8. Investigações em aberto

Nenhuma delas bloqueia a 1.0.1. São conhecimento que falta.

| # | em aberto |
|---|---|
| 1 | **A camada de mensagem não quebra linha.** `page_info` monta uma mensagem (descritor `0x008238F0`, entregue a `0x00D0D818`) e esse caminho ignora `\n`. Por isso a tela Sobre mostra uma linha só. Confirmado na tela |
| 2 | **O desenho do descanso de tela.** Não existe página de descanso — só `page_scrsaver_time`, que é a configuração. O relógio grande é desenhado sem transição de página, e o chrome só é destruído em `view_page_create` |
| 3 | **ESC (`0x1B`) morto nas subtelas** — cai num `pop` puro. Só importa se algum botão emitir `0x1B`; não se sabe se algum emite |
| 4 | **28 telas fora da tabela de navegação** — não tratam `0x12` como "próximo". Entre elas o **Now Playing** |
| 5 | **Página 23 (`page_record_time`) não identificada** — tem faixa e linhas, mas só carrega glifos de ícone |
| 6 | **O contador da lista de Música não foi localizado** — a página `0x03` só faz `align(CENTER)` e `set_width` |

---

## 9. As regras que custaram versão

Estão em `PROTOCOLO_GRAVACAO.md` (R0–R7) e em
`OpenPod_Design_System.md` (R-L1 a R-L3). As que mais se repetiram:

- **Um caminho corrigido, outro esquecido.** Quando um patch muda a
  aparência de um objeto, enumerar **todos** os pontos que criam ou
  repintam aquele objeto.
- **Semelhança visual não é evidência de código compartilhado.** Extras e
  Configurar *parecem* a mesma tela e são funções diferentes.
- **Prévia em ASCII prova correção, não estética.** Para decisão visual,
  o aparelho é o único juiz.
- **Nenhuma versão nova é gerada sem o mantenedor pedir.** Corrige-se,
  valida-se, e só então se empacota.
- **Aparência se decide pela referência do Marte**, ou pelos objetos
  dele — nunca por invenção.
