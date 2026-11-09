#!/bin/sh
# flash_OpenPod_OpenPodReload1.0RC7DiagB3.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# OpenPod Reload 1.0 RC7 Diag B3
#
# Grava 3 setores de 4096 B (12 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_OpenPod_OpenPodReload1.0RC7DiagB3.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
VERSAO="OpenPod_OpenPodReload1.0RC7DiagB3"
# Os setores moram ao lado deste script, em setores/. Entramos la
# para os nomes de arquivo resolverem, mas os logs e os dumps ficam
# onde o usuario chamou o script -- nao enterrados no pacote.
ORIGEM="$(pwd)"
DADOS="$(cd "$(dirname "$0")" && pwd)/setores"
[ -d "$DADOS" ] || { echo "faltando: $DADOS"; exit 1; }
cd "$DADOS" || exit 1
WORK="$ORIGEM/openpod_flash_$VERSAO"
LOG="$WORK/flash_$VERSAO.log"
WROTE=0

mkdir -p "$WORK"; : > "$LOG"; exec 3>&1
log() { printf '%s\n' "$*" | tee -a "$LOG" >&3; }
die() {
    log ""
    log "*** $*"
    if [ "$WROTE" -ne 0 ]; then
        log "$(m ja_gravou) $WROTE $(m ja_gravou2)"
        log "$(m reversao)"
        log "***   (de dentro de $DADOS)"
        log "***   sudo $TOOL --id $DEV write_flash 0x146000 0 0x1000 base_146000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A4000 0 0x1000 base_1A4000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1AA000 0 0x1000 base_1AA000.bin"
        log "$(m diag)"
    else
        log "$(m nada)"
    fi
    exit 1
}
sha()  { python3 -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$1"; }
size() { python3 -c "import os,sys;print(os.path.getsize(sys.argv[1]))" "$1"; }
rsha() { python3 -c "import hashlib,sys;d=open(sys.argv[1],'rb').read()[int(sys.argv[2]):int(sys.argv[2])+int(sys.argv[3])];print(hashlib.sha256(d).hexdigest())" "$1" "$2" "$3"; }

# ------------------------------------------------------------------ idioma
# Se o install.sh ja perguntou, ele passa OPENPOD_LANG e nao perguntamos
# de novo. Rodando este script sozinho, a pergunta vem aqui.
OPENPOD_LANG=${OPENPOD_LANG:-}
if [ "$OPENPOD_LANG" != en ] && [ "$OPENPOD_LANG" != pt ]; then
    printf '\n  1) English     2) Portugues do Brasil\n  > '
    read -r _IDIOMA
    case "$_IDIOMA" in 1) OPENPOD_LANG=en ;; *) OPENPOD_LANG=pt ;; esac
    echo
fi
m() {
    if [ "$OPENPOD_LANG" = en ]; then
        case "$1" in
        so_linux) echo "This script is for Linux." ;;
        tool_falta) echo "smtlink_dump not found in" ;;
        falta) echo "missing:" ;;
        p1) echo "[1/6] checking the sector files..." ;;
        nao_achei) echo "file not found:" ;;
        tam_err) echo "wrong size, expected 4096 bytes:" ;;
        sha_err) echo "SHA-256 does not match:" ;;
        esperado) echo "expected" ;;
        obtido) echo "got     " ;;
        p2) echo "[2/6] looking for the player..." ;;
        ja_conectado) echo "already connected:" ;;
        conecte1) echo ">>> CONNECT THE GN-438 NOW (with the card inserted)." ;;
        conecte2) echo ">>> NOTE: the MOST RELIABLE way is the other way round —" ;;
        conecte3) echo ">>> plug it in, wait ~10s and ONLY THEN run the script." ;;
        conecte4) echo ">>> Seen on 2026-09-12: connecting now, the player often" ;;
        conecte5) echo ">>> re-enumerates right after (the Device N changes)." ;;
        aguardando) echo ">>> Waiting up to" ;;
        nao_apareceu) echo "the player did not show up in" ;;
        detectado) echo "detected:" ;;
        estab1) echo "waiting" ;;
        estab2) echo "to stabilize..." ;;
        caiu) echo "the player dropped while stabilizing. Reconnect and run again." ;;
        continua) echo "still connected — OK" ;;
        raio) echo "Screen shows the bolt and the player is steady? [y/N] " ;;
        abortado) echo "aborted by the operator" ;;
        p2b) echo "[2b/6] checking the tool first (recovery check)..." ;;
        rc_ask) echo "Run the recovery check now? (checks the tool, reads the flash) [Y/n] " ;;
        rc_skip) echo "SKIPPED at the operator's request" ;;
        rc_run) echo "running — may take a while (clone, 15 hashes, build, read 2 MiB)" ;;
        rc_fail) echo "recovery check FAILED. DO NOT PROCEED. code" ;;
        rc_ok) echo "recovery check OK" ;;
        rc_go) echo "Recovery check passed. Go ahead and write? [y/N] " ;;
        rc_ausente) echo "recovery_check_linux.sh is not in this folder — skipping" ;;
        p3) echo "[3/6] reading the flash, checking the state BEFORE..." ;;
        le_ini) echo "initial read failed" ;;
        incompleto) echo "is incomplete" ;;
        falha) echo "FAIL " ;;
        estado_err) echo "the player is NOT in the expected state. DO NOT PROCEED." ;;
        conf1) echo " All checks passed. The next step MODIFIES the firmware." ;;
        conf4) echo "   UNTOUCHED: bootloader, TONE, PSMP" ;;
        palavra) echo "FLASH" ;;
        digite) echo "Type EXACTLY  FLASH  to continue: " ;;
        confirmou) echo "operator confirmed" ;;
        gravando) echo "writing" ;;
        wf_falhou) echo "write_flash failed at" ;;
        rel_falhou) echo "re-read failed at" ;;
        rel_tam) echo "re-read has the wrong size at" ;;
        setor_err) echo "sector does NOT match after writing:" ;;
        setor_ok) echo "OK — sector matches" ;;
        p5) echo "[5/6] reading the whole flash, checking the state AFTER..." ;;
        le_fim) echo "final read failed" ;;
        res_ok) echo "RESULT: WRITTEN AND VERIFIED" ;;
        desconecte) echo "   Disconnect and open the main menu." ;;
        res_err) echo "RESULT: SOME REGION DOES NOT MATCH" ;;
        nao_desligue) echo "   DO NOT power off. ROLLBACK to the PREVIOUS state:" ;;
        leve) echo "  keep these: before.bin  after.bin  flash_" ;;
        ja_gravou) echo "*** ALREADY WROTE" ;;
        ja_gravou2) echo "sector(s). DO NOT POWER THE PLAYER OFF." ;;
        reversao) echo "*** ROLLBACK to the PREVIOUS state (this kit's base):" ;;
        diag) echo "*** Then run diag.sh and check before powering off." ;;
        nada) echo "*** Nothing was written." ;;
        escreve) echo "   writes   :" ;;
        muda) echo "   changes  :" ;;
        hdr) echo " OpenPod — writing" ;;
        setores) echo "sectors" ;;
        boot_na) echo " bootloader (0x0..0xD000): NOT ADDRESSED" ;;
        *) echo "$1" ;;
        esac
    else
        case "$1" in
        so_linux) echo "Este script e para Linux." ;;
        tool_falta) echo "smtlink_dump nao encontrado em" ;;
        falta) echo "faltando:" ;;
        p1) echo "[1/6] conferindo os arquivos de setor..." ;;
        nao_achei) echo "nao encontrei:" ;;
        tam_err) echo "tamanho errado, esperado 4096 bytes:" ;;
        sha_err) echo "SHA-256 nao confere:" ;;
        esperado) echo "esperado" ;;
        obtido) echo "obtido  " ;;
        p2) echo "[2/6] procurando o aparelho..." ;;
        ja_conectado) echo "ja conectado:" ;;
        conecte1) echo ">>> CONECTE O GN-438 AGORA (com o cartao inserido)." ;;
        conecte2) echo ">>> ATENCAO: o caminho MAIS CONFIAVEL e o contrario —" ;;
        conecte3) echo ">>> plugar, esperar ~10s e SO ENTAO rodar o script." ;;
        conecte4) echo ">>> Observado em 2026-09-12: conectando agora, o aparelho" ;;
        conecte5) echo ">>> costuma re-enumerar logo depois (muda o Device N)." ;;
        aguardando) echo ">>> Aguardando ate" ;;
        nao_apareceu) echo "o aparelho nao apareceu em" ;;
        detectado) echo "detectado:" ;;
        estab1) echo "aguardando" ;;
        estab2) echo "para estabilizar..." ;;
        caiu) echo "o aparelho caiu durante a estabilizacao. Reconecte e rode de novo." ;;
        continua) echo "continua conectado — OK" ;;
        raio) echo "A tela mostra o raio e o aparelho esta estavel? [s/N] " ;;
        abortado) echo "abortado pelo operador" ;;
        p2b) echo "[2b/6] verificacao previa da ferramenta (recovery check)..." ;;
        rc_ask) echo "Rodar o recovery check agora? (confere a ferramenta e le a flash) [S/n] " ;;
        rc_skip) echo "PULADO a pedido do operador" ;;
        rc_run) echo "rodando — pode demorar (clona, confere 15 hashes, compila, le 2 MiB)" ;;
        rc_fail) echo "recovery check FALHOU. NAO PROSSIGA. codigo" ;;
        rc_ok) echo "recovery check OK" ;;
        rc_go) echo "O recovery check passou. Pode seguir para a gravacao? [s/N] " ;;
        rc_ausente) echo "recovery_check_linux.sh nao esta nesta pasta — pulando" ;;
        p3) echo "[3/6] lendo a flash e conferindo o estado ANTES..." ;;
        le_ini) echo "leitura inicial falhou" ;;
        incompleto) echo "esta incompleto" ;;
        falha) echo "FALHA" ;;
        estado_err) echo "o aparelho NAO esta no estado esperado. NAO PROSSIGA." ;;
        conf1) echo " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho." ;;
        conf4) echo "   NAO toca: bootloader, TONE, PSMP" ;;
        palavra) echo "GRAVAR" ;;
        digite) echo "Digite EXATAMENTE  GRAVAR  para continuar: " ;;
        confirmou) echo "operador confirmou" ;;
        gravando) echo "gravando" ;;
        wf_falhou) echo "write_flash falhou em" ;;
        rel_falhou) echo "releitura falhou em" ;;
        rel_tam) echo "releitura com tamanho errado em" ;;
        setor_err) echo "setor NAO confere apos gravar:" ;;
        setor_ok) echo "OK — setor confere" ;;
        p5) echo "[5/6] lendo a flash inteira e conferindo o estado DEPOIS..." ;;
        le_fim) echo "leitura final falhou" ;;
        res_ok) echo "RESULTADO: GRAVADO E VERIFICADO" ;;
        desconecte) echo "   Desconecte e abra o menu principal." ;;
        res_err) echo "RESULTADO: ALGUMA REGIAO NAO CONFERE" ;;
        nao_desligue) echo "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:" ;;
        leve) echo "  leve de volta: before.bin  after.bin  flash_" ;;
        ja_gravou) echo "*** JA HAVIA GRAVADO" ;;
        ja_gravou2) echo "setor(es). NAO DESLIGUE O APARELHO." ;;
        reversao) echo "*** REVERSAO para o estado ANTERIOR (a base deste kit):" ;;
        diag) echo "*** Depois rode diag.sh e confira antes de desligar." ;;
        nada) echo "*** Nada foi gravado." ;;
        escreve) echo "   grava  :" ;;
        muda) echo "   muda   :" ;;
        hdr) echo " OpenPod — gravacao do" ;;
        setores) echo "setores" ;;
        boot_na) echo " bootloader (0x0..0xD000): NAO ENDERECADO" ;;
        *) echo "$1" ;;
        esac
    fi
}
# --------------------------------------------------------------------------

log "======================================================================"
log "$(m hdr) OPENPOD_OPENPODRELOAD1.0RC7DIAGB3   (3 $(m setores), 12 KiB)"
log " 0x146000 +0x1000   <- OpenPod_OpenPodReload1.0RC7DiagB3_146000.bin"
log " 0x1A4000 +0x1000   <- OpenPod_OpenPodReload1.0RC7DiagB3_1A4000.bin"
log " 0x1AA000 +0x1000   <- OpenPod_OpenPodReload1.0RC7DiagB3_1AA000.bin"
log "$(m boot_na)"
log "======================================================================"
log ""

[ "$(uname -s)" = "Linux" ] || die "$(m so_linux)"
[ -x "$TOOL" ] || die "$(m tool_falta) $TOOLDIR"
for c in python3 lsusb; do
    command -v "$c" >/dev/null 2>&1 || die "$(m falta) $c"
done

log "$(m p1)"
ck_file() {
    [ -f "$1" ] || die "$(m nao_achei) $1"
    s=$(size "$1"); [ "$s" = "4096" ] || die "$(m tam_err) $1 ($s)"
    g=$(sha "$1");  [ "$g" = "$2" ] || die "$(m sha_err) $1
    $(m esperado) $2
    $(m obtido) $g"
    log "        OK   $1"
}
ck_file "OpenPod_OpenPodReload1.0RC7DiagB3_146000.bin" 7420d43726c3d569a28511f0a62b19d303d551025cd5d48a62e18a1bdac259ff
ck_file "OpenPod_OpenPodReload1.0RC7DiagB3_1A4000.bin" e1d4f3cd9a3529026ab83b6b9b52aafc236a282b18ac390bade4595ae1dc72e2
ck_file "OpenPod_OpenPodReload1.0RC7DiagB3_1AA000.bin" 96b1c14f904aedbbc361b757df47afa4009e6340368dc030297654928c2cc2b3
ck_file "base_146000.bin" dae0fdb6b5cd6421109dd57bb199320d6b24fba3c7a28a3d5bcbe3c257305e3d
ck_file "base_1A4000.bin" b3045335665b4de85fb09e5398d554c5075632859f7f5f50acbf5b9fe2471fb5
ck_file "base_1AA000.bin" a31ec6accd1ca7d3a012e3fe5f3076424dc05ad5cd88f049f004e94635d79fa2

log "$(m p2)"
# --- espera ativa pelo aparelho ---------------------------------
# O aparelho precisa de alguns segundos entre plugar e o primeiro
# comando, senao cai do modo card reader no meio da operacao.
ESPERA=180        # segundos ate desistir
ESTABILIZA=8      # segundos de folga apos detectar
aguardar_aparelho() {
    U=$(lsusb | grep -i "301a:2801" || true)
    if [ -n "$U" ]; then
        log "        $(m ja_conectado) $U"
    else
        log ""
        log "        $(m conecte1)"
        log "        $(m conecte2)"
        log "        $(m conecte3)"
        log "        $(m conecte4)"
        log "        $(m conecte5)"
        log "        $(m aguardando) ${ESPERA}s..."
        i=0
        while [ "$i" -lt "$ESPERA" ]; do
            U=$(lsusb | grep -i "301a:2801" || true)
            [ -n "$U" ] && break
            i=$((i + 1)); sleep 1
        done
        [ -n "$U" ] || die "$(m nao_apareceu) ${ESPERA}s."
        log "        $(m detectado) $U"
    fi
    log "        $(m estab1) ${ESTABILIZA}s $(m estab2)"
    sleep "$ESTABILIZA"
    V=$(lsusb | grep -i "301a:2801" || true)
    [ -n "$V" ] || die "$(m caiu)"
    log "        $(m continua)"
}
aguardar_aparelho
log ""
printf '%s' "$(m raio)"
read -r OK
case "$OK" in [sSyY]*) ;; *) die "$(m abortado)" ;; esac
# ----------------------------------------------------------------

# --- verificacao previa: recovery check -------------------------
# Confere os 15 hashes do codigo-fonte do smtlink_dump no commit
# travado e recompila. Garante que a ferramenta que vai ESCREVER
# no aparelho e exatamente a versao auditada. Ver RECOVERY_CHECK.md.
log ""
log "$(m p2b)"
if [ -f ./recovery_check_linux.sh ]; then
    printf '%s' "$(m rc_ask)"
    read -r R0
    case "$R0" in
        [nN]*) log "        $(m rc_skip)" ;;
        *) log "        $(m rc_run)"
           # IMPORTANTE: nao usar  cmd | tee || die  — o || receberia o
           # status do tee, e um recovery check REPROVADO passaria batido.
           if sh ./recovery_check_linux.sh "$WORK/precheck" >"$WORK/.rc_out" 2>&1; then
               RCST=0; else RCST=$?; fi
           tee -a "$LOG" >&3 < "$WORK/.rc_out"; rm -f "$WORK/.rc_out"
           [ "$RCST" -eq 0 ] || die "$(m rc_fail) $RCST"
           log ""
           log "        $(m rc_ok)"
           printf '%s' "$(m rc_go)"
           read -r R1
           case "$R1" in [sSyY]*) ;; *) die "$(m abortado)" ;; esac ;;
    esac
else
    log "        $(m rc_ausente)"
fi
# ----------------------------------------------------------------

log "$(m p3)"
"$TOOL" --id "$DEV" read_flash 0 2M "$WORK/before.bin" >>"$LOG" 2>&1 \
    || die "$(m le_ini)"
[ "$(size "$WORK/before.bin")" = "2097152" ] || die "before.bin $(m incompleto)"
F=0
ck() {
    g=$(rsha "$WORK/before.bin" "$2" "$3")
    if [ "$g" = "$4" ]; then log "        OK   $1"
    else log "        $(m falha) $1"; log "          $(m esperado) $4"; log "          $(m obtido) $g"; F=1; fi
}
ck "bootloader" 0 51532 861184003923634be0f2ae9883456035b40d1ea72f97682890238edfae3acb31
ck "ptable" 53248 64 9f93d4435e7cb819b2dad2f38edf91fb0a0af44654c4d9fcd3df174bf3380a2d
ck "FIRM" 57344 1647984 1ab0a73540682bea0ed5f95dd370b7a926f1740a1081a746cbedebf2a318f765
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "$(m estado_err)"

log ""
log "======================================================================"
log "$(m conf1)"
log "$(m escreve) 12 KiB / 3 $(m setores)"
log "$(m muda) OpenPod Reload 1.0 RC7 Diag B3"
log "$(m conf4)"
log "======================================================================"
printf '%s' "$(m digite)"
read -r R
[ "$R" = "$(m palavra)" ] || die "$(m abortado)"
log "$(m confirmou)"
log ""

wr() {
    log "[$1] $(m gravando) $2 <- $3..."
    WROTE=$((WROTE + 1))
    "$TOOL" --id "$DEV" write_flash "$2" 0 0x1000 "$3" >>"$LOG" 2>&1 \
        || die "$(m wf_falhou) $2"
    "$TOOL" --id "$DEV" read_flash "$2" 0x1000 "$WORK/sec.bin" >>"$LOG" 2>&1 \
        || die "$(m rel_falhou) $2"
    s=$(size "$WORK/sec.bin"); [ "$s" = "4096" ] || die "$(m rel_tam) $2 ($s)"
    g=$(sha "$WORK/sec.bin")
    [ "$g" = "$4" ] || die "$(m setor_err) $2
    $(m esperado) $4
    $(m obtido) $g"
    log "        $(m setor_ok)"
}
wr "4/6 1/3" 0x146000 "OpenPod_OpenPodReload1.0RC7DiagB3_146000.bin" 7420d43726c3d569a28511f0a62b19d303d551025cd5d48a62e18a1bdac259ff
wr "4/6 2/3" 0x1A4000 "OpenPod_OpenPodReload1.0RC7DiagB3_1A4000.bin" e1d4f3cd9a3529026ab83b6b9b52aafc236a282b18ac390bade4595ae1dc72e2
wr "4/6 3/3" 0x1AA000 "OpenPod_OpenPodReload1.0RC7DiagB3_1AA000.bin" 96b1c14f904aedbbc361b757df47afa4009e6340368dc030297654928c2cc2b3
rm -f "$WORK/sec.bin"

log "$(m p5)"
"$TOOL" --id "$DEV" read_flash 0 2M "$WORK/after.bin" >>"$LOG" 2>&1 \
    || die "$(m le_fim)"
[ "$(size "$WORK/after.bin")" = "2097152" ] || die "after.bin $(m incompleto)"
F=0
ck2() {
    g=$(rsha "$WORK/after.bin" "$2" "$3")
    if [ "$g" = "$4" ]; then log "        OK   $1"
    else log "        $(m falha) $1"; log "          $(m esperado) $4"; log "          $(m obtido) $g"; F=1; fi
}
ck2 "bootloader" 0 51532 861184003923634be0f2ae9883456035b40d1ea72f97682890238edfae3acb31
ck2 "ptable" 53248 64 9f93d4435e7cb819b2dad2f38edf91fb0a0af44654c4d9fcd3df174bf3380a2d
ck2 "FIRM" 57344 1647984 8260a78cae15236367b894055908c08fc321a726ddc6b9dffdcf1ac9d78f14e9
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] OPENPOD_OPENPODRELOAD1.0RC7DIAGB3 — $(m res_ok)"
    log ""
    log "$(m desconecte)"
else
    log " [6/6] $(m res_err)"
    log ""
    log "$(m nao_desligue)"
    log "     sudo $TOOL --id $DEV write_flash 0x146000 0 0x1000 base_146000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A4000 0 0x1000 base_1A4000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1AA000 0 0x1000 base_1AA000.bin"
fi
log "======================================================================"
log ""
log "$(m leve)$VERSAO.log"
log ""
