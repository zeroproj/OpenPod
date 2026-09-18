#!/usr/bin/env python3
"""
gera_versao.py — de uma imagem para os DOIS release, numa passada so.

O PROBLEMA QUE RESOLVE
    O projeto tem dois lugares de release, e ate hoje eles divergiam:

        firmware/RELEASE/<versao>/   kit interno, um por versao, o
                                     historico de tudo que foi gravado
        release/<versao>/            o pacote publico, o que vai para
                                     o GitHub e para o usuario

    A Beta 2 foi gerada direto no publico e nunca teve kit interno. Isso
    quebra a cadeia: a versao que esta no ar nao aparece no historico.

    Aqui o publico e DERIVADO do interno -- mesmos setores, mesmos
    hashes -- em vez de ser um irmao gerado a parte.

O QUE FAZ

    imagem .bin
        |
        +-- make_install_kit.py ----> firmware/RELEASE/<versao>/
        |                              kit de setores + flash + diag
        |
        +-- bilingue_kit.py --------> script de gravacao EN/pt-BR
        +-- docs/pacote/* ----------> install.sh, README, LEIA-ME
        +-- organiza_pacote.py -----> release/<versao>/
                                       cabo/setores/, windows/, .up

    E confere, no fim: o .up bate com todos os setores, a PSMP fica
    fora, o bootloader e o de fabrica, e o ORIGINAL nao foi tocado.

USO
    python3 tools/gera_versao.py \\
        --imagem   firmware/WORKING/GN438_beta3_carimbado.bin \\
        --versao   OpenPod-Core-5.7-Public-Beta-3 \\
        --nome-tela "OpenPod 5.7 Beta 3"

    --base      o que o aparelho TEM antes (padrao: o ORIGINAL de fabrica)
    --refazer   sobrescreve um <versao>/ que ja exista

DEPOIS
    python3 tools/publica_release.py --versao <versao> --push

DEPENDENCIAS
    tools/make_install_kit.py, bilingue_kit.py, organiza_pacote.py
    docs/pacote/  -- os modelos de install.sh, README.md e LEIA-ME.txt

LIMITACOES
    Nao carimba a versao na imagem. Isso e do patch_versao.py, e vem
    antes -- a imagem ja tem que chegar aqui com o nome certo na tela.
"""
import argparse
import glob
import hashlib
import os
import re
import shutil
import struct
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = "firmware/ORIGINAL/GN438_original.bin"
SHA_ORIGINAL = "b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f"
PSMP = 0x1FC000
BOOT = 0xD000
EXE = "FlashloaderSL-DEV-6.9.5.exe"


def sh(*a):
    return subprocess.run(a, cwd=RAIZ, capture_output=True, text=True)


def parar(msg):
    sys.exit("ABORTADO: " + msg)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def crc16(b):
    c = 0xFFFF
    for x in b:
        c ^= x << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) & 0xFFFF if c & 0x8000 else (c << 1) & 0xFFFF
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--imagem", required=True)
    ap.add_argument("--versao", required=True,
                    help="ex: OpenPod-Core-5.7-Public-Beta-3")
    ap.add_argument("--nome-tela", required=True,
                    help="o que a tela Informacao mostra, ex 'OpenPod 5.7 Beta 3'")
    ap.add_argument("--base", default=ORIGINAL)
    ap.add_argument("--refazer", action="store_true")
    a = ap.parse_args()

    # --- o original e sagrado: confere antes de qualquer coisa -------
    if sha(os.path.join(RAIZ, ORIGINAL)) != SHA_ORIGINAL:
        parar("o firmware ORIGINAL nao confere com o SHA-256 conhecido. PARE.")
    print("original: SHA-256 confere")

    if not os.path.isfile(os.path.join(RAIZ, a.imagem)):
        parar("nao achei %s" % a.imagem)

    curto = a.versao.replace("OpenPod-Core-", "").replace("-", " ")   # "5.7 Public Beta 3"
    beta = re.sub(r".*?(Beta\s*\d+).*", r"\1", curto) or "Beta"        # "Beta 3"
    up = "OpenPod_" + beta.replace(" ", "")                            # "OpenPod_Beta3"

    interno = os.path.join(RAIZ, "firmware", "RELEASE", a.versao.replace("-", " "))
    publico = os.path.join(RAIZ, "release", a.versao)
    for d in (interno, publico):
        if os.path.isdir(d):
            if not a.refazer:
                parar("%s ja existe. Use --refazer para sobrescrever." % d)
            shutil.rmtree(d)

    # --- 1. kit interno ----------------------------------------------
    print("\n[1/4] kit interno -> firmware/RELEASE/%s" % os.path.basename(interno))
    r = sh(sys.executable, "tools/make_install_kit.py",
           "--base", a.base, "--alvo", a.imagem, "--origem", ORIGINAL,
           "--versao", up, "--saida", interno, "--sem-carimbo",
           "--descricao", "OpenPod %s" % curto)
    if r.returncode:
        parar("make_install_kit falhou:\n" + r.stdout[-2000:] + r.stderr[-2000:])
    setores = sorted(glob.glob(os.path.join(interno, "%s_*.bin" % up)))
    print("      %d setores, %d arquivos" % (len(setores), len(os.listdir(interno))))

    # --- 2. pacote publico, derivado do interno ----------------------
    print("[2/4] pacote publico -> release/%s" % a.versao)
    os.makedirs(os.path.join(publico, "cabo", "setores"))
    os.makedirs(os.path.join(publico, "windows"))
    for f in glob.glob(os.path.join(interno, "*.bin")):
        shutil.copy2(f, os.path.join(publico, "cabo", "setores"))
    shutil.copy2(os.path.join(interno, "%s.up" % up), publico)

    flash = os.path.join(interno, "flash_%s.sh" % up)
    r = sh(sys.executable, "tools/bilingue_kit.py", flash,
           os.path.join(publico, "cabo", "flash_%s.sh" % up))
    if r.returncode:
        parar("bilingue_kit falhou:\n" + r.stdout + r.stderr)
    print("      " + r.stdout.strip())

    # o script tem que entrar na propria pasta de setores -- mesmo ajuste
    # que o organiza_pacote faz quando arruma um pacote plano.
    sys.path.insert(0, os.path.join(RAIZ, "tools"))
    import organiza_pacote
    organiza_pacote.ajusta_flash(os.path.join(publico, "cabo", "flash_%s.sh" % up))
    print("      script ajustado para achar setores/")

    # os modelos, com a versao preenchida
    subs = {"{UP}": up, "{TELA}": a.nome_tela, "{CURTO}": curto, "{BETA}": beta}
    for src, dst, nl in [("docs/pacote/install.sh", "install.sh", "\n"),
                         ("docs/pacote/README.md", "README.md", "\n"),
                         ("docs/pacote/windows/LEIA-ME.txt", "windows/LEIA-ME.txt", "")]:
        p = os.path.join(RAIZ, src)
        if not os.path.isfile(p):
            parar("falta o modelo %s" % src)
        t = open(p, encoding="utf-8", newline=nl if nl else "").read()
        for k, v in subs.items():
            t = t.replace(k, v)
        if "{" in re.sub(r"\{[^A-Z}]", "", t) and re.search(r"\{[A-Z]+\}", t):
            parar("sobrou marcador nao substituido em %s" % src)
        d = os.path.join(publico, dst)
        open(d, "w", encoding="utf-8", newline=nl if nl else "").write(t)
        os.chmod(d, 0o755) if dst.endswith(".sh") else None
    os.chmod(os.path.join(publico, "cabo", "flash_%s.sh" % up), 0o755)

    exe = os.path.join(RAIZ, "firmware", "VENDOR", EXE)
    if os.path.isfile(exe):
        shutil.copy2(exe, os.path.join(publico, "windows", EXE))
        print("      Flashloader incluido (fica fora do git)")
    else:
        print("      AVISO: %s nao esta em firmware/VENDOR/" % EXE)

    # --- 3. arrumar o pacote -----------------------------------------
    print("[3/4] arrumando")
    r = sh(sys.executable, "tools/organiza_pacote.py", "release/" + a.versao, "--conferir")
    if r.returncode:
        # ainda plano? o organiza espera setores/ na raiz; aqui ja montamos
        parar("organiza_pacote reprovou:\n" + r.stdout + r.stderr)
    print("      " + r.stdout.strip().replace("\n", "\n      "))

    # --- 4. conferencia final ----------------------------------------
    print("[4/4] conferindo")
    d = open(os.path.join(publico, "%s.up" % up), "rb").read()
    off = struct.unpack_from("<I", d, 6)[0]
    tam = struct.unpack_from("<I", d, 0x10)[0]
    crc = struct.unpack_from("<H", d, 0x14)[0]
    pay = d[off:off + tam]
    orig = open(os.path.join(RAIZ, ORIGINAL), "rb").read()

    falhas = []
    if d[0:6] != b"CONFIG" or d[0x16:0x1C] != b"SL6801":
        falhas.append("cabecalho do .up")
    if crc16(pay) != crc:
        falhas.append("CRC do .up")
    if tam > PSMP:
        falhas.append("a cobertura alcanca a PSMP")
    if pay[:BOOT] != orig[:BOOT]:
        falhas.append("o bootloader dentro do .up difere do de fabrica")
    mal = 0
    for f in glob.glob(os.path.join(publico, "cabo", "setores", "%s_*.bin" % up)):
        end = int(re.search(r"_([0-9A-F]+)\.bin$", os.path.basename(f)).group(1), 16)
        s = open(f, "rb").read()
        if pay[end:end + len(s)] != s:
            mal += 1
    if mal:
        falhas.append("%d setores nao batem com o .up" % mal)
    if sha(os.path.join(RAIZ, ORIGINAL)) != SHA_ORIGINAL:
        falhas.append("o ORIGINAL foi alterado durante a geracao")

    n = len(glob.glob(os.path.join(publico, "cabo", "setores", "%s_*.bin" % up)))
    print("      CRC 0x%04X confere · cobertura 0x%X · PSMP fora · %d setores batem"
          % (crc, tam, n))
    if falhas:
        parar("\n  - " + "\n  - ".join(falhas))

    print("\nPRONTO")
    print("  interno: firmware/RELEASE/%s" % os.path.basename(interno))
    print("  publico: release/%s" % a.versao)
    print("\n  publicar:  python3 tools/publica_release.py --versao %s --nome-tela %r --push"
          % (a.versao, a.nome_tela))
    return 0


if __name__ == "__main__":
    sys.exit(main())
