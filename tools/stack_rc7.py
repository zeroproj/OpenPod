#!/usr/bin/env python3
"""
stack_rc7.py — o tamanho de PILHA (estático) das cadeias de chamada do
firmware GN-438, para a ficha 009 (a RC7 reinicia no aparelho).

PROPOSITO

    A ficha 008 somou "1216 B" no ramo `get_path` e disse que a MainTask
    (pilha 0x400) executa esse mesmo caminho. As duas coisas so fecham se a
    unidade de 0x1000/0x400 for PALAVRA (o FreeRTOS conta a pilha em
    palavras) — ou se a soma da 008 estiver errada. Esta ferramenta mede a
    soma por conta propria: le o quadro (push/sub sp) de cada funcao e
    soma o maximo ao longo da cadeia de chamadas.

    Ela tambem responde onde roda a `page_music_play_label_process`
    (a view) e qual e a cadeia real da `get_path` a partir da ViewTask.

COMO MEDE

    - varre a regiao XIP (0x00C00000..0x00DA0000) instrucao a instrucao;
    - cada `push {...,lr}` (16 ou 32 bits) marca o inicio de uma funcao; o
      quadro dela e o `push` + o `sub sp,#imm` que vem logo depois;
    - a funcao vai ate o proximo inicio de funcao (ou 0x400 bytes);
    - as chamadas sao os `bl` (T1) dentro do corpo, com o alvo decodificado
      do proprio binario;
    - o uso de pilha de uma funcao = quadro + maximo das chamadas;
    - uma chamada para fora do dump (mask ROM em 0x00xxxxxx, RAM em
      0x008xxxxx) e tratada como "quadro desconhecido" e sinalizada.

USO

    python3 tools/stack_rc7.py --cadeia 0xCFEFC4          # a partir da get_path
    python3 tools/stack_rc7.py --cadeia 0xD32204 --rotulo "view"
    python3 tools/stack_rc7.py --tarefas                   # as pilhas das tarefas
    python3 tools/stack_rc7.py --imagem firmware/WORKING/x.bin --cadeia 0x...

DEPENDENCIAS

    Python 3 + capstone (pip3 install capstone).

LIMITACOES

    - analise ESTATICA: nao mede o uso real, mede o maximo possivel por
      ramo de chamada (o pico e o maximo das chains, nao a soma);
    - o limite de cada funcao e o proximo `push {...,lr}`: um compilador
      que deixa codigo solto depois do `pop` faz a funcao "engolir" o
      vizinho (e o resultado fica MAIOR, nunca menor — o que serve para
      provar que a pilha cabe);
    - as rotinas da mask ROM (0x00xxxxxx) e da RAM (0x008xxxxx) nao estao
      no dump: o quadro delas e desconhecido e a cadeia e marcada como
      incompleta;
    - nao sabe de interrupcoes: uma ISR que consome pilha durante o ramo
      analisado nao entra na conta.
"""

import argparse
import struct
import sys

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
except ImportError:
    sys.exit("capstone ausente: pip3 install capstone")

XIP = 0x00C00000
FIM = 0x00DA0000
ORIGINAL = "firmware/ORIGINAL/GN438_original.bin"

# a criacao de tarefas (osFreeRTOS): o wrapper e a funcao de criacao
TASK_CREATE = 0x00D6ACAC
OS_THREAD = 0x00CF7AD4


def _regs(ins):
    """Os nomes dos registradores de um `push`/`pop`."""
    out = []
    for o in ins.operands:
        if o.type == 1:
            out.append(ins.reg_name(o.reg))
        elif o.type == 4:            # REG_LIST
            out.extend(ins.reg_name(r) for r in o.regs)
    return out


class Firmware:
    """A imagem disassemblada: funcoes, quadros e chamadas."""

    def __init__(self, dados, base=XIP, fim=FIM):
        self.d = dados
        self.base = base
        self.fim = fim
        self.funcs = {}      # addr -> {"quadro": int, "calls": [addr]}
        self._scan()

    # ------------------------------------------------------------ scanner
    def _scan(self):
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
        md.detail = True
        md.skipdata = True
        d, base = self.d, self.base
        prologues = []
        instr = {}
        i = base
        while i < self.fim:
            bloco = d[i - base:i - base + 4]
            if len(bloco) < 4:
                break
            res = list(md.disasm(bloco, i, count=1))
            if not res:
                i += 2
                continue
            ins = res[0]
            instr[i] = ins
            if ins.mnemonic in ("push", "push.w"):
                regs = _regs(ins)
                # "push {...,lr}" marca o inicio de uma funcao
                if "lr" in regs:
                    prologues.append(i)
            i += ins.size
        prologues = sorted(set(prologues))
        # uma unica varredura: cada instrucao pertence a funcao do ultimo
        # inicio de funcao; as chamadas sao guardadas por funcao
        idx = 0
        for a in sorted(instr):
            while idx + 1 < len(prologues) and prologues[idx + 1] <= a:
                idx += 1
            ini = prologues[idx]
            f = self.funcs.setdefault(ini, {"quadro": 0, "calls": [],
                                             "fim": prologues[idx + 1]
                                             if idx + 1 < len(prologues)
                                             else ini + 0x400})
            ins = instr[a]
            if ins.mnemonic in ("bl", "bl.w"):
                f["calls"].append(self._alvo(ins))
        # quadro de cada funcao: o push + o sub sp que vem depois
        for ini, f in self.funcs.items():
            quadro = 0
            j = ini
            while j < min(f["fim"], ini + 0x40):
                ins = instr.get(j)
                if ins is None:
                    break
                if ins.mnemonic in ("push", "push.w"):
                    quadro += 4 * len(_regs(ins))
                elif ins.mnemonic in ("sub", "sub.w"):
                    # "sub sp,#imm" (2 operandos) ou "sub.w sp,sp,#imm" (3)
                    if len(ins.operands) == 2 and ins.operands[1].type == 2:
                        quadro += ins.operands[1].value.imm
                        break
                    if len(ins.operands) == 3 and ins.operands[2].type == 2:
                        quadro += ins.operands[2].value.imm
                        break
                j += ins.size
            f["quadro"] = quadro

    @staticmethod
    def _alvo(ins):
        """O alvo de um `bl` (T1), decodificado do proprio binario."""
        if ins.mnemonic == "bl.w":
            return ins.operands[0].value if ins.operands else None
        # bl (T1): F000 F800
        h1, h2 = struct.unpack_from("<HH", ins.bytes)
        if (h1 & 0xF800) != 0xF000 or (h2 & 0xD000) != 0xD000:
            return None
        s = (h1 >> 10) & 1
        i1 = 1 - (((h2 >> 13) & 1) ^ s)
        i2 = 1 - (((h2 >> 11) & 1) ^ s)
        off = ((s << 24) | (i1 << 23) | (i2 << 22) | ((h1 & 0x3FF) << 12)
               | ((h2 & 0x7FF) << 1))
        if s:
            off -= (1 << 25)
        return (ins.address + 4 + off) & 0xFFFFFFFF

    # ------------------------------------------------------------- medidas
    def funcao(self, addr):
        """A funcao que contem `addr` (ou None)."""
        if addr in self.funcs:
            return addr
        cand = [a for a in self.funcs if a <= addr < self.funcs[a]["fim"]]
        return max(cand) if cand else None

    def cadeia(self, raiz, prof=6):
        """(bytes, cadeia, fora) — o maximo de pilha a partir de `raiz`.

        `bytes` e um MINIMO: as chamadas para fora do dump (mask ROM/RAM)
        entram com quadro 0 e sao listadas em `fora`."""
        memo = {}
        na_pilha = set()

        def rec(addr):
            if addr in memo:
                return memo[addr]
            ini = self.funcao(addr)
            if ini is None:
                return (0, [addr], [])
            if ini in na_pilha:        # recursao: nao conta duas vezes
                return (0, [], [])
            na_pilha.add(ini)
            f = self.funcs[ini]
            melhor = (f["quadro"], [ini], [])
            for c in f["calls"]:
                if c is None:
                    continue
                if not (self.base <= c < self.fim):
                    # fora do dump (mask ROM / RAM): quadro desconhecido
                    cand = (f["quadro"], [ini] + [c], [c])
                else:
                    sub = rec(c)
                    cand = (f["quadro"] + sub[0], [ini] + sub[1], sub[2])
                if cand[0] > melhor[0]:
                    melhor = cand
            na_pilha.discard(ini)
            memo[addr] = melhor
            return melhor

        sys.setrecursionlimit(10000)
        return rec(raiz)

    # ------------------------------------------------------------ tarefas
    def quem_chama(self, alvo):
        """Os enderecos que chamam `alvo` (bl/bl.w, alvo decodificado)."""
        achados = []
        for ini, f in self.funcs.items():
            for c in f["calls"]:
                if c == alvo:
                    achados.append(ini)
        return sorted(set(achados))

    def tarefas(self):
        """As criacoes de tarefa: (endereço da criacao, tamanho da pilha)."""
        d, base = self.d, self.base
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
        md.detail = True
        md.skipdata = True
        achados = []
        i = base
        while i < self.fim:
            bloco = d[i - base:i - base + 4]
            if len(bloco) < 4:
                break
            res = list(md.disasm(bloco, i, count=1))
            if not res:
                i += 2
                continue
            ins = res[0]
            if ins.mnemonic in ("bl", "bl.w"):
                alvo = self._alvo(ins)
                if alvo in (TASK_CREATE,):
                    tam = self._tamanho_pilha(i)
                    achados.append((i, tam))
            i += ins.size
        return achados

    def _tamanho_pilha(self, addr):
        """O `str rX, [sp, #0x24]` que vem antes da criacao da tarefa."""
        d, base = self.d, self.base
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
        md.detail = True
        md.skipdata = True
        achados = []
        j = addr - 0x60
        while j < addr:
            bloco = d[j - base:j - base + 4]
            if len(bloco) < 4:
                j += 2
                continue
            res = list(md.disasm(bloco, j, count=1))
            if not res:
                j += 2
                continue
            ins = res[0]
            if ins.mnemonic in ("str", "str.w") and len(ins.operands) >= 2:
                m = ins.operands[1]
                if m.type == 3 and getattr(m.mem, "base", None) == 12 and \
                        (getattr(m.mem, "disp", 0) or 0) == 0x24:
                    achados.append((ins.address, ins.operands[0].reg))
            j += ins.size
        if not achados:
            return None
        end, reg = achados[-1]
        # volta ate o `mov.w rX, #imm` que carregou o valor
        j = end - 0x40
        while j < end:
            bloco = d[j - base:j - base + 4]
            res = list(md.disasm(bloco, j, count=1))
            if res and res[0].mnemonic in ("mov", "mov.w") and \
                    len(res[0].operands) == 2 and res[0].operands[0].reg == reg \
                    and res[0].operands[1].type == 2:
                return res[0].operands[1].value.imm
            j += 2
        return None


def main():
    ap = argparse.ArgumentParser(description="pilha estatica do GN-438")
    ap.add_argument("--imagem", default=ORIGINAL)
    ap.add_argument("--cadeia", type=lambda s: int(s, 0), action="append",
                    default=[])
    ap.add_argument("--tarefas", action="store_true")
    ap.add_argument("--quem", type=lambda s: int(s, 0), action="append",
                    default=[], help="quem chama este endereco")
    ap.add_argument("--rotulo", default="")
    a = ap.parse_args()

    dados = open(a.imagem, "rb").read()
    fw = Firmware(dados)

    if a.tarefas:
        print("criacoes de tarefa (osFreeRTOS):")
        for end, tam in fw.tarefas():
            print("  criacao em 0x%08X  pilha = %s (0x%X)" %
                  (end, tam, tam if tam else 0))
        return 0

    if a.quem:
        for alvo in a.quem:
            print("quem chama 0x%08X:" % alvo)
            for c in fw.quem_chama(alvo):
                f = fw.funcs.get(c)
                print("    0x%08X  (quadro %s)" % (c, f["quadro"] if f else "?"))
        return 0

    for raiz in a.cadeia:
        bytes_, cadeia, fora = fw.cadeia(raiz)
        print("cadeia a partir de 0x%08X %s" % (raiz, a.rotulo))
        print("  pico de pilha: >= %d bytes (0x%X)  [MINIMO: as chamadas "
              "fora do dump entram com quadro 0]" % (bytes_, bytes_))
        for c in cadeia:
            f = fw.funcs.get(fw.funcao(c) or 0)
            nome = ("quadro %s" % (f["quadro"] if f else "?")) \
                if fw.base <= c < fw.fim else "FORA DO DUMP"
            print("    0x%08X  %s" % (c, nome))
        if fora:
            print("  chamadas fora do dump no caminho: %s" %
                  ", ".join("0x%08X" % c for c in sorted(set(fora))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
