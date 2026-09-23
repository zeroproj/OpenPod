# Bluetooth quebrado — CAUSA ENCONTRADA

> 2026-09-19. Duas correções minhas antes do diagnóstico:
>
> 1. Eu escrevi "defeito de fábrica". **Errado** — de fábrica funciona.
> 2. Eu reverti "a região do Bluetooth" `0x00D28000`–`0x00D2B000` e
>    concluí que a causa estava fora. **Aquela faixa nunca foi só do
>    Bluetooth**: ela contém as páginas 12, 16, 17, 35, 47 e 48. O teste
>    não testou o que eu disse que testava.

## A causa

O Extras abre o Bluetooth com **argumentos errados**.

### Como a tela inicial de fábrica abre

```asm
0x00D012D6   movs r3, #0x23     ; página 35
             movs r2, #6        ; índice do item na home
             b    0xd0123e
0x00D0123E   movs r1, #2
             b    0xd011f2
0x00D011F2   pop {r4,r5,r6,r7,r8,lr}
             b.w  0xd0dae0      ; abre
```

### Como o nosso despacho do Extras abre

```asm
0x00DA622C   ldrb r3, [tabela_C, r5]   ; r3 = 35     ✓
             movs r2, #0               ;             ✗ fábrica usa 6
             ldrh r1, [r4, #0xa]       ;             ✗ fábrica usa 2
             ldrh r0, [r4, #8]
             b.w  0xd0dae0
```

A página está certa. Os argumentos não.

## O padrão de fábrica, levantado nos doze itens da home

```text
página 35 (Bluetooth)    r1=2   r2=6
página 40 (Configurar)   r1=2   r2=7
página 30                r1=2   r2=11
```

`r1` é sempre **2**; `r2` é o **índice do item na home de fábrica**.

## Os dois tipos de item, e por que só o Bluetooth quebrou

| tipo | abertura | itens do Extras |
|---|---|---|
| **A** | verifica, prepara, `b 0xd01036` | Gravação, Rádio, Livro digital, Imagem, Pastas |
| **B** | `movs r3,#pág; movs r2,#índice; movs r1,#2` | **Bluetooth** |

Os cinco do tipo A já têm rotina de preparação no nosso despacho. O
Bluetooth é o **único do tipo B**, e o que ele precisa não é preparação
— são argumentos.

> **Nota histórica:** esse mesmo `r2` (o "sub") já quebrou o Configurar
> nas Core 4.8/4.9, e a DIAG 7 provou que era ele. Ali o efeito foi a
> página não abrir; aqui é reiniciar.

## O conserto — 8 bytes, NÃO ESCRITO

```asm
cmp  r5, #4          ; índice do Bluetooth
bne  segue
movs r1, #2
movs r2, #6
segue:
```

Não toca nos outros cinco: o `cmp` desvia antes.

Falta achar espaço contíguo na área livre depois da rotina — a cauda
atual está apertada entre saltos.

## Estado

**Causa confirmada por leitura. Conserto não escrito, não testado.**

---

## O conserto dos argumentos FALHOU — e eu não sei por quê

> 2026-09-20. Gravado nas Betas 10 e 11. **Quebrou os seis itens do
> Extras** — nada abre, o aparelho fica preso na tela. Retirado na
> Beta 12.

### O que eu escrevi

Os 4 bytes de `movs r2,#0 ; ldrh r1,[r4,#0xa]` em `0x00DA6230` viraram
um `b.w` para uma rotina de 22 bytes em `0x00DA6112`:

```asm
movs r2, #0
ldrh r1, [r4, #0xa]
cmp  r5, #4
bne  sai
movs r1, #2
movs r2, #6
sai:
ldrh r0, [r4, #8]
pop.w {r4,r5,r6,r7,r8,lr}
b.w  0xd0dae0
```

### O que eu conferi, e que estava certo

| | |
|---|---|
| a desmontagem da rotina | instrução a instrução, igual ao pretendido |
| o `b.w` da cauda | capstone lê `b.w #0xda6112`, alcance folgado |
| a área de destino | só continha a string morta `"OpenPod Core 3.3"`, terminada antes de `0x00DA6112`. **Nenhum ponteiro e nenhum salto** apontavam para lá |
| as três tabelas | `A`, `B`, `C` byte a byte iguais às da Beta 8 |
| os três pools | `0x00DA6248`, `0x00DA624C`, `0x00DA6250` inalterados |
| `check_branch_targets` | APROVADO |
| o diff | **só os 4 bytes da cauda** mudaram naquela região |

E mesmo assim não funciona.

### O que eu NÃO conferi, e devia

**`check_pilha.py` reportou 0 ganchos.** Ele procura saltos *do
firmware* para a área livre; o meu vai de área livre para área livre.
**Ele nunca verificou esta rotina**, e eu registrei isso como ressalva
em vez de tratar como lacuna.

### Hipóteses para a próxima tentativa

1. **`r5` não vale o índice naquele ponto em todos os caminhos.** O
   código original lê `r5` em `0x00DA622E`, então ele vale ali — mas
   pode não valer depois do `blx r3` em todos os itens.
2. **O `b.w` para trás dentro da área livre** tem algum efeito que eu
   não modelei — alinhamento, ou a região não ser executável do jeito
   que presumo.
3. **`r1=2, r2=6` não é o que a página 35 espera** quando chamada com
   `r0` vindo da mensagem em vez do valor que a home usa.

### Regra que fica

**Não reescrever isto sem antes provar, por diagnóstico isolado, que
uma rotina alcançada por `b.w` a partir da área livre executa.** Foi o
único elo que eu nunca verifiquei, e é o mais provável.

---

## RESPOSTA DA BETA 13 — 2026-09-21

A Beta 13 (mesmo salto, destino = cauda original, sem lógica) **funciona
nos seis itens** — relato do mantenedor no aparelho. Portanto:

- **Hipótese 2 REFUTADA.** O `b.w` para a área livre executa, e a rotina
  de destino roda e retorna corretamente.
- **A causa da Beta 10 era a lógica adicionada** (hipóteses 1/3): o
  `cmp r5,#4` com `r5` possivelmente corrompido após o `blx r3`, ou os
  argumentos `r1=2,r2=6` aplicados a páginas que não os esperam.

O conserto do `sub` (`docs/EXTRAS_INDICE.md`) foi escrito e testado na
Beta 14, mas se mostrou **insuficiente**: Bluetooth continuou
reiniciando nas opções. A hipótese atual é que, além do `sub`, a
**origem** (`r0`) da mensagem do Extras também está errada. Investigação
em aberto; voltar para Beta 12 como uso diário.
