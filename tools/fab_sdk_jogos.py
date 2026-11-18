#!/usr/bin/env python3
"""fab_sdk_jogos.py - put the Reload 3.1 C SDK into the 3.0 image.

Usage:
    python3 tools/fab_sdk_jogos.py --in reload_3.0.bin --out 3.1.bin \
        --variante diag|jogos

Premises checked BEFORE writing (the tool refuses and leaves no output):
  - input is exactly the 3.0 image (sha256 43aaf5d5...);
  - the factory call at 0xD23CF8 is still bl 0xD2F0A0;
  - the 3.0 Apps stub at 0x1011AE is the expected one;
  - the whole free area 0x1AB000..0x1FC000 is 0xFF.
The tool writes only the SDK binary at 0x1AB000 and the 4-byte BL at
0x123CF8.  Nothing below 0xE000, the 0xD000 sector or the PSMP changes.
"""
import argparse
import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_sdk

TAMANHO = 0x200000
SHA_3_0 = "43aaf5d51c364e03f9934aba0348230dda4911c2e7264c34555f69554c36ec32"
LOTE_INI = 0x001AB000
LOTE_FIM = 0x001FC000
GANCHO = 0x00D23CF8
GANCHO_OFF = GANCHO - 0x00C00000
FABRICA = 0x00D2F0A0
GANCHO_FABRICA = bytes.fromhex("0bf0d2f9")
STUB = 0x001011AE
STUB_3_0 = bytes.fromhex("53230022022101201ce0")
PSMP = 0x001FC000


def sha(d):
    return hashlib.sha256(d).hexdigest()


def dec_bl(d, addr):
    """Decode a Thumb-2 BL (T1 encoding).

    imm32 = SignExtend(S:I1:I2:imm10:imm11:'0'), with I1 = NOT(J1 XOR S)
    and I2 = NOT(J2 XOR S).  Getting the I bits wrong only shows up when
    S = 1 (a backward branch): the decode comes out 0xC00000 off, which
    would accept a BL that the CPU reads as another address entirely.
    """
    off = addr - 0x00C00000
    h1, h2 = struct.unpack_from("<HH", d, off)
    if (h1 & 0xF800) != 0xF000 or (h2 & 0xD000) != 0xD000:
        return None
    s = (h1 >> 10) & 1
    j1, j2 = (h2 >> 13) & 1, (h2 >> 11) & 1
    i1, i2 = 1 - (j1 ^ s), 1 - (j2 ^ s)
    imm = (s << 24) | (i1 << 23) | (i2 << 22) | ((h1 & 0x3FF) << 12) | ((h2 & 0x7FF) << 1)
    if imm & (1 << 24):
        imm -= 1 << 25
    return (addr + 4 + imm) & 0xFFFFFFFF


def enc_bl(de, para):
    off = para - (de + 4)
    if not -(1 << 24) <= off < (1 << 24):
        raise ValueError(f"0x{de:08X} -> 0x{para:08X} fora do alcance do bl")
    s = (off >> 24) & 1
    i1, i2 = (off >> 23) & 1, (off >> 22) & 1
    j1, j2 = 1 - (i1 ^ s), 1 - (i2 ^ s)
    h1 = 0xF000 | (s << 10) | ((off >> 12) & 0x3FF)
    h2 = 0xD000 | (j1 << 13) | (j2 << 11) | ((off >> 1) & 0x7FF)
    return struct.pack("<HH", h1, h2)


def mesma_entrada(src, dst):
    if os.path.abspath(src) == os.path.abspath(dst):
        return True
    if not os.path.lexists(dst):
        return False
    try:
        return os.path.samefile(src, dst)
    except OSError:
        return False


def confere(d, variante):
    erros = []
    if len(d) != TAMANHO:
        return [f"a imagem tem {len(d)} bytes, esperado {TAMANHO}"]
    got = sha(d)
    if got != SHA_3_0:
        erros.append(f"sha256 {got}; a entrada tem de ser a 3.0 {SHA_3_0}")
    if d[GANCHO_OFF:GANCHO_OFF + 4] != GANCHO_FABRICA:
        erros.append(f"o bl em 0x{GANCHO:08X} nao e o de fabrica {GANCHO_FABRICA.hex()}")
    else:
        alvo = dec_bl(d, GANCHO)
        if alvo != FABRICA:
            erros.append(f"0x{GANCHO:08X} aponta para 0x{alvo:08X}, esperado 0x{FABRICA:08X}")
    if d[STUB:STUB + 10] != STUB_3_0:
        erros.append(f"o stub 3.0 em 0x{STUB:06X} nao confere")
    if any(b != 0xFF for b in d[LOTE_INI:LOTE_FIM]):
        erros.append(f"a area livre 0x{LOTE_INI:06X}..0x{LOTE_FIM:06X} nao e toda 0xFF")
    return erros


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="entrada", required=True)
    ap.add_argument("--out", dest="saida", required=True)
    ap.add_argument("--variante", choices=("diag", "jogos"), required=True)
    ap.add_argument("--em", help="lote declarado no MAPA (0x1AB000)")
    ap.add_argument("--build-dir", default=os.path.join(build_sdk.SDK, "build", "sdk"))
    a = ap.parse_args()

    if a.em is not None and int(a.em, 0) != LOTE_INI:
        sys.exit(f"PARE: --em {a.em} difere do lote 0x{LOTE_INI:06X}")
    if mesma_entrada(a.entrada, a.saida):
        sys.exit("PARE: --out igual/symlink/hardlink de --in")

    d = open(a.entrada, "rb").read()
    erros = confere(d, a.variante)
    if erros:
        print("PARE: premissas nao conferem; nada foi escrito.")
        for e in erros:
            print("  -", e)
        return 1

    info, binf = build_sdk.build(a.variante, os.path.abspath(a.build_dir))
    app = open(binf, "rb").read()
    hook = info["hook"]
    if info["size"] != len(app) or len(app) > LOTE_FIM - LOTE_INI:
        sys.exit("PARE: tamanho do SDK fora do lote")
    if not (LOTE_INI <= info["flash_offset"] < LOTE_FIM):
        sys.exit("PARE: offset de carga fora do lote")
    if hook < 0x00DAB000 or hook >= 0x00DAB000 + len(app) or (hook & 1):
        sys.exit(f"PARE: gancho 0x{hook:08X} invalido")

    novo = bytearray(d)
    novo[LOTE_INI:LOTE_INI + len(app)] = app
    novo[GANCHO_OFF:GANCHO_OFF + 4] = enc_bl(GANCHO, hook)

    # Only the lot and the 4 hook bytes may differ.
    dif = [i for i in range(TAMANHO) if novo[i] != d[i]]
    permitido = set(range(LOTE_INI, LOTE_INI + len(app)))
    permitido |= set(range(GANCHO_OFF, GANCHO_OFF + 4))
    fora = [i for i in dif if i not in permitido]
    if fora:
        sys.exit(f"PARE: escreveu fora do lote/gancho em 0x{min(fora):06X}")
    if min(dif, default=TAMANHO) < 0xE000:
        sys.exit("PARE: escreveu abaixo de 0xE000")
    if any(0xD000 <= i < 0xE000 for i in dif):
        sys.exit("PARE: tocou o setor 0xD000")
    if any(i >= PSMP for i in dif):
        sys.exit("PARE: tocou a PSMP")
    if dec_bl(novo, GANCHO) != hook:
        sys.exit("PARE: o bl gravado nao decodifica de volta")

    with open(a.saida, "wb") as f:
        f.write(novo)
    print(f"SDK {a.variante}: {len(app)} bytes em 0x{LOTE_INI:06X}; "
          f"bl 0x{GANCHO:08X} -> 0x{hook:08X}; sha {sha(novo)[:16]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
