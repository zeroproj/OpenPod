#!/usr/bin/env python3
"""
patch_bateria_casca.py — a casca da bateria ganha o prateado do Marte

A IDEIA, e por que ela e viavel
    O icone da bateria e um ROTULO com a fonte de icones (U+E626) mais um
    `lv_bar` filho. Rotulo tem COR DE TEXTO -- entao da para pintar a
    casca sem trocar o objeto.

    Isso NAO reproduz o bitmap do Marte (casca metalica com degrade):
    o glifo e monocromatico. Reproduz a COR dominante dele, que e o que
    da a leitura de "bateria prateada com nivel verde".

    Junto com a Core 5.2 (o verde do nivel), chega perto do alvo por
    6 bytes, sem objeto de imagem e sem codigo novo.

MEDIDO
    0x00D22622  bl   #0x00D21384   <- getter da cor do glifo
    0x00D22626  movs r2, #0
    0x00D22628  mov  r1, r0
    0x00D2262C  bl   #0x00D4D10A   (set_style_text_color)

    Os 8 bytes de 0x00D22622 a 0x00D22629 viram:
        movw r1, #<cor>    (4)
        movs r2, #0        (2)
        nop                (2)

    E o mesmo padrao que a Core 2.4 usou na CRIA_FAIXA: trocar o `bl` do
    getter por um imediato. Provado nesta imagem.

A COR
    marte/adaptado/icones/battery_09.png, o tom mais usado da casca:
    RGB(197,206,213). Pre-invertida (LV_COLOR_16_SWAP): 0x7AC6.

USO
    python3 tools/patch_bateria_casca.py entrada.bin saida.bin

LIMITACOES
    - A bateria FRACA continua vermelha: `view_set_icon_bat`
      (0x00D23666) pinta por cima em tempo de execucao. E desejavel.
    - O getter 0x00D21384 continua existindo; outros objetos seguem
      usando.
"""
import sys

BASE_XIP = 0x00C00000
SITIO    = 0x00D22622
ANTES    = bytes.fromhex("fef7affe" "0022" "0146")   # bl / movs r2,#0 / mov r1,r0
MARTE    = (197, 206, 213)


def to565(r, g, b):
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


def pre_inverte(v):
    return ((v & 0xFF) << 8) | (v >> 8)


def movw(rd, valor):
    imm4, i = (valor >> 12) & 0xF, (valor >> 11) & 1
    imm3, imm8 = (valor >> 8) & 7, valor & 0xFF
    w1 = 0xF240 | (i << 10) | imm4
    w2 = (imm3 << 12) | (rd << 8) | imm8
    return w1.to_bytes(2, "little") + w2.to_bytes(2, "little")


def main():
    import argparse
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--in", dest="src")
    ap.add_argument("--out", dest="dst")
    ap.add_argument("pos_src", nargs="?")
    ap.add_argument("pos_dst", nargs="?")
    a,_ = ap.parse_known_args()
    src = a.src or a.pos_src
    dst = a.dst or a.pos_dst
    if not src or not dst:
        sys.exit("uso: patch_bateria_casca.py <entrada.bin> <saida.bin> ou --in/--out")
    img = bytearray(open(src, "rb").read())
    if len(img) != 2 * 1024 * 1024:
        sys.exit("erro: esperava 2 MiB")
    off = SITIO - BASE_XIP
    if bytes(img[off:off + 8]) != ANTES:
        sys.exit(f"erro: {SITIO:#x} tem {img[off:off+8].hex()}, "
                 f"esperava {ANTES.hex()} — imagem errada?")

    cor = pre_inverte(to565(*MARTE))
    novo = movw(1, cor) + bytes.fromhex("0022") + bytes.fromhex("00bf")
    assert len(novo) == 8
    img[off:off + 8] = novo
    open(dst, "wb").write(img)
    print(f"  {SITIO:#010x}  bl getter  ->  movw r1, #{cor:#06x}")
    print(f"     a casca passa a ser RGB{MARTE} — o prateado do Marte")
    print(f"\n  escrito: {dst}")


if __name__ == "__main__":
    main()
