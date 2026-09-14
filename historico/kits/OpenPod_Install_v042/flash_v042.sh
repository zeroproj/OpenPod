#!/bin/sh
# flash_v042.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# Extras no padrao da home + separador some + linha 16px em todas as listas
#
# Grava 24 setores de 4096 B (96 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_v042.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
WORK=$(pwd)/openpod_flash_v042
LOG="$WORK/flash_v042.log"
WROTE=0

mkdir -p "$WORK"; : > "$LOG"; exec 3>&1
log() { printf '%s\n' "$*" | tee -a "$LOG" >&3; }
die() {
    log ""
    log "*** $*"
    if [ "$WROTE" -ne 0 ]; then
        log "*** JA HAVIA GRAVADO $WROTE setor(es). NAO DESLIGUE O APARELHO."
        log "*** REVERSAO para o estado ANTERIOR (a base deste kit):"
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
log " OpenPod — gravacao do V042   (24 setores, 96 KiB)"
log " 0x121000 +0x1000   <- v042_121000.bin"
log " 0x126000 +0x1000   <- v042_126000.bin"
log " 0x127000 +0x1000   <- v042_127000.bin"
log " 0x128000 +0x1000   <- v042_128000.bin"
log " 0x12A000 +0x1000   <- v042_12A000.bin"
log " 0x12B000 +0x1000   <- v042_12B000.bin"
log " 0x12C000 +0x1000   <- v042_12C000.bin"
log " 0x12D000 +0x1000   <- v042_12D000.bin"
log " 0x12E000 +0x1000   <- v042_12E000.bin"
log " 0x12F000 +0x1000   <- v042_12F000.bin"
log " 0x130000 +0x1000   <- v042_130000.bin"
log " 0x131000 +0x1000   <- v042_131000.bin"
log " 0x132000 +0x1000   <- v042_132000.bin"
log " 0x133000 +0x1000   <- v042_133000.bin"
log " 0x134000 +0x1000   <- v042_134000.bin"
log " 0x135000 +0x1000   <- v042_135000.bin"
log " 0x136000 +0x1000   <- v042_136000.bin"
log " 0x137000 +0x1000   <- v042_137000.bin"
log " 0x138000 +0x1000   <- v042_138000.bin"
log " 0x139000 +0x1000   <- v042_139000.bin"
log " 0x13A000 +0x1000   <- v042_13A000.bin"
log " 0x13B000 +0x1000   <- v042_13B000.bin"
log " 0x13C000 +0x1000   <- v042_13C000.bin"
log " 0x13D000 +0x1000   <- v042_13D000.bin"
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
ck_file v042_121000.bin 68e387f01aa6e98ccaa45ef33ace340049fc6b5c662ee031c05481335f458619
ck_file v042_126000.bin 9a1332383b4b92fbb7c85dd9422023b6533cf65e1dc463dadff7672bd4db7006
ck_file v042_127000.bin 1769ddc290989e25fe224f7d4b0332de3d7f5002edbeb0700f90141e9a3de600
ck_file v042_128000.bin 9c619940389eadf55e07c027d3b63fb00dc150ad798d49ba86822587c0a2813d
ck_file v042_12A000.bin 6203f49c248a4891bc4a034a286350da079c07f65a72449f797845b756d5bc86
ck_file v042_12B000.bin d5fd51005833137b9cd99f072ebb5699b90a0f2c4e85d0cbdeed440cc9f898eb
ck_file v042_12C000.bin 74c66fdccfc36aad610341e3ee0de4c829805bad4f353e09bca8a37dd2089512
ck_file v042_12D000.bin c2f0803e87f2519d91e23106874ab52b98388e7fb74b763d3c8d3b3baf388ae5
ck_file v042_12E000.bin 989c59233ece7cdf59fde1af68f9f33ae600be487ceab3e08bd9b8df2ca1149f
ck_file v042_12F000.bin 94cd3f3973619879d713651818c80911e57d33ab53f1d3369677505489879778
ck_file v042_130000.bin f1ba015f283fc081c41f422c5554eb8efa5d49084bde9a428d01cfffe6be0d4e
ck_file v042_131000.bin 996fe84660f3962f40131f7c2f2841ee19e31233cb753751cba8398e9a032031
ck_file v042_132000.bin e4b4b52687ad2b31593141e27d997ae31cf291a3da51b4f058540181947b57cd
ck_file v042_133000.bin e2ac50c43956ad206d67da291e58d80daea5f8909929c3ab3851053748edca82
ck_file v042_134000.bin 7210b822569cd80053ff6d0c51fed3e59469e503c519ca28ed075f6cd860a0e0
ck_file v042_135000.bin 30d3ffbb8e5760725d34cdabd2bb013878227d3f9e61fc0dcfedb8ded6692c10
ck_file v042_136000.bin 8ff5e9dc8d96564aaad2ad56a6a8e99d2d6ba4f1117b447aa72468954d214c31
ck_file v042_137000.bin c169e1f7ef13ba4fa53ce9329226afa8f829a037a1eab0f3b20677190423df05
ck_file v042_138000.bin 959f55983781c2b0a11fa80b7f36114be9da631af3eb71bf4f32feb77f1acbb2
ck_file v042_139000.bin db9b4c3917fbd7534858ab0cdc07e3b782a0d0fd32c893a68e2c1ca32ec37572
ck_file v042_13A000.bin 209445635397dca5d3e2ff78b80bfb98f7f2aa20a4ef9a5d36817301091c327f
ck_file v042_13B000.bin 48e67d459c807d5f072204e2009eef7d24a1b85221d9c51fff07cf942daefaef
ck_file v042_13C000.bin 76e61f3785a17206819ecef9abaf3c8be5887e341f4fa4aa9f6fe7437519ec78
ck_file v042_13D000.bin 58683ef08ff6e8c2544596c5c44073af8827edcfd4db0c8bd063dc88e4b10570
ck_file base_121000.bin 3c0b61d3ff10c2a9838873f743b9a198b13c904d560808efbba851fb98b335e3
ck_file base_126000.bin cc31a3d9cea495315d60f231c08705f2396ddd1eb70dcc962853aff1b346da35
ck_file base_127000.bin 0318cc59765edcc893008ee976b24ace551a27ce8b3212837f5d072f2f186b27
ck_file base_128000.bin 4393a597215fa98b88eaee6ef9855b6b12f9401d4e2e506029fa91b6c4450b6d
ck_file base_12A000.bin aa94827f67ae6f0c2b57f83c1806b79e7759329c4a975efd3ad7781621447dda
ck_file base_12B000.bin aa3358950b8cd2d6b8c65702c33d2efda29516144b3c69d7a0a74f770826b5cd
ck_file base_12C000.bin ccc11583d6490eebb0b292115bb32c139c984ef40d3d39286bd86c00c6fb0356
ck_file base_12D000.bin 84bf9e4e0c04ea9352d343e34e5603d64876e192d3556f5341bc970810f94c85
ck_file base_12E000.bin ad7c05b035cd4b48cefccd8cddf01d59b3de49bb0228c0dd847ba751cc6d92ae
ck_file base_12F000.bin 5252d4ac12cb5f879d331fa081a6ff2c1663cdb8849bf69fd1d65009ccb08c38
ck_file base_130000.bin 2a2d6c1641e5c2ca12fac749062fcfd45beb944fabeb3c8729de03b61e504b2d
ck_file base_131000.bin 93a71390d6fc97d25914e309237068a629084dd7ecece96a005469c1720e465c
ck_file base_132000.bin fa5a5bba47c3517b8aabda238496f2a9b0f407516f89d96f4f4fbf07f2203536
ck_file base_133000.bin 3cddc24926e15507b9e3592ee80616d7d38df8f9b7bf0fd3b6b4907aabef377c
ck_file base_134000.bin eb3d37a83e74423e0d1db56b0891c3889acee08ac9f501fc3067e6578fdb4826
ck_file base_135000.bin 4eecf7a661e1ca9f41a8b8d4b4fffe37cf4c9bd50091d245c22763092b12f78f
ck_file base_136000.bin 35ee889edf0de18419e8e3af91852f7527336250937affee022d5af8bd1e7594
ck_file base_137000.bin c53024a5371196563c6ba5b50a88d190b75f958523bb7aa893144560f5775558
ck_file base_138000.bin f236f6919146873d8ca237a7b699ff2f1db3c88690a9c5f25e5d3d97adeaa1d5
ck_file base_139000.bin c663ab140ea8f16b5eccd26b11317c931f23f339ca171ec133423871b4bf6cda
ck_file base_13A000.bin 0c3c38e2e72b5e1a45a5bed762bbda0700d7814f24a75fe8eb1a81b7c2374173
ck_file base_13B000.bin bab42fa2f1aa4db37450e353783a262129d0852f17d53f7f2c93c05de0d95ddb
ck_file base_13C000.bin bf4146959ee1417989cb85d2fc5f1573ba8a731e8d59e0ca04bfcbbbcf8ca8b2
ck_file base_13D000.bin 990c996fc6c868ad50ca5b3e09f60c4b7ae9f6ac7998e362e7d55b383091adf8

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
ck "FIRM" 57344 1647984 3f4119b2d6fb67e71ea2551ae95d2cb828cc4a96fdcecbebcabfa6225891efa8
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."

log ""
log "======================================================================"
log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."
log "   grava  : 96 KiB em 24 setores"
log "   muda   : Extras no padrao da home + separador some + linha 16px em todas as listas"
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
wr "4/6 1/24" 0x121000 v042_121000.bin 68e387f01aa6e98ccaa45ef33ace340049fc6b5c662ee031c05481335f458619
wr "4/6 2/24" 0x126000 v042_126000.bin 9a1332383b4b92fbb7c85dd9422023b6533cf65e1dc463dadff7672bd4db7006
wr "4/6 3/24" 0x127000 v042_127000.bin 1769ddc290989e25fe224f7d4b0332de3d7f5002edbeb0700f90141e9a3de600
wr "4/6 4/24" 0x128000 v042_128000.bin 9c619940389eadf55e07c027d3b63fb00dc150ad798d49ba86822587c0a2813d
wr "4/6 5/24" 0x12A000 v042_12A000.bin 6203f49c248a4891bc4a034a286350da079c07f65a72449f797845b756d5bc86
wr "4/6 6/24" 0x12B000 v042_12B000.bin d5fd51005833137b9cd99f072ebb5699b90a0f2c4e85d0cbdeed440cc9f898eb
wr "4/6 7/24" 0x12C000 v042_12C000.bin 74c66fdccfc36aad610341e3ee0de4c829805bad4f353e09bca8a37dd2089512
wr "4/6 8/24" 0x12D000 v042_12D000.bin c2f0803e87f2519d91e23106874ab52b98388e7fb74b763d3c8d3b3baf388ae5
wr "4/6 9/24" 0x12E000 v042_12E000.bin 989c59233ece7cdf59fde1af68f9f33ae600be487ceab3e08bd9b8df2ca1149f
wr "4/6 10/24" 0x12F000 v042_12F000.bin 94cd3f3973619879d713651818c80911e57d33ab53f1d3369677505489879778
wr "4/6 11/24" 0x130000 v042_130000.bin f1ba015f283fc081c41f422c5554eb8efa5d49084bde9a428d01cfffe6be0d4e
wr "4/6 12/24" 0x131000 v042_131000.bin 996fe84660f3962f40131f7c2f2841ee19e31233cb753751cba8398e9a032031
wr "4/6 13/24" 0x132000 v042_132000.bin e4b4b52687ad2b31593141e27d997ae31cf291a3da51b4f058540181947b57cd
wr "4/6 14/24" 0x133000 v042_133000.bin e2ac50c43956ad206d67da291e58d80daea5f8909929c3ab3851053748edca82
wr "4/6 15/24" 0x134000 v042_134000.bin 7210b822569cd80053ff6d0c51fed3e59469e503c519ca28ed075f6cd860a0e0
wr "4/6 16/24" 0x135000 v042_135000.bin 30d3ffbb8e5760725d34cdabd2bb013878227d3f9e61fc0dcfedb8ded6692c10
wr "4/6 17/24" 0x136000 v042_136000.bin 8ff5e9dc8d96564aaad2ad56a6a8e99d2d6ba4f1117b447aa72468954d214c31
wr "4/6 18/24" 0x137000 v042_137000.bin c169e1f7ef13ba4fa53ce9329226afa8f829a037a1eab0f3b20677190423df05
wr "4/6 19/24" 0x138000 v042_138000.bin 959f55983781c2b0a11fa80b7f36114be9da631af3eb71bf4f32feb77f1acbb2
wr "4/6 20/24" 0x139000 v042_139000.bin db9b4c3917fbd7534858ab0cdc07e3b782a0d0fd32c893a68e2c1ca32ec37572
wr "4/6 21/24" 0x13A000 v042_13A000.bin 209445635397dca5d3e2ff78b80bfb98f7f2aa20a4ef9a5d36817301091c327f
wr "4/6 22/24" 0x13B000 v042_13B000.bin 48e67d459c807d5f072204e2009eef7d24a1b85221d9c51fff07cf942daefaef
wr "4/6 23/24" 0x13C000 v042_13C000.bin 76e61f3785a17206819ecef9abaf3c8be5887e341f4fa4aa9f6fe7437519ec78
wr "4/6 24/24" 0x13D000 v042_13D000.bin 58683ef08ff6e8c2544596c5c44073af8827edcfd4db0c8bd063dc88e4b10570
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
ck2 "FIRM" 57344 1647984 2da296865c3848ba3dca1f5d427d6f5a022b3566d50f99d0dc22384dd2425fa7
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] RESULTADO: V042 GRAVADO E VERIFICADO"
    log ""
    log "   Desconecte e abra o menu principal."
else
    log " [6/6] RESULTADO: ALGUMA REGIAO NAO CONFERE"
    log ""
    log "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:"
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
log "  leve de volta: before.bin  after.bin  flash_v042.log"
log ""
