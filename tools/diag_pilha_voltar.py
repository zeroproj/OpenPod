#!/usr/bin/env python3
"""
diag_pilha_voltar.py — INSTRUMENTACAO, nao conserto

PERGUNTA QUE ELE RESPONDE
    Por que o voltar de um item do Extras vai para a tela inicial?
    Ha tres explicacoes possiveis e nenhuma foi medida:

      A. a pilha de navegacao esta VAZIA no momento do voltar
      B. a pilha tem 0x53, mas outra coisa sobrescreve o destino
      C. o voltar nao passa por este desempilhador

COMO ELE RESPONDE, COM UM BYTE
    0x00D0DAB0 e o ramo "pilha vazia" de 0x00D0DA64:

        movs r5, #1        ; devolve 1 = a tela inicial

    Trocando o 1 por 0x28 (Configurar), o voltar de pilha vazia passa a
    cair numa tela INCONFUNDIVEL. Entao, ao voltar de um item do Extras:

        cai em CONFIGURAR  -> a pilha estava vazia          (hipotese A)
        cai no EXTRAS      -> a pilha tinha 0x53 e funcionou (hipotese B)
        cai na TELA INICIAL-> o voltar nem passa por aqui    (hipotese C)

    Tres respostas, tres telas, uma gravacao.

ATENCAO
    Esta imagem e de DIAGNOSTICO. Enquanto ela estiver gravada, TODO
    voltar que encontre a pilha vazia vai para Configurar em vez da tela
    inicial -- inclusive os legitimos. E o preco da medicao, e e
    reversivel: volte para a 4.4.

USO
    python3 tools/diag_pilha_voltar.py entrada.bin saida.bin
    python3 tools/diag_pilha_voltar.py entrada.bin saida.bin --pagina 0x23
"""
import argparse
import sys

BASE_XIP = 0x00C00000
# dois sitios, duas perguntas diferentes
SITIOS = {
    # ramo "pilha vazia": so dispara quando a pilha esta vazia
    "vazia":  (0x00D0DAB0, bytes.fromhex("0125"), "movs r5, #1",
               lambda pg: bytes([pg, 0x25])),
    # a saida COMUM do desempilhador: dispara sempre que o pop roda
    "sempre": (0x00D0DAAC, bytes.fromhex("2846"), "mov  r0, r5",
               lambda pg: bytes([pg, 0x20])),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("saida")
    ap.add_argument("--pagina", type=lambda s: int(s, 0), default=0x28,
                    help="pagina de diagnostico (padrao 0x28 = Configurar)")
    ap.add_argument("--sitio", choices=sorted(SITIOS), default="vazia",
                    help="'vazia' = so quando a pilha estiver vazia; "
                         "'sempre' = em toda saida do desempilhador")
    a = ap.parse_args()

    img = bytearray(open(a.entrada, "rb").read())
    if len(img) != 2 * 1024 * 1024:
        sys.exit("erro: esperava 2 MiB")
    sitio, esperado, texto, monta = SITIOS[a.sitio]
    off = sitio - BASE_XIP
    if bytes(img[off:off + 2]) != esperado:
        sys.exit(f"erro: {sitio:#x} nao tem `{texto}` "
                 f"(achei {img[off:off+2].hex()}) — imagem errada?")
    if not 0 < a.pagina <= 0x53:
        sys.exit("erro: pagina fora da faixa 1..0x53")

    img[off:off + 2] = monta(a.pagina)
    open(a.saida, "wb").write(img)
    quando = ("com a pilha VAZIA" if a.sitio == "vazia"
              else "SEMPRE que o desempilhador rodar")
    print(f"  {sitio:#010x}  {texto}  ->  devolve {a.pagina:#04x}")
    print(f"\n  o voltar vai para a pagina {a.pagina:#04x} {quando}")
    print(f"  escrito: {a.saida}")


if __name__ == "__main__":
    main()
