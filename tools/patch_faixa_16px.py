#!/usr/bin/env python3
"""
patch_faixa_16px.py — a faixa superior fica com 16 px em TODAS as telas

O PROBLEMA, medido em 2026-09-18
    As 53 telas que criam a faixa nao concordam sobre a altura dela:

        divisor 10  ->  160/10 = 16 px      25 telas
        divisor  7  ->  160/7  = 22 px      22 telas   <- o desvio
        altura fixa 16                       1 tela    <- a home
        sem divisor identificado              5 telas

    A Core 2.2 padronizou as LINHAS de 7 para 10, em 54 pontos, e deixou
    a FAIXA de 22 telas no 7.

    Isso se soma a bateria, que e posicionada FIXA em y = 0:

        0x00D22614  bl #0x00D4A2D4    ; set_pos(obj, 107, 0)

    Numa faixa de 16 px o glifo de 13 px fica quase centrado. Numa de
    22 px sobram 9 px embaixo e ele fica colado no topo.

    Mantenedor: "a barra degrade ta diferente do menu iniciar para o
    restante das paginas, e no restante das paginas ta muito desalinhado
    o icone da bateria. Ou afina tudo igual da home ou coloca a da home
    igual do restante."

    Escolhido: **afinar tudo para 16 px**, que e o que a home ja usa e o
    que o resto do sistema calcula. O nanoclone.json pede 18.

COMO
    Para cada `bl CRIA_FAIXA` (0x00D216F0), procura nos 0x40 bytes
    seguintes um `movs rX, #7` que alimente um `sdiv` cujo resultado vai
    para `set_height` (0x00D4A1EA). So esses sao trocados por #10.

    E dado: 1 byte por tela. Mesma classe do patch da Core 2.2.

USO
    python3 tools/patch_faixa_16px.py entrada.bin saida.bin
    python3 tools/patch_faixa_16px.py entrada.bin saida.bin --listar

LIMITACOES
    - As 5 telas "sem divisor identificado" nao sao tocadas: o padrao
      delas nao foi reconhecido, e a ferramenta prefere recusar a chutar.
    - Nao mexe na posicao da bateria. Com a faixa em 16 px ela para de
      parecer desalinhada, mas continua em y = 0.
"""
import argparse
import sys

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
except ImportError:
    sys.exit("erro: falta capstone.  pip install capstone")

BASE_XIP   = 0x00C00000
CRIA_FAIXA = 0x00D216F0
# a altura chega por set_height OU por set_size (w,h) — as duas formas existem
ALTURA     = (0x00D4A1EA, 0x00D4A21A)
FIRM_INI, FIRM_FIM = 0x0000E000, 0x001A0570
NOVO = 10


def acha_sitios(img):
    """Devolve [(offset_do_byte, endereco_da_instrucao, tela)] a trocar."""
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    achados = []
    for off in range(FIRM_INI, FIRM_FIM, 2):
        ins = next(md.disasm(img[off:off + 4], off + BASE_XIP), None)
        if ins is None or ins.mnemonic not in ("bl", "b.w"):
            continue
        if ins.op_str != f"#{CRIA_FAIXA:#x}":
            continue
        janela = list(md.disasm(img[off:off + 0x40], off + BASE_XIP))
        for k, j in enumerate(janela):
            if j.mnemonic != "movs" or "#" not in j.op_str:
                continue
            try:
                v = int(j.op_str.split("#")[1], 16)
            except ValueError:
                continue
            if v != 7:
                continue
            seguintes = janela[k:k + 8]
            tem_div = any(x.mnemonic == "sdiv" for x in seguintes)
            tem_alt = any(x.op_str in (f"#{h:#x}" for h in ALTURA)
                          for x in seguintes)
            if tem_div and tem_alt:
                # `movs rX,#7` = 0x20NN|7 ; o 7 e o byte BAIXO
                achados.append((j.address - BASE_XIP, j.address, off + BASE_XIP))
                break
    return achados


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("saida", nargs="?")
    ap.add_argument("--listar", action="store_true")
    a = ap.parse_args()

    img = bytearray(open(a.entrada, "rb").read())
    if len(img) != 2 * 1024 * 1024:
        sys.exit("erro: esperava 2 MiB")

    sitios = acha_sitios(img)
    print(f"  telas com faixa de 160/7 = 22 px: {len(sitios)}")
    if a.listar or not a.saida:
        for off, addr, tela in sitios:
            print(f"    {addr:#010x}  (CRIA_FAIXA em {tela:#010x})")
        if not a.saida:
            return

    for off, addr, _ in sitios:
        if img[off] != 7:
            sys.exit(f"erro: {addr:#x} tem {img[off]:#04x}, esperava 0x07")
        img[off] = NOVO
    open(a.saida, "wb").write(img)
    print(f"\n  {len(sitios)} bytes trocados: 7 -> {NOVO}")
    print(f"  a faixa passa a ser 160/{NOVO} = {160//NOVO} px em todas elas")
    print(f"  escrito: {a.saida}")


if __name__ == "__main__":
    main()
