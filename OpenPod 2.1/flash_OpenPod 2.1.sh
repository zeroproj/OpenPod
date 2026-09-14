#!/bin/sh
# flash_OpenPod 2.1.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# Projeto Saturno: tema em tabela de 19 bytes + Extras corrigido
#
# Grava 32 setores de 4096 B (128 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_OpenPod 2.1.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
WORK=$(pwd)/openpod_flash_OpenPod 2.1
LOG="$WORK/flash_OpenPod 2.1.log"
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
        log "***   sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCE000 0 0x1000 base_CE000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x100000 0 0x1000 base_100000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x10C000 0 0x1000 base_10C000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x121000 0 0x1000 base_121000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x122000 0 0x1000 base_122000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x126000 0 0x1000 base_126000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x127000 0 0x1000 base_127000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x128000 0 0x1000 base_128000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x129000 0 0x1000 base_129000.bin"
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
log " OpenPod — gravacao do OPENPOD 2.1   (32 setores, 128 KiB)"
log " 0x1A3000 +0x1000   <- OpenPod 2.1_1A3000.bin"
log " 0x1A5000 +0x1000   <- OpenPod 2.1_1A5000.bin"
log " 0x10A000 +0x1000   <- OpenPod 2.1_10A000.bin"
log " 0x0CE000 +0x1000   <- OpenPod 2.1_CE000.bin"
log " 0x100000 +0x1000   <- OpenPod 2.1_100000.bin"
log " 0x10C000 +0x1000   <- OpenPod 2.1_10C000.bin"
log " 0x121000 +0x1000   <- OpenPod 2.1_121000.bin"
log " 0x122000 +0x1000   <- OpenPod 2.1_122000.bin"
log " 0x126000 +0x1000   <- OpenPod 2.1_126000.bin"
log " 0x127000 +0x1000   <- OpenPod 2.1_127000.bin"
log " 0x128000 +0x1000   <- OpenPod 2.1_128000.bin"
log " 0x129000 +0x1000   <- OpenPod 2.1_129000.bin"
log " 0x12A000 +0x1000   <- OpenPod 2.1_12A000.bin"
log " 0x12B000 +0x1000   <- OpenPod 2.1_12B000.bin"
log " 0x12C000 +0x1000   <- OpenPod 2.1_12C000.bin"
log " 0x12D000 +0x1000   <- OpenPod 2.1_12D000.bin"
log " 0x12E000 +0x1000   <- OpenPod 2.1_12E000.bin"
log " 0x12F000 +0x1000   <- OpenPod 2.1_12F000.bin"
log " 0x130000 +0x1000   <- OpenPod 2.1_130000.bin"
log " 0x131000 +0x1000   <- OpenPod 2.1_131000.bin"
log " 0x132000 +0x1000   <- OpenPod 2.1_132000.bin"
log " 0x133000 +0x1000   <- OpenPod 2.1_133000.bin"
log " 0x134000 +0x1000   <- OpenPod 2.1_134000.bin"
log " 0x135000 +0x1000   <- OpenPod 2.1_135000.bin"
log " 0x136000 +0x1000   <- OpenPod 2.1_136000.bin"
log " 0x137000 +0x1000   <- OpenPod 2.1_137000.bin"
log " 0x138000 +0x1000   <- OpenPod 2.1_138000.bin"
log " 0x139000 +0x1000   <- OpenPod 2.1_139000.bin"
log " 0x13A000 +0x1000   <- OpenPod 2.1_13A000.bin"
log " 0x13B000 +0x1000   <- OpenPod 2.1_13B000.bin"
log " 0x13C000 +0x1000   <- OpenPod 2.1_13C000.bin"
log " 0x13D000 +0x1000   <- OpenPod 2.1_13D000.bin"
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
ck_file OpenPod 2.1_1A3000.bin 00eed4690887e1836766f1a377b6c1ab498fe53bc724993fbb52b29de0066b11
ck_file OpenPod 2.1_1A5000.bin 70fb6649a93e8db83ed8b17cafbf3b35871cd99f5148ce09eaf7a8940629e9e0
ck_file OpenPod 2.1_10A000.bin c02dec62e6d0ed4d6e21fa62c1f3a5601db7c8b705bf6d73155b51b4e2a18bf3
ck_file OpenPod 2.1_CE000.bin 211e10b7d6b10a4fd70ede2918c1d73e403ea6f2a4f3a1e85e2945160d65db5a
ck_file OpenPod 2.1_100000.bin 63226b9148313aab9973cc7aa5d57d9f6d1de1aed334806353aca0f006502633
ck_file OpenPod 2.1_10C000.bin 4b9b828e702aa054c3b9c647ec16b6d59d1cf9df36e266e5f57a9dc9bf56de85
ck_file OpenPod 2.1_121000.bin c2fd2f15a09ff421b57c10457db7a60e389138f388e728678962c5a0d8159041
ck_file OpenPod 2.1_122000.bin 5b12b97a05e230b71ea589ea63d9e736101f9a93a6604ae5f2bbc25dd68d2fae
ck_file OpenPod 2.1_126000.bin c13d91cce3b9e786cf94c604102c41c9e1e555c1cdb358ce7f1c097b1c880cae
ck_file OpenPod 2.1_127000.bin 6a46aa011081d0882f8dd866eb387f083d2594e891e06bf037425eb8de865769
ck_file OpenPod 2.1_128000.bin d2386cbbf4ab49017050ee23c2fa0d170d627cd996d64898cda9e7c495a1044a
ck_file OpenPod 2.1_129000.bin e05b6c3408132f0c03e7dbd13612f9bde06f793a7c15bbcc592485d59cd37a32
ck_file OpenPod 2.1_12A000.bin fddb2b7a6e4cc8f255d74496d2fe9550db60573afcf51576a12b8b9b749e4a67
ck_file OpenPod 2.1_12B000.bin 495379969a054a47343a7ecd544b2b68f42769d6b6d4bb457d36267fa315b9ae
ck_file OpenPod 2.1_12C000.bin 7e5ef84b9bc08923c4d872f22c9b97ede606afb1cb6f731e218041940026441e
ck_file OpenPod 2.1_12D000.bin 32ebf046cae701d440a8f744e59a3467b57ba08e53f8305dc126625826c9063d
ck_file OpenPod 2.1_12E000.bin beb4db72db0e4fe34e0af92ca0cbff68c9fbc970a76b0c1ce6003cf6e21dcbe0
ck_file OpenPod 2.1_12F000.bin 53a3c56e8706513df2c2614dfcd7867a00d4904ee324f5b9312ea62326d6df42
ck_file OpenPod 2.1_130000.bin feca8a0b907c6fb3c0d931fdd6fac9a3c51762d675a740909852ea6d62d93b1d
ck_file OpenPod 2.1_131000.bin 1a29704d982ca3b2f834f43aff24371a813ca4ca8d087678a83141af1f64cc48
ck_file OpenPod 2.1_132000.bin 504644fe4cd41a835fd2fe065294241959f735a09b3f187b5ac0449d378379bd
ck_file OpenPod 2.1_133000.bin 5c8f607d4cb93092b6c579d0aaf206af944ce76d84bf827cd80ca42d30206d70
ck_file OpenPod 2.1_134000.bin fe7440e3fb7625c9487ef15d51989955023466d6b3026db2b0abe9e813595948
ck_file OpenPod 2.1_135000.bin 6d773591d468d5c86cd1a724a6de54deaf83f1cc476133813ad1e616b837958f
ck_file OpenPod 2.1_136000.bin cc786dbbd3e1d1135f2b79b3195a67dd71cd467cd3b944ef481d26c11bee6d5f
ck_file OpenPod 2.1_137000.bin 985c972e66f33653d63fb2e9e21c76cce714055e0b8fe4b1bbd57aa986d93d46
ck_file OpenPod 2.1_138000.bin c0031d339638593de65c3c19bca2a779adf334c0a3b90bbfa4cd897865e0eea7
ck_file OpenPod 2.1_139000.bin 0b271d8a4ab1b6680c6b02929930f848f3ff7633703994974cc4215bdf3f6cbc
ck_file OpenPod 2.1_13A000.bin 0e747214c91e91afea1be4450c9eee61e76592811438a443ee8ce7b09049a78e
ck_file OpenPod 2.1_13B000.bin 9512027059c35d602d37ec287cd8d2d4aabab71b4fe6837f78dc7fb110958442
ck_file OpenPod 2.1_13C000.bin 5999f66a0cbfee939b7a82134aa0efe643113b0af0f4aa9b64324f91ef1e30ed
ck_file OpenPod 2.1_13D000.bin 540171453f002a9a2443d4881db0e7f0770343b63ba57a4a8e868f5de94f3f21
ck_file base_1A3000.bin e4c75816c039dc648d8344f622b4ff8d6a0cbfdd5d6a215037fab0f3bed82837
ck_file base_1A5000.bin 007e6ebe35a4e2e2f4745626792db0c05b27bd62cf4f29ccdf1263f4f5a85a47
ck_file base_10A000.bin db44efbe6e65ec3d35ee9670f411f174a455174afddd49bce7bc4df8d32a5034
ck_file base_CE000.bin 719e073c97507d92824536e965b0b0377b1a8b951af3b90efbec4b567ccc8234
ck_file base_100000.bin 9235a8b222f535fb17acdf729fa7b2bab7dffb89deb37ec6e3fadc6d6e154892
ck_file base_10C000.bin da58ee1b07cc42893b98fb55a5248ac2ee4ee67a43b4bcd63b8651f25263441a
ck_file base_121000.bin d3885627432303167cc88f25fee677f5d720626a149e0deb5b77574ab8272490
ck_file base_122000.bin 168e1ea8100caad9c3456cf5ac895a431e4bac831e069b1b85f18a9acc0657d5
ck_file base_126000.bin 0435a61f8ba0cb26d6126c561ac7c2ce2bedea8b7bbbbba0bae62d35501799cd
ck_file base_127000.bin 5c81b5ae3a51fc2aa640301f27ead9e2a3da9a1675660c2b32c0f0bfe4e4f2a5
ck_file base_128000.bin 721c077d8f1a92eded8403c5c0e87648a991f34dc1f2daae5973791fbe188ec4
ck_file base_129000.bin c0b55f64c4bbd7536bb7ce506fa03a5fabb47335d80022d742be31791440d6d6
ck_file base_12A000.bin f142a6ac098e44618bb6ae13991006ea6134fe7ff15b0953a6339dc0a37d4f55
ck_file base_12B000.bin 8ce8ab07b06bc752e03ba32da841fe78b98a4d407ab0fa0e2c7cebf50b0d4b57
ck_file base_12C000.bin fc2fec034f5ddb1bacf7dfdaecf58ae3f07bdc01f3dcb03732618dd1dd7b5355
ck_file base_12D000.bin 44059e4d33be5a14b8e32deff0b663f575ed421fbe75f55a8afc59f8bcd81a83
ck_file base_12E000.bin 146424205cd63809e89bd7b10c78b90f5a7b732afb972b144b7380ced9cca2ef
ck_file base_12F000.bin 2159bede1ac246002b94fd5329daacb5f6deacad742c675c4c12c6dea0e52196
ck_file base_130000.bin 80e3059c19b337df03c3c470d73e8ed3cf67fb314f9616213cd1b7a4b3675837
ck_file base_131000.bin 05f990f4e511cea71a3bbcc4317d125f18a2fde26ce37223870c7cc120a1fdaf
ck_file base_132000.bin 90439556a858992f4e92f4198482e567a3ddd23d51cc8a7f4ca57a3f322a42aa
ck_file base_133000.bin 443e703b424e03c79c689ae1303b084ab8476c43f496abad7648f8b2ba65d8ed
ck_file base_134000.bin 1652a285a90556753cb6208876c57796f5bba2c6d31b4c50b07b38e90a6155cf
ck_file base_135000.bin 559d22b127f8e07a32db49f28752ef44d331a80bb939744e5a7a99f1c1322306
ck_file base_136000.bin 70bb0f6eeb358f691939c2bc70806b5a6d7951d5a5bfff5ceb3f81911813464c
ck_file base_137000.bin b50d972620d6f8a78380c2a04c528f1e5e50bf8639e94539f0cb39c7b061a614
ck_file base_138000.bin ef9bf3151e978142e5c6be8da977ba5e51763515f1016af8c21794a71eab9879
ck_file base_139000.bin 2db155b2344c822b0bd351bacf2f5067287b1aef080e53c73cab2184c1968d06
ck_file base_13A000.bin 9552dcdae61ccda6b92740f7b32a74e68cf88db5fa581711c6eb16f2a87f9643
ck_file base_13B000.bin 3b024e966649c0ae4bb25d817eb04e4568e93bb741fb1ade010a136aae036aa2
ck_file base_13C000.bin 23019da31eae49aa7872c342cbc4093a723681dae473d8eb7b392811e482b4d6
ck_file base_13D000.bin 456a1f25f81683a8099da921793eae67f4ac0b823f869048e833ebe4f529a666

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
ck "FIRM" 57344 1647984 5aad5ee92a49f2551091ccca69e8c36e68b55914dc798c7b36902d8d380e73e7
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."

log ""
log "======================================================================"
log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."
log "   grava  : 128 KiB em 32 setores"
log "   muda   : Projeto Saturno: tema em tabela de 19 bytes + Extras corrigido"
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
wr "4/6 1/32" 0x1A3000 OpenPod 2.1_1A3000.bin 00eed4690887e1836766f1a377b6c1ab498fe53bc724993fbb52b29de0066b11
wr "4/6 2/32" 0x1A5000 OpenPod 2.1_1A5000.bin 70fb6649a93e8db83ed8b17cafbf3b35871cd99f5148ce09eaf7a8940629e9e0
wr "4/6 3/32" 0x10A000 OpenPod 2.1_10A000.bin c02dec62e6d0ed4d6e21fa62c1f3a5601db7c8b705bf6d73155b51b4e2a18bf3
wr "4/6 4/32" 0xCE000 OpenPod 2.1_CE000.bin 211e10b7d6b10a4fd70ede2918c1d73e403ea6f2a4f3a1e85e2945160d65db5a
wr "4/6 5/32" 0x100000 OpenPod 2.1_100000.bin 63226b9148313aab9973cc7aa5d57d9f6d1de1aed334806353aca0f006502633
wr "4/6 6/32" 0x10C000 OpenPod 2.1_10C000.bin 4b9b828e702aa054c3b9c647ec16b6d59d1cf9df36e266e5f57a9dc9bf56de85
wr "4/6 7/32" 0x121000 OpenPod 2.1_121000.bin c2fd2f15a09ff421b57c10457db7a60e389138f388e728678962c5a0d8159041
wr "4/6 8/32" 0x122000 OpenPod 2.1_122000.bin 5b12b97a05e230b71ea589ea63d9e736101f9a93a6604ae5f2bbc25dd68d2fae
wr "4/6 9/32" 0x126000 OpenPod 2.1_126000.bin c13d91cce3b9e786cf94c604102c41c9e1e555c1cdb358ce7f1c097b1c880cae
wr "4/6 10/32" 0x127000 OpenPod 2.1_127000.bin 6a46aa011081d0882f8dd866eb387f083d2594e891e06bf037425eb8de865769
wr "4/6 11/32" 0x128000 OpenPod 2.1_128000.bin d2386cbbf4ab49017050ee23c2fa0d170d627cd996d64898cda9e7c495a1044a
wr "4/6 12/32" 0x129000 OpenPod 2.1_129000.bin e05b6c3408132f0c03e7dbd13612f9bde06f793a7c15bbcc592485d59cd37a32
wr "4/6 13/32" 0x12A000 OpenPod 2.1_12A000.bin fddb2b7a6e4cc8f255d74496d2fe9550db60573afcf51576a12b8b9b749e4a67
wr "4/6 14/32" 0x12B000 OpenPod 2.1_12B000.bin 495379969a054a47343a7ecd544b2b68f42769d6b6d4bb457d36267fa315b9ae
wr "4/6 15/32" 0x12C000 OpenPod 2.1_12C000.bin 7e5ef84b9bc08923c4d872f22c9b97ede606afb1cb6f731e218041940026441e
wr "4/6 16/32" 0x12D000 OpenPod 2.1_12D000.bin 32ebf046cae701d440a8f744e59a3467b57ba08e53f8305dc126625826c9063d
wr "4/6 17/32" 0x12E000 OpenPod 2.1_12E000.bin beb4db72db0e4fe34e0af92ca0cbff68c9fbc970a76b0c1ce6003cf6e21dcbe0
wr "4/6 18/32" 0x12F000 OpenPod 2.1_12F000.bin 53a3c56e8706513df2c2614dfcd7867a00d4904ee324f5b9312ea62326d6df42
wr "4/6 19/32" 0x130000 OpenPod 2.1_130000.bin feca8a0b907c6fb3c0d931fdd6fac9a3c51762d675a740909852ea6d62d93b1d
wr "4/6 20/32" 0x131000 OpenPod 2.1_131000.bin 1a29704d982ca3b2f834f43aff24371a813ca4ca8d087678a83141af1f64cc48
wr "4/6 21/32" 0x132000 OpenPod 2.1_132000.bin 504644fe4cd41a835fd2fe065294241959f735a09b3f187b5ac0449d378379bd
wr "4/6 22/32" 0x133000 OpenPod 2.1_133000.bin 5c8f607d4cb93092b6c579d0aaf206af944ce76d84bf827cd80ca42d30206d70
wr "4/6 23/32" 0x134000 OpenPod 2.1_134000.bin fe7440e3fb7625c9487ef15d51989955023466d6b3026db2b0abe9e813595948
wr "4/6 24/32" 0x135000 OpenPod 2.1_135000.bin 6d773591d468d5c86cd1a724a6de54deaf83f1cc476133813ad1e616b837958f
wr "4/6 25/32" 0x136000 OpenPod 2.1_136000.bin cc786dbbd3e1d1135f2b79b3195a67dd71cd467cd3b944ef481d26c11bee6d5f
wr "4/6 26/32" 0x137000 OpenPod 2.1_137000.bin 985c972e66f33653d63fb2e9e21c76cce714055e0b8fe4b1bbd57aa986d93d46
wr "4/6 27/32" 0x138000 OpenPod 2.1_138000.bin c0031d339638593de65c3c19bca2a779adf334c0a3b90bbfa4cd897865e0eea7
wr "4/6 28/32" 0x139000 OpenPod 2.1_139000.bin 0b271d8a4ab1b6680c6b02929930f848f3ff7633703994974cc4215bdf3f6cbc
wr "4/6 29/32" 0x13A000 OpenPod 2.1_13A000.bin 0e747214c91e91afea1be4450c9eee61e76592811438a443ee8ce7b09049a78e
wr "4/6 30/32" 0x13B000 OpenPod 2.1_13B000.bin 9512027059c35d602d37ec287cd8d2d4aabab71b4fe6837f78dc7fb110958442
wr "4/6 31/32" 0x13C000 OpenPod 2.1_13C000.bin 5999f66a0cbfee939b7a82134aa0efe643113b0af0f4aa9b64324f91ef1e30ed
wr "4/6 32/32" 0x13D000 OpenPod 2.1_13D000.bin 540171453f002a9a2443d4881db0e7f0770343b63ba57a4a8e868f5de94f3f21
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
ck2 "FIRM" 57344 1647984 da5fd1ac48f0cf6af78ee46a412092fd11fceb004515ccda96e4d8d9674822b7
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] RESULTADO: OPENPOD 2.1 GRAVADO E VERIFICADO"
    log ""
    log "   Desconecte e abra o menu principal."
else
    log " [6/6] RESULTADO: ALGUMA REGIAO NAO CONFERE"
    log ""
    log "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:"
    log "     sudo $TOOL --id $DEV write_flash 0x1A3000 0 0x1000 base_1A3000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A5000 0 0x1000 base_1A5000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCE000 0 0x1000 base_CE000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x100000 0 0x1000 base_100000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x10C000 0 0x1000 base_10C000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x121000 0 0x1000 base_121000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x122000 0 0x1000 base_122000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x126000 0 0x1000 base_126000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x127000 0 0x1000 base_127000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x128000 0 0x1000 base_128000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x129000 0 0x1000 base_129000.bin"
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
log "  leve de volta: before.bin  after.bin  flash_OpenPod 2.1.log"
log ""
