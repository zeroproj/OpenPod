#!/usr/bin/env python3
"""
gera_mp3.py — gera os MP3 de teste da RC7 (ficha 007) a partir das capas
desta pasta e do áudio `_audio_6s.mp3` (tom de 440 Hz, 6 s, 64 kbps, sem tag;
ffmpeg + lame 3.100). Os arquivos gerados são versionados; os testes
conferem o sha256 de cada um (tests/test_rc7.py).

USO
    python3 tests/assets/rc7/gera_mp3.py
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", ".."))
from emu_rc7 import tag_id3, texto, apic, ext_header  # noqa: E402


def le(n):
    return open(os.path.join(AQUI, n), "rb").read()


AUDIO = le("_audio_6s.mp3")
A, B, C = le("capa_a_300.jpg"), le("capa_b_500.jpg"), le("capa_c_200x120.jpg")
ARQ = {
    "01_capa_v23.mp3": tag_id3(3, [texto(3, b"TIT2", "Capa rosa v2.3"), texto(3, b"TPE1", "OpenPod"),
                                   apic(3, A)]),
    "02_capa_v24.mp3": tag_id3(4, [texto(4, b"TIT2", "Capa azul v2.4"), texto(4, b"TPE1", "OpenPod"),
                                   texto(4, b"TALB", "RC7"), apic(4, B, enc=1, desc="Capa da frente")]),
    "03_capa_v24_cabecalho_estendido.mp3": tag_id3(4, [texto(4, b"TIT2", "Listras v2.4"),
                                                       apic(4, C, enc=3, desc="listras")],
                                                   flags=0x40, ext=ext_header(4)),
    "04_capa_progressiva.mp3": tag_id3(3, [texto(3, b"TIT2", "Progressiva"),
                                           apic(3, le("capa_a_progressiva.jpg"))]),
    "05_capa_png.mp3": tag_id3(3, [texto(3, b"TIT2", "PNG"), apic(3, le("capa_a.png"), mime=b"image/png")]),
    "06_sem_capa.mp3": tag_id3(3, [texto(3, b"TIT2", "Sem capa"), texto(3, b"TPE1", "OpenPod")]),
    "07_sem_tag.mp3": b"",
}
for nome, tag in ARQ.items():
    with open(os.path.join(AQUI, nome), "wb") as f:
        f.write(tag + AUDIO)
    print(nome, len(tag) + len(AUDIO))
