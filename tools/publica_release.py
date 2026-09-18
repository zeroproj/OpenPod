#!/usr/bin/env python3
"""
publica_release.py — publica uma versao no repositorio publico.

O QUE E O REPOSITORIO PUBLICO
    github.com/zeroproj/OpenPod expoe SO duas coisas:

        index.html + .nojekyll     a pagina (GitHub Pages, servida da raiz)
        release/<versao>/          os binarios de atualizacao

    O codigo-fonte, a analise e o historico de engenharia reversa NAO
    sao publicos. O branch publico e orfao: um commit, sem historico.

O QUE ESTA FERRAMENTA FAZ
    1. confere que a versao existe e passa no organiza_pacote --conferir;
    2. atualiza a versao citada na pagina e no README publico;
    3. monta o branch publico DENTRO DE UM WORKTREE separado
       -- nunca toca no seu diretorio de trabalho;
    4. mostra o que vai subir e para, a menos que venha --push.

    O worktree existe porque a alternativa (trocar de branch no proprio
    diretorio) ja apagou arquivos ignorados uma vez. Nao se repete.

USO
    python3 tools/publica_release.py --versao OpenPod-Core-5.7-Public-Beta-2
    python3 tools/publica_release.py --versao ... --push

    --nome-tela "OpenPod 5.7 Beta 2"   o que a tela Informacao mostra
    --push                             empurra para origin main

DEPENDENCIAS
    git, e a ferramenta tools/organiza_pacote.py

O QUE NUNCA SOBE
    release/*/windows/*.exe   gravador proprietario da Shenju
    qualquer coisa fora de release/<versao>/ e da pagina

LIMITACOES
    Nao cria tag nem GitHub Release. Se um dia o pacote for distribuido
    como .zip anexado, e aqui que esse passo entra.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRANCH = "publico"
REMOTO = "origin"


def sh(*a, **kw):
    return subprocess.run(a, cwd=kw.pop("cwd", RAIZ), capture_output=True,
                          text=True, check=False, **kw)


def exigir(cond, msg):
    if not cond:
        sys.exit("ABORTADO: " + msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--versao", required=True,
                    help="nome da pasta em release/, ex OpenPod-Core-5.7-Public-Beta-2")
    ap.add_argument("--nome-tela", default=None,
                    help="o que a tela Informacao mostra, ex 'OpenPod 5.7 Beta 2'")
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args()

    pac = os.path.join(RAIZ, "release", a.versao)
    exigir(os.path.isdir(pac), "nao achei release/%s" % a.versao)

    # 1. o pacote se sustenta?
    r = sh(sys.executable, "tools/organiza_pacote.py",
           "release/" + a.versao, "--conferir")
    exigir(r.returncode == 0, "o pacote nao passou na conferencia:\n" + r.stdout + r.stderr)
    print(r.stdout.strip())

    up = [f for f in os.listdir(pac) if f.endswith(".up")]
    exigir(len(up) == 1, "esperava exatamente um .up em release/%s" % a.versao)

    # 2. a pagina cita a versao certa?
    pag = os.path.join(RAIZ, "docs", "index.html")
    exigir(os.path.isfile(pag), "nao achei docs/index.html")
    s = open(pag, encoding="utf-8").read()

    curto = a.nome_tela or re.sub(r"^OpenPod-Core-", "", a.versao).replace("-", " ")
    s = re.sub(r'<span class="ver">[^<]*</span>',
               '<span class="ver">%s</span>' % curto.replace("OpenPod ", ""), s)
    s = re.sub(r'(tree/main/release/)[^"]+', r"\g<1>" + a.versao, s)
    s = re.sub(r"(5\.7 Public Beta 2|Public Beta \d+)",
               a.versao.replace("OpenPod-Core-", "").replace("-", " "), s)
    open(pag, "w", encoding="utf-8").write(s)
    print("pagina aponta para %s" % a.versao)

    # 3. monta o branch publico num worktree separado
    wt = os.path.join(RAIZ, ".publicar-tmp")
    if os.path.isdir(wt):
        sh("git", "worktree", "remove", "--force", wt)
        shutil.rmtree(wt, ignore_errors=True)
    r = sh("git", "worktree", "add", "--force", "-B", BRANCH, wt, "HEAD")
    exigir(r.returncode == 0, "nao consegui criar o worktree:\n" + r.stderr)

    try:
        for n in os.listdir(wt):
            if n == ".git":
                continue
            p = os.path.join(wt, n)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)

        shutil.copy2(pag, os.path.join(wt, "index.html"))
        open(os.path.join(wt, ".nojekyll"), "w").close()
        shutil.copy2(os.path.join(RAIZ, "LICENSE"), wt)
        os.makedirs(os.path.join(wt, "release"), exist_ok=True)
        shutil.copytree(pac, os.path.join(wt, "release", a.versao),
                        ignore=shutil.ignore_patterns("*.exe"))
        open(os.path.join(wt, ".gitignore"), "w").write(
            "# Gravador da Shenju: proprietario, sem licenca para redistribuir.\n"
            "release/*/windows/*.exe\n")

        readme = os.path.join(RAIZ, "docs", "README_PUBLICO.md")
        if os.path.isfile(readme):
            t = open(readme, encoding="utf-8").read().replace("{VERSAO}", a.versao)
            open(os.path.join(wt, "README.md"), "w", encoding="utf-8").write(t)

        sh("git", "add", "-A", cwd=wt)
        r = sh("git", "-c", "user.name=Lucas Matheus", "-c", "user.email=osluky@gmail.com",
               "commit", "-q", "--allow-empty",
               "-m", "OpenPod %s\n\nDistribuicao publica: os binarios de atualizacao e a\n"
                     "pagina do projeto. As ferramentas de analise e o historico de\n"
                     "engenharia reversa nao sao publicos."
                     % a.versao.replace("OpenPod-Core-", "").replace("-", " "), cwd=wt)
        exigir(r.returncode == 0, "commit falhou:\n" + r.stderr)

        r = sh("git", "ls-files", cwd=wt)
        arqs = r.stdout.split()
        setores = [f for f in arqs if "/setores/" in f]
        print("\nvai subir:")
        for f in arqs:
            if f not in setores:
                print("  " + f)
        print("  release/%s/cabo/setores/  -> %d arquivos" % (a.versao, len(setores)))

        vaza = [f for f in arqs if re.search(r"\.exe$|B27|CLAUDE\.md|^tools/|^analysis/"
                                             r"|^firmware/|^docs/.*\.md$", f)]
        exigir(not vaza, "isto NAO pode subir:\n  " + "\n  ".join(vaza))
        print("\nconferido: nada de codigo-fonte, analise ou .exe")

        if a.push:
            r = sh("git", "push", "--force", REMOTO, "%s:main" % BRANCH)
            exigir(r.returncode == 0, "push falhou:\n" + r.stderr)
            print("\nempurrado para %s main" % REMOTO)
            print("https://zeroproj.github.io/OpenPod/")
        else:
            print("\nnada foi empurrado. Rode de novo com --push quando conferir.")
    finally:
        sh("git", "worktree", "remove", "--force", wt)
        shutil.rmtree(wt, ignore_errors=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
