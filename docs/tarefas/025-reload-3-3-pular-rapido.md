# Ficha 025 — OpenPod Reload 3.3: pular músicas rápido sem travar (e a capa sem atrasar o relógio)

Tipo: **Risco + Pesada** (caminho da capa; correção de defeito relatado por usuários). Base: `privado-completo` (Reload 3.2,
publicada). Desenvolvedor: `opencode/deepseek-v4.1-flash-free`.

## Problema (relatos de usuários, 2026-11-18)
"Quando passa a música rápido fica travando, às vezes reinicia." Também: o relógio engasga quando a capa carrega.

**HIPÓTESE da coordenação** (ver `016-analise.md` §2 e `015-analise.md`):
- Cada capa manda **8 mensagens tipo 6** de `0x414` B (8.352 B) para o ring da view, que tem **15.360 B**.
- O decode roda **na PreTask**, dentro da rajada, e leva até ~1 s.
- Pulando rápido:
  - a PreTask fica ocupada decodificando capas que já ficaram velhas;
  - os pedidos se acumulam;
  - o ring enche, e o `0xD0D818` devolve 0 e **perde mensagens da fábrica** (título, tempo, estado);
  - o resultado é travamento e, às vezes, reinício (watchdog ou estado inconsistente).

## Parte 0 (obrigatória, primeiro) — o chip tem dois núcleos (achado de 2026-11-20)
**Fonte:** README do SL6801_player, seção "Two cores" (commit `1e62711`, 2026-11-20; licença MIT). Os **endereços do Dmitry são de outra
compilação** (`0xCD8C7A` não é `bl` no nosso ORIGINAL): só o conceito vale, e cada endereço nosso tem de ser provado no ORIGINAL.
- **CPU0** roda o FreeRTOS e todas as tarefas (PreTask, MediaTask, cartão). **CPU1** roda a interface: LVGL, eventos, timers e o
  `label_process`. Os dois conversam por rings de mensagem.
- **Qualquer chamada ao kernel feita da CPU1** (heap do FreeRTOS, tarefas, semáforos, sleep, FatFs, dispositivos) corre junto com a CPU0
  e às vezes corrompe o heap ou as listas do escalonador. O aparelho congela e o watchdog reinicia uns 15 s depois. A CPU0 está mais
  ocupada **durante a música**. Isso explica os travamentos das fichas 011–014 (arquivo na "ViewTask").

**CONFIRMADO pela coordenação na imagem da 3.2** (`reload_3.2`):
- O gancho CRIA (`0xD31EB6` → `0xDAA010` → `0xDAA028`, `corpo_cria` em `tools/capa_album.s`) roda na criação da página Tocando Agora,
  ou seja, **na CPU1**, e chama `CALLOC` `0xCF7840` (`fw_os_calloc`/OAL, **heap do FreeRTOS**, ficha 020) para o contexto de ~8 KiB.
- O APAGA (`0xDAA024` → `0xDAA212`, cb de `LV_EVENT_DELETE`) roda **na CPU1** e chama `FREE` `0xCF7884`.
- O TITULO está desviado para o epílogo desde a B6 (não chama arquivo) e o tipo 6 só copia pixels: ok.

**O que fazer:**
1. **Nenhuma chamada ao kernel a partir da CPU1** em código nosso. Auditar e listar, com endereço: CRIA, APAGA, `label_dispatch`
   (tipos 5 e 6), o gancho do menu Apps, o SDK dos jogos (`sdk/src`, `sdk/apps`: `fw_os_*`, sleep, calloc, tarefas) e o overlay.
2. **Tirar o contexto da capa do heap do FreeRTOS** na CPU1. Escolher uma opção e provar:
   - (a) o alocador do **LVGL** (`lv_mem_alloc`/`lv_mem_free` da fábrica: provar endereço e a folga do pool, ~40 KiB, com o ORIGINAL rodando);
   - (b) um buffer **alocado uma vez na CPU0** (na PreTask, no primeiro `envia_path`) e nunca liberado, com o ponteiro num lugar provadamente
     livre. Justificar os ~8 KiB fixos no heap.
3. **Provar** se a fábrica recria a página Tocando Agora ao trocar de faixa. Se recria, o CRIA/APAGA roda a cada pulo, e essa é a causa
   mais provável do relato. Se não, registrar.
4. Depois da Parte 0, fazer a Parte 1. Se a Parte 0 sozinha explicar o defeito, a Parte 1 continua (é guarda barata), mas a Parte 2
   pode virar ficha própria.

## Parte 1 (obrigatória) — guardas sem estado global
1. **Desistir da capa velha.** Antes do decode e **dentro do yield** de cada callback do TJpgDec (o wrapper da 015/B7b), conferir se
   **a fila da PreTask tem mensagem esperando**, ou seja, se o usuário já pulou.
   - Se tiver: **abortar o decode** (o callback devolve erro, o `jd_decomp` para e o `carrega_capa` cai no caminho de falha: libera
     tudo, fecha o arquivo e manda o cinza ou nada).
   - **Achar e provar no ORIGINAL a função da fábrica que conta as mensagens pendentes de uma fila** (OAL/FreeRTOS:
     `uxQueueMessagesWaiting` ou equivalente) e o objeto de fila da PreTask: a tabela de tarefas `0x0081D68C`, id `0xB`,
     `0xD6AE38(0xB)`.
   - Se não houver função de contagem, **provar** um campo equivalente na estrutura da fila. Sem prova: ESCALADA.
2. **Não atropelar a fábrica no ring.** Antes de mandar os 8 pedaços tipo 6, conferir o **espaço livre** do ring da view (`0xD6A9EA`,
   usado em `0xCF8406`).
   - Exigir espaço para os 8 pedaços **mais uma reserva** de pelo menos 4 KiB para as mensagens da fábrica. Justificar o número.
   - Sem espaço: não mandar a capa; mandar só o tipo 5 vazio (cinza, 9 B) se couber.
3. Medir no emulador:
   - com fila vazia, o decode é igual ao da 3.2 (mesmos pixels);
   - com mensagem pendente, o decode aborta em poucas instruções;
   - com o ring cheio, a capa não é enviada.

## Parte 2 (se fechar com prova) — o relógio sem engasgo
O decode vai para **uma tarefa própria**, criada uma vez, usando um **id livre da tabela de tarefas da fábrica** (opção 1 da
`ESCALADA-024.md`; ler `024-analise.md`).
- O pedido chega com o hash do caminho.
- A view descarta o tipo 6 de hash velho.
- Prioridade abaixo da PreTask e da MediaTask; buffer de mensagem próprio.
- As mesmas guardas da Parte 1.
- **Se alguma regra não fechar:** entregar só a Parte 1, registrar e terminar com `PRONTO-025`. A Parte 2 vira ficha própria.

## O que entregar
1. `docs/tarefas/025-analise.md`: as provas (função de contagem da fila, objeto da fila da PreTask, espaço do ring, reserva) e a
   medição.
2. Receita `reload_3.3`, testes em `tests/test_reload_3_3.py` (emulador e estáticos) e as regras de sempre.
3. Kit por `gera_versao` **com a base padrão (ORIGINAL)**:
   - carimbo **`Reload 3.3`**;
   - `release/OpenPod-Reload-3.3/`;
   - `TESTAR.txt`:
     - pular 10 músicas **seguidas e rápido**, com capa: não trava e não reinicia;
     - a capa da música em que você parou aparece;
     - capas de 640 e 1000 px: o relógio (se a Parte 2 entrar);
     - jogos e capa normais;
     - volta de segurança: 3.2.
   - README "New in 3.3".
4. Entrada no `docs/CHANGELOG.md`.

**Não publicar.** Commit obrigatório antes do sinal.

Regras de sempre:
- Nunca alterar `firmware/ORIGINAL`, gravar no aparelho, fazer push ou merge.
- Testes protegidos intactos; `sh tools/ci.sh` verde.
- Bit Thumb em todo `bx`/`blx`; lr de `bl` com bit0=1; tabelas alinhadas; XIP só leitura; nada de RAM nova sem prova.
- A ViewTask não toca em arquivo nem espera.
- Não usar `cd` nem caminho absoluto; nada em `/tmp`.

**Atenção:** as receitas antigas compilam o SDK atual (pendência de processo). Não mexa no SDK nesta ficha, a não ser que a Parte 2
exija.

Sinal final sozinho numa linha: `PRONTO-025` ou `ESCALADA-025`.
