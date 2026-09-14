#!/bin/sh
# flash_OpenPod_1.0.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# OpenPod 1.0
#
# Grava 8 setores de 4096 B (32 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_OpenPod_1.0.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
WORK=$(pwd)/openpod_flash_OpenPod_1.0
LOG="$WORK/flash_OpenPod_1.0.log"
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
        log "***   sudo $TOOL --id $DEV write_flash 0x48000 0 0x1000 base_48000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCE000 0 0x1000 base_CE000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCF000 0 0x1000 base_CF000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD0000 0 0x1000 base_D0000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x109000 0 0x1000 base_109000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
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
log " OpenPod — gravacao do OPENPOD_1.0   (8 setores, 32 KiB)"
log " 0x1A3000 +0x1000   <- OpenPod_1.0_1A3000.bin"
log " 0x048000 +0x1000   <- OpenPod_1.0_48000.bin"
log " 0x0CE000 +0x1000   <- OpenPod_1.0_CE000.bin"
log " 0x0CF000 +0x1000   <- OpenPod_1.0_CF000.bin"
log " 0x0D0000 +0x1000   <- OpenPod_1.0_D0000.bin"
log " 0x109000 +0x1000   <- OpenPod_1.0_109000.bin"
log " 0x10A000 +0x1000   <- OpenPod_1.0_10A000.bin"
log " 0x12E000 +0x1000   <- OpenPod_1.0_12E000.bin"
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
ck_file OpenPod_1.0_1A3000.bin 68cabdd203a64b29ba84096be53ef17e5eaa3ea0471516efda03483ff2194784
ck_file OpenPod_1.0_48000.bin de2dcc3d2e9dce53f640f23edc030dc04910a562e6e60a981af1342988df9233
ck_file OpenPod_1.0_CE000.bin 719e073c97507d92824536e965b0b0377b1a8b951af3b90efbec4b567ccc8234
ck_file OpenPod_1.0_CF000.bin 3431383721510cf1c211de027cf958c183e16db5fabb6b230eb284c85e196aa9
ck_file OpenPod_1.0_D0000.bin 3431383721510cf1c211de027cf958c183e16db5fabb6b230eb284c85e196aa9
ck_file OpenPod_1.0_109000.bin ff601736e89cac9a992ea699080030b13ed05c9d32e072ec8088d575133cfbce
ck_file OpenPod_1.0_10A000.bin b3a62ac8945aa089e9fcd8c63cc76a38804e21cc78e48e3c123ed0ecb82513f2
ck_file OpenPod_1.0_12E000.bin 2e9ebe303f47f437476087d65046002259696940dea07591c9e5af21f042e863
ck_file base_1A3000.bin cb28783690b8a9b7421160db7f67f6f36e9084b8afe4085cb54abc41f0c3c80d
ck_file base_48000.bin 0a1b511164cb6db2fd8a33e97fb8a5af0bedc383a92072e64c9a444578248294
ck_file base_CE000.bin 89b2779769649cec6878f09032af14b1148073fe7e4f4de5b2055a685b820a45
ck_file base_CF000.bin 444a33b06a3f04df497f9697a00856292e761d758029f9c33e981586b8fccef8
ck_file base_D0000.bin 9c0b0b4382c9bd79daa6b0085bcdfeef1a97736c65853e70a00f24012f9b883f
ck_file base_109000.bin 40e5a7786b3a7c82c786da0effb5036c6da0c234462dfaa5c435581cf5f03411
ck_file base_10A000.bin ad962e28861a9a9914ef70e26cfc50283fa51daee636051a4907db930839dd6a
ck_file base_12E000.bin 989c59233ece7cdf59fde1af68f9f33ae600be487ceab3e08bd9b8df2ca1149f

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
ck "FIRM" 57344 1647984 2da296865c3848ba3dca1f5d427d6f5a022b3566d50f99d0dc22384dd2425fa7
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."

log ""
log "======================================================================"
log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."
log "   grava  : 32 KiB em 8 setores"
log "   muda   : OpenPod 1.0"
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
wr "4/6 1/8" 0x1A3000 OpenPod_1.0_1A3000.bin 68cabdd203a64b29ba84096be53ef17e5eaa3ea0471516efda03483ff2194784
wr "4/6 2/8" 0x48000 OpenPod_1.0_48000.bin de2dcc3d2e9dce53f640f23edc030dc04910a562e6e60a981af1342988df9233
wr "4/6 3/8" 0xCE000 OpenPod_1.0_CE000.bin 719e073c97507d92824536e965b0b0377b1a8b951af3b90efbec4b567ccc8234
wr "4/6 4/8" 0xCF000 OpenPod_1.0_CF000.bin 3431383721510cf1c211de027cf958c183e16db5fabb6b230eb284c85e196aa9
wr "4/6 5/8" 0xD0000 OpenPod_1.0_D0000.bin 3431383721510cf1c211de027cf958c183e16db5fabb6b230eb284c85e196aa9
wr "4/6 6/8" 0x109000 OpenPod_1.0_109000.bin ff601736e89cac9a992ea699080030b13ed05c9d32e072ec8088d575133cfbce
wr "4/6 7/8" 0x10A000 OpenPod_1.0_10A000.bin b3a62ac8945aa089e9fcd8c63cc76a38804e21cc78e48e3c123ed0ecb82513f2
wr "4/6 8/8" 0x12E000 OpenPod_1.0_12E000.bin 2e9ebe303f47f437476087d65046002259696940dea07591c9e5af21f042e863
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
ck2 "FIRM" 57344 1647984 3f262fd4d865b23a33d6cf498d733f9e3309bc8929fc51bac7575b710680f3cc
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] RESULTADO: OPENPOD_1.0 GRAVADO E VERIFICADO"
    log ""
    log "   Desconecte e abra o menu principal."
else
    log " [6/6] RESULTADO: ALGUMA REGIAO NAO CONFERE"
    log ""
    log "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:"
    log "     sudo $TOOL --id $DEV write_flash 0x1A3000 0 0x1000 base_1A3000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x48000 0 0x1000 base_48000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCE000 0 0x1000 base_CE000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCF000 0 0x1000 base_CF000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD0000 0 0x1000 base_D0000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x109000 0 0x1000 base_109000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x12E000 0 0x1000 base_12E000.bin"
fi
log "======================================================================"
log ""
log "  leve de volta: before.bin  after.bin  flash_OpenPod_1.0.log"
log ""
