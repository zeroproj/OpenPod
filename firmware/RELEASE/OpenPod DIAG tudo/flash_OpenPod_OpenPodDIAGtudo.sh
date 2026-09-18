#!/bin/sh
# flash_OpenPod_OpenPodDIAGtudo.sh — OpenPod. GERADO por tools/make_install_kit.py.
# NAO EDITE A MAO: as constantes sao calculadas a partir das imagens.
#
# OpenPod OpenPod DIAG tudo
#
# Grava 44 setores de 4096 B (176 KiB). O bootloader (0x0..0xD000)
# nao e endereçado. write_flash sempre com 0 no 2o argumento, a
# partir de um arquivo por setor (docs/WRITE_FLASH_SEMANTICS.md).
#
# USO   sudo sh flash_OpenPod_OpenPodDIAGtudo.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
VERSAO="OpenPod_OpenPodDIAGtudo"
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
log " OpenPod — gravacao do OPENPOD_OPENPODDIAGTUDO   (44 setores, 176 KiB)"
log " 0x048000 +0x1000   <- OpenPod_OpenPodDIAGtudo_48000.bin"
log " 0x052000 +0x1000   <- OpenPod_OpenPodDIAGtudo_52000.bin"
log " 0x053000 +0x1000   <- OpenPod_OpenPodDIAGtudo_53000.bin"
log " 0x054000 +0x1000   <- OpenPod_OpenPodDIAGtudo_54000.bin"
log " 0x05D000 +0x1000   <- OpenPod_OpenPodDIAGtudo_5D000.bin"
log " 0x0C7000 +0x1000   <- OpenPod_OpenPodDIAGtudo_C7000.bin"
log " 0x0CC000 +0x1000   <- OpenPod_OpenPodDIAGtudo_CC000.bin"
log " 0x0CD000 +0x1000   <- OpenPod_OpenPodDIAGtudo_CD000.bin"
log " 0x0D3000 +0x1000   <- OpenPod_OpenPodDIAGtudo_D3000.bin"
log " 0x0DF000 +0x1000   <- OpenPod_OpenPodDIAGtudo_DF000.bin"
log " 0x101000 +0x1000   <- OpenPod_OpenPodDIAGtudo_101000.bin"
log " 0x108000 +0x1000   <- OpenPod_OpenPodDIAGtudo_108000.bin"
log " 0x109000 +0x1000   <- OpenPod_OpenPodDIAGtudo_109000.bin"
log " 0x10A000 +0x1000   <- OpenPod_OpenPodDIAGtudo_10A000.bin"
log " 0x10C000 +0x1000   <- OpenPod_OpenPodDIAGtudo_10C000.bin"
log " 0x10D000 +0x1000   <- OpenPod_OpenPodDIAGtudo_10D000.bin"
log " 0x121000 +0x1000   <- OpenPod_OpenPodDIAGtudo_121000.bin"
log " 0x122000 +0x1000   <- OpenPod_OpenPodDIAGtudo_122000.bin"
log " 0x123000 +0x1000   <- OpenPod_OpenPodDIAGtudo_123000.bin"
log " 0x126000 +0x1000   <- OpenPod_OpenPodDIAGtudo_126000.bin"
log " 0x127000 +0x1000   <- OpenPod_OpenPodDIAGtudo_127000.bin"
log " 0x12B000 +0x1000   <- OpenPod_OpenPodDIAGtudo_12B000.bin"
log " 0x12C000 +0x1000   <- OpenPod_OpenPodDIAGtudo_12C000.bin"
log " 0x12D000 +0x1000   <- OpenPod_OpenPodDIAGtudo_12D000.bin"
log " 0x12E000 +0x1000   <- OpenPod_OpenPodDIAGtudo_12E000.bin"
log " 0x12F000 +0x1000   <- OpenPod_OpenPodDIAGtudo_12F000.bin"
log " 0x130000 +0x1000   <- OpenPod_OpenPodDIAGtudo_130000.bin"
log " 0x131000 +0x1000   <- OpenPod_OpenPodDIAGtudo_131000.bin"
log " 0x132000 +0x1000   <- OpenPod_OpenPodDIAGtudo_132000.bin"
log " 0x133000 +0x1000   <- OpenPod_OpenPodDIAGtudo_133000.bin"
log " 0x134000 +0x1000   <- OpenPod_OpenPodDIAGtudo_134000.bin"
log " 0x135000 +0x1000   <- OpenPod_OpenPodDIAGtudo_135000.bin"
log " 0x136000 +0x1000   <- OpenPod_OpenPodDIAGtudo_136000.bin"
log " 0x137000 +0x1000   <- OpenPod_OpenPodDIAGtudo_137000.bin"
log " 0x138000 +0x1000   <- OpenPod_OpenPodDIAGtudo_138000.bin"
log " 0x139000 +0x1000   <- OpenPod_OpenPodDIAGtudo_139000.bin"
log " 0x13A000 +0x1000   <- OpenPod_OpenPodDIAGtudo_13A000.bin"
log " 0x13B000 +0x1000   <- OpenPod_OpenPodDIAGtudo_13B000.bin"
log " 0x13C000 +0x1000   <- OpenPod_OpenPodDIAGtudo_13C000.bin"
log " 0x13D000 +0x1000   <- OpenPod_OpenPodDIAGtudo_13D000.bin"
log " 0x149000 +0x1000   <- OpenPod_OpenPodDIAGtudo_149000.bin"
log " 0x1A3000 +0x1000   <- OpenPod_OpenPodDIAGtudo_1A3000.bin"
log " 0x1A4000 +0x1000   <- OpenPod_OpenPodDIAGtudo_1A4000.bin"
log " 0x1A6000 +0x1000   <- OpenPod_OpenPodDIAGtudo_1A6000.bin"
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
ck_file "OpenPod_OpenPodDIAGtudo_48000.bin" 6ea532bf216161b7d65e6fec3857f9f27890899a6e7ccd0cccff654fb471dd12
ck_file "OpenPod_OpenPodDIAGtudo_52000.bin" 3b36d143a96aaab07e0927c9eecf4351f6b0a21c833d0a6f5352fd8226bc5ca3
ck_file "OpenPod_OpenPodDIAGtudo_53000.bin" a62c6180f15359d58c91eb6b96c087dbbeae1e0403e8b94accc7e00a7b8e8fe8
ck_file "OpenPod_OpenPodDIAGtudo_54000.bin" a96553f46460656f6a7c1a5d9636c0743f9ca606013b1901cd3ac95df109abb5
ck_file "OpenPod_OpenPodDIAGtudo_5D000.bin" 7e3402a71dd7d45f80e9d1eb5bc03a5d56a9f9dfb87c5829efcb76e1a5a947c1
ck_file "OpenPod_OpenPodDIAGtudo_C7000.bin" f678974cafcb27f9b636e9713360e6f34a9d03f1b6082f3de9897e1513f3a421
ck_file "OpenPod_OpenPodDIAGtudo_CC000.bin" ef8ffb2966867c44f8a87315ad7469a97018d0b7367ce864c19ffa102a8ba165
ck_file "OpenPod_OpenPodDIAGtudo_CD000.bin" 99d56432ede44c31aa9fc2b928c7965db70129bd8e4bc3f3a9b00b82abd4554e
ck_file "OpenPod_OpenPodDIAGtudo_D3000.bin" eddeb2ee73066fdef9b81eee7fb5dd74e0710b594c0e0b67090daf9822ac630c
ck_file "OpenPod_OpenPodDIAGtudo_DF000.bin" fd20c126093f6bc74a4068300166e922236d7eb571e87848c9bb0a841872686e
ck_file "OpenPod_OpenPodDIAGtudo_101000.bin" 673da19a6d3d37b673316192ec95fab51e36ae91df6e3d1c0f72e560635d94eb
ck_file "OpenPod_OpenPodDIAGtudo_108000.bin" 6f585b511bbac156970de30b91d52f56f15bdfba2e42137df2ef049098c51da6
ck_file "OpenPod_OpenPodDIAGtudo_109000.bin" 3bc16bacee418a50f79df0aa7c3f5604241fc55f126ee8d7bec7d802849312c2
ck_file "OpenPod_OpenPodDIAGtudo_10A000.bin" 5b67962d54acc73a7ad01de367b444d4fb88711ebe763ba9e0496a51117b028c
ck_file "OpenPod_OpenPodDIAGtudo_10C000.bin" 3b8683d363ba2d88fe25955572dfcb27a2153ec413f40a207ccf012d5e89b4d4
ck_file "OpenPod_OpenPodDIAGtudo_10D000.bin" 6fe1812c1a69ae6e876e9fc7a63e10e83055850f60e209d3c0ed34a67231f40a
ck_file "OpenPod_OpenPodDIAGtudo_121000.bin" 30ebefbe8d45d7d26c18201cd385b35f67e8e27396f726be0050649f77b1216d
ck_file "OpenPod_OpenPodDIAGtudo_122000.bin" df9b903aa340d40041a61cffd9082181033811098b832b0e0603b97b09885250
ck_file "OpenPod_OpenPodDIAGtudo_123000.bin" 213ef142bcbd7696faccc4e2139605cffda0d9f6e2bfbf0b368feca2fb2f0e50
ck_file "OpenPod_OpenPodDIAGtudo_126000.bin" 25f7937818203d1f7e320fbd4aeef456aa71927db2a89d6ff14f05ad0d571b9f
ck_file "OpenPod_OpenPodDIAGtudo_127000.bin" e9d327492dd109c2513cbf07d402e9443eca0acd47193c5de856a9ce03a5a498
ck_file "OpenPod_OpenPodDIAGtudo_12B000.bin" 27de098786b4fd862aa7f7f852bfad6e73d53cce0fc0ee3fa23b9433406745e9
ck_file "OpenPod_OpenPodDIAGtudo_12C000.bin" bd9fd998d33622f70ba6c0ba311f0bd1aabd5200df1296406646530a41a94bb2
ck_file "OpenPod_OpenPodDIAGtudo_12D000.bin" 6f2c626887db52348a599f6bf544611bedb43cc2751dd4b75104333c1ae3dcba
ck_file "OpenPod_OpenPodDIAGtudo_12E000.bin" 34338f09581e5aa1c689c188201ddfdebc29d251a0bfe7e1074d58c429be7157
ck_file "OpenPod_OpenPodDIAGtudo_12F000.bin" a640a2e36034aed5c4b51653fb7b6cc85d94f5d43eb12224c3b16a74c61ef102
ck_file "OpenPod_OpenPodDIAGtudo_130000.bin" a209c305d8cc078e6b1947f7e437cda6a8f92d7ae757b986f8d0b4e2fcead5b6
ck_file "OpenPod_OpenPodDIAGtudo_131000.bin" 13cbb12b13d73a421e60cbd298869e9cf68d0ce2eca5548602adf6cf37e2e8c5
ck_file "OpenPod_OpenPodDIAGtudo_132000.bin" e05828e015b71a8c3f2290b03b843188771855583e7ee886244de7d17bd46f0e
ck_file "OpenPod_OpenPodDIAGtudo_133000.bin" ffdb8e5ee01d4219eec486d7f3bc60df7e62e30269361daad437835008b513bf
ck_file "OpenPod_OpenPodDIAGtudo_134000.bin" bdb077624bce3c8b2d508b03393c0608004a53cefbd1ab1c3e1142f5ef0cb6b4
ck_file "OpenPod_OpenPodDIAGtudo_135000.bin" e52b4f721ab955ce0acc404d7bbffb4dded60b0c0b09d43fcd8b54b04ebfab7e
ck_file "OpenPod_OpenPodDIAGtudo_136000.bin" 37133af6fa7684d462b11159bacebd685f7f5e533830fd2607ce63f0d177d7b8
ck_file "OpenPod_OpenPodDIAGtudo_137000.bin" 9f27ec07c3773ed74cc2702121298b8cdbbcb4ec5815b994d8a430226b9e8bf5
ck_file "OpenPod_OpenPodDIAGtudo_138000.bin" b4ae75cffaf10da6b7edb44bb19483b627db21dcbfcd9b6388b8f1aa11626863
ck_file "OpenPod_OpenPodDIAGtudo_139000.bin" 0809afdd572786578e9713711d83177fd77ebe5c89734a78cf16d55d90242c8d
ck_file "OpenPod_OpenPodDIAGtudo_13A000.bin" 72f6bc37de6f618d6528e4411c86c090bdcf45a9e565ed5bcae94ed0d3d7f629
ck_file "OpenPod_OpenPodDIAGtudo_13B000.bin" e76fe152ae3b0f4414952f7f658add959f41adf86e0297a5ea657288cafa1a6e
ck_file "OpenPod_OpenPodDIAGtudo_13C000.bin" f9b05c7df264e8c210701e056986e0167641e37ed7cf32d8f477f15aa77feb34
ck_file "OpenPod_OpenPodDIAGtudo_13D000.bin" e8bb94264408ab85f7e905d3561ed2a4527295409f6b8381c6a154e4d2139120
ck_file "OpenPod_OpenPodDIAGtudo_149000.bin" 47c9bc96248f581805ec555ccc7e6166a454ef6a5b0ae472531c9d24d3683884
ck_file "OpenPod_OpenPodDIAGtudo_1A3000.bin" 9f06327e4e94065d21a686623ade77e48141f60be7a2c680712c73c9748a78e0
ck_file "OpenPod_OpenPodDIAGtudo_1A4000.bin" 276a5497517bf2f5aa9572c7db7a0adb003dfc70ade9fabfa420cd6ad3450edf
ck_file "OpenPod_OpenPodDIAGtudo_1A6000.bin" 476d72151529b50f9f3fe61c03ff361de5ab96e1b28a870c4c5e1299d505c0a0
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
ck "FIRM" 57344 1647984 e2a7b86339030b94268dac7d562a167613a3e769c866790353b4921cad85dbdc
ck "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace
[ "$F" -eq 0 ] || die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."

log ""
log "======================================================================"
log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."
log "   grava  : 176 KiB em 44 setores"
log "   muda   : OpenPod OpenPod DIAG tudo"
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
wr "4/6 1/44" 0x48000 "OpenPod_OpenPodDIAGtudo_48000.bin" 6ea532bf216161b7d65e6fec3857f9f27890899a6e7ccd0cccff654fb471dd12
wr "4/6 2/44" 0x52000 "OpenPod_OpenPodDIAGtudo_52000.bin" 3b36d143a96aaab07e0927c9eecf4351f6b0a21c833d0a6f5352fd8226bc5ca3
wr "4/6 3/44" 0x53000 "OpenPod_OpenPodDIAGtudo_53000.bin" a62c6180f15359d58c91eb6b96c087dbbeae1e0403e8b94accc7e00a7b8e8fe8
wr "4/6 4/44" 0x54000 "OpenPod_OpenPodDIAGtudo_54000.bin" a96553f46460656f6a7c1a5d9636c0743f9ca606013b1901cd3ac95df109abb5
wr "4/6 5/44" 0x5D000 "OpenPod_OpenPodDIAGtudo_5D000.bin" 7e3402a71dd7d45f80e9d1eb5bc03a5d56a9f9dfb87c5829efcb76e1a5a947c1
wr "4/6 6/44" 0xC7000 "OpenPod_OpenPodDIAGtudo_C7000.bin" f678974cafcb27f9b636e9713360e6f34a9d03f1b6082f3de9897e1513f3a421
wr "4/6 7/44" 0xCC000 "OpenPod_OpenPodDIAGtudo_CC000.bin" ef8ffb2966867c44f8a87315ad7469a97018d0b7367ce864c19ffa102a8ba165
wr "4/6 8/44" 0xCD000 "OpenPod_OpenPodDIAGtudo_CD000.bin" 99d56432ede44c31aa9fc2b928c7965db70129bd8e4bc3f3a9b00b82abd4554e
wr "4/6 9/44" 0xD3000 "OpenPod_OpenPodDIAGtudo_D3000.bin" eddeb2ee73066fdef9b81eee7fb5dd74e0710b594c0e0b67090daf9822ac630c
wr "4/6 10/44" 0xDF000 "OpenPod_OpenPodDIAGtudo_DF000.bin" fd20c126093f6bc74a4068300166e922236d7eb571e87848c9bb0a841872686e
wr "4/6 11/44" 0x101000 "OpenPod_OpenPodDIAGtudo_101000.bin" 673da19a6d3d37b673316192ec95fab51e36ae91df6e3d1c0f72e560635d94eb
wr "4/6 12/44" 0x108000 "OpenPod_OpenPodDIAGtudo_108000.bin" 6f585b511bbac156970de30b91d52f56f15bdfba2e42137df2ef049098c51da6
wr "4/6 13/44" 0x109000 "OpenPod_OpenPodDIAGtudo_109000.bin" 3bc16bacee418a50f79df0aa7c3f5604241fc55f126ee8d7bec7d802849312c2
wr "4/6 14/44" 0x10A000 "OpenPod_OpenPodDIAGtudo_10A000.bin" 5b67962d54acc73a7ad01de367b444d4fb88711ebe763ba9e0496a51117b028c
wr "4/6 15/44" 0x10C000 "OpenPod_OpenPodDIAGtudo_10C000.bin" 3b8683d363ba2d88fe25955572dfcb27a2153ec413f40a207ccf012d5e89b4d4
wr "4/6 16/44" 0x10D000 "OpenPod_OpenPodDIAGtudo_10D000.bin" 6fe1812c1a69ae6e876e9fc7a63e10e83055850f60e209d3c0ed34a67231f40a
wr "4/6 17/44" 0x121000 "OpenPod_OpenPodDIAGtudo_121000.bin" 30ebefbe8d45d7d26c18201cd385b35f67e8e27396f726be0050649f77b1216d
wr "4/6 18/44" 0x122000 "OpenPod_OpenPodDIAGtudo_122000.bin" df9b903aa340d40041a61cffd9082181033811098b832b0e0603b97b09885250
wr "4/6 19/44" 0x123000 "OpenPod_OpenPodDIAGtudo_123000.bin" 213ef142bcbd7696faccc4e2139605cffda0d9f6e2bfbf0b368feca2fb2f0e50
wr "4/6 20/44" 0x126000 "OpenPod_OpenPodDIAGtudo_126000.bin" 25f7937818203d1f7e320fbd4aeef456aa71927db2a89d6ff14f05ad0d571b9f
wr "4/6 21/44" 0x127000 "OpenPod_OpenPodDIAGtudo_127000.bin" e9d327492dd109c2513cbf07d402e9443eca0acd47193c5de856a9ce03a5a498
wr "4/6 22/44" 0x12B000 "OpenPod_OpenPodDIAGtudo_12B000.bin" 27de098786b4fd862aa7f7f852bfad6e73d53cce0fc0ee3fa23b9433406745e9
wr "4/6 23/44" 0x12C000 "OpenPod_OpenPodDIAGtudo_12C000.bin" bd9fd998d33622f70ba6c0ba311f0bd1aabd5200df1296406646530a41a94bb2
wr "4/6 24/44" 0x12D000 "OpenPod_OpenPodDIAGtudo_12D000.bin" 6f2c626887db52348a599f6bf544611bedb43cc2751dd4b75104333c1ae3dcba
wr "4/6 25/44" 0x12E000 "OpenPod_OpenPodDIAGtudo_12E000.bin" 34338f09581e5aa1c689c188201ddfdebc29d251a0bfe7e1074d58c429be7157
wr "4/6 26/44" 0x12F000 "OpenPod_OpenPodDIAGtudo_12F000.bin" a640a2e36034aed5c4b51653fb7b6cc85d94f5d43eb12224c3b16a74c61ef102
wr "4/6 27/44" 0x130000 "OpenPod_OpenPodDIAGtudo_130000.bin" a209c305d8cc078e6b1947f7e437cda6a8f92d7ae757b986f8d0b4e2fcead5b6
wr "4/6 28/44" 0x131000 "OpenPod_OpenPodDIAGtudo_131000.bin" 13cbb12b13d73a421e60cbd298869e9cf68d0ce2eca5548602adf6cf37e2e8c5
wr "4/6 29/44" 0x132000 "OpenPod_OpenPodDIAGtudo_132000.bin" e05828e015b71a8c3f2290b03b843188771855583e7ee886244de7d17bd46f0e
wr "4/6 30/44" 0x133000 "OpenPod_OpenPodDIAGtudo_133000.bin" ffdb8e5ee01d4219eec486d7f3bc60df7e62e30269361daad437835008b513bf
wr "4/6 31/44" 0x134000 "OpenPod_OpenPodDIAGtudo_134000.bin" bdb077624bce3c8b2d508b03393c0608004a53cefbd1ab1c3e1142f5ef0cb6b4
wr "4/6 32/44" 0x135000 "OpenPod_OpenPodDIAGtudo_135000.bin" e52b4f721ab955ce0acc404d7bbffb4dded60b0c0b09d43fcd8b54b04ebfab7e
wr "4/6 33/44" 0x136000 "OpenPod_OpenPodDIAGtudo_136000.bin" 37133af6fa7684d462b11159bacebd685f7f5e533830fd2607ce63f0d177d7b8
wr "4/6 34/44" 0x137000 "OpenPod_OpenPodDIAGtudo_137000.bin" 9f27ec07c3773ed74cc2702121298b8cdbbcb4ec5815b994d8a430226b9e8bf5
wr "4/6 35/44" 0x138000 "OpenPod_OpenPodDIAGtudo_138000.bin" b4ae75cffaf10da6b7edb44bb19483b627db21dcbfcd9b6388b8f1aa11626863
wr "4/6 36/44" 0x139000 "OpenPod_OpenPodDIAGtudo_139000.bin" 0809afdd572786578e9713711d83177fd77ebe5c89734a78cf16d55d90242c8d
wr "4/6 37/44" 0x13A000 "OpenPod_OpenPodDIAGtudo_13A000.bin" 72f6bc37de6f618d6528e4411c86c090bdcf45a9e565ed5bcae94ed0d3d7f629
wr "4/6 38/44" 0x13B000 "OpenPod_OpenPodDIAGtudo_13B000.bin" e76fe152ae3b0f4414952f7f658add959f41adf86e0297a5ea657288cafa1a6e
wr "4/6 39/44" 0x13C000 "OpenPod_OpenPodDIAGtudo_13C000.bin" f9b05c7df264e8c210701e056986e0167641e37ed7cf32d8f477f15aa77feb34
wr "4/6 40/44" 0x13D000 "OpenPod_OpenPodDIAGtudo_13D000.bin" e8bb94264408ab85f7e905d3561ed2a4527295409f6b8381c6a154e4d2139120
wr "4/6 41/44" 0x149000 "OpenPod_OpenPodDIAGtudo_149000.bin" 47c9bc96248f581805ec555ccc7e6166a454ef6a5b0ae472531c9d24d3683884
wr "4/6 42/44" 0x1A3000 "OpenPod_OpenPodDIAGtudo_1A3000.bin" 9f06327e4e94065d21a686623ade77e48141f60be7a2c680712c73c9748a78e0
wr "4/6 43/44" 0x1A4000 "OpenPod_OpenPodDIAGtudo_1A4000.bin" 276a5497517bf2f5aa9572c7db7a0adb003dfc70ade9fabfa420cd6ad3450edf
wr "4/6 44/44" 0x1A6000 "OpenPod_OpenPodDIAGtudo_1A6000.bin" 476d72151529b50f9f3fe61c03ff361de5ab96e1b28a870c4c5e1299d505c0a0
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
ck2 "FIRM" 57344 1647984 2d9ff99f1a37bf5bf77cd6de973e038c94168001097a484b7aabecfef436ae77
ck2 "TONE" 1708032 8248 7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace

log ""
log "======================================================================"
if [ "$F" -eq 0 ]; then
    log " [6/6] RESULTADO: OPENPOD_OPENPODDIAGTUDO GRAVADO E VERIFICADO"
    log ""
    log "   Desconecte e abra o menu principal."
else
    log " [6/6] RESULTADO: ALGUMA REGIAO NAO CONFERE"
    log ""
    log "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:"
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
log "  leve de volta: before.bin  after.bin  flash_$VERSAO.log"
log ""
