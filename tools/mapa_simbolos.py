#!/usr/bin/env python3
"""
mapa_simbolos.py — recupera a tabela de simbolos que o firmware carrega.

A IDEIA

    O firmware YP3 registra os proprios nomes de funcao para depuracao:
    ha 475 strings como `page_music_play_create`, delimitadas por NUL, e
    o codigo carrega o endereco delas para passar a um log.

    Entao da para ligar NOME -> ENDERECO mecanicamente:

        1. acha as strings de nome;
        2. acha toda carga de literal (LDR PC-relativo) que aponta
           para uma delas;
        3. atribui a carga a funcao que a contem (recuando ate o `push`);
        4. a funcao que cita UM unico nome, e esse nome.

    Isso transforma `0x00131E7C` em `page_music_play_create`. Nao e
    adivinhacao: o binario esta dizendo o proprio nome.

CONFIANCA — e por isso que nao afirmo tudo como certo

    ALTA    a funcao cita 1 nome (ou varios da MESMA pagina) E foi
            validada por fonte independente (tabela 0x00D23B38)
    MEDIA   a funcao cita 1 nome, OU varios nomes que concordam no
            numero da pagina — `page10_mbox_process` e
            `page10_scr_process` sao a MESMA funcao tratando eventos
            diferentes, nao duas funcoes
    BAIXA   a funcao cita nomes que NAO concordam (ex.: `btplay_stop`
            junto de `pstr_bt_analysis`). Isso e pista, nao fato.

    A primeira versao desta ferramenta marcava como BAIXA tudo que citava
    mais de um nome, e 43 dos 51 BAIXA eram so pontos de log da mesma
    pagina. Medir "quantos nomes" era a pergunta errada; a certa e "os
    nomes concordam?".

    Um simbolo BAIXA e uma pista, nao um fato. O `CLAUDE.md` manda
    distinguir CONFIRMADO / PROVAVEL / HIPOTESE; aqui e o mesmo.

USO
    python3 tools/mapa_simbolos.py            # le a ORIGINAL
    python3 tools/mapa_simbolos.py --in X.bin --md docs/SIMBOLOS.md

POR QUE A ORIGINAL, E NAO A NOSSA
    Na imagem de trabalho 77 ganchos ja desviam chamadas para a area
    livre. Mapear ela seria ler as nossas decisoes como se fossem
    projeto de fabrica. A original tem hash conferido e nunca muda.
"""

import argparse
import re
import struct
import sys
from collections import Counter, defaultdict

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
except ImportError:
    sys.exit("capstone ausente: pip3 install capstone")

XIP = 0x00C00000
CODIGO_INI, CODIGO_FIM = 0x0E0000, 0x1A0570
TAB_PAGINAS = 0x00D23B38
RECUO_MAX = 0x600


def nomes_de(d):
    """Strings de nome, delimitadas por NUL dos dois lados."""
    out = {}
    for m in re.finditer(
            rb'\x00([a-zA-Z][a-zA-Z0-9]{1,18}_[a-zA-Z0-9_]{2,48})\x00', d):
        out[XIP + m.start(1)] = m.group(1).decode()
    return out


def cargas(d, nomes):
    """Toda carga de literal PC-relativa que aponta para um nome."""
    out = {}
    for a in range(CODIGO_INI, CODIGO_FIM, 2):
        hw = struct.unpack_from('<H', d, a)[0]
        if 0x4800 <= hw <= 0x4FFF:                      # LDR Rt,[PC,#imm8*4]
            tgt = ((a + XIP + 4) & ~3) + (hw & 0xFF) * 4
        elif hw in (0xF85F, 0xF8DF) and a + 4 <= CODIGO_FIM:
            imm = struct.unpack_from('<H', d, a + 2)[0] & 0xFFF
            base = (a + XIP + 4) & ~3
            tgt = base + imm if hw == 0xF8DF else base - imm
        else:
            continue
        o = tgt - XIP
        if 0 <= o < len(d) - 4:
            v = struct.unpack_from('<I', d, o)[0]
            if v in nomes:
                out[a + XIP] = nomes[v]
    return out


def inicio_funcao(d, addr):
    """Recua ate o `push {...,lr}` que abre a funcao."""
    for a in range(addr - 2, max(addr - RECUO_MAX, CODIGO_INI + XIP), -2):
        o = a - XIP
        hw = struct.unpack_from('<H', d, o)[0]
        if 0xB500 <= hw <= 0xB5FF:                      # push {..., lr}
            return a
        if hw == 0xE92D:                                # push.w {..., lr}
            hw2 = struct.unpack_from('<H', d, o + 2)[0]
            if hw2 & 0x4000:
                return a
    return None


def paginas(d):
    """Funcoes alcancadas pela tabela de paginas — fonte independente.

       Usa capstone: decodificar BL a mao foi a primeira versao desta
       funcao e devolvia zero paginas, silenciosamente."""
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    out = {}
    for i in range(0x53):
        t = TAB_PAGINAS + 2 * d[TAB_PAGINAS - XIP + i]
        k = next(md.disasm(d[t - XIP:t - XIP + 4], t), None)
        if k and k.mnemonic == "bl" and k.op_str.startswith("#"):
            out.setdefault(int(k.op_str.strip("#"), 0), i + 1)
    return out


def main():
    ap = argparse.ArgumentParser(description="recupera simbolos do firmware")
    ap.add_argument("--in", dest="src",
                    default="firmware/ORIGINAL/GN438_original.bin")
    ap.add_argument("--md", default="docs/SIMBOLOS.md")
    a = ap.parse_args()
    d = open(a.src, "rb").read()
    if len(d) != 0x200000:
        sys.exit(f"tamanho inesperado: {len(d)}")

    nm = nomes_de(d)
    cg = cargas(d, nm)
    pg = paginas(d)

    porfn = defaultdict(set)
    orfas = 0
    for site, nome in cg.items():
        f = inicio_funcao(d, site)
        if f is None:
            orfas += 1
            continue
        porfn[f].add(nome)

    def resolver(ns):
        """Os nomes concordam? Se todos apontam a mesma pagina, e uma
           funcao so com varios pontos de log."""
        if len(ns) == 1:
            return next(iter(ns)), True
        # (a) concordam no NUMERO da pagina?  page10_mbox / page10_scr
        nums = {int(m.group(1)) for n in ns
                for m in [re.search(r'page(\d+)[_\b]', n)] if m}
        # (b) concordam no NOME da pagina?  page_set_offscr_btn / _event_reply
        pref = {m.group(1) for n in ns
                for m in [re.search(r'^(page_[a-z0-9]+(?:_[a-z0-9]+)*?)_'
                                    r'(?:btn|scr|cont|mbox|index|label|btnm|'
                                    r'event|media|build|search|show)', n)] if m}
        if len(nums) != 1 and len(pref) == 1:
            base = pref.pop()
            return " + ".join(sorted(ns)) + f"   [mesma tela: {base}]", True
        if len(nums) == 1:
            n = nums.pop()
            corpo = sorted(x for x in ns if re.search(rf'page{n}[_\b]', x))
            fora = sorted(x for x in ns if not re.search(rf'page{n}[_\b]', x))
            nome = " + ".join(corpo)
            if fora:
                nome += "  [tambem cita: " + ", ".join(fora) + "]"
            return nome, True
        return " | ".join(sorted(ns)), False

    simbolos = {}
    for f, ns in porfn.items():
        nome, concorda = resolver(ns)
        if not concorda:
            conf = "BAIXA"
        else:
            conf = "ALTA" if f in pg else "MEDIA"
        simbolos[f] = (nome, conf, len(ns))

    cn = Counter(c for _, c, _ in simbolos.values())
    print()
    print("  MAPA DE SIMBOLOS —", a.src.split("/")[-1])
    print()
    print(f"  strings de nome        : {len(nm)}")
    print(f"  cargas apontando nome  : {len(cg)}")
    print(f"  nomes distintos citados: {len(set(cg.values()))}")
    print(f"  cargas sem funcao      : {orfas}")
    print(f"  FUNCOES IDENTIFICADAS  : {len(simbolos)}")
    for k in ("ALTA", "MEDIA", "BAIXA"):
        print(f"     {k:6s} {cn.get(k,0)}")
    print(f"  paginas na tabela      : {len(pg)}")

    # ---------------- markdown ----------------
    linhas = []
    w = linhas.append
    w("# SIMBOLOS — a tabela de nomes recuperada do firmware\n")
    w(f"Gerado por `tools/mapa_simbolos.py` a partir de `{a.src}`.\n")
    w("O firmware YP3 registra os proprios nomes de funcao para depuracao.")
    w("Esta tabela liga NOME -> ENDERECO achando as cargas de literal que")
    w("apontam para essas strings e atribuindo-as a funcao que as contem.\n")
    w("**Confianca:** `ALTA` = a funcao cita um unico nome E aparece na")
    w("tabela de paginas (`0x00D23B38`), que e fonte independente. `MEDIA` =")
    w("cita um unico nome. `BAIXA` = cita varios (pode estar logando nomes")
    w("alheios) — e **pista, nao fato**.\n")
    w("| # | valor |")
    w("|---|---|")
    w(f"| strings de nome | {len(nm)} |")
    w(f"| nomes distintos citados | {len(set(cg.values()))} |")
    w(f"| **funcoes identificadas** | **{len(simbolos)}** |")
    for k in ("ALTA", "MEDIA", "BAIXA"):
        w(f"| confianca {k} | {cn.get(k,0)} |")
    w("")
    w("## Paginas (confianca ALTA — validadas pela tabela de despacho)\n")
    w("| pagina | endereco | simbolo |")
    w("|---|---|---|")
    for f, p in sorted(pg.items(), key=lambda x: x[1]):
        s = simbolos.get(f)
        w(f"| 0x{p:02X} | `0x{f-XIP:06X}` | "
          f"{('`%s`' % s[0]) if s and s[1] != 'BAIXA' else '—'} |")
    w("")
    w("## Todos os simbolos, por endereco\n")
    w("| endereco | confianca | simbolo |")
    w("|---|---|---|")
    for f in sorted(simbolos):
        nome, conf, _ = simbolos[f]
        w(f"| `0x{f-XIP:06X}` | {conf} | `{nome}` |")
    open(a.md, "w").write("\n".join(linhas) + "\n")
    print(f"\n  gravado: {a.md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
