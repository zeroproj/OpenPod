# Bluetooth reinicia o aparelho — DEFEITO DE FÁBRICA

> Confirmado no aparelho em 2026-09-18.

## O sintoma

O Bluetooth **liga normalmente**. Mas ao entrar nas opções do menu, o
aparelho **reinicia**.

Reportado pelo mantenedor, que nunca havia testado o subsistema — então
não há histórico de quando começou.

## Não é nosso — CONFIRMADO

A Beta 9 restaurou a região inteira do Bluetooth
(`0x00D28000`–`0x00D2B000`) ao estado de fábrica: **13 bytes**, todos
altura de linha (`07` → `0a`), acumulados ao longo de cinco versões do
projeto.

```text
0x00D2872E  0x00D28804  0x00D2892A  0x00D28A0A  0x00D28AEA
0x00D28D6E  0x00D28E3C  0x00D29072  0x00D2A16A  0x00D2A244
0x00D2A69A  0x00D2AB88  0x00D2AC56
```

Sete deles vieram do `patch_faixa_16px.py` da Core 5.x, que tocou o
Bluetooth sem que ninguém tivesse notado.

**Com os treze revertidos, o aparelho continuou reiniciando igual.**

Conferido antes do teste: zero bytes alterados fora daquela região em
relação à Beta 8. A variável estava isolada.

**Consequência:** os 13 bytes voltam. Eles nunca foram a causa, e sem
eles o Bluetooth fica fora do padrão visual do resto do aparelho.

## O que se sabe da região

| | |
|---|---|
| página | 35 (`0x23`), `page_bt_menu_option_event_cb` em `0x001286E0` |
| funções | `page_bt_menu_create`, `_paired_list_process`, `_search_list_process`, `_anim_process`, `_mbox_process`, `_event_reply` |
| o que o OpenPod mexeu | **só** 13 divisores de altura — nenhuma estrutura, nenhuma rotina |

## O que NÃO foi investigado

Tudo. O reinício não foi diagnosticado — só foi **descartada a nossa
participação**.

Hipóteses por ordem de custo, nenhuma testada:

1. **Estouro de pilha** na tarefa do Bluetooth ao montar a lista. O
   subsistema tem pilha própria, e reinício (em vez de congelamento) é
   sintoma típico de watchdog disparando por travamento de tarefa.
2. **Ponteiro nulo** quando a lista de pareados está vazia — o aparelho
   nunca pareou com nada.
3. **Rádio não inicializado** — a opção depende de hardware que só
   acorda em outro caminho.

A 2 é a mais barata de testar: parear com algum aparelho e ver se o
reinício some.

## Estado

**ABERTO**, e **não é regressão**. Entra em "problemas conhecidos" do
README público quando a próxima versão for publicada.
