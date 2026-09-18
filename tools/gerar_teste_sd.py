#!/usr/bin/env python3
"""
gerar_teste_sd.py — arquivos de teste para o cartao do GN-438

PROPOSITO
    Gerar um lote NOVO de imagens e textos a cada rodada de teste. Nomes
    novos importam: a varredura ("Lendo arquivos. Nao desligue") so tem
    trabalho a fazer quando ha arquivo que o aparelho ainda nao indexou.
    Reusar o lote anterior faz um teste de varredura passar por engano.

FORMATOS ACEITOS PELO FIRMWARE   (tabela em 0x00048860 do dump)
    imagem : .bmp  .jpg  .jpeg
    texto  : .txt
    (tambem .mp3 .wav .flac .ape .aac .m4a .ogg .wma .avi)

USO
    python3 tools/gerar_teste_sd.py                 # lote com a data de hoje
    python3 tools/gerar_teste_sd.py --lote B        # lote nomeado
    python3 tools/gerar_teste_sd.py --saida /Volumes/SD

DEPENDENCIAS
    Pillow (PIL)

LIMITACOES
    - Nomes em 8.3 MAIUSCULO: o navegador de arquivos do aparelho nao
      foi testado com nome longo nem com acento no NOME do arquivo.
    - O conteudo dos .txt usa CRLF, que e o que o leitor espera.
"""
import argparse
import datetime
import os
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("erro: falta Pillow.  pip install pillow")

W, H = 128, 160          # a tela do GN-438


def imagem_padrao(titulo, cor_fundo):
    """Faixas de cor puras + grade de 8 px. Revela canal trocado e escala."""
    img = Image.new("RGB", (W, H), cor_fundo)
    d = ImageDraw.Draw(img)
    faixas = [((255, 0, 0), "VERMELHO"), ((0, 255, 0), "VERDE"),
              ((0, 0, 255), "AZUL"), ((255, 255, 0), "AMARELO"),
              ((255, 255, 255), "BRANCO")]
    h = 24
    for i, (cor, nome) in enumerate(faixas):
        d.rectangle([0, i * h, W, (i + 1) * h - 1], fill=cor)
        d.text((4, i * h + 7), nome, fill=(0, 0, 0) if cor != (0, 0, 255) else (255, 255, 255))
    y0 = len(faixas) * h
    d.rectangle([0, y0, W - 1, H - 1], fill=cor_fundo)
    for x in range(0, W, 8):
        d.line([(x, y0), (x, H - 1)], fill=(90, 90, 90))
    for y in range(y0, H, 8):
        d.line([(0, y), (W - 1, y)], fill=(90, 90, 90))
    d.rectangle([0, y0, W - 1, H - 1], outline=(255, 0, 255))
    d.text((4, y0 + 6), f"{W}x{H}", fill=(255, 255, 255))
    d.text((4, y0 + 18), titulo, fill=(255, 255, 255))
    return img


def main():
    ap = argparse.ArgumentParser(description="arquivos de teste para o cartao")
    ap.add_argument("--saida", default="teste_sd")
    ap.add_argument("--lote", default=None,
                    help="sufixo do lote; o padrao e MMDD da data de hoje")
    args = ap.parse_args()

    lote = args.lote or datetime.date.today().strftime("%m%d")
    lote = "".join(c for c in lote.upper() if c.isalnum())[:4]
    os.makedirs(args.saida, exist_ok=True)
    feitos = []

    def salvar(nome, dados):
        caminho = os.path.join(args.saida, nome)
        modo = "wb" if isinstance(dados, bytes) else None
        if modo:
            open(caminho, modo).write(dados)
        else:
            dados.save(caminho, quality=90)
        feitos.append((nome, os.path.getsize(caminho)))

    # ---- imagens ----
    salvar(f"IMG{lote}A.BMP", imagem_padrao(f"lote {lote} A", (18, 18, 24)))
    salvar(f"IMG{lote}B.JPG", imagem_padrao(f"lote {lote} B", (24, 18, 18)))
    grande = imagem_padrao(f"lote {lote} C", (18, 24, 18)).resize((320, 400), Image.NEAREST)
    caminho = os.path.join(args.saida, f"IMG{lote}C.JPG")
    grande.save(caminho, quality=85)
    feitos.append((f"IMG{lote}C.JPG", os.path.getsize(caminho)))

    # ---- textos ----
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    roteiro = [
        f"OPENPOD - LOTE {lote}  ({hoje})",
        "=" * 34, "",
        "Este arquivo e NOVO para o aparelho.",
        "Se a varredura funcionar, ele aparece",
        "na lista sem passar pela tela principal.", "",
        "O QUE CONFERIR:", "",
        "1. Ao entrar pelo EXTRAS, aparece",
        "   'Lendo arquivos. Nao desligue'?",
        "2. Depois da varredura, este arquivo",
        "   esta na lista?",
        "3. Compare com IMAGEM, que nesta versao",
        "   usa o mecanismo ANTIGO de proposito.",
        "4. O botao voltar leva para onde?",
        "   ANOTE: Extras ou tela inicial?", "",
        "-" * 34,
        "FIM",
    ]
    salvar(f"TXT{lote}A.TXT", ("\r\n".join(roteiro) + "\r\n").encode("ascii"))

    acentos = (f"OPENPOD - LOTE {lote} - ACENTOS\r\n"
               "Codificacao: LATIN-1\r\n\r\n"
               "A cancao e otima, porem a manutencao\r\n"
               "do coracao e dificil.\r\n\r\n"
               "agudo  a e i o u\r\ntil    ~a ~o\r\n"
               "circ   ^a ^e ^o\r\ncedilha c\r\n").replace(
        "a e i o u", "á é í ó ú").replace(
        "~a ~o", "ã õ").replace(
        "^a ^e ^o", "â ê ô").replace(
        "cedilha c", "cedilha ç")
    salvar(f"TXT{lote}B.TXT", acentos.encode("latin-1"))
    salvar(f"TXT{lote}C.TXT", acentos.replace("LATIN-1", "UTF-8").encode("utf-8"))

    longo = f"OPENPOD - LOTE {lote} - PAGINACAO\r\n\r\n"
    longo += "".join(f"Linha {i:04d} - teste de paginacao.\r\n" for i in range(1, 401))
    longo += "\r\nFIM - a paginacao funciona.\r\n"
    salvar(f"TXT{lote}D.TXT", longo.encode("ascii"))

    print(f"lote {lote} em {args.saida}/\n")
    for nome, tam in feitos:
        print(f"  {nome:<16} {tam:>8} B")
    print("\nCopie TODOS para a raiz do cartao. Sao nomes novos: a varredura")
    print("tem trabalho a fazer, que e o que o teste precisa medir.")


if __name__ == "__main__":
    main()
