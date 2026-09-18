#!/usr/bin/env python3
"""
patch_voltar_extras.py — o voltar de um item do Extras retorna ao Extras

O MECANISMO, medido por cinco diagnosticos na tela
    O voltar usa uma PILHA (0x00823D05: entradas de 5 B em +0x0C,
    profundidade em +0x57). Toda abertura de pagina EMPILHA a origem;
    o voltar DESEMPILHA (0x00D0DA64) e abre o que sair.

    Funciona perfeitamente no firmware de fabrica: Configurar ->
    Despertador -> voltar volta para Configurar, em cima do Despertador.

O DEFEITO
    Ao abrir um item pelo Extras, a pagina empilha `1` (a home) por
    conta propria. O `0x53` que o nosso despacho empilha antes fica por
    baixo, e o voltar desempilha o `1`.

    DIAG 4: a Pastas foi a unica a obedecer a nossa empilhada -- ela e a
            unica que NAO usa a maquina normal de paginas, entao nao
            empilha por cima.
    DIAG 5: forcando TODA empilhada a guardar 0x53, os seis voltam para
            o Extras. Confirma que elas empilham, e que o valor e o
            problema.

A CORRECAO
    Uma regra, no empilhador: **se a pagina a empilhar e `1` e o topo da
    pilha ja e `0x53`, nao empilha.**

    Assim o `0x53` do nosso despacho sobrevive, e o voltar o encontra.
    Toda outra navegacao fica intacta -- a condicao so e verdadeira
    logo depois de o despacho do Extras ter empilhado.

    E o mesmo espirito da protecao contra duplicata que o proprio
    empilhador ja tem em 0x00D0DA12.

USO
    python3 tools/patch_voltar_extras.py entrada.bin saida.bin

LIMITACOES
    - Nao ajuda a Pastas, que usa outro mecanismo (0x00D3EBAC).
    - Se algum dia uma tela legitima empilhar `1` tendo `0x53` no topo,
      essa empilhada e perdida.
"""
import struct
import sys

BASE_XIP = 0x00C00000
GANCHO   = 0x00D0D9F2        # `mov r6, r0` + `bls #0x00D0DA04`
ESPERADO = bytes.fromhex("064606d9")
SEGUE    = 0x00D0DA04        # destino do `bls` original
ERRO     = 0x00D0D9F6        # o caminho de "pilha cheia"
GLOBAL   = 0x00823D05
ROTINA   = 0x00DA6A00
PAG_EXTRAS = 0x53


def bw(origem, destino, link=False):
    off = destino - (origem + 4)
    assert -(1 << 24) <= off < (1 << 24) and off % 2 == 0
    off >>= 1
    s = (off >> 23) & 1
    i1, i2 = (off >> 22) & 1, (off >> 21) & 1
    w1 = 0xF000 | (s << 10) | ((off >> 11) & 0x3FF)
    w2 = (0xD000 if link else 0x9000) | (((~i1 & 1) ^ s) << 13) \
        | (((~i2 & 1) ^ s) << 11) | (off & 0x7FF)
    return w1.to_bytes(2, "little") + w2.to_bytes(2, "little")


def main():
    if len(sys.argv) != 3:
        sys.exit("uso: patch_voltar_extras.py <entrada.bin> <saida.bin>")
    img = bytearray(open(sys.argv[1], "rb").read())
    if len(img) != 2 * 1024 * 1024:
        sys.exit("erro: esperava 2 MiB")
    og = GANCHO - BASE_XIP
    if bytes(img[og:og + 4]) != ESPERADO:
        sys.exit(f"erro: {GANCHO:#x} nao tem `mov r6,r0 / bls` "
                 f"(achei {img[og:og+4].hex()})")

    r = ROTINA
    c = bytearray()
    def h(v): c.extend(v.to_bytes(2, "little"))

    #  r0 = pagina a empilhar, r4 = profundidade, r5 = base da struct.
    #  As flags de `cmp r4,#0xd` (em 0x00D0D9F0) sao perdidas aqui, entao
    #  o teste de pilha cheia e refeito no fim.
    h(0x4606)                       # mov  r6, r0          (o original)
    h(0x2801)                       # cmp  r0, #1          e a home?
    pend = []
    pend.append((len(c), r + len(c), 0xD100, "fim")); h(0xD100)   # bne FIM
    h(0x2C00)                       # cmp  r4, #0          pilha vazia?
    pend.append((len(c), r + len(c), 0xD000, "fim")); h(0xD000)   # beq FIM
    p_lit = len(c); a_lit = r + len(c); h(0x4B00)                 # ldr r3,=GLOBAL
    h(0x1E62)                       # subs r2, r4, #1
    h(0xEB02); h(0x0282)            # add.w r2, r2, r2, lsl #2
    h(0x189A)                       # adds r2, r3, r2
    h(0x7B13)                       # ldrb r3, [r2, #0xc]  o topo
    h(0x2B53)                       # cmp  r3, #0x53
    pend.append((len(c), r + len(c), 0xD100, "fim")); h(0xD100)   # bne FIM
    # O hospedeiro (0x00D0D9E8) entra com `push {r4,r5,r6,lr}`. Esta
    # rotina e alcancada por `b.w`, entao HERDA esse frame: sair por
    # `bx lr` volta sem desfazer o push -- pilha desbalanceada, e o
    # aparelho reinicia. Foi o que a Core 4.5 fez.
    # O caminho equivalente do firmware (0x00D0DA50) sai assim:
    h(0xBD70)                       # pop  {r4, r5, r6, pc}  <- NAO empilha
    rot_fim = r + len(c)
    h(0x2C0D)                       # FIM: cmp r4, #0xd   (refaz o teste)
    # `bls` curto nao alcanca 0x00D0DA04, entao inverte-se a condicao:
    # `bhi` pula o b.w do caminho normal e cai no do erro.
    h(0xD801)                       # bhi  -> o b.w de ERRO
    c += bw(r + len(c), SEGUE)      # b.w  0x00D0DA04   (pilha com espaco)
    c += bw(r + len(c), ERRO)       # b.w  0x00D0D9F6   (pilha cheia)
    while len(c) % 4:
        h(0xBF00)
    a_pool = r + len(c)
    c += GLOBAL.to_bytes(4, "little")
    # resolve os desvios e o literal
    for pos, addr, op, _ in pend:
        off = (rot_fim - (addr + 4)) // 2
        assert 0 <= off <= 127, hex(off)
        c[pos:pos + 2] = (op | off).to_bytes(2, "little")
    imm = a_pool - ((a_lit + 4) & ~3)
    assert 0 <= imm <= 0x3FC and imm % 4 == 0, hex(imm)
    c[p_lit:p_lit + 2] = (0x4B00 | (imm // 4)).to_bytes(2, "little")

    orr = ROTINA - BASE_XIP
    if any(b != 0xFF for b in img[orr:orr + len(c)]):
        sys.exit(f"erro: {ROTINA:#x} nao esta apagado")
    img[orr:orr + len(c)] = c
    img[og:og + 4] = bw(GANCHO, ROTINA)

    open(sys.argv[2], "wb").write(img)
    print(f"  {GANCHO:#010x}  mov r6,r0 / bls  ->  b.w {ROTINA:#x}")
    print(f"  rotina em {ROTINA:#010x}, {len(c)} bytes")
    print(f"\n  regra: empilhar 1 com 0x53 no topo -> nao empilha")
    print(f"  escrito: {sys.argv[2]}")


if __name__ == "__main__":
    main()
