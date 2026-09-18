#!/usr/bin/env python3
"""
diag_topo_pilha.py — DIAG 3: qual e o topo da pilha no momento do voltar?

O QUE JA SABEMOS
    DIAG 1 (voltar com pilha vazia -> Configurar): caiu na tela inicial,
           entao a pilha NAO estava vazia.
    DIAG 2 (toda saida do pop -> Configurar): caiu em Configurar, entao
           o voltar USA o desempilhador 0x00D0DA64.

    Logo: a pilha tinha algo, e esse algo nao era 0x53 -- ou era, e
    alguem sobrescreve o destino depois. Falta separar as duas.

COMO
    Nao reescreve o desempilhador. Intercepta a CHAMADA dele dentro de
    0x00D0E138 (o navegador com voltar, 77 chamadores):

        0x00D0E142  bl #0x00D0DA64   ->   bl <rotina na area livre>

    A rotina chama o desempilhador de verdade e so traduz o resultado:

        se devolveu 0x53  ->  devolve 0x28 (Configurar)
        senao             ->  devolve o valor original, intacto

LEITURA DO RESULTADO
    voltar de um item do Extras cai em CONFIGURAR
        -> o topo ERA 0x53. O desempilhador funciona e o problema esta
           DEPOIS dele: alguem sobrescreve o destino.
    voltar cai na TELA INICIAL
        -> o topo era 1. O 0x53 nunca chegou ao topo, ou foi consumido
           antes. O conserto e no empilhamento.

    O resto da navegacao fica NORMAL -- so o valor 0x53 e traduzido.
    E o diagnostico menos invasivo dos tres.

USO
    python3 tools/diag_topo_pilha.py entrada.bin saida.bin
"""
import sys

BASE_XIP = 0x00C00000
CHAMADA  = 0x00D0E142        # o `bl #0x00D0DA64` dentro de 0x00D0E138
POP_REAL = 0x00D0DA64
ROTINA   = 0x00DA6900        # area livre, setor do roteador
ALVO     = 0x53              # o valor que queremos flagrar
FLAG     = 0x28              # Configurar


def bl(origem, destino):
    off = destino - (origem + 4)
    assert -(1 << 24) <= off < (1 << 24) and off % 2 == 0
    off >>= 1
    s = (off >> 23) & 1
    i1, i2 = (off >> 22) & 1, (off >> 21) & 1
    w1 = 0xF000 | (s << 10) | ((off >> 11) & 0x3FF)
    w2 = 0xD000 | (((~i1 & 1) ^ s) << 13) | (((~i2 & 1) ^ s) << 11) | (off & 0x7FF)
    return w1.to_bytes(2, "little") + w2.to_bytes(2, "little")


def main():
    if len(sys.argv) != 3:
        sys.exit("uso: diag_topo_pilha.py <entrada.bin> <saida.bin>")
    img = bytearray(open(sys.argv[1], "rb").read())
    if len(img) != 2 * 1024 * 1024:
        sys.exit("erro: esperava 2 MiB")

    oc = CHAMADA - BASE_XIP
    if bytes(img[oc:oc + 4]) != bl(CHAMADA, POP_REAL):
        sys.exit(f"erro: {CHAMADA:#x} nao e o `bl {POP_REAL:#x}` esperado")

    r = ROTINA
    c = bytearray()
    c += bytes.fromhex("00b5")                 # push {lr}
    c += bl(r + 2, POP_REAL)                   # bl   desempilhador real
    c += (0x2800 | ALVO).to_bytes(2, "little") # cmp  r0, #0x53
    c += bytes.fromhex("00d1")                 # bne  -> pop (devolve intacto)
    c += (0x2000 | FLAG).to_bytes(2, "little") # movs r0, #0x28
    c += bytes.fromhex("00bd")                 # pop  {pc}

    orr = ROTINA - BASE_XIP
    if any(b != 0xFF for b in img[orr:orr + len(c)]):
        sys.exit(f"erro: {ROTINA:#x} nao esta apagado")
    img[orr:orr + len(c)] = c
    img[oc:oc + 4] = bl(CHAMADA, ROTINA)

    open(sys.argv[2], "wb").write(img)
    print(f"  {CHAMADA:#010x}  bl {POP_REAL:#x}  ->  bl {ROTINA:#x}")
    print(f"  rotina em {ROTINA:#010x}, {len(c)} bytes")
    print(f"\n  topo {ALVO:#04x} -> vai para {FLAG:#04x} (Configurar)")
    print(f"  qualquer outro topo -> comportamento normal")
    print(f"  escrito: {sys.argv[2]}")


if __name__ == "__main__":
    main()
