#!/usr/bin/env python3
"""
patch_extras_app.py — os seis destinos do Extras, na camada APP

PROPOSITO
    Fazer o handler da pagina 0x53 (camada APP) entender SEIS indices em
    vez de tres, e mandar cada um para a tela certa.

    E a segunda metade do conserto. A primeira (Core 3.3) esta em
    `tools/patch_extras_router.py` e ja foi confirmada no aparelho.

POR QUE AQUI, E NAO NO CALLBACK DO LVGL
    A Core 3.2 chamou a navegacao de dentro do callback do LVGL e travou
    o aparelho: a navegacao roda noutra task. Este patch fica DENTRO do
    handler da APP, que ja e a task certa -- o mesmo lugar onde o
    firmware de fabrica abre as paginas.

O QUE O HANDLER DE FABRICA FAZ  (0x00D0CC7C, medido)

    ldrh r2, [r4, #0xc]     ; indice do item
    cmp  r2, #2
    bhi  #0x00D0CD6E        ; > 2 -> retorno limpo      <<< O LIMITE
    ...
    ldrh r5, [r4, #0xc]
    cmp  r5, #1 / beq / blo / cmp #2 / beq   ; despacho de TRES

    E cada caso abre a pagina assim (indice 0, o mais simples):

        movs r3, #0x1e          ; pagina destino (Alarme)
        movs r2, #0             ; sub
        ldrh r1, [r4, #0xa]     ; r1 vem DA MENSAGEM, nao e literal
        ldrh r0, [r4, #8]       ; r0 = pagina corrente, DA MENSAGEM
        pop.w {r4,r5,r6,r7,r8,lr}
        b.w  #0x00D0DAE0

    Confirmado no aparelho em 17/09: o item 1 do Extras abria o Alarme,
    que e exatamente a pagina 0x1E deste caso.

O QUE ESTE PATCH FAZ
    1. Troca 4 bytes em 0x00D0CC7E (`cmp r2,#2` + `bhi`) por um `b.w`.
    2. Instala em 0x00DA6200 um despacho de SEIS, com a MESMA convencao
       medida acima, incluindo a checagem de cartao e a mensagem de
       "sem cartao" de fabrica (0x00D0CCC2).

USO
    python3 tools/patch_extras_app.py \
        firmware/WORKING/GN438_core_3.3_carimbado.bin \
        firmware/WORKING/GN438_core_3.4_sem_versao.bin

LIMITACOES
    - Feito para uma imagem que ja tenha o roteador da 3.3.
    - Nao recalcula CRC (politica do projeto).
"""
import sys

BASE_XIP  = 0x00C00000
APP_ROUTER = 0x00DA6200          # mesma area livre, depois do roteador LVGL
HOOK       = 0x00D0CC7E          # cmp r2,#2 / bhi  -> 4 bytes
ABRE_PAG   = 0x00D0DAE0          # primitiva (chamada da task certa)
SEM_CARTAO = 0x00D0CCC2          # movs r0,#0x2f ; mostra "sem cartao"
RETORNO    = 0x00D0CD6E          # pop.w {r4,r5,r6,r7,r8,pc}
CHECA_CART = 0x00CFE714

# indice na tela -> (pagina, precisa de cartao, nome, view)
DESTINOS = [
    (0x18, 1, "Gravacao",      "page_record_menu"),
    (0x1A, 0, "Radio",         "page_fm_play"),
    (0x0C, 1, "Livro digital", "page_ebook_list"),
    (0x15, 1, "Imagem",        "page_pict_list"),
    (0x23, 0, "Bluetooth",     "page_bt_menu_option"),
    (0x22, 1, "Pastas",        "page_folder_list"),
]


def bl(origem, destino):
    off = destino - (origem + 4)
    assert -(1 << 24) <= off < (1 << 24) and off % 2 == 0, "BL fora de alcance"
    off >>= 1
    s = (off >> 23) & 1
    i1, i2 = (off >> 22) & 1, (off >> 21) & 1
    w1 = 0xF000 | (s << 10) | ((off >> 11) & 0x3FF)
    w2 = 0xD000 | (((~i1 & 1) ^ s) << 13) | (((~i2 & 1) ^ s) << 11) | (off & 0x7FF)
    return w1.to_bytes(2, "little") + w2.to_bytes(2, "little")


def bw(origem, destino):
    b = bytearray(bl(origem, destino))
    b[3] &= ~0x40
    return bytes(b)


def montar():
    c = bytearray()
    def h(v): c.extend(v.to_bytes(2, "little"))
    A = APP_ROUTER

    h(0x89A2)                          # 0x00  ldrh r2, [r4, #0xc]   indice
    h(0x2A06)                          # 0x02  cmp  r2, #6
    h(0xD213)                          # 0x04  bhs  FIM (0x2e)
    h(0x4615)                          # 0x06  mov  r5, r2           (sobrevive ao bl)
    h(0x4B0A)                          # 0x08  ldr  r3, [pc,#0x28] -> &TAB_CHK
    h(0x5C9B)                          # 0x0A  ldrb r3, [r3, r2]
    h(0x2B00)                          # 0x0C  cmp  r3, #0
    h(0xD003)                          # 0x0E  beq  ABRE (0x18)
    c += bl(A + 0x10, CHECA_CART)      # 0x10  bl   checa cartao
    h(0x2800)                          # 0x14  cmp  r0, #0
    h(0xD008)                          # 0x16  beq  SEMCARTAO (0x2a)
    # ABRE (0x18) — convencao medida em 0x00D0CCAC
    h(0x4B07)                          # 0x18  ldr  r3, [pc,#0x1c] -> &TAB_PAG
    h(0x5D5B)                          # 0x1A  ldrb r3, [r3, r5]     pagina destino
    h(0x2200)                          # 0x1C  movs r2, #0           sub
    h(0x8961)                          # 0x1E  ldrh r1, [r4, #0xa]   da mensagem
    h(0x8920)                          # 0x20  ldrh r0, [r4, #8]     da mensagem
    c += bytes.fromhex("bde8f041")     # 0x22  pop.w {r4,r5,r6,r7,r8,lr}
    c += bw(A + 0x26, ABRE_PAG)        # 0x26  b.w  abrir pagina
    c += bw(A + 0x2A, SEM_CARTAO)      # 0x2A  SEMCARTAO
    c += bw(A + 0x2E, RETORNO)         # 0x2E  FIM
    h(0xBF00)                          # 0x32  nop (alinha)
    assert len(c) == 0x34, hex(len(c))
    c += (A + 0x3C).to_bytes(4, "little")   # 0x34 -> &TAB_CHK
    c += (A + 0x42).to_bytes(4, "little")   # 0x38 -> &TAB_PAG
    c += bytes(chk for _, chk, _, _ in DESTINOS)   # 0x3C
    c += bytes(pg for pg, _, _, _ in DESTINOS)     # 0x42
    assert len(c) == 0x48, hex(len(c))
    return bytes(c)


def main():
    if len(sys.argv) != 3:
        sys.exit("uso: patch_extras_app.py <entrada.bin> <saida.bin>")
    img = bytearray(open(sys.argv[1], "rb").read())
    if len(img) != 2 * 1024 * 1024:
        sys.exit("erro: esperava 2 MiB")
    # exige o roteador da 3.3 ja instalado
    if img[0x001A6000:0x001A6004] != bytes.fromhex("002254f8"):
        sys.exit("erro: o roteador LVGL da Core 3.3 nao esta na imagem")

    off = APP_ROUTER - BASE_XIP
    cod = montar()
    if any(b != 0xFF for b in img[off:off + len(cod)]):
        sys.exit(f"erro: {APP_ROUTER:#x} nao esta apagado")
    img[off:off + len(cod)] = cod
    oh = HOOK - BASE_XIP
    img[oh:oh + 4] = bw(HOOK, APP_ROUTER)
    open(sys.argv[2], "wb").write(img)

    print(f"despacho APP  {APP_ROUTER:#010x}  {len(cod)} bytes")
    print(f"gancho        {HOOK:#010x}  4 bytes (cmp r2,#2 / bhi)")
    print(f"  despacho de 3 -> 6 indices\n")
    for i, (pg, chk, nome, view) in enumerate(DESTINOS):
        print(f"  {i}  {nome:<14} -> pagina {pg:#04x}  {view}"
              f"{'   (checa cartao)' if chk else ''}")
    print(f"\nescrito: {sys.argv[2]}")


if __name__ == "__main__":
    main()
