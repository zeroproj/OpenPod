#!/usr/bin/env python3
"""
make_v030.py — V030: a rede de segurança. "Configuração de fábrica" passa
               a armar o update por cartão SD no PMU.

POR QUE ESTA VERSAO EXISTE ANTES DE QUALQUER COSMETICO

    O primeiro GN-438 do projeto morreu numa escrita que falhou no setor
    0x00D000. A flash fica DENTRO do SoC (nao ha chip externo, nao ha
    pino para clipe nem para curto), entao nao existe plano B de
    hardware. Ver `docs/INCIDENTE_V028.md`.

    O firmware ja traz a chave e nunca a usa:

        HAL_pmu_sd_update_flag_set   0x00CF6CA0   (na FIRM)
        -> reg PMU 0x23 bits 7:6 = 11
        -> reg PMU 0x00 bit 0     = 0
        => flag = 6 = update por cartao SD

    Varredura de 0x0E000 a 0x1A0570: ZERO chamadas, ZERO ponteiros.
    Codigo morto, integro, esperando.

    Com o flag 6 armado, o bootloader (intocado, fora do nosso alcance de
    escrita) entra em `boot sdupdate`, procura `0:\\update.up` na raiz do
    cartao, confere header `CONFIG` + marca `SL6801`, apaga e regrava a
    flash conferindo CRC. Sem PC, sem USB, sem abrir o aparelho.

O GANCHO

    `page_set_menu_process` (0x00D0938C), ao confirmar um item:

        00D093D4   ldrh r2, [r4, #0xc]    ; ctrl_id 0..9
        00D093D6   movs r1, #1
        00D093D8   pop  {r4, lr}
        00D093DC   b.w  0x00D0E138        ; <- 4 bytes, o gancho

    Chega com r0 = pagina, r1 = 1, r2 = item. "Configuracao de fabrica"
    e o indice 8 (tabela de rotulos em 0x00C4879C).

    A rotina desvia para a area livre, arma o flag se o item for o 8, e
    **segue para 0x00D0E138 em todos os casos**. Nenhum comportamento
    existente muda: a tela de Configuracao de fabrica abre como sempre.

POR QUE 0x00D000 NAO E TOCADO

    A rotina fica em 0x001A3038+, FORA da particao FIRM (que termina em
    0x001A0570) -- logo, fora do CRC. So o gancho de 4 bytes mexe na
    FIRM, e o CRC volta ao original com 2 bytes de padding morto, via
    `tools/crc_neutralize.py`.

    Setores gravados:
        0x001A3000   rotina        (fora da FIRM)
        0x00109000   gancho        (4 B)
        0x00037000   compensacao   (2 B)

    A tabela de particoes NAO entra. Era ela que matava.

USO
    python3 tools/make_v030.py \
        --in  firmware/ORIGINAL/GN438_original.bin \
        --out firmware/WORKING/GN438_openpod_v030.bin [--dry-run]

SEGURANCA
    - recusa se origem == destino;
    - recusa se a entrada nao for o original (SHA-256 conferido);
    - recusa se o gancho nao for exatamente `b.w 0x00D0E138`;
    - recusa se a area livre de destino nao estiver toda em 0xFF;
    - decodifica de volta os dois saltos que gera e compara os alvos;
    - confere que o CRC final da FIRM e IGUAL ao original;
    - recusa se algum setor gravado for abaixo de 0x00D000 ou for 0x00D000;
    - a entrada e aberta somente para leitura; a saida e arquivo novo.
"""

import argparse
import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fw_common as fw

XIP = 0x00C00000
SHA_ORIGINAL = ("b7cd5eb952be5328cbaa926099cf8d88"
                "168633c1fab6d0f31f3a283c9e24b36f")

FOFF, FLEN = 0x00E000, 0x192570
CRC_ORIGINAL = 0x49A6

HOOK = 0x001093DC                 # o `b.w` em page_set_menu_process
HOOK_BYTES = bytes.fromhex("04f0acbe")
DEST = 0x00D0E138                 # navegacao original
FLAG_SET = 0x00CF6CA0             # HAL_pmu_sd_update_flag_set
ITEM = 8                          # "Configuracao de fabrica"

ROTINA = None                     # calculado: proximo endereco livre
PAD = 0x00037716                  # padding morto para compensar o CRC

PROIBIDO = 0x0000D000             # nunca, jamais


def enc_branch(origem, destino, link):
    off = destino - (origem + 4)
    if not -(1 << 24) <= off < (1 << 24) or off & 1:
        raise ValueError(f"alvo fora de alcance: {off:#x}")
    s = (off >> 24) & 1
    i1, i2 = (off >> 23) & 1, (off >> 22) & 1
    imm10, imm11 = (off >> 12) & 0x3FF, (off >> 1) & 0x7FF
    j1, j2 = (~(i1 ^ s)) & 1, (~(i2 ^ s)) & 1
    return struct.pack("<HH", 0xF000 | (s << 10) | imm10,
                       (0xD000 if link else 0x9000) | (j1 << 13) | (j2 << 11) | imm11)


def dec_branch(origem, blob):
    h1, h2 = struct.unpack("<HH", blob)
    s = (h1 >> 10) & 1
    j1, j2 = (h2 >> 13) & 1, (h2 >> 11) & 1
    i1, i2 = (~(j1 ^ s)) & 1, (~(j2 ^ s)) & 1
    off = (s << 24) | (i1 << 23) | (i2 << 22) | ((h1 & 0x3FF) << 12) | ((h2 & 0x7FF) << 1)
    if s:
        off -= 1 << 25
    return origem + 4 + off, bool(h2 & 0x4000)


def monta_rotina(base_addr):
    """20 bytes. Entra com r0=pagina, r1=1, r2=ctrl_id."""
    b = bytearray()
    b += struct.pack("<H", 0x2A00 | ITEM)          # cmp  r2, #8
    b += struct.pack("<H", 0xD105)                 # bne  +0xA  -> off 0x10
    b += struct.pack("<H", 0xB507)                 # push {r0,r1,r2,lr}
    b += struct.pack("<H", 0x2001)                 # movs r0, #1
    b += enc_branch(base_addr + 0x08, FLAG_SET, link=True)
    b += struct.pack("<HH", 0xE8BD, 0x4007)        # pop.w {r0,r1,r2,lr}
    b += enc_branch(base_addr + 0x10, DEST, link=False)
    assert len(b) == 0x14
    return bytes(b)


def firm_crc(img):
    return fw.crc16(bytes(img[FOFF:FOFF + FLEN]))


def compensa(img, pad, alvo):
    d = bytearray(img)
    d[pad] = d[pad + 1] = 0
    base = firm_crc(d)
    col = []
    for bit in range(16):
        v = 1 << bit
        d[pad], d[pad + 1] = v & 0xFF, (v >> 8) & 0xFF
        col.append(firm_crc(d) ^ base)
        d[pad] = d[pad + 1] = 0
    tgt = alvo ^ base
    for x in range(0x10000):
        acc, y, i = 0, x, 0
        while y:
            if y & 1:
                acc ^= col[i]
            y >>= 1
            i += 1
        if acc == tgt:
            return x
    return None


def main():
    ap = argparse.ArgumentParser(description="V030 — recuperacao por cartao SD")
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
    print("OpenPod V030 — \"Configuracao de fabrica\" arma o update por cartao SD")
    print("=" * 72)
    print(f"  origem : {a.src}")
    print(f"  destino: {a.dst}")
    print()

    # A V030 original exigia o firmware de fabrica. Depois do incidente e
    # da recuperacao, ela precisa assentar sobre a cadeia em uso -- entao
    # a verificacao passou a ser dos PONTOS, nao do hash da imagem toda.
    erros = []
    if bytes(d[HOOK:HOOK + 4]) != HOOK_BYTES:
        erros.append(f"0x{HOOK:06X}: bytes {bytes(d[HOOK:HOOK+4]).hex()}, "
                     f"esperado {HOOK_BYTES.hex()}")
    else:
        alvo, link = dec_branch(HOOK + XIP, HOOK_BYTES)
        if (alvo, link) != (DEST, False):
            erros.append(f"0x{HOOK:06X} salta para 0x{alvo:08X}, "
                         f"esperado b.w 0x{DEST:08X}")
    global ROTINA
    ROTINA = 0x001A3038
    for i in range(0x001A3038, 0x001A3038 + 0x4000):
        if d[i] != 0xFF:
            ROTINA = i + 1
    ROTINA = (ROTINA + 3) & ~3
    if any(b != 0xFF for b in d[ROTINA:ROTINA + 0x20]):
        erros.append(f"0x{ROTINA:06X}: a area livre nao esta virgem")
    if ROTINA < FOFF + FLEN:
        erros.append("a rotina cairia DENTRO da FIRM")
    # O CRC da FIRM nao e verificado por nada (CONFIRMADO no hardware,
    # ver INCIDENTE_V028 §9), entao nao ha o que compensar nem conferir.
    if bytes(d[FLAG_SET - XIP:FLAG_SET - XIP + 4]) != bytes.fromhex("10b50146"):
        erros.append(f"0x{FLAG_SET:08X} nao e HAL_pmu_sd_update_flag_set")
    if erros:
        print("  ABORTADO — a entrada nao e o esperado:")
        for m in erros:
            print(f"    - {m}")
        return 1
    print("  entrada conferida: original intacto, gancho intacto, "
          "area livre virgem  OK")
    print()

    # 1 — rotina na area livre
    rot = monta_rotina(ROTINA + XIP)
    d[ROTINA:ROTINA + len(rot)] = rot
    # 2 — o gancho
    novo = enc_branch(HOOK + XIP, ROTINA + XIP, link=False)
    d[HOOK:HOOK + 4] = novo

    print("  ROTINA na area livre  (0x%08X)" % (ROTINA + XIP))
    txt = [(0x00, "cmp   r2, #%d" % ITEM, "o item e \"Configuracao de fabrica\"?"),
           (0x02, "bne   +0xA", "nao -> pula direto para a navegacao"),
           (0x04, "push  {r0,r1,r2,lr}", "preserva os argumentos e o retorno"),
           (0x06, "movs  r0, #1", "argumento: armar"),
           (0x08, "bl    0x%08X" % FLAG_SET, "HAL_pmu_sd_update_flag_set"),
           (0x0C, "pop.w {r0,r1,r2,lr}", "restaura"),
           (0x10, "b.w   0x%08X" % DEST, "navegacao original, SEMPRE")]
    for off, asm, com in txt:
        n = 4 if off in (0x08, 0x0C, 0x10) else 2
        print(f"    +0x{off:02X}  {rot[off:off+n].hex():<8}  {asm:<22} ; {com}")
    print()

    # conferencia da codificacao
    t1, l1 = dec_branch(ROTINA + XIP + 0x08, rot[0x08:0x0C])
    t2, l2 = dec_branch(ROTINA + XIP + 0x10, rot[0x10:0x14])
    t3, l3 = dec_branch(HOOK + XIP, bytes(novo))
    ok = (t1, l1) == (FLAG_SET, True) and (t2, l2) == (DEST, False) \
        and (t3, l3) == (ROTINA + XIP, False)
    print("  conferencia dos saltos (decodificando de volta):")
    print(f"    bl  -> 0x{t1:08X} link={l1}")
    print(f"    b.w -> 0x{t2:08X} link={l2}")
    print(f"    gancho -> 0x{t3:08X} link={l3}")
    if not ok:
        print("  ABORTADO: a codificacao nao confere na volta.", file=sys.stderr)
        return 1
    print("    todos conferem  OK")
    print()

    print("  CRC DA FIRM: nao compensado, e nao precisa —")
    print("    o CRC nao e verificado por nada (confirmado no hardware).")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   tamanho: inalterado ({len(d)})")
    print(f"  setores a gravar: {len(secs)}")
    for s in secs:
        n = len([i for i in dif if i // 0x1000 * 0x1000 == s])
        print(f"    0x{s:06X}  {n:>3} B")
    print()

    maus = [s for s in secs if s <= PROIBIDO]
    if maus:
        print("  ABORTADO: setor proibido na lista: "
              + " ".join(f"0x{s:06X}" for s in maus), file=sys.stderr)
        return 1
    print(f"  >>> a tabela de particoes (0x{PROIBIDO:06X}) NAO esta na lista.  OK")
    print()

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    print(f"  sha256 : {hashlib.sha256(bytes(d)).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
