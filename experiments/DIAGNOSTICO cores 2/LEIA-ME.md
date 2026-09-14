# DIAGNÓSTICO DE CORES 2 — instrumento, não versão

Gerado em 2026-09-14, sobre a **Core 2.2**.

## A pergunta

Com o tema claro, apareceu um **cinza atrás do texto** nas listas — e o
mantenedor notou que ele parece **o mesmo cinza da faixa superior**.

A leitura estática não fechou: a linha está mandada a ler `cor_tela`
(`0x0012177C` → `0x00DA5A20`, conferido), mas o que se vê não é branco.
Ou outra coisa repinta depois, ou eu estou lendo o caminho errado.

**Em vez de continuar adivinhando, pergunta-se ao aparelho.**

## As cores

```
+00  cor_tela        VERMELHO
+02  cor_faixa       VERDE
+04  cor_separador   AMARELO
+06  cor_texto       AZUL
+08  cor_texto_sel   MAGENTA
+0A  cor_selecao     CIANO
```

O aparelho vai ficar horroroso. É de propósito — cada cor tem de ser
impossível de confundir com as outras.

## Como usar

```
1. copie  update.up  para a raiz do cartao
2. Configurar -> Atualizar por SD -> Sim
3. fotografe a tela CONFIGURAR
4. APAGUE o update.up do cartao
5. regrave a Core 2.2 depois
```

## O que a foto vai dizer

| a linha (onde está o texto) ficou | significa |
|---|---|
| **VERMELHA** | lê `cor_tela`, como mandamos — e o cinza vinha de outra coisa |
| **VERDE** | lê `cor_faixa` — a suspeita do mantenedor está certa |
| outra cor | lê outro campo, e aí o mapa está errado |
| **não mudou** | **não vem da tabela** — é um dos 79 pontos que pintam fundo fora dela |

A última linha é a mais informativa, e é a que eu considero mais
provável: o censo de 14/09 achou **84 chamadas de `set_style_bg_color`
no firmware, e a nossa tabela governa 5**.

## Voltar

O `.up` da Core 2.2 desfaz. Ou `recovery/RECOVERY.sh --alvo core`.
