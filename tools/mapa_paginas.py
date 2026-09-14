#!/usr/bin/env python3
"""
mapa_paginas.py — a tabela que liga NUMERO <-> PRESENTER <-> VIEW.

POR QUE ESTA TABELA EXISTE

    O firmware tem DOIS vocabularios para a mesma tela:

        presenter   identifica por NUMERO   page4_scr_process
        view        identifica por NOME     page_music_play_create

    Os nossos dois acidentes (cartao SD e Extras) foram nessas camadas.
    Sem esta tabela, "pagina 0x53" e "page84" pareciam numeros diferentes
    da mesma coisa — ou a mesma coisa com numeros diferentes. Nenhum dos
    dois: eram camadas diferentes.

COMO A LIGACAO FOI ESTABELECIDA (e nao adivinhada)

    1. `0x0010F0B0` e uma lista de STUBS de 6 bytes:

           bl <presenter>  ;  b <retorno comum>

    2. `0x0010EF64` e uma tabela de ponteiros **indexada por numero de
       pagina** (entrada N-1) que aponta para o stub daquela pagina.

    3. Prova: a entrada 22 (pagina 23) aponta para o stub 24, cujo
       presenter o proprio firmware chama de `page23_scr_process`.
       A ordem dos stubs NAO e a ordem das paginas — ha trocas e buracos,
       e a tabela de ponteiros e que desembaralha.

    4. Entradas que nao apontam para stub valido = paginas **sem
       presenter**. Sao os numeros ausentes.

    O lado da VIEW vem da tabela `0x00D23B38` (indice i -> pagina i+1).

USO
    python3 tools/mapa_paginas.py [--md docs/PAGINAS.md]
"""

import argparse
import re
import struct
import sys

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
except ImportError:
    sys.exit("capstone ausente: pip3 install capstone")

XIP = 0x00C00000
STUBS = 0x0010F0B0
PONTEIROS = 0x0010EF64
TAB_VIEW = 0x00D23B38
N_VIEW = 0x53


def simbolos(p="docs/SIMBOLOS.md"):
    s = {}
    for L in open(p):
        m = re.match(r'\| `0x([0-9A-F]+)` \| (\w+) \| `(.+)` \|', L.strip())
        if m:
            s[int(m.group(1), 16)] = (m.group(2), m.group(3))
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src",
                    default="firmware/ORIGINAL/GN438_original.bin")
    ap.add_argument("--md", default="docs/PAGINAS.md")
    a = ap.parse_args()
    d = open(a.src, "rb").read()
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    sim = simbolos()
    fs = sorted(sim)

    def nome(off):
        c = [f for f in fs if f <= off]
        if not c or off - max(c) > 0x1400:
            return None, None
        return sim[max(c)][1], sim[max(c)][0]

    # stubs -> presenter
    stub = {}
    for i in range(200):
        o = STUBS + 6 * i
        ins = list(md.disasm(d[o:o + 6], o + XIP))
        if (len(ins) < 2 or ins[0].mnemonic != "bl"
                or not ins[0].op_str.startswith("#") or ins[1].mnemonic != "b"):
            break
        stub[i] = int(ins[0].op_str.strip("#"), 0) - XIP

    # ponteiros indexados por numero de pagina
    presenter = {}
    for n in range(1, 120):
        v = struct.unpack_from("<I", d, PONTEIROS + 4 * (n - 1))[0]
        if not (XIP <= v < 0xDB0000):
            break
        off = (v - 1 - XIP) - STUBS
        if off >= 0 and off % 6 == 0 and off // 6 in stub:
            presenter[n] = stub[off // 6]

    # view
    view = {}
    for i in range(N_VIEW):
        t = TAB_VIEW + 2 * d[TAB_VIEW - XIP + i]
        k = next(md.disasm(d[t - XIP:t - XIP + 4], t), None)
        if k and k.mnemonic == "bl":
            view[i + 1] = int(k.op_str.strip("#"), 0) - XIP

    todas = sorted(set(presenter) | set(view))
    coerentes = divergentes = 0
    linhas = []
    for n in todas:
        pa = presenter.get(n)
        va = view.get(n)
        pn = nome(pa)[0] if pa else None
        vn = nome(va)[0] if va else None
        bate = bool(pn and re.search(rf'page{n}[_\b]', pn))
        if pn:
            coerentes += bate
            divergentes += (not bate)
        linhas.append((n, pa, pn, va, vn, bate))

    print()
    print("  MAPA DE PAGINAS")
    print()
    print(f"  stubs de presenter ......... {len(stub)}")
    print(f"  paginas com presenter ...... {len(presenter)}")
    print(f"  paginas com view ........... {len(view)}")
    print(f"  paginas no total ........... {len(todas)}")
    print(f"  presenter cujo NOME confirma o numero: {coerentes}"
          f"   divergentes: {divergentes}")
    semp = [n for n in view if n not in presenter]
    semv = [n for n in presenter if n not in view]
    print(f"  view SEM presenter ......... {len(semp)}  {semp}")
    print(f"  presenter SEM view ......... {len(semv)}  {semv}")

    out = []
    w = out.append
    w("# PAGINAS — numero, presenter e view\n")
    w("Gerado por `tools/mapa_paginas.py` a partir de "
      "`firmware/ORIGINAL/GN438_original.bin`.\n")
    w("O firmware tem **dois vocabularios** para a mesma tela: o presenter")
    w("a identifica por NUMERO, a view por NOME. Esta tabela liga os dois.\n")
    w("A ligacao vem de `0x0010EF64`, tabela de ponteiros **indexada por")
    w("numero de pagina**, que aponta para stubs de 6 bytes em `0x0010F0B0`")
    w("(`bl <presenter>; b <retorno>`). A ordem dos stubs **nao** e a ordem")
    w("das paginas — ha trocas e buracos, e a tabela de ponteiros desembaralha.\n")
    w("Coluna `ok` = o nome que o proprio firmware da ao presenter cita este")
    w("numero de pagina. E a validacao independente.\n")
    w("## O desencontro de numeracao, resolvido\n")
    w("O nome do presenter e o ID da pagina **coincidem ate a pagina 70** e")
    w("**divergem de 1 a partir da 75**:\n")
    w("```")
    w("pagina 0x1E (30)  ->  page30_scr_process     bate")
    w("pagina 0x44 (68)  ->  page68_btn_process     bate")
    w("pagina 0x4B (75)  ->  page76_scr_process     +1")
    w("pagina 0x53 (83)  ->  page84_scr_process     +1")
    w("```\n")
    w("**O ID da pagina e a autoridade** — ele vem de duas tabelas")
    w("independentes (`0x0010EF64` do presenter e `0x00D23B38` da view), e")
    w("as duas concordam: a pagina 83 e o Extras nas duas.\n")
    w("O numero **no nome** e historico: presenters foram acrescentados ou")
    w("removidos entre a 70 e a 75 e os nomes nao foram renumerados. Isso")
    w("desfaz o alarme que ficou em `ARQUITETURA.md` §7.3: `page84` e a")
    w("pagina 0x53 sao a mesma tela, e o Extras sempre foi a 83.\n")
    w("Nao ha pagina nenhuma nos intervalos 36-39, 50, 52-54, 57-59, 61-67")
    w("e 71-74: nem presenter, nem view.\n")
    w(f"| # | presenter | nome do presenter | view | nome da view | ok |")
    w("|---|---|---|---|---|---|")
    for n, pa, pn, va, vn, bate in linhas:
        w(f"| **{n}** (0x{n:02X}) | "
          + (f"`0x{pa:06X}`" if pa else "—") + " | "
          + (f"`{pn}`" if pn else "—") + " | "
          + (f"`0x{va:06X}`" if va else "—") + " | "
          + (f"`{vn}`" if vn else "—") + " | "
          + ("sim" if bate else ("**nao**" if pn else "—")) + " |")
    w("")
    w("## Paginas sem presenter\n")
    w(f"{semp}\n")
    w("Sao telas que a view constroi mas que nao tem logica propria de")
    w("presenter — provavelmente sub-telas tratadas pelo presenter do pai.\n")
    w("## Paginas sem view\n")
    w(f"{semv}\n")
    open(a.md, "w").write("\n".join(out) + "\n")
    print(f"\n  gravado: {a.md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
