#!/usr/bin/env python3
"""
fab_barra_centro.py — item 1 da ficha 004 (Reload 1.0 RC4): relogio,
"OpenPod" e bateria no MEIO da barra superior.

PROPOSITO

    Na foto da RC3.1 o texto da barra superior ocupa y≈4..14 numa barra de
    16 px: o centro do texto fica em y=9 e o centro da barra em y=7,5.
    Ou seja, os tres estao 1,5 px para baixo — o que o decisor descreveu
    como "poderia subir um pouquinho... no meio da barra superior".

    A correcao sao SEIS BYTES: o `y_ofs` de tres `lv_obj_align`/`set_pos`
    que vivem todos na faixa `0x1`. Nenhum objeto novo, nenhuma alocacao,
    nenhum endereco novo. O desenho da barra (o degradê da RC3) nao e
    tocado: subir o texto nao muda uma unica cor da paleta.

OS TRES PONTOS (medidos, na RC3.1)

        0x1217D6   movs r3,#2  ->  movs r3,#0     relogio, y_ofs
        0x1226B6   movs r3,#2  ->  movs r3,#0     titulo "OpenPod", y_ofs
        0x12260E   movs r2,#2  ->  movs r2,#0     bateria, y

    Os dois primeiros sao `movs r3,#2` de `lv_obj_align(obj, ..., y_ofs)`,
    e o terceiro e o `y` de `lv_obj_set_pos(bat, 107, y)`. Os tres
    immediatos sao de 8 bits: `02` -> `00` e a instrucao nao muda de
    tamanho, entao nenhum endereco do aparelho se move.

    Detalhe que a ficha mediu e que importa para o risco D6: o y da
    bateria e o Argumento da `set_pos`, e nao um `y_ofs`. Na RC3 ele valia
    2 por causa da R1 da ficha 002, que subiu a bateria para a altura do
    relogio; em FABRICA ele e 0. Esta RC volta os tres a 0 — que e o que o
    pedido quer, e o que a foto mostra. O risco D6 (bateria encostando no
    topo em telas com outros elementos) e conhecido e aceito pela ficha.

POR QUE ISSO NAO QUEBRA A NAVEGACAO

    Os tres objetos sao Factory: o rotulo do cartao continua sendo criado
    nos mesmos lugares e nas mesmas condicoes (sem cartao SD, a home fica
    sem titulo — comportamento de fabrica, aceito pela ficha 002). So a
    coordenada vertical muda. A selecao da home nao passa por nenhum dos
    tres: ela acha o rotulo pelo indice no array B e pinta a cor do texto
    (docs/PLANO_HOME.md 1.3).

PREMISSAS, conferidas ANTES de escrever qualquer byte

    A ficha pede recusa (D3) e nao aceitacao. Se UMA premissa falhar, a
    ferramenta sai com codigo diferente de zero, sem criar o arquivo de
    saida e sem tocar na entrada:

      - a imagem tem 2 MiB;
      - os tres pontos estao com os bytes da RC3.1 (`0223`, `0223`,
        `0222`). So isso ja recusa o ORIGINAL, onde a bateria ainda esta
        em `0022`;
      - os TRES FATOS que dizem que estes immediatos sao mesmo o y:

            0x1217D2 = `0121`   o alinhamento do relogio
            0x1217D8 = `0322`   o x do relogio
            0x1217DA            `bl 0x00D4A3A2` = lv_obj_align
            0x1226BA = `062200bf`  o x_ofs do titulo (+6 px, a RC3.1)
            0x1226BE = `0221`      o alinhamento do titulo (TOP_MID)
            0x1226C0            `bl 0x00D4A3A2` = lv_obj_align
            0x122612 = `6b21`      o x da bateria (107 px)
            0x122614            `bl 0x00D4A2D4` = lv_obj_set_pos

        Sem o `bl` lido como ALVO, comparar bytes crus nao diria para onde
        o aparelho vai: e o alvo que diz que o imediato de 2 bytes antes
        dele e o `y` daquela chamada;
      - o TITULO INTEIRO da RC3 (0x1226AC..0x1226F8, 0x4C bytes) e o da
        RC3.1, sha256 preso. Sao os quatro pontos que a ficha 002 trocou
        (o `nop; nop` da fonte em 0x1226CA e o ponteiro do texto em
        0x1226F4) mais o resto do codigo do rotulo e o pool. A R0 desta
        ficha pediu exatamente esta cobertura: um `movs` trocado em um
        rotulo que ja nao e o da ficha escreveria o y no lugar errado sem
        nenhum erro visivel;
      - a FUNCAO DA BATERIA inteira (0x1225B0..0x1226AC) e a da RC3.1,
        sha256 preso. E a `view_icon_create`, compartilhada pelas telas que
        mostram bateria; e a regiao onde mora o y;
      - o DEGRADE da barra continua no lugar: o `bl` de 0x121724 ainda
        aponta para a rotina da RC3 (0x00DA7000). A entrada precisa ser a
        RC3, nao uma imagem qualquer com os mesmos bytes nos tres pontos;
      - o texto "OpenPod\\0" esta no lote 0x1A7040 e o resto do lote e
        0xFF. Sem o texto, o rotulo do centro apontaria para lixo;
      - os DOIS chamadores do rotulo (0x123898 e 0x123E9C) ainda chamam
        0x00D226AC — o titulo continua nascendo onde nascia.

    As regioes "tem de ser as da RC3" sao presas por sha256 em vez de
    coladas no fonte: 0x4C + 0xFC bytes de codigo no fonte seriam ruido, e
    o sha diz a mesma coisa sem chance de erro de digito. A conferencia
    com bytes crus continua existindo para o que ESTA ferramenta escreve.

CONFERENCIA DE SAIDA

    Apos escrever, a ferramenta relê os tres bytes, decodifica de novo os
    tres `bl` (para dizer que o texto dos dois `align` e da `set_pos`
    continua no lugar) e confere que o resto das tres regioes nao mudou.

SEGURANCA DA ESCRITA

    `--out` e recusado quando aponta para a propria entrada — mesmo
    caminho, symlink ou hardlink (`os.path.samefile`, achado 001-R1).
    Sem isso, um link com outro nome passaria pela comparacao de caminho
    e a gravacao escreveria por cima da entrada.

    E so se escreve DENTRO de: 0x1217D6..0x1217D8, 0x1226B6..0x1226B8 e
    0x12260E..0x122610. Qualquer byte fora disso e recusa, sem gravar.

USO

    python3 tools/fab_barra_centro.py --in <entrada.bin> --out <saida.bin>
                                      [--dry-run]

DEPENDENCIAS

    Python 3 (stdlib). Nao abre USB, nao grava no aparelho.

LIMITACOES

    - so serve na imagem que a ficha mediu: a RC3.1. Qualquer outra e
      recusada, mesmo que os enderecos existam;
    - o y novo e 0, que e a MESMA posicao vertical do relogio e do titulo
      na RC1/RC2 e da bateria em fabrica. Quem mediu o resultado foi a foto
      da RC3.1; o aparelho nao foi testado com esta RC;
    - o deslocamento vale para TODA tela que mostra relogio, titulo e
      bateria, e nao so para a home: as duas rotinas que os posicionam sao
      compartilhadas. Nas telas onde a barra tem outros elementos o
      deslocamento e o mesmo de 2 px, que foi o que a foto pediu;
    - o titulo continua sendo o rotulo do icone de cartao: sem cartao SD
      a home fica sem "OpenPod" no centro. Comportamento de fabrica,
      aceito pela ficha 002;
    - depois de aplicada, rodar de novo sobre a saida e recusado (os tres
      pontos ja estao em `00`). E o comportamento correto: a ferramenta e
      feita para a receita, uma vez.
"""

import argparse
import hashlib
import os
import struct
import sys

XIP = 0x00C00000
TAMANHO = 0x200000                          # 2 MiB

# --- as tres regioes presas por sha256 (a entrada e a RC3.1, 286e8ba8)
REGIOES = (
    (0x1217D0, 0x1217DE,                    # o relogio e o seu align
     "9a85aa1e48d03042d00972172dadcdcd7a27a3362e3f2327e7f0163a851e8e37",
     "o align do relogio"),
    (0x1225B0, 0x1226AC,                    # view_icon_create (bateria)
     "50d392f2692a039bcb30d1d4b45296d1f99d9634ffa925c490eed1b2ea571657",
     "a funcao da bateria"),
    (0x1226AC, 0x1226F8,                    # o rotulo do titulo + pool
     "894b5d63ee7203dfd8b8e10845901836b2aa246590f7451cd9edb2227f9468be",
     "o rotulo do titulo"),
)

# --- os tres pontos que mudam: (endereco, RC3.1, RC4, o que e)
PONTOS = (
    (0x1217D6, bytes.fromhex("0223"), bytes.fromhex("0023"),
     "relogio: y_ofs 2 -> 0, o centro da barra"),
    (0x1226B6, bytes.fromhex("0223"), bytes.fromhex("0023"),
     'titulo "OpenPod": y_ofs 2 -> 0, o centro da barra'),
    (0x12260E, bytes.fromhex("0222"), bytes.fromhex("0022"),
     "bateria: y 2 -> 0, o centro da barra (o valor de fabrica)"),
)

# --- os TRES FATOS que dizem que o imediato trocado e o y daquela chamada
FATOS = (
    (0x1217D2, bytes.fromhex("0121"), "o alinhamento do relogio"),
    (0x1217D8, bytes.fromhex("0322"), "o x do relogio"),
    (0x1226BA, bytes.fromhex("062200bf"), "o x_ofs do titulo (+6 px, RC3.1)"),
    (0x1226BE, bytes.fromhex("0221"), "o alinhamento do titulo (TOP_MID)"),
    (0x122612, bytes.fromhex("6b21"), "o x da bateria (107 px)"),
)

# --- os `bl`: o alvo e o que da sentido ao imediato que vem antes. Os tres
# primeiros sao os da ficha; os tres seguintes dizem que a entrada e a RC3.1
# (o degradê no lugar, e o titulo ainda nascendo onde nascia).
ALVOS = (
    (0x1217DA, 0x00D4A3A2, "o align do relogio"),
    (0x1226C0, 0x00D4A3A2, "o align do titulo"),
    (0x122614, 0x00D4A2D4, "o set_pos da bateria"),
    (0x121724, 0x00DA7000, "o gancho do degradê da RC3"),
    (0x123898, 0x00D226AC, "o chamador 1 do rotulo"),
    (0x123E9C, 0x00D226AC, "o chamador 2 do rotulo"),
)

# --- o texto do titulo, no lote da RC3.1
TEXTO = 0x1A7040
TEXTO_LOTE = 0x10
TEXTO_CONTEUDO = b"OpenPod\0"
TEXTO_SHA = "84e9d82ae46d47ab9d0f97bd4352d97a154bca87aea8ec4e6a5e8631ec42bc7e"

PERMITIDO = [(a, a + len(novo)) for a, _, novo, _ in PONTOS]


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

def confere_sha(d, ini, tam, esperado, nome):
    got = hashlib.sha256(bytes(d[ini:ini + tam])).hexdigest()
    if got == esperado:
        return []
    return [f"{nome} 0x{ini:06X}..0x{ini + tam:06X} (sha256 {got[:16]}..., "
            f"esperado {esperado[:16]}...) — a regiao nao e a da RC3.1"]


def confere_bl(d, a, esperado, nome):
    alvo = bl_alvo(d, a)
    if alvo == esperado:
        return []
    return [f"{nome} 0x{a:06X} chama "
            f"{'nada' if alvo is None else f'0x{alvo:08X}'}, esperado "
            f"0x{esperado:08X}"]


def confere_premissas(d):
    """TODAS as premissas da ficha. Devolve a lista de erros (vazia = ok)."""
    erros = []
    if len(d) != TAMANHO:
        return [f"a imagem tem {len(d)} bytes, esperado {TAMANHO} (2 MiB)"]

    for a, esperado, novo, o_que in PONTOS:
        if bytes(d[a:a + len(esperado)]) != esperado:
            erros.append(f"ponto 0x{a:06X} ({o_que}) = "
                         f"{bytes(d[a:a + len(esperado)]).hex()}, esperado "
                         f"{esperado.hex()}")
    for a, esperado, o_que in FATOS:
        if bytes(d[a:a + len(esperado)]) != esperado:
            erros.append(f"0x{a:06X} ({o_que}) = "
                         f"{bytes(d[a:a + len(esperado)]).hex()}, esperado "
                         f"{esperado.hex()}")
    for ini, fim, esperado, nome in REGIOES:
        erros += confere_sha(d, ini, fim - ini, esperado, nome)
    for a, esperado, nome in ALVOS:
        erros += confere_bl(d, a, esperado, nome)

    erros += confere_sha(d, TEXTO, TEXTO_LOTE, TEXTO_SHA, "lote do texto")
    if bytes(d[TEXTO:TEXTO + len(TEXTO_CONTEUDO)]) != TEXTO_CONTEUDO:
        erros.append(f"o texto em 0x{TEXTO:06X} = "
                     f"{bytes(d[TEXTO:TEXTO + len(TEXTO_CONTEUDO)])!r}, "
                     f"esperado {TEXTO_CONTEUDO!r}")
    return erros


# ---------------------------------------------------------------------------
# a escrita
# ---------------------------------------------------------------------------

def escreve(d):
    """Os tres y: 2 -> 0. Nada mais."""
    for a, esperado, novo, o_que in PONTOS:
        if bytes(d[a:a + len(esperado)]) != esperado:
            raise ValueError(f"ponto 0x{a:06X} nao e o da RC3.1 ({o_que})")
        d[a:a + len(novo)] = novo
    return len(PONTOS)


def confere_resultado(d, orig):
    """Relê o que foi escrito e confere, sem confiar na escrita."""
    erros = []
    trocados = set()
    for a, _, novo, o_que in PONTOS:
        trocados |= set(range(a, a + len(novo)))
        if bytes(d[a:a + len(novo)]) != novo:
            erros.append(f"0x{a:06X} nao recebeu o byte novo ({o_que})")

    # o resto das tres regioes tem de estar como na entrada
    for ini, fim, _, nome in REGIOES:
        fora = [i for i in range(ini, fim)
                if i not in trocados and d[i] != orig[i]]
        if fora:
            erros.append(f"{nome} mudou fora dos tres y, em 0x{fora[0]:06X}")

    for a, esperado, nome in ALVOS:
        erros += confere_bl(d, a, esperado, nome)
    if bytes(d[TEXTO:TEXTO + TEXTO_LOTE]) != \
            bytes(orig[TEXTO:TEXTO + TEXTO_LOTE]):
        erros.append(f"o lote do texto em 0x{TEXTO:06X} mudou — esta "
                     f"ferramenta so mexe nos tres y")
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
        description="RC4 item 1: relogio, titulo e bateria no meio da barra")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

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
    print("OpenPod — RC4 item 1: relogio, titulo e bateria no meio da barra")
    print("=" * 72)
    print(f"  origem : {a.src}\n  destino: {a.dst}\n")

    # --- premissas, ANTES de qualquer escrita
    erros = confere_premissas(d)
    if erros:
        print("  RECUSADO — a entrada nao e a imagem da RC3.1 que a "
              "ficha mediu:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print("  entrada conferida:")
    print("    - 2 MiB")
    print("    - os tres pontos com os bytes da RC3.1 (y = 2 nos tres)")
    print("    - os tres `bl` (os dois `align` e a `set_pos`) nos alvos "
          "de fabrica")
    print("    - o gancho do degradê da RC3 ainda em 0x00DA7000 e os dois "
          "chamadores do rotulo")
    print("    - o align do relogio, a funcao da bateria e o rotulo do "
          "titulo inteiros\n")

    try:
        quantos = escreve(d)
    except ValueError as e:
        print(f"  RECUSADO — {e}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1

    print(f"  {quantos} pontos, {sum(len(n) for _, _, n, _ in PONTOS)} bytes:")
    for end, rc3, novo, o_que in PONTOS:
        print(f"    0x{end:06X}  {rc3.hex()} -> {novo.hex()}   {o_que}")
    print("    o desenho da barra (o degradê) NAO muda: nenhuma cor da "
          "paleta foi tocada")
    print("    nada mais na imagem muda: nem a CRIA_FAIXA, nem o rotulo, "
          "nem o texto\n")

    erros = confere_resultado(d, orig)
    if erros:
        print("  RECUSADO — a conferencia do resultado falhou:")
        for m in erros:
            print(f"    - {m}")
        print(f"\n  nada foi escrito em {a.dst}")
        return 1
    print("  conferencia (os tres bytes novos, os tres `bl` lidos de volta, o "
          "resto das tres regioes e o lote do texto): tudo OK\n")

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