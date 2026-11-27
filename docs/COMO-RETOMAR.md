# COMO RETOMAR — documento de entrada da coordenação (atualizado em 2026-11-26)

> **Leia isto primeiro.** Este documento substitui o `docs/ESTADO_ATUAL.md` (parado em set/2026) como ponto de partida.
> As decisões, com data e a fala do decisor, estão em `docs/decisoes.md` (D1–D44). O processo detalhado está em `docs/processo.md`.
> As regras de byte e de revisão do firmware estão no `AGENTS.md` (raiz) e no `CLAUDE.md`.

## 1. Quem é quem
**O guia completo de como coordenar os agentes está em `docs/COORDENACAO-AGENTES.md`. Leia logo depois deste.**

| Papel | Quem | Observação |
|---|---|---|
| **Decisor** | Lucas (usuário) | Escreve em português. Só ele grava no aparelho e dá o **"pode"** para publicar. |
| **Coordenação** (você) | `opencode-go/minimax-m3` | Escreve as fichas, despacha, **confere byte a byte**, manda revisar, empacota, assina e publica com o "pode". Não desenvolve as fichas. |
| **Desenvolvedor** | agente `desenvolvedor` = `opencode/deepseek-v4.1-flash-free` | Faz as fichas. Quando a cota acaba, o opencode **fica parado em silêncio**. |
| **Desenvolvedor reserva** | agente `desenvolvedor-go` = `opencode-go/deepseek-v4.1-flash` | Quando a cota do grátis acabar. Se o Go também acabar, avise o decisor (a reserva paga `minimax/MiniMax-M3` só com o aval dele). |
| **Revisor** | agente `revisor` = `opencode/big-pickle` (grátis) | Só lê e escreve o parecer (`APROVADO` / `APROVADO COM RESSALVAS` / `REPROVADO`). |

Os agentes estão em `.opencode/agents/` nos dois repositórios (`OpenPod/` e `OpenPod-instalador/`).

## 2. Regras inegociáveis

1. **Nunca alterar `firmware/ORIGINAL/GN438_original.bin`** (sha `b7cd5eb952be5328…`). **Nunca gravar no aparelho**: quem grava é o decisor.
2. **Nada de linhas antigas**: Core, Alphas e Betas são proibidas. Só se parte do **ORIGINAL**. Nada de flash abaixo de `0xE000`; o setor
   `0xD000` (tabela) e a PSMP (`0x1FC000+`) ficam intocados.
3. **Publicar só com o "pode" explícito do decisor.** A trava do Claude Code bloqueava `push --force` sem ele; mantenha a regra.
4. **Código-fonte do OpenPod System NUNCA é público** (D35). Só o lado Rockbox é público, pela GPL:
   - `zeroproj/openpod-installer` (o código do OpenPod Tune);
   - `zeroproj/rockbox-gn438` (o Rockbox que distribuímos).
5. **Textos públicos neutros:** nenhuma marca de terceiros (nada de Apple/iPod). Jogos descritos pelo estilo ("voar entre obstáculos",
   "encaixar blocos", "cobrinha"). O bichinho é "bichinho virtual". O NanoClone128 é de **uso pessoal** e nunca vai a público.
6. **Classificar o que se afirma:** CONFIRMADO / PROVÁVEL / HIPÓTESE.
7. **Referência de terceiros:** primeiro um fork/sync na conta `zeroproj` e a leitura a partir do fork (D29).
   - Código **sem licença** nunca é copiado.
   - Código **GPL** nunca entra no firmware OpenPod.
   - Código **MIT** entra com o aviso.
8. **Chave secreta dos pacotes:** `~/.openpod/chave-pacotes-ed25519.pem`. **Nunca** vai a repositório, log ou teste. A pública é
   `0cfcee1aec04170d33d46c99164061111354003518f93c68b2b5369a4116c949`.

## 3. Pastas e repositórios

| O quê | Onde |
|---|---|
| **Projeto (privado)** | `/Users/zeroproj/Sistemas LWP/OpenPod`, branch `privado-completo` → remoto `privado` = `zeroproj/OpenPod-dev` (main). |
| **Site e downloads (público)** | `zeroproj/OpenPod` (branch órfão `main`, montado pelo `tools/publica_release.py`), no ar em https://zeroproj.github.io/OpenPod/ |
| **OpenPod Tune (privado)** | `/Users/zeroproj/Sistemas LWP/OpenPod-instalador` (`zeroproj/openpod-instalador`, branch `instalador-029`). O crate fica em `instalador/`; os geradores em `pacotes/`; as fichas em `docs/openpod/`. |
| **OpenPod Tune (público, GPL)** | `zeroproj/openpod-installer`: uma **cópia limpa** (sem histórico e sem `docs/openpod`), atualizada a cada versão publicada. |
| **Rockbox (público, GPL)** | `zeroproj/rockbox-gn438`: espelho do `jaydens-tasty-slop/rockbox`, no commit `822b9f5e99`. |
| **Forks de referência** | `zeroproj/SL6801_player`, `zeroproj/smartlink_flash`, `zeroproj/epet`, `zeroproj/rockslop`. |
| **Arquivos locais (fora do Git)** | `OpenPod/_local/`: `publicar/{pacotes,instalador,storepod}` (o que vai ao site), `pacotes-teste/`, `instalador-teste/`, `aparelho/` (backup do aparelho do decisor), `storepod/itens/`, os textos do Reddit. |
| **Tema RockBox** | `OpenPod/rockbox/tema/`: `gera_openpod128.py` (tema), `ttf2fnt.py` (conversor de fontes nosso), `fontes/` (Inter e Source Sans, OFL), `gera_nanoclone128.py` (só pessoal). |
| **Máquina Linux** | Mint 22.3 pelo Tailscale: `ssh lab-linux-ts` (usuário zeroproj, `sudo` pede senha). Ali se compila o Tune para Linux (`~/openpod-tune-build`). |
| **GitHub** | O `gh` ativo é limtistech. Para a zeroproj: `GH_TOKEN=$(gh auth token --user zeroproj)`. O Git usa SSH (zeroproj). |

## 4. O que está no ar (2026-11-26)

> **PUBLICADO (26/11/2026, com o "pode" do decisor): OpenPod RockBox 5.3.822b9f5e99** (D46, D49, D50).
> - Nova numeração `firmware.customização.compilação` (era 1.2) e de volta os plugins que o próprio Rockbox chama:
>   `main_menu_config`, `playing_time`, `disktidy`. Mesma flash da 1.2.
> - Conferido antes de publicar: assinatura Ed25519 válida, todos os sha256 do SHA256SUMS batem, o `config.cfg` e o
>   `instalados.json` do usuário **não** estão no pacote, o `sistema.json` (tema 1.2) está.
> - No ar: `pacotes/openpod-rockbox-5.3.822b9f5e99.tar.gz` (sha `dac4f8c6…`), o `pacotes/index.json` aponta para 5.3 e o
>   pacote antigo da 1.2 dá **404**. O `index.html` mostra 5.3 no card e no histórico (PT/EN).

| Produto | Versão | Arquivo no site |
|---|---|---|
| **OpenPod System** (firmware de fábrica melhorado) | **Reload 3.5** (imagem `ba56813d…` + carimbo; o nome da música no cartão da home) — **vai virar 5.3** (D51: só a renumeração, mesmas funções) | `pacotes/openpod-system-3.5.tar.gz`, `atual/update.up`, `release/OpenPod-Reload-3.5/` |
| **OpenPod RockBox** | **5.3.822b9f5e99** (enxuto: só os temas OpenPod/Rockbox, sem jogos/apps/demos; volume na tela; registra o tema no cartão; plugins do sistema) | `pacotes/openpod-rockbox-5.3.822b9f5e99.tar.gz` |
| **OpenPod Tune** (instalador, ex-"Instalador OpenPod") | 0.4 | `instalador/openpod-tune-macos.dmg`, `-windows.exe`, `-linux-x86_64.tar.gz` |
| **StorePod** (a loja dentro do Tune) | o Tema OpenPod 1.2 (`sistema: true`) | `storepod/index.json`, `storepod/tema-openpod-1.2.tar.gz`, `storepod/tema-openpod.png` |
| **Índice do Tune** | — | `pacotes/index.json` (System + RockBox). O Tune lê de `https://zeroproj.github.io/OpenPod/pacotes/index.json`. |
| Recovery | ORS e Factory Reset | `recovery/ors/`, `recovery/fr/` (sempre sobem) |

O decisor testou o Tune no **macOS (com a senha), no Windows e no Linux**: funcionou. O System 3.5 e o RockBox estão no aparelho dele.

## 5. Como gerar e publicar (receitas)

**O pacote do RockBox atual (5.3), para regerar se preciso** (de dentro de `OpenPod-instalador/`; a fonte original do Jayden fica guardada
em `OpenPod/_local/fontes/rockbox-yp3-822b9f5e99-261122.tar.xz`, sha `1095e4b2…`):
```
python3 pacotes/gera_pacotes.py --rockbox "/Users/zeroproj/Sistemas LWP/OpenPod/_local/fontes/rockbox-yp3-822b9f5e99-261122.tar.xz" \
  --tema assets/openpod/OpenPod128.zip --versao "5.3.822b9f5e99" --enxuto --tema-storepod tema-openpod 1.2 \
  --saida "/Users/zeroproj/Sistemas LWP/OpenPod/_local/publicar/pacotes" --indice <indice-temporario.json>
```
e depois funda o índice temporário no `_local/publicar/pacotes/index.json` (conferindo o sha de cada pacote).
Regra da versão (D46): mudou só a customização → sobe o 2º número (pelo cartão); mudou o firmware ou a compilação → sobe o 1º (Recovery).

**OpenPod System (nova versão):**
1. `python3 tools/build.py --receita <receita> --saida firmware/WORKING/x.bin`. A 3.5 usa a receita `reload_3.5b`.
2. `python3 tools/patch_versao.py --in x.bin --out x_carimbado.bin --texto "Reload X" --em 0x1A4F00`. O `gera_versao` **não** carimba.
3. `python3 tools/gera_versao.py --imagem x_carimbado.bin --versao OpenPod-Reload-X --nome-tela "Reload X"` gera `release/OpenPod-Reload-X/`.
   Escreva à mão o "New in X" no README.
4. O pacote do Tune:
   `cd OpenPod-instalador && python3 pacotes/gera_pacotes.py --system release/.../*.up --versao X --saida OpenPod/_local/publicar/pacotes --indice …`.
   Depois junte o trecho do índice ao `index.json`, conferindo cada sha256.

**OpenPod RockBox:**
`python3 pacotes/gera_pacotes.py --rockbox <rockbox-yp3-*.tar.xz> --tema assets/openpod/OpenPod128.zip --versao 1.N.<build> --enxuto --tema-storepod tema-openpod <versao-do-tema> --saida …`
- O tar.xz do Rockbox vem dos releases do Jayden e deve ser **espelhado** antes em `zeroproj/rockbox-gn438`.
- O tema sai de `rockbox/tema/gera_openpod128.py`. Copie o zip para `OpenPod-instalador/assets/openpod/OpenPod128.zip`.

**Item da StorePod:**
`python3 pacotes/gera_storepod.py --item <pasta com .rockbox/> --id … --tipo tema|app|jogo --versao … --nome-pt … --nome-en … --desc-pt … --desc-en … --print img.png [--sistema] --saida OpenPod/_local/publicar/storepod`

**OpenPod Tune (os três):**
- `cd OpenPod-instalador/instalador && sh empacota-macos.sh && sh empacota-windows.sh`.
- Linux:
  `git archive HEAD | ssh lab-linux-ts 'rm -rf ~/openpod-tune-build && mkdir -p ~/openpod-tune-build && tar -x -C ~/openpod-tune-build && cd ~/openpod-tune-build/instalador && sh empacota-linux.sh'`,
  depois `scp lab-linux-ts:openpod-tune-build/instalador/dist/openpod-tune-linux-x86_64.tar.gz instalador/dist/`.
- Copie os três para `OpenPod/_local/publicar/instalador/`.
- **Pela GPL**, atualize o `zeroproj/openpod-installer` com uma cópia limpa: `git archive HEAD`, tire `docs/openpod`, `.opencode` e `.tmp`, renomeie o
  README do rockslop para `README-rockslop.md`, mantenha o README do Tune e rode `gitleaks`.

**Publicar (só com o "pode"):**
```
cd "/Users/zeroproj/Sistemas LWP/OpenPod" && python3 tools/publica_release.py --versao OpenPod-Reload-3.5 --nome-tela "Reload 3.5" \
  --com-flashloader --pacotes _local/publicar/pacotes --instalador _local/publicar/instalador --storepod _local/publicar/storepod --push
```
- Depois, **confira online**: o `curl` do `index.json` (o sha certo), o download dos pacotes (sha256) e os três instaladores (HTTP 200).
- O site é o `docs/index.html` (bilíngue PT/EN, abas, imagens embutidas). O `REFERENCIAS.md` público é o `docs/REFERENCIAS_PUBLICO.md`.

## 6. O processo das fichas
> O passo a passo atualizado, com os agentes do opencode, está em **`docs/COORDENACAO-AGENTES.md`** (ele vale mais que esta seção).
1. A coordenação escreve a ficha (OpenPod: `docs/tarefas/NNN-*.md`; Tune: `OpenPod-instalador/docs/openpod/NNN-*.md`). Ela tem o
   objetivo, o que provar, as regras e o sinal `PRONTO-NNN` / `ESCALADA-NNN`.
2. Despache num **terminal do Orca**:
   `orca terminal create --worktree "path:<worktree>" --title "OpenCode NNN" --command "cd <repo> && opencode run -m <modelo> \"$(cat prompt.txt)\""`.
   Para retomar a mesma sessão: `opencode run -s <session_id> -m <modelo> "…"`.
3. **Checagem de parado** (o opencode não avisa quando a cota acaba): compare o `max(time_created)` da tabela `part` em
   `~/.local/share/opencode/opencode.db` (só leitura) com o relógio. Se passar de 15 min, veja `"stream error"` em
   `~/.local/share/opencode/log/opencode.log`.
4. **Conferência da coordenação:**
   - testes;
   - firmware: compile 2 vezes (sha igual), ORIGINAL intacto e **desmontagem byte a byte de todo gancho**;
   - instalador: as regras de escrita, a assinatura e o que apaga.
   Escreva `NNN-conferencia.md` e devolva.
5. **Revisão** (Big Pickle), depois o **teste do decisor** (kit "Diag"), o **"pode"** e a **publicação**.
6. **Feche o terminal do Orca** quando a ficha acabar. O decisor pediu isso.

## 7. Lições que custaram caro
- **Ganchos no firmware:**
  - `bl` numa função **folha** destrói o LR (CRÍTICO na 028): use `b.w` para um trampolim que salva o LR;
  - frame de pilha byte a byte;
  - testes unicorn com a **função real** e um chamador real, nunca frame artificial.
- **O tipo 3 da view do player:** o índice do elemento fica em `msg+4`: 0 = contador da fila, 1 = título (028b).
  `[view+0]` é o contador e `[view+4]` é o título.
- **Dois núcleos:** a CPU1 (LVGL/home) **só lê memória**. Nada de kernel, FatFs ou banco a partir dela (025).
- **opencode:** recusa **qualquer** caminho "fora" do projeto, e isso o encerra:
  - `cd` para caminho absoluto com espaço;
  - `../`;
  - `/tmp`;
  - `~/.cargo`.
  Diga ao agente: "o diretório atual já é a raiz; use caminhos relativos". **Proíba `git stash`**, porque a pilha é compartilhada.
- **macOS:** o modo de download (`301a:2800`) exige root para tirar o driver de disco. O `osascript … with administrator privileges`
  **não serve**, mesmo com `launchctl asuser`, e dá **E216** no claim. O que funciona é o **`sudo` de verdade**: o Tune usa
  `sudo -A` com uma caixa de senha (askpass), numa chamada só, e se reabre como root (CONFIRMADO no aparelho).
- **Cartão:** E/S (E521) em sequência = sistema de arquivos corrompido. O caminho é o Primeiros Socorros ou a formatação em FAT32.
  O Tune desliga o Spotlight no cartão e ignora os `._*` do macOS.
- **egui:** sem `request_repaint_after`, a tela não atualiza com os eventos da thread do aparelho.
- **Rockbox YP3:** foi compilado **sem `HAVE_ALBUMART`**, então não mostra capa. A capa exige recompilar (planejado para a RockBox 1.3).
  Os plugins são compilados por aparelho, então só os da build YP3 servem. O JPEG progressivo nunca funciona.

## 8. Pendências (por ordem)
00. ~~Publicar o RockBox 5.3~~ — **feito** em 26/11/2026 (D50).
01. **Renumerar o OpenPod System: "Reload 3.5" → 5.3** (D51). Só a renumeração: as funções são as mesmas da 3.5.
    - **Nome na tela decidido: `OpenPod 5.3`** (o carimbo é gravado dentro do firmware, então não basta
      mudar o site). O texto novo cabe no mesmo endereço `0x1A4F00`, então o **ponteiro não muda**.
    - O que muda no firmware são **12 bytes** (medido): `0x1A4F00..0x1A4F0B`, só o texto do carimbo
      (`"Reload 3.5\0"` → `"OpenPod 5.3\0"`).
    - **FICHA 030 PRONTA** (`docs/tarefas/030-openpod-system-5-3.md`), com a conferência
      (`030-conferencia.md`) e a revisão **APROVADO COM RESSALVAS** (`030-revisao.md`). `sh tools/ci.sh` verde.
    - **Pronto, aguardando o teste do decisor:** imagem `firmware/WORKING/openpod_5_3_carimbado.bin`
      (sha `8551ea02…`), kit `release/OpenPod-5.3/` (`.up` sha `63520f82…`, CRC16 `0xD5DF`), pacote do Tune
      `openpod-system-5.3.tar.gz` (sha `612d015b…`, assinado) e o `index.json` com `system: 5.3`.
      O `.up` novo difere do `.up` publicado da 3.5 em **14 bytes**: os 12 do carimbo + os 2 do CRC16.
    - **Um ponto para o decisor:** o site renumerou também o `4.0 · previsto` para `5.5 · previsto`
      (o desenvolvedor marcou como PROVÁVEL; a revisão apontou como ressalva BAIXA). Manter o 5.5 ou
      voltar para 4.0?
    - **O decisor testa no aparelho antes. Publicar só com o "pode" dele.**
0. **Ficha 032, o Tune como plataforma** (`OpenPod-instalador/docs/openpod/032-tune-plataforma.md`): a especificação do decisor de 26/11, já conferida contra o código e dividida nas fases A–E. As decisões (a)–(d) da §2 **já estão decididas** (D45–D49). Começar pela **Fase A** (registros e manifestos).
    - **033 (os registros no cartão) — PRONTA e APROVADA.** `OpenPod-instalador/docs/openpod/033-registros-no-cartao.md`.
      - O registro do cartão: `.openpod/version.json` (System) e `.rockbox/openpod/version.json` (RockBox), com
        `sistema`, `versao`, `flash_sha256`, `estado` (`pendente`\|`instalado`), `anterior`, `data`.
      - **A ordem crítica virou barreira de tipo:** `conferir_flash` devolve a prova `FlashConferida`, e o passo do
        cartão **exige** a prova — não dá para gravar o registro sem a conferência da ROM.
      - 96 testes verdes; builds do macOS, do Windows e do Linux verdes; revisão **APROVADO** (`033-revisao2.md`).
      - **Pendências do decisor:** (a) o `flash_sha256` do System — recomendo o sha do payload do `.up` a partir de
        `0xE000` (mesmo conceito do segmento do RockBox); (b) o cartão do System **não** é acessível hoje (o
        `sdcard.rs` só acha o volume do RockBox), então o `.openpod/` fica para a Fase B.
      - **O `flash_sha256` que vai no MANIFEST (034) tem que ser o sha256 dos bytes do segmento em `0xE000`** — o
        mesmo que o `registro.rs` calcula. Se a 034 usar outra definição, a comparação da D46 quebra.
    - **034 (o manifesto v2 + a regra da D46) — PRONTA e APROVADA** (`034-revisao2.md`, APROVADO COM
      RESSALVAS, e a ressalva BAIXA foi corrigida). 110 testes; os três sistemas compilam.
      - **O ponto que mata o projeto se estiver errado, e foi conferido:** o `flash_sha256` do MANIFEST é
        **calculado** pelo gerador, e o gerador **recusa** um valor manual divergente (provado com o
        gerador de verdade: divergente → recusa, correto → aceita, sem opção → calculado). Sem isso, o
        pacote seria assinado com o sha errado e **todo mundo cairia no Recovery**.
    - **035 (o aviso de Tune novo) — PRONTA e APROVADA COM RESSALVAS** (`035-revisao.md`, nenhum
      CRÍTICO nem ALTO). 117 testes. O `tune/index.json` **assinado** no site; o Tune confere a
      assinatura, compara com a versão local e **avisa** (sem baixar nem instalar).
      - **O número público do Tune é `0.4.0`**, com o `Cargo.toml` como **fonte única** (o
        `Info.plist` do macOS tinha a versão escrita à mão; agora vem do `versao.sh`, que falha alto).
    - **A FASE A DA 032 ESTÁ COMPLETA** (D53). São 21 commits, do `32d0c85` ao `a81203c`.
      - **Um ponto de vida:** se o `flash_sha256` do MANIFEST divergir do que o Tune calcula, **todo
        mundo cai no Recovery**. Por isso o gerador **recusa** um `--flash-sha256` manual que não bate
        (o revisor achou o buraco; a coordenação provou que ele fechava, com o gerador de verdade).
      - **O `publica_release.py` agora publica o `tune/index.json`** (opção `--tune`) — sem isso o
        aviso nunca chegaria ao cliente.
      - **O site foi reformulado** (`tools/gera_site.py` → `docs/index_novo.html`): o Tune no centro, a
        home explicando **os três tipos** (System, RockBox, Tune), os **recursos divididos por linha**, e
        os **métodos manuais antigos** numa página *legacy* escondida do menu. **O site no ar não foi
        trocado** — isso é publicação.
    - **Compatibilidade com o Tune 0.4 já instalado: CONFIRMADO.** O parser do MANIFEST é genérico
      (`chave=valor`), então chave desconhecida não é erro; o `index.json` é lido com `serde_json::Value`. O
      **único** jeito de quebrar o 0.4 é **subir o `formato`** → a 034 tem que manter `formato=1`.
1. **StorePod:**
   - ampliar o `requer` para a versão do RockBox (`rockbox >= 1.2`), antes de pôr jogos e apps;
   - depois, os jogos e apps que **o decisor testar** no aparelho entram no catálogo um por um.
2. **Revisão externa da 028b** (3.5): só a conferência da coordenação foi feita. O decisor ainda não confirmou que o nome acompanha a
   troca de faixa na home.
3. **OpenPod RockBox 6.0 (mudança de firmware):** a capa do álbum, **com os mesmos limites do OpenPod System** (D49): JPEG comum (baseline) embutido no MP3; ideal de 300×300 a 500×500; aceita até 1000×1000 e 512 KB. Acima disso, JPEG progressivo ou PNG: mostra a nota e a música toca normal. Os limites ficam no **código do nosso Rockbox**, que confere antes de decodificar. Junto vem o `.rockbox/aparelho.json` (F2b). Recompilar o Rockbox YP3 com `HAVE_ALBUMART` (melhor no Linux) e publicar a fonte em
   `rockbox-gn438`.
4. **OpenPod 5.4** (10/01/2027, era a "3.6"): os jogos novos e o **bichinho virtual** (ficha 027, regras do ePet/MIT).
5. **3.4 = Ghidra** (o firmware todo desmontado; D21), no Linux.
6. **Mudança para o Linux:** `mudanca/empacota_mac.sh` e `instala_linux.sh` (D30).
7. Ficha 026 (a caixa-preta `crashlog.txt`).
8. A mensagem clara para erro de E/S do cartão na tela do Tune ("rode Primeiros Socorros ou formate").
9. Os testes de StorePod escrevem `janela.log` na casa real do usuário. Isso é inofensivo, mas dá para isolar.
