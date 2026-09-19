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
