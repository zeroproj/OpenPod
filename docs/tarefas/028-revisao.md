APROVADO

Provas (imagem real `.tmp/35.bin`, sha `f49c8195…`, desmontagem com capstone):
- **Bytes:** o diff 3.3→3.5 só toca `0x486A0..0x486C4`, `0x0CE15C..0x0D315C`, os quatro ganchos e o lote `0x1AB000..0x1AB813` (13944 B); nada abaixo de `0xE000`, no setor `0xD000` nem na PSMP.
- **Ganchos:** `0xD23CF8 87 f0 82 f9`→`0xDAB000`; `0xD23B8C 87 f0 38 fb`→`0xDAB200`; `0xD3225E 79 f0 cf b9`→`0xDAB600`; `0xD2EEE4 7c f0 0c bc`→`0xDAB700`.
- **CRÍTICO 1 corrigido:** `0xDAB700` faz `push {r0-r4,lr}`, `bl 0xDABE9E`, `pop`, `movw/movt r3,#0x00823EB0`, `ldrb r3,[r3]`, `b.w 0xD2EEE8`. O LR da folha `0xD2EEC4` sobrevive e `r3` volta com o byte, não com o endereço.
- **CRÍTICO 2 corrigido:** `0xDAB600` faz `push {r0-r2,lr}`, `bl 0xDABE3A`, `pop`, `b.w 0xDAA014` — a entrada TITULO da capa. O teste Unicorn executa o caminho real e confirma `label_set_text` no rótulo certo sem perder a capa.
- **Timer/estado:** `find_state` em `0xDADEAC` lê `n_size` de `[0x81D2D4]` e compara `timer_cb & ~1`; o callback em `0xDAB800` só chama `lv_label_set_text` quando `version` muda. Nenhum chamado a kernel, FatFs, banco ou `get_path`; `.data`/`.bss` vazios.
- **Kit:** `.up` com `0x1AF000` bytes de payload, CRC `0x9112`, sha `3d8b9b79…`; só 19 bytes diferentes da imagem (carimbo em `0x1A4F00` e ponteiro em `0x10A59C`). Setores base/finais batem com a 3.3 e com o payload; PSMP fora.
- **Origem/testes:** ferramenta nova, fora das listas PROIBIDAS; testes protegidos intactos. A suíte inteira passou (028: 11/11), com temporários em `.tmp/ci`.

Achados:
- **BAIXA** — `tests/test_reload_3_5.py:11` e `:17`: o docstring ainda cita o sha `f0faee10…` e o SDK de 13912 B, enquanto as constantes em `:69` e `:71` estão certas (`f49c8195…`, 13944 B). Cenário: quem lê só o cabeçalho conclui que a imagem reprovada na conferência anterior é a esperada.
- **BAIXA** — `release/OpenPod-Reload-3.5-Diag/install.sh:219` e `:231`: o menu diz que o caminho de cabo vem "do firmware de fábrica", mas `cabo/flash_OpenPodReload3.5Diag.sh:366-370` exige o hash de FIRM da 3.3. Cenário: o decisor em firmware de fábrica escolhe a opção 1 e o pré-check recusa antes de gravar; o `README.md:13` está correto.
- **BAIXA** — `docs/tarefas/028-analise.md:108`: "~0,9 KiB" de código novo, contra 11868→13944 B medidos (+2076 B). Cenário: estimativa de capacidade desatualizada, ainda folga dentro do lote de `0x51000`.

REVISAO-028
