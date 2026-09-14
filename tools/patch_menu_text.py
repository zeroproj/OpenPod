#!/usr/bin/env python3
"""
patch_menu_text.py — Troca o texto de um item de menu, sem tocar em
                     nenhuma string existente.

POR QUE NAO EDITAR A STRING NO LUGAR

    As tabelas de idioma sao vetores de PONTEIROS, e varios ponteiros
    apontam para o MEIO de strings maiores. Dois casos ja encontrados
    neste firmware:

      0x00C4CD5D  "%02d:%02d"   e a cauda de "%02d. %02d:%02d:%02d"
      0x00C5537C  "vidoo"(pt 3) e a cauda de "Reproducao de video"

    Sobrescrever os bytes mudaria a string longa junto. O dado PARECE
    isolado e nao esta.

O QUE ESTA FERRAMENTA FAZ

    1. grava a string nova na AREA LIVRE da flash (0x001A3038 em diante,
       364 KiB de 0xFF fora de todas as particoes);
    2. repoe o ponteiro da tabela do idioma para o novo endereco XIP.

    Nenhuma string existente e alterada. O ponteiro antigo continua
    valido para quem mais o use.

    A leitura por XIP dessa area foi CONFIRMADA no V017: a string
    "OpenPod", gravada em 0x001A3038, apareceu na tela.

TABELAS DE IDIOMA (offsets de arquivo)

    de 0x52744   zh 0x523E4   en 0x52AA4   fr 0x52E04
    it 0x534C4   nl 0x53824   pt 0x53B84   es 0x53EE4

    Cada entrada e um ponteiro de 4 bytes: tabela + id*4.

USO
    python3 tools/patch_menu_text.py \
        --in  firmware/WORKING/GN438_openpod_v018.bin \
        --out firmware/WORKING/GN438_openpod_v019.bin \
        --set pt:3=Video  [--set pt:12=Extras ...]  [--dry-run]

    O texto pode ter acento; e gravado em UTF-8, como o firmware usa.

DEPENDENCIAS
    Python 3 + tools/fw_common.py

SEGURANCA
    - recusa se origem == destino;
    - recusa se o id estiver fora da tabela;
    - recusa se a string nao couber na area livre restante;
    - recusa se algum caractere nao existir na fonte (sairia em branco);
    - nunca escreve por cima de dado que nao seja 0xFF;
    - a entrada e aberta somente para leitura; a saida e arquivo novo.

LIMITACOES
    - Nao mede se o texto novo cabe na largura do rotulo da tela; use
      tools/preview_home.py depois para conferir.

ENDERECO EXPLICITO (--em)

    Sem ele a ferramenta aloca sozinha e o endereco passa a depender da
    ordem de aplicacao. Ver `tools/build.py`.
"""

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fw_common as fw

FLASH_XIP = 0x00C00000
LIVRE_INI = 0x001A3038
LIVRE_FIM = 0x001FC000          # inicio da particao PSMP

LANGS = {"de": 0x52744, "zh": 0x523E4, "en": 0x52AA4, "fr": 0x52E04,
         "it": 0x534C4, "nl": 0x53824, "pt": 0x53B84, "es": 0x53EE4}

# O portugues pode ter sido REALOCADO para a area livre
# (`relocate_lang_table.py`). Os enderecos acima sao os de fabrica; se a
# tabela mudou de lugar, escrever neles altera uma copia que ninguem le —
# e o patch "funciona" sem efeito nenhum. Foi exatamente o que aconteceu
# ao montar a receita do `build.py`.
#
# O codigo carrega a tabela viva deste ponteiro:
POOL_PT = 0x00121104


def tabela_viva(d, lang):
    """Endereco da tabela REALMENTE em uso para este idioma."""
    if lang != "pt":
        return LANGS[lang]
    p = struct.unpack_from("<I", d, POOL_PT)[0] - FLASH_XIP
    return p if 0 <= p < len(d) else LANGS[lang]
IDS_MAX = 200

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
    o = ptr - FLASH_XIP
    return d[o:d.index(b"\0", o)].decode("utf-8", "replace")


def proximo_livre(d, em=None):
    if em is not None:
        return em
    """Primeiro byte 0xFF depois do ultimo dado gravado na area livre."""
    fim = LIVRE_INI
    for i in range(LIVRE_INI, LIVRE_INI + 0x1000):
        if d[i] != 0xFF:
            fim = i + 1
    return (fim + 3) & ~3          # alinha em 4


def main():
    ap = argparse.ArgumentParser(
        description="Troca o texto de itens de menu via area livre")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--set", dest="sets", action="append", required=True,
                    metavar="IDIOMA:ID=TEXTO")
    ap.add_argument("--em", type=lambda x: int(x, 0), default=None,
                    help="endereco EXPLICITO das strings novas")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if os.path.abspath(args.src) == os.path.abspath(args.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2

    with open(args.src, "rb") as fh:
        orig = fh.read()
    data = bytearray(orig)

    cmap = struct.unpack_from("<%dH" % FONT_N, data, FONT_CMAP)
    gid = {c: i for i, c in enumerate(cmap)}

    pedidos = []
    for spec in args.sets:
        try:
            alvo, texto = spec.split("=", 1)
            lang, sid = alvo.split(":")
            sid = int(sid, 0)
        except ValueError:
            print(f"RECUSADO: --set mal formado: {spec!r}", file=sys.stderr)
            return 2
        if lang not in LANGS:
            print(f"RECUSADO: idioma {lang!r} desconhecido "
                  f"({', '.join(sorted(LANGS))})", file=sys.stderr)
            return 2
        if not 0 <= sid < IDS_MAX:
            print(f"RECUSADO: id {sid} fora da faixa", file=sys.stderr)
            return 2
        faltando = [c for c in texto if ord(c) not in gid]
        if faltando:
            print(f"RECUSADO: {texto!r} tem caractere fora da fonte: "
                  f"{faltando}", file=sys.stderr)
            return 2
        pedidos.append((lang, sid, texto))

    print("=" * 72)
    print("OpenPod — texto de itens de menu, via area livre")
    print("=" * 72)
    print(f"  origem : {args.src}")
    print(f"  destino: {args.dst}")
    print()

    cursor = proximo_livre(data, args.em)
    print(f"  area livre: primeiro endereco disponivel 0x{cursor:06X}")
    print()
    print(f"  {'idioma':<7}{'id':>4}  {'antes':<24}{'depois':<16}{'novo endereco'}")

    for lang, sid, texto in pedidos:
        pool = tabela_viva(data, lang) + sid * 4
        antigo = struct.unpack_from("<I", data, pool)[0]
        antes = string_at(data, antigo) if antigo >= FLASH_XIP else "?"

        blob = texto.encode("utf-8") + b"\0"
        if cursor + len(blob) > LIVRE_FIM:
            print("ABORTADO: nao cabe na area livre.", file=sys.stderr)
            return 1
        if any(b != 0xFF for b in data[cursor:cursor + len(blob)]):
            print(f"ABORTADO: 0x{cursor:06X} nao esta virgem.", file=sys.stderr)
            return 1

        data[cursor:cursor + len(blob)] = blob
        struct.pack_into("<I", data, pool, cursor + FLASH_XIP)
        print(f"  {lang:<7}{sid:>4}  {antes!r:<24}{texto!r:<16}"
              f"0x{cursor + FLASH_XIP:08X}")
        cursor = (cursor + len(blob) + 3) & ~3

    print()
    base, foff, flen = firm_entry(data)
    old_crc = struct.unpack_from("<H", data, base + 0x0C)[0]
    new_crc = fw.crc16(bytes(data[foff:foff + flen]))
    if args.dry_run:
        print(f"  CRC da FIRM: 0x{old_crc:04X} -> 0x{new_crc:04X} (nao gravado)")
    else:
        # R1: o CRC da FIRM nao e verificado pelo aparelho, e gravar aqui
        # poria o setor 0x00D000 (tabela de particoes) de volta na lista
        # de setores a escrever. Foi esse setor que matou o primeiro
        # aparelho. Achado pelo tools/build.py ao reconstruir do zero.
        pass   # NAO gravar o CRC (R1)
        print(f"  CRC da FIRM: 0x{old_crc:04X} -> 0x{new_crc:04X}")

    d2 = [i for i in range(len(orig)) if orig[i] != data[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in d2})
    print(f"  bytes alterados: {len(d2)}   tamanho: inalterado ({len(data)})")
    print(f"  setores de 4 KiB a regravar: {len(secs)}")
    print("    " + "  ".join(f"0x{s:06X}" for s in secs))
    print()

    if args.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0

    with open(args.dst, "wb") as fh:
        fh.write(data)
    print(f"  gravado: {args.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
