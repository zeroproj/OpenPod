#!/usr/bin/env python3
"""
textos_fixos.py — acha o texto da interface que NAO passa pela tabela
                  de idiomas.

A PERGUNTA QUE ISTO RESPONDE

    "Temos mapeado tudo que a interface mostra de texto, em todos os
    idiomas?"

    `exporta_textos.py` cobre os 216 ids x 8 idiomas. Mas isso e a
    tabela de idiomas — nao e necessariamente TUDO que aparece na tela.

    Esta ferramenta mede a diferenca: varre as chamadas a
    `lv_label_set_text` e classifica a origem de cada texto.

O QUE ELA ACHOU (e por que importa)

    Ha texto em INGLES fixo no codigo, que nenhuma traducao alcanca —
    por exemplo " Time's up!" e "OK" na tela do despertador.

    Sem esta varredura, "os textos estao todos em portugues" era uma
    afirmacao sobre a tabela, nao sobre a tela.

CORRECAO IMPORTANTE (nao repetir o erro da primeira versao)

    A primeira versao concluiu "so 35 textos sao traduziveis". **Errado,
    e enganoso.** Ela contava so o que chega ao rotulo DIRETO, dentro da
    camada VIEW. Mas o firmware e MVP: o caminho principal do texto
    traduzido e OUTRO —

        presenter:  get_lang_str(id)        163 chamadas
                        |
                        v
                    pstr_cmd_view(ctrl, texto)   63 delas
                        | monta mensagem de 0x414 B,
                        | copia o texto para o offset 0x14
                        v
        view:       recebe por mensagem e poe no rotulo

    Por isso as 82 chamadas classificadas como "origem nao determinada"
    (texto vindo de registrador): boa parte **e texto traduzido chegando
    por mensagem**, nao texto dinamico.

    O numero honesto de textos traduziveis nao sai desta varredura. O que
    sai, e e solido, e a lista de LITERAIS — esses nenhuma traducao pega.

LIMITES

    - textos montados em tempo de execucao (hora, nome de arquivo,
      contador) entram como "origem nao determinada": vem de registrador
      e nao da para resolver estaticamente;
    - o filtro de string aceita qualquer byte imprimivel, entao
      ponteiros de FONTE as vezes passam como texto. Sao marcados.

USO
    python3 tools/textos_fixos.py \\
        --in firmware/WORKING/GN438_openpod_v073_carimbado.bin
"""

import argparse
import re
import struct
import sys

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
except ImportError:
    sys.exit("capstone ausente: pip3 install capstone")

XIP = 0x00C00000
SET_TEXT = 0xD5ED94
GET_LANG = 0xD2108C
FONTES = {0x0AF5EC, 0x0A671C, 0x0AA8A8, 0x0DED88, 0x0B0D3C, 0x0CACFE4,
          0x0CC2064, 0x0CC19B8}


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
                    default="firmware/WORKING/GN438_openpod_v073_carimbado.bin")
    ap.add_argument("--md", default="docs/TEXTOS_FIXOS.md")
    a = ap.parse_args()
    d = open(a.src, "rb").read()
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    sim = simbolos()
    fs = sorted(sim)

    def nome(o):
        c = [f for f in fs if f <= o]
        return sim[max(c)] if c and o - max(c) < 0x1400 else "?"

    def ins(x):
        try:
            return next(md.disasm(d[x - XIP:x - XIP + 4], x), None)
        except Exception:
            return None

    n_lang = n_reg = 0
    fixos = {}
    for x in range(0xD20000, 0xD40000, 2):
        k = ins(x)
        if not (k and k.mnemonic == "bl" and k.op_str.startswith("#")):
            continue
        if int(k.op_str.strip("#"), 0) != SET_TEXT:
            continue
        origem = None
        for b in range(x - 16, x, 2):
            j = ins(b)
            if not j:
                continue
            if (j.mnemonic == "bl" and j.op_str.startswith("#")
                    and int(j.op_str.strip("#"), 0) == GET_LANG):
                origem = "lang"
            if j.mnemonic == "ldr" and "r1, [pc" in j.op_str:
                imm = int(j.op_str.split("#")[-1].rstrip("]"), 0)
                p = (((b + 4) & ~3) + imm) - XIP
                if 0 <= p < len(d) - 4:
                    v = struct.unpack_from("<I", d, p)[0]
                    if XIP <= v < XIP + 0x200000:
                        o = v - XIP
                        s = d[o:o + 48].split(b"\0")[0]
                        if s and all(9 <= c < 127 or c >= 0xC0 for c in s):
                            origem = ("fixo", o, s.decode("latin1", "replace"),
                                      b - XIP)
        if origem == "lang":
            n_lang += 1
        elif isinstance(origem, tuple):
            fixos.setdefault(origem[1], (origem[2], []))[1].append(origem[3])
        else:
            n_reg += 1

    total = n_lang + n_reg + sum(len(v[1]) for v in fixos.values())
    reais = {o: v for o, v in fixos.items() if o not in FONTES}
    print()
    print("  TEXTO DA INTERFACE — de onde vem")
    print()
    print(f"  chamadas a lv_label_set_text nas telas : {total}")
    print(f"    da tabela de idiomas, DIRETO         : {n_lang}")
    print(f"    LITERAL no codigo (nao traduzivel)   : "
          f"{sum(len(v[1]) for v in fixos.values())}")
    print(f"    vindo de registrador                 : {n_reg}")
    print("    (boa parte dos 'de registrador' e texto traduzido que")
    print("     chegou por mensagem via pstr_cmd_view — ver cabecalho)")
    print(f"  literais distintos (fora ponteiros de fonte): {len(reais)}")

    out = []
    w = out.append
    w("# TEXTOS FIXOS — o que a tabela de idiomas NAO alcanca\n")
    w(f"Gerado por `tools/textos_fixos.py` sobre `{a.src}`.\n")
    w("`docs/TEXTOS_SISTEMA.md` cobre os **216 ids x 8 idiomas**. Este")
    w("arquivo cobre o resto: o texto que a interface mostra **sem passar**")
    w("pela tabela — logo, **nenhuma traducao o alcanca**.\n")
    w("| origem no rotulo | chamadas |")
    w("|---|---:|")
    w(f"| tabela de idiomas, **direto** | {n_lang} |")
    w(f"| literal no codigo (**nao traduzivel**) | "
      f"{sum(len(v[1]) for v in fixos.values())} |")
    w(f"| vindo de registrador | {n_reg} |")
    w(f"| **total** | **{total}** |")
    w("")
    w("> **Nao leia isto como \"so 35 textos sao traduziveis\".** O caminho")
    w("> principal do texto traduzido nao passa pelo rotulo direto:")
    w("> `get_lang_str` tem **163** chamadas, e **63** delas vao para")
    w("> `pstr_cmd_view`, que copia o texto para dentro de uma mensagem")
    w("> (offset `0x14`) e a envia a view. Boa parte das chamadas \"vindo")
    w("> de registrador\" e justamente isso chegando. A lista de LITERAIS")
    w("> abaixo e que e solida — esses nenhuma traducao alcanca.\n")
    w("## Os literais\n")
    w("| texto | endereco | onde aparece | avaliacao |")
    w("|---|---|---|---|")
    AVAL = {
        "Time's up!": "**INGLES visivel** — mensagem do despertador",
        "OK": "**INGLES visivel** — botao do despertador",
        "yes": "**INGLES visivel** — dialogo de desligar",
        "no": "**INGLES visivel** — dialogo de desligar",
        "MHZ": "unidade; aceitavel sem traduzir",
        "--": "marcador de vazio",
        "1/253": "**espaco reservado do contador** da tela Tocando Agora",
        "00:00:21": "espaco reservado de tempo decorrido",
        "00:03:25": "espaco reservado de tempo restante",
        "14:00": "espaco reservado de hora",
        "OpenPod": "nosso — carimbo da area livre",
        " ": "espaco",
        ":": "separador",
    }
    for o, (s, sites) in sorted(reais.items(), key=lambda kv: kv[1][0]):
        onde = ", ".join(sorted({nome(z) for z in sites}))
        w(f"| `{s}` | `0x{o:06X}` | {onde} | {AVAL.get(s.strip(), '—')} |")
    w("")
    w("## Conclusao\n")
    w("**Nao, a tabela de idiomas nao cobre tudo.** Ha texto em ingles")
    w("fixo no binario que aparece na tela em qualquer idioma:")
    w("`Time's up!`, `OK`, `yes`, `no`.\n")
    w("Traduzir isso **nao** e editar a tabela: exige gravar a string nova")
    w("na area livre e repor o ponteiro, um a um — o mesmo metodo do")
    w("`patch_menu_text.py`.\n")
    w("Os ponteiros de FONTE que passam pelo filtro de string estao")
    w("excluidos desta lista: " +
      ", ".join(f"`0x{x:06X}`" for x in sorted(FONTES)) + ".")
    open(a.md, "w").write("\n".join(out) + "\n")
    print(f"\n  gravado: {a.md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
