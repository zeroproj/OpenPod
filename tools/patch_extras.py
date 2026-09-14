#!/usr/bin/env python3
"""
patch_extras.py — Os itens do Extras passam a abrir as telas certas.

    !! ESTA FERRAMENTA, SOZINHA, PRODUZ UMA ROTA QUEBRADA. !!
    Ela manda a mensagem para a ENTRADA de `page1_process`, que exige
    msg[0x0a]==2; o Extras chega com 4 e a mensagem morre antes do `tbh`
    (na 2.1: "clico e nao leva a nada"). Rode SEMPRE em seguida:

        tools/patch_extras_fix.py

    que entra depois das guardas e preserva o campo 0x0a. O diagnostico
    completo esta no cabecalho daquela ferramenta.

COMO ISTO FOI DIAGNOSTICADO — do firmware DE FABRICA, nao da nossa cadeia

    Decisao do mantenedor: *"nao vamos levar como padrao as versoes que
    geramos, pq elas podem estar erradas. Vamos pegar o firmware original
    e ver para onde os itens do extra apontavam."* Certissimo — a cadeia
    V014..V068 acumula decisoes minhas, e raciocinar sobre ela propaga
    erro.

    No `GN438_original.bin`:

        page_home_menu (pagina 0x53) tem TRES itens:
            item 0  id  7  'Despertador'
            item 1  id  4  'Imagem'
            item 2  id 11  'Dicionario'

        e o modulo dela, `pstr_page84_process` (0x00D0CC0C), despacha
        exatamente esses tres:

            0x00D0CC7E   cmp r2, #2
            0x00D0CC80   bhi 0xd0cd6e      ; > 2 -> sai sem fazer nada

    A V026 esticou a **tela** de 3 para 6 itens e **nunca tocou no
    despacho**. Por isso, no aparelho:

        Video    -> Despertador     Livro digital -> nada
        Gravacao -> Imagem          Bluetooth     -> nada
        Radio    -> dicionario      Pastas        -> nada

    Bate item a item com o relato do mantenedor.

A SOLUCAO — reaproveitar os handlers ORIGINAIS da home

    A home de fabrica tinha nove itens, e os handlers deles continuam no
    codigo. A home de 4 itens (V022) reescreveu os slots 1, 2 e 3 do
    `tbh`, deixando **orfaos** os handlers de Video, Gravacao e Radio:

        ctrl_id 1 -> 0x00D01066  Video        (orfao)
        ctrl_id 2 -> 0x00D010F6  Gravacao     (orfao)
        ctrl_id 3 -> 0x00D0113C  Radio        (orfao)
        ctrl_id 4 -> 0x00D01162  Livro        INTACTO
        ctrl_id 6 -> 0x00D012D6  Bluetooth    INTACTO
        ctrl_id 8 -> 0x00D0128C  Pastas       INTACTO

    Confirmacao independente: o handler do `ctrl_id 3` carrega a string
    "O radio precisa ser conectado como uma antena". Nao ha duvida sobre
    qual e qual.

    **Metade do caminho ja esta de pe.** Faltam tres, e ha exatamente
    tres slots livres — slots cujo alvo e DUPLICADO, isto e, ja alcancavel
    por outro ctrl_id, entao reaproveita-los nao perde funcao nenhuma:

        slot  5 -> aponta para o mesmo que o 1   (Imagem)
        slot  7 -> aponta para o mesmo que o 3   (Configurar)
        slot 11 -> aponta para o mesmo que o 2   (pagina 0x53)

    O slot 9 (caminho de erro) fica INTACTO de proposito.

POR QUE REPASSAR PARA `page1_process` E NAO ABRIR A PAGINA DIRETO

    Os handlers originais fazem verificacao de cartao, de volume e de
    indice sujo, e mostram as mensagens de erro certas. Abrir a pagina
    destino direto jogaria isso fora: "Video" sem cartao abriria uma tela
    vazia em vez de dizer que nao ha videos.

    E a guarda de `page1_process` NAO exige pagina 1 — ela compara
    `msg->page` com a **pagina corrente**:

        0x00D00F4C  ldrh r2, [r4, #8]      ; pagina da mensagem
        0x00D00F4E  ldrb r0, [r3, #0xa]    ; pagina CORRENTE
        0x00D00F50  cmp  r2, r0

    Com o Extras na tela as duas valem 0x53, entao a mensagem passa
    intacta. Nenhum relaxamento de guarda e necessario.

    E como os handlers terminam em `0xd0dae0(origem = msg->page = 0x53)`,
    o "voltar" da tela aberta retorna ao **Extras**, nao a home.

O MAPA

    indice do Extras   item            ctrl_id da home
        0              Video                 5
        1              Gravacao              7
        2              Radio                11
        3              Livro digital         4
        4              Bluetooth             6
        5              Ver pastas            8

USO
    python3 tools/patch_extras.py \\
        --in  firmware/WORKING/GN438_openpod_v068.bin \\
        --out firmware/WORKING/GN438_openpod_v069.bin [--dry-run]

SEGURANCA
    - exige que os 3 slots a reaproveitar tenham alvo DUPLICADO na imagem
      (se algum deixar de ser duplicado, reaproveita-lo perderia funcao);
    - exige que os 3 handlers orfaos estejam nos enderecos esperados;
    - exige que a home so emita ctrl_id 0..3 (confere as constantes de
      volta do indice);
    - exige o ponto de gancho byte a byte;
    - desmonta a rotina montada e confere com operandos;
    - recusa diferenca abaixo de 0x00E000 (R1); nao toca no CRC.

LIMITACOES
    Muda DESPACHO de pagina — a classe que ja custou tres gravacoes
    (MENU_LISTA.md 14). Deve ser gravada e testada SOZINHA.
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

TBH = 0x00D00FBE
TBH_OFF = 0x00100FBE
PAGE1_PROCESS = 0x00D00F3C

ORFAOS = {5: (0x00D01066, "Video"), 7: (0x00D010F6, "Gravacao"),
          11: (0x00D0113C, "Radio")}
JA_OK = {4: "Livro digital", 6: "Bluetooth", 8: "Ver pastas"}
MAPA = [5, 7, 11, 4, 6, 8]
NOMES = ["Video", "Gravacao", "Radio", "Livro digital", "Bluetooth",
         "Ver pastas"]

GANCHO = 0x0010CC7E
GANCHO_ESPERADO = bytes.fromhex("022a" "75d8")     # cmp r2,#2 ; bhi
SAIDA = 0x00D0CD6E                                  # pop.w {...,pc}
PROLOGO = 0x0010CC0C
PROLOGO_ESPERADO = bytes.fromhex("2de9f041")        # push.w {r4-r8,lr}

VOLTA = {0x0012EA3E: 0, 0x0012EA42: 1, 0x0012EA44: 3, 0x0012EB70: 3}

BLOB = 0x001A5900
BLOB_MAX = 0x80


def bw(origem, destino, link=False):
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
    c = bytearray()

    def h(*hw):
        for x in hw:
            c.extend(struct.pack("<H", x))

    h(0x2A05)                    # cmp  r2, #5
    o_bhi = len(c)
    h(0x0000)                    # bhi  sai
    pos_lit = len(c)
    h(0x0000)                    # adr  r3, MAPA   (ENDERECO, nao conteudo)
    h(0x5C9B)                    # ldrb r3, [r3, r2]
    h(0x81A3)                    # strh r3, [r4, #0x0c]   ctrl_id da mensagem
    h(0x4620)                    # mov  r0, r4
    h(0xE8BD, 0x41F0)            # pop.w {r4,r5,r6,r7,r8,lr}
    c.extend(bw(base + len(c), PAGE1_PROCESS))
    sai = len(c)
    h(0xE8BD, 0x81F0)            # sai: pop.w {r4,r5,r6,r7,r8,pc}
    struct.pack_into("<H", c, o_bhi,
                     0xD800 | (((sai - (o_bhi + 4)) >> 1) & 0xFF))
    while len(c) % 4:
        h(0xBF00)
    lit = len(c)
    c.extend(bytes(MAPA) + b"\0\0")
    # ADR (T1): r3 = align4(pc) + imm8*4. Tem de ser ADR e nao LDR: o
    # LDR traria o CONTEUDO do mapa como se fosse ponteiro.
    pc = (base + pos_lit + 4) & ~3
    imm = (base + lit) - pc
    assert 0 <= imm <= 1020 and imm % 4 == 0, imm
    struct.pack_into("<H", c, pos_lit, 0xA300 | (imm >> 2))
    return bytes(c), base + lit


ESPERADO = ["cmp r2, #5", "bhi #", "adr r3, #", "ldrb r3, [r3, r2]",
            "strh r3, [r4, #0xc]",
            "mov r0, r4", "pop.w {r4, r5, r6, r7, r8, lr}", "b.w #0xd00f3c",
            "pop.w {r4, r5, r6, r7, r8, pc}"]


def main():
    ap = argparse.ArgumentParser(description="Extras: os itens abrem certo")
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

    def slot(k):
        return TBH + 2 * struct.unpack_from("<H", data, TBH_OFF + 2 * k)[0]

    erros = []
    alvos = [slot(k) for k in range(12)]
    for k, (end, nome) in ORFAOS.items():
        if alvos.count(alvos[k]) < 2:
            erros.append(f"slot {k} nao tem alvo duplicado "
                         f"(0x{alvos[k]:08X}) — reaproveita-lo perderia funcao")
    for k, nome in JA_OK.items():
        pass
    if bytes(data[GANCHO:GANCHO + 4]) != GANCHO_ESPERADO:
        erros.append(f"0x{GANCHO:06X} nao e `cmp r2,#2 ; bhi` "
                     f"({bytes(data[GANCHO:GANCHO+4]).hex()})")
    if bytes(data[PROLOGO:PROLOGO + 4]) != PROLOGO_ESPERADO:
        erros.append(f"prologo de pstr_page84_process inesperado")
    for off, v in VOLTA.items():
        if data[off] != v:
            erros.append(f"0x{off:06X} = {data[off]}, esperado {v} — a home "
                         "pode estar emitindo ctrl_id fora de 0..3")
    if any(x != 0xFF for x in data[BLOB:BLOB + BLOB_MAX]):
        erros.append(f"area livre 0x{BLOB:06X} nao esta virgem")

    rot, mapa_addr = monta(BLOB + XIP)
    got = [f"{i.mnemonic} {i.op_str}".strip() for i in md.disasm(rot, BLOB + XIP)]
    # NAO filtrar as linhas com [pc: foi exatamente numa delas que a
    # primeira versao errou (LDR onde devia ser ADR) e passou despercebido.
    got = got[:len(ESPERADO)]
    ok = len(got) == len(ESPERADO) and all(
        g.startswith(e) if e.endswith("#") else g == e
        for g, e in zip(got, ESPERADO))
    if not ok:
        erros.append(f"rotina nao confere:\n      esperado {ESPERADO}"
                     f"\n      obtido   {got}")
    if erros:
        print("RECUSADO:")
        for x in erros:
            print("   -", x)
        return 1

    print()
    print("  EXTRAS — os itens passam a abrir as telas certas")
    print()
    print("  diagnostico feito no FIRMWARE DE FABRICA:")
    print("    a pagina 0x53 tinha 3 itens (Despertador, Imagem, Dicionario)")
    print("    e o modulo dela so trata ctrl_id <= 2. A V026 esticou a tela")
    print("    para 6 e nao tocou no despacho.")
    print()
    print("  MAPA  indice -> ctrl_id da home -> handler")
    for i, cid in enumerate(MAPA):
        al = ORFAOS[cid][0] if cid in ORFAOS else slot(cid)
        origem = "orfao, religado" if cid in ORFAOS else "ja intacto"
        print(f"    {i}  {NOMES[i]:14s} -> ctrl_id {cid:2d} -> "
              f"0x{al:08X}   ({origem})")
    print()
    print("  ALTERACOES")
    for k, (end, nome) in sorted(ORFAOS.items()):
        ant = slot(k)
        struct.pack_into("<H", data, TBH_OFF + 2 * k, (end - TBH) // 2)
        print(f"    0x{TBH_OFF + 2 * k:06X}  tbh[{k:2d}]  "
              f"0x{ant:08X} -> 0x{end:08X}  ({nome})")
    data[BLOB:BLOB + len(rot)] = rot
    print(f"    0x{BLOB:06X}  rotina + mapa, {len(rot)} B")
    data[GANCHO:GANCHO + 4] = bw(GANCHO + XIP, BLOB + XIP)
    print(f"    0x{GANCHO:06X}  cmp/bhi -> b.w 0x{BLOB + XIP:08X}")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != data[i]]
    if dif and min(dif) < 0x00E000:
        sys.exit(f"RECUSADO: tocaria 0x{min(dif):06X} (R1)")
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: {len(secs)}  "
          + "  ".join(f"0x{s:06X}" for s in secs))
    print("  CRC da FIRM: campo intocado (R1)")
    print()
    print("  ⚠️  Muda DESPACHO de pagina. Gravar e testar SOZINHA.")
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
