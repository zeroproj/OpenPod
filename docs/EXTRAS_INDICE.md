# O índice do Extras — um bug, quatro sintomas

> Levantado em 2026-09-20 por leitura do firmware de fábrica.
> **Causa confirmada. Conserto NÃO escrito.**

---

## O mecanismo

Na tela inicial **de fábrica**, cada item passa o **próprio índice** como
parâmetro (`r2`) para a abertura da página. Confirmado em três pontos
onde o valor é explícito:

```asm
0x00D012D6   movs r3, #0x23 ; movs r2, #6     Bluetooth, índice 6
0x00D0123A   movs r3, #0x28 ; movs r2, #7     Configurar, índice 7
0x00D012DC   movs r3, #0x1E ; movs r2, #11    página 30, índice 11
```

Os itens que têm rotina de preparação **não escrevem `r2`**: eles
terminam saltando para `0x00D01036`, que faz

```asm
ldrh r2, [r4, #0xc]     ; lê o índice DA MENSAGEM
ldrh r1, [r4, #0xa]
ldrh r0, [r4, #8]
b    0xd011f2           ; pop e abre a página
```

Vindo da home, esse índice é o índice na home. **Vindo do nosso Extras,
é o índice no nosso menu.**

---

## A tabela de tradução — COMPLETA

| nosso índice | item | página | `sub` de fábrica | origem |
|---|---|---|---|---|
| 0 | Gravação | 24 | **2** | entrada 2 da TBH |
| 1 | Rádio | 26 | **3** | entrada 3 da TBH |
| 2 | Livro digital | 12 | **4** | entrada 4 da TBH |
| 3 | Imagem | 21 | **5** | entrada 5 da TBH |
| 4 | Bluetooth | 35 | **6** | `movs r2,#6` explícito |
| 5 | Pastas | 34 | **0** | `movs r2,#0` explícito em `0x00D00A90` |

Hoje o despacho passa **`0` para os seis**.

A TBH da home está em `0x00D00FBA` (`cmp r3, #0xb`, 12 entradas). Cada
entrada foi mapeada para a página que abre.

---

## O que isso explica

| item | `sub` passado | efeito |
|---|---|---|
| **Pastas** | 0, e o certo é 0 | **acerta por acidente** — abre bem; o defeito de voltar é outro |
| **Gravação, Rádio** | errado | funcionam mesmo assim — essas páginas ignoram o parâmetro |
| **Imagem, Livro digital** | errado | **a biblioteca não atualiza, a tela fica vazia** |
| **Bluetooth** | errado | **reinicia o aparelho** |

**Não são quatro defeitos. É um.**

---

## Por que o conserto da Beta 10 não resolveu

A Beta 10 forçou `r2=6` **na cauda do despacho** (`0x00DA6230`). Mas para
Imagem e Livro digital a cauda **nunca executa**: a preparação deles
salta direto para `0x00D01036` e abre a página de lá.

O conserto alcançava metade dos itens. E, por motivo ainda desconhecido,
**quebrou os seis** — ver `BLUETOOTH_REINICIA.md`.

---

## O conserto correto — NÃO ESCRITO

Reescrever o campo `[r4, #0xc]` da mensagem **antes** de chamar a
preparação, usando uma tabela de 6 bytes na área livre:

```asm
; logo após  mov r5, r2  em 0x00DA6206
ldr  r3, =tabela_sub
ldrb r3, [r3, r5]
strh r3, [r4, #0xc]
```

Assim vale para os **dois** caminhos — o que passa pela cauda e o que
salta de `0x00D01036`. É menor e mais central que o da Beta 10.

> ⚠️ **Não escrever isto antes de saber por que a Beta 10 falhou.** É o
> mesmo despacho, a mesma classe de alteração. A **Beta 13** responde
> essa pergunta.
