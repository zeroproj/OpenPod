#!/usr/bin/env python3
"""
fab_diag_trava.py — as tres imagens de BISSECAO da ficha 008 (a RC7 trava
ao tocar): um degrau a mais a partir da RC7 exata.

PROPOSITO

    O decisor precisa saber ONDE a Tocando Agora trava quando o aparelho
    comeca a tocar (a ficha 008). A analise estatica do ORIGINAL deu H1
    como PROVAVEL: a ViewTask ficou lenta (o TITULO agora abre o banco e o
    MP3), o ring de mensagens enche, e o bug da fabrica (o take do mutex do
    ring sem give no caminho "cheio") trava toda tarefa que manda mensagem
    para a view.

    Para fechar a duvida no aparelho, tres imagens, cada uma um degrau a
    mais. As tres sao PATCHES CIRURGICOS no lote JA MONTADO da RC7 (4/2/2
    bytes): nada e remontado, nada fora dos bytes da RC7 e mexido.

      A  "TITULO so faz o set_text"
         A entrada TITULO da tabela do lote (0x001AA014) deixa de apontar
         para o TITULO_impl e passa a apontar para o lv_label_set_text da
         fabrica (0x00D5ED94). O `b.w` do gancho (0x13225E) cai na entrada
         e repassa direto: o comportamento e o de fabrica (sem get_path,
         sem FatFs, sem JPEG). CRIA e APAGA ficam intactos: o quadrado
         cinza continua e o contexto continua criado e liberado. 4 bytes.

      B  "A + get_path, sem arquivo"
         A entrada TITULO fica ORIGINAL (o TITULO_impl inteiro roda: o
         get_path de verdade, com o mutex do banco e o FatFs do db_audio
         .db) e a UNICA chamada externa ao f_open (0x00D777CD) dentro do
         codigo do lote e desligada: o `blx` vira `movs r0, #1`. O f_open
         "falha" (r0 = 1) e o codigo entra no caminho de erro ja testado
         (cinza, sem f_close, sem jd_*). Sem decodificacao. 2 bytes.

      C  "B + f_open/f_close"
         A entrada TITULO fica ORIGINAL e a vitima e a UNICA chamada
         externa ao jd_prepare (0x00D10B21): o `blx` vira `movs r0, #1`.
         O f_open do MP3 roda DE VERDADE (o arquivo abre), o jd_prepare
         "falha", e o caminho de erro fecha o arquivo (f_close real) e
         mostra o cinza. Sem leitura de JPEG, sem jd_decomp, sem
         reescala. 2 bytes.

    (D e a RC7 inteira, que ja existe.)

PREMISSAS, conferidas ANTES de escrever qualquer byte

    Se UMA premissa falhar, a ferramenta sai com codigo diferente de zero,
    sem criar o arquivo de saida e sem tocar na entrada:

      - a imagem tem 2 MiB;
      - o sha256 da entrada e o da RC7 exata (3af97713...). A receita e a
        RC7 mais esta ferramenta; qualquer outra imagem e recusada;
      - a tabela de entradas do lote esta no lugar: 0x001AA010/14/18
        decodificam como `b.w` para o CRIA/TITULO/APAGA (0xDAA01C/20/24);
      - nivel a: a entrada TITULO (0x001AA014) ainda e o `b.w` para o
        TITULO_impl (0x00DAA020) — nao foi patcheada antes;
      - nivel b/c: o par `movw/movt` que carrega o alvo (0x00D777CD do
        f_open, 0x00D10B21 do jd_prepare, com o bit do Thumb) aparece
        EXATAMENTE UMA vez no codigo do lote, e o `blx` que o segue ainda
        esta la (nao foi patcheado antes).

CONFERENCIA DE SAIDA

    Depois de escrever, a ferramenta RELE o que escreveu e confere: o
    `b.w` novo da entrada TITULO decodificado de volta (alvo 0x00D5ED94) ou
    os 2 bytes novos (`movs r0, #1` = 01 20) lidos de volta como
    instrucao. Depois faz o diff final contra a entrada: A tem de ser
    4 bytes em 0x001AA014, B e C tem de ser 2 bytes (o `blx` escolhido).
    Qualquer byte a mais ou a menos e recusa, sem gravar a saida.

SEGURANCA DA ESCRITA

    `--out` e recusado quando aponta para a propria entrada — mesmo
    caminho, symlink ou hardlink (`os.path.samefile`). E so se escreve
    DENTRO do lote 0x001A8000..0x001AB000 (4/2/2 bytes). Nada abaixo de
    0x00E000, e o setor 0x00D000 e a PSMP (0x001FC000+) ficam intocados.

USO

    python3 tools/fab_diag_trava.py --in <rc7.bin> --out <diag.bin>
                                    --nivel a|b|c [--em 0x1a8000] [--dry-run]

    O `--em` e o endereco do lote onde o patch acontece (0x001A8000, o
    mesmo da RC7). A receita do build.py passa esse endereco; a
    ferramenta recusa se vier outro.

DEPENDENCIAS

    Python 3 (stdlib) + o modulo `tools/diag_trava_asm.py` (o layout do
    lote e o scanner das chamadas; ele usa o `tools/capa_album_asm.py`, o
    mesmo par encoder/leitor de Thumb-2 que o `tests/test_rc7.py` usa).
    Nao abre USB, nao grava no aparelho.

LIMITACOES

    - so serve na RC7 exata: qualquer outra imagem e recusada;
    - o codigo do lote NAO e remontado: as tres imagens sao a RC7 com 4,
      2 ou 2 bytes trocados. O que o lote faz alem do ponto cortado
      continua igual (e o que a bissecao mede);
    - no nivel B o `f_open` e substituido por `movs r0, #1`: o caminho de
      erro chama `free` duas vezes com ponteiro NULO (o JDEC e o pool nunca
      foram alocados). Se a libc da ROM nao tolerar free(NULL), a imagem B
      REINICIA o aparelho no primeiro titulo — e nao trava (diferenca
      observavel na hora);
    - depois de aplicada, rodar de novo sobre a saida e recusado (o sha da
      entrada ja nao e o da RC7 e a regiao ja esta patcheada).
"""

import argparse
import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capa_album_asm as A  # noqa: E402
import diag_trava_asm as G  # noqa: E402

TAMANHO = 0x200000


# ---------------------------------------------------------------------------
# premissas
# ---------------------------------------------------------------------------

def confere_premissas(d, nivel):
    """TODAS as premissas da ficha. Devolve a lista de erros (vazia = ok)."""
    erros = []
    if len(d) != TAMANHO:
        return [f"a imagem tem {len(d)} bytes, esperado {TAMANHO} (2 MiB)"]
    sha = hashlib.sha256(bytes(d)).hexdigest()
    if sha != G.SHA_RC7:
        erros.append(f"sha256 da entrada {sha[:16]}..., esperado "
                     f"{G.SHA_RC7[:16]}... — a receita e a RC7 exata mais esta "
                     f"ferramenta, e so a RC7 entra")
    for i, alvo in enumerate(G.ENTRADAS):
        lido = A.desvio(d, G.TABELA + 4 * i)
        if lido is None or lido[0] != "b.w" or lido[1] != alvo:
            erros.append(f"a entrada {i} da tabela (0x{G.TABELA + 4 * i:06X}) "
                         f"nao e um b.w para 0x{alvo:08X} — o lote da RC7 "
                         f"nao esta no lugar")
    if nivel == "a":
        lido = A.desvio(d, G.TABELA + 4)
        if lido is not None and lido[0] == "b.w" and lido[1] == G.SET_TEXT:
            erros.append("a entrada TITULO ja aponta para o lv_label_set_text "
                         "da fabrica: a imagem ja foi patcheada")
        return erros
    # nivel b/c: a chamada alvo tem de existir exatamente uma vez
    valor = G.NIVEL[nivel][1]
    pares = G.acha_pares(d, valor)
    if len(pares) != 1:
        erros.append(f"o par movw/movt que carrega 0x{valor:08X} aparece "
                     f"{len(pares)}x no codigo do lote, esperado 1")
        return erros
    off = pares[0] + 8
    if bytes(d[off:off + 2]) == G.FALHA:
        erros.append(f"a chamada em 0x{off:06X} ja esta patcheada "
                     f"(movs r0, #1)")
        return erros
    h = struct.unpack_from("<H", d, off)[0]
    _, h2 = struct.unpack_from("<HH", d, pares[0])
    if not G.e_blx(h) or ((h >> 3) & 0xF) != ((h2 >> 8) & 0xF):
        erros.append(f"em 0x{off:06X} nao ha um blx para o registrador "
                     f"carregado — o codigo do lote mudou")
    return erros


# ---------------------------------------------------------------------------
# a escrita
# ---------------------------------------------------------------------------

def alvo_do_patch(d, nivel):
    """(deslocamento, tamanho) do que o patch do nivel vai mexer."""
    if nivel == "a":
        return G.TABELA + 4, 4
    off = G.achado_unico(d, G.NIVEL[nivel][1])
    if off is None:
        return None, 0
    return off, 2


def escreve(d, nivel, off, tam):
    """Escreve o patch do nivel (4 bytes no nivel a, 2 nos niveis b e c)."""
    if nivel == "a":
        d[off:off + 4] = A.enc(A.XIP + off, G.SET_TEXT, False)
    else:
        d[off:off + 2] = G.FALHA
    return tam


def confere_resultado(d, nivel, off, tam):
    """Rele o que foi escrito e confere, sem confiar na montagem."""
    erros = []
    if nivel == "a":
        lido = A.desvio(d, off)
        if lido is None or lido[0] != "b.w" or lido[1] != G.SET_TEXT:
            erros.append(f"a entrada TITULO nao ficou um b.w para "
                         f"0x{G.SET_TEXT:08X}")
    else:
        if bytes(d[off:off + 2]) != G.FALHA:
            erros.append("os 2 bytes novos nao sao 01 20 (movs r0, #1)")
        h = struct.unpack_from("<H", d, off)[0]
        if (h & 0xF800) != 0x2000 or ((h >> 8) & 0x7) != 0:
            erros.append("os 2 bytes novos nao decodificam como movs r0, #1")
    return erros


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


def main():
    ap = argparse.ArgumentParser(
        description="RC7: as tres imagens de bissecao da ficha 008")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--nivel", required=True, choices=sorted(G.NIVEL),
                    help="a: so o set_text | b: + get_path | c: + f_open")
    ap.add_argument("--em", default=None,
                    help=f"endereco do lote (tem de ser {G.LOTE:#x})")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.em is not None:
        try:
            em = int(a.em, 0)
        except ValueError:
            print(f"RECUSADO: --em {a.em!r} nao e um endereco.",
                  file=sys.stderr)
            return 2
        if em != G.LOTE:
            print(f"RECUSADO: --em {em:#x}; o lote desta ferramenta esta em "
                  f"{G.LOTE:#x} (e a receita passa esse endereco).",
                  file=sys.stderr)
            return 2
    if not os.path.exists(a.src):
        print(f"RECUSADO: {a.src} nao existe.", file=sys.stderr)
        return 2
    if mesma_entrada(a.src, a.dst):
        print("RECUSADO: --out e a propria entrada (mesmo caminho, symlink "
              "ou hardlink).", file=sys.stderr)
        return 2

    orig = open(a.src, "rb").read()
    d = bytearray(orig)
    medido = G.NIVEL[a.nivel][0]
    print("=" * 72)
    print("OpenPod — RC7: a imagem de bisseção da ficha 008")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n")
    print(f"  nivel {a.nivel.upper()}: {medido}")

    erros = confere_premissas(d, a.nivel)
    if erros:
        print("\n  RECUSADO — a entrada nao e a RC7 que a ficha mediu:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print("  entrada conferida:")
    print("    - 2 MiB")
    print(f"    - sha256 {G.SHA_RC7[:16]}... (a RC7 exata)")
    print("    - a tabela de entradas do lote esta no lugar (CRIA/TITULO/APAGA)")
    if a.nivel == "a":
        print("    - a entrada TITULO ainda e o TITULO_impl (nao patcheada)")
    else:
        print(f"    - a chamada a 0x{G.NIVEL[a.nivel][1]:08X} aparece 1x no lote")

    off, tam = alvo_do_patch(d, a.nivel)
    if off is None:
        print("\n  RECUSADO: a chamada alvo nao foi achada no codigo do lote.")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print(f"\n  PATCH\n    0x{off:06X}..0x{off + tam:06X}  {tam} byte(s)")
    if a.nivel == "a":
        print(f"    a entrada TITULO vira b.w 0x{G.SET_TEXT:08X} "
              f"(o lv_label_set_text da fabrica)")
    else:
        print("    o blx da chamada vira movs r0, #1 (a chamada falha)")

    escreve(d, a.nivel, off, tam)
    erros = confere_resultado(d, a.nivel, off, tam)
    if erros:
        print("\n  RECUSADO — a conferencia do resultado falhou:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    esperado = list(range(off, off + tam))
    if dif != esperado:
        print(f"\n  RECUSADO: o diff final nao e o esperado — {len(dif)} byte(s) "
              f"diferentes, esperado {tam} em 0x{off:06X}..0x{off + tam:06X}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    if any(not (G.LOTE <= i < G.LOTE + G.LOTE_TAM) for i in dif):
        print("  RECUSADO: escreveu fora do lote.", file=sys.stderr)
        return 1
    if any(i < 0x00E000 for i in dif) or any(0xD000 <= i < 0xE000 for i in dif) \
            or any(i >= 0x1FC000 for i in dif):
        print("  RECUSADO: tocou o bootloader, o setor 0xD000 ou a PSMP.",
              file=sys.stderr)
        return 1
    print(f"\n  bytes alterados: {len(dif)}   em 0x{min(dif):06X}.."
          f"0x{max(dif):06X}")
    print("  nada abaixo de 0x00E000; setor 0xD000 e PSMP intocados   OK")

    if a.dry_run:
        print("\n  --dry-run: nada foi gravado.")
        return 0
    with open(a.dst, "wb") as f:
        f.write(bytes(d))
    print(f"\n  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
