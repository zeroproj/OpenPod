#!/usr/bin/env python3
"""
make_install_kit.py — gera um kit OpenPod_Install completo e coerente.

PROPOSITO
    Elimina a classe de erro mais perigosa deste projeto: constantes
    (enderecos, tamanhos, hashes) transcritas a mao para dentro de um
    script de gravacao. Aqui TUDO e calculado a partir das imagens.

    Em 2026-09-12 uma suposicao transcrita a mao sobre a assinatura do
    write_flash corrompeu a tabela de particoes do aparelho. Este gerador
    existe por causa disso.

USO
    python3 tools/make_install_kit.py \\
        --base   firmware/WORKING/GN438_openpod_v001.bin \\
        --alvo   firmware/WORKING/GN438_openpod_v002.bin \\
        --origem firmware/ORIGINAL/GN438_original.bin \\
        --versao v002 \\
        --saida  OpenPod_Install_v002

    --base    o que o aparelho TEM agora (estado esperado ANTES)
    --alvo    o que queremos gravar
    --origem  ORIGINAL de fabrica, usado SO como referencia de hashes
              no diag.sh. A REVERSAO do patch usa a --base, nunca este.

SAIDA
    <saida>/  com os setores, o script de gravacao e o LEIA-ME.

REGRAS APLICADAS (ver docs/WRITE_FLASH_SEMANTICS.md)
    - um arquivo por setor de 4096 B; offset 0 = conteudo de destino
    - write_flash sempre com 0 no 2o argumento
    - nenhuma gravacao abaixo de 0x00D000 (bootloader intocado)
"""

import argparse
import subprocess, hashlib, os, sys

SETOR = 0x1000
LIMITE_BOOTLOADER = 0x00D000

REGIOES = [
    ("bootloader", 0,       51532),
    ("ptable",     53248,   64),
    ("FIRM",       57344,   1647984),
    ("TONE",       1708032, 8248),
]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def carregar(p):
    d = open(p, "rb").read()
    if len(d) != 0x200000:
        sys.exit("ERRO: %s tem %d bytes, esperado 2097152" % (p, len(d)))
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--alvo", required=True)
    ap.add_argument("--origem", required=True)
    ap.add_argument("--versao", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--descricao", default="")
    ap.add_argument("--sem-carimbo", action="store_true",
                    help="NAO carimbar a versao na tela Informacoes. "
                         "Use so para depuracao — um build publicado sem "
                         "carimbo mente sobre a propria versao.")
    ap.add_argument("--sem-up", action="store_true",
                    help="NAO gerar o .up. Por padrao ele sai sempre: desde "
                         "a OpenPod 1.0 o mantenedor atualiza pelo cartao SD, "
                         "e o .up e o unico formato que o bootloader le.")
    ap.add_argument("--ordem", default="",
                    help="Ordem EXPLICITA de gravacao, enderecos separados "
                         "por virgula (ex: 0x1A3000,0x37000,0x109000). "
                         "Regra R2 do PROTOCOLO_GRAVACAO.md: o setor que "
                         "ATIVA o patch vai por ultimo, para que todo "
                         "estado intermediario continue bootavel.")
    a = ap.parse_args()

    V = a.versao

    # CARIMBO DE VERSAO — obrigatorio, nao opcional.
    #
    # Regra do mantenedor (2026-09-13): *"toda vez que tiver uma coisa
    # muda a compilacao, e muda la no sistema, pois ai vou ter
    # visibilidade se aquela versao ta funcionando"*.
    #
    # A tela Configurar > Informacoes le um literal que NAO se atualiza
    # sozinho. Na 1.1 ela continuou dizendo "1.0" e o aparelho mentiu
    # sobre si mesmo. Agora o proprio gerador de kit carimba a versao no
    # alvo antes de empacotar: e impossivel publicar um build cuja tela
    # discorde do nome do kit.
    if not a.sem_carimbo:
        carimbado = a.alvo.replace(".bin", "_carimbado.bin")
        # UMA linha. A tela Informacoes sobrepoe linhas quando ha mais de
        # duas mensagens -- defeito de layout na camada VIEW, ainda nao
        # localizado. Enquanto nao for, menos linhas = mais legivel.
        texto = a.versao.replace("_", " ")
        r = subprocess.run(
            [sys.executable,
             os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "patch_versao.py"),
             "--in", a.alvo, "--out", carimbado, "--texto", texto],
            capture_output=True, text=True)
        if r.returncode:
            sys.exit("ERRO ao carimbar a versao:\n" + r.stdout + r.stderr)
        for ln in r.stdout.splitlines():
            if "texto novo" in ln or "relido pelo ponteiro" in ln:
                print("  " + ln.strip())
        a.alvo = carimbado

    base, alvo, origem = carregar(a.base), carregar(a.alvo), carregar(a.origem)

    dif = [i for i in range(len(alvo)) if alvo[i] != base[i]]
    if not dif:
        sys.exit("ERRO: alvo e base sao identicos. Nada a gravar.")
    setores = sorted({(i // SETOR) * SETOR for i in dif})

    if a.ordem:
        pedida = [int(x, 0) for x in a.ordem.split(",") if x.strip()]
        if sorted(pedida) != setores:
            sys.exit("ERRO: --ordem nao e uma permutacao dos setores do patch.\n"
                     "  patch : %s\n  ordem : %s"
                     % ([hex(s_) for s_ in setores], [hex(s_) for s_ in pedida]))
        setores = pedida
        print("ordem de gravacao EXPLICITA (R2): %s"
              % "  ".join(hex(s_) for s_ in setores))

    baixos = [s for s in setores if s < LIMITE_BOOTLOADER]
    if baixos:
        sys.exit("ERRO: o patch tocaria o bootloader em %s. RECUSADO." %
                 [hex(s) for s in baixos])

    os.makedirs(a.saida, exist_ok=True)
    for f in os.listdir(a.saida):
        os.remove(os.path.join(a.saida, f))

    # Os setores de REVERSAO vem da BASE, nao do ORIGINAL de fabrica.
    #
    # Por que: um patch toca um subconjunto dos setores. Se a reversao
    # escrevesse conteudo de fabrica nesse subconjunto, o resto da flash
    # continuaria no estado da base -> a FIRM ficaria MISTURADA e o CRC
    # gravado na tabela de particoes deixaria de bater com o conteudo.
    # Medido em 2026-09-12 sobre o V013: gravado 0x49A6, calculado 0xACBB.
    # Voltar para a BASE devolve o aparelho a um estado que ja foi
    # verificado e que ja bootou. Ver docs/ROLLBACK_POLICY.md.
    arquivos = []   # (endereco, nome_alvo, sha_alvo, nome_base, sha_base_f, sha_base)
    for s in setores:
        na, no = "%s_%X.bin" % (V, s), "base_%X.bin" % s
        ba, bo = alvo[s:s + SETOR], base[s:s + SETOR]
        open(os.path.join(a.saida, na), "wb").write(ba)
        open(os.path.join(a.saida, no), "wb").write(bo)
        arquivos.append((s, na, sha(ba), no, sha(bo), sha(base[s:s + SETOR])))

    reg_antes = [(n, o, t, sha(base[o:o + t])) for n, o, t in REGIOES]
    reg_depois = [(n, o, t, sha(alvo[o:o + t])) for n, o, t in REGIOES]

    # .up: gerado SEMPRE.
    #
    # A decisao mudou no mesmo dia em que foi tomada, e por evidencia de
    # uso: assim que a atualizacao por cartao passou a funcionar (V046), o
    # mantenedor passou a atualizar so por ela. O kit de setores e mais
    # economico, mas o .up e o unico formato que o bootloader le -- e e o
    # que dispensa PC, cabo e linha de comando.
    #
    # Vantagem que so ficou clara depois: o .up **nao confere estado**.
    # Reescreve a imagem inteira, entao funciona a partir de qualquer
    # versao. Nao ha como gravar o kit errado.
    if not a.sem_up:
        up = os.path.join(a.saida, "%s.up" % V)
        r = subprocess.run(
            [sys.executable,
             os.path.join(os.path.dirname(os.path.abspath(__file__)), "gera_up.py"),
             "--in", a.alvo, "--out", up],
            capture_output=True, text=True)
        if r.returncode:
            sys.exit("ERRO ao gerar o .up:\n" + r.stdout + r.stderr)
        for ln in r.stdout.splitlines():
            if "area livre em uso" in ln or "gravado:" in ln or "CRC do payload" in ln:
                print("  " + ln.strip())

    kib = len(setores) * SETOR // 1024
    script = os.path.join(a.saida, "flash_%s.sh" % V)
    with open(script, "w") as f:
        f.write(gerar_script(V, a.descricao, arquivos, reg_antes, reg_depois, kib))
    os.chmod(script, 0o755)

    with open(os.path.join(a.saida, "LEIA-ME.txt"), "w") as f:
        f.write(gerar_leiame(V, a.descricao, arquivos, kib))

    rc_src = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "recovery_check_linux.sh")
    if os.path.exists(rc_src):
        import shutil
        shutil.copy(rc_src, os.path.join(a.saida, "recovery_check_linux.sh"))
        os.chmod(os.path.join(a.saida, "recovery_check_linux.sh"), 0o755)

    dg = os.path.join(a.saida, "diag.sh")
    with open(dg, "w") as f:
        f.write(gerar_diag(V, reg_antes, reg_depois,
                           [(n, o, t, sha(origem[o:o + t])) for n, o, t in REGIOES]))
    os.chmod(dg, 0o755)

    print("kit gerado em %s/" % a.saida)
    print("  %d setores, %d KiB, %d bytes alterados" % (len(setores), kib, len(dif)))
    for s, na, ha, no, ho, hb in arquivos:
        print("  0x%06X  %-16s %s" % (s, na, ha[:16]))


def gerar_script(V, desc, arquivos, antes, depois, kib):
    L = []
    w = L.append
    w("#!/bin/sh")
    w("# flash_%s.sh — OpenPod. GERADO por tools/make_install_kit.py." % V)
    w("# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.")
    w("#")
    if desc:
        w("# %s" % desc)
        w("#")
    w("# Grava %d setores de 4096 B (%d KiB). O bootloader (0x0..0xD000)" % (len(arquivos), kib))
    w("# nao e endereçado. write_flash sempre com 0 no 2o argumento, a")
    w("# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).")
    w("#")
    w("# USO   sudo sh flash_%s.sh [/opt/smartlink_flash]" % V)
    w("")
    w("set -eu")
    w("export LC_ALL=C")
    w("")
    w('TOOLDIR=${1:-/opt/smartlink_flash}')
    w('TOOL="$TOOLDIR/smtlink_dump"')
    w("DEV=301a:2801")
    w('WORK=$(pwd)/openpod_flash_%s' % V)
    w('LOG="$WORK/flash_%s.log"' % V)
    w("WROTE=0")
    w("")
    w('mkdir -p "$WORK"; : > "$LOG"; exec 3>&1')
    w("""log() { printf '%s\\n' "$*" | tee -a "$LOG" >&3; }""")
    w("die() {")
    w('    log ""')
    w('    log "*** $*"')
    w('    if [ "$WROTE" -ne 0 ]; then')
    w('        log "*** JA HAVIA GRAVADO $WROTE setor(es). NAO DESLIGUE O APARELHO."')
    w('        log "*** REVERSAO para o estado ANTERIOR (a base deste kit):"')
    for s, na, ha, no, ho, hb in arquivos:
        w('        log "***   sudo $TOOL --id $DEV write_flash 0x%X 0 0x1000 %s"' % (s, no))
    w('        log "*** Depois rode diag.sh e confira antes de desligar."')
    w("    else")
    w('        log "*** Nada foi gravado."')
    w("    fi")
    w("    exit 1")
    w("}")
    w("""sha()  { python3 -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$1"; }""")
    w("""size() { python3 -c "import os,sys;print(os.path.getsize(sys.argv[1]))" "$1"; }""")
    w("""rsha() { python3 -c "import hashlib,sys;d=open(sys.argv[1],'rb').read()[int(sys.argv[2]):int(sys.argv[2])+int(sys.argv[3])];print(hashlib.sha256(d).hexdigest())" "$1" "$2" "$3"; }""")
    w("")
    w('log "======================================================================"')
    w('log " OpenPod — gravacao do %s   (%d setores, %d KiB)"' % (V.upper(), len(arquivos), kib))
    for s, na, ha, no, ho, hb in arquivos:
        w('log " 0x%06X +0x1000   <- %s"' % (s, na))
    w('log " bootloader (0x0..0xD000): NAO ENDERECADO"')
    w('log "======================================================================"')
    w('log ""')
    w("")
    w('[ "$(uname -s)" = "Linux" ] || die "Este script e para Linux."')
    w('[ -x "$TOOL" ] || die "smtlink_dump nao encontrado em $TOOLDIR"')
    w('for c in python3 lsusb; do')
    w('    command -v "$c" >/dev/null 2>&1 || die "faltando: $c"')
    w("done")
    w("")
    w('log "[1/6] conferindo os arquivos de setor..."')
    w("ck_file() {")
    w('    [ -f "$1" ] || die "nao encontrei $1"')
    w('    s=$(size "$1"); [ "$s" = "4096" ] || die "$1 tem $s bytes, esperado 4096"')
    w('    g=$(sha "$1");  [ "$g" = "$2" ] || die "SHA-256 de $1 nao confere.')
    w("    esperado $2")
    w('    obtido   $g"')
    w('    log "        OK   $1"')
    w("}")
    for s, na, ha, no, ho, hb in arquivos:
        w("ck_file %s %s" % (na, ha))
    for s, na, ha, no, ho, hb in arquivos:
        w("ck_file %s %s" % (no, ho))
    w("")
    w('log "[2/6] procurando o aparelho..."')
    w(bloco_aguardar())
    w("")
    w('# --- verificacao previa: recovery check -------------------------')
    w('# Confere os 15 hashes do codigo-fonte do smtlink_dump no commit')
    w('# travado e recompila. Garante que a ferramenta que vai ESCREVER')
    w('# no aparelho e exatamente a versao auditada. Ver RECOVERY_CHECK.md.')
    w('log ""')
    w('log "[2b/6] verificacao previa da ferramenta (recovery check)..."')
    w('if [ -f ./recovery_check_linux.sh ]; then')
    w('    printf "Rodar o recovery check agora? (confere a ferramenta e le a flash) [S/n] "')
    w('    read -r R0')
    w('    case "$R0" in')
    w('        [nN]*) log "        PULADO a pedido do operador" ;;')
    w('        *) log "        rodando — pode demorar (clona, confere 15 hashes, compila, le 2 MiB)"')
    w('           # IMPORTANTE: nao usar  cmd | tee || die  — o || receberia o')
    w('           # status do tee, e um recovery check REPROVADO passaria batido.')
    w('           if sh ./recovery_check_linux.sh "$WORK/precheck" >"$WORK/.rc_out" 2>&1; then')
    w('               RCST=0; else RCST=$?; fi')
    w('           tee -a "$LOG" >&3 < "$WORK/.rc_out"; rm -f "$WORK/.rc_out"')
    w('           [ "$RCST" -eq 0 ] || die "recovery check FALHOU (codigo $RCST). NAO PROSSIGA."')
    w('           log ""')
    w('           log "        recovery check OK"')
    w('           printf "O recovery check passou. Pode seguir para a gravacao? [s/N] "')
    w('           read -r R1')
    w('           case "$R1" in [sSyY]*) ;; *) die "abortado pelo operador" ;; esac ;;')
    w('    esac')
    w('else')
    w('    log "        recovery_check_linux.sh nao esta nesta pasta — pulando"')
    w('fi')
    w('# ----------------------------------------------------------------')
    w("")
    w('log "[3/6] lendo a flash e conferindo o estado ANTES..."')
    w('"$TOOL" --id "$DEV" read_flash 0 2M "$WORK/before.bin" >>"$LOG" 2>&1 \\')
    w('    || die "leitura inicial falhou"')
    w('[ "$(size "$WORK/before.bin")" = "2097152" ] || die "before.bin incompleto"')
    w("F=0")
    w("ck() {")
    w('    g=$(rsha "$WORK/before.bin" "$2" "$3")')
    w('    if [ "$g" = "$4" ]; then log "        OK   $1"')
    w('    else log "        FALHA $1"; log "          esperado $4"; log "          obtido   $g"; F=1; fi')
    w("}")
    for n, o, t, h in antes:
        w('ck "%s" %d %d %s' % (n, o, t, h))
    w('[ "$F" -eq 0 ] || die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."')
    w("")
    w('log ""')
    w('log "======================================================================"')
    w('log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."')
    w('log "   grava  : %d KiB em %d setores"' % (kib, len(arquivos)))
    if desc:
        w('log "   muda   : %s"' % desc)
    w('log "   NAO toca: bootloader, TONE, PSMP"')
    w('log "======================================================================"')
    w("""printf 'Digite EXATAMENTE  GRAVAR  para continuar: '""")
    w("read -r R")
    w('[ "$R" = "GRAVAR" ] || die "abortado pelo operador"')
    w('log "operador confirmou"')
    w('log ""')
    w("")
    w("wr() {")
    w('    log "[$1] gravando $2 a partir de $3..."')
    w("    WROTE=$((WROTE + 1))")
    w('    "$TOOL" --id "$DEV" write_flash "$2" 0 0x1000 "$3" >>"$LOG" 2>&1 \\')
    w('        || die "write_flash em $2 falhou"')
    w('    "$TOOL" --id "$DEV" read_flash "$2" 0x1000 "$WORK/sec.bin" >>"$LOG" 2>&1 \\')
    w('        || die "releitura de $2 falhou"')
    w('    s=$(size "$WORK/sec.bin"); [ "$s" = "4096" ] || die "releitura de $2 tem $s bytes"')
    w('    g=$(sha "$WORK/sec.bin")')
    w('    [ "$g" = "$4" ] || die "setor $2 NAO confere apos gravar.')
    w("    esperado $4")
    w('    obtido   $g"')
    w('    log "        OK — setor confere"')
    w("}")
    for k, (s, na, ha, no, ho, hb) in enumerate(arquivos, 1):
        w('wr "4/6 %d/%d" 0x%X %s %s' % (k, len(arquivos), s, na, ha))
    w('rm -f "$WORK/sec.bin"')
    w("")
    w('log "[5/6] lendo a flash inteira e conferindo o estado DEPOIS..."')
    w('"$TOOL" --id "$DEV" read_flash 0 2M "$WORK/after.bin" >>"$LOG" 2>&1 \\')
    w('    || die "leitura final falhou"')
    w('[ "$(size "$WORK/after.bin")" = "2097152" ] || die "after.bin incompleto"')
    w("F=0")
    w("ck2() {")
    w('    g=$(rsha "$WORK/after.bin" "$2" "$3")')
    w('    if [ "$g" = "$4" ]; then log "        OK   $1"')
    w('    else log "        FALHA $1"; log "          esperado $4"; log "          obtido   $g"; F=1; fi')
    w("}")
    for n, o, t, h in depois:
        w('ck2 "%s" %d %d %s' % (n, o, t, h))
    w("")
    w('log ""')
    w('log "======================================================================"')
    w('if [ "$F" -eq 0 ]; then')
    w('    log " [6/6] RESULTADO: %s GRAVADO E VERIFICADO"' % V.upper())
    w('    log ""')
    w('    log "   Desconecte e abra o menu principal."')
    w("else")
    w('    log " [6/6] RESULTADO: ALGUMA REGIAO NAO CONFERE"')
    w('    log ""')
    w('    log "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:"')
    for s, na, ha, no, ho, hb in arquivos:
        w('    log "     sudo $TOOL --id $DEV write_flash 0x%X 0 0x1000 %s"' % (s, no))
    w("fi")
    w('log "======================================================================"')
    w('log ""')
    w('log "  leve de volta: before.bin  after.bin  flash_%s.log"' % V)
    w('log ""')
    return "\n".join(L) + "\n"


def gerar_leiame(V, desc, arquivos, kib):
    L = []
    w = L.append
    w("OpenPod_Install — %s" % V)
    w("=" * (22 + len(V)))
    w("")
    if desc:
        w(desc)
        w("")
    w("GERADO por tools/make_install_kit.py. Nao edite a mao.")
    w("Requisitos: Linux, python3, lsusb, smtlink_dump.")
    w("")
    w("")
    w("A REGRA QUE NASCEU DE UM ERRO REAL")
    w("----------------------------------")
    w("  O write_flash grava A PARTIR DO OFFSET 0 DO ARQUIVO.")
    w("  O 2o argumento NAO e o offset dentro do arquivo.")
    w("")
    w("  ERRADO  write_flash 0xD000 0xD000 0x1000 imagem_2MiB.bin")
    w("  CERTO   write_flash 0xD000 0      0x1000 setor_D000.bin")
    w("")
    w("  Por isso: um arquivo POR SETOR, sempre 0 no 2o argumento.")
    w("  Detalhe em docs/WRITE_FLASH_SEMANTICS.md.")
    w("")
    w("")
    w("CONTEUDO")
    w("--------")
    w("  flash_%s.sh      grava (%d setores, %d KiB)" % (V, len(arquivos), kib))
    w("  diag.sh                diagnostico          (SO LEITURA)")
    w("  recovery_check_linux.sh  confere a ferramenta (SO LEITURA)")
    w("")
    w("  SETORES A GRAVAR (4096 B cada)")
    for s, na, ha, no, ho, hb in arquivos:
        w("    %-16s 0x%06X  %s" % (na, s, ha))
    w("")
    w("  SETORES DE REVERSAO -> ESTADO ANTERIOR (a base deste kit)")
    for s, na, ha, no, ho, hb in arquivos:
        w("    %-16s 0x%06X  %s" % (no, s, ho))
    w("")
    w("")
    w("COMO RODAR")
    w("----------")
    w("  sha256sum *.bin          # conferir a transferencia")
    w("")
    w("  sudo sh diag.sh /opt/smartlink_flash        # so leitura")
    w("  sudo sh flash_%s.sh /opt/smartlink_flash" % V)
    w("")
    w("ORDEM RECOMENDADA (a que se mostrou mais confiavel):")
    w("  1. plugue o aparelho, com o cartao, e espere o raio na tela")
    w("  2. espere mais ~10 segundos")
    w("  3. SO ENTAO rode o script")
    w("")
    w("O script tambem aceita a ordem inversa — se o aparelho nao estiver")
    w("conectado ele espera e avisa a hora de plugar. Mas por esse caminho")
    w("o aparelho costuma RE-ENUMERAR logo depois de detectado (observado")
    w("em 2026-09-12: Device 094 na espera, Device 098 segundos depois).")
    w("")
    w("Por que a folga importa: o aparelho precisa de alguns segundos")
    w("entre plugar e o primeiro comando, senao cai do modo card reader no")
    w("meio da operacao. Era por isso que o recovery_check_linux.sh")
    w("'funcionava melhor' — ele gastava tempo compilando antes de falar")
    w("com o aparelho. Agora essa folga e explicita.")
    w("")
    w("O script para e pede GRAVAR digitado. Ate ai, so houve leitura.")
    w("")
    w("")
    w("SE DER ERRADO")
    w("-------------")
    w("NAO DESLIGUE O APARELHO. Enquanto ele enumera, tem conserto.")
    w("")
    for s, na, ha, no, ho, hb in arquivos:
        w("  sudo /opt/smartlink_flash/smtlink_dump --id 301a:2801 \\")
        w("       write_flash 0x%X 0 0x1000 %s" % (s, no))
    w("")
    w("Isso devolve o aparelho ao estado ANTERIOR — o mesmo que ele tinha")
    w("antes deste kit, ja verificado e ja testado bootando.")
    w("")
    w("NAO use setores de fabrica para reverter um patch parcial: o resto")
    w("da flash continuaria no estado da base e a FIRM ficaria misturada,")
    w("com o CRC da tabela de particoes sem bater. Para voltar de fato ao")
    w("ORIGINAL DE FABRICA, use o procedimento completo de recuperacao.")
    return "\n".join(L) + "\n"


def bloco_aguardar(dev="301a:2801"):
    """Espera ativa pelo aparelho — a forma que funciona na pratica.

    Descoberto com o mantenedor em 2026-09-12: o aparelho precisa de um
    intervalo entre plugar e o primeiro comando para estabilizar em modo
    card reader. O recovery_check_linux.sh funcionava por acidente — ele
    gastava tempo clonando e compilando antes de falar com o aparelho.

    Aqui isso vira explicito: espera aparecer, deixa estabilizar,
    reconfirma que continua la, e so entao pergunta se pode seguir.
    """
    L = []
    w = L.append
    w("# --- espera ativa pelo aparelho ---------------------------------")
    w("# O aparelho precisa de alguns segundos entre plugar e o primeiro")
    w("# comando, senao cai do modo card reader no meio da operacao.")
    w("ESPERA=180        # segundos ate desistir")
    w("ESTABILIZA=8      # segundos de folga apos detectar")
    w("aguardar_aparelho() {")
    w('    U=$(lsusb | grep -i "%s" || true)' % dev)
    w('    if [ -n "$U" ]; then')
    w('        log "        ja conectado: $U"')
    w("    else")
    w('        log ""')
    w('        log "        >>> CONECTE O GN-438 AGORA (com o cartao inserido)."')
    w('        log "        >>> ATENCAO: o caminho MAIS CONFIAVEL e o contrario —"')
    w('        log "        >>> plugar, esperar ~10s e SO ENTAO rodar o script."')
    w('        log "        >>> Observado em 2026-09-12: conectando agora, o aparelho"')
    w('        log "        >>> costuma re-enumerar logo depois (muda o Device N)."')
    w('        log "        >>> Aguardando ate ${ESPERA}s..."')
    w("        i=0")
    w('        while [ "$i" -lt "$ESPERA" ]; do')
    w('            U=$(lsusb | grep -i "%s" || true)' % dev)
    w('            [ -n "$U" ] && break')
    w("            i=$((i + 1)); sleep 1")
    w("        done")
    w('        [ -n "$U" ] || die "aparelho nao apareceu em ${ESPERA}s."')
    w('        log "        detectado: $U"')
    w("    fi")
    w('    log "        aguardando ${ESTABILIZA}s para estabilizar..."')
    w('    sleep "$ESTABILIZA"')
    w('    V=$(lsusb | grep -i "%s" || true)' % dev)
    w('    [ -n "$V" ] || die "o aparelho caiu durante a estabilizacao. Reconecte e rode de novo."')
    w('    log "        continua conectado — OK"')
    w("}")
    w("aguardar_aparelho")
    w('log ""')
    w('printf "A tela mostra o raio e o aparelho esta estavel? [s/N] "')
    w("read -r OK")
    w('case "$OK" in [sSyY]*) ;; *) die "abortado pelo operador" ;; esac')
    w("# ----------------------------------------------------------------")
    return "\n".join(L)


def gerar_diag(V, antes, depois, orig):
    """diag.sh que conhece os tres estados possiveis deste kit."""
    L = []
    w = L.append
    w("#!/bin/sh")
    w("# diag.sh — OpenPod. GERADO por tools/make_install_kit.py.")
    w("# SOMENTE LEITURA. Nao grava nada no aparelho.")
    w("#")
    w("# USO   sudo sh diag.sh [/opt/smartlink_flash]")
    w("")
    w("set -eu")
    w("export LC_ALL=C")
    w('TOOLDIR=${1:-/opt/smartlink_flash}')
    w('TOOL="$TOOLDIR/smtlink_dump"')
    w('[ -x "$TOOL" ] || { echo "smtlink_dump nao encontrado em $TOOLDIR" >&2; exit 1; }')
    w('command -v python3 >/dev/null 2>&1 || { echo "falta python3" >&2; exit 1; }')
    w("")
    w('log() { printf "%s\\n" "$*"; }')
    w('die() { printf "\\n*** %s\\n" "$*" >&2; exit 1; }')
    w("")
    w(bloco_aguardar())
    w("")
    w('echo "=== lendo a flash inteira (SO LEITURA) ==="')
    w('"$TOOL" --id 301a:2801 read_flash 0 2M diag.bin || { echo "leitura falhou" >&2; exit 1; }')
    w('echo')
    w("")
    w("python3 - <<'PYEOF'")
    w("import hashlib")
    w("d = open('diag.bin','rb').read()")
    w('print("tamanho lido: %d bytes (esperado 2097152)" % len(d))')
    w("if len(d) != 2097152:")
    w('    print("!! tamanho errado — o relatorio abaixo nao e confiavel")')
    w("print()")
    w("# lista de (hash, rotulo) — NUNCA um dict: hashes iguais colapsariam")
    w("# e a regiao intacta seria rotulada com o ultimo estado inserido.")
    w("reg = [")
    for i in range(len(antes)):
        n, o, t, ha = antes[i]
        w("    (%r, %d, %d, [(%r,'ORIGINAL'), (%r,'ANTES esperado'), (%r,'ALVO %s')])," %
          (n, o, t, orig[i][3], ha, depois[i][3], V.upper()))
    w("]")
    w('print("%-11s %-18s %s" % ("REGIAO","SHA-256 (16)","ESTADO"))')
    w('print("-" * 60)')
    w("for n, o, t, pares in reg:")
    w("    g = hashlib.sha256(d[o:o+t]).hexdigest()")
    w("    hits = [lab for h, lab in pares if h == g]")
    w("    if not hits:            est = '??? DESCONHECIDO'")
    w("    elif len(hits) == len(pares): est = 'INTACTA (igual em todos)'")
    w("    else:                   est = ' / '.join(hits)")
    w('    print("%-11s %-18s %s" % (n, g[:16], est))')
    w("print()")
    w('print("=== cabecalho HLKJ ===")')
    w('print("  ", d[0:8].hex(), "(deve comecar com 484c4b4a)")')
    w("PYEOF")
    w("")
    w('echo')
    w('echo "=== pronto. envie TODO o texto acima. diag.bin ficou salvo aqui. ==="')
    return "\n".join(L) + "\n"

if __name__ == "__main__":
    main()
