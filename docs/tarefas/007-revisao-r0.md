REPROVADO
ANÁLISE 007 — MODO: FICHA — MODELO: glm-5.3 (opencode-go, D10/D12)

Escopo lido: `docs/tarefas/007-rc7-capa-album.md`, `tests/test_rc7.py`,
`tests/emu_rc7.py`, `tools/build.py` (MAPA/AREA_FIM), `tools/ci.sh`,
`docs/seguranca.md`. Cobertura geral boa: ganchos com premissa de fábrica e
alvo novo conferidos, catraca RC6 por sha, C5 byte a byte (RC6→RC7), nada
abaixo de 0xE000 / no 0xD000 / na PSMP, pixels exatos com o TJpgDec da
fábrica emulado (erro máximo 0), recusas com arquivo fechado, sem vazamento
e pico ≤ 0x1800, D6 recusando rc5/truncado/bytes trocados/link. Achados:

[MÉDIA] tests/test_rc7.py:349 (caso `frame_maior_que_tag`) — o laço de
quadros da ficha (docs/tarefas/007-rc7-capa-album.md:99-102) diz só "quadro
que passa do fim do tag → cinza"; nada impede implementar o avanço como
`ptr += 10 + tam` em u32 (com wrap) antes da checagem de fim. Cenário
concreto: MP3 corrompido/hostil com quadro v2.3 `APIC` de tamanho BE32
`0xFFFFFFF6` — `10 + 0xFFFFFFF6` faz wrap para 0 e o ponteiro volta ao
mesmo quadro para sempre; a ViewTask entra em laço infinito e a GUI congela
até reset. O caso atual (+5000, sem wrap) aceita tanto a implementação
segura (compara o tamanho com o resto do tag antes de avançar) quanto a que
laça; os 60 s do arnês só pegam o laço se o caso existir — e no aparelho
não há limite de tempo. O dano D4 da ficha ("laço infinito") está declarado,
mas o caso que o dispara não está nos testes. Correção: casos novos no
`test_d3_recusas` — quadro v2.3 com tamanho BE32 `0xFFFFFFF6` e quadro v2.4
com tamanho synchsafe com byte ≥ `0x80` (a ficha também não define o
tratamento do synchsafe inválido no tamanho do QUADRO, só no do tag).

[BAIXA] docs/tarefas/007-rc7-capa-album.md:39 (A15, "pilha suficiente:
PROVÁVEL") — o arnês (tests/emu_rc7.py:281-293) chama as rotinas com 64 KiB
de pilha e confere só o equilíbrio do SP, nunca a descida. Se o código novo
(buf de caminho 256 B + FIL 0x25C + aninhamento com o TJpgDec da fábrica)
descer mais que a folga da ViewTask (0x1000), o aparelho reinicia ao abrir
a Tocando Agora com capa. O E1 no aparelho dá evidência parcial (o TJpgDec
já roda lá com música tocando), mas a premissa segue sem prova e sem risco
aceito correspondente. Sugestão: o arnês medir o menor SP durante
CRIA/TITULO e impor teto.

[BAIXA] tests/emu_rc7.py:41,73 — o arnês vige EXECUÇÃO fora do permitido,
mas a RAM do aparelho (0x800000, 0x40000) é mapeada sem vigia de escrita:
o dano D11 (colisão com o visualizador de fotos, global 0x81CDE8) fica
coberto só pelo contrato e pela revisão do diff — uma escrita direta nova
no global passaria nos testes e corromperia o contexto do visualizador de
fotos com música tocando. Sugestão: guardar 0x81CDE8..0x81CDE8+0x4180 e
conferir intacto após cada chamada.

Teste sugerido (regressão): `test_d3_recusas` com quadro v2.3 de tamanho
`0xFFFFFFF6` e quadro v2.4 synchsafe com byte ≥ `0x80` — ambos têm de virar
quadrado cinza SEM laço (volta dentro do limite de tempo); linha nova em
`docs/seguranca.md`: "tamanho de quadro ≥ 0x80000000 (ou synchsafe inválido)
é recusado antes de qualquer avanço de ponteiro (007-R0)".

Observação (sem severidade): o critério D2 "v2.3 grande (BE32 com byte ≥
0x80)" é exercitado com `capa_b_500.jpg` (~29 KiB → bytes do tamanho
`00 00 74 xx`, sem byte ≥ 0x80). O efeito (BE32 decodificado como
synchsafe dá outro tamanho e os pixels não batem) continua coberto, mas o
texto da ficha e o ativo não correspondem literalmente.

## Pergunta ao decisor
O achado [MÉDIA] pede caso novo em `tests/test_rc7.py` (protegido) e linha
em `docs/seguranca.md` — pelo processo e pela própria ficha (item 1 de
"Para a sessão glm-5.3"), teste protegido só entra pelo arquiteto, e a
sessão não pode alterar ficha nem testes. Como seguir?
A) o arquiteto (Claude, Fases A/B) acrescenta os casos hostis ao
`test_d3_recusas` e a linha em `docs/seguranca.md` (e, se quiser, as duas
BAIXAS), a ficha registra a rodada, e a sessão retoma a Fase D com o
desenvolvedor MiniMax;
B) aceitar o risco (laço infinito só com MP3 corrompido/hostil construído
à mão; o desenho da ficha, bem implementado, recusa antes de avançar) e
seguir para a Fase D sem o teste, registrando a aceitação na ficha.
