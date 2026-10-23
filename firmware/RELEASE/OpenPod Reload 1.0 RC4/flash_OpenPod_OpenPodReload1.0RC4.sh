#!/bin/sh
# flash_OpenPod_OpenPodReload1.0RC4.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# OpenPod OpenPod Reload 1.0 RC4
#
# Grava 18 setores de 4096 B (72 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_OpenPod_OpenPodReload1.0RC4.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
VERSAO="OpenPod_OpenPodReload1.0RC4"
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
        log "***   sudo $TOOL --id $DEV write_flash 0x109000 0 0x1000 base_109000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x121000 0 0x1000 base_121000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x122000 0 0x1000 base_122000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x156000 0 0x1000 base_156000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A3000 0 0x1000 base_1A3000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A4000 0 0x1000 base_1A4000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A7000 0 0x1000 base_1A7000.bin"
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
log " OpenPod — gravacao do OPENPOD_OPENPODRELOAD1.0RC4   (18 setores, 72 KiB)"
log " 0x053000 +0x1000   <- OpenPod_OpenPodReload1.0RC4_53000.bin"
log " 0x0C7000 +0x1000   <- OpenPod_OpenPodReload1.0RC4_C7000.bin"
log " 0x0CC000 +0x1000   <- OpenPod_OpenPodReload1.0RC4_CC000.bin"
log " 0x0CD000 +0x1000   <- OpenPod_OpenPodReload1.0RC4_CD000.bin"
log " 0x0CE000 +0x1000   <- OpenPod_OpenPodReload1.0RC4_CE000.bin"
log " 0x0CF000 +0x1000   <- OpenPod_OpenPodReload1.0RC4_CF000.bin"
log " 0x0D0000 +0x1000   <- OpenPod_OpenPodReload1.0RC4_D0000.bin"
log " 0x0D1000 +0x1000   <- OpenPod_OpenPodReload1.0RC4_D1000.bin"
log " 0x0D2000 +0x1000   <- OpenPod_OpenPodReload1.0RC4_D2000.bin"
log " 0x0D3000 +0x1000   <- OpenPod_OpenPodReload1.0RC4_D3000.bin"
log " 0x109000 +0x1000   <- OpenPod_OpenPodReload1.0RC4_109000.bin"
log " 0x10A000 +0x1000   <- OpenPod_OpenPodReload1.0RC4_10A000.bin"
log " 0x121000 +0x1000   <- OpenPod_OpenPodReload1.0RC4_121000.bin"
log " 0x122000 +0x1000   <- OpenPod_OpenPodReload1.0RC4_122000.bin"
log " 0x156000 +0x1000   <- OpenPod_OpenPodReload1.0RC4_156000.bin"
log " 0x1A3000 +0x1000   <- OpenPod_OpenPodReload1.0RC4_1A3000.bin"
log " 0x1A4000 +0x1000   <- OpenPod_OpenPodReload1.0RC4_1A4000.bin"
log " 0x1A7000 +0x1000   <- OpenPod_OpenPodReload1.0RC4_1A7000.bin"
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
ck_file "OpenPod_OpenPodReload1.0RC4_53000.bin" 322f7017f57626346d4940d0ed8c9d524ef7403e4bb1adbb4965626d4d561f1f
ck_file "OpenPod_OpenPodReload1.0RC4_C7000.bin" f678974cafcb27f9b636e9713360e6f34a9d03f1b6082f3de9897e1513f3a421
ck_file "OpenPod_OpenPodReload1.0RC4_CC000.bin" ef8ffb2966867c44f8a87315ad7469a97018d0b7367ce864c19ffa102a8ba165
ck_file "OpenPod_OpenPodReload1.0RC4_CD000.bin" d0c5465d70e6235fa28a635d78a052866a4cb88715d490652196225e4dd9d463
ck_file "OpenPod_OpenPodReload1.0RC4_CE000.bin" 16dac6b0c7ee7314cdd5ccea581d0d6e9fde9fca0a2552d8f0d36921aba8e745
ck_file "OpenPod_OpenPodReload1.0RC4_CF000.bin" 6d7653f4aea678bc17f4cbb5d30cb78740d1c121517da4bad53e51db3acd5b40
ck_file "OpenPod_OpenPodReload1.0RC4_D0000.bin" 5b0926f99b564db888ce8e36a75ddae8af5b1725c620f8575cba9360d56e3bdb
ck_file "OpenPod_OpenPodReload1.0RC4_D1000.bin" 827eefce3301bcf892e0d58fa63965ad746b39a474b7f7374db88da1edfc21d5
ck_file "OpenPod_OpenPodReload1.0RC4_D2000.bin" 5972cb3a09438449a8dbe2d02f9593c708f4e09ca00302773b409af5a8b71a56
ck_file "OpenPod_OpenPodReload1.0RC4_D3000.bin" 9e242a69a939a614a750587d1e62df82126d0068ab6b6a72d76deca52a0639b3
ck_file "OpenPod_OpenPodReload1.0RC4_109000.bin" 3bc16bacee418a50f79df0aa7c3f5604241fc55f126ee8d7bec7d802849312c2
ck_file "OpenPod_OpenPodReload1.0RC4_10A000.bin" 8c35d232644fbcec0e57519558b61e1d3f0a7b0d269bbadde0c4eae6ba5316d3
ck_file "OpenPod_OpenPodReload1.0RC4_121000.bin" ba21f47d4ae0797174245e1bd9fb837afdfd8619184d01b4d1553116e3daed1e
ck_file "OpenPod_OpenPodReload1.0RC4_122000.bin" f1a868b530c26ea9b1c55b95e453cd32d6d8c97101f944ba367273c1beb214fe
ck_file "OpenPod_OpenPodReload1.0RC4_156000.bin" 09ea275aa3916096700af353b3a9b51b3f51ab9fcad3a8ee616a504bae18d60d
ck_file "OpenPod_OpenPodReload1.0RC4_1A3000.bin" af75be67379e86296b217b520d2ef959fcfaff0bbe6aae9f712e4422452ab683
ck_file "OpenPod_OpenPodReload1.0RC4_1A4000.bin" ee29c5be9f9e3eeaa288d9a5616f7592de0fd53904953c87359a5b885b89a1b0
ck_file "OpenPod_OpenPodReload1.0RC4_1A7000.bin" 142b9638e43a185341ae27973131aa4bc2cf998c5d16defb8852bd1ba5fe0b02
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
ck_file "base_109000.bin" 40e5a7786b3a7c82c786da0effb5036c6da0c234462dfaa5c435581cf5f03411
ck_file "base_10A000.bin" ad962e28861a9a9914ef70e26cfc50283fa51daee636051a4907db930839dd6a
ck_file "base_121000.bin" dbea2b9d18646cad64d3a5ea402a2a633bb0c4036fca689ad997ecb2545ba9ac
ck_file "base_122000.bin" dc3b6a4a0150763564474047400cebac7b4e331820901505eacf3644083c7c48
ck_file "base_156000.bin" b1791e9f5e5a62402d93ada9f3174129843ed8af22b7d23904d5cd472e9b43c5
ck_file "base_1A3000.bin" 6f4ef0b382a9fa4d2792e8446613308544b251e2d512ea1b5d3b83ce8f1d10e4
ck_file "base_1A4000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6
ck_file "base_1A7000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6

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
log "   grava  : 72 KiB em 18 setores"
log "   muda   : OpenPod OpenPod Reload 1.0 RC4"
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
wr "4/6 1/18" 0x53000 "OpenPod_OpenPodReload1.0RC4_53000.bin" 322f7017f57626346d4940d0ed8c9d524ef7403e4bb1adbb4965626d4d561f1f
wr "4/6 2/18" 0xC7000 "OpenPod_OpenPodReload1.0RC4_C7000.bin" f678974cafcb27f9b636e9713360e6f34a9d03f1b6082f3de9897e1513f3a421
wr "4/6 3/18" 0xCC000 "OpenPod_OpenPodReload1.0RC4_CC000.bin" ef8ffb2966867c44f8a87315ad7469a97018d0b7367ce864c19ffa102a8ba165
wr "4/6 4/18" 0xCD000 "OpenPod_OpenPodReload1.0RC4_CD000.bin" d0c5465d70e6235fa28a635d78a052866a4cb88715d490652196225e4dd9d463
wr "4/6 5/18" 0xCE000 "OpenPod_OpenPodReload1.0RC4_CE000.bin" 16dac6b0c7ee7314cdd5ccea581d0d6e9fde9fca0a2552d8f0d36921aba8e745
wr "4/6 6/18" 0xCF000 "OpenPod_OpenPodReload1.0RC4_CF000.bin" 6d7653f4aea678bc17f4cbb5d30cb78740d1c121517da4bad53e51db3acd5b40
wr "4/6 7/18" 0xD0000 "OpenPod_OpenPodReload1.0RC4_D0000.bin" 5b0926f99b564db888ce8e36a75ddae8af5b1725c620f8575cba9360d56e3bdb
wr "4/6 8/18" 0xD1000 "OpenPod_OpenPodReload1.0RC4_D1000.bin" 827eefce3301bcf892e0d58fa63965ad746b39a474b7f7374db88da1edfc21d5
wr "4/6 9/18" 0xD2000 "OpenPod_OpenPodReload1.0RC4_D2000.bin" 5972cb3a09438449a8dbe2d02f9593c708f4e09ca00302773b409af5a8b71a56
wr "4/6 10/18" 0xD3000 "OpenPod_OpenPodReload1.0RC4_D3000.bin" 9e242a69a939a614a750587d1e62df82126d0068ab6b6a72d76deca52a0639b3
wr "4/6 11/18" 0x109000 "OpenPod_OpenPodReload1.0RC4_109000.bin" 3bc16bacee418a50f79df0aa7c3f5604241fc55f126ee8d7bec7d802849312c2
wr "4/6 12/18" 0x10A000 "OpenPod_OpenPodReload1.0RC4_10A000.bin" 8c35d232644fbcec0e57519558b61e1d3f0a7b0d269bbadde0c4eae6ba5316d3
wr "4/6 13/18" 0x121000 "OpenPod_OpenPodReload1.0RC4_121000.bin" ba21f47d4ae0797174245e1bd9fb837afdfd8619184d01b4d1553116e3daed1e
wr "4/6 14/18" 0x122000 "OpenPod_OpenPodReload1.0RC4_122000.bin" f1a868b530c26ea9b1c55b95e453cd32d6d8c97101f944ba367273c1beb214fe
wr "4/6 15/18" 0x156000 "OpenPod_OpenPodReload1.0RC4_156000.bin" 09ea275aa3916096700af353b3a9b51b3f51ab9fcad3a8ee616a504bae18d60d
wr "4/6 16/18" 0x1A3000 "OpenPod_OpenPodReload1.0RC4_1A3000.bin" af75be67379e86296b217b520d2ef959fcfaff0bbe6aae9f712e4422452ab683
wr "4/6 17/18" 0x1A4000 "OpenPod_OpenPodReload1.0RC4_1A4000.bin" ee29c5be9f9e3eeaa288d9a5616f7592de0fd53904953c87359a5b885b89a1b0
wr "4/6 18/18" 0x1A7000 "OpenPod_OpenPodReload1.0RC4_1A7000.bin" 142b9638e43a185341ae27973131aa4bc2cf998c5d16defb8852bd1ba5fe0b02
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
ck2 "FIRM" 57344 1647984 f3a78bd5b25ee1cb5e499a832dd0c5160c9d567a2d0d03704dffb6893d425dab
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] RESULTADO: OPENPOD_OPENPODRELOAD1.0RC4 GRAVADO E VERIFICADO"
    log ""
    log "   Desconecte e abra o menu principal."
else
    log " [6/6] RESULTADO: ALGUMA REGIAO NAO CONFERE"
    log ""
    log "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:"
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
    log "     sudo $TOOL --id $DEV write_flash 0x109000 0 0x1000 base_109000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x121000 0 0x1000 base_121000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x122000 0 0x1000 base_122000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x156000 0 0x1000 base_156000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A3000 0 0x1000 base_1A3000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A4000 0 0x1000 base_1A4000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A7000 0 0x1000 base_1A7000.bin"
fi
log "======================================================================"
log ""
log "  leve de volta: before.bin  after.bin  flash_$VERSAO.log"
log ""
