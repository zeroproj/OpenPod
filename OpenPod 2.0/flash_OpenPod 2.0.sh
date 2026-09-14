#!/bin/sh
# flash_OpenPod 2.0.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# Chrome padrao da home em 36 telas de lista
#
# Grava 26 setores de 4096 B (104 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_OpenPod 2.0.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
WORK=$(pwd)/openpod_flash_OpenPod 2.0
LOG="$WORK/flash_OpenPod 2.0.log"
WROTE=0

mkdir -p "$WORK"; : > "$LOG"; exec 3>&1
log() { printf '%s\n' "$*" | tee -a "$LOG" >&3; }
die() {
    log ""
    log "*** $*"
    if [ "$WROTE" -ne 0 ]; then
        log "*** JA HAVIA GRAVADO $WROTE setor(es). NAO DESLIGUE O APARELHO."
        log "*** REVERSAO para o estado ANTERIOR (a base deste kit):"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A5000 0 0x1000 base_1A5000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x121000 0 0x1000 base_121000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x126000 0 0x1000 base_126000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x127000 0 0x1000 base_127000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x128000 0 0x1000 base_128000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x12A000 0 0x1000 base_12A000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x12B000 0 0x1000 base_12B000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x12C000 0 0x1000 base_12C000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x12D000 0 0x1000 base_12D000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x12E000 0 0x1000 base_12E000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x12F000 0 0x1000 base_12F000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x130000 0 0x1000 base_130000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x131000 0 0x1000 base_131000.bin"
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
        log "***   sudo $TOOL --id $DEV write_flash 0x13D000 0 0x1000 base_13D000.bin"
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
log " OpenPod — gravacao do OPENPOD 2.0   (26 setores, 104 KiB)"
log " 0x1A5000 +0x1000   <- OpenPod 2.0_1A5000.bin"
log " 0x10A000 +0x1000   <- OpenPod 2.0_10A000.bin"
log " 0x121000 +0x1000   <- OpenPod 2.0_121000.bin"
log " 0x126000 +0x1000   <- OpenPod 2.0_126000.bin"
log " 0x127000 +0x1000   <- OpenPod 2.0_127000.bin"
log " 0x128000 +0x1000   <- OpenPod 2.0_128000.bin"
log " 0x12A000 +0x1000   <- OpenPod 2.0_12A000.bin"
log " 0x12B000 +0x1000   <- OpenPod 2.0_12B000.bin"
log " 0x12C000 +0x1000   <- OpenPod 2.0_12C000.bin"
log " 0x12D000 +0x1000   <- OpenPod 2.0_12D000.bin"
log " 0x12E000 +0x1000   <- OpenPod 2.0_12E000.bin"
log " 0x12F000 +0x1000   <- OpenPod 2.0_12F000.bin"
log " 0x130000 +0x1000   <- OpenPod 2.0_130000.bin"
log " 0x131000 +0x1000   <- OpenPod 2.0_131000.bin"
log " 0x132000 +0x1000   <- OpenPod 2.0_132000.bin"
log " 0x133000 +0x1000   <- OpenPod 2.0_133000.bin"
log " 0x134000 +0x1000   <- OpenPod 2.0_134000.bin"
log " 0x135000 +0x1000   <- OpenPod 2.0_135000.bin"
log " 0x136000 +0x1000   <- OpenPod 2.0_136000.bin"
log " 0x137000 +0x1000   <- OpenPod 2.0_137000.bin"
log " 0x138000 +0x1000   <- OpenPod 2.0_138000.bin"
log " 0x139000 +0x1000   <- OpenPod 2.0_139000.bin"
log " 0x13A000 +0x1000   <- OpenPod 2.0_13A000.bin"
log " 0x13B000 +0x1000   <- OpenPod 2.0_13B000.bin"
log " 0x13C000 +0x1000   <- OpenPod 2.0_13C000.bin"
log " 0x13D000 +0x1000   <- OpenPod 2.0_13D000.bin"
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
ck_file OpenPod 2.0_1A5000.bin 007e6ebe35a4e2e2f4745626792db0c05b27bd62cf4f29ccdf1263f4f5a85a47
ck_file OpenPod 2.0_10A000.bin db44efbe6e65ec3d35ee9670f411f174a455174afddd49bce7bc4df8d32a5034
ck_file OpenPod 2.0_121000.bin d3885627432303167cc88f25fee677f5d720626a149e0deb5b77574ab8272490
ck_file OpenPod 2.0_126000.bin 0435a61f8ba0cb26d6126c561ac7c2ce2bedea8b7bbbbba0bae62d35501799cd
ck_file OpenPod 2.0_127000.bin 5c81b5ae3a51fc2aa640301f27ead9e2a3da9a1675660c2b32c0f0bfe4e4f2a5
ck_file OpenPod 2.0_128000.bin 721c077d8f1a92eded8403c5c0e87648a991f34dc1f2daae5973791fbe188ec4
ck_file OpenPod 2.0_12A000.bin f142a6ac098e44618bb6ae13991006ea6134fe7ff15b0953a6339dc0a37d4f55
ck_file OpenPod 2.0_12B000.bin 8ce8ab07b06bc752e03ba32da841fe78b98a4d407ab0fa0e2c7cebf50b0d4b57
ck_file OpenPod 2.0_12C000.bin fc2fec034f5ddb1bacf7dfdaecf58ae3f07bdc01f3dcb03732618dd1dd7b5355
ck_file OpenPod 2.0_12D000.bin 44059e4d33be5a14b8e32deff0b663f575ed421fbe75f55a8afc59f8bcd81a83
ck_file OpenPod 2.0_12E000.bin 146424205cd63809e89bd7b10c78b90f5a7b732afb972b144b7380ced9cca2ef
ck_file OpenPod 2.0_12F000.bin 2159bede1ac246002b94fd5329daacb5f6deacad742c675c4c12c6dea0e52196
ck_file OpenPod 2.0_130000.bin 80e3059c19b337df03c3c470d73e8ed3cf67fb314f9616213cd1b7a4b3675837
ck_file OpenPod 2.0_131000.bin 05f990f4e511cea71a3bbcc4317d125f18a2fde26ce37223870c7cc120a1fdaf
ck_file OpenPod 2.0_132000.bin 90439556a858992f4e92f4198482e567a3ddd23d51cc8a7f4ca57a3f322a42aa
ck_file OpenPod 2.0_133000.bin 443e703b424e03c79c689ae1303b084ab8476c43f496abad7648f8b2ba65d8ed
ck_file OpenPod 2.0_134000.bin 1652a285a90556753cb6208876c57796f5bba2c6d31b4c50b07b38e90a6155cf
ck_file OpenPod 2.0_135000.bin 559d22b127f8e07a32db49f28752ef44d331a80bb939744e5a7a99f1c1322306
ck_file OpenPod 2.0_136000.bin 70bb0f6eeb358f691939c2bc70806b5a6d7951d5a5bfff5ceb3f81911813464c
ck_file OpenPod 2.0_137000.bin b50d972620d6f8a78380c2a04c528f1e5e50bf8639e94539f0cb39c7b061a614
ck_file OpenPod 2.0_138000.bin ef9bf3151e978142e5c6be8da977ba5e51763515f1016af8c21794a71eab9879
ck_file OpenPod 2.0_139000.bin 2db155b2344c822b0bd351bacf2f5067287b1aef080e53c73cab2184c1968d06
ck_file OpenPod 2.0_13A000.bin 9552dcdae61ccda6b92740f7b32a74e68cf88db5fa581711c6eb16f2a87f9643
ck_file OpenPod 2.0_13B000.bin 3b024e966649c0ae4bb25d817eb04e4568e93bb741fb1ade010a136aae036aa2
ck_file OpenPod 2.0_13C000.bin 23019da31eae49aa7872c342cbc4093a723681dae473d8eb7b392811e482b4d6
ck_file OpenPod 2.0_13D000.bin 456a1f25f81683a8099da921793eae67f4ac0b823f869048e833ebe4f529a666
ck_file base_1A5000.bin 3ebab7028a497f355f330cb49ce4d060f7612a84cbdff7a52afa4420d4455acf
ck_file base_10A000.bin 7b43b61a034b566e9af5321434b542d36e8336e451f184ef56f19ed8c8d92767
ck_file base_121000.bin 6a86e47e0a38da870cdd7acf125a388c40b7e464720dc29bf8b32858eb0ce5be
ck_file base_126000.bin 9a1332383b4b92fbb7c85dd9422023b6533cf65e1dc463dadff7672bd4db7006
ck_file base_127000.bin 1769ddc290989e25fe224f7d4b0332de3d7f5002edbeb0700f90141e9a3de600
ck_file base_128000.bin 9c619940389eadf55e07c027d3b63fb00dc150ad798d49ba86822587c0a2813d
ck_file base_12A000.bin 6203f49c248a4891bc4a034a286350da079c07f65a72449f797845b756d5bc86
ck_file base_12B000.bin d5fd51005833137b9cd99f072ebb5699b90a0f2c4e85d0cbdeed440cc9f898eb
ck_file base_12C000.bin 74c66fdccfc36aad610341e3ee0de4c829805bad4f353e09bca8a37dd2089512
ck_file base_12D000.bin c2f0803e87f2519d91e23106874ab52b98388e7fb74b763d3c8d3b3baf388ae5
ck_file base_12E000.bin 2e9ebe303f47f437476087d65046002259696940dea07591c9e5af21f042e863
ck_file base_12F000.bin 94cd3f3973619879d713651818c80911e57d33ab53f1d3369677505489879778
ck_file base_130000.bin f1ba015f283fc081c41f422c5554eb8efa5d49084bde9a428d01cfffe6be0d4e
ck_file base_131000.bin 996fe84660f3962f40131f7c2f2841ee19e31233cb753751cba8398e9a032031
ck_file base_132000.bin e4b4b52687ad2b31593141e27d997ae31cf291a3da51b4f058540181947b57cd
ck_file base_133000.bin e2ac50c43956ad206d67da291e58d80daea5f8909929c3ab3851053748edca82
ck_file base_134000.bin 7210b822569cd80053ff6d0c51fed3e59469e503c519ca28ed075f6cd860a0e0
ck_file base_135000.bin 30d3ffbb8e5760725d34cdabd2bb013878227d3f9e61fc0dcfedb8ded6692c10
ck_file base_136000.bin 8ff5e9dc8d96564aaad2ad56a6a8e99d2d6ba4f1117b447aa72468954d214c31
ck_file base_137000.bin c169e1f7ef13ba4fa53ce9329226afa8f829a037a1eab0f3b20677190423df05
ck_file base_138000.bin 959f55983781c2b0a11fa80b7f36114be9da631af3eb71bf4f32feb77f1acbb2
ck_file base_139000.bin db9b4c3917fbd7534858ab0cdc07e3b782a0d0fd32c893a68e2c1ca32ec37572
ck_file base_13A000.bin 5d8673e59d52ca034b15a73a819c33f3b6c2d52b2461ff67d71f66e5fab016fb
ck_file base_13B000.bin 48e67d459c807d5f072204e2009eef7d24a1b85221d9c51fff07cf942daefaef
ck_file base_13C000.bin 76e61f3785a17206819ecef9abaf3c8be5887e341f4fa4aa9f6fe7437519ec78
ck_file base_13D000.bin 58683ef08ff6e8c2544596c5c44073af8827edcfd4db0c8bd063dc88e4b10570

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
ck "FIRM" 57344 1647984 1acb506ba4f680f33a0d894f38de374198136d742c39cc2957e3c7cb9ddeb908
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."

log ""
log "======================================================================"
log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."
log "   grava  : 104 KiB em 26 setores"
log "   muda   : Chrome padrao da home em 36 telas de lista"
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
wr "4/6 1/26" 0x1A5000 OpenPod 2.0_1A5000.bin 007e6ebe35a4e2e2f4745626792db0c05b27bd62cf4f29ccdf1263f4f5a85a47
wr "4/6 2/26" 0x10A000 OpenPod 2.0_10A000.bin db44efbe6e65ec3d35ee9670f411f174a455174afddd49bce7bc4df8d32a5034
wr "4/6 3/26" 0x121000 OpenPod 2.0_121000.bin d3885627432303167cc88f25fee677f5d720626a149e0deb5b77574ab8272490
wr "4/6 4/26" 0x126000 OpenPod 2.0_126000.bin 0435a61f8ba0cb26d6126c561ac7c2ce2bedea8b7bbbbba0bae62d35501799cd
wr "4/6 5/26" 0x127000 OpenPod 2.0_127000.bin 5c81b5ae3a51fc2aa640301f27ead9e2a3da9a1675660c2b32c0f0bfe4e4f2a5
wr "4/6 6/26" 0x128000 OpenPod 2.0_128000.bin 721c077d8f1a92eded8403c5c0e87648a991f34dc1f2daae5973791fbe188ec4
wr "4/6 7/26" 0x12A000 OpenPod 2.0_12A000.bin f142a6ac098e44618bb6ae13991006ea6134fe7ff15b0953a6339dc0a37d4f55
wr "4/6 8/26" 0x12B000 OpenPod 2.0_12B000.bin 8ce8ab07b06bc752e03ba32da841fe78b98a4d407ab0fa0e2c7cebf50b0d4b57
wr "4/6 9/26" 0x12C000 OpenPod 2.0_12C000.bin fc2fec034f5ddb1bacf7dfdaecf58ae3f07bdc01f3dcb03732618dd1dd7b5355
wr "4/6 10/26" 0x12D000 OpenPod 2.0_12D000.bin 44059e4d33be5a14b8e32deff0b663f575ed421fbe75f55a8afc59f8bcd81a83
wr "4/6 11/26" 0x12E000 OpenPod 2.0_12E000.bin 146424205cd63809e89bd7b10c78b90f5a7b732afb972b144b7380ced9cca2ef
wr "4/6 12/26" 0x12F000 OpenPod 2.0_12F000.bin 2159bede1ac246002b94fd5329daacb5f6deacad742c675c4c12c6dea0e52196
wr "4/6 13/26" 0x130000 OpenPod 2.0_130000.bin 80e3059c19b337df03c3c470d73e8ed3cf67fb314f9616213cd1b7a4b3675837
wr "4/6 14/26" 0x131000 OpenPod 2.0_131000.bin 05f990f4e511cea71a3bbcc4317d125f18a2fde26ce37223870c7cc120a1fdaf
wr "4/6 15/26" 0x132000 OpenPod 2.0_132000.bin 90439556a858992f4e92f4198482e567a3ddd23d51cc8a7f4ca57a3f322a42aa
wr "4/6 16/26" 0x133000 OpenPod 2.0_133000.bin 443e703b424e03c79c689ae1303b084ab8476c43f496abad7648f8b2ba65d8ed
wr "4/6 17/26" 0x134000 OpenPod 2.0_134000.bin 1652a285a90556753cb6208876c57796f5bba2c6d31b4c50b07b38e90a6155cf
wr "4/6 18/26" 0x135000 OpenPod 2.0_135000.bin 559d22b127f8e07a32db49f28752ef44d331a80bb939744e5a7a99f1c1322306
wr "4/6 19/26" 0x136000 OpenPod 2.0_136000.bin 70bb0f6eeb358f691939c2bc70806b5a6d7951d5a5bfff5ceb3f81911813464c
wr "4/6 20/26" 0x137000 OpenPod 2.0_137000.bin b50d972620d6f8a78380c2a04c528f1e5e50bf8639e94539f0cb39c7b061a614
wr "4/6 21/26" 0x138000 OpenPod 2.0_138000.bin ef9bf3151e978142e5c6be8da977ba5e51763515f1016af8c21794a71eab9879
wr "4/6 22/26" 0x139000 OpenPod 2.0_139000.bin 2db155b2344c822b0bd351bacf2f5067287b1aef080e53c73cab2184c1968d06
wr "4/6 23/26" 0x13A000 OpenPod 2.0_13A000.bin 9552dcdae61ccda6b92740f7b32a74e68cf88db5fa581711c6eb16f2a87f9643
wr "4/6 24/26" 0x13B000 OpenPod 2.0_13B000.bin 3b024e966649c0ae4bb25d817eb04e4568e93bb741fb1ade010a136aae036aa2
wr "4/6 25/26" 0x13C000 OpenPod 2.0_13C000.bin 23019da31eae49aa7872c342cbc4093a723681dae473d8eb7b392811e482b4d6
wr "4/6 26/26" 0x13D000 OpenPod 2.0_13D000.bin 456a1f25f81683a8099da921793eae67f4ac0b823f869048e833ebe4f529a666
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
ck2 "FIRM" 57344 1647984 5aad5ee92a49f2551091ccca69e8c36e68b55914dc798c7b36902d8d380e73e7
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] RESULTADO: OPENPOD 2.0 GRAVADO E VERIFICADO"
    log ""
    log "   Desconecte e abra o menu principal."
else
    log " [6/6] RESULTADO: ALGUMA REGIAO NAO CONFERE"
    log ""
    log "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:"
    log "     sudo $TOOL --id $DEV write_flash 0x1A5000 0 0x1000 base_1A5000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x121000 0 0x1000 base_121000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x126000 0 0x1000 base_126000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x127000 0 0x1000 base_127000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x128000 0 0x1000 base_128000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x12A000 0 0x1000 base_12A000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x12B000 0 0x1000 base_12B000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x12C000 0 0x1000 base_12C000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x12D000 0 0x1000 base_12D000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x12E000 0 0x1000 base_12E000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x12F000 0 0x1000 base_12F000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x130000 0 0x1000 base_130000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x131000 0 0x1000 base_131000.bin"
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
    log "     sudo $TOOL --id $DEV write_flash 0x13D000 0 0x1000 base_13D000.bin"
fi
log "======================================================================"
log ""
log "  leve de volta: before.bin  after.bin  flash_OpenPod 2.0.log"
log ""
