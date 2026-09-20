#!/bin/sh
# flash_OpenPod_Beta11.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# OpenPod 5.7 Public Beta 11
#
# Grava 47 setores de 4096 B (188 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_OpenPod_Beta11.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
VERSAO="OpenPod_Beta11"
# Os setores moram ao lado deste script, em setores/. Entramos la
# para os nomes de arquivo resolverem, mas os logs e os dumps ficam
# onde o usuario chamou o script -- nao enterrados no pacote.
ORIGEM="$(pwd)"
DADOS="$(cd "$(dirname "$0")" && pwd)/setores"
[ -d "$DADOS" ] || { echo "faltando: $DADOS"; exit 1; }
cd "$DADOS" || exit 1
WORK="$ORIGEM/openpod_flash_$VERSAO"
LOG="$WORK/flash_$VERSAO.log"
WROTE=0

mkdir -p "$WORK"; : > "$LOG"; exec 3>&1
log() { printf '%s\n' "$*" | tee -a "$LOG" >&3; }
die() {
    log ""
    log "*** $*"
    if [ "$WROTE" -ne 0 ]; then
        log "$(m ja_gravou) $WROTE $(m ja_gravou2)"
        log "$(m reversao)"
        log "***   (de dentro de $DADOS)"
        log "***   sudo $TOOL --id $DEV write_flash 0x48000 0 0x1000 base_48000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x52000 0 0x1000 base_52000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x53000 0 0x1000 base_53000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x54000 0 0x1000 base_54000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x5D000 0 0x1000 base_5D000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xC7000 0 0x1000 base_C7000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCC000 0 0x1000 base_CC000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCD000 0 0x1000 base_CD000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD3000 0 0x1000 base_D3000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xDF000 0 0x1000 base_DF000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x101000 0 0x1000 base_101000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x108000 0 0x1000 base_108000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x109000 0 0x1000 base_109000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x10C000 0 0x1000 base_10C000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x10D000 0 0x1000 base_10D000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x121000 0 0x1000 base_121000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x122000 0 0x1000 base_122000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x123000 0 0x1000 base_123000.bin"
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
        log "***   sudo $TOOL --id $DEV write_flash 0x149000 0 0x1000 base_149000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A3000 0 0x1000 base_1A3000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A4000 0 0x1000 base_1A4000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A6000 0 0x1000 base_1A6000.bin"
        log "$(m diag)"
    else
        log "$(m nada)"
    fi
    exit 1
}
sha()  { python3 -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$1"; }
size() { python3 -c "import os,sys;print(os.path.getsize(sys.argv[1]))" "$1"; }
rsha() { python3 -c "import hashlib,sys;d=open(sys.argv[1],'rb').read()[int(sys.argv[2]):int(sys.argv[2])+int(sys.argv[3])];print(hashlib.sha256(d).hexdigest())" "$1" "$2" "$3"; }

# ------------------------------------------------------------------ idioma
# Se o install.sh ja perguntou, ele passa OPENPOD_LANG e nao perguntamos
# de novo. Rodando este script sozinho, a pergunta vem aqui.
OPENPOD_LANG=${OPENPOD_LANG:-}
if [ "$OPENPOD_LANG" != en ] && [ "$OPENPOD_LANG" != pt ]; then
    printf '\n  1) English     2) Portugues do Brasil\n  > '
    read -r _IDIOMA
    case "$_IDIOMA" in 1) OPENPOD_LANG=en ;; *) OPENPOD_LANG=pt ;; esac
    echo
fi
m() {
    if [ "$OPENPOD_LANG" = en ]; then
        case "$1" in
        so_linux) echo "This script is for Linux." ;;
        tool_falta) echo "smtlink_dump not found in" ;;
        falta) echo "missing:" ;;
        p1) echo "[1/6] checking the sector files..." ;;
        nao_achei) echo "file not found:" ;;
        tam_err) echo "wrong size, expected 4096 bytes:" ;;
        sha_err) echo "SHA-256 does not match:" ;;
        esperado) echo "expected" ;;
        obtido) echo "got     " ;;
        p2) echo "[2/6] looking for the player..." ;;
        ja_conectado) echo "already connected:" ;;
        conecte1) echo ">>> CONNECT THE GN-438 NOW (with the card inserted)." ;;
        conecte2) echo ">>> NOTE: the MOST RELIABLE way is the other way round —" ;;
        conecte3) echo ">>> plug it in, wait ~10s and ONLY THEN run the script." ;;
        conecte4) echo ">>> Seen on 2026-09-12: connecting now, the player often" ;;
        conecte5) echo ">>> re-enumerates right after (the Device N changes)." ;;
        aguardando) echo ">>> Waiting up to" ;;
        nao_apareceu) echo "the player did not show up in" ;;
        detectado) echo "detected:" ;;
        estab1) echo "waiting" ;;
        estab2) echo "to stabilize..." ;;
        caiu) echo "the player dropped while stabilizing. Reconnect and run again." ;;
        continua) echo "still connected — OK" ;;
        raio) echo "Screen shows the bolt and the player is steady? [y/N] " ;;
        abortado) echo "aborted by the operator" ;;
        p2b) echo "[2b/6] checking the tool first (recovery check)..." ;;
        rc_ask) echo "Run the recovery check now? (checks the tool, reads the flash) [Y/n] " ;;
        rc_skip) echo "SKIPPED at the operator's request" ;;
        rc_run) echo "running — may take a while (clone, 15 hashes, build, read 2 MiB)" ;;
        rc_fail) echo "recovery check FAILED. DO NOT PROCEED. code" ;;
        rc_ok) echo "recovery check OK" ;;
        rc_go) echo "Recovery check passed. Go ahead and write? [y/N] " ;;
        rc_ausente) echo "recovery_check_linux.sh is not in this folder — skipping" ;;
        p3) echo "[3/6] reading the flash, checking the state BEFORE..." ;;
        le_ini) echo "initial read failed" ;;
        incompleto) echo "is incomplete" ;;
        falha) echo "FAIL " ;;
        estado_err) echo "the player is NOT in the expected state. DO NOT PROCEED." ;;
        conf1) echo " All checks passed. The next step MODIFIES the firmware." ;;
        conf4) echo "   UNTOUCHED: bootloader, TONE, PSMP" ;;
        palavra) echo "FLASH" ;;
        digite) echo "Type EXACTLY  FLASH  to continue: " ;;
        confirmou) echo "operator confirmed" ;;
        gravando) echo "writing" ;;
        wf_falhou) echo "write_flash failed at" ;;
        rel_falhou) echo "re-read failed at" ;;
        rel_tam) echo "re-read has the wrong size at" ;;
        setor_err) echo "sector does NOT match after writing:" ;;
        setor_ok) echo "OK — sector matches" ;;
        p5) echo "[5/6] reading the whole flash, checking the state AFTER..." ;;
        le_fim) echo "final read failed" ;;
        res_ok) echo "RESULT: WRITTEN AND VERIFIED" ;;
        desconecte) echo "   Disconnect and open the main menu." ;;
        res_err) echo "RESULT: SOME REGION DOES NOT MATCH" ;;
        nao_desligue) echo "   DO NOT power off. ROLLBACK to the PREVIOUS state:" ;;
        leve) echo "  keep these: before.bin  after.bin  flash_" ;;
        ja_gravou) echo "*** ALREADY WROTE" ;;
        ja_gravou2) echo "sector(s). DO NOT POWER THE PLAYER OFF." ;;
        reversao) echo "*** ROLLBACK to the PREVIOUS state (this kit's base):" ;;
        diag) echo "*** Then run diag.sh and check before powering off." ;;
        nada) echo "*** Nothing was written." ;;
        escreve) echo "   writes   :" ;;
        muda) echo "   changes  :" ;;
        hdr) echo " OpenPod — writing" ;;
        setores) echo "sectors" ;;
        boot_na) echo " bootloader (0x0..0xD000): NOT ADDRESSED" ;;
        *) echo "$1" ;;
        esac
    else
        case "$1" in
        so_linux) echo "Este script e para Linux." ;;
        tool_falta) echo "smtlink_dump nao encontrado em" ;;
        falta) echo "faltando:" ;;
        p1) echo "[1/6] conferindo os arquivos de setor..." ;;
        nao_achei) echo "nao encontrei:" ;;
        tam_err) echo "tamanho errado, esperado 4096 bytes:" ;;
        sha_err) echo "SHA-256 nao confere:" ;;
        esperado) echo "esperado" ;;
        obtido) echo "obtido  " ;;
        p2) echo "[2/6] procurando o aparelho..." ;;
        ja_conectado) echo "ja conectado:" ;;
        conecte1) echo ">>> CONECTE O GN-438 AGORA (com o cartao inserido)." ;;
        conecte2) echo ">>> ATENCAO: o caminho MAIS CONFIAVEL e o contrario —" ;;
        conecte3) echo ">>> plugar, esperar ~10s e SO ENTAO rodar o script." ;;
        conecte4) echo ">>> Observado em 2026-09-12: conectando agora, o aparelho" ;;
        conecte5) echo ">>> costuma re-enumerar logo depois (muda o Device N)." ;;
        aguardando) echo ">>> Aguardando ate" ;;
        nao_apareceu) echo "o aparelho nao apareceu em" ;;
        detectado) echo "detectado:" ;;
        estab1) echo "aguardando" ;;
        estab2) echo "para estabilizar..." ;;
        caiu) echo "o aparelho caiu durante a estabilizacao. Reconecte e rode de novo." ;;
        continua) echo "continua conectado — OK" ;;
        raio) echo "A tela mostra o raio e o aparelho esta estavel? [s/N] " ;;
        abortado) echo "abortado pelo operador" ;;
        p2b) echo "[2b/6] verificacao previa da ferramenta (recovery check)..." ;;
        rc_ask) echo "Rodar o recovery check agora? (confere a ferramenta e le a flash) [S/n] " ;;
        rc_skip) echo "PULADO a pedido do operador" ;;
        rc_run) echo "rodando — pode demorar (clona, confere 15 hashes, compila, le 2 MiB)" ;;
        rc_fail) echo "recovery check FALHOU. NAO PROSSIGA. codigo" ;;
        rc_ok) echo "recovery check OK" ;;
        rc_go) echo "O recovery check passou. Pode seguir para a gravacao? [s/N] " ;;
        rc_ausente) echo "recovery_check_linux.sh nao esta nesta pasta — pulando" ;;
        p3) echo "[3/6] lendo a flash e conferindo o estado ANTES..." ;;
        le_ini) echo "leitura inicial falhou" ;;
        incompleto) echo "esta incompleto" ;;
        falha) echo "FALHA" ;;
        estado_err) echo "o aparelho NAO esta no estado esperado. NAO PROSSIGA." ;;
        conf1) echo " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho." ;;
        conf4) echo "   NAO toca: bootloader, TONE, PSMP" ;;
        palavra) echo "GRAVAR" ;;
        digite) echo "Digite EXATAMENTE  GRAVAR  para continuar: " ;;
        confirmou) echo "operador confirmou" ;;
        gravando) echo "gravando" ;;
        wf_falhou) echo "write_flash falhou em" ;;
        rel_falhou) echo "releitura falhou em" ;;
        rel_tam) echo "releitura com tamanho errado em" ;;
        setor_err) echo "setor NAO confere apos gravar:" ;;
        setor_ok) echo "OK — setor confere" ;;
        p5) echo "[5/6] lendo a flash inteira e conferindo o estado DEPOIS..." ;;
        le_fim) echo "leitura final falhou" ;;
        res_ok) echo "RESULTADO: GRAVADO E VERIFICADO" ;;
        desconecte) echo "   Desconecte e abra o menu principal." ;;
        res_err) echo "RESULTADO: ALGUMA REGIAO NAO CONFERE" ;;
        nao_desligue) echo "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:" ;;
        leve) echo "  leve de volta: before.bin  after.bin  flash_" ;;
        ja_gravou) echo "*** JA HAVIA GRAVADO" ;;
        ja_gravou2) echo "setor(es). NAO DESLIGUE O APARELHO." ;;
        reversao) echo "*** REVERSAO para o estado ANTERIOR (a base deste kit):" ;;
        diag) echo "*** Depois rode diag.sh e confira antes de desligar." ;;
        nada) echo "*** Nada foi gravado." ;;
        escreve) echo "   grava  :" ;;
        muda) echo "   muda   :" ;;
        hdr) echo " OpenPod — gravacao do" ;;
        setores) echo "setores" ;;
        boot_na) echo " bootloader (0x0..0xD000): NAO ENDERECADO" ;;
        *) echo "$1" ;;
        esac
    fi
}
# --------------------------------------------------------------------------

log "======================================================================"
log "$(m hdr) OPENPOD_BETA11   (47 $(m setores), 188 KiB)"
log " 0x048000 +0x1000   <- OpenPod_Beta11_48000.bin"
log " 0x052000 +0x1000   <- OpenPod_Beta11_52000.bin"
log " 0x053000 +0x1000   <- OpenPod_Beta11_53000.bin"
log " 0x054000 +0x1000   <- OpenPod_Beta11_54000.bin"
log " 0x05D000 +0x1000   <- OpenPod_Beta11_5D000.bin"
log " 0x0C7000 +0x1000   <- OpenPod_Beta11_C7000.bin"
log " 0x0CC000 +0x1000   <- OpenPod_Beta11_CC000.bin"
log " 0x0CD000 +0x1000   <- OpenPod_Beta11_CD000.bin"
log " 0x0D3000 +0x1000   <- OpenPod_Beta11_D3000.bin"
log " 0x0DF000 +0x1000   <- OpenPod_Beta11_DF000.bin"
log " 0x101000 +0x1000   <- OpenPod_Beta11_101000.bin"
log " 0x108000 +0x1000   <- OpenPod_Beta11_108000.bin"
log " 0x109000 +0x1000   <- OpenPod_Beta11_109000.bin"
log " 0x10A000 +0x1000   <- OpenPod_Beta11_10A000.bin"
log " 0x10C000 +0x1000   <- OpenPod_Beta11_10C000.bin"
log " 0x10D000 +0x1000   <- OpenPod_Beta11_10D000.bin"
log " 0x121000 +0x1000   <- OpenPod_Beta11_121000.bin"
log " 0x122000 +0x1000   <- OpenPod_Beta11_122000.bin"
log " 0x123000 +0x1000   <- OpenPod_Beta11_123000.bin"
log " 0x126000 +0x1000   <- OpenPod_Beta11_126000.bin"
log " 0x127000 +0x1000   <- OpenPod_Beta11_127000.bin"
log " 0x128000 +0x1000   <- OpenPod_Beta11_128000.bin"
log " 0x129000 +0x1000   <- OpenPod_Beta11_129000.bin"
log " 0x12A000 +0x1000   <- OpenPod_Beta11_12A000.bin"
log " 0x12B000 +0x1000   <- OpenPod_Beta11_12B000.bin"
log " 0x12C000 +0x1000   <- OpenPod_Beta11_12C000.bin"
log " 0x12D000 +0x1000   <- OpenPod_Beta11_12D000.bin"
log " 0x12E000 +0x1000   <- OpenPod_Beta11_12E000.bin"
log " 0x12F000 +0x1000   <- OpenPod_Beta11_12F000.bin"
log " 0x130000 +0x1000   <- OpenPod_Beta11_130000.bin"
log " 0x131000 +0x1000   <- OpenPod_Beta11_131000.bin"
log " 0x132000 +0x1000   <- OpenPod_Beta11_132000.bin"
log " 0x133000 +0x1000   <- OpenPod_Beta11_133000.bin"
log " 0x134000 +0x1000   <- OpenPod_Beta11_134000.bin"
log " 0x135000 +0x1000   <- OpenPod_Beta11_135000.bin"
log " 0x136000 +0x1000   <- OpenPod_Beta11_136000.bin"
log " 0x137000 +0x1000   <- OpenPod_Beta11_137000.bin"
log " 0x138000 +0x1000   <- OpenPod_Beta11_138000.bin"
log " 0x139000 +0x1000   <- OpenPod_Beta11_139000.bin"
log " 0x13A000 +0x1000   <- OpenPod_Beta11_13A000.bin"
log " 0x13B000 +0x1000   <- OpenPod_Beta11_13B000.bin"
log " 0x13C000 +0x1000   <- OpenPod_Beta11_13C000.bin"
log " 0x13D000 +0x1000   <- OpenPod_Beta11_13D000.bin"
log " 0x149000 +0x1000   <- OpenPod_Beta11_149000.bin"
log " 0x1A3000 +0x1000   <- OpenPod_Beta11_1A3000.bin"
log " 0x1A4000 +0x1000   <- OpenPod_Beta11_1A4000.bin"
log " 0x1A6000 +0x1000   <- OpenPod_Beta11_1A6000.bin"
log "$(m boot_na)"
log "======================================================================"
log ""

[ "$(uname -s)" = "Linux" ] || die "$(m so_linux)"
[ -x "$TOOL" ] || die "$(m tool_falta) $TOOLDIR"
for c in python3 lsusb; do
    command -v "$c" >/dev/null 2>&1 || die "$(m falta) $c"
done

log "$(m p1)"
ck_file() {
    [ -f "$1" ] || die "$(m nao_achei) $1"
    s=$(size "$1"); [ "$s" = "4096" ] || die "$(m tam_err) $1 ($s)"
    g=$(sha "$1");  [ "$g" = "$2" ] || die "$(m sha_err) $1
    $(m esperado) $2
    $(m obtido) $g"
    log "        OK   $1"
}
ck_file "OpenPod_Beta11_48000.bin" 6ea532bf216161b7d65e6fec3857f9f27890899a6e7ccd0cccff654fb471dd12
ck_file "OpenPod_Beta11_52000.bin" 3b36d143a96aaab07e0927c9eecf4351f6b0a21c833d0a6f5352fd8226bc5ca3
ck_file "OpenPod_Beta11_53000.bin" a62c6180f15359d58c91eb6b96c087dbbeae1e0403e8b94accc7e00a7b8e8fe8
ck_file "OpenPod_Beta11_54000.bin" a96553f46460656f6a7c1a5d9636c0743f9ca606013b1901cd3ac95df109abb5
ck_file "OpenPod_Beta11_5D000.bin" 7e3402a71dd7d45f80e9d1eb5bc03a5d56a9f9dfb87c5829efcb76e1a5a947c1
ck_file "OpenPod_Beta11_C7000.bin" f678974cafcb27f9b636e9713360e6f34a9d03f1b6082f3de9897e1513f3a421
ck_file "OpenPod_Beta11_CC000.bin" ef8ffb2966867c44f8a87315ad7469a97018d0b7367ce864c19ffa102a8ba165
ck_file "OpenPod_Beta11_CD000.bin" 99d56432ede44c31aa9fc2b928c7965db70129bd8e4bc3f3a9b00b82abd4554e
ck_file "OpenPod_Beta11_D3000.bin" eddeb2ee73066fdef9b81eee7fb5dd74e0710b594c0e0b67090daf9822ac630c
ck_file "OpenPod_Beta11_DF000.bin" fd20c126093f6bc74a4068300166e922236d7eb571e87848c9bb0a841872686e
ck_file "OpenPod_Beta11_101000.bin" 673da19a6d3d37b673316192ec95fab51e36ae91df6e3d1c0f72e560635d94eb
ck_file "OpenPod_Beta11_108000.bin" 78dbabe4822551a5eaa29b063785c8473cc7ca49a53397c9c7514fb4c2ccc983
ck_file "OpenPod_Beta11_109000.bin" 3bc16bacee418a50f79df0aa7c3f5604241fc55f126ee8d7bec7d802849312c2
ck_file "OpenPod_Beta11_10A000.bin" a85ff54b0a34ef5319afd4c65f282cbcc222b1e6d84570bbf721d9275e805501
ck_file "OpenPod_Beta11_10C000.bin" 3b8683d363ba2d88fe25955572dfcb27a2153ec413f40a207ccf012d5e89b4d4
ck_file "OpenPod_Beta11_10D000.bin" 6fe1812c1a69ae6e876e9fc7a63e10e83055850f60e209d3c0ed34a67231f40a
ck_file "OpenPod_Beta11_121000.bin" 30ebefbe8d45d7d26c18201cd385b35f67e8e27396f726be0050649f77b1216d
ck_file "OpenPod_Beta11_122000.bin" df9b903aa340d40041a61cffd9082181033811098b832b0e0603b97b09885250
ck_file "OpenPod_Beta11_123000.bin" 213ef142bcbd7696faccc4e2139605cffda0d9f6e2bfbf0b368feca2fb2f0e50
ck_file "OpenPod_Beta11_126000.bin" 25f7937818203d1f7e320fbd4aeef456aa71927db2a89d6ff14f05ad0d571b9f
ck_file "OpenPod_Beta11_127000.bin" e9d327492dd109c2513cbf07d402e9443eca0acd47193c5de856a9ce03a5a498
ck_file "OpenPod_Beta11_128000.bin" 6fb81fe21a9645d59e484516a5a342e0c1e2a0f1362f9678a528c270d58bf599
ck_file "OpenPod_Beta11_129000.bin" fd209596a64baccb1937d1b15097048e2158ab478e40c75bf96ffba0c0f5bd26
ck_file "OpenPod_Beta11_12A000.bin" fdba7d5b8cadf02fd1c59c6bda8c60e95fb1ee7efd827ca77462adc6af2cc5fd
ck_file "OpenPod_Beta11_12B000.bin" 27de098786b4fd862aa7f7f852bfad6e73d53cce0fc0ee3fa23b9433406745e9
ck_file "OpenPod_Beta11_12C000.bin" bd9fd998d33622f70ba6c0ba311f0bd1aabd5200df1296406646530a41a94bb2
ck_file "OpenPod_Beta11_12D000.bin" 6f2c626887db52348a599f6bf544611bedb43cc2751dd4b75104333c1ae3dcba
ck_file "OpenPod_Beta11_12E000.bin" 34338f09581e5aa1c689c188201ddfdebc29d251a0bfe7e1074d58c429be7157
ck_file "OpenPod_Beta11_12F000.bin" a640a2e36034aed5c4b51653fb7b6cc85d94f5d43eb12224c3b16a74c61ef102
ck_file "OpenPod_Beta11_130000.bin" a209c305d8cc078e6b1947f7e437cda6a8f92d7ae757b986f8d0b4e2fcead5b6
ck_file "OpenPod_Beta11_131000.bin" 13cbb12b13d73a421e60cbd298869e9cf68d0ce2eca5548602adf6cf37e2e8c5
ck_file "OpenPod_Beta11_132000.bin" e05828e015b71a8c3f2290b03b843188771855583e7ee886244de7d17bd46f0e
ck_file "OpenPod_Beta11_133000.bin" ffdb8e5ee01d4219eec486d7f3bc60df7e62e30269361daad437835008b513bf
ck_file "OpenPod_Beta11_134000.bin" bdb077624bce3c8b2d508b03393c0608004a53cefbd1ab1c3e1142f5ef0cb6b4
ck_file "OpenPod_Beta11_135000.bin" e52b4f721ab955ce0acc404d7bbffb4dded60b0c0b09d43fcd8b54b04ebfab7e
ck_file "OpenPod_Beta11_136000.bin" 37133af6fa7684d462b11159bacebd685f7f5e533830fd2607ce63f0d177d7b8
ck_file "OpenPod_Beta11_137000.bin" 9f27ec07c3773ed74cc2702121298b8cdbbcb4ec5815b994d8a430226b9e8bf5
ck_file "OpenPod_Beta11_138000.bin" b4ae75cffaf10da6b7edb44bb19483b627db21dcbfcd9b6388b8f1aa11626863
ck_file "OpenPod_Beta11_139000.bin" 0809afdd572786578e9713711d83177fd77ebe5c89734a78cf16d55d90242c8d
ck_file "OpenPod_Beta11_13A000.bin" 72f6bc37de6f618d6528e4411c86c090bdcf45a9e565ed5bcae94ed0d3d7f629
ck_file "OpenPod_Beta11_13B000.bin" e76fe152ae3b0f4414952f7f658add959f41adf86e0297a5ea657288cafa1a6e
ck_file "OpenPod_Beta11_13C000.bin" f9b05c7df264e8c210701e056986e0167641e37ed7cf32d8f477f15aa77feb34
ck_file "OpenPod_Beta11_13D000.bin" e8bb94264408ab85f7e905d3561ed2a4527295409f6b8381c6a154e4d2139120
ck_file "OpenPod_Beta11_149000.bin" 47c9bc96248f581805ec555ccc7e6166a454ef6a5b0ae472531c9d24d3683884
ck_file "OpenPod_Beta11_1A3000.bin" 9f06327e4e94065d21a686623ade77e48141f60be7a2c680712c73c9748a78e0
ck_file "OpenPod_Beta11_1A4000.bin" 276a5497517bf2f5aa9572c7db7a0adb003dfc70ade9fabfa420cd6ad3450edf
ck_file "OpenPod_Beta11_1A6000.bin" d2a1a3ed0dfa9dfa1bde5123f496142bf3c67dbe425e452ff68594f95dde7c25
ck_file "base_48000.bin" cd43df9cf6f193ab32cd4c0963555f95e95e7ecb02b836bc720c2d1873dcbc01
ck_file "base_52000.bin" 91360fd9e5a5e0871f1682f38174f0acf9b29588e16d18e810f59ef01b158c2f
ck_file "base_53000.bin" 5decc107dd674f7b6bdd34436f9a7e9b68900c61a7552df7a24be1f7f85bf4c5
ck_file "base_54000.bin" f5757388180b2ec2c3c1da4c51068af8bf44bd526d48b8fff5fd3ccfe075d41c
ck_file "base_5D000.bin" e0d56d6422cf0f404cda889d124397e73caaf81f7a6b758b304df46d60a73435
ck_file "base_C7000.bin" ae29fc778567f832164a237fd2f523dd6eedb4eefad4c7d843676d63931039b4
ck_file "base_CC000.bin" 83597203bed419cc2f76f1b8c942194d07a4b23c34f67e2e7834864361dd6688
ck_file "base_CD000.bin" ab039386aa645f414a0580730cc4b62ca7831c9d4d8dff7b01c80f9b7be16f5f
ck_file "base_D3000.bin" b53d3f48030da1ab150ad3d52b4a21771ce6ae766d1750d589fa4d811a12fe3b
ck_file "base_DF000.bin" 6e2c7679d881a81f37dccd0d55e335779f649a760bd29bd1f7ef21a500c8b08c
ck_file "base_101000.bin" 3fc82037a6ed598d4004f1aa2f4c44b9534bf10433fe70f8c31af85bbd190a1d
ck_file "base_108000.bin" ccd6967286db00a55df42f50d7af6d633f736c482ebf08807ecf0e2e6d71dbf4
ck_file "base_109000.bin" 40e5a7786b3a7c82c786da0effb5036c6da0c234462dfaa5c435581cf5f03411
ck_file "base_10A000.bin" ad962e28861a9a9914ef70e26cfc50283fa51daee636051a4907db930839dd6a
ck_file "base_10C000.bin" da58ee1b07cc42893b98fb55a5248ac2ee4ee67a43b4bcd63b8651f25263441a
ck_file "base_10D000.bin" f43913b07336f83cee66dfb7779c6e88d93738189879b486ba97aaef9b2e63ba
ck_file "base_121000.bin" dbea2b9d18646cad64d3a5ea402a2a633bb0c4036fca689ad997ecb2545ba9ac
ck_file "base_122000.bin" dc3b6a4a0150763564474047400cebac7b4e331820901505eacf3644083c7c48
ck_file "base_123000.bin" fdd9e6ef0752425d429d354bc74652402039880f251c0a390b42b60c087a5805
ck_file "base_126000.bin" cc31a3d9cea495315d60f231c08705f2396ddd1eb70dcc962853aff1b346da35
ck_file "base_127000.bin" 0318cc59765edcc893008ee976b24ace551a27ce8b3212837f5d072f2f186b27
ck_file "base_128000.bin" 4393a597215fa98b88eaee6ef9855b6b12f9401d4e2e506029fa91b6c4450b6d
ck_file "base_129000.bin" c0b55f64c4bbd7536bb7ce506fa03a5fabb47335d80022d742be31791440d6d6
ck_file "base_12A000.bin" aa94827f67ae6f0c2b57f83c1806b79e7759329c4a975efd3ad7781621447dda
ck_file "base_12B000.bin" aa3358950b8cd2d6b8c65702c33d2efda29516144b3c69d7a0a74f770826b5cd
ck_file "base_12C000.bin" ccc11583d6490eebb0b292115bb32c139c984ef40d3d39286bd86c00c6fb0356
ck_file "base_12D000.bin" 84bf9e4e0c04ea9352d343e34e5603d64876e192d3556f5341bc970810f94c85
ck_file "base_12E000.bin" e135e686ad0de20f085fc204494b51873731b520ad24930487896b63b29109cc
ck_file "base_12F000.bin" d882556ecd8e1f18038733b1befaa656f9a49034c5dc1305031114176f8064d3
ck_file "base_130000.bin" 2a2d6c1641e5c2ca12fac749062fcfd45beb944fabeb3c8729de03b61e504b2d
ck_file "base_131000.bin" 93a71390d6fc97d25914e309237068a629084dd7ecece96a005469c1720e465c
ck_file "base_132000.bin" fa5a5bba47c3517b8aabda238496f2a9b0f407516f89d96f4f4fbf07f2203536
ck_file "base_133000.bin" 3cddc24926e15507b9e3592ee80616d7d38df8f9b7bf0fd3b6b4907aabef377c
ck_file "base_134000.bin" eb3d37a83e74423e0d1db56b0891c3889acee08ac9f501fc3067e6578fdb4826
ck_file "base_135000.bin" 4eecf7a661e1ca9f41a8b8d4b4fffe37cf4c9bd50091d245c22763092b12f78f
ck_file "base_136000.bin" 35ee889edf0de18419e8e3af91852f7527336250937affee022d5af8bd1e7594
ck_file "base_137000.bin" c53024a5371196563c6ba5b50a88d190b75f958523bb7aa893144560f5775558
ck_file "base_138000.bin" f236f6919146873d8ca237a7b699ff2f1db3c88690a9c5f25e5d3d97adeaa1d5
ck_file "base_139000.bin" c663ab140ea8f16b5eccd26b11317c931f23f339ca171ec133423871b4bf6cda
ck_file "base_13A000.bin" 867fc7c28b75e651f73086c36d49c6eebf891d47ad5f36957043baa5ca22ceda
ck_file "base_13B000.bin" bab42fa2f1aa4db37450e353783a262129d0852f17d53f7f2c93c05de0d95ddb
ck_file "base_13C000.bin" bf4146959ee1417989cb85d2fc5f1573ba8a731e8d59e0ca04bfcbbbcf8ca8b2
ck_file "base_13D000.bin" 990c996fc6c868ad50ca5b3e09f60c4b7ae9f6ac7998e362e7d55b383091adf8
ck_file "base_149000.bin" 25ad539edd56b3cf92e8105bf46fb73233f5841ea482709a68aa862cacce2a97
ck_file "base_1A3000.bin" 6f4ef0b382a9fa4d2792e8446613308544b251e2d512ea1b5d3b83ce8f1d10e4
ck_file "base_1A4000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6
ck_file "base_1A6000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6

log "$(m p2)"
# --- espera ativa pelo aparelho ---------------------------------
# O aparelho precisa de alguns segundos entre plugar e o primeiro
# comando, senao cai do modo card reader no meio da operacao.
ESPERA=180        # segundos ate desistir
ESTABILIZA=8      # segundos de folga apos detectar
aguardar_aparelho() {
    U=$(lsusb | grep -i "301a:2801" || true)
    if [ -n "$U" ]; then
        log "        $(m ja_conectado) $U"
    else
        log ""
        log "        $(m conecte1)"
        log "        $(m conecte2)"
        log "        $(m conecte3)"
        log "        $(m conecte4)"
        log "        $(m conecte5)"
        log "        $(m aguardando) ${ESPERA}s..."
        i=0
        while [ "$i" -lt "$ESPERA" ]; do
            U=$(lsusb | grep -i "301a:2801" || true)
            [ -n "$U" ] && break
            i=$((i + 1)); sleep 1
        done
        [ -n "$U" ] || die "$(m nao_apareceu) ${ESPERA}s."
        log "        $(m detectado) $U"
    fi
    log "        $(m estab1) ${ESTABILIZA}s $(m estab2)"
    sleep "$ESTABILIZA"
    V=$(lsusb | grep -i "301a:2801" || true)
    [ -n "$V" ] || die "$(m caiu)"
    log "        $(m continua)"
}
aguardar_aparelho
log ""
printf '%s' "$(m raio)"
read -r OK
case "$OK" in [sSyY]*) ;; *) die "$(m abortado)" ;; esac
# ----------------------------------------------------------------

# --- verificacao previa: recovery check -------------------------
# Confere os 15 hashes do codigo-fonte do smtlink_dump no commit
# travado e recompila. Garante que a ferramenta que vai ESCREVER
# no aparelho e exatamente a versao auditada. Ver RECOVERY_CHECK.md.
log ""
log "$(m p2b)"
if [ -f ./recovery_check_linux.sh ]; then
    printf '%s' "$(m rc_ask)"
    read -r R0
    case "$R0" in
        [nN]*) log "        $(m rc_skip)" ;;
        *) log "        $(m rc_run)"
           # IMPORTANTE: nao usar  cmd | tee || die  — o || receberia o
           # status do tee, e um recovery check REPROVADO passaria batido.
           if sh ./recovery_check_linux.sh "$WORK/precheck" >"$WORK/.rc_out" 2>&1; then
               RCST=0; else RCST=$?; fi
           tee -a "$LOG" >&3 < "$WORK/.rc_out"; rm -f "$WORK/.rc_out"
           [ "$RCST" -eq 0 ] || die "$(m rc_fail) $RCST"
           log ""
           log "        $(m rc_ok)"
           printf '%s' "$(m rc_go)"
           read -r R1
           case "$R1" in [sSyY]*) ;; *) die "$(m abortado)" ;; esac ;;
    esac
else
    log "        $(m rc_ausente)"
fi
# ----------------------------------------------------------------

log "$(m p3)"
"$TOOL" --id "$DEV" read_flash 0 2M "$WORK/before.bin" >>"$LOG" 2>&1 \
    || die "$(m le_ini)"
[ "$(size "$WORK/before.bin")" = "2097152" ] || die "before.bin $(m incompleto)"
F=0
ck() {
    g=$(rsha "$WORK/before.bin" "$2" "$3")
    if [ "$g" = "$4" ]; then log "        OK   $1"
    else log "        $(m falha) $1"; log "          $(m esperado) $4"; log "          $(m obtido) $g"; F=1; fi
}
ck "bootloader" 0 51532 861184003923634be0f2ae9883456035b40d1ea72f97682890238edfae3acb31
ck "ptable" 53248 64 9f93d4435e7cb819b2dad2f38edf91fb0a0af44654c4d9fcd3df174bf3380a2d
ck "FIRM" 57344 1647984 e2a7b86339030b94268dac7d562a167613a3e769c866790353b4921cad85dbdc
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "$(m estado_err)"

log ""
log "======================================================================"
log "$(m conf1)"
log "$(m escreve) 188 KiB / 47 $(m setores)"
log "$(m muda) OpenPod 5.7 Public Beta 11"
log "$(m conf4)"
log "======================================================================"
printf '%s' "$(m digite)"
read -r R
[ "$R" = "$(m palavra)" ] || die "$(m abortado)"
log "$(m confirmou)"
log ""

wr() {
    log "[$1] $(m gravando) $2 <- $3..."
    WROTE=$((WROTE + 1))
    "$TOOL" --id "$DEV" write_flash "$2" 0 0x1000 "$3" >>"$LOG" 2>&1 \
        || die "$(m wf_falhou) $2"
    "$TOOL" --id "$DEV" read_flash "$2" 0x1000 "$WORK/sec.bin" >>"$LOG" 2>&1 \
        || die "$(m rel_falhou) $2"
    s=$(size "$WORK/sec.bin"); [ "$s" = "4096" ] || die "$(m rel_tam) $2 ($s)"
    g=$(sha "$WORK/sec.bin")
    [ "$g" = "$4" ] || die "$(m setor_err) $2
    $(m esperado) $4
    $(m obtido) $g"
    log "        $(m setor_ok)"
}
wr "4/6 1/47" 0x48000 "OpenPod_Beta11_48000.bin" 6ea532bf216161b7d65e6fec3857f9f27890899a6e7ccd0cccff654fb471dd12
wr "4/6 2/47" 0x52000 "OpenPod_Beta11_52000.bin" 3b36d143a96aaab07e0927c9eecf4351f6b0a21c833d0a6f5352fd8226bc5ca3
wr "4/6 3/47" 0x53000 "OpenPod_Beta11_53000.bin" a62c6180f15359d58c91eb6b96c087dbbeae1e0403e8b94accc7e00a7b8e8fe8
wr "4/6 4/47" 0x54000 "OpenPod_Beta11_54000.bin" a96553f46460656f6a7c1a5d9636c0743f9ca606013b1901cd3ac95df109abb5
wr "4/6 5/47" 0x5D000 "OpenPod_Beta11_5D000.bin" 7e3402a71dd7d45f80e9d1eb5bc03a5d56a9f9dfb87c5829efcb76e1a5a947c1
wr "4/6 6/47" 0xC7000 "OpenPod_Beta11_C7000.bin" f678974cafcb27f9b636e9713360e6f34a9d03f1b6082f3de9897e1513f3a421
wr "4/6 7/47" 0xCC000 "OpenPod_Beta11_CC000.bin" ef8ffb2966867c44f8a87315ad7469a97018d0b7367ce864c19ffa102a8ba165
wr "4/6 8/47" 0xCD000 "OpenPod_Beta11_CD000.bin" 99d56432ede44c31aa9fc2b928c7965db70129bd8e4bc3f3a9b00b82abd4554e
wr "4/6 9/47" 0xD3000 "OpenPod_Beta11_D3000.bin" eddeb2ee73066fdef9b81eee7fb5dd74e0710b594c0e0b67090daf9822ac630c
wr "4/6 10/47" 0xDF000 "OpenPod_Beta11_DF000.bin" fd20c126093f6bc74a4068300166e922236d7eb571e87848c9bb0a841872686e
wr "4/6 11/47" 0x101000 "OpenPod_Beta11_101000.bin" 673da19a6d3d37b673316192ec95fab51e36ae91df6e3d1c0f72e560635d94eb
wr "4/6 12/47" 0x108000 "OpenPod_Beta11_108000.bin" 78dbabe4822551a5eaa29b063785c8473cc7ca49a53397c9c7514fb4c2ccc983
wr "4/6 13/47" 0x109000 "OpenPod_Beta11_109000.bin" 3bc16bacee418a50f79df0aa7c3f5604241fc55f126ee8d7bec7d802849312c2
wr "4/6 14/47" 0x10A000 "OpenPod_Beta11_10A000.bin" a85ff54b0a34ef5319afd4c65f282cbcc222b1e6d84570bbf721d9275e805501
wr "4/6 15/47" 0x10C000 "OpenPod_Beta11_10C000.bin" 3b8683d363ba2d88fe25955572dfcb27a2153ec413f40a207ccf012d5e89b4d4
wr "4/6 16/47" 0x10D000 "OpenPod_Beta11_10D000.bin" 6fe1812c1a69ae6e876e9fc7a63e10e83055850f60e209d3c0ed34a67231f40a
wr "4/6 17/47" 0x121000 "OpenPod_Beta11_121000.bin" 30ebefbe8d45d7d26c18201cd385b35f67e8e27396f726be0050649f77b1216d
wr "4/6 18/47" 0x122000 "OpenPod_Beta11_122000.bin" df9b903aa340d40041a61cffd9082181033811098b832b0e0603b97b09885250
wr "4/6 19/47" 0x123000 "OpenPod_Beta11_123000.bin" 213ef142bcbd7696faccc4e2139605cffda0d9f6e2bfbf0b368feca2fb2f0e50
wr "4/6 20/47" 0x126000 "OpenPod_Beta11_126000.bin" 25f7937818203d1f7e320fbd4aeef456aa71927db2a89d6ff14f05ad0d571b9f
wr "4/6 21/47" 0x127000 "OpenPod_Beta11_127000.bin" e9d327492dd109c2513cbf07d402e9443eca0acd47193c5de856a9ce03a5a498
wr "4/6 22/47" 0x128000 "OpenPod_Beta11_128000.bin" 6fb81fe21a9645d59e484516a5a342e0c1e2a0f1362f9678a528c270d58bf599
wr "4/6 23/47" 0x129000 "OpenPod_Beta11_129000.bin" fd209596a64baccb1937d1b15097048e2158ab478e40c75bf96ffba0c0f5bd26
wr "4/6 24/47" 0x12A000 "OpenPod_Beta11_12A000.bin" fdba7d5b8cadf02fd1c59c6bda8c60e95fb1ee7efd827ca77462adc6af2cc5fd
wr "4/6 25/47" 0x12B000 "OpenPod_Beta11_12B000.bin" 27de098786b4fd862aa7f7f852bfad6e73d53cce0fc0ee3fa23b9433406745e9
wr "4/6 26/47" 0x12C000 "OpenPod_Beta11_12C000.bin" bd9fd998d33622f70ba6c0ba311f0bd1aabd5200df1296406646530a41a94bb2
wr "4/6 27/47" 0x12D000 "OpenPod_Beta11_12D000.bin" 6f2c626887db52348a599f6bf544611bedb43cc2751dd4b75104333c1ae3dcba
wr "4/6 28/47" 0x12E000 "OpenPod_Beta11_12E000.bin" 34338f09581e5aa1c689c188201ddfdebc29d251a0bfe7e1074d58c429be7157
wr "4/6 29/47" 0x12F000 "OpenPod_Beta11_12F000.bin" a640a2e36034aed5c4b51653fb7b6cc85d94f5d43eb12224c3b16a74c61ef102
wr "4/6 30/47" 0x130000 "OpenPod_Beta11_130000.bin" a209c305d8cc078e6b1947f7e437cda6a8f92d7ae757b986f8d0b4e2fcead5b6
wr "4/6 31/47" 0x131000 "OpenPod_Beta11_131000.bin" 13cbb12b13d73a421e60cbd298869e9cf68d0ce2eca5548602adf6cf37e2e8c5
wr "4/6 32/47" 0x132000 "OpenPod_Beta11_132000.bin" e05828e015b71a8c3f2290b03b843188771855583e7ee886244de7d17bd46f0e
wr "4/6 33/47" 0x133000 "OpenPod_Beta11_133000.bin" ffdb8e5ee01d4219eec486d7f3bc60df7e62e30269361daad437835008b513bf
wr "4/6 34/47" 0x134000 "OpenPod_Beta11_134000.bin" bdb077624bce3c8b2d508b03393c0608004a53cefbd1ab1c3e1142f5ef0cb6b4
wr "4/6 35/47" 0x135000 "OpenPod_Beta11_135000.bin" e52b4f721ab955ce0acc404d7bbffb4dded60b0c0b09d43fcd8b54b04ebfab7e
wr "4/6 36/47" 0x136000 "OpenPod_Beta11_136000.bin" 37133af6fa7684d462b11159bacebd685f7f5e533830fd2607ce63f0d177d7b8
wr "4/6 37/47" 0x137000 "OpenPod_Beta11_137000.bin" 9f27ec07c3773ed74cc2702121298b8cdbbcb4ec5815b994d8a430226b9e8bf5
wr "4/6 38/47" 0x138000 "OpenPod_Beta11_138000.bin" b4ae75cffaf10da6b7edb44bb19483b627db21dcbfcd9b6388b8f1aa11626863
wr "4/6 39/47" 0x139000 "OpenPod_Beta11_139000.bin" 0809afdd572786578e9713711d83177fd77ebe5c89734a78cf16d55d90242c8d
wr "4/6 40/47" 0x13A000 "OpenPod_Beta11_13A000.bin" 72f6bc37de6f618d6528e4411c86c090bdcf45a9e565ed5bcae94ed0d3d7f629
wr "4/6 41/47" 0x13B000 "OpenPod_Beta11_13B000.bin" e76fe152ae3b0f4414952f7f658add959f41adf86e0297a5ea657288cafa1a6e
wr "4/6 42/47" 0x13C000 "OpenPod_Beta11_13C000.bin" f9b05c7df264e8c210701e056986e0167641e37ed7cf32d8f477f15aa77feb34
wr "4/6 43/47" 0x13D000 "OpenPod_Beta11_13D000.bin" e8bb94264408ab85f7e905d3561ed2a4527295409f6b8381c6a154e4d2139120
wr "4/6 44/47" 0x149000 "OpenPod_Beta11_149000.bin" 47c9bc96248f581805ec555ccc7e6166a454ef6a5b0ae472531c9d24d3683884
wr "4/6 45/47" 0x1A3000 "OpenPod_Beta11_1A3000.bin" 9f06327e4e94065d21a686623ade77e48141f60be7a2c680712c73c9748a78e0
wr "4/6 46/47" 0x1A4000 "OpenPod_Beta11_1A4000.bin" 276a5497517bf2f5aa9572c7db7a0adb003dfc70ade9fabfa420cd6ad3450edf
wr "4/6 47/47" 0x1A6000 "OpenPod_Beta11_1A6000.bin" d2a1a3ed0dfa9dfa1bde5123f496142bf3c67dbe425e452ff68594f95dde7c25
rm -f "$WORK/sec.bin"

log "$(m p5)"
"$TOOL" --id "$DEV" read_flash 0 2M "$WORK/after.bin" >>"$LOG" 2>&1 \
    || die "$(m le_fim)"
[ "$(size "$WORK/after.bin")" = "2097152" ] || die "after.bin $(m incompleto)"
F=0
ck2() {
    g=$(rsha "$WORK/after.bin" "$2" "$3")
    if [ "$g" = "$4" ]; then log "        OK   $1"
    else log "        $(m falha) $1"; log "          $(m esperado) $4"; log "          $(m obtido) $g"; F=1; fi
}
ck2 "bootloader" 0 51532 861184003923634be0f2ae9883456035b40d1ea72f97682890238edfae3acb31
ck2 "ptable" 53248 64 9f93d4435e7cb819b2dad2f38edf91fb0a0af44654c4d9fcd3df174bf3380a2d
ck2 "FIRM" 57344 1647984 0f85b511fef5b1e10e138189cb2482fbda4ab6386b183cee48b9cbb01ab93417
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] OPENPOD_BETA11 — $(m res_ok)"
    log ""
    log "$(m desconecte)"
else
    log " [6/6] $(m res_err)"
    log ""
    log "$(m nao_desligue)"
    log "     sudo $TOOL --id $DEV write_flash 0x48000 0 0x1000 base_48000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x52000 0 0x1000 base_52000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x53000 0 0x1000 base_53000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x54000 0 0x1000 base_54000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x5D000 0 0x1000 base_5D000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xC7000 0 0x1000 base_C7000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCC000 0 0x1000 base_CC000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCD000 0 0x1000 base_CD000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD3000 0 0x1000 base_D3000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xDF000 0 0x1000 base_DF000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x101000 0 0x1000 base_101000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x108000 0 0x1000 base_108000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x109000 0 0x1000 base_109000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x10C000 0 0x1000 base_10C000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x10D000 0 0x1000 base_10D000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x121000 0 0x1000 base_121000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x122000 0 0x1000 base_122000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x123000 0 0x1000 base_123000.bin"
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
    log "     sudo $TOOL --id $DEV write_flash 0x149000 0 0x1000 base_149000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A3000 0 0x1000 base_1A3000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A4000 0 0x1000 base_1A4000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A6000 0 0x1000 base_1A6000.bin"
fi
log "======================================================================"
log ""
log "$(m leve)$VERSAO.log"
log ""
