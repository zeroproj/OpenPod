# 020 — Estudo do SL6801_player aplicado ao GN-438

Base: `firmware/ORIGINAL/GN438_original.bin` (sha256 `b7cd5eb9…`,
YP3 `yp3_2.0.43`). Toda evidência de código é do **nosso** binário, lida com
`tools/disasm.py`. Nada foi gravado no aparelho. A referência
`referencias/SL6801_player/` foi lida como documento: nenhum código ou trecho
foi copiado, nem os scripts dela foram executados.

Convenção de endereço: código em **XIP** (`0xC00000 + offset`), como no
`analysis/funcmap.json`; strings e tabelas em **offset de flash**, marcadas
com `off`.

## Veredito curto

| # | Pergunta | Existe no GN-438? | Classe | Vale para o OpenPod? | Custo/risco |
|---|---|---|---|---|---|
| 1 | Camada de SO (sleep, tarefa, semáforo, memória) | Sim, completa | CONFIRMADO | Sim, como ferramenta | Baixo |
| 2 | Trava de ~10 s + reset na tarefa de UI | Mesma **classe** de defeito | PROVÁVEL | Sim, como regra de projeto | Zero (regra) |
| 3 | Vídeo espelhado na horizontal | Mesmo player, sem flag achada | HIPÓTESE | Sim, se confirmado no aparelho | Médio |
| 4 | Recursos escondidos | Páginas existem; quase todas sem entrada | CONFIRMADO (existência) | Só o menu Apps | Baixo a alto |
| 5 | Fontes (`° ¡ ¿`, polonês, romeno) | Faltam; português completo | CONFIRMADO | Não para pt-BR | Médio (fonte inteira) |
| 6 | Regras do `.avi` | Todas menos `idx1` | CONFIRMADO | Sim, para página de ajuda | Zero |
| 7 | Dump da ROM | Ferramenta serve, mas não para o mutex | CONFIRMADO | Sim, com decisor | Baixo |
| 8 | SDK em C da referência | Cabe na nossa área livre | CONFIRMADO (espaço) | Estratégico, não agora | Médio |
| 9 | Item "Apps" e apps próprios | Página 0x52 já existe e monta 3 itens | CONFIRMADO | Sim, alto valor | Baixo a médio |

---

## 1. Camada de SO

A ficha 015 não achou o `sleep` porque procurou no tratador de mensagem
(`0xD2436E`, tipo 0x11). A camada de SO fica no bloco OAL, em `0xCF78xx`.

| Equivalente no `fw.h` da referência | Nosso endereço | Evidência | Classe |
|---|---|---|---|
| `fw_os_sleep(ms)` | `0xCF78E4` | `bl 0xCF78B4` converte ms→ticks (`freq @0x00800470 / 1000.0`, float em `0xCF78E0`); cauda `b.w 0xA500` | CONFIRMADO (ms) |
| `fw_task_create` | `0xCF7AD4` | `oal_malloc 0xCF780C`, `memset 0xBAA`, dois semáforos `0xCF790E`, `os_thread_create 0x8A30`; logs `Error creating exitSem/joinSem` | CONFIRMADO |
| `fw_task_join` | `0xCF7B90` | `sem_give 0xCF799E` → `sem_take 0xCF7996` → `sem_delete 0xCF7918` ×2 → `0x8BF4` → `oal_free 0xCF7884` | CONFIRMADO |
| semáforo criar/apagar/tomar/dar | `0xCF790E` / `0xCF7918` / `0xCF7930` / `0xCF799E` | criar confirmado pelo chamador de áudio `0xD665E8`, logo antes de `hw eq OAL_sem_create_binary fail` (`off 0xE2873`) | CONFIRMADO |
| `fw_os_calloc` | `0xCF7840` | multiplica os dois tamanhos, chama `0x9D50` e `memset 0xBAA` | CONFIRMADO |
| `fw_os_free` | `0xCF7884` | `b.w 0x9E3C` | CONFIRMADO |
| liberar bloco do heap | `0xCF7890` | `b.w 0x9E88` | CONFIRMADO |
| mutex recursivo | `0xCF7A32` (tomar) / `0xCF7A86` (dar) | chamam o primitivo de kernel `0x80DB48` / `0x80DB6E` | CONFIRMADO |

Uso prático: dá para fazer pausa real sem busy-wait e criar tarefa própria com
pilha. **Não** usar `sleep` dentro de mutex nem na tarefa de UI (ver §2). O
`0xCF79D2` é um laço que dorme 60 s (`0xEA60`) — útil como exemplo de tarefa
periódica, não como API.

## 2. Trava de ~10 s e reset

Referência: a tarefa de UI escreve em `/dev/audio0`; com o anel cheio, a
escrita bloqueia; o watchdog é alimentado por outra tarefa; ~10 s e reinicia.
Nosso caso (fichas 011–014): a `ViewTask` (`0xCF8210`, prioridade 0) pega o
mutex do banco e faz I/O de SD; a `MainTask` (`0xCF7DF1`, prioridade 1) — que
alimenta o watchdog em `0xCF7FBE` → `0xD46B14` — fica presa no mesmo mutex;
reset em ~15 s.

| Fato | Endereço | Classe |
|---|---|---|
| laço da ViewTask | `0xCF8274` | CONFIRMADO |
| prioridade da ViewTask = 0 | `0xCF8394` (`memset` do TCB) + tabela em RAM `0x0081D68C` | CONFIRMADO |
| prioridade da MainTask = 1 | `0xCF8068` (`movs r3,#1`) | CONFIRMADO |
| alimentação do watchdog | `0xCF7FBE` → `0xD46B14` | CONFIRMADO |
| limite de ~20 s (`0x14`) | `0xD46AAA` | CONFIRMADO |
| fábrica **desregistra** o monitor da ViewTask | `0xCFCA0E` | CONFIRMADO |

Resposta: **não é a mesma causa**, é a mesma **classe**: chamada que bloqueia
na tarefa de UI + watchdog alimentado por outra tarefa. O recurso é diferente
(anel de áudio × mutex de banco), e a prova do nosso lado é o mutex. A lição é
a mesma: I/O e espera não podem morar na tarefa de UI; ou vão para
`PreTask`/tarefa de serviço, ou o monitor da ViewTask é desregistrado como a
fábrica faz. As fichas 011–014 já resolveram o caso concreto por esse caminho.

## 3. Vídeo espelhado

O player é o mesmo: `avi_init 0xD12600`, chamado por
`pstr_page20_show_video 0xD03440` em `0xD03476`; módulo `0xD12600–0xD185E8`.
As strings são idênticas às da referência (`-video player is alive!`,
`-avi_init failed!`, `-avi channel is not 2!`, `-avi width and height failed!`,
`RIFFAVI LISThdrl`, `audsMJPGvids` em `off 0x112120`).

O que **não** foi provado:

- não há flag/`cmp` de espelhamento no `avi_init` nem no parser;
- o autor da referência também não achou a causa e compensa no ffmpeg com
  `hflip` (README, linhas 491–507);
- o candidato natural é a cópia do quadro decodificado para o buffer do LCD,
  dentro do player (`0xD12600–0xD185E8`), não o decodificador de foto.

Classe: **HIPÓTESE**. Não existe correção de poucos bytes provada. O teste
barato é gerar um `.avi` 128×160 MJPEG com marcador assimétrico, tocar no
aparelho e ver se espelha; se espelhar, a correção é no blit do player. O
caminho de foto é separado o bastante para o conserto não o atingir.

## 4. Recursos escondidos

Os IDs de página **nossos** são diferentes dos da referência (o menu Apps dela
é 0x53; o nosso é 0x52). Mapa real, tirado da tabela `tbb` de
`view_page_create 0xD23B10` (`0xD23B38`) e dos `bl` de cada caso:

| Recurso | Página nossa | Criador (XIP) | Evidência de texto | Classe |
|---|---|---|---|---|
| Apps | **0x52** | `page_home_menu_create 0xD2F0A0` | 3 itens: Despertador, Imagem, Dicionário | CONFIRMADO |
| Dicionário (entrada) | **0x36** | `page_dict_input_create 0xD29934` | `0:/dict/dict.txt` `off 0x4C5BF` | CONFIRMADO |
| Dicionário (tocar) | **0x37** | `page_dict_play_create 0xD29C6C` | `dict.pcm` `off 0x4C5F4`, `dict.id` `off 0x4C605` | CONFIRMADO |
| Senha de ligar (entrada) | **0x4E** | `page_pass_input_create 0xD371B8` | `Senha original` `off 0x552EE`, `Nova senha` `off 0x55300` | CONFIRMADO |
| Senha de ligar (menu) | **0x4F** | `page_pass_menu_create 0xD3773C` | `Senha ligada` `off 0x5521B`, `Erro da senha` `off 0x55236` | CONFIRMADO |
| Luz da tecla | **0x4A** | `page_set_keylight_create 0xD39A44` | `Key light` `off 0x5D23B` | CONFIRMADO |
| Home expandida | **0x50** | `page_expand_home_create 0xD2E6B4` | — | CONFIRMADO |

A existência é certa; a **entrada** não. A home é uma grade 3×3 fixa
(`page_home_create 0xD2EBB8`, 9 posições) e os rótulos vêm da tabela
`off 0xC486C4`: `[1,3,5,6,2,4,9,10,8]` — Música, vídeo, Gravação, Rádio, Livro digital,
Imagem, Bluetooth, Configurar, Ver pastas. O índice 5 é **Imagem** (string 4),
exatamente onde a referência põe Apps. Nenhuma chamada com página 0x52 foi
achada fora do despacho; é PROVÁVEL que a página Apps esteja compilada e
inacessível. O mesmo vale para senha, dicionário e luz da tecla: existem, mas
não têm linha de menu.

Custo de ligar: o menu Apps é o mais barato e é o que o decisor quer (§9). A
senha é média (duas páginas prontas, mas exige gravação em NV e risco de
trancar o aparelho). O dicionário é alto (precisa dos três arquivos em
`0:/dict/`; sem eles a tela abre e falha). A home expandida é média/alta e a
própria referência a considera abandonada.

## 5. Fontes

Fonte principal: tabela de glifos `0x86C44`, `cmap 0xA27E6`, **7098 glifos**,
1 bpp, faixa U+0020–U+FFE5. O português está completo (á à â ã é ê í ó ô õ ú
ü ç, maiúsculas e minúsculas).

Faltam:

- `°` U+00B0, `¡` U+00A1, `¿` U+00BF;
- polonês: `ć ł ń ś ź ż` e maiúsculas (só `ą ę Ą Ę` existem);
- romeno: `ă ș ț` e maiúsculas (só `â î Â Î` existem).

Impacto no nosso português: **nenhum**. Os únicos textos com `°` são
`N° di versione` (`off 0x57A21`) e `N° de version` (`off 0x5AC6D`); o
português usa `Número da versão` (`off 0x544A6`). Não há interface em polonês
nem romeno no binário (não há `Polski`, `Română`, `Język`, `Limba`). Só mexer
na fonte se um dia entrar um desses idiomas ou um texto com `°`; aí é rebuild
da fonte inteira, não um patch de byte (risco alto para toda a UI).

## 6. Regras do `.avi`

| Regra | Evidência nossa | Classe |
|---|---|---|
| extensão `.avi` | `*.avi` `off 0xE4321`, `db_video.db` `off 0xE40E5` | CONFIRMADO |
| vídeo MJPEG | parser compara `MJPG` (`audsMJPGvids`, `off 0x112120`) | CONFIRMADO |
| 128×160 | `0xD12718` `cmp 0x80`; `0xD12722` `cmp 0xA0` | CONFIRMADO |
| estéreo (2 canais) | `0xD126F2` / `0xD126FC` `cmp 2` | CONFIRMADO |
| blocos ≤ 30 KiB | `0xD1248A` `cmp.w r2,#0x7800; bhi erro`; buffer `0x7800` | CONFIRMADO |
| `movi` nos primeiros 30 KiB | lê `0x7800` em `0xD12684`; procura `movi` em `0xD12738` | CONFIRMADO |
| termina em `idx1` | não há constante `idx1` no binário | NÃO CONFIRMADO |

Para a página de ajuda do site: pode afirmar as seis primeiras; `idx1` é
recomendação de formato, não exigência comprovada do firmware.

## 7. Dump da ROM

Comando da referência: `smtlink_dump init read_mem 0 0x10000 rom.bin`.
É **somente leitura**, mas exige entrar no modo bootloader. Risco para a
flash: baixo; risco operacional: o aparelho fica no bootloader até sair.

O que ele responde (ROM em `0x0`): `printf 0x2B0`, `malloc 0x9D50`,
`free 0x9E3C`, liberação de heap `0x9E88`, `memcpy 0xB2A`, `memset 0xBAA`,
`delay 0xA500` e o `SysTick` `0xB5A9` (ficha 015). Isso fecha a unidade do
`delay`, o limite do alocador e o período do tick.

O que ele **não** responde: `0x80DB48` / `0x80DB6E` (mutex), `0x80D580`,
`0x80D81E` (fila) e o escalonador. Esses endereços estão na **RAM**
(`0x00800000–0x0087FFFF`), não na ROM. Para eles seria preciso um dump de RAM
pelo mesmo canal (`read_mem 0x800000 …`), que é a pergunta certa se o objetivo
for entender a trava do §2. Decisão do decisor; não é bloqueante para o resto.

## 8. SDK em C da referência

Como a referência faz: app em C em `0x00DD0000` (flash `0x1D0000`), 176 KiB,
toolchain **fixa** (xPack `arm-none-eabi-gcc 15.2.1`, ou `zig cc`),
`-nostdlib -ffreestanding -fno-builtin -fno-stack-protector -fno-pic
-mcpu=cortex-m4 -mfloat-abi=soft -mthumb -Os -std=c11`, **sem** `.data`/
`.bss` (o linker recusa), chamando o firmware por endereço via `fw.h` e
redirecionando `bl` com `patches.json` (confere o alvo esperado antes de
escrever).

Nosso lado: ferramentas de byte em Python, com conferência de premissas e
testes; para patch pequeno é mais seguro e mais barato. Para app maior (jogo,
utilitário, tela própria), o C ganha em legibilidade e verificação do
compilador, mas cria dependência de toolchain reproduzível, ABI/Thumb,
ausência de globais e endereços que mudam entre builds.

Espaço: a área livre declarada vai de `0x1A3040` a `0x1AB000` (lotes usados) e
de `0x1AB000` a `0x1FC000` fica **331.776 B (~324 KiB) contíguos**. Cabe com
folga um app do tamanho do da referência (176 KiB). Recomendação: não trocar o
método agora; se o menu Apps evoluir para apps próprios, prototipar um caminho
C em paralelo, com toolchain fixa, sem `.data`/`.bss`, e manter as mesmas
travas de premissa. O gargalo real de um app não é flash, é a RAM/heap do
LVGL.

## 9. Item "Apps" e apps próprios (acréscimo do decisor)

### (a) Como o menu Apps é montado — e o que temos

Na referência, a página 0x53 (`page_home_menu_create`) monta uma **lista** com
`fw_list_item_create` e duas linhas: Alarme e Imagens. No nosso GN-438 a página
equivalente é a **0x52** (`page_home_menu_create 0xD2F0A0`), e ela não usa
lista: monta **3 itens** com o criador de linha/tile da casa, com os
títulos vindos da tabela `off 0xC486E8` = `[7, 4, 11]`.

Conferido na tabela de português (`off 0xC53B84`, índice por idioma):

- id 7 = **Despertador**;
- id 4 = **Imagem** (a mesma Imagem da home);
- id 11 = **Dicionário**.

Ou seja: o menu Apps **já existe**, já tem Despertador e Imagem, e ainda ganhou
Dicionário. O que falta é só a porta de entrada na home. O despacho
`view_page_create 0xD23B10` tem a entrada 0x52 apontando para `0xD2F0A0`
(`bl` em `0xD23CF8`), e essa é a última entrada válida da tabela. O id 0x53
não tem caso: a leitura do `tbb` cai fora da tabela e executa lixo, então não
serve como id livre. A chamada existe, mas nenhuma tecla da home passa 0x52: a
home tem 9 posições fixas e o índice 5 é Imagem (0x15). É PROVÁVEL que a
página esteja inacessível hoje.

### (b) Como o OpenPod teria "Apps" na home

O caminho mais barato é o que o decisor propôs, e ele encaixa quase de graça:

1. **Na home, trocar o tile 5.** O rótulo do tile 5 é o id 4 (Imagem) em
   `off 0xC486D4`. Trocar esse id por um texto novo "Apps" (a tabela de
   idiomas é relocável; o `aplica_textos.py` já sabe mexer nela) e trocar o
   **alvo** do tile 5 de 0x15 (Imagem) para **0x52** (Apps). O alvo não está
   nessa tabela de rótulos: ele é resolvido no tratador da mensagem do tile.
   Localizar esse ponto é o único trabalho de reversão que falta; a estrutura
   é clara (índice 5 = Imagem = 0x15). Classe: PROVÁVEL.
2. **Nada se perde:** Imagem continua dentro do menu Apps, como item 2.
   Assim a home fica igual à da referência (Apps no lugar de Imagem) sem
   criar página nova.
3. **Apps próprios:** o menu Apps tem 3 slots. Dicionário é o candidato
   natural a sair (não tem dados em `0:/dict/` e não é traduzido); no lugar
   dele entra "Jogos" ou "Extras". Para mais de 3 apps, é preciso estender o
   laço `cmp r6,#3` e a tabela de coordenadas — aí o custo sobe e vale mais
   fazer uma página de lista nova.
4. **Onde mora o código do app:** na área livre (`0x1AB000–0x1FC000`), em
   XIP, chamado por um `bl`/ponteiro com bit Thumb. O jeito que a referência
   usa e que funciona no nosso caso é **gancho no criador**: trocar o `bl` de
   `0xD23CF8` (que hoje chama `0xD2F0A0`) por um `bl` para a nossa rotina; a
   rotina chama a fábrica e depois acrescenta/troca o que quiser. Criar uma
   página **nova** é pior: a tabela `tbb` usa deslocamento de 1 byte (alcance
   de ±256 bytes), então não dá para apontar direto para a área livre; teria
   de haver um stub perto do `switch`. Reutilizar/hookar uma página existente
   é o caminho de menor risco.
5. **Abrir o app:** a linha "Jogos" chama `view_page_create` com o id da
   página que o app usa. Se o app reutiliza a própria 0x52 com um estado
   interno, não precisa de id novo; se usa uma página que o OpenPod não
   aproveita, o id já está despachado.

### (c) Teclas e desenho com segurança

- **Uma tarefa só desenha:** o LVGL não é thread-safe. Toda criação, mudança e
  destruição de objeto tem de rodar na tarefa de UI (`ViewTask 0xCF8210`), que
  é quem chama `view_page_create 0xD23B10`. Tarefa própria só para cálculo,
  SD ou som; ela nunca chama LVGL. Comunique por fila/semáforo e mande a
  atualização de tela para a UI (timer do LVGL ou mensagem de view).
- **Teclas:** o caminho é o mesmo das páginas de fábrica: o evento da página
  recebe o código da tecla. Exemplos confirmados em `page_home_event_cb
  0xD2E950`: Enter `0x0A`, anterior `0x0B`, próximo `0x09`, Esc `0x1B`,
  esquerda `0x14`/`0x81`, direita `0x13`/`0x8A`/`0xA0`, cima/baixo
  `0x92`/`0x87`. O app deve registrar o próprio `event_cb`
  (`lv_obj_add_event_cb 0xD47064`) e entrar no grupo de teclas
  (`lv_group_create 0xD473A8`), não ler o driver de tecla por conta própria.
  Para uma tela cheia, o padrão da referência é um overlay em
  `lv_disp_get_layer_top 0xD46E8C`, com o grupo focado e congelado enquanto o
  app está aberto.
- **Memória:** alocar no create e liberar no `LV_EVENT_DELETE`: apagar timers,
  remover callbacks, liberar buffers (`lv_mem_realloc 0xD58200`,
  `lv_mem_buf_release 0xD58358`) e zerar ponteiros. Se o app usou
  `OAL_calloc 0xCF7840`, liberar com `oal_free 0xCF7884`; não misturar os dois
  alocadores. `lv_obj_del 0xD4D350` dispara o `DELETE` — a limpeza tem de
  estar lá, não depois.
- **Não bloquear:** nada de `sleep` (`0xCF78E4`) nem espera de SD/áudio na
  tarefa de UI (§2). Se o app precisa de arquivo, lê em tarefa própria e
  entrega o buffer pronto.
- **Ciclo de vida:** se uma tarefa de fundo pode postar para a tela, carimbe a
  geração da tela e descarte o posto depois do `DELETE`; é a fonte clássica de
  use-after-free em app de firmware.

### (d) Espaço livre

| Faixa | Tamanho | Uso |
|---|---|---|
| `0x1A3040–0x1AB000` | 32.704 B | lotes declarados no `MAPA` (todos usados) |
| `0x1A4F00–0x1A5000` | 256 B | carimbo de versão (reservado) |
| **`0x1AB000–0x1FC000`** | **331.776 B (~324 KiB)** | **livre, contíguo** |

Cabe um app pequeno (jogo de dezenas de KiB) com muita folga, e cabe até um
app em C do tamanho do da referência (176 KiB). O limite prático é a RAM/heap
do LVGL e o custo de manter a UI fluida, não a flash. Reservar o início da
faixa para a rotina de gancho e o restante para o app; declarar o lote no
`MAPA` de `tools/build.py` antes de escrever, como manda o processo.

## O que não deu para provar

- a causa exata do espelhamento do vídeo (§3): só o teste com marcador
  assimétrico no aparelho decide;
- que a trava da referência e a nossa têm a mesma causa (§2): a classe é a
  mesma, o recurso não;
- o ponto exato que traduz índice de tile → página na home (§9b): a estrutura e
  o valor 0x15 do índice 5 estão certos, mas o `cmp`/tabela final não foi
  isolado;
- que `idx1` seja exigido pelo firmware (§6): não há constante no binário;
- a unidade do `delay` da ROM sem o dump (§7): a conversão ms→ticks do
  `sleep` está confirmada, a função `0xA500` em si não foi lida.

## Recomendações, por ordem de valor

1. **Menu Apps (§9):** ligar a página 0x52 trocando o tile 5 da home de
   Imagem para Apps. É o maior valor pelo menor custo; preserva Imagem
   dentro do menu e reabre Despertador/Dicionário. Ficha de implementação precisa
   localizar o alvo do índice 5 e o texto "Apps".
2. **Regra de projeto (§2):** nenhum I/O ou espera na tarefa de UI; serviço em
   `PreTask`/tarefa própria; não segurar mutex durante SD. Custo zero e evita
   a repetição da trava.
3. **Vídeo (§3):** teste com `.avi` assimétrico antes de qualquer patch. Se
   confirmar, corrigir no blit do player; não mexer no decodificador de foto.
4. **Página de ajuda do site (§6):** publicar as seis regras confirmadas do
   `.avi`; deixar `idx1` como recomendação, não como exigência.
5. **Dump da ROM (§7):** decisor. Se o objetivo for a trava, pedir também a
   faixa de RAM; a ROM sozinha não responde o mutex.
6. **Fonte (§5):** não mexer para pt-BR. Só reabrir se entrar idioma que use
   `°`, polonês ou romeno.
7. **Senha/luz da tecla (§4):** existem, mas o custo/risco não se paga agora;
   a senha pode trancar o aparelho e o dicionário depende de dados externos.
8. **SDK em C (§8):** não trocar o método. Prototipar em paralelo só quando o
   menu Apps virar plataforma de apps; a área livre (§9d) comporta.
