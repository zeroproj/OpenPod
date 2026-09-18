# Bluetooth quebrado — É NOSSO

> ⚠️ **ESTE DOCUMENTO FOI CORRIGIDO EM 2026-09-18.** A primeira versão
> concluía "defeito de fábrica". **Estava errado.**
>
> O mantenedor gravou o firmware de fábrica e **o Bluetooth funciona
> inteiro lá** — pareia, conecta, tudo. No OpenPod não funciona nada.
>
> Meu erro de método: a Beta 9 restaurou apenas a **região**
> `0x00D28000`–`0x00D2B000` e o defeito continuou, e eu li isso como
> "não é nosso". A conclusão correta era **"não está nessa região"**.
> Janela estreita, conclusão larga — o mesmo erro da bateria e da
> altura de linha, pela terceira vez.

## O sintoma

De fábrica: o Bluetooth funciona.
No OpenPod: **nada funciona**, e entrar nas opções reinicia o aparelho.

O mantenedor nunca havia testado o subsistema — por isso não há
histórico de quando quebrou. Pode estar quebrado desde a Core 1.0.

## O que já foi descartado

A região `0x00D28000`–`0x00D2B000` (as telas do Bluetooth). São 13 bytes
nossos ali, todos altura de linha. Revertidos na Beta 9: **o defeito
continuou**. A causa está fora.

## O mapa do que a Beta 8 muda vs fábrica — 47 setores

```text
0x00C48000   1 sec      5 B    tabela de rótulos da home
0x00C52000   3 sec     24 B
0x00C5D000   1 sec      1 B
0x00CC7000   1 sec    767 B    paleta do papel de parede (fundo preto)
0x00CCC000   2 sec   5320 B    imagens
0x00CD3000   1 sec      1 B
0x00CDF000   1 sec      2 B
0x00D01000   1 sec     19 B    despacho da home
0x00D08000   3 sec     70 B    presenter da música
0x00D0C000   2 sec      8 B
0x00D21000   3 sec     56 B    faixa e ícones de status
0x00D26000  24 sec    498 B    camada de view
0x00D49000   1 sec      1 B
0x00DA3000   2 sec   3834 B    ⚠️ tabela de idiomas realocada
0x00DA6000   1 sec    657 B    ⚠️ rotinas e strings na área livre
```

## Hipótese principal — NÃO TESTADA

**A realocação da tabela de idiomas** (`relocate_lang_table.py`, passo 3
da receita `core1.0`). Ela move a tabela do português para a área livre.

Por que ela encabeça a lista:

1. é das **primeiras** mudanças do projeto — se quebrou, quebrou cedo,
   e o mantenedor nunca testou o Bluetooth depois;
2. o menu do Bluetooth é **texto puro** — nomes de aparelhos, estados
   de pareamento;
3. se alguma leitura de string do subsistema não foi repontada, ela lê
   lixo — e ler lixo como ponteiro reinicia o aparelho.

## Hipóteses secundárias

2. as **rotinas em área livre** (roteador do Extras, despacho APP) —
   se alguma escreve fora do lugar;
3. a **camada de view** (24 setores, 498 bytes) — alturas e cores.

## Como descobrir

Bisseção por região, no aparelho. Reverter metade dos 47 setores,
testar, estreitar. São ~6 gravações no pior caso — mas a hipótese
principal pode resolver na primeira.

## Estado

**ABERTO, e é regressão nossa.** Não pode ser publicado sem aviso.
