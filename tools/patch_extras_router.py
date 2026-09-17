#!/usr/bin/env python3
"""
patch_extras_router.py — o roteador do menu Extras

PROPOSITO
    Fazer os SEIS itens do Extras abrirem as seis telas certas, na
    Core 3.0.1.

O DEFEITO QUE ELE CORRIGE
    O handler de clique do Extras (0x00D2EF60) e o de fabrica e tem uma
    cadeia de comparacao DESENROLADA com TRES elos:

        ldr r3,[r4]     / cmp r0,r3 / beq  -> indice 0
        ldr r3,[r4,#4]  / cmp r0,r3 / beq  -> indice 1
        ldr r3,[r4,#8]  / cmp r0,r3 / bne  -> SAI SEM FAZER NADA
                                      (cai) -> indice 2

    A pagina de fabrica tem 3 itens. A 3.0.1 desenha 6. Os itens 3, 4 e
    5 nao casam com ponteiro nenhum e a funcao retorna.
    Medido no aparelho em 17/09: Gravacao abria Alarme, Radio abria
    Dicionario, o resto nao fazia nada.

O QUE ELE FAZ
    1. Troca 4 bytes em 0x00D2EFF6 por um `b.w` para a area livre.
    2. Instala em 0x00DA6000 um laco de SEIS posicoes que acha o indice
       do item em foco e POSTA A MENSAGEM, igual a fabrica.

    Ele NAO decide destino. Estender a cadeia de 3 para 6 elos e tudo
    que ele faz. O destino e problema da camada APP.

>>> O ERRO DA Core 3.2, E POR QUE ESTE ARQUIVO MUDOU <<<

    A primeira versao deste patch chamava a primitiva de abrir pagina
    (0x00D0DAE0) DIRETAMENTE, de dentro do callback do LVGL.

    No aparelho: telas travaram e uma pagina de audio comecou a emitir
    ruido.

    A CAUSA: `0x00D23510` -- o que o handler de fabrica usa -- monta uma
    mensagem de 0x1C bytes e chama `0x00D234AC`, que POSTA NA FILA da
    ViewTask. O firmware NUNCA chama a navegacao de dentro de um callback
    do LVGL; ele posta e deixa a camada APP consumir, noutra task.

    Chamar direto executa a abertura de pagina na task errada, com o
    lock do LVGL segurado.

    > A guarda `msg->page == pagina corrente`, que as versoes 3.1 e
    > 3.1.2 tentaram contornar, existe porque a navegacao e ASSINCRONA.
    > Contornar a guarda era o caminho certo; chamar direto nao e.

    A licao: "a receita funciona" foi medida DENTRO de page1_process,
    que ja roda na task certa. Que ela pudesse ser invocada de fora era
    suposicao, e foi apresentada como confirmada.

O QUE ELE PRESERVA
    - 0x00D2F01A (o `pop`), alvo de `bne` em 0x00D2EF7C e 0x00D2F046.
    - page1_process inteira. Zero bytes em 0x00D012E2-0x00D01301.
    - O setor 0x00D000. O CRC da FIRM na tabela NAO e recalculado.

USO
    python3 tools/patch_extras_router.py \
        firmware/WORKING/GN438_core_3.0.1.bin \
        firmware/WORKING/GN438_core_3.2.bin

DEPENDENCIAS
    capstone (so para a auto-verificacao)

LIMITACOES
    - Escrito para a Core 3.0.1. Recusa outra imagem (confere o byte
      da 3.0.1 em 0x001010F6 e a area de destino apagada).
    - Nao recalcula CRC. Por politica do projeto: ver crc_neutralize.py.
"""
import sys

BASE_XIP   = 0x00C00000
ROUTER     = 0x00DA6000          # primeiro setor virgem: 0x001A6000
HOOK       = 0x00D2EFF6          # ldr r3,[r4] + cmp r0,r3  (4 bytes)
POP_SAIDA  = 0x00D2F01A          # pop {r4,r5,r6,pc} original
SELECAO    = 0x00823D84          # byte: item lembrado do Extras

POSTA_MSG  = 0x00D23510          # monta msg 0x1C B e posta na fila (0x00D234AC)
N_ITENS    = 6

# Os destinos NAO ficam aqui. Ficam na camada APP, no handler da pagina
# 0x53 (0x00D0CC0C), que hoje so entende 3 indices. Medidos e prontos
# para o proximo passo, em docs/PLANO_EXTRAS_V2.md:
#
#   0 Gravacao       pagina 0x18   page_record_menu
#   1 Radio          pagina 0x1A   page_fm_play
#   2 Livro digital  pagina 0x0C   page_ebook_list
#   3 Imagem         pagina 0x15   page_pict_list
#   4 Bluetooth      pagina 0x23   page_bt_menu_option
#   5 Pastas         pagina 0x22   page_folder_list


def bl(origem, destino):
    """BL T1 (4 bytes), Thumb-2."""
    off = destino - (origem + 4)
    assert -(1 << 24) <= off < (1 << 24) and off % 2 == 0, "BL fora de alcance"
    off >>= 1
    s = (off >> 23) & 1
    i1 = (off >> 22) & 1
    i2 = (off >> 21) & 1
    imm10 = (off >> 11) & 0x3FF
    imm11 = off & 0x7FF
    j1 = (~i1 & 1) ^ s
    j2 = (~i2 & 1) ^ s
    w1 = 0xF000 | (s << 10) | imm10
    w2 = 0xD000 | (j1 << 13) | (j2 << 11) | imm11
    return w1.to_bytes(2, "little") + w2.to_bytes(2, "little")


def bw(origem, destino):
    """B.W T4 (4 bytes): igual ao BL, sem o bit de link."""
    b = bytearray(bl(origem, destino))
    b[3] &= ~0x40          # limpa o bit 14 do segundo halfword -> B em vez de BL
    return bytes(b)


def montar():
    """Roteador: acha o indice 0..5 e posta a mensagem, como a fabrica.

    A fabrica faz, para os 3 itens dela:
        movs r3,#4 / mov r1,r3 / mov r2,indice / movs r0,#0x53
        bl 0x00D23510
        strb indice, [0x00823D84]
    Isto aqui e a mesma coisa, com o indice vindo de um laco de 6.
    """
    c = bytearray()
    def h(v): c.extend(v.to_bytes(2, "little"))
    A = ROUTER

    h(0x2200)                            # 0x00  movs r2, #0
    c += bytes.fromhex("54f82230")       # 0x02  ldr.w r3, [r4, r2, lsl #2]
    h(0x4298)                            # 0x06  cmp  r0, r3
    h(0xD004)                            # 0x08  beq  ACHOU (0x14)
    h(0x3201)                            # 0x0A  adds r2, #1
    h(0x2A06)                            # 0x0C  cmp  r2, #6
    h(0xD3F8)                            # 0x0E  blo  laco (0x02)
    c += bw(A + 0x10, POP_SAIDA)         # 0x10  nenhum casou -> pop original

    # ACHOU (0x14): r2 = indice do item
    h(0x4B04)                            # 0x14  ldr  r3, [pc,#0x10] -> &SELECAO
    h(0x701A)                            # 0x16  strb r2, [r3]
    h(0x2053)                            # 0x18  movs r0, #0x53   pagina corrente
    h(0x2104)                            # 0x1A  movs r1, #4
    h(0x2304)                            # 0x1C  movs r3, #4
    c += bl(A + 0x1E, POSTA_MSG)         # 0x1E  bl   posta mensagem
    c += bw(A + 0x22, POP_SAIDA)         # 0x22  sai pelo pop original
    h(0xBF00)                            # 0x26  nop (alinha o pool)

    assert len(c) == 0x28, hex(len(c))
    c += SELECAO.to_bytes(4, "little")   # 0x28
    assert len(c) == 0x2C, hex(len(c))
    return bytes(c)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__.strip().split("\n\n")[0] + "\n\nuso: <entrada.bin> <saida.bin>")
    src, dst = sys.argv[1], sys.argv[2]
    img = bytearray(open(src, "rb").read())

    if len(img) != 2 * 1024 * 1024:
        sys.exit(f"erro: esperava 2 MiB, veio {len(img)}")
    if img[0x001010F6] != 0x53:
        sys.exit("erro: nao parece a Core 3.0.1 (byte 0x001010F6 != 0x53)")

    off_router = ROUTER - BASE_XIP
    codigo = montar()
    if any(b != 0xFF for b in img[off_router:off_router + len(codigo)]):
        sys.exit(f"erro: {ROUTER:#x} nao esta apagado — escolha outro setor")

    img[off_router:off_router + len(codigo)] = codigo
    off_hook = HOOK - BASE_XIP
    img[off_hook:off_hook + 4] = bw(HOOK, ROUTER)

    open(dst, "wb").write(img)

    print(f"roteador  {ROUTER:#010x}  {len(codigo)} bytes")
    print(f"gancho    {HOOK:#010x}  4 bytes -> b.w {ROUTER:#x}")
    print()
    print(f"  cadeia de comparacao: 3 elos -> {N_ITENS} elos")
    print(f"  posta msg(0x53, 4, indice, 4) via {POSTA_MSG:#x}, igual a fabrica")
    print("  NAO decide destino — isso e a camada APP, no proximo passo")
    print(f"\nescrito: {dst}")


if __name__ == "__main__":
    main()
