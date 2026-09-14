#!/bin/sh
# flash_v018.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# faixa mais alta com 2 px de respiro antes da lista, lista re-espacada, e video vira Video
#
# Grava 11 setores de 4096 B (44 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_v018.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
WORK=$(pwd)/openpod_flash_v018
LOG="$WORK/flash_v018.log"
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
        log "***   sudo $TOOL --id $DEV write_flash 0x53000 0 0x1000 base_53000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCE000 0 0x1000 base_CE000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCF000 0 0x1000 base_CF000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD0000 0 0x1000 base_D0000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD1000 0 0x1000 base_D1000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD2000 0 0x1000 base_D2000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x121000 0 0x1000 base_121000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x122000 0 0x1000 base_122000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A3000 0 0x1000 base_1A3000.bin"
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
log " OpenPod — gravacao do V018   (11 setores, 44 KiB)"
log " 0x00D000 +0x1000   <- v018_D000.bin"
log " 0x048000 +0x1000   <- v018_48000.bin"
log " 0x053000 +0x1000   <- v018_53000.bin"
log " 0x0CE000 +0x1000   <- v018_CE000.bin"
log " 0x0CF000 +0x1000   <- v018_CF000.bin"
log " 0x0D0000 +0x1000   <- v018_D0000.bin"
log " 0x0D1000 +0x1000   <- v018_D1000.bin"
log " 0x0D2000 +0x1000   <- v018_D2000.bin"
log " 0x121000 +0x1000   <- v018_121000.bin"
log " 0x122000 +0x1000   <- v018_122000.bin"
log " 0x1A3000 +0x1000   <- v018_1A3000.bin"
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
ck_file v018_D000.bin f795becc340e8f79b0d1dc80ca0314a5fc463912ea3c4c32c16ab4036c717b74
ck_file v018_48000.bin c160a68cab4a5a7982222bc52908cb607c55c43b700e43c50f9637c6def05582
ck_file v018_53000.bin 955c524790aaa400968e228e5adfdea8683263fdb14a20f9215e55dbbf8e7880
ck_file v018_CE000.bin 9beea3aaa2da29815bd060465d8a3ae47ff920e8d1c1a0c109a28098012ae352
ck_file v018_CF000.bin 20e9abcea0e539ce4fd2cce8a18e7e6c3f29fac7b107b8613eceef1fbc734eba
ck_file v018_D0000.bin 7ff368fc24d00e8156ff7d6e7830b9ff70d4832fe2d5e83795a0f6b2c4cb8b16
ck_file v018_D1000.bin 5bae1c8a56f6497b3186e85e9aa9ab153b5f273445500c7c05b7e3f5a77fb1ec
ck_file v018_D2000.bin ff29c013ba2a7361036bdaab6377d8dfb784e9f34a1408ba8effa0ecb5776b9e
ck_file v018_121000.bin 2729d03dc57c70b8a20d2e339dfe586ed523fe0fb37747bb861964b71edf1c98
ck_file v018_122000.bin a12a4865bcef55276a5df3418e5f71b2c63381cc5d8a22078cdf34ad15823831
ck_file v018_1A3000.bin 4e1d2cd94f20a2a109cd1dcc86ea2671ef23679c41639e2acdf2115cf8f66619
ck_file base_D000.bin 2ac1bd57d7bf12c57db13fb4614ecf7eee52a8554e51b0be9caac519239c6d9b
ck_file base_48000.bin c4ca393ec94be6d45325d8e77b890d94ef5c61284ac5692d2b071566cb5499dd
ck_file base_53000.bin 5decc107dd674f7b6bdd34436f9a7e9b68900c61a7552df7a24be1f7f85bf4c5
ck_file base_CE000.bin 65f384783370375cbefdae7696834d6638ba0d968cb1bac4add2a82a3386c5fe
ck_file base_CF000.bin 6765c47e8934259006fa526a0e42ea8faf274c28758451d940539d1c28d38982
ck_file base_D0000.bin 6765c47e8934259006fa526a0e42ea8faf274c28758451d940539d1c28d38982
ck_file base_D1000.bin 6765c47e8934259006fa526a0e42ea8faf274c28758451d940539d1c28d38982
ck_file base_D2000.bin 6765c47e8934259006fa526a0e42ea8faf274c28758451d940539d1c28d38982
ck_file base_121000.bin dbea2b9d18646cad64d3a5ea402a2a633bb0c4036fca689ad997ecb2545ba9ac
ck_file base_122000.bin 028a837f2cd9da2d4080f4e2109f30a52c4633f53f5dd69a6cca04da3cbf3213
ck_file base_1A3000.bin 0fc9de50f9f26ac90fd3ee01dc5ae2017961517cc0c42ff5f6128d25ff611428

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
ck "ptable" 53248 64 a3b6d68aa7feada97865237f8d687d394a4ddf9373ce44d4d3956c6cef260e2c
ck "FIRM" 57344 1647984 210d07c13f07f71485856afd0aa084ab7730278ab0672e7eed1609b7e4674dcc
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."

log ""
log "======================================================================"
log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."
log "   grava  : 44 KiB em 11 setores"
log "   muda   : faixa mais alta com 2 px de respiro antes da lista, lista re-espacada, e video vira Video"
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
wr "4/6 1/11" 0xD000 v018_D000.bin f795becc340e8f79b0d1dc80ca0314a5fc463912ea3c4c32c16ab4036c717b74
wr "4/6 2/11" 0x48000 v018_48000.bin c160a68cab4a5a7982222bc52908cb607c55c43b700e43c50f9637c6def05582
wr "4/6 3/11" 0x53000 v018_53000.bin 955c524790aaa400968e228e5adfdea8683263fdb14a20f9215e55dbbf8e7880
wr "4/6 4/11" 0xCE000 v018_CE000.bin 9beea3aaa2da29815bd060465d8a3ae47ff920e8d1c1a0c109a28098012ae352
wr "4/6 5/11" 0xCF000 v018_CF000.bin 20e9abcea0e539ce4fd2cce8a18e7e6c3f29fac7b107b8613eceef1fbc734eba
wr "4/6 6/11" 0xD0000 v018_D0000.bin 7ff368fc24d00e8156ff7d6e7830b9ff70d4832fe2d5e83795a0f6b2c4cb8b16
wr "4/6 7/11" 0xD1000 v018_D1000.bin 5bae1c8a56f6497b3186e85e9aa9ab153b5f273445500c7c05b7e3f5a77fb1ec
wr "4/6 8/11" 0xD2000 v018_D2000.bin ff29c013ba2a7361036bdaab6377d8dfb784e9f34a1408ba8effa0ecb5776b9e
wr "4/6 9/11" 0x121000 v018_121000.bin 2729d03dc57c70b8a20d2e339dfe586ed523fe0fb37747bb861964b71edf1c98
wr "4/6 10/11" 0x122000 v018_122000.bin a12a4865bcef55276a5df3418e5f71b2c63381cc5d8a22078cdf34ad15823831
wr "4/6 11/11" 0x1A3000 v018_1A3000.bin 4e1d2cd94f20a2a109cd1dcc86ea2671ef23679c41639e2acdf2115cf8f66619
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
ck2 "ptable" 53248 64 9af77158b0f69796d51cafebcda1243c7cc69dc83992bd420cabcc8d90884dff
ck2 "FIRM" 57344 1647984 954789a8104d35c7355855e7050e44b8dc25fd039f6b9d07b8cba65d162df0c8
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] RESULTADO: V018 GRAVADO E VERIFICADO"
    log ""
    log "   Desconecte e abra o menu principal."
else
    log " [6/6] RESULTADO: ALGUMA REGIAO NAO CONFERE"
    log ""
    log "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:"
    log "     sudo $TOOL --id $DEV write_flash 0xD000 0 0x1000 base_D000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x48000 0 0x1000 base_48000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x53000 0 0x1000 base_53000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCE000 0 0x1000 base_CE000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCF000 0 0x1000 base_CF000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD0000 0 0x1000 base_D0000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD1000 0 0x1000 base_D1000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD2000 0 0x1000 base_D2000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x121000 0 0x1000 base_121000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x122000 0 0x1000 base_122000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A3000 0 0x1000 base_1A3000.bin"
fi
log "======================================================================"
log ""
log "  leve de volta: before.bin  after.bin  flash_v018.log"
log ""
