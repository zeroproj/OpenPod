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
