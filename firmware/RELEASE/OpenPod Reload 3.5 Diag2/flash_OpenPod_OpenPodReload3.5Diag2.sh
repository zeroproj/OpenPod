#!/bin/sh
# flash_OpenPod_OpenPodReload3.5Diag2.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# OpenPod OpenPod Reload 3.5 Diag2
#
# Grava 5 setores de 4096 B (20 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_OpenPod_OpenPodReload3.5Diag2.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
VERSAO="OpenPod_OpenPodReload3.5Diag2"
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
        log "***   sudo $TOOL --id $DEV write_flash 0x1A4000 0 0x1000 base_1A4000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1AB000 0 0x1000 base_1AB000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1AC000 0 0x1000 base_1AC000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1AD000 0 0x1000 base_1AD000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1AE000 0 0x1000 base_1AE000.bin"
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
log " OpenPod — gravacao do OPENPOD_OPENPODRELOAD3.5DIAG2   (5 setores, 20 KiB)"
log " 0x1A4000 +0x1000   <- OpenPod_OpenPodReload3.5Diag2_1A4000.bin"
log " 0x1AB000 +0x1000   <- OpenPod_OpenPodReload3.5Diag2_1AB000.bin"
log " 0x1AC000 +0x1000   <- OpenPod_OpenPodReload3.5Diag2_1AC000.bin"
log " 0x1AD000 +0x1000   <- OpenPod_OpenPodReload3.5Diag2_1AD000.bin"
log " 0x1AE000 +0x1000   <- OpenPod_OpenPodReload3.5Diag2_1AE000.bin"
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
ck_file "OpenPod_OpenPodReload3.5Diag2_1A4000.bin" 14bf213f9efdea1e98ce504168b03fe6788f1f5737d47f8ef6c2bcedf5fff32a
ck_file "OpenPod_OpenPodReload3.5Diag2_1AB000.bin" e209436ef4c8923d5e45bc183624b305104e5bf233c22954f7e1207d117144f3
ck_file "OpenPod_OpenPodReload3.5Diag2_1AC000.bin" 037426e5f8b6e4027aeb571d00c0d09e378cd3bc5d8202963391d8dde3555af6
ck_file "OpenPod_OpenPodReload3.5Diag2_1AD000.bin" 3c9344424cc1701b1d9f9179cf6074cf7f61e313ee68369a32d3451ff81f5dd8
ck_file "OpenPod_OpenPodReload3.5Diag2_1AE000.bin" bc006461a964e4576c41b1a5b7a62c765d4ef10086715909f5a72bcb68a0263f
ck_file "base_1A4000.bin" 460fd73af7e960800e95e4e141fd98fe6842b70b6f39ae510c56e259e12218f5
ck_file "base_1AB000.bin" c0bc8eca950a81e2fc4fe16d37df4f0822c957221997b0f7ee6bfac885d4e46d
ck_file "base_1AC000.bin" 3022093ebbc1a0f3eadb2fab98e8bbe74d2af2124bb442017d77852c160059c7
ck_file "base_1AD000.bin" e2f322ed2e84d951b5bcd8f6f837d2a4f84b66663002387276d1ba92b52c9bcd
ck_file "base_1AE000.bin" d2630e02f4e1e6f8ec52372668cdbaf6747700e38483a9894ce3970dfe74c479

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
ck "FIRM" 57344 1647984 69fc1abafd5d951c4a13b7d3b47e46ad3c8160c95b8a0845ffa6bf7fd6ae7ddd
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."

log ""
log "======================================================================"
log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."
log "   grava  : 20 KiB em 5 setores"
log "   muda   : OpenPod OpenPod Reload 3.5 Diag2"
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
wr "4/6 1/5" 0x1A4000 "OpenPod_OpenPodReload3.5Diag2_1A4000.bin" 14bf213f9efdea1e98ce504168b03fe6788f1f5737d47f8ef6c2bcedf5fff32a
wr "4/6 2/5" 0x1AB000 "OpenPod_OpenPodReload3.5Diag2_1AB000.bin" e209436ef4c8923d5e45bc183624b305104e5bf233c22954f7e1207d117144f3
wr "4/6 3/5" 0x1AC000 "OpenPod_OpenPodReload3.5Diag2_1AC000.bin" 037426e5f8b6e4027aeb571d00c0d09e378cd3bc5d8202963391d8dde3555af6
wr "4/6 4/5" 0x1AD000 "OpenPod_OpenPodReload3.5Diag2_1AD000.bin" 3c9344424cc1701b1d9f9179cf6074cf7f61e313ee68369a32d3451ff81f5dd8
wr "4/6 5/5" 0x1AE000 "OpenPod_OpenPodReload3.5Diag2_1AE000.bin" bc006461a964e4576c41b1a5b7a62c765d4ef10086715909f5a72bcb68a0263f
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
ck2 "FIRM" 57344 1647984 69fc1abafd5d951c4a13b7d3b47e46ad3c8160c95b8a0845ffa6bf7fd6ae7ddd
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] RESULTADO: OPENPOD_OPENPODRELOAD3.5DIAG2 GRAVADO E VERIFICADO"
    log ""
    log "   Desconecte e abra o menu principal."
else
    log " [6/6] RESULTADO: ALGUMA REGIAO NAO CONFERE"
    log ""
    log "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:"
    log "     sudo $TOOL --id $DEV write_flash 0x1A4000 0 0x1000 base_1A4000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1AB000 0 0x1000 base_1AB000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1AC000 0 0x1000 base_1AC000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1AD000 0 0x1000 base_1AD000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1AE000 0 0x1000 base_1AE000.bin"
fi
log "======================================================================"
log ""
log "  leve de volta: before.bin  after.bin  flash_$VERSAO.log"
log ""
