#!/usr/bin/env python3
"""
gera_capa_1000.py — gera a capa de teste 1000x1000 da ficha 015.

A imagem e derivada de `capa_b_500.jpg` (500x500) pelo mesmo metodo das
outras capas: Pillow, LANCZOS, JPEG baseline, qualidade 88. O arquivo
`capa_d_1000.jpg` e versionado; os testes da ficha 015 o usam para medir
as chamadas de entrada/saida do TJpgDec no emulador. Nao mexe nos MP3.

USO
    python3 tests/assets/rc7/gera_capa_1000.py
"""
import hashlib
import os

from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
ORIGEM = os.path.join(AQUI, "capa_b_500.jpg")
DESTINO = os.path.join(AQUI, "capa_d_1000.jpg")


def main():
    im = Image.open(ORIGEM).convert("RGB").resize((1000, 1000),
                                                  Image.LANCZOS)
    im.save(DESTINO, "JPEG", quality=88, optimize=False, progressive=False)
    dados = open(DESTINO, "rb").read()
    print(f"{os.path.basename(DESTINO)} {len(dados)} B "
          f"sha256 {hashlib.sha256(dados).hexdigest()}")


if __name__ == "__main__":
    main()
