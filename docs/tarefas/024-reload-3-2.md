# Ficha 024 — OpenPod Reload 3.2: Cobrinha com os controles do celular e a capa numa tarefa própria

Tipo: **Risco + Pesada** (a parte B mexe no caminho da capa, que já travou o aparelho antes). Base: `privado-completo` (Reload 3.1c,
aprovada no aparelho: "tudo funcionou"). Desenvolvedor: `opencode/deepseek-v4.1-flash-free`.

Decisão do decisor (2026-11-18): Cobrinha com direções absolutas (como no celular), mais a correção da capa, lançadas como **3.2**.
Os jogos novos passam para a 3.3.

Antes de começar, ler:
- `docs/tarefas/014-analise.md`, `015-analise.md` e `019-analise.md`: o caminho atual da capa (PreTask, `envia_path`, `carrega_capa`,
  8 mensagens tipo 6, yield `0xC43634`, limites de 1000 px e 512 KiB).
- `docs/tarefas/020-analise.md` §1 (camada de SO: tarefa, semáforo, `sleep`, `calloc`/`free`) e §2 (regra da tarefa de UI).
- `docs/tarefas/023-analise.md`, `sdk/apps/cobrinha/main.c` e `docs/BUTTON_ANALYSIS.md` (códigos de tecla).

## Parte A — Cobrinha com direções absolutas
| Botão | Ação |
|---|---|
| ⏮ (`0x14`) | esquerda |
| ⏭ (`0x13`) | direita |
| M (`0xA0`) | cima |
| Play/Pause (`0x0A`) | baixo; na tela inicial, começa; no fim de jogo, recomeça |
| segurar M (`0xA2`) | pausa e continua |
| VOL/Sair (`0x81`) 2x | sai |

- **Meia-volta direta é ignorada**, como no celular.
- **Mensagens de ajuda nos dois idiomas**, com os botões novos.

## Parte B — a capa numa tarefa própria
**Problema (aparelho):** com capas de 500 a 1000 px, o contador de tempo engasga enquanto a capa carrega. O decode roda na PreTask
(`envia_path`, dentro da rajada), e é a PreTask que atualiza o tempo da música. O yield a cada callback (2.2.1) salvou o áudio, mas
não libera a PreTask.

**Objetivo:** a PreTask só **pede** a capa e volta na hora. Uma **tarefa própria** abre o MP3, decodifica (`carrega_capa`) e manda
os pixels para a view.

**Regras (provar cada uma no ORIGINAL):**
1. **Criar tarefa:** usar a API da fábrica (`0xCF7AD4` e afins, 020 §1).
   - Provar a assinatura: entrada, argumento, nome, prioridade e pilha.
   - Provar se a tarefa pode **terminar sozinha** sem vazar memória. A função de criar aloca dois semáforos para o join.
   - **Sem prova de término limpo:** usar **uma tarefa só, criada uma vez**, que espera pedidos num semáforo ou fila da fábrica.
2. **Prioridade abaixo da PreTask e da MediaTask** (provar os números: PreTask 3, MediaTask 3 etc.). Assim ela nunca atrasa o áudio
   nem o relógio. **O yield a cada callback pode continuar.**
3. **Pilha:** pelo menos 2 KiB. O decode mediu 352 B de pico na PreTask; medir de novo no emulador.
4. **Buffer de mensagem próprio.** A tarefa da capa **não pode** usar o buffer global `0x8238F1` da PreTask: as duas montariam
   mensagens ao mesmo tempo. Ela usa um buffer alocado dela para `0xD0D818`, e chama o `0xD0D880` como a fábrica.
5. **Pedido copiado:** o caminho vai **copiado** para o contexto da tarefa. Nada de ponteiro para o buffer da rajada, que é liberado.
6. **Troca rápida de faixa:** não pode acumular decodes nem mandar a capa da faixa errada.
   - Usar um **número de pedido**: o mais novo vence, e o decode em andamento é abandonado ou descartado ao terminar.
   - A view só aplica os pedaços (tipo 6) se eles forem do caminho atual: marcar os pedaços com o número de pedido ou com um resumo
     do caminho.
   - Provar que um pedido velho nunca pinta a capa de outra faixa.
7. **Estado global:** se for preciso guardar algo entre pedidos (o handle da tarefa, o número de pedido), **provar** um lugar seguro.
   - Opções: memória alocada com o ponteiro guardado num lugar provado como livre. Nada de flash XIP como variável, nada de RAM "que
     parece livre" sem prova.
   - **Sem lugar seguro: ESCALADA-024**, com as opções.
8. **A ViewTask continua sem tocar em arquivo nem esperar.** A tarefa da capa nunca chama LVGL.
9. **Limites e falhas iguais à 2.2.1:** 1000 px e 512 KiB → cinza; falha → cinza; tudo liberado e o arquivo fechado em todos os
   caminhos.

## O que entregar
1. `docs/tarefas/024-analise.md` com as provas de cada regra da parte B.
2. Receita `reload_3.2` = `reload_3.1c` + parte A + parte B.
   - Testes em `tests/test_reload_3_2.py`.
   - Emulador: o pedido volta à PreTask em poucas instruções; a tarefa decodifica; uma troca rápida descarta o pedido velho.
   - Estáticos: bit Thumb, sem `.data`/`.bss` no SDK, nada abaixo de `0xE000`, setor `0xD000` e PSMP intocados.
3. Kit por `gera_versao` **com a base padrão (ORIGINAL)**:
   - carimbo **`Reload 3.2`**;
   - `release/OpenPod-Reload-3.2/`;
   - `TESTAR.txt`:
     - Cobrinha com os controles novos;
     - capa 640 e 1000 px: o contador **não engasga** e a capa aparece;
     - pular faixas rápido: a capa certa, sem travar;
     - capa de 1500 px: cinza na hora;
     - volta de segurança: 3.1c.
   - README "New in 3.2", com o crédito ao Dmitry mantido.
4. Entrada no `docs/CHANGELOG.md`.

**Não publicar.** Commit obrigatório antes do sinal.

Regras de sempre:
- Nunca alterar `firmware/ORIGINAL`, gravar no aparelho, fazer push ou merge.
- Testes protegidos intactos; `sh tools/ci.sh` verde.
- Todo destino de `bx`/`blx` com bit Thumb; lr de `bl` com bit0=1; tabelas alinhadas; XIP só leitura.
- Não usar `cd` nem caminho absoluto; nada em `/tmp`.

Sinal final sozinho numa linha: `PRONTO-024` ou `ESCALADA-024`.
