#!/bin/sh
# flash_OpenPod_OpenPodReload1.0RC7DiagB5b.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# OpenPod OpenPod Reload 1.0 RC7 Diag B5b
#
# Grava 5 setores de 4096 B (20 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_OpenPod_OpenPodReload1.0RC7DiagB5b.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
VERSAO="OpenPod_OpenPodReload1.0RC7DiagB5b"
WORK="$(pwd)/openpod_flash_$VERSAO"
LOG="$WORK/flash_$VERSAO.log"
WROTE=0

mkdir -p "$WORK"; : > "$LOG"; exec 3>&1
log() { printf '%s\n' "$*" | tee -a "$LOG" >&3; }
die() {
    log ""
    log "*** $*"
    if [ "$WROTE" -ne 0 ]; then
        log "*** JA HAVIA GRAVADO $WROTE setor(es). NAO DESLIGUE O APARELHO."
        log "*** REVERSAO para o estado ANTERIOR (a base deste kit):"
        log "***   sudo $TOOL --id $DEV write_flash 0xFF000 0 0x1000 base_FF000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x132000 0 0x1000 base_132000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A4000 0 0x1000 base_1A4000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1AA000 0 0x1000 base_1AA000.bin"
        log "*** Depois rode diag.sh e confira antes de desligar."
    else
        log "*** Nada foi gravado."
    fi
    exit 1
}
sha()  { python3 -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$1"; }
size() { python3 -c "import os,sys;print(os.path.getsize(sys.argv[1]))" "$1"; }
rsha() { python3 -c "import hashlib,sys;d=open(sys.argv[1],'rb').read()[int(sys.argv[2]):int(sys.argv[2])+int(sys.argv[3])];print(hashlib.sha256(d).hexdigest())" "$1" "$2" "$3"; }

log "======================================================================"
log " OpenPod — gravacao do OPENPOD_OPENPODRELOAD1.0RC7DIAGB5B   (5 setores, 20 KiB)"
log " 0x0FF000 +0x1000   <- OpenPod_OpenPodReload1.0RC7DiagB5b_FF000.bin"
log " 0x10A000 +0x1000   <- OpenPod_OpenPodReload1.0RC7DiagB5b_10A000.bin"
log " 0x132000 +0x1000   <- OpenPod_OpenPodReload1.0RC7DiagB5b_132000.bin"
log " 0x1A4000 +0x1000   <- OpenPod_OpenPodReload1.0RC7DiagB5b_1A4000.bin"
log " 0x1AA000 +0x1000   <- OpenPod_OpenPodReload1.0RC7DiagB5b_1AA000.bin"
log " bootloader (0x0..0xD000): NAO ENDERECADO"
log "======================================================================"
log ""

[ "$(uname -s)" = "Linux" ] || die "Este script e para Linux."
[ -x "$TOOL" ] || die "smtlink_dump nao encontrado em $TOOLDIR"
for c in python3 lsusb; do
    command -v "$c" >/dev/null 2>&1 || die "faltando: $c"
done

log "[1/6] conferindo os arquivos de setor..."
ck_file() {
    [ -f "$1" ] || die "nao encontrei $1"
    s=$(size "$1"); [ "$s" = "4096" ] || die "$1 tem $s bytes, esperado 4096"
    g=$(sha "$1");  [ "$g" = "$2" ] || die "SHA-256 de $1 nao confere.
    esperado $2
    obtido   $g"
    log "        OK   $1"
}
ck_file "OpenPod_OpenPodReload1.0RC7DiagB5b_FF000.bin" 43a5058b2539d0b3752f2390a485e3fa6f8c2fb700cdca71c1839fde9a5ab4a2
ck_file "OpenPod_OpenPodReload1.0RC7DiagB5b_10A000.bin" 8c35d232644fbcec0e57519558b61e1d3f0a7b0d269bbadde0c4eae6ba5316d3
ck_file "OpenPod_OpenPodReload1.0RC7DiagB5b_132000.bin" eb7bd5dd2bf1760211137e8264d0f784ce6b21483b08bbb9b99a102f75baf7ae
ck_file "OpenPod_OpenPodReload1.0RC7DiagB5b_1A4000.bin" 3c68bac928dce183e238a01d7421d328c0f3f6a24a5a9189781cad4e834d3016
ck_file "OpenPod_OpenPodReload1.0RC7DiagB5b_1AA000.bin" 30d08f10084f4acdf42adf1bcdfc6ef70cfb4054d15d8b2fc60c78d944e1784a
ck_file "base_FF000.bin" 2b44bef648c5f8fcc08072cc529a8002cf37b11c3ce5ce8e88e1b2a24ed6d820
ck_file "base_10A000.bin" ad962e28861a9a9914ef70e26cfc50283fa51daee636051a4907db930839dd6a
ck_file "base_132000.bin" 8e53b1c5dd6b993d9052c3ee04b4a4c1fa543f5676d507c7ea7b8ffa63977942
ck_file "base_1A4000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6
ck_file "base_1AA000.bin" f40bc113d430a60cab21a0dc82e159566e2598442c3cbc74788912749b7be0ce

log "[2/6] procurando o aparelho..."
# --- espera ativa pelo aparelho ---------------------------------
# O aparelho precisa de alguns segundos entre plugar e o primeiro
# comando, senao cai do modo card reader no meio da operacao.
ESPERA=180        # segundos ate desistir
ESTABILIZA=8      # segundos de folga apos detectar
aguardar_aparelho() {
    U=$(lsusb | grep -i "301a:2801" || true)
    if [ -n "$U" ]; then
        log "        ja conectado: $U"
    else
        log ""
        log "        >>> CONECTE O GN-438 AGORA (com o cartao inserido)."
        log "        >>> ATENCAO: o caminho MAIS CONFIAVEL e o contrario —"
        log "        >>> plugar, esperar ~10s e SO ENTAO rodar o script."
        log "        >>> Observado em 2026-09-12: conectando agora, o aparelho"
        log "        >>> costuma re-enumerar logo depois (muda o Device N)."
        log "        >>> Aguardando ate ${ESPERA}s..."
        i=0
        while [ "$i" -lt "$ESPERA" ]; do
            U=$(lsusb | grep -i "301a:2801" || true)
            [ -n "$U" ] && break
            i=$((i + 1)); sleep 1
        done
        [ -n "$U" ] || die "aparelho nao apareceu em ${ESPERA}s."
        log "        detectado: $U"
    fi
    log "        aguardando ${ESTABILIZA}s para estabilizar..."
    sleep "$ESTABILIZA"
    V=$(lsusb | grep -i "301a:2801" || true)
    [ -n "$V" ] || die "o aparelho caiu durante a estabilizacao. Reconecte e rode de novo."
    log "        continua conectado — OK"
}
aguardar_aparelho
log ""
printf "A tela mostra o raio e o aparelho esta estavel? [s/N] "
read -r OK
case "$OK" in [sSyY]*) ;; *) die "abortado pelo operador" ;; esac
# ----------------------------------------------------------------

# --- verificacao previa: recovery check -------------------------
# Confere os 15 hashes do codigo-fonte do smtlink_dump no commit
# travado e recompila. Garante que a ferramenta que vai ESCREVER
# no aparelho e exatamente a versao auditada. Ver RECOVERY_CHECK.md.
log ""
log "[2b/6] verificacao previa da ferramenta (recovery check)..."
if [ -f ./recovery_check_linux.sh ]; then
    printf "Rodar o recovery check agora? (confere a ferramenta e le a flash) [S/n] "
    read -r R0
    case "$R0" in
        [nN]*) log "        PULADO a pedido do operador" ;;
        *) log "        rodando — pode demorar (clona, confere 15 hashes, compila, le 2 MiB)"
           # IMPORTANTE: nao usar  cmd | tee || die  — o || receberia o
           # status do tee, e um recovery check REPROVADO passaria batido.
           if sh ./recovery_check_linux.sh "$WORK/precheck" >"$WORK/.rc_out" 2>&1; then
               RCST=0; else RCST=$?; fi
           tee -a "$LOG" >&3 < "$WORK/.rc_out"; rm -f "$WORK/.rc_out"
           [ "$RCST" -eq 0 ] || die "recovery check FALHOU (codigo $RCST). NAO PROSSIGA."
           log ""
           log "        recovery check OK"
           printf "O recovery check passou. Pode seguir para a gravacao? [s/N] "
           read -r R1
           case "$R1" in [sSyY]*) ;; *) die "abortado pelo operador" ;; esac ;;
    esac
else
    log "        recovery_check_linux.sh nao esta nesta pasta — pulando"
fi
# ----------------------------------------------------------------

log "[3/6] lendo a flash e conferindo o estado ANTES..."
"$TOOL" --id "$DEV" read_flash 0 2M "$WORK/before.bin" >>"$LOG" 2>&1 \
    || die "leitura inicial falhou"
[ "$(size "$WORK/before.bin")" = "2097152" ] || die "before.bin incompleto"
F=0
ck() {
    g=$(rsha "$WORK/before.bin" "$2" "$3")
    if [ "$g" = "$4" ]; then log "        OK   $1"
    else log "        FALHA $1"; log "          esperado $4"; log "          obtido   $g"; F=1; fi
}
ck "bootloader" 0 51532 861184003923634be0f2ae9883456035b40d1ea72f97682890238edfae3acb31
ck "ptable" 53248 64 9f93d4435e7cb819b2dad2f38edf91fb0a0af44654c4d9fcd3df174bf3380a2d
ck "FIRM" 57344 1647984 cd26e3a3bc999a9b308166d52edc05cf395e9fc4c4314011539e7fde4546827e
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."

log ""
log "======================================================================"
log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."
log "   grava  : 20 KiB em 5 setores"
log "   muda   : OpenPod OpenPod Reload 1.0 RC7 Diag B5b"
log "   NAO toca: bootloader, TONE, PSMP"
log "======================================================================"
printf 'Digite EXATAMENTE  GRAVAR  para continuar: '
read -r R
[ "$R" = "GRAVAR" ] || die "abortado pelo operador"
log "operador confirmou"
log ""

wr() {
    log "[$1] gravando $2 a partir de $3..."
    WROTE=$((WROTE + 1))
    "$TOOL" --id "$DEV" write_flash "$2" 0 0x1000 "$3" >>"$LOG" 2>&1 \
        || die "write_flash em $2 falhou"
    "$TOOL" --id "$DEV" read_flash "$2" 0x1000 "$WORK/sec.bin" >>"$LOG" 2>&1 \
        || die "releitura de $2 falhou"
    s=$(size "$WORK/sec.bin"); [ "$s" = "4096" ] || die "releitura de $2 tem $s bytes"
    g=$(sha "$WORK/sec.bin")
    [ "$g" = "$4" ] || die "setor $2 NAO confere apos gravar.
    esperado $4
    obtido   $g"
    log "        OK — setor confere"
}
wr "4/6 1/5" 0xFF000 "OpenPod_OpenPodReload1.0RC7DiagB5b_FF000.bin" 43a5058b2539d0b3752f2390a485e3fa6f8c2fb700cdca71c1839fde9a5ab4a2
wr "4/6 2/5" 0x10A000 "OpenPod_OpenPodReload1.0RC7DiagB5b_10A000.bin" 8c35d232644fbcec0e57519558b61e1d3f0a7b0d269bbadde0c4eae6ba5316d3
wr "4/6 3/5" 0x132000 "OpenPod_OpenPodReload1.0RC7DiagB5b_132000.bin" eb7bd5dd2bf1760211137e8264d0f784ce6b21483b08bbb9b99a102f75baf7ae
wr "4/6 4/5" 0x1A4000 "OpenPod_OpenPodReload1.0RC7DiagB5b_1A4000.bin" 3c68bac928dce183e238a01d7421d328c0f3f6a24a5a9189781cad4e834d3016
wr "4/6 5/5" 0x1AA000 "OpenPod_OpenPodReload1.0RC7DiagB5b_1AA000.bin" 30d08f10084f4acdf42adf1bcdfc6ef70cfb4054d15d8b2fc60c78d944e1784a
rm -f "$WORK/sec.bin"

log "[5/6] lendo a flash inteira e conferindo o estado DEPOIS..."
"$TOOL" --id "$DEV" read_flash 0 2M "$WORK/after.bin" >>"$LOG" 2>&1 \
    || die "leitura final falhou"
[ "$(size "$WORK/after.bin")" = "2097152" ] || die "after.bin incompleto"
F=0
ck2() {
    g=$(rsha "$WORK/after.bin" "$2" "$3")
    if [ "$g" = "$4" ]; then log "        OK   $1"
    else log "        FALHA $1"; log "          esperado $4"; log "          obtido   $g"; F=1; fi
}
ck2 "bootloader" 0 51532 861184003923634be0f2ae9883456035b40d1ea72f97682890238edfae3acb31
ck2 "ptable" 53248 64 9f93d4435e7cb819b2dad2f38edf91fb0a0af44654c4d9fcd3df174bf3380a2d
ck2 "FIRM" 57344 1647984 f47ea9efb677132a64daa4103a2c97c739f1de035d420e76b8e20595a8297368
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] RESULTADO: OPENPOD_OPENPODRELOAD1.0RC7DIAGB5B GRAVADO E VERIFICADO"
    log ""
    log "   Desconecte e abra o menu principal."
else
    log " [6/6] RESULTADO: ALGUMA REGIAO NAO CONFERE"
    log ""
    log "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:"
    log "     sudo $TOOL --id $DEV write_flash 0xFF000 0 0x1000 base_FF000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x132000 0 0x1000 base_132000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A4000 0 0x1000 base_1A4000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1AA000 0 0x1000 base_1AA000.bin"
fi
log "======================================================================"
log ""
log "  leve de volta: before.bin  after.bin  flash_$VERSAO.log"
log ""
