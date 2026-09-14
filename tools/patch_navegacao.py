#!/usr/bin/env python3
"""
patch_navegacao.py — M volta, VOL desce, nas telas de lista.

O QUE O MANTENEDOR RELATOU (2026-09-13, aparelho na mao)

    "M nao faz nada!! e o VOL VOLTA. Os botoes voltar e proxima navega no
     menu e o play/pause entra na opcao"

    Isso resolveu a ambiguidade que o BUTTON_ANALYSIS.md carregava desde
    o inicio: **0x81 e o VOL, 0xA0 e o M.**

O DEFEITO, MEDIDO

    | tecla        | home              | subtelas                     |
    |--------------|-------------------|------------------------------|
    | 0x81  VOL    | navega            | SAI DA TELA ("-%s back")     |
    | 0xA0  M      | navega            | nao tratada -> nao faz nada  |
    | 0x1B  ESC    | sai               | `pop` puro -> nao faz nada   |

    O VOL e a seta PARA BAIXO do aparelho, e sair da tela e o oposto de
    descer. O M, que tem o nome do Menu, esta morto.

O PONTO UNICO — por que isto nao custa 21 patches

    Toda tecla de toda tela passa por UM lugar so, o `lv_group_send_data`
    da LVGL. E o unico ponto do firmware que envia `LV_EVENT_KEY`:

        00D47652   push {r0, r1, r2, lr}    ; r0 = grupo, r1 = A TECLA
        00D47654   str  r1, [sp, #4]        ; o slot que sera enviado
        00D47656   bl   0xd47648            ; objeto focado
        00D4765C   add  r2, sp, #4          ; &tecla
        00D4765E   movs r1, #0xd            ; LV_EVENT_KEY
        00D47660   bl   0xd46ff0            ; lv_event_send(obj, KEY, &tecla)

    Trocando 6 bytes em 0x00D47654 por uma chamada a uma rotina na area
    livre, da para TRADUZIR a tecla antes de ela chegar em qualquer
    callback -- e decidir por pagina, como a tabela do titulo.

O QUE A ROTINA FAZ

        se a pagina corrente esta na tabela:
            0x81 (VOL) -> 0x12   LV_KEY_DOWN
            0xA0 (M)   -> 0x81   o codigo que a tela trata como "back"

    **Nenhum comportamento novo e criado.** As telas ja tratam `0x12`
    como "proximo" e `0x81` como "voltar"; isto so escolhe qual botao
    aciona qual. A home nao esta na tabela e nao muda em nada.

A TABELA NAO FOI ESCOLHIDA A DEDO

    Uma pagina so entra se as TRES condicoes forem verdadeiras, cada uma
    verificada simulando a cadeia de comparacoes do callback daquela
    tela:

        1. 0x12 chega num ramo que chama lv_group_focus_next (0xD474C4)
        2. 0x81 chega num ramo rotulado "-%s back"
        3. 0xA0 hoje cai no ramo de erro ("-%s no c: %d"), isto e, nao
           esta em uso -- entao dar um trabalho a ele nao tira nada

    21 paginas passam. As que ficam de fora nao tratam `0x12` como
    "proximo": remapear o VOL nelas o deixaria MORTO, que e pior que
    hoje. Notavelmente fora: 0x04 (Now Playing), 0x1A (FM), e os
    seletores de hora.

    A ferramenta REFAZ essa verificacao na imagem de entrada e recusa se
    alguma pagina da tabela nao passar.

USO
    python3 tools/patch_navegacao.py \\
        --in  firmware/WORKING/GN438_openpod_v055.bin \\
        --out firmware/WORKING/GN438_openpod_v056.bin [--dry-run]

DEPENDENCIAS
    Python 3 + capstone

SEGURANCA
    - re-verifica as 3 condicoes de cada pagina da tabela na imagem;
    - exige os 6 bytes do gancho exatamente como esperado;
    - exige que a area livre de destino esteja virgem (0xFF);
    - desmonta a rotina montada e confere instrucao por instrucao;
    - recusa qualquer diferenca abaixo de 0x00E000 (regra R1);
    - nao toca no campo de CRC da FIRM (regra R1).

LIMITACOES
    - NAO conserta o ESC (`0x1B`), que continua sendo `pop` puro nas
      subtelas. Fica registrado como pendencia separada.
    - O mapeamento bit-alto -> gesto (press/long) continua NAO
      DETERMINADO; isto trata `0x81` e `0xA0` como os codigos que o
      aparelho comprovadamente emite para VOL e M.
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

VIEW_P_PTR = 0x0081CE2C
FOCUS_NEXT = 0x00D474C4
OBJ_FOCADO = 0x00D47648        # o `bl` que o gancho substitui
ADD_EVENT_CB = 0x00D47064
TAB_PAGINAS = 0x00D23B38

TECLA_VOL = 0x81
TECLA_M = 0xA0
LV_KEY_DOWN = 0x12

HOOK = 0x00147654
HOOK_ESPERADO = bytes.fromhex("0191" "fff7f7ff")   # str r1,[sp,#4] ; bl 0xd47648

BLOB_OFF = 0x001A50C0          # mesmo setor da rotina do titulo, apos ela
BLOB_MAX = 0x340               # ate o fim do setor 0x1A5000

# As 21 paginas aprovadas. Reconferidas na imagem a cada execucao.
PAGINAS = [0x02, 0x09, 0x0B, 0x0E, 0x10, 0x17, 0x18, 0x1E, 0x20, 0x23,
           0x28, 0x29, 0x2A, 0x2E, 0x30, 0x3C, 0x4B, 0x4C, 0x4D, 0x50, 0x53]


# ===================== analise: repete a verificacao =====================
class Analise:
    def __init__(self, d):
        self.d = d
        self.md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    def ins(self, a):
        return next(self.md.disasm(self.d[a - XIP:a - XIP + 4], a), None)

    def cstr(self, a):
        o = a - XIP
        if not (0 <= o < len(self.d)):
            return None
        e = self.d.find(b"\0", o)
        try:
            return self.d[o:e].decode("ascii")
        except UnicodeDecodeError:
            return None

    def callbacks(self):
        """pagina -> endereco do callback de LV_EVENT_KEY."""
        pages = {}
        for i in range(0x53):
            t = TAB_PAGINAS + 2 * self.d[TAB_PAGINAS - XIP + i]
            k = self.ins(t)
            if k and k.mnemonic == "bl":
                pages.setdefault(int(k.op_str.strip("#"), 0), i + 1)
        fns = sorted(pages)
        out = {}
        for a in range(0xD20000, 0xD40000, 2):
            k = self.ins(a)
            if not k or k.mnemonic != "bl":
                continue
            try:
                t = int(k.op_str.strip("#"), 0)
            except ValueError:
                continue
            if t != ADD_EVENT_CB:
                continue
            owner = max([f for f in fns if f <= a], default=None)
            pg = pages.get(owner)
            if pg is None:
                continue
            cb = ev = None
            for b in range(a - 20, a, 2):
                j = self.ins(b)
                if not j:
                    continue
                if j.mnemonic == "ldr" and "[pc" in j.op_str:
                    imm = int(j.op_str.split("#")[-1].rstrip("]"), 0)
                    cb = struct.unpack_from("<I", self.d,
                                            (((b + 4) & ~3) + imm) - XIP)[0]
                if j.mnemonic == "movs" and j.op_str.startswith("r2, #"):
                    ev = int(j.op_str.split("#")[1], 0)
            if ev == 13 and cb:
                out.setdefault(pg, cb & ~1)
        return out

    def despacha(self, cb, key, limite=400):
        """Simula a cadeia de `cmp r2,#imm` do callback com r2 = key."""
        pc = None
        for a in range(cb, cb + 0x80, 2):
            k = self.ins(a)
            if k and k.mnemonic == "ldrb" and k.op_str.startswith("r2, [r0"):
                pc = a + 2
                break
        if pc is None:
            return None
        flags = None
        for _ in range(limite):
            k = self.ins(pc)
            if k is None:
                return None
            m, ops = k.mnemonic, k.op_str
            if m == "cmp" and ops.startswith("r2, #"):
                v = int(ops.split("#")[1], 0)
                flags = (key == v, key > v, key < v)
                pc += k.size
                continue
            if m in ("sub.w", "subs") and ops.startswith("r3, r2, #"):
                pc += k.size
                continue
            if m.startswith("b") and ops.startswith("#"):
                tgt = int(ops.strip("#"), 0)
                bm = m.split(".")[0]
                if bm == "b":
                    pc = tgt
                    continue
                if flags is None:
                    return pc
                eq, hi, lo = flags
                take = {"beq": eq, "bne": not eq, "bhi": hi, "bls": not hi,
                        "bhs": eq or hi, "blo": lo, "bcs": eq or hi,
                        "bcc": lo}.get(bm)
                if take is None:
                    return pc
                pc = tgt if take else pc + k.size
                continue
            return pc
        return None

    def chama(self, t, fn, span=0x60):
        """O ramo costuma terminar em `pop.w {..,lr}` + `b.w alvo` (tail
        call); por isso seguimos UMA instrucao alem do primeiro pop, e
        percorremos por TAMANHO de instrucao -- andar de 2 em 2 cai no meio
        de um pop.w de 4 bytes e perde o alvo."""
        if t is None:
            return False
        c, n, pos_pop = t, 0, False
        while c < t + span and n < 40:
            k = self.ins(c)
            if k is None:
                return False
            if k.mnemonic in ("bl", "b.w") and k.op_str.startswith("#"):
                if int(k.op_str.strip("#"), 0) == fn:
                    return True
            if pos_pop:
                return False
            if k.mnemonic.startswith("pop"):
                pos_pop = True
            c += k.size
            n += 1
        return False

    def rotulo(self, t, span=0x40):
        if t is None:
            return None
        for c in range(t, t + span, 2):
            k = self.ins(c)
            if k and k.mnemonic == "ldr" and "r0, [pc" in k.op_str:
                imm = int(k.op_str.split("#")[-1].rstrip("]"), 0)
                v = struct.unpack_from("<I", self.d,
                                       (((c + 4) & ~3) + imm) - XIP)[0]
                s = self.cstr(v)
                if s and s.startswith("-%s "):
                    return s.strip()[4:]
        return None

    def qualifica(self, cb):
        n12 = self.chama(self.despacha(cb, LV_KEY_DOWN), FOCUS_NEXT)
        b81 = self.rotulo(self.despacha(cb, TECLA_VOL)) == "back"
        a0 = self.rotulo(self.despacha(cb, TECLA_M)) == "no c: %d"
        return n12, b81, a0


# ============================== montagem =================================
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


def monta(base_addr, tabela_addr):
    """
    r0 = grupo, r1 = tecla. `bl` NAO mexe em sp, e a rotina nao chama
    ninguem, entao `lr` sobrevive sozinho -- por isso nao empilhamos lr.
    Empilhamos r0/r2/r3 porque r0 (o grupo) e usado como rascunho na busca
    e precisa voltar intacto para o tail call.
    """
    for _ in range(2):
        c, pos = [], 0

        def emit(b):
            nonlocal pos
            c.append(b)
            pos += len(b)
            return pos - len(b)

        emit(struct.pack("<H", 0xB40D))                 # push {r0, r2, r3}
        emit(struct.pack("<H", 0x2900 | TECLA_VOL))     # cmp r1, #0x81
        o_beq_ck = emit(b"\0\0")                        # beq checa
        emit(struct.pack("<H", 0x2900 | TECLA_M))       # cmp r1, #0xA0
        o_bne_fim = emit(b"\0\0")                       # bne fim
        rot_ck = pos
        o_ldr_vp = emit(b"\0\0")                        # ldr r2, =&view_p
        emit(struct.pack("<H", 0x6812))                 # ldr r2, [r2]
        emit(struct.pack("<H", 0x2A00))                 # cmp r2, #0
        o_beq_fim1 = emit(b"\0\0")
        emit(struct.pack("<H", 0x7812))                 # ldrb r2, [r2]
        o_ldr_tab = emit(b"\0\0")                       # ldr r3, =tabela
        rot_busca = pos
        emit(struct.pack("<H", 0x7818))                 # ldrb r0, [r3]
        emit(struct.pack("<H", 0x2800))                 # cmp r0, #0
        o_beq_fim2 = emit(b"\0\0")
        emit(struct.pack("<H", 0x4290))                 # cmp r0, r2
        o_beq_achou = emit(b"\0\0")
        emit(struct.pack("<H", 0x3301))                 # adds r3, #1
        o_b_busca = emit(b"\0\0")
        rot_achou = pos
        emit(struct.pack("<H", 0x2900 | TECLA_VOL))     # cmp r1, #0x81
        o_bne_m = emit(b"\0\0")
        emit(struct.pack("<H", 0x2100 | LV_KEY_DOWN))   # movs r1, #0x12
        o_b_fim = emit(b"\0\0")
        rot_m = pos
        emit(struct.pack("<H", 0x2100 | TECLA_VOL))     # movs r1, #0x81
        rot_fim = pos
        emit(struct.pack("<H", 0xBC0D))                 # pop {r0, r2, r3}
        emit(struct.pack("<H", 0x9101))                 # str r1, [sp, #4]
        o_b_obj = emit(b"\0\0\0\0")                     # b.w obj_focado
        n_code = pos
        while pos % 4:
            emit(struct.pack("<H", 0xBF00))
        lit = pos
        emit(struct.pack("<I", VIEW_P_PTR))
        emit(struct.pack("<I", tabela_addr))

        blob = bytearray(b"".join(c))

        def put(o, b):
            blob[o:o + len(b)] = b

        def r8(o, alvo):
            dd = (alvo - (o + 4)) >> 1
            assert -128 <= dd <= 127, (o, alvo)
            return dd & 0xFF

        def ldrpc(o, rt, alvo):
            pc_ = (o + 4) & ~3
            imm = alvo - pc_
            assert 0 <= imm <= 1020 and imm % 4 == 0
            return struct.pack("<H", 0x4800 | (rt << 8) | (imm >> 2))

        put(o_beq_ck, struct.pack("<H", 0xD000 | r8(o_beq_ck, rot_ck)))
        put(o_bne_fim, struct.pack("<H", 0xD100 | r8(o_bne_fim, rot_fim)))
        put(o_ldr_vp, ldrpc(o_ldr_vp, 2, lit))
        put(o_beq_fim1, struct.pack("<H", 0xD000 | r8(o_beq_fim1, rot_fim)))
        put(o_ldr_tab, ldrpc(o_ldr_tab, 3, lit + 4))
        put(o_beq_fim2, struct.pack("<H", 0xD000 | r8(o_beq_fim2, rot_fim)))
        put(o_beq_achou, struct.pack("<H", 0xD000 | r8(o_beq_achou, rot_achou)))
        put(o_b_busca, struct.pack(
            "<H", 0xE000 | (((rot_busca - (o_b_busca + 4)) >> 1) & 0x7FF)))
        put(o_bne_m, struct.pack("<H", 0xD100 | r8(o_bne_m, rot_m)))
        put(o_b_fim, struct.pack(
            "<H", 0xE000 | (((rot_fim - (o_b_fim + 4)) >> 1) & 0x7FF)))
        put(o_b_obj, bl(base_addr + o_b_obj, OBJ_FOCADO, link=False))

        tabela_addr = base_addr + len(blob)
    return bytes(blob), tabela_addr, n_code


ESPERADO = ["push", "cmp", "beq", "cmp", "bne", "ldr", "ldr", "cmp", "beq",
            "ldrb", "ldr", "ldrb", "cmp", "beq", "cmp", "beq", "adds", "b",
            "cmp", "bne", "movs", "b", "movs", "pop", "str", "b.w"]


# ================================ main ===================================
def main():
    ap = argparse.ArgumentParser(description="M volta, VOL desce")
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

    erros = []
    if bytes(data[HOOK:HOOK + 6]) != HOOK_ESPERADO:
        erros.append(f"0x{HOOK:06X}: gancho inesperado "
                     f"{bytes(data[HOOK:HOOK+6]).hex()} "
                     f"(esperado {HOOK_ESPERADO.hex()})")
    if any(b != 0xFF for b in data[BLOB_OFF:BLOB_OFF + BLOB_MAX]):
        erros.append(f"area livre 0x{BLOB_OFF:06X} nao esta virgem")

    an = Analise(data)
    cbs = an.callbacks()
    print()
    print("  OPENPOD — NAVEGACAO: M volta, VOL desce")
    print()
    print("  reconferindo cada pagina na imagem de entrada:")
    print(f"  {'pg':>5}  {'0x12->next':>10} {'0x81->back':>10} {'0xA0 livre':>10}")
    for pg in PAGINAS:
        cb = cbs.get(pg)
        if cb is None:
            erros.append(f"pagina 0x{pg:02X} nao tem callback de LV_EVENT_KEY")
            continue
        n12, b81, a0 = an.qualifica(cb)
        marca = "OK" if (n12 and b81 and a0) else "FALHA"
        print(f"  0x{pg:02X}   {str(n12):>10} {str(b81):>10} {str(a0):>10}   {marca}")
        if not (n12 and b81 and a0):
            erros.append(f"pagina 0x{pg:02X} nao qualifica mais "
                         f"(next={n12} back={b81} livre={a0})")

    base_addr = BLOB_OFF + XIP
    rotina, tabela_addr, n_code = monta(base_addr, 0)
    tabela = bytes(PAGINAS) + b"\0"
    blob = rotina + tabela

    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    got = [i.mnemonic for i in md.disasm(blob[:n_code], base_addr)]
    if got != ESPERADO:
        erros.append(f"rotina montada nao confere:\n      esperado {ESPERADO}"
                     f"\n      obtido   {got}")
    if len(blob) > BLOB_MAX:
        erros.append(f"rotina+tabela {len(blob)} B, cabe {BLOB_MAX}")

    if erros:
        print()
        print("RECUSADO:")
        for x in erros:
            print("   -", x)
        return 1

    print()
    print(f"  {len(PAGINAS)} paginas qualificam. Nenhum comportamento novo:")
    print(f"    0x81 VOL -> 0x{LV_KEY_DOWN:02X}  LV_KEY_DOWN  (a tela ja trata "
          "como 'proximo')")
    print(f"    0xA0 M   -> 0x{TECLA_VOL:02X}  (a tela ja trata como 'back')")
    print()
    print("  ALTERACOES")
    data[BLOB_OFF:BLOB_OFF + len(blob)] = blob
    print(f"    0x{BLOB_OFF:06X}  rotina {len(rotina)} B + tabela "
          f"{len(tabela)} B — area livre, XIP 0x{base_addr:08X}")
    data[HOOK:HOOK + 6] = bl(HOOK + XIP, base_addr) + b"\x00\xbf"
    print(f"    0x{HOOK:06X}  str r1,[sp,#4] ; bl 0x{OBJ_FOCADO:08X}")
    print(f"              ->  bl 0x{base_addr:08X} ; nop")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != data[i]]
    if dif and min(dif) < 0x00E000:
        sys.exit(f"RECUSADO: tocaria 0x{min(dif):06X}, abaixo de 0x00E000 (R1)")
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   tamanho: inalterado ({len(data)})")
    print(f"  setores de 4 KiB: {len(secs)}  "
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
