# Ficha 026 — Caixa-preta: `crashlog.txt` no cartão quando o aparelho trava

Tipo: **Risco + Pesada** (gancho no início do sistema, vetores de falha, tarefa nova na CPU0). Base: a **3.3** publicada (ficha 025).
Desenvolvedor: `opencode/deepseek-v4.1-flash-free`. Pedido do decisor em 2026-11-20 ("pode colocar essa questão do crashlog.txt").
**Começa só depois do `PRONTO-025`**, no mesmo fluxo: desenvolvedor, revisão, conferência da coordenação e teste no aparelho.

## Por quê
Hoje um relato de "travou e reiniciou" não diz nada. A RAM não sobrevive ao reset do watchdog. Com a caixa-preta, o aparelho grava no
cartão, **antes de reiniciar**, o que travou: a falha, as tarefas, a pilha, o heap. Cada relato de usuário vira um relatório exato.

## Fonte (licença MIT, com crédito)
`dbrant/SL6801_player`, commit `1e62711` (2026-11-20): `sdk/src/blackbox.c`, `sdk/src/service.c`, `sdk/apps/crashlog`, e a seção
"Two cores" do README.
- Portar mantendo o aviso MIT de Dmitry Brant no cabeçalho de cada arquivo portado (D22).
- **Os endereços dele são de outra compilação** (`0xCD8C7A` não é `bl` no nosso ORIGINAL). Cada endereço nosso tem de ser **achado e
  provado no ORIGINAL**, com a instrução e o motivo. Sem prova: ESCALADA.

## Como funciona (o conceito, a adaptar)
1. **Tarefa de serviço na CPU0.** Um gancho numa chamada que a primeira tarefa faz uma vez no início (no dele, o `bl` da configuração do
   watchdog). Ele chama o original e cria a tarefa da caixa-preta. Provar o equivalente no nosso ORIGINAL.
2. **Estado sem variável global.** No dele, o ponteiro do estado fica na entrada reservada da tabela de vetores (`0x80001C`). Provar que
   ela é livre no nosso firmware, ou achar outro lugar provadamente livre.
3. **Falhas.** Os vetores 3 a 6 (HardFault, MemManage, BusFault, UsageFault) apontam para o tratador da caixa-preta. Ele guarda os
   registradores, o status da falha e a pilha. Numa tarefa da CPU0, estaciona a tarefa que falhou num laço de espera, para o resto
   continuar rodando até gravar. Na CPU1, só espera.
4. **Travamento da tela.** O check-in do watchdog do laço da interface marca a hora de cada volta. Provar o equivalente no ORIGINAL.
5. **Gravação.** A cada 100 ms, a tarefa confere. Depois de uma falha, ou com a tela parada há 3 s, grava **uma vez** `0:/crashlog.txt`:
   a falha, o estado e o uso de CPU de cada tarefa, pc e lr salvos, os bits do watchdog e o heap.
6. **Toda chamada ao kernel e ao cartão roda na CPU0** (Parte 0 da ficha 025). Nada disso pode rodar na CPU1.

## O que NÃO entra
- O `bbstatus.txt` contínuo e o app "Crash log" com testes de travar: só no kit de diagnóstico (item 3 abaixo), nunca na versão pública.
- Nenhuma mudança de comportamento quando nada trava: sem escrita no cartão, sem efeito no som, no relógio ou na bateria.

## O que entregar
1. `docs/tarefas/026-analise.md`: cada endereço com prova; o tamanho do código e do estado; o custo de CPU da tarefa a cada 100 ms; o
   impacto no heap (Dmitry deixa 32 KiB livres para a fábrica); o que acontece se o cartão não estiver presente ou estiver cheio.
2. Receita nova = a da 3.3 + a caixa-preta. Lote próprio na área livre, sem `.data`/`.bss`, bit Thumb em todo `bx`/`blx`.
3. **Kit de diagnóstico** `Reload 3.3 Diag` (base ORIGINAL) com o app "Caixa-preta" no menu Aplicativos e os dois testes (falha e
   travamento da tela), para o decisor provar no aparelho que o `crashlog.txt` aparece antes do reset.
4. Só depois do teste do decisor: proposta de incluir a caixa-preta (sem o app de teste) na próxima versão pública.
5. Testes sem o aparelho e `sh tools/ci.sh` verde.

Regras de sempre:
- Nunca alterar `firmware/ORIGINAL`, gravar no aparelho, fazer push ou merge.
- Testes protegidos intactos; nada abaixo de `0xE000`; setor `0xD000` e PSMP intocados.
- Classificar tudo como CONFIRMADO, PROVÁVEL ou HIPÓTESE.

Sinal final sozinho numa linha: `PRONTO-026` ou `ESCALADA-026`.
