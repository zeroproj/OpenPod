#!/usr/bin/env python3
"""
patch_barra_selecao.py — A selecao da home vira BARRA, nao cor de texto.

O MECANISMO

    Hoje a selecao chama `lv_obj_set_style_text_color` (0x00D4D10A):
    o item selecionado muda a cor da letra. Trocando o alvo da chamada
    para `lv_obj_set_style_bg_color` (0x00D4D092) -- mesma assinatura
    (obj, cor, seletor) -- o item ganha uma barra de fundo e o texto
    continua branco. E o realce do iPod nano.

        0x00D4D092   set_style_bg_color    propriedade 0x20
        0x00D4D0B4   set_style_bg_opa      propriedade 0x21
        0x00D4D10A   set_style_text_color  (o que era usado)

    Os numeros de propriedade batem com o enum da LVGL v8.

O QUE E ALTERADO

    selecao      0x0012EB4C   bl text_color -> bl bg_color
    desselecao   4 ramos de tecla, cada um com DOIS pontos:
                   bl 0xd2e948 (branco) -> bl 0xd2138a (preto)
                   bl text_color        -> bl bg_color
    largura      0x0012ED5E   0x64 (100) -> 0x74 (116)
    bg_opa       0x0012ED58   bl text_align -> bl <rotina na area livre>

    A rotina na area livre chama o text_align original e depois liga
    bg_opa = 255 no rotulo. Sem ela a cor de fundo nao aparece: um
    rotulo nasce com fundo transparente.

GEOMETRIA

    O rotulo fica em x = 6. Com largura 116 a barra vai de 6 a 122,
    simetrica nos dois lados, e cobre o chevron da linha selecionada --
    a opcao escolhida pelo mantenedor.

    Barra colada nas bordas (0..128) exigiria recuo interno, e os
    setters de PAD nao usam o mesmo caminho generico, entao nao foram
    localizados. **A largura e 1 byte: da para mudar depois.**

USO
    python3 tools/patch_barra_selecao.py \
        --in  firmware/WORKING/GN438_openpod_v026.bin \
        --out firmware/WORKING/GN438_openpod_v027.bin [--largura 116] [--dry-run]

SEGURANCA
    - recusa se qualquer ponto nao estiver no valor esperado;
    - decodifica de volta cada `bl` que gera e compara o alvo;
    - recusa se a area livre de destino nao estiver virgem.

ENDERECO EXPLICITO (--em)

    Sem ele o endereco depende da ordem. Ver `tools/build.py`.
"""
import argparse, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fw_common as fw

XIP = 0x00C00000
BG_COLOR, BG_OPA, TEXT_COLOR = 0x00D4D092, 0x00D4D0B4, 0x00D4D10A
BRANCO, PRETO, TEXT_ALIGN = 0x00D2E948, 0x00D2138A, 0x00D4D13A
DESSEL_COR = [0x0012E9C0, 0x0012EA1C, 0x0012EAB0, 0x0012EB08]
DESSEL_SET = [0x0012E9CA, 0x0012EA26, 0x0012EABA, 0x0012EB12]
SEL_SET = 0x0012EB4C
LARGURA = 0x0012ED5E
ALIGN_CALL = 0x0012ED58
LIVRE_FIM = 0x001FC000


def enc_bl(origem, destino):
    off = destino - (origem + 4)
    assert -(1 << 24) <= off < (1 << 24) and not off & 1
    s = (off >> 24) & 1
    i1, i2 = (off >> 23) & 1, (off >> 22) & 1
    j1, j2 = (~(i1 ^ s)) & 1, (~(i2 ^ s)) & 1
    return struct.pack("<HH", 0xF000 | (s << 10) | ((off >> 12) & 0x3FF),
                       0xD000 | (j1 << 13) | (j2 << 11) | ((off >> 1) & 0x7FF))


def dec_bl(origem, b):
    h1, h2 = struct.unpack("<HH", b)
    s, imm10 = (h1 >> 10) & 1, h1 & 0x3FF
    j1, j2, imm11 = (h2 >> 13) & 1, (h2 >> 11) & 1, h2 & 0x7FF
    i1, i2 = (~(j1 ^ s)) & 1, (~(j2 ^ s)) & 1
    off = (s << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm11 << 1)
    return origem + 4 + (off - (1 << 25) if s else off)


def firm(d):
    pt = struct.unpack_from("<I", d, 0x20)[0]
    n = struct.unpack_from("<I", d, pt)[0]
    for i in range(n):
        b = pt + 0x10 + i * 0x10
        if d[b:b + 4] == b"FIRM":
            o, l = struct.unpack_from("<2I", d, b + 4)
            return b, o, l


def proximo_livre(d, ini=0x001A3038, em=None):
    if em is not None:
        return em
    fim = ini
    for i in range(ini, ini + 0x4000):
        if d[i] != 0xFF:
            fim = i + 1
    return (fim + 3) & ~3


def main():
    ap = argparse.ArgumentParser(description="Barra de selecao na home")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--largura", type=int, default=116)
    ap.add_argument("--em", type=lambda x: int(x, 0), default=None,
                    help="endereco EXPLICITO da rotina")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if os.path.abspath(a.src) == os.path.abspath(a.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2
    if not 16 <= a.largura <= 128:
        print("RECUSADO: largura fora de 16..128.", file=sys.stderr)
        return 2
    orig = open(a.src, "rb").read()
    d = bytearray(orig)

    print("=" * 72)
    print("OpenPod — selecao da home vira BARRA")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n")

    erros = []
    for o in DESSEL_COR:
        if dec_bl(o + XIP, bytes(d[o:o + 4])) != BRANCO:
            erros.append(f"0x{o:06X} nao chama o getter de branco")
    for o in DESSEL_SET + [SEL_SET]:
        if dec_bl(o + XIP, bytes(d[o:o + 4])) != TEXT_COLOR:
            erros.append(f"0x{o:06X} nao chama set_style_text_color")
    if dec_bl(ALIGN_CALL + XIP, bytes(d[ALIGN_CALL:ALIGN_CALL + 4])) != TEXT_ALIGN:
        erros.append(f"0x{ALIGN_CALL:06X} nao chama set_style_text_align")
    if d[LARGURA] != 0x64:
        erros.append(f"0x{LARGURA:06X} largura e 0x{d[LARGURA]:02X}, esperado 0x64")
    if erros:
        print("  ABORTADO — entrada fora do esperado:")
        for m in erros:
            print(f"    - {m}")
        return 1
    print(f"  estado de entrada conferido: {len(DESSEL_COR)+len(DESSEL_SET)+2} "
          "pontos  OK\n")

    cur = proximo_livre(d, em=a.em)
    corpo = bytearray()
    corpo += bytes.fromhex("01b5")                       # push {r0, lr}
    corpo += enc_bl(cur + len(corpo) + XIP, TEXT_ALIGN)  # bl text_align
    corpo += bytes.fromhex("0098")                       # ldr r0,[sp]
    corpo += bytes.fromhex("ff21")                       # movs r1,#255
    corpo += bytes.fromhex("0022")                       # movs r2,#0
    corpo += enc_bl(cur + len(corpo) + XIP, BG_OPA)      # bl bg_opa
    corpo += bytes.fromhex("01bd")                       # pop {r0, pc}
    if cur + len(corpo) > LIVRE_FIM or any(b != 0xFF for b in d[cur:cur + len(corpo)]):
        print("  ABORTADO: area livre nao esta virgem.", file=sys.stderr)
        return 1
    d[cur:cur + len(corpo)] = corpo

    print(f"  ROTINA NA AREA LIVRE  0x{cur:06X}  ({len(corpo)} B)")
    print("    push {r0,lr} ; bl text_align ; ldr r0,[sp] ;")
    print("    movs r1,#255 ; movs r2,#0 ; bl bg_opa ; pop {r0,pc}")
    print()
    print("  PONTOS")
    for o in DESSEL_COR:
        d[o:o + 4] = enc_bl(o + XIP, PRETO)
        print(f"    0x{o:06X}  branco -> preto")
    for o in DESSEL_SET:
        d[o:o + 4] = enc_bl(o + XIP, BG_COLOR)
        print(f"    0x{o:06X}  text_color -> bg_color   (desselecao)")
    d[SEL_SET:SEL_SET + 4] = enc_bl(SEL_SET + XIP, BG_COLOR)
    print(f"    0x{SEL_SET:06X}  text_color -> bg_color   (SELECAO)")
    d[ALIGN_CALL:ALIGN_CALL + 4] = enc_bl(ALIGN_CALL + XIP, cur + XIP)
    print(f"    0x{ALIGN_CALL:06X}  text_align -> rotina (liga bg_opa)")
    d[LARGURA] = a.largura
    print(f"    0x{LARGURA:06X}  largura 0x64 (100) -> 0x{a.largura:02X} ({a.largura})"
          f"   barra de x=6 a x={6+a.largura}")
    print()

    ruim = 0
    for o, alvo in ([(x, PRETO) for x in DESSEL_COR] +
                    [(x, BG_COLOR) for x in DESSEL_SET] +
                    [(SEL_SET, BG_COLOR), (ALIGN_CALL, cur + XIP)]):
        if dec_bl(o + XIP, bytes(d[o:o + 4])) != alvo:
            print(f"    DIVERGE 0x{o:06X}"); ruim += 1
    if ruim:
        print("  ABORTADO: saltos nao conferem na volta.", file=sys.stderr)
        return 1
    print(f"  conferencia: {len(DESSEL_COR)+len(DESSEL_SET)+2} saltos "
          "decodificados de volta, todos corretos  OK\n")

    b, fo, fl = firm(d)
    old = struct.unpack_from("<H", d, b + 0x0C)[0]
    new = fw.crc16(bytes(d[fo:fo + fl]))
    if a.dry_run:
        print(f"  CRC da FIRM: 0x{old:04X} -> 0x{new:04X} (nao gravado)")
    else:
        # R1: NAO gravar o CRC da FIRM. Nao e verificado pelo aparelho, e
        # escrever aqui poe o setor 0x00D000 (tabela de particoes) de
        # volta na lista de setores — foi ele que matou o primeiro
        # aparelho. Achado pelo tools/build.py ao reconstruir do zero.
        pass   # NAO gravar o CRC (R1)
        print(f"  CRC da FIRM: 0x{old:04X} -> 0x{new:04X}")
    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in sorted({i // 0x1000 * 0x1000 for i in dif})))
    print()
    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
