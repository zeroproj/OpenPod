#!/usr/bin/env python3
"""
fab_barra_titulo.py — item 3 da ficha 002 (Reload 1.0 RC3): "OpenPod" no
centro da barra da home, alinhado com o relogio e a bateria.

PROPOSITO

    A home nao tem uma "faixa": e uma folha de imagem com o relogio e a
    bateria desenhados por cima, e o que existe no meio dela e o rotulo do
    icone de cartao SD. Este item troca esse rotulo por um texto, o
    centraliza, e alinha a bateria com o resto da barra.

    Quatro bytes viram codigo, quatro viram dados, e um imediato muda:

        0x1226BA  mvn r2,#0x1d  ->  movs r2,#6 ; nop
                   x_ofs = -30 -> +6. Com o rotulo no centro, o deslocamento
                   que o alinhamento de fabrica usava para grudar no canto
                   direito empurraria "OpenPod" para fora da tela. A revisao
                   R0 pôs +4; na foto do aparelho (R1, 2026-10-23) o titulo
                   ainda ficava torto, e +6 e o que centra entre o relogio
                   (a esquerda) e a bateria (a direita): x 44..96, ~10 px de
                   cada lado.

        0x1226BE  movs r1,#3    ->  movs r1,#2
                   LV_ALIGN_TOP_RIGHT -> LV_ALIGN_TOP_MID.

        0x1226CA  bl 0x00D4D12E ->  nop ; nop
                   deixa de aplicar a fonte de icones: o rotulo passa a usar
                   a fonte do tema, a mesma do relogio. E o que faz "OpenPod"
                   sair como texto em vez de vir como glifo.

        0x1226F4  0x00C5D614    ->  0x00DA7040
                   o ponteiro do texto, que passa a apontar para a string
                   nova no lote 0x1A7040.

        0x12260E  movs r2,#0    ->  movs r2,#2      (R1)
                   o y da bateria. Em `view_icon_create` (0x00D225B0) a
                   bateria nasce em `set_pos(bat, 107, 0)` — y = 0, enquanto o
                   relogio e o titulo nascem com y_ofs 2. Na foto do aparelho
                   a bateria ficava ~1,5 px acima dos dois. Este e o unico
                   ponto que mexe FORA do rotulo: a funcao e compartilhada,
                   entao vale para todas as telas que mostram bateria.

    E a string, 8 bytes:

        0x1A7040  "OpenPod\\0",  o resto do lote em 0xFF

    Nada mais. O rotulo continua sendo criado nos mesmos lugares, nas
    mesmas condicoes — e isso e comportamento de fabrica, aceito pela ficha:
    sem cartao SD, a home fica sem titulo, porque o rotulo e o rotulo do
    icone do cartao.

PREMISSAS, conferidas ANTES de escrever qualquer byte

    A ficha pede recusa (D3) e nao aceitacao. Se UMA premissa falhar, a
    ferramenta sai com codigo diferente de zero, sem criar o arquivo de
    saida e sem tocar na entrada:

      - a imagem tem 2 MiB;
      - a rotina do rotulo (0x1226AC..0x1226F8) e a de fabrica, inteira.
        Sao 0x4C bytes: os quatro pontos que esta ferramenta troca, o resto
        do codigo do rotulo, e o pool com o ponteiro do texto. Conferir so
        os quatro pontos deixaria passar um rotulo que ja nao e o da ficha —
        e o texto novo apareceria em um rotulo com outra geometria;
      - a funcao da bateria (0x1225B0..0x1226AC) e a de fabrica, inteira: o
        `view_icon_create` do icone, do `push` ate o `pop`, mais o pool. E a
        regiao onde mora o y; sem ela, um `movs r2,#0` em outro lugar seria
        lido como "a bateria" sem ser a bateria;
      - os TRES fatos que a R1 nomeia, um a um e legiveis: 0x12260E =
        `0022` (o y de fabrica), 0x122612 = `6b21` (o x = 107), e o `bl` de
        0x122614 ainda decodificando para 0x00D4A2D4 (lv_obj_set_pos). Sao
        eles que dizem que o imediato que a ferramenta troca e mesmo o y
        daquela chamada;
      - o `bl` da fonte (0x1226CA) ainda decodifica para 0x00D4D12E. E o
        `bl` que vira `nop`; sem saber que era ele, a troca seria um
        chute sobre 4 bytes de pool;
      - os DOIS chamadores do rotulo (0x123898, na criacao, e 0x123E9C, na
        recriacao depois de inserir o cartao) ainda chamam 0x00D226AC. Sao
        eles que dizem onde o rotulo existe; sem os dois, o titulo poderia
        sumir ou aparecer em telas que a ficha nao mediu;
      - o lote 0x1A7040..0x1A7050 esta virgem (todo 0xFF);
      - `--em`, se vier, e o endereco fixo desta ferramenta.

SEGURANCA DA ESCRITA

    `--out` e recusado quando aponta para a propria entrada — mesmo
    caminho, symlink ou hardlink (`os.path.samefile`, achado 001-R1).
    Sem isso, um link com outro nome passaria pela comparacao de caminho
    e a gravacao escreveria por cima da entrada.

    E so se escreve DENTRO de: 0x1226BA..0x1226C0, 0x1226CA..0x1226CE,
    0x1226F4..0x1226F8, 0x12260E..0x122610 e 0x1A7040..0x1A7050. Qualquer
    byte fora disso e recusa, sem gravar.

USO

    python3 tools/fab_barra_titulo.py --in <entrada.bin> --out <saida.bin>
                                     [--em 0x1a7040] [--dry-run]

DEPENDENCIAS

    Python 3 (stdlib). Nao abre USB, nao grava no aparelho.

LIMITACOES

    - so serve na imagem que a ficha mediu: qualquer outra e recusada, mesmo
      que os enderecos existam;
    - o titulo so aparece na home (e na pagina 0x51, se alcancavel) e
      somente com cartao SD presente. Fora disso a home fica sem titulo —
      comportamento de fabrica do rotulo, aceito pela ficha;
    - o texto novo nao tem acentuacao, maiuscula nem caixa alta alem do
      proprio nome; ele vai na fonte do tema, nao na de icones, entao o
      desenho exato depende do tema que a fabrica traz;
    - o y da bateria vale para TODA tela que mostra bateria, nao so para a
      home: a funcao que cria o icone e uma so. Nas telas onde a barra tem
      outros elementos, o deslocamento de 2 px e o mesmo que o relogio ja
      usa — foi o que a foto pediu — mas o unico lugar onde da para ver o
      resultado e a home;
    - depois de aplicada, rodar de novo sobre a saida e recusado (o lote ja
      nao esta virgem). E o comportamento correto: a ferramenta e feita
      para a receita, uma vez.
"""

import argparse
import hashlib
import os
import struct
import sys

XIP = 0x00C00000
TAMANHO = 0x200000                          # 2 MiB

# --- o rotulo e o texto
ROTULO, ROTULO_FIM = 0x1226AC, 0x1226F8
ROTULO_SHA = "63620850b8be9e105b79ec6fffb9afb8ccbe5731e05751fe9b411d9d862e1d4d"
SET_TEXT_FONT = 0x00D4D12E
CHAMADORES = (0x123898, 0x123E9C)          # criacao e recriacao, com cartao
TEXTO = 0x1A7040                            # XIP 0x00DA7040
TEXTO_LOTE = 0x10
TEXTO_CONTEUDO = b"OpenPod\0"
EM_PADRAO = TEXTO

# --- a bateria (R1): view_icon_create, 0x00D225B0, funcao compartilhada
BATERIA, BATERIA_FIM = 0x1225B0, 0x1226AC    # do push ate o pool,exclusive
BATERIA_SHA = "e207ef1605da18faacaef398cc3c62c6eb0eea326d5dc0a149985c0e4f04b8e9"
BATERIA_Y = 0x12260E                        # movs r2,#y  (o ponto que muda)
BATERIA_X = 0x122612                        # movs r1,#107
BATERIA_X_FABRICA = bytes.fromhex("6b21")
BATERIA_POS = 0x122614                      # bl lv_obj_set_pos
SET_POS = 0x00D4A2D4

# --- os cinco pontos: (endereco, fabrica, RC3, o que muda)
PONTOS = (
    (0x1226BA, bytes.fromhex("6ff01d02"),
     bytes.fromhex("062200bf"),
     "x_ofs -30 -> +6 px (R1: centro entre relogio e bateria)"),
    (0x1226BE, bytes.fromhex("0321"),
     bytes.fromhex("0221"), "alinhar TOP_RIGHT -> TOP_MID"),
    (0x1226CA, bytes.fromhex("2af030fd"),
     bytes.fromhex("00bf00bf"), "fonte de icones -> a do tema (2 nop)"),
    (0x1226F4, struct.pack("<I", 0x00C5D614),
     struct.pack("<I", XIP + TEXTO), 'o texto vira "OpenPod"'),
    (BATERIA_Y, bytes.fromhex("0022"),
     bytes.fromhex("0222"),
     "bateria: y_ofs 0 -> 2 (R1: a mesma altura do relogio)"),
)


# ---------------------------------------------------------------------------
# Thumb-2: `bl` de 32 bits (T1). A premissa e sobre o ALVO do salto, e o
# alvo so se le decodificando — comparar bytes crus nao diz para onde o
# aparelho vai.
# ---------------------------------------------------------------------------

def bl_alvo(b, a):
    """offset no arquivo -> endereco XIP de um `bl` de 32 bits, ou None."""
    h1, h2 = struct.unpack_from("<HH", b, a)
    if (h1 & 0xF800) != 0xF000 or (h2 & 0xD000) != 0xD000:
        return None
    S = (h1 >> 10) & 1
    J1, J2 = (h2 >> 13) & 1, (h2 >> 11) & 1
    I1, I2 = 1 - (J1 ^ S), 1 - (J2 ^ S)
    off = (S << 24) | (I1 << 23) | (I2 << 22) | ((h1 & 0x3FF) << 12) \
        | ((h2 & 0x7FF) << 1)
    if S:
        off -= 1 << 25
    return XIP + a + 4 + off


# ---------------------------------------------------------------------------
# premissas
# ---------------------------------------------------------------------------

def confere_bl(d, a, esperado, nome):
    alvo = bl_alvo(d, a)
    if alvo == esperado:
        return []
    return [f"{nome} 0x{a:06X} chama "
            f"{'nada' if alvo is None else f'0x{alvo:08X}'}, esperado "
            f"0x{esperado:08X}"]


def confere_lote(d, ini, tam, nome):
    ocupado = [i for i in range(ini, ini + tam) if d[i] != 0xFF]
    if ocupado:
        return [f"{nome} 0x{ini:06X}..0x{ini + tam:06X}: "
                f"{len(ocupado)} byte(s) fora do 0xFF, o primeiro em "
                f"0x{ocupado[0]:06X} — o lote tem de estar virgem"]
    return []


def confere_premissas(d):
    """TODAS as premissas da ficha. Devolve a lista de erros (vazia = ok)."""
    erros = []
    if len(d) != TAMANHO:
        return [f"a imagem tem {len(d)} bytes, esperado {TAMANHO} (2 MiB)"]

    got = hashlib.sha256(
        bytes(d[ROTULO:ROTULO_FIM])).hexdigest()
    if got != ROTULO_SHA:
        erros.append(f"o rotulo 0x{ROTULO:06X}..0x{ROTULO_FIM:06X} (sha256 "
                     f"{got[:16]}..., esperado {ROTULO_SHA[:16]}...) nao e o "
                     f"de fabrica")
    for a, esperado, novo, o_que in PONTOS:
        if bytes(d[a:a + len(esperado)]) != esperado:
            erros.append(f"ponto 0x{a:06X} ({o_que}) = "
                         f"{bytes(d[a:a + len(esperado)]).hex()}, esperado "
                         f"{esperado.hex()}")

    # a funcao da bateria inteira, e os tres fatos que a R1 nomeia. O sha
    # pega a regiao inteira (inclusive as bordas); os tres checks dao a
    # mensagem legivel de "o que era este lugar".
    got = hashlib.sha256(bytes(d[BATERIA:BATERIA_FIM])).hexdigest()
    if got != BATERIA_SHA:
        erros.append(f"a funcao da bateria 0x{BATERIA:06X}..0x{BATERIA_FIM:06X} "
                     f"(sha256 {got[:16]}..., esperado {BATERIA_SHA[:16]}...) "
                     f"nao e a de fabrica")
    if bytes(d[BATERIA_X:BATERIA_X + 2]) != BATERIA_X_FABRICA:
        erros.append(f"0x{BATERIA_X:06X} (o x da bateria) = "
                     f"{bytes(d[BATERIA_X:BATERIA_X + 2]).hex()}, esperado "
                     f"{BATERIA_X_FABRICA.hex()}")
    erros += confere_bl(d, BATERIA_POS, SET_POS, "o set_pos da bateria")

    erros += confere_bl(d, 0x1226CA, SET_TEXT_FONT, "o bl da fonte")
    for i, a in enumerate(CHAMADORES):
        erros += confere_bl(d, a, XIP + ROTULO,
                            f"o chamador {i + 1} do rotulo")
    erros += confere_lote(d, TEXTO, TEXTO_LOTE, "lote do texto")
    return erros


PERMITIDO = [(TEXTO, TEXTO + TEXTO_LOTE)] + \
    [(a, a + len(novo)) for a, _, novo, _ in PONTOS]


# ---------------------------------------------------------------------------
# a escrita
# ---------------------------------------------------------------------------

def escreve_texto(d):
    """`OpenPod\\0` no lote, o resto em 0xFF."""
    if len(TEXTO_CONTEUDO) > TEXTO_LOTE:
        raise ValueError(f"o texto tem {len(TEXTO_CONTEUDO)} bytes e o lote "
                         f"{TEXTO_LOTE}")
    d[TEXTO:TEXTO + TEXTO_LOTE] = TEXTO_CONTEUDO + b"\xFF" * (
        TEXTO_LOTE - len(TEXTO_CONTEUDO))


def escreve_pontos(d):
    """Os cinco pontos: quatro bytes viram codigo, quatro viram dados, e o
    y da bateria sai de 0 para 2."""
    for a, esperado, novo, o_que in PONTOS:
        if bytes(d[a:a + len(esperado)]) != esperado:
            raise ValueError(f"ponto 0x{a:06X} nao e o de fabrica ({o_que})")
        d[a:a + len(novo)] = novo


def confere_resultado(d, orig):
    """Relê o que foi escrito e confere, sem confiar na escrita."""
    erros = []
    for a, esperado, novo, o_que in PONTOS:
        if bytes(d[a:a + len(novo)]) != novo:
            erros.append(f"0x{a:06X} nao recebeu o byte novo ({o_que})")
    texto = bytes(d[TEXTO:TEXTO + TEXTO_LOTE])
    if texto[:len(TEXTO_CONTEUDO)] != TEXTO_CONTEUDO:
        erros.append(f"o texto em 0x{TEXTO:06X} ficou {texto[:8]!r}, "
                     f"esperado {TEXTO_CONTEUDO!r}")
    if any(x != 0xFF for x in texto[len(TEXTO_CONTEUDO):]):
        erros.append(f"lixo depois do texto, em "
                     f"0x{TEXTO + len(TEXTO_CONTEUDO):06X}..")

    # o resto do rotulo e do pool tem de estar como na entrada
    trocados = set()
    for a, _, novo, _ in PONTOS:
        trocados |= set(range(a, a + len(novo)))
    for i in range(ROTULO, ROTULO_FIM + 4):
        if i not in trocados and d[i] != orig[i]:
            erros.append(f"o rotulo mudou fora dos quatro pontos, em "
                         f"0x{i:06X}")
            break

    # a funcao da bateria tambem: so o y pode ter mudado
    for i in range(BATERIA, BATERIA_FIM):
        if i not in trocados and d[i] != orig[i]:
            erros.append(f"a funcao da bateria mudou fora do y, em "
                         f"0x{i:06X}")
            break

    erros += confere_bl(d, BATERIA_POS, SET_POS, "o set_pos da bateria")
    erros += confere_bl(d, 0x123898, XIP + ROTULO, "o chamador 1 do rotulo")
    erros += confere_bl(d, 0x123E9C, XIP + ROTULO, "o chamador 2 do rotulo")
    return erros


def mesma_entrada(src, dst):
    """--out aponta para a propria entrada?

    Comparar caminho resolve so o caso literal. Um symlink ou um hardlink
    com outro nome passa pela comparacao e a gravacao vai DENTRO da
    entrada — que e o que a regra do projeto proibe (achado 001-R1,
    BAIXA). `samefile` pergunta ao sistema de arquivos qual arquivo e,
    nao como ele se chama.
    """
    if os.path.abspath(src) == os.path.abspath(dst):
        return True
    if not os.path.lexists(dst):          # saida ainda nao existe: nada a ver
        return False
    try:
        return os.path.samefile(src, dst)
    except OSError:                       # link pendurado, sem permissao
        return False


def main():
    ap = argparse.ArgumentParser(
        description='RC3 item 3: "OpenPod" no centro da barra da home')
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--em", default=None,
                    help=f"endereco do texto (tem de ser {EM_PADRAO:#x})")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.em is not None:
        try:
            em = int(a.em, 0)
        except ValueError:
            print(f"RECUSADO: --em {a.em!r} nao e um endereco.", file=sys.stderr)
            return 2
        if em != EM_PADRAO:
            print(f"RECUSADO: --em {em:#x}; o texto desta ferramenta esta "
                  f"em {EM_PADRAO:#x}, e o MAPA do build.py declara esse.",
                  file=sys.stderr)
            return 2

    if not os.path.exists(a.src):
        print(f"RECUSADO: {a.src} nao existe.", file=sys.stderr)
        return 2
    if mesma_entrada(a.src, a.dst):
        print("RECUSADO: --out e a propria entrada (mesmo caminho, symlink "
              "ou hardlink).", file=sys.stderr)
        return 2

    orig = open(a.src, "rb").read()
    d = bytearray(orig)

    print("=" * 72)
    print('OpenPod — RC3 item 3: "OpenPod" no centro, alinhado com o '
          'relogio e a bateria')
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n")

    # --- premissas, ANTES de qualquer escrita
    erros = confere_premissas(d)
    if erros:
        print("  RECUSADO — a entrada nao e a imagem de fabrica que a ficha mediu:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print("  entrada conferida:")
    print("    - 2 MiB")
    print(f"    - o rotulo 0x{ROTULO:06X}..0x{ROTULO_FIM:06X} e o de fabrica")
    print(f"    - a funcao da bateria 0x{BATERIA:06X}..0x{BATERIA_FIM:06X} e a "
          f"de fabrica, e o seu set_pos(bat, 107, y) esta no lugar")
    print(f"    - o `bl` da fonte em 0x1226CA ainda chama "
          f"0x{SET_TEXT_FONT:08X}")
    print(f"    - os dois chamadores do rotulo ainda chamam "
          f"0x{XIP + ROTULO:08X}")
    print(f"    - lote 0x{TEXTO:06X}..0x{TEXTO + TEXTO_LOTE:06X} virgem\n")

    try:
        escreve_texto(d)
        escreve_pontos(d)
    except ValueError as e:
        print(f"  RECUSADO — {e}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    print('  "OpenPod" — o rotulo do icone de cartao, agora texto')
    print(f"    texto  0x{TEXTO:06X}..0x{TEXTO + len(TEXTO_CONTEUDO):06X}  "
          f"{TEXTO_CONTEUDO!r} (XIP 0x{XIP + TEXTO:08X}), "
          "o resto do lote em 0xFF")
    for end, fabrica, novo, o_que in PONTOS:
        print(f"    0x{end:06X}  {fabrica.hex()} -> {novo.hex()}   {o_que}")
    print(f"    o resto de 0x{ROTULO:06X}..0x{ROTULO_FIM:06X} NAO tocado")
    print(f"    a funcao da bateria so mudou no y; x=107 e o set_pos em "
          f"0x{SET_POS:08X} continuam como na fabrica")
    print("    os dois chamadores continuam intactos: o rotulo nasce nas "
          "mesmas condicoes de fabrica\n")

    erros = confere_resultado(d, orig)
    if erros:
        print("  RECUSADO — a conferencia do resultado falhou:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print("  conferencia (os cinco pontos, o texto e o 0xFF depois dele, o "
          "resto do rotulo e da funcao da bateria, os dois chamadores): "
          "tudo OK\n")

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    fora = [i for i in dif if not any(a0 <= i < b0 for a0, b0 in PERMITIDO)]
    if fora:
        print(f"  RECUSADO: escreveu fora do permitido em "
              f"0x{min(fora):06X}..0x{max(fora):06X}", file=sys.stderr)
        return 1
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   setores: "
          + "  ".join(f"0x{s:06X}" for s in secs))

    if a.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    open(a.dst, "wb").write(bytes(d))
    print(f"  gravado: {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())