APROVADO
ANÁLISE 007 — MODO: FINAL — MODELO: glm-5.3 (opencode-go, D12)

Escopo: só o diff desde a 1ª análise (6fe71e2..5cec8c8) — tools/capa_album.s
(+74/-18), tools/capa_album_asm.py (+29), docs/tarefas/007-rc7-capa-album.md
(Rodada 2, sha novo, medições). Nada mais mudou (testes protegidos, ci.sh,
ORIGINAL e os demais arquivos conferidos por hash no ci.sh, que a sessão
rodou de novo: verde, e o build manual reproduz sha
3af97713c9d8e28c2b36b872fd5883d18af9e65bff443c5e99ab645678237d9e).

- [MÉDIA do diff, fechada] os 4 `udiv` saíram; a `div_soft` nova é a divisão
  longa binária correta: 32 passos, quociente em r2, resto em r3, o carry do
  `lsls r0` vai para o `adcs r3` sem instrução no meio; a invariante
  "resto < divisor antes de dobrar" segura os 32 bits (dividendos < 2^23,
  divisores W/H ≥ 64); `blo`/`sub`/`orr` certos e o `bne` usa as flags do
  `subs` seguinte. r4 preservado (push/pop {r4, lr}); r0/r2 destruídos e
  r1/r3 saem como divisor/resto — o chamador `saida` recarrega W/H da pilha
  a cada fórmula e r2/r3 são scratch dali em diante. Os `bl div_soft` têm
  os argumentos certos nas quatro fórmulas (r0 = dividendo, r1 = W ou H).
- A trava permanente mora na ferramenta: `tem_divisao_hardware` varre o
  `.text` montado por meia-palavra e o `confere_codigo` recusa a receita
  (sem criar saída) com `sdiv` (0xFB90..0xFB9F) ou `udiv` (0xFBB0..0xFBBF) —
  encodings T32 corretos; verificação estática de propósito (o QEMU executa
  divisão em qualquer ARMv7, a dinâmica não discriminaria).
- [BAIXA do diff, fechada] o id do quadro agora confere os 4 bytes
  ('A','P','I','C'); "ZPIC" hostil → cinza.
- Ficha: Rodada 2 completa (o que mudou, por quê, sha novo, pilha remedida
  392 B de 0x1000, pico 4500 B de 0x1800). Imagem: só os bytes permitidos
  (RC6→RC7: 10711 B, 0x131E80..0x1AA9D7; nada abaixo de 0xE000, setor
  0xD000 e PSMP intocados — reconferido contra o ORIGINAL pela sessão).

Pendência para o arquiteto (fora deste diff, registrado na ficha): teste de
regressão permanente da ausência de udiv/sdiv e do id "APIC" inteiro é
protegido (test_rc7.py) — a trava da ferramenta cobre o build, o teste
cobriria quem reescrever a ferramenta.

Sem achados. APROVADO.
