# Processo

## Como retomar
**Ponto de retomada (2026-10-30):** Reload 1.0 **RC6** publicada em
https://zeroproj.github.io/OpenPod/ (links fixos `atual/update.up` e
`atual/FlashloaderSL-DEV-6.9.5.exe`); página PT/EN genérica. Código-fonte só
no branch local `privado-completo`. Processo v1.8 (D06).

- **RC6 APROVADA no aparelho (2026-10-30)** e publicada; catraca em
  `tests/test_catraca.py` (sha `af3a2b6d…`).
- **Ficha 008 (RC7 trava ao tocar) — resultado no aparelho (2026-11-05):** A tocou; B reiniciou; C não
  gravada. O defeito está na rotina TITULO ou no `get_path` chamado por ela (ver fim da ficha 008). RC6
  segue de referência. **Ficha 009 entregue** (`docs/tarefas/009-analise.md`, MiniMax com conferência da coordenação): fault e MainTask parada reiniciam; causa principal é HIPÓTESE (ring da view). Diag B0 **toca** no aparelho. **Ficha 010 entregue:** a ViewTask é monitorada pelo watchdog e o ring tem 15360 B (`docs/tarefas/010-analise.md`, D1 a D4). **Diag B2 no aparelho:** congela ~15 s e reinicia (D5). **Ficha 011 entregue** (DeepSeek grátis; revisões GLM Flash grátis e Nemotron/NVIDIA; conferência da coordenação): Diag B3 lê o caminho do rótulo 2 em vez de chamar o `get_path` na ViewTask, sem o quadrado se o caminho for válido. **Diag B3 no aparelho: toca sem travar, com o cinza** (o rótulo 2 não traz caminho `0:/`; ver 011-analise, resultado). **Ficha 012 entregue** (DeepSeek grátis; revisão GLM Flash grátis REPROVOU a guarda do lr par, corrigida; conferência da coordenação pegou os destinos `bx/blx` sem bit Thumb, também corrigidos): Diag B4 envia o caminho da rajada numa mensagem da fábrica (classe 3, tipo 5) e a view decide o quadrado; a ordem título/caminho deixou de importar. **Diag B4 no aparelho: toca, troca de faixa, para, sai e entra sem travar; o cinza vira "No data"** (o caminho chegou válido; `release/OpenPod-Reload-1.0-RC7-Diag-B4`, `.up` 16c4cf05…). **Ficha 013 entregue** (DeepSeek grátis; revisão GLM grátis APROVADO com 2 BAIXA; a coordenação pegou os kits do cabo com base errada, regerados com a base ORIGINAL). Correção da 012: a rajada roda na **PreTask**, o `label_process` na ViewTask. **B5b e B5a no aparelho: os dois travam e reiniciam** — abrir arquivo na ViewTask trava (013-analise, resultados). **Ficha 014 entregue** (DeepSeek grátis; GLM APROVADO; a coordenação pegou o tipo 6 barrado em 0xD3223E, o retorno do envio e o 0xD0D880). **Diag B6b no aparelho: A CAPA APARECEU** — com uma engasgada curta no áudio no início de cada música. **Ficha 015 entregue** (DeepSeek grátis; GLM APROVADO). **Diag B7b no aparelho: capa aparece rápido, sem engasgar a música** (`release/OpenPod-Reload-1.0-RC7-Diag-B7b`, `.up` bd14f18e…, CRC 0xEAC9). **Ficha 016 entregue** (DeepSeek grátis): **OpenPod Reload 2.0** = o B7b byte a byte + carimbo, kit `release/OpenPod-Reload-2.0/` no formato da RC6, roteiro de regressão completo (`docs/tarefas/016-analise.md`). **Aguardando o teste do decisor; não publicar.** A conferir: a 012-analise diz que a rajada roda na ViewTask (PROVÁVEL até a coordenação confirmar); se for, a causa do reinício do B não é só "get_path na ViewTask". B1 fica de reserva. **Publicada em 2026-11-12** com o "pode" do decisor ("Pode aprovar.. e ja atualizar o git"): README sem "Beta"; branch órfão `publico` → `origin/main` (`0187730`), só kit, página e `atual/`. O roteiro de regressão completo do TESTAR ainda não foi feito. Pendências: crédito NanoClone no README (manter ou tirar); ícones grafite na 2.1 (D13).
- **RC7 REPROVADA no aparelho (trava ao tocar, 2026-11-01; ver ficha 008):** ficha 007 (capa do álbum) fechada pela
  sessão GLM (PRONTO-007; R0 opção A, 1ª análise REPROVADO udiv + id APIC → R1 div_soft,
  conferência final APROVADO). Merge no privado-completo; regressão protegida
  `tests/test_rc7_trava.py` (sem UDIV/SDIV no lote; id do quadro inteiro). Imagem `3af97713…`,
  carimbada `a184dd07…`, `.up` `bd3c3640…` CRC 0x82C0, kit `release/OpenPod-Reload-1.0-RC7`
  (TESTAR.txt). Não publicar.
  Depois: bateria prata/verde (refeita da fábrica).
- **Com o decisor:** teste do fundo pálido (olhar a
  Tocando Agora de frente: se o preto também parecer azul, é a tela).
- **Decisão do decisor (2026-11-07), fluxo em teste a partir da ficha 011; se não ficar bom, voltamos ao anterior:**
  Claude escreve a ficha → `opencode/deepseek-v4.1-flash-free` faz a análise e o código → `opencode/glm-5.3-flash-free`
  faz a primeira revisão → `minimax/MiniMax-M3` revisa só o principal, e só quando a ficha gera versão para gravar (limite de
  US$ 3 por revisão) → Claude confere no firmware ORIGINAL → o decisor grava e testa. Reservas: MiniMax M3 refaz se o DeepSeek
  vier fraco; GLM-5.3 do plano Go quando houver cota. Privacidade não restringe a escolha de modelo (decisor, 2026-11-09: "openpod vai ser liberado"); o push de código para o repo público continua dependendo do "pode" do decisor.
- **Pendências técnicas:**
  - [BAIXA 006] `fab_home_moldura.confere_resultado` não confere o `00` em
    `0x1A6448` (coberto pelo `test_c4_rotinas`).
  - Auditoria do toolchain (D06) ainda não rodada.
  - Créditos "NanoClone" no README do pacote: confirmar com o decisor se sai.
  - Remoto privado para o código (Fase 1) — decisão do decisor.

**2026-11-14:** limpeza do projeto (arquivo em `../OpenPod-arquivo-2026-11-14/`); código no privado `zeroproj/OpenPod-dev`; branch `privado-completo` apagado do público. **Ficha 017 entregue e Reload 2.1 publicada (2026-11-15)** com o "pode" do decisor: 2.0 + ícones grafite; só a folha da home muda (9739 B em `0x0CDDA0..0x0D2BCD`); público `origin/main` `956c6ef`.

**2026-11-15 — retorno de usuário no Reddit (pendente, decisor: "ainda não, depois eu falo"):**
- **Relato:** GN-408 (mesmo SL6801, flash ID 85148514), Reload 2.x gravada inteira pelo Flashloader. **Reinicia ao tocar música com capa.** A "1.0" antiga funcionou.
- **Causa: HIPÓTESE.** Pode ser hardware do GN-408 ou um tipo de capa que nunca testamos. No segundo caso, o GN-438 também reiniciaria.
- **Propostas, em espera:**
  - pedir ao usuário um MP3 que reinicia;
  - o decisor testar a 2.1 com músicas reais;
  - gerar uma "2.1 sem capa" (RC6 + grafite);
  - aviso no README público.
- **Atualização (decisor, 2026-11-15):** "eu tenho 300 músicas, eu nunca tive problemas".
  - No GN-438, com a 2.x e a biblioteca real dele, a capa nunca reiniciou.
  - **PROVÁVEL:** o reinício é específico do GN-408 (hardware) ou das músicas daquele usuário, e não um bug geral.
  - Próximo: o MP3 ou o `.up` do usuário do GN-408. A ficha 019 (estresse da capa no emulador) fica como opcional.

**Reload 2.2 publicada (2026-11-15)** com o "pode mandar a 2.2" do decisor: ícones escuros com símbolos coloridos (D14). Só a folha da home muda em relação à 2.1 (9665 B). Kit `release/OpenPod-Reload-2.2` (`.up` CRC 0x7147).

**2026-11-15 — segundo relato do GN-408 (usuário do Reddit):**
- **Ambiente:** 208 MP3 320 kbps do **SpotiFLAC**, que embute a capa sozinho; SD SanDisk Extreme 64 GB.
- **Sintomas na 2.0:**
  - o play começa **7–8 s depois**;
  - na **troca de faixa trava e desliga**, em geral depois que a capa carrega.
- A **ROM de fábrica do 438 roda perfeita no 408** e a RC6 ("v1.0") também. O hardware é praticamente o mesmo.
- **HIPÓTESE forte (coordenação):** **capas grandes** (SpotiFLAC costuma embutir a capa em alta resolução, centenas de KB a MB).
  - O TJpgDec decodifica o Huffman da imagem inteira mesmo em 1/8, e isso leva segundos na PreTask, que segura o fluxo do play.
  - O travamento na troca pode ser a fila da view cheia ou trabalho sobreposto.
  - As 300 músicas do decisor provavelmente têm capas pequenas.
- **Teste para o decisor:** 5 MP3 com capa de 640/1000/1500/2000/3000 px (baseline, q95, 173 KB a 3,1 MB), entregues em zip.
- **Teste do decisor (2.2, GN-438, 2026-11-15)**, MP3 com capa baseline q95 4:4:4:
  - 640 px (173 KB) e 1000 px (392 KB) tocam, mas **o contador de tempo engasga** enquanto a capa carrega;
  - **1500 px (842 KB) trava tudo.**
  - **Hipótese das capas grandes CONFIRMADA no aparelho.** Ficha 019 (2.2.1) com `LIMITE_PX = 1000` e `LIMITE_BYTES = 512 KiB`.

**Reload 2.2.1 publicada (2026-11-16)** com o "pode" do decisor: limite de capa de 1000 px / 512 KiB (58 B a mais que a 2.2). Público `origin/main` `a0c60f0`. O crédito NanoClone saiu também do modelo `docs/pacote/README.md`.

**2026-11-16 — retorno dos usuários:** decisor: "o pessoal testou e tá funcionando". A **2.2.1 funciona** com os aparelhos dos usuários (GN-408 incluído). O limite de capa resolveu o travamento das capas grandes.
- **Feito em 2026-11-16 (decisor: "pode trocar no site"):** trocar o GN-408 de "Em teste" para "Testado por usuários" no site e nos READMEs, quando o decisor pedir.

**Reload 3.0 publicada (2026-11-17)** com o "pode publicar" do decisor: o menu Apps (ícone 5 → página 0x53, rótulo id 159 "Aplicativos", glifo de 4 quadrados verdes), com Despertador, Imagem e Dicionário. 463 B a mais que a 2.2.1. O site mostra a tela inicial da 3.0 e "Menu Aplicativos" nas novidades; a linha de versão foi atualizada pela ferramenta. **Próximo:** os jogos do SDK do SL6801_player (D15) dentro do Apps; a galeria de telas no site espera a foto da Tocando Agora com capa.
- **Relógio (2026-11-17):** o decisor testou no GN-438, que não tem chave liga/desliga: desligou e religou e a hora ficou certa ("acho que eu tava errado"). **Sem defeito de relógio**; a ficha de diagnóstico do relógio não é necessária.
- **Pendências para uma ficha 3.x futura** (decisor: "quando chegarmos nela, fazemos o teste"):
  - **(a) Vídeo espelhado:** gerar um `.avi` de teste com uma seta assimétrica e tocar no GN-438. Se espelhar, corrigir no blit do player (020 §3) e incluir no site.
  - **(b) exFAT:** confirmar que cartões de 64 GB+ em exFAT funcionam no GN-438 e pôr no site.

**3.1b no aparelho (decisor, 2026-11-18):** os apps funcionam, os controles respondem e **a música tocando não atrapalhou** os jogos. Defeito: **o Mp3tris não gira a peça**, porque o GN-438 não tem a tecla "cima" (`0x11`). Mapa de teclas medido em `docs/BUTTON_ANALYSIS.md`: M `0xA0`/`0xA2`, VOL/Sair `0x81`, ⏭ `0x13`/`0x89`, ⏮ `0x14`/`0x87`, Play/Pause `0x0A`. Revisão do Big Pickle: APROVADO. A do MiMo esperava o limite grátis.

**Ponto de retomada (2026-11-18):** a ficha 024 (Reload 3.2) está no worktree `tarefa-024` (terminal `deepseek-024`). O DeepSeek grátis bateu o limite e volta sozinho quando ele renovar. Depois: conferência da coordenação no ORIGINAL, revisão (Big Pickle), teste do decisor e publicação da 3.2, com o site atualizado (3.2 na lista; "previsto para dezembro": 3.3 jogos novos e 4.0). Também espera: a revisão do MiMo (teste de revisores, worktree `rev-mimo-022`).

