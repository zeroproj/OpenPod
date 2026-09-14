#!/bin/sh
# flash_v021r.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# VOLTA: do V022 de volta ao V021, que funcionava
#
# Grava 10 setores de 4096 B (40 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_v021r.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
WORK=$(pwd)/openpod_flash_v021r
LOG="$WORK/flash_v021r.log"
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
        log "***   sudo $TOOL --id $DEV write_flash 0x12F000 0 0x1000 base_12F000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A3000 0 0x1000 base_1A3000.bin"
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
log " OpenPod — gravacao do V021R   (10 setores, 40 KiB)"
log " 0x00D000 +0x1000   <- v021r_D000.bin"
log " 0x048000 +0x1000   <- v021r_48000.bin"
log " 0x0D0000 +0x1000   <- v021r_D0000.bin"
log " 0x0D1000 +0x1000   <- v021r_D1000.bin"
log " 0x0D2000 +0x1000   <- v021r_D2000.bin"
log " 0x100000 +0x1000   <- v021r_100000.bin"
log " 0x101000 +0x1000   <- v021r_101000.bin"
log " 0x12E000 +0x1000   <- v021r_12E000.bin"
log " 0x12F000 +0x1000   <- v021r_12F000.bin"
log " 0x1A3000 +0x1000   <- v021r_1A3000.bin"
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
ck_file v021r_D000.bin 8aad91631026db6c1d6b75f5b50facef61b37fc93a85d7b7e942399d0d2c1195
ck_file v021r_48000.bin c0f925f4c0b77d74772c3baa5ad808055531d51ebdb286dd7d9a5eef8954f01e
ck_file v021r_D0000.bin 7ff368fc24d00e8156ff7d6e7830b9ff70d4832fe2d5e83795a0f6b2c4cb8b16
ck_file v021r_D1000.bin 5bae1c8a56f6497b3186e85e9aa9ab153b5f273445500c7c05b7e3f5a77fb1ec
ck_file v021r_D2000.bin ff29c013ba2a7361036bdaab6377d8dfb784e9f34a1408ba8effa0ecb5776b9e
ck_file v021r_100000.bin d98d199384f58bce5d30be920273437538f28572b76c80783c80430e3ae74451
ck_file v021r_101000.bin 3fc82037a6ed598d4004f1aa2f4c44b9534bf10433fe70f8c31af85bbd190a1d
ck_file v021r_12E000.bin 229f129437b064c65c93e03c25f94151bbb2b5b9d21f9ae20ea8d01618ab6f7e
ck_file v021r_12F000.bin d882556ecd8e1f18038733b1befaa656f9a49034c5dc1305031114176f8064d3
ck_file v021r_1A3000.bin 2f5806489089b286b54fc6731acd93ebe5f05ba97dfac85a388ca6d1e97af22c
ck_file base_D000.bin f9c71b1d4def564cfd77a451463771e615ac468d283b2061a031c782efdc7bbc
ck_file base_48000.bin 9c81efc5bc7a9c29a68a32820315bea734d6aa09668cd095a3e02107763bdb74
ck_file base_D0000.bin 1486610febbed13f90d63ca36f9d2f154b2364fc4d47024ffa4c7f6af05ee115
ck_file base_D1000.bin 3431383721510cf1c211de027cf958c183e16db5fabb6b230eb284c85e196aa9
ck_file base_D2000.bin 3431383721510cf1c211de027cf958c183e16db5fabb6b230eb284c85e196aa9
ck_file base_100000.bin 9a8e8eac3029de1b3ab7bea7dcc0ad95929afff819bc0d13bbe161c3f2ad1253
ck_file base_101000.bin 3824acd00b9e61fa4abcad83a4cc08f383d74e62df29b884548dc803a0f742a5
ck_file base_12E000.bin 1519c18e3064f645cb02479db2fe0ec988acef6cbfda0ad467762fee7697c2de
ck_file base_12F000.bin 1957e6f490d604dc694cf2165d9fbd805c14213c5f05c271f3a7a55ec85a79b9
ck_file base_1A3000.bin 481efa03cefb2ba6800643580a784e71a78c2dc2cf86a34bf333eb2c1adde43e

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
ck "ptable" 53248 64 14094d745ac1c9c439b87c2d302d36b2d7cfdae85cc0c2668e4211a54cbe0bd3
ck "FIRM" 57344 1647984 d16940567f10b363205b7abc6c4cc5c6796fe414e7b78a75a220cc14c1e8ea82
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."

log ""
log "======================================================================"
log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."
log "   grava  : 40 KiB em 10 setores"
log "   muda   : VOLTA: do V022 de volta ao V021, que funcionava"
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
wr "4/6 1/10" 0xD000 v021r_D000.bin 8aad91631026db6c1d6b75f5b50facef61b37fc93a85d7b7e942399d0d2c1195
wr "4/6 2/10" 0x48000 v021r_48000.bin c0f925f4c0b77d74772c3baa5ad808055531d51ebdb286dd7d9a5eef8954f01e
wr "4/6 3/10" 0xD0000 v021r_D0000.bin 7ff368fc24d00e8156ff7d6e7830b9ff70d4832fe2d5e83795a0f6b2c4cb8b16
wr "4/6 4/10" 0xD1000 v021r_D1000.bin 5bae1c8a56f6497b3186e85e9aa9ab153b5f273445500c7c05b7e3f5a77fb1ec
wr "4/6 5/10" 0xD2000 v021r_D2000.bin ff29c013ba2a7361036bdaab6377d8dfb784e9f34a1408ba8effa0ecb5776b9e
wr "4/6 6/10" 0x100000 v021r_100000.bin d98d199384f58bce5d30be920273437538f28572b76c80783c80430e3ae74451
wr "4/6 7/10" 0x101000 v021r_101000.bin 3fc82037a6ed598d4004f1aa2f4c44b9534bf10433fe70f8c31af85bbd190a1d
wr "4/6 8/10" 0x12E000 v021r_12E000.bin 229f129437b064c65c93e03c25f94151bbb2b5b9d21f9ae20ea8d01618ab6f7e
wr "4/6 9/10" 0x12F000 v021r_12F000.bin d882556ecd8e1f18038733b1befaa656f9a49034c5dc1305031114176f8064d3
wr "4/6 10/10" 0x1A3000 v021r_1A3000.bin 2f5806489089b286b54fc6731acd93ebe5f05ba97dfac85a388ca6d1e97af22c
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
ck2 "ptable" 53248 64 1f2d0c30c3c16509e8299c3bac563fc8c20d5bb63f9dafc8e53b5014b4e79809
ck2 "FIRM" 57344 1647984 e7aa3b0e0f6a9fc0e8f09caabcbdda729ae119a2151116378be01d16062d96b7
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] RESULTADO: V021R GRAVADO E VERIFICADO"
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
    log "     sudo $TOOL --id $DEV write_flash 0x12F000 0 0x1000 base_12F000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A3000 0 0x1000 base_1A3000.bin"
fi
log "======================================================================"
log ""
log "  leve de volta: before.bin  after.bin  flash_v021r.log"
log ""
