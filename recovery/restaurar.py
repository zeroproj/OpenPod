#!/usr/bin/env python3
"""
restaurar.py — o miolo do 2_RESTAURAR.sh. Nao rode direto.

O QUE FAZ

    Reinstala o sistema inteiro: grava 0x000000..0x1A3038 do firmware de
    fabrica — bootloader, tabela de particoes, FIRM e TONE. Nao e um
    remendo do que mudou: e a imagem completa, como um reinstalar.

POR QUE ISSO E SEGURO, apesar de endereçar 0x00D000

    O `write_flash` do smtlink_dump compara ANTES de apagar. Para cada
    bloco de 4 KiB ele le o que esta na flash, mescla com o que vai
    gravar, e:

        if (!m2) continue;   // same data

    Se o bloco ja esta correto, ele **nao e apagado nem regravado**. Logo
    "gravar tudo" toca fisicamente so o que difere — e a tabela de
    particoes, que neste aparelho ja e a de fabrica, nao e tocada.

    Ainda assim, o script CONFERE isso antes: se o setor 0x00D000 estiver
    diferente do de fabrica, ele avisa em separado, porque ai a gravacao
    passaria por cima do setor que brickou o primeiro aparelho.

O QUE ELE NAO TOCA

    0x1A3038..0x1FC000   area livre. Pode conter rotinas do OpenPod, que
                         ficam inertes: a FIRM de fabrica nao tem gancho
                         para elas. Para zerar, ver 9b_APAGAR_AREA_LIVRE.sh
    0x1FC000..0x200000   PSMP, suas configuracoes de usuario
"""

import hashlib, os, subprocess, sys

SMT      = os.environ["SMT"]
ORIGINAL = "imagens/GN438_original.bin"
SHA_ORIG = "b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f"
ANTES    = "leitura/GN438_antes_recovery.bin"
ATUAL    = "leitura/estado_atual.bin"
DEPOIS   = "leitura/estado_depois.bin"
SETOR    = 0x1000
PTABLE   = 0x00D000
ATE      = 0x1A3038          # fim da TONE


def sha(b):
    return hashlib.sha256(b).hexdigest()


def roda(*args):
    return subprocess.run([SMT, "init"] + [str(a) for a in args]).returncode == 0


def main():
    os.makedirs("leitura", exist_ok=True)
    print()
    print("=" * 64)
    print("  REINSTALAR O SISTEMA DE FABRICA NO GN-438")
    print("=" * 64)
    print()

    orig = open(ORIGINAL, "rb").read()
    if sha(orig) != SHA_ORIG:
        sys.exit("PARE: imagens/GN438_original.bin nao confere com o sha conhecido")
    print(f"  imagem de fabrica conferida   {SHA_ORIG[:24]}...")
    print(f"  vai gravar                    0x000000..0x{ATE:06X}  "
          f"({ATE:,} bytes)".replace(",", "."))
    print()

    # --- 1. estado antes ----------------------------------------------
    print("  [1/4] lendo o estado atual (2 MiB) — nao escreve nada")
    if not roda("read_flash", 0, "2M", ATUAL):
        sys.exit("\n  a leitura FALHOU. Nada foi escrito. Refaca o modo download.")
    atual = open(ATUAL, "rb").read()
    if len(atual) != 0x200000:
        sys.exit(f"\n  leitura incompleta: {len(atual)} bytes")
    if not os.path.exists(ANTES):          # guarda a 1a fotografia
        open(ANTES, "wb").write(atual)
    print(f"        sha {sha(atual)[:24]}...")
    print()

    # --- 2. o que vai mudar de verdade --------------------------------
    conta = {}
    for i in range(ATE):
        if orig[i] != atual[i]:
            s = i // SETOR * SETOR
            conta[s] = conta.get(s, 0) + 1
    sujos_livre = len({i // SETOR * SETOR for i in range(ATE, 0x1FC000)
                       if atual[i] != 0xFF})

    print("  [2/4] o que a gravacao vai tocar")
    print()
    print(f"        setores em 0x000000..0x{ATE:06X} : 420")
    print(f"        ja corretos, serao PULADOS       : {420 - len(conta)}")
    print(f"        diferentes, serao regravados     : {len(conta)}")
    print()
    if conta:
        for s in sorted(conta):
            marca = "   <<< TABELA DE PARTICOES" if s == PTABLE else ""
            print(f"          0x{s:06X}  {conta[s]:5d} bytes{marca}")
        print()

    if PTABLE in conta:
        print("  " + "!" * 60)
        print("  A TABELA DE PARTICOES (0x00D000) ESTA DIFERENTE DA DE FABRICA.")
        print("  E o setor que brickou o primeiro aparelho do projeto.")
        print("  Ele SERA regravado por esta operacao.")
        print("  " + "!" * 60)
        print()
    else:
        print("  A tabela de particoes ja e a de fabrica — nao sera tocada.")
        print()

    if not conta:
        print("  O sistema JA e o de fabrica, byte a byte. Nada a gravar.")
        if sujos_livre:
            print(f"  (a area livre tem {sujos_livre} setores com bytes do OpenPod,")
            print("   inertes; ./9b_APAGAR_AREA_LIVRE.sh zera, se quiser)")
        print("  Pode desplugar.")
        return 0

    # --- 3. confirmacao ------------------------------------------------
    print("  [3/4] confirmacao")
    print()
    print("  Nao desligue nem desplugue durante a gravacao.")
    print("  Digite GRAVAR para continuar, qualquer outra coisa sai.")
    try:
        if input("  > ").strip() != "GRAVAR":
            print("\n  cancelado. Nada foi escrito.")
            return 0
    except (EOFError, KeyboardInterrupt):
        print("\n  cancelado. Nada foi escrito.")
        return 0
    print()

    # --- 4. gravar a imagem inteira ------------------------------------
    print("  [4/4] gravando o sistema (pode levar alguns minutos)")
    print()
    if not roda("write_flash", 0, 0, hex(ATE), ORIGINAL):
        print()
        print("  A GRAVACAO FALHOU. *** NAO DESLIGUE O APARELHO. ***")
        print("  Rode ./1_LER.sh e mande o resultado.")
        return 1
    print()

    print("  relendo os 2 MiB para conferir")
    if not roda("read_flash", 0, "2M", DEPOIS):
        print("  a releitura falhou — rode ./1_LER.sh para conferir a mao")
        return 1
    dep = open(DEPOIS, "rb").read()
    dif = [i for i in range(ATE) if orig[i] != dep[i]]
    livre = len({i // SETOR * SETOR for i in range(ATE, 0x1FC000)
                 if dep[i] != 0xFF})

    print()
    print("=" * 64)
    if dif:
        print(f"  AINDA HA {len(dif)} BYTES DIFERENTES — o 1o em 0x{dif[0]:06X}")
        print("  *** NAO DESLIGUE. Mande este resultado. ***")
        print("=" * 64)
        return 1
    print(f"  0x000000..0x{ATE:06X}  IDENTICO AO DE FABRICA")
    print("  PSMP (suas configuracoes)  intocada")
    if livre:
        print(f"  area livre                 {livre} setores com bytes do OpenPod,")
        print("                             inertes. ./9b_APAGAR_AREA_LIVRE.sh zera")
    print()
    print("  Pode desplugar e ligar.")
    print("  Deve abrir com o logotipo GENAI e a home em grade 3x3.")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
