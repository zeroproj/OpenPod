# Estado atual — leia isto primeiro

> Atualizado em **2026-09-14**, depois da limpeza que removeu a linha 2.x.
>
> **Este é o documento de entrada.** Depois dele: `CLAUDE.md` (regras do
> projeto), `PROTOCOLO_GRAVACAO.md` (como gravar), `MODO_DOWNLOAD.md`
> (como recuperar).

---

## 1. Onde o aparelho está

```
OpenPod Core 1.0.1   <- NO APARELHO, e a unica STABLE
                        firmware/RELEASE/OpenPod Core 1.0.1/
                        imagem     7312fbd066b1a31e508a51c9c44c5e20...
                        carimbada  36125f5665b8613e0d96215e2ffcf361...
```

Confirmada na tela pelo mantenedor em 14/09: *"Tudo funcionou."*

**Não existe nenhuma outra versão viva.** Se você encontrar referência a
uma Core 2.x, a uma OpenPod 1.4–3.1 ou a um kit `V0xx`, é referência
morta: foi tudo removido em 14/09 e não deve ser usado como base.

### Como reconstruir a 1.0.1 do zero

```
tools/build.py --receita core1.0
```

É a única receita que existe. **Seis passos**, partindo do ORIGINAL:

```
1. patch_logo.py              a logo do OpenPod na tela de abertura
2. patch_fundo_abertura.py    o fundo da abertura fica preto
3. relocate_lang_table.py     tabela do portugues para a area livre
4. aplica_textos.py           textos revisados em portugues do Brasil
5. patch_menu_text.py         'Video' com maiuscula
6. patch_update_sd.py         item 'Atualizar por SD' em Configurar
```

A imagem **sem carimbo** é reproduzível byte a byte. A carimbada não —
ver `docs/releases/OpenPod_Core_1.0.1.md` §7-bis.

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
M-a  separador entre itens    existe, deveria sumir     1 BYTE   0x0012179E
M-b  home                     grade 3x3, deveria ser LISTA        codigo novo
M-c  titulo na faixa          nao existe                          rotina
M-d  barra de rolagem         existe, deveria sumir               1 ponto
M-e  icones de linha          existem, deveriam sumir             1 ponto
M-f  selecao                  A MEDIR
M-g  bateria                  glifo mono, deveria ser colorida    bitmap
M-h  degrade da faixa         faixa lisa                          rotina
M-i  as 6 cores               A MEDIR
M-j  luminancia               DESVIO ACEITO — nao fazer (§0-bis)
```

**O passo 1 é o M-a**: um byte, em código de fábrica, verificável na tela
em segundos. É o único item do alvo que não dependia da infraestrutura
removida na limpeza.

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
