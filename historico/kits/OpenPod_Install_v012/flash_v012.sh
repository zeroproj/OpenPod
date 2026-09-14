#!/bin/sh
# flash_v012.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# OpenPod v012 — tema escuro consolidado: icones cinza, selecao azul, logo OpenPod sobre preto
#
# Grava 6 setores de 4096 B (24 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_v012.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
WORK=$(pwd)/openpod_flash_v012
LOG="$WORK/flash_v012.log"
WROTE=0

mkdir -p "$WORK"; : > "$LOG"; exec 3>&1
log() { printf '%s\n' "$*" | tee -a "$LOG" >&3; }
die() {
    log ""
    log "*** $*"
    if [ "$WROTE" -ne 0 ]; then
        log "*** JA HAVIA GRAVADO $WROTE setor(es). NAO DESLIGUE O APARELHO."
        log "*** Restauracao para o ORIGINAL de fabrica:"
        log "***   sudo $TOOL --id $DEV write_flash 0xD000 0 0x1000 orig_D000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCC000 0 0x1000 orig_CC000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCD000 0 0x1000 orig_CD000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCE000 0 0x1000 orig_CE000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x121000 0 0x1000 orig_121000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x12E000 0 0x1000 orig_12E000.bin"
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
log " OpenPod — gravacao do V012   (6 setores, 24 KiB)"
log " 0x00D000 +0x1000   <- v012_D000.bin"
log " 0x0CC000 +0x1000   <- v012_CC000.bin"
log " 0x0CD000 +0x1000   <- v012_CD000.bin"
log " 0x0CE000 +0x1000   <- v012_CE000.bin"
log " 0x121000 +0x1000   <- v012_121000.bin"
log " 0x12E000 +0x1000   <- v012_12E000.bin"
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
ck_file v012_D000.bin bdb36efaef38fcd748c8dd0f85f0376a9097700133c87a4189a4a4b1a19c6b28
ck_file v012_CC000.bin ef8ffb2966867c44f8a87315ad7469a97018d0b7367ce864c19ffa102a8ba165
ck_file v012_CD000.bin d77710d5a99db95967dc5ba61a2f3bbc2f1081cea272c688f616c9a305aabc6c
ck_file v012_CE000.bin 818fe7daabe129795f089f15ff7000e96a3e754bb4eef1188a30cd9d6781e923
ck_file v012_121000.bin f02709501538c03fff136ae91cabe6f7897c31538973ef9e1d0a0406f1f935d7
ck_file v012_12E000.bin 460cd8b5a036ccfc103adc88724e8ef4d3628efec3e1cb1eda828e9f81113014
ck_file orig_D000.bin c3d16a15b7df6a8feac96169d93da82a5562ae3d17a94bf8906c2d24fc507091
ck_file orig_CC000.bin 83597203bed419cc2f76f1b8c942194d07a4b23c34f67e2e7834864361dd6688
ck_file orig_CD000.bin ab039386aa645f414a0580730cc4b62ca7831c9d4d8dff7b01c80f9b7be16f5f
ck_file orig_CE000.bin f46bdf8b56e3b463e8461ea5b35bfae201cafda178ac8296a5c2d8bc19cbf175
ck_file orig_121000.bin dbea2b9d18646cad64d3a5ea402a2a633bb0c4036fca689ad997ecb2545ba9ac
ck_file orig_12E000.bin e135e686ad0de20f085fc204494b51873731b520ad24930487896b63b29109cc

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
ck "ptable" 53248 64 588785f987617321a2c9aa065a59a98a9a75f2fbc3c5484b101b59ff811208be
ck "FIRM" 57344 1647984 720971c31bf7df790868083c07f1dbb3ecb5160d42a7d64f0a74cae322b32c33
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."

log ""
log "======================================================================"
log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."
log "   grava  : 24 KiB em 6 setores"
log "   muda   : OpenPod v012 — tema escuro consolidado: icones cinza, selecao azul, logo OpenPod sobre preto"
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
wr "4/6 1/6" 0xD000 v012_D000.bin bdb36efaef38fcd748c8dd0f85f0376a9097700133c87a4189a4a4b1a19c6b28
wr "4/6 2/6" 0xCC000 v012_CC000.bin ef8ffb2966867c44f8a87315ad7469a97018d0b7367ce864c19ffa102a8ba165
wr "4/6 3/6" 0xCD000 v012_CD000.bin d77710d5a99db95967dc5ba61a2f3bbc2f1081cea272c688f616c9a305aabc6c
wr "4/6 4/6" 0xCE000 v012_CE000.bin 818fe7daabe129795f089f15ff7000e96a3e754bb4eef1188a30cd9d6781e923
wr "4/6 5/6" 0x121000 v012_121000.bin f02709501538c03fff136ae91cabe6f7897c31538973ef9e1d0a0406f1f935d7
wr "4/6 6/6" 0x12E000 v012_12E000.bin 460cd8b5a036ccfc103adc88724e8ef4d3628efec3e1cb1eda828e9f81113014
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
ck2 "ptable" 53248 64 ce0a1ddbb012854093ed7547d73a2d88afec26c26fe33507cc8b6a1428052c9d
ck2 "FIRM" 57344 1647984 42e41bbeb880d824e3e568c38dc83352e614dd46dfcca73dd0985ffcd925ec1f
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] RESULTADO: V012 GRAVADO E VERIFICADO"
    log ""
    log "   Desconecte e abra o menu principal."
else
    log " [6/6] RESULTADO: ALGUMA REGIAO NAO CONFERE"
    log ""
    log "   NAO desligue o aparelho. Restauracao para o ORIGINAL:"
    log "     sudo $TOOL --id $DEV write_flash 0xD000 0 0x1000 orig_D000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCC000 0 0x1000 orig_CC000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCD000 0 0x1000 orig_CD000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCE000 0 0x1000 orig_CE000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x121000 0 0x1000 orig_121000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x12E000 0 0x1000 orig_12E000.bin"
fi
log "======================================================================"
log ""
log "  leve de volta: before.bin  after.bin  flash_v012.log"
log ""
