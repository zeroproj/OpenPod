#!/usr/bin/env python3
"""
patch_versao.py — A tela Informacao passa a mostrar a versao do OpenPod.

O QUE A TELA MOSTRA HOJE

    `page_info` (camada APP, 0x00D0A4C8) monta duas coisas:

        00D0A4CC  movs r0, #0x2B          ; id 43, o titulo
        00D0A4D0  bl   get_string
        ...
        00D0A53C  ldr  r1, ="yp3_2.0.43"  ; a versao, direto de um literal
        00D0A542  bl   strcpy

    A versao NAO vem da tabela de idiomas: vem de uma string em
    0x0004EA8B, apontada por um unico literal em 0x0010A59C.

    O id 156 ('TP version:') e **string morta** -- nenhuma chamada a
    `get_string` o busca. O que aparece na tela e so titulo + versao.

POR QUE REPONTAR E NAO SOBRESCREVER

    Mesma regra das strings de menu: nunca editar no lugar. Aqui o risco
    e menor (um so referenciador), mas a regra vale igual -- e repontar
    ainda deixa escolher um texto de qualquer tamanho.

DUAS LINHAS — NAO. CORRIGIDO EM 2026-09-14

    Eu escrevia aqui que o rotulo aceita `\n`, porque a tabela de idiomas
    tem strings assim (ids 140, 154, 161). **Estava errado para ESTA
    tela.**

    Aqueles ids vao para um rotulo LVGL comum. A tela Informacao nao:
    `page_info` monta uma MENSAGEM (descritor em 0x008238F0, entregue a
    0x00D0D818) e esse caminho **nao quebra linha**. Gravada a Core 1.0
    com "OpenPod Core 1.0\nGN-438", o aparelho desenhou os dois textos
    **sobrepostos numa linha so**.

    CONFIRMADO no aparelho em 14/09/2026.

    A tela tem DOIS espacos de texto que funcionam: o titulo, vindo de
    `get_string(43)` — que tem **um unico chamador**, este aqui — e a
    linha de baixo, este literal. Cada um aceita UMA linha.

    Limite de largura: 113 px.

        'OpenPod Core 1.0'     102 px
        'OpenPod Core 1.0.1'   112 px
        'Core 1.0 - GN-438'    100 px
        'OpenPod Core 1.0 GN-438'  148 px   NAO CABE

O QUE E ALTERADO

    area livre   o texto novo
    0x0010A59C   4 B  o literal, repontado

    A string 'yp3_2.0.43' original fica intacta em 0x0004EA8B.

USO
    python3 tools/patch_versao.py \\
        --in  firmware/WORKING/GN438_openpod_v043.bin \\
        --out firmware/WORKING/GN438_openpod_v044.bin \\
        [--texto "OpenPod 1.0\\nBase: yp3_2.0.43"]

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
LIT = 0x0010A59C
ATUAL = 0x00C4EA8B
LIVRE_INI = 0x001A3038
LIVRE_FIM = 0x001FC000
TBL, CMAP, N_GLIFOS = 0x00086C44, 0x000A27E6, 7098
PROIBIDO = 0x0000D000
PADRAO = "OpenPod 1.0\nBase: yp3_2.0.43"


def proximo_livre(d, em=None):
    if em is not None:
        return em
    fim = LIVRE_INI
    for i in range(LIVRE_INI, LIVRE_INI + 0x4000):
        if d[i] != 0xFF:
            fim = i + 1
    return (fim + 3) & ~3


def main():
    ap = argparse.ArgumentParser(description="Versao do OpenPod na tela Informacao")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--texto", default=PADRAO)
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
    txt = a.texto.replace("\\n", "\n")

    print("=" * 72)
    print("OpenPod — versao na tela Informacao")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n")

    cmap = struct.unpack_from("<%dH" % N_GLIFOS, d, CMAP)
    idx = {c: i for i, c in enumerate(cmap)}

    def w(t):
        s = 0
        for ch in t:
            g = idx.get(ord(ch))
            if g is None:
                return None
            s += struct.unpack_from("<I", d, TBL + g * 16 + 4)[0]
        return s

    # O literal pode estar (a) de fabrica, apontando para 'yp3_2.0.43', ou
    # (b) ja repontado para a area livre por uma versao anterior. Os dois
    # sao entrada valida -- o texto e reescrito num endereco novo de
    # qualquer forma, e o anterior fica orfao (inofensivo, area livre).
    erros = []
    lit = struct.unpack_from("<I", d, LIT)[0]
    if lit == ATUAL:
        print("  literal de fabrica, apontando para 'yp3_2.0.43'")
    elif LIVRE_INI + XIP <= lit < LIVRE_FIM + XIP:
        o0 = lit - XIP
        e0 = d.find(b"\0", o0)
        print(f"  literal ja repontado -> {d[o0:e0].decode('utf-8')!r}")
    else:
        erros.append(f"literal 0x{LIT:06X} = 0x{lit:08X}: nem de fabrica "
                     f"nem na area livre")
    faltando = [c for c in txt if c != "\n" and ord(c) not in idx]
    if faltando:
        erros.append(f"caracteres fora da fonte: {faltando}")
    blob = txt.encode("utf-8") + b"\0"
    cur = proximo_livre(d, a.em)
    if cur + len(blob) > LIVRE_FIM:
        erros.append("nao cabe na area livre")
    if any(b != 0xFF for b in d[cur:cur + len(blob)]):
        erros.append(f"0x{cur:06X} nao esta virgem")
    if erros:
        print("  ABORTADO:")
        for m in erros:
            print(f"    - {m}")
        return 1

    o = ATUAL - XIP
    e = d.find(b"\0", o)
    print(f"  texto atual : {d[o:e].decode()!r}   ({w(d[o:e].decode())} px)")
    print("  texto novo  :")
    for ln in txt.split("\n"):
        print(f"      {ln!r:<28} {w(ln):>4} px")
    print()

    d[cur:cur + len(blob)] = blob
    struct.pack_into("<I", d, LIT, cur + XIP)

    print("  ALTERACOES")
    print(f"    0x{cur:06X}  {len(blob)} B  o texto, na area livre")
    print(f"    0x{LIT:06X}   4 B  literal 0x{ATUAL:08X} -> 0x{cur + XIP:08X}")
    print(f"    a string original em 0x{o:06X} fica intacta")
    print()

    # confere relendo pelo ponteiro
    p = struct.unpack_from("<I", d, LIT)[0] - XIP
    e2 = d.find(b"\0", p)
    lido = d[p:e2].decode("utf-8")
    print(f"  conferencia: relido pelo ponteiro -> {lido!r}  "
          f"{'OK' if lido == txt else 'DIVERGE'}")
    if lido != txt:
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
