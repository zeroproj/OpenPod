#!/usr/bin/env python3
"""
check_branch_targets.py — a trava que faltava na 3.x

PROPOSITO
    Antes de gravar qualquer imagem modificada, responder duas perguntas
    que a verificacao byte a byte NAO responde:

      1. Algum desvio (b/bl/bne/bhi/tbb/...) do firmware ORIGINAL aponta
         para dentro de uma faixa que o patch sobrescreveu?
         -> Foi assim que a Core 3.1.2 apagou 5 destinos de page1_process.

      2. Alguma faixa modificada comeca no MEIO de uma instrucao do
         original, deixando meia instrucao orfa?
         -> Foi assim que a 3.1.2 deixou lixo em 0x00D01100.

    Nenhuma das duas aparece no diff, no CRC ou na releitura do aparelho.
    Sao a classe de defeito que so quebra na tela.

USO
    python3 tools/check_branch_targets.py ORIGINAL.bin PATCHED.bin
    python3 tools/check_branch_targets.py ORIGINAL.bin PATCHED.bin --json

    Saida: relatorio no stdout. Codigo de saida 1 se achar qualquer
    problema, 0 se estiver limpo. Serve para travar um build.

DEPENDENCIAS
    capstone  (pip install capstone)

LIMITACOES
    - So enxerga desvios com destino IMEDIATO. Desvios por registrador
      (bx rN, blx rN) e tabelas de ponteiros NAO sao cobertos.
    - Varre a faixa de codigo como fluxo linear Thumb-2; dados embutidos
      no meio do codigo podem gerar instrucao falsa. Por isso o relatorio
      informa a confianca e nao substitui leitura humana.
    - Nao valida semantica: dizer que nada quebrou aqui nao prova que o
      patch esta correto, so que nao destruiu alvo de desvio.

EXEMPLO REAL
    $ python3 tools/check_branch_targets.py \
        firmware/ORIGINAL/GN438_original.bin \
        firmware/WORKING/GN438_core_3.1.2.bin

    5 desvios apontam para faixa sobrescrita   <- a 3.1.2 reprovaria
"""
import argparse
import json
import struct
import sys

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
except ImportError:
    sys.exit("erro: falta capstone.  pip install capstone")

XIP_BASE = 0x00C00000
# faixa de codigo da particao FIRM (ver docs/FIRMWARE_MAP.md)
CODE_START = 0x0000E000
CODE_END = 0x001A0570

BRANCHES = ("b", "bl", "blx", "bx", "cbz", "cbnz")


def regioes_alteradas(orig: bytes, patch: bytes, folga: int = 8):
    """Faixas [ini, fim] onde os bytes diferem, unindo o que estiver a
    menos de `folga` bytes de distancia."""
    if len(orig) != len(patch):
        sys.exit(f"erro: tamanhos diferentes ({len(orig)} vs {len(patch)})")
    runs, cur = [], None
    for i in range(len(orig)):
        if orig[i] != patch[i]:
            if cur is None:
                cur = [i, i]
            else:
                cur[1] = i
        elif cur is not None and i - cur[1] > folga:
            runs.append(tuple(cur))
            cur = None
    if cur:
        runs.append(tuple(cur))
    return runs


def varre_desvios(orig: bytes, ini: int, fim: int, base: int):
    """Devolve todo desvio com destino imediato encontrado na faixa.

    NAO desmonta linearmente: a FIRM mistura codigo e dados, e um
    fluxo linear morre no primeiro byte de dado -- foi assim que a
    primeira versao desta ferramenta deu 'aprovado' numa imagem com
    cinco destinos destruidos.

    Em vez disso tenta decodificar UMA instrucao em cada alinhamento de
    2 bytes. Isso gera falso positivo em cima de dados, e isso e
    DESEJADO: a ferramenta e uma trava, entao ela erra para o lado de
    reclamar demais, nunca para o lado de deixar passar.
    """
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    achados = []
    for off in range(ini, fim, 2):
        try:
            ins = next(md.disasm(orig[off:off + 4], off + base, count=1), None)
        except Exception:
            continue
        if ins is None or not ins.mnemonic.startswith("b"):
            continue
        if not ins.op_str.startswith("#"):
            continue
        try:
            alvo = int(ins.op_str[1:], 16)
        except ValueError:
            continue
        achados.append((ins.address, f"{ins.mnemonic} {ins.op_str}", alvo, ins.size))
    return achados


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("original")
    ap.add_argument("patched")
    ap.add_argument("--json", action="store_true", help="saida legivel por maquina")
    ap.add_argument("--baseline", metavar="IMG",
                    help="imagem boa conhecida (ex: a ultima estavel). "
                         "Com ela, so os achados NOVOS reprovam -- o ruido "
                         "que a baseline ja tinha vira nota de rodape.")
    ap.add_argument("--base", type=lambda s: int(s, 0), default=XIP_BASE)
    args = ap.parse_args()

    orig = open(args.original, "rb").read()
    patch = open(args.patched, "rb").read()

    regioes = regioes_alteradas(orig, patch)
    dentro_codigo = [r for r in regioes if r[1] >= CODE_START and r[0] < CODE_END]

    desvios = varre_desvios(orig, CODE_START, CODE_END, args.base)

    def parece_tabela_de_ponteiros(a, b):
        """A faixa esta dentro de uma corrida densa de ponteiros XIP?

        Patch de DADO -- repontar uma entrada de tabela de strings, por
        exemplo -- cai numa faixa de 3 ou 4 bytes no meio de uma tabela
        de ponteiros. A varredura por alinhamento decodifica as palavras
        vizinhas como instrucao e inventa desvios que apontam para la.

        Se as 8 palavras ao redor forem todas ponteiros XIP validos, e
        tabela, nao codigo.
        """
        centro = (a // 4) * 4
        validos = 0
        for k in range(-4, 5):
            q = centro + 4 * k
            if q < 0 or q + 4 > len(orig):
                continue
            v = struct.unpack("<I", orig[q:q + 4])[0]
            if 0x00C00000 <= v < 0x00E00000:
                validos += 1
        return validos >= 8

    def parece_codigo(a, b):
        """Uma faixa e CODIGO se desmonta de ponta a ponta sem morrer.

        Regiao de recurso grafico nao passa nesse teste -- e e por isso
        que ela existe: sem o filtro, a folha de icones do menu gera
        dezenas de 'desvios' falsos que afogam os verdadeiros.
        """
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        n = b - a + 1
        if parece_tabela_de_ponteiros(a, b):
            return False          # tabela de ponteiros: e dado
        if n < 4:
            return True            # curto demais para julgar: trata como codigo
        coberto = sum(i.size for i in md.disasm(orig[a:b + 1], a + args.base))
        return coberto >= 0.7 * n

    classe = {r: ("codigo" if parece_codigo(*r) else "dados")
              for r in dentro_codigo}

    def em_regiao_alterada(off):
        for a, b in dentro_codigo:
            if a <= off <= b:
                return (a, b)
        return None

    # --- verificacao 1: desvios cujo destino caiu em faixa sobrescrita ---
    quebrados = []
    for addr, texto, alvo, _sz in desvios:
        reg = em_regiao_alterada(alvo - args.base)
        if reg is None:
            continue
        # um desvio que esta DENTRO da propria faixa reescrita nao conta:
        # o patch substituiu origem e destino de proposito.
        if em_regiao_alterada(addr - args.base):
            continue
        if classe.get(reg) == "dados":
            continue          # faixa de recurso: desvio decodificado e ruido
        # O alvo ainda e inicio de instrucao valida na imagem nova?
        # Se sim, a instrucao foi ALTERADA NO LUGAR -- o desvio continua
        # pousando certo. Se nao, o alvo foi DESTRUIDO.
        md1 = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        o_alvo = alvo - args.base
        ins_nova = next(md1.disasm(patch[o_alvo:o_alvo + 4], alvo), None)
        no_lugar = ins_nova is not None and alvo == reg[0] + args.base
        quebrados.append({
            "origem": addr,
            "instrucao": texto,
            "alvo": alvo,
            "faixa": [reg[0] + args.base, reg[1] + args.base],
            "no_lugar": no_lugar,
            "virou": f"{ins_nova.mnemonic} {ins_nova.op_str}" if ins_nova else "?",
        })

    # --- linha de base: separa o que e REGRESSAO do que e ruido antigo ---
    herdados = set()
    if args.baseline:
        base_img = open(args.baseline, "rb").read()
        base_regioes = [r for r in regioes_alteradas(orig, base_img)
                        if r[1] >= CODE_START and r[0] < CODE_END]

        def em_base(off):
            return any(a <= off <= b for a, b in base_regioes)

        for q in quebrados:
            if em_base(q["alvo"] - args.base):
                herdados.add(q["origem"])
        novos = [q for q in quebrados if q["origem"] not in herdados]
    else:
        novos = quebrados

    # separa os que foram DESTRUIDOS dos que so mudaram de instrucao
    destruidos = [q for q in novos if not q.get("no_lugar")]
    no_lugar = [q for q in novos if q.get("no_lugar")]

    # --- verificacao 2: desvio que PULA PARA O MEIO da faixa reescrita ---
    # (roda sobre `novos`, ja filtrado pela baseline)
    # Mais util que procurar instrucao partida (que da falso positivo em
    # cima de dados): se alguem desvia para o meio do que voce reescreveu,
    # o patch tem que ter preservado aquele ponto de entrada.
    orfas = []
    for q in destruidos:
        if q["alvo"] != q["faixa"][0]:
            orfas.append({
                "desvio_em": q["origem"],
                "entra_no_meio_de": q["faixa"],
                "no_offset": q["alvo"],
            })

    if args.json:
        print(json.dumps({"destinos_quebrados": destruidos,
                          "alterados_no_lugar": no_lugar,
                          "instrucoes_partidas": orfas}, indent=2))
        return 1 if (destruidos or orfas) else 0

    print(f"original : {args.original}")
    print(f"patched  : {args.patched}")
    n_cod = sum(1 for v in classe.values() if v == "codigo")
    print(f"regioes alteradas dentro da FIRM: {len(dentro_codigo)}"
          f"  ({n_cod} de codigo, {len(dentro_codigo) - n_cod} de dados)")
    print("faixas de dados sao ignoradas na verificacao de desvios.\n")

    if args.baseline:
        print(f"baseline : {args.baseline}")
        print(f"achados herdados da baseline (ignorados): {len(herdados)}\n")

    if no_lugar:
        print(f"-- {len(no_lugar)} alvo(s) ALTERADO(S) NO LUGAR (confira, "
              f"nao reprova)\n")
        for q in no_lugar:
            print(f"   {q['origem']:#010x}  {q['instrucao']:<22}"
                  f" -> {q['alvo']:#010x} virou `{q['virou']}`")
        print()

    if destruidos:
        etiqueta = "NOVO(S)" if args.baseline else ""
        print(f"!! {len(destruidos)} desvio(s) {etiqueta} apontam para "
              f"alvo DESTRUIDO\n")
        for q in destruidos:
            print(f"   {q['origem']:#010x}  {q['instrucao']:<22}"
                  f" -> destino {q['alvo']:#010x} foi reescrito")
            print(f"       (faixa {q['faixa'][0]:#010x}-{q['faixa'][1]:#010x})")
        print()
    else:
        print("ok: nenhum desvio novo aponta para alvo destruido\n")

    if orfas:
        print(f"!! {len(orfas)} desvio(s) entram no MEIO de uma faixa reescrita\n")
        for o in orfas:
            print(f"   {o['desvio_em']:#010x} entra em {o['no_offset']:#010x},"
                  f" no meio da faixa {o['entra_no_meio_de'][0]:#010x}"
                  f"-{o['entra_no_meio_de'][1]:#010x}")
        print()
    else:
        print("ok: nenhum desvio entra no meio de faixa reescrita\n")

    ruim = bool(destruidos or orfas)
    print("REPROVADO" if ruim else "APROVADO")
    return 1 if ruim else 0


if __name__ == "__main__":
    sys.exit(main())
