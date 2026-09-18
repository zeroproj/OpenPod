#!/bin/sh
# flash_OpenPod_Core_5.4.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# A faixa superior fica com 16 px em todas as telas
#
# Grava 17 setores de 4096 B (68 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_OpenPod_Core_5.4.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
VERSAO="OpenPod_Core_5.4"
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
        log "***   sudo $TOOL --id $DEV write_flash 0x127000 0 0x1000 base_127000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x128000 0 0x1000 base_128000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x12E000 0 0x1000 base_12E000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x12F000 0 0x1000 base_12F000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x130000 0 0x1000 base_130000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x132000 0 0x1000 base_132000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x133000 0 0x1000 base_133000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x134000 0 0x1000 base_134000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x135000 0 0x1000 base_135000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x136000 0 0x1000 base_136000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x137000 0 0x1000 base_137000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x138000 0 0x1000 base_138000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x139000 0 0x1000 base_139000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x13A000 0 0x1000 base_13A000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x13B000 0 0x1000 base_13B000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x13C000 0 0x1000 base_13C000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A6000 0 0x1000 base_1A6000.bin"
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
log " OpenPod — gravacao do OPENPOD_CORE_5.4   (17 setores, 68 KiB)"
log " 0x127000 +0x1000   <- OpenPod_Core_5.4_127000.bin"
log " 0x128000 +0x1000   <- OpenPod_Core_5.4_128000.bin"
log " 0x12E000 +0x1000   <- OpenPod_Core_5.4_12E000.bin"
log " 0x12F000 +0x1000   <- OpenPod_Core_5.4_12F000.bin"
log " 0x130000 +0x1000   <- OpenPod_Core_5.4_130000.bin"
log " 0x132000 +0x1000   <- OpenPod_Core_5.4_132000.bin"
log " 0x133000 +0x1000   <- OpenPod_Core_5.4_133000.bin"
log " 0x134000 +0x1000   <- OpenPod_Core_5.4_134000.bin"
log " 0x135000 +0x1000   <- OpenPod_Core_5.4_135000.bin"
log " 0x136000 +0x1000   <- OpenPod_Core_5.4_136000.bin"
log " 0x137000 +0x1000   <- OpenPod_Core_5.4_137000.bin"
log " 0x138000 +0x1000   <- OpenPod_Core_5.4_138000.bin"
log " 0x139000 +0x1000   <- OpenPod_Core_5.4_139000.bin"
log " 0x13A000 +0x1000   <- OpenPod_Core_5.4_13A000.bin"
log " 0x13B000 +0x1000   <- OpenPod_Core_5.4_13B000.bin"
log " 0x13C000 +0x1000   <- OpenPod_Core_5.4_13C000.bin"
log " 0x1A6000 +0x1000   <- OpenPod_Core_5.4_1A6000.bin"
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
ck_file "OpenPod_Core_5.4_127000.bin" e9d327492dd109c2513cbf07d402e9443eca0acd47193c5de856a9ce03a5a498
ck_file "OpenPod_Core_5.4_128000.bin" 34fa1dc3c4fb1832216c8ecac2b3e469f32988dcdad6d6bdf8c7a94cd92a8adc
ck_file "OpenPod_Core_5.4_12E000.bin" 34338f09581e5aa1c689c188201ddfdebc29d251a0bfe7e1074d58c429be7157
ck_file "OpenPod_Core_5.4_12F000.bin" a640a2e36034aed5c4b51653fb7b6cc85d94f5d43eb12224c3b16a74c61ef102
ck_file "OpenPod_Core_5.4_130000.bin" 2dba79928d0639acae56054c764ffcb757ca3d14c75fa3b33607e8b70da36531
ck_file "OpenPod_Core_5.4_132000.bin" e05828e015b71a8c3f2290b03b843188771855583e7ee886244de7d17bd46f0e
ck_file "OpenPod_Core_5.4_133000.bin" ffdb8e5ee01d4219eec486d7f3bc60df7e62e30269361daad437835008b513bf
ck_file "OpenPod_Core_5.4_134000.bin" bdb077624bce3c8b2d508b03393c0608004a53cefbd1ab1c3e1142f5ef0cb6b4
ck_file "OpenPod_Core_5.4_135000.bin" e52b4f721ab955ce0acc404d7bbffb4dded60b0c0b09d43fcd8b54b04ebfab7e
ck_file "OpenPod_Core_5.4_136000.bin" 37133af6fa7684d462b11159bacebd685f7f5e533830fd2607ce63f0d177d7b8
ck_file "OpenPod_Core_5.4_137000.bin" 9f27ec07c3773ed74cc2702121298b8cdbbcb4ec5815b994d8a430226b9e8bf5
ck_file "OpenPod_Core_5.4_138000.bin" 69c8b20ae8e76e94436678ef7e3552b665b766e0335584e0b5649736edae6778
ck_file "OpenPod_Core_5.4_139000.bin" 0809afdd572786578e9713711d83177fd77ebe5c89734a78cf16d55d90242c8d
ck_file "OpenPod_Core_5.4_13A000.bin" 26aad81f09b8b23a6b3b1af03f9af0bde7107f59d6078b2e0ec2540d5f8de0aa
ck_file "OpenPod_Core_5.4_13B000.bin" e76fe152ae3b0f4414952f7f658add959f41adf86e0297a5ea657288cafa1a6e
ck_file "OpenPod_Core_5.4_13C000.bin" f9b05c7df264e8c210701e056986e0167641e37ed7cf32d8f477f15aa77feb34
ck_file "OpenPod_Core_5.4_1A6000.bin" f3374c73f299fe0a136efd52a01b77f4025eb3b7eec759d071bf06a58f2f6f4f
ck_file "base_127000.bin" a72494f6d0474e8921d084c7dbdc287e4de6f85ad4e534fe4b6f8d7f3b98cc2b
ck_file "base_128000.bin" e3195af0f62cc2555032938b4ed147a4951db9f63301d49447afa8e146288f23
ck_file "base_12E000.bin" f67b84d10aed29637e6be627d6588e6af0bac98b9c4dd52e9ef75d668b79c529
ck_file "base_12F000.bin" bfdecd14bfb43abb02ec40c8adce0a40fd71039c886cdd395e89b4b127c49918
ck_file "base_130000.bin" f1ba015f283fc081c41f422c5554eb8efa5d49084bde9a428d01cfffe6be0d4e
ck_file "base_132000.bin" 53e7b18c837abb3b36b704c27c0581bd24e1533b6afffb701fca4c74b6603aa8
ck_file "base_133000.bin" 628bab444f257429242533c3f8073fb3f4a5d0e86283fe55f033c21c0f95129b
ck_file "base_134000.bin" 7210b822569cd80053ff6d0c51fed3e59469e503c519ca28ed075f6cd860a0e0
ck_file "base_135000.bin" c97273135f137a9791aa788d15130cc311ceb263d5c834bf9fdffd5a0c66d73e
ck_file "base_136000.bin" 7a8cc2e71a8f2aa704ba434e824f88d9a9a1410f207f52e96f9dd72d67e73e0a
ck_file "base_137000.bin" 6bcdf868d93c2ae949167761e7c819cd1bc2ffc5a4e22a89fce427ae555ea169
ck_file "base_138000.bin" 44715091732627568898584d334cf0bc80ff09440e440d9b80006110fc8d310a
ck_file "base_139000.bin" db9b4c3917fbd7534858ab0cdc07e3b782a0d0fd32c893a68e2c1ca32ec37572
ck_file "base_13A000.bin" beecb9996543bb73f983d423ae24dd704dc9067d98c81aa69f6d30a7c3701d99
ck_file "base_13B000.bin" 48e67d459c807d5f072204e2009eef7d24a1b85221d9c51fff07cf942daefaef
ck_file "base_13C000.bin" 1c7c56e5eda5fcecd4a488dfdfccf93f3795f8971a3b62c73ec36ee51d26b588
ck_file "base_1A6000.bin" 7f9ba1eaa80a0ff8169167cfc32654419febafc5eb3e5431e71465765a07d872

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
ck "FIRM" 57344 1647984 a7d786e1c84d13323a5d3c5e5019f3cc795df70a40ce3bcd08461b08b1bc34df
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."

log ""
log "======================================================================"
log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."
log "   grava  : 68 KiB em 17 setores"
log "   muda   : A faixa superior fica com 16 px em todas as telas"
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
wr "4/6 1/17" 0x127000 "OpenPod_Core_5.4_127000.bin" e9d327492dd109c2513cbf07d402e9443eca0acd47193c5de856a9ce03a5a498
wr "4/6 2/17" 0x128000 "OpenPod_Core_5.4_128000.bin" 34fa1dc3c4fb1832216c8ecac2b3e469f32988dcdad6d6bdf8c7a94cd92a8adc
wr "4/6 3/17" 0x12E000 "OpenPod_Core_5.4_12E000.bin" 34338f09581e5aa1c689c188201ddfdebc29d251a0bfe7e1074d58c429be7157
wr "4/6 4/17" 0x12F000 "OpenPod_Core_5.4_12F000.bin" a640a2e36034aed5c4b51653fb7b6cc85d94f5d43eb12224c3b16a74c61ef102
wr "4/6 5/17" 0x130000 "OpenPod_Core_5.4_130000.bin" 2dba79928d0639acae56054c764ffcb757ca3d14c75fa3b33607e8b70da36531
wr "4/6 6/17" 0x132000 "OpenPod_Core_5.4_132000.bin" e05828e015b71a8c3f2290b03b843188771855583e7ee886244de7d17bd46f0e
wr "4/6 7/17" 0x133000 "OpenPod_Core_5.4_133000.bin" ffdb8e5ee01d4219eec486d7f3bc60df7e62e30269361daad437835008b513bf
wr "4/6 8/17" 0x134000 "OpenPod_Core_5.4_134000.bin" bdb077624bce3c8b2d508b03393c0608004a53cefbd1ab1c3e1142f5ef0cb6b4
wr "4/6 9/17" 0x135000 "OpenPod_Core_5.4_135000.bin" e52b4f721ab955ce0acc404d7bbffb4dded60b0c0b09d43fcd8b54b04ebfab7e
wr "4/6 10/17" 0x136000 "OpenPod_Core_5.4_136000.bin" 37133af6fa7684d462b11159bacebd685f7f5e533830fd2607ce63f0d177d7b8
wr "4/6 11/17" 0x137000 "OpenPod_Core_5.4_137000.bin" 9f27ec07c3773ed74cc2702121298b8cdbbcb4ec5815b994d8a430226b9e8bf5
wr "4/6 12/17" 0x138000 "OpenPod_Core_5.4_138000.bin" 69c8b20ae8e76e94436678ef7e3552b665b766e0335584e0b5649736edae6778
wr "4/6 13/17" 0x139000 "OpenPod_Core_5.4_139000.bin" 0809afdd572786578e9713711d83177fd77ebe5c89734a78cf16d55d90242c8d
wr "4/6 14/17" 0x13A000 "OpenPod_Core_5.4_13A000.bin" 26aad81f09b8b23a6b3b1af03f9af0bde7107f59d6078b2e0ec2540d5f8de0aa
wr "4/6 15/17" 0x13B000 "OpenPod_Core_5.4_13B000.bin" e76fe152ae3b0f4414952f7f658add959f41adf86e0297a5ea657288cafa1a6e
wr "4/6 16/17" 0x13C000 "OpenPod_Core_5.4_13C000.bin" f9b05c7df264e8c210701e056986e0167641e37ed7cf32d8f477f15aa77feb34
wr "4/6 17/17" 0x1A6000 "OpenPod_Core_5.4_1A6000.bin" f3374c73f299fe0a136efd52a01b77f4025eb3b7eec759d071bf06a58f2f6f4f
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
ck2 "FIRM" 57344 1647984 356cea7cbe462a889b71f9708a897c066b74686d57cf84115475ee2560d35ab8
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] RESULTADO: OPENPOD_CORE_5.4 GRAVADO E VERIFICADO"
    log ""
    log "   Desconecte e abra o menu principal."
else
    log " [6/6] RESULTADO: ALGUMA REGIAO NAO CONFERE"
    log ""
    log "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:"
    log "     sudo $TOOL --id $DEV write_flash 0x127000 0 0x1000 base_127000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x128000 0 0x1000 base_128000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x12E000 0 0x1000 base_12E000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x12F000 0 0x1000 base_12F000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x130000 0 0x1000 base_130000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x132000 0 0x1000 base_132000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x133000 0 0x1000 base_133000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x134000 0 0x1000 base_134000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x135000 0 0x1000 base_135000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x136000 0 0x1000 base_136000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x137000 0 0x1000 base_137000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x138000 0 0x1000 base_138000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x139000 0 0x1000 base_139000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x13A000 0 0x1000 base_13A000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x13B000 0 0x1000 base_13B000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x13C000 0 0x1000 base_13C000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A6000 0 0x1000 base_1A6000.bin"
fi
log "======================================================================"
log ""
log "  leve de volta: before.bin  after.bin  flash_$VERSAO.log"
log ""
