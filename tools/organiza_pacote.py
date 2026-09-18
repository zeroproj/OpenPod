#!/usr/bin/env python3
"""
organiza_pacote.py — arruma um pacote de release do OpenPod.

O PROBLEMA
    O make_install_kit.py cospe tudo numa pasta so. Com 88 arquivos de
    setor no mesmo nivel do README, quem abre o pacote nao sabe por onde
    comecar.

O QUE FAZ
    De:                          Para:
      README.md                    README.md
      install.sh                   install.sh          <- Linux/macOS
      OpenPod_Beta1.up             OpenPod_Beta1.up
      flash_*.sh                   windows/            <- Windows
      88x *.bin                      LEIA-ME.txt
      windows/...                    *.exe
                                   cabo/
                                     flash_*.sh
                                     setores/  (88 .bin)

    E ajusta os dois scripts para acharem os arquivos no lugar novo:

      flash_*.sh   passa a entrar na propria pasta de setores, e guarda
                   os logs e dumps onde o usuario chamou o script
      install.sh   passa a chamar cabo/flash_*.sh

USO
    python3 tools/organiza_pacote.py release/OpenPod-Core-5.7-Public-Beta-1

    --conferir   so verifica um pacote ja arrumado, nao move nada

DEPENDENCIAS
    nenhuma (so a biblioteca padrao)

SEGURANCA
    - aborta se um dos ajustes de script nao casar (nao deixa pacote
      meio arrumado);
    - no fim, confere que TODO .bin citado pelos scripts existe no
      lugar onde o script vai procurar;
    - roda `sh -n` nos dois scripts.

LIMITACOES
    Nao mexe em hash, offset nem no .up. Se algum dia o gerador mudar
    as linhas que esta ferramenta ajusta, ela para e diz qual.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys


def ajusta_flash(p):
    s = open(p, encoding="utf-8").read()

    a = 'WORK="$(pwd)/openpod_flash_$VERSAO"'
    b = ('# Os setores moram ao lado deste script, em setores/. Entramos la\n'
         '# para os nomes de arquivo resolverem, mas os logs e os dumps ficam\n'
         '# onde o usuario chamou o script -- nao enterrados no pacote.\n'
         'ORIGEM="$(pwd)"\n'
         'DADOS="$(cd "$(dirname "$0")" && pwd)/setores"\n'
         '[ -d "$DADOS" ] || { echo "faltando: $DADOS"; exit 1; }\n'
         'cd "$DADOS" || exit 1\n'
         'WORK="$ORIGEM/openpod_flash_$VERSAO"')
    if s.count(a) != 1:
        sys.exit("ABORTADO: nao achei a linha do WORK em %s" % p)
    s = s.replace(a, b, 1)

    # as instrucoes de reversao que o die() imprime sao rodadas a mao
    a2 = 'log "$(m reversao)"'
    b2 = a2 + '\n        log "***   (de dentro de $DADOS)"'
    if s.count(a2) != 1:
        sys.exit("ABORTADO: nao achei a linha da reversao em %s" % p)
    s = s.replace(a2, b2, 1)

    open(p, "w", encoding="utf-8").write(s)


def ajusta_install(p, nome_flash):
    s = open(p, encoding="utf-8").read()
    trocas = [
        ('[ -f "$HERE/%s" ] ||' % nome_flash, '[ -f "$HERE/cabo/%s" ] ||' % nome_flash),
        ('sh "$HERE/%s" "$(dirname "$TOOL")"' % nome_flash,
         'sh "$HERE/cabo/%s" "$(dirname "$TOOL")"' % nome_flash),
        ("die \"$(t '%s is missing.' 'falta o %s.')\"" % (nome_flash, nome_flash),
         "die \"$(t 'cabo/%s is missing.' 'falta o cabo/%s.')\"" % (nome_flash, nome_flash)),
    ]
    for a, b in trocas:
        if s.count(a) != 1:
            sys.exit("ABORTADO: nao achei em %s:\n  %s" % (p, a))
        s = s.replace(a, b, 1)
    open(p, "w", encoding="utf-8").write(s)


def confere(raiz):
    problemas = []
    flash = None
    cabo = os.path.join(raiz, "cabo")
    for f in os.listdir(cabo) if os.path.isdir(cabo) else []:
        if f.startswith("flash_") and f.endswith(".sh"):
            flash = os.path.join(cabo, f)
    if not flash:
        return ["nao achei o flash_*.sh em cabo/"]

    s = open(flash, encoding="utf-8").read()
    setores = os.path.join(cabo, "setores")
    citados = set(re.findall(r'"([A-Za-z0-9_.]+\.bin)"', s))
    for nome in sorted(citados):
        if not os.path.isfile(os.path.join(setores, nome)):
            problemas.append("citado pelo script, ausente em setores/: %s" % nome)

    sobrando = {f for f in os.listdir(setores) if f.endswith(".bin")} - citados
    for nome in sorted(sobrando):
        problemas.append("em setores/ mas nao citado pelo script: %s" % nome)

    for sh in (os.path.join(raiz, "install.sh"), flash):
        r = subprocess.run(["sh", "-n", sh], capture_output=True, text=True)
        if r.returncode:
            problemas.append("sh -n falhou em %s: %s" % (sh, r.stderr.strip()))

    for exigido in ("README.md", "install.sh"):
        if not os.path.isfile(os.path.join(raiz, exigido)):
            problemas.append("faltando na raiz: %s" % exigido)

    n = len(citados)
    print("setores citados pelo script e presentes: %d" % (n - len(problemas)
                                                           if problemas else n))
    return problemas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raiz")
    ap.add_argument("--conferir", action="store_true")
    a = ap.parse_args()
    raiz = a.raiz.rstrip("/")

    if not a.conferir:
        cabo = os.path.join(raiz, "cabo")
        setores = os.path.join(cabo, "setores")
        os.makedirs(setores, exist_ok=True)

        nome_flash = None
        for f in sorted(os.listdir(raiz)):
            o = os.path.join(raiz, f)
            if not os.path.isfile(o):
                continue
            if f.endswith(".bin"):
                shutil.move(o, os.path.join(setores, f))
            elif f.startswith("flash_") and f.endswith(".sh"):
                nome_flash = f
                shutil.move(o, os.path.join(cabo, f))
        if not nome_flash:
            sys.exit("ABORTADO: nao achei flash_*.sh na raiz de %s" % raiz)

        ajusta_flash(os.path.join(cabo, nome_flash))
        ajusta_install(os.path.join(raiz, "install.sh"), nome_flash)
        print("arrumado: %s" % raiz)

    problemas = confere(raiz)
    if problemas:
        print("\nPROBLEMAS:")
        for p in problemas:
            print("  " + p)
        return 1
    print("pacote conferido: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
