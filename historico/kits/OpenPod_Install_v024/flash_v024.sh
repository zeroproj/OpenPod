#!/bin/sh
# flash_v024.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# BISSECCAO 2: V021 + somente os 7 bytes de limite de indice. Home volta a 9 itens com rotulos originais.
#
# Grava 8 setores de 4096 B (32 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_v024.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
WORK=$(pwd)/openpod_flash_v024
LOG="$WORK/flash_v024.log"
WROTE=0

mkdir -p "$WORK"; : > "$LOG"; exec 3>&1
log() { printf '%s\n' "$*" | tee -a "$LOG" >&3; }
die() {
    log ""
    log "*** $*"
    if [ "$WROTE" -ne 0 ]; then
        log "*** JA HAVIA GRAVADO $WROTE setor(es). NAO DESLIGUE O APARELHO."
        log "*** REVERSAO para o estado ANTERIOR (a base deste kit):"
        log "***   sudo $TOOL --id $DEV write_flash 0xD000 0 0x1000 base_D000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x48000 0 0x1000 base_48000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD0000 0 0x1000 base_D0000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD1000 0 0x1000 base_D1000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD2000 0 0x1000 base_D2000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x100000 0 0x1000 base_100000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x101000 0 0x1000 base_101000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x12E000 0 0x1000 base_12E000.bin"
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
log " OpenPod — gravacao do V024   (8 setores, 32 KiB)"
log " 0x00D000 +0x1000   <- v024_D000.bin"
log " 0x048000 +0x1000   <- v024_48000.bin"
log " 0x0D0000 +0x1000   <- v024_D0000.bin"
log " 0x0D1000 +0x1000   <- v024_D1000.bin"
log " 0x0D2000 +0x1000   <- v024_D2000.bin"
log " 0x100000 +0x1000   <- v024_100000.bin"
log " 0x101000 +0x1000   <- v024_101000.bin"
log " 0x12E000 +0x1000   <- v024_12E000.bin"
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
ck_file v024_D000.bin 382036913757ae6101ead97f28f9196f0407fb3874293dc9f8b88d44c26adfaf
ck_file v024_48000.bin c0f925f4c0b77d74772c3baa5ad808055531d51ebdb286dd7d9a5eef8954f01e
ck_file v024_D0000.bin 7ff368fc24d00e8156ff7d6e7830b9ff70d4832fe2d5e83795a0f6b2c4cb8b16
ck_file v024_D1000.bin 5bae1c8a56f6497b3186e85e9aa9ab153b5f273445500c7c05b7e3f5a77fb1ec
ck_file v024_D2000.bin ff29c013ba2a7361036bdaab6377d8dfb784e9f34a1408ba8effa0ecb5776b9e
ck_file v024_100000.bin d98d199384f58bce5d30be920273437538f28572b76c80783c80430e3ae74451
ck_file v024_101000.bin 3fc82037a6ed598d4004f1aa2f4c44b9534bf10433fe70f8c31af85bbd190a1d
ck_file v024_12E000.bin b37ca356cd5c2fdb5b360386b224cd73061ae2184a94ad2e3413d1eda36bb3fa
ck_file base_D000.bin 4d08eebda9eb6b2870ad4ce4b99d96a51a3a31ccffda31c3219659b5e4cd0535
ck_file base_48000.bin 9c81efc5bc7a9c29a68a32820315bea734d6aa09668cd095a3e02107763bdb74
ck_file base_D0000.bin 1486610febbed13f90d63ca36f9d2f154b2364fc4d47024ffa4c7f6af05ee115
ck_file base_D1000.bin 3431383721510cf1c211de027cf958c183e16db5fabb6b230eb284c85e196aa9
ck_file base_D2000.bin 3431383721510cf1c211de027cf958c183e16db5fabb6b230eb284c85e196aa9
ck_file base_100000.bin 9235a8b222f535fb17acdf729fa7b2bab7dffb89deb37ec6e3fadc6d6e154892
ck_file base_101000.bin 3824acd00b9e61fa4abcad83a4cc08f383d74e62df29b884548dc803a0f742a5
ck_file base_12E000.bin e9a7f5f346fd506660b958b6f81fb39b0ec71dc7e8e923e400ab1430348a51f5

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
ck "ptable" 53248 64 3ba8438d3724a4817d97ae719cf06b56e74033a9b237e898afd30c6417833ec6
ck "FIRM" 57344 1647984 c45b84497844b74c31f3e11e5ebc686195268833bce18af472524eb8547e526f
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."

log ""
log "======================================================================"
log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."
log "   grava  : 32 KiB em 8 setores"
log "   muda   : BISSECCAO 2: V021 + somente os 7 bytes de limite de indice. Home volta a 9 itens com rotulos originais."
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
wr "4/6 1/8" 0xD000 v024_D000.bin 382036913757ae6101ead97f28f9196f0407fb3874293dc9f8b88d44c26adfaf
wr "4/6 2/8" 0x48000 v024_48000.bin c0f925f4c0b77d74772c3baa5ad808055531d51ebdb286dd7d9a5eef8954f01e
wr "4/6 3/8" 0xD0000 v024_D0000.bin 7ff368fc24d00e8156ff7d6e7830b9ff70d4832fe2d5e83795a0f6b2c4cb8b16
wr "4/6 4/8" 0xD1000 v024_D1000.bin 5bae1c8a56f6497b3186e85e9aa9ab153b5f273445500c7c05b7e3f5a77fb1ec
wr "4/6 5/8" 0xD2000 v024_D2000.bin ff29c013ba2a7361036bdaab6377d8dfb784e9f34a1408ba8effa0ecb5776b9e
wr "4/6 6/8" 0x100000 v024_100000.bin d98d199384f58bce5d30be920273437538f28572b76c80783c80430e3ae74451
wr "4/6 7/8" 0x101000 v024_101000.bin 3fc82037a6ed598d4004f1aa2f4c44b9534bf10433fe70f8c31af85bbd190a1d
wr "4/6 8/8" 0x12E000 v024_12E000.bin b37ca356cd5c2fdb5b360386b224cd73061ae2184a94ad2e3413d1eda36bb3fa
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
ck2 "ptable" 53248 64 19cc7456b96f13a2978e948d63ab3f4f811d61d0b607bc972fb61e0b73be675c
ck2 "FIRM" 57344 1647984 239227d1a184e4e09c25683372e3d00d3604cdbcc024923988df729cbadf09f5
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] RESULTADO: V024 GRAVADO E VERIFICADO"
    log ""
    log "   Desconecte e abra o menu principal."
else
    log " [6/6] RESULTADO: ALGUMA REGIAO NAO CONFERE"
    log ""
    log "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:"
    log "     sudo $TOOL --id $DEV write_flash 0xD000 0 0x1000 base_D000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x48000 0 0x1000 base_48000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD0000 0 0x1000 base_D0000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD1000 0 0x1000 base_D1000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD2000 0 0x1000 base_D2000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x100000 0 0x1000 base_100000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x101000 0 0x1000 base_101000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x12E000 0 0x1000 base_12E000.bin"
fi
log "======================================================================"
log ""
log "  leve de volta: before.bin  after.bin  flash_v024.log"
log ""
