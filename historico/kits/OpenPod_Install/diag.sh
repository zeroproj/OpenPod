#!/bin/sh
# diag.sh — OpenPod: diagnostico do estado do GN-438 apos a falha do V001.
#
# SOMENTE LEITURA. Nao grava absolutamente nada no aparelho.
#
# USO
#   sudo sh diag.sh [/opt/smartlink_flash]
#
# SAIDA
#   diag.bin  (2 MiB, dump do estado atual)  + relatorio no terminal

set -eu
export LC_ALL=C

TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
DEV=301a:2801

[ -x "$TOOL" ] || { echo "smtlink_dump nao encontrado em $TOOLDIR" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "falta python3" >&2; exit 1; }

echo "=== lendo a flash inteira (SO LEITURA) ==="
"$TOOL" --id "$DEV" read_flash 0 2M diag.bin || { echo "leitura falhou" >&2; exit 1; }
echo

python3 - <<'PYEOF'
import hashlib, sys
d = open('diag.bin','rb').read()
print("tamanho lido: %d bytes (esperado 2097152)" % len(d))
if len(d) != 2097152:
    print("!! tamanho errado — o resto do relatorio nao e confiavel")
print()

def h(o, s):
    return hashlib.sha256(d[o:o+s]).hexdigest()

# (nome, offset, tamanho, prefixo ORIGINAL, prefixo V001)
reg = [
    ("bootloader", 0,       51532,   "86118400", "86118400"),
    ("ptable",     53248,   64,      "9f93d443", "3bb70ce0"),
    ("FIRM",       57344,   1647984, "e2a7b863", "96b355e3"),
    ("TONE",       1708032, 8248,    "7f2882af", "7f2882af"),
]
print("%-11s %-18s %s" % ("REGIAO", "SHA-256 (16)", "ESTADO"))
print("-" * 52)
for n, o, s, antes, depois in reg:
    g = h(o, s)
    if g.startswith(antes) and g.startswith(depois):
        est = "INTACTA (igual nos dois)"
    elif g.startswith(antes):
        est = "ORIGINAL"
    elif g.startswith(depois):
        est = "V001"
    else:
        est = "??? DESCONHECIDO"
    print("%-11s %-18s %s" % (n, g[:16], est))

print()
print("=== o setor da gravacao ===")
print("setor 0xD000 +0x1000 sha256:")
print("  ", h(0xD000, 0x1000))
print("  esperado V001    : c2124ab4b1c6eebd4b13a3156e9b1482f79385aa855276929ff2ef79dd6a9686")
print("  esperado ORIGINAL: c3d16a15b7df6a8feac96169d93da82a5562ae3d17a94bf8906c2d24fc507091")
print()
b = d[0xD01C:0xD01E]
print("bytes 0xD01C-0xD01D = %s   (CRC da FIRM)" % b.hex())
if b == bytes.fromhex('a649'):
    print("  -> ORIGINAL. A gravacao NAO pegou. Aparelho intacto.")
elif b == bytes.fromhex('3a58'):
    print("  -> V001. A gravacao FUNCIONOU; o erro foi so na conferencia.")
else:
    print("  -> DESCONHECIDO. Escrita parcial ou leitura suspeita.")

print()
print("=== o outro setor (ainda nao gravado) ===")
print("setor 0xCE000 +0x2000 sha256:")
print("  ", h(0xCE000, 0x2000))
print("  esperado V001    : a30962bce6b71e4ad5dc5922ee8e121d58dd8e5db13925318725f3f663d45597")
print("  esperado ORIGINAL: 10739e6db5bc6f7647823b187ea6c1f6ad1a1d2b3698b4dac00d22dc2b81780c")

print()
print("=== primeiros 16 bytes da flash (cabecalho HLKJ) ===")
print("  ", d[0:16].hex())
print("   esperado: 484c4b4a" + " (HLKJ em ASCII)")
PYEOF

echo
echo "=== pronto. envie TODO o texto acima. diag.bin ficou salvo aqui. ==="
