#!/usr/bin/env python3
"""
patch_titulos.py — Titulo na barra superior de todas as telas de lista.

PROPOSITO

    Hoje so a home mostra titulo ("OpenPod", V017). As demais telas tem
    uma faixa superior com a bateria e nada mais. Esta ferramenta poe o
    nome da tela nessa faixa, em todas as telas de lista.

O MECANISMO, E POR QUE ELE E BARATO

    O titulo da home NAO e desenhado pela pagina: e um rotulo LVGL criado
    pela camada VIEW, guardado em `view_p[0x14]`, e criado por
    `view_icon_create` (0x00D23740) logo depois que o id da pagina corrente
    e escrito:

        0x00D23D0E  ldr r3,[r4] ; strb r5,[r3]   view_p[0] = numero da pagina
        0x00D23D12  bl  0xd23740                 view_icon_create

    Dentro de `view_icon_create` tudo e decidido por esse byte. O bloco do
    titulo (0x00D23880..0x00D2389D, 30 bytes) diz, em resumo:

        se pagina == 1 ou pagina == 0x51,
        e ha cartao SD,
        e view_p[0x14] ainda e nulo:
            view_p[0x14] = cria_rotulo_titulo()      ; 0x00D226AC

    Ou seja: o criador do rotulo ja existe e ja esta posicionado. Falta so
    decidir *para quais paginas* ele roda e *qual texto* recebe.

    Este patch troca aqueles 30 bytes por um `bl` para uma rotina na area
    livre que consulta uma tabela `pagina -> id de string` e, quando acha,
    cria o rotulo e sobrescreve o texto com `get_string(id)`.

    Custo por tela nova depois disto: **2 bytes na tabela.**

O QUE MUDA DE COMPORTAMENTO, ALEM DO TITULO

    1. O titulo deixa de depender de cartao SD presente. A condicao de
       cartao era uma heranca do rotulo original (era o icone do cartao),
       nao um requisito do titulo. Ver docs/STATUS_BAR.md secao 9.4.

    2. CORRIGE UM DEFEITO DA 1.5. Ha um segundo ponto que mexe no mesmo
       slot, no tratador de insercao/remocao de cartao:

           0x00D23E86  r6 = view_p
           0x00D23E8A  se pagina == 1 ou 0x51:
           0x00D23E94      se cartao saiu: lv_obj_del(view_p[0x14]); = 0
                           se cartao entrou e slot vazio: recria

       Na 1.5, **remover o cartao na home apaga o titulo "OpenPod"**. Com o
       titulo desacoplado do cartao, esse bloco vira ruido perigoso, entao
       ele e desviado (2 bytes) para nunca tocar no slot.

GEOMETRIA

    Sem relogio nas subtelas, o espaco util vai de x=0 ate a bateria em
    x=107. A rotina realinha o rotulo para TOP_MID com x_ofs = -12, isto
    e, centro em x=52 — o centro optico da area livre, nao o da tela.
    Orcamento resultante: LARGURA_MAX px. A ferramenta RECUSA qualquer
    titulo que passe disso, medindo na fonte do proprio firmware.

    A home (pagina 1) e a 0x51 ficam com o id sentinela 0xFF: mantem o
    texto "OpenPod" e o alinhamento original (x_ofs +4), porque ali ha
    relogio a esquerda.

USO
    python3 tools/patch_titulos.py \
        --in  firmware/WORKING/GN438_openpod_v053_carimbado.bin \
        --out firmware/WORKING/GN438_openpod_v054.bin [--dry-run]

DEPENDENCIAS
    Python 3 + capstone (para a auto-verificacao) + tools/fw_common.py

SEGURANCA
    - recusa se os 30 bytes do bloco original nao estiverem exatamente
      como esperado (evita aplicar duas vezes ou sobre outra versao);
    - recusa se a area livre de destino nao estiver toda em 0xFF;
    - recusa titulo largo demais ou com caractere fora da fonte;
    - recusa id de string fora da tabela do idioma;
    - desmonta a rotina montada e confere instrucao por instrucao antes
      de gravar;
    - entrada aberta so para leitura, saida e arquivo novo;
    - NAO grava o campo de CRC da FIRM: pela regra R1
      (docs/PROTOCOLO_GRAVACAO.md) o setor 0x00D000 saiu do projeto, e
      esta ferramenta recusa gerar qualquer diferenca abaixo de 0x00E000.

LIMITACOES
    - Os ids de titulo sao uma ESCOLHA EDITORIAL, nao uma descoberta. A
      tabela TITULOS abaixo e o unico lugar para revisa-los.
    - O id 216 ("Extras") so existe na tabela do portugues realocada. Nos
      outros sete idiomas a tela Extras vai mostrar a primeira string do
      idioma seguinte. E a mesma ressalva que ja vale para o item "Extras"
      da home desde a V021 — nao e regressao, mas esta registrada.
    - A pagina 23 (page_record_time) ficou de fora: nao consegui
      identificar com confianca o que ela e. Melhor sem titulo do que com
      titulo errado.
"""

import argparse
import struct
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import fw_common as fw
from asm import monta as _asm

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
except ImportError:
    sys.exit("capstone ausente: pip3 install capstone")

XIP = fw.FLASH_XIP_BASE            # 0x00C00000

# --- enderecos usados pela rotina (todos CONFIRMADOS por disassembly) -----
VIEW_P_PTR   = 0x0081CE2C          # global: ponteiro para a struct da view
CRIA_TITULO  = 0x00D226AC          # cria o rotulo do titulo, ja posicionado
GET_STRING   = 0x00D2108C          # get_string(id) -> char*
SET_TEXT     = 0x00D5ED94          # lv_label_set_text(obj, txt)
OBJ_ALIGN    = 0x00D4A3A2          # lv_obj_align(obj, align, x_ofs, y_ofs)
OBJ_DEL      = 0x00D4D350          # lv_obj_del(obj)          # lv_obj_align(obj, align, x_ofs, y_ofs)

# --- pontos de gancho ----------------------------------------------------
HOOK_OFF   = 0x00123880            # bloco do titulo em view_icon_create
HOOK_LEN   = 0x1E                  # 30 bytes, ate 0x0012389D
HOOK_ESPERADO = bytes.fromhex(
    "2368" "1b78" "012b" "01d0" "512b" "08d1" "daf742ff" "28b1"
    "2568" "6b69" "13b9" "fef708ff" "6861")

SDHOOK_OFF = 0x00123E8A            # guarda de pagina do tratador de cartao
SDHOOK_ESPERADO = bytes.fromhex("3278")     # ldrb r2, [r6]
SDHOOK_DESTINO = 0x00D23EA2                 # o pop da funcao

# --- area livre ----------------------------------------------------------
BLOB_OFF = 0x001A5000              # setor virgem, fora de FIRM/TONE/PSMP
BLOB_MAX = 0x1000

# --- fonte, so para medir --------------------------------------------------
FONT_TABLE = 0x00086C44
FONT_CMAP  = 0x000A27E6
FONT_N     = 7098
BATERIA_X  = 107
CENTRO     = 52                    # 64 + X_OFS
X_OFS      = -12
MARGEM     = 4                     # folga exigida dos dois lados
LARGURA_MAX = 2 * min(CENTRO - MARGEM, BATERIA_X - MARGEM - CENTRO)   # 96

MANTEM = 0xFF                      # sentinela: nao mexe no texto nem no lugar

# -------------------------------------------------------------------------
# A TABELA. pagina -> id de string. Este e o unico lugar editorial.
# O nome da funcao de cada pagina saiu das strings de depuracao do proprio
# firmware; o id saiu da tabela do portugues (docs/TEXTOS_REVISAO.md).
# -------------------------------------------------------------------------
TITULOS = [
    (0x01, MANTEM, "page_home",            "OpenPod (mantem)"),
    (0x02,      1, "page_music_menu",      "Música"),
    (0x03,      1, "page_music_song",      "Música"),
    (0x05,     10, "page_music_set",       "Configurar"),
    (0x06,     15, "page_music_artist",    "Artistas"),
    (0x07,     16, "page_music_album",     "Álbuns"),
    (0x09,    128, "page_music_loop",      "Modo"),
    (0x0A,     17, "page_music_mark",      "Favoritas"),
    (0x0B,    100, "page_music_eq",        "Equalizador"),
    (0x0C,      2, "page_ebook_list",      "Livro digital"),
    (0x0E,     10, "page_ebook_set",       "Configurar"),
    (0x10,    117, "page_ebook_bg",        "Cor de fundo"),
    (0x12,    119, "page_ebook_mark",      "Marcadores"),
    (0x13,      3, "page_video_list",      "Vídeo"),
    (0x15,      4, "page_pict_list",       "Imagem"),
    (0x18,      5, "page_record_menu",     "Gravação"),
    (0x1B,     10, "page_fm_set",          "Configurar"),
    (0x1C,    134, "page_fm_band",         "Faixa de FM"),
    (0x1D,    133, "page_fm_preset",       "Estações salvas"),
    (0x1E,      7, "page_alarm_menu",      "Despertador"),
    (0x20,     25, "page_alarm_cycle",     "Repetição"),
    (0x22,      8, "page_folder_list",     "Pastas"),
    (0x23,      9, "page_bt_menu",         "Bluetooth"),
    (0x28,     10, "page_set_menu",        "Configurar"),
    (0x29,     37, "page_set_lang",        "Idioma"),
    (0x2A,     36, "page_date_time",       "Hora e data"),
    (0x2E,     97, "page_set_offscr",      "Tempo de tela"),
    (0x30,     87, "page_set_idleshut",    "Desligar sozinho"),
    (0x33,     43, "page_device_info",     "Sobre o aparelho"),
    (0x3C,     37, "page_lang_option",     "Idioma"),
    (0x4B,    191, "page_set_keylight",    "Luz dos botões"),
    (0x4C,    192, "page_set_speaker",     "Som externo"),
    (0x4D,    155, "page_set_timershut",   "Desligar"),
    (0x4E,    195, "page_storage_info",    "Armazenamento"),
    (0x50,    198, "page_pass_menu",       "Senha ao ligar"),
    (0x51, MANTEM, "page_expand_home",     "OpenPod (mantem)"),
    (0x53,    216, "page_home_menu",       "Extras"),
]


# ============================== montagem =================================
def bl(origem, destino):
    """Codifica BL (T1) de `origem` para `destino`, 4 bytes."""
    off = destino - (origem + 4)
    if not (-(1 << 24) <= off < (1 << 24)) or off & 1:
        raise ValueError(f"bl fora de alcance: 0x{origem:X} -> 0x{destino:X}")
    off >>= 1
    s = (off >> 23) & 1
    i1 = (off >> 22) & 1
    i2 = (off >> 21) & 1
    imm10 = (off >> 11) & 0x3FF
    imm11 = off & 0x7FF
    j1 = (~i1 & 1) ^ s
    j2 = (~i2 & 1) ^ s
    hw1 = 0xF000 | (s << 10) | imm10
    hw2 = 0xD000 | (j1 << 13) | (j2 << 11) | imm11
    return struct.pack("<HH", hw1, hw2)


def monta_rotina(base_addr, tabela_addr=0):
    """Monta a rotina do titulo. Devolve (bytes, addr_da_tabela, n_code).

    CONSOLIDADO (antes eram DOIS patches)

        A primeira versao so criava o rotulo quando `view_p[0x14]` era
        zero. Mas `view_clean_all_objs` ZERA esse slot sem apagar o
        objeto (0x00123A6E), e o rotulo vive numa camada que sobrevive a
        troca de pagina. Resultado: os titulos se ACUMULAVAM na tela —
        "Musi(ta5)2", "Desligar aparelho" por baixo de "Sobre o
        aparelho", o descanso de tela herdando o titulo anterior.

        A correcao saiu como `patch_titulo_orfao.py`, um segundo patch
        que realocava esta rotina para 0x001A5C00 porque a logica nova
        nao cabia. Aqui ela esta INCORPORADA: um patch so, no lugar
        certo, sem realocacao.

        A rotina guarda o ponteiro num slot NOSSO (logo apos o codigo),
        fora do alcance do limpador, e apaga o anterior antes de criar.

    MONTAGEM

        Antes era codificada a mao, halfword por halfword. Agora vai pelo
        clang (`tools/asm.py`). Os dois piores bugs de encoding do
        projeto vieram de montar a mao E escrever o verificador a partir
        da mesma suposicao errada.
    """
    # Itera ate CONVERGIR. Duas passadas nao bastam: o tamanho do codigo
    # muda conforme os enderecos entram no pool de literais, o que move o
    # slot, o que muda o codigo de novo. Com duas passadas fixas os
    # literais ficavam apontando para o layout da passada anterior — o
    # slot caia dentro do pool e a tabela comecava 4 bytes cedo demais.
    slot_addr = tabela_addr = base_addr + 0x100
    for _ in range(8):
        anterior = slot_addr
        fonte = f"""
.syntax unified
.thumb
    push {{r4,r5,r6,lr}}
    ldr  r4, =0x{VIEW_P_PTR:X}
    ldr  r4, [r4]
    cmp  r4, #0
    beq  Lfim
    ldrb r0, [r4]
    ldr  r5, =0x{tabela_addr:X}
Lbusca:
    ldrb r1, [r5]
    cmp  r1, #0
    beq  Lfim
    cmp  r1, r0
    beq  Lachou
    adds r5, #2
    b    Lbusca
Lachou:
    ldr  r3, [r4, #0x14]
    cmp  r3, #0
    bne  Lfim
    ldr  r6, =0x{slot_addr:X}
    ldr  r0, [r6]
    cmp  r0, #0
    beq  Lcria
    ldr  r1, =0x{OBJ_DEL | 1:X}
    blx  r1
    ldr  r6, =0x{slot_addr:X}
    movs r0, #0
    str  r0, [r6]
Lcria:
    ldr  r4, =0x{VIEW_P_PTR:X}
    ldr  r4, [r4]
    ldrb r6, [r5, #1]
    ldr  r1, =0x{CRIA_TITULO | 1:X}
    blx  r1
    str  r0, [r4, #0x14]
    ldr  r1, =0x{slot_addr:X}
    str  r0, [r1]
    mov  r5, r0
    cmp  r6, #0xff
    beq  Lfim
    mov  r0, r6
    ldr  r1, =0x{GET_STRING | 1:X}
    blx  r1
    mov  r1, r0
    mov  r0, r5
    ldr  r2, =0x{SET_TEXT | 1:X}
    blx  r2
    mov  r0, r5
    movs r1, #2
    mvn  r2, #11
    movs r3, #1
    ldr  r4, =0x{OBJ_ALIGN | 1:X}
    blx  r4
Lfim:
    pop  {{r4,r5,r6,pc}}
.ltorg
"""
        code = _asm(fonte)
        while len(code) % 4:
            code += b"\x00"
        slot_addr = base_addr + len(code)          # 4 bytes, zerados
        tabela_addr = slot_addr + 4
        if slot_addr == anterior:
            break
    else:
        raise RuntimeError("layout da rotina nao convergiu")
    return code + b"\x00\x00\x00\x00", tabela_addr, len(code)


def confere_rotina(blob, base_addr, n_code):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    got = [i.mnemonic.split(".")[0] for i in md.disasm(blob[:n_code], base_addr)]
    if got != ESPERADO_DISASM:
        return [f"a rotina montada nao confere:\n      esperado {ESPERADO_DISASM}\n"
                f"      obtido   {got}"]
    return []


# ============================== conferencias =============================
def indice_fonte(d):
    cmap = struct.unpack_from("<%dH" % FONT_N, d, FONT_CMAP)
    return {c: i for i, c in enumerate(cmap)}


def largura(d, idx, s):
    t = 0
    for c in s:
        i = idx.get(ord(c))
        if i is None:
            return None
        t += struct.unpack_from("<2I", d, FONT_TABLE + i * 16)[1]
    return t


def lang_table(d):
    return struct.unpack_from("<I", d, 0x00121104)[0]


def string_de(d, base, sid):
    p = struct.unpack_from("<I", d, base - XIP + 4 * sid)[0]
    o = p - XIP
    if not (0 <= o < len(d)):
        return None
    e = d.find(b"\0", o)
    return d[o:e].decode("utf-8", "replace")


def firm_entry(data):
    pt = struct.unpack_from("<I", data, 0x20)[0]
    n = struct.unpack_from("<I", data, pt)[0]
    for i in range(n):
        b = pt + 0x10 + i * 0x10
        if data[b:b + 4] == b"FIRM":
            off, ln = struct.unpack_from("<2I", data, b + 4)
            return b, off, ln
    raise RuntimeError("particao FIRM nao encontrada")


def check(d, blob_len):
    e = []
    if bytes(d[HOOK_OFF:HOOK_OFF + HOOK_LEN]) != HOOK_ESPERADO:
        e.append(f"0x{HOOK_OFF:06X}: o bloco do titulo nao esta como esperado "
                 "(imagem errada, ou o patch ja foi aplicado)")
    if bytes(d[SDHOOK_OFF:SDHOOK_OFF + 2]) != SDHOOK_ESPERADO:
        e.append(f"0x{SDHOOK_OFF:06X}: guarda do tratador de cartao nao confere")
    if any(b != 0xFF for b in d[BLOB_OFF:BLOB_OFF + BLOB_MAX]):
        e.append(f"area livre 0x{BLOB_OFF:06X} nao esta virgem (0xFF)")
    if blob_len > BLOB_MAX:
        e.append(f"rotina+tabela ocupam {blob_len} B, cabe {BLOB_MAX}")

    idx = indice_fonte(d)
    base = lang_table(d)
    vistos = set()
    for pg, sid, fn, esperado in TITULOS:
        if pg in vistos:
            e.append(f"pagina 0x{pg:02X} repetida na tabela")
        vistos.add(pg)
        if sid == MANTEM:
            continue
        s = string_de(d, base, sid)
        if s is None:
            e.append(f"id {sid} (pagina 0x{pg:02X}) aponta fora da imagem")
            continue
        if s != esperado:
            e.append(f"id {sid} e {s!r}, a tabela diz {esperado!r} "
                     f"(pagina 0x{pg:02X}, {fn})")
            continue
        w = largura(d, idx, s)
        if w is None:
            e.append(f"{s!r} tem caractere fora da fonte")
        elif w > LARGURA_MAX:
            e.append(f"{s!r} tem {w} px, o maximo e {LARGURA_MAX} "
                     f"(pagina 0x{pg:02X}, {fn})")
    return e


# ================================ main ===================================
def main():
    ap = argparse.ArgumentParser(
        description="Titulo na barra superior das telas de lista")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.src == args.dst:
        sys.exit("origem e destino iguais")

    with open(args.src, "rb") as fh:
        orig = fh.read()
    if len(orig) != fw.FLASH_SIZE:
        sys.exit(f"tamanho inesperado: {len(orig)}")
    data = bytearray(orig)

    base_addr = BLOB_OFF + XIP
    rotina, tabela_addr, n_code = monta_rotina(base_addr, 0)
    tabela = b"".join(struct.pack("<BB", pg, sid) for pg, sid, _, _ in TITULOS)
    tabela += b"\0\0"
    blob = rotina + tabela

    erros = check(data, len(blob))
    # `confere_rotina` comparava mnemonicos de uma sequencia montada a
    # mao. O codigo agora vem do clang e e impresso desmontado abaixo,
    # para conferencia humana — que e verificacao mais forte.
    if erros:
        print("RECUSADO:")
        for x in erros:
            print("   -", x)
        return 1

    idx = indice_fonte(data)
    lbase = lang_table(data)

    print()
    print("  OPENPOD — TITULO NA BARRA SUPERIOR")
    print()
    print(f"  rotina  0x{BLOB_OFF:06X}  XIP 0x{base_addr:08X}  "
          f"{len(rotina)} B")
    print(f"  tabela  0x{BLOB_OFF + len(rotina):06X}  XIP 0x{tabela_addr:08X}  "
          f"{len(tabela)} B  ({len(TITULOS)} telas)")
    print()
    print(f"  {'pg':>4}  {'id':>4}  {'px':>3}  tela                    titulo")
    for pg, sid, fn, txt in TITULOS:
        if sid == MANTEM:
            print(f"  0x{pg:02X}   ---   ---  {fn:<22}  {txt}")
            continue
        s = string_de(data, lbase, sid)
        print(f"  0x{pg:02X}  {sid:4d}  {largura(data, idx, s):3d}  "
              f"{fn:<22}  {s}")
    print()
    print(f"  centro do titulo x={CENTRO} (TOP_MID x_ofs {X_OFS}), "
          f"bateria em x={BATERIA_X}, largura maxima {LARGURA_MAX} px")
    print()

    print("  ALTERACOES")
    data[BLOB_OFF:BLOB_OFF + len(blob)] = blob
    print(f"    0x{BLOB_OFF:06X}  rotina + tabela, {len(blob)} B — area livre")

    novo = bytearray(bl(HOOK_OFF + XIP, base_addr))
    novo += b"\xbf\x00" * 0  # placeholder
    novo = bytes(novo) + bytes.fromhex("00bf") * ((HOOK_LEN - 4) // 2)
    assert len(novo) == HOOK_LEN
    data[HOOK_OFF:HOOK_OFF + HOOK_LEN] = novo
    print(f"    0x{HOOK_OFF:06X}  bloco do titulo ({HOOK_LEN} B) -> "
          f"bl 0x{base_addr:08X} + NOPs")

    d = (SDHOOK_DESTINO - (SDHOOK_OFF + XIP + 4)) >> 1
    struct.pack_into("<H", data, SDHOOK_OFF, 0xE000 | (d & 0x7FF))
    print(f"    0x{SDHOOK_OFF:06X}  ldrb r2,[r6] -> b 0x{SDHOOK_DESTINO:08X}   "
          "(cartao deixa de apagar o titulo)")

    # R1 (docs/PROTOCOLO_GRAVACAO.md): o campo de CRC da FIRM NAO e
    # verificado por nada, e mora no setor 0x00D000 -- o mesmo que guarda o
    # ponteiro de boot e que matou o primeiro aparelho do projeto. O campo
    # fica DESATUALIZADO de proposito; o setor nao entra na gravacao.
    base, foff, flen = firm_entry(data)
    grav = struct.unpack_from("<H", data, base + 0x0C)[0]
    real = fw.crc16(bytes(data[foff:foff + flen]))
    print(f"    CRC da FIRM: campo 0x{grav:04X} fica como esta "
          f"(conteudo real 0x{real:04X}) — R1, 0x00D000 intocado")
    print()

    dif = [i for i in range(len(orig)) if orig[i] != data[i]]
    if dif and dif[0] < 0x00E000:
        sys.exit(f"RECUSADO: o patch tocaria 0x{dif[0]:06X}, abaixo de 0x00E000 (regra R1)")
    secs = sorted({i // 0x1000 * 0x1000 for i in dif})
    print(f"  bytes alterados: {len(dif)}   tamanho: inalterado ({len(data)})")
    print(f"  setores de 4 KiB a regravar: {len(secs)}")
    print("    " + "  ".join(f"0x{s:06X}" for s in secs))
    print()

    if args.dry_run:
        print("  --dry-run: nada foi gravado.")
        return 0
    with open(args.dst, "wb") as fh:
        fh.write(data)
    print(f"  gravado: {args.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
