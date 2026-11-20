#!/bin/sh
# flash_OpenPod_OpenPodReload3.3.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# OpenPod OpenPod Reload 3.3
#
# Grava 33 setores de 4096 B (132 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_OpenPod_OpenPodReload3.3.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
VERSAO="OpenPod_OpenPodReload3.3"
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
        log "***   sudo $TOOL --id $DEV write_flash 0x48000 0 0x1000 base_48000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x53000 0 0x1000 base_53000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xC7000 0 0x1000 base_C7000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCC000 0 0x1000 base_CC000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCD000 0 0x1000 base_CD000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCE000 0 0x1000 base_CE000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCF000 0 0x1000 base_CF000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD0000 0 0x1000 base_D0000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD1000 0 0x1000 base_D1000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD2000 0 0x1000 base_D2000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD3000 0 0x1000 base_D3000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xFF000 0 0x1000 base_FF000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x101000 0 0x1000 base_101000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x109000 0 0x1000 base_109000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x121000 0 0x1000 base_121000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x122000 0 0x1000 base_122000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x123000 0 0x1000 base_123000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x12E000 0 0x1000 base_12E000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x131000 0 0x1000 base_131000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x132000 0 0x1000 base_132000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x156000 0 0x1000 base_156000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A3000 0 0x1000 base_1A3000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A4000 0 0x1000 base_1A4000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A5000 0 0x1000 base_1A5000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A6000 0 0x1000 base_1A6000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A7000 0 0x1000 base_1A7000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A8000 0 0x1000 base_1A8000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A9000 0 0x1000 base_1A9000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1AA000 0 0x1000 base_1AA000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1AB000 0 0x1000 base_1AB000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1AC000 0 0x1000 base_1AC000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1AD000 0 0x1000 base_1AD000.bin"
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
log " OpenPod — gravacao do OPENPOD_OPENPODRELOAD3.3   (33 setores, 132 KiB)"
log " 0x048000 +0x1000   <- OpenPod_OpenPodReload3.3_48000.bin"
log " 0x053000 +0x1000   <- OpenPod_OpenPodReload3.3_53000.bin"
log " 0x0C7000 +0x1000   <- OpenPod_OpenPodReload3.3_C7000.bin"
log " 0x0CC000 +0x1000   <- OpenPod_OpenPodReload3.3_CC000.bin"
log " 0x0CD000 +0x1000   <- OpenPod_OpenPodReload3.3_CD000.bin"
log " 0x0CE000 +0x1000   <- OpenPod_OpenPodReload3.3_CE000.bin"
log " 0x0CF000 +0x1000   <- OpenPod_OpenPodReload3.3_CF000.bin"
log " 0x0D0000 +0x1000   <- OpenPod_OpenPodReload3.3_D0000.bin"
log " 0x0D1000 +0x1000   <- OpenPod_OpenPodReload3.3_D1000.bin"
log " 0x0D2000 +0x1000   <- OpenPod_OpenPodReload3.3_D2000.bin"
log " 0x0D3000 +0x1000   <- OpenPod_OpenPodReload3.3_D3000.bin"
log " 0x0FF000 +0x1000   <- OpenPod_OpenPodReload3.3_FF000.bin"
log " 0x101000 +0x1000   <- OpenPod_OpenPodReload3.3_101000.bin"
log " 0x109000 +0x1000   <- OpenPod_OpenPodReload3.3_109000.bin"
log " 0x10A000 +0x1000   <- OpenPod_OpenPodReload3.3_10A000.bin"
log " 0x121000 +0x1000   <- OpenPod_OpenPodReload3.3_121000.bin"
log " 0x122000 +0x1000   <- OpenPod_OpenPodReload3.3_122000.bin"
log " 0x123000 +0x1000   <- OpenPod_OpenPodReload3.3_123000.bin"
log " 0x12E000 +0x1000   <- OpenPod_OpenPodReload3.3_12E000.bin"
log " 0x131000 +0x1000   <- OpenPod_OpenPodReload3.3_131000.bin"
log " 0x132000 +0x1000   <- OpenPod_OpenPodReload3.3_132000.bin"
log " 0x156000 +0x1000   <- OpenPod_OpenPodReload3.3_156000.bin"
log " 0x1A3000 +0x1000   <- OpenPod_OpenPodReload3.3_1A3000.bin"
log " 0x1A4000 +0x1000   <- OpenPod_OpenPodReload3.3_1A4000.bin"
log " 0x1A5000 +0x1000   <- OpenPod_OpenPodReload3.3_1A5000.bin"
log " 0x1A6000 +0x1000   <- OpenPod_OpenPodReload3.3_1A6000.bin"
log " 0x1A7000 +0x1000   <- OpenPod_OpenPodReload3.3_1A7000.bin"
log " 0x1A8000 +0x1000   <- OpenPod_OpenPodReload3.3_1A8000.bin"
log " 0x1A9000 +0x1000   <- OpenPod_OpenPodReload3.3_1A9000.bin"
log " 0x1AA000 +0x1000   <- OpenPod_OpenPodReload3.3_1AA000.bin"
log " 0x1AB000 +0x1000   <- OpenPod_OpenPodReload3.3_1AB000.bin"
log " 0x1AC000 +0x1000   <- OpenPod_OpenPodReload3.3_1AC000.bin"
log " 0x1AD000 +0x1000   <- OpenPod_OpenPodReload3.3_1AD000.bin"
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
ck_file "OpenPod_OpenPodReload3.3_48000.bin" fd8f9e331e445088937a9f40e59ce4d8ea9d59c6757d70b115ad4e8dd51fffa6
ck_file "OpenPod_OpenPodReload3.3_53000.bin" 375f0cd07c44dbdcce0851620088623eb65d3838b25cd03b2726df5e5433a4de
ck_file "OpenPod_OpenPodReload3.3_C7000.bin" f678974cafcb27f9b636e9713360e6f34a9d03f1b6082f3de9897e1513f3a421
ck_file "OpenPod_OpenPodReload3.3_CC000.bin" ef8ffb2966867c44f8a87315ad7469a97018d0b7367ce864c19ffa102a8ba165
ck_file "OpenPod_OpenPodReload3.3_CD000.bin" c477c23325168a978ac0225164135302abf9a266c603ed6cbb57ae0e19189e9f
ck_file "OpenPod_OpenPodReload3.3_CE000.bin" 2a2c829ab51bccc16be92686e727c28a8d9d29a2e22374fcefa05fb0435813c7
ck_file "OpenPod_OpenPodReload3.3_CF000.bin" 8880fba8f255f760bcdc1d04f5ad98f370694338c0668f225defbb76b64e45f2
ck_file "OpenPod_OpenPodReload3.3_D0000.bin" 67ea86fd40cadc01c2cda19ec76a57d0168a198cbd55a6e8b382104e51c2d768
ck_file "OpenPod_OpenPodReload3.3_D1000.bin" 94b1fef151d582cbcb001c44a18d2101c3139e2efe71e55a023a21e5edf0e7b3
ck_file "OpenPod_OpenPodReload3.3_D2000.bin" 7a72f47b203da13bb231c4c392ec1da0cdd6f7cfb841cf103c278a5adf0e9189
ck_file "OpenPod_OpenPodReload3.3_D3000.bin" 9e242a69a939a614a750587d1e62df82126d0068ab6b6a72d76deca52a0639b3
ck_file "OpenPod_OpenPodReload3.3_FF000.bin" 2b44bef648c5f8fcc08072cc529a8002cf37b11c3ce5ce8e88e1b2a24ed6d820
ck_file "OpenPod_OpenPodReload3.3_101000.bin" 7e7bdfe6068f95cf1bf978177ec38a835301bb738405e423ad573aefee634bc7
ck_file "OpenPod_OpenPodReload3.3_109000.bin" 3bc16bacee418a50f79df0aa7c3f5604241fc55f126ee8d7bec7d802849312c2
ck_file "OpenPod_OpenPodReload3.3_10A000.bin" 8c35d232644fbcec0e57519558b61e1d3f0a7b0d269bbadde0c4eae6ba5316d3
ck_file "OpenPod_OpenPodReload3.3_121000.bin" ba21f47d4ae0797174245e1bd9fb837afdfd8619184d01b4d1553116e3daed1e
ck_file "OpenPod_OpenPodReload3.3_122000.bin" f1a868b530c26ea9b1c55b95e453cd32d6d8c97101f944ba367273c1beb214fe
ck_file "OpenPod_OpenPodReload3.3_123000.bin" a6e8c5fb593aafc7d57ba4de6505466b270b39aafb422c932d1c81c708b201b0
ck_file "OpenPod_OpenPodReload3.3_12E000.bin" 9fa129ccd988f4c2a6a962867782b42305e82bc5610b8111f312b5779d9297cb
ck_file "OpenPod_OpenPodReload3.3_131000.bin" 030d3b7bce7cd133207ce440fc1dc7f3137bdab0cc62e4fe7a1a746434ff579e
ck_file "OpenPod_OpenPodReload3.3_132000.bin" c85d831ba2bc0abb2457d1ef1a294cfa01e4b5cf063c1499fbf54b3865e6cc7a
ck_file "OpenPod_OpenPodReload3.3_156000.bin" 09ea275aa3916096700af353b3a9b51b3f51ab9fcad3a8ee616a504bae18d60d
ck_file "OpenPod_OpenPodReload3.3_1A3000.bin" af75be67379e86296b217b520d2ef959fcfaff0bbe6aae9f712e4422452ab683
ck_file "OpenPod_OpenPodReload3.3_1A4000.bin" aba33a55c863920bfccdaab7a93a9bd2bdbddf110fa55e28ac75cd66018993d1
ck_file "OpenPod_OpenPodReload3.3_1A5000.bin" 635b023a309245579152502c2e06268e963f0f2158bcd6f41838bf3d9d81760c
ck_file "OpenPod_OpenPodReload3.3_1A6000.bin" 25d6784a3323dc277f51e9bcff59c53121c11c743f2be8e68cc398f1921c4dcc
ck_file "OpenPod_OpenPodReload3.3_1A7000.bin" 142b9638e43a185341ae27973131aa4bc2cf998c5d16defb8852bd1ba5fe0b02
ck_file "OpenPod_OpenPodReload3.3_1A8000.bin" 380953cff47806c257df31a7599300111b386cbc098fd69c42e16001448d0544
ck_file "OpenPod_OpenPodReload3.3_1A9000.bin" 5153d4d74d7f85164aa63adfebcc3e37e858724cd29f5862ea42b685c6850342
ck_file "OpenPod_OpenPodReload3.3_1AA000.bin" efdc442aa6c94dd991991d17159ee09108fd5da22d69b2903c927345ec13f3d1
ck_file "OpenPod_OpenPodReload3.3_1AB000.bin" f822d7424f404331f9c581988419629bb000eb86930b14b6dd4ea64895813d48
ck_file "OpenPod_OpenPodReload3.3_1AC000.bin" 3333e5abb265bdde9248ada0ca3afbd007100bac551325de0ce0252a60f83564
ck_file "OpenPod_OpenPodReload3.3_1AD000.bin" a9793232801c6e5e4a0c37b3c46aee6307ab2eef4696b7fe5bbde847f449729b
ck_file "base_48000.bin" cd43df9cf6f193ab32cd4c0963555f95e95e7ecb02b836bc720c2d1873dcbc01
ck_file "base_53000.bin" 5decc107dd674f7b6bdd34436f9a7e9b68900c61a7552df7a24be1f7f85bf4c5
ck_file "base_C7000.bin" ae29fc778567f832164a237fd2f523dd6eedb4eefad4c7d843676d63931039b4
ck_file "base_CC000.bin" 83597203bed419cc2f76f1b8c942194d07a4b23c34f67e2e7834864361dd6688
ck_file "base_CD000.bin" ab039386aa645f414a0580730cc4b62ca7831c9d4d8dff7b01c80f9b7be16f5f
ck_file "base_CE000.bin" f46bdf8b56e3b463e8461ea5b35bfae201cafda178ac8296a5c2d8bc19cbf175
ck_file "base_CF000.bin" cb87b8bb4828c63b87c36788f17d54049cf1b4c21e5757e0204a5e693fecf683
ck_file "base_D0000.bin" 0d7deca9d471b627b9eaede3872d233da2b9b643006476fe654f3d504713a8cf
ck_file "base_D1000.bin" 0d7ab5dc9d9ad6d369103ebd1db42c77e31d4969bece99fdb25943bd1df1db41
ck_file "base_D2000.bin" a0e9f30c578c5f06f9d0428b53eb181e1097ad5a6342f3837e4f6646c0a1f3fe
ck_file "base_D3000.bin" b53d3f48030da1ab150ad3d52b4a21771ce6ae766d1750d589fa4d811a12fe3b
ck_file "base_FF000.bin" f4cce2c7eb1bab2ded6433ce9f925810f29c4d62778c1a2c744d6a6afc5683fd
ck_file "base_101000.bin" 3fc82037a6ed598d4004f1aa2f4c44b9534bf10433fe70f8c31af85bbd190a1d
ck_file "base_109000.bin" 40e5a7786b3a7c82c786da0effb5036c6da0c234462dfaa5c435581cf5f03411
ck_file "base_10A000.bin" ad962e28861a9a9914ef70e26cfc50283fa51daee636051a4907db930839dd6a
ck_file "base_121000.bin" dbea2b9d18646cad64d3a5ea402a2a633bb0c4036fca689ad997ecb2545ba9ac
ck_file "base_122000.bin" dc3b6a4a0150763564474047400cebac7b4e331820901505eacf3644083c7c48
ck_file "base_123000.bin" fdd9e6ef0752425d429d354bc74652402039880f251c0a390b42b60c087a5805
ck_file "base_12E000.bin" e135e686ad0de20f085fc204494b51873731b520ad24930487896b63b29109cc
ck_file "base_131000.bin" 93a71390d6fc97d25914e309237068a629084dd7ecece96a005469c1720e465c
ck_file "base_132000.bin" fa5a5bba47c3517b8aabda238496f2a9b0f407516f89d96f4f4fbf07f2203536
ck_file "base_156000.bin" b1791e9f5e5a62402d93ada9f3174129843ed8af22b7d23904d5cd472e9b43c5
ck_file "base_1A3000.bin" 6f4ef0b382a9fa4d2792e8446613308544b251e2d512ea1b5d3b83ce8f1d10e4
ck_file "base_1A4000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6
ck_file "base_1A5000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6
ck_file "base_1A6000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6
ck_file "base_1A7000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6
ck_file "base_1A8000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6
ck_file "base_1A9000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6
ck_file "base_1AA000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6
ck_file "base_1AB000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6
ck_file "base_1AC000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6
ck_file "base_1AD000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6

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
ck "FIRM" 57344 1647984 e2a7b86339030b94268dac7d562a167613a3e769c866790353b4921cad85dbdc
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."

log ""
log "======================================================================"
log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."
log "   grava  : 132 KiB em 33 setores"
log "   muda   : OpenPod OpenPod Reload 3.3"
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
wr "4/6 1/33" 0x48000 "OpenPod_OpenPodReload3.3_48000.bin" fd8f9e331e445088937a9f40e59ce4d8ea9d59c6757d70b115ad4e8dd51fffa6
wr "4/6 2/33" 0x53000 "OpenPod_OpenPodReload3.3_53000.bin" 375f0cd07c44dbdcce0851620088623eb65d3838b25cd03b2726df5e5433a4de
wr "4/6 3/33" 0xC7000 "OpenPod_OpenPodReload3.3_C7000.bin" f678974cafcb27f9b636e9713360e6f34a9d03f1b6082f3de9897e1513f3a421
wr "4/6 4/33" 0xCC000 "OpenPod_OpenPodReload3.3_CC000.bin" ef8ffb2966867c44f8a87315ad7469a97018d0b7367ce864c19ffa102a8ba165
wr "4/6 5/33" 0xCD000 "OpenPod_OpenPodReload3.3_CD000.bin" c477c23325168a978ac0225164135302abf9a266c603ed6cbb57ae0e19189e9f
wr "4/6 6/33" 0xCE000 "OpenPod_OpenPodReload3.3_CE000.bin" 2a2c829ab51bccc16be92686e727c28a8d9d29a2e22374fcefa05fb0435813c7
wr "4/6 7/33" 0xCF000 "OpenPod_OpenPodReload3.3_CF000.bin" 8880fba8f255f760bcdc1d04f5ad98f370694338c0668f225defbb76b64e45f2
wr "4/6 8/33" 0xD0000 "OpenPod_OpenPodReload3.3_D0000.bin" 67ea86fd40cadc01c2cda19ec76a57d0168a198cbd55a6e8b382104e51c2d768
wr "4/6 9/33" 0xD1000 "OpenPod_OpenPodReload3.3_D1000.bin" 94b1fef151d582cbcb001c44a18d2101c3139e2efe71e55a023a21e5edf0e7b3
wr "4/6 10/33" 0xD2000 "OpenPod_OpenPodReload3.3_D2000.bin" 7a72f47b203da13bb231c4c392ec1da0cdd6f7cfb841cf103c278a5adf0e9189
wr "4/6 11/33" 0xD3000 "OpenPod_OpenPodReload3.3_D3000.bin" 9e242a69a939a614a750587d1e62df82126d0068ab6b6a72d76deca52a0639b3
wr "4/6 12/33" 0xFF000 "OpenPod_OpenPodReload3.3_FF000.bin" 2b44bef648c5f8fcc08072cc529a8002cf37b11c3ce5ce8e88e1b2a24ed6d820
wr "4/6 13/33" 0x101000 "OpenPod_OpenPodReload3.3_101000.bin" 7e7bdfe6068f95cf1bf978177ec38a835301bb738405e423ad573aefee634bc7
wr "4/6 14/33" 0x109000 "OpenPod_OpenPodReload3.3_109000.bin" 3bc16bacee418a50f79df0aa7c3f5604241fc55f126ee8d7bec7d802849312c2
wr "4/6 15/33" 0x10A000 "OpenPod_OpenPodReload3.3_10A000.bin" 8c35d232644fbcec0e57519558b61e1d3f0a7b0d269bbadde0c4eae6ba5316d3
wr "4/6 16/33" 0x121000 "OpenPod_OpenPodReload3.3_121000.bin" ba21f47d4ae0797174245e1bd9fb837afdfd8619184d01b4d1553116e3daed1e
wr "4/6 17/33" 0x122000 "OpenPod_OpenPodReload3.3_122000.bin" f1a868b530c26ea9b1c55b95e453cd32d6d8c97101f944ba367273c1beb214fe
wr "4/6 18/33" 0x123000 "OpenPod_OpenPodReload3.3_123000.bin" a6e8c5fb593aafc7d57ba4de6505466b270b39aafb422c932d1c81c708b201b0
wr "4/6 19/33" 0x12E000 "OpenPod_OpenPodReload3.3_12E000.bin" 9fa129ccd988f4c2a6a962867782b42305e82bc5610b8111f312b5779d9297cb
wr "4/6 20/33" 0x131000 "OpenPod_OpenPodReload3.3_131000.bin" 030d3b7bce7cd133207ce440fc1dc7f3137bdab0cc62e4fe7a1a746434ff579e
wr "4/6 21/33" 0x132000 "OpenPod_OpenPodReload3.3_132000.bin" c85d831ba2bc0abb2457d1ef1a294cfa01e4b5cf063c1499fbf54b3865e6cc7a
wr "4/6 22/33" 0x156000 "OpenPod_OpenPodReload3.3_156000.bin" 09ea275aa3916096700af353b3a9b51b3f51ab9fcad3a8ee616a504bae18d60d
wr "4/6 23/33" 0x1A3000 "OpenPod_OpenPodReload3.3_1A3000.bin" af75be67379e86296b217b520d2ef959fcfaff0bbe6aae9f712e4422452ab683
wr "4/6 24/33" 0x1A4000 "OpenPod_OpenPodReload3.3_1A4000.bin" aba33a55c863920bfccdaab7a93a9bd2bdbddf110fa55e28ac75cd66018993d1
wr "4/6 25/33" 0x1A5000 "OpenPod_OpenPodReload3.3_1A5000.bin" 635b023a309245579152502c2e06268e963f0f2158bcd6f41838bf3d9d81760c
wr "4/6 26/33" 0x1A6000 "OpenPod_OpenPodReload3.3_1A6000.bin" 25d6784a3323dc277f51e9bcff59c53121c11c743f2be8e68cc398f1921c4dcc
wr "4/6 27/33" 0x1A7000 "OpenPod_OpenPodReload3.3_1A7000.bin" 142b9638e43a185341ae27973131aa4bc2cf998c5d16defb8852bd1ba5fe0b02
wr "4/6 28/33" 0x1A8000 "OpenPod_OpenPodReload3.3_1A8000.bin" 380953cff47806c257df31a7599300111b386cbc098fd69c42e16001448d0544
wr "4/6 29/33" 0x1A9000 "OpenPod_OpenPodReload3.3_1A9000.bin" 5153d4d74d7f85164aa63adfebcc3e37e858724cd29f5862ea42b685c6850342
wr "4/6 30/33" 0x1AA000 "OpenPod_OpenPodReload3.3_1AA000.bin" efdc442aa6c94dd991991d17159ee09108fd5da22d69b2903c927345ec13f3d1
wr "4/6 31/33" 0x1AB000 "OpenPod_OpenPodReload3.3_1AB000.bin" f822d7424f404331f9c581988419629bb000eb86930b14b6dd4ea64895813d48
wr "4/6 32/33" 0x1AC000 "OpenPod_OpenPodReload3.3_1AC000.bin" 3333e5abb265bdde9248ada0ca3afbd007100bac551325de0ce0252a60f83564
wr "4/6 33/33" 0x1AD000 "OpenPod_OpenPodReload3.3_1AD000.bin" a9793232801c6e5e4a0c37b3c46aee6307ab2eef4696b7fe5bbde847f449729b
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
ck2 "FIRM" 57344 1647984 7e1732035a5a48d742d3f11e1cdae267cbb41dbda872331570761c75ea308561
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] RESULTADO: OPENPOD_OPENPODRELOAD3.3 GRAVADO E VERIFICADO"
    log ""
    log "   Desconecte e abra o menu principal."
else
    log " [6/6] RESULTADO: ALGUMA REGIAO NAO CONFERE"
    log ""
    log "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:"
    log "     sudo $TOOL --id $DEV write_flash 0x48000 0 0x1000 base_48000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x53000 0 0x1000 base_53000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xC7000 0 0x1000 base_C7000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCC000 0 0x1000 base_CC000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCD000 0 0x1000 base_CD000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCE000 0 0x1000 base_CE000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCF000 0 0x1000 base_CF000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD0000 0 0x1000 base_D0000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD1000 0 0x1000 base_D1000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD2000 0 0x1000 base_D2000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD3000 0 0x1000 base_D3000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xFF000 0 0x1000 base_FF000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x101000 0 0x1000 base_101000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x109000 0 0x1000 base_109000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x121000 0 0x1000 base_121000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x122000 0 0x1000 base_122000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x123000 0 0x1000 base_123000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x12E000 0 0x1000 base_12E000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x131000 0 0x1000 base_131000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x132000 0 0x1000 base_132000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x156000 0 0x1000 base_156000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A3000 0 0x1000 base_1A3000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A4000 0 0x1000 base_1A4000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A5000 0 0x1000 base_1A5000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A6000 0 0x1000 base_1A6000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A7000 0 0x1000 base_1A7000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A8000 0 0x1000 base_1A8000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A9000 0 0x1000 base_1A9000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1AA000 0 0x1000 base_1AA000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1AB000 0 0x1000 base_1AB000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1AC000 0 0x1000 base_1AC000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1AD000 0 0x1000 base_1AD000.bin"
fi
log "======================================================================"
log ""
log "  leve de volta: before.bin  after.bin  flash_$VERSAO.log"
log ""
