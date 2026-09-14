#!/usr/bin/env python3
"""
exporta_textos.py — Exporta TODOS os textos do sistema, em todos os
                    idiomas, para um markdown revisavel.

POR QUE

    O mantenedor quer revisar traducoes e padronizar a escrita. Sem uma
    visao lado a lado e impossivel perceber que "Configuracao do ecra" e
    portugues europeu enquanto outro item usa brasileiro, ou que dois ids
    diferentes dizem a mesma coisa de formas diferentes.

O QUE MAIS ELE FAZ

    Mede a **largura em pixels** de cada texto em portugues usando a
    fonte real do firmware (blob 0x0005E7E0, tabela 0x00086C44), e marca
    o que nao cabe. Foi assim que se explicou o "Configuracao do ecr:"
    cortado na tela do Configurar.

        rotulo da home    128 px, recuo 6  ->  122 px uteis
        rotulo das listas hor_res - 15     ->  113 px uteis

    O limite mais apertado (113) e o que vale como alerta.

TABELAS DE IDIOMA (offsets de arquivo)

    de 0x52744   zh 0x523E4   en 0x52AA4   fr 0x52E04
    it 0x534C4   nl 0x53824   pt (realocada)   es 0x53EE4

    O portugues foi realocado para a area livre no V021; a base real e
    lida do pool de `get_string` (0x00121104), nunca fixa no codigo.

USO
    python3 tools/exporta_textos.py \
        --in  firmware/WORKING/GN438_openpod_v043.bin \
        --out docs/TEXTOS_SISTEMA.md
"""

import argparse
import os
import struct
import sys

XIP = 0x00C00000
N_IDS = 216
POOL_PT = 0x00121104
LANGS = [("pt", None), ("en", 0x00052AA4), ("es", 0x00053EE4),
         ("fr", 0x00052E04), ("it", 0x000534C4), ("de", 0x00052744),
         ("nl", 0x00053824), ("zh", 0x000523E4)]
TBL = 0x00086C44
CMAP = 0x000A27E6
BLOB = 0x0005E7E0
N_GLIFOS = 7098
LIM_LISTA = 113
LIM_HOME = 122


def main():
    ap = argparse.ArgumentParser(description="Exporta os textos do sistema")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    a = ap.parse_args()
    d = open(a.src, "rb").read()

    base_pt = struct.unpack_from("<I", d, POOL_PT)[0] - XIP
    langs = [(n, base_pt if o is None else o) for n, o in LANGS]

    cmap = struct.unpack_from("<%dH" % N_GLIFOS, d, CMAP)
    idx = {c: i for i, c in enumerate(cmap)}

    def largura(txt):
        w = 0
        for ch in txt:
            g = idx.get(ord(ch))
            if g is None:
                return None
            w += struct.unpack_from("<I", d, TBL + g * 16 + 4)[0]
        return w

    def ler(off, i):
        p = struct.unpack_from("<I", d, off + i * 4)[0]
        o = p - XIP
        if not 0 <= o < len(d):
            return ""
        e = d.find(b"\0", o)
        if e < 0 or e - o > 200:
            return ""
        return d[o:e].decode("utf-8", "replace")

    linhas, longos = [], 0
    for i in range(N_IDS):
        col = {n: ler(o, i) for n, o in langs}
        w = largura(col["pt"])
        alerta = ""
        if w is None:
            alerta = "?"
        elif w > LIM_LISTA:
            alerta = "**CORTA**"
            longos += 1
        linhas.append((i, w, alerta, col))

    with open(a.dst, "w", encoding="utf-8") as f:
        f.write("# Textos do sistema — todos os idiomas\n\n")
        f.write("> Gerado por `tools/exporta_textos.py` a partir de "
                f"`{os.path.basename(a.src)}`.\n"
                "> **Este arquivo é para revisão.** Edite a coluna `pt` à "
                "vontade; depois eu gero o patch\n"
                "> com `tools/patch_menu_text.py`, que nunca edita string "
                "no lugar — grava a nova na área\n"
                "> livre e repõe o ponteiro.\n\n")
        f.write("## Como ler\n\n")
        f.write(f"- **px** = largura do texto em português, medida com a "
                f"fonte real do firmware.\n")
        f.write(f"- **CORTA** = passa de {LIM_LISTA} px e será truncado nas "
                f"listas do sistema (Extras, Configurar).\n")
        f.write(f"  Na home o limite é {LIM_HOME} px.\n")
        f.write(f"- Linha em branco = id não usado naquele idioma.\n\n")
        f.write(f"**{longos} textos em português passam de {LIM_LISTA} px.**\n\n")
        f.write("---\n\n")
        f.write("| id | px | | pt | en | es | fr | it | de | nl | zh |\n")
        f.write("|---:|---:|---|---|---|---|---|---|---|---|---|\n")
        for i, w, al, col in linhas:
            def esc(s):
                return s.replace("|", "\\|").replace("\n", " ") or " "
            f.write(f"| {i} | {w if w is not None else '?'} | {al} | "
                    + " | ".join(esc(col[n]) for n, _ in langs) + " |\n")

    print(f"gerado: {a.dst}")
    print(f"  {N_IDS} ids x {len(langs)} idiomas")
    print(f"  tabela pt em uso: 0x{base_pt + XIP:08X}")
    print(f"  {longos} textos em pt passam de {LIM_LISTA} px e serao cortados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
