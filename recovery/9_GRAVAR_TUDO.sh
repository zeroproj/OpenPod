#!/bin/sh
# 9_GRAVAR_TUDO.sh — restauracao COMPLETA de fabrica, do endereco 0 ao
# fim da TONE, direto da imagem de 2 MiB.
#
# ESTE SCRIPT ESCREVE NA FLASH.
#
# E o caminho de ULTIMO RECURSO, para quando nao ha como analisar o dump.
# O caminho preferido e gravar SO os setores divergentes — menos escrita,
# e cada byte com motivo conhecido. Veja VOLTAR_AO_ORIGINAL.md, Passo 4.
#
# Uso:  ./9_GRAVAR_TUDO.sh CONFIRMO
set -u
cd "$(dirname "$0")"

[ "${1:-}" = "CONFIRMO" ] || {
  echo "Este script ESCREVE na flash do aparelho, inclusive no BOOTLOADER."
  echo
  echo "Antes de rodar:"
  echo "  1. rode ./1_LER.sh e guarde o dump"
  echo "  2. prefira o kit de setores, se houver analise"
  echo
  echo "  ./9_GRAVAR_TUDO.sh CONFIRMO"
  exit 1; }

if [ -n "${SMT:-}" ]; then :
elif [ -x ferramenta/smtlink_dump ]; then SMT=ferramenta/smtlink_dump
elif [ "$(uname -s)" = "Darwin" ]; then SMT=ferramenta/smtlink_dump_macos_arm64
else SMT=ferramenta/smtlink_dump_linux_x86_64
fi

if command -v sha256sum >/dev/null 2>&1; then SHA="sha256sum -c"
else SHA="shasum -a 256 -c"; fi

echo "conferindo a imagem de origem..."
$SHA <<'SUM' || { echo "IMAGEM DE ORIGEM CORROMPIDA. ABORTADO."; exit 1; }
b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f  imagens/GN438_original.bin
SUM
echo

# 0x1A3038 = fim da particao TONE. A area livre e a PSMP ficam de fora.
echo "gravando 0x000000..0x1A3038 (1716280 bytes)..."
echo "  o 2o argumento e 0 porque o write_flash le o arquivo do byte 0."
sudo "$SMT" init write_flash 0 0 0x1A3038 imagens/GN438_original.bin || {
  echo; echo "A GRAVACAO FALHOU. NAO DESLIGUE O APARELHO."
  echo "Rode ./1_LER.sh e mande o resultado."; exit 1; }
echo

echo "relendo para conferir..."
mkdir -p leitura
sudo "$SMT" init read_flash 0 2M leitura/GN438_depois.bin || exit 1
echo

python3 - <<'PY'
a = open('imagens/GN438_original.bin','rb').read()
b = open('leitura/GN438_depois.bin','rb').read()
dif = [i for i in range(0x1A3038) if a[i] != b[i]]
print("bytes diferentes de fabrica em 0x000000..0x1A3038:", len(dif))
if dif:
    print("primeiro em 0x%06X" % dif[0])
    print()
    print("NAO CONFERE. NAO DESLIGUE. Mande este resultado.")
else:
    print()
    print("CONFERE. Pode desplugar e ligar.")
    print("Deve abrir com o logotipo GENAI e a home em grade 3x3.")
PY
