#!/usr/bin/env python3
"""
test_roundtrip.py — Testes de regressao do rebuilder do OpenPod.

PROPOSITO
    Um round-trip que devolve um arquivo identico ao original NAO prova,
    sozinho, que o formato foi entendido: uma ferramenta que simplesmente
    copiasse o arquivo passaria no mesmo teste.

    Este script fecha essa lacuna com tres testes:

      T1  IDENTIDADE
          original -> parse -> build  deve reproduzir o original byte a byte.

      T2  REGENERACAO DE CRC (controle negativo)
          Zera na entrada os campos de CRC (headerCrc, loadCrc do boot,
          CRCs das particoes, loadCrc da FIRM) e verifica que o build os
          reconstroi com os valores corretos. Se o rebuilder estivesse
          copiando bytes, o resultado sairia com os campos zerados.

      T3  SENSIBILIDADE AO CONTEUDO
          Altera um byte do corpo da particao FIRM e verifica que o CRC
          emitido na tabela MUDA e passa a corresponder ao novo conteudo.
          Prova que o CRC acompanha os dados, e nao um valor memorizado.

    Nenhum teste escreve em firmware/ORIGINAL/. Tudo acontece em memoria.

USO
    python3 tests/test_roundtrip.py [--in firmware/ORIGINAL/GN438_original.bin]

DEPENDENCIAS
    Python 3 + tools/fw_common.py + tools/rebuild_firmware.py

SAIDA
    Codigo de saida 0 se os tres testes passarem, 1 caso contrario.
"""

import argparse
import hashlib
import os
import struct
import sys

# as ferramentas moram em tools/; os testes sairam para tests/ em 14/09
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import fw_common as fw
import rebuild_firmware as rb

FAILS = []


def ok(label, cond, detail=""):
    print(f"  [{'OK' if cond else 'FALHA'}] {label}" + (f" — {detail}" if detail else ""))
    if not cond:
        FAILS.append(label)
    return cond


def t1_identidade(data):
    print("-" * 70)
    print("T1 — IDENTIDADE: original -> parse -> build")
    print("-" * 70)
    r = rb.parse(data)
    ok("parse sem problemas", not r["problemas"], f"{len(r['problemas'])} problema(s)")
    out, _ = rb.build(r)
    diffs = sum(1 for i in range(len(data)) if data[i] != out[i])
    ok("bytes divergentes = 0", diffs == 0, f"{diffs}")
    ok("sha256 identico",
       hashlib.sha256(out).hexdigest() == hashlib.sha256(data).hexdigest())


def t2_regeneracao(data):
    print()
    print("-" * 70)
    print("T2 — REGENERACAO DE CRC (controle negativo)")
    print("-" * 70)
    z = bytearray(data)
    r0 = rb.parse(data)

    # zera todos os campos de integridade na ENTRADA
    struct.pack_into("<I", z, 0x14, 0)                       # loadCrc boot
    struct.pack_into("<I", z, fw.BOOT_HDR_CRC_OFF, 0)        # headerCrc
    pt = r0["ptable_off"]
    for i in range(r0["n_parts"]):
        struct.pack_into("<I", z, pt + fw.PT_HDR_LEN + i * fw.PT_ENTRY_SIZE + 12, 0)
    firm = next(p for p in r0["parts"] if p.name == b"FIRM")
    struct.pack_into("<I", z, firm.offset + 0x1C, 0)         # loadCrc FIRM

    zerados = sum(1 for off in (0x14, fw.BOOT_HDR_CRC_OFF, firm.offset + 0x1C)
                  if int.from_bytes(z[off:off+4], "little") == 0)
    ok("campos de CRC zerados na entrada", zerados == 3, f"{zerados}/3")

    # o parse deve RECUSAR a entrada adulterada — isso e uma feature
    r = rb.parse(bytes(z))
    # esperado: loadCrc boot, headerCrc, CRC FIRM zerado, CRC TONE zerado,
    # loadCrc FIRM  = 5 problemas. O PSMP zerado e legitimo pela politica.
    ok("parse detecta os CRCs invalidos", len(r["problemas"]) >= 5,
       f"{len(r['problemas'])} problema(s): " + "; ".join(r["problemas"]))

    # build a partir da receita adulterada: os CRCs tem de voltar corretos
    out, novos = rb.build(r)
    h = fw.BootHeader(out[:fw.BOOT_HDR_LEN])
    ok("headerCrc regenerado", h.header_crc == 0x34DB, f"0x{h.header_crc:04X}")
    ok("loadCrc do boot regenerado", h.load_crc == 0x759D, f"0x{h.load_crc:04X}")
    ok("CRC da FIRM regenerado", novos[b"FIRM"] == 0x49A6,
       f"0x{novos[b'FIRM']:04X}")
    ok("CRC da TONE regenerado", novos[b"TONE"] == 0x9177,
       f"0x{novos[b'TONE']:04X}")
    fh = fw.FirmHeader(out[firm.offset:firm.offset + fw.FIRM_HDR_LEN])
    ok("loadCrc da FIRM regenerado", fh.load_crc == 0x68E1, f"0x{fh.load_crc:04X}")
    ok("saida identica ao original apesar da entrada adulterada",
       bytes(out) == data)


def t3_sensibilidade(data):
    print()
    print("-" * 70)
    print("T3 — SENSIBILIDADE AO CONTEUDO")
    print("-" * 70)
    r0 = rb.parse(data)
    firm = next(p for p in r0["parts"] if p.name == b"FIRM")

    # um byte bem dentro do corpo da FIRM, fora dos 4 KiB carregados em RAM
    alvo = firm.offset + 0x30 + 0x100000
    m = bytearray(data)
    antes = m[alvo]
    m[alvo] = antes ^ 0xFF
    ok("byte alterado no corpo da FIRM", m[alvo] != data[alvo],
       f"0x{alvo:08X}: 0x{antes:02X} -> 0x{m[alvo]:02X}")

    r = rb.parse(bytes(m))
    out, novos = rb.build(r)
    novo_crc = novos[b"FIRM"]
    esperado = fw.crc16(bytes(out[firm.offset:firm.end]))

    ok("CRC da FIRM mudou", novo_crc != 0x49A6,
       f"0x49A6 -> 0x{novo_crc:04X}")
    ok("novo CRC corresponde ao novo conteudo", novo_crc == esperado,
       f"tabela 0x{novo_crc:04X} / conteudo 0x{esperado:04X}")
    ok("loadCrc da FIRM inalterado (byte fora dos 4 KiB)",
       fw.FirmHeader(bytes(out[firm.offset:firm.offset+fw.FIRM_HDR_LEN])).load_crc
       == 0x68E1)
    ok("saida difere do original", bytes(out) != data)


def main():
    ap = argparse.ArgumentParser(description="Testes de regressao do rebuilder")
    ap.add_argument("--in", dest="src",
                    default="firmware/ORIGINAL/GN438_original.bin")
    args = ap.parse_args()
    data = open(args.src, "rb").read()

    print("=" * 70)
    print(f"TESTES DE ROUND-TRIP — {args.src}")
    print("=" * 70)
    t1_identidade(data)
    t2_regeneracao(data)
    t3_sensibilidade(data)

    print()
    print("=" * 70)
    if FAILS:
        print(f"RESULTADO: {len(FAILS)} FALHA(S) — {', '.join(FAILS)}")
    else:
        print("RESULTADO: TODOS OS TESTES PASSARAM")
    print("=" * 70)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
