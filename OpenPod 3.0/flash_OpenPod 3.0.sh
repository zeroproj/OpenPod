#!/bin/sh
# flash_OpenPod 3.0.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# Primeira imagem RECONSTRUIDA do ORIGINAL por receita declarada (tools/build.py).
#
# Grava 41 setores de 4096 B (164 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_OpenPod 3.0.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
WORK=$(pwd)/openpod_flash_OpenPod 3.0
LOG="$WORK/flash_OpenPod 3.0.log"
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
        log "***   sudo $TOOL --id $DEV write_flash 0x1A4000 0 0x1000 base_1A4000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x1A5000 0 0x1000 base_1A5000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x48000 0 0x1000 base_48000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x53000 0 0x1000 base_53000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCC000 0 0x1000 base_CC000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCD000 0 0x1000 base_CD000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCE000 0 0x1000 base_CE000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xCF000 0 0x1000 base_CF000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0xD0000 0 0x1000 base_D0000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x100000 0 0x1000 base_100000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x109000 0 0x1000 base_109000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x10C000 0 0x1000 base_10C000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x121000 0 0x1000 base_121000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x122000 0 0x1000 base_122000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x123000 0 0x1000 base_123000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x126000 0 0x1000 base_126000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x127000 0 0x1000 base_127000.bin"
        log "***   sudo $TOOL --id $DEV write_flash 0x128000 0 0x1000 base_128000.bin"
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
        log "***   sudo $TOOL --id $DEV write_flash 0x156000 0 0x1000 base_156000.bin"
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
log " OpenPod — gravacao do OPENPOD 3.0   (41 setores, 164 KiB)"
log " 0x1A3000 +0x1000   <- OpenPod 3.0_1A3000.bin"
log " 0x1A4000 +0x1000   <- OpenPod 3.0_1A4000.bin"
log " 0x1A5000 +0x1000   <- OpenPod 3.0_1A5000.bin"
log " 0x048000 +0x1000   <- OpenPod 3.0_48000.bin"
log " 0x053000 +0x1000   <- OpenPod 3.0_53000.bin"
log " 0x0CC000 +0x1000   <- OpenPod 3.0_CC000.bin"
log " 0x0CD000 +0x1000   <- OpenPod 3.0_CD000.bin"
log " 0x0CE000 +0x1000   <- OpenPod 3.0_CE000.bin"
log " 0x0CF000 +0x1000   <- OpenPod 3.0_CF000.bin"
log " 0x0D0000 +0x1000   <- OpenPod 3.0_D0000.bin"
log " 0x100000 +0x1000   <- OpenPod 3.0_100000.bin"
log " 0x109000 +0x1000   <- OpenPod 3.0_109000.bin"
log " 0x10A000 +0x1000   <- OpenPod 3.0_10A000.bin"
log " 0x10C000 +0x1000   <- OpenPod 3.0_10C000.bin"
log " 0x121000 +0x1000   <- OpenPod 3.0_121000.bin"
log " 0x122000 +0x1000   <- OpenPod 3.0_122000.bin"
log " 0x123000 +0x1000   <- OpenPod 3.0_123000.bin"
log " 0x126000 +0x1000   <- OpenPod 3.0_126000.bin"
log " 0x127000 +0x1000   <- OpenPod 3.0_127000.bin"
log " 0x128000 +0x1000   <- OpenPod 3.0_128000.bin"
log " 0x12A000 +0x1000   <- OpenPod 3.0_12A000.bin"
log " 0x12B000 +0x1000   <- OpenPod 3.0_12B000.bin"
log " 0x12C000 +0x1000   <- OpenPod 3.0_12C000.bin"
log " 0x12D000 +0x1000   <- OpenPod 3.0_12D000.bin"
log " 0x12E000 +0x1000   <- OpenPod 3.0_12E000.bin"
log " 0x12F000 +0x1000   <- OpenPod 3.0_12F000.bin"
log " 0x130000 +0x1000   <- OpenPod 3.0_130000.bin"
log " 0x131000 +0x1000   <- OpenPod 3.0_131000.bin"
log " 0x132000 +0x1000   <- OpenPod 3.0_132000.bin"
log " 0x133000 +0x1000   <- OpenPod 3.0_133000.bin"
log " 0x134000 +0x1000   <- OpenPod 3.0_134000.bin"
log " 0x135000 +0x1000   <- OpenPod 3.0_135000.bin"
log " 0x136000 +0x1000   <- OpenPod 3.0_136000.bin"
log " 0x137000 +0x1000   <- OpenPod 3.0_137000.bin"
log " 0x138000 +0x1000   <- OpenPod 3.0_138000.bin"
log " 0x139000 +0x1000   <- OpenPod 3.0_139000.bin"
log " 0x13A000 +0x1000   <- OpenPod 3.0_13A000.bin"
log " 0x13B000 +0x1000   <- OpenPod 3.0_13B000.bin"
log " 0x13C000 +0x1000   <- OpenPod 3.0_13C000.bin"
log " 0x13D000 +0x1000   <- OpenPod 3.0_13D000.bin"
log " 0x156000 +0x1000   <- OpenPod 3.0_156000.bin"
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
ck_file OpenPod 3.0_1A3000.bin c7ebd237e44ae52fa0f0ae12e1045498a3e89be89932c2fcabc09876e51af533
ck_file OpenPod 3.0_1A4000.bin 49b008c2eec15da2945a197cb31228eca91d4a25f33f912722445866c6ec2634
ck_file OpenPod 3.0_1A5000.bin 01290b9215002a96349d3af13bbab56d0c97e4cab32e8dffed6c6e8e91cfed4d
ck_file OpenPod 3.0_48000.bin 888eddabd7ddbc871c714a7cf49a9c9736dc8ca2bb2d45ec58a392b441da7841
ck_file OpenPod 3.0_53000.bin 5decc107dd674f7b6bdd34436f9a7e9b68900c61a7552df7a24be1f7f85bf4c5
ck_file OpenPod 3.0_CC000.bin 83597203bed419cc2f76f1b8c942194d07a4b23c34f67e2e7834864361dd6688
ck_file OpenPod 3.0_CD000.bin ab039386aa645f414a0580730cc4b62ca7831c9d4d8dff7b01c80f9b7be16f5f
ck_file OpenPod 3.0_CE000.bin 526d5263d25a6bbeb6b960a052b434442bad41bc1150f9251dd39ec3c0022a12
ck_file OpenPod 3.0_CF000.bin 20e9abcea0e539ce4fd2cce8a18e7e6c3f29fac7b107b8613eceef1fbc734eba
ck_file OpenPod 3.0_D0000.bin 1486610febbed13f90d63ca36f9d2f154b2364fc4d47024ffa4c7f6af05ee115
ck_file OpenPod 3.0_100000.bin 9a8e8eac3029de1b3ab7bea7dcc0ad95929afff819bc0d13bbe161c3f2ad1253
ck_file OpenPod 3.0_109000.bin c523eccfe2be4d16da8b146883adef2279fc6df7c9094b10103168d9e29878b4
ck_file OpenPod 3.0_10A000.bin ea98b618b0412ef07110f5378bcc464a62e520a1aa3b20d095152f75dd5ef99c
ck_file OpenPod 3.0_10C000.bin da58ee1b07cc42893b98fb55a5248ac2ee4ee67a43b4bcd63b8651f25263441a
ck_file OpenPod 3.0_121000.bin 207074b906bf0fe4830e2d66ed56b972c21690c31dda86ec132b752ae9025a9e
ck_file OpenPod 3.0_122000.bin ec7e02442e91c3eff704ceb49d3f57a668c136f249d4d69d823a1090e7399ad5
ck_file OpenPod 3.0_123000.bin 56f6996c47eceda5076a0202b0b0b678c5135fede20b97a29a025e798d856723
ck_file OpenPod 3.0_126000.bin f64787945149cab69de6c35d5cf9962170d23bcca2ad984d226dadfb96934fa8
ck_file OpenPod 3.0_127000.bin 1c235dc2ba59303641cefe6ac64409d0b4bc0815d4c4cabc55b430795af17c78
ck_file OpenPod 3.0_128000.bin 9796f96c62223cf50b388deb747ba74c11252e63f46be3f27e337e5b63643b15
ck_file OpenPod 3.0_12A000.bin 6e260ae5a7ca61b72d4d90e9fe3b72dc728d183a50dbec587c66aa534766803e
ck_file OpenPod 3.0_12B000.bin 9d9077fed5570dd05581cde677adac049f9463e9a22f8d25f2677e8444451edf
ck_file OpenPod 3.0_12C000.bin 18320484779cc6fb338904a1e1edf9638dab71dd39315f66811faeeb5afcc22a
ck_file OpenPod 3.0_12D000.bin d1c0cdd6a07456c411b905bcbef76969639fedab9c185e3d31ea3cb991e675b7
ck_file OpenPod 3.0_12E000.bin f7028cb9d8f1868c843c46de295138287fd430e0778b30aa709373089feaad86
ck_file OpenPod 3.0_12F000.bin c1f92c43ac8b1722b83ddb5c9238792b09bdb2938b11c099be8ba6e7d71317de
ck_file OpenPod 3.0_130000.bin 761c66a590f555a92e655960e90b3a5ab4f5ed728c965c765da309b526dce613
ck_file OpenPod 3.0_131000.bin 5b749e6d71982125ec99df57766260450ace31af5f31559f900455afd17e410b
ck_file OpenPod 3.0_132000.bin df140c90cd0dd2f2bc4b4c0322b0631be402fbf7027c5342fca2ecc48471a605
ck_file OpenPod 3.0_133000.bin 73d1019ddc88c7e4b46d79bfd2f0e442b9bf20291cef50ac7d11635977e91a48
ck_file OpenPod 3.0_134000.bin be92e3c32a6fa4232ef6915a926a0cf3ec4bcad399481c97396db99fb82837de
ck_file OpenPod 3.0_135000.bin 943a4bc523784f3645162eff8071ce8832c6404bf581a9c2dc39821fbe012cb4
ck_file OpenPod 3.0_136000.bin f8b2c6a08f548005ec064e1a98d7b34dbb58fcab276f201fa21ac8c3e7066a87
ck_file OpenPod 3.0_137000.bin 4b3c256dca2dc15e4fc6150c05bc95671a4964892970e5d0049bbee250a53bd5
ck_file OpenPod 3.0_138000.bin 3746fcf5d0c9536e4ed6f0b90ef9b90acb60d787bce1e30c7bd8bf00cacd534a
ck_file OpenPod 3.0_139000.bin f34cdfef6e1ad9b00c1651af0dff296be2693c39b8a6d526215f2211555a8da7
ck_file OpenPod 3.0_13A000.bin f380204929cecc60b37cde55ff6f4c24ea9b02fb67640da9e821d6803730aa92
ck_file OpenPod 3.0_13B000.bin 4149ec06285a44fd806acec271cbe34beaf6d8b271d9efa972e83004d8930090
ck_file OpenPod 3.0_13C000.bin ce42171c262ea6868b36ec29fb314996966ea637440c91ae5aac6a11d4102221
ck_file OpenPod 3.0_13D000.bin f3d20028d9fe994e7a335fa9df8cae4a2dd0ccd7b08d420c313c609ca8827f85
ck_file OpenPod 3.0_156000.bin b1791e9f5e5a62402d93ada9f3174129843ed8af22b7d23904d5cd472e9b43c5
ck_file base_1A3000.bin 00eed4690887e1836766f1a377b6c1ab498fe53bc724993fbb52b29de0066b11
ck_file base_1A4000.bin adaab6cd1c598f4121e669b953757aac35f5ba853e45adf8558afa5ee3dfaaa9
ck_file base_1A5000.bin 868a5c58bf77448ebf3b9e77622d1dbe8a65656556f9bd018cbbd6439cb93fd5
ck_file base_48000.bin de2dcc3d2e9dce53f640f23edc030dc04910a562e6e60a981af1342988df9233
ck_file base_53000.bin 955c524790aaa400968e228e5adfdea8683263fdb14a20f9215e55dbbf8e7880
ck_file base_CC000.bin ef8ffb2966867c44f8a87315ad7469a97018d0b7367ce864c19ffa102a8ba165
ck_file base_CD000.bin 20b7358f0730727472e16f1422127b601c9aa30a7b1bf2b1ad9494c148cf45fd
ck_file base_CE000.bin 211e10b7d6b10a4fd70ede2918c1d73e403ea6f2a4f3a1e85e2945160d65db5a
ck_file base_CF000.bin 3431383721510cf1c211de027cf958c183e16db5fabb6b230eb284c85e196aa9
ck_file base_D0000.bin 3431383721510cf1c211de027cf958c183e16db5fabb6b230eb284c85e196aa9
ck_file base_100000.bin 63226b9148313aab9973cc7aa5d57d9f6d1de1aed334806353aca0f006502633
ck_file base_109000.bin ff601736e89cac9a992ea699080030b13ed05c9d32e072ec8088d575133cfbce
ck_file base_10A000.bin a2c4f5c1f06a5e5e87228007a463525497aab491ff765e1194f987eec832194b
ck_file base_10C000.bin 4b9b828e702aa054c3b9c647ec16b6d59d1cf9df36e266e5f57a9dc9bf56de85
ck_file base_121000.bin c2fd2f15a09ff421b57c10457db7a60e389138f388e728678962c5a0d8159041
ck_file base_122000.bin ecc414142349e473ca449f7722013b854fce447fa4a54b66d1156920b8854073
ck_file base_123000.bin 0dd1b355e8afc41093cf8e45a1a7cbb9a0d1385c706eb93717eb3053dd5df88d
ck_file base_126000.bin 80d189dcbe6ed4797d0570ebd5e5c6d528488c258125c747c8ce76ad59acbf4e
ck_file base_127000.bin 32048d5c9adb41fb576c68f9846faa2ce805644c8658a349bf9bb01d4c975cae
ck_file base_128000.bin b02754c1999e8bce6c7ebb011d70b04b3f0e85805db4f7b3a5ddc884b55f0266
ck_file base_12A000.bin 60beee015ac46dda2163b9b73a9fed9ea93a8df5ba2e2180e30149f5125e8b2d
ck_file base_12B000.bin 976f9ac7ee3f02f0e526c7874c1d511e08cf686f36c3a2d6a1eeaad3a86102f7
ck_file base_12C000.bin a4051be71072af683b25cdbfd12b5ed79c2186f81a72b4d4072f67937bb1b7c7
ck_file base_12D000.bin 690b60926f8854a28e009a1771e6d52e304fb2d96959edc88c96595546a0a468
ck_file base_12E000.bin 93e940efa132f349eb62361da36d47563ab75cd1d4c6782a99c8d548b29b967c
ck_file base_12F000.bin b5997b80ec127987906c06d3b31faf44cf6e0f6ac6f7f592743388a1a6b4d453
ck_file base_130000.bin ce3474e7d59595b49dcd64fdf0a9f897c471c93af58c82bc503ab4cb4654e6de
ck_file base_131000.bin 0b1bb722152cfcf0fb5d08f37f0abcc9d38d306d72bd1f53489ea87c9b3460e0
ck_file base_132000.bin b37153ad80bbc3c076e1310dfc2deeaf24a115431d1c5eef757925a0f1575b44
ck_file base_133000.bin d53a37d1926fd24e3cbaf0124dbea1e66c7ce4ad5a213f8e5a039efbdc3d8389
ck_file base_134000.bin 9910fa6d08f40619c40324271bc6c8d5e153ca64a0bfc156df4f34601f8ee675
ck_file base_135000.bin 6d7bd35f0f7beef8b79fad15c488d64737eb82ba465fe1ab6e579c70e4bccaaa
ck_file base_136000.bin 30d2cf00ebee109fc079f32d9f6d9a112a4885aaab1247930ad2432e6652aa4b
ck_file base_137000.bin 91b55bbae89ee0b8e2edf1dcbc2d437f5d08dca6fc9722a34f60fe2471cbac2e
ck_file base_138000.bin c0031d339638593de65c3c19bca2a779adf334c0a3b90bbfa4cd897865e0eea7
ck_file base_139000.bin c23d8bfc8d03dfdd582184a95ac31dda8aafce5aeb2a1aa3dbd4c61423322c47
ck_file base_13A000.bin faa9a1d21f8394273be46be1aed9655660e471d781e4c59ae836fdbfc5ddc55e
ck_file base_13B000.bin 94ff5fd537ee6cb9a0ee8235405a47061c08b56df21203c92f0c9a5ed6440747
ck_file base_13C000.bin 7631b497f3271b42cb29371253c653bca3ce00e26a1c249d47ca4cf3cc6c0992
ck_file base_13D000.bin 2b88bab656e9a64840f6d78e822e6ff887882845c0e0f6b368fdc9e7654a90ac
ck_file base_156000.bin 09ea275aa3916096700af353b3a9b51b3f51ab9fcad3a8ee616a504bae18d60d

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
ck "FIRM" 57344 1647984 712353757dd1539b3def3be0d0b8efd212229b0bc858328f27a22d0ab7960a7c
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."

log ""
log "======================================================================"
log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."
log "   grava  : 164 KiB em 41 setores"
log "   muda   : Primeira imagem RECONSTRUIDA do ORIGINAL por receita declarada (tools/build.py)."
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
wr "4/6 1/41" 0x1A3000 OpenPod 3.0_1A3000.bin c7ebd237e44ae52fa0f0ae12e1045498a3e89be89932c2fcabc09876e51af533
wr "4/6 2/41" 0x1A4000 OpenPod 3.0_1A4000.bin 49b008c2eec15da2945a197cb31228eca91d4a25f33f912722445866c6ec2634
wr "4/6 3/41" 0x1A5000 OpenPod 3.0_1A5000.bin 01290b9215002a96349d3af13bbab56d0c97e4cab32e8dffed6c6e8e91cfed4d
wr "4/6 4/41" 0x48000 OpenPod 3.0_48000.bin 888eddabd7ddbc871c714a7cf49a9c9736dc8ca2bb2d45ec58a392b441da7841
wr "4/6 5/41" 0x53000 OpenPod 3.0_53000.bin 5decc107dd674f7b6bdd34436f9a7e9b68900c61a7552df7a24be1f7f85bf4c5
wr "4/6 6/41" 0xCC000 OpenPod 3.0_CC000.bin 83597203bed419cc2f76f1b8c942194d07a4b23c34f67e2e7834864361dd6688
wr "4/6 7/41" 0xCD000 OpenPod 3.0_CD000.bin ab039386aa645f414a0580730cc4b62ca7831c9d4d8dff7b01c80f9b7be16f5f
wr "4/6 8/41" 0xCE000 OpenPod 3.0_CE000.bin 526d5263d25a6bbeb6b960a052b434442bad41bc1150f9251dd39ec3c0022a12
wr "4/6 9/41" 0xCF000 OpenPod 3.0_CF000.bin 20e9abcea0e539ce4fd2cce8a18e7e6c3f29fac7b107b8613eceef1fbc734eba
wr "4/6 10/41" 0xD0000 OpenPod 3.0_D0000.bin 1486610febbed13f90d63ca36f9d2f154b2364fc4d47024ffa4c7f6af05ee115
wr "4/6 11/41" 0x100000 OpenPod 3.0_100000.bin 9a8e8eac3029de1b3ab7bea7dcc0ad95929afff819bc0d13bbe161c3f2ad1253
wr "4/6 12/41" 0x109000 OpenPod 3.0_109000.bin c523eccfe2be4d16da8b146883adef2279fc6df7c9094b10103168d9e29878b4
wr "4/6 13/41" 0x10A000 OpenPod 3.0_10A000.bin ea98b618b0412ef07110f5378bcc464a62e520a1aa3b20d095152f75dd5ef99c
wr "4/6 14/41" 0x10C000 OpenPod 3.0_10C000.bin da58ee1b07cc42893b98fb55a5248ac2ee4ee67a43b4bcd63b8651f25263441a
wr "4/6 15/41" 0x121000 OpenPod 3.0_121000.bin 207074b906bf0fe4830e2d66ed56b972c21690c31dda86ec132b752ae9025a9e
wr "4/6 16/41" 0x122000 OpenPod 3.0_122000.bin ec7e02442e91c3eff704ceb49d3f57a668c136f249d4d69d823a1090e7399ad5
wr "4/6 17/41" 0x123000 OpenPod 3.0_123000.bin 56f6996c47eceda5076a0202b0b0b678c5135fede20b97a29a025e798d856723
wr "4/6 18/41" 0x126000 OpenPod 3.0_126000.bin f64787945149cab69de6c35d5cf9962170d23bcca2ad984d226dadfb96934fa8
wr "4/6 19/41" 0x127000 OpenPod 3.0_127000.bin 1c235dc2ba59303641cefe6ac64409d0b4bc0815d4c4cabc55b430795af17c78
wr "4/6 20/41" 0x128000 OpenPod 3.0_128000.bin 9796f96c62223cf50b388deb747ba74c11252e63f46be3f27e337e5b63643b15
wr "4/6 21/41" 0x12A000 OpenPod 3.0_12A000.bin 6e260ae5a7ca61b72d4d90e9fe3b72dc728d183a50dbec587c66aa534766803e
wr "4/6 22/41" 0x12B000 OpenPod 3.0_12B000.bin 9d9077fed5570dd05581cde677adac049f9463e9a22f8d25f2677e8444451edf
wr "4/6 23/41" 0x12C000 OpenPod 3.0_12C000.bin 18320484779cc6fb338904a1e1edf9638dab71dd39315f66811faeeb5afcc22a
wr "4/6 24/41" 0x12D000 OpenPod 3.0_12D000.bin d1c0cdd6a07456c411b905bcbef76969639fedab9c185e3d31ea3cb991e675b7
wr "4/6 25/41" 0x12E000 OpenPod 3.0_12E000.bin f7028cb9d8f1868c843c46de295138287fd430e0778b30aa709373089feaad86
wr "4/6 26/41" 0x12F000 OpenPod 3.0_12F000.bin c1f92c43ac8b1722b83ddb5c9238792b09bdb2938b11c099be8ba6e7d71317de
wr "4/6 27/41" 0x130000 OpenPod 3.0_130000.bin 761c66a590f555a92e655960e90b3a5ab4f5ed728c965c765da309b526dce613
wr "4/6 28/41" 0x131000 OpenPod 3.0_131000.bin 5b749e6d71982125ec99df57766260450ace31af5f31559f900455afd17e410b
wr "4/6 29/41" 0x132000 OpenPod 3.0_132000.bin df140c90cd0dd2f2bc4b4c0322b0631be402fbf7027c5342fca2ecc48471a605
wr "4/6 30/41" 0x133000 OpenPod 3.0_133000.bin 73d1019ddc88c7e4b46d79bfd2f0e442b9bf20291cef50ac7d11635977e91a48
wr "4/6 31/41" 0x134000 OpenPod 3.0_134000.bin be92e3c32a6fa4232ef6915a926a0cf3ec4bcad399481c97396db99fb82837de
wr "4/6 32/41" 0x135000 OpenPod 3.0_135000.bin 943a4bc523784f3645162eff8071ce8832c6404bf581a9c2dc39821fbe012cb4
wr "4/6 33/41" 0x136000 OpenPod 3.0_136000.bin f8b2c6a08f548005ec064e1a98d7b34dbb58fcab276f201fa21ac8c3e7066a87
wr "4/6 34/41" 0x137000 OpenPod 3.0_137000.bin 4b3c256dca2dc15e4fc6150c05bc95671a4964892970e5d0049bbee250a53bd5
wr "4/6 35/41" 0x138000 OpenPod 3.0_138000.bin 3746fcf5d0c9536e4ed6f0b90ef9b90acb60d787bce1e30c7bd8bf00cacd534a
wr "4/6 36/41" 0x139000 OpenPod 3.0_139000.bin f34cdfef6e1ad9b00c1651af0dff296be2693c39b8a6d526215f2211555a8da7
wr "4/6 37/41" 0x13A000 OpenPod 3.0_13A000.bin f380204929cecc60b37cde55ff6f4c24ea9b02fb67640da9e821d6803730aa92
wr "4/6 38/41" 0x13B000 OpenPod 3.0_13B000.bin 4149ec06285a44fd806acec271cbe34beaf6d8b271d9efa972e83004d8930090
wr "4/6 39/41" 0x13C000 OpenPod 3.0_13C000.bin ce42171c262ea6868b36ec29fb314996966ea637440c91ae5aac6a11d4102221
wr "4/6 40/41" 0x13D000 OpenPod 3.0_13D000.bin f3d20028d9fe994e7a335fa9df8cae4a2dd0ccd7b08d420c313c609ca8827f85
wr "4/6 41/41" 0x156000 OpenPod 3.0_156000.bin b1791e9f5e5a62402d93ada9f3174129843ed8af22b7d23904d5cd472e9b43c5
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
ck2 "FIRM" 57344 1647984 e75a48679e4f48987cacd7461878c2e93d204071e0e76b1ec8d01a63eb02bf87
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] RESULTADO: OPENPOD 3.0 GRAVADO E VERIFICADO"
    log ""
    log "   Desconecte e abra o menu principal."
else
    log " [6/6] RESULTADO: ALGUMA REGIAO NAO CONFERE"
    log ""
    log "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:"
    log "     sudo $TOOL --id $DEV write_flash 0x1A3000 0 0x1000 base_1A3000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A4000 0 0x1000 base_1A4000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x1A5000 0 0x1000 base_1A5000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x48000 0 0x1000 base_48000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x53000 0 0x1000 base_53000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCC000 0 0x1000 base_CC000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCD000 0 0x1000 base_CD000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCE000 0 0x1000 base_CE000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xCF000 0 0x1000 base_CF000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0xD0000 0 0x1000 base_D0000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x100000 0 0x1000 base_100000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x109000 0 0x1000 base_109000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x10A000 0 0x1000 base_10A000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x10C000 0 0x1000 base_10C000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x121000 0 0x1000 base_121000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x122000 0 0x1000 base_122000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x123000 0 0x1000 base_123000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x126000 0 0x1000 base_126000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x127000 0 0x1000 base_127000.bin"
    log "     sudo $TOOL --id $DEV write_flash 0x128000 0 0x1000 base_128000.bin"
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
    log "     sudo $TOOL --id $DEV write_flash 0x156000 0 0x1000 base_156000.bin"
fi
log "======================================================================"
log ""
log "  leve de volta: before.bin  after.bin  flash_OpenPod 3.0.log"
log ""
