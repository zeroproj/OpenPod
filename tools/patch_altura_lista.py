#!/usr/bin/env python3
"""
patch_altura_lista.py — as listas passam a ocupar a tela toda.

O DEFEITO
    Seis paginas de lista reservam 96 px de altura para a lista, numa
    tela de 160 px com faixa de 16 px. Sobram 48 px de nada no rodape.

    O firmware calcula assim:

        bl    tela_altura          ; 160
        sdiv  r0, r0, r4           ; /10      = 16
        add.w r0, r0, r0, lsl #1   ; x3       = 48
        lsls  r1, r0, #1           ; x2       = 96
        bl    set_height

    E DE FABRICA -- conferido byte a byte contra o GN438_original.bin.
    Nao veio do nosso trabalho.

    Passou despercebido porque de fabrica as linhas tinham 22 px: 96 px
    davam 4 linhas e meia e a lista parecia cheia. Nos padronizamos as
    linhas em 16 px (Core 5.x), entao agora cabem 6 linhas nos mesmos
    96 px e sobram tres linhas vazias.

    Nos criamos o sintoma sem criar a causa.

    Custo real: Configurar tem 10 itens e mostra 6. Informacoes,
    Armazenamento, Atualizar por SD e Atualizar biblioteca exigem
    rolar -- e tres deles caberiam na tela.

O CONSERTO
    Muda so os multiplicadores. Para N linhas de 16 px:

        N=9  add.w r0,r0,r0,lsl #3   (x9)   movs r1,r0      (x1)  144 px
        N=8  add.w r0,r0,r0,lsl #0   (x2)   lsls r1,r0,#2   (x4)  128 px
        N=6  add.w r0,r0,r0,lsl #1   (x3)   lsls r1,r0,#1   (x2)   96 px  (fabrica)

    Um byte em cada instrucao. Doze bytes no firmware inteiro.

    9 linhas encostam na borda de baixo: 16 da faixa + 144 = 160.
    8 linhas deixam 16 px de folga. Se a nona linha cortar na tela,
    e so rodar de novo com --linhas 8.

USO
    python3 tools/patch_altura_lista.py \\
        --in  firmware/WORKING/GN438_beta3_carimbado.bin \\
        --out firmware/WORKING/GN438_lista_alta.bin [--linhas 9]

DEPENDENCIAS
    capstone (para conferir cada sitio antes e depois)

SEGURANCA
    - so aceita sitios onde as DUAS instrucoes batem com o esperado;
    - desmonta de volta cada sitio depois de escrever e confere que a
      instrucao ficou como pedido;
    - recusa se o numero de sitios nao for o esperado.
"""
import argparse
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

XIP = 0x00C00000
TAM = 2 * 1024 * 1024

# padrao de fabrica: add.w r0,r0,r0,lsl#1 ; lsls r1,r0,#1 ; sxth r1,r1
ANTES = bytes.fromhex("00eb4000410009b2")

# linhas -> (bytes novos das duas instrucoes, o que deve desmontar)
RECEITA = {
    9: (bytes.fromhex("00ebc000010009b2"),
        ["add.w\tr0, r0, r0, lsl #3", "movs\tr1, r0"]),
    8: (bytes.fromhex("00eb0000810009b2"),
        ["add.w\tr0, r0, r0", "lsls\tr1, r0, #2"]),
    6: (ANTES, ["add.w\tr0, r0, r0, lsl #1", "lsls\tr1, r0, #1"]),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--linhas", type=int, default=9, choices=sorted(RECEITA))
    a = ap.parse_args()

    d = bytearray(open(a.src, "rb").read())
    if len(d) != TAM:
        sys.exit("ABORTADO: %s tem %d bytes, esperado %d" % (a.src, len(d), TAM))

    novo, esperado = RECEITA[a.linhas]
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)

    sitios = []
    i = 0
    while True:
        i = d.find(ANTES, i)
        if i < 0:
            break
        sitios.append(i)
        i += 2

    print("=" * 72)
    print("OpenPod — altura das listas: 6 linhas -> %d linhas" % a.linhas)
    print("=" * 72)
    print("  tela 160 px · faixa 16 px · disponivel 144 px = 9 linhas de 16")
    print("  antes: 96 px (6 linhas), 48 px desperdicados")
    print("  agora: %d px (%d linhas)" % (a.linhas * 16, a.linhas))
    print()
    print("  sitios encontrados: %d" % len(sitios))
    if len(sitios) != 6:
        sys.exit("ABORTADO: esperava 6 sitios, achei %d. Nao escrevi nada." % len(sitios))

    for o in sitios:
        d[o:o + len(novo)] = novo

    # confere desmontando de volta
    print()
    for o in sitios:
        ins = list(md.disasm(bytes(d[o:o + 8]), o + XIP))
        txt = ["%s\t%s" % (x.mnemonic, x.op_str) for x in ins[:2]]
        ok = txt == esperado
        print("  0x%08X  %-34s %-18s %s"
              % (o + XIP, txt[0] if txt else "?", txt[1] if len(txt) > 1 else "?",
                 "OK" if ok else "NAO CONFERE"))
        if not ok:
            sys.exit("ABORTADO: o sitio 0x%08X nao desmontou como esperado. "
                     "Nao gravei." % (o + XIP))

    open(a.dst, "wb").write(bytes(d))
    orig = open(a.src, "rb").read()
    mudou = sum(1 for k in range(TAM) if d[k] != orig[k])
    setores = sorted({(o // 0x1000) * 0x1000 for o in sitios})
    print()
    print("  bytes alterados: %d   setores: %s"
          % (mudou, ", ".join("0x%06X" % s for s in setores)))
    print("  gravado: %s" % a.dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
