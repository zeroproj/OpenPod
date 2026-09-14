#!/bin/sh
# flash_v014.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# menu principal em lista vertical estilo iPod nano 2G: 9 linhas, texto a esquerda, chevron a direita
#
# Grava 8 setores de 4096 B (32 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_v014.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
WORK=$(pwd)/openpod_flash_v014
LOG="$WORK/flash_v014.log"
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
        log "***   sudo $TOOL --id $DEV write_flash 0xCE000 0 0x1000 base_CE000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCF000 0 0x1000 base_CF000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD0000 0 0x1000 base_D0000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD1000 0 0x1000 base_D1000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD2000 0 0x1000 base_D2000.bin"
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
log " OpenPod — gravacao do V014   (8 setores, 32 KiB)"
log " 0x00D000 +0x1000   <- v014_D000.bin"
log " 0x048000 +0x1000   <- v014_48000.bin"
log " 0x0CE000 +0x1000   <- v014_CE000.bin"
log " 0x0CF000 +0x1000   <- v014_CF000.bin"
log " 0x0D0000 +0x1000   <- v014_D0000.bin"
log " 0x0D1000 +0x1000   <- v014_D1000.bin"
log " 0x0D2000 +0x1000   <- v014_D2000.bin"
log " 0x12E000 +0x1000   <- v014_12E000.bin"
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
ck_file v014_D000.bin cf32c556a6f0f309cbe2bea33d761396f738243c9da52aebf8e2163aed3ec4f6
ck_file v014_48000.bin c4ca393ec94be6d45325d8e77b890d94ef5c61284ac5692d2b071566cb5499dd
ck_file v014_CE000.bin 6b08a80091ba655392ddb18be923b3b96114588de547e1c883b9faa0264b602b
ck_file v014_CF000.bin 6765c47e8934259006fa526a0e42ea8faf274c28758451d940539d1c28d38982
ck_file v014_D0000.bin 6765c47e8934259006fa526a0e42ea8faf274c28758451d940539d1c28d38982
ck_file v014_D1000.bin 6765c47e8934259006fa526a0e42ea8faf274c28758451d940539d1c28d38982
ck_file v014_D2000.bin 6765c47e8934259006fa526a0e42ea8faf274c28758451d940539d1c28d38982
ck_file v014_12E000.bin b03d579ba033bc8b425bd729b08269ffe081366fc7f4d8c6359b5df2d63194fa
ck_file base_D000.bin 6ede6ab8242ef1368efe8e1de8992f972f9724984d342a8e5144a86355acacd7
ck_file base_48000.bin cd43df9cf6f193ab32cd4c0963555f95e95e7ecb02b836bc720c2d1873dcbc01
ck_file base_CE000.bin 818fe7daabe129795f089f15ff7000e96a3e754bb4eef1188a30cd9d6781e923
ck_file base_CF000.bin cb87b8bb4828c63b87c36788f17d54049cf1b4c21e5757e0204a5e693fecf683
ck_file base_D0000.bin 0d7deca9d471b627b9eaede3872d233da2b9b643006476fe654f3d504713a8cf
ck_file base_D1000.bin 0d7ab5dc9d9ad6d369103ebd1db42c77e31d4969bece99fdb25943bd1df1db41
ck_file base_D2000.bin a0e9f30c578c5f06f9d0428b53eb181e1097ad5a6342f3837e4f6646c0a1f3fe
ck_file base_12E000.bin 5e8d678c7409819d482412447af3d3fba3128c23e53589b8e16317f50ebeeaa5

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
ck "ptable" 53248 64 744f5f5096d60bce43a21bda8358c68bc09ea9d3d3644f2ec5373a7c73330376
ck "FIRM" 57344 1647984 c84877d4dcce201dc9c144ae1008c2896ddb57f798ff9c86c84f7d5ed5a05653
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."

log ""
log "======================================================================"
log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."
log "   grava  : 32 KiB em 8 setores"
log "   muda   : menu principal em lista vertical estilo iPod nano 2G: 9 linhas, texto a esquerda, chevron a direita"
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
wr "4/6 1/8" 0xD000 v014_D000.bin cf32c556a6f0f309cbe2bea33d761396f738243c9da52aebf8e2163aed3ec4f6
wr "4/6 2/8" 0x48000 v014_48000.bin c4ca393ec94be6d45325d8e77b890d94ef5c61284ac5692d2b071566cb5499dd
wr "4/6 3/8" 0xCE000 v014_CE000.bin 6b08a80091ba655392ddb18be923b3b96114588de547e1c883b9faa0264b602b
wr "4/6 4/8" 0xCF000 v014_CF000.bin 6765c47e8934259006fa526a0e42ea8faf274c28758451d940539d1c28d38982
wr "4/6 5/8" 0xD0000 v014_D0000.bin 6765c47e8934259006fa526a0e42ea8faf274c28758451d940539d1c28d38982
wr "4/6 6/8" 0xD1000 v014_D1000.bin 6765c47e8934259006fa526a0e42ea8faf274c28758451d940539d1c28d38982
wr "4/6 7/8" 0xD2000 v014_D2000.bin 6765c47e8934259006fa526a0e42ea8faf274c28758451d940539d1c28d38982
wr "4/6 8/8" 0x12E000 v014_12E000.bin b03d579ba033bc8b425bd729b08269ffe081366fc7f4d8c6359b5df2d63194fa
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
ck2 "ptable" 53248 64 1d6875ecf61243fd5cb733a280c58bdde45232edad936d58d5e688f62a9bd95e
ck2 "FIRM" 57344 1647984 a1b1090bfa2e3fb71de0184a9c4914a1b2976ee6293a92781b3d6b29da3139f0
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] RESULTADO: V014 GRAVADO E VERIFICADO"
    log ""
    log "   Desconecte e abra o menu principal."
else
    log " [6/6] RESULTADO: ALGUMA REGIAO NAO CONFERE"
    log ""
    log "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:"
    log "     sudo $TOOL --id $DEV write_flash 0xD000 0 0x1000 base_D000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x48000 0 0x1000 base_48000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCE000 0 0x1000 base_CE000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCF000 0 0x1000 base_CF000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD0000 0 0x1000 base_D0000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD1000 0 0x1000 base_D1000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD2000 0 0x1000 base_D2000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x12E000 0 0x1000 base_12E000.bin"
fi
log "======================================================================"
log ""
log "  leve de volta: before.bin  after.bin  flash_v014.log"
log ""
