# ESCALADA-024 — a capa numa tarefa própria

**Resolvida em 2026-11-18.** Decisão do decisor: **opção 4** — a Reload 3.2
sai **só com a Parte A** (Cobrinha com direções absolutas); a capa continua
como na 3.1c. A Parte B (opção 1, tabela de tarefas da fábrica) fica para
**dezembro**, numa ficha própria. O kit 3.2 foi gerado em
`release/OpenPod-Reload-3.2`.

O que está provado no ORIGINAL está em `docs/tarefas/024-analise.md`:
`fw_task_create` `0xCF7AD4` (entrada, argumento, nome, prioridade, pilha),
TCB de `0x18` B, wrapper `0xCF79D3` que nunca retorna, `fw_task_join`
`0xCF7B90` que bloqueia, PreTask e MediaTask em prioridade 3 com pilha
`0x800`, e a tabela de tarefas `0x0081D68C` com ids de fila em `+0x54`.

Opções registradas para dezembro:

1. **Aprovar a tabela da fábrica (recomendada).** Usar um id livre (6, 7,
   0xC, 0xD ou 0xE), criar a tarefa uma vez pela PreTask com `0xD6ACAC`,
   enviar o pedido por `0xD7DAFE` e pôr o hash do caminho em `msg+8`. A view
   descarta o tipo 6 de hash velho. Não usa RAM nova; exige patch no
   tratador tipo 6 e prova de que ele ignora `+8`.
2. **Reservar 4 B de RAM com prova.** O arquiteto indica um endereço livre
   comprovado (mapa/dump) para o handle/contador.
3. **Fatiar o decode na PreTask.** Sem tarefa nova, mas reescreve o caminho
   do `carrega_capa`; maior risco de áudio.
4. **Só a Parte A.** Foi a decisão: a capa fica como a 3.1c.

A Parte A está no branch `limtistech/tarefa-024`, com `tools/ci.sh` verde e
`tests/test_reload_3_2.py` passando. Nada foi publicado.
