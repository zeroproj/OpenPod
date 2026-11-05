#!/usr/bin/env python3
"""
fab_diag_trava.py — as tres imagens de BISSECAO da ficha 008 (a RC7 trava
ao tocar) e o degrau B0 da ficha 009 (a RC7 REINICIA o aparelho).

PROPOSITO

    O decisor precisa saber ONDE a Tocando Agora trava quando o aparelho
    comeca a tocar (a ficha 008). A analise estatica do ORIGINAL deu H1
    como PROVAVEL: a ViewTask ficou lenta (o TITULO agora abre o banco e o
    MP3), o ring de mensagens enche, e o bug da fabrica (o take do mutex do
    ring sem give no caminho "cheio") trava toda tarefa que manda mensagem
    para a view.

    Para fechar a duvida no aparelho, tres imagens, cada uma um degrau a
    mais. As tres sao PATCHES CIRURGICOS no lote JA MONTADO da RC7 (4/4/2
    bytes): nada e remontado, nada fora dos bytes da RC7 e mexido.

      A  "TITULO so faz o set_text" — 4 bytes em 0x001AA014.
         A entrada TITULO da tabela do lote deixa de apontar para o
         TITULO_impl e passa a apontar para o lv_label_set_text da
         fabrica (0x00D5ED94). O `b.w` do gancho (0x13225E) cai na entrada
         e repassa direto: o comportamento e o de fabrica (sem get_path,
         sem FatFs, sem JPEG). CRIA e APAGA ficam intactos: o quadrado
         cinza continua e o contexto continua criado e liberado.

      B  "A + get_path, sem arquivo" — 4 bytes (o `bl` do carrega_capa).
         A entrada TITULO fica ORIGINAL (o TITULO_impl inteiro roda: o
         get_path de verdade, com o mutex do banco e o FatFs do db_audio
         .db) e o que e cortado e o `bl` interno que chama o
         `carrega_capa`: ele vira `movs r0, #0` + `nop`. O `cmp r0,#0;
         beq fim_titulo` que ja existe logo depois termina o TITULO — de
         pois do get_path, da comparacao do caminho, do caminho guardado e
         do quadrado cinza. **Sem calloc, sem free, sem arquivo**: e
         literalmente "A + get_path, sem arquivo".

      C  "B + f_open/f_close" — 2 bytes (o `blx` do jd_prepare).
         A entrada TITULO fica ORIGINAL e a vitima e a UNICA chamada
         externa ao jd_prepare (0x00D10B21): o `blx` vira `movs r0, #1`.
         O f_open do MP3 roda DE VERDADE (o arquivo abre), o jd_prepare
         "falha", e o caminho de erro fecha o arquivo (f_close real) e
         mostra o cinza. Sem leitura de JPEG, sem jd_decomp, sem
         reescala.

      B0 "TITULO ligado, get_path cortado" — 2 bytes (ficha 009).
         A entrada TITULO fica ORIGINAL (a rotina INTEIRA roda, com o
         set_text, a leitura da view/ext, a comparacao do caminho e o
         quadrado cinza) e a vitima e a chamada ao `get_path`
         (0x00CFEFC5): o `blx` vira `movs r0, #0` — o get_path "falha",
         o caminho guardado fica vazio e o quadrado cinza aparece. E o
         degrau que separa "a ROTINA" de "o get_path".

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
      - nivel b: o `carrega_capa` e a UNICA rotina do lote com o prologo
        `push {r4-r11,lr}` + `sub sp,#12` (as outras seis usam `sub
        sp,#4`), e o `bl` interno que a chama aparece EXATAMENTE UMA vez
        (o alvo e decodificado do binario) — e esse `bl` ainda esta la
        (nao foi patcheado antes);
      - nivel c: o par `movw/movt` que carrega o jd_prepare
        (0x00D10B21, com o bit do Thumb) aparece EXATAMENTE UMA vez no
        codigo do lote, e o `blx` que o segue ainda esta la;
      - nivel b0: o par `movw/movt` que carrega o get_path
        (0x00CFEFC5, com o bit do Thumb) aparece EXATAMENTE UMA vez no
        codigo do lote, e o `blx` que o segue ainda esta la.

CONFERENCIA DE SAIDA

    Depois de escrever, a ferramenta RELE o que escreveu e confere: o
    `b.w` novo da entrada TITULO decodificado de volta (alvo 0x00D5ED94),
    os 4 bytes novos do nivel B lidos de volta (`movs r0, #0` + `nop`) ou
    os 2 bytes novos do nivel C (`movs r0, #1` = 01 20). Depois faz o diff
    final contra a entrada: nenhum byte pode mudar FORA da regiao do patch
    (4/4/2 bytes). Qualquer byte a mais e recusa, sem gravar a saida.

SEGURANCA DA ESCRITA

    `--out` e recusado quando aponta para a propria entrada — mesmo
    caminho, symlink ou hardlink (`os.path.samefile`). E so se escreve
    DENTRO do lote 0x001A8000..0x001AB000 (4/4/2 bytes). Nada abaixo de
    0x00E000, e o setor 0x00D000 e a PSMP (0x001FC000+) ficam intocados.

USO

    python3 tools/fab_diag_trava.py --in <rc7.bin> --out <diag.bin>
                                    --nivel a|b|c|b0 [--em 0x1a8000] [--dry-run]

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
      4 ou 2 bytes trocados. O que o lote faz alem do ponto cortado
      continua igual (e o que a bissecao mede);
    - o nivel B NAO entra no `carrega_capa` (e nao tem `calloc`, `free`
      nem arquivo): e por isso que ele mede so o `get_path` — o
      `free(NULL)` do caminho de erro da RC7 (que fica no nivel C e no D)
      nao aparece nele;
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
    if nivel == "b":
        # o carrega_capa: o prologo e unico, e o bl que o chama tambem
        prologos = G.acha_carrega_capa(d)
        if len(prologos) != 1:
            erros.append(f"o prologo do carrega_capa aparece {len(prologos)}x "
                         f"no codigo do lote, esperado 1")
            return erros
        alvo = prologos[0] + G.XIP
        bls = G.acha_bl_para(d, alvo)
        if len(bls) != 1:
            if G.acha_bytes(d, G.FALHA_BL):
                erros.append("o bl do carrega_capa ja esta patcheado "
                             "(movs r0, #0 + nop)")
            else:
                erros.append(f"o bl interno que chama o carrega_capa aparece "
                             f"{len(bls)}x no codigo do lote, esperado 1")
            return erros
        off = bls[0]
        if bytes(d[off:off + 4]) == G.FALHA_BL:
            erros.append(f"o bl em 0x{off:06X} ja esta patcheado "
                         f"(movs r0, #0 + nop)")
            return erros
        lido = A.desvio(d, off)
        if lido is None or lido[0] != "bl" or lido[1] != alvo:
            erros.append(f"em 0x{off:06X} nao ha um bl para o carrega_capa "
                         f"(0x{alvo:08X}) — o codigo do lote mudou")
        return erros
    # niveis c e b0: a chamada externa tem de existir exatamente uma vez
    valor = G.GET_PATH if nivel == "b0" else G.JD_PREP
    pares = G.acha_pares(d, valor)
    if len(pares) != 1:
        erros.append(f"o par movw/movt que carrega 0x{valor:08X} aparece "
                     f"{len(pares)}x no codigo do lote, esperado 1")
        return erros
    off = pares[0] + 8
    if bytes(d[off:off + 2]) == (G.FALHA_ZERO if nivel == "b0" else G.FALHA):
        erros.append(f"a chamada em 0x{off:06X} ja esta patcheada "
                     f"({'movs r0, #0' if nivel == 'b0' else 'movs r0, #1'})")
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
                    help="a: so o set_text | b: + get_path | c: + f_open "
                         "| b0: TITULO ligado, get_path cortado")
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
    medido = G.NIVEL[a.nivel]
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
    elif a.nivel == "b":
        print("    - o carrega_capa (prologo unico) e o bl que o chama: 1x")
    elif a.nivel == "b0":
        print(f"    - a chamada ao get_path (0x{G.GET_PATH:08X}) aparece 1x "
              f"no lote")
    else:
        print(f"    - a chamada a 0x{G.JD_PREP:08X} aparece 1x no lote")

    off, tam, novos = G.bytes_do_patch(d, a.nivel)
    if off is None:
        print("\n  RECUSADO: o alvo do patch nao foi achado no codigo do lote.")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print(f"\n  PATCH\n    0x{off:06X}..0x{off + tam:06X}  {tam} byte(s)")
    if a.nivel == "a":
        print(f"    a entrada TITULO vira b.w 0x{G.SET_TEXT:08X} "
              f"(o lv_label_set_text da fabrica)")
    elif a.nivel == "b":
        print("    o bl do carrega_capa vira movs r0, #0 + nop "
              "(o TITULO para depois do get_path)")
    elif a.nivel == "b0":
        print("    o blx do get_path vira movs r0, #0 "
              "(o get_path 'falha': o caminho guardado fica vazio e o "
              "quadrado cinza aparece)")
    else:
        print("    o blx da chamada vira movs r0, #1 (a chamada falha)")

    d[off:off + tam] = novos
    erros = G.confere_patch(d, a.nivel, off, tam, novos)
    if erros:
        print("\n  RECUSADO — a conferencia do resultado falhou:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    fora = [i for i in dif if not (off <= i < off + tam)]
    if fora:
        print(f"\n  RECUSADO: o diff final tem {len(fora)} byte(s) FORA do "
              f"patch (0x{min(fora):06X}..0x{max(fora):06X})")
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
    print(f"\n  bytes alterados: {len(dif)} (de {tam} da regiao "
          f"0x{off:06X}..0x{off + tam:06X})")
    print("  nada fora do patch, nada abaixo de 0x00E000; setor 0xD000 e "
          "PSMP intocados   OK")

    if a.dry_run:
        print("\n  --dry-run: nada foi gravado.")
        return 0
    with open(a.dst, "wb") as f:
        f.write(bytes(d))
    print(f"\n  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
