# O "voltar" — a pilha de navegação

> Medido em 2026-09-18, ao tentar fazer o voltar de um item do Extras
> retornar ao Extras em vez da tela inicial.
>
> **RESOLVIDO na Core 4.6**, em 2026-09-18, depois de cinco
> diagnósticos na tela. Ver `docs/CHANGELOG.md`.
>
> Este documento foi escrito quando o defeito estava aberto. O
> mecanismo descrito abaixo está confirmado; a seção 2 registra a
> tentativa que falhou e por quê.

---

## 1. O mecanismo — CONFIRMADO

O destino do voltar **não** vem da origem guardada na página. Vem de uma
**pilha de navegação** na struct global `0x00823D05`:

```text
+0x0C   base da pilha, entradas de 5 bytes
          byte 0     a página
          bytes 1-4  payload (copiado de +0x58)
+0x57   profundidade (máx 14)
```

### O desempilhador — `0x00D0DA64`

```asm
ldrb.w r3, [r4, #0x57]      ; profundidade
cbz    r3, +                ; VAZIA -> devolve 1, a TELA INICIAL
subs   r3, #1
add.w  r3, r3, r3, lsl #2   ; 5 bytes por entrada
ldr.w  r2, [r3, #0xd]       ; payload
ldrb   r5, [r3, #0xc]       ; a página
strb.w r3, [r4, #0x57]      ; decrementa
mov    r0, r5               ; devolve
```

**`cbz r3` é a origem do sintoma:** pilha vazia ⇒ tela inicial.

13 chamadores.

### O empilhador — `0x00D0D9E8(r0 = página)`

Máximo 14 níveis; se o topo já for a mesma página, **não empilha**
(proteção contra duplicata). **Um único chamador:** `0x00D0DC1A`.

### A cauda compartilhada — `0x00D0DC02`

```asm
strb r5, [r3, #0xb]    ; guarda a origem
strb r7, [r3, #0xa]    ; current_page = destino
adds r2, r4, #1
beq.w #0x00D0E0AC      ; <- desvio que PULA o push
uxtb r0, r4            ; r0 = origem
pop.w {...}
b.w  #0x00D0D9E8       ; empilha a origem
```

### Como uma página volta — `0x00D0E138`

```asm
mov r4, r0             ; página atual
bl  #0x00D0DA64        ; desempilha -> destino
uxth r3, r5
b.w #0x00D0DAE0        ; abre o destino
```

77 chamadores. Exemplo, no presenter da Imagem:

```asm
0x00D0397E  ldrh r2, [r4, #0xc]
0x00D03980  movs r1, #1
0x00D03986  b.w  #0x00D0E138
```

---

## 2. O que foi tentado, e falhou

**Core 4.4:** empilhar `0x53` explicitamente no despacho do Extras,
antes de abrir o item:

```asm
movs r0, #0x53
bl   #0x00D0D9E8
```

Resultado no aparelho: **o voltar continua indo para a tela inicial.**

---

## 3. O que NÃO está medido

1. **Por que a pilha chega vazia no voltar.** Como o despacho já passa
   origem `0x53`, a cauda `0x00D0DC02` deveria empilhar sozinha.
2. **Se o `beq.w 0x00D0E0AC` em `0x00D0DC0A` está sendo tomado**, o push
   é pulado. Ele testa `adds r2, r4, #1` — ou seja, origem `== -1`.
3. **Qual dos 13 chamadores do pop** roda entre abrir e voltar.

---

## 4. A próxima tentativa deve MEDIR, não supor

Três versões seguidas (4.0, 4.3, 4.4) foram hipóteses apresentadas com
confiança, e as três erraram. A saída não é uma quarta.

**Instrumentar:** mostrar na tela o valor de `0x00823D05 + 0x57` (a
profundidade) no momento do voltar. Isso responde (1) e (3) de uma vez.

Um caminho barato: repontar um rótulo já existente para um buffer na
área livre e escrever a profundidade nele em hexadecimal — o mesmo
mecanismo que `patch_versao.py` usa para a tela Informações.

---

## 5. Classificação

| Afirmação | Classe |
|---|---|
| O voltar usa uma pilha, não a origem da página | CONFIRMADO |
| Pilha vazia devolve 1 (tela inicial) | CONFIRMADO |
| `0x00D0D9E8` empilha, `0x00D0DA64` desempilha | CONFIRMADO |
| O push tem um único chamador (`0x00D0DC1A`) | CONFIRMADO |
| Empilhar `0x53` no despacho resolve | **REFUTADO** (Core 4.4) |
| As páginas empilham `1` por cima do nosso `0x53` | CONFIRMADO (DIAG 4 e 5) |
| Não deixar o `1` cobrir o `0x53` resolve | **CONFIRMADO** (Core 4.6) |
| Por que a pilha chega vazia | resposta: **não chegava vazia** — o topo era `1` |
