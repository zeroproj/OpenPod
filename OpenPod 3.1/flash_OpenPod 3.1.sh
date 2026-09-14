#!/bin/sh
# flash_OpenPod 3.1.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# 3.0 + as tres ferramentas que a medicao mostrou faltando.
#
# Grava 9 setores de 4096 B (36 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_OpenPod 3.1.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
WORK=$(pwd)/openpod_flash_OpenPod 3.1
LOG="$WORK/flash_OpenPod 3.1.log"
WROTE=0

mkdir -p "$WORK"; : > "$LOG"; exec 3>&1
log() { printf '%s\n' "$*" | tee -a "$LOG" >&3; }
die() {
    log ""
    log "*** $*"
    if [ "$WROTE" -ne 0 ]; then
        log "*** JA HAVIA GRAVADO $WROTE setor(es). NAO DESLIGUE O APARELHO."
        log "*** REVERSAO para o estado ANTERIOR (a base deste kit):"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A3000 0 0x1000 base_1A3000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A5000 0 0x1000 base_1A5000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A6000 0 0x1000 base_1A6000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCD000 0 0x1000 base_CD000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x109000 0 0x1000 base_109000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x122000 0 0x1000 base_122000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x12E000 0 0x1000 base_12E000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x12F000 0 0x1000 base_12F000.bin"
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
log " OpenPod — gravacao do OPENPOD 3.1   (9 setores, 36 KiB)"
log " 0x1A3000 +0x1000   <- OpenPod 3.1_1A3000.bin"
log " 0x1A5000 +0x1000   <- OpenPod 3.1_1A5000.bin"
log " 0x1A6000 +0x1000   <- OpenPod 3.1_1A6000.bin"
log " 0x0CD000 +0x1000   <- OpenPod 3.1_CD000.bin"
log " 0x109000 +0x1000   <- OpenPod 3.1_109000.bin"
log " 0x10A000 +0x1000   <- OpenPod 3.1_10A000.bin"
log " 0x122000 +0x1000   <- OpenPod 3.1_122000.bin"
log " 0x12E000 +0x1000   <- OpenPod 3.1_12E000.bin"
log " 0x12F000 +0x1000   <- OpenPod 3.1_12F000.bin"
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
ck_file OpenPod 3.1_1A3000.bin d0008a84d9e70fdb69574635372731a8d4b5d8ff6116036f5e8161076890ef67
ck_file OpenPod 3.1_1A5000.bin 0fe0d3f4359e92a39d854d76e860084f6595f73f9911a15017a0cfc512594fe3
ck_file OpenPod 3.1_1A6000.bin 2100db6a65888504ac98c414cfa5662a8999879a1a02d747470b38047f5df4fb
ck_file OpenPod 3.1_CD000.bin 4744cde05261477dc2cab5cb768921ab70e231f23a5772d7546553945fd12dd2
ck_file OpenPod 3.1_109000.bin 3bc16bacee418a50f79df0aa7c3f5604241fc55f126ee8d7bec7d802849312c2
ck_file OpenPod 3.1_10A000.bin 1279cb5ee45c35cd103e0fb312396dcbc58286b6e789c22baee8e190cb4ab192
ck_file OpenPod 3.1_122000.bin 8ca14bfbc3ad7cdbb2ad2308b28a44bb4509fcacbf94fa70fc0fe1fd751a1297
ck_file OpenPod 3.1_12E000.bin 366270cccc963eb94aaf21081eba7a0ba7d54a438a4f4503e72a29a01d391d06
ck_file OpenPod 3.1_12F000.bin 6949cbb9213b546ff0b0c60fc5ddd4e0558aaf370a4b88cbff830deca7a956b1
ck_file base_1A3000.bin c7ebd237e44ae52fa0f0ae12e1045498a3e89be89932c2fcabc09876e51af533
ck_file base_1A5000.bin 01290b9215002a96349d3af13bbab56d0c97e4cab32e8dffed6c6e8e91cfed4d
ck_file base_1A6000.bin f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6
ck_file base_CD000.bin ab039386aa645f414a0580730cc4b62ca7831c9d4d8dff7b01c80f9b7be16f5f
ck_file base_109000.bin c523eccfe2be4d16da8b146883adef2279fc6df7c9094b10103168d9e29878b4
ck_file base_10A000.bin ea98b618b0412ef07110f5378bcc464a62e520a1aa3b20d095152f75dd5ef99c
ck_file base_122000.bin ec7e02442e91c3eff704ceb49d3f57a668c136f249d4d69d823a1090e7399ad5
ck_file base_12E000.bin f7028cb9d8f1868c843c46de295138287fd430e0778b30aa709373089feaad86
ck_file base_12F000.bin c1f92c43ac8b1722b83ddb5c9238792b09bdb2938b11c099be8ba6e7d71317de

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
ck "FIRM" 57344 1647984 e75a48679e4f48987cacd7461878c2e93d204071e0e76b1ec8d01a63eb02bf87
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."

log ""
log "======================================================================"
log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."
log "   grava  : 36 KiB em 9 setores"
log "   muda   : 3.0 + as tres ferramentas que a medicao mostrou faltando."
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
wr "4/6 1/9" 0x1A3000 OpenPod 3.1_1A3000.bin d0008a84d9e70fdb69574635372731a8d4b5d8ff6116036f5e8161076890ef67
wr "4/6 2/9" 0x1A5000 OpenPod 3.1_1A5000.bin 0fe0d3f4359e92a39d854d76e860084f6595f73f9911a15017a0cfc512594fe3
wr "4/6 3/9" 0x1A6000 OpenPod 3.1_1A6000.bin 2100db6a65888504ac98c414cfa5662a8999879a1a02d747470b38047f5df4fb
wr "4/6 4/9" 0xCD000 OpenPod 3.1_CD000.bin 4744cde05261477dc2cab5cb768921ab70e231f23a5772d7546553945fd12dd2
wr "4/6 5/9" 0x109000 OpenPod 3.1_109000.bin 3bc16bacee418a50f79df0aa7c3f5604241fc55f126ee8d7bec7d802849312c2
wr "4/6 6/9" 0x10A000 OpenPod 3.1_10A000.bin 1279cb5ee45c35cd103e0fb312396dcbc58286b6e789c22baee8e190cb4ab192
wr "4/6 7/9" 0x122000 OpenPod 3.1_122000.bin 8ca14bfbc3ad7cdbb2ad2308b28a44bb4509fcacbf94fa70fc0fe1fd751a1297
wr "4/6 8/9" 0x12E000 OpenPod 3.1_12E000.bin 366270cccc963eb94aaf21081eba7a0ba7d54a438a4f4503e72a29a01d391d06
wr "4/6 9/9" 0x12F000 OpenPod 3.1_12F000.bin 6949cbb9213b546ff0b0c60fc5ddd4e0558aaf370a4b88cbff830deca7a956b1
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
ck2 "FIRM" 57344 1647984 a3250f0b254334273c95374ab55eaf94bccd6ecc67f895f7007aafc7bc652f91
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] RESULTADO: OPENPOD 3.1 GRAVADO E VERIFICADO"
    log ""
    log "   Desconecte e abra o menu principal."
else
    log " [6/6] RESULTADO: ALGUMA REGIAO NAO CONFERE"
    log ""
    log "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:"
    log "     sudo $TOOL --id $DEV write_flash 0x1A3000 0 0x1000 base_1A3000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A5000 0 0x1000 base_1A5000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A6000 0 0x1000 base_1A6000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCD000 0 0x1000 base_CD000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x109000 0 0x1000 base_109000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x122000 0 0x1000 base_122000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x12E000 0 0x1000 base_12E000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x12F000 0 0x1000 base_12F000.bin"
fi
log "======================================================================"
log ""
log "  leve de volta: before.bin  after.bin  flash_OpenPod 3.1.log"
log ""
