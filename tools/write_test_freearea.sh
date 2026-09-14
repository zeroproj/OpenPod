#!/bin/sh
# write_test_freearea.sh — OpenPod: teste de ESCRITA na area livre da flash.
#
# ############################################################
# #  ESTE E O PRIMEIRO COMANDO DE ESCRITA DO PROJETO.        #
# ############################################################
#
# PROPOSITO
#   Provar que erase + write + readback funcionam neste aparelho, ANTES de
#   precisar deles para recuperar um firmware quebrado.
#
#   A rede de seguranca confirmada em 2026-09-12 cobre apenas LEITURA.
#   Se o V001 corromper a FIRM, a recuperacao exige ESCRITA por USB — um
#   caminho nunca exercitado, cujo suporte no smartlink_flash tem poucos
#   meses e que o proprio autor descreve como "tested very little".
#   Este teste fecha essa lacuna.
#
# ONDE ESCREVE
#   Apenas no setor 0x1D0000 (4 KiB), dentro dos 356 KiB de area livre
#   entre a particao TONE e a PSMP. Verificado em 2026-09-12: todo 0xFF.
#     - 180 KiB depois do fim da TONE   (0x1A3038)
#     - 172 KiB antes do inicio da PSMP (0x1FC000)
#   O firmware NAO usa essa area. Ela nem entra no pacote update.up.
#
#   O ENDERECO E FIXO NO CODIGO. Nao e parametro. Nao ha como apontar
#   para FIRM, TONE, bootloader ou PSMP por engano de digitacao.
#
# O QUE FAZ, EM ORDEM
#   1. le a flash inteira e confere as 4 regioes criticas por SHA-256
#   2. confirma que o setor alvo esta todo 0xFF
#   3. pede confirmacao explicita
#   4. ESCREVE um padrao conhecido de 4 KiB
#   5. rele e compara byte a byte
#   6. APAGA o setor
#   7. rele e confirma que voltou a 0xFF
#   8. le a flash inteira de novo e reconfere as 4 regioes criticas
#
#   Se qualquer etapa falhar, para. Se falhar depois da escrita, tenta
#   apagar o setor antes de sair.
#
# USO
#   sh write_test_freearea.sh [diretorio-do-smartlink_flash]
#
# SAIDA
#   before.bin  after.bin  writetest.log   — levar de volta ao projeto
#
# NAO USE ESTE SCRIPT PARA OUTRA COISA. Ele existe para um unico teste.

set -eu
export LC_ALL=C   # 'tr' com bytes >0x7F depende de locale

TARGET=0x1D0000          # FIXO. Nao alterar sem refazer toda a analise.
TSIZE=0x1000             # 4 KiB = um setor
TDEC=1900544             # TARGET em decimal
TSZDEC=4096

DEV_CR=301a:2801
EXPECTED_FLASH_ID=0x14851485

# SHA-256 das regioes criticas, medidos no readback verificado de 2026-09-12
H_BOOT=861184003923634be0f2ae9883456035b40d1ea72f97682890238edfae3acb31
H_PTAB=9f93d4435e7cb819b2dad2f38edf91fb0a0af44654c4d9fcd3df174bf3380a2d
H_FIRM=e2a7b86339030b94268dac7d562a167613a3e769c866790353b4921cad85dbdc
H_TONE=7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

TOOLDIR=${1:-.}
WORK=$(pwd)/openpod_writetest
LOG="$WORK/writetest.log"
WROTE=0

mkdir -p "$WORK"
: > "$LOG"
exec 3>&1
log() { printf '%s\n' "$*" | tee -a "$LOG" >&3; }
die() {
    log ""
    log "*** $*"
    if [ "$WROTE" -eq 1 ]; then
        log "*** o setor foi escrito. tentando apagar para deixar limpo..."
        sudo "$TOOL" --id "$DEV_CR" erase_flash "$TARGET" "$TSIZE" >>"$LOG" 2>&1 \
            && log "*** setor apagado" || log "*** NAO foi possivel apagar — registre e pare"
    fi
    exit 1
}

# extrai uma faixa e devolve o sha256
# usa tail+head: dd com bs=1 sobre 1,6 MB levaria minutos
range_sha() {
    tail -c +$(( $2 + 1 )) "$1" | head -c "$3" | sha256sum | cut -d' ' -f1
}

log "======================================================================"
log " OpenPod — teste de ESCRITA na area livre"
log " alvo FIXO: $TARGET .. +$TSIZE   (area livre, nao usada pelo firmware)"
log "======================================================================"
log ""

[ "$(uname -s)" = "Linux" ] || die "Este script e para Linux."
TOOL="$TOOLDIR/smtlink_dump"
[ -x "$TOOL" ] || die "smtlink_dump nao encontrado em $TOOLDIR"
for c in tail head sha256sum cmp lsusb tr; do
    command -v "$c" >/dev/null 2>&1 || die "faltando: $c"
done

USBLINE=$(lsusb | grep -i "301a:" || true)
[ -n "$USBLINE" ] || die "aparelho nao enumera. Conecte COM O CARTAO INSERIDO."
printf '%s' "$USBLINE" | grep -q "$DEV_CR" \
    || die "esperado modo card reader ($DEV_CR). Encontrado: $USBLINE"
log "aparelho: $USBLINE"
log ""

# ---------- 1. estado ANTES ----------
log "[1/8] lendo a flash inteira (antes)..."
sudo "$TOOL" --id "$DEV_CR" flash_id read_flash 0 2M "$WORK/before.bin" >>"$LOG" 2>&1 \
    || die "leitura inicial falhou"
[ "$(stat -c%s "$WORK/before.bin")" = "2097152" ] || die "before.bin com tamanho errado"

log "      conferindo as 4 regioes criticas..."
FAIL=0
check_region() {
    got=$(range_sha "$WORK/before.bin" "$2" "$3")
    if [ "$got" = "$4" ]; then log "        OK   $1"
    else log "        FALHA $1"; log "          esperado $4"; log "          obtido   $got"; FAIL=1; fi
}
check_region "bootloader" 0      51532   "$H_BOOT"
check_region "ptable"     53248  64      "$H_PTAB"
check_region "FIRM"       57344  1647984 "$H_FIRM"
check_region "TONE"       1708032 8248   "$H_TONE"
[ "$FAIL" -eq 0 ] || die "o aparelho NAO esta no estado de referencia. NAO PROSSIGA."

# ---------- 2. o setor alvo esta livre? ----------
log "[2/8] conferindo que o setor alvo esta todo 0xFF..."
tail -c +$(( TDEC + 1 )) "$WORK/before.bin" | head -c "$TSZDEC" > "$WORK/target_before.bin"
NONFF=$(tr -d '\377' < "$WORK/target_before.bin" | wc -c | tr -d ' ')
[ "$NONFF" = "0" ] || die "o setor alvo NAO esta livre ($NONFF bytes != 0xFF). NAO PROSSIGA."
log "        OK — 4096 bytes de 0xFF"
log ""

# ---------- 3. confirmacao ----------
log "======================================================================"
log " Tudo conferido. A proxima etapa ESCREVE na flash."
log "   endereco : $TARGET   (area livre, 180 KiB depois da TONE)"
log "   tamanho  : $TSIZE (4 KiB, um setor)"
log "   reversivel: sim — o setor e apagado ao final"
log "======================================================================"
printf 'Digite EXATAMENTE  ESCREVER  para continuar (qualquer outra coisa aborta): '
read -r RESP
[ "$RESP" = "ESCREVER" ] || die "abortado pelo operador (nada foi escrito)"
log "operador confirmou"
log ""

# ---------- 4. gerar padrao e escrever ----------
log "[3/8] gerando o padrao de 4 KiB..."
yes 'OPENPOD-WRITE-TEST-1D0000-' | tr -d '\n' | head -c "$TSZDEC" > "$WORK/pattern.bin"
[ "$(stat -c%s "$WORK/pattern.bin")" = "$TSZDEC" ] || die "padrao com tamanho errado"
log "        sha256: $(sha256sum "$WORK/pattern.bin" | cut -d' ' -f1)"

log "[4/8] ESCREVENDO..."
WROTE=1
sudo "$TOOL" --id "$DEV_CR" write_flash "$TARGET" 0 "$TSIZE" "$WORK/pattern.bin" >>"$LOG" 2>&1 \
    || die "write_flash falhou"
log "        comando concluido"

# ---------- 5. verificar a escrita ----------
log "[5/8] relendo o setor e comparando..."
sudo "$TOOL" --id "$DEV_CR" read_flash "$TARGET" "$TSIZE" "$WORK/target_written.bin" >>"$LOG" 2>&1 \
    || die "leitura pos-escrita falhou"
if cmp -s "$WORK/pattern.bin" "$WORK/target_written.bin"; then
    log "        OK — escrita conferiu byte a byte"
    WRITE_OK=1
else
    DIFF=$(cmp -l "$WORK/pattern.bin" "$WORK/target_written.bin" | wc -l | tr -d ' ')
    log "        DIVERGENTE — $DIFF bytes diferentes do esperado"
    log "        (isto e exatamente o tipo de anomalia relatada para esta flash)"
    WRITE_OK=0
fi

# ---------- 6. apagar ----------
log "[6/8] apagando o setor..."
sudo "$TOOL" --id "$DEV_CR" erase_flash "$TARGET" "$TSIZE" >>"$LOG" 2>&1 \
    || die "erase_flash falhou — o setor ficou escrito"
WROTE=0

log "[7/8] conferindo que voltou a 0xFF..."
sudo "$TOOL" --id "$DEV_CR" read_flash "$TARGET" "$TSIZE" "$WORK/target_erased.bin" >>"$LOG" 2>&1 \
    || die "leitura pos-apagamento falhou"
# compara com o estado lido ANTES do teste: tem de voltar identico
if cmp -s "$WORK/target_before.bin" "$WORK/target_erased.bin"; then
    log "        OK — setor voltou EXATAMENTE ao estado anterior (4096 x 0xFF)"
    ERASE_OK=1
else
    DIFF=$(cmp -l "$WORK/target_before.bin" "$WORK/target_erased.bin" | wc -l | tr -d ' ')
    log "        DIVERGENTE — $DIFF bytes nao voltaram ao estado original"
    ERASE_OK=0
fi

# ---------- 7. estado DEPOIS ----------
log "[8/8] lendo a flash inteira (depois) e reconferindo..."
sudo "$TOOL" --id "$DEV_CR" read_flash 0 2M "$WORK/after.bin" >>"$LOG" 2>&1 \
    || die "leitura final falhou"
FAIL=0
check_region2() {
    got=$(range_sha "$WORK/after.bin" "$2" "$3")
    if [ "$got" = "$4" ]; then log "        OK   $1"
    else log "        FALHA $1 — REGIAO CRITICA ALTERADA"; FAIL=1; fi
}
check_region2 "bootloader" 0      51532   "$H_BOOT"
check_region2 "ptable"     53248  64      "$H_PTAB"
check_region2 "FIRM"       57344  1647984 "$H_FIRM"
check_region2 "TONE"       1708032 8248   "$H_TONE"

log ""
log "======================================================================"
log " RESULTADO"
log "======================================================================"
log "  escrita conferiu       : $([ "${WRITE_OK:-0}" = 1 ] && echo SIM || echo NAO)"
log "  apagamento conferiu    : $([ "${ERASE_OK:-0}" = 1 ] && echo SIM || echo NAO)"
log "  regioes criticas intactas: $([ "$FAIL" = 0 ] && echo SIM || echo 'NAO  <<< GRAVE')"
log ""
if [ "$FAIL" != 0 ]; then
    log "  *** UMA REGIAO CRITICA MUDOU. Nao grave mais nada."
    log "  *** Preserve before.bin e after.bin e leve ao projeto."
elif [ "${WRITE_OK:-0}" = 1 ] && [ "${ERASE_OK:-0}" = 1 ]; then
    log "  >>> CAMINHO DE ESCRITA POR USB CONFIRMADO."
    log "  >>> A recuperacao e viavel. O teste do V001 fica liberado."
else
    log "  >>> escrita ou apagamento nao conferiram, mas nada critico mudou."
    log "  >>> Leve os arquivos ao projeto para analise antes de prosseguir."
fi
log ""
log "  leve de volta: before.bin  after.bin  writetest.log"
log "                 target_written.bin  target_erased.bin  pattern.bin"
log ""
