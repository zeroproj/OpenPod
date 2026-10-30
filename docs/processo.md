# Processo

## Como retomar
**Ponto de retomada (2026-10-30):** Reload 1.0 **RC6** publicada em
https://zeroproj.github.io/OpenPod/ (links fixos `atual/update.up` e
`atual/FlashloaderSL-DEV-6.9.5.exe`); página PT/EN genérica. Código-fonte só
no branch local `privado-completo`. Processo v1.8 (D06).

- **RC6 APROVADA no aparelho (2026-10-30)** e publicada; catraca em
  `tests/test_catraca.py` (sha `af3a2b6d…`).
- **Próximo:** RC7 (primeira ficha com **sessão por ficha**, `docs/prompts/sessao-da-ficha.md`) = capa do álbum de dentro do MP3 (análise em
  `docs/tarefas/003-rc5-analise-capa.md`, modelo aprovado 64×64; falta P10 —
  caminho da faixa atual no presenter `0xD08A90` — e os experimentos E1/E2).
  Depois: bateria prata/verde (refeita da fábrica).
- **Com o decisor:** experimento E1 da RC7 (foto grande em Fotos com música tocando); teste do fundo pálido (olhar a
  Tocando Agora de frente: se o preto também parecer azul, é a tela).
- **Pendências técnicas:**
  - [BAIXA 006] `fab_home_moldura.confere_resultado` não confere o `00` em
    `0x1A6448` (coberto pelo `test_c4_rotinas`).
  - Auditoria do toolchain (D06) ainda não rodada.
  - Créditos "NanoClone" no README do pacote: confirmar com o decisor se sai.
  - Remoto privado para o código (Fase 1) — decisão do decisor.
