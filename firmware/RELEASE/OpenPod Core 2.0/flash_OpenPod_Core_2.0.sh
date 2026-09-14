#!/bin/sh
# flash_OpenPod_Core_2.0.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# A carcaca da interface: home em lista, faixa com titulo, tabela de tema.
#
# Grava 38 setores de 4096 B (152 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_OpenPod_Core_2.0.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
VERSAO="OpenPod_Core_2.0"
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
        log "***   sudo $TOOL --id $DEV write_flash 0x48000 0 0x1000 base_48000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCD000 0 0x1000 base_CD000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCE000 0 0x1000 base_CE000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCF000 0 0x1000 base_CF000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD0000 0 0x1000 base_D0000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD1000 0 0x1000 base_D1000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD2000 0 0x1000 base_D2000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
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
        log "***   sudo $TOOL --id $DEV write_flash 0x1A3000 0 0x1000 base_1A3000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A4000 0 0x1000 base_1A4000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A5000 0 0x1000 base_1A5000.bin"
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
log " OpenPod — gravacao do OPENPOD CORE 2.0   (38 setores, 152 KiB)"
log " 0x048000 +0x1000   <- OpenPod_Core_2.0_48000.bin"
log " 0x0CD000 +0x1000   <- OpenPod_Core_2.0_CD000.bin"
log " 0x0CE000 +0x1000   <- OpenPod_Core_2.0_CE000.bin"
log " 0x0CF000 +0x1000   <- OpenPod_Core_2.0_CF000.bin"
log " 0x0D0000 +0x1000   <- OpenPod_Core_2.0_D0000.bin"
log " 0x0D1000 +0x1000   <- OpenPod_Core_2.0_D1000.bin"
log " 0x0D2000 +0x1000   <- OpenPod_Core_2.0_D2000.bin"
log " 0x10A000 +0x1000   <- OpenPod_Core_2.0_10A000.bin"
log " 0x121000 +0x1000   <- OpenPod_Core_2.0_121000.bin"
log " 0x122000 +0x1000   <- OpenPod_Core_2.0_122000.bin"
log " 0x123000 +0x1000   <- OpenPod_Core_2.0_123000.bin"
log " 0x126000 +0x1000   <- OpenPod_Core_2.0_126000.bin"
log " 0x127000 +0x1000   <- OpenPod_Core_2.0_127000.bin"
log " 0x128000 +0x1000   <- OpenPod_Core_2.0_128000.bin"
log " 0x129000 +0x1000   <- OpenPod_Core_2.0_129000.bin"
log " 0x12A000 +0x1000   <- OpenPod_Core_2.0_12A000.bin"
log " 0x12B000 +0x1000   <- OpenPod_Core_2.0_12B000.bin"
log " 0x12C000 +0x1000   <- OpenPod_Core_2.0_12C000.bin"
log " 0x12D000 +0x1000   <- OpenPod_Core_2.0_12D000.bin"
log " 0x12E000 +0x1000   <- OpenPod_Core_2.0_12E000.bin"
log " 0x12F000 +0x1000   <- OpenPod_Core_2.0_12F000.bin"
log " 0x130000 +0x1000   <- OpenPod_Core_2.0_130000.bin"
log " 0x131000 +0x1000   <- OpenPod_Core_2.0_131000.bin"
log " 0x132000 +0x1000   <- OpenPod_Core_2.0_132000.bin"
log " 0x133000 +0x1000   <- OpenPod_Core_2.0_133000.bin"
log " 0x134000 +0x1000   <- OpenPod_Core_2.0_134000.bin"
log " 0x135000 +0x1000   <- OpenPod_Core_2.0_135000.bin"
log " 0x136000 +0x1000   <- OpenPod_Core_2.0_136000.bin"
log " 0x137000 +0x1000   <- OpenPod_Core_2.0_137000.bin"
log " 0x138000 +0x1000   <- OpenPod_Core_2.0_138000.bin"
log " 0x139000 +0x1000   <- OpenPod_Core_2.0_139000.bin"
log " 0x13A000 +0x1000   <- OpenPod_Core_2.0_13A000.bin"
log " 0x13B000 +0x1000   <- OpenPod_Core_2.0_13B000.bin"
log " 0x13C000 +0x1000   <- OpenPod_Core_2.0_13C000.bin"
log " 0x13D000 +0x1000   <- OpenPod_Core_2.0_13D000.bin"
log " 0x1A3000 +0x1000   <- OpenPod_Core_2.0_1A3000.bin"
log " 0x1A4000 +0x1000   <- OpenPod_Core_2.0_1A4000.bin"
log " 0x1A5000 +0x1000   <- OpenPod_Core_2.0_1A5000.bin"
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
ck_file "OpenPod_Core_2.0_48000.bin" a45303734ee0fc80530bbe803f6603505f36b133fa770f1b17f662c596068edc
ck_file "OpenPod_Core_2.0_CD000.bin" f51cf984cf9e75ed6f112b3c0111a98db1b4dd2e9b3690e574d46cc5e7e37426
ck_file "OpenPod_Core_2.0_CE000.bin" 268612f901bf76ee02d81839387067e7c729759a82bbf3ffd7a11907419d3ae3
ck_file "OpenPod_Core_2.0_CF000.bin" 6765c47e8934259006fa526a0e42ea8faf274c28758451d940539d1c28d38982
ck_file "OpenPod_Core_2.0_D0000.bin" 6765c47e8934259006fa526a0e42ea8faf274c28758451d940539d1c28d38982
ck_file "OpenPod_Core_2.0_D1000.bin" 6765c47e8934259006fa526a0e42ea8faf274c28758451d940539d1c28d38982
ck_file "OpenPod_Core_2.0_D2000.bin" 6765c47e8934259006fa526a0e42ea8faf274c28758451d940539d1c28d38982
ck_file "OpenPod_Core_2.0_10A000.bin" 8c35d232644fbcec0e57519558b61e1d3f0a7b0d269bbadde0c4eae6ba5316d3
ck_file "OpenPod_Core_2.0_121000.bin" 207074b906bf0fe4830e2d66ed56b972c21690c31dda86ec132b752ae9025a9e
ck_file "OpenPod_Core_2.0_122000.bin" 468fa023f05059785f071b183afcc255a81626ba54896b2d460aa2cd7f37559f
ck_file "OpenPod_Core_2.0_123000.bin" 56f6996c47eceda5076a0202b0b0b678c5135fede20b97a29a025e798d856723
ck_file "OpenPod_Core_2.0_126000.bin" f64787945149cab69de6c35d5cf9962170d23bcca2ad984d226dadfb96934fa8
ck_file "OpenPod_Core_2.0_127000.bin" 1c235dc2ba59303641cefe6ac64409d0b4bc0815d4c4cabc55b430795af17c78
ck_file "OpenPod_Core_2.0_128000.bin" 9796f96c62223cf50b388deb747ba74c11252e63f46be3f27e337e5b63643b15
ck_file "OpenPod_Core_2.0_129000.bin" e05b6c3408132f0c03e7dbd13612f9bde06f793a7c15bbcc592485d59cd37a32
ck_file "OpenPod_Core_2.0_12A000.bin" 6e260ae5a7ca61b72d4d90e9fe3b72dc728d183a50dbec587c66aa534766803e
ck_file "OpenPod_Core_2.0_12B000.bin" 9d9077fed5570dd05581cde677adac049f9463e9a22f8d25f2677e8444451edf
ck_file "OpenPod_Core_2.0_12C000.bin" 18320484779cc6fb338904a1e1edf9638dab71dd39315f66811faeeb5afcc22a
ck_file "OpenPod_Core_2.0_12D000.bin" d1c0cdd6a07456c411b905bcbef76969639fedab9c185e3d31ea3cb991e675b7
ck_file "OpenPod_Core_2.0_12E000.bin" 7a025bbb63b5a88548f63bc839d5eebb4f8f2449e5f9c119011735d33e742f6d
ck_file "OpenPod_Core_2.0_12F000.bin" fbcdb265734294c844b4a89b3c666b2d412fd21fbaea26336824143562dae492
ck_file "OpenPod_Core_2.0_130000.bin" 761c66a590f555a92e655960e90b3a5ab4f5ed728c965c765da309b526dce613
ck_file "OpenPod_Core_2.0_131000.bin" 5b749e6d71982125ec99df57766260450ace31af5f31559f900455afd17e410b
ck_file "OpenPod_Core_2.0_132000.bin" df140c90cd0dd2f2bc4b4c0322b0631be402fbf7027c5342fca2ecc48471a605
ck_file "OpenPod_Core_2.0_133000.bin" 73d1019ddc88c7e4b46d79bfd2f0e442b9bf20291cef50ac7d11635977e91a48
ck_file "OpenPod_Core_2.0_134000.bin" be92e3c32a6fa4232ef6915a926a0cf3ec4bcad399481c97396db99fb82837de
ck_file "OpenPod_Core_2.0_135000.bin" 943a4bc523784f3645162eff8071ce8832c6404bf581a9c2dc39821fbe012cb4
ck_file "OpenPod_Core_2.0_136000.bin" f8b2c6a08f548005ec064e1a98d7b34dbb58fcab276f201fa21ac8c3e7066a87
ck_file "OpenPod_Core_2.0_137000.bin" 4b3c256dca2dc15e4fc6150c05bc95671a4964892970e5d0049bbee250a53bd5
ck_file "OpenPod_Core_2.0_138000.bin" 3746fcf5d0c9536e4ed6f0b90ef9b90acb60d787bce1e30c7bd8bf00cacd534a
ck_file "OpenPod_Core_2.0_139000.bin" f34cdfef6e1ad9b00c1651af0dff296be2693c39b8a6d526215f2211555a8da7
ck_file "OpenPod_Core_2.0_13A000.bin" f380204929cecc60b37cde55ff6f4c24ea9b02fb67640da9e821d6803730aa92
ck_file "OpenPod_Core_2.0_13B000.bin" 4149ec06285a44fd806acec271cbe34beaf6d8b271d9efa972e83004d8930090
ck_file "OpenPod_Core_2.0_13C000.bin" ce42171c262ea6868b36ec29fb314996966ea637440c91ae5aac6a11d4102221
ck_file "OpenPod_Core_2.0_13D000.bin" f3d20028d9fe994e7a335fa9df8cae4a2dd0ccd7b08d420c313c609ca8827f85
ck_file "OpenPod_Core_2.0_1A3000.bin" d0008a84d9e70fdb69574635372731a8d4b5d8ff6116036f5e8161076890ef67
ck_file "OpenPod_Core_2.0_1A4000.bin" 02ead2577c26da4138c7b5b1043a8f53de3b74b8f3de17a2fff14457903bf9ae
ck_file "OpenPod_Core_2.0_1A5000.bin" 0fe0d3f4359e92a39d854d76e860084f6595f73f9911a15017a0cfc512594fe3
ck_file "base_48000.bin" 41308534ac9a54ca3960d82de64dcef4959c85b9278d2a1c82eac5c1ed5afd5b
ck_file "base_CD000.bin" 99d56432ede44c31aa9fc2b928c7965db70129bd8e4bc3f3a9b00b82abd4554e
ck_file "base_CE000.bin" f46bdf8b56e3b463e8461ea5b35bfae201cafda178ac8296a5c2d8bc19cbf175
ck_file "base_CF000.bin" cb87b8bb4828c63b87c36788f17d54049cf1b4c21e5757e0204a5e693fecf683
ck_file "base_D0000.bin" 0d7deca9d471b627b9eaede3872d233da2b9b643006476fe654f3d504713a8cf
ck_file "base_D1000.bin" 0d7ab5dc9d9ad6d369103ebd1db42c77e31d4969bece99fdb25943bd1df1db41
ck_file "base_D2000.bin" a0e9f30c578c5f06f9d0428b53eb181e1097ad5a6342f3837e4f6646c0a1f3fe
ck_file "base_10A000.bin" 59c1e2e2b2a76131daeb2dbe1fe19d9f362903a36c45fa2782fdb0b1b223c856
ck_file "base_121000.bin" 5a210420e87bf0f9da73338e0f0ddac91018e0715207660cbeda881e02828c90
ck_file "base_122000.bin" 23d44d20cd914ab860eedd25f938eece99af4a059e8e229b3a33e6195fef06ac
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
ck_file "base_1A3000.bin" a8d62682b5a02eb5a2287e58a4754385d579a16e05b2c23de5821b458dad074f
ck_file "base_1A4000.bin" 1e9d3b128b55dbada2d51ce0ce01365fd23126f5be34629626825d333cffdec0
ck_file "base_1A5000.bin" f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6

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
ck "FIRM" 57344 1647984 a97035e918938668fef304a37037900645d8c0e1bacb22360ed5ce8157a3e7e4
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."

log ""
log "======================================================================"
log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."
log "   grava  : 152 KiB em 38 setores"
log "   muda   : A carcaca da interface: home em lista, faixa com titulo, tabela de tema."
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
wr "4/6 1/38" 0x48000 "OpenPod_Core_2.0_48000.bin" a45303734ee0fc80530bbe803f6603505f36b133fa770f1b17f662c596068edc
wr "4/6 2/38" 0xCD000 "OpenPod_Core_2.0_CD000.bin" f51cf984cf9e75ed6f112b3c0111a98db1b4dd2e9b3690e574d46cc5e7e37426
wr "4/6 3/38" 0xCE000 "OpenPod_Core_2.0_CE000.bin" 268612f901bf76ee02d81839387067e7c729759a82bbf3ffd7a11907419d3ae3
wr "4/6 4/38" 0xCF000 "OpenPod_Core_2.0_CF000.bin" 6765c47e8934259006fa526a0e42ea8faf274c28758451d940539d1c28d38982
wr "4/6 5/38" 0xD0000 "OpenPod_Core_2.0_D0000.bin" 6765c47e8934259006fa526a0e42ea8faf274c28758451d940539d1c28d38982
wr "4/6 6/38" 0xD1000 "OpenPod_Core_2.0_D1000.bin" 6765c47e8934259006fa526a0e42ea8faf274c28758451d940539d1c28d38982
wr "4/6 7/38" 0xD2000 "OpenPod_Core_2.0_D2000.bin" 6765c47e8934259006fa526a0e42ea8faf274c28758451d940539d1c28d38982
wr "4/6 8/38" 0x10A000 "OpenPod_Core_2.0_10A000.bin" 8c35d232644fbcec0e57519558b61e1d3f0a7b0d269bbadde0c4eae6ba5316d3
wr "4/6 9/38" 0x121000 "OpenPod_Core_2.0_121000.bin" 207074b906bf0fe4830e2d66ed56b972c21690c31dda86ec132b752ae9025a9e
wr "4/6 10/38" 0x122000 "OpenPod_Core_2.0_122000.bin" 468fa023f05059785f071b183afcc255a81626ba54896b2d460aa2cd7f37559f
wr "4/6 11/38" 0x123000 "OpenPod_Core_2.0_123000.bin" 56f6996c47eceda5076a0202b0b0b678c5135fede20b97a29a025e798d856723
wr "4/6 12/38" 0x126000 "OpenPod_Core_2.0_126000.bin" f64787945149cab69de6c35d5cf9962170d23bcca2ad984d226dadfb96934fa8
wr "4/6 13/38" 0x127000 "OpenPod_Core_2.0_127000.bin" 1c235dc2ba59303641cefe6ac64409d0b4bc0815d4c4cabc55b430795af17c78
wr "4/6 14/38" 0x128000 "OpenPod_Core_2.0_128000.bin" 9796f96c62223cf50b388deb747ba74c11252e63f46be3f27e337e5b63643b15
wr "4/6 15/38" 0x129000 "OpenPod_Core_2.0_129000.bin" e05b6c3408132f0c03e7dbd13612f9bde06f793a7c15bbcc592485d59cd37a32
wr "4/6 16/38" 0x12A000 "OpenPod_Core_2.0_12A000.bin" 6e260ae5a7ca61b72d4d90e9fe3b72dc728d183a50dbec587c66aa534766803e
wr "4/6 17/38" 0x12B000 "OpenPod_Core_2.0_12B000.bin" 9d9077fed5570dd05581cde677adac049f9463e9a22f8d25f2677e8444451edf
wr "4/6 18/38" 0x12C000 "OpenPod_Core_2.0_12C000.bin" 18320484779cc6fb338904a1e1edf9638dab71dd39315f66811faeeb5afcc22a
wr "4/6 19/38" 0x12D000 "OpenPod_Core_2.0_12D000.bin" d1c0cdd6a07456c411b905bcbef76969639fedab9c185e3d31ea3cb991e675b7
wr "4/6 20/38" 0x12E000 "OpenPod_Core_2.0_12E000.bin" 7a025bbb63b5a88548f63bc839d5eebb4f8f2449e5f9c119011735d33e742f6d
wr "4/6 21/38" 0x12F000 "OpenPod_Core_2.0_12F000.bin" fbcdb265734294c844b4a89b3c666b2d412fd21fbaea26336824143562dae492
wr "4/6 22/38" 0x130000 "OpenPod_Core_2.0_130000.bin" 761c66a590f555a92e655960e90b3a5ab4f5ed728c965c765da309b526dce613
wr "4/6 23/38" 0x131000 "OpenPod_Core_2.0_131000.bin" 5b749e6d71982125ec99df57766260450ace31af5f31559f900455afd17e410b
wr "4/6 24/38" 0x132000 "OpenPod_Core_2.0_132000.bin" df140c90cd0dd2f2bc4b4c0322b0631be402fbf7027c5342fca2ecc48471a605
wr "4/6 25/38" 0x133000 "OpenPod_Core_2.0_133000.bin" 73d1019ddc88c7e4b46d79bfd2f0e442b9bf20291cef50ac7d11635977e91a48
wr "4/6 26/38" 0x134000 "OpenPod_Core_2.0_134000.bin" be92e3c32a6fa4232ef6915a926a0cf3ec4bcad399481c97396db99fb82837de
wr "4/6 27/38" 0x135000 "OpenPod_Core_2.0_135000.bin" 943a4bc523784f3645162eff8071ce8832c6404bf581a9c2dc39821fbe012cb4
wr "4/6 28/38" 0x136000 "OpenPod_Core_2.0_136000.bin" f8b2c6a08f548005ec064e1a98d7b34dbb58fcab276f201fa21ac8c3e7066a87
wr "4/6 29/38" 0x137000 "OpenPod_Core_2.0_137000.bin" 4b3c256dca2dc15e4fc6150c05bc95671a4964892970e5d0049bbee250a53bd5
wr "4/6 30/38" 0x138000 "OpenPod_Core_2.0_138000.bin" 3746fcf5d0c9536e4ed6f0b90ef9b90acb60d787bce1e30c7bd8bf00cacd534a
wr "4/6 31/38" 0x139000 "OpenPod_Core_2.0_139000.bin" f34cdfef6e1ad9b00c1651af0dff296be2693c39b8a6d526215f2211555a8da7
wr "4/6 32/38" 0x13A000 "OpenPod_Core_2.0_13A000.bin" f380204929cecc60b37cde55ff6f4c24ea9b02fb67640da9e821d6803730aa92
wr "4/6 33/38" 0x13B000 "OpenPod_Core_2.0_13B000.bin" 4149ec06285a44fd806acec271cbe34beaf6d8b271d9efa972e83004d8930090
wr "4/6 34/38" 0x13C000 "OpenPod_Core_2.0_13C000.bin" ce42171c262ea6868b36ec29fb314996966ea637440c91ae5aac6a11d4102221
wr "4/6 35/38" 0x13D000 "OpenPod_Core_2.0_13D000.bin" f3d20028d9fe994e7a335fa9df8cae4a2dd0ccd7b08d420c313c609ca8827f85
wr "4/6 36/38" 0x1A3000 "OpenPod_Core_2.0_1A3000.bin" d0008a84d9e70fdb69574635372731a8d4b5d8ff6116036f5e8161076890ef67
wr "4/6 37/38" 0x1A4000 "OpenPod_Core_2.0_1A4000.bin" 02ead2577c26da4138c7b5b1043a8f53de3b74b8f3de17a2fff14457903bf9ae
wr "4/6 38/38" 0x1A5000 "OpenPod_Core_2.0_1A5000.bin" 0fe0d3f4359e92a39d854d76e860084f6595f73f9911a15017a0cfc512594fe3
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
ck2 "FIRM" 57344 1647984 de569488054688e457a64d59fa59c36caaf745d46e59ebca6ba98ae829796eef
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] RESULTADO: OPENPOD CORE 2.0 GRAVADO E VERIFICADO"
    log ""
    log "   Desconecte e abra o menu principal."
else
    log " [6/6] RESULTADO: ALGUMA REGIAO NAO CONFERE"
    log ""
    log "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:"
    log "     sudo $TOOL --id $DEV write_flash 0x48000 0 0x1000 base_48000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCD000 0 0x1000 base_CD000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCE000 0 0x1000 base_CE000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCF000 0 0x1000 base_CF000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD0000 0 0x1000 base_D0000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD1000 0 0x1000 base_D1000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD2000 0 0x1000 base_D2000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
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
    log "     sudo $TOOL --id $DEV write_flash 0x1A3000 0 0x1000 base_1A3000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A4000 0 0x1000 base_1A4000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A5000 0 0x1000 base_1A5000.bin"
fi
log "======================================================================"
log ""
log "  leve de volta: before.bin  after.bin  flash_$VERSAO.log"
log ""
