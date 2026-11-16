#!/usr/bin/env python3
"""
fab_limite_capa.py — a receita da Reload 2.2.1 (ficha 019): o limite de
tamanho da capa do album.

PROPOSITO

    Uma ferramenta so, aplicada sobre a 2.2 exata (sha 4fdd31c0...):

      1. troca o `sub.w r0, fp, r5` do `carrega_capa` (0xDAA882) por um
         `bl` para uma rotina nova que refaz o calculo e recusa a imagem
         acima de LIMITE_BYTES (512 KiB);
      2. troca o `movs.w fp, #0` (0xDAA334) por um `bl` para uma rotina
         nova que recusa largura ou altura acima de LIMITE_PX (1000);
      3. escreve as duas rotinas na area livre do lote da capa
         (0x1AAE90 e 0x1AAEC0).

    As rotinas ficam em tools/limite_capa_asm.py, montadas com o clang
    (tools/asm.py): assembly Thumb-2, sem compilador C, para a saida ser
    reprodutivel. Quando o limite passa, a rotina devolve exatamente o
    que a fabrica devolvia (o tamanho restante ou fp=0) e o codigo segue.

PREMISSAS, conferidas ANTES de escrever qualquer byte

    Se UMA premissa falhar, a ferramenta sai com codigo diferente de zero,
    sem criar o arquivo de saida e sem tocar na entrada:

      - a imagem tem 2 MiB e o sha256 e o da 2.2 (4fdd31c0...);
      - os dois pontos de patch ainda tem os bytes de fabrica;
      - a area livre 0x1AAE82..0x1AB000 esta zerada;
      - as duas rotinas montadas cabem e os `bl`/desvios conferem;
      - nada abaixo de 0xE000, nem o setor 0xD000, nem a PSMP.

CONFERENCIA DE SAIDA

    Depois de escrever, a ferramenta RELE o que escreveu e confere: os
    dois `bl` apontam para as rotinas, as rotinas estao byte a byte como
    foram montadas, os desvios de falha (com o bit Thumb) estao certos e
    a diferenca contra a 2.2 fica so nos dois pontos e nas duas rotinas.

SEGURANCA DA ESCRITA

    `--out` e recusado quando aponta para a propria entrada — mesmo
    caminho, symlink ou hardlink (`os.path.samefile`).

USO

    python3 tools/fab_limite_capa.py --in <2.2.bin> --out <2.2.1.bin>
                                     [--limite-px 1000]
                                     [--limite-bytes 524288] [--dry-run]

DEPENDENCIAS

    Python 3 (stdlib) + o clang (tools/asm.py) + capstone (conferencia).

LIMITACOES

    - so serve na 2.2 exata: qualquer outra imagem e recusada;
    - os limites sao os da ficha; mudar aqui muda a 2.2.1 (o teste de
      aceite confere os valores);
    - depois de aplicada, rodar de novo sobre a saida e recusado (o sha
      da entrada ja nao e o da 2.2).
"""

import argparse
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capa_album_asm as A  # noqa: E402
import limite_capa_asm as L  # noqa: E402


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


def confere_premissas(d, cod_b, cod_p, limite_px, limite_bytes):
    erros = []
    if len(d) != L.TAMANHO:
        return [f"a imagem tem {len(d)} bytes, esperado {L.TAMANHO} (2 MiB)"]
    sha = hashlib.sha256(bytes(d)).hexdigest()
    if sha != L.SHA_22:
        erros.append(f"sha256 da entrada {sha[:16]}..., esperado "
                     f"{L.SHA_22[:16]}... (a 2.2 exata, sem carimbo)")
    for nome, a, fab in (("bytes", L.P_BYTES, L.ORIG_BYTES),
                         ("px", L.P_PX, L.ORIG_PX)):
        if bytes(d[a:a + len(fab)]) != fab:
            erros.append(f"o ponto de {nome} em 0x{a:06X} e "
                         f"{bytes(d[a:a + len(fab)]).hex()}, esperado "
                         f"{fab.hex()} (o codigo de fabrica)")
    livre = bytes(d[L.LIVRE_INI:L.LIVRE_FIM])
    if any(livre):
        i = L.LIVRE_INI + next(k for k, v in enumerate(livre) if v)
        erros.append(f"a area livre 0x{L.LIVRE_INI:06X}..0x{L.LIVRE_FIM:06X} "
                     f"nao esta zerada (primeiro byte em 0x{i:06X})")
    erros += L.confere_rotinas(cod_b, cod_p, limite_px, limite_bytes)
    return erros


def escreve(d, cod_b, cod_p):
    d[L.P_BYTES:L.P_BYTES + 4] = A.enc(A.XIP + L.P_BYTES,
                                       A.XIP + L.R_BYTES, True)
    d[L.P_PX:L.P_PX + 4] = A.enc(A.XIP + L.P_PX,
                                 A.XIP + L.R_PX, True)
    d[L.R_BYTES:L.R_BYTES + len(cod_b)] = cod_b
    d[L.R_PX:L.R_PX + len(cod_p)] = cod_p


def confere_resultado(d, cod_b, cod_p, limite_px, limite_bytes):
    erros = []
    for nome, p, r in (("bytes", L.P_BYTES, L.R_BYTES),
                       ("px", L.P_PX, L.R_PX)):
        lido = A.desvio(d, p)
        if lido is None or lido[0] != "bl" or lido[1] != A.XIP + r:
            erros.append(f"o ponto de {nome} em 0x{p:06X} nao e um bl para "
                         f"0x{A.XIP + r:08X}")
    if bytes(d[L.R_BYTES:L.R_BYTES + len(cod_b)]) != cod_b:
        erros.append("a rotina de bytes nao ficou como foi montada")
    if bytes(d[L.R_PX:L.R_PX + len(cod_p)]) != cod_p:
        erros.append("a rotina de px nao ficou como foi montada")
    livre = bytes(d[L.LIVRE_INI:L.LIVRE_FIM])
    ocupado = (set(range(L.R_BYTES - L.LIVRE_INI,
                         L.R_BYTES - L.LIVRE_INI + len(cod_b)))
               | set(range(L.R_PX - L.LIVRE_INI,
                           L.R_PX - L.LIVRE_INI + len(cod_p))))
    if any(v for k, v in enumerate(livre) if k not in ocupado):
        erros.append("sobrou lixo na area livre depois das rotinas")
    erros += L.confere_rotinas(cod_b, cod_p, limite_px, limite_bytes)
    return erros


def main():
    ap = argparse.ArgumentParser(
        description="Reload 2.2.1: limite de tamanho da capa do album")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--limite-px", type=lambda s: int(s, 0),
                    default=L.LIMITE_PX,
                    help=f"limite de largura/altura (padrao {L.LIMITE_PX})")
    ap.add_argument("--limite-bytes", type=lambda s: int(s, 0),
                    default=L.LIMITE_BYTES,
                    help=f"limite do JPEG em bytes (padrao {L.LIMITE_BYTES})")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.limite_px <= 0 or a.limite_bytes <= 0:
        print("RECUSADO: os limites tem de ser positivos.", file=sys.stderr)
        return 2
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
    print("OpenPod — Reload 2.2.1: limite de tamanho da capa")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}")
    print(f"  limites: {a.limite_px} px, {a.limite_bytes} bytes "
          f"({a.limite_bytes / 1024:.0f} KiB)\n")

    try:
        cod_b, cod_p = L.monta_rotinas(a.limite_px, a.limite_bytes)
    except (OSError, RuntimeError, ValueError) as e:
        print(f"  RECUSADO — nao deu para montar o codigo: {e}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    erros = confere_premissas(d, cod_b, cod_p,
                              a.limite_px, a.limite_bytes)
    if erros:
        print("  RECUSADO — a entrada nao e a 2.2 que a ficha mediu:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print("  entrada conferida:")
    print("    - 2 MiB")
    print(f"    - sha256 {L.SHA_22[:16]}... (a 2.2)")
    print(f"    - os dois pontos com o codigo de fabrica")
    print(f"    - area livre 0x{L.LIVRE_INI:06X}..0x{L.LIVRE_FIM:06X} zerada")
    print(f"    - rotinas montadas: bytes {len(cod_b)} B, px {len(cod_p)} B\n")

    escreve(d, cod_b, cod_p)
    erros = confere_resultado(d, cod_b, cod_p,
                              a.limite_px, a.limite_bytes)
    if erros:
        print("\n  RECUSADO — a conferencia do resultado falhou:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    permitido = ((L.P_BYTES, L.P_BYTES + 4), (L.P_PX, L.P_PX + 4),
                 (L.R_BYTES, L.R_BYTES + len(cod_b)),
                 (L.R_PX, L.R_PX + len(cod_p)))
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
    print(f"\n  PONTOS")
    print(f"    0x{L.P_BYTES:06X}  sub.w r0, fp, r5 -> bl 0x{A.XIP + L.R_BYTES:08X}")
    print(f"    0x{L.P_PX:06X}  movs.w fp, #0 -> bl 0x{A.XIP + L.R_PX:08X}")
    print(f"\n  ROTINAS")
    print(f"    0x{L.R_BYTES:06X}  limite de {a.limite_bytes} bytes "
          f"({len(cod_b)} B)")
    print(f"    0x{L.R_PX:06X}  limite de {a.limite_px} px ({len(cod_p)} B)")
    print("  conferencia (bls lidos de volta, rotinas e desvios): tudo OK")

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    with open(a.dst, "wb") as f:
        f.write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
