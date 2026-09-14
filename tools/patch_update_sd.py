#!/usr/bin/env python3
"""
patch_update_sd.py — "Atualizar por SD" no menu Configurar.

O QUE FAZ

    O item que hoje se chama "Configuracao de fabrica" passa a ser
    "Atualizar por SD". Confirmando no "Sim", o aparelho arma o flag de
    update no PMU e **reinicia sozinho**; no boot seguinte o bootloader
    le `0:\\update.up` do cartao e regrava a flash.

    Sem PC. Sem cabo. Sem abrir o aparelho.

A PECA QUE JA EXISTIA

    `HAL_pmu_sd_update_flag_set` (0x00CF6CA0) esta na FIRM, integra, e
    **nada no firmware inteiro a chama** -- varredura de 0x0E000 a
    0x1A0570, zero `bl`, zero ponteiro. Codigo morto desde a fabrica.

    Ela grava reg[0x23] bits 7:6 = 11 e reg[0x00] bit 0 = 0, o que da
    flag = 6 = update por cartao SD. Ver `docs/MODO_DOWNLOAD.md`.

ONDE O GANCHO ENTRA, E POR QUE AQUI

    Primeiro desenho (V030/V045) pendurava no **item do menu**. Errado: o
    flag era armado ao ENTRAR, antes da janelinha -- escolher "Nao" nao
    cancelava nada.

    O lugar certo e o tratador do botao, em `page40_mbox_process`:

        00D092AA  cmp r2, #8          ; ctrl_id 8 = o "Sim"
        00D092B8  movs r1, #0
        00D092BC  bl 0xD09084
        00D092C0  bl 0xD91D4C   <- apaga "btlinknum", "btlinkinfo"
        00D092C4  bl 0xD453B8   <- apaga "language", "bright", "offscr"...
        00D092CC  b  0xCFC64C   <- "do_reboot_mode": REINICIA

    O fluxo **ja reinicia**. Era a peca que faltava: o desenho anterior
    dependia do botao de reset fisico, e nao depende.

O QUE E ALTERADO

    0x001092C0   4 B  bl apaga-Bluetooth -> bl <rotina: arma o flag>
    0x001092C4   4 B  bl apaga-ajustes   -> nop nop
    0x001093DC   4 B  reverte o gancho da V045
    area livre        a rotina (10 B) e os dois textos
    tabela pt         ids 40 e 91 repontados

    Decisao do mantenedor: "So atualizar" -- as configuracoes NAO sao
    apagadas. Idioma, brilho e pareamentos Bluetooth sobrevivem. O reset
    de fabrica sai do menu; se um dia fizer falta, volta como item
    proprio (exige mexer no malloc da tela).

USO
    python3 tools/patch_update_sd.py \\
        --in  firmware/WORKING/GN438_openpod_v045.bin \\
        --out firmware/WORKING/GN438_openpod_v046.bin [--dry-run]

ENDERECO EXPLICITO (--em)

    Por padrao esta ferramenta ALOCAVA sozinha: varria a area livre e se
    encaixava depois do ultimo byte ocupado. Isso fazia o endereco da
    rotina depender de TUDO que rodou antes — e os patches seguintes
    fixavam esse endereco no codigo. Resultado: a corrente so compunha
    na ordem historica exata (ver `tools/build.py`).

    Com `--em 0x1A3200` o endereco passa a ser declarado por quem chama.
    O comportamento antigo continua sendo o padrao, para nao quebrar uso
    manual; a receita do `build.py` sempre passa `--em`.
"""

import argparse
import os
import struct
import sys

XIP = 0x00C00000
POOL_PT = 0x00121104
FLAG_SET = 0x00CF6CA0
H_LIMPA_BT = 0x001092C0
H_LIMPA_CFG = 0x001092C4
H_V045 = 0x001093DC
NAV = 0x00D0E138
LIMPA_BT = 0x00D91D4C
LIMPA_CFG = 0x00D453B8
LIVRE_INI = 0x001A3038
TBL, CMAP, N_GLIFOS = 0x00086C44, 0x000A27E6, 7098
PROIBIDO = 0x0000D000
TEXTOS = {40: "Atualizar por SD",
          91: "Atualizar o sistema\npelo cartão SD?"}


def enc(o, dst, link=True):
    off = dst - (o + 4)
    s = (off >> 24) & 1
    i1, i2 = (off >> 23) & 1, (off >> 22) & 1
    j1, j2 = (~(i1 ^ s)) & 1, (~(i2 ^ s)) & 1
    return struct.pack("<HH", 0xF000 | (s << 10) | ((off >> 12) & 0x3FF),
                       (0xD000 if link else 0x9000) | (j1 << 13) | (j2 << 11)
                       | ((off >> 1) & 0x7FF))


def dec(o, b):
    h1, h2 = struct.unpack("<HH", b)
    s = (h1 >> 10) & 1
    j1, j2 = (h2 >> 13) & 1, (h2 >> 11) & 1
    i1, i2 = (~(j1 ^ s)) & 1, (~(j2 ^ s)) & 1
    off = (s << 24) | (i1 << 23) | (i2 << 22) | ((h1 & 0x3FF) << 12) | ((h2 & 0x7FF) << 1)
    if s:
        off -= 1 << 25
    return o + 4 + off, bool(h2 & 0x4000)


def livre(d, em=None):
    if em is not None:
        return em
    f = LIVRE_INI
    for i in range(LIVRE_INI, LIVRE_INI + 0x4000):
        if d[i] != 0xFF:
            f = i + 1
    return (f + 3) & ~3


def main():
    ap = argparse.ArgumentParser(description="Atualizar por SD no menu")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--em", type=lambda x: int(x, 0), default=None,
                    help="endereco EXPLICITO da rotina na area livre. "
                         "Sem ele, a ferramenta aloca sozinha — e o "
                         "endereco passa a depender da ordem.")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if os.path.abspath(a.src) == os.path.abspath(a.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2
    orig = open(a.src, "rb").read()
    d = bytearray(orig)

    print("=" * 72)
    print("OpenPod — Atualizar por SD")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n")

    cmap = struct.unpack_from("<%dH" % N_GLIFOS, d, CMAP)
    idx = {c: i for i, c in enumerate(cmap)}

    def w(t):
        return sum(struct.unpack_from("<I", d, TBL + idx[ord(c)] * 16 + 4)[0]
                   for c in t)

    erros = []
    for off, alvo, nome in ((H_LIMPA_BT, LIMPA_BT, "apaga-Bluetooth"),
                            (H_LIMPA_CFG, LIMPA_CFG, "apaga-ajustes")):
        got, link = dec(off + XIP, bytes(d[off:off + 4]))
        if (got, link) != (alvo, True):
            erros.append(f"0x{off:06X} chama 0x{got:08X}, esperado "
                         f"0x{alvo:08X} ({nome})")
    if bytes(d[FLAG_SET - XIP:FLAG_SET - XIP + 4]) != bytes.fromhex("10b50146"):
        erros.append("0x00CF6CA0 nao e HAL_pmu_sd_update_flag_set")
    base = struct.unpack_from("<I", d, POOL_PT)[0] - XIP
    for i, t in TEXTOS.items():
        falta = [c for c in t if c != "\n" and ord(c) not in idx]
        if falta:
            erros.append(f"id {i}: caractere fora da fonte {falta}")
    if erros:
        print("  ABORTADO:")
        for m in erros:
            print(f"    - {m}")
        return 1
    print("  entrada conferida: os dois `bl` do Sim, o armador do flag, "
          "a fonte  OK\n")

    rot = livre(d, a.em)
    c = struct.pack("<H", 0xB508)                 # push {r3, lr}
    c += struct.pack("<H", 0x2001)                # movs r0, #1
    c += enc(rot + XIP + 4, FLAG_SET)             # bl flag_set
    c += struct.pack("<H", 0xBD08)                # pop {r3, pc}
    d[rot:rot + len(c)] = c
    d[H_LIMPA_BT:H_LIMPA_BT + 4] = enc(H_LIMPA_BT + XIP, rot + XIP)
    d[H_LIMPA_CFG:H_LIMPA_CFG + 4] = b"\x00\xbf\x00\xbf"        # nop; nop
    d[H_V045:H_V045 + 4] = enc(H_V045 + XIP, NAV, link=False)

    print("  ROTINA  (0x%08X)" % (rot + XIP))
    for o, n, asm in ((0, 2, "push  {r3, lr}"), (2, 2, "movs  r0, #1"),
                      (4, 4, "bl    0x%08X" % FLAG_SET), (8, 2, "pop   {r3, pc}")):
        print(f"    +0x{o:02X}  {bytes(c[o:o+n]).hex():<8}  {asm}")
    print()
    print("  GANCHOS")
    print(f"    0x{H_LIMPA_BT:06X}  bl apaga-Bluetooth -> bl 0x{rot + XIP:08X}")
    print(f"    0x{H_LIMPA_CFG:06X}  bl apaga-ajustes   -> nop nop")
    print(f"    0x{H_V045:06X}  gancho da V045     -> revertido para b.w nav")
    print(f"    o `b.w do_reboot_mode` em 0x001092CC fica intacto")
    print()

    cur = rot + len(c)
    cur = (cur + 3) & ~3
    print("  TEXTOS")
    for i, t in sorted(TEXTOS.items()):
        p = struct.unpack_from("<I", d, base + i * 4)[0] - XIP
        e = d.find(b"\0", p)
        antes = d[p:e].decode("utf-8")
        blob = t.encode("utf-8") + b"\0"
        if any(b != 0xFF for b in d[cur:cur + len(blob)]):
            print(f"  ABORTADO: 0x{cur:06X} nao esta virgem.", file=sys.stderr)
            return 1
        d[cur:cur + len(blob)] = blob
        struct.pack_into("<I", d, base + i * 4, cur + XIP)
        print(f"    id {i}: {antes!r}")
        for ln in t.split("\n"):
            print(f"           -> {ln!r:<26} {w(ln):>4} px")
        cur = (cur + len(blob) + 3) & ~3
    print()

    ok = True
    got, link = dec(H_LIMPA_BT + XIP, bytes(d[H_LIMPA_BT:H_LIMPA_BT + 4]))
    ok &= (got, link) == (rot + XIP, True)
    got, _ = dec(rot + XIP + 4, bytes(c[4:8]))
    ok &= got == FLAG_SET
    for i, t in TEXTOS.items():
        p = struct.unpack_from("<I", d, base + i * 4)[0] - XIP
        e = d.find(b"\0", p)
        ok &= d[p:e].decode("utf-8") == t
    print(f"  conferencia (saltos e strings relidas): "
          f"{'todos OK' if ok else 'ERRO'}")
    if not ok:
        return 1
    print()

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))
    if any(s <= PROIBIDO for s in secs):
        print("  ABORTADO: setor proibido.", file=sys.stderr)
        return 1
    print("  tabela de particoes NAO tocada   OK\n")
    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
