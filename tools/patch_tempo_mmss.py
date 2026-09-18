#!/usr/bin/env python3
"""
patch_tempo_mmss.py — os tempos da Tocando Agora viram mm:ss.

O QUE MUDA
    00:03:19  ->  03:19
    00:00:07  ->  00:07

    As horas sao sempre 00 numa faixa de musica. Gastar tres caracteres
    nelas numa tela de 128 px e desperdicio, e o Projeto Marte mostra
    mm:ss (1:04, -2:31).

COMO O FIRMWARE FORMATA HOJE

    movs  r2, #0x3c          ; 60
    udiv  r3, r4, r2         ; r3 = total/60      minutos totais
    mls   r0, r2, r3, r4     ; r0 = total - 60*r3 segundos
    udiv  r1, r3, r2         ; r1 = r3/60         horas
    mls   r3, r2, r1, r3     ; r3 = r3 - 60*r1    minutos
    mov.w r2, #0xe10         ; 3600
    udiv  r2, r4, r2         ; r2 = total/3600    horas
    ldr   r1, [pc, ...]      ; "%02d:%02d:%02d"
    bl    sprintf            ; (r2=h, r3=m, [sp]=s)

    Repare que r3 e r0 JA carregam minutos totais e segundos antes das
    quatro ultimas instrucoes. Elas existem so para quebrar em horas.

O CONSERTO
    Descartar a quebra em horas e passar o que ja esta calculado:

        mov r2, r3     ; r2 = minutos totais
        mov r3, r0     ; r3 = segundos
        nop x6

    E repontar o literal para "%02d:%02d", que JA EXISTE no firmware em
    0x00C4CD5D -- nenhuma string nova precisa ser criada.

    16 bytes por sitio, tres sitios, mais tres ponteiros. Nao mexe em
    pilha, nem em fluxo, nem em chamada. O `str r0,[sp]` que empilhava
    os segundos continua la e vira argumento extra ignorado.

USO
    python3 tools/patch_tempo_mmss.py --in <fw.bin> --out <novo.bin>

DEPENDENCIAS
    capstone

SEGURANCA
    - cada sitio so e aceito se os bytes baterem EXATAMENTE;
    - desmonta os tres de volta e confere a sequencia resultante;
    - confere que os tres ponteiros passaram a apontar para o formato
      curto.

LIMITACOES
    Os tres sitios sao chamados de dentro da faixa do presenter da
    Tocando Agora (0x00D088E0..0x00D09038). Se algum deles servir
    tambem a outra tela -- video, por exemplo -- aquela tela tambem
    passa a mostrar mm:ss. Efeito cosmetico, nunca travamento.
"""
import argparse
import struct
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

XIP = 0x00C00000
TAM = 2 * 1024 * 1024
LONGO = 0x00C4CD58    # "%02d:%02d:%02d"
CURTO = 0x00C4CD5D    # "%02d:%02d"

MOV_R2_R3 = bytes.fromhex("1a46")
MOV_R3_R0 = bytes.fromhex("0346")
NOP = bytes.fromhex("00bf")

# sitio -> (offset do bloco, bytes de fabrica, bytes novos)
def blocos():
    quebra = bytes.fromhex("b3fbf2f102fb11334ff46162b4fbf2f2")   # A e B
    novo_ab = MOV_R2_R3 + MOV_R3_R0 + NOP * 6
    quebra6 = bytes.fromhex("b6fbf2f2")                          # C, udiv r2,r6,r2
    return quebra, novo_ab, quebra6


POOLS = [0x00D08740, 0x00D087D4, 0x00D088B0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    a = ap.parse_args()

    d = bytearray(open(a.src, "rb").read())
    if len(d) != TAM:
        sys.exit("ABORTADO: %s tem %d bytes, esperado %d" % (a.src, len(d), TAM))

    quebra, novo_ab, _ = blocos()
    print("=" * 70)
    print("OpenPod — tempos da Tocando Agora: hh:mm:ss -> mm:ss")
    print("=" * 70)

    # --- sitios A e B: o bloco de quebra em horas e contiguo -----------
    feitos = []
    for base in (0x1086CE, 0x108762):
        if bytes(d[base:base + 16]) != quebra:
            sys.exit("ABORTADO: sitio 0x%08X nao bate com o padrao de fabrica."
                     % (base + XIP))
        d[base:base + 16] = novo_ab
        feitos.append(base)

    # --- sitio C: as quatro instrucoes estao intercaladas --------------
    c = 0x1087EE
    esperado = {
        c + 12: bytes.fromhex("b3fbf2f1"),   # udiv r1,r3,r2
        c + 18: bytes.fromhex("02fb1133"),   # mls  r3,r2,r1,r3
        c + 26: bytes.fromhex("4ff46162"),   # mov.w r2,#0xe10
        c + 30: bytes.fromhex("b6fbf2f2"),   # udiv r2,r6,r2
    }
    for off, esp in esperado.items():
        if bytes(d[off:off + 4]) != esp:
            sys.exit("ABORTADO: sitio C, offset 0x%08X nao bate." % (off + XIP))
    d[c + 12:c + 16] = MOV_R2_R3 + MOV_R3_R0
    for off in (c + 18, c + 26, c + 30):
        d[off:off + 4] = NOP * 2
    feitos.append(c)

    # --- os tres ponteiros de formato ---------------------------------
    trocados = 0
    for p in POOLS:
        o = p - XIP
        if struct.unpack_from("<I", d, o)[0] != LONGO:
            sys.exit("ABORTADO: o ponteiro em 0x%08X nao aponta para o "
                     "formato longo." % p)
        struct.pack_into("<I", d, o, CURTO)
        trocados += 1

    # --- conferencia por desmontagem ----------------------------------
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print()
    for base in (0x1086CE, 0x108762):
        ins = list(md.disasm(bytes(d[base:base + 8]), base + XIP))
        txt = ["%s %s" % (i.mnemonic, i.op_str) for i in ins[:2]]
        ok = txt == ["mov r2, r3", "mov r3, r0"]
        print("  0x%08X  %-14s %-14s %s" % (base + XIP, txt[0], txt[1],
                                            "OK" if ok else "NAO CONFERE"))
        if not ok:
            sys.exit("ABORTADO: nao desmontou como esperado. Nao gravei.")
    ins = list(md.disasm(bytes(d[c + 12:c + 16]), c + 12 + XIP))
    txt = ["%s %s" % (i.mnemonic, i.op_str) for i in ins[:2]]
    ok = txt == ["mov r2, r3", "mov r3, r0"]
    print("  0x%08X  %-14s %-14s %s" % (c + 12 + XIP, txt[0], txt[1],
                                        "OK" if ok else "NAO CONFERE"))
    if not ok:
        sys.exit("ABORTADO: sitio C nao desmontou como esperado.")

    print()
    print("  ponteiros de formato repontados: %d  (0x%08X -> 0x%08X)"
          % (trocados, LONGO, CURTO))
    orig = open(a.src, "rb").read()
    mudou = sum(1 for k in range(TAM) if d[k] != orig[k])
    setores = sorted({(o // 0x1000) * 0x1000
                      for o in list(feitos) + [p - XIP for p in POOLS]})
    print("  bytes alterados: %d   setores: %s"
          % (mudou, ", ".join("0x%06X" % s for s in setores)))
    open(a.dst, "wb").write(bytes(d))
    print("  gravado: %s" % a.dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
