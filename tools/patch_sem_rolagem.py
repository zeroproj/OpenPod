#!/usr/bin/env python3
"""
patch_sem_rolagem.py — a barra de rolagem some de TODAS as telas.

O ALVO

    Item M-d de `docs/MARTE_ALVO.md` §2. A lista do iPod nano nao tem
    barra de rolagem. O firmware de fabrica desenha uma, fina, a direita
    — visivel na foto de 2026-09-14, tela Configurar.

A CAUSA — medida, e o caminho barato so apareceu na segunda olhada

    Primeiro eu procurei em `CRIA_CONTEINER` (0x00D21690) e conclui que
    o firmware nao configurava a barra, logo o item exigiria GANCHO na
    area livre. Isso estava certo sobre a `CRIA_CONTEINER` — ela so mexe
    em padding — e errado como conclusao.

    A barra nao e CONFIGURADA em lugar nenhum: ela e DESENHADA pelo
    tratador de evento compartilhado do `lv_obj`, no evento
    `LV_EVENT_DRAW_POST` (24 = 0x18). E como na LVGL v8:

        else if(code == LV_EVENT_DRAW_POST) {
            draw_scrollbar(obj, draw_ctx);
        }

    No binario:

        00D4967E  182f      cmp   r7, #0x18      <- o evento
        00D49680  7ff46cae  bne.w 0xD4935C       <- nao e? retorna
        00D49684  ...                            <- e? desenha a barra

    E `0xD4935C` e o EPILOGO da funcao:

        00D4935C  add sp, #0x48
        00D4935E  pop.w {r4, r5, r6, r7, r8, pc}

    Todas as leituras de estilo do bloco sao de `LV_PART_SCROLLBAR`
    (`mov.w r1, #0x10000`) — props 0x20 cor, 0x21 opacidade, 0x30/0x31
    borda, 0x1032 largura. O bloco e so a barra, e e a cauda da funcao.

O CONSERTO — 1 byte

    0x0014967E   18 -> FF     cmp r7, #0x18  ->  cmp r7, #0xFF

    Os codigos de evento da LVGL vao ate ~35; `r7` nunca vale 0xFF.
    Entao o `bne` passa a ser SEMPRE tomado, e a funcao retorna sem
    desenhar a barra.

    **Para todos os outros eventos o comportamento e IDENTICO** — o
    desvio ja era tomado antes. So o caso `r7 == 0x18` muda.

POR QUE MEXER NO COMPARADOR, E NAO NO ESTILO

    Zerar a largura ou a opacidade exigiria SETAR estilo em cada
    conteiner — 59 telas, ou um gancho. O comparador e um ponto so, no
    tratador compartilhado, e desliga o desenho na raiz.

USO
    python3 tools/patch_sem_rolagem.py --in <entrada.bin> --out <saida.bin>
    python3 tools/patch_sem_rolagem.py --in <entrada.bin> --dry-run
    python3 tools/patch_sem_rolagem.py --autoteste

DEPENDENCIAS
    Python 3. Nada mais.

LIMITACOES
    - desliga a barra em TODAS as telas, sem excecao. E o que o alvo
      pede, mas e bom saber: nao ha como manter em uma tela so;
    - a ROLAGEM continua funcionando. So o indicador visual some;
    - nao aloca, nao usa a area livre, nao tem `--em`.
"""

import argparse, hashlib, os, sys

RAIZ     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = "firmware/ORIGINAL/GN438_original.bin"
PROIBIDO = 0x0000D000
TAMANHO  = 0x200000

OFF  = 0x0014967E     # o imediato do `cmp r7, #0x18`
DE   = 0x18           # LV_EVENT_DRAW_POST
PARA = 0xFF           # codigo de evento que nunca ocorre

# guarda-corpo: o contexto exato em volta do portao.
CONTEXTO = [
    (0x0014967F, bytes([0x2F])),                    # o `cmp r7,` do proprio
    (0x00149680, bytes.fromhex("7ff46cae")),        # bne.w 0xD4935C
    (0x00149684, bytes.fromhex("3046")),            # mov r0, r6
    (0x0014935C, bytes.fromhex("12b0")),            # add sp,#0x48  (epilogo)
    (0x0014935E, bytes.fromhex("bde8f081")),        # pop.w {...,pc}
    (0x001496AA, bytes.fromhex("4ff48031")),        # mov.w r1,#0x10000
]


def confere_contexto(d):
    for off, esperado in CONTEXTO:
        achado = bytes(d[off:off + len(esperado)])
        if achado != esperado:
            return False, (f"contexto em 0x{off:06X}: achei {achado.hex()}, "
                           f"esperava {esperado.hex()} — esta imagem nao e o "
                           f"firmware esperado")
    return True, "ok"


def aplica(d):
    ok, msg = confere_contexto(d)
    if not ok:
        return False, msg
    if d[OFF] == PARA:
        return False, f"0x{OFF:06X} ja esta {PARA:02X}: patch ja aplicado"
    if d[OFF] != DE:
        return False, f"0x{OFF:06X} tem {d[OFF]:02X}, esperado {DE:02X}"
    d[OFF] = PARA
    return True, "ok"


def autoteste():
    print("\n  AUTOTESTE — 1 byte no portao do DRAW_POST\n")
    o = os.path.join(RAIZ, ORIGINAL)
    if not os.path.exists(o):
        print(f"  FALTA: {o}")
        return 1
    orig = open(o, "rb").read()
    d = bytearray(orig)

    ok, msg = aplica(d)
    if not ok:
        print(f"  FALHOU: {msg}")
        return 1

    falhas = []
    dif = [i for i in range(len(orig)) if orig[i] != d[i]]
    print(f"    bytes alterados        {len(dif)}  "
          + ("OK" if len(dif) == 1 else "FALHOU"))
    if len(dif) != 1:
        falhas.append(f"esperava 1 byte, foram {len(dif)}")
    elif dif[0] != OFF:
        falhas.append(f"byte em 0x{dif[0]:06X}, esperava 0x{OFF:06X}")
    print(f"    offset                 0x{dif[0]:06X}  "
          + ("OK" if dif and dif[0] == OFF else "FALHOU"))

    hw = d[OFF] | (d[OFF + 1] << 8)
    print(f"    instrucao resultante   cmp r7,#0x{hw & 0xFF:02X}  "
          + ("OK" if hw == 0x2FFF else "FALHOU"))
    if hw != 0x2FFF:
        falhas.append(f"halfword 0x{hw:04X}, esperava 0x2FFF")

    # o desvio NAO pode ter sido tocado
    bne = bytes(d[0x00149680:0x00149684])
    print(f"    bne.w intocado         {bne.hex()}  "
          + ("OK" if bne == bytes.fromhex("7ff46cae") else "FALHOU"))
    if bne != bytes.fromhex("7ff46cae"):
        falhas.append("o bne.w foi alterado — nao devia")

    ok2, _ = aplica(d)
    print("    recusa 2a aplicacao    " + ("OK" if not ok2 else "FALHOU"))
    if ok2:
        falhas.append("aplicar duas vezes NAO foi recusado")

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
        description="a barra de rolagem some de todas as telas (M-d)")
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

    print("\n  SEM BARRA DE ROLAGEM  (Marte M-d)\n")
    ok, msg = aplica(d)
    if not ok:
        print(f"  ABORTADO: {msg}", file=sys.stderr)
        return 1

    print("  ALTERACAO")
    print(f"    0x{OFF:06X}   1 B  {DE:02X} -> {PARA:02X}")
    print("      cmp r7,#0x18  ->  cmp r7,#0xFF")
    print("      o portao do LV_EVENT_DRAW_POST, onde a barra e desenhada")
    print()
    print("  NAO TOCADO")
    print("    o bne.w em 0x00149680 — o desvio continua o mesmo")
    print("    o resto do tratador: para todo evento != 0x18, identico")
    print()
    print("  ALCANCE   tratador de evento COMPARTILHADO do lv_obj")
    print("            nenhuma tela desenha barra de rolagem")
    print("            a ROLAGEM continua funcionando; some so o indicador")
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
