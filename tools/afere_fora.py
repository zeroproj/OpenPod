#!/usr/bin/env python3
"""
afere_fora.py — MEDE se cada ferramenta excluida da receita ainda faz algo.

POR QUE ISTO EXISTE

    A lista `FORA` do `build.py` foi montada lendo a DESCRICAO de cada
    ferramenta, nao medindo o efeito. Isso ja falhou quatro vezes:

        patch_chrome_padrao    "superado pelo Saturno"  -> era PRE-REQUISITO
        patch_cor_texto_lista  "superado pelo S10"      -> era PRE-REQUISITO
        patch_status_bar       "superado pelo Saturno"  -> escreve "OpenPod",
        fix_status_bar          idem                       usada no BOOT e no
                                                           titulo da home

    A 3.0 saiu sem o "OpenPod" no boot e sem titulo na home por causa
    disso. Suposicao nao e medicao.

O QUE FAZ

    Aplica cada ferramenta de `FORA` sobre a imagem construida e conta
    quantos bytes mudam. O resultado classifica sozinho:

        RECUSA      a ferramenta se nega — ja aplicada, ou incompativel
        0 bytes     nao faz nada aqui: e mesmo superada
        N bytes     AINDA FAZ ALGO. Nao pode ser descartada sem olhar.

USO
    python3 tools/afere_fora.py firmware/WORKING/GN438_openpod_v100.bin
"""

import os
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# argumentos obrigatorios de algumas ferramentas
EXTRA = {
    "patch_menu_text.py": ["--set", "pt:3=Vídeo"],
    "patch_versao.py": ["--texto", "teste"],
}


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    base = os.path.abspath(sys.argv[1])
    sys.path.insert(0, os.path.join(RAIZ, "tools"))
    import build                                            # noqa: E402

    orig = open(base, "rb").read()
    print()
    print("  AFERICAO DAS FERRAMENTAS FORA DA RECEITA")
    print(f"  base: {os.path.basename(base)}")
    print()
    print(f"  {'ferramenta':28s} {'efeito':>12s}  motivo declarado")
    ativas = []
    with tempfile.TemporaryDirectory() as t:
        for nome, motivo in build.FORA:
            cam = os.path.join(RAIZ, "tools", nome)
            if not os.path.exists(cam):
                print(f"  {nome:28s} {'(nao existe)':>12s}  {motivo}")
                continue
            out = os.path.join(t, nome + ".bin")
            r = subprocess.run(
                [sys.executable, cam, "--in", base, "--out", out]
                + EXTRA.get(nome, []),
                capture_output=True, text=True, cwd=RAIZ)
            if r.returncode or not os.path.exists(out):
                print(f"  {nome:28s} {'RECUSA':>12s}  {motivo}")
                continue
            novo = open(out, "rb").read()
            n = sum(1 for i in range(len(orig)) if orig[i] != novo[i])
            marca = f"{n} bytes" if n else "nada"
            print(f"  {nome:28s} {marca:>12s}  {motivo}")
            if n:
                ativas.append((nome, n, motivo))
    print()
    print(f"  AINDA FAZEM ALGO: {len(ativas)}")
    for nome, n, motivo in sorted(ativas, key=lambda x: -x[1]):
        print(f"     {nome:28s} {n:6d} bytes")
    print()
    print("  'nada' = de fato superada.  'RECUSA' = ja aplicada ou incompativel.")
    print("  O resto precisa ser OLHADO, nao descartado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
