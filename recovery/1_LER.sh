#!/bin/sh
# 1_LER.sh — le a flash inteira do GN-438 e mostra o que interessa.
#
# NAO ESCREVE NADA NO APARELHO. Nenhum comando de escrita e emitido.
# Precisa de sudo so para falar com o USB.
set -u
cd "$(dirname "$0")"

SAIDA="leitura/GN438_antes_recovery.bin"
mkdir -p leitura

# --- qual binario usar
if [ -n "${SMT:-}" ]; then :
elif [ -x ferramenta/smtlink_dump ]; then SMT=ferramenta/smtlink_dump
elif [ "$(uname -s)" = "Darwin" ]; then SMT=ferramenta/smtlink_dump_macos_arm64
else SMT=ferramenta/smtlink_dump_linux_x86_64
fi
[ -x "$SMT" ] || { echo "ERRO: $SMT nao existe ou nao e executavel."
                   echo "Rode ./0_COMPILAR.sh"; exit 1; }

if command -v sha256sum >/dev/null 2>&1; then SHA=sha256sum
else SHA="shasum -a 256"; fi

echo "=========================================================="
echo "  OpenPod — leitura da flash          (NAO ESCREVE NADA)"
echo "=========================================================="
echo "  ferramenta: $SMT"
echo

echo "--- 1. o aparelho esta em modo download? ---"
if command -v lsusb >/dev/null 2>&1; then
  lsusb | grep -i 301a || { echo "NADA ENCONTRADO."; echo
    echo "Ponha o aparelho em modo download:"
    echo "   USB conectado  ->  segure VOLUME BAIXO  ->  aperte RESET"
    exit 1; }
  if lsusb | grep -qi "301a:2801"; then
    echo
    echo "ATENCAO: esta em 2801 (aparelho normal), nao em 2800 (download)."
    echo "Refaca: segure VOLUME BAIXO e aperte RESET."
    exit 1
  fi
else
  echo "(lsusb nao existe aqui — seguindo assim mesmo)"
fi
echo

echo "--- 2. lendo 2 MiB (1 a 2 minutos) ---"
sudo "$SMT" init flash_id read_flash 0 2M "$SAIDA" || {
  echo; echo "A leitura FALHOU. Refaca o modo download e tente de novo."
  echo "Nada foi escrito no aparelho."; exit 1; }
echo

echo "--- 3. resultado ---"
ls -l "$SAIDA"
$SHA "$SAIDA"
echo

echo "=========================================================="
echo "  COLE DAQUI PARA BAIXO NO CHAT"
echo "=========================================================="
echo
echo "--- tamanho e hash ---"
wc -c < "$SAIDA"
$SHA "$SAIDA"
echo
echo "--- e o firmware de fabrica? ---"
$SHA imagens/GN438_original.bin
echo "  (se os dois hashes acima forem iguais, o aparelho JA esta original)"
echo
echo "--- cabecalho HLKJ (0x000000) ---"
xxd -s 0      -l 64  "$SAIDA" 2>/dev/null || od -A x -t x1z -j 0      -N 64  "$SAIDA"
echo
echo "--- tabela de particoes (0x00D000)   <<< O QUE MAIS IMPORTA ---"
xxd -s 0xD000 -l 128 "$SAIDA" 2>/dev/null || od -A x -t x1z -j 53248  -N 128 "$SAIDA"
echo
echo "--- inicio da FIRM (0x00E000) ---"
xxd -s 0xE000 -l 48  "$SAIDA" 2>/dev/null || od -A x -t x1z -j 57344  -N 48  "$SAIDA"
echo
echo "--- versao na tela Informacoes ---"
strings -n 6 "$SAIDA" 2>/dev/null | grep -iE '^(OpenPod|yp3_)' | head -5
echo
echo "=========================================================="
echo "  PARE AQUI. Nada foi escrito."
echo "  Mande o bloco acima — e, se der, o proprio arquivo:"
echo "    $(pwd)/$SAIDA"
echo "=========================================================="
