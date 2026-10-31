#!/usr/bin/env python3
"""
fab_capa_album.py — a receita da Reload 1.0 RC7 (ficha 007): a capa do
álbum (ID3v2 APIC) na tela Tocando Agora.

PROPOSITO

    Uma ferramenta so, aplicada sobre a RC6 (sha af3a2b6d...). Ela:

      1. aumenta a struct da view da Tocando Agora de 0x30 para 0x34 bytes
         (o campo novo, [view+0x30], e o contexto da capa);
      2. troca o `lv_img_create` do papel de parede por uma rotina nova
         (CRIA) que cria o fundo, o contexto e a imagem da capa;
      3. troca o `lv_label_set_text` das mensagens por uma rotina nova
         (TITULO) que, depois de escrever o texto, procura a capa no MP3
         da faixa e troca a imagem;
      4. escreve no lote 0x001A8000..0x001AB000: o descritor do quadrado
         cinza (com a nota musical), os 8192 pixels dele, a tabela das
         entradas e o codigo das rotinas.

    O codigo das rotinas esta em tools/capa_album.s e e montado com o
    clang (tools/asm.py): assembly Thumb-2, sem compilador C, para a
    saida ser reprodutivel (catraca).

    Nao mexe no visualizador de fotos (o global 0x81CDE8), nem em outra
    tela, nem na letra. Nao usa nem copia patch_icones_home.py,
    patch_home_barra.py, patch_cor_selecao.py, patch_menu_text.py,
    aplica_textos.py ou patch_nome_faixa.py.

    O layout do lote, os encoders do Thumb-2 e a montagem do codigo moram
    no modulo capa_album_asm.py (a regra do projeto: ate 350 linhas por
    ferramenta).

PREMISSAS, conferidas ANTES de escrever qualquer byte

    Se UMA premissa falhar, a ferramenta sai com codigo diferente de zero,
    sem criar o arquivo de saida e sem tocar na entrada:

      - a imagem tem 2 MiB;
      - o sha256 da entrada e o da RC6 (af3a2b6d...). A receita e a RC6
        mais esta ferramenta; qualquer outra imagem e recusada;
      - os dois `movs` de tamanho da view sao os de fabrica (0x30);
      - o `bl` do papel de parede ainda chama o lv_img_create (0x00D5D850)
        e o `b.w` do texto ainda chama o lv_label_set_text (0x00D5ED94);
      - o lote 0x001A8000..0x001AB000 esta virgem (todo 0xFF);
      - o TJpgDec da fabrica (0x00D10900..0x00D12000) esta intacto: e ele
        que decodifica a capa, e um TJpgDec diferente decodifica outra
        coisa (sem erro visivel);
      - o quadrado cinza (tests/assets/rc7/placeholder_64x64.rgb565swap)
        esta com o sha esperado;
      - o codigo das rotinas tem os tres trampolins no lugar e cabe no
        lote.

CONFERENCIA DE SAIDA

    Depois de escrever, a ferramenta RELE o que escreveu e confere: os
    alvos dos dois ganchos, os bytes do tamanho da view, o descritor da
    imagem cinza, os 8192 pixels, a tabela das entradas (cada `b.w` para
    dentro do lote) e o codigo montado. Qualquer byte fora do permitido e
    recusa, sem gravar.

SEGURANCA DA ESCRITA

    `--out` e recusado quando aponta para a propria entrada — mesmo
    caminho, symlink ou hardlink (`os.path.samefile`). E so se escreve
    DENTRO de: 0x00131E80..0x00131E82, 0x00131E9E..0x00131EA0,
    0x00131EB6..0x00131EBA, 0x0013225E..0x00132262 e o lote
    0x001A8000..0x001AB000. Nada abaixo de 0x00E000, e o setor 0x00D000
    e a PSMP (0x001FC000+) ficam intocados.

USO

    python3 tools/fab_capa_album.py --in <entrada.bin> --out <saida.bin>
                                     [--em 0x1a8000] [--dry-run]

DEPENDENCIAS

    Python 3 (stdlib) + o clang (usado por tools/asm.py para montar o
    Thumb-2). Nao abre USB, nao grava no aparelho.

LIMITACOES

    - so serve na RC6 exata: qualquer outra imagem e recusada;
    - o codigo das rotinas e montado na hora: e preciso ter o clang
      instalado (o tools/asm.py procura `clang` no PATH);
    - so o 1º APIC conta, e a capa tem de ser JPEG baseline;
    - depois de aplicada, rodar de novo sobre a saida e recusado (o sha da
      entrada ja nao e o da RC6 e o lote ja nao esta virgem).
"""

import argparse
import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capa_album_asm as A  # noqa: E402


# ---------------------------------------------------------------------------
# premissas
# ---------------------------------------------------------------------------

def confere_premissas(d, cod):
    """TODAS as premissas da ficha. Devolve a lista de erros (vazia = ok)."""
    erros = []
    if len(d) != A.TAMANHO:
        return [f"a imagem tem {len(d)} bytes, esperado {A.TAMANHO} (2 MiB)"]
    sha = hashlib.sha256(bytes(d)).hexdigest()
    if sha != A.SHA_ENTRADA:
        erros.append(f"sha256 da entrada {sha[:16]}..., esperado "
                     f"{A.SHA_ENTRADA[:16]}... — a receita e a RC6 mais esta "
                     f"ferramenta, e so a RC6 entra")
    for a, (fab, _novo) in sorted(A.TAM_VIEW.items()):
        if bytes(d[a:a + 2]) != fab:
            erros.append(f"o tamanho da view em 0x{a:06X} e "
                         f"{bytes(d[a:a + 2]).hex()}, esperado {fab.hex()} "
                         f"(o `movs` de fabrica)")
    for a, fab, _novo in (A.GANCHO_BL, A.GANCHO_B):
        alvo = A.desvio(d, a)
        if alvo is None or alvo[1] != fab:
            erros.append(f"0x{a:06X} chama "
                         f"{'nada' if alvo is None else f'0x{alvo[1]:08X}'}, "
                         f"esperado 0x{fab:08X} (o gancho de fabrica)")
    ocupado = [i for i in range(A.LOTE, A.LOTE + A.LOTE_TAM) if d[i] != 0xFF]
    if ocupado:
        erros.append(f"o lote 0x{A.LOTE:06X}..0x{A.LOTE + A.LOTE_TAM:06X} tem "
                     f"{len(ocupado)} byte(s) fora do 0xFF, o primeiro em "
                     f"0x{ocupado[0]:06X} — o lote tem de estar virgem")
    ini, fim = A.TJPGDEC
    got = hashlib.sha256(bytes(d[ini:fim])).hexdigest()
    if got != A.SHA_TJPGDEC:
        erros.append(f"o TJpgDec da fabrica (0x{ini + A.XIP:08X}..) mudou "
                     f"(sha {got[:16]}..., esperado {A.SHA_TJPGDEC[:16]}...)")
    try:
        quad, got = A.sha_placeholder()
    except OSError as e:
        erros.append(f"o quadrado cinza nao pode ser lido: {e}")
        quad = b""
    if quad:
        if got != A.SHA_PLACEHOLDER:
            erros.append(f"o quadrado cinza mudou (sha {got[:16]}..., "
                         f"esperado {A.SHA_PLACEHOLDER[:16]}...)")
        elif len(quad) != A.PIX_TAM:
            erros.append(f"o quadrado cinza tem {len(quad)} bytes, "
                         f"esperado {A.PIX_TAM}")
    erros += A.confere_codigo(cod)
    return erros


# ---------------------------------------------------------------------------
# a escrita
# ---------------------------------------------------------------------------

def escreve(d, cod, quad):
    """Escreve os ganchos e o lote."""
    for a, (_fab, novo) in sorted(A.TAM_VIEW.items()):
        d[a:a + 2] = A.TAM_VIEW[a][1]
    d[A.GANCHO_BL[0]:A.GANCHO_BL[0] + 4] = A.enc(A.XIP + A.GANCHO_BL[0],
                                                 A.GANCHO_BL[2], True)
    d[A.GANCHO_B[0]:A.GANCHO_B[0] + 4] = A.enc(A.XIP + A.GANCHO_B[0],
                                               A.GANCHO_B[2], False)
    lote = bytearray(b"\xFF" * A.LOTE_TAM)
    struct.pack_into("<III", lote, A.DSC - A.LOTE, A.HDR_64, A.PIX_TAM,
                      A.PIX_GRAY)
    lote[A.PIX - A.LOTE:A.PIX - A.LOTE + A.PIX_TAM] = quad
    for i, alvo in enumerate(A.ENTRADAS):
        struct.pack_into("<HH", lote, A.TABELA + 4 * i - A.LOTE,
                         *struct.unpack("<HH",
                                        A.enc(A.XIP + A.TABELA + 4 * i,
                                              alvo, False)))
    lote[A.CODIGO - A.LOTE:A.CODIGO - A.LOTE + len(cod)] = cod
    d[A.LOTE:A.LOTE + A.LOTE_TAM] = bytes(lote)


def confere_resultado(d, cod, quad):
    """Rele o que foi escrito e confere, sem confiar na montagem."""
    erros = []
    for a, (_fab, novo) in sorted(A.TAM_VIEW.items()):
        if bytes(d[a:a + 2]) != novo:
            erros.append(f"o tamanho da view em 0x{a:06X} nao ficou "
                         f"{novo.hex()}")
    for a, _fab, novo in (A.GANCHO_BL, A.GANCHO_B):
        alvo = A.desvio(d, a)
        if alvo is None or alvo[1] != novo:
            erros.append(f"0x{a:06X} nao aponta para 0x{novo:08X}")
    if bytes(d[A.DSC:A.DSC + A.DSC_TAM]) != struct.pack("<III", A.HDR_64,
                                                         A.PIX_TAM, A.PIX_GRAY):
        erros.append("o descritor da imagem cinza nao ficou como a ficha")
    if bytes(d[A.PIX:A.PIX + A.PIX_TAM]) != quad:
        erros.append("os pixels do quadrado cinza nao ficaram como o modelo")
    for i, alvo in enumerate(A.ENTRADAS):
        lido = A.desvio(d, A.TABELA + 4 * i)
        if lido is None or lido[0] != "b.w" or lido[1] != alvo:
            erros.append(f"a entrada {i} da tabela nao e um b.w para "
                         f"0x{alvo:08X}")
    if bytes(d[A.CODIGO:A.CODIGO + len(cod)]) != cod:
        erros.append("o codigo das rotinas nao ficou como foi montado")
    if any(x != 0xFF for x in d[A.CODIGO + len(cod):A.LOTE + A.LOTE_TAM]):
        erros.append("lixo depois do codigo, dentro do lote")
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
        description="RC7: a capa do álbum (ID3v2 APIC) na Tocando Agora")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--em", default=None,
                    help=f"endereco do lote (tem de ser {A.LOTE:#x})")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.em is not None:
        try:
            em = int(a.em, 0)
        except ValueError:
            print(f"RECUSADO: --em {a.em!r} nao e um endereco.",
                  file=sys.stderr)
            return 2
        if em != A.LOTE:
            print(f"RECUSADO: --em {em:#x}; o lote desta ferramenta esta em "
                  f"{A.LOTE:#x}, e o MAPA do build.py declara esse.",
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
    print("=" * 72)
    print("OpenPod — RC7: a capa do álbum na Tocando Agora")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n")

    try:
        cod = A.monta_codigo()
        quad, _sha = A.sha_placeholder()
    except (OSError, RuntimeError) as e:
        print(f"  RECUSADO — nao deu para montar o codigo: {e}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    erros = confere_premissas(d, cod)
    if erros:
        print("  RECUSADO — a entrada nao e a RC6 que a ficha mediu:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print("  entrada conferida:")
    print("    - 2 MiB")
    print(f"    - sha256 {A.SHA_ENTRADA[:16]}... (a RC6)")
    print("    - os dois `movs` de tamanho da view sao os de fabrica (0x30)")
    print("    - os dois ganchos ainda chamam o alvo de fabrica")
    print(f"    - lote 0x{A.LOTE:06X}..0x{A.LOTE + A.LOTE_TAM:06X} virgem")
    print(f"    - o TJpgDec da fabrica intacto (0x{A.TJPGDEC[0] + A.XIP:08X}..)")
    print("    - o quadrado cinza com o sha esperado")
    print(f"    - o codigo das rotinas: {len(cod)} bytes\n")

    escreve(d, cod, quad)
    erros = confere_resultado(d, cod, quad)
    if erros:
        print("\n  RECUSADO — a conferencia do resultado falhou:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    fora = [i for i in dif if not any(a0 <= i < b0 for a0, b0 in A.PERMITIDO)]
    if fora:
        print(f"  RECUSADO: escreveu fora do permitido em "
              f"0x{min(fora):06X}..0x{max(fora):06X}", file=sys.stderr)
        return 1
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))
    print("\n  GANCHOS")
    print("    0x131E80  lv_mem_alloc(0x30) -> 0x34")
    print("    0x131E9E  memset(view, 0, 0x30) -> 0x34")
    print(f"    0x{A.GANCHO_BL[0]:06X}  bl 0x{A.GANCHO_BL[1]:08X} -> "
          f"0x{A.GANCHO_BL[2]:08X} (CRIA)")
    print(f"    0x{A.GANCHO_B[0]:06X}  b.w 0x{A.GANCHO_B[1]:08X} -> "
          f"0x{A.GANCHO_B[2]:08X} (TITULO)")
    print(f"\n  LOTE 0x{A.LOTE:06X}..0x{A.LOTE + A.LOTE_TAM:06X}")
    print(f"    0x{A.DSC:06X}  o descritor da imagem cinza (64x64, TRUE_COLOR)")
    print(f"    0x{A.PIX:06X}  os {A.PIX_TAM} pixels do quadrado cinza (o modelo)")
    print(f"    0x{A.TABELA:06X}  CRIA, TITULO e APAGA")
    print(f"    0x{A.CODIGO:06X}  o codigo ({len(cod)} bytes)")
    print("\n  conferencia (alvos dos ganchos lidos de volta, o descritor, os "
          "pixels, a tabela e o codigo): tudo OK")

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    with open(a.dst, "wb") as f:
        f.write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
