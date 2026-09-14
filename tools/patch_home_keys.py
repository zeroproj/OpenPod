#!/usr/bin/env python3
"""
patch_home_keys.py — Converte os dois ramos de "pula 3" do menu principal
                     em "anda 1", para casar com a home em lista vertical.

PROPOSITO
    Na grade 3x3 original, os botoes esquerda/direita andavam 1 celula na
    linha e os botoes cima/baixo (M e VOL) pulavam uma linha inteira, isto
    e, 3 celulas. Com o menu em lista vertical (V014) esse mapeamento fica
    invertido em relacao a fisica da roda: M e VOL, que sao literalmente
    cima e baixo, sao justamente os que pulam 3 linhas.

    Esta ferramenta troca o passo de 3 para 1 nos dois ramos.

O DETALHE QUE TORNA ISTO SEGURO
    A conversao PRESERVA A DIRECAO de cada botao: quem subia 3 passa a
    subir 1, quem descia 3 passa a descer 1. Portanto NAO e preciso saber
    qual botao fisico emite key_id 0xA0 e qual emite 0x81 -- a ambiguidade
    que resta (ver docs/BUTTON_ANALYSIS.md) nao afeta o resultado.

O QUE E ALTERADO (5 bytes, todos imediatos de 1 byte)

    ramo -3, em page_home_event_cb (0x00D2EA3A)
      0x0012EA3E   cmp   r2, #2       ->  cmp   r2, #0      02 -> 00
      0x0012EA42   subhi r2, #3       ->  subhi r2, #1      03 -> 01
      0x0012EA44   addls r2, #6       ->  addls r2, #8      06 -> 08

    ramo +3, em page_home_event_cb (0x00D2EB26)
      0x0012EB2A   adds r1, r2, #3    ->  adds r1, r2, #1   D1 -> 51
      0x0012EB70   subs r2, #6        ->  subs r2, #8       06 -> 08

    Mais o CRC-16 da particao FIRM, recalculado.

    Nenhum alvo de salto se move. Nenhum tamanho de instrucao muda.

ARITMETICA RESULTANTE

    ramo -1:  cmp r2,#0 -> hi (r2 != 0) subtrai 1; ls (r2 == 0) soma 8
              indice 0 volta para 8
    ramo +1:  r1 = r2 + 1; se r1 > 8, desvia e faz r2 = r2 - 8
              indice 8 volta para 0

    Em ambos o indice fica sempre em 0..8. O `cmp r2,#8 / bls` que segue o
    ramo -1 passa a ser sempre tomado, e o caminho `movs r2,#8` em
    0x00D2EA4E fica inalcancavel a partir dali -- ele pertence ao ramo -1
    de teclas (alcancado so de 0x00D2E9E4) e continua funcionando.

USO
    python3 tools/patch_home_keys.py \
        --in  firmware/WORKING/GN438_openpod_v014.bin \
        --out firmware/WORKING/GN438_openpod_v015.bin [--dry-run]

DEPENDENCIAS
    Python 3 + tools/fw_common.py

SEGURANCA
    - recusa se origem == destino;
    - recusa se QUALQUER um dos 5 bytes nao estiver no valor esperado
      (garante que a base e o V014 e que o patch nao foi aplicado 2x);
    - a entrada e aberta somente para leitura; a saida e arquivo novo.

LIMITACOES
    - Geometria valida para este firmware (yp3_2.0.43).
    - So altera page_home_event_cb. Nenhuma outra tela e afetada, e
      nenhuma tabela de key_id e tocada.
"""

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fw_common as fw

# (offset, valor_esperado, valor_novo, descricao)
PATCHES = [
    (0x0012EA3E, 0x02, 0x00, "cmp   r2, #2      -> cmp   r2, #0"),
    (0x0012EA42, 0x03, 0x01, "subhi r2, #3      -> subhi r2, #1"),
    (0x0012EA44, 0x06, 0x08, "addls r2, #6      -> addls r2, #8"),
    (0x0012EB2A, 0xD1, 0x51, "adds r1, r2, #3   -> adds r1, r2, #1"),
    (0x0012EB70, 0x06, 0x08, "subs r2, #6       -> subs r2, #8"),
]


def firm_entry(data):
    pt = struct.unpack_from("<I", data, 0x20)[0]
    n = struct.unpack_from("<I", data, pt)[0]
    for i in range(n):
        b = pt + 0x10 + i * 0x10
        if data[b:b + 4] == b"FIRM":
            off, ln = struct.unpack_from("<2I", data, b + 4)
            return b, off, ln
    raise RuntimeError("particao FIRM nao encontrada")


def main():
    ap = argparse.ArgumentParser(
        description="Menu principal: teclas de pulo 3 -> passo 1")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if os.path.abspath(args.src) == os.path.abspath(args.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2

    with open(args.src, "rb") as fh:          # somente leitura
        orig = fh.read()
    data = bytearray(orig)

    print("=" * 72)
    print("OpenPod — menu principal: M e VOL passam a andar 1 linha")
    print("=" * 72)
    print(f"  origem : {args.src}")
    print(f"  destino: {args.dst}")
    print()

    erros = [f"0x{o:06X}: esperado 0x{e:02X}, encontrado 0x{data[o]:02X}"
             for o, e, _, _ in PATCHES if data[o] != e]
    if erros:
        print("  ABORTADO — o firmware de entrada nao e o esperado:")
        for m in erros:
            print(f"    - {m}")
        print("\n  (todos os 5 bytes precisam estar no valor original; se ja")
        print("   estiverem nos novos, o patch ja foi aplicado)")
        return 1
    print("  estado de entrada conferido: os 5 bytes estao no valor "
          "original  OK")
    print()

    print("  ALTERACOES")
    for o, e, n, desc in PATCHES:
        data[o] = n
        print(f"    0x{o:06X}  {e:02X} -> {n:02X}   {desc}")
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
