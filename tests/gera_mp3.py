#!/usr/bin/env python3
"""
gera_mp3.py — gera as capas de teste da ficha 019 (JPEG baseline q95,
4:4:4, com textura) e o MP3 com o APIC.

O objetivo e medir o custo do `carrega_capa` em tamanhos que o aparelho
ainda nao tinha visto: 640, 1000, 1200, 1500, 2000 e 3000 px. A imagem
tem textura de verdade (blocos coloridos e aneis) para o JPEG nao virar
um arquivo minusculo e enganar a medicao.

Nada e versionado: o teste gera no diretorio temporario e apaga.
"""

import io

from PIL import Image, ImageDraw


def jpeg(lado):
    """JPEG RGB baseline, q95, sem subsampling (4:4:4), com textura."""
    img = Image.new("RGB", (lado, lado))
    d = ImageDraw.Draw(img)
    passo = max(1, lado // 16)
    for y in range(0, lado, passo):
        for x in range(0, lado, passo):
            d.rectangle([x, y, x + passo - 1, y + passo - 1],
                        fill=((x * 7 + y * 3) % 256,
                              (x * 3 + y * 11) % 256,
                              (x * 13 + y * 5) % 256))
    cx, cy = lado * 0.37, lado * 0.61
    for i in range(12):
        r = int(lado * (0.05 + i * 0.035))
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  outline=((i * 37) % 256, (i * 71) % 256, (i * 113) % 256),
                  width=max(1, lado // 300))
    b = io.BytesIO()
    img.save(b, "JPEG", quality=95, subsampling=0)
    return b.getvalue()


def mp3(lado, audio):
    """Um MP3 minimo com um APIC JPEG do tamanho pedido."""
    import emu_rc7 as E
    return E.tag_id3(3, [E.apic(3, jpeg(lado))]) + audio
