#!/usr/bin/env python3
"""
patch_faixa_alinha.py — relogio, titulo e bateria na mesma linha,
                        e a casca da bateria realmente prateada

DOIS DEFEITOS, MEDIDOS EM 2026-09-18 A PARTIR DA FOTO DA Core 5.4

1. O ALINHAMENTO
       relogio  0x00D217D6  movs r3, #2   ; y_ofs = 2  (align TOP_LEFT)
       titulo   0x00D226B6  movs r3, #2   ; y_ofs = 2  (align TOP_RIGHT)
       bateria  0x00D22614  set_pos(107, 0)            ; y = 0 absoluto

   Sao 2 px de diferenca. Mantenedor: "a hora, OpenPod e bateria nao
   estao alinhados; bateria ta centralizado mas a hora e OpenPod nao".

   Os dois y_ofs viram 0, igualando a bateria.

2. A COR DA CASCA — por que a Core 5.3 nao teve efeito
       A 5.3 pintou a casca na CRIACAO do objeto. Mas
       `view_set_icon_bat` (0x00D2361C) REPINTA em tempo de execucao,
       toda vez que o nivel muda:

           <= 10%   mov.w r1, #0xf8     -> vermelho (pre-invertido)
           senao    mov.w r1, #-1       -> BRANCO   <- apagava o prateado

       O sitio certo e 0x00D23686, o ramo "senao".

       Licao: pintar na criacao nao basta quando existe um atualizador.
       A pergunta que faltou foi a mesma do V016: **quem MAIS escreve
       neste slot?**

USO
    python3 tools/patch_faixa_alinha.py entrada.bin saida.bin
    python3 tools/patch_faixa_alinha.py entrada.bin saida.bin --y 1

LIMITACOES
    - A bateria fraca continua vermelha, e deve continuar.
    - `--y` permite 0, 1 ou 2, caso 0 fique alto demais na tela.
"""
import argparse
import sys

BASE_XIP = 0x00C00000
MARTE = (197, 206, 213)

ALINHA = [
    (0x00D217D6, "0223", "relogio  y_ofs"),
    (0x00D226B6, "0223", "titulo   y_ofs"),
]
# TODOS os sitios que pintam a casca de BRANCO. Sao CINCO, nao um.
# A Core 5.3 pintou na criacao (apagado pelo atualizador) e a 5.5
# pegou so 0x00D23686. A pergunta que faltou, pela TERCEIRA vez neste
# mesmo icone: "quem MAIS escreve neste slot?"
# Os dois sitios de vermelho (0x00D23674 e 0x00D23876) NAO sao tocados:
# bateria fraca deve continuar vermelha.
BRANCO = bytes.fromhex("4ff0ff31")          # mov.w r1, #-1
COR_RUNTIME = [0x00D23686, 0x00D236CA, 0x00D238E8, 0x00D23912]

# 0x00D236B0 fica FORA, e o motivo e instrutivo:
#
#     bytes          4f f0 ff 31
#     lido de 0xB0   mov.w r1, #-1       <- caminho de queda
#     lido de 0xB2   adds  r1, #0xff     <- TRES `bpl` saltam para ca
#
# Sao INSTRUCOES SOBREPOSTAS: os mesmos bytes servem a dois caminhos,
# um entrando no meio do outro. Trocar por `movw` faria o caminho B
# executar `movs r1,#0xc6` em vez de `adds r1,#0xff`.
#
# Quem pegou isso foi tools/check_branch_targets.py, com
# "3 desvios apontam para alvo DESTRUIDO". A desmontagem linear nao
# pega: ela le so um dos dois alinhamentos.


def to565(r, g, b):
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


def pre_inverte(v):
    return ((v & 0xFF) << 8) | (v >> 8)


def movw(rd, valor):
    imm4, i = (valor >> 12) & 0xF, (valor >> 11) & 1
    imm3, imm8 = (valor >> 8) & 7, valor & 0xFF
    return ((0xF240 | (i << 10) | imm4).to_bytes(2, "little")
            + ((imm3 << 12) | (rd << 8) | imm8).to_bytes(2, "little"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("saida")
    ap.add_argument("--y", type=int, default=0, choices=(0, 1, 2))
    a = ap.parse_args()

    img = bytearray(open(a.entrada, "rb").read())
    if len(img) != 2 * 1024 * 1024:
        sys.exit("erro: esperava 2 MiB")

    for addr, antes, texto in ALINHA:
        off = addr - BASE_XIP
        if img[off:off + 2].hex() != antes:
            sys.exit(f"erro: {addr:#x} tem {img[off:off+2].hex()}, esperava {antes}")
        img[off] = a.y                      # `movs r3,#N` — o N e o byte baixo
        print(f"  {addr:#010x}  {texto}: 2 -> {a.y}")

    cor = pre_inverte(to565(*MARTE))
    novo = movw(1, cor)
    for addr in COR_RUNTIME:
        off = addr - BASE_XIP
        atual = bytes(img[off:off + 4])
        if atual == novo:
            print(f"  {addr:#010x}  casca: ja estava prateado")
            continue
        if atual != BRANCO:
            sys.exit(f"erro: {addr:#x} tem {atual.hex()}, "
                     f"esperava {BRANCO.hex()} (mov.w r1,#-1)")
        img[off:off + 4] = novo
        print(f"  {addr:#010x}  casca: branco -> movw r1, #{cor:#06x}")
    print(f"     RGB{MARTE} — o prateado do Marte, em {len(COR_RUNTIME)} sitios")

    open(a.saida, "wb").write(img)
    print(f"\n  escrito: {a.saida}")


if __name__ == "__main__":
    main()
