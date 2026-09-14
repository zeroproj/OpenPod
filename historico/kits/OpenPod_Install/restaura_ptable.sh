#!/bin/sh
# restaura_ptable.sh — OpenPod: devolve a tabela de particoes ao ORIGINAL.
#
# POR QUE ISTO EXISTE
#   O flash_v001.sh gravou errado em 0xD000. Causa comprovada: o
#   write_flash do smtlink_dump NAO honra o argumento de offset no
#   arquivo — ele grava a partir do offset 0. Resultado: os 4096 bytes
#   iniciais do .bin (cabecalho HLKJ + inicio do bootloader) foram
#   parar em 0xD000.
#
#   A correcao e passar um arquivo que ja contenha, NO OFFSET 0,
#   exatamente o conteudo desejado. E o que orig_D000.bin e.
#
# O QUE GRAVA
#   0xD000 +0x1000, a partir de orig_D000.bin (4096 bytes, offset 0).
#   Nada mais. O bootloader nao e endereçado.
#
# USO
#   sudo sh restaura_ptable.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801
SRC=orig_D000.bin
SRC_SHA=c3d16a15b7df6a8feac96169d93da82a5562ae3d17a94bf8906c2d24fc507091

[ -x "$TOOL" ] || { echo "smtlink_dump nao encontrado em $TOOLDIR" >&2; exit 1; }
[ -f "$SRC" ]  || { echo "$SRC nao encontrado" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "falta python3" >&2; exit 1; }

G=$(python3 -c "import hashlib,sys;print(hashlib.sha256(open('$SRC','rb').read()).hexdigest())")
[ "$G" = "$SRC_SHA" ] || {
    echo "SHA-256 de $SRC nao confere." >&2
    echo "  esperado $SRC_SHA" >&2
    echo "  obtido   $G" >&2
    exit 1
}
S=$(python3 -c "import os;print(os.path.getsize('$SRC'))")
[ "$S" = "4096" ] || { echo "$SRC nao tem 4096 bytes (tem $S)" >&2; exit 1; }
echo "[1/3] $SRC autentico — 4096 bytes, sha confere"

echo
echo "======================================================================"
echo " Vai gravar 4 KiB em 0xD000, restaurando a tabela de particoes."
echo " Origem: orig_D000.bin (offset 0 = conteudo correto)"
echo " O bootloader NAO e endereçado."
echo "======================================================================"
printf 'Digite EXATAMENTE  RESTAURAR  para continuar: '
read -r R
[ "$R" = "RESTAURAR" ] || { echo "abortado."; exit 1; }

echo
echo "[2/3] gravando..."
# offset 0 explicito: correto tanto se o argumento for honrado
# quanto se for ignorado (que e o comportamento observado).
"$TOOL" --id "$DEV" write_flash 0xD000 0 0x1000 "$SRC" || {
    echo "!! write_flash falhou. NAO desligue o aparelho." >&2; exit 1; }

echo
echo "[3/3] relendo e conferindo..."
"$TOOL" --id "$DEV" read_flash 0xD000 0x1000 check.bin || {
    echo "!! releitura falhou. NAO desligue o aparelho." >&2; exit 1; }

python3 - <<'PYEOF'
import hashlib, os, sys
d = open('check.bin','rb').read()
print("   lido: %d bytes" % len(d))
g = hashlib.sha256(d).hexdigest()
esperado = "c3d16a15b7df6a8feac96169d93da82a5562ae3d17a94bf8906c2d24fc507091"
print("   sha256 : %s" % g)
print("   esperado: %s" % esperado)
print()
if g == esperado:
    print("   *** RESTAURADO. A tabela de particoes voltou ao ORIGINAL. ***")
    print("   Desconecte e ligue o aparelho: deve bootar normalmente.")
else:
    print("   *** AINDA NAO CONFERE ***")
    print("   bytes 0x1C-0x1D = %s  (original = a649)" % d[0x1C:0x1E].hex())
    print("   NAO desligue o aparelho. Envie esta saida.")
    sys.exit(1)
PYEOF
