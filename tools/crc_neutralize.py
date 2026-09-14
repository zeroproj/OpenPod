#!/usr/bin/env python3
"""
crc_neutralize.py — Faz o CRC da FIRM voltar ao valor ORIGINAL ajustando
                    2 bytes de padding morto DENTRO da propria FIRM.

POR QUE ISTO EXISTE

    O campo de CRC da FIRM mora na tabela de particoes, em
    `ptable + 0x1C` (arquivo 0x00D01C). Toda versao que mudava a FIRM
    obrigava a regravar o setor 0x00D000 -- e esse setor guarda, 8 bytes
    antes, o ponteiro que o bootloader segue para achar o firmware:

        ptable + 0x14 = 0x0000E000

    Flash NOR nao escreve 2 bytes: apaga 4096 e reescreve. Foi nessa
    janela que a gravacao do V028 falhou, e o primeiro GN-438 do projeto
    morreu. Detalhe em `docs/INCIDENTE_V028.md`.

A IDEIA

    CRC-16 e uma funcao AFIM sobre GF(2): mudar bytes da mensagem muda o
    CRC de forma linear. Entao, depois de aplicar o patch de verdade, da
    para escolher 2 bytes num pedaco morto da FIRM que levam o CRC de
    volta ao valor que ja esta gravado na tabela de particoes.

    Resultado: **o setor 0x00D000 nunca mais precisa ser tocado.**

    Nao e trapaca -- o CRC continua correto para o conteudo real. E o
    mesmo argumento de qualquer campo de ajuste: o dado e valido, so
    escolhemos a folga para bater o valor.

ONDE FICAM OS 2 BYTES

    Ha 133.602 bytes de 0x00 seguidos dentro da FIRM, em
    0x018A8E..0x039470. O padrao escolhido e 0x00037716, no meio da maior
    lacuna sem nenhum endereco referenciado por perto: 2.325 bytes de
    folga de cada lado.

    Se o patch ja sujar um setor que tenha padding utilizavel, prefira
    esse -- assim nao se acrescenta setor nenhum a gravacao.

USO
    python3 tools/crc_neutralize.py \
        --in  firmware/WORKING/GN438_openpod_v030.bin \
        --out firmware/WORKING/GN438_openpod_v030n.bin [--pad 0x37716] [--dry-run]

DEPENDENCIAS
    Python 3 + tools/fw_common.py

SEGURANCA
    - recusa se origem == destino;
    - recusa se os 2 bytes escolhidos nao estiverem zerados;
    - recusa se houver dado nao-zero a menos de 64 B do ponto escolhido;
    - recusa se o CRC resultante nao bater EXATAMENTE com o alvo;
    - a entrada e aberta somente para leitura; a saida e arquivo novo.

LIMITACAO
    Muda o conteudo de uma regiao que o projeto **acredita** ser morta.
    217 valores de 32 bits da imagem caem dentro da faixa grande, quase
    certamente por coincidencia; por isso o padrao fica a 2.325 B do mais
    proximo deles. Classificacao: PROVAVEL, nao CONFIRMADO. Confirmar no
    aparelho novo antes de adotar como padrao.
"""

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fw_common as fw

FOFF, FLEN = 0x00E000, 0x192570
CRC_ORIGINAL = 0x49A6
PAD_PADRAO = 0x00037716
FOLGA = 64


def firm_crc(img):
    return fw.crc16(bytes(img[FOFF:FOFF + FLEN]))


def resolve(img, pad, alvo):
    """Acha o valor de 16 bits em `pad` que leva o CRC da FIRM a `alvo`.

    Usa a linearidade do CRC: 17 varreduras da FIRM em vez de 65536.
    """
    d = bytearray(img)
    d[pad] = d[pad + 1] = 0
    base = firm_crc(d)
    col = []
    for bit in range(16):
        v = 1 << bit
        d[pad], d[pad + 1] = v & 0xFF, (v >> 8) & 0xFF
        col.append(firm_crc(d) ^ base)
        d[pad] = d[pad + 1] = 0
    tgt = alvo ^ base
    for x in range(0x10000):
        acc, y, i = 0, x, 0
        while y:
            if y & 1:
                acc ^= col[i]
            y >>= 1
            i += 1
        if acc == tgt:
            return x
    return None


def main():
    ap = argparse.ArgumentParser(
        description="Devolve o CRC da FIRM ao original via 2 bytes de padding")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--pad", type=lambda s: int(s, 0), default=PAD_PADRAO)
    ap.add_argument("--alvo", type=lambda s: int(s, 0), default=CRC_ORIGINAL)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if os.path.abspath(a.src) == os.path.abspath(a.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2

    orig = open(a.src, "rb").read()
    d = bytearray(orig)
    pad = a.pad

    print("=" * 72)
    print("OpenPod — neutralizacao do CRC da FIRM")
    print("=" * 72)
    print(f"  origem : {a.src}")
    print(f"  destino: {a.dst}")
    print()

    erros = []
    if not FOFF <= pad < FOFF + FLEN - 1:
        erros.append(f"0x{pad:06X} esta fora da FIRM")
    elif any(b != 0 for b in d[pad - FOLGA:pad + FOLGA + 2]):
        erros.append(f"0x{pad:06X} tem dado nao-zero a menos de {FOLGA} B")
    if erros:
        print("  ABORTADO:")
        for m in erros:
            print(f"    - {m}")
        return 1

    antes = firm_crc(d)
    print(f"  CRC da FIRM agora : 0x{antes:04X}")
    print(f"  CRC alvo          : 0x{a.alvo:04X}  (o que ja esta na tabela"
          " de particoes)")
    if antes == a.alvo:
        print("\n  nada a fazer: o CRC ja bate.")
        return 0

    print(f"  ponto de ajuste   : 0x{pad:06X}  (setor 0x{pad // 0x1000 * 0x1000:06X})")
    print()
    x = resolve(d, pad, a.alvo)
    if x is None:
        print("  ABORTADO: nenhum par de bytes resolve. Tente outro --pad.",
              file=sys.stderr)
        return 1
    d[pad], d[pad + 1] = x & 0xFF, (x >> 8) & 0xFF
    depois = firm_crc(d)
    if depois != a.alvo:
        print(f"  ABORTADO: conferencia falhou (0x{depois:04X}).", file=sys.stderr)
        return 1

    print(f"  2 bytes gravados  : {d[pad]:02X} {d[pad+1]:02X}")
    print(f"  CRC da FIRM agora : 0x{depois:04X}   == alvo   OK")
    print()
    print("  >>> a tabela de particoes (0x00D000) NAO precisa ser gravada.")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores tocados por esta etapa: "
          + "  ".join(f"0x{s:06X}" for s in secs))
    print()

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
