#!/usr/bin/env python3
"""
fab_reload_3_3.py — a Parte 0 da ficha 025 na Reload 3.3.

PROPOSITO

    A Reload 3.2 chama o heap do FreeRTOS na CPU1: o CRIA e o APAGA da
    capa do album (a pagina Tocando Agora) chamam `CALLOC` 0xCF7840 e
    `FREE` 0xCF7884. A CPU1 e a interface (LVGL); mexer no heap da CPU0
    dali corrompe o heap/lista de tarefas e o aparelho congela ou
    reinicia (README do SL6801_player, "Two cores").

    Esta ferramenta aplica, sobre a 3.2 exata (sem carimbo, sha
    aa7e7a5a...), tres trocas dentro do lote da capa:

      1. `corpo_cria`, 0xDAA03E: o `calloc(1, 0x2210)` vira um `bl` para
         um trampolim que usa `lv_mem_alloc` (0xD58188), que devolve 0
         na falta de memoria (provado: `cbnz r0` em 0xD5819C);
      2. `corpo_apaga`, 0xDAA0D0/DAA0D4: o `movw/movt ip` de
         `0xCF7885` vira `0xD5811D` (`lv_mem_free`);
      3. `corpo_cria`, caminho de erro, 0xDAA246/DAA24A: a mesma troca
         de `0xCF7885` para `0xD5811D`.

    O trampolim e montado com o clang (tools/asm.py) e zera o buffer
    com o `memset` 0xBAA da fabrica: o `lv_mem_alloc` nao zera, e o
    `calloc` antigo zerava. Se o LVGL nao tiver os 0x2210 B, o `cmp
    r7,#0` que ja existia em `corpo_cria` leva ao quadrado cinza, sem
    escrever em ponteiro ruim.

PREMISSAS

    - a imagem tem 2 MiB e o sha256 e o da 3.2 sem carimbo (aa7e7a5a...);
    - os bytes dos tres pontos sao os da 3.2 (as instrucoes de fabrica);
    - o gap 0x1AA9D8..0x1AAA00 e todo 0xFF (40 bytes) e o trampolim cabe;
    - `lv_mem_alloc`/`lv_mem_free` estao no lugar (0xD58188/0xD5811C);
    - nada abaixo de 0xE000, nem o setor 0xD000, nem a PSMP (0x1FC000+).
CONFERENCIA DE SAIDA

    Depois de escrever, a ferramenta rele o `bl`, o trampolim e os dois
    `movw/movt`, e recusa se a diferenca sair dos quatro intervalos.

USO

    python3 tools/fab_reload_3_3.py --in <3.2.bin> --out <3.3.bin>
                                     [--dry-run]

DEPENDENCIAS

    Python 3 (stdlib) + clang (tools/asm.py) + capstone.

LIMITACOES

    - so serve na 3.2 exata; qualquer outra imagem e recusada;
    - o patch e da imagem 3.2, nao do `capa_album.s` (montado por todas
      as receitas desde a RC7: mudar o .s quebraria a catraca);
    - rodar de novo sobre a saida e recusado (o sha ja nao e o da 3.2).
"""

import argparse
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capa_album_asm as A  # noqa: E402
from asm import monta  # noqa: E402

TAMANHO = 0x200000
SHA_32 = "aa7e7a5aa453f9f0969c3a083e5c85c4b3e79e567b8c3f1c0c10f76adf3a5ef1"

# --- o lote da capa (o MAPA do build.py ja declara o lote da RC7)
LOTE, LOTE_TAM = 0x1A8000, 0x3000

# --- os pontos da 3.2 (deslocamentos no arquivo)
ALLOC = 0x1AA03E                      # calloc(1, 0x2210) em corpo_cria
FREE1 = 0x1AA0D0                      # movw/movt ip,#0xCF7885 (erro do CRIA)
FREE2 = 0x1AA246                      # movw/movt ip,#0xCF7885 (APAGA)
TRAMP = 0x1AA9D8                      # gap de 40 bytes 0xFF antes do B6b
FIM_GAP = 0x1AAA00                    # comeco do blob B6b (nao e nosso)

# --- os enderecos XIP
X_ALLOC = 0x00DAA03E
X_BL = 0x00DAA04A
X_TRAMP = 0x00DAA9D8
LV_ALLOC = 0x00D58188
LV_FREE = 0x00D5811D                  # 0xD5811C com o bit Thumb
MEMSET = 0x00000BAB                   # 0xBAA com o bit Thumb
TAM = 0x2210

# --- os bytes de fabrica (16 B do alloc; 8 B de cada movw/movt)
ORIG_ALLOC = bytes.fromhex("012042f2102147f6410cc0f2cf0ce047")
ORIG_FREE = bytes.fromhex("47f6850cc0f2cf0c")
# --- os primeiros bytes de lv_mem_alloc/lv_mem_free no ORIGINAL
LV_ALLOC_8 = bytes.fromhex("30b505468fb048b3")
LV_FREE_8 = bytes.fromhex("044b9842014604d0")
OFF_LV_ALLOC = LV_ALLOC - A.XIP
OFF_LV_FREE = (LV_FREE - 1) - A.XIP

NOP = b"\x00\xbf"


def mesma_entrada(src, dst):
    """--out aponta para a propria entrada? (mesmo caminho, symlink, hardlink)"""
    if os.path.abspath(src) == os.path.abspath(dst):
        return True
    if not os.path.lexists(dst):
        return False
    try:
        return os.path.samefile(src, dst)
    except OSError:
        return False


def _movw_movt_r4(alvo):
    """Monta `movw ip,#lo; movt ip,#hi` para o endereco Thumb `alvo`."""
    lo, hi = alvo & 0xFFFF, (alvo >> 16) & 0xFFFF
    return monta(f"""
.syntax unified
.thumb
.text
.align 2
movw ip, #{lo:#06x}
movt ip, #{hi:#06x}
""")


def fonte_trampolim():
    return f"""
.syntax unified
.thumb
.text
.align 2
trampolim:
    push {{r4, lr}}
    movw r0, #{TAM:#06x}
    movw ip, #{(LV_ALLOC | 1) & 0xFFFF:#06x}
    movt ip, #{((LV_ALLOC | 1) >> 16) & 0xFFFF:#06x}
    blx ip
    cbz r0, 1f
    mov r4, r0
    movs r1, #0
    movw r2, #{TAM:#06x}
    movw ip, #{MEMSET & 0xFFFF:#06x}
    movt ip, #{0:#06x}
    blx ip
    mov r0, r4
1:  pop {{r4, pc}}
"""


def monta_trampolim():
    cod = monta(fonte_trampolim())
    if len(cod) > FIM_GAP - TRAMP:
        raise RuntimeError(
            f"o trampolim tem {len(cod)} B e o gap so tem "
            f"{FIM_GAP - TRAMP} B")
    return cod


def enc_free():
    """Os 8 B de `movw/movt ip,#0xD5811D`."""
    return _movw_movt_r4(LV_FREE)


def confere_trampolim(cod):
    """Le de volta o trampolim (capstone) e confere os alvos e a saida."""
    try:
        from capstone import Cs, CS_ARCH_ARM, CS_MODE_LITTLE_ENDIAN, CS_MODE_THUMB
    except ImportError as e:
        raise RuntimeError("capstone ausente: pip3 install capstone") from e
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    ins = list(md.disasm(cod, X_TRAMP))
    erros = []
    if not ins:
        return ["o trampolim nao desmontou"]
    if ins[0].mnemonic != "push" or "r4" not in ins[0].op_str or \
            "lr" not in ins[0].op_str:
        erros.append("o trampolim nao comeca com push {r4, lr}")
    if ins[-1].mnemonic != "pop" or "pc" not in ins[-1].op_str:
        erros.append("o trampolim nao termina com pop {..., pc}")
    blx = [i for i in ins if i.mnemonic == "blx"]
    if len(blx) != 2:
        erros.append(f"o trampolim tem {len(blx)} blx, esperado 2")
    else:
        # os `movw/movt` anteriores a cada blx montam o ip
        if not any(i.mnemonic == "movw" and i.op_str.startswith("ip,")
                   and "0x8189" in i.op_str for i in ins):
            erros.append("falta movw ip,#0x8189 (lv_mem_alloc)")
        if not any(i.mnemonic == "movw" and i.op_str.startswith("ip,")
                   and "0xbab" in i.op_str for i in ins):
            erros.append("falta movw ip,#0x0bab (memset)")
        if not any(i.mnemonic == "movt" and i.op_str == "ip, #0xd5"
                   for i in ins):
            erros.append("falta movt ip,#0xd5 (lv_mem_alloc)")
    if len(cod) != FIM_GAP - TRAMP:
        erros.append(f"o trampolim tem {len(cod)} B, esperado "
                     f"{FIM_GAP - TRAMP} B")
    return erros


def confere_premissas(d, cod, free):
    erros = []
    if len(d) != TAMANHO:
        return [f"a imagem tem {len(d)} bytes, esperado {TAMANHO} (2 MiB)"]
    sha = hashlib.sha256(bytes(d)).hexdigest()
    if sha != SHA_32:
        erros.append(f"sha256 da entrada {sha[:16]}..., esperado "
                     f"{SHA_32[:16]}... (a 3.2 exata, sem carimbo)")
    if bytes(d[ALLOC:ALLOC + len(ORIG_ALLOC)]) != ORIG_ALLOC:
        erros.append(f"o alloc em 0x{ALLOC:06X} e "
                     f"{bytes(d[ALLOC:ALLOC + 16]).hex()}, esperado "
                     f"{ORIG_ALLOC.hex()}")
    for nome, p in (("FREE do erro do CRIA", FREE1),
                    ("FREE do APAGA", FREE2)):
        if bytes(d[p:p + len(ORIG_FREE)]) != ORIG_FREE:
            erros.append(f"o {nome} em 0x{p:06X} e "
                         f"{bytes(d[p:p + 8]).hex()}, esperado "
                         f"{ORIG_FREE.hex()}")
    gap = bytes(d[TRAMP:FIM_GAP])
    if gap != b"\xff" * (FIM_GAP - TRAMP):
        erros.append(f"o gap 0x{TRAMP:06X}..0x{FIM_GAP:06X} nao e todo 0xFF")
    if bytes(d[OFF_LV_ALLOC:OFF_LV_ALLOC + 8]) != LV_ALLOC_8:
        erros.append("lv_mem_alloc 0xD58188 nao tem os bytes do ORIGINAL")
    if bytes(d[OFF_LV_FREE:OFF_LV_FREE + 8]) != LV_FREE_8:
        erros.append("lv_mem_free 0xD5811C nao tem os bytes do ORIGINAL")
    if not os.path.exists("firmware/ORIGINAL/GN438_original.bin"):
        erros.append("firmware/ORIGINAL/GN438_original.bin nao existe")
    if len(cod) != FIM_GAP - TRAMP:
        erros.append(f"o trampolim montou {len(cod)} B, esperado "
                     f"{FIM_GAP - TRAMP} B")
    if len(free) != 8:
        erros.append(f"o movw/movt montou {len(free)} B, esperado 8 B")
    erros += confere_trampolim(cod)
    return erros


def escreve(d, cod, free):
    d[ALLOC:ALLOC + len(ORIG_ALLOC)] = NOP * 6 + A.enc(X_BL, X_TRAMP, True)
    d[TRAMP:TRAMP + len(cod)] = cod
    d[FREE1:FREE1 + len(free)] = free
    d[FREE2:FREE2 + len(free)] = free


def confere_resultado(d, cod, free):
    erros = []
    lido = A.desvio(d, ALLOC + 12)
    if lido is None or lido[0] != "bl" or lido[1] != X_TRAMP:
        erros.append(f"o bl em 0x{X_BL:08X} nao aponta para 0x{X_TRAMP:08X}")
    if bytes(d[ALLOC:ALLOC + 12]) != NOP * 6:
        erros.append("os 12 B antes do bl nao sao 6 nop")
    if bytes(d[TRAMP:TRAMP + len(cod)]) != cod:
        erros.append("o trampolim nao ficou como foi montado")
    for nome, p in (("FREE do erro do CRIA", FREE1),
                    ("FREE do APAGA", FREE2)):
        if bytes(d[p:p + len(free)]) != free:
            erros.append(f"o {nome} em 0x{p:06X} nao ficou como foi montado")
    return erros


def main():
    ap = argparse.ArgumentParser(
        description="Reload 3.3: Parte 0 (LVGL em vez do heap na CPU1)")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if not os.path.exists(a.src):
        print(f"RECUSADO: {a.src} nao existe.", file=sys.stderr)
        return 2
    if mesma_entrada(a.src, a.dst):
        print("RECUSADO: --out e a propria entrada (mesmo caminho, symlink "
              "ou hardlink).", file=sys.stderr)
        return 2

    with open(a.src, "rb") as f:
        orig = f.read()
    d = bytearray(orig)
    print("=" * 72)
    print("OpenPod — Reload 3.3: Parte 0, o contexto da capa no LVGL")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n")

    try:
        cod = monta_trampolim()
        free = enc_free()
    except (OSError, RuntimeError, ValueError) as e:
        print(f"  RECUSADO — nao deu para montar o codigo: {e}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    erros = confere_premissas(d, cod, free)
    if erros:
        print("  RECUSADO — a entrada nao e a 3.2 que a ficha mediu:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print("  entrada conferida:")
    print("    - 2 MiB")
    print(f"    - sha256 {SHA_32[:16]}... (a 3.2 sem carimbo)")
    print("    - os tres pontos com as instrucoes de fabrica")
    print(f"    - gap 0x{TRAMP:06X}..0x{FIM_GAP:06X} todo 0xFF")
    print("    - lv_mem_alloc 0xD58188 e lv_mem_free 0xD5811C no lugar")
    print(f"    - trampolim montado: {len(cod)} B (cabe nos 40 B)\n")

    escreve(d, cod, free)
    erros = confere_resultado(d, cod, free)
    if erros:
        print("\n  RECUSADO — a conferencia do resultado falhou:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    permitido = ((ALLOC, ALLOC + 16), (FREE1, FREE1 + 8),
                 (FREE2, FREE2 + 8), (TRAMP, TRAMP + len(cod)))
    fora = [i for i in dif if not any(x <= i < y for x, y in permitido)]
    if fora:
        print(f"  RECUSADO: escreveu fora do permitido em "
              f"0x{min(fora):06X}..0x{max(fora):06X}", file=sys.stderr)
        return 1
    if any(i < 0xE000 or 0xD000 <= i < 0xE000 or i >= 0x1FC000 for i in dif):
        print("  RECUSADO: tocou abaixo de 0xE000, o setor 0xD000 ou a PSMP.",
              file=sys.stderr)
        return 1
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))
    print("\n  PONTOS")
    print(f"    0x{X_ALLOC:08X}  calloc(1,0x2210) -> nop x6 + "
          f"bl 0x{X_TRAMP:08X}")
    print(f"    0x00DAA0D0/0x00DAA0D4  FREE 0xCF7885 -> 0xD5811D")
    print(f"    0x00DAA246/0x00DAA24A  FREE 0xCF7885 -> 0xD5811D")
    print(f"\n  TRAMPOLIM")
    print(f"    0x{X_TRAMP:08X}  lv_mem_alloc(0x2210) + memset ({len(cod)} B)")
    print("  conferencia (bl lido de volta, trampolim, movw/movt): tudo OK")

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    with open(a.dst, "wb") as f:
        f.write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
