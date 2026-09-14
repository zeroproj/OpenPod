#!/bin/sh
# flash_v002.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# os 9 icones do menu principal passam a grafite com glifo branco (recolorido pela paleta)
#
# Grava 4 setores de 4096 B (16 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_v002.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
WORK=$(pwd)/openpod_flash_v002
LOG="$WORK/flash_v002.log"
WROTE=0

mkdir -p "$WORK"; : > "$LOG"; exec 3>&1
log() { printf '%s\n' "$*" | tee -a "$LOG" >&3; }
die() {
    log ""
    log "*** $*"
    if [ "$WROTE" -ne 0 ]; then
        log "*** JA HAVIA GRAVADO $WROTE setor(es). NAO DESLIGUE O APARELHO."
        log "*** Restauracao para o ORIGINAL de fabrica:"
        log "***   sudo $TOOL --id $DEV write_flash 0xD000 0 0x1000 orig_D000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCD000 0 0x1000 orig_CD000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCE000 0 0x1000 orig_CE000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCF000 0 0x1000 orig_CF000.bin"
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
log " OpenPod — gravacao do V002   (4 setores, 16 KiB)"
log " 0x00D000 +0x1000   <- v002_D000.bin"
log " 0x0CD000 +0x1000   <- v002_CD000.bin"
log " 0x0CE000 +0x1000   <- v002_CE000.bin"
log " 0x0CF000 +0x1000   <- v002_CF000.bin"
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
ck_file v002_D000.bin b5632a2bc3ee1905f9027a3983ea78cfd767e01f810a33148e74d1fbfd0a646e
ck_file v002_CD000.bin b2448c6bf18a23b1911bdad1f5a950ad411bab82433a3efa5ead11f266b46b5c
ck_file v002_CE000.bin 27a9084db21161075d0e7ec72cb9c602534edff484d2a4776b18c90a3d8236c8
ck_file v002_CF000.bin cb87b8bb4828c63b87c36788f17d54049cf1b4c21e5757e0204a5e693fecf683
ck_file orig_D000.bin c3d16a15b7df6a8feac96169d93da82a5562ae3d17a94bf8906c2d24fc507091
ck_file orig_CD000.bin ab039386aa645f414a0580730cc4b62ca7831c9d4d8dff7b01c80f9b7be16f5f
ck_file orig_CE000.bin f46bdf8b56e3b463e8461ea5b35bfae201cafda178ac8296a5c2d8bc19cbf175
ck_file orig_CF000.bin cb87b8bb4828c63b87c36788f17d54049cf1b4c21e5757e0204a5e693fecf683

log "[2/6] procurando o aparelho..."
U=$(lsusb | grep -i "$DEV" || true)
[ -n "$U" ] || die "aparelho nao enumera como $DEV. Conecte COM O CARTAO."
log "        $U"

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
ck "ptable" 53248 64 3bb70ce0f1e5830a56a9e288cac525ae2230a7623f92da5dad449ea65ed9d2ec
ck "FIRM" 57344 1647984 96b355e3bd33702953c445e4681f77b743e3c55d59007d6550d385280bfba633
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."

log ""
log "======================================================================"
log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."
log "   grava  : 16 KiB em 4 setores"
log "   muda   : os 9 icones do menu principal passam a grafite com glifo branco (recolorido pela paleta)"
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
wr "4/6 1/4" 0xD000 v002_D000.bin b5632a2bc3ee1905f9027a3983ea78cfd767e01f810a33148e74d1fbfd0a646e
wr "4/6 2/4" 0xCD000 v002_CD000.bin b2448c6bf18a23b1911bdad1f5a950ad411bab82433a3efa5ead11f266b46b5c
wr "4/6 3/4" 0xCE000 v002_CE000.bin 27a9084db21161075d0e7ec72cb9c602534edff484d2a4776b18c90a3d8236c8
wr "4/6 4/4" 0xCF000 v002_CF000.bin cb87b8bb4828c63b87c36788f17d54049cf1b4c21e5757e0204a5e693fecf683
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
ck2 "ptable" 53248 64 5cba69808576a5a94f34016576c2c5566e004a1191ab90389b61e64c1aa0038d
ck2 "FIRM" 57344 1647984 a3e73c7d62622b311063b75a91ee9e78081d9a287f5b2072c5942f17fc9b85cf
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] RESULTADO: V002 GRAVADO E VERIFICADO"
    log ""
    log "   Desconecte e abra o menu principal."
else
    log " [6/6] RESULTADO: ALGUMA REGIAO NAO CONFERE"
    log ""
    log "   NAO desligue o aparelho. Restauracao para o ORIGINAL:"
    log "     sudo $TOOL --id $DEV write_flash 0xD000 0 0x1000 orig_D000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCD000 0 0x1000 orig_CD000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCE000 0 0x1000 orig_CE000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCF000 0 0x1000 orig_CF000.bin"
fi
log "======================================================================"
log ""
log "  leve de volta: before.bin  after.bin  flash_v002.log"
log ""
