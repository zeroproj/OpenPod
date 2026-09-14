#!/usr/bin/env python3
"""
mapa_auxiliares.py — identifica por COMPORTAMENTO as funcoes sem nome.

O PROBLEMA QUE ISTO RESOLVE

    `mapa_simbolos.py` nomeia 412 funcoes lendo os nomes que o firmware
    registra para depuracao. Mas o codigo tem ~3.210 funcoes: **2.798 nao
    tem nome** porque nao fazem log. E sao justamente os AUXILIARES —
    inclusive os criadores de faixa, conteiner e linha, que o Saturno
    mais toca.

    Nome nao da para inventar. Mas comportamento da para medir:

        quem chama       um auxiliar chamado por 50 telas e infraestrutura
        o que chama      quem chama `lv_obj_set_size` cria objeto
        onde mora        0x12xxxx e VIEW, 0x14xxxx e LVGL

    Esta ferramenta ranqueia as funcoes anonimas por numero de chamadores
    distintos e descreve cada uma pelo que ela chama. Nao inventa nome:
    entrega evidencia para a gente nomear.

METODO, E SEUS LIMITES

    - funcoes sao detectadas pelo prologo `push {..., lr}`. Funcoes
      folha sem prologo **nao sao vistas** — a contagem de 3.210 e piso,
      nao total;
    - o grafo usa apenas `bl` com destino imediato. Chamada por ponteiro
      (callback) **nao aparece**, e o firmware usa callbacks a rodo;
    - portanto: quem aparece com muitos chamadores realmente tem; quem
      aparece com poucos pode ter mais.

USO
    python3 tools/mapa_auxiliares.py [--top 40] [--md docs/AUXILIARES.md]
"""

import argparse
import re
import struct
import sys
from collections import defaultdict

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
except ImportError:
    sys.exit("capstone ausente: pip3 install capstone")

XIP = 0x00C00000
INI, FIM = 0x0E0000, 0x1A0570

CAMADAS = [(0x0E0000, 0x100000, "sistema/tarefas"),
           (0x100000, 0x110000, "PRESENTER"),
           (0x110000, 0x120000, "?"),
           (0x120000, 0x140000, "VIEW"),
           (0x140000, 0x1A0570, "LVGL/infra")]

# auxiliares ja identificados por COMPORTAMENTO (nao por nome).
# Confianca declarada, como manda o CLAUDE.md.
CONHECIDOS = {
    # --- camada VIEW: os criadores que o Saturno inteiro usa
    0x121690: ("CONFIRMADO", "cria CONTEINER da lista"),
    0x1216F0: ("CONFIRMADO", "cria FAIXA superior"),
    0x121764: ("CONFIRMADO", "cria LINHA de lista"),
    0x1226AC: ("CONFIRMADO", "cria TITULO (usado pelo patch_titulos)"),
    0x123740: ("CONFIRMADO", "view_icon_create"),
    0x121384: ("CONFIRMADO", "getter de cor de TEXTO (fabrica: -1 = branco)"),
    0x12138A: ("CONFIRMADO", "getter de cor de FUNDO (fabrica: 0 = preto)"),
    # --- LVGL: geometria
    0x14A1A2: ("CONFIRMADO", "lv_obj_set_pos"),
    0x14A1BA: ("CONFIRMADO", "lv_obj_set_width"),
    0x14A1EA: ("CONFIRMADO", "lv_obj_set_height"),
    0x14A21A: ("CONFIRMADO", "lv_obj_set_size"),
    0x14A3A2: ("CONFIRMADO", "lv_obj_align"),
    0x14924A: ("CONFIRMADO", "lv_obj_clear_flag"),
    # --- LVGL: estilo (numero da propriedade entre parenteses)
    0x14CAC4: ("CONFIRMADO", "lv_obj_set_local_style_prop — o despachante"),
    0x14D064: ("CONFIRMADO", "set_style_radius (96)"),
    0x14D092: ("CONFIRMADO", "set_style_bg_color (32)"),
    0x14D0C8: ("CONFIRMADO", "set_style_border_color (48)"),
    0x14D0F4: ("CONFIRMADO", "set_style_border_width (50)"),
    0x14D100: ("CONFIRMADO", "set_style_border_side (51)"),
    0x14D10A: ("CONFIRMADO", "set_style_text_color (87)"),
    0x14D12E: ("CONFIRMADO", "set_style_text_font (89)"),
    # --- LVGL: objetos e entrada
    0x15B890: ("CONFIRMADO", "lv_obj_create"),
    0x15E2E8: ("CONFIRMADO", "lv_label_create"),
    0x15ED94: ("CONFIRMADO", "lv_label_set_text"),
    0x147654: ("CONFIRMADO", "lv_group_send_data — ponto unico de tecla"),
    0x157B48: ("CONFIRMADO", "palette_main"),
    # --- achados desta varredura
    0x0F780C: ("PROVAVEL", "alocador: confere o limite, loga erro, aloca"),
    0x10D818: ("CONFIRMADO", "PRESENTER -> VIEW: envia a mensagem pelo buffer "
                             "circular. A mais chamada do presenter (173)"),
    0x0F83E4: ("CONFIRMADO", "escreve no buffer circular (moldura 0x55AA+tam)"),
    0x0F8444: ("CONFIRMADO", "LE do buffer circular; consumido por "
                             "watch_view_rec_analysis -> view_page_msg_analysis"),
    # --- configuracoes persistentes (NV) — ver ARQUITETURA.md §9
    0x16B6A8: ("PROVAVEL", "NV: grava chave (tail-call 0x00D6CEA4)"),
    0x16B6BC: ("PROVAVEL", "NV: le chave (tail-call 0x00D6CBDE)"),
    0x10D880: ("HIPOTESE", "monta struct de mensagem de 0x24 bytes na pilha"),
}


def camada(a):
    for lo, hi, nm in CAMADAS:
        if lo <= a < hi:
            return nm
    return "?"


def simbolos(p="docs/SIMBOLOS.md"):
    s = {}
    for L in open(p):
        m = re.match(r'\| `0x([0-9A-F]+)` \| (\w+) \| `(.+)` \|', L.strip())
        if m:
            s[int(m.group(1), 16)] = m.group(3)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src",
                    default="firmware/ORIGINAL/GN438_original.bin")
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--md", default="docs/AUXILIARES.md")
    a = ap.parse_args()
    d = open(a.src, "rb").read()
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    sim = simbolos()

    # 1) prologos
    fs = []
    for o in range(INI, FIM, 2):
        hw = struct.unpack_from('<H', d, o)[0]
        if 0xB500 <= hw <= 0xB5FF:
            fs.append(o)
        elif hw == 0xE92D and (struct.unpack_from('<H', d, o + 2)[0] & 0x4000):
            fs.append(o)
    fs.sort()

    def dono(o):
        lo, hi = 0, len(fs) - 1
        r = None
        while lo <= hi:
            m = (lo + hi) // 2
            if fs[m] <= o:
                r = fs[m]
                lo = m + 1
            else:
                hi = m - 1
        return r

    # 2) grafo de chamadas
    chamam = defaultdict(set)     # callee -> {callers}
    chama = defaultdict(set)      # caller -> {callees}
    for o in range(INI, FIM, 2):
        k = next(md.disasm(d[o:o + 4], o + XIP), None)
        if not (k and k.mnemonic == "bl" and k.op_str.startswith("#")):
            continue
        alvo = int(k.op_str.strip("#"), 0) - XIP
        if not (INI <= alvo < FIM):
            continue
        c = dono(o)
        if c is None or c == alvo:
            continue
        chamam[alvo].add(c)
        chama[c].add(alvo)

    anon = [f for f in fs if f not in sim]
    print()
    print("  MAPA DE AUXILIARES")
    print()
    print(f"  funcoes (por prologo) ...... {len(fs)}")
    print(f"  com nome ................... {len(sim)}")
    print(f"  ANONIMAS ................... {len(anon)}")
    print(f"  arestas de chamada ......... {sum(len(v) for v in chamam.values())}")

    # validacao: os auxiliares que ja conheciamos aparecem no topo?
    print("\n  validacao — auxiliares que ja identificamos por comportamento:")
    rank = sorted(anon, key=lambda f: -len(chamam.get(f, ())))
    pos = {f: i for i, f in enumerate(rank)}
    for f, nm in sorted(CONHECIDOS.items()):
        conf, desc = nm
        if f in pos:
            print(f"    0x{f:06X}  {len(chamam.get(f,())):3d} chamadores  "
                  f"#{pos[f]+1:<5d} {conf:11s} {desc}")
        else:
            print(f"    0x{f:06X}  (sem prologo push){' '*13}{conf:11s} {desc}")

    def descreve(f):
        alvos = sorted(chama.get(f, ()), key=lambda x: -len(chamam.get(x, ())))
        nomes = [sim[x] for x in alvos if x in sim][:3]
        return nomes

    out = []
    w = out.append
    w("# AUXILIARES — as funcoes sem nome, identificadas por comportamento\n")
    w("Gerado por `tools/mapa_auxiliares.py` sobre "
      "`firmware/ORIGINAL/GN438_original.bin`.\n")
    w(f"| | |")
    w("|---|---|")
    w(f"| funcoes detectadas (prologo `push {{..,lr}}`) | {len(fs)} |")
    w(f"| com nome (`docs/SIMBOLOS.md`) | {len(sim)} |")
    w(f"| **anonimas** | **{len(anon)}** |")
    w(f"| arestas de chamada | {sum(len(v) for v in chamam.values())} |")
    w("")
    w("Nome nao da para inventar; comportamento da para medir. A lista")
    w("abaixo ranqueia as anonimas por **numero de chamadores distintos**.")
    w("Uma funcao chamada por dezenas de telas e infraestrutura — e é onde")
    w("um patch nosso tem o maior alcance, para o bem e para o mal.\n")
    w("**Limites:** funcoes folha sem prologo nao sao vistas, e chamadas")
    w("por ponteiro (callback) nao entram no grafo. Muitos chamadores e")
    w("evidencia forte; poucos chamadores **nao** e evidencia de nada.\n")
    w("## As mais chamadas\n")
    w("| # | endereco | chamadores | camada | chama (por nome) | ja identificamos |")
    w("|---|---|---|---|---|---|")
    for i, f in enumerate(rank[:a.top]):
        nn = descreve(f)
        w(f"| {i+1} | `0x{f:06X}` | **{len(chamam[f])}** | {camada(f)} | "
          + (", ".join(f"`{x}`" for x in nn) if nn else "—") + " | "
          + (CONHECIDOS[f][1] if f in CONHECIDOS else "—") + " |")
    w("")
    w("## Auxiliares ja identificados por comportamento\n")
    w("Nenhum destes tem nome no binario. Foram identificados pelo que")
    w("fazem, ao longo do projeto e nesta varredura.\n")
    w("| endereco | chamadores | confianca | o que e |")
    w("|---|---|---|---|")
    for f, (conf, desc) in sorted(CONHECIDOS.items()):
        w(f"| `0x{f:06X}` | "
          + (str(len(chamam.get(f, ()))) if f in chamam else "—")
          + f" | {conf} | {desc} |")
    open(a.md, "w").write("\n".join(out) + "\n")
    print(f"\n  gravado: {a.md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
