#!/usr/bin/env python3
"""
build.py — constroi a imagem do OpenPod a partir do ORIGINAL, numa
           sequencia DECLARADA.

POR QUE ISTO EXISTE

    Ate hoje o firmware era uma CORRENTE: v070 -> v071 -> v072 -> v073,
    cada passo aplicado a mao sobre o anterior. Sao 90 imagens em
    `firmware/WORKING/`. Consequencias:

      - para corrigir um patch antigo era preciso refazer todos os
        seguintes, ou remendar o resultado (foi o que aconteceu com o
        `patch_extras` -> `patch_extras_fix` -> e agora um terceiro);
      - ninguem sabia dizer, sem ler o CHANGELOG inteiro, **o que** esta
        dentro da imagem;
      - patches superados (tres versoes de `scrollbar`, `bar_height`
        contra `status_bar`) continuavam na historia sem estar na lista.

    Aqui a imagem passa a ser uma RECEITA. Mudou um passo? Reconstroi.

O QUE O PIPELINE DESCOBRIU — e por que ele PARA no passo 7

    Rodando, ele bateu tres vezes em dependencia escondida e na quarta
    achou a causa de fundo.

    As tres primeiras eram erros de contabilidade minha:

      1. `patch_home_keys.py` nao estava em lugar nenhum — nem na receita,
         nem na lista de excluidos. Eu tinha perdido ele de vista.
      2. `patch_chrome_padrao.py` NAO e superado pelo Saturno: e
         PRE-REQUISITO. A tabela de tema foi retrofitada em cima das
         rotinas que ele cria. Eu vinha descrevendo o Saturno como
         fundacao; ele e revestimento.
      3. `patch_cor_texto_lista.py`, idem: o S10 reescreve o gancho que
         ele criou.

    A quarta e estrutural, e nenhuma reordenacao resolve:

        # patch_cor_selecao.py, e varios outros
        f = LIVRE_INI
        for i in range(LIVRE_INI, LIVRE_INI + 0x4000):
            if d[i] != 0xFF:
                f = i + 1
        return (f + 3) & ~3

    E um ALOCADOR INCREMENTAL. Cada patch se encaixa logo depois do
    ultimo byte ocupado. Logo **o endereco de uma rotina nao e escolhido:
    ele emerge de tudo que rodou antes**. E os patches seguintes fixam
    esse endereco no proprio codigo.

    Medida: depois dos 6 primeiros passos desta receita, a area livre
    comeca em 0x001A4041. Mas `patch_cor_texto_lista` exige a rotina em
    0x001A3518 — 2.857 bytes ANTES. Na historia real aquele patch rodou
    mais cedo, com menos coisa ocupada.

    **Conclusao: a corrente so compoe na ordem historica exata**, patches
    mortos inclusive. Uma receita limpa e impossivel com as ferramentas
    como estao.

O CAMINHO PARA A 3.0

    O conserto nao e reordenar: e tirar dos patches a decisao de onde
    morar. Cada ferramenta que aloca deve receber o endereco como
    PARAMETRO (`--em 0x1A5300`), e a receita declara o mapa da area
    livre. Ai:

      - o endereco deixa de depender da historia;
      - a receita passa a ser reordenavel e podavel;
      - um patch corrigido nao move os outros.

    E trabalho delimitado: ~12 ferramentas alocam assim.

O QUE ELE **NAO** FAZ

    Nao reproduz a historia. A receita declara o que queremos HOJE, na
    ordem certa — patches superados ficam de fora de proposito.

    Por isso `--verificar` existe: comparando a saida com uma imagem
    conhecida (a 2.2, que boota), a diferenca mostra **o que a corrente
    tem e a receita nao** — que e exatamente a pergunta do mantenedor
    ("acho que vem com muita coisa errada").

USO
    python3 tools/build.py --saida firmware/WORKING/GN438_build.bin
    python3 tools/build.py --so-lista
    python3 tools/build.py --verificar firmware/WORKING/GN438_openpod_v073_carimbado.bin

SEGURANCA
    - le o ORIGINAL e confere o sha256 antes de comecar;
    - cada passo roda em arquivo proprio dentro de um diretorio temporario;
    - para no primeiro erro e mostra a saida da ferramenta que falhou;
    - nao grava nada no aparelho e nao gera kit.
"""

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = os.path.join(RAIZ, "firmware/ORIGINAL/GN438_original.bin")
SHA_ORIGINAL = ("b7cd5eb952be5328cbaa926099cf8d88168633c1"
                "fab6d0f31f3a283c9e24b36f")

# ---------------------------------------------------------------------------
# O MAPA DA AREA LIVRE
#
# Cada ferramenta que aloca recebe `--em` e passa a ter lugar FIXO. Sem
# isto o endereco emergia da ordem (ver o cabecalho), e a corrente so
# compunha na sequencia historica exata.
#
# O pipeline CONFERE, depois de cada passo, que a ferramenta escreveu
# apenas dentro de lotes DECLARADOS. Escrever no proprio lote e obvio;
# escrever no lote de um passo anterior tambem e legitimo (o
# `aplica_textos`, por exemplo, atualiza os ponteiros da tabela que o
# `relocate_lang_table` moveu). O que o pipeline recusa e escrever em
# area livre NAO declarada — que e exatamente o alocador incremental
# voltando pela porta dos fundos.
#
# Abaixo de 0x001A5000 ficam os lotes alocados; de 0x001A5000 em diante
# ficam as rotinas de endereco FIXO (titulos, Saturno, Extras), que ja
# eram bem-comportadas e nao mudam.
# ---------------------------------------------------------------------------
MAPA = {
    # 0x001A3038..0x001A3040 e a string "OpenPod" do patch_status_bar,
    # em endereco FIXO na ferramenta. Os lotes comecam depois dela.
    "patch_texto_branco_fixo.py": (0x001A6000, 0x0010),
    "patch_barra_selecao.py":  (0x001A3040, 0x0100),
    "patch_scrollbar3.py":     (0x001A3140, 0x0100),
    "patch_update_sd.py":      (0x001A3240, 0x0100),
    "patch_menu_text.py":      (0x001A3340, 0x00D8),
    # 0x001A3518 NAO e escolha nossa: o `patch_cor_texto_lista` fixou
    # esse endereco no proprio codigo e recusa se a rotina nao estiver
    # exatamente ali. Divida tecnica herdada.
    "patch_cor_selecao.py":    (0x001A3518, 0x00E8),
    "relocate_lang_table.py":  (0x001A3600, 0x0700),
    "aplica_textos.py":        (0x001A3D00, 0x1200),
    # 0x001A4F00..0x001A5000 e do CARIMBO DE VERSAO (`patch_versao.py`,
    # aplicado pelo `make_install_kit`, regra R7). Ele nao roda nesta
    # receita, mas o slot fica reservado aqui para nao ser dado a
    # ninguem: a constante vive em make_install_kit.EM_VERSAO.
    #
    # 0x001A5000..0x001A6000 e reservado: o `patch_titulos` exige esses
    # 4 KiB virgens. O que nao cabe antes vai para depois dele.
    "make_extras_menu.py":     (0x001A6000, 0x0400),
}
AREA_INI, AREA_FIM = 0x001A3040, 0x001A8000


# ---------------------------------------------------------------------------
# OPENPOD CORE 1.0 — deliberadamente pequena.
#
# Esta receita produz a **OpenPod Core 1.0.1**, declarada STABLE pelo
# mantenedor em 2026-09-14 depois de rodar no aparelho: logo sobre preto,
# tela Informacoes certa, e instalada PELO CARTAO — o que confirmou o
# caminho de atualizacao inteiro.
#
#     imagem      7312fbd066b1a31e508a51c9c44c5e203e17e6d1e1b9719c0df7e37e7b250d34
#     carimbada   36125f5665b8613e0d96215e2ffcf36170d847068d0c72e572167fe506400c1f
#
# E a BASELINE da linha Core: versoes novas podem partir dela.
#
# Base decidida pelo mantenedor em 2026-09-14: o firmware ORIGINAL.
#
# O objetivo desta versao nao e parecer melhor: e ser uma fundacao em que
# um defeito tenha causa obvia. Por isso NAO entram home em lista, faixa
# superior, titulos, Saturno, Extras, cor de selecao — tudo isso continua
# na receita `interface`, inteiro, e volta na Core 2.0.
#
# Consequencia aceita: a Core 1.0 tem a home em grade 3x3 de fabrica.
# ---------------------------------------------------------------------------
CORE_1_0 = [
    ("patch_logo.py",          [], "a logo do OpenPod na tela de abertura"),
    ("patch_fundo_abertura.py", [], "o fundo da abertura fica preto (V008)"),
    # A tabela do portugues sai para a area livre ANTES de ser reescrita:
    # a de fabrica emenda direto na do espanhol e nao tem folga.
    ("relocate_lang_table.py", [], "tabela do portugues para a area livre"),
    ("aplica_textos.py",       [], "textos revisados em portugues do Brasil"),
    ("patch_menu_text.py", ["--set", "pt:3=Vídeo"],
     "'Vídeo' com maiuscula (o original e minusculo)"),
    ("patch_update_sd.py",     [], "item 'Atualizar por SD' em Configurar"),

    # --- Marte M-a, 2026-09-14. O PRIMEIRO passo rumo ao alvo visual.
    #
    # 1 byte DENTRO de CRIA_LINHA (0x00D21764), a rotina compartilhada
    # que 39 telas usam. Nao aloca, nao usa area livre, nao cria objeto.
    #
    # Entra no FIM da receita de proposito: e independente de tudo o que
    # vem antes, entao pode sair daqui sem quebrar nada. Foi essa
    # propriedade que faltou na linha 2.x.
    ("patch_sem_separador.py", [], "M-a: sem traco entre os itens, como o nano"),

    # Marte M-f. Tambem independente: 2 bytes na TABELA de paletas da
    # LVGL (0x000DF082), nao em codigo. Nao depende do M-a nem de
    # nenhum outro passo, e sair daqui nao quebra nada.
    ("patch_selecao_marte.py", [], "M-f: a selecao ganha o azul do Marte"),

    # Marte M-d. 1 byte no portao do LV_EVENT_DRAW_POST, no tratador de
    # evento compartilhado do lv_obj. Independente dos anteriores.
    ("patch_sem_rolagem.py",   [], "M-d: sem barra de rolagem, como o nano"),
]


# ---------------------------------------------------------------------------
# AS RECEITAS 2.x FORAM REMOVIDAS — 2026-09-14, a pedido do mantenedor.
#
# Estavam aqui: `interface`, `core2.0`, `core2.1`, `core2.2`, `marte` e
# `carcaca`. Sairam junto com as 25 ferramentas que so elas usavam.
#
# Motivo, nas palavras dele: "pedi para voce mudar so o menu, voce veio
# com um update 2.4 com alteracao da barra superior que nao pedi".
#
# A causa era ESTRUTURAL, nao desatencao. Aquelas receitas encadeavam ate
# 31 passos em que o `patch_chrome_padrao` — a barra superior — era
# PRE-REQUISITO declarado dos doze passos do Saturno. Mexer em qualquer
# item da lista arrastava a barra junto, porque a receita nao permitia
# separar. O acoplamento foi criado aqui, nao no firmware.
#
# Nada se perdeu: esta tudo no git, no commit anterior a este.
#
# REGRA para quem retomar: volta um passo por vez, testado no aparelho, e
# NUNCA empacotado com algo que nao foi pedido.
# ---------------------------------------------------------------------------

RECEITAS = {
    "core1.0": CORE_1_0,
}

# Ferramentas que existem mas NAO entram na receita, e por que.
#
# Esta lista tinha 23 entradas ate 2026-09-14. As outras 22 eram patches
# de interface da linha 2.x — chevron, Extras, sonda, scrollbar, raio,
# respiro, navegacao, e seis marcados so como "experimento". Os arquivos
# foram APAGADOS junto com a linha, a pedido do mantenedor:
#
#     "experiments sao problematicas"
#     "nao podemos usar essas referencias, elas nao sao boas"
#
# Manter a lista descrevendo arquivos inexistentes seria manter o convite
# a reaproveita-los. Esta tudo no git, no commit da limpeza.
FORA = [
    ("patch_versao.py",  "aplicado pelo make_install_kit (regra R7)"),
]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def valida(img):
    """validate_firmware.py, com a falha de CRC da R1 reclassificada.

    A FIRM tem um campo de CRC na tabela de particoes, e a regra R1 manda
    NUNCA regravar esse setor — entao o campo fica desatualizado de
    proposito, e o validador acusa. Confirmado no aparelho em 13/09: ele
    boota com a tabela de fabrica sobre uma FIRM diferente.

    Um validador que grita FALHA no caso normal ensina a ignorar falhas.
    Aqui essa linha vira ESPERADO, e qualquer OUTRA falha e falha mesmo.
    """
    print("\n  VALIDACAO ESTRUTURAL")
    r = subprocess.run([sys.executable,
                        os.path.join(RAIZ, "tools/validate_firmware.py"), img],
                       capture_output=True, text=True, cwd=RAIZ)
    reais = []
    for ln in r.stdout.splitlines():
        if "[FALHA]" not in ln:
            continue
        if "particao FIRM: CRC" in ln:
            print("    ESPERADO  CRC da FIRM desatualizado (regra R1)")
        else:
            reais.append(ln.strip())
    ok = [ln for ln in r.stdout.splitlines() if "RESULTADO" in ln]
    if ok:
        print("    " + ok[0].strip())
    if reais:
        print("\n  FALHAS REAIS:")
        for ln in reais:
            print("    " + ln)
        return False
    print("    nenhuma falha alem da esperada   OK")
    return True


def diferenca(img, base, receita):
    """binary diff contra a base, com as guardas do projeto.

    Nao e enfeite: §12 do prompt-mestre exige que toda versao seja
    comparada com sua base, e que alteracao inesperada PARE o processo.
    As tres guardas abaixo sao as que ja custaram aparelho ou versao.
    """
    print(f"\n  BINARY DIFF contra {os.path.basename(base)}")
    A = open(os.path.join(RAIZ, base), "rb").read()
    B = open(img, "rb").read()
    if len(A) != len(B):
        print(f"    PARE: tamanhos diferentes, {len(A)} e {len(B)}")
        return False
    dif = [i for i in range(len(A)) if A[i] != B[i]]
    if not dif:
        print("    nenhuma diferenca — a receita nao mudou nada?")
        return True
    secs = {}
    for i in dif:
        secs[i // 0x1000 * 0x1000] = secs.get(i // 0x1000 * 0x1000, 0) + 1
    print(f"    {len(dif)} bytes em {len(secs)} setores, "
          f"menor offset 0x{min(dif):06X}")
    for s in sorted(secs):
        print(f"      0x{s:06X}  {secs[s]:6d} B")

    guardas = [
        ("nada abaixo de 0x00D000 (bootloader)", min(dif) >= 0x00D000),
        ("setor 0x00D000 intocado (regra R1)",
         not any(0xD000 <= i < 0xE000 for i in dif)),
        ("PSMP intocada (0x1FC000+)",
         not any(i >= 0x1FC000 for i in dif)),
    ]
    print()
    falhou = False
    for texto, passou in guardas:
        print(f"    {'OK  ' if passou else 'PARE'}  {texto}")
        falhou |= not passou
    if falhou:
        print("\n    PARE: a receita tocou onde nao devia. Investigue "
              "antes de seguir.")
        return False
    return True


def main():
    ap = argparse.ArgumentParser(description="constroi o OpenPod do ORIGINAL")
    ap.add_argument("--saida", default="firmware/WORKING/GN438_build.bin")
    ap.add_argument("--so-lista", action="store_true",
                    help="mostra a receita e sai")
    ap.add_argument("--verificar", metavar="IMAGEM",
                    help="compara a saida com uma imagem de referencia")
    ap.add_argument("--ate", metavar="FERRAMENTA",
                    help="para depois deste passo")
    ap.add_argument("--base", metavar="IMAGEM",
                    help="imagem de referencia do binary diff "
                         "(padrao: o ORIGINAL)")
    ap.add_argument("--sem-validar", action="store_true",
                    help="nao roda validacao nem diff ao final")
    ap.add_argument("--receita", default="core1.0",
                    choices=sorted(RECEITAS),
                    help="qual receita construir (padrao: interface)")
    a = ap.parse_args()

    RECEITA = RECEITAS[a.receita]

    print()
    print(f"  RECEITA DO OPENPOD — {a.receita}")
    print()
    for i, (t, extra, por) in enumerate(RECEITA, 1):
        print(f"   {i:2d}. {t:26s} {por}")
    print(f"\n  fora da receita de proposito: {len(FORA)} ferramentas")
    if a.so_lista:
        for t, por in FORA:
            print(f"       {t:26s} {por}")
        return 0

    if sha(ORIGINAL) != SHA_ORIGINAL:
        sys.exit("PARE: o sha256 do ORIGINAL nao confere")
    print(f"\n  ORIGINAL conferido ({SHA_ORIGINAL[:16]}...)")

    tmp = tempfile.mkdtemp(prefix="openpod_build_")
    atual = os.path.join(tmp, "000_original.bin")
    shutil.copy(ORIGINAL, atual)
    print(f"  area de trabalho: {tmp}\n")

    for i, (t, extra, por) in enumerate(RECEITA, 1):
        prox = os.path.join(tmp, f"{i:03d}_{t.replace('.py','')}.bin")
        cam = os.path.join(RAIZ, "tools", t)
        if not os.path.exists(cam):
            print(f"   {i:2d}. {t:26s} FERRAMENTA NAO EXISTE")
            return 1
        args = list(extra)
        if t in MAPA:
            args += ["--em", hex(MAPA[t][0])]
        r = subprocess.run([sys.executable, cam, "--in", atual,
                            "--out", prox] + args,
                           capture_output=True, text=True, cwd=RAIZ)
        if r.returncode or not os.path.exists(prox):
            print(f"   {i:2d}. {t:26s} FALHOU")
            print("       ---- saida da ferramenta ----")
            for ln in (r.stdout + r.stderr).splitlines()[-25:]:
                print("       " + ln)
            print(f"\n  parou no passo {i}. Imagem ate aqui: {atual}")
            return 1
        # confere que a ferramenta respeitou o proprio lote
        if t in MAPA:
            A, B = open(atual, "rb").read(), open(prox, "rb").read()
            declarado = set()
            for bb, tt in MAPA.values():
                declarado |= set(range(bb, bb + tt))
            fora = [x for x in range(AREA_INI, AREA_FIM)
                    if A[x] != B[x] and x not in declarado]
            if fora:
                print(f"   {i:2d}. {t:26s} ESCREVEU FORA DO MAPA")
                print(f"       lote declarado: 0x{MAPA[t][0]:06X}"
                      f"..0x{MAPA[t][0]+MAPA[t][1]:06X}")
                print(f"       escreveu tambem em 0x{min(fora):06X}"
                      f"..0x{max(fora):06X}  ({len(fora)} bytes)")
                return 1
        atual = prox
        nota = f"  [0x{MAPA[t][0]:06X}]" if t in MAPA else ""
        print(f"   {i:2d}. {t:26s} ok{nota}")
        if a.ate and t == a.ate:
            break

    dst = os.path.join(RAIZ, a.saida)
    shutil.copy(atual, dst)
    print(f"\n  gravado: {a.saida}")
    print(f"  sha256 : {sha(dst)}")

    if not a.sem_validar:
        if not valida(dst):
            return 1
        if not diferenca(dst, a.base or ORIGINAL, RECEITA):
            return 1

    if a.verificar:
        ref = os.path.join(RAIZ, a.verificar)
        A, B = open(dst, "rb").read(), open(ref, "rb").read()
        dif = [i for i in range(min(len(A), len(B))) if A[i] != B[i]]
        secs = sorted({i // 0x1000 * 0x1000 for i in dif})
        print(f"\n  COMPARACAO com {os.path.basename(ref)}")
        print(f"    bytes diferentes: {len(dif)}   setores: {len(secs)}")
        for s in secs:
            n = sum(1 for i in dif if s <= i < s + 0x1000)
            print(f"      0x{s:06X}  {n} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
