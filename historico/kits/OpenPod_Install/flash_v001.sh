#!/bin/sh
# flash_v001.sh — OpenPod: grava o patch V001 no GN-438.   [v2]
#
# ############################################################
# #  ESTA E A PRIMEIRA MODIFICACAO REAL DO FIRMWARE.         #
# ############################################################
#
# MUDANCA CRITICA NA v2 — LEIA
#   A v1 chamava:   write_flash 0xD000 0xD000 0x1000 imagem_2MiB.bin
#   supondo que o 2o argumento fosse o offset DENTRO DO ARQUIVO.
#
#   NAO E. Comprovado em hardware em 2026-09-12: o write_flash grava
#   a partir do OFFSET 0 do arquivo. A v1 gravou os 4096 bytes iniciais
#   do .bin (cabecalho HLKJ + inicio do bootloader) em 0xD000,
#   corrompendo a tabela de particoes. Foi restaurado.
#
#   A v2 grava a partir de ARQUIVOS POR SETOR, em que o offset 0 ja e
#   o conteudo desejado, e passa 0 como 2o argumento — correto tanto
#   se o argumento for honrado quanto se for ignorado.
#
# O QUE FAZ
#   Grava os 3 setores de 4 KiB que diferem entre o original e o V001:
#
#     0x00D000 (1 setor)   tabela de particoes — 2 bytes (CRC da FIRM)
#     0x0CE000 (1 setor)   pixels do icone Musica
#     0x0CF000 (1 setor)   pixels do icone Musica — 716 bytes no total
#
#   12 KiB no total. O bootloader (0x000000..0x00D000) NAO e
#   endereçado. Os enderecos sao FIXOS; nao ha parametro que os altere.
#
# SEGURANCA
#   - confere o SHA-256 e o TAMANHO de cada arquivo de setor
#   - le a flash inteira e exige o estado ESPERADO ANTES
#   - exige confirmacao digitada
#   - grava setor a setor, conferindo cada um logo apos gravar
#   - rele a flash inteira e confere o estado DEPOIS
#   - se falhar depois de gravar, imprime a restauracao CORRETA
#
#   Nao usa tail/head: o coreutils em Rust de algumas distros aborta
#   com "Broken pipe" nesses pipelines. Tudo por python3.
#
# USO
#   sudo sh flash_v001.sh [/opt/smartlink_flash]
#
#   Os arquivos de setor precisam estar no diretorio atual:
#     v001_D000.bin  v001_CE000.bin  v001_CF000.bin
#     orig_D000.bin  orig_CE000.bin  orig_CF000.bin
#
# SAIDA
#   before.bin  after.bin  flash_v001.log

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801

WORK=$(pwd)/openpod_flash_v001
LOG="$WORK/flash_v001.log"
WROTE=0

mkdir -p "$WORK"; : > "$LOG"; exec 3>&1
log() { printf '%s\n' "$*" | tee -a "$LOG" >&3; }
die() {
    log ""
    log "*** $*"
    if [ "$WROTE" -ne 0 ]; then
        log "*** JA HAVIA GRAVADO $WROTE setor(es). NAO DESLIGUE O APARELHO."
        log "*** Restauracao (na ordem):"
        log "***   sudo $TOOL --id $DEV write_flash 0xD000  0 0x1000 orig_D000.bin"
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
log " OpenPod — gravacao do V001   (3 setores, 12 KiB)   [v2]"
log " 0x00D000 +0x1000   tabela de particoes     <- v001_D000.bin"
log " 0x0CE000 +0x1000   pixels do icone Musica  <- v001_CE000.bin"
log " 0x0CF000 +0x1000   pixels do icone Musica  <- v001_CF000.bin"
log " bootloader (0x0..0xD000): NAO ENDERECADO"
log "======================================================================"
log ""

[ "$(uname -s)" = "Linux" ] || die "Este script e para Linux."
[ -x "$TOOL" ] || die "smtlink_dump nao encontrado em $TOOLDIR"
for c in python3 lsusb; do
    command -v "$c" >/dev/null 2>&1 || die "faltando: $c"
done

# ---------- 1. arquivos de setor ----------
log "[1/7] conferindo os arquivos de setor..."
ck_file() {
    [ -f "$1" ] || die "nao encontrei $1"
    s=$(size "$1"); [ "$s" = "$2" ] || die "$1 tem $s bytes, esperado $2"
    g=$(sha "$1");  [ "$g" = "$3" ] || die "SHA-256 de $1 nao confere.
    esperado $3
    obtido   $g"
    log "        OK   $1  ($2 bytes)"
}
ck_file v001_D000.bin   4096 c2124ab4b1c6eebd4b13a3156e9b1482f79385aa855276929ff2ef79dd6a9686
ck_file v001_CE000.bin  4096 7121e4487603daa536e8ed6eaf1928a9e3dca49662fe815beaf6c1e1858b288f
ck_file v001_CF000.bin  4096 c77537695339f7b0aa27d29435cdc0f90d8f93b7856a027dddf5cfc0e6f10492
ck_file orig_D000.bin   4096 c3d16a15b7df6a8feac96169d93da82a5562ae3d17a94bf8906c2d24fc507091
ck_file orig_CE000.bin  4096 f46bdf8b56e3b463e8461ea5b35bfae201cafda178ac8296a5c2d8bc19cbf175
ck_file orig_CF000.bin  4096 cb87b8bb4828c63b87c36788f17d54049cf1b4c21e5757e0204a5e693fecf683

# ---------- 2. aparelho ----------
log "[2/7] procurando o aparelho..."
U=$(lsusb | grep -i "$DEV" || true)
[ -n "$U" ] || die "aparelho nao enumera como $DEV. Conecte COM O CARTAO."
log "        $U"

# ---------- 3. estado ANTES ----------
log "[3/7] lendo a flash e conferindo o estado ANTES..."
"$TOOL" --id "$DEV" read_flash 0 2M "$WORK/before.bin" >>"$LOG" 2>&1 \
    || die "leitura inicial falhou"
[ "$(size "$WORK/before.bin")" = "2097152" ] || die "before.bin incompleto"
F=0
ck() {
    g=$(rsha "$WORK/before.bin" "$2" "$3")
    if [ "$g" = "$4" ]; then log "        OK   $1"
    else log "        FALHA $1"; log "          esperado $4"; log "          obtido   $g"; F=1; fi
}
ck "bootloader" 0       51532   861184003923634be0f2ae9883456035b40d1ea72f97682890238edfae3acb31
ck "ptable"     53248   64      9f93d4435e7cb819b2dad2f38edf91fb0a0af44654c4d9fcd3df174bf3380a2d
ck "FIRM"       57344   1647984 e2a7b86339030b94268dac7d562a167613a3e769c866790353b4921cad85dbdc
ck "TONE"       1708032 8248    7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."

# ---------- 4. confirmacao ----------
log ""
log "======================================================================"
log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."
log "   grava  : 12 KiB em 3 setores"
log "   muda   : o icone Musica do menu principal (prata -> azul)"
log "   NAO toca: bootloader, TONE, PSMP, resto da FIRM"
log "======================================================================"
printf 'Digite EXATAMENTE  GRAVAR  para continuar: '
read -r R
[ "$R" = "GRAVAR" ] || die "abortado pelo operador"
log "operador confirmou"
log ""

# ---------- 5. gravar setor a setor ----------
# wr <etapa> <endereco> <tamanho> <arquivo-do-setor> <sha-esperado>
wr() {
    log "[$1] gravando $2 (+$3) a partir de $4..."
    # marcar ANTES: se o write_flash falhar no meio, o die() precisa
    # dizer que ja houve escrita, nao "nada foi gravado".
    WROTE=$((WROTE + 1))
    # 2o argumento = 0: offset 0 do arquivo do setor. Correto tanto se
    # o argumento for honrado quanto se for ignorado.
    "$TOOL" --id "$DEV" write_flash "$2" 0 "$3" "$4" >>"$LOG" 2>&1 \
        || die "write_flash em $2 falhou"
    "$TOOL" --id "$DEV" read_flash "$2" "$3" "$WORK/sec.bin" >>"$LOG" 2>&1 \
        || die "releitura de $2 falhou"
    s=$(size "$WORK/sec.bin")
    [ "$s" = "$(size "$4")" ] || die "releitura de $2 tem $s bytes, esperado $(size "$4")"
    g=$(sha "$WORK/sec.bin")
    [ "$g" = "$5" ] || die "setor $2 NAO confere apos gravar.
    esperado $5
    obtido   $g"
    log "        OK — setor confere"
}
# TODAS as gravacoes sao de 4096 bytes — exatamente a forma ja provada
# em hardware em 2026-09-12 (a restauracao da ptable). Nenhum tamanho
# novo e exercitado.
wr "4/7" 0xD000  0x1000 v001_D000.bin  c2124ab4b1c6eebd4b13a3156e9b1482f79385aa855276929ff2ef79dd6a9686
wr "5/7" 0xCE000 0x1000 v001_CE000.bin 7121e4487603daa536e8ed6eaf1928a9e3dca49662fe815beaf6c1e1858b288f
wr "6/7" 0xCF000 0x1000 v001_CF000.bin c77537695339f7b0aa27d29435cdc0f90d8f93b7856a027dddf5cfc0e6f10492
rm -f "$WORK/sec.bin"

# ---------- 6. estado DEPOIS ----------
log "[7/7] lendo a flash inteira e conferindo o estado DEPOIS..."
"$TOOL" --id "$DEV" read_flash 0 2M "$WORK/after.bin" >>"$LOG" 2>&1 \
    || die "leitura final falhou"
[ "$(size "$WORK/after.bin")" = "2097152" ] || die "after.bin incompleto"
F=0
ck2() {
    g=$(rsha "$WORK/after.bin" "$2" "$3")
    if [ "$g" = "$4" ]; then log "        OK   $1"
    else log "        FALHA $1"; log "          esperado $4"; log "          obtido   $g"; F=1; fi
}
ck2 "bootloader (deve estar INTACTO)" 0       51532   861184003923634be0f2ae9883456035b40d1ea72f97682890238edfae3acb31
ck2 "ptable     (deve ter MUDADO)"    53248   64      3bb70ce0f1e5830a56a9e288cac525ae2230a7623f92da5dad449ea65ed9d2ec
ck2 "FIRM       (deve ter MUDADO)"    57344   1647984 96b355e3bd33702953c445e4681f77b743e3c55d59007d6550d385280bfba633
ck2 "TONE       (deve estar INTACTA)" 1708032 8248    7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " RESULTADO: V001 GRAVADO E VERIFICADO"
    log ""
    log "   Desconecte e abra o menu principal."
    log "   O icone de Musica (disco, canto superior esquerdo) deve estar AZUL."
else
    log " RESULTADO: ALGUMA REGIAO NAO CONFERE"
    log ""
    log "   NAO desligue o aparelho ainda."
    log "   Restauracao:"
    log "     sudo $TOOL --id $DEV write_flash 0xD000  0 0x1000 orig_D000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCE000 0 0x1000 orig_CE000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCF000 0 0x1000 orig_CF000.bin"
fi
log "======================================================================"
log ""
log "  leve de volta: before.bin  after.bin  flash_v001.log"
log ""
