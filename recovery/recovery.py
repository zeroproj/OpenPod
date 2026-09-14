#!/usr/bin/env python3
"""
recovery.py — o miolo do RECOVERY.sh. Nao rode direto.

O QUE FAZ, DE UMA VEZ

    1. confere a imagem de fabrica pelo sha256
    2. confere que o aparelho esta em modo download (301a:2800)
    3. LE os 2 MiB e guarda a fotografia do estado anterior
    4. compara com o de fabrica e mostra o que vai mudar
    5. pede que se digite GRAVAR
    6. grava 0x000000..0x1A3038 — bootloader, tabela, FIRM, TONE
    7. apaga 0x1A3038..0x1FC000 — a area livre
    8. rele os 2 MiB e confere as tres regioes
    9. diz o que o aparelho tinha antes

    Resultado: a flash volta a ser identica a de fabrica, exceto a PSMP
    (as configuracoes do usuario), que nunca e tocada.

AS DUAS COISAS QUE PARECEM PERIGOSAS E NAO SAO

    Gravar 0x000000..0x1A3038 endereca o setor 0x00D000, a tabela de
    particoes, que a regra R1 manda nunca escrever — foi ela que brickou
    o primeiro aparelho do projeto. Mas o `write_flash` compara cada
    bloco de 4 KiB antes de apagar:

        if (!m2) continue;   // same data

    Bloco ja correto nao e apagado nem regravado. Ainda assim este script
    CONFERE e avisa em separado se a tabela divergir, porque a garantia
    so vale enquanto a premissa valer.

    Apagar o que sobra da area livre parece destrutivo e e o contrario:
    a regiao e 0xFF no firmware de fabrica. Voltar para 0xFF e restaurar.

    O cuidado esta no SETOR DE FRONTEIRA — aquele em que o conteudo da
    imagem acaba no meio. Apaga-lo levaria junto o que vem antes (a cauda
    da TONE, no alvo `fabrica`). Por isso a gravacao vai ate o limite
    ALINHADO para cima: o setor de fronteira recebe o conteudo da imagem
    inteiro, 0xFF do rabo incluso, e o apagamento comeca no setor
    seguinte.

CONFIRMADO EM HARDWARE em 2026-09-14, num GN-438 que rodava a OpenPod
3.0: 37 setores regravados, area livre zerada, releitura identica a de
fabrica.
"""

import hashlib, os, subprocess, sys, time

SMT      = os.environ["SMT"]

# Os dois alvos. FABRICA e o padrao, e continua sendo a garantia: e o
# unico artefato cuja correcao nao depende de trabalho nosso. CORE e
# conveniencia — poupa reinstalar tudo quando o defeito e outro.
# Detalhe em imagens/ALVOS.md.
ALVOS = {
    "fabrica": ("imagens/GN438_original.bin",
                "b7cd5eb952be5328cbaa926099cf8d88168633c1"
                "fab6d0f31f3a283c9e24b36f",
                "firmware de fabrica"),
    "core":    ("imagens/OpenPod_Core_1.0.1.bin",
                "36125f5665b8613e0d96215e2ffcf36170d847068"
                "d0c72e572167fe506400c1f",
                "OpenPod Core 1.0.1 (STABLE)"),
}
SETOR    = 0x1000
PTABLE   = 0x00D000
TONE_FIM = 0x1A3038          # fim da particao TONE
LIVRE    = 0x1FC000          # inicio da PSMP: nada e tocado dali em diante

MANTER = "--manter-area-livre" in sys.argv
SO_VER = "--so-analise" in sys.argv
ALVO   = "fabrica"
for i, x in enumerate(sys.argv):
    if x == "--alvo" and i + 1 < len(sys.argv):
        ALVO = sys.argv[i + 1]
if ALVO not in ALVOS:
    sys.exit("alvo desconhecido: %s  (use %s)" % (ALVO, " ou ".join(ALVOS)))
IMAGEM, SHA_ALVO, DESC_ALVO = ALVOS[ALVO]


def extensao(d):
    """Ate onde esta imagem tem conteudo, arredondado para setor.

    O `fabrica` termina na TONE (0x1A3038) e tem a area livre virgem. O
    `core` usa a area livre — as rotinas e os textos do OpenPod moram
    la. Entao o limite nao pode ser constante: e o ultimo byte que nao e
    0xFF, nunca antes do fim da TONE.

        fabrica      0x1A3038 -> alinhado 0x1A4000
        core 1.0.1   0x1A493B -> alinhado 0x1A5000

    Dali ate a PSMP, apaga. Assim o alvo fica exato: nem sobra byte de
    uma versao anterior, nem se apaga o que a versao nova precisa.
    """
    fim = 0
    for i in range(LIVRE - 1, 0, -1):
        if d[i] != 0xFF:
            fim = i + 1
            break
    return (max(fim, TONE_FIM) + SETOR - 1) & ~(SETOR - 1)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def roda(*args):
    return subprocess.run([SMT, "init"] + [str(a) for a in args]).returncode == 0


def titulo(t):
    print()
    print("=" * 66)
    print("  " + t)
    print("=" * 66)
    print()


def setores(a, b, ini, fim):
    """{setor: bytes diferentes} entre duas imagens, no intervalo."""
    c = {}
    for i in range(ini, fim):
        if a[i] != b[i]:
            s = i // SETOR * SETOR
            c[s] = c.get(s, 0) + 1
    return c


def identifica(d):
    """o que este aparelho estava rodando?"""
    for chave in (b"OpenPod Core ", b"OpenPod "):
        i = d.find(chave)
        if i > 0:
            fim = i
            while fim < len(d) and 0x20 <= d[fim] < 0x7F and fim - i < 40:
                fim += 1
            return d[i:fim].decode("ascii", "replace").strip()
    return "yp3_2.0.43 (fabrica)" if d.find(b"yp3_2.0.43") > 0 else "nao identificado"


def main():
    os.makedirs("leitura", exist_ok=True)
    titulo("OPENPOD — RECOVERY OFICIAL DO GN-438")

    if not os.path.exists(IMAGEM):
        sys.exit(f"PARE: {IMAGEM} nao existe neste kit")
    orig = open(IMAGEM, "rb").read()
    if sha(orig) != SHA_ALVO:
        sys.exit(f"PARE: {IMAGEM} nao confere com o sha conhecido")
    SISTEMA = extensao(orig)
    print(f"  alvo                {DESC_ALVO}")
    print(f"  imagem              {IMAGEM}")
    print(f"                      conferida, {SHA_ALVO[:24]}...")
    print(f"  vai gravar          0x000000..0x{SISTEMA:06X}")
    if MANTER:
        print( "  nao apaga           --manter-area-livre")
    else:
        print(f"  vai apagar          0x{SISTEMA:06X}..0x{LIVRE:06X}   "
              f"({(LIVRE-SISTEMA)//1024} KiB)")
    print(f"  nao toca            0x{LIVRE:06X}..0x200000   PSMP, suas configuracoes")
    if SO_VER:
        print( "  modo                --so-analise: NADA sera escrito")
    print()

    # ---------------------------------------------------------------- 1
    print("  [1/5] lendo o aparelho (2 MiB, 1 a 2 minutos) — nao escreve nada")
    antes = f"leitura/antes_{time.strftime('%Y%m%d_%H%M%S')}.bin"
    if not roda("read_flash", 0, "2M", antes):
        sys.exit("\n  a leitura FALHOU. Nada foi escrito. Refaca o modo download.")
    d = open(antes, "rb").read()
    if len(d) != 0x200000:
        sys.exit(f"\n  leitura incompleta: {len(d)} bytes")
    print(f"        guardado em  {antes}")
    print(f"        sha          {sha(d)[:24]}...")
    print(f"        tinha        {identifica(d)}")
    print()

    # ---------------------------------------------------------------- 2
    print("  [2/5] o que vai mudar")
    print()
    sis = setores(orig, d, 0, SISTEMA)
    suj = sorted({i // SETOR * SETOR for i in range(SISTEMA, LIVRE)
                  if d[i] != 0xFF})
    n_sis = SISTEMA // SETOR
    print(f"        SISTEMA    {n_sis} setores, {n_sis - len(sis)} ja corretos, "
          f"{len(sis)} a regravar")
    for s in sorted(sis):
        marca = "   <<< TABELA DE PARTICOES" if s == PTABLE else ""
        print(f"                     0x{s:06X}  {sis[s]:5d} bytes{marca}")
    print()
    print(f"        AREA LIVRE {len(suj)} setores com bytes que nao sao 0xFF"
          + ("  (serao apagados)" if not MANTER and suj else ""))
    for s in suj:
        print(f"                     0x{s:06X}")
    print()

    if PTABLE in sis:
        print("  " + "!" * 62)
        print("  A TABELA DE PARTICOES (0x00D000) ESTA DIFERENTE DA DE FABRICA.")
        print("  E o setor que brickou o primeiro aparelho do projeto.")
        print("  Esta operacao VAI regrava-lo.")
        print("  " + "!" * 62)
    else:
        print("  A tabela de particoes ja esta certa — nao sera tocada.")
    print()

    nada = not sis and (MANTER or not suj)
    if nada:
        print(f"  O aparelho JA esta em {DESC_ALVO}. Nada a fazer. Pode desplugar.")
        return 0
    if SO_VER:
        print("  --so-analise: parando aqui. Nada foi escrito.")
        return 0

    # ---------------------------------------------------------------- 3
    print("  [3/5] confirmacao")
    print()
    print("  Nao desligue nem desplugue ate o fim.")
    print("  Digite GRAVAR para continuar, qualquer outra coisa sai.")
    try:
        if input("  > ").strip() != "GRAVAR":
            print("\n  cancelado. Nada foi escrito.")
            return 0
    except (EOFError, KeyboardInterrupt):
        print("\n  cancelado. Nada foi escrito.")
        return 0
    print()

    def morreu(oque):
        print()
        print("  " + "*" * 62)
        print(f"  {oque} FALHOU.   *** NAO DESLIGUE O APARELHO. ***")
        print("  O modo download esta na ROM de mascara e continua respondendo.")
        print("  Rode  sh 1_LER.sh  e mande o resultado.")
        print("  " + "*" * 62)
        return 1

    # ---------------------------------------------------------------- 4
    print("  [4/5] gravando")
    if sis:
        print(f"        sistema 0x000000..0x{SISTEMA:06X}")
        if not roda("write_flash", 0, 0, hex(SISTEMA), IMAGEM):
            return morreu("a gravacao do sistema")
    else:
        print("        sistema ja correto, pulado")

    if not MANTER and suj:
        # Nao ha mais setor misto para tratar a parte: a gravacao acima
        # vai ate o limite ALINHADO, entao o setor de fronteira ja
        # recebeu o conteudo da imagem — inclusive o 0xFF do rabo.
        print(f"        apagando 0x{SISTEMA:06X}..0x{LIVRE:06X}  "
              f"({(LIVRE - SISTEMA) // 1024} KiB)")
        if not roda("erase_flash", hex(SISTEMA), hex(LIVRE - SISTEMA)):
            return morreu("o apagamento da area livre")
    print()

    # ---------------------------------------------------------------- 5
    print("  [5/5] relendo os 2 MiB para conferir")
    depois = "leitura/depois.bin"
    if not roda("read_flash", 0, "2M", depois):
        print("  a releitura falhou — rode  sh 1_LER.sh  para conferir a mao")
        return 1
    r = open(depois, "rb").read()

    dif_sis = [i for i in range(SISTEMA) if orig[i] != r[i]]
    dif_liv = [i for i in range(SISTEMA, LIVRE) if r[i] != 0xFF]
    psmp_ok = r[LIVRE:] == d[LIVRE:]

    titulo("RESULTADO")
    print(f"  sistema     0x000000..0x{SISTEMA:06X}   "
          + ("IDENTICO AO ALVO" if not dif_sis
             else f"{len(dif_sis)} BYTES DIFERENTES, 1o em 0x{dif_sis[0]:06X}"))
    print(f"  area livre  0x{SISTEMA:06X}..0x{LIVRE:06X}   "
          + ("MANTIDA a pedido" if MANTER else
             "TODA 0xFF" if not dif_liv
             else f"{len(dif_liv)} bytes nao sao 0xFF"))
    print(f"  PSMP        0x{LIVRE:06X}..0x200000   "
          + ("intocada" if psmp_ok else "MUDOU — nao devia"))
    print()
    print(f"  antes       {identifica(d)}")
    print(f"  agora       {identifica(r)}")
    print(f"  fotografia  {antes}")
    print()

    if dif_sis or (not MANTER and dif_liv) or not psmp_ok:
        print("  *** NAO DESLIGUE. Mande este resultado. ***")
        print("=" * 66)
        return 1
    print("  Pode desplugar e ligar.")
    print("  Deve abrir com o logotipo GENAI e a home em grade 3x3."
          if ALVO == "fabrica" else
          "  Deve abrir com a logo do OpenPod sobre preto.")
    print("=" * 66)
    return 0


if __name__ == "__main__":
    sys.exit(main())
