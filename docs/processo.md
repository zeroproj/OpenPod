# Processo

## Como retomar
**Ponto de retomada (2026-10-30):** Reload 1.0 **RC6** publicada em
https://zeroproj.github.io/OpenPod/ (links fixos `atual/update.up` e
`atual/FlashloaderSL-DEV-6.9.5.exe`); página PT/EN genérica. Código-fonte só
no branch local `privado-completo`. Processo v1.8 (D06).

- **Em andamento:** RC6 (ficha 006) — kit gerado e publicado, **aguarda a foto do
  decisor** com a home gravada (moldura nas 4 direções, abrir/voltar).
  Aprovada → catraca do sha `af3a2b6d…` num `test_rc7.py`, métricas.
- **Próximo:** RC7 = capa do álbum de dentro do MP3 (análise em
  `docs/tarefas/003-rc5-analise-capa.md`, modelo aprovado 64×64; falta P10 —
  caminho da faixa atual no presenter `0xD08A90` — e os experimentos E1/E2).
  Depois: bateria prata/verde (refeita da fábrica).
- **Com o decisor:** gravar a RC6 e mandar foto; teste do fundo pálido (olhar a
  Tocando Agora de frente: se o preto também parecer azul, é a tela).
- **Pendências técnicas:**
  - [BAIXA 006] `fab_home_moldura.confere_resultado` não confere o `00` em
    `0x1A6448` (coberto pelo `test_c4_rotinas`).
  - Seção `## Pacote` da ficha 006 e custo nas métricas, quando a RC6 for aprovada.
  - Auditoria do toolchain (D06) ainda não rodada.
  - Créditos "NanoClone" no README do pacote: confirmar com o decisor se sai.
  - Worktrees e branches `tarefa-002/004/005/006` a apagar depois da aprovação da RC6.
  - Remoto privado para o código (Fase 1) — decisão do decisor.
