#!/usr/bin/env python3
"""
patch_fundo_display.py — fundo do display vira PRETO (global).

O QUE FAZ
    O display LVGL nasce branco em lv_disp_drv_register:

        00D567F6  ff23      movs r3, #0xff
        00D567F8  84f82930  strb.w r3,[r4,#0x29]  ; bg_color R
        00D567FC  84f82a30  strb.w r3,[r4,#0x2a]  ; G
        00D56800  84f82b30  strb.w r3,[r4,#0x2b]  ; B

    Qualquer região não coberta por faixa/contêiner mostra esse branco
    (fresta entre faixa e lista, fundo de telas sem lista, etc).

    Trocar movs #0xFF -> #0x00 faz os três bytes virarem 0x00 = preto.
    É o teste de 1 byte documentado em docs/ARQUITETURA.md §12.4.

POR QUE 1 BYTE BASTA
    Os três strb escrevem o MESMO r3. Mudando o imediato, os três viram
    0x00 de uma vez.

USO
    python3 tools/patch_fundo_display.py --in <entrada.bin> --out <saida.bin>
    python3 tools/patch_fundo_display.py --autoteste

SEGURANCA
    - confere os 4 bytes seguintes (os três strb) antes de escrever
    - recusa se já está 0x00 (já aplicado)
    - recusa se byte não é 0xFF (imagem inesperada)
"""
import argparse, hashlib, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = "firmware/ORIGINAL/GN438_original.bin"
PROIBIDO = 0x0000D000
TAMANHO = 0x200000

OFF = 0x001567F6  # file offset do imediato
ESPERADO_FF = 0xFF
NOVO_00 = 0x00
CONTEXTO = [
    (0x001567F8, bytes.fromhex("84f82930"), "strb.w r3,[r4,#0x29]"),
    (0x001567FC, bytes.fromhex("84f82a30"), "strb.w r3,[r4,#0x2a]"),
    (0x00156800, bytes.fromhex("84f82b30"), "strb.w r3,[r4,#0x2b]"),
    (0x001567F2, bytes.fromhex("01f0a3fb"), "bl lv_disp_drv_register setup"),
]

def confere(d):
    for off, exp, desc in CONTEXTO:
        if bytes(d[off:off+len(exp)]) != exp:
            return False, f"0x{off:06X} ({desc}): achei {bytes(d[off:off+len(exp)]).hex()}, esperava {exp.hex()}"
    return True, "ok"

def aplica(d):
    if d[OFF] == NOVO_00 and d[OFF+1] == 0x23:
        return False, "patch já aplicado (0x2300 = movs r3,#0x00)"
    if d[OFF] != ESPERADO_FF:
        return False, f"0x{OFF:06X} tem {d[OFF]:02X}, esperado {ESPERADO_FF:02X}"
    # movs r3,#FF = 0x23FF (LE: FF 23), movs r3,#00 = 0x2300 (LE: 00 23)
    if d[OFF+1] != 0x23:
        return False, f"0x{OFF+1:06X} tem {d[OFF+1]:02X}, esperado 23 (opcode movs r3)"
    ok, msg = confere(d)
    if not ok:
        return False, msg
    d[OFF] = NOVO_00
    return True, "ok"

def autoteste():
    print("\n  AUTOTESTE — fundo do display preto (1 byte)\n")
    o = os.path.join(RAIZ, ORIGINAL)
    if not os.path.exists(o):
        print(f"  FALTA: {o}")
        return 1
    d = bytearray(open(o, "rb").read())
    ok, msg = aplica(d)
    if not ok:
        print(f"  FALHOU: {msg}")
        return 1
    print(f"    0x{OFF:06X}  FF -> 00  movs r3,#0x00  OK")
    for off, exp, desc in CONTEXTO:
        print(f"    0x{off:06X}  {desc}  OK")
    # segunda aplicação deve recusar
    ok2, _ = aplica(d)
    print(f"    recusa 2a aplicacao  {'OK' if not ok2 else 'FALHOU'}")
    if ok2:
        return 1
    print("\n  AUTOTESTE OK")
    return 0

def main():
    ap = argparse.ArgumentParser(description="fundo do display preto (global)")
    ap.add_argument("--in", dest="src")
    ap.add_argument("--out", dest="dst")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--autoteste", action="store_true")
    a = ap.parse_args()
    if a.autoteste:
        return autoteste()
    if not a.src or (not a.dst and not a.dry_run):
        ap.error("--in e --out obrigatórios (ou --autoteste)")
    d = bytearray(open(a.src, "rb").read())
    if len(d) != TAMANHO:
        print(f"ERRO: {a.src} tem {len(d)} B, esperado {TAMANHO}", file=sys.stderr)
        return 1
    orig = bytes(d)
    print("\n  FUNDO DO DISPLAY PRETO (global)\n")
    ok, msg = aplica(d)
    if not ok:
        print(f"  ABORTADO: {msg}", file=sys.stderr)
        return 1
    print("  ALTERACAO")
    print(f"    0x{OFF:06X}  1 B  FF -> 00  movs r3,#0xFF -> movs r3,#0x00")
    print(f"      disp->bg_color = 0x000000 (preto) em vez de 0xFFFFFF (branco)")
    print(f"      strb [r4,#0x29/2a/2b] escrevem 0x00 nas 3 componentes")
    print()
    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: " + "  ".join(f"0x{s:06X}" for s in secs))
    if any(s <= PROIBIDO for s in secs):
        print("  ABORTADO: setor proibido (R1).", file=sys.stderr)
        return 1
    print("  tabela de partições NÃO tocada   OK")
    print(f"  sha256: {hashlib.sha256(bytes(d)).hexdigest()}\n")
    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
