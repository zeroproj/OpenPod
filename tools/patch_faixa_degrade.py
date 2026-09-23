#!/usr/bin/env python3
"""
patch_faixa_degrade.py — degradê vertical na faixa superior (bar principal)

O QUE FAZ
    A CRIA_FAIXA (0x00D216F0) pinta a faixa com cor chapada preta:
        00D2171A  bl 0xD2138A  -> devolve 0x0000 (preto, via getter)
        00D2171E  movs r2,#0
        00D21720  mov r1,r0
        00D21722  mov r0,r4
        00D21724  bl set_style_bg_color (prop 0x20)
    Para degradê, precisa de duas cores + direção:
        BG_COLOR      prop 0x20 = 32  (cor topo)
        BG_GRAD_COLOR prop 0x22 = 34  (cor base)
        BG_GRAD_DIR   prop 0x23 = 35  (1 = vertical)

    Este patch desvia o `bl getter` em 0x0012171A para uma rotina na área
    livre (0x001A6000) que faz os três `dispatch` e volta em 0x00121728,
    pulando o `bl bg_color` original. Próx. chamada (texto) segue intacta.

CORES (pre-invertidas, LV_COLOR_16_SWAP)
    Topo  RGB(70,75,90)  -> 0x4B42
    Base  RGB(30,34,40)  -> 0x0519
    São sutis sobre fundo preto, mantêm contraste 4.5:1 com branco.

USO
    python3 tools/patch_faixa_degrade.py --in <in> --out <out> [--em 0x1A6000]
    python3 tools/patch_faixa_degrade.py --autoteste

ORIGEM: adaptação do Marte (faixa 128x18) para tema escuro da Reload.
"""
import argparse, hashlib, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asm import monta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = "firmware/ORIGINAL/GN438_original.bin"
PROIBIDO = 0x0000D000
TAMANHO = 0x200000
XIP = 0x00C00000
HOOK = 0x0012171A
HOOK_ORIG = bytes.fromhex("fff736fe")  # bl 0xD2138A
RET = 0x00121728  # após bl bg_color
DISPATCH = 0x00D4CAC4
TOP = 0x4B42
BASE = 0x0519

def enc_branch(src, dst):
    # b.w src->dst (Thumb-2)
    off = dst - (src + 4)
    s = (off >> 24) & 1
    i1 = (off >> 23) & 1
    i2 = (off >> 22) & 1
    j1 = (~(i1 ^ s)) & 1
    j2 = (~(i2 ^ s)) & 1
    imm10 = (off >> 12) & 0x3FF
    imm11 = (off >> 1) & 0x7FF
    return struct.pack("<HH", 0xF000 | (s << 10) | imm10, 0x9000 | (j1 << 13) | (j2 << 11) | imm11)

def gen_routine(em):
    # rotina em Thumb-2 que faz 3 dispatch e volta
    # r4 = faixa obj (preservado do caller, ainda em r4)
    # precisa salvar r4,lr
    asm = f"""
    .syntax unified
    .thumb
    push {{r4, lr}}
    mov r4, r4           @ r4 já é faixa, só para documentar
    @ BG_COLOR = top
    mov r0, r4
    movs r1, #0x20
    movw r2, #0x{TOP:04X}
    movs r3, #0
    bl 0x{DISPATCH:08X}
    @ BG_GRAD_COLOR = base
    mov r0, r4
    movs r1, #0x22
    movw r2, #0x{BASE:04X}
    movs r3, #0
    bl 0x{DISPATCH:08X}
    @ BG_GRAD_DIR = vertical (1)
    mov r0, r4
    movs r1, #0x23
    movs r2, #1
    movs r3, #0
    bl 0x{DISPATCH:08X}
    pop {{r4, pc}}
    """
    # monta via asm.py (usa keystone/gcc)
    blob = monta(asm)
    # append branch de retorno já está no pop pc; mas precisamos garantir que
    # o último bl volta corretamente - o pop pc já retorna ao caller?
    # Na verdade, o hook é b.w (não bl), então lr não foi setado. O pop {{r4,pc}}
    # retorna para 0x00121728? Não, pc do pop vem da pilha (lr original do
    # CRIA_FAIXA, não do hook). Precisamos fazer b.w explicito para RET.
    # Então trocamos pop {{r4,pc}} por pop {{r4,lr}} + b.w RET
    # Para simplificar, geramos sem pop pc e adicionamos branch.
    asm2 = f"""
    .syntax unified
    .thumb
    push {{r4, lr}}
    mov r0, r4
    movs r1, #0x20
    movw r2, #0x{TOP:04X}
    movs r3, #0
    bl 0x{DISPATCH:08X}
    mov r0, r4
    movs r1, #0x22
    movw r2, #0x{BASE:04X}
    movs r3, #0
    bl 0x{DISPATCH:08X}
    mov r0, r4
    movs r1, #0x23
    movs r2, #1
    movs r3, #0
    bl 0x{DISPATCH:08X}
    pop {{r4, lr}}
    b 0x{RET + XIP:08X}
    """
    blob2 = monta(asm2)
    return blob2

def aplica(d, em):
    if bytes(d[HOOK:HOOK+4]) == enc_branch(HOOK+XIP, em+XIP):
        return False, "patch já aplicado (hook já é b.w)"
    if bytes(d[HOOK:HOOK+4]) != HOOK_ORIG:
        return False, f"0x{HOOK:06X} tem {bytes(d[HOOK:HOOK+4]).hex()}, esperado {HOOK_ORIG.hex()}"
    # confere que o RET ainda é bl getter texto
    if bytes(d[RET:RET+4]) != bytes.fromhex("fff72cfe"):
        return False, f"0x{RET:06X} não é bl getter texto esperado"
    routine = gen_routine(em)
    if any(b != 0xFF for b in d[em:em+len(routine)]):
        return False, f"área livre 0x{em:06X} não está virgem ({len(routine)}B)"
    d[em:em+len(routine)] = routine
    d[HOOK:HOOK+4] = enc_branch(HOOK+XIP, em+XIP)
    return True, f"rotina {len(routine)}B em 0x{em:06X} hook 0x{HOOK:06X} -> 0x{em+XIP:08X} ret -> 0x{RET+XIP:08X}"

def autoteste():
    print("\n  AUTOTESTE — degradê na faixa\n")
    o = os.path.join(RAIZ, ORIGINAL)
    if not os.path.exists(o):
        print(f"  FALTA: {o}"); return 1
    d = bytearray(open(o, "rb").read())
    em = 0x001A6000
    ok, msg = aplica(d, em)
    if not ok:
        print(f"  FALHOU: {msg}"); return 1
    print(f"    hook: {msg}  OK")
    # segunda deve recusar
    ok2,_ = aplica(d, em)
    print(f"    recusa 2a: {'OK' if not ok2 else 'FALHOU'}")
    if ok2: return 1
    print("\n  AUTOTESTE OK"); return 0

def main():
    ap = argparse.ArgumentParser(description="degradê na faixa superior")
    ap.add_argument("--in", dest="src")
    ap.add_argument("--out", dest="dst")
    ap.add_argument("--em", type=lambda s: int(s,0), default=0x001A6000)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--autoteste", action="store_true")
    a = ap.parse_args()
    if a.autoteste: return autoteste()
    if not a.src or (not a.dst and not a.dry_run):
        ap.error("--in e --out obrigatórios")
    d = bytearray(open(a.src,"rb").read())
    if len(d)!=TAMANHO: sys.exit(f"ERRO: {a.src} tem {len(d)}")
    orig = bytes(d)
    print("\n  FAIXA COM DEGRADÊ\n")
    ok, msg = aplica(d, a.em)
    if not ok:
        print(f"  ABORTADO: {msg}", file=sys.stderr); return 1
    print(f"  {msg}")
    print(f"    topo  RGB(70,75,90) 0x{TOP:04X}  base RGB(30,34,40) 0x{BASE:04X}  dir vertical")
    dif=[i for i in range(len(orig)) if orig[i]!=d[i]]
    secs=sorted({i//0x1000*0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)} setores: {' '.join(f'0x{s:06X}' for s in secs)}")
    if any(s<=PROIBIDO for s in secs):
        print("  ABORTADO: setor proibido", file=sys.stderr); return 1
    print(f"  sha256: {hashlib.sha256(bytes(d)).hexdigest()}\n")
    if a.dry_run:
        print("  --dry-run: nada gravado."); return 0
    open(a.dst,"wb").write(bytes(d))
    print(f"  gravado: {a.dst}"); return 0

if __name__=="__main__": sys.exit(main())
