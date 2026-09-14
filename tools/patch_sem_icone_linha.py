#!/usr/bin/env python3
"""
patch_sem_icone_linha.py — some o icone DECORATIVO das linhas de lista.

O ALVO

    Item M-e de `docs/MARTE_ALVO.md` §2. A lista do iPod nano nao tem
    icone por item. O firmware de fabrica poe um em toda linha:
    engrenagem no Configurar, "tres tracinhos" nas demais.

O QUE ESTE PATCH **NAO** TIRA — e isto e o ponto todo

    Nem todo icone de linha e enfeite. Medido, funcao a funcao:

        U+F0C9  "tres tracinhos"   21 telas   DECORACAO   <- sai
        U+F013  engrenagem          2 telas   DECORACAO   <- sai
        ------------------------------------------------- 23 telas
        U+F00C  tique / check      10 telas   FUNCIONAL   <- FICA
        U+F028  volume              2 telas   FUNCIONAL   <- FICA
        U+F294  bluetooth           1 tela    FUNCIONAL   <- FICA
        U+F095  telefone            1 tela    FUNCIONAL   <- FICA

    **O tique `U+F00C` FICA, e nao e negociavel.** Ele mostra QUAL opcao
    esta escolhida — em Idioma, sem ele nao da para saber qual idioma
    esta ativo. Tirar seria seguir o mockup ao custo de quebrar a tela,
    e a regra §0 do MARTE_ALVO manda registrar o desvio, nao forcar.

    O nano tambem marca a opcao selecionada nessas telas.

COMO EU QUASE ERREI ISTO

    Medindo so o binario, vi "U+F0C9 em 21 das 37 funcoes que usam a
    fonte de icones" e conclui: apagar deixaria 21 telas sem icone e 16
    com — inconsistente, logo SEM PORTAO, logo M-e custa 37 pontos ou um
    gancho. Registrei isso como resultado.

    Estava errado. As outras 16 nao sao listas com enfeite: sao icones
    que FAZEM alguma coisa. O mantenedor e que separou, observando a
    tela — "a engrenagem sempre aparece e tem outras subtelas que
    aparece tres tracinho".

    A licao: o binario diz QUANTOS e ONDE. Ele nao diz o que e
    DECORACAO e o que e INFORMACAO. Isso a tela responde.

O CONSERTO — 2 bytes

    As strings de glifo sao UTF-8 de 3 bytes + terminador. Zerar o
    primeiro byte transforma cada uma em string VAZIA, e o rotulo do
    icone fica sem texto.

        0x000D3261   EF -> 00     U+F0C9  (0x00CD3261)   38 ponteiros
        0x0005D622   EF -> 00     U+F013  (0x00C5D622)    2 ponteiros

    CONFERIDO: nenhum ponteiro aponta para o MEIO de nenhuma das duas
    strings (offsets +1, +2, +3). So para o inicio. Entao zerar o
    primeiro byte e seguro — os bytes restantes viram lixo que ninguem
    le.

USO
    python3 tools/patch_sem_icone_linha.py --in <entrada.bin> --out <saida.bin>
    python3 tools/patch_sem_icone_linha.py --in <entrada.bin> --dry-run
    python3 tools/patch_sem_icone_linha.py --autoteste

DEPENDENCIAS
    Python 3. Nada mais.

LIMITACOES E RISCOS

    - NAO SE SABE se o texto vai encostar na esquerda ou se vai ficar um
      BURACO onde estava o icone. Depende de a linha usar layout flex ou
      posicao absoluta para os filhos. `lv_flex.c` esta compilado neste
      firmware, o que sugere que encosta — mas isso a TELA responde.
      Se ficar buraco, o conserto e outro patch, sobre a posicao do
      rotulo, e ai medido com a tela na mao;
    - o ponto branco de estado (ex.: "Ativar alarme") e OUTRO objeto, a
      direita, e nao e tocado;
    - nao aloca, nao usa a area livre, nao tem `--em`.
"""

import argparse, hashlib, os, sys

RAIZ     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = "firmware/ORIGINAL/GN438_original.bin"
PROIBIDO = 0x0000D000
TAMANHO  = 0x200000

# (offset, bytes esperados, addr XIP, nome, quantas telas)
GLIFOS = [
    (0x000D3261, bytes.fromhex("ef8389"), 0x00CD3261, "U+F0C9 tres tracinhos", 21),
    (0x0005D622, bytes.fromhex("ef8093"), 0x00C5D622, "U+F013 engrenagem",      2),
]

# guarda-corpo: os glifos FUNCIONAIS tem de continuar intactos.
# Se algum destes nao bater, a imagem nao e a esperada — ou alguem ja
# mexeu nos icones, e este patch nao deve rodar por cima.
PRESERVAR = [
    (0x0005D610, bytes.fromhex("ef808c"), "U+F00C tique — FICA, e informacao"),
    (0x0005D6E8, bytes.fromhex("ef80a8"), "U+F028 volume — FICA"),
    (0x0005D6EC, bytes.fromhex("ef8a94"), "U+F294 bluetooth — FICA"),
    (0x0005D6F0, bytes.fromhex("ef8295"), "U+F095 telefone — FICA"),
]


def confere_contexto(d):
    for off, esperado, desc in PRESERVAR:
        achado = bytes(d[off:off + 3])
        if achado != esperado:
            return False, (f"0x{off:06X} ({desc}): achei {achado.hex()}, "
                           f"esperava {esperado.hex()}")
    # o terminador tem de estar onde se espera
    for off, esperado, addr, nome, _ in GLIFOS:
        if d[off + 3] != 0x00:
            return False, (f"0x{off + 3:06X}: esperava terminador 00, "
                           f"achei {d[off + 3]:02X} — {nome} nao e string de "
                           f"um glifo")
    return True, "ok"


def aplica(d):
    ok, msg = confere_contexto(d)
    if not ok:
        return False, msg
    ja = 0
    for off, esperado, addr, nome, _ in GLIFOS:
        if d[off] == 0x00:
            ja += 1
        elif bytes(d[off:off + 3]) != esperado:
            return False, (f"0x{off:06X} tem {bytes(d[off:off+3]).hex()}, "
                           f"esperado {esperado.hex()} — {nome}")
    if ja == len(GLIFOS):
        return False, "patch ja aplicado"
    if ja:
        return False, f"{ja} de {len(GLIFOS)} glifos ja zerados: estado misto"
    for off, _, _, _, _ in GLIFOS:
        d[off] = 0x00
    return True, "ok"


def autoteste():
    print("\n  AUTOTESTE — 2 bytes, e os icones FUNCIONAIS intactos\n")
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
          + ("OK" if len(dif) == 2 else "FALHOU"))
    if len(dif) != 2:
        falhas.append(f"esperava 2 bytes, foram {len(dif)}")

    esperados = sorted(g[0] for g in GLIFOS)
    print(f"    offsets                {[f'0x{i:06X}' for i in dif]}  "
          + ("OK" if sorted(dif) == esperados else "FALHOU"))
    if sorted(dif) != esperados:
        falhas.append("os offsets nao sao os dois glifos decorativos")

    for off, esperado, nome, in [(a, b, c) for a, b, c in PRESERVAR]:
        igual = bytes(d[off:off + 3]) == esperado
        print(f"    {nome[:34]:34} " + ("OK" if igual else "FALHOU"))
        if not igual:
            falhas.append(f"{nome} foi alterado")

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
        description="some o icone decorativo das linhas (M-e)")
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

    print("\n  SEM ICONE DECORATIVO NAS LINHAS  (Marte M-e)\n")
    ok, msg = aplica(d)
    if not ok:
        print(f"  ABORTADO: {msg}", file=sys.stderr)
        return 1

    print("  ALTERACOES")
    for off, esperado, addr, nome, telas in GLIFOS:
        print(f"    0x{off:06X}   1 B  {esperado[0]:02X} -> 00   "
              f"{nome}  ({telas} telas)")
    print()
    print("  PRESERVADOS — icones que sao INFORMACAO, nao enfeite")
    for off, _, desc in PRESERVAR:
        print(f"    0x{off:06X}   {desc}")
    print()
    print("  o ponto de estado a direita (ex.: 'Ativar alarme') e outro")
    print("  objeto, e nao foi tocado")
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
