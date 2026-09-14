# OpenPod — Viabilidade: home com 4 itens + submenu "Extras"

> Pedido do mantenedor em 2026-09-12, depois de ver o V014 no aparelho:
> *"achei com muito dado na tela principal. É possível manter Música,
> Imagem, Extras e Configurar? O restante todo dentro de Extras."*
>
> **Veredito: VIÁVEL. A Parte A é dado puro. A Parte B é código novo em
> flash livre — e o obstáculo que eu esperava encontrar não existe.**

---

## 1. Como a navegação da home funciona, de verdade

Levantado por disassembly nesta investigação. São **duas** camadas, cada
uma com sua própria tabela de páginas:

```text
tecla Enter na home
   ↓
page_home_event_cb (VIEW, 0x00D2EA52)
   ↓  view_send(page=1, ctrl_grp=2, ctrl_id=índice, evento=4)
   ↓
   ├─ camada VIEW: view_msg_analysis -> tabela por página
   │
   └─ camada APP : tabela tbh de 83 entradas em 0x00D0DB1C
                      ↓  página 1 -> page1_process (0x00D00F3C)
                      ↓  confere msg->page == página corrente
                      ↓  tbh de 12 entradas em 0x00D00FBE, por ctrl_id
                      ↓  bloco fixo por item -> carrega o id da página
                      ↓  view_page_create(id)
```

### A tabela que decide o destino de cada item da home

`0x00D00FBE` — **12 halfwords**, `tbh [pc, r3, lsl #1]`, limite
`cmp r3, #0xB`:

| idx | valor | destino | item hoje |
|---|---|---|---|
| 0 | `0x000C` | `0x00D00FD6` | Música |
| 1 | `0x0054` | `0x00D01066` | vídeo |
| 2 | `0x009C` | `0x00D010F6` | Gravação |
| 3 | `0x00BF` | `0x00D0113C` | Rádio |
| 4 | `0x00D2` | `0x00D01162` | Livro digital |
| 5 | `0x00F8` | `0x00D011AE` | Imagem |
| 6 | `0x018C` | `0x00D012D6` | Bluetooth |
| 7 | `0x013E` | `0x00D0123A` | Configurar |
| 8 | `0x0167` | `0x00D0128C` | Ver pastas |
| 9–11 | — | — | existem, não usados pela grade |

> **Descoberta que muda a economia do problema:** o destino de cada item
> **não é código fixo em cadeia — é uma entrada de tabela.** Trocar para
> onde um item vai custa **2 bytes**.
>
> Isto corrige o enquadramento da `MENU_LISTA.md` §15.3, que dizia "ramo
> fixo por item". Os ramos são fixos, mas **quem escolhe o ramo é uma
> tabela editável**.

---

## 2. PARTE A — home com 4 itens: **VIÁVEL, só dado**

| # | Onde | O quê | Bytes |
|---|---|---|---|
| 1 | `0x00C486C4` | 4 primeiros ids de texto → Música, Imagem, Extras, Configurar | 16 |
| 2 | `0x00D00FBE+2` | idx1 → `0x00F8` (bloco da Imagem) | 2 |
| 3 | `0x00D00FBE+4` | idx2 → bloco do Extras | 2 |
| 4 | `0x00D00FBE+6` | idx3 → `0x013E` (bloco do Configurar) | 2 |
| 5 | `0x00D2ED88` | limite do laço `cmp r5,#0x24` → `#0x10` | 1 |
| 6 | `page_home_event_cb` | limites e voltas de índice: `8` → `3` | ~6 |
| 7 | `0x0004867C` / `0x000486A0` | 4 pares de coordenadas em vez de 9 | dado |
| 8 | folha `0x000CDD50` | 4 chevrons em vez de 9 | imagem |

**Nenhum `malloc`, nenhum offset de estrutura.** O `malloc(0x54)` da home
continua igual — sobra espaço, não falta. Os 5 objetos não criados ficam
NULL e nunca são indexados, porque os limites passam a 3.

### O único ponto que falta medir na Parte A

O texto **"Extras"** precisa de um id. As tabelas de idioma ficam em
`0x00C52744`–`0x00C53EE4` (8 idiomas). Falta:

- procurar um id livre ou uma string aproveitável (*Ferramentas*,
  *Outros*, *Extras*);
- se não houver, escrever a string em área livre e apontar a entrada do
  id em cada um dos 8 idiomas.

**NÃO DETERMINADO** — é a próxima medição.

---

## 3. PARTE B — a tela "Extras": **não há hospedeiro livre**

Varri as **83 tabelas de salto** da camada APP procurando uma tela de
lista com despacho por índice de 6 ou mais destinos que pudesse ser
reaproveitada. Só existem duas com esse formato:

| Módulo | Entradas | O que é |
|---|---|---|
| `page1_process` | 12 | **a própria home** |
| `page82_process` | 8 | `page_set_timershut_time` — seletor de tempo de desligamento |

E as candidatas de 6 entradas são todas telas em uso:
`page_music_mark`, `page_ebook_mark`, `page_video_list`,
`page_alarm_time`, `page_set_idleshut`, `page_scrsaver_time`.

**Conclusão: canibalizar não é opção.** Extras precisa de tela nova.

---

## 4. O obstáculo que eu esperava — e que NÃO existe

Há **12 ids de página completamente livres**, nas duas camadas:

```text
0x39  0x3A  0x3B  0x3D  0x3E  0x40  0x41  0x42  0x43  0x47  0x48  0x49
```

Na camada VIEW caem no erro de `view_page_create`; na camada APP, no
destino comum `0x00D0DF36` da tabela de 83 entradas.

**Mas usá-los esbarraria no alcance das tabelas de salto:**

| Tabela | Tipo | Alcance a partir da tabela |
|---|---|---|
| `view_page_create` `0x00D23B38` | **`tbb`** (byte) | 2 × 255 = **510 bytes** |
| camada APP `0x00D0DB1C` | `tbh` (halfword) | 2 × 65535 = 128 KiB |

A área livre da flash (`0x1A3038`, 364 KiB) fica em `0x00DA3038` na
janela XIP — **fora do alcance das duas**. Um id de página novo exigiria
achar bytes mortos perto das tabelas.

### A saída: reaproveitar a página `0x53`, que já tem os dois slots

A página `0x53` (`page_home_menu`) já tem entrada nas duas tabelas, e seu
conteúdo atual é inútil para nós (3 itens fixos; o módulo APP ignora todo
`ctrl_id != 0` — `MENU_LISTA.md` §15.3). Basta **desviar os dois pontos
de entrada**, e ambos são `BL`/`B.W`, com alcance de **±16 MB** — a flash
inteira tem 2 MiB:

```text
VIEW  0x00D23CF8   bl  page_home_menu_create   ->  bl  <create em flash livre>
APP   0x00D0DF2C   (corpo do page83_process)   ->  b.w <módulo em flash livre>
```

**4 bytes em cada.** O problema de alcance desaparece por construção.

---

## 5. Veredito por parte

| Parte | Classe | Custo | Risco |
|---|---|---|---|
| A — home com 4 itens | **dado** | ~30 B + imagem | baixo, erro visível na hora |
| B — tela Extras com 6 itens | **código novo** | 2 desvios de 4 B + código em flash livre | camada 6 |

### Ressalva que manda nas duas

> **A e B têm de ser gravadas juntas.** Uma home de 4 itens cujo "Extras"
> não abre nada é pior que a de hoje: esconde seis funções sem oferecer
> caminho para elas. Não existe meio-caminho seguro aqui.

### Sobre a Parte B ser "código novo"

Não é um obstáculo técnico — é uma mudança de categoria de trabalho:

- há **364 KiB de flash livre** (`0x1A3038`), fora da partição FIRM, logo
  **fora do CRC da FIRM** — não há checksum a satisfazer lá;
- a flash inteira é XIP em `0x00C00000`, então código gravado ali executa
  direto, com endereço conhecido em tempo de montagem;
- `page_home_create` e `page_set_menu_create` servem de modelo pronto
  para a tela de lista de 6 itens;
- `page1_process` serve de modelo para o despacho de 6 destinos.

**Mas:** até hoje o projeto só alterou **valores**. Escrever Thumb-2 novo
é o primeiro passo em que um erro pode não ser visual — e volta a valer
tudo o que a `MENU_LISTA.md` §14 dizia sobre montar inteiro, de uma vez,
com o kit de reversão já na máquina.

---

## 6. Recomendação

1. **Fechar a medição do texto "Extras"** (§2) — é análise estática, sem
   risco, e pode mudar o desenho: se não houver id livre, a string entra
   em área livre e as 8 tabelas de idioma precisam de um ponteiro cada.
2. **Escrever e validar a Parte B estaticamente** antes de tocar na
   Parte A: montar a tela e o módulo em flash livre, desmontar de volta e
   conferir instrução por instrução.
3. **Gravar A + B juntas**, como V016, com o kit do V015 já copiado para
   a máquina Linux.

> **Alternativa mais barata, se a prioridade for enxugar a tela já:**
> reordenar os 9 itens para pôr os mais usados no topo custa **2 bytes
> por item** na tabela `0x00C486C4` mais 2 na `0x00D00FBE`. Não resolve o
> pedido, mas é hoje, sem código novo. Fica registrada como opção, não
> como recomendação.

---

## 7. Classificação

| Afirmação | Classe |
|---|---|
| O destino de cada item da home vem de uma tabela `tbh` de 12 entradas em `0x00D00FBE` | **CONFIRMADO** |
| A camada APP tem sua própria tabela de páginas, 83 entradas em `0x00D0DB1C` | **CONFIRMADO** |
| 12 ids de página estão livres nas duas camadas | **CONFIRMADO** |
| Não existe tela de lista livre com despacho ≥6 por índice | **CONFIRMADO** (varredura das 83 tabelas de salto) |
| O `tbb` de `view_page_create` alcança só 510 bytes | **CONFIRMADO** (codificação T1) |
| Desviar os dois pontos de entrada da página `0x53` contorna o alcance | ✅ **CONFIRMADO** no V020 — o mesmo mecanismo, `bl` para a área livre + `b.w` de volta, funcionou no aparelho |
| Código em `0x1A3038` executa por XIP e está fora do CRC da FIRM | **PROVÁVEL** — o layout confirma, nunca foi executado código de lá |

---

## 8. V020 — o ensaio de execução, antes de escrever a tela

Decisão do mantenedor: fazer o teste de execução **separado** do Extras.
Está certo — se der errado, a causa é uma só.

### 8.1 Por que o teste precisa existir

O V017 provou **leitura** de dado na área livre. A Parte B precisa de
**execução**. São coisas diferentes, e confundir *"está aplicado"* com
*"vai rodar"* já custou o V016 a este projeto.

### 8.2 O achado que mudou o desenho do teste

Eu ia usar a tela inicial como cobaia. Antes, fui ver onde mora o modo
card reader — o caminho de recuperação:

```text
"CARDREADER"  em  0x00046FC7   ->  dentro da FIRM, NAO no bootloader
```

O bootloader (`0x60..0xC94C`) não tem nenhuma string de USB. **Se o teste
travasse durante a montagem da tela inicial, a recuperação ficaria
incerta** — o USB poderia não subir.

> Isso reinterpreta o incidente da Sessão 25: a recuperação funcionou
> com a tabela de partições destruída porque a **FIRM continuou
> rodando** — ela é achada em `0x0000E000` por cabeçalho próprio, não
> pela tabela. A tabela é metadado do atualizador. **PROVÁVEL**, pela
> convergência das duas evidências.

### 8.3 O desenho seguro

A cobaia passou a ser **`page_set_menu_create` (`0x00D3A638`)**, a tela
de Configurações — executada **só quando o usuário entra nela**.

```text
0x001A3048   b.w 0x00D58188        trampolim na área livre
0x0013A640   bl 0x00D58188  ->  bl 0x00DA3048
```

O `b.w` é salto de cauda: `LR` continua apontando para o retorno
original, então a semântica é **idêntica** se a execução funcionar.

| Resultado | O que significa | O que fazer |
|---|---|---|
| Configurar abre normal | **código executa na área livre** ✅ | seguir para o Extras |
| Configurar trava | não executa | desligar e ligar — a tela inicial volta, o USB sobe, o kit reverte 2 setores |

**O caminho de recuperação fica intacto nos dois resultados.** Era isso
que o desenho precisava garantir.

### 8.4 Conferência dupla da codificação

A ferramenta codifica os dois saltos, **decodifica de volta** e compara
os alvos. Depois conferi por fora, com capstone:

```text
0x00D3A640   68f002fd   bl   #0xda3048
0x00DA3048   b5f79eb8   b.w  #0xd58188
```

**8 bytes, 3 setores.** `tools/test_exec_free_area.py`.

---

## 9. ✅ V020 no aparelho — execução na área livre CONFIRMADA

Gravado em 2026-09-13. **A tela Configurar abriu normalmente**, ou seja,
a chamada passou pelo trampolim em `0x00DA3048` e voltou.

```text
0x0013A640   bl 0x00DA3048        (era bl 0x00D58188)
0x00DA3048   b.w 0x00D58188       trampolim na area livre
```

| Afirmação | Antes | Agora |
|---|---|---|
| Dados na área livre são legíveis por XIP | CONFIRMADO (V017) | — |
| **Código na área livre executa por XIP** | PROVÁVEL | ✅ **CONFIRMADO** |
| `bl` da FIRM para a área livre alcança | PROVÁVEL | ✅ **CONFIRMADO** |
| `b.w` da área livre de volta para a FIRM alcança | PROVÁVEL | ✅ **CONFIRMADO** |
| Salto de cauda preserva `LR` através da fronteira | HIPÓTESE | ✅ **CONFIRMADO** |

> **A Parte B deixou de ter incógnita de plataforma.** O que sobra é
> trabalho: escrever Thumb-2 correto. Isso é difícil, mas é difícil de um
> jeito que a gente controla — dá para desmontar de volta e conferir
> instrução por instrução antes de gravar, que é o que as ferramentas
> deste projeto já fazem.
>
> Um teste de 8 bytes respondeu cinco perguntas de uma vez, e o fez num
> lugar onde o pior resultado custaria um ciclo de energia.

### O que o trampolim deve virar

O mecanismo provado é exatamente o que a §4 propunha para a página
`0x53`:

```text
VIEW  0x00D23CF8   bl page_home_menu_create   ->  bl <create na area livre>
APP   0x00D0DF2C   corpo de page83_process    ->  b.w <modulo na area livre>
```

**O trampolim do V020 deve ser revertido** quando o V021 for montado: ele
cumpriu a função e não tem razão para continuar no caminho de
Configurar. Patch que não serve mais é armadilha adormecida — a lição do
V016.

---

## 10. A medição que faltava: o texto "Extras"

Era o último item NÃO DETERMINADO da §2. Resolvido por leitura.

### 10.1 Não existe id livre

A tabela do português tem **216 entradas (ids 0..215)** e emenda **direto**
na do espanhol:

```text
0x00C53B84   pt, 216 ids, 864 bytes
0x00C53EE4   es  <- começa exatamente onde a do pt acaba
```

`get_string` não confere limite — `ldr.w r4, [r3, r4, lsl #2]` —, então
um id 216 em português leria `es[0]` = `"Español"`. **Não há folga para
um id novo.**

### 10.2 Mas a base da tabela é um ponteiro, em dois lugares

```asm
; get_string (0x00D2108C), despacho por idioma via tbb
0x00D210A8   ldr r3, [pc, #0x38]   ; literal de pool -> base da tabela
0x00D210AA   ldr.w r4, [r3, r4, lsl #2]
```

| Onde | O quê |
|---|---|
| `0x00121104` | literal de pool do `get_string`, por idioma |
| `0x00048798` | entrada do **pt** num vetor de bases de tabela em `0x00048780` |

**Realocar a tabela do português custa 2 ponteiros de 4 bytes.**

### 10.3 As duas saídas

| Opção | Custo | O que aparece | Risco |
|---|---|---|---|
| **A — realocar a tabela do pt** para a área livre com 217 ids, o 216 sendo "Extras" | 864 B (cópia) + 7 B (string) + 8 B (2 ponteiros) | **"Extras"** | baixo: só o português muda; o mecanismo (dado na área livre + ponteiro) está provado desde o V017 |
| **B — reaproveitar o id 159**, cujo texto é `'Aplicação'` | **0 bytes** | "Aplicação" | nenhum no firmware, mas a palavra não é a pedida, e renomear o id afetaria onde mais ele for usado |

> **Recomendo a A.** 880 bytes numa área de 364 KiB não é custo, e evita
> a única coisa que eu não consigo garantir na B: onde mais o id 159
> aparece. Duas vezes hoje eu supus "isto provavelmente não é usado" e
> estava errado — o label `view_p[0x18]` e a cauda da string do relógio.
>
> A A também deixa **um id novo disponível** para renomear outros itens
> depois, sem repetir o trabalho.

**Ressalva da A, registrada:** passa a existir uma **cópia** da tabela do
português. Quem editar a original em `0x00C53B84` não verá efeito — a
que vale passa a ser a da área livre. Isso precisa ficar no
`FIRMWARE_MAP.md` quando for feito.

---

## 11. V021 — a fundação: tabela do português realocada

Decisão: **dividir o trabalho.** O V021 faz só a realocação; a
reestruturação do menu e a tela Extras ficam para o V022.

### 11.1 Por que dividir

- a **Parte A sozinha seria pior que hoje**: esconderia seis funções
  atrás de um "Extras" que não abre nada;
- a realocação é **independente das duas partes** e é a fundação delas;
- e tem o melhor tipo de teste que existe neste projeto: **se eu errar,
  todos os textos do menu quebram de uma vez.** Um defeito assim é
  impossível de não ver, e a reversão são 5 setores.

> Comprar a fundação barato, antes de construir em cima, é o mesmo
> raciocínio do V020 — que respondeu cinco perguntas com 8 bytes.

### 11.2 O que o V021 faz

```text
0x0013A640   bl 0x00DA3048 -> bl 0x00D58188   reverte o trampolim do V020
0x001A304C   "Extras\0"                        area livre
0x00DA3054   tabela do pt realocada, 217 ids   868 bytes na area livre
0x00121104   0x00C53B84 -> 0x00DA3054          pool do get_string
0x00048798   0x00C53B84 -> 0x00DA3054          vetor de bases
```

**885 bytes, 5 setores.** `tools/relocate_lang_table.py`.

A tabela original em `0x00C53B84` **continua intacta** — apenas deixa de
ser consultada. Nenhuma string existente foi alterada.

### 11.3 Conferência antes de gravar

A ferramenta relê os 217 ponteiros da tabela nova e compara **string por
string** com a original. Conferido também por fora:

```text
id   1 'Música'   id 3 'Vídeo'    id   5 'Gravação'
id   6 'Rádio'    id 2 'Livro digital'  id 4 'Imagem'
id   9 'Bluetooth'  id 10 'Configurar'  id 8 'Ver pastas'
id 216 'Extras'   <- novo
id   0 'Português'  id 100 'Equalizador'  id 215 'SD card error'
```

### 11.4 ⚠️ Consequência permanente, para não se perder

> **Passa a existir uma cópia da tabela do português.** Quem editar a
> original em `0x00C53B84` daqui em diante **não verá efeito** — a que
> vale é a de `0x00DA3054`.
>
> `tools/patch_menu_text.py` precisa ser apontado para a base nova antes
> de ser usado de novo em português. **Anotado como pendência do V022.**

### 11.5 O que o V022 ainda precisa

| Peça | Classe |
|---|---|
| Home com 4 itens: ids, tabela de saltos, limites, coordenadas, folha | dado |
| Bloco que abre a página `0x53` a partir do índice 2 | ~4 bytes de código, em bloco morto de `page1_process` |
| Tela Extras: 6 itens | **código novo em Thumb-2** |
| Despacho dos 6 destinos | **código novo em Thumb-2** |

---

## 12. V022 — o projeto completo, e por que encolheu

### 12.1 Correção de leitura: `0xd0e2f0` não abre página

Eu tinha lido os blocos de `page1_process` como *"carrega o id da página e
abre"*. **Errado.** `0xd0e2f0(param, str)` faz `strncpy` do segundo
argumento para `+0x14` de uma mensagem: é **caixa de texto**, não
navegação. Os `movs r0,#0x31` dos blocos são **id de string**.

Isso invalida a frase da §3 *"carrega o id da página (`0x31`, `0x33`…)"* —
aqueles números são ids de texto de erro ("Nenhum ficheiro de ebook
detectado", etc.).

> Terceira correção de enquadramento neste documento. Todas vieram de ler
> a função em vez de inferir pelo nome ou pelo contexto.

### 12.2 Quem abre página, de fato

```asm
; bloco do Configurar em page1_process
0x00D0123A   movs r3, #0x28      ; pagina DESTINO (0x28 = page_set_menu)
0x00D0123C   movs r2, #7         ; ctrl_id do item
0x00D0123E   movs r1, #2         ; ctrl_grp
0x00D01240   b    #0xd011f2      ; -> pop ; b.w 0xd0dae0
```

`0xd0dae0(pagina_atual, ctrl_grp, ctrl_id, pagina_destino)` é a transição
de página da camada APP: ela indexa a **tabela de 83 entradas** em
`0x00D0DB1C` pelo **destino** e entra no módulo daquela página.

**CONFIRMADO:** `add.w r3, r7, #-1` / `cmp r3, #0x52` / `tbh` — com
`r7 = 4º argumento`.

### 12.3 Parte A — home com 4 itens

| # | Onde | Hoje | Vira | B |
|---|---|---|---|---|
| 1 | `0x000486C4` | ids `[1,3,5,6,…]` | `[1, 4, 216, 10]` | 16 |
| 2 | `0x00D00FC0` (tbh idx1) | `0x0054` (vídeo) | `0x00F8` (Imagem) | 2 |
| 3 | `0x00D00FC2` (tbh idx2) | `0x009C` (Gravação) | `0x018F` (bloco morto) | 2 |
| 4 | `0x00D00FC4` (tbh idx3) | `0x00BF` (Rádio) | `0x013E` (Configurar) | 2 |
| 5 | `0x0012_12DC` | `movs r3,#0x1e` | `movs r3,#0x53` | 1 |
| 6 | `0x0012_12DE` | `movs r2,#0xb` | `movs r2,#2` | 1 |
| 7 | `0x0012_ED88` | `cmp r5,#0x24` | `#0x10` | 1 |
| 8 | `page_home_event_cb` | limites `8` e voltas | `3` | ~6 |
| 9 | `0x0004867C` / `0x000486A0` | 9 pares | 4 pares | dado |
| 10 | folha `0x000CE15C` | 9 chevrons | 4 chevrons | imagem |

**O bloco do Extras custa 2 bytes**, não código novo: o bloco em
`0x00D012DC` serve hoje ao índice 11, que fica morto quando a home passa
a ter 4 itens, e tem exatamente a forma certa
(`movs r3,#dest ; movs r2,#id ; b 0xd0123e`). Verificado: só o índice 11
aponta para ele.

### 12.4 Parte B — a tela Extras, sem escrever uma tela

**`page_home_menu_create` já É uma tela de lista.** Basta estendê-la de 3
para 6 itens — e o despacho, que era o bloqueio da §15.3, some: a
mensagem chega ao **`btn_process` do view**, que abre
`vmsgp->page` direto. Não é preciso módulo novo na camada APP.

Estrutura para 6 itens, pelo esquema confirmado em `page_set_menu`
(`rótulos = N·4`, `ícones = 2·N·4`):

```text
botoes 0x00   rotulos 0x18   icones 0x30   indice 0x48   malloc 0x4C
```

Os **16 pontos**, com os bytes conferidos no V021:

```text
0x0012F0A4  2820  movs r0,#0x28      -> 0x4C     malloc
0x0012F0C2  2822  movs r2,#0x28      -> 0x4C     memset
0x0012F246  022e  cmp r6,#2          -> #5
0x0012F2B6  03ab  add r3,sp,#0xc     -> ldr r3,[pc,#0x6c]
0x0012F2DA  032e  cmp r6,#3          -> #6       contagem
0x0012F2DC  c8f80c90  str.w sb,[r8,#0xc]   -> #0x18
0x0012F2E0  c8f818a0  str.w sl,[r8,#0x18]  -> #0x30
0x0012F2FA  d868  ldr r0,[r3,#0xc]   -> #0x18
0x0012F302  87f82630  strb.w r3,[r7,#0x26] -> #0x48
0x0012F324  e886c400  pool da tabela de ids -> tabela de 6 na area livre
0x0012F3E2  022b  cmp r3,#2          -> #5
0x0012F406  022b  cmp r3,#2          -> #5
0x0012F40E  e868  ldr r0,[r5,#0xc]   -> #0x18
0x0012F414  ad69  ldr r5,[r5,#0x18]  -> #0x30
0x0012F486  db68  ldr r3,[r3,#0xc]   -> #0x18
0x0012EFF6  20 B  cadeia de 3 comparacoes -> laco de 6
```

Mais: tabela de 6 ids na área livre, e os 6 destinos — que vêm do
`btn_process` lendo `vmsgp->page`, ou seja, de quem envia. **Ponto ainda
em aberto: quem envia a mensagem type=2 para a página `0x53` com o
destino.** É o último detalhe a resolver antes de montar.

### 12.5 O risco que continua

`malloc` e aritmética de ponteiro. É o que a `MENU_LISTA.md` §14 avisou:
**corrupção de heap não aparece na verificação byte a byte.** Vale a
regra de lá — montar inteiro, validar cada ponto por disassembly, e ter o
kit de reversão na máquina antes de gravar.

O que mudou a favor: o esquema `N·4 / 2·N·4` está **confirmado** contra
uma tela real de 10 itens, e os 16 pontos estão enumerados com os bytes
atuais lidos do binário, não de memória.

---

## 13. A última peça, fechada — e ela mudou o desenho

### 13.1 O que eu descobri ao abrir os blocos

Eu ia extrair o **id da página destino** de cada item e pôr numa tabela.
Abri o bloco do "vídeo" (`0x00D01066`) inteiro. Ele **não abre uma
página**:

```asm
bl #0xcfe714        ; cartao presente?
bl #0xd45cac        ; volume montado?
bl #0xd3ec44        ; lista de video suja?
...
movs r0, #0x9a
bl #0xd2108c        ; get_string("Digitalizar o ficheiro...")
bl #0xd0e2f0        ; mostra a mensagem
ldr  r1, =0x00D00E85
bl #0xd3eda8        ; registra CALLBACK de fim de varredura
bl #0xd3ead8        ; dispara a varredura
b.w #0xd0e8ec
```

Só **4 dos 9 itens** (Bluetooth, Configurar e mais dois) abrem por
`movs r3,#destino`. Os outros cinco fazem verificação de cartão, de
volume, de índice sujo, mostram mensagem de erro e às vezes disparam uma
**varredura assíncrona** antes de abrir qualquer coisa.

> **Uma tabela de destinos teria jogado tudo isso fora.** Escolher
> "Vídeo" sem cartão abriria uma tela vazia em vez de dizer "Não foram
> detectados ficheiros de vídeo". Eu teria descoberto isso no aparelho,
> depois de gravar.

### 13.2 A saída: não duplicar a lógica — reusá-la inteira

O Extras não precisa de despacho próprio. Precisa que o Enter dele
**chegue a `page1_process` como se viesse da home**:

```text
Extras, item i  ->  view_send(page=1, grp=2, ctrl_id=home_idx[i], evt=4)
```

Aí roda o bloco original do item, com todas as verificações.

**O único obstáculo** é a guarda de página no topo de `page1_process`:

```asm
0x00D00F4C   ldrh r2, [r4, #8]     ; msg->page
0x00D00F4E   ldrb r0, [r3, #0xa]   ; pagina corrente
0x00D00F50   cmp  r2, r0           ; -> "curr page error !!!"
```

Com o Extras na tela, a página corrente é `0x53` e a mensagem diz 1.
Relaxar a guarda para `cmp r2, #1` — aceitar sempre mensagens
endereçadas à página 1 — são **2 bytes**, e é exatamente a Rota C da §17.

### 13.3 O mapa Extras → home

| Extras | item | índice na home |
|---|---|---|
| 0 | Vídeo | 1 |
| 1 | Gravação | 2 |
| 2 | Rádio | 3 |
| 3 | Livro digital | 4 |
| 4 | Bluetooth | 6 |
| 5 | Ver pastas | 8 |

Tabela de 6 bytes na área livre. O `event_cb` do Extras troca
`movs r0,#0x53` → `#1`, `r1` 4 → 2, e passa `mapa[i]` em vez de `i`.
Cabe: o laço de 6 (§11) libera os 8 bytes do código morto em
`0x00D2F01C`.

### 13.4 Ressalvas novas, registradas antes de montar

1. **A guarda relaxada aceita mensagens de página 1 vindas de qualquer
   tela.** Hoje só a home e o Extras as enviam. Se outra tela passar a
   enviar, o comportamento muda. **Classe: PROVÁVEL que seja inócuo** —
   não verifiquei todos os emissores.
2. **A camada view continuará entregando a mensagem à página 1**, cujo
   `page_p` estará NULL com o Extras na tela: log `-%s page_p NULL` e
   retorno. Inócuo, mas polui o log de depuração.
3. **A varredura assíncrona do "vídeo" registra um callback
   (`0x00D00E85`) que reabre a tela ao terminar.** Com o Extras na tela,
   é preciso confirmar para onde ele volta. **NÃO DETERMINADO** — é o
   próximo item a ler, e pode exigir mais um ajuste.

### 13.5 Onde o V022 está

| Peça | Estado |
|---|---|
| Parte A — home com 4 itens | **projetada**, 10 pontos, bytes conferidos |
| Parte B — Extras com 6 itens | **projetada**, 16 pontos, bytes conferidos |
| Roteamento do Enter via `page1_process` | **projetado**, 2 + ~8 bytes |
| Callback da varredura assíncrona | **NÃO DETERMINADO** |

Montar antes de fechar o item 3 seria repetir o erro do V016: ter o
patch certo sobre uma premissa não verificada.

---

## 14. ✅ O callback da varredura, lido — e não é problema

`page1_video_build_cb` (`0x00D00E84`), registrado pelo bloco do "vídeo"
antes de disparar a varredura:

```asm
bl   #0xd0d278        ; quantos videos foram encontrados
subs r4, r0, #0
ble  #0xd00ebe        ; nenhum -> mostra "Nao foram detectados..."
movs r3, #0x13        ; DESTINO = pagina 0x13
movs r2, #3           ; ctrl_id
movs r1, #2           ; ctrl_grp
movs r0, #1           ; pagina de ORIGEM
pop  {r4, lr}
b.w  #0xd0dae0
```

Página `0x13` (19) → `page_video_list_create`. **O callback abre a lista
de vídeos direto. Ele NÃO reabre a tela inicial.**

| Receio | Verificado |
|---|---|
| o callback reabre a home e joga o usuário para fora do Extras | ❌ **não** — abre a página `0x13` |
| guarda um ponteiro de tela que não existe mais | ❌ **não** — usa ids de página, não ponteiros |
| o `movs r0,#1` (origem) quebra alguma coisa | não: `0xd0dae0` usa a origem só em comparações de caso especial e a repassa; o despacho é pelo **destino** |

**A peça está fechada: o V022 não precisa de ajuste por causa disso.**

### 14.1 Mas apareceu uma consequência de comportamento

`0xd0dae0` recebe a **página de origem** e a repassa ao módulo da página
destino. Com o roteamento do Extras, essa origem será sempre **1**, não
`0x53`.

> **Consequência provável: "voltar" da lista de vídeos devolve à tela
> inicial, não ao Extras.** Classe: **PROVÁVEL** — não rastreei como a
> volta é decidida; pode haver uma pilha de páginas em outro lugar.
>
> Não é travamento nem perda de função: é navegação que pode ficar
> estranha. **É observável no aparelho** e, se incomodar, vira um ajuste
> próprio depois — não um bloqueio agora.

Registrado para ser **olhado no teste do V022**, não descoberto por
acidente depois.

---

## 15. V022 — montado

**30 pontos com guarda individual + código novo na área livre.**
Ferramenta: `tools/make_extras_menu.py`. 217 bytes, 10 setores.

### 15.1 O que ficou onde

```text
HOME (pagina 1), 4 itens          Musica · Imagem · Extras · Configurar
  0x000486C4  ids [1, 4, 216, 10]
  0x00100FC0  tbh idx1 -> bloco da Imagem
  0x00100FC2  tbh idx2 -> bloco do Extras
  0x00100FC4  tbh idx3 -> bloco do Configurar
  0x001012DC  bloco morto do idx11 vira: movs r3,#0x53 ; movs r2,#2
  0x0012ED88  limite do laco 0x24 -> 0x10
  7 bytes de limite e volta de indice no event_cb

EXTRAS (pagina 0x53), 6 itens     Video · Gravacao · Radio · Livro ·
                                  Bluetooth · Ver pastas
  malloc 0x28 -> 0x4C ; rotulos 0x0C -> 0x18 ; icones 0x18 -> 0x30 ;
  indice 0x26 -> 0x48 ; limites 2 -> 5 ; contagem 3 -> 6
  0x0012F324  pool da tabela de ids -> 0x00DA33B8
  0x0012EFF6  cadeia de 3 comparacoes -> laco de 6 (20 B)

ROTEAMENTO
  0x00100F4E  ldrb r0,[r3,#0xa] -> cmp r2,#1   guarda de pagina relaxada
  0x00100F50  cmp r2,r0         -> nop
  0x0012F00A  convergencia      -> b.w 0x00DA33D8

AREA LIVRE
  0x001A33B8  tabela de ids do Extras   [3, 5, 6, 2, 9, 8]
  0x001A33D0  mapa Extras -> home       [1, 2, 3, 4, 6, 8]
  0x001A33D8  rotina do Enter, 28 B
```

### 15.2 A rotina nova, conferida por disassembly

```asm
00DA33D8   044a       ldr  r2, [pc, #16]   ; -> 0x00DA33D0 (MAPA)
00DA33DA   125d       ldrb r2, [r2, r4]    ; r2 = MAPA[indice]
00DA33DC   0423       movs r3, #4          ; evento
00DA33DE   0221       movs r1, #2          ; ctrl_grp da HOME
00DA33E0   0120       movs r0, #1          ; pagina = 1  (a home)
00DA33E2   80f795f8   bl   #0xd23510       ; view_send
00DA33E6   024b       ldr  r3, [pc, #8]    ; -> 0x00823D84
00DA33E8   1c70       strb r4, [r3]        ; guarda o indice selecionado
00DA33EA   70bd       pop  {r4, r5, r6, pc}
00DA33EC   .word 0x00DA33D0
00DA33F0   .word 0x00823D84
```

A ferramenta **decodifica os dois `ldr` literais que ela mesma gera** e
confere que apontam para as palavras certas, com os valores certos.
Conferido de novo por fora, com capstone.

### 15.3 O que observar no aparelho, em ordem

1. **a home mostra 4 itens** — Música, Imagem, Extras, Configurar;
2. **Música, Imagem e Configurar abrem o que sempre abriram** — se algum
   abrir a tela errada, a tabela de saltos está trocada;
3. **Extras abre uma lista de 6** com realce de linha (a lista usa botões
   de largura total, diferente da home);
4. **cada item do Extras abre a tela certa** — é o roteamento;
5. **sair do Extras** com a tecla de "voltar" (uma das M/VOL);
6. ⚠️ **"voltar" da lista de vídeos**: provavelmente devolve à tela
   inicial, não ao Extras (§14.1). Comportamento, não defeito.

### 15.4 O risco, dito sem rodeio

Este é o primeiro patch do projeto que mexe em **`malloc` e aritmética de
ponteiro**. Um offset errado corrompe a heap, e **corrupção de heap não
aparece na verificação byte a byte pós-gravação** — o sintoma seria
travamento aleatório, minutos depois, em outra parte do sistema.

O que temos a favor:

- o esquema `N·4 / 2·N·4` está **confirmado** contra `page_set_menu`, uma
  tela real de 10 itens;
- os 30 pontos têm **guarda individual** e a ferramenta recusa tudo se um
  só divergir — e ela de fato recusou duas vezes durante a montagem, por
  erro meu de ordem e de cálculo de literal;
- o código novo foi **desmontado de volta** e conferido instrução por
  instrução;
- a reversão são 10 setores, com o kit já gerado.

**Se o aparelho travar de forma aleatória depois de um tempo de uso —
mesmo que tudo pareça certo na tela — reverta.** Esse é o sintoma que
estamos vigiando, e ele não aparece na hora.

---

## 16. ⚠️ V022 no aparelho: a home ficou certa, mas NENHUM item abre

Gravado em 2026-09-13. A tela está exatamente como projetada — 4 itens,
"Extras" no lugar certo, faixa e seleção corretas. **Mas o Enter não
abre nada, em nenhum item, incluindo Música.**

### 16.1 O que eu já descartei, por leitura

| Suspeita | Verificação |
|---|---|
| algum byte saiu errado | ❌ o disassembly do V022 confere com o projetado, ponto a ponto |
| a guarda relaxada perdeu as flags | ❌ `cmp r2,#1` / `nop` / `mov r6,r3` (T1, não afeta flags) / `beq` — a sequência está correta |
| o limite do Enter (`cmp r2,#3`) corta | ❌ a seleção visível é o item 0; o índice está na faixa |
| a tabela de saltos está trocada | ❌ e **Música é o índice 0, que eu não toquei** |

**É esse último ponto que manda:** a falha atinge um caminho que eu
**não** alterei. Logo, a causa é algo compartilhado — e é uma premissa
minha, não um byte errado.

### 16.2 O que eu ainda não sei

Nunca tracei **quem entrega a mensagem de evento da view ao módulo da
camada APP**. Encontrei três chamadores de `page1_process`
(`0x00D0ED5E`, `0x00D0F0B0`, `0x00D0F8F4`), e não sei qual serve este
caminho nem que condições ele impõe.

> Essa lacuna estava aberta desde a §13 e eu segui assim mesmo, porque o
> roteamento "parecia" resolvido. **Era exatamente o tipo de premissa não
> verificada que já custou o V016 — e desta vez custou um patch de 30
> pontos.**

### 16.3 O que NÃO vou fazer

Chutar outra gravação. O patch está correto contra o projeto; o projeto é
que tem um furo. Gravar de novo sem saber qual gasta o tempo do
mantenedor e não produz informação.

### 16.4 Bissecção — V023

`V023 = V021 + SOMENTE a Parte A`: home com 4 itens, tabela de saltos,
bloco do Extras, limites e folha. **Sem** a guarda relaxada e **sem**
qualquer mudança na página `0x53`.

| Resultado | Conclusão |
|---|---|
| **os 4 itens abrem** | a Parte A está boa; a causa está na guarda relaxada ou em algo da Parte B que afeta código compartilhado |
| **continua sem abrir** | a causa está nos 13 pontos da Parte A — e são poucos o bastante para conferir um a um |

Uma gravação, e o espaço de busca cai pela metade.

Também foi gerado `OpenPod_Volta_v021/`, que devolve direto ao V021 —
o último estado que funcionava.

---

## 17. ✅ A lacuna da §16.2, fechada — e ela derruba o roteamento do V022

Quem entrega a mensagem de evento da view ao módulo da camada APP:

```text
_watch_presenter_work_process
   ldrb r2, [r0, #2]        ; cmd
   subs r3, r2, #1
   cmp  r3, #0xF
   tbh  [pc, r3, lsl #1]    ; cmd 6 -> 0x00D0EEF0
      ↓
0x00D0EEF0   casos especiais (ctrl_grp 0xE, pagina 0x3D)
0x00D0EF54   ldrb  r1, [r5, #0xa]      ; <<< PAGINA CORRENTE
0x00D0EF56   subs  r3, r1, #1
0x00D0EF58   cmp   r3, #0x52
0x00D0EF60   ldr.w pc, [r2, r3, lsl #2]  ; tabela de 83 enderecos
```

### 17.1 O despacho é pela PÁGINA CORRENTE, não pela página da mensagem

**CONFIRMADO** por disassembly. A consequência é direta:

> Com o Extras na tela, a página corrente é `0x53`. Uma mensagem dizendo
> `page = 1` **não** chega a `page1_process` — ela chega ao módulo da
> página `0x53`, que é quem o despachante escolhe.
>
> **O roteamento do V022 não podia funcionar.** Relaxar a guarda de
> `page1_process` foi inútil: aquela função nunca é alcançada a partir do
> Extras.

`page1_process` verifica `msg->page == pagina corrente` como **sanidade**,
não como roteamento. Eu li a guarda e inferi o roteamento a partir dela.
**A guarda não é o despachante** — e eu tratei uma como a outra.

### 17.2 O que isto ainda NÃO explica

**Por que a home parou de abrir.** Para a home, página corrente = 1 e
`msg->page` = 1: o despacho chega a `page1_process` e a guarda passa nas
duas formas, original ou relaxada. Pelo que li, a Parte A deveria
funcionar.

**Portanto continuo sem a causa da falha observada.** O V023 (só a Parte
A) responde: se os 4 itens abrirem, a Parte A está boa e a falha vinha da
Parte B; se não abrirem, está nos 13 pontos da Parte A.

### 17.3 Como o Extras tem de ser feito, agora que se sabe o despacho

O módulo da página `0x53` **precisa existir e fazer o trabalho** — não dá
para desviar a mensagem para o módulo da home. As opções reais:

| Opção | O que é | Custo |
|---|---|---|
| **A** — módulo próprio na área livre para a página `0x53`, que chama `0xd0dae0(0x53, grp, id, destino)` com uma tabela de 6 destinos | perde as verificações de cartão/volume e as mensagens de erro de cada item | pequeno |
| **B** — módulo próprio que **replica a chamada de `page1_process`** passando a página corrente como 1 | exigiria escrever na RAM a página corrente antes de chamar — mexe em estado global do sistema | médio, e arriscado |
| **C** — módulo próprio que faz a verificação certa por item, copiando a lógica de cada bloco | mantém tudo, mas é o maior volume de Thumb-2 do projeto | alto |

> **Recomendação: A**, aceitando a perda das pré-verificações, e medindo
> depois se elas fazem falta de verdade. É o caminho mais curto para algo
> funcionando, e as pré-verificações podem voltar item a item.
>
> Mas nada disso antes do resultado do V023.

### 17.4 A lição, sem rodeio

Eu segui com a §13 marcando o despacho como "projetado" quando o que eu
tinha era **uma guarda lida e uma inferência**. A diferença entre as duas
coisas é exatamente o que este documento vem repetindo desde o V016 — e
desta vez eu escrevi a advertência na §16.2 **depois** de ter cometido o
erro, não antes.

---

## 18. V023 também falhou — a bissecção continua

**V023 = V021 + só a Parte A. Continua sem abrir nenhum item.**

### 18.1 O que isso elimina

| Eliminado | Por quê |
|---|---|
| toda a Parte B (página `0x53`, 16 pontos) | não está no V023 |
| a guarda relaxada de `page1_process` | não está no V023 |
| a rotina nova na área livre | não está no V023 |
| o `b.w` da convergência | não está no V023 |

**A causa está nos 13 pontos da Parte A.** E como **Música é o índice 0,
cuja entrada na tabela de saltos eu não toquei**, ela também não pode
ser a tabela de saltos nem o bloco do Extras.

Sobram quatro grupos:

1. os **7 bytes de limite de índice** no `event_cb` — os únicos que ficam
   no caminho do Enter;
2. o **limite do laço de criação** (`cmp r5,#0x24` → `#0x10`);
3. a **tabela de ids** (`[1, 4, 216, 10]`);
4. **coordenadas e folha**.

### 18.2 V024 — isolar o grupo 1, com segurança

`V024 = V021 + SOMENTE os 7 bytes de limite.` A home volta a mostrar
**9 itens com os rótulos originais**; só o índice passa a ser limitado a
0..3.

É seguro: 3 < 9 itens criados, então nenhum acesso sai da estrutura.

| Resultado | Conclusão |
|---|---|
| **os 4 primeiros itens abrem** (Música, vídeo, Gravação, Rádio) | os limites são inocentes → a causa está nos grupos 2, 3 ou 4 |
| **continua sem abrir** | **os limites são a causa** — e são 7 bytes, dá para ler um a um |

9 bytes alterados, 2 setores. É a menor mudança possível que ainda
separa as hipóteses.

### 18.3 Nota de método

Eu poderia ter testado dois grupos de uma vez, mas isso exigiria deixar o
índice ir até 8 com só 4 itens criados — e aí `labels[idx]` sairia da
faixa preenchida, lendo NULL da estrutura zerada. **Um teste que pode
travar por um motivo diferente do que se quer medir não mede nada.**
Preferi um grupo por vez.

---

## 19. ✅ V024 funciona — e revela um erro real no V022

**V024 (só os 7 bytes de limite) abre os 4 primeiros itens.** Os limites
são inocentes.

### 19.1 O erro que o V022 tinha, e eu não tinha visto

```asm
0x00D00F4E   ldrb r0, [r3, #0xa]    ; r0 = PAGINA CORRENTE
0x00D00F50   cmp  r2, r0
```

Eu li essas duas instruções como **só uma guarda** e troquei a primeira
por `cmp r2,#1`. Mas `ldrb r0,[r3,#0xa]` **também carrega r0**, e os
blocos que chamam `0xd0dae0` contam com isso:

```asm
; bloco do Configurar
0x00D0123A   movs r3, #0x28     ; destino
0x00D0123C   movs r2, #7        ; ctrl_id
0x00D0123E   movs r1, #2        ; ctrl_grp
0x00D01240   b    #0xd011f2     ; -> pop ; b.w 0xd0dae0
```

**Nenhum deles carrega r0.** O 1º argumento de `0xd0dae0` — a página de
origem — vem daquele `ldrb` lá do começo da função, 0x2EC bytes antes.

> Ao apagar o `ldrb`, o V022 passou lixo como página de origem para todo
> bloco que não recarrega r0 — incluindo **Configurar** e o bloco novo do
> **Extras**. E `0xd0dae0` começa com `cmp r0, r3` ("same page"): com
> lixo em r0, o resultado é imprevisível.

**Classificação: CONFIRMADO por leitura.** É um erro real, e é meu — eu
tratei uma instrução com dois efeitos como se tivesse um só.

### 19.2 Mas isso NÃO explica o V023

O V023 **não** tem a guarda relaxada: o `ldrb r0` está intacto. E mesmo
assim nenhum item abriu.

**Nota importante sobre o bloco de cada item:**

| Item | Bloco | Recarrega r0? |
|---|---|---|
| Música (idx 0) | `0x00D00FD6` | **sim** — `bl 0xcfe714` |
| Imagem | `0x00D011AE` | **sim** — `bl 0xcfe714` |
| Configurar | `0x00D0123A` | **não** — depende do `ldrb` |
| Extras (novo) | `0x00D012DC` | **não** — depende do `ldrb` |

Ou seja: no V023, **Música deveria abrir**.

### 19.3 A pergunta que pode fechar isso sem gravar nada

> No V023, apertando **Música** logo ao ligar, sem mexer em mais nada:
> ela abre?

Se abrir, o padrão fica claro: os itens que dependem de r0 quebram, os
que recarregam funcionam — e a primeira tentativa do mantenedor pode ter
travado a interface, fazendo parecer que nada respondia.

Se **não** abrir, a causa está mesmo nos grupos 2, 3 ou 4 (limite do
laço, tabela de ids, coordenadas), e o próximo passo é `V025 = V024 +
limite do laço`.

---

## 20. A causa, por eliminação — e o contorno

**V023 (Parte A inteira): Música não abre. V024 (só os limites): abre.**

### 20.1 Eliminação

| Grupo | Veredito |
|---|---|
| 1 — os 7 bytes de limite de índice | ✅ **inocente** — o V024 prova |
| 4 — coordenadas e folha | ✅ **inocente** — as coordenadas dos 4 primeiros no V023 são **idênticas** às do V021, que funciona |
| 3 — tabela de ids | ✅ **inocente** — só muda valores, e o texto renderiza certo ("Extras" aparece na tela) |
| 2 — **limite do laço de criação** | ⬅️ **a única mudança estrutural que sobra** |

`cmp r5,#0x24` → `#0x10` faz o `page_home_create` construir **4 objetos
em vez de 9**. É a única alteração do V023 que muda **estrutura**, não
valores — e é exatamente a classe de mudança que quebra coisas.

**Não consegui achar o mecanismo por leitura.** O que vem depois do laço
(`0xd56000`, `0xd476b0`, `str [r8,#0x48]`) usa o índice 0 e não parece
depender da contagem. Fica **PROVÁVEL por eliminação**, não CONFIRMADO
por mecanismo — e está registrado assim de propósito.

### 20.2 O contorno: não brigar com a causa, removê-la

Em vez de descobrir por que 4 objetos quebram, **continuo criando os 9** e
mando os 5 que sobram para **fora da tela** (`y = 200`, numa tela de
160 px). O índice já está limitado a 0..3 pelo V024, então eles nunca são
alcançados.

```text
0x0012ED88   limite do laco   NAO ALTERADO   (9 objetos, como sempre)
0x000486A0   rotulos  y = 19, 35, 50, 66,  200 x5
0x0004867C   chevrons y = 19, 35, 50, 66,  200 x5
0x000486C4   ids [1, 4, 216, 10] + os 5 antigos
```

> **É o mesmo raciocínio do V001→V002 com o `write_flash`:** a correção
> forte não é a que acerta o comportamento desconhecido, é a que **torna
> o desconhecido irrelevante.** Se 4 objetos quebram algo que eu não
> entendi, a resposta é continuar criando 9.

**V025 = V024 + Parte A sem o limite do laço.** 112 bytes, 7 setores.

### 20.3 O que o resultado dirá

| Resultado | Conclusão |
|---|---|
| os 4 itens aparecem e **todos abrem** | a Parte A está resolvida; o limite do laço era mesmo a causa, e o contorno serve |
| aparecem e **Música abre, os outros não** | a tabela de saltos está errada — são 3 halfwords, dá para conferir um a um |
| **nada abre** | minha eliminação tem um furo, e volto a ler em vez de gravar |

---

## 21. ✅ V025 funciona — Parte A resolvida

**Os 4 itens aparecem e todos abrem.** Música, Imagem e Configurar vão
para as telas certas; "Extras" abre a página `0x53` — a lista antiga de
3 itens (Despertador, Imagens, Dicionário), que é o conteúdo original
dela. Esperado: a Parte B foi descartada no V023.

**Confirma a hipótese da §20:** o limite do laço de criação era a causa,
e criar os 9 objetos escondendo 5 fora da tela contorna sem precisar
entender o mecanismo.

### 21.1 O erro que eu cometi no V022, agora inteiramente explicado

Eu tinha trocado **duas** instruções:

```asm
0x00D00F4E   ldrb r0, [r3, #0xa]   ->  cmp r2, #1     ❌
0x00D00F50   cmp  r2, r0           ->  nop            ❌
```

O certo, se o relaxamento fosse necessário, seria trocar **só a segunda**:

```asm
0x00D00F4E   ldrb r0, [r3, #0xa]   ->  (intacta: carrega r0)
0x00D00F50   cmp  r2, r0           ->  cmp r2, #1
```

Eu apaguei a instrução errada das duas. **Mas o melhor é não relaxar
nada** — ver §21.2.

---

## 22. A Parte B, redesenhada com o despacho correto

### 22.1 A chave

O despacho da camada APP é pela **página corrente** (§17). Com o Extras na
tela, a corrente é `0x53`, então a mensagem vai para o módulo da página
`0x53`. Não adianta endereçá-la à página 1.

**Mas o módulo da página `0x53` pode simplesmente repassar para
`page1_process`, com o índice remapeado:**

```asm
extras_module:                    ; r0 = mensagem
    ldrh r3, [r0, #0xc]           ; ctrl_id do Extras (0..5)
    ldr  r2, =MAPA                ; [1, 2, 3, 4, 6, 8]
    ldrb r3, [r2, r3]
    strh r3, [r0, #0xc]           ; ctrl_id vira o indice da HOME
    b.w  #0xd00f3c                ; page1_process
```

E o `event_cb` do Extras envia `page = 0x53` — **a página corrente**.
Então, dentro de `page1_process`:

```asm
ldrh r2, [r4, #8]      ; msg->page   = 0x53
ldrb r0, [r3, #0xa]    ; corrente    = 0x53
cmp  r2, r0            ; PASSA, sem patch nenhum
```

> **Nenhuma guarda precisa ser relaxada.** E `r0` fica valendo `0x53`, que
> é a página de origem **correta** para os blocos que chamam `0xd0dae0`
> sem recarregar r0.
>
> A solução certa deixou de precisar do patch que eu errei. Era o patch
> que estava errado **e** desnecessário.

### 22.2 O que sobra de trabalho

| Peça | Classe | Risco |
|---|---|---|
| módulo remapeador na área livre (~6 instruções) | código novo | baixo — desvia `bl 0xd0cdb0` em `0x0010DF30` |
| `event_cb` do Extras: enviar `page=0x53, grp=2` | 2 bytes | baixo |
| tela `0x53` de 3 para 6 itens | **estrutural** — `malloc` e offsets | **alto** |

### 22.3 A lição do V023 aplicada ao que falta

O único ponto de risco é o mesmo tipo que acabou de nos custar três
gravações: **mudar a contagem de itens de uma tela**. No `page_home_create`
isso quebrou por um motivo que nunca identifiquei.

> **Portanto: a extensão da página `0x53` de 3 para 6 itens deve ser
> gravada e testada SOZINHA**, antes de qualquer roteamento. Se quebrar,
> quebra isolada e sabemos na hora.
>
> E se quebrar do mesmo jeito misterioso, o contorno é o mesmo: **não
> mexer na contagem** — e aí o Extras fica com 3 itens, ou muda de
> hospedeiro.

---

## 23. V026 — só a extensão da página `0x53`, isolada

A foto do V025 confirmou: "Extras" abre a página `0x53` com
**Despertador, Imagem, Dicionário** — e com a **barra de seleção azul de
largura total**, o realce do nano que a home não tem.

> Vale registrar: o widget que o Design System pedia desde o começo
> **existe nativo nessa tela**. A home usa labels soltos e só muda a cor
> do texto; a lista usa botões de largura total com estado de realce.
> Quando o Extras estiver pronto, ele será visualmente mais fiel ao nano
> do que a própria home.

### 23.1 O que o V026 faz, e só

**16 pontos**, todos na página `0x53`, mais uma tabela de 6 ids na área
livre. **Nenhum roteamento.** O despacho da página continua o original.

```text
malloc/memset 0x28 -> 0x4C     contagem 3 -> 6
rotulos 0x0C -> 0x18           icones  0x18 -> 0x30
indice  0x26 -> 0x48           limites 2 -> 5
cadeia de 3 comparacoes -> laco de 6
pool da tabela de ids -> 0x00DA33B8  [3, 5, 6, 2, 9, 8]
```

67 bytes, 4 setores.

### 23.2 Por que sozinho

É **exatamente a classe de mudança que custou três gravações**: mexer na
contagem de itens de uma tela. No `page_home_create` isso quebrou por um
motivo que nunca identifiquei, e eu só descobri porque bissectei.

> **Desta vez a mudança estrutural vai sozinha.** Se quebrar, quebra
> isolada e sabemos na hora — sem ter cinco variáveis em jogo.

### 23.3 O que observar

1. a home continua com 4 itens, todos abrindo (nada da Parte A mudou);
2. **"Extras" mostra 6 linhas**: Vídeo, Gravação, Rádio, Livro digital,
   Bluetooth, Ver pastas — com a barra azul;
3. a seleção anda pelas 6 e volta nas pontas;
4. **os itens ainda NÃO abrem nada** — o despacho é o original, que só
   trata o índice 0. Isso é esperado, não é defeito;
5. **use o aparelho um tempo depois.** Se travar de forma aleatória, é o
   sintoma de heap, e aí a extensão de 3 para 6 é a culpada.

Se esta versão for estável, o que falta é só o roteamento da §22 — que
não mexe em estrutura nenhuma.

---

## 24. V029 — o roteamento, e o desenho que dispensou o patch errado

### 24.1 O achado que fechou tudo

Existem **duas** tabelas de 83 entradas na camada APP, e eu tinha
confundido as duas:

| Tabela | Tipo | Indexada por | Para quê |
|---|---|---|---|
| `0x00D0DB1C` | `tbh` (offsets) | página **destino** | transição: criar a página |
| `0x00D0EF64` | **endereços absolutos** | página **corrente** | evento: tratar a tecla |

```asm
0x00D0EF54   ldrb  r1, [r5, #0xa]        ; PAGINA CORRENTE
0x00D0EF60   ldr.w pc, [r2, r3, lsl #2]  ; enderecos ABSOLUTOS
```

**A segunda usa endereços absolutos** — dá para apontar direto para a
área livre, sem limite de alcance. E a entrada da página `0x53` apontava
para o **caminho de erro** (`"-%s no pstrp->curr_page"`): a página nunca
teve tratador de eventos. Era essa a causa de os itens não abrirem.

### 24.2 O módulo

```asm
00DA3400   ldrh r3, [r0, #0xa]    ; ctrl_grp
00DA3402   cmp  r3, #2            ; so o Enter da nossa lista
00DA3404   bne  fora
00DA3406   ldrh r3, [r0, #0xc]    ; ctrl_id do Extras (0..5)
00DA3408   cmp  r3, #5
00DA340A   bhi  fora
00DA340C   ldr  r2, [pc, #12]     ; -> MAPA
00DA340E   ldrb r3, [r2, r3]      ; indice na HOME
00DA3410   strh r3, [r0, #0xc]    ; reescreve o ctrl_id na mensagem
00DA3412   bl   #0xd00f3c         ; page1_process
00DA3416   fora: b.w #0xd0ed94    ; saida comum
           MAPA = [5, 7, 10, 4, 6, 8]
```

Mesma convenção da página 1 (`bl` do módulo, depois `b` para a saída).

### 24.3 Por que a guarda NÃO precisa ser relaxada

O `event_cb` do Extras envia `page = 0x53`, que **é** a página corrente.
Então em `page1_process`:

```asm
ldrh r2, [r4, #8]      ; msg->page  = 0x53
ldrb r0, [r3, #0xa]    ; corrente   = 0x53
cmp  r2, r0            ; PASSA
```

E `r0` fica valendo `0x53` — a página de origem **correta** para os
blocos que chamam `0xd0dae0` sem recarregar r0. **O patch que eu errei no
V022 era, além de errado, desnecessário.**

### 24.4 As entradas da tabela de saltos que voltaram

O V025 tinha repontado os índices 1, 2 e 3 para Imagem / Extras /
Configurar, deixando **vídeo, Gravação e Rádio sem entrada**. Foram
devolvidos a slots que sobraram:

| tbh | antes | agora |
|---|---|---|
| idx 5 | Imagem (duplicado do idx 1) | **vídeo** |
| idx 7 | Configurar (duplicado do idx 3) | **Gravação** |
| idx 10 | não usado | **Rádio** |

Por isso o `MAPA` é `[5, 7, 10, 4, 6, 8]` e não `[1, 2, 3, 4, 6, 8]`.

### 24.5 Um erro pego pela conferência

A primeira montagem gerou `ldrb r3, [r3, r3]` em vez de
`ldrb r3, [r2, r3]` — eu montei `0x5CDB` quando o certo era `0x5CD3`,
trocando o registrador **base**. O disassembly de volta pegou antes de
qualquer kit ser gerado.

> Teria dado um índice lixo e um salto para bloco errado — sintoma
> confuso, difícil de atribuir. **Desmontar o que se monta não é
> cerimônia: é o que separa um erro de 2 bits de uma tarde de
> bissecção.**

**50 bytes, 5 setores.**

---

## 23. ⚠️ 2026-09-14 — O roteamento do Extras está QUEBRADO no aparelho

Relato do mantenedor, com a 1.8 gravada:

```text
Video        -> abre Despertador
Gravacao     -> abre Imagem
Radio        -> "Sem dados de dicionario"
Livro digital, Bluetooth, Pastas -> nao abrem nada
```

### 23.1 O que está CONFIRMADO

**A camada APP está intacta de fábrica.** Conferido byte a byte entre o
original, a V029 e a V057:

| região | original == V057 |
|---|---|
| tabela APP de 83 entradas `0x0010DB1C` | **igual** |
| módulo APP da página `0x53` `0x0010CDB0` | **igual** |
| guarda de página `0x00100F4C` | **igual** |

Ou seja: **o roteamento do Extras nunca passou pela camada APP.** Tudo o
que existe está na camada VIEW e na tabela `tbh` da home.

**O `event_cb` do Extras** (`0x00D2EFF6`) acha o índice do item (laço de
6) e envia:

```asm
view_send(page = 0x53, ctrl_grp = 4, ctrl_id = indice)
```

O despacho da camada APP é pela **página corrente** (§17), que é `0x53`.
A mensagem cai no módulo de fábrica da `0x53`, que **só trata o índice
0** (`MENU_LISTA.md` §15.3).

### 23.2 A tabela `tbh` da home, através das versões

```text
ctrl   original      V025/V026     V029          V057 (hoje)
  1    0xD01066      0xD011AE      0xD011AE      0xD011AE
  2    0xD010F6      0xD012DC p53  0xD012DC p53  0xD012DC p53
  3    0xD0113C      0xD0123A p28  0xD0123A p28  0xD0123A p28
  5    0xD011AE      0xD011AE      0xD01066 <<   0xD011AE
  7    0xD0123A p28  0xD0123A p28  0xD010F6 <<   0xD0123A p28
 10    0xD01202      0xD01202      0xD0113C <<   0xD01202
 11    0xD012DC p1E  0xD012DC p53  0xD012DC p53  0xD012DC p53
```

**A V057 tem exatamente a tabela da V025/V026.** A tabela **não é** a
regressão.

**A V029 é a única que estaciona os handlers originais deslocados** —
`0xD01066`, `0xD010F6`, `0xD0113C`, que na fábrica eram os `ctrl_id`
1, 2 e 3 — nas vagas livres 5, 7 e 10, para que o Extras pudesse
alcançá-los. **A V029 nunca foi gravada.**

### 23.3 A contradição que precisa ser resolvida

O CHANGELOG marca a V029 como **OBSOLETA** com a justificativa:

> *"O mantenedor confirmou no aparelho que todos os itens do Extras já
> abrem corretamente."*

Mas o próprio CHANGELOG da **V026** diz o contrário, como expectativa
declarada antes de gravar:

> *"Esperado: os 6 itens aparecem e a seleção anda, **mas nenhum abre** —
> o despacho é o original, que só trata o índice 0. Não é defeito."*

**Uma das duas afirmações está errada, e o relato de hoje dá razão à
V026.** Aposentei a V029 com base numa confirmação que contradizia a
expectativa escrita duas entradas antes, e não notei.

> **Lição:** quando um resultado no aparelho contradiz uma expectativa
> **escrita e específica**, isso é um conflito a investigar, não uma boa
> notícia a aceitar. Custou aposentar a versão que continha o conserto.

### 23.4 A RAIZ, encontrada

`page_home_menu_scr_process` — o tratador de mensagens da camada VIEW
para a página `0x53` — trata **dois** tipos de mensagem:

```asm
00D2F33C   ldrh r2, [r0, #6]      ; tipo da mensagem
00D2F33E   cmp  r2, #2            ; tipo 2 = trocar de tela
00D2F344   beq  0xd2f350          ;   -> b.w view_page_create
00D2F346   cmp  r2, #4            ; tipo 4 = "enter" de item
00D2F348   beq  0xd2f372          ;   -> SO IMPRIME DEBUG E RETORNA
```

O `event_cb` do Extras envia **tipo 4**. A camada VIEW o descarta — e
isso é normal: em `page_set_menu_scr_process` (Configurar) a estrutura é
**idêntica**, o tipo 4 também só loga. **Quem serve o "enter" é a camada
APP.**

E aí está o problema:

| página | módulo APP | estado |
|---|---|---|
| `0x28` Configurar | `0xD09354` | de fábrica, **completo** — funciona |
| `0x53` Extras | `0xD0CDB0` | de fábrica do `page_home_menu`, que **só trata o índice 0** |

**A página `0x53` nunca ganhou módulo APP.** Toda a obra do Extras
(V022–V026) foi na camada VIEW: a tela, os 6 itens, os textos, a
seleção. O despacho dos itens ficou com o módulo de fábrica de uma tela
que tinha 3 itens mortos.

**Isso confirma a expectativa escrita da V026** — *"os 6 itens aparecem
e a seleção anda, mas nenhum abre"* — e confirma que a V029, que existia
para resolver exatamente isto, foi aposentada por engano.

### 23.4-bis A CAUSA EXATA, encontrada

O módulo real da página `0x53` **não** é `0xD0CDB0` (essa é a função que
*abre* a página, da tabela por destino). É `0xD0CC0C`, alcançado pela
**segunda** tabela de 83 entradas — a indexada pela página **corrente**,
`0x00D0EF64`, que a V029 tinha descoberto:

```text
pagina corrente 0x01 -> 0xD0F0B1  bl 0xd00f3c   page1_process
pagina corrente 0x28 -> 0xD0F183  bl 0xd09150   page_set_menu   (funciona)
pagina corrente 0x53 -> 0xD0F219  bl 0xd0cc0c   pstr_page84_process
```

E dentro dele, o despacho dos itens:

```asm
00D0CC7C   ldrh r2, [r4, #0xc]    ; ctrl_id = indice do item
00D0CC7E   cmp  r2, #2
00D0CC80   bhi  0xd0cd6e          ; > 2 -> sai sem fazer nada

ctrl_id 0 -> 0xD0CCAC   movs r3, #0x1e   ; pagina 0x1E = Despertador
ctrl_id 1 -> 0xD0CCBC   confere cartao, conta arquivos -> imagem
ctrl_id 2 -> 0xD0CD3C   -> dicionario
```

**Bate item a item com o relato do aparelho:** Vídeo→Despertador,
Gravação→Imagem, Rádio→dicionário, e os três últimos não fazem nada.

É a lista antiga de 3 itens da página `0x53`, intacta. A V026 estendeu a
**tela** de 3 para 6 itens e **nunca tocou no despacho** — exatamente o
que a própria entrada dela dizia que aconteceria.

> Correção de leitura: `MENU_LISTA.md` §15.3 dizia *"ignora todo
> `ctrl_id != 0`"*. É `ctrl_id > 2`. Três itens, não um.

### 23.5 O que ainda NÃO está determinado

Por que três itens abrem **alguma coisa** (e errada) se o módulo de
fábrica da `0x53` só trata o índice 0. Há um caminho que eu ainda não
mapeei. **Não vou propor patch antes de fechar isso** — é exatamente o
tipo de lacuna que produziu o V016.

Por que três itens abrem **alguma coisa** — e errada — se o módulo de
fábrica só trata o índice 0. O módulo `0xD0CDB0` faz algo com os índices
baixos que eu ainda não li por inteiro. **Esse resto precisa ser lido
antes de qualquer patch**, porque é ele que diz se o módulo novo pode
simplesmente substituir o antigo ou tem de conviver com ele.

### 23.6 As duas rotas, agora que a raiz é conhecida

| rota | o que é | custo | risco |
|---|---|---|---|
| **A** — módulo próprio para a `0x53` na área livre, com tabela de 6 destinos, chamando `0xd0dae0(0x53, grp, id, destino)` | o desenho da §17 | ~60 B de código + tabela + 1 desvio | perde as verificações de cartão/volume e as mensagens de erro de cada item |
| **B** — o desenho da **V029**: estacionar os handlers originais deslocados (`0xD01066`, `0xD010F6`, `0xD0113C`) nas vagas 5, 7 e 10 do `tbh` da home, e o Extras envia `ctrl_id` para a **página 1** | 6 bytes de tabela + ajuste no `event_cb` | mantém **todas** as verificações originais de cada item |

**A rota B é melhor** e já estava montada na V029 — é ela que preserva
*"Vídeo sem cartão diz que não há vídeos"* em vez de abrir tela vazia.
O que falta é conferir por que a V029 foi considerada desnecessária e
reconstruí-la sobre a V058.

### 23.7 O DESENHO DO CONSERTO — rota B, completo

**A guarda de `page1_process` não exige página 1.** Ela compara
`msg->page` com a **página corrente**:

```asm
00D00F4C   ldrh r2, [r4, #8]      ; pagina da mensagem
00D00F4E   ldrb r0, [r3, #0xa]    ; pagina CORRENTE (global 0x00823D0F)
00D00F50   cmp  r2, r0
```

Com o Extras na tela as duas valem `0x53`, então **a mensagem passa
intacta**. Não é preciso relaxar guarda nenhuma — a V025 tinha razão em
dizer que o relaxamento era desnecessário.

Logo o módulo da `0x53` pode simplesmente **reescrever o `ctrl_id` e
repassar para `page1_process`**, que roda o handler ORIGINAL de cada
item, com todas as verificações de cartão e volume e as mensagens de
erro. E como os handlers terminam em
`0xd0dae0(origem = msg->page = 0x53, …)`, o "voltar" da tela aberta
retorna ao Extras, não à home.

#### O mapa, derivado da tabela de fábrica

```text
home ORIGINAL, 9 ids: [1, 3, 5, 6, 2, 4, 9, 10, 8]

ctrl_id 0 Musica   1 Video   2 Gravacao  3 Radio   4 Livro
        5 Imagem   6 Bluetooth  7 Configurar  8 Pastas
```

| Extras | item | ctrl_id da home |
|---|---|---|
| 0 | Vídeo | 1 |
| 1 | Gravação | 2 |
| 2 | Rádio | 3 |
| 3 | Livro digital | **4** ✅ já correto hoje |
| 4 | Bluetooth | **6** ✅ já correto hoje |
| 5 | Pastas | **8** ✅ já correto hoje |

Bate com a `EXTRAS` da `make_extras_menu.py` — confirmação independente.

#### ⚠️ A pegadinha: o `tbh` da home foi reescrito

Os `ctrl_id` 1, 2 e 3 **não apontam mais** para Vídeo, Gravação e Rádio:

```text
ctrl_id 1 -> 0xD011AE  (Imagem)       ctrl_id 2 -> 0x53   ctrl_id 3 -> 0x28
```

Os handlers originais continuam no código, **órfãos**: `0xD01066`
(Vídeo), `0xD010F6` (Gravação), `0xD0113C` (Rádio). Por isso a V029
estacionava os três em vagas livres do `tbh` — 5, 7 e 10 — e o mapa
virava `[5, 7, 10, 4, 6, 8]`.

**É esse o desenho a reconstruir.** Duas partes:

```text
A)  tbh da home: vagas 5, 7 e 10 recebem 0xD01066, 0xD010F6, 0xD0113C
B)  0x0010CC7E: `cmp r2,#2 ; bhi` -> b.w <rotina na area livre>
        rotina: se indice > 5 -> sai
                ctrl_id = MAPA[indice]       MAPA = [5,7,10,4,6,8]
                strh ctrl_id, [r4, #0xc]
                mov  r0, r4
                pop.w {r4,r5,r6,r7,r8,lr}
                b.w  0xD00F3C                ; page1_process
```

O prólogo de `0xD0CC0C` é `push.w {r4,r5,r6,r7,r8,lr}` **sem `sub sp`**,
e a saída é `pop.w {…,pc}` em `0xD0CD6E` — o desempilhamento é direto.

#### O que conferir ANTES de gravar

1. **Se alguém envia `ctrl_id` 5, 7 ou 10 para `page1_process`.** A home
   tem 4 itens (0..3), mas a página `0x51` (`page_expand_home`) pode usar
   ids altos. Se usar, as vagas escolhidas mudam.
2. Cada um dos 6 destinos, desmontando o handler que o `tbh` passa a
   apontar.
3. Gravar **sozinha** (R4): é mudança de despacho, a classe que já custou
   três gravações.

---

## 24. ✅ O Extras consertado — diagnosticado no firmware DE FÁBRICA

> Decisão do mantenedor: *"não vamos levar como padrão as versões que
> geramos, pq elas podem estar erradas. Vamos pegar o firmware original e
> ver para onde os itens do extra apontavam."*
>
> **Certíssimo.** A cadeia V014..V068 acumula decisões minhas; raciocinar
> sobre ela propaga erro. Refiz o diagnóstico no `GN438_original.bin`.

### 24.1 O que a fábrica diz

```text
page_home_menu (pagina 0x53), DE FABRICA — TRES itens:
   item 0  id  7  'Despertador'
   item 1  id  4  'Imagem'
   item 2  id 11  'Dicionario'

pstr_page84_process (0x00D0CC0C):
   0x00D0CC7E   cmp r2, #2
   0x00D0CC80   bhi 0xd0cd6e      ; > 2 -> sai sem fazer nada
```

A V026 esticou a **tela** de 3 para 6 itens e **nunca tocou no despacho**.
Por isso: Vídeo→Despertador, Gravação→Imagem, Rádio→dicionário, e os três
últimos nada. **Bate item a item com o relato.**

### 24.2 A home de fábrica, e os órfãos

```text
ctrl_id 0 Musica   1 Video   2 Gravacao  3 Radio   4 Livro
        5 Imagem   6 Bluetooth  7 Configurar  8 Ver pastas

tbh de fabrica:  1 -> 0xD01066 Video      4 -> 0xD01162 Livro
                 2 -> 0xD010F6 Gravacao   6 -> 0xD012D6 Bluetooth
                 3 -> 0xD0113C Radio      8 -> 0xD0128C Pastas
```

Confirmação independente: o handler do `ctrl_id 3` carrega
**"O rádio precisa ser conectado como uma antena"**. Não há dúvida.

A home de 4 itens (V022) reescreveu os slots 1, 2 e 3 — deixando
**órfãos** os handlers de Vídeo, Gravação e Rádio. Os de Livro, Bluetooth
e Pastas (4, 6, 8) **nunca foram tocados**: metade do caminho já estava
de pé.

### 24.3 Os três slots reaproveitados — e por que estes

Comparando `tbh` de fábrica × atual, três slots têm alvo **duplicado**,
isto é, já alcançável por outro `ctrl_id`:

```text
slot  5 -> mesmo alvo do 1        slot 11 -> mesmo alvo do 2
slot  7 -> mesmo alvo do 3
```

Reaproveitá-los não perde função nenhuma. O slot **9** (caminho de erro)
fica intacto de propósito.

### 24.4 Por que repassar para `page1_process`

Os handlers originais verificam cartão, volume e índice sujo, e mostram
as mensagens certas. Abrir a página destino direto jogaria isso fora:
*"Vídeo"* sem cartão abriria tela vazia em vez de avisar.

E a guarda de `page1_process` **não exige página 1** — compara
`msg->page` com a **página corrente**, e com o Extras na tela as duas
valem `0x53`. **Nenhum relaxamento de guarda é necessário** — a V025
tinha razão.

Como os handlers terminam em `0xd0dae0(origem = 0x53)`, o "voltar" da
tela aberta retorna ao **Extras**, não à home.

### 24.5 O patch

```text
0x00100FC8  tbh[ 5]  Imagem      -> 0xD01066 Video
0x00100FCC  tbh[ 7]  Configurar  -> 0xD010F6 Gravacao
0x00100FD4  tbh[11]  pagina 0x53 -> 0xD0113C Radio
0x001A5900  32 B  rotina + mapa [5, 7, 11, 4, 6, 8]
0x0010CC7E  cmp/bhi -> b.w 0x00DA5900
```

**41 bytes, 3 setores.** `tools/patch_extras.py`.

### 24.6 ⚠️ Um erro meu, pego na conferência

A primeira montagem usou `ldr r3, =MAPA` — que traz o **conteúdo** do
mapa como se fosse ponteiro (`0x040B0705` = os bytes 5,7,11,4). O certo
é `adr r3, MAPA`, que dá o **endereço**.

E o verificador não pegou: ele **filtrava as linhas com `[pc`**, que é
exatamente onde o erro estava.

> **Lição:** filtrar o que é "ruído de montador" da conferência cria um
> ponto cego no lugar mais perigoso. O filtro foi removido.

### 24.7 O que falta

Gravar e testar **sozinha** — muda despacho de página, a classe que já
custou três gravações.
