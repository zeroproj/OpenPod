#!/usr/bin/env python3
"""
patch_home_barra.py — a selecao da home vira BARRA, como nas outras telas.

O ALVO

    Etapa 2 do `docs/PLANO_HOME.md` §5. A Etapa 1 (patch_home_lista.py)
    converteu o DESENHO da home e deixou a selecao como estava: COR DE
    TEXTO. Na tela, o item escolhido ficava AMARELO.

    O Configurar, e as outras 38 telas de lista, mostram BARRA: fundo da
    linha pintado, texto branco por cima. Confirmado nas fotos de
    2026-09-14.

POR QUE ISTO SO PODE VIR AGORA

    A Etapa 1 fez a home guardar A LINHA no array A (+0x00), no lugar do
    antigo quadro de icone. Sem esse objeto nao havia o que pintar de
    fundo — a home so tinha rotulos soltos.

    Esta etapa foi mantida SEPARADA de proposito: juntar as duas numa
    versao so repetiria o acoplamento que afundou a linha 2.x.

O QUE MUDA, e por que fica igual ao Configurar

        antes                          depois
        rotulo  cor = palette(0xC)     LINHA   fundo = palette(5)
                amarelo                        o azul do Marte (M-f)
        rotulo  cor = 0xD2E948         LINHA   fundo = 0xD2138A
                -1, branco                     0, preto

    O texto NUNCA mais muda de cor: fica branco sempre. Branco sobre
    azul quando selecionado, branco sobre preto quando nao. E o mesmo
    desenho das outras telas.

    A paleta 5 ja e o AZUL DO MARTE — trocada na Core 1.2, RGB(41,101,222).
    Entao a barra da home nasce com a cor certa, sem ajuste extra.

OS TRES LUGARES — e por que sao tres

    A home pinta a selecao em tres momentos distintos:

    A) na CRIACAO da tela, para o item que ja estava escolhido
           0x0012EDAE  movs r0,#0xc      -> #5
           0x0012EDB0  ldr r6,[r3,#0x24] -> ldr r6,[r3]     array B -> A
           0x0012EDBC  bl set_text_color -> bl set_bg_color

    B) ao SELECIONAR o item novo
           0x0012EB3E  movs r0,#0xc      -> #5
           0x0012EB40  ldr r6,[r3,#0x24] -> ldr r6,[r3]
           0x0012EB4C  bl set_text_color -> bl set_bg_color

    C) ao DESSELECIONAR o anterior
           0x0012EB06  ldr r3,[r3,#0x24] -> ldr r3,[r3]
           0x0012EB08  bl 0xD2E948       -> bl 0xD2138A     branco -> preto
           0x0012EB12  bl set_text_color -> bl set_bg_color

    Esquecer o (C) deixaria TODAS as linhas visitadas azuis — a "segunda
    selecao" que ja apareceu neste projeto antes. Esquecer o (A) faria a
    barra so aparecer depois do primeiro toque numa tecla.

USO
    python3 tools/patch_home_barra.py --in <entrada.bin> --out <saida.bin>
    python3 tools/patch_home_barra.py --in <entrada.bin> --dry-run
    python3 tools/patch_home_barra.py --autoteste

DEPENDENCIAS
    Python 3. Nada mais.

LIMITACOES
    - depende do `patch_home_lista.py` ter rodado antes: e ele que poe a
      LINHA no array A. A ferramenta NAO consegue verificar isso sozinha,
      porque so olha os tres pontos que edita — por isso ela entra DEPOIS
      dele na receita, e isso esta declarado no build.py;
    - nao mexe na faixa superior (M-c);
    - nao aloca, nao usa a area livre.
"""

import argparse, hashlib, os, sys

RAIZ     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = "firmware/ORIGINAL/GN438_original.bin"
PROIBIDO = 0x0000D000
TAMANHO  = 0x200000
BIAS     = 0x00C00000

SET_BG_COLOR   = 0x00D4D092
SET_TEXT_COLOR = 0x00D4D10A
GETTER_BRANCO  = 0x00D2E948     # mov.w r0,#-1
GETTER_PRETO   = 0x00D2138A     # mov.w r0,#0


def _bl(origem, alvo):
    off = alvo - (origem + 4)
    if not (-(1 << 24) <= off < (1 << 24)) or off & 1:
        raise RuntimeError(f"bl fora de alcance: 0x{origem:08X} -> 0x{alvo:08X}")
    v = off & 0x1FFFFFF
    S = (v >> 24) & 1
    i1 = (v >> 23) & 1
    i2 = (v >> 22) & 1
    w1 = 0xF000 | (S << 10) | ((v >> 12) & 0x3FF)
    w2 = (0xD000 | (((~i1 ^ S) & 1) << 13) | (((~i2 ^ S) & 1) << 11)
          | ((v >> 1) & 0x7FF))
    return bytes([w1 & 0xFF, w1 >> 8, w2 & 0xFF, w2 >> 8])


# ---------------------------------------------------------------------------
# AS QUATRO DESELECOES — e o erro que custou a Core 2.1
#
#     A 2.1 tratou UMA deselecao, a de 0x0012EB06. Na tela, cada linha
#     visitada FICAVA AZUL para tras: a "segunda selecao", que este
#     projeto ja tinha visto antes.
#
#     Medido depois: o getter branco 0x00D2E948 tem CINCO chamadores.
#
#         0x00D2E9C0   0x00D2EA1C   0x00D2EAB0   0x00D2EB08   0x00D2ED3C
#
#     Quatro sao caminhos de deselecao — um por tecla de direcao — e os
#     quatro sao IDENTICOS instrucao por instrucao. O quinto
#     (0x00D2ED3C) cai dentro da regiao que o `patch_home_lista` ja
#     reescreveu, entao nao existe mais na imagem final.
#
#     E exatamente a regra que o proprio projeto registrou depois de
#     perder versoes com isso, em PROTOCOLO_GRAVACAO e em ESTADO_ATUAL:
#     "Um caminho corrigido, outro esquecido. Quando um patch muda a
#     aparencia de um objeto, enumerar TODOS os pontos que criam ou
#     repintam aquele objeto."
#
#     Eu tinha a regra escrita e nao a apliquei: achei um ponto, li o
#     codigo em volta, e parei. A ferramenta agora enumera, e o
#     autoteste CONTA — se aparecer um quinto caminho num firmware
#     diferente, ele recusa em vez de deixar passar.
# ---------------------------------------------------------------------------
DESELECOES = [
    (0x0012E9BE, 0x0012E9C0, 0x0012E9CA, "C1"),
    (0x0012EA1A, 0x0012EA1C, 0x0012EA26, "C2"),
    (0x0012EAAE, 0x0012EAB0, 0x0012EABA, "C3"),
    (0x0012EB06, 0x0012EB08, 0x0012EB12, "C4"),
]


# (offset, bytes esperados, bytes novos, descricao)
def _pontos():
    p = []
    for off, desc in [(0x0012EDAE, "A criacao: indice de paleta"),
                      (0x0012EB3E, "B selecao: indice de paleta")]:
        p.append((off, bytes([0x0C, 0x20]), bytes([0x05, 0x20]),
                  f"{desc}  movs r0,#0xc -> #5 (azul do Marte)"))
    for off, desc in [(0x0012EDB0, "A criacao"), (0x0012EB40, "B selecao")]:
        p.append((off, bytes([0x5E, 0x6A]), bytes([0x1E, 0x68]),
                  f"{desc}: ldr r6,[r3,#0x24] -> [r3]   array B -> array A"))
    for ldr, getter, setter, nome in DESELECOES:
        p.append((ldr, bytes([0x5B, 0x6A]), bytes([0x1B, 0x68]),
                  f"{nome} deselecao: ldr r3,[r3,#0x24] -> [r3]"))
        p.append((getter,
                  _bl(BIAS + getter, GETTER_BRANCO),
                  _bl(BIAS + getter, GETTER_PRETO),
                  f"{nome} deselecao: getter BRANCO -> getter PRETO"))
        p.append((setter,
                  _bl(BIAS + setter, SET_TEXT_COLOR),
                  _bl(BIAS + setter, SET_BG_COLOR),
                  f"{nome} deselecao: set_text_color -> set_bg_color"))
    for off, desc in [(0x0012EDBC, "A criacao"), (0x0012EB4C, "B selecao")]:
        p.append((off,
                  _bl(BIAS + off, SET_TEXT_COLOR),
                  _bl(BIAS + off, SET_BG_COLOR),
                  f"{desc}: set_style_text_color -> set_style_bg_color"))
    return p


def conta_deselecoes(d):
    """Conta os chamadores do getter BRANCO que ainda restam fora dos
    quatro caminhos conhecidos. Se houver algum, ha um caminho de
    deselecao que esta ferramenta nao trata — e a barra ficaria para tras
    naquele caminho."""
    alvo = GETTER_BRANCO
    conhecidos = {g for _, g, _, _ in DESELECOES}
    sobrando = []
    for o in range(0, len(d) - 3, 2):
        w1 = d[o] | (d[o + 1] << 8)
        if (w1 & 0xF800) != 0xF000:
            continue
        w2 = d[o + 2] | (d[o + 3] << 8)
        if (w2 & 0xD000) != 0xD000:
            continue
        S = (w1 >> 10) & 1
        j1 = (w2 >> 13) & 1
        j2 = (w2 >> 11) & 1
        i1 = (~(j1 ^ S)) & 1
        i2 = (~(j2 ^ S)) & 1
        v = (S << 24) | (i1 << 23) | (i2 << 22) | ((w1 & 0x3FF) << 12) \
            | ((w2 & 0x7FF) << 1)
        if S:
            v -= (1 << 25)
        if BIAS + o + 4 + v == alvo and o not in conhecidos:
            sobrando.append(BIAS + o)
    return sobrando


PONTOS = _pontos()

# guarda-corpo: o contexto em volta dos tres lugares.
CONTEXTO = [
    (0x0012EB02, bytes.fromhex("05eb8303"), "C: add.w r3,r5,r3,lsl#2"),
    (0x0012EB3A, bytes.fromhex("05eb8303"), "B: add.w r3,r5,r3,lsl#2"),
    (0x0012EDAA, bytes.fromhex("08eb8303"), "A: add.w r3,r8,r3,lsl#2"),
    (0x0012EB32, bytes.fromhex("1970"),     "B: strb r1,[r3] — o indice"),
]


def confere_contexto(d):
    for off, esperado, desc in CONTEXTO:
        achado = bytes(d[off:off + len(esperado)])
        if achado != esperado:
            return False, (f"0x{off:06X} ({desc}): achei {achado.hex()}, "
                           f"esperava {esperado.hex()}")
    return True, "ok"


def aplica(d):
    ok, msg = confere_contexto(d)
    if not ok:
        return False, msg
    ja = sum(1 for off, _, novo, _ in PONTOS
             if bytes(d[off:off + len(novo)]) == novo)
    if ja == len(PONTOS):
        return False, "patch ja aplicado"
    if ja:
        return False, f"{ja} de {len(PONTOS)} pontos ja aplicados: estado misto"
    for off, velho, _, desc in PONTOS:
        achado = bytes(d[off:off + len(velho)])
        if achado != velho:
            return False, (f"0x{off:06X} tem {achado.hex()}, esperado "
                           f"{velho.hex()} — {desc}")
    for off, _, novo, _ in PONTOS:
        d[off:off + len(novo)] = novo
    return True, "ok"


def autoteste():
    print("\n  AUTOTESTE — a selecao da home vira barra\n")
    o = os.path.join(RAIZ, ORIGINAL)
    if not os.path.exists(o):
        print(f"  FALTA: {o}")
        return 1
    orig = open(o, "rb").read()
    d = bytearray(orig)

    ok, msg = aplica(d)
    if not ok:
        print(f"  FALHOU: {msg}")
        return 1

    falhas = []
    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    esperado = sum(len(n) for _, _, n, _ in PONTOS)
    print(f"    bytes alterados        {len(dif)} (max {esperado})  "
          + ("OK" if len(dif) <= esperado else "FALHOU"))
    if len(dif) > esperado:
        falhas.append("mexeu em mais bytes do que os pontos declarados")

    # TODO `bl` de cor tem de apontar para set_style_bg_color
    alvos = [(0x0012EDBC, "A criacao"), (0x0012EB4C, "B selecao")]
    alvos += [(s, f"{n} deselecao") for _, _, s, n in DESELECOES]
    for off, desc in alvos:
        certo = bytes(d[off:off + 4]) == _bl(BIAS + off, SET_BG_COLOR)
        print(f"    {desc:14} -> bg_color  " + ("OK" if certo else "FALHOU"))
        if not certo:
            falhas.append(f"{desc}: bl nao aponta para set_style_bg_color")

    # TODA deselecao tem de buscar o PRETO
    for _, g, _, n in DESELECOES:
        certo = bytes(d[g:g + 4]) == _bl(BIAS + g, GETTER_PRETO)
        print(f"    {n} deselecao -> PRETO  " + ("OK" if certo else "FALHOU"))
        if not certo:
            falhas.append(f"{n}: nao aponta para o getter preto")

    # TODO `ldr` tem de ler o array A (offset 0)
    lidos = [(0x0012EDB0, "A"), (0x0012EB40, "B")]
    lidos += [(l, n) for l, _, _, n in DESELECOES]
    for off, desc in lidos:
        hw = d[off] | (d[off + 1] << 8)
        imm = (hw >> 6) & 0x1F
        print(f"    {desc}: ldr offset {imm*4:#04x}    "
              + ("OK" if imm == 0 else "FALHOU"))
        if imm:
            falhas.append(f"{desc}: o ldr ainda le o array B")

    # NENHUM caminho de deselecao pode ter sobrado. Este e o teste que
    # a Core 2.1 nao tinha, e que teria pego o defeito antes da tela.
    sobra = [a for a in conta_deselecoes(d) if not (0x0012EC42 <= a - BIAS < 0x0012ED90)]
    print(f"    nenhuma deselecao sobrando  "
          + ("OK" if not sobra else f"FALHOU: {[hex(a) for a in sobra]}"))
    if sobra:
        falhas.append(f"caminhos de deselecao nao tratados: "
                      f"{[hex(a) for a in sobra]}")

    ok2, _ = aplica(d)
    print("    recusa 2a aplicacao    " + ("OK" if not ok2 else "FALHOU"))
    if ok2:
        falhas.append("aplicar duas vezes NAO foi recusado")

    print()
    if falhas:
        for f in falhas:
            print(f"  FALHA: {f}")
        print("\n  AUTOTESTE FALHOU")
        return 1
    print("  AUTOTESTE OK")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="a selecao da home vira barra (M-b, Etapa 2)")
    ap.add_argument("--in", dest="src")
    ap.add_argument("--out", dest="dst")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--autoteste", action="store_true")
    a = ap.parse_args()

    if a.autoteste:
        return autoteste()
    if not a.src:
        ap.error("--in e obrigatorio (ou use --autoteste)")
    if not a.dst and not a.dry_run:
        ap.error("--out e obrigatorio, ou use --dry-run")

    d = bytearray(open(a.src, "rb").read())
    if len(d) != TAMANHO:
        print(f"ERRO: {a.src} tem {len(d)} B, esperado {TAMANHO}",
              file=sys.stderr)
        return 1
    orig = bytes(d)

    print("\n  A SELECAO DA HOME VIRA BARRA  (M-b, Etapa 2)\n")
    ok, msg = aplica(d)
    if not ok:
        print(f"  ABORTADO: {msg}", file=sys.stderr)
        return 1

    print("  ALTERACOES")
    for off, velho, novo, desc in PONTOS:
        print(f"    0x{off:06X}  {velho.hex()} -> {novo.hex()}  {desc}")
    print()
    print("  RESULTADO")
    print("    selecionado   fundo da LINHA = paleta 5 = azul do Marte")
    print("    normal        fundo da LINHA = preto")
    print("    texto         branco SEMPRE — igual as outras 38 telas")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))
    if any(s <= PROIBIDO for s in secs):
        print("  ABORTADO: setor proibido (R1).", file=sys.stderr)
        return 1
    print("  nada abaixo de 0x00D000   OK")
    print(f"  sha256: {hashlib.sha256(bytes(d)).hexdigest()}\n")

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
