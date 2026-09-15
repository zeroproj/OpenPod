#!/usr/bin/env python3
"""
patch_extras_rota.py — o roteamento INTERNO do Extras: cada um dos seis
                       itens passa a abrir a tela certa.

O DEFEITO QUE ELE CONSERTA

    A Core 3.0.1 mostrou a lista dos seis com os textos certos, mas ao
    entrar (relato do mantenedor, no aparelho):

        Gravacao -> Alarme     Radio -> Imagem     Livro -> Dicionario
        Imagem, Bluetooth, Pastas -> NADA

    Alarme, Imagens e Dicionario eram os TRES destinos ORIGINAIS da
    pagina. Os ROTULOS mudaram; o ROTEAMENTO nao.

A CAUSA — rotulo e destino sao camadas separadas

    O enter da pagina compara o objeto focado contra o array, numa
    CADEIA DE TRES comparacoes fixas:

        00D2EFF6  ldr r3,[r4]      array A[0] -> item 0
        00D2EFFC  ldr r3,[r4,#4]   array A[1] -> item 1
        00D2F002  ldr r3,[r4,#8]   array A[2] -> item 2
        00D2F006  bne 0xD2F01A     nenhum     -> NADA

    Os itens 3, 4 e 5 caem no "nenhum". Bate exatamente com o relato.

A SOLUCAO — reaproveitar o despacho da HOME, sem reimplementar nada

    Os tres caminhos ja convergem para a mesma mensagem que a home usa:

        movs r3, #4
        mov  r2, r4        <- o indice
        movs r0, #0x53     <- a pagina de ORIGEM
        bl   0xD23510

    Trocando a ORIGEM para **1** (a home) e o INDICE para o indice que
    aquele item tem NA HOME, a mensagem cai no `page1_process` — e cada
    item executa EXATAMENTE a rotina de fabrica dele.

    Isso importa porque VARIOS destinos nao sao "abrir a pagina N":

        Gravacao  confere se ha arquivos antes (bl 0xCFE714, 0xD3EC50)
        Pastas    registra o page1_folder_build_cb (0x00D00DE1)

    Uma tabela de paginas puras pularia essa preparacao. Redespachar
    pela home nao pula nada.

A TABELA

        Extras 0  Gravacao       -> 9   (ver o AVISO abaixo)
        Extras 1  Radio          -> 3
        Extras 2  Livro digital  -> 4
        Extras 3  Imagem         -> 5
        Extras 4  Bluetooth      -> 6
        Extras 5  Pastas         -> 8

⚠️ O AVISO — o "Gravacao" do Extras ainda NAO funciona, e o motivo

    O item que ABRE o Extras e o indice 2 da home (hoje rotulado
    "Gravacao"). Se o "Gravacao" de DENTRO do Extras redespachasse para
    o indice 2, ele reabriria o proprio Extras — LACO.

    Entao ele vai para o indice **9**, que o `page1_process` trata como
    fora de faixa: registra "-%s no ctrl_id" e volta. **No-op seguro**,
    conferido em 0x00D012E2.

    Isto se resolve sozinho no passo seguinte, quando a home ganhar um
    item "Extras" PROPRIO e o indice 2 voltar a ser a Gravacao de
    verdade. Nao e um defeito escondido: e uma consequencia declarada de
    o Extras ainda entrar por uma porta emprestada.

O ALINHAMENTO — o mesmo erro que quase foi para o aparelho na Core 2.0

    `0x00D2EFF6` e 2 mod 4, e a tabela precisa de alinhamento 4 para o
    `adr` funcionar. O codigo montado comeca em `0x00D2EFF8`, e o byte
    de `0x00D2EFF6` vira NOP.

USO
    python3 tools/patch_extras_rota.py --in <e.bin> --out <s.bin>
    python3 tools/patch_extras_rota.py --autoteste

DEPENDENCIAS
    Python 3 e `clang` (via tools/asm.py).

LIMITACOES
    - depende do `patch_extras.py` ter rodado antes: e ele que faz a
      pagina ter 6 itens;
    - o item Gravacao do Extras e no-op ate a home ser reduzida;
    - o `strb r4,[indice]` que o codigo antigo fazia depois do despacho
      deixa de acontecer. A navegacao ja mantem esse global, e o valor
      gravado era o mesmo que ja estava la.
"""

import argparse, hashlib, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asm import monta

RAIZ     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = "firmware/ORIGINAL/GN438_original.bin"
PROIBIDO = 0x0000D000
TAMANHO  = 0x200000
BIAS     = 0x00C00000

INI      = 0x0012EFF6          # o `ldr r3,[r4]` da cadeia
FIM      = 0x0012F024          # exclusivo — depois do `b 0xd2f00a` do item 1
ESPACO   = FIM - INI           # 46 bytes
NOP      = b"\x00\xbf"
DESLOC   = 2                   # o NOP de alinhamento
BASE     = BIAS + INI + DESLOC # 0x00D2EFF8 — MULTIPLO DE 4
assert BASE % 4 == 0

DESPACHA = 0x00D23510          # o despachante, o mesmo da home
IDX_GLOB = 0x00823D84          # o indice do Extras
POOL_IDX = 0x0012F090          # um pool que ja guarda IDX_GLOB
TABELA   = [9, 3, 4, 5, 6, 8]  # Extras -> indice equivalente NA HOME
ETIQUETA = 0x00200000

CONTEXTO = [
    (0x0012EFEE, bytes.fromhex("18f03dfa"), "bl 0xD4746C, logo antes"),
    (0x0012EFF6, bytes.fromhex("2368"),     "ldr r3,[r4] — inicio da cadeia"),
    (0x0012F024, bytes.fromhex("174b"),     "ldr r3,[pc,#0x5c] — logo depois"),
    (POOL_IDX,   IDX_GLOB.to_bytes(4, "little"), "o pool do indice"),
]


def _bl(origem, alvo):
    off = alvo - (origem + 4)
    v = off & 0x1FFFFFF
    S = (v >> 24) & 1
    i1 = (v >> 23) & 1
    i2 = (v >> 22) & 1
    w1 = 0xF000 | (S << 10) | ((v >> 12) & 0x3FF)
    w2 = (0xD000 | (((~i1 ^ S) & 1) << 13) | (((~i2 ^ S) & 1) << 11)
          | ((v >> 1) & 0x7FF))
    return bytes([w1 & 0xFF, w1 >> 8, w2 & 0xFF, w2 >> 8])


def _imm_bl(b, i):
    w1 = b[i] | (b[i + 1] << 8)
    if (w1 & 0xF800) != 0xF000:
        return None
    w2 = b[i + 2] | (b[i + 3] << 8)
    if (w2 & 0xD000) != 0xD000:
        return None
    S = (w1 >> 10) & 1
    j1 = (w2 >> 13) & 1
    j2 = (w2 >> 11) & 1
    i1 = (~(j1 ^ S)) & 1
    i2 = (~(j2 ^ S)) & 1
    v = ((S << 24) | (i1 << 23) | (i2 << 22)
         | ((w1 & 0x3FF) << 12) | ((w2 & 0x7FF) << 1))
    return v - (1 << 25) if S else v


def codigo():
    """Monta, e depois reencoda o `bl` — o clang nao subtrai o PC de
    simbolo absoluto (a mesma armadilha do patch_home_lista)."""
    pc_ldr = (BASE + 4) & ~3
    desloc_pool = (BIAS + POOL_IDX) - pc_ldr
    if desloc_pool % 4 or not (0 <= desloc_pool // 4 <= 255):
        raise RuntimeError(f"o pool do indice esta fora do alcance do ldr")
    fonte = f""".syntax unified
.thumb
DESPACHA = {ETIQUETA}

    ldr   r2, [pc, #{desloc_pool}]   @ = 0x{IDX_GLOB:08X}
    ldrb  r2, [r2]                   @ r2 = indice do Extras, 0..5
    adr   r3, TAB
    ldrb  r2, [r3, r2]               @ r2 = o indice equivalente NA HOME
    movs  r3, #4
    movs  r1, #2
    movs  r0, #1                     @ pagina 1 = a home
    bl    DESPACHA
    pop   {{r4, r5, r6, pc}}
    .p2align 2
TAB:
    .byte {", ".join(str(v) for v in TABELA)}
    .byte 0, 0
"""
    b = bytearray(monta(fonte))
    # reencoda o bl
    achou = False
    for i in range(0, len(b) - 3, 2):
        if _imm_bl(b, i) == ETIQUETA:
            b[i:i + 4] = _bl(BASE + i, DESPACHA)
            achou = True
            break
    if not achou:
        raise RuntimeError("nao achei o `bl` da etiqueta")
    b = bytes(b)
    cabe = ESPACO - DESLOC
    if len(b) > cabe:
        raise RuntimeError(f"o codigo tem {len(b)} B e so cabem {cabe}")
    return NOP + b + NOP * ((cabe - len(b)) // 2)


def confere_contexto(d):
    for off, esperado, desc in CONTEXTO:
        achado = bytes(d[off:off + len(esperado)])
        if achado != esperado:
            return False, (f"0x{off:06X} ({desc}): achei {achado.hex()}, "
                           f"esperava {esperado.hex()}")
    return True, "ok"


def aplica(d):
    novo = codigo()
    if bytes(d[INI:FIM]) == novo:
        return False, "patch ja aplicado"
    ok, msg = confere_contexto(d)
    if not ok:
        return False, msg
    d[INI:FIM] = novo
    return True, "ok"


def autoteste():
    print("\n  AUTOTESTE — o roteamento interno do Extras\n")
    o = os.path.join(RAIZ, ORIGINAL)
    if not os.path.exists(o):
        print(f"  FALTA: {o}")
        return 1
    orig = open(o, "rb").read()
    d = bytearray(orig)
    falhas = []

    b = codigo()
    util = len(b.rstrip(b"\x00\xbf"))

    def chk(nome, cond):
        print(f"    {nome:34} " + ("OK" if cond else "FALHOU"))
        if not cond:
            falhas.append(nome)

    chk(f"codigo cabe ({util} B em {ESPACO} B)", util <= ESPACO)
    chk(f"base multipla de 4 (0x{BASE:08X})", BASE % 4 == 0)

    ok, msg = aplica(d)
    if not ok:
        print(f"  FALHOU: {msg}")
        return 1

    # o `bl` tem de apontar para o despachante
    pos = None
    for i in range(DESLOC, len(b) - 3, 2):
        v = _imm_bl(b, i)
        if v is not None and BASE + (i - DESLOC) + 4 + v == DESPACHA:
            pos = i
            break
    chk("o `bl` aponta para 0xD23510", pos is not None)

    # a tabela tem de estar 4-alinhada e com os valores certos
    tab = b.find(bytes(TABELA))
    end_tab = BIAS + INI + tab
    chk("a tabela esta 4-alinhada", tab >= 0 and end_tab % 4 == 0)
    chk(f"a tabela = {TABELA}",
        tab >= 0 and list(b[tab:tab + 6]) == TABELA)

    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    chk("tudo dentro da regiao", all(INI <= i < FIM for i in dif))
    chk("nada abaixo de 0x00D000", all(i > PROIBIDO for i in dif))

    ok2, _ = aplica(d)
    chk("recusa 2a aplicacao", not ok2)

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
        description="o roteamento interno do Extras")
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

    print("\n  O ROTEAMENTO INTERNO DO EXTRAS\n")
    ok, msg = aplica(d)
    if not ok:
        print(f"  ABORTADO: {msg}", file=sys.stderr)
        return 1

    b = codigo()
    util = len(b.rstrip(b"\x00\xbf"))
    print(f"  REGIAO   0x{INI:06X}..0x{FIM-1:06X}   {ESPACO} B")
    print(f"    a cadeia de 3 comparacoes sai; entram {util} B + NOP")
    print()
    print("  A TABELA — Extras -> indice equivalente NA HOME")
    nomes = ["Gravacao", "Radio", "Livro digital", "Imagem",
             "Bluetooth", "Pastas"]
    for i, (n, v) in enumerate(zip(nomes, TABELA)):
        extra = "   <- no-op ate a home ser reduzida" if v == 9 else ""
        print(f"    {i}  {n:14} -> {v}{extra}")
    print()
    print("  Cada item executa a rotina DE FABRICA dele, com preparacao")
    print("  (Gravacao confere arquivos; Pastas registra o build_cb)")
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
