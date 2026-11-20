REPROVADO

Ficha 025 — Reload 3.3 (pular rápido). Branch `limtistech/tarefa-025`, HEAD `3ddfe86`, diff `6ea6c72..HEAD`. Revisão somente leitura; único arquivo escrito: este.

Achados

CRÍTICO — `tools/fab_reload_3_3_guardas.py:141-145` (`add sp, #4; pop {r4-r6, pc}` em `0xDAAF42`/`0xDAAF48`) — `CONFIRMADO`.
O gancho em `0xDAAE30` chama a guarda por `bl`; quem chamou os wrappers `0xDAAE00`/`0xDAAE20` deixou na pilha exatamente 16 B (`push {r4,r5,r6,lr}`, `tools/diag_b7.s:38,48,57-64`). Não há palavra extra: o `lr` salvo está em `SP+12`. Com `SP=0x30000800`, frame `[0xAAAAAAAA,0xBBBBBBBB,0xCCCCCCCC,0x12345679]`, `r4=jd`, `r0=1`, a guarda devolve `PC=0x0` (ou `0xAAAAAAAA` no caminho completo desde `0xDAAE00`), `SP=0x30000814`, `r4=0xBBBBBBBB`, `r5=0xCCCCCCCC`, `r6=0x12345679`. A imagem 3.2, com o mesmo frame, restaura `SP=0x30000800`. Cenário: no primeiro `yield` do `jd_decomp`, o callback B7b salta para lixo e deixa a pilha desbalanceada — a capa não termina e a PreTask morre/reinicia, mesmo sem o usuário ter pulado. `tests/test_reload_3_3.py:244-250` monta um frame artificial de 20 B com o retorno em `sp-4`, que mascara exatamente esse deslocamento de 4 B; por isso os 11 testes passam.

CRÍTICO — `tools/fab_reload_3_3_guardas.py:123-135` e `docs/tarefas/025-analise.md:167` — `CONFIRMADO`.
A guarda compara `jd+0x12C` (capturado em `0xDAAF22`) com `[0x0081BC84+0x20]` (`0xDAAF2E`) e só devolve 0 se eles divergirem (`0xDAAF30/0xDAAF32`). Ocorre que a gravação que representa o pulo do usuário — `0xD08966 str r2,[r3,#0x20]` em `page4_media_cb` (cases 4/5) e `0xD0EEAE`/`0xD0EEC2` na rajada — roda na mesma PreTask (`docs/tarefas/016-analise.md:10,31,41`; `0xCF8124 bl 0xD0ED0C` → `0xD0EEE8`). Enquanto o `jd_decomp` ocupa a PreTask, a mensagem de pulo fica em `MgrTaskQue`; o campo só é atualizado depois que o decode retorna. Cenário: usuário aperta “próxima” no meio dos ~1 s de decode; a comparação em `0xDAAF30` vê valores iguais, a guarda não aborta e a capa velha é exibida. A ficha pedia justamente detectar “a fila da PreTask tem mensagem esperando” (`025-reload-3-3-pular-rapido.md:52`); o proxy escolhido não observa isso.

MÉDIA — `tools/fab_reload_3_3_guardas.py:9-16`, `docs/tarefas/025-analise.md:167` — `CONFIRMADO` quanto à existência do gravador; `HIPÓTESE` quanto ao dano.
Não é literalmente verdade que só a PreTask grave `[0x0081BC84+0x20]`. `0xCFF218 strd r4,r4,[r5,#0x20]` (em `0xCFF1FC`, literal `0x0081BC84`) zera o campo quando `0xD6D13C` devolve 0 (erro de banco); é alcançável pela MgrTask via slot 0 `0xD00E28`, instalado por `0xD0101E bl 0xD3EDA8`. Não é gravação de pulo do usuário, mas mostra que a premissa da análise é incompleta. Outros gravadores diretos: `0xCFF23E`, `0xCFF27E/0xCFF296`, `0xCFF948`, `0xD030A2`, `0xD08966`, `0xD0C960`, `0xD0EEAE`, `0xD0EEC2`. Cenário: se o erro de banco ocorrer no meio do decode, `0xDAAF30` vê divergência e aborta uma capa que ainda era válida (falso positivo); não há prova de que isso aconteça na prática.

BAIXA — `docs/tarefas/025-analise.md:229` — `CONFIRMADO`.
O texto diz `8×0x414 + 0x1000 = 0x30A0`, mas a linha 188 do mesmo arquivo e `tools/fab_reload_3_3_guardas.py:22,85` usam `0x30C0`. A conta correta é `8*(0x414+4)=0x20C0`, mais `0x1000` = `0x30C0`; é divergência documental, sem efeito no byte gravado.

Verificado sem achado

- ORIGINAL `firmware/ORIGINAL/GN438_original.bin` sha256 `b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f`; XIP `0xC00000`. `0xD58100` inicializa pool `0xA000` em `0x00876000`; `0xD5811C` ignora `NULL` e `0x00819E60`; `0xD58188` devolve 0 na falta de memória (`cmp r0,#0`/`mov r0,r4`).
- Parte 0.2: trampolim de 40 B em `0xDAA9D8` (`lv_mem_alloc(0x2210)` → `memset(...,0,0x2210)`), `bl` em `0xDAA04A`, FREEs em `0xDAA0D0`/`0xDAA246`; bit Thumb correto em todos os `blx` (`0xD58189`, `0xBAB`, `0xD5811D`).
- Parte 1.2: `bl 0xDAAF50` em `0xDAAC68`; guarda preserva `r5/r6/r7/r8` e `sp`, recarrega `r0/r1/ip`, `r3` é morto, retorno via `bx ip` (`0xDAAC6D` sucesso / `0xDAACFB` falha com `lv_mem_free(r8)`). `[0x81BBC8]` e `0xD6A9EA` batem com a fábrica; capacidade `0x3C00` em `0xCF82B4`; reserva `0x30C0` cabe.
- Reprodução: `reload_3.3` = `87ca28e74246f149e2024b90936ae9401b5d0b928d994691aa09e248d523aad2` em duas compilações; `reload_3.2` = `aa7e7a5aa453f9f0969c3a083e5c85c4b3e79e567b8c3f1c0c10f76adf3a5ef1`. Diff 3.2→3.3: 195 B, 15 intervalos, todos no setor de arquivo `0x1AA000` (`0x1AA03E..0x1AAF86`); nada abaixo de `0xE000`, nada em `0xD000`, nada na PSMP.
- Área livre: rotinas em `0x1AAF00..0x1AB000` (XIP `0xDAAF00..0xDAB000`) dentro do lote declarado `fab_capa_album.py` (`0x1A8000..0x3000`) no MAPA de `tools/build.py:174`; não cruzam outro lote.
- Kit: `OpenPod_OpenPodReload3.3.up` (1.761.536 B, `off=0x100`, `tam=0x1AE000`) tem CRC-16/XMODEM `0xa202` conferido com o payload; payload = imagem 3.3 + carimbo em `0x10A59C` e `Reload 3.3\0` em `0x1A4F00`. Os 21 setores em `cabo/setores/` (de `0x101000` a `0x1AD000`) são iguais ao payload; os `base_*` são iguais ao ORIGINAL; ausência de `0xD000` e de PSMP.
- Testes: `python3 tests/test_reload_3_3.py -v` → 11/11 OK (executado à parte; não consta de `tools/ci.sh:24-34`); `sh tools/ci.sh` → `CI OK`.

FIM-025-REVISAO
