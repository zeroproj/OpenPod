#!/usr/bin/env python3
"""
patch_fundo_display.py — o fundo do display deixa de ser BRANCO.

O DEFEITO

    A "faixa clara" esta aberta desde a 2.0: uma tira clara sob o titulo,
    que nao se move e a qual nao se consegue navegar. Ja descartei
    heranca de tema, linha vazia e barra de rolagem.

A CAUSA PROVAVEL

    Em `lv_disp_drv_register`, imediatamente antes de criar as telas:

        0x001567F6   movs   r3, #0xff
        0x001567F8   strb.w r3, [r4, #0x29]
        0x001567FC   strb.w r3, [r4, #0x2a]
        0x00156800   strb.w r3, [r4, #0x2b]
        0x00156804   movs   r0, #0
        0x00156806   bl     0x00D491EC        <- cria a tela

    Tres bytes 0xFF num `lv_disp_t`, logo antes das telas. E o padrao do
    LVGL v8:

        disp->bg_color = lv_color_white();
        disp->bg_opa   = LV_OPA_COVER;

    **O fundo do display e branco.** E nenhuma pagina pinta o fundo da
    tela: quem pinta e a faixa e o conteiner. Entao toda regiao que esses
    dois nao cobrem mostra o branco do display — nas listas, a fresta
    entre o fim da faixa (y=17) e o inicio do conteiner (y=19).

O QUE ESTE PATCH E

    **Um experimento de 1 byte**, nao a correcao definitiva:

        movs r3, #0xff   ->   movs r3, #0x00

    Se a faixa clara ficar preta, a hipotese esta provada. Se continuar
    clara, a hipotese cai — e isso tambem e resposta.

POR QUE NAO E A CORRECAO DEFINITIVA

    O certo e o fundo do display **ler `cor_tela`** da tabela do Saturno.
    Hoje esse campo tem UM unico leitor (o thunk do S12, pagina 0x18) —
    e praticamente morto. Liga-lo aqui e o que o Projeto Marte vai
    precisar para o tema claro.

    Mas isso e mudanca de projeto, e primeiro convem saber se a hipotese
    se sustenta. Um byte responde.

USO
    python3 tools/patch_fundo_display.py \\
        --in  firmware/WORKING/GN438_openpod_v074.bin \\
        --out firmware/WORKING/GN438_openpod_v075.bin [--dry-run]
    (--cor 0xNN para experimentar outro valor)

SEGURANCA
    - exige a sequencia inteira (movs + tres strb + o bl que cria a tela);
      se qualquer parte nao bater, RECUSA — nao altera constante solta;
    - recusa diferenca abaixo de 0x00E000 (R1); nao toca no CRC.
"""

import argparse
import sys

XIP = 0x00C00000
FLASH_SIZE = 0x200000
ALVO = 0x001567F6
# movs r3,#0xff | strb.w r3,[r4,#0x29] | strb.w r3,[r4,#0x2a]
# strb.w r3,[r4,#0x2b] | movs r0,#0
ESPERADO = bytes.fromhex("ff23" "84f82930" "84f82a30" "84f82b30" "0020")


def main():
    ap = argparse.ArgumentParser(description="fundo do display")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--cor", default="0x00",
                    help="valor do byte (padrao 0x00 = preto)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.src == a.dst:
        sys.exit("origem e destino iguais")
    orig = open(a.src, "rb").read()
    if len(orig) != FLASH_SIZE:
        sys.exit(f"tamanho inesperado: {len(orig)}")
    data = bytearray(orig)
    cor = int(a.cor, 0)
    if not 0 <= cor <= 0xFF:
        sys.exit("--cor fora de 0..255")

    achado = bytes(data[ALVO:ALVO + len(ESPERADO)])
    if achado != ESPERADO:
        print("RECUSADO: a sequencia do fundo do display nao confere")
        print(f"   esperado {ESPERADO.hex()}")
        print(f"   achei    {achado.hex()}")
        return 1

    print()
    print("  FUNDO DO DISPLAY — experimento de 1 byte")
    print()
    print("  lv_disp_drv_register, logo antes de criar as telas:")
    print(f"    0x{ALVO:06X}  movs r3, #0xff  ->  movs r3, #0x{cor:02X}")
    print("    os tres strb seguintes gravam esse valor em")
    print("    [r4,#0x29..0x2b] = bg_color + bg_opa do lv_disp_t")
    print()
    print("  Se a faixa clara ficar preta, a hipotese esta provada.")
    print("  Se continuar clara, a hipotese cai — e isso tambem e resposta.")
    print()
    data[ALVO] = cor

    dif = [i for i in range(len(orig)) if orig[i] != data[i]]
    if dif and min(dif) < 0x00E000:
        sys.exit(f"RECUSADO: tocaria 0x{min(dif):06X} (R1)")
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))
    print("  CRC da FIRM: campo intocado (R1)")
    print()
    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(data))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
