#!/usr/bin/env python3
"""
fab_reload_3_3_guardas.py — a Parte 1.2 da ficha 025 na Reload 3.3.

PROPOSITO
    Uma guarda sobre a imagem da Parte 0 (sha 368a7c8c...), sem estado
    global: **nao atropelar a fabrica no ring**. Antes dos 8 pedacos tipo
    6, `envia_path` (0xDAAC68) chama a guarda: `[0x81BBC8]` e o struct do
    ring, `0xD6A9EA` o livre. Exige `0x30C0` (8 x (0x414+4) = 0x20C0,
    mais 0x1000 de reserva para a fabrica). Sem espaco, desvia para o
    caminho de falha (libera o tmp e manda o tipo 5 vazio).

    A Parte 1.1 (desistir da capa velha) foi RETIRADA na revisao: o
    gancho do yield em 0xDAAE30 nao respeita o frame de 16 B dos
    wrappers 0xDAAE00/0xDAAE20, e o indice da faixa so muda depois que a
    propria PreTask termina o decode. Desistir da capa velha precisa da
    contagem da fila da PreTask e fica para a tarefa da capa.

    A guarda do ring mora em 0x1AAF50, no lote da capa; a area
    0x1AAF00..0x1AAF4F volta a 0xFF (livre) e as rotinas sao montadas
    com o clang (tools/asm.py).

PREMISSAS
    - a entrada e a Parte 0 exata (sha 368a7c8c...); o `bl` do alloc, o
      trampolim do LVGL e os dois FREE estao no lugar;
    - o ponto do ring em 0xDAAC68 tem a instrucao de fabrica;
    - a area 0x1AAF00..0x1AB000 esta zerada e a rotina cabe;
    - nada abaixo de 0xE000, nem o setor 0xD000, nem a PSMP.
USO
    python3 tools/fab_reload_3_3_guardas.py --in <3.3-p0.bin> --out <3.3.bin>
                                            [--dry-run]
LIMITACOES
    - so serve na Parte 0 exata; o sha da entrada e a catraca;
    - a Parte 1.1 nao entrou; ver `docs/tarefas/025-revisao.md`.
"""
import argparse
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capa_album_asm as A  # noqa: E402
from asm import monta  # noqa: E402

TAMANHO = 0x200000
SHA_P0 = "368a7c8c98f6b6b68c7e38853a69673bb05d5216219406f8ccdc9a858a73713d"
LOTE, LOTE_TAM = 0x1A8000, 0x3000

# --- o ponto da Parte 1.2 (deslocamento no arquivo)
GUARDA_R = 0x1AAC68                   # movw r0,#0x38f1 no envia_path
ORIG_GUARDA_R = bytes.fromhex("43f6f100")

# --- a area livre: os 0x50 B retirados da Parte 1.1 e a guarda do ring
R_LIVRE = 0x1AAF00
R_GUARDA_R = 0x1AAF50
FIM_LIVRE = 0x1AB000

# --- alvos XIP
X_GUARDA_R = 0x00DAAC68
X_R_GUARDA_R = 0x00DAAF50
X_RING = 0x0081BBC8
X_RING_FREE = 0x00D6A9EB
X_FALHA_RING = 0x00DAACFB
X_VOLTA_RING = 0x00DAAC6D
LIMITE_RING = 0x30C0

# --- a Parte 0, para a premissa
P0_BL = 0x1AA04A
P0_TRAMP = 0x1AA9D8
P0_FREE1 = 0x1AA0D0
P0_FREE2 = 0x1AA246
P0_FREE = bytes.fromhex("48f21d1cc0f2d50c")


def mesma_entrada(src, dst):
    if os.path.abspath(src) == os.path.abspath(dst):
        return True
    if not os.path.lexists(dst):
        return False
    try:
        return os.path.samefile(src, dst)
    except OSError:
        return False


def _fonte_guarda_ring():
    return f"""
.syntax unified
.thumb
.text
.align 2
movw r3, #{X_RING & 0xFFFF:#06x}
movt r3, #{(X_RING >> 16) & 0xFFFF:#06x}
ldr r0, [r3]
cbz r0, 1f
movw ip, #{X_RING_FREE & 0xFFFF:#06x}
movt ip, #{(X_RING_FREE >> 16) & 0xFFFF:#06x}
blx ip
movw r1, #{LIMITE_RING:#06x}
cmp r0, r1
blo 1f
movw r0, #0x38f1
movw ip, #{X_VOLTA_RING & 0xFFFF:#06x}
movt ip, #{(X_VOLTA_RING >> 16) & 0xFFFF:#06x}
bx ip
1: movw ip, #{X_FALHA_RING & 0xFFFF:#06x}
movt ip, #{(X_FALHA_RING >> 16) & 0xFFFF:#06x}
bx ip
"""


def monta_rotinas():
    return monta(_fonte_guarda_ring())


def confere_rotinas(ring):
    if not ring:
        return ["a guarda do ring nao montou"]
    if R_GUARDA_R + len(ring) > FIM_LIVRE:
        return ["a guarda do ring passa de 0x1AB000"]
    return []


def confere_premissas(d, ring):
    erros = []
    if len(d) != TAMANHO:
        return [f"a imagem tem {len(d)} bytes, esperado 2 MiB"]
    sha = hashlib.sha256(bytes(d)).hexdigest()
    if sha != SHA_P0:
        erros.append(f"sha256 da entrada {sha[:16]}..., esperado "
                     f"{SHA_P0[:16]}... (a Parte 0 exata)")
    lido = A.desvio(d, P0_BL)
    if lido is None or lido[0] != "bl" or lido[1] != P0_TRAMP + A.XIP:
        erros.append("o bl do alloc da Parte 0 nao esta no lugar")
    if bytes(d[P0_FREE1:P0_FREE1 + 8]) != P0_FREE or \
            bytes(d[P0_FREE2:P0_FREE2 + 8]) != P0_FREE:
        erros.append("os FREE da Parte 0 nao estao no lugar")
    if not any(d[P0_TRAMP:P0_TRAMP + 0x28]):
        erros.append("o trampolim da Parte 0 nao esta escrito")
    if bytes(d[GUARDA_R:GUARDA_R + 4]) != ORIG_GUARDA_R:
        erros.append(f"o ponto do ring em 0x{GUARDA_R:06X} e "
                     f"{bytes(d[GUARDA_R:GUARDA_R + 4]).hex()}, esperado "
                     f"{ORIG_GUARDA_R.hex()}")
    livre = bytes(d[R_LIVRE:FIM_LIVRE])
    if any(livre):
        i = R_LIVRE + next(k for k, v in enumerate(livre) if v)
        erros.append(f"a area 0x{R_LIVRE:06X}..0x{FIM_LIVRE:06X} nao esta "
                     f"zerada (primeiro byte em 0x{i:06X})")
    erros += confere_rotinas(ring)
    return erros


def escreve(d, ring):
    d[GUARDA_R:GUARDA_R + 4] = A.enc(X_GUARDA_R, X_R_GUARDA_R, True)
    d[R_LIVRE:R_GUARDA_R] = b"\xff" * (R_GUARDA_R - R_LIVRE)
    d[R_GUARDA_R:R_GUARDA_R + len(ring)] = ring


def confere_resultado(d, ring):
    erros = []
    lido = A.desvio(d, GUARDA_R)
    if lido is None or lido[0] != "bl" or lido[1] != X_R_GUARDA_R:
        erros.append(f"o bl do ring em 0x{GUARDA_R:06X} nao aponta para "
                     f"0x{X_R_GUARDA_R:08X}")
    if bytes(d[R_LIVRE:R_GUARDA_R]) != b"\xff" * (R_GUARDA_R - R_LIVRE):
        erros.append("a area retirada da Parte 1.1 nao ficou 0xFF")
    if bytes(d[R_GUARDA_R:R_GUARDA_R + len(ring)]) != ring:
        erros.append("a guarda do ring nao ficou como foi montada")
    return erros


def main():
    ap = argparse.ArgumentParser(
        description="Reload 3.3: Parte 1.2 (reserva do ring)")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if not os.path.exists(a.src):
        print(f"RECUSADO: {a.src} nao existe.", file=sys.stderr)
        return 2
    if mesma_entrada(a.src, a.dst):
        print("RECUSADO: --out e a propria entrada.", file=sys.stderr)
        return 2

    with open(a.src, "rb") as f:
        orig = f.read()
    d = bytearray(orig)
    print("=" * 72)
    print("OpenPod — Reload 3.3: Parte 1.2 (reserva do ring)")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n")

    try:
        ring = monta_rotinas()
    except (OSError, RuntimeError, ValueError) as e:
        print(f"  RECUSADO — nao deu para montar o codigo: {e}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    erros = confere_premissas(d, ring)
    if erros:
        print("  RECUSADO — a entrada nao e a Parte 0 esperada:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print("  entrada conferida:")
    print(f"    - sha256 {SHA_P0[:16]}... (a Parte 0)")
    print("    - bl do alloc, trampolim e os dois FREE da Parte 0")
    print(f"    - ponto do ring 0x{GUARDA_R:06X} com a instrucao de fabrica")
    print(f"    - area 0x{R_LIVRE:06X}..0x{FIM_LIVRE:06X} zerada")
    print(f"    - guarda do ring: {len(ring)} B\n")

    escreve(d, ring)
    erros = confere_resultado(d, ring)
    if erros:
        print("\n  RECUSADO — a conferencia do resultado falhou:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    permitido = ((GUARDA_R, GUARDA_R + 4), (R_LIVRE, R_GUARDA_R),
                 (R_GUARDA_R, R_GUARDA_R + len(ring)))
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
    print(f"\n  PONTO\n    0x{X_GUARDA_R:08X}  movw do envia_path -> bl "
          f"0x{X_R_GUARDA_R:08X}")
    print(f"\n  ROTINA\n    0x{X_R_GUARDA_R:08X}  exige 0x30C0 livre no ring "
          f"({len(ring)} B)")
    print("    area 0xDAAF00..0xDAAF4F de volta a 0xFF")
    print("  conferencia (bl lido de volta, area e rotina): tudo OK")

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    with open(a.dst, "wb") as f:
        f.write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
