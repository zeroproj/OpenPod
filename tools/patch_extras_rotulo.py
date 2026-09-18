#!/usr/bin/env python3
"""
patch_extras_rotulo.py — o item da home passa a se chamar "Extras"

O PROBLEMA
    A Core 3.0.1 trocou o DESTINO do item 2 da home (abre a pagina 0x53,
    o Extras) e nao trocou o ROTULO. Ele continua escrito "Gravacao".

DE ONDE VEM O ROTULO   (medido em page_home_menu_create)

    0x00D2EC60  ldr  r6, [pc,#0xa0]  -> 0x00C486C4   a tabela de ids
    0x00D2ECE2  ldr  r0, [r6]                        id do item
    0x00D2ECE4  adds r6, #4
    0x00D2ECE6  bl   #0x00D2108C                     get_string(id)

    Tabela em 0x00C486C4, 9 entradas de 4 bytes:
        0:1 Musica  1:3 Video  2:5 Gravacao  3:6 Radio  4:2 Livro
        5:4 Imagem  6:9 Bluetooth  7:10 Configurar  8:8 Pastas

POR QUE NAO TROCAR O TEXTO DO id 5
    O id 5 tambem nomeia o PRIMEIRO ITEM DENTRO do Extras. Trocar o
    texto mudaria os dois.

POR QUE O id 156, E NAO UM id NOVO
    `get_string` (0x00D2108C) NAO valida o id -- so o idioma
    (`cmp r0,#8`) -- e depois faz `ldr.w r4,[r3, r4, lsl #2]` cru.
    Inventar um id 216 leria ponteiro selvagem nas outras tabelas.

    O id 156 ("TP version:") e string MORTA: existe e e ponteiro valido
    nos NOVE idiomas, e nenhuma chamada em toda a FIRM faz
    `get_string(156)` -- verificado por varredura.

USO
    python3 tools/patch_extras_rotulo.py entrada.bin saida.bin

LIMITACOES
    - Se algum dia algo passar a usar o id 156, os dois textos colidem.
    - As traducoes abaixo sao escolha editorial, nao medicao.
"""
import struct
import sys

BASE_XIP = 0x00C00000
TAB_HOME = 0x00C486C4        # 9 ids, um por item da home
ITEM     = 2                 # o que abre o Extras
ID_MORTO = 156               # "TP version:"
TEXTOS   = 0x00DA6400        # area livre, mesmo setor do roteador

# tabela de strings de cada idioma, na ordem do tbb de get_string
IDIOMAS = [
    (0x00C52AA4, "ingles",    "Extras"),
    (0x00C523E4, "chines",    "更多"),        # 更多  = "mais"
    (0x00C52E04, "frances",   "Extras"),
    (0x00C52744, "alemao",    "Extras"),
    (0x00C534C4, "italiano",  "Extra"),
    (0x00C53EE4, "espanhol",  "Extras"),
    (0x00C53164, "hebraico",  "תוספות"),  # תוספות
    (0x00C53824, "holandes",  "Extra"),
    (0x00DA3600, "portugues", "Extras"),
]


def main():
    if len(sys.argv) != 3:
        sys.exit("uso: patch_extras_rotulo.py <entrada.bin> <saida.bin>")
    img = bytearray(open(sys.argv[1], "rb").read())
    if len(img) != 2 * 1024 * 1024:
        sys.exit("erro: esperava 2 MiB")

    # 1. escreve os textos na area livre
    blob, mapa = bytearray(), {}
    for _, nome, txt in IDIOMAS:
        if txt not in mapa:                  # textos iguais compartilham bytes
            mapa[txt] = TEXTOS + len(blob)
            blob += txt.encode("utf-8") + b"\x00"
    off = TEXTOS - BASE_XIP
    if any(b != 0xFF for b in img[off:off + len(blob)]):
        sys.exit(f"erro: {TEXTOS:#x} nao esta apagado")
    img[off:off + len(blob)] = blob

    # 2. reponta o id 156 em cada idioma
    for tab, nome, txt in IDIOMAS:
        e = tab - BASE_XIP + ID_MORTO * 4
        antigo = struct.unpack("<I", img[e:e + 4])[0]
        img[e:e + 4] = mapa[txt].to_bytes(4, "little")
        print(f"  {nome:<10} {tab:#010x}+{ID_MORTO*4:#x}  "
              f"{antigo:#010x} -> {mapa[txt]:#010x}  {txt!r}")

    # 3. o item 2 da home passa a usar o id 156
    e = TAB_HOME - BASE_XIP + ITEM * 4
    antigo = struct.unpack("<I", img[e:e + 4])[0]
    img[e:e + 4] = ID_MORTO.to_bytes(4, "little")
    print(f"\n  home item {ITEM}: id {antigo} -> id {ID_MORTO}")

    open(sys.argv[2], "wb").write(img)
    print(f"\n  textos: {TEXTOS:#010x}  {len(blob)} bytes")
    print(f"  escrito: {sys.argv[2]}")


if __name__ == "__main__":
    main()
