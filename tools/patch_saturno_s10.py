#!/usr/bin/env python3
"""
patch_saturno_s10.py — SATURNO S10: a cor do texto vem da tabela.

O MANTENEDOR PERGUNTOU

    "as fontes estao todas com cor branca? isso tb esta centralizado?
     paleta do seletor tb a cor e centralizada?"

    Conferi em vez de afirmar, e a resposta era:

        fontes brancas?            SIM   os dois getters devolvem -1
        cor do texto centralizada? NAO   `cor_texto` esta na tabela e
                                         NINGUEM a le
        seletor centralizado?      SIM   3 pontos leem `cor_selecao`

    O branco vinha dos **getters patchados na V013**, nao da tabela. E
    exatamente a segunda fonte de verdade que o Saturno existe para
    eliminar: mudar `cor_texto` na tabela nao mudava nada.

O QUE FAZ

    A —  Os dois getters de cor de texto passam a LER A TABELA:

            0x00D21384   getter do tema  (11 pontos o usam)
            0x00D2E948   getter da home  ( 1 ponto)

         Sao os pontos unicos por onde passa a cor de texto da faixa, das
         linhas, dos rotulos da home e do relogio. Patch na funcao, nao
         nos chamadores.

    B —  `cor_texto_sel` passa a existir de verdade: a rotina da linha
         acrescenta a cor de texto no estado FOCUS_KEY (seletor 4).
         Antes o texto selecionado herdava o normal; agora sao dois
         campos independentes na tabela.

O QUE NAO E TOCADO, E POR QUE

    Dentro das 36 telas de lista ha **4** pontos que definem cor de texto
    propria:

        0x00128DD6, 0x00128F18 (imediato 3), 0x00128FC0  pagina 0x23
        0x0012B882                                        pagina 0x12

    Sao cores de ESTADO (a 0x23 e o menu de Bluetooth: conectado,
    pareando, etc.). Nao sao ruido de padronizacao, e mudar sem entender
    o que cada uma significa seria o mesmo atalho de sempre. **Ficam
    anotadas, nao alteradas.**

USO
    python3 tools/patch_saturno_s10.py \\
        --in  firmware/WORKING/GN438_openpod_v069.bin \\
        --out firmware/WORKING/GN438_openpod_v070.bin [--dry-run]

SEGURANCA
    - exige que os dois getters estejam no estado da V013 (`mov.w r0,#-1`);
      se algum nao estiver, a cor vem de outro lugar e o patch RECUSA;
    - exige o gancho da linha como o S3 deixou;
    - confere cada instrucao montada COM OPERANDOS, sem filtrar as linhas
      de literal (foi num literal filtrado que o `patch_extras` errou);
    - recusa diferenca abaixo de 0x00E000 (R1); nao toca no CRC.
"""

import argparse
import struct
import sys

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
except ImportError:
    sys.exit("capstone ausente: pip3 install capstone")

XIP = 0x00C00000
FLASH_SIZE = 0x200000

TAB = 0x00DA5400
OFS_TEXTO, OFS_TEXTO_SEL = 0x06, 0x08

GETTERS = {0x00121384: "getter do tema", 0x0012E948: "getter da home"}
GETTER_ESPERADO = bytes.fromhex("4ff0ff30")          # mov.w r0, #-1

SET_TEXT_COLOR = 0xD4D10A
LINHA_S3 = 0x00DA5558
GANCHO_LINHA = 0x001217AA
GANCHO_LINHA_ESPERADO = bytes.fromhex("83f0d5fe")    # bl 0xda5558
ESTADO_FOCUS = 4

BLOB = 0x001A5980
BLOB_MAX = 0x80


def bl(origem, destino, link=True):
    off = destino - (origem + 4)
    if off & 1 or not (-(1 << 24) <= off < (1 << 24)):
        raise ValueError("fora de alcance")
    off >>= 1
    s = (off >> 23) & 1
    i1, i2 = (off >> 22) & 1, (off >> 21) & 1
    hw1 = 0xF000 | (s << 10) | ((off >> 11) & 0x3FF)
    hw2 = ((0xD000 if link else 0x9000)
           | (((~i1 & 1) ^ s) << 13) | (((~i2 & 1) ^ s) << 11) | (off & 0x7FF))
    return struct.pack("<HH", hw1, hw2)


def monta(base):
    out, cur = {}, base

    def emite(nome, corpo):
        nonlocal cur
        out[nome] = (cur, corpo(cur))
        cur += len(out[nome][1])

    def cor_texto(b):
        c = bytearray()
        pos = len(c)
        c += b"\0\0"                       # ldr r0, =TAB
        c += struct.pack("<H", 0x88C0)     # ldrh r0, [r0, #6]
        c += struct.pack("<H", 0x4770)     # bx lr
        while len(c) % 4:
            c += struct.pack("<H", 0xBF00)
        lit = len(c)
        c += struct.pack("<I", TAB)
        pc = (b + pos + 4) & ~3
        struct.pack_into("<H", c, pos, 0x4800 | (((b + lit) - pc) >> 2))
        return bytes(c)
    emite("cor_texto", cor_texto)

    def linha(b):
        c = bytearray()
        c += struct.pack("<H", 0xB501)     # push {r0, lr}
        c += bl(b + len(c), LINHA_S3)      # a cadeia que ja existia
        c += struct.pack("<H", 0x9800)     # ldr r0, [sp]
        pos = len(c)
        c += b"\0\0"                       # ldr r1, =TAB
        c += struct.pack("<H", 0x8909)     # ldrh r1, [r1, #8]  cor_texto_sel
        c += struct.pack("<H", 0x2200 | ESTADO_FOCUS)   # movs r2, #4
        c += bl(b + len(c), SET_TEXT_COLOR)
        c += struct.pack("<H", 0xBD01)     # pop {r0, pc}
        while len(c) % 4:
            c += struct.pack("<H", 0xBF00)
        lit = len(c)
        c += struct.pack("<I", TAB)
        pc = (b + pos + 4) & ~3
        struct.pack_into("<H", c, pos, 0x4900 | (((b + lit) - pc) >> 2))
        return bytes(c)
    emite("linha", linha)
    return out


ESPERADO = {
    "cor_texto": ["ldr r0, [pc, #4]", "ldrh r0, [r0, #6]", "bx lr"],
    "linha": ["push {r0, lr}", "bl #0xda5558", "ldr r0, [sp]",
              "ldr r1, [pc, #8]", "ldrh r1, [r1, #8]", "movs r2, #4",
              "bl #0xd4d10a", "pop {r0, pc}"],
}


def main():
    ap = argparse.ArgumentParser(description="Saturno S10: cor do texto")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.src == a.dst:
        sys.exit("origem e destino iguais")
    with open(a.src, "rb") as fh:
        orig = fh.read()
    if len(orig) != FLASH_SIZE:
        sys.exit(f"tamanho inesperado: {len(orig)}")
    data = bytearray(orig)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    erros = []
    for off, nome in GETTERS.items():
        if bytes(data[off:off + 4]) != GETTER_ESPERADO:
            erros.append(f"{nome} em 0x{off:06X} nao esta no estado da V013 "
                         f"({bytes(data[off:off+4]).hex()}) — a cor de texto "
                         "vem de outro lugar; RECUSADO")
    if bytes(data[GANCHO_LINHA:GANCHO_LINHA + 4]) != GANCHO_LINHA_ESPERADO:
        erros.append(f"gancho da linha em 0x{GANCHO_LINHA:06X} inesperado")
    if any(x != 0xFF for x in data[BLOB:BLOB + BLOB_MAX]):
        erros.append(f"area livre 0x{BLOB:06X} nao esta virgem")

    rots = monta(BLOB + XIP)
    for nome, (addr, b) in rots.items():
        got = [f"{i.mnemonic} {i.op_str}".strip() for i in md.disasm(b, addr)]
        got = got[:len(ESPERADO[nome])]
        if got != ESPERADO[nome]:
            erros.append(f"rotina {nome} nao confere:\n"
                         f"      esperado {ESPERADO[nome]}\n"
                         f"      obtido   {got}")
    if erros:
        print("RECUSADO:")
        for x in erros:
            print("   -", x)
        return 1

    t = struct.unpack_from("<H", data, 0x001A5400 + OFS_TEXTO)[0]
    ts = struct.unpack_from("<H", data, 0x001A5400 + OFS_TEXTO_SEL)[0]
    print()
    print("  SATURNO S10 — a cor do texto vem da tabela")
    print()
    print(f"  cor_texto      0x{t:04X}    cor_texto_sel  0x{ts:04X}")
    print()
    print("  ALTERACOES")
    for nome, (addr, b) in sorted(rots.items(), key=lambda x: x[1][0]):
        data[addr - XIP:addr - XIP + len(b)] = b
        print(f"    0x{addr - XIP:06X}  {nome:10s} {len(b):3d} B")
    for off, nome in GETTERS.items():
        data[off:off + 4] = bl(off + XIP, rots["cor_texto"][0], link=False)
        print(f"    0x{off:06X}  {nome} -> le a tabela")
    data[GANCHO_LINHA:GANCHO_LINHA + 4] = bl(GANCHO_LINHA + XIP,
                                             rots["linha"][0])
    print(f"    0x{GANCHO_LINHA:06X}  linha -> acrescenta cor_texto_sel "
          f"(seletor {ESTADO_FOCUS} = FOCUS_KEY)")
    print()
    print("  NAO tocados (cores de ESTADO, nao de padronizacao):")
    for x in (0x00128DD6, 0x00128F18, 0x00128FC0, 0x0012B882):
        print(f"    0x{x:06X}")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != data[i]]
    if dif and min(dif) < 0x00E000:
        sys.exit(f"RECUSADO: tocaria 0x{min(dif):06X} (R1)")
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: {len(secs)}  "
          + "  ".join(f"0x{s:06X}" for s in secs))
    print("  CRC da FIRM: campo intocado (R1)")
    print()
    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    with open(a.dst, "wb") as fh:
        fh.write(data)
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
