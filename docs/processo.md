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
  segue de referência. **Ficha 009 entregue** (`docs/tarefas/009-analise.md`, MiniMax com conferência da coordenação): fault e MainTask parada reiniciam; causa principal é HIPÓTESE (ring da view). Diag B0 **toca** no aparelho. **Ficha 010 entregue:** a ViewTask é monitorada pelo watchdog e o ring tem 15360 B (`docs/tarefas/010-analise.md`, D1 a D4). **Diag B2 no aparelho:** congela ~15 s e reinicia (D5). **Ficha 011 entregue** (DeepSeek grátis; revisões GLM Flash grátis e Nemotron/NVIDIA; conferência da coordenação): Diag B3 lê o caminho do rótulo 2 em vez de chamar o `get_path` na ViewTask, sem o quadrado se o caminho for válido. **Diag B3 no aparelho: toca sem travar, com o cinza** (o rótulo 2 não traz caminho `0:/`; ver 011-analise, resultado). **Ficha 012 entregue** (DeepSeek grátis; revisão GLM Flash grátis REPROVOU a guarda do lr par, corrigida; conferência da coordenação pegou os destinos `bx/blx` sem bit Thumb, também corrigidos): Diag B4 envia o caminho da rajada numa mensagem da fábrica (classe 3, tipo 5) e a view decide o quadrado; a ordem título/caminho deixou de importar. **Diag B4 no aparelho: toca, troca de faixa, para, sai e entra sem travar; o cinza vira "No data"** (o caminho chegou válido; `release/OpenPod-Reload-1.0-RC7-Diag-B4`, `.up` 16c4cf05…). **Ficha 013 entregue** (DeepSeek grátis; revisão GLM grátis APROVADO com 2 BAIXA; a coordenação pegou os kits do cabo com base errada, regerados com a base ORIGINAL). Correção da 012: a rajada roda na **PreTask**, o `label_process` na ViewTask. **B5b e B5a no aparelho: os dois travam e reiniciam** — abrir arquivo na ViewTask trava (013-analise, resultados). **Ficha 014 entregue** (DeepSeek grátis; GLM APROVADO; a coordenação pegou o tipo 6 barrado em 0xD3223E, o retorno do envio e o 0xD0D880). **Diag B6b no aparelho: A CAPA APARECEU** — com uma engasgada curta no áudio no início de cada música. **Ficha 015 em andamento** (DeepSeek grátis): B7a decodifica menor (1/8), B7b soma pausas. A conferir: a 012-analise diz que a rajada roda na ViewTask (PROVÁVEL até a coordenação confirmar); se for, a causa do reinício do B não é só "get_path na ViewTask". B1 fica de reserva.
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
