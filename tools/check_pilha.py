#!/usr/bin/env python3
"""
check_pilha.py — a trava que a Core 4.5 provou que faltava

O DEFEITO QUE ELE PEGA
    Quando se enxerta uma rotina no MEIO de uma funcao de fabrica, o
    desvio e um `b.w` -- nao um `bl`. A rotina herda o frame da funcao
    hospedeira: o `push` do prologo dela ja aconteceu.

    Se a rotina enxertada sai com `bx lr` ou `pop {pc}` sem ter
    empilhado nada, ela volta SEM desfazer o `push` do hospedeiro:
    pilha desbalanceada e registradores salvos nao restaurados.

    Core 4.5: o empilhador comeca com `push {r4,r5,r6,lr}`; a rotina
    enxertada saia com `bx lr`. Como o empilhador roda em TODA navegacao
    de pagina, o aparelho reiniciava ao entrar em qualquer item do
    Extras.

    Core 3.2 foi a mesma familia: saltar para um trampolim que faz
    `pop.w` de SEIS registradores a partir de um frame de QUATRO.

    Nenhuma das duas aparece no diff, no CRC, nem em
    check_branch_targets -- nao e desvio quebrado, e pilha.

A REGRA
    Rotina alcancada por `b.w` a partir de codigo de fabrica:
      - pode sair por `b`/`b.w` de volta para dentro do hospedeiro;
      - pode sair por um epilogo que espelhe o prologo do hospedeiro;
      - NAO pode sair por `bx lr` nem por `pop {pc}` sem ter feito o
        `push {lr}` correspondente DENTRO da propria rotina.

    Rotina alcancada por `bl` tem frame proprio: a regra nao se aplica.

USO
    python3 tools/check_pilha.py ORIGINAL.bin PATCHED.bin

    Codigo de saida 1 se achar problema. Serve para travar um build.

LIMITACOES
    - So enxerga rotinas na area livre (>= 0x001A3038) alcancadas por
      desvio vindo da FIRM de fabrica.
    - Nao simula a pilha: aplica a regra acima, que cobre as duas
      classes que ja quebraram aparelho neste projeto.
"""
import sys

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
except ImportError:
    sys.exit("erro: falta capstone.  pip install capstone")

BASE_XIP   = 0x00C00000
FIRM_INI   = 0x0000E000
AREA_LIVRE = 0x001A3038
FIRM_FIM   = 0x001A0570


def decodifica(buf, off, base=BASE_XIP, n=4):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    return next(md.disasm(buf[off:off + n], off + base), None)


def acha_ganchos(orig, patch):
    """Desvios `b.w` de dentro da FIRM de fabrica para a area livre."""
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    out = []
    for off in range(FIRM_INI, FIRM_FIM, 2):
        if patch[off:off + 4] == orig[off:off + 4]:
            continue
        ins = next(md.disasm(patch[off:off + 4], off + BASE_XIP), None)
        if ins is None or ins.size != 4:
            continue
        if not ins.mnemonic.startswith("b") or not ins.op_str.startswith("#"):
            continue
        alvo = int(ins.op_str[1:], 16) - BASE_XIP
        # alvo tem que cair DENTRO da flash, na area livre. Fora disso e
        # ruido: dado grafico decodificado como instrucao.
        if not (AREA_LIVRE <= alvo < 0x00200000):
            continue
        com_link = ins.mnemonic.startswith("bl")
        out.append((off, alvo, com_link, f"{ins.mnemonic} {ins.op_str}"))
    return out


def regs(op):
    """{'r4','r5','lr'} a partir de 'push {r4, r5, lr}'."""
    return {x.strip() for x in op.strip("{} ").split(",") if x.strip()}


def prologo_do_hospedeiro(patch, gancho, recuo=0x80):
    """Sobe a partir do gancho ate o `push` que abre a funcao."""
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    achado = None
    for ini in range(max(0, gancho - recuo), gancho, 2):
        for ins in md.disasm(patch[ini:ini + 4], ini + BASE_XIP):
            if ins.mnemonic.startswith("push"):
                achado = (ins.address, regs(ins.op_str))
            break
    return achado


def analisa_rotina(patch, ini, salvos, limite=0x120):
    """`salvos` = registradores que o HOSPEDEIRO empilhou.

    Saida valida, herdando o frame:
      - `pop` com os mesmos registradores, trocando lr por pc;
      - qualquer desvio de volta para dentro do hospedeiro;
      - `pop {pc}` casando com um `push {lr}` feito na propria rotina.
    """
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    esperado = (salvos - {"lr"}) | {"pc"} if salvos else None
    proprio = False
    suspeitas = []
    for ins in md.disasm(patch[ini:ini + limite], ini + BASE_XIP):
        m, op = ins.mnemonic, ins.op_str
        if m.startswith("push"):
            proprio = "lr" in regs(op)
            continue
        if m.startswith("pop") and "pc" in op:
            if proprio:
                pass                      # frame proprio: ok
            elif esperado is None:
                suspeitas.append((ins.address, f"{m} {op}", "hospedeiro nao identificado"))
            elif regs(op) != esperado:
                suspeitas.append((ins.address, f"{m} {op}",
                                  "nao espelha o prologo "
                                  f"{{{', '.join(sorted(salvos))}}}"))
            break
        if m == "bx" and op == "lr":
            if not proprio:
                suspeitas.append((ins.address, f"{m} {op}",
                                  "nao desfaz o push do hospedeiro"))
            break
        if m in ("b", "b.w") and op.startswith("#"):
            break
    return suspeitas


def main():
    if len(sys.argv) != 3:
        sys.exit("uso: check_pilha.py <ORIGINAL.bin> <PATCHED.bin>")
    orig = open(sys.argv[1], "rb").read()
    patch = open(sys.argv[2], "rb").read()
    if len(orig) != len(patch):
        sys.exit("erro: tamanhos diferentes")

    ganchos = acha_ganchos(orig, patch)
    print(f"ganchos da area livre encontrados: {len(ganchos)}\n")
    ruim = 0
    for off, alvo, com_link, texto in ganchos:
        tipo = "bl  (frame proprio)" if com_link else "b.w (herda o frame)"
        print(f"  {off + BASE_XIP:#010x}  {texto:<22} {tipo}")
        if com_link:
            continue
        pro = prologo_do_hospedeiro(patch, off)
        if pro:
            print(f"      hospedeiro abre em {pro[0]:#010x} com "
                  f"push {{{', '.join(sorted(pro[1]))}}}")
        for addr, ins, motivo in analisa_rotina(patch, alvo, pro[1] if pro else None):
            print(f"      !! {addr:#010x}  {ins}  — {motivo}")
            ruim += 1
    print()
    if ruim:
        print(f"REPROVADO: {ruim} saida(s) desbalanceada(s)")
        return 1
    print("APROVADO: nenhuma saida desbalanceada")
    return 0


if __name__ == "__main__":
    sys.exit(main())
