# Processo

## Como retomar
**Ponto de retomada (2026-10-30):** Reload 1.0 **RC6** publicada em
https://zeroproj.github.io/OpenPod/ (links fixos `atual/update.up` e
`atual/FlashloaderSL-DEV-6.9.5.exe`); página PT/EN genérica. Código-fonte só
no branch local `privado-completo`. Processo v1.8 (D06).

- **RC6 APROVADA no aparelho (2026-10-30)** e publicada; catraca em
  `tests/test_catraca.py` (sha `af3a2b6d…`).
- **RC7 PRONTA, aguardando o aparelho (2026-10-31):** ficha 007 (capa do álbum) fechada pela
  sessão GLM (PRONTO-007; R0 opção A, 1ª análise REPROVADO udiv + id APIC → R1 div_soft,
  conferência final APROVADO). Merge no privado-completo; regressão protegida
  `tests/test_rc7_trava.py` (sem UDIV/SDIV no lote; id do quadro inteiro). Imagem `3af97713…`,
  carimbada `a184dd07…`, `.up` `bd3c3640…` CRC 0x82C0, kit `release/OpenPod-Reload-1.0-RC7`
  (TESTAR.txt). Aprovada no aparelho → catraca com a RC7 e publicar com o "pode".
  Depois: bateria prata/verde (refeita da fábrica).
- **Com o decisor:** teste do fundo pálido (olhar a
  Tocando Agora de frente: se o preto também parecer azul, é a tela).
- **Pendências técnicas:**
  - [BAIXA 006] `fab_home_moldura.confere_resultado` não confere o `00` em
    `0x1A6448` (coberto pelo `test_c4_rotinas`).
  - Auditoria do toolchain (D06) ainda não rodada.
  - Créditos "NanoClone" no README do pacote: confirmar com o decisor se sai.
  - Remoto privado para o código (Fase 1) — decisão do decisor.
