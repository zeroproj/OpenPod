REPROVADO
ANÁLISE 007 — MODO: DIFF — MODELO: glm-5.3 (opencode-go, D12)

Escopo: `git diff privado-completo...HEAD` (três pontos), foco no commit do
desenvolvedor 6fe71e2 (tools/fab_capa_album.py 322 l., tools/capa_album_asm.py
162 l., tools/capa_album.s 1138 l., tools/build.py +42, ficha Entrega/Rodadas).
Verificado contra a ficha item a item: premissas todas conferidas ANTES de
escrever e sem criar saída ao falhar (sha RC6, `movs` de fábrica, ganchos
decodificados de volta, lote virgem, TJpgDec intacto, placeholder por sha);
`PERMITIDO` = exatamente os bytes da ficha (0x131E80/82, 0x131E9E/A0,
0x131EB6/BA, 0x13225E/62, lote 0x1A8000..0x1AB000), nada abaixo de 0xE000,
setor 0xD000 e PSMP conferidos; `--out` igual/symlink/hardlink recusado;
MAPA/AREA_FIM sem cruzar o lote anterior (fab_home_moldura termina 0x1A6480);
regra do R0 IMPLEMENTADA no laço de quadros (tamanho comparado com o resto da
tag antes de avançar; v2.4 synchsafe do quadro recusado com byte ≥ 0x80 —
capa_album.s:834-845, 857-860); cabeçalho estendido v2.3/v2.4 correto; corpo
do APIC nunca lê além do quadro (todo le_n precedido de conferência);
varre_marcadores limita todo salto ao fim do quadro; r4..r11 preservados e
pilha balanceada/alinhada em todas as rotinas; CRIA devolve o fundo e trata
sem-memória/sem-objeto como a ficha; TITULO faz set_text primeiro e uma vez
só (o b.w de fábrica é tail call — o pop volta a quem chamou o
label_process); APAGA conferindo [view+0x30]==ext antes de zerar; f_lseek com
o offset de 64 bits em r2:r3 (r1 ignorado, coerente com A13 e com o stub);
saída com fórmulas exatas de teto/chão e bytes trocados. Origem: nenhuma
ferramenta Core/Alphas; testes protegidos, ci.sh e ORIGINAL intocados no
commit do desenvolvedor. Achados:

[MÉDIA] tools/capa_album.s:593,600,609,616 — a reescala usa `udiv`
(divisão por hardware) 4 vezes, e NADA evidencia que o núcleo do SL6801
implementa UDIV/SDIV: (a) zero ocorrências de udiv/sdiv (e clz) em todo o
código de fábrica visível (0xC00000..0xDA0000, 1,75 MiB, varredura capstone)
— um SDK compilado para um núcleo com divisão as usaria em algum lugar; (b)
a ROM baixa (0x0..0x10000, onde mora a libc do chip — o `free` de 0xCF7884
desvia para lá) não está no dump, impossível inspecionar; (c) não há
documentação pública do SoC (Shenju/YP3, sem SDK vazado); (d) divisão por
hardware é OPCIONAL no ARMv7-M (Cortex-M3 licenciado sem ela é comum em
SoC de player barato). O arnês não pega: o unicorn/QEMU (mesmo setup do
emu_rc7.py) executa UDIV em qualquer ARMv7 — provado ao rodar `udiv` no
setup do emulador (100/7 = 14), então o verde do test_rc7 não diz nada
sobre o aparelho. Cenário concreto: o decisor grava a RC7, toca
`01_capa_v23.mp3` → TITULO → carrega_capa → jd_decomp → saida() executa
`udiv` → se o núcleo não tiver a instrução, UsageFault→HardFault e a
Tocando Agora reinicia ao tocar QUALQUER MP3 com capa (o dano D1 da ficha,
fora dos testes). Correção: dividir por software (laço
shift-subtract; os dividendos aqui são < 2^22 e os divisores são W/H ≥ 64,
sem risco de overflow) — custo desprezível: 4 divisões por retângulo do
TJpgDec; e nenhuma instrução de divisão por hardware no código novo.

[BAIXA] tools/capa_album.s:817-872 — o id do quadro é conferido só em
"não começa com 00" + 'P','I','C' (bytes 1..3); o byte 0 (que deveria ser
'A' de APIC) não é conferido. Um MP3 hostil com quadro "ZPIC" cujo corpo
por acaso parseia como imagem é tratado como capa (a ficha: "Só o 1º
APIC conta") → mostra imagem que não é capa. Sem travar, sem ler fora —
dano cosmético. Correção: conferir id[0] == 0x41 ('A').

Teste sugerido (regressão, para o arquiteto — test_rc7.py é protegido):
varredura estática do código montado do lote recusando qualquer instrução
de divisão por hardware (encodings udiv/sdiv) — o arnês de emulação não
discrimina (o QEMU implementa divisão em todo ARMv7); conferir também
id[0] == 'A' no quadro APIC (MP3 hostil "ZPIC" → cinza).

Linha nova em docs/seguranca.md (adicionada pela sessão): "código novo não
usa instrução cuja presença no núcleo não foi evidenciada no firmware de
fábrica — divisão por hardware udiv/sdiv tem ZERO ocorrências na flash
inteira; dividir por software (achado 007-D1, MÉDIA)".

Observação (sem severidade): o varre_marcadores exige 0xFF depois de um
filler 0xFF (capa_album.s:1056-1057), então um JPEG legítimo com fillers
duplos antes do SOF vira cinza — conservador e sem dano; JPEGs reais de
encoder não emitem FF FF aí.

Veredito: REPROVADO — correção R1 (udiv → divisão por software; id[0]
== 'A'), depois conferência final só do diff da correção.
