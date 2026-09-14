#!/bin/sh
# flash_OpenPod 2.2.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# Altura de linha unica (S11), fundo lendo o campo de fundo (S12) e a rota do Extras consertada.
#
# Grava 25 setores de 4096 B (100 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_OpenPod 2.2.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
WORK=$(pwd)/openpod_flash_OpenPod 2.2
LOG="$WORK/flash_OpenPod 2.2.log"
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
        log "***   sudo $TOOL --id $DEV write_flash 0x122000 0 0x1000 base_122000.bin"
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
log " OpenPod — gravacao do OPENPOD 2.2   (25 setores, 100 KiB)"
log " 0x1A5000 +0x1000   <- OpenPod 2.2_1A5000.bin"
log " 0x10A000 +0x1000   <- OpenPod 2.2_10A000.bin"
log " 0x122000 +0x1000   <- OpenPod 2.2_122000.bin"
log " 0x126000 +0x1000   <- OpenPod 2.2_126000.bin"
log " 0x127000 +0x1000   <- OpenPod 2.2_127000.bin"
log " 0x128000 +0x1000   <- OpenPod 2.2_128000.bin"
log " 0x12A000 +0x1000   <- OpenPod 2.2_12A000.bin"
log " 0x12B000 +0x1000   <- OpenPod 2.2_12B000.bin"
log " 0x12C000 +0x1000   <- OpenPod 2.2_12C000.bin"
log " 0x12D000 +0x1000   <- OpenPod 2.2_12D000.bin"
log " 0x12E000 +0x1000   <- OpenPod 2.2_12E000.bin"
log " 0x12F000 +0x1000   <- OpenPod 2.2_12F000.bin"
log " 0x130000 +0x1000   <- OpenPod 2.2_130000.bin"
log " 0x131000 +0x1000   <- OpenPod 2.2_131000.bin"
log " 0x132000 +0x1000   <- OpenPod 2.2_132000.bin"
log " 0x133000 +0x1000   <- OpenPod 2.2_133000.bin"
log " 0x134000 +0x1000   <- OpenPod 2.2_134000.bin"
log " 0x135000 +0x1000   <- OpenPod 2.2_135000.bin"
log " 0x136000 +0x1000   <- OpenPod 2.2_136000.bin"
log " 0x137000 +0x1000   <- OpenPod 2.2_137000.bin"
log " 0x139000 +0x1000   <- OpenPod 2.2_139000.bin"
log " 0x13A000 +0x1000   <- OpenPod 2.2_13A000.bin"
log " 0x13B000 +0x1000   <- OpenPod 2.2_13B000.bin"
log " 0x13C000 +0x1000   <- OpenPod 2.2_13C000.bin"
log " 0x13D000 +0x1000   <- OpenPod 2.2_13D000.bin"
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
ck_file OpenPod 2.2_1A5000.bin 38ceb7870b6a1bfea341f8f26dfa4bb17f1a33059ac5e6baf39c598433ecfc5e
ck_file OpenPod 2.2_10A000.bin ea98b618b0412ef07110f5378bcc464a62e520a1aa3b20d095152f75dd5ef99c
ck_file OpenPod 2.2_122000.bin ecc414142349e473ca449f7722013b854fce447fa4a54b66d1156920b8854073
ck_file OpenPod 2.2_126000.bin 80d189dcbe6ed4797d0570ebd5e5c6d528488c258125c747c8ce76ad59acbf4e
ck_file OpenPod 2.2_127000.bin 32048d5c9adb41fb576c68f9846faa2ce805644c8658a349bf9bb01d4c975cae
ck_file OpenPod 2.2_128000.bin b02754c1999e8bce6c7ebb011d70b04b3f0e85805db4f7b3a5ddc884b55f0266
ck_file OpenPod 2.2_12A000.bin 60beee015ac46dda2163b9b73a9fed9ea93a8df5ba2e2180e30149f5125e8b2d
ck_file OpenPod 2.2_12B000.bin 976f9ac7ee3f02f0e526c7874c1d511e08cf686f36c3a2d6a1eeaad3a86102f7
ck_file OpenPod 2.2_12C000.bin a4051be71072af683b25cdbfd12b5ed79c2186f81a72b4d4072f67937bb1b7c7
ck_file OpenPod 2.2_12D000.bin 690b60926f8854a28e009a1771e6d52e304fb2d96959edc88c96595546a0a468
ck_file OpenPod 2.2_12E000.bin 93e940efa132f349eb62361da36d47563ab75cd1d4c6782a99c8d548b29b967c
ck_file OpenPod 2.2_12F000.bin b5997b80ec127987906c06d3b31faf44cf6e0f6ac6f7f592743388a1a6b4d453
ck_file OpenPod 2.2_130000.bin ce3474e7d59595b49dcd64fdf0a9f897c471c93af58c82bc503ab4cb4654e6de
ck_file OpenPod 2.2_131000.bin 0b1bb722152cfcf0fb5d08f37f0abcc9d38d306d72bd1f53489ea87c9b3460e0
ck_file OpenPod 2.2_132000.bin b37153ad80bbc3c076e1310dfc2deeaf24a115431d1c5eef757925a0f1575b44
ck_file OpenPod 2.2_133000.bin d53a37d1926fd24e3cbaf0124dbea1e66c7ce4ad5a213f8e5a039efbdc3d8389
ck_file OpenPod 2.2_134000.bin 9910fa6d08f40619c40324271bc6c8d5e153ca64a0bfc156df4f34601f8ee675
ck_file OpenPod 2.2_135000.bin 6d7bd35f0f7beef8b79fad15c488d64737eb82ba465fe1ab6e579c70e4bccaaa
ck_file OpenPod 2.2_136000.bin 30d2cf00ebee109fc079f32d9f6d9a112a4885aaab1247930ad2432e6652aa4b
ck_file OpenPod 2.2_137000.bin 91b55bbae89ee0b8e2edf1dcbc2d437f5d08dca6fc9722a34f60fe2471cbac2e
ck_file OpenPod 2.2_139000.bin c23d8bfc8d03dfdd582184a95ac31dda8aafce5aeb2a1aa3dbd4c61423322c47
ck_file OpenPod 2.2_13A000.bin faa9a1d21f8394273be46be1aed9655660e471d781e4c59ae836fdbfc5ddc55e
ck_file OpenPod 2.2_13B000.bin 94ff5fd537ee6cb9a0ee8235405a47061c08b56df21203c92f0c9a5ed6440747
ck_file OpenPod 2.2_13C000.bin 7631b497f3271b42cb29371253c653bca3ce00e26a1c249d47ca4cf3cc6c0992
ck_file OpenPod 2.2_13D000.bin 2b88bab656e9a64840f6d78e822e6ff887882845c0e0f6b368fdc9e7654a90ac
ck_file base_1A5000.bin 70fb6649a93e8db83ed8b17cafbf3b35871cd99f5148ce09eaf7a8940629e9e0
ck_file base_10A000.bin c02dec62e6d0ed4d6e21fa62c1f3a5601db7c8b705bf6d73155b51b4e2a18bf3
ck_file base_122000.bin 5b12b97a05e230b71ea589ea63d9e736101f9a93a6604ae5f2bbc25dd68d2fae
ck_file base_126000.bin c13d91cce3b9e786cf94c604102c41c9e1e555c1cdb358ce7f1c097b1c880cae
ck_file base_127000.bin 6a46aa011081d0882f8dd866eb387f083d2594e891e06bf037425eb8de865769
ck_file base_128000.bin d2386cbbf4ab49017050ee23c2fa0d170d627cd996d64898cda9e7c495a1044a
ck_file base_12A000.bin fddb2b7a6e4cc8f255d74496d2fe9550db60573afcf51576a12b8b9b749e4a67
ck_file base_12B000.bin 495379969a054a47343a7ecd544b2b68f42769d6b6d4bb457d36267fa315b9ae
ck_file base_12C000.bin 7e5ef84b9bc08923c4d872f22c9b97ede606afb1cb6f731e218041940026441e
ck_file base_12D000.bin 32ebf046cae701d440a8f744e59a3467b57ba08e53f8305dc126625826c9063d
ck_file base_12E000.bin beb4db72db0e4fe34e0af92ca0cbff68c9fbc970a76b0c1ce6003cf6e21dcbe0
ck_file base_12F000.bin 53a3c56e8706513df2c2614dfcd7867a00d4904ee324f5b9312ea62326d6df42
ck_file base_130000.bin feca8a0b907c6fb3c0d931fdd6fac9a3c51762d675a740909852ea6d62d93b1d
ck_file base_131000.bin 1a29704d982ca3b2f834f43aff24371a813ca4ca8d087678a83141af1f64cc48
ck_file base_132000.bin 504644fe4cd41a835fd2fe065294241959f735a09b3f187b5ac0449d378379bd
ck_file base_133000.bin 5c8f607d4cb93092b6c579d0aaf206af944ce76d84bf827cd80ca42d30206d70
ck_file base_134000.bin fe7440e3fb7625c9487ef15d51989955023466d6b3026db2b0abe9e813595948
ck_file base_135000.bin 6d773591d468d5c86cd1a724a6de54deaf83f1cc476133813ad1e616b837958f
ck_file base_136000.bin cc786dbbd3e1d1135f2b79b3195a67dd71cd467cd3b944ef481d26c11bee6d5f
ck_file base_137000.bin 985c972e66f33653d63fb2e9e21c76cce714055e0b8fe4b1bbd57aa986d93d46
ck_file base_139000.bin 0b271d8a4ab1b6680c6b02929930f848f3ff7633703994974cc4215bdf3f6cbc
ck_file base_13A000.bin 0e747214c91e91afea1be4450c9eee61e76592811438a443ee8ce7b09049a78e
ck_file base_13B000.bin 9512027059c35d602d37ec287cd8d2d4aabab71b4fe6837f78dc7fb110958442
ck_file base_13C000.bin 5999f66a0cbfee939b7a82134aa0efe643113b0af0f4aa9b64324f91ef1e30ed
ck_file base_13D000.bin 540171453f002a9a2443d4881db0e7f0770343b63ba57a4a8e868f5de94f3f21

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
ck "FIRM" 57344 1647984 da5fd1ac48f0cf6af78ee46a412092fd11fceb004515ccda96e4d8d9674822b7
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."

log ""
log "======================================================================"
log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."
log "   grava  : 100 KiB em 25 setores"
log "   muda   : Altura de linha unica (S11), fundo lendo o campo de fundo (S12) e a rota do Extras consertada."
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
wr "4/6 1/25" 0x1A5000 OpenPod 2.2_1A5000.bin 38ceb7870b6a1bfea341f8f26dfa4bb17f1a33059ac5e6baf39c598433ecfc5e
wr "4/6 2/25" 0x10A000 OpenPod 2.2_10A000.bin ea98b618b0412ef07110f5378bcc464a62e520a1aa3b20d095152f75dd5ef99c
wr "4/6 3/25" 0x122000 OpenPod 2.2_122000.bin ecc414142349e473ca449f7722013b854fce447fa4a54b66d1156920b8854073
wr "4/6 4/25" 0x126000 OpenPod 2.2_126000.bin 80d189dcbe6ed4797d0570ebd5e5c6d528488c258125c747c8ce76ad59acbf4e
wr "4/6 5/25" 0x127000 OpenPod 2.2_127000.bin 32048d5c9adb41fb576c68f9846faa2ce805644c8658a349bf9bb01d4c975cae
wr "4/6 6/25" 0x128000 OpenPod 2.2_128000.bin b02754c1999e8bce6c7ebb011d70b04b3f0e85805db4f7b3a5ddc884b55f0266
wr "4/6 7/25" 0x12A000 OpenPod 2.2_12A000.bin 60beee015ac46dda2163b9b73a9fed9ea93a8df5ba2e2180e30149f5125e8b2d
wr "4/6 8/25" 0x12B000 OpenPod 2.2_12B000.bin 976f9ac7ee3f02f0e526c7874c1d511e08cf686f36c3a2d6a1eeaad3a86102f7
wr "4/6 9/25" 0x12C000 OpenPod 2.2_12C000.bin a4051be71072af683b25cdbfd12b5ed79c2186f81a72b4d4072f67937bb1b7c7
wr "4/6 10/25" 0x12D000 OpenPod 2.2_12D000.bin 690b60926f8854a28e009a1771e6d52e304fb2d96959edc88c96595546a0a468
wr "4/6 11/25" 0x12E000 OpenPod 2.2_12E000.bin 93e940efa132f349eb62361da36d47563ab75cd1d4c6782a99c8d548b29b967c
wr "4/6 12/25" 0x12F000 OpenPod 2.2_12F000.bin b5997b80ec127987906c06d3b31faf44cf6e0f6ac6f7f592743388a1a6b4d453
wr "4/6 13/25" 0x130000 OpenPod 2.2_130000.bin ce3474e7d59595b49dcd64fdf0a9f897c471c93af58c82bc503ab4cb4654e6de
wr "4/6 14/25" 0x131000 OpenPod 2.2_131000.bin 0b1bb722152cfcf0fb5d08f37f0abcc9d38d306d72bd1f53489ea87c9b3460e0
wr "4/6 15/25" 0x132000 OpenPod 2.2_132000.bin b37153ad80bbc3c076e1310dfc2deeaf24a115431d1c5eef757925a0f1575b44
wr "4/6 16/25" 0x133000 OpenPod 2.2_133000.bin d53a37d1926fd24e3cbaf0124dbea1e66c7ce4ad5a213f8e5a039efbdc3d8389
wr "4/6 17/25" 0x134000 OpenPod 2.2_134000.bin 9910fa6d08f40619c40324271bc6c8d5e153ca64a0bfc156df4f34601f8ee675
wr "4/6 18/25" 0x135000 OpenPod 2.2_135000.bin 6d7bd35f0f7beef8b79fad15c488d64737eb82ba465fe1ab6e579c70e4bccaaa
wr "4/6 19/25" 0x136000 OpenPod 2.2_136000.bin 30d2cf00ebee109fc079f32d9f6d9a112a4885aaab1247930ad2432e6652aa4b
wr "4/6 20/25" 0x137000 OpenPod 2.2_137000.bin 91b55bbae89ee0b8e2edf1dcbc2d437f5d08dca6fc9722a34f60fe2471cbac2e
wr "4/6 21/25" 0x139000 OpenPod 2.2_139000.bin c23d8bfc8d03dfdd582184a95ac31dda8aafce5aeb2a1aa3dbd4c61423322c47
wr "4/6 22/25" 0x13A000 OpenPod 2.2_13A000.bin faa9a1d21f8394273be46be1aed9655660e471d781e4c59ae836fdbfc5ddc55e
wr "4/6 23/25" 0x13B000 OpenPod 2.2_13B000.bin 94ff5fd537ee6cb9a0ee8235405a47061c08b56df21203c92f0c9a5ed6440747
wr "4/6 24/25" 0x13C000 OpenPod 2.2_13C000.bin 7631b497f3271b42cb29371253c653bca3ce00e26a1c249d47ca4cf3cc6c0992
wr "4/6 25/25" 0x13D000 OpenPod 2.2_13D000.bin 2b88bab656e9a64840f6d78e822e6ff887882845c0e0f6b368fdc9e7654a90ac
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
ck2 "FIRM" 57344 1647984 3369b8d766cbc4c85485d5455b2183fa3366e92e1e5c3ae562219da6672dc743
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] RESULTADO: OPENPOD 2.2 GRAVADO E VERIFICADO"
    log ""
    log "   Desconecte e abra o menu principal."
else
    log " [6/6] RESULTADO: ALGUMA REGIAO NAO CONFERE"
    log ""
    log "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:"
    log "     sudo $TOOL --id $DEV write_flash 0x1A5000 0 0x1000 base_1A5000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x122000 0 0x1000 base_122000.bin"
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
    log "     sudo $TOOL --id $DEV write_flash 0x139000 0 0x1000 base_139000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x13A000 0 0x1000 base_13A000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x13B000 0 0x1000 base_13B000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x13C000 0 0x1000 base_13C000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x13D000 0 0x1000 base_13D000.bin"
fi
log "======================================================================"
log ""
log "  leve de volta: before.bin  after.bin  flash_OpenPod 2.2.log"
log ""
