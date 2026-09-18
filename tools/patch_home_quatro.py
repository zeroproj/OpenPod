#!/usr/bin/env python3
"""
patch_home_quatro.py — a tela inicial passa a ter QUATRO itens

O ALVO, do docs/PLANO_EXTRAS.md (14/09)

    HOME                    EXTRAS
      Musica                  Gravacao
      Video                   Radio
      Extras      ->          Livro digital
      Configurar              Imagem
                              Bluetooth
                              Pastas

    Hoje a home tem nove itens e cinco deles se repetem dentro do
    Extras. Com quatro, a geometria tambem fecha:

        hoje      22 + 9 x 16 = 166   nao cabe em 160
        com 4     22 + 4 x 16 =  86   sobra folga

SEIS PONTOS ACOPLADOS, todos medidos

  1. o laco do create desenha 9 vezes
        0x00D2ECFC  cmp r5, #9   ->  cmp r5, #4
  2. rotacao para cima: 0 volta para 8
        0x00D2EA4E  movs r2, #8  ->  movs r2, #3
  3. rotacao para baixo: passou de 8 volta para 0
        0x00D2EAD6  cmp r2, #8   ->  cmp r2, #3
  4. o ENTRAR valida a faixa antes de postar a mensagem
        0x00D2EA66  cmp r2, #8   ->  cmp r2, #3
  5. a tabela de rotulos da home (0x00C486C4)
        [1, 3, 156, 6, 2, 4, 9, 10, 8]  ->  [1, 3, 156, 10, ...]
  6. o indice 3 tem que abrir CONFIGURAR
        O caso do indice 3 (0x00D0113C) e o do RADIO. Ele e reescrito
        com o padrao do indice 2 -- o Extras, que funciona NESTA imagem:

            movs r3, #0x28 / movs r2, #0 / movs r1, #2
            movs r0, #1    / b 0x00D011F2

        NAO copiar o caso de fabrica do indice 7 (0x00D0123A). Ele omite
        `movs r0,#1` (conta com r0 ja valer 1) e passa `sub = 7`. As
        duas coisas quebraram: a Core 4.8 e a 4.9 nao abriam Configurar.
        Medido pela DIAG 6 (o codigo executa) e pela DIAG 7 (o sub era
        o culpado).

POR QUE E SEGURO DESTRUIR O CASO DO RADIO
    O Radio continua acessivel pelo Extras, e o nosso despacho NAO
    salta para 0x00D0113C: ele REPLICA a inicializacao do FM numa
    sub-rotina propria (ver patch_extras_app.py, rotulo "fm"). A Core
    3.5 provou que saltar para casos da home nao funciona.

USO
    python3 tools/patch_home_quatro.py entrada.bin saida.bin

LIMITACOES
    - Os itens 4..8 continuam existindo na tabela de rotulos e no
      despacho; so ficam inalcancaveis pela home.
    - A geometria da lista NAO e alterada aqui. Se a home ficar com
      sobra de espaco embaixo, e assunto de outro patch.
"""
import struct
import sys

BASE_XIP = 0x00C00000
TAB_HOME = 0x00C486C4
CASO_IDX3 = 0x00D0113C       # hoje: o caso do Radio
TRAMPOLIM = 0x00D011F2
N_ITENS  = 4

# rotulos: Musica, Video, Extras, Configurar
ROTULOS = [1, 3, 156, 10]

BYTES = [
    (0x00D2ECFC, "092d", "042d", "create: desenha 9 -> 4 itens"),
    (0x00D2EA4E, "0822", "0322", "rotacao p/ cima: 0 volta para 3"),
    (0x00D2EAD6, "082a", "032a", "rotacao p/ baixo: passou de 3 volta a 0"),
    (0x00D2EA66, "082a", "032a", "entrar: valida indice <= 3"),
]


def main():
    if len(sys.argv) != 3:
        sys.exit("uso: patch_home_quatro.py <entrada.bin> <saida.bin>")
    img = bytearray(open(sys.argv[1], "rb").read())
    if len(img) != 2 * 1024 * 1024:
        sys.exit("erro: esperava 2 MiB")

    for addr, antes, depois, texto in BYTES:
        off = addr - BASE_XIP
        if img[off:off + 2].hex() != antes:
            sys.exit(f"erro: {addr:#x} tem {img[off:off+2].hex()}, "
                     f"esperava {antes} — imagem errada?")
        img[off:off + 2] = bytes.fromhex(depois)
        print(f"  {addr:#010x}  {texto}")

    # 5. a tabela de rotulos
    for i, rid in enumerate(ROTULOS):
        off = TAB_HOME - BASE_XIP + 4 * i
        antigo = struct.unpack("<I", img[off:off + 4])[0]
        img[off:off + 4] = rid.to_bytes(4, "little")
        if antigo != rid:
            print(f"  {TAB_HOME + 4*i:#010x}  rotulo do item {i}: "
                  f"id {antigo} -> id {rid}")

    # 6. o indice 3 abre Configurar
    off = CASO_IDX3 - BASE_XIP
    c = bytearray()
    c += (0x2300 | 0x28).to_bytes(2, "little")   # movs r3, #0x28  (pagina)
    # O caso de fabrica do indice 7 passa sub = 7. Copiar esse 7 fazia
    # Configurar NAO ABRIR (Core 4.8 e 4.9). O `sub` vira
    # `strh r2,[r3,#4]` na struct da pagina, e o valor 7 nao sobrevive a
    # home reduzida a quatro itens. Medido pela DIAG 7: com sub = 0,
    # Configurar abre normalmente. O caso do indice 2 (o Extras), que
    # sempre funcionou nesta imagem, tambem usa 0.
    c += (0x2200 | 0).to_bytes(2, "little")      # movs r2, #0     (sub)
    c += (0x2100 | 2).to_bytes(2, "little")      # movs r1, #2
    # `movs r0, #1` NAO estava no caso de fabrica do indice 7, que conta
    # com r0 ja valendo 1 ao chegar na tbh. Copiei a forma sem verificar
    # a dependencia, e Configurar nao abria. O caso do indice 2 (o
    # Extras, que funciona nesta mesma imagem) define r0 explicitamente.
    c += (0x2000 | 1).to_bytes(2, "little")      # movs r0, #1  (origem)
    salto = CASO_IDX3 + 8
    delta = (TRAMPOLIM - (salto + 4)) // 2
    assert -1024 <= delta < 1024, hex(delta)
    c += (0xE000 | (delta & 0x7FF)).to_bytes(2, "little")   # b TRAMPOLIM
    img[off:off + len(c)] = c
    print(f"  {CASO_IDX3:#010x}  indice 3 passa a abrir Configurar "
          f"(pagina 0x28) — o caso do Radio e reescrito")

    open(sys.argv[2], "wb").write(img)
    print(f"\n  home: {' | '.join(['Musica','Video','Extras','Configurar'])}")
    print(f"  escrito: {sys.argv[2]}")


if __name__ == "__main__":
    main()
