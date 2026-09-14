#!/bin/sh
# 9b_APAGAR_AREA_LIVRE.sh — OPCIONAL. Zera 0x1A3038..0x1FC000, a area
# onde moram as rotinas do OpenPod, deixando a flash igualzinha a de
# fabrica tambem ali.
#
# NAO E NECESSARIO. Depois do 2_RESTAURAR.sh o aparelho ja e um GN-438 de
# fabrica: a FIRM original nao tem nenhum gancho para essa area, entao o
# que sobrou la nunca e lido. Este script existe so para quem quer a
# flash literalmente identica.
#
# ⚠️  O comando `erase_flash` NUNCA foi usado neste projeto. E o unico
#     passo de todo o kit que estreia um mecanismo. Rode DEPOIS de o
#     2_RESTAURAR.sh ter conferido, e so se quiser mesmo.
#
# A PSMP (0x1FC000, suas configuracoes) continua intocada.
#
# Uso:  sudo ./9b_APAGAR_AREA_LIVRE.sh CONFIRMO
set -u
cd "$(dirname "$0")"

[ "$(id -u)" = "0" ] || { echo "Rode como root:  sudo ./9b_APAGAR_AREA_LIVRE.sh CONFIRMO"; exit 1; }
[ "${1:-}" = "CONFIRMO" ] || {
  echo "Este script APAGA a area livre da flash (0x1A3038..0x1FC000)."
  echo "Nao e necessario para voltar ao firmware de fabrica."
  echo
  echo "  sudo ./9b_APAGAR_AREA_LIVRE.sh CONFIRMO"
  exit 1; }

if [ -n "${SMT:-}" ]; then :
elif [ -x ferramenta/smtlink_dump ]; then SMT=./ferramenta/smtlink_dump
elif [ "$(uname -s)" = "Darwin" ]; then SMT=./ferramenta/smtlink_dump_macos_arm64
else SMT=./ferramenta/smtlink_dump_linux_x86_64
fi

mkdir -p leitura

# O setor 0x1A3000 e MISTO: 0x1A3000..0x1A3038 e a cauda da TONE, e o
# resto e area livre. Apagar o setor inteiro destruiria a TONE — por isso
# ele e REESCRITO com o conteudo de fabrica em vez de apagado.
echo "1/3  reescrevendo o setor misto 0x1A3000 (cauda da TONE + inicio da area livre)"
python3 -c "
d=open('imagens/GN438_original.bin','rb').read()
open('leitura/_1A3000.bin','wb').write(d[0x1A3000:0x1A4000])
" || exit 1
"$SMT" init write_flash 0x1A3000 0 0x1000 leitura/_1A3000.bin || {
  echo "FALHOU. NAO DESLIGUE. Rode ./1_LER.sh e mande o resultado."; exit 1; }

echo
echo "2/3  apagando 0x1A4000..0x1FC000 (352 KiB, 88 setores de 4 KiB)"
"$SMT" init erase_flash 0x1A4000 0x58000 || {
  echo "FALHOU. NAO DESLIGUE. Rode ./1_LER.sh e mande o resultado."; exit 1; }

echo
echo "3/3  relendo para conferir"
"$SMT" init read_flash 0 2M leitura/estado_depois.bin || exit 1

python3 - <<'PY'
o = open('imagens/GN438_original.bin','rb').read()
d = open('leitura/estado_depois.bin','rb').read()
a = [i for i in range(0x1A3038)            if o[i] != d[i]]
b = [i for i in range(0x1A3038, 0x1FC000)  if d[i] != 0xFF]
print()
print("=" * 58)
print("  0x000000..0x1A3038 igual ao de fabrica : %s" % ("SIM" if not a else "NAO (%d bytes)" % len(a)))
print("  0x1A3038..0x1FC000 todo 0xFF          : %s" % ("SIM" if not b else "NAO (%d bytes)" % len(b)))
print("  PSMP (0x1FC000..0x200000)             : intocada")
print("=" * 58)
if a or b:
    print("  NAO DESLIGUE. Mande este resultado.")
else:
    print("  A flash esta identica a de fabrica. Pode desplugar e ligar.")
PY
rm -f leitura/_1A3000.bin
