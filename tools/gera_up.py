#!/usr/bin/env python3
"""
gera_up.py — Empacota um firmware como `.up`, o formato oficial da Shenju.

PARA QUE

    Da ao projeto um **segundo caminho de instalacao**, complementar ao
    kit de setores:

      kit de setores (Linux/Mac)   grava so o que mudou, segundos
      .up (Windows, Flashloader)   imagem inteira, GUI, arquivo unico

    O `.up` tambem serve de **recuperacao**: o bootloader le
    `0:\\update.up` do cartao, e o Flashloader grava com o firmware morto.

O FORMATO, DECODIFICADO

    Cabecalho de 0x100 bytes, o resto e a imagem crua a partir de 0:

        0x00  "CONFIG"
        0x06  u32   0x100   offset do payload (o proprio cabecalho)
        0x10  u32   tamanho do payload
        0x14  u16   CRC-16/CCITT-FALSE do payload
        0x16  "SL6801"
        0xFE  55 AA   assinatura de fim de cabecalho

    Validado contra `B27_251112.up`, arquivo oficial da Shenju: o mesmo
    algoritmo reproduz o CRC gravado por eles.

ATE ONDE COBRIR

    O `.up` de fabrica cobre 0x000000..0x1A3038 -- exatamente o fim da
    particao TONE. **Nao basta para o OpenPod:** nossas rotinas e strings
    vivem na area livre logo depois, a partir de 0x1A3038.

    Por isso o tamanho e calculado: ate o ultimo byte nao-0xFF da area
    livre, arredondado para 4 KiB. A PSMP (0x1FC000, configuracoes do
    usuario) fica sempre de fora.

USO
    python3 tools/gera_up.py \\
        --in  firmware/WORKING/GN438_openpod_v044.bin \\
        --out "firmware/RELEASE/OpenPod 1.0/OpenPod_1.0.up"

    python3 tools/gera_up.py --autoteste
        reconstroi o .up original e compara byte a byte com
        firmware/WORKING/update_restore_original.up

SEGURANCA
    - recusa se a imagem nao tiver 2 MiB;
    - recusa se o tamanho calculado alcancar a PSMP;
    - relê o proprio arquivo gerado e confere magic, tamanho e CRC.
"""

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fw_common as fw

HDR = 0x100
TONE_FIM = 0x1A3038
PSMP = 0x1FC000
LIVRE_INI = 0x1A3038


def tamanho_util(d):
    """Ate o ultimo byte gravado na area livre, arredondado para 4 KiB."""
    ult = LIVRE_INI
    for i in range(LIVRE_INI, PSMP):
        if d[i] != 0xFF:
            ult = i + 1
    if ult <= TONE_FIM:
        return TONE_FIM
    return (ult + 0xFFF) & ~0xFFF


def monta(d, tam):
    h = bytearray(HDR)
    h[0:6] = b"CONFIG"
    struct.pack_into("<I", h, 0x06, HDR)
    struct.pack_into("<I", h, 0x10, tam)
    struct.pack_into("<H", h, 0x14, fw.crc16(bytes(d[:tam])))
    h[0x16:0x1C] = b"SL6801"
    h[0xFE:0x100] = b"\x55\xaa"      # assinatura, presente nos dois .up oficiais
    return bytes(h) + bytes(d[:tam])


def confere(blob, esperado_tam):
    ok = []
    ok.append(("magic", blob[:6] == b"CONFIG"))
    ok.append(("offset do payload", struct.unpack_from("<I", blob, 6)[0] == HDR))
    tam = struct.unpack_from("<I", blob, 0x10)[0]
    ok.append(("tamanho", tam == esperado_tam))
    ok.append(("marca SL6801", blob[0x16:0x1C] == b"SL6801"))
    ok.append(("assinatura 55AA", blob[0xFE:0x100] == b"\x55\xaa"))
    crc = struct.unpack_from("<H", blob, 0x14)[0]
    ok.append(("CRC", crc == fw.crc16(blob[HDR:HDR + tam])))
    ok.append(("tamanho do arquivo", len(blob) == HDR + tam))
    return ok


def autoteste():
    ref = "firmware/WORKING/update_restore_original.up"
    src = "firmware/ORIGINAL/GN438_original.bin"
    if not (os.path.exists(ref) and os.path.exists(src)):
        print("autoteste: arquivos de referencia ausentes.", file=sys.stderr)
        return 1
    d = open(src, "rb").read()
    esperado = open(ref, "rb").read()
    gerado = monta(d, TONE_FIM)
    print("=" * 72)
    print("autoteste — reconstruir o .up original e comparar")
    print("=" * 72)
    print(f"  referencia : {ref}  ({len(esperado)} B)")
    print(f"  gerado     : {len(gerado)} B")
    if gerado == esperado:
        print("\n  IDENTICO byte a byte  OK")
        print("  o formato esta correto: cabecalho, tamanho, CRC e marca.")
        return 0
    dif = [i for i in range(min(len(gerado), len(esperado)))
           if gerado[i] != esperado[i]]
    print(f"\n  DIVERGE em {len(dif)} bytes; primeiros: "
          f"{[hex(x) for x in dif[:8]]}")
    return 1


def main():
    ap = argparse.ArgumentParser(description="Empacota firmware como .up")
    ap.add_argument("--in", dest="src")
    ap.add_argument("--out", dest="dst")
    ap.add_argument("--autoteste", action="store_true")
    a = ap.parse_args()
    if a.autoteste:
        return autoteste()
    if not (a.src and a.dst):
        ap.error("--in e --out sao obrigatorios (ou use --autoteste)")

    d = open(a.src, "rb").read()
    print("=" * 72)
    print("OpenPod — empacotando como .up")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n")
    if len(d) != 0x200000:
        print(f"  ABORTADO: {len(d)} bytes, esperado 2097152.", file=sys.stderr)
        return 1

    tam = tamanho_util(d)
    print("  COBERTURA")
    print(f"    fim da particao TONE     0x{TONE_FIM:06X}")
    print(f"    area livre em uso ate    0x{tam:06X}"
          f"   ({tam - TONE_FIM} B a mais)")
    print(f"    PSMP em 0x{PSMP:06X}          "
          f"{'INTOCADA' if tam < PSMP else 'EM RISCO'}")
    if tam >= PSMP:
        print("  ABORTADO: o payload alcancaria a PSMP.", file=sys.stderr)
        return 1
    print()

    blob = monta(d, tam)
    os.makedirs(os.path.dirname(a.dst) or ".", exist_ok=True)
    open(a.dst, "wb").write(blob)

    relido = open(a.dst, "rb").read()
    print("  CONFERENCIA (relendo o arquivo gravado)")
    tudo = True
    for nome, v in confere(relido, tam):
        print(f"    {nome:<20} {'OK' if v else 'FALHOU'}")
        tudo &= v
    if not tudo:
        print("  ABORTADO: o arquivo gerado nao confere.", file=sys.stderr)
        return 1
    print()
    print(f"  gravado: {a.dst}  ({len(blob)} B)")
    print(f"  CRC do payload: 0x{struct.unpack_from('<H', relido, 0x14)[0]:04X}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
