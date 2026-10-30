# Processo

## Como retomar
**Ponto de retomada (2026-10-30):** Reload 1.0 **RC6** publicada em
https://zeroproj.github.io/OpenPod/ (links fixos `atual/update.up` e
`atual/FlashloaderSL-DEV-6.9.5.exe`); página PT/EN genérica. Código-fonte só
no branch local `privado-completo`. Processo v1.8 (D06).

- **RC6 APROVADA no aparelho (2026-10-30)** e publicada; catraca em
  `tests/test_catraca.py` (sha `af3a2b6d…`).
- **Em andamento:** RC7 (ficha 007, capa do álbum): Fases A/B feitas pelo Claude (ficha
  `docs/tarefas/007-rc7-capa-album.md`, `tests/test_rc7.py` + `tests/emu_rc7.py` vermelhos e
  protegidos, MP3 de teste em `tests/assets/rc7/`); **Fases C/D com glm-5.3 no OpenCode (D10/D12)**,
  terminal "GLM | Tarefa 007", pedido `docs/prompts/sessao-da-ficha-glm.md`; GLM substitui o Codex.
  Depois: bateria prata/verde (refeita da fábrica).
- **Com o decisor:** teste do fundo pálido (olhar a
  Tocando Agora de frente: se o preto também parecer azul, é a tela).
- **Pendências técnicas:**
  - [BAIXA 006] `fab_home_moldura.confere_resultado` não confere o `00` em
    `0x1A6448` (coberto pelo `test_c4_rotinas`).
  - Auditoria do toolchain (D06) ainda não rodada.
  - Créditos "NanoClone" no README do pacote: confirmar com o decisor se sai.
  - Remoto privado para o código (Fase 1) — decisão do decisor.
