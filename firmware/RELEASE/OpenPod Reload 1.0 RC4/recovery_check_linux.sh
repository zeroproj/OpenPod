#!/bin/sh
# recovery_check_linux.sh — OpenPod: verificacao da recuperacao por USB.
#
# AUTOCONTIDO. Este e o UNICO arquivo que precisa ir para a maquina Linux.
# Nao depende da arvore do projeto.
#
# PROPOSITO
#   Provar que o caminho de recuperacao por USB funciona, ANTES de gravar
#   qualquer coisa. Ver docs/RECOVERY_CHECK.md.
#
# ESTE SCRIPT E SOMENTE LEITURA.
#   Os unicos comandos enviados ao aparelho sao 'flash_id' (opcode
#   CMD_SL_READID = 0) e 'read_flash' (CMD_SL_READ = 7). Nenhuma escrita,
#   nenhum apagamento, nenhuma execucao.
#
# USO
#   sh recovery_check_linux.sh [diretorio-de-trabalho]
#
# SAIDA
#   readback.bin   dump de 2 MiB lido do aparelho
#   readback.log   registro completo da sessao
#
#   Leve os DOIS de volta para a maquina do projeto e rode:
#       python3 tools/verify_device_readback.py readback.bin

set -eu

WORK=${1:-$(pwd)/openpod_recovery_check}
URL=https://github.com/ilyakurdyukov/smartlink_flash
COMMIT=49d51d17e825afbbbc2be7d91d6367674543c2e3
EXPECTED_FLASH_ID=0x14851485   # so para conferencia visual no log
EXPECTED_SIZE=2097152

say() { printf '%s\n' "$*"; }
die() { printf '\n*** %s\n' "$*" >&2; exit 1; }

say "======================================================================"
say " OpenPod — verificacao da recuperacao por USB  (SOMENTE LEITURA)"
say "======================================================================"
say ""

# ---------- 0. checagens de ambiente ----------
[ "$(uname -s)" = "Linux" ] || die "Este script e para Linux. Ver docs/RECOVERY_CHECK.md §2."
for c in git make cc lsusb; do
    command -v "$c" >/dev/null 2>&1 || die "faltando: $c   (sudo apt install git build-essential usbutils)"
done
[ -f /usr/include/libusb-1.0/libusb.h ] || die "faltando libusb-1.0-0-dev   (sudo apt install libusb-1.0-0-dev)"

mkdir -p "$WORK"
cd "$WORK"
LOG="$WORK/readback.log"
: > "$LOG"
exec 3>&1
log() { printf '%s\n' "$*" | tee -a "$LOG" >&3; }

log "diretorio de trabalho: $WORK"
log ""

# ---------- 1. obter a ferramenta na versao travada ----------
if [ ! -d smartlink_flash ]; then
    log "[1/5] clonando a ferramenta no commit travado..."
    git clone --quiet "$URL" smartlink_flash
    ( cd smartlink_flash && git checkout --quiet "$COMMIT" )
else
    log "[1/5] clone existente encontrado — conferindo o commit..."
    HAVE=$( cd smartlink_flash && git rev-parse HEAD 2>/dev/null || echo "?" )
    if [ "$HAVE" != "$COMMIT" ]; then
        log "    commit diferente: $HAVE"
        log "    ajustando para $COMMIT"
        ( cd smartlink_flash && git fetch --quiet origin && git checkout --quiet "$COMMIT" ) \
            || die "nao foi possivel ajustar o commit. Apague $WORK/smartlink_flash e rode de novo."
    fi
    log "    OK — commit $COMMIT"
fi

# ---------- 2. conferir os hashes ----------
log "[2/5] conferindo SHA-256 dos arquivos..."
cd smartlink_flash
FAIL=0
while IFS= read -r line; do
    [ -n "$line" ] || continue
    h=$(printf '%s' "$line" | cut -d' ' -f1)
    f=$(printf '%s' "$line" | sed 's/^[0-9a-f]*  //')
    r=$(sha256sum "$f" 2>/dev/null | cut -d' ' -f1)
    if [ "$r" != "$h" ]; then
        log "    DIVERGENTE: $f"
        FAIL=$((FAIL+1))
    fi
done <<'HASHES_EOF'
b1b6312643568b49f925ad8e75ea2f90d56037913021ed100ddd95c8414fadf7  Makefile
0211a93cbb6adc1c686007cf2cd09f76b5ee893bb9dd5b4b1021404b4b9ba044  README.md
5730957c9f2e076ebb4a2aa1348f6ee4c8a770921d4af1e32583c5dfa569caa6  fwhelper/Makefile
29ef758f97e0888e181bd0062992c911089e00f9562c53b43d49817faa6c6ecc  fwhelper/README.md
a66ed2dca6130f75550b942c6f37ab50ac0162551a0299583c82b52b314a300b  fwhelper/main.c
310b29d049038996f9851264e9ec3e959f7404a743040a30906db7af84abde5f  payload/Makefile
ca020d89b91b9d0b6e4b2e65abdb2e918d0e522f183a0162825618124970012f  payload/README.md
f2da43594575fda13f84b8d629bb14247d4f77c32c19109517dd0814b6a28b33  payload/entry.c
33bee69579e725f700fa3b399abc99d5fe4618dbd7b605c8751aaf99d64975e4  payload/simple.ld
c51e878f8e55ec68ecee94cabdea7da6a879d1984b244caa9558ede60644e115  payload/sl6801_sys.h
49d897658a7e47e95b63f56792a9deba1002d284e4b9dc1f706396429a9fa6c1  payload/sl6806_sys.h
051c182141768341af3f683696062eee9aa246cb3f244192515e57eeac92a364  payload/start.s
4cfd6c2303fe921cbc395a319c65ab7d9fed695253ba95511b14dd4880972512  payload/tinycopy.s
4b9eebb054a8f157a592b3c3bdfc55902a06d8562e9dead1a7ae7f3274c01253  payload/tinycopy_6806.s
caeff938fac8a7436b6c9d6089d5ca9ea7975ca52c78e2ef997c1181eb8a04a6  smtlink_dump.c
HASHES_EOF
[ "$FAIL" -eq 0 ] || die "$FAIL arquivo(s) divergem da versao travada. NAO PROSSIGA."
log "    OK — 15 arquivos conferem"

# ---------- 3. compilar ----------
log "[3/5] compilando smtlink_dump..."
make >>"$LOG" 2>&1 || die "falha ao compilar (ver $LOG)"
[ -x ./smtlink_dump ] || die "smtlink_dump nao foi gerado"
log "    OK"

# ---------- 4. enumeracao ----------
log "[4/5] procurando o aparelho..."
USBLINE=$(lsusb | grep -i "301a:" || true)
if [ -z "$USBLINE" ]; then
    log ""
    log "    NAO ENCONTRADO."
    log "    - conecte o GN-438 COM O CARTAO INSERIDO"
    log "    - troque de cabo (muitos cabos sao so de energia) e de porta"
    log "    - ver docs/RECOVERY_CHECK.md §4 e §6"
    die "aparelho nao enumera"
fi
log "    $USBLINE"
# A sequencia de comandos DIFERE conforme o modo:
#   card reader -> passar --id e NAO usar 'init' (o upstream avisa que trava)
#   bootloader  -> usar 'init' primeiro, sem --id (exemplo do upstream)
if printf '%s' "$USBLINE" | grep -q "301a:2801"; then
    log "    modo: card reader  (301a:2801)"
    set -- --id 301a:2801 flash_id read_flash 0 2M "$WORK/readback.bin"
elif printf '%s' "$USBLINE" | grep -q "301a:2800"; then
    log "    modo: bootloader  (301a:2800)"
    log "    -> usando 'init' primeiro, como exige o upstream para este modo"
    set -- init flash_id read_flash 0 2M "$WORK/readback.bin"
else
    die "VID 301a encontrado, mas PID inesperado: $USBLINE"
fi

# ---------- 5. leitura ----------
log "[5/5] lendo a flash (SOMENTE LEITURA)..."
log "      comando: smtlink_dump $*"
log ""
TMPOUT="$WORK/.dump_out"
if sudo ./smtlink_dump "$@" >"$TMPOUT" 2>&1; then STATUS=0; else STATUS=$?; fi
tee -a "$LOG" >&3 < "$TMPOUT"
rm -f "$TMPOUT"
if [ "$STATUS" -ne 0 ]; then
    log ""
    log "    smtlink_dump saiu com codigo $STATUS"
    log "    causas comuns: cabo so de energia; porta USB; falta de regra udev;"
    log "                   aparelho mudou de modo no meio da operacao."
    log "    ver docs/RECOVERY_CHECK.md §6"
    die "leitura falhou"
fi

cd "$WORK"
[ -f readback.bin ] || die "readback.bin nao foi criado"
SIZE=$(stat -c%s readback.bin)
SHA=$(sha256sum readback.bin | cut -d' ' -f1)

log ""
log "======================================================================"
log " RESULTADO"
log "======================================================================"
log "  tamanho : $SIZE bytes  (esperado $EXPECTED_SIZE)"
log "  sha256  : $SHA"
log ""
if [ "$SIZE" -ne "$EXPECTED_SIZE" ]; then
    log "  ATENCAO: tamanho inesperado — leitura incompleta?"
fi
if [ "$SHA" = "b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f" ]; then
    log "  >>> IDENTICO ao GN438_original.bin do projeto."
    log "  >>> O aparelho nao mudou. Rede de seguranca CONFIRMADA."
else
    log "  >>> DIFERENTE do original do projeto."
    log "  >>> Pode ser legitimo: a particao PSMP (config) muda em runtime."
    log "  >>> Rode a conferencia por regiao na maquina do projeto:"
    log "  >>>     python3 tools/verify_device_readback.py readback.bin"
fi
log ""
log "  leve de volta:  readback.bin  e  readback.log"
log ""
