#!/usr/bin/env python3
"""
relocate_lang_table.py — Realoca a tabela de strings de um idioma para a
                         area livre, com ids extras no fim.

POR QUE PRECISA EXISTIR

    A tabela do portugues tem 216 ids (0..215) e emenda DIRETO na do
    espanhol, em 0x00C53EE4. `get_string` nao confere limite:

        ldr.w r4, [r3, r4, lsl #2]

    ou seja, um id 216 em portugues leria es[0] = "Espanol". **Nao ha
    folga para um id novo no lugar.**

    Mas a base da tabela e um PONTEIRO, e esta em dois lugares:

        0x00121104   literal de pool do get_string (0x00D2108C)
        0x00048798   entrada do pt num vetor de bases em 0x00048780

    Realocar custa 2 ponteiros de 4 bytes. A copia vai para a area livre,
    cuja leitura por XIP foi CONFIRMADA no V017 e cuja execucao foi
    CONFIRMADA no V020.

O QUE ESTA FERRAMENTA FAZ

    1. copia os N ponteiros da tabela original para a area livre;
    2. grava as strings novas na area livre;
    3. acrescenta um ponteiro por string nova, no fim da tabela;
    4. repoe os DOIS ponteiros de base.

    Nenhuma string existente e alterada. A tabela original continua onde
    estava, intacta -- so deixa de ser consultada.

RESSALVA IMPORTANTE

    Passa a existir uma **copia** da tabela. Quem editar a original em
    0x00C53B84 depois disto nao vera efeito: a que vale e a da area
    livre. Isto precisa estar no FIRMWARE_MAP.md.

USO
    python3 tools/relocate_lang_table.py \
        --in  firmware/WORKING/GN438_openpod_v020.bin \
        --out firmware/WORKING/GN438_openpod_v021.bin \
        --idioma pt --add Extras [--add Outro ...] [--dry-run]

DEPENDENCIAS
    Python 3 + tools/fw_common.py

SEGURANCA
    - recusa se origem == destino;
    - recusa se os dois ponteiros de base nao tiverem o valor esperado;
    - recusa se a area livre de destino nao estiver toda em 0xFF;
    - recusa texto com caractere fora da fonte;
    - CONFERE a tabela nova relendo os N+M ponteiros e comparando string
      por string com a original antes de gravar;
    - a entrada e aberta somente para leitura; a saida e arquivo novo.

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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fw_common as fw

XIP = 0x00C00000
LIVRE_INI = 0x001A3038
LIVRE_FIM = 0x001FC000

# idioma -> (base na flash, n de ids, offset do pool no get_string,
#            offset da entrada no vetor de bases)
IDIOMAS = {
    "pt": (0x00053B84, 216, 0x00121104, 0x00048798),
}

FONT_TABLE = 0x00086C44
FONT_CMAP = 0x000A27E6
FONT_N = 7098


def firm_entry(data):
    pt = struct.unpack_from("<I", data, 0x20)[0]
    n = struct.unpack_from("<I", data, pt)[0]
    for i in range(n):
        b = pt + 0x10 + i * 0x10
        if data[b:b + 4] == b"FIRM":
            off, ln = struct.unpack_from("<2I", data, b + 4)
            return b, off, ln
    raise RuntimeError("particao FIRM nao encontrada")


def string_at(d, ptr):
    o = ptr - XIP
    if not 0 <= o < len(d):
        return None
    e = d.find(b"\0", o)
    if e < 0 or e - o > 200:
        return None
    return d[o:e]


def proximo_livre(d, em=None):
    if em is not None:
        return em
    fim = LIVRE_INI
    for i in range(LIVRE_INI, LIVRE_INI + 0x2000):
        if d[i] != 0xFF:
            fim = i + 1
    return (fim + 3) & ~3


def main():
    ap = argparse.ArgumentParser(
        description="Realoca a tabela de strings de um idioma")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--idioma", default="pt", choices=sorted(IDIOMAS))
    ap.add_argument("--add", action="append", default=[],
                    help="texto de um id novo, no fim da tabela")
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
    base, n_ids, pool_off, vetor_off = IDIOMAS[a.idioma]
    base_addr = base + XIP

    cmap = struct.unpack_from("<%dH" % FONT_N, d, FONT_CMAP)
    gid = {c: i for i, c in enumerate(cmap)}

    print("=" * 72)
    print(f"OpenPod — realocacao da tabela de strings ({a.idioma})")
    print("=" * 72)
    print(f"  origem : {a.src}")
    print(f"  destino: {a.dst}")
    print()

    erros = []
    for off, nome in ((pool_off, "pool do get_string"),
                      (vetor_off, "vetor de bases")):
        got = struct.unpack_from("<I", d, off)[0]
        if got != base_addr:
            erros.append(f"0x{off:06X} ({nome}) = 0x{got:08X}, "
                         f"esperado 0x{base_addr:08X}")
    for t in a.add:
        falta = [c for c in t if ord(c) not in gid]
        if falta:
            erros.append(f"{t!r} tem caractere fora da fonte: {falta}")
    if erros:
        print("  ABORTADO — o firmware de entrada nao e o esperado:")
        for m in erros:
            print(f"    - {m}")
        return 1

    antigos = [struct.unpack_from("<I", d, base + i * 4) [0]
               for i in range(n_ids)]
    cursor = proximo_livre(d, a.em)
    print(f"  tabela original : 0x{base_addr:08X}, {n_ids} ids "
          f"({n_ids * 4} bytes)")
    print(f"  area livre livre a partir de : 0x{cursor:06X}")
    print()

    # 1 — strings novas
    novos_ptrs = []
    print("  IDS NOVOS")
    for i, t in enumerate(a.add):
        blob = t.encode("utf-8") + b"\0"
        if any(b != 0xFF for b in d[cursor:cursor + len(blob)]):
            print(f"  ABORTADO: 0x{cursor:06X} nao esta virgem.", file=sys.stderr)
            return 1
        d[cursor:cursor + len(blob)] = blob
        novos_ptrs.append(cursor + XIP)
        print(f"    id {n_ids + i:>3}  {t!r:<16} 0x{cursor + XIP:08X}")
        cursor = (cursor + len(blob) + 3) & ~3
    print()

    # 2 — tabela nova
    nova_base = cursor
    total = n_ids + len(novos_ptrs)
    tam = total * 4
    if nova_base + tam > LIVRE_FIM:
        print("  ABORTADO: nao cabe na area livre.", file=sys.stderr)
        return 1
    if any(b != 0xFF for b in d[nova_base:nova_base + tam]):
        print(f"  ABORTADO: 0x{nova_base:06X} nao esta virgem.", file=sys.stderr)
        return 1
    for i, p in enumerate(antigos + novos_ptrs):
        struct.pack_into("<I", d, nova_base + i * 4, p)
    print(f"  TABELA NOVA  0x{nova_base + XIP:08X}  {total} ids  ({tam} bytes)")
    print()

    # 3 — os dois ponteiros de base
    print("  PONTEIROS DE BASE")
    for off, nome in ((pool_off, "pool do get_string"),
                      (vetor_off, "vetor de bases")):
        struct.pack_into("<I", d, off, nova_base + XIP)
        print(f"    0x{off:06X}  0x{base_addr:08X} -> 0x{nova_base + XIP:08X}"
              f"   ({nome})")
    print()

    # 4 — conferencia: releitura da tabela nova, string por string
    ruim = 0
    for i in range(total):
        p = struct.unpack_from("<I", d, nova_base + i * 4)[0]
        s = string_at(d, p)
        esperado = (string_at(orig, antigos[i]) if i < n_ids
                    else a.add[i - n_ids].encode("utf-8"))
        if s != esperado:
            ruim += 1
            if ruim <= 5:
                print(f"    DIVERGE id {i}: {s!r} != {esperado!r}")
    if ruim:
        print(f"  ABORTADO: {ruim} ids divergem na releitura.", file=sys.stderr)
        return 1
    print(f"  conferencia: {total} ids relidos da tabela nova, "
          "todos identicos  OK")
    print()

    base_e, foff, flen = firm_entry(d)
    old = struct.unpack_from("<H", d, base_e + 0x0C)[0]
    new = fw.crc16(bytes(d[foff:foff + flen]))
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
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
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
