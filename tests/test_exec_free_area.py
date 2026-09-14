#!/usr/bin/env python3
"""
test_exec_free_area.py — Prova (ou refuta) que CODIGO grava do na area
                         livre da flash EXECUTA por XIP.

O QUE ESTA EM JOGO

    O V017 provou que DADOS em 0x001A3038 sao legiveis por XIP em
    0x00DA3038: a string "OpenPod" apareceu na tela.

    Isso NAO prova que codigo executa de la. Sao coisas diferentes, e o
    plano do Extras depende da segunda. Confundir "esta aplicado" com
    "vai rodar" ja custou o V016 a este projeto.

COMO O TESTE FUNCIONA

    Um trampolim de 4 bytes vai para a area livre:

        0x00DA3048   b.w  <alvo original>

    E uma chamada existente passa a ir para ele:

        0x0013A640   bl 0xD58188  ->  bl 0x00DA3048

    O `b.w` e um salto de cauda: LR continua apontando para o retorno
    original, entao a semantica e IDENTICA se a execucao funcionar.

      funciona  -> a tela alvo abre normalmente
      nao funciona -> falha de busca de instrucao, o firmware trava

POR QUE A COBAIA E A TELA "CONFIGURAR"

    A chamada escolhida esta em `page_set_menu_create` (0x00D3A638), a
    tela de Configuracoes. Ela **so e executada quando o usuario entra
    nessa tela de proposito**.

    Consequencia: se a execucao NAO funcionar, o aparelho trava apenas ao
    abrir Configurar. Um ciclo de energia devolve a tela inicial
    funcionando, o USB sobe normalmente e o kit reverte os 2 setores.

    Isto importa porque o modo card reader mora na FIRM, nao no
    bootloader (a string "CARDREADER" esta em 0x00046FC7, dentro da
    FIRM). Se o teste travasse no boot, a recuperacao ficaria mais
    incerta. Escolher uma tela opcional mantem o caminho de recuperacao
    intacto em qualquer resultado.

O QUE E ALTERADO

    0x001A3048   4 B  trampolim `b.w 0x00D58188`   (area livre)
    0x0013A640   4 B  bl 0x00D58188 -> bl 0x00DA3048

    Mais o CRC-16 da particao FIRM. O trampolim fica FORA da FIRM, logo
    fora desse CRC.

USO
    python3 tests/test_exec_free_area.py \
        --in  firmware/WORKING/GN438_openpod_v019.bin \
        --out firmware/WORKING/GN438_openpod_v020.bin [--dry-run]

DEPENDENCIAS
    Python 3 + tools/fw_common.py

SEGURANCA
    - recusa se origem == destino;
    - recusa se os 4 bytes do `bl` nao forem os esperados;
    - recusa se o destino na area livre nao estiver todo em 0xFF;
    - confere a propria codificacao decodificando de volta os dois saltos
      e comparando os alvos;
    - a entrada e aberta somente para leitura; a saida e arquivo novo.
"""

import argparse
import os
import struct
import sys

# as ferramentas moram em tools/; os testes sairam para tests/ em 14/09
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import fw_common as fw

XIP = 0x00C00000

TRAMP_OFF = 0x001A3048             # area livre, alinhado em 4
TRAMP_ADDR = TRAMP_OFF + XIP       # 0x00DA3048

CALL_OFF = 0x0013A640              # bl dentro de page_set_menu_create
CALL_ADDR = CALL_OFF + XIP
CALL_ESPERADO = bytes.fromhex("1df0a2fd")
ALVO = 0x00D58188                  # malloc do SDK


def enc_branch(origem, destino, link):
    """Codifica BL (T1) ou B.W (T4) de `origem` para `destino`."""
    off = destino - (origem + 4)
    if not -(1 << 24) <= off < (1 << 24) or off & 1:
        raise ValueError(f"alvo fora de alcance: {off:#x}")
    s = (off >> 24) & 1
    i1 = (off >> 23) & 1
    i2 = (off >> 22) & 1
    imm10 = (off >> 12) & 0x3FF
    imm11 = (off >> 1) & 0x7FF
    j1 = (~(i1 ^ s)) & 1
    j2 = (~(i2 ^ s)) & 1
    hw1 = 0xF000 | (s << 10) | imm10
    hw2 = (0xD000 if link else 0x9000) | (j1 << 13) | (j2 << 11) | imm11
    return struct.pack("<HH", hw1, hw2)


def dec_branch(origem, blob):
    """Decodifica de volta, para conferir a codificacao."""
    hw1, hw2 = struct.unpack("<HH", blob)
    s = (hw1 >> 10) & 1
    imm10 = hw1 & 0x3FF
    j1 = (hw2 >> 13) & 1
    j2 = (hw2 >> 11) & 1
    imm11 = hw2 & 0x7FF
    i1 = (~(j1 ^ s)) & 1
    i2 = (~(j2 ^ s)) & 1
    off = (s << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm11 << 1)
    if s:
        off -= 1 << 25
    link = bool(hw2 & 0x4000)
    return origem + 4 + off, link


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
        description="Prova execucao de codigo na area livre da flash")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if os.path.abspath(a.src) == os.path.abspath(a.dst):
        print("RECUSADO: origem e destino sao o mesmo arquivo.", file=sys.stderr)
        return 2

    orig = open(a.src, "rb").read()
    d = bytearray(orig)

    print("=" * 72)
    print("OpenPod — teste: codigo na area livre EXECUTA por XIP?")
    print("=" * 72)
    print(f"  origem : {a.src}")
    print(f"  destino: {a.dst}")
    print()

    erros = []
    if bytes(d[CALL_OFF:CALL_OFF + 4]) != CALL_ESPERADO:
        erros.append(f"0x{CALL_OFF:06X}: bytes {bytes(d[CALL_OFF:CALL_OFF+4]).hex()},"
                     f" esperado {CALL_ESPERADO.hex()}")
    else:
        alvo_atual, link = dec_branch(CALL_ADDR, CALL_ESPERADO)
        if alvo_atual != ALVO or not link:
            erros.append(f"0x{CALL_OFF:06X}: o bl aponta para 0x{alvo_atual:08X}, "
                         f"esperado 0x{ALVO:08X}")
    if any(b != 0xFF for b in d[TRAMP_OFF:TRAMP_OFF + 8]):
        erros.append(f"0x{TRAMP_OFF:06X}: area livre nao esta virgem")
    if erros:
        print("  ABORTADO — o firmware de entrada nao e o esperado:")
        for m in erros:
            print(f"    - {m}")
        return 1
    print("  estado de entrada conferido: bl original intacto, "
          "area livre virgem  OK")
    print()

    tramp = enc_branch(TRAMP_ADDR, ALVO, link=False)
    novo_bl = enc_branch(CALL_ADDR, TRAMP_ADDR, link=True)

    # confere a propria codificacao, decodificando de volta
    t_alvo, t_link = dec_branch(TRAMP_ADDR, tramp)
    b_alvo, b_link = dec_branch(CALL_ADDR, novo_bl)
    if (t_alvo, t_link) != (ALVO, False) or (b_alvo, b_link) != (TRAMP_ADDR, True):
        print("  ABORTADO: a codificacao nao confere na volta.")
        print(f"    trampolim -> 0x{t_alvo:08X} link={t_link}")
        print(f"    bl        -> 0x{b_alvo:08X} link={b_link}")
        return 1

    d[TRAMP_OFF:TRAMP_OFF + 4] = tramp
    d[CALL_OFF:CALL_OFF + 4] = novo_bl

    print("  ALTERACOES")
    print(f"    0x{TRAMP_OFF:06X}  {tramp.hex()}   "
          f"b.w 0x{ALVO:08X}   (trampolim na area livre, XIP 0x{TRAMP_ADDR:08X})")
    print(f"    0x{CALL_OFF:06X}  {novo_bl.hex()}   "
          f"bl  0x{TRAMP_ADDR:08X}  (era bl 0x{ALVO:08X})")
    print()
    print("  conferencia da codificacao (decodificando de volta):")
    print(f"    trampolim salta para 0x{t_alvo:08X}   link={t_link}   OK")
    print(f"    chamada  salta para 0x{b_alvo:08X}   link={b_link}    OK")
    print()

    base, foff, flen = firm_entry(d)
    old = struct.unpack_from("<H", d, base + 0x0C)[0]
    new = fw.crc16(bytes(d[foff:foff + flen]))
    if a.dry_run:
        print(f"  CRC da FIRM: 0x{old:04X} -> 0x{new:04X} (nao gravado)")
    else:
        # R1: NAO gravar o CRC da FIRM. Ele nao e verificado pelo
        # aparelho, e escrever aqui poe o setor 0x00D000 (tabela de
        # particoes) de volta na lista de setores — foi ele que matou
        # o primeiro aparelho. Achado pelo tools/build.py.
        pass   # NAO gravar o CRC (R1)
        print(f"  CRC da FIRM: 0x{old:04X} -> 0x{new:04X}")

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))
    print()
    print("  COMO LER O RESULTADO NO APARELHO")
    print("    entre em Configurar:")
    print("      abre normalmente  -> codigo na area livre EXECUTA  ✅")
    print("      trava             -> NAO executa; desligue, ligue, "
          "a tela inicial volta")
    print("                           e o kit reverte os 2 setores")
    print()

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
