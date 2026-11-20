#!/usr/bin/env python3
"""
fab_reload_3_3_guardas.py — a Parte 1 da ficha 025 na Reload 3.3.

PROPOSITO
    Duas guardas sobre a imagem da Parte 0 (sha 368a7c8c...), sem estado
    global:

    1. **Desistir da capa velha.** O `page4_media_cb` grava o indice da
       faixa em `[0x0081BC84+0x20]` no comando 5 (`0xD08966:
       str r2,[r3,#0x20]`). O `get_path` le esse campo. Na decodificacao,
       o indice e copiado para `jd+0x118+0x14` (o CTX do leitor; o
       `+0x10/+0x12` sao largura/altura e o `+0x14` esta livre) logo
       depois do `jd_prepare`; cada yield do B7b compara o capturado com
       o atual e, se mudou, devolve 0 (o `jd_decomp` para e o
       `carrega_capa` cai no caminho de falha).
       A API visivel nao tem contagem (`0x9068` create, `0x8FFC` reset,
       `0xB372` send/recv, `0x9442` delete); o indice e o campo provado
       de "o usuario pulou" e nao depende do layout da fila.
    2. **Nao atropelar a fabrica no ring.** Antes dos 8 pedacos tipo 6,
       `envia_path` (0xDAAC68) chama a guarda: `[0x81BBC8]` e o struct
       do ring, `0xD6A9EA` o livre. Exige `0x30C0` (8 x (0x414+4) =
       0x20C0, mais 0x1000 de reserva para a fabrica). Sem espaco,
       desvia para o caminho de falha (libera o tmp e manda o tipo 5
       vazio).
    As rotinas ficam na area zerada do lote da capa (0x1AAF00..0x1AB000,
    depois do B7b) e sao montadas com o clang.
PREMISSAS

    - a entrada e a Parte 0 exata (sha 368a7c8c...); o `bl` do alloc, o
      trampolim do LVGL e os dois FREE estao no lugar;
    - os tres pontos da Parte 1 tem as instrucoes de fabrica;
    - a area 0x1AAF00..0x1AB000 esta zerada e as rotinas cabem;
    - nada abaixo de 0xE000, nem o setor 0xD000, nem a PSMP.
USO
    python3 tools/fab_reload_3_3_guardas.py --in <3.3-p0.bin> --out <3.3.bin>
                                            [--dry-run]
LIMITACOES
    - so serve na Parte 0 exata; o sha da entrada e a catraca;
    - o indice e uma decisao de engenharia: a ficha pedia a contagem da
      fila, que nao existe na API visivel; o `025-analise.md` registra a
      prova e o desvio.
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

# --- os tres pontos da Parte 1 (deslocamentos no arquivo)
CAPTURA = 0x1AA324                    # ldrh r0,[r8,#0x1c] no carrega_capa
GUARDA_I = 0x1AAE30                   # mov r5,r0; movs r0,#1 no b7_common
GUARDA_R = 0x1AAC68                   # movw r0,#0x38f1 no envia_path
# --- os bytes de fabrica
ORIG_CAPTURA = bytes.fromhex("b8f81c00")
ORIG_GUARDA_I = bytes.fromhex("05460120")
ORIG_GUARDA_R = bytes.fromhex("43f6f100")

# --- as rotinas novas, na area zerada do lote
R_CAPTURA = 0x1AAF00
R_GUARDA_I = 0x1AAF20
R_GUARDA_R = 0x1AAF50
FIM_LIVRE = 0x1AB000
# --- alvos XIP
X_CAPTURA = 0x00DAA324
X_GUARDA_I = 0x00DAAE30
X_GUARDA_R = 0x00DAAC68
X_R_CAPTURA = 0x00DAAF00
X_R_GUARDA_I = 0x00DAAF20
X_R_GUARDA_R = 0x00DAAF50
X_INDICE = 0x0081BC84
X_RING = 0x0081BBC8
X_YIELD = 0x00C43635
X_RING_FREE = 0x00D6A9EB
X_FALHA_RING = 0x00DAACFB
X_VOLTA_RING = 0x00DAAC6D
X_CTX_INDICE = 0x12C                  # CTX (0x118) + 0x14
LIMITE_RING = 0x30C0

# --- a Parte 0, para a premissa
P0_ALLOC = 0x1AA03E
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


def _fonte_captura():
    return f"""
.syntax unified
.thumb
.text
.align 2
push {{r3, lr}}
movw r3, #{(X_INDICE) & 0xFFFF:#06x}
movt r3, #{(X_INDICE >> 16) & 0xFFFF:#06x}
ldr r3, [r3, #0x20]
str r3, [r8, #{X_CTX_INDICE:#06x}]
ldrh r0, [r8, #0x1c]
pop {{r3, pc}}
"""


def _fonte_guarda_indice():
    return f"""
.syntax unified
.thumb
.text
.align 2
mov r5, r0
ldr r0, [r4, #{X_CTX_INDICE:#06x}]
movw r1, #{(X_INDICE) & 0xFFFF:#06x}
movt r1, #{(X_INDICE >> 16) & 0xFFFF:#06x}
ldr r1, [r1, #0x20]
cmp r0, r1
bne 1f
movs r0, #1
movw ip, #{X_YIELD & 0xFFFF:#06x}
movt ip, #{(X_YIELD >> 16) & 0xFFFF:#06x}
blx ip
mov r0, r5
add sp, #4
pop {{r4-r6, pc}}
1: movs r0, #0
add sp, #4
pop {{r4-r6, pc}}
"""


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
    return (monta(_fonte_captura()), monta(_fonte_guarda_indice()),
            monta(_fonte_guarda_ring()))


def confere_rotinas(cod):
    cap, gid, ring = cod
    erros = []
    if len(cap) == 0 or len(gid) == 0 or len(ring) == 0:
        return ["uma rotina nao montou"]
    if R_CAPTURA + len(cap) > R_GUARDA_I:
        erros.append("a captura invade a guarda do indice")
    if R_GUARDA_I + len(gid) > R_GUARDA_R:
        erros.append("a guarda do indice invade a guarda do ring")
    if R_GUARDA_R + len(ring) > FIM_LIVRE:
        erros.append("a guarda do ring passa de 0x1AB000")
    return erros


def confere_premissas(d, cod):
    erros = []
    if len(d) != TAMANHO:
        return [f"a imagem tem {len(d)} bytes, esperado 2 MiB"]
    sha = hashlib.sha256(bytes(d)).hexdigest()
    if sha != SHA_P0:
        erros.append(f"sha256 da entrada {sha[:16]}..., esperado "
                     f"{SHA_P0[:16]}... (a Parte 0 exata)")
    # a Parte 0 esta aplicada
    lido = A.desvio(d, P0_BL)
    if lido is None or lido[0] != "bl" or lido[1] != P0_TRAMP + A.XIP:
        erros.append("o bl do alloc da Parte 0 nao esta no lugar")
    if bytes(d[P0_FREE1:P0_FREE1 + 8]) != P0_FREE or \
            bytes(d[P0_FREE2:P0_FREE2 + 8]) != P0_FREE:
        erros.append("os FREE da Parte 0 nao estao no lugar")
    if not any(d[P0_TRAMP:P0_TRAMP + 0x28]):
        erros.append("o trampolim da Parte 0 nao esta escrito")
    # os tres pontos da Parte 1
    for nome, p, fab in (("captura", CAPTURA, ORIG_CAPTURA),
                         ("guarda do indice", GUARDA_I, ORIG_GUARDA_I),
                         ("guarda do ring", GUARDA_R, ORIG_GUARDA_R)):
        if bytes(d[p:p + len(fab)]) != fab:
            erros.append(f"o ponto de {nome} em 0x{p:06X} e "
                         f"{bytes(d[p:p + len(fab)]).hex()}, esperado "
                         f"{fab.hex()}")
    livre = bytes(d[R_CAPTURA:FIM_LIVRE])
    if any(livre):
        i = R_CAPTURA + next(k for k, v in enumerate(livre) if v)
        erros.append(f"a area 0x{R_CAPTURA:06X}..0x{FIM_LIVRE:06X} nao esta "
                     f"zerada (primeiro byte em 0x{i:06X})")
    erros += confere_rotinas(cod)
    return erros


def escreve(d, cod):
    cap, gid, ring = cod
    d[CAPTURA:CAPTURA + 4] = A.enc(X_CAPTURA, X_R_CAPTURA, True)
    d[GUARDA_I:GUARDA_I + 4] = A.enc(X_GUARDA_I, X_R_GUARDA_I, True)
    d[GUARDA_R:GUARDA_R + 4] = A.enc(X_GUARDA_R, X_R_GUARDA_R, True)
    d[R_CAPTURA:R_CAPTURA + len(cap)] = cap
    d[R_GUARDA_I:R_GUARDA_I + len(gid)] = gid
    d[R_GUARDA_R:R_GUARDA_R + len(ring)] = ring


def confere_resultado(d, cod):
    cap, gid, ring = cod
    erros = []
    for nome, p, alvo in (("captura", CAPTURA, X_R_CAPTURA),
                          ("guarda do indice", GUARDA_I, X_R_GUARDA_I),
                          ("guarda do ring", GUARDA_R, X_R_GUARDA_R)):
        lido = A.desvio(d, p)
        if lido is None or lido[0] != "bl" or lido[1] != alvo:
            erros.append(f"o bl de {nome} em 0x{p:06X} nao aponta para "
                         f"0x{alvo:08X}")
    for nome, r, c in (("captura", R_CAPTURA, cap),
                       ("guarda do indice", R_GUARDA_I, gid),
                       ("guarda do ring", R_GUARDA_R, ring)):
        if bytes(d[r:r + len(c)]) != c:
            erros.append(f"a rotina de {nome} nao ficou como foi montada")
    return erros


def main():
    ap = argparse.ArgumentParser(
        description="Reload 3.3: Parte 1 (indice da faixa e ring)")
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
    print("OpenPod — Reload 3.3: Parte 1 (capa velha e ring)")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n")

    try:
        cod = monta_rotinas()
    except (OSError, RuntimeError, ValueError) as e:
        print(f"  RECUSADO — nao deu para montar o codigo: {e}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    erros = confere_premissas(d, cod)
    if erros:
        print("  RECUSADO — a entrada nao e a Parte 0 esperada:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print("  entrada conferida:")
    print(f"    - sha256 {SHA_P0[:16]}... (a Parte 0)")
    print("    - bl do alloc, trampolim e os dois FREE da Parte 0")
    print("    - os tres pontos da Parte 1 com as instrucoes de fabrica")
    print(f"    - area 0x{R_CAPTURA:06X}..0x{FIM_LIVRE:06X} zerada")
    print(f"    - rotinas: captura {len(cod[0])} B, indice {len(cod[1])} B, "
          f"ring {len(cod[2])} B\n")

    escreve(d, cod)
    erros = confere_resultado(d, cod)
    if erros:
        print("\n  RECUSADO — a conferencia do resultado falhou:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    permitido = ((CAPTURA, CAPTURA + 4), (GUARDA_I, GUARDA_I + 4),
                 (GUARDA_R, GUARDA_R + 4),
                 (R_CAPTURA, R_CAPTURA + len(cod[0])),
                 (R_GUARDA_I, R_GUARDA_I + len(cod[1])),
                 (R_GUARDA_R, R_GUARDA_R + len(cod[2])))
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
    print(f"    0x{X_CAPTURA:08X}  ldrh -> bl 0x{X_R_CAPTURA:08X}")
    print(f"    0x{X_GUARDA_I:08X}  inicio do b7_common -> bl "
          f"0x{X_R_GUARDA_I:08X}")
    print(f"    0x{X_GUARDA_R:08X}  movw do envia_path -> bl "
          f"0x{X_R_GUARDA_R:08X}")
    print("\n  ROTINAS")
    print(f"    0x{X_R_CAPTURA:08X}  captura o indice em jd+0x12C")
    print(f"    0x{X_R_GUARDA_I:08X}  compara e aborta (0) se mudou")
    print(f"    0x{X_R_GUARDA_R:08X}  exige 0x30C0 livre no ring")
    print("  conferencia (bls lidos de volta e rotinas): tudo OK")

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    with open(a.dst, "wb") as f:
        f.write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
