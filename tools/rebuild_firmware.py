#!/usr/bin/env python3
"""
rebuild_firmware.py — Desmonta e remonta a imagem de flash do GN-438.

PROPOSITO
    Prova que o formato do container foi entendido, executando o ciclo

        ORIGINAL  ->  PARSE  ->  REBUILD  ->  ORIGINAL

    O rebuild NAO copia o arquivo. Ele reconstroi o container a partir das
    estruturas identificadas e REGENERA todos os campos derivados:

        REGENERADO   cabecalho HLKJ (layout e campos conhecidos)
        REGENERADO   loadCrc do bootloader          (CRC do payload)
        REGENERADO   headerCrc do cabecalho HLKJ    (CRC de [0x00:0x5C])
        REGENERADO   tabela de particoes (nomes, offsets, tamanhos)
        REGENERADO   CRC de cada particao           (CRC do conteudo)
        REGENERADO   cabecalho da imagem FIRM
        REGENERADO   loadCrc da FIRM                (CRC dos 4 KiB iniciais)
        REGENERADO   todas as lacunas               (a partir do byte de preenchimento)

        PRESERVADO   payload do bootloader          (codigo opaco)
        PRESERVADO   corpo das particoes FIRM/TONE/PSMP (conteudo opaco)
        PRESERVADO   campos +0x18, +0x1C, +0x2C do HLKJ  (NAO IDENTIFICADOS)
        PRESERVADO   timestamp do cabecalho FIRM         (nao derivavel)

    Se qualquer lacuna nao for um preenchimento uniforme, ou se algum CRC
    lido divergir do calculado, o script PARA e reporta, em vez de
    corrigir silenciosamente.

USO
    python3 tools/rebuild_firmware.py --in <original.bin> --out <rebuilt.bin>
                                      [--json recipe.json]

DEPENDENCIAS
    Python 3 (biblioteca padrao) + tools/fw_common.py

EXEMPLO
    python3 tools/rebuild_firmware.py \
        --in  firmware/ORIGINAL/GN438_original.bin \
        --out firmware/WORKING/GN438_rebuilt_original.bin

LIMITACOES
    - O arquivo de entrada e aberto somente para leitura e nunca reescrito.
    - Campos marcados NAO IDENTIFICADOS sao copiados textualmente. Um
      round-trip bem sucedido prova que o container foi entendido, mas NAO
      prova que esses campos especificos foram compreendidos.
    - A particao PSMP tem CRC gravado 0x0000 na imagem original. O rebuild
      preserva esse zero porque escrever um CRC onde o original tem zero
      MUDARIA o firmware. Essa decisao vem da lista explicita
      fw_common.PARTICOES_SEM_CRC, nao do valor presente na entrada.
      NAO foi confirmado por disassembly que o boot ignora o CRC do PSMP.
"""

import argparse
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fw_common as fw


class Inconsistencia(Exception):
    """Levantada quando o parse encontra algo que contradiz o modelo."""


def parse(data: bytes):
    """Desmonta a imagem em uma receita verificavel."""
    problemas = []

    if len(data) != fw.FLASH_SIZE:
        raise Inconsistencia(
            f"tamanho {len(data)} != {fw.FLASH_SIZE} esperado")

    hdr = fw.BootHeader(data[:fw.BOOT_HDR_LEN])
    if hdr.magic != fw.BOOT_MAGIC:
        raise Inconsistencia(f"magic {hdr.magic!r} != {fw.BOOT_MAGIC!r}")
    if hdr.header_len != fw.BOOT_HDR_LEN:
        problemas.append(f"firmware_header_len=0x{hdr.header_len:X}, "
                         f"esperado 0x{fw.BOOT_HDR_LEN:X}")

    # --- payload do bootloader ---
    p_off = hdr.header_len
    p_end = p_off + hdr.load_length
    payload = data[p_off:p_end]
    c = fw.crc16(payload)
    if c != hdr.load_crc:
        problemas.append(f"loadCrc do bootloader: gravado 0x{hdr.load_crc:04X}, "
                         f"calculado 0x{c:04X}")
    hc = fw.crc16(data[:fw.BOOT_HDR_CRC_OFF])
    if hc != hdr.header_crc:
        problemas.append(f"headerCrc: gravado 0x{hdr.header_crc:04X}, "
                         f"calculado 0x{hc:04X}")

    # --- tabela de particoes ---
    pt = hdr.ptable_off
    n1, n2 = struct.unpack_from("<2I", data, pt)
    if n1 != n2:
        problemas.append(f"contagem de particoes divergente: {n1} != {n2}")
    parts = []
    for i in range(n1):
        b = pt + fw.PT_HDR_LEN + i * fw.PT_ENTRY_SIZE
        name = data[b:b + 4]
        off, size, crc = struct.unpack_from("<3I", data, b + 4)
        if off + size > len(data):
            raise Inconsistencia(
                f"particao {name!r} extrapola a flash: "
                f"0x{off:X}+0x{size:X} > 0x{len(data):X}")
        calc = fw.crc16(data[off:off + size])
        if name in fw.PARTICOES_SEM_CRC:
            if crc != 0:
                problemas.append(
                    f"particao {name.decode()}: esperado campo de CRC zerado "
                    f"(nao verificada), mas ha 0x{crc:04X}")
        elif crc == 0:
            problemas.append(
                f"particao {name.decode()}: campo de CRC zerado, mas esta "
                f"particao deveria ser verificada (calculado 0x{calc:04X})")
        elif calc != crc:
            problemas.append(f"CRC da particao {name.decode()}: "
                             f"gravado 0x{crc:04X}, calculado 0x{calc:04X}")
        parts.append(fw.Partition(name, off, size, crc))

    # --- cabecalho da imagem FIRM ---
    firm = next((p for p in parts if p.name == b"FIRM"), None)
    firm_hdr = None
    if firm:
        firm_hdr = fw.FirmHeader(
            data[firm.offset:firm.offset + fw.FIRM_HDR_LEN])
        body = data[firm.offset + firm_hdr.header_len:firm.end]
        fc = fw.crc16(body[:firm_hdr.load_length])
        if fc != firm_hdr.load_crc:
            problemas.append(f"loadCrc da FIRM: gravado 0x{firm_hdr.load_crc:04X}, "
                             f"calculado 0x{fc:04X}")

    # --- lacunas: cada uma tem de ser preenchimento uniforme ---
    ocupado = [(0, fw.BOOT_HDR_LEN + hdr.load_length),
               (pt, pt + fw.PT_HDR_LEN + n1 * fw.PT_ENTRY_SIZE)]
    ocupado += [(p.offset, p.end) for p in parts]
    ocupado.sort()

    lacunas = []
    cur = 0
    for s, e in ocupado:
        if s > cur:
            blob = data[cur:s]
            vals = set(blob)
            if len(vals) != 1:
                raise Inconsistencia(
                    f"lacuna 0x{cur:06X}-0x{s:06X} nao e preenchimento "
                    f"uniforme ({len(vals)} valores distintos) — "
                    f"pode conter dados nao mapeados")
            lacunas.append((cur, s - cur, blob[0]))
        cur = max(cur, e)
    if cur < len(data):
        blob = data[cur:]
        vals = set(blob)
        if len(vals) != 1:
            raise Inconsistencia(
                f"lacuna final 0x{cur:06X} nao e preenchimento uniforme")
        lacunas.append((cur, len(data) - cur, blob[0]))

    return {
        "hdr": hdr, "payload": payload, "payload_off": p_off,
        "ptable_off": pt, "n_parts": n1,
        "parts": parts, "firm_hdr": firm_hdr,
        "lacunas": lacunas, "problemas": problemas,
        "data": data,
    }


def build(r):
    """Remonta a imagem a partir da receita, regenerando os campos derivados."""
    out = bytearray(b"\x00" * fw.FLASH_SIZE)

    # 1. lacunas primeiro (base de preenchimento)
    for off, ln, val in r["lacunas"]:
        out[off:off + ln] = bytes([val]) * ln

    # 2. payload do bootloader
    payload = r["payload"]
    out[r["payload_off"]:r["payload_off"] + len(payload)] = payload

    # 3. cabecalho HLKJ — loadCrc e headerCrc RECALCULADOS
    out[0:fw.BOOT_HDR_LEN] = r["hdr"].rebuild(payload)

    # 4. particoes
    src = r["data"]
    novos_crc = {}
    for p in r["parts"]:
        if p.name == b"FIRM" and r["firm_hdr"]:
            fh = r["firm_hdr"]
            body = src[p.offset + fh.header_len:p.end]
            blob = fh.rebuild(body) + body          # loadCrc RECALCULADO
        else:
            blob = src[p.offset:p.end]
        if len(blob) != p.size:
            raise Inconsistencia(
                f"particao {p.name!r}: blob de {len(blob)} B != "
                f"tamanho declarado {p.size} B")
        out[p.offset:p.end] = blob
        # A decisao de zerar vem da POLITICA em fw.PARTICOES_SEM_CRC,
        # NUNCA do valor que estava na entrada. Inferir da entrada faria
        # um CRC zerado invalido ser propagado silenciosamente.
        novos_crc[p.name] = 0 if p.name in fw.PARTICOES_SEM_CRC \
            else fw.crc16(blob)

    # 5. tabela de particoes — CRCs RECALCULADOS
    pt = r["ptable_off"]
    struct.pack_into("<2I", out, pt, r["n_parts"], r["n_parts"])
    struct.pack_into("<2I", out, pt + 8, 0, 0)
    for i, p in enumerate(r["parts"]):
        b = pt + fw.PT_HDR_LEN + i * fw.PT_ENTRY_SIZE
        out[b:b + 4] = p.name
        struct.pack_into("<3I", out, b + 4, p.offset, p.size, novos_crc[p.name])

    return bytes(out), novos_crc


def main():
    ap = argparse.ArgumentParser(
        description="Desmonta e remonta a imagem de flash (round-trip)")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--json", default=None, help="grava a receita em JSON")
    args = ap.parse_args()

    src_abs = os.path.abspath(args.src)
    dst_abs = os.path.abspath(args.dst)
    if src_abs == dst_abs:
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2

    with open(args.src, "rb") as fh:      # somente leitura, sempre
        data = fh.read()

    print("=" * 74)
    print("PARSE")
    print("=" * 74)
    try:
        r = parse(data)
    except Inconsistencia as e:
        print(f"  INCONSISTENCIA: {e}")
        print("\n  PARADO. Nada foi gravado.")
        return 1

    h = r["hdr"]
    print(f"  magic               : {h.magic.decode()}")
    print(f"  loadToRam           : 0x{h.load_to_ram:08X}")
    print(f"  runFromRam          : 0x{h.run_from_ram:08X}")
    print(f"  firmware_header_len : 0x{h.header_len:X}")
    print(f"  loadLength          : 0x{h.load_length:X}")
    print(f"  loadCrc             : 0x{h.load_crc:04X}")
    print(f"  headerCrc (+0x5C)   : 0x{h.header_crc:04X}")
    print(f"  ptable_off          : 0x{h.ptable_off:08X}")
    print(f"  NAO IDENTIFICADOS   : +0x18=0x{h.unk_18:X}  "
          f"+0x1C=0x{h.unk_1c:X}  +0x2C=0x{h.unk_2c:X}")
    print(f"  particoes           : {r['n_parts']}")
    for p in r["parts"]:
        print(f"      {p.name.decode():<6} 0x{p.offset:08X} "
              f"0x{p.size:08X}  crc=0x{p.crc:04X}")
    if r["firm_hdr"]:
        f = r["firm_hdr"]
        print(f"  FIRM header         : len=0x{f.header_len:X} "
              f"loadToRam=0x{f.load_to_ram:08X} "
              f"loadLength=0x{f.load_length:X} loadCrc=0x{f.load_crc:04X}")
    print(f"  lacunas             : {len(r['lacunas'])}")
    for off, ln, val in r["lacunas"]:
        print(f"      0x{off:08X} +{ln:>8} bytes  preenchimento 0x{val:02X}")

    if r["problemas"]:
        print("\n  PROBLEMAS ENCONTRADOS NO ORIGINAL:")
        for p in r["problemas"]:
            print(f"      - {p}")
        print("\n  PARADO. Nada foi gravado.")
        return 1
    print("\n  parse consistente: todos os CRCs do original conferem")

    print()
    print("=" * 74)
    print("BUILD")
    print("=" * 74)
    out, novos = build(r)
    for name, c in novos.items():
        orig = next(p.crc for p in r["parts"] if p.name == name)
        tag = "preservado (era 0)" if c == 0 and orig == 0 else \
              ("igual" if c == orig else "DIFERENTE")
        print(f"  CRC recalculado {name.decode():<6} 0x{c:04X}   ({tag})")

    with open(args.dst, "wb") as fh:
        fh.write(out)
    print(f"\n  gravado: {args.dst} ({len(out)} bytes)")
    print(f"  sha256 origem : {hashlib.sha256(data).hexdigest()}")
    print(f"  sha256 rebuild: {hashlib.sha256(out).hexdigest()}")

    if args.json:
        rec = {
            "header": {k: getattr(h, k) for k in
                       ("load_to_ram", "run_from_ram", "header_len",
                        "load_length", "load_crc", "header_crc",
                        "unk_18", "unk_1c", "unk_2c", "ptable_off")},
            "partitions": [{"name": p.name.decode(), "offset": p.offset,
                            "size": p.size, "crc": p.crc} for p in r["parts"]],
            "gaps": [{"offset": o, "length": l, "fill": v}
                     for o, l, v in r["lacunas"]],
        }
        with open(args.json, "w") as fh:
            json.dump(rec, fh, indent=2)
        print(f"  receita: {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
