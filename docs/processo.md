# Processo

## Como retomar
**Ponto de retomada (2026-10-30):** Reload 1.0 **RC6** publicada em
https://zeroproj.github.io/OpenPod/ (links fixos `atual/update.up` e
`atual/FlashloaderSL-DEV-6.9.5.exe`); página PT/EN genérica. Código-fonte só
no branch local `privado-completo`. Processo v1.8 (D06).

- **RC6 APROVADA no aparelho (2026-10-30)** e publicada; catraca em
  `tests/test_catraca.py` (sha `af3a2b6d…`).
- **Em andamento:** RC7 (ficha 007) no worktree `tarefa-007-rc7-capa`: sessão Claude "CL | Tarefa 007" nas
  Fases A/B até `FASEB-007`; depois sessão GLM 5.3 (D10/D11, `docs/prompts/sessao-da-ficha-glm.md`).
- **RC7** = capa do álbum de dentro do MP3 (análise em
  `docs/tarefas/003-rc5-analise-capa.md`, modelo aprovado 64×64; **E1 e E2 feitos — memória OK**;
  falta P10 — caminho da faixa atual no presenter `0xD08A90` — e os pontos de gancho).
  Depois: bateria prata/verde (refeita da fábrica).
- **Com o decisor:** teste do fundo pálido (olhar a
  Tocando Agora de frente: se o preto também parecer azul, é a tela).
- **Pendências técnicas:**
  - [BAIXA 006] `fab_home_moldura.confere_resultado` não confere o `00` em
    `0x1A6448` (coberto pelo `test_c4_rotinas`).
  - Auditoria do toolchain (D06) ainda não rodada.
  - Créditos "NanoClone" no README do pacote: confirmar com o decisor se sai.
  - Remoto privado para o código (Fase 1) — decisão do decisor.
