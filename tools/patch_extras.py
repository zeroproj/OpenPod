#!/usr/bin/env python3
"""
patch_extras.py — a tela EXTRAS: a pagina 0x52 passa de 3 para 6 itens,
                  e a home ganha um caminho ate ela.

O ALVO

    Modelo do iPod nano 2G, decidido pelo mantenedor: a home com poucos
    itens, e o resto recolhido num submenu Extras.

        EXTRAS
          Gravacao   Radio    Livro digital
          Imagem     Bluetooth   Pastas

    Plano completo e medido: `docs/PLANO_EXTRAS.md`.

⚠️ ESTA E A CLASSE DE MUDANCA QUE JA FALHOU TRES VEZES AQUI

    `patch_extras`, `patch_extras_fix`, `patch_extras_fix2`: tres patches
    empilhados, e os itens NUNCA abriram no aparelho. Apagados na limpeza
    de 2026-09-14.

    A causa: esticar a contagem de itens de uma pagina mexe em ALOCACAO e
    aritmetica de ponteiro, e corrupcao de heap **nao aparece na
    verificacao byte a byte pos-gravacao**.

    O que mudou, e nao e coragem — e medicao:

      - a aritmetica esta em 8 PONTOS, todos localizados (§3-bis do plano);
      - o campo +0x24 da estrutura NAO e lido por ninguem: e folga real;
      - o TRANSBORDO DE PILHA foi achado ANTES de gravar, e contornado
        sem crescer a pilha;
      - a PAGINA NAO E A 0x53, e a 0x52 — os tres patches antigos diziam
        0x53. Medido na tabela do view_page_create.

A CORRECAO QUE MAIS IMPORTA — a pagina e a 0x52

    Tabela TBB do `view_page_create` em 0x00D23B34:

        pagina 0x51 (81) -> bl 0x00D3CAA8
        pagina 0x52 (82) -> bl 0x00D2F0A0   <- page_home_menu_create
        pagina 0x53 (83) -> outra coisa

    Toda referencia a "pagina 0x53" nos documentos antigos deste projeto
    esta errada por um.

AS DEZ EDICOES NA PAGINA, e por que cada uma

    1-2   malloc/memset 0x28 -> 0x4C
          3 arrays x 6 itens x 4 = 0x48, mais 4 de folga = 0x4C

    3-8   array B: +0x0C -> +0x18    (6 pontos, 1 escrita e 5 leituras)
    9-10  array C: +0x18 -> +0x30    (2 pontos)

          O passo entre arrays e (n_itens * 4). Com 3 itens era 0x0C;
          com 6 e 0x18.

          ⚠️ O offset NOVO do array B (+0x18) COLIDE com o offset ANTIGO
          do array C. Por isso a ferramenta calcula TODAS as posicoes a
          partir da imagem de entrada, e so depois escreve.

    11    cmp r6,#3 -> #6     o limite do laco
    12    cmp r6,#2 -> #5     qual item recebe a borda de baixo
    13-14 cmp r3,#2 -> #5     os dois limites de navegacao

O TRANSBORDO DE PILHA, contornado sem crescer a pilha

        00D2F0A6  sub sp, #0x1c          28 bytes
        00D2F20E  ldm.w r3,{r0,r1,r2}    copia TRES ids para sp+0xC
        00D2F2B6  add r3, sp, #0xc       o laco recarrega o ponteiro AQUI

    Copiar 6 ids ocuparia sp+0xC..sp+0x24, e a pilha so tem 0x1C:
    TRANSBORDARIA — e transbordo de pilha e da mesma familia do defeito
    que nao aparece na verificacao pos-gravacao.

    A saida SIMPLIFICA em vez de complicar: o laco passa a ler o ponteiro
    do POOL, apontando direto para a tabela nova. A copia continua
    acontecendo, fica inofensiva, e nada transborda.

        0x0012F2B6  03 ab  add r3,sp,#0xc  ->  1b 4b  ldr r3,[pc,#108]
        0x0012F324  o pool: 0x00C486E8     ->  a tabela nova

    O pool fica a 108 bytes do `pc` alinhado — dentro dos 1020 do `ldr`
    de 16 bits. Conferido.

O ROTEAMENTO — sem ele a versao NAO SERIA TESTAVEL

    A pagina 0x52 esta MORTA no firmware de fabrica: nada chega nela.
    Expandi-la e gravar produziria uma tela que nao abre por lugar
    nenhum — e um teste que nao testa. Foi assim que as tentativas
    antigas se perderam.

    Um destino da tabela TBH abre uma pagina assim:

        movs r3, #<pagina>  ;  movs r2,#0  ;  movs r1,#2  ;  movs r0,#1
        b 0x00D011F2        -> pop e b.w 0xD0DAE0

    Confirmado por cruzamento: o destino do indice 7 (Configurar) seta
    r3 = 0x28, e PAGINAS.md registra a pagina 40 = 0x28 como
    `page_set_menu` — o Configurar.

    Esta ferramenta reescreve o comeco do destino do INDICE 2 (hoje
    Gravacao, 0x00D010F6) com 10 bytes. O resto daquele destino vira
    codigo morto: so era alcancavel pela entrada 2 do TBH.

    EFEITO: o item "Gravacao" da home passa a ABRIR A LISTA DE SEIS. O
    rotulo fica errado ate a home ser reduzida, e Gravacao continua
    acessivel DE DENTRO do Extras.

USO
    python3 tools/patch_extras.py --in <e.bin> --out <s.bin> --em 0x1A3050
    python3 tools/patch_extras.py --autoteste

DEPENDENCIAS
    Python 3. Nada mais.

LIMITACOES
    - o item da home ainda se chama "Gravacao". Renomear e o passo
      seguinte, junto com a reducao da home para 4 itens;
    - a pagina 0x52 nasceu para 3 itens; com 6 ela usa toda a folga da
      estrutura. Nao ha espaco para um setimo sem medir de novo.
"""

import argparse, hashlib, os, sys

RAIZ     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = "firmware/ORIGINAL/GN438_original.bin"
PROIBIDO = 0x0000D000
TAMANHO  = 0x200000
BIAS     = 0x00C00000

PAGINA   = 0x52                 # page_home_menu — MEDIDO, nao 0x53
N_VELHO, N_NOVO = 3, 6
IDS      = [5, 6, 2, 4, 9, 8]   # Gravacao, Radio, Livro, Imagem, Bluetooth, Pastas
TAB_VELHA = 0x00C486E8          # a tabela de 3 ids, de fabrica
POOL     = 0x0012F324           # o pool que aponta para ela

# --- os pontos de deslocamento dos arrays -------------------------------
ARRAY_B = [0x0012F2DC, 0x0012F2FA, 0x0012F37A,
           0x0012F40E, 0x0012F43E, 0x0012F486]
ARRAY_C = [0x0012F2E0, 0x0012F414]

# --- os imediatos -------------------------------------------------------
IMEDIATOS = [
    (0x0012F0A4, 0x28, 0x4C, "malloc"),
    (0x0012F0C2, 0x28, 0x4C, "memset"),
    (0x0012F2DA, N_VELHO, N_NOVO, "limite do laco"),
    (0x0012F246, N_VELHO - 1, N_NOVO - 1, "qual item leva a borda"),
    (0x0012F3E2, N_VELHO - 1, N_NOVO - 1, "limite de navegacao 1"),
    (0x0012F406, N_VELHO - 1, N_NOVO - 1, "limite de navegacao 2"),
]

# --- o roteamento -------------------------------------------------------
ROTA_OFF = 0x001010F6
ROTA_DE  = bytes.fromhex("fdf70dfb0546")      # bl 0xCFE714 ; mov r5,r0
ROTA_NOVA = (bytes([0x52, 0x23])              # movs r3, #0x52
             + bytes([0x00, 0x22])            # movs r2, #0
             + bytes([0x02, 0x21])            # movs r1, #2
             + bytes([0x01, 0x20])            # movs r0, #1
             + bytes([0x78, 0xE0]))           # b 0x00D011F2

# --- a troca do ponteiro de ids -----------------------------------------
PTR_OFF = 0x0012F2B6
PTR_DE  = bytes([0x03, 0xAB])                 # add r3, sp, #0xc
PTR_NOVA = bytes([0x1B, 0x4B])                # ldr r3, [pc, #108]

CONTEXTO = [
    (0x0012F0A8, bytes.fromhex("29f06ef8"), "bl malloc, logo apos o tamanho"),
    (0x0012F2B8, bytes.fromhex("53f82600"), "ldr.w r0,[r3,r6,lsl#2] — le o id"),
    (0x0012F2D6, bytes.fromhex("48f8044f"), "str r4,[r8,#4]! — o array A"),
    (0x0012F324, TAB_VELHA.to_bytes(4, "little"), "o pool da tabela de ids"),
    (0x001011F2, bytes.fromhex("bde8f041"), "pop da cauda de troca de pagina"),
]


def _ldr_t1(hw):
    """(base, imm) de um `ldr rX,[rY,#imm5*4]` de 16 bits, ou None."""
    if (hw & 0xF800) != 0x6800:
        return None
    return hw & ~(0x1F << 6), ((hw >> 6) & 0x1F) * 4


def _le_desloc(d, off):
    """Devolve (tipo, deslocamento) do acesso em `off`."""
    hw = d[off] | (d[off + 1] << 8)
    t1 = _ldr_t1(hw)
    if t1:
        return "ldr", t1[1]
    if (hw & 0xFFF0) in (0xF8C0, 0xF8D0):
        return "w", (d[off + 2] | (d[off + 3] << 8)) & 0xFFF
    return None, None


def _escreve_desloc(d, off, novo):
    tipo, _ = _le_desloc(d, off)
    if tipo == "ldr":
        hw = d[off] | (d[off + 1] << 8)
        base = hw & ~(0x1F << 6)
        hw = base | ((novo // 4) << 6)
        d[off] = hw & 0xFF
        d[off + 1] = hw >> 8
    elif tipo == "w":
        w2 = d[off + 2] | (d[off + 3] << 8)
        w2 = (w2 & ~0xFFF) | novo
        d[off + 2] = w2 & 0xFF
        d[off + 3] = w2 >> 8
    else:
        raise RuntimeError(f"0x{off:06X}: nao e ldr/str reconhecido")


def confere_contexto(d):
    for off, esperado, desc in CONTEXTO:
        achado = bytes(d[off:off + len(esperado)])
        if achado != esperado:
            return False, (f"0x{off:06X} ({desc}): achei {achado.hex()}, "
                           f"esperava {esperado.hex()}")
    return True, "ok"


def aplica(d, em):
    if bytes(d[ROTA_OFF:ROTA_OFF + len(ROTA_NOVA)]) == ROTA_NOVA:
        return False, "patch ja aplicado"
    ok, msg = confere_contexto(d)
    if not ok:
        return False, msg

    passo_velho = N_VELHO * 4        # 0x0C
    passo_novo = N_NOVO * 4          # 0x18

    # 1. CONFERE TUDO ANTES DE ESCREVER NADA.
    #    O offset novo do array B colide com o antigo do array C, entao
    #    ler depois de escrever daria leitura errada.
    for off in ARRAY_B:
        tipo, v = _le_desloc(d, off)
        if v != passo_velho:
            return False, (f"0x{off:06X}: deslocamento 0x{v:02X}, esperava "
                           f"0x{passo_velho:02X} (array B)")
    for off in ARRAY_C:
        tipo, v = _le_desloc(d, off)
        if v != 2 * passo_velho:
            return False, (f"0x{off:06X}: deslocamento 0x{v:02X}, esperava "
                           f"0x{2*passo_velho:02X} (array C)")
    for off, velho, _, desc in IMEDIATOS:
        if d[off] != velho:
            return False, (f"0x{off:06X} ({desc}): tem {d[off]}, esperava "
                           f"{velho}")
    if bytes(d[ROTA_OFF:ROTA_OFF + len(ROTA_DE)]) != ROTA_DE:
        return False, (f"0x{ROTA_OFF:06X}: o destino do indice 2 nao e o "
                       f"esperado")
    if bytes(d[PTR_OFF:PTR_OFF + 2]) != PTR_DE:
        return False, f"0x{PTR_OFF:06X}: nao e `add r3,sp,#0xc`"
    livre = d[em:em + 4 * N_NOVO]
    if any(b != 0xFF for b in livre):
        return False, f"a area livre em 0x{em:06X} nao esta virgem"

    # 2. agora escreve
    for off in ARRAY_B:
        _escreve_desloc(d, off, passo_novo)
    for off in ARRAY_C:
        _escreve_desloc(d, off, 2 * passo_novo)
    for off, _, novo, _ in IMEDIATOS:
        d[off] = novo
    for i, v in enumerate(IDS):
        d[em + i * 4:em + i * 4 + 4] = v.to_bytes(4, "little")
    d[PTR_OFF:PTR_OFF + 2] = PTR_NOVA
    d[POOL:POOL + 4] = (BIAS + em).to_bytes(4, "little")
    d[ROTA_OFF:ROTA_OFF + len(ROTA_NOVA)] = ROTA_NOVA
    return True, "ok"


def autoteste():
    print("\n  AUTOTESTE — a tela EXTRAS, 6 itens\n")
    o = os.path.join(RAIZ, ORIGINAL)
    if not os.path.exists(o):
        print(f"  FALTA: {o}")
        return 1
    orig = open(o, "rb").read()
    d = bytearray(orig)
    em = 0x001A3050
    falhas = []

    ok, msg = aplica(d, em)
    if not ok:
        print(f"  FALHOU: {msg}")
        return 1

    def chk(nome, cond):
        print(f"    {nome:34} " + ("OK" if cond else "FALHOU"))
        if not cond:
            falhas.append(nome)

    chk("malloc e memset = 0x4C",
        d[0x0012F0A4] == 0x4C and d[0x0012F0C2] == 0x4C)
    chk("array B nos 6 pontos = +0x18",
        all(_le_desloc(d, o2)[1] == 0x18 for o2 in ARRAY_B))
    chk("array C nos 2 pontos = +0x30",
        all(_le_desloc(d, o2)[1] == 0x30 for o2 in ARRAY_C))
    chk("limite do laco = 6", d[0x0012F2DA] == 6)
    chk("borda no item 5", d[0x0012F246] == 5)
    chk("limites de navegacao = 5",
        d[0x0012F3E2] == 5 and d[0x0012F406] == 5)
    chk("o laco le o pool, nao a pilha",
        bytes(d[PTR_OFF:PTR_OFF + 2]) == PTR_NOVA)
    chk("o pool aponta para a tabela nova",
        int.from_bytes(d[POOL:POOL + 4], "little") == BIAS + em)
    chk("a tabela tem os 6 ids certos",
        [int.from_bytes(d[em + i * 4:em + i * 4 + 4], "little")
         for i in range(6)] == IDS)
    chk("o roteamento abre a pagina 0x52",
        bytes(d[ROTA_OFF:ROTA_OFF + 10]) == ROTA_NOVA and d[ROTA_OFF] == 0x52)

    # NADA pode ter sido escrito fora dos pontos declarados
    prev = set()
    for off in ARRAY_B:
        prev.update(range(off, off + 4))
    for off in ARRAY_C:
        prev.update(range(off, off + 4))
    prev.update(o2 for o2, _, _, _ in IMEDIATOS)
    prev.update(range(PTR_OFF, PTR_OFF + 2))
    prev.update(range(POOL, POOL + 4))
    prev.update(range(ROTA_OFF, ROTA_OFF + 10))
    prev.update(range(em, em + 4 * N_NOVO))
    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    fora = [i for i in dif if i not in prev]
    chk(f"so nos pontos declarados ({len(dif)} B)", not fora)
    if fora:
        falhas.append(f"escreveu fora: {[hex(i) for i in fora[:6]]}")

    chk("nada abaixo de 0x00D000", all(i > PROIBIDO for i in dif))

    ok2, _ = aplica(d, em)
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
        description="a tela EXTRAS: a pagina 0x52 passa de 3 para 6 itens")
    ap.add_argument("--in", dest="src")
    ap.add_argument("--out", dest="dst")
    ap.add_argument("--em", type=lambda s: int(s, 0), default=0x001A3050,
                    help="endereco da tabela de ids na area livre")
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

    print("\n  A TELA EXTRAS — a pagina 0x52 passa de 3 para 6 itens\n")
    ok, msg = aplica(d, a.em)
    if not ok:
        print(f"  ABORTADO: {msg}", file=sys.stderr)
        return 1

    print("  ALOCACAO")
    print(f"    0x0012F0A4 / 0x0012F0C2   0x28 -> 0x4C")
    print(f"      3 arrays x 6 itens x 4 = 0x48, mais 4 de folga")
    print()
    print("  OS ARRAYS")
    print(f"    array B  +0x0C -> +0x18   {len(ARRAY_B)} pontos")
    print(f"    array C  +0x18 -> +0x30   {len(ARRAY_C)} pontos")
    print()
    print("  LIMITES")
    for off, velho, novo, desc in IMEDIATOS[2:]:
        print(f"    0x{off:06X}   {velho} -> {novo}   {desc}")
    print()
    print("  A TABELA DE IDS, e o transbordo contornado")
    print(f"    0x{a.em:06X}   {4*N_NOVO} B   {IDS}")
    print(f"    0x{PTR_OFF:06X}   add r3,sp,#0xc -> ldr r3,[pc,#108]")
    print(f"    0x{POOL:06X}   o pool -> 0x{BIAS+a.em:08X}")
    print()
    print("  O ROTEAMENTO — e o que torna a versao TESTAVEL")
    print(f"    0x{ROTA_OFF:06X}  10 B  movs r3,#0x52 ... b 0x00D011F2")
    print(f"    o item 'Gravacao' da home passa a ABRIR A LISTA DE SEIS")
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
