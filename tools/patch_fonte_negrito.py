#!/usr/bin/env python3
"""
patch_fonte_negrito.py — Engrossa a fonte de texto, sem alargar o texto.

A FONTE

    Uma unica fonte de texto no firmware inteiro: menus, relogio, titulo,
    Extras, Configurar. Engrossar ela engrossa tudo junto.

        blob de bitmaps   0x0005E7E0   164.946 B
        tabela de glifos  0x00086C44   7098 x 16 B
        cmap              0x000A27E6   7098 x u16

    Descritor de 16 B, decodificado e validado renderizando glifos:

        +0   u32  offset do bitmap dentro do blob
        +4   u32  largura de avanco
        +8   u16  stride em bits (alinhado a byte)
        +10  u16  altura
        +12  s16  ofs_x        +14  s16  ofs_y

    1 bpp: sem canal alfa, entao engrossar e adicionar pixel.

O ALGORITMO, E POR QUE NAO E O INGENUO

    Espalhar cada pixel 1 px para a direita e o "faux bold" classico. Num
    corpo de 12 px ele DESTROI glifos com vao interno de 1 px:

        'M' normal   .#.#.#.#.
        'M' ingenuo  .########.   <- virou bloco

    Duas travas resolvem:

    1. **Nao fechar vao.** So espalha para x+1 se x+2 estiver apagado.
       Preserva os vaos internos; glifos densos ficam como estao.
    2. **Nao passar do avanco.** So espalha dentro de x < avanco. Nenhuma
       letra encosta na seguinte, e **o texto nao fica mais largo** --
       nenhum rotulo que hoje cabe passa a ser cortado.

    Como nem o stride nem a altura mudam, o bitmap tem o MESMO tamanho e
    e reescrito no lugar. Nada e realocado, nenhum ponteiro muda.

USO
    python3 tools/patch_fonte_negrito.py \
        --in  firmware/WORKING/GN438_openpod_v034.bin \
        --out firmware/WORKING/GN438_openpod_v035.bin \
        [--faixa latino|tudo] [--dry-run]

SEGURANCA
    - trabalha so sobre os glifos da faixa escolhida;
    - recusa se o descritor nao for coerente (bitmap fora do blob);
    - nunca muda tamanho de bitmap, stride, altura, avanco ou offset;
    - confere relendo cada glifo alterado e comparando com o esperado;
    - recusa se algum setor alterado for <= 0x00D000.
"""

import argparse
import os
import struct
import sys

TBL = 0x00086C44
CMAP = 0x000A27E6
BLOB = 0x0005E7E0
BLOB_LEN = 164946
N = 7098
PROIBIDO = 0x0000D000

FAIXAS = {
    "latino": [(0x20, 0x7E), (0xA0, 0xFF), (0x100, 0x17F)],
    "tudo": [(0x20, 0xFFFF)],
}


def dsc(d, g):
    e = TBL + g * 16
    return (struct.unpack_from("<I", d, e)[0],
            struct.unpack_from("<I", d, e + 4)[0],
            struct.unpack_from("<H", d, e + 8)[0],
            struct.unpack_from("<H", d, e + 10)[0])


def ler(d, bi, stride, h):
    wb = stride // 8
    return [[(d[BLOB + bi + r * wb + (c >> 3)] >> (7 - (c & 7))) & 1
             for c in range(stride)] for r in range(h)]


def escrever(d, bi, stride, h, rows):
    wb = stride // 8
    for r in range(h):
        for b in range(wb):
            v = 0
            for k in range(8):
                if rows[r][b * 8 + k]:
                    v |= 1 << (7 - k)
            d[BLOB + bi + r * wb + b] = v


def engrossa(rows, stride, adv):
    lim = min(stride, adv)          # nunca passar do avanco
    out = [r[:] for r in rows]
    n = 0
    for r, row in enumerate(rows):
        for c in range(stride):
            if not row[c]:
                continue
            if c + 1 >= lim:
                continue            # sairia do avanco: nao engrossa
            if c + 2 < stride and row[c + 2]:
                continue            # fecharia um vao de 1 px
            if not out[r][c + 1]:
                out[r][c + 1] = 1
                n += 1
    return out, n


def main():
    ap = argparse.ArgumentParser(description="Fonte um pouco mais grossa")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--faixa", choices=sorted(FAIXAS), default="latino")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if os.path.abspath(a.src) == os.path.abspath(a.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2

    orig = open(a.src, "rb").read()
    d = bytearray(orig)
    cmap = struct.unpack_from("<%dH" % N, d, CMAP)

    print("=" * 72)
    print("OpenPod — fonte um pouco mais grossa")
    print("=" * 72)
    print(f"  origem : {a.src}")
    print(f"  destino: {a.dst}")
    print(f"  faixa  : {a.faixa}")
    print()

    faixas = FAIXAS[a.faixa]
    alvos = [g for g, cp in enumerate(cmap)
             if any(lo <= cp <= hi for lo, hi in faixas)]
    print(f"  glifos na faixa: {len(alvos)} de {N}")

    mudados = px = pulados = 0
    conferidos = []
    for g in alvos:
        bi, adv, stride, h = dsc(d, g)
        if stride == 0 or h == 0:
            continue
        if not (0 <= bi and bi + (stride // 8) * h <= BLOB_LEN):
            pulados += 1
            continue
        rows = ler(d, bi, stride, h)
        novo, n = engrossa(rows, stride, adv)
        if n:
            escrever(d, bi, stride, h, novo)
            mudados += 1
            px += n
            conferidos.append((g, bi, stride, h, novo))
    print(f"  glifos engrossados: {mudados}   pixels acrescentados: {px}")
    if pulados:
        print(f"  glifos pulados por descritor incoerente: {pulados}")
    print()

    ruim = 0
    for g, bi, stride, h, esperado in conferidos:
        if ler(d, bi, stride, h) != esperado:
            ruim += 1
    if ruim:
        print(f"  ABORTADO: {ruim} glifos divergem na releitura.", file=sys.stderr)
        return 1
    print(f"  conferencia: {len(conferidos)} glifos relidos, todos iguais  OK")
    print()

    for ch in "MAoOpenPd":
        pass
    print("  PREVIA")
    for txt in ("Musica", "OpenPod"):
        linhas = [""] * 14
        x = 0
        idx = {c: i for i, c in enumerate(cmap)}
        for ch in txt:
            g = idx.get(ord(ch))
            if g is None:
                continue
            bi, adv, stride, h = dsc(d, g)
            oy = struct.unpack_from("<h", d, TBL + g * 16 + 14)[0]
            rows = ler(d, bi, stride, h)
            for r in range(h):
                while len(linhas[oy + r]) < x:
                    linhas[oy + r] += "."
                s = "".join("#" if v else "." for v in rows[r][:adv])
                linhas[oy + r] = linhas[oy + r][:x] + s
            x += adv
        print(f"    {txt!r}")
        for L in linhas:
            if L.strip("."):
                print("      " + L)
    print()

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: {len(secs)}")
    print("    " + "  ".join(f"0x{s:06X}" for s in secs))
    if any(s <= PROIBIDO for s in secs):
        print("  ABORTADO: setor proibido.", file=sys.stderr)
        return 1
    print(f"  tabela de particoes (0x{PROIBIDO:06X}) NAO tocada   OK")
    print()
    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
