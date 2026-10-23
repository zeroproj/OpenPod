#!/bin/sh
# flash_OpenPod_OpenPodReload1.0RC6.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# OpenPod OpenPod Reload 1.0 RC6
#
# Grava 22 setores de 4096 B (88 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_OpenPod_OpenPodReload1.0RC6.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
VERSAO="OpenPod_OpenPodReload1.0RC6"
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
        log "***   sudo $TOOL --id $DEV write_flash 0x12E000 0 0x1000 base_12E000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x156000 0 0x1000 base_156000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A3000 0 0x1000 base_1A3000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A4000 0 0x1000 base_1A4000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A5000 0 0x1000 base_1A5000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A6000 0 0x1000 base_1A6000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A7000 0 0x1000 base_1A7000.bin"
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
log "$(m hdr) OPENPOD_OPENPODRELOAD1.0RC6   (22 $(m setores), 88 KiB)"
log " 0x048000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_48000.bin"
log " 0x053000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_53000.bin"
log " 0x0C7000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_C7000.bin"
log " 0x0CC000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_CC000.bin"
log " 0x0CD000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_CD000.bin"
log " 0x0CE000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_CE000.bin"
log " 0x0CF000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_CF000.bin"
log " 0x0D0000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_D0000.bin"
log " 0x0D1000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_D1000.bin"
log " 0x0D2000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_D2000.bin"
log " 0x0D3000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_D3000.bin"
log " 0x109000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_109000.bin"
log " 0x10A000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_10A000.bin"
log " 0x121000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_121000.bin"
log " 0x122000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_122000.bin"
log " 0x12E000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_12E000.bin"
log " 0x156000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_156000.bin"
log " 0x1A3000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_1A3000.bin"
log " 0x1A4000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_1A4000.bin"
log " 0x1A5000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_1A5000.bin"
log " 0x1A6000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_1A6000.bin"
log " 0x1A7000 +0x1000   <- OpenPod_OpenPodReload1.0RC6_1A7000.bin"
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
ck_file "OpenPod_OpenPodReload1.0RC6_48000.bin" 686de926ce218ab8654f0a1565ab4206a787e18de8951edeef859c6ce6f3abda
ck_file "OpenPod_OpenPodReload1.0RC6_53000.bin" 375f0cd07c44dbdcce0851620088623eb65d3838b25cd03b2726df5e5433a4de
ck_file "OpenPod_OpenPodReload1.0RC6_C7000.bin" f678974cafcb27f9b636e9713360e6f34a9d03f1b6082f3de9897e1513f3a421
ck_file "OpenPod_OpenPodReload1.0RC6_CC000.bin" ef8ffb2966867c44f8a87315ad7469a97018d0b7367ce864c19ffa102a8ba165
ck_file "OpenPod_OpenPodReload1.0RC6_CD000.bin" d0c5465d70e6235fa28a635d78a052866a4cb88715d490652196225e4dd9d463
ck_file "OpenPod_OpenPodReload1.0RC6_CE000.bin" 09d0c2e38fd6444a74e5c81a9c0128258e0ca7c844791482060d7198cb480d9e
ck_file "OpenPod_OpenPodReload1.0RC6_CF000.bin" f43003839101eec5f795415ed777e13f98a0c064a0e7fab105e794e6c7bf7a6a
ck_file "OpenPod_OpenPodReload1.0RC6_D0000.bin" dbfdb7cc759998de66d982f46deeaf1c620bc30e76cfc7d121e3691b2a3187e6
ck_file "OpenPod_OpenPodReload1.0RC6_D1000.bin" e2fb141bed6667eda01dc0643d2596b7d49864926e61bc1d326b7542dbbb7415
ck_file "OpenPod_OpenPodReload1.0RC6_D2000.bin" 8aea4c36ba5f9cdf27c088842264167c543dae1a23a173f92904c158a74d8bbd
ck_file "OpenPod_OpenPodReload1.0RC6_D3000.bin" 9e242a69a939a614a750587d1e62df82126d0068ab6b6a72d76deca52a0639b3
ck_file "OpenPod_OpenPodReload1.0RC6_109000.bin" 3bc16bacee418a50f79df0aa7c3f5604241fc55f126ee8d7bec7d802849312c2
ck_file "OpenPod_OpenPodReload1.0RC6_10A000.bin" 8c35d232644fbcec0e57519558b61e1d3f0a7b0d269bbadde0c4eae6ba5316d3
ck_file "OpenPod_OpenPodReload1.0RC6_121000.bin" ba21f47d4ae0797174245e1bd9fb837afdfd8619184d01b4d1553116e3daed1e
ck_file "OpenPod_OpenPodReload1.0RC6_122000.bin" f1a868b530c26ea9b1c55b95e453cd32d6d8c97101f944ba367273c1beb214fe
ck_file "OpenPod_OpenPodReload1.0RC6_12E000.bin" 9fa129ccd988f4c2a6a962867782b42305e82bc5610b8111f312b5779d9297cb
ck_file "OpenPod_OpenPodReload1.0RC6_156000.bin" 09ea275aa3916096700af353b3a9b51b3f51ab9fcad3a8ee616a504bae18d60d
ck_file "OpenPod_OpenPodReload1.0RC6_1A3000.bin" af75be67379e86296b217b520d2ef959fcfaff0bbe6aae9f712e4422452ab683
ck_file "OpenPod_OpenPodReload1.0RC6_1A4000.bin" 3ae337a1e13fbedb256cf811702b97af4cdd993c61722c3b4344e9a2937ae265
ck_file "OpenPod_OpenPodReload1.0RC6_1A5000.bin" 635b023a309245579152502c2e06268e963f0f2158bcd6f41838bf3d9d81760c
ck_file "OpenPod_OpenPodReload1.0RC6_1A6000.bin" 25d6784a3323dc277f51e9bcff59c53121c11c743f2be8e68cc398f1921c4dcc
ck_file "OpenPod_OpenPodReload1.0RC6_1A7000.bin" 142b9638e43a185341ae27973131aa4bc2cf998c5d16defb8852bd1ba5fe0b02
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
ck_file "base_109000.bin" 40e5a7786b3a7c82c786da0effb5036c6da0c234462dfaa5c435581cf5f03411
ck_file "base_10A000.bin" ad962e28861a9a9914ef70e26cfc50283fa51daee636051a4907db930839dd6a
ck_file "base_121000.bin" dbea2b9d18646cad64d3a5ea402a2a633bb0c4036fca689ad997ecb2545ba9ac
ck_file "base_122000.bin" dc3b6a4a0150763564474047400cebac7b4e331820901505eacf3644083c7c48
ck_file "base_12E000.bin" e135e686ad0de20f085fc204494b51873731b520ad24930487896b63b29109cc
ck_file "base_156000.bin" b1791e9f5e5a62402d93ada9f3174129843ed8af22b7d23904d5cd472e9b43c5
ck_file "base_1A3000.bin" 6f4ef0b382a9fa4d2792e8446613308544b251e2d512ea1b5d3b83ce8f1d10e4
ck_file "base_1A4000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6
ck_file "base_1A5000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6
ck_file "base_1A6000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6
ck_file "base_1A7000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6

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
log "$(m escreve) 88 KiB / 22 $(m setores)"
log "$(m muda) OpenPod OpenPod Reload 1.0 RC6"
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
wr "4/6 1/22" 0x48000 "OpenPod_OpenPodReload1.0RC6_48000.bin" 686de926ce218ab8654f0a1565ab4206a787e18de8951edeef859c6ce6f3abda
wr "4/6 2/22" 0x53000 "OpenPod_OpenPodReload1.0RC6_53000.bin" 375f0cd07c44dbdcce0851620088623eb65d3838b25cd03b2726df5e5433a4de
wr "4/6 3/22" 0xC7000 "OpenPod_OpenPodReload1.0RC6_C7000.bin" f678974cafcb27f9b636e9713360e6f34a9d03f1b6082f3de9897e1513f3a421
wr "4/6 4/22" 0xCC000 "OpenPod_OpenPodReload1.0RC6_CC000.bin" ef8ffb2966867c44f8a87315ad7469a97018d0b7367ce864c19ffa102a8ba165
wr "4/6 5/22" 0xCD000 "OpenPod_OpenPodReload1.0RC6_CD000.bin" d0c5465d70e6235fa28a635d78a052866a4cb88715d490652196225e4dd9d463
wr "4/6 6/22" 0xCE000 "OpenPod_OpenPodReload1.0RC6_CE000.bin" 09d0c2e38fd6444a74e5c81a9c0128258e0ca7c844791482060d7198cb480d9e
wr "4/6 7/22" 0xCF000 "OpenPod_OpenPodReload1.0RC6_CF000.bin" f43003839101eec5f795415ed777e13f98a0c064a0e7fab105e794e6c7bf7a6a
wr "4/6 8/22" 0xD0000 "OpenPod_OpenPodReload1.0RC6_D0000.bin" dbfdb7cc759998de66d982f46deeaf1c620bc30e76cfc7d121e3691b2a3187e6
wr "4/6 9/22" 0xD1000 "OpenPod_OpenPodReload1.0RC6_D1000.bin" e2fb141bed6667eda01dc0643d2596b7d49864926e61bc1d326b7542dbbb7415
wr "4/6 10/22" 0xD2000 "OpenPod_OpenPodReload1.0RC6_D2000.bin" 8aea4c36ba5f9cdf27c088842264167c543dae1a23a173f92904c158a74d8bbd
wr "4/6 11/22" 0xD3000 "OpenPod_OpenPodReload1.0RC6_D3000.bin" 9e242a69a939a614a750587d1e62df82126d0068ab6b6a72d76deca52a0639b3
wr "4/6 12/22" 0x109000 "OpenPod_OpenPodReload1.0RC6_109000.bin" 3bc16bacee418a50f79df0aa7c3f5604241fc55f126ee8d7bec7d802849312c2
wr "4/6 13/22" 0x10A000 "OpenPod_OpenPodReload1.0RC6_10A000.bin" 8c35d232644fbcec0e57519558b61e1d3f0a7b0d269bbadde0c4eae6ba5316d3
wr "4/6 14/22" 0x121000 "OpenPod_OpenPodReload1.0RC6_121000.bin" ba21f47d4ae0797174245e1bd9fb837afdfd8619184d01b4d1553116e3daed1e
wr "4/6 15/22" 0x122000 "OpenPod_OpenPodReload1.0RC6_122000.bin" f1a868b530c26ea9b1c55b95e453cd32d6d8c97101f944ba367273c1beb214fe
wr "4/6 16/22" 0x12E000 "OpenPod_OpenPodReload1.0RC6_12E000.bin" 9fa129ccd988f4c2a6a962867782b42305e82bc5610b8111f312b5779d9297cb
wr "4/6 17/22" 0x156000 "OpenPod_OpenPodReload1.0RC6_156000.bin" 09ea275aa3916096700af353b3a9b51b3f51ab9fcad3a8ee616a504bae18d60d
wr "4/6 18/22" 0x1A3000 "OpenPod_OpenPodReload1.0RC6_1A3000.bin" af75be67379e86296b217b520d2ef959fcfaff0bbe6aae9f712e4422452ab683
wr "4/6 19/22" 0x1A4000 "OpenPod_OpenPodReload1.0RC6_1A4000.bin" 3ae337a1e13fbedb256cf811702b97af4cdd993c61722c3b4344e9a2937ae265
wr "4/6 20/22" 0x1A5000 "OpenPod_OpenPodReload1.0RC6_1A5000.bin" 635b023a309245579152502c2e06268e963f0f2158bcd6f41838bf3d9d81760c
wr "4/6 21/22" 0x1A6000 "OpenPod_OpenPodReload1.0RC6_1A6000.bin" 25d6784a3323dc277f51e9bcff59c53121c11c743f2be8e68cc398f1921c4dcc
wr "4/6 22/22" 0x1A7000 "OpenPod_OpenPodReload1.0RC6_1A7000.bin" 142b9638e43a185341ae27973131aa4bc2cf998c5d16defb8852bd1ba5fe0b02
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
ck2 "FIRM" 57344 1647984 527ed1681aad857ceba963b7c67903e3f7fb668aaf82579d13438442f5337221
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] OPENPOD_OPENPODRELOAD1.0RC6 — $(m res_ok)"
    log ""
    log "$(m desconecte)"
else
    log " [6/6] $(m res_err)"
    log ""
    log "$(m nao_desligue)"
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
    log "     sudo $TOOL --id $DEV write_flash 0x109000 0 0x1000 base_109000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x121000 0 0x1000 base_121000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x122000 0 0x1000 base_122000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x12E000 0 0x1000 base_12E000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x156000 0 0x1000 base_156000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A3000 0 0x1000 base_1A3000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A4000 0 0x1000 base_1A4000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A5000 0 0x1000 base_1A5000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A6000 0 0x1000 base_1A6000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A7000 0 0x1000 base_1A7000.bin"
fi
log "======================================================================"
log ""
log "$(m leve)$VERSAO.log"
log ""
