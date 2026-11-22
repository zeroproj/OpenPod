#!/bin/sh
# flash_OpenPodReload3.5Diag.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# Player na tela inicial (ficha 028)
#
# Grava 15 setores de 4096 B (60 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_OpenPodReload3.5Diag.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
VERSAO="OpenPodReload3.5Diag"
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
        log "***   sudo $TOOL --id $DEV write_flash 0xCE000 0 0x1000 base_CE000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCF000 0 0x1000 base_CF000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD0000 0 0x1000 base_D0000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD1000 0 0x1000 base_D1000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD2000 0 0x1000 base_D2000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x123000 0 0x1000 base_123000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x12E000 0 0x1000 base_12E000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x132000 0 0x1000 base_132000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A4000 0 0x1000 base_1A4000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1AB000 0 0x1000 base_1AB000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1AC000 0 0x1000 base_1AC000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1AD000 0 0x1000 base_1AD000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1AE000 0 0x1000 base_1AE000.bin"
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
log "$(m hdr) OPENPODRELOAD3.5DIAG   (15 $(m setores), 60 KiB)"
log " 0x048000 +0x1000   <- OpenPodReload3.5Diag_48000.bin"
log " 0x0CE000 +0x1000   <- OpenPodReload3.5Diag_CE000.bin"
log " 0x0CF000 +0x1000   <- OpenPodReload3.5Diag_CF000.bin"
log " 0x0D0000 +0x1000   <- OpenPodReload3.5Diag_D0000.bin"
log " 0x0D1000 +0x1000   <- OpenPodReload3.5Diag_D1000.bin"
log " 0x0D2000 +0x1000   <- OpenPodReload3.5Diag_D2000.bin"
log " 0x10A000 +0x1000   <- OpenPodReload3.5Diag_10A000.bin"
log " 0x123000 +0x1000   <- OpenPodReload3.5Diag_123000.bin"
log " 0x12E000 +0x1000   <- OpenPodReload3.5Diag_12E000.bin"
log " 0x132000 +0x1000   <- OpenPodReload3.5Diag_132000.bin"
log " 0x1A4000 +0x1000   <- OpenPodReload3.5Diag_1A4000.bin"
log " 0x1AB000 +0x1000   <- OpenPodReload3.5Diag_1AB000.bin"
log " 0x1AC000 +0x1000   <- OpenPodReload3.5Diag_1AC000.bin"
log " 0x1AD000 +0x1000   <- OpenPodReload3.5Diag_1AD000.bin"
log " 0x1AE000 +0x1000   <- OpenPodReload3.5Diag_1AE000.bin"
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
ck_file "OpenPodReload3.5Diag_48000.bin" f9359f759de013d1a3be4299d63ec0ef75c16bd88cfa0035f411df185abdb9c4
ck_file "OpenPodReload3.5Diag_CE000.bin" 89aae60a38eea6662777afad9f28a29e98e3850e15bd4cb2fa6d085141f7c205
ck_file "OpenPodReload3.5Diag_CF000.bin" 39c5a13e1d4b34d4f41e35766841cd57c10d7505bfcdd0f7ddbda523f5033e13
ck_file "OpenPodReload3.5Diag_D0000.bin" b47ab78997d8a88e67a2f8cdc197569890624c3d389986e63614e58bca2b8d1e
ck_file "OpenPodReload3.5Diag_D1000.bin" 3e52acea70e54a1abf810e83c9abe2cc1245bb072190fd6abdae2ec2511a1c3c
ck_file "OpenPodReload3.5Diag_D2000.bin" 23da3a5be0802ff3488354f9ead86e166b0541d85f5a24def84b3e6c101e4b22
ck_file "OpenPodReload3.5Diag_10A000.bin" 8c35d232644fbcec0e57519558b61e1d3f0a7b0d269bbadde0c4eae6ba5316d3
ck_file "OpenPodReload3.5Diag_123000.bin" 9c9be8a117d448e5a8331ae2029d4eb227a5cf66bb02bf9410687f3def65007a
ck_file "OpenPodReload3.5Diag_12E000.bin" 996d2241d56cc3a1bd23f8baa356f9137d66b21e22c402138abe5b6df1bee942
ck_file "OpenPodReload3.5Diag_132000.bin" c271a5541ab7c88713b76894c59c307c5ebe9f0f77e76ee9b5d10aa30db2021a
ck_file "OpenPodReload3.5Diag_1A4000.bin" 460fd73af7e960800e95e4e141fd98fe6842b70b6f39ae510c56e259e12218f5
ck_file "OpenPodReload3.5Diag_1AB000.bin" c0bc8eca950a81e2fc4fe16d37df4f0822c957221997b0f7ee6bfac885d4e46d
ck_file "OpenPodReload3.5Diag_1AC000.bin" 3022093ebbc1a0f3eadb2fab98e8bbe74d2af2124bb442017d77852c160059c7
ck_file "OpenPodReload3.5Diag_1AD000.bin" e2f322ed2e84d951b5bcd8f6f837d2a4f84b66663002387276d1ba92b52c9bcd
ck_file "OpenPodReload3.5Diag_1AE000.bin" d2630e02f4e1e6f8ec52372668cdbaf6747700e38483a9894ce3970dfe74c479
ck_file "base_48000.bin" fd8f9e331e445088937a9f40e59ce4d8ea9d59c6757d70b115ad4e8dd51fffa6
ck_file "base_CE000.bin" 2a2c829ab51bccc16be92686e727c28a8d9d29a2e22374fcefa05fb0435813c7
ck_file "base_CF000.bin" 8880fba8f255f760bcdc1d04f5ad98f370694338c0668f225defbb76b64e45f2
ck_file "base_D0000.bin" 67ea86fd40cadc01c2cda19ec76a57d0168a198cbd55a6e8b382104e51c2d768
ck_file "base_D1000.bin" 94b1fef151d582cbcb001c44a18d2101c3139e2efe71e55a023a21e5edf0e7b3
ck_file "base_D2000.bin" 7a72f47b203da13bb231c4c392ec1da0cdd6f7cfb841cf103c278a5adf0e9189
ck_file "base_10A000.bin" ad962e28861a9a9914ef70e26cfc50283fa51daee636051a4907db930839dd6a
ck_file "base_123000.bin" a6e8c5fb593aafc7d57ba4de6505466b270b39aafb422c932d1c81c708b201b0
ck_file "base_12E000.bin" 9fa129ccd988f4c2a6a962867782b42305e82bc5610b8111f312b5779d9297cb
ck_file "base_132000.bin" c85d831ba2bc0abb2457d1ef1a294cfa01e4b5cf063c1499fbf54b3865e6cc7a
ck_file "base_1A4000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6
ck_file "base_1AB000.bin" f822d7424f404331f9c581988419629bb000eb86930b14b6dd4ea64895813d48
ck_file "base_1AC000.bin" 3333e5abb265bdde9248ada0ca3afbd007100bac551325de0ce0252a60f83564
ck_file "base_1AD000.bin" a9793232801c6e5e4a0c37b3c46aee6307ab2eef4696b7fe5bbde847f449729b
ck_file "base_1AE000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6

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
ck "FIRM" 57344 1647984 a0e6ad9b20c17ad7dcc75390cc904d1578126ce195bf314474707bdd54cb441a
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "$(m estado_err)"

log ""
log "======================================================================"
log "$(m conf1)"
log "$(m escreve) 60 KiB / 15 $(m setores)"
log "$(m muda) Player na tela inicial (ficha 028)"
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
wr "4/6 1/15" 0x48000 "OpenPodReload3.5Diag_48000.bin" f9359f759de013d1a3be4299d63ec0ef75c16bd88cfa0035f411df185abdb9c4
wr "4/6 2/15" 0xCE000 "OpenPodReload3.5Diag_CE000.bin" 89aae60a38eea6662777afad9f28a29e98e3850e15bd4cb2fa6d085141f7c205
wr "4/6 3/15" 0xCF000 "OpenPodReload3.5Diag_CF000.bin" 39c5a13e1d4b34d4f41e35766841cd57c10d7505bfcdd0f7ddbda523f5033e13
wr "4/6 4/15" 0xD0000 "OpenPodReload3.5Diag_D0000.bin" b47ab78997d8a88e67a2f8cdc197569890624c3d389986e63614e58bca2b8d1e
wr "4/6 5/15" 0xD1000 "OpenPodReload3.5Diag_D1000.bin" 3e52acea70e54a1abf810e83c9abe2cc1245bb072190fd6abdae2ec2511a1c3c
wr "4/6 6/15" 0xD2000 "OpenPodReload3.5Diag_D2000.bin" 23da3a5be0802ff3488354f9ead86e166b0541d85f5a24def84b3e6c101e4b22
wr "4/6 7/15" 0x10A000 "OpenPodReload3.5Diag_10A000.bin" 8c35d232644fbcec0e57519558b61e1d3f0a7b0d269bbadde0c4eae6ba5316d3
wr "4/6 8/15" 0x123000 "OpenPodReload3.5Diag_123000.bin" 9c9be8a117d448e5a8331ae2029d4eb227a5cf66bb02bf9410687f3def65007a
wr "4/6 9/15" 0x12E000 "OpenPodReload3.5Diag_12E000.bin" 996d2241d56cc3a1bd23f8baa356f9137d66b21e22c402138abe5b6df1bee942
wr "4/6 10/15" 0x132000 "OpenPodReload3.5Diag_132000.bin" c271a5541ab7c88713b76894c59c307c5ebe9f0f77e76ee9b5d10aa30db2021a
wr "4/6 11/15" 0x1A4000 "OpenPodReload3.5Diag_1A4000.bin" 460fd73af7e960800e95e4e141fd98fe6842b70b6f39ae510c56e259e12218f5
wr "4/6 12/15" 0x1AB000 "OpenPodReload3.5Diag_1AB000.bin" c0bc8eca950a81e2fc4fe16d37df4f0822c957221997b0f7ee6bfac885d4e46d
wr "4/6 13/15" 0x1AC000 "OpenPodReload3.5Diag_1AC000.bin" 3022093ebbc1a0f3eadb2fab98e8bbe74d2af2124bb442017d77852c160059c7
wr "4/6 14/15" 0x1AD000 "OpenPodReload3.5Diag_1AD000.bin" e2f322ed2e84d951b5bcd8f6f837d2a4f84b66663002387276d1ba92b52c9bcd
wr "4/6 15/15" 0x1AE000 "OpenPodReload3.5Diag_1AE000.bin" d2630e02f4e1e6f8ec52372668cdbaf6747700e38483a9894ce3970dfe74c479
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
ck2 "FIRM" 57344 1647984 69fc1abafd5d951c4a13b7d3b47e46ad3c8160c95b8a0845ffa6bf7fd6ae7ddd
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] OPENPODRELOAD3.5DIAG — $(m res_ok)"
    log ""
    log "$(m desconecte)"
else
    log " [6/6] $(m res_err)"
    log ""
    log "$(m nao_desligue)"
    log "     sudo $TOOL --id $DEV write_flash 0x48000 0 0x1000 base_48000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCE000 0 0x1000 base_CE000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCF000 0 0x1000 base_CF000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD0000 0 0x1000 base_D0000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD1000 0 0x1000 base_D1000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD2000 0 0x1000 base_D2000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x123000 0 0x1000 base_123000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x12E000 0 0x1000 base_12E000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x132000 0 0x1000 base_132000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A4000 0 0x1000 base_1A4000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1AB000 0 0x1000 base_1AB000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1AC000 0 0x1000 base_1AC000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1AD000 0 0x1000 base_1AD000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1AE000 0 0x1000 base_1AE000.bin"
fi
log "======================================================================"
log ""
log "$(m leve)$VERSAO.log"
log ""
