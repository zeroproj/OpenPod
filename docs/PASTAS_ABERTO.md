# Pastas — o voltar, ainda ABERTO

> Última tentativa: Core 5.1, em 2026-09-18. **Não resolveu.**
> Este documento existe para a próxima tentativa começar de uma medição
> e não de uma teoria — a regra que fechou o voltar do Extras.

---

## 1. O sintoma

Entrar em **Pastas** pelo Extras e clicar voltar **imediatamente**: nada
acontece. Se você navegar para dentro de uma pasta primeiro, o voltar
passa a funcionar.

Mantenedor, em 4.4: *"consigo fazer tudo mas não consigo voltar, parece
que ele não sabe o que fazer"*. Em 4.6: *"só a pasta com bug chatinho,
que tem que navegar primeiro para voltar"*. E era **intermitente**.

---

## 2. O que está CONFIRMADO

A Pastas **não usa a máquina de páginas**. A abertura de fábrica (home
idx 8, `0x00D0128C`) termina assim:

```asm
ldr r3, =0x0081BE68
ldr r0, =0x00C4CA69        ; a string "0:" (raiz do cartão)
str.w r0, [r3, #0x100]     ; guarda o caminho em 0x0081BF68 (RAM)
movs r1, #2
pop.w {r4, r5, r6, r7, r8, lr}
b.w  #0x00D3EBAC           ; o navegador de arquivos
```

`0x00D3EBAC(r0 = caminho, r1 = 2)` — não é `0x00D0DAE0`.

O nosso despacho abre a **página `0x22`** pela primitiva normal.

---

## 3. O que foi tentado, e falhou

| | O quê | Resultado |
|---|---|---|
| **Core 4.3** | replicar a abertura inteira (checagens + contagem + a cauda acima) | a Pastas **parou até de abrir** |
| **Core 5.1** | manter a abertura e só escrever o contexto (`0x0081BF68 = "0:"`) antes | **não resolveu** |

A 5.1 era a hipótese mais forte e estava errada: escrever o caminho não
basta.

---

## 4. O que NÃO está medido

1. **O que o navegador guarda quando você navega para dentro** — é isso
   que faz o voltar passar a funcionar, e é a pista mais direta.
   `0x0081BE68` tem 14 referências na FIRM; vale mapear os outros campos
   além do `+0x100`.
2. **Como o voltar da Pastas decide o destino.** Ela não usa a pilha de
   navegação (`0x00D0DA64`) do resto do sistema — ou usa, e falha por
   falta de contexto.
3. **Por que era intermitente** na 4.4. Intermitência costuma indicar
   estado, não lógica.

---

## 5. A próxima tentativa deve MEDIR

Duas falhas seguidas neste mesmo item, as duas por hipótese. O caminho
que funcionou para o voltar do Extras foi **gastar gravações eliminando
hipóteses**, uma variável por vez, em vez de tentar consertos.

Sugestão concreta, no espírito das DIAG 1–7:

> Instrumentar `0x00D3EBAC` para revelar o que ele recebe, ou comparar
> o conteúdo de `0x0081BE68`+campos logo após abrir pela home (funciona)
> e logo após abrir pelo Extras (não funciona). A diferença é a resposta.

---

## 6. Classificação

| Afirmação | Classe |
|---|---|
| A Pastas abre por `0x00D3EBAC`, não pela primitiva de página | CONFIRMADO |
| A abertura de fábrica escreve o caminho em `0x0081BF68` | CONFIRMADO |
| Replicar a abertura inteira | **REFUTADO** (Core 4.3) |
| Escrever só o contexto | **REFUTADO** (Core 5.1) |
| O que o navegador precisa além do caminho | **NÃO RESOLVIDO** |
