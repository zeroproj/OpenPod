#!/usr/bin/env bash
# Le a flash do GN-438 e imprime o que o Claude precisa ver.
# NAO ESCREVE NADA NO APARELHO.
set -u
cd "$(dirname "$0")"

SMT="${SMT:-}"
if [ -z "$SMT" ]; then
  if [ -x ferramenta/smtlink_dump ]; then SMT=ferramenta/smtlink_dump
  elif [ -x ferramenta/smtlink_dump_linux_x86_64 ]; then SMT=ferramenta/smtlink_dump_linux_x86_64
  else echo "ERRO: nao achei o smtlink_dump. Rode ./0_compilar.sh"; exit 1; fi
fi

echo "=========================================================="
echo " OpenPod — leitura da flash  (nao escreve nada)"
echo "=========================================================="
echo
echo "--- 1. o aparelho esta em modo download? ---"
lsusb | grep -i 301a || { echo "NADA ENCONTRADO."; echo
  echo "Ponha o aparelho em modo download:"
  echo "   USB conectado  ->  segure VOLUME BAIXO  ->  aperte RESET"; exit 1; }
echo
if lsusb | grep -qi "301a:2801"; then
  echo "ATENCAO: esta em 2801 (card reader), nao em 2800 (bootloader)."
  echo "Refaca: segure VOLUME BAIXO e aperte RESET."; exit 1
fi
echo
echo "--- 2. lendo 2 MiB (1 a 2 minutos) ---"
sudo "$SMT" init flash_id read_flash 0 2M GN438_bricked_dump.bin || {
  echo; echo "A leitura falhou. Refaca o modo download e tente de novo."; exit 1; }
echo
echo "--- 3. resultado ---"
ls -l GN438_bricked_dump.bin
sha256sum GN438_bricked_dump.bin
echo
echo "=========================================================="
echo " COLE DAQUI PARA BAIXO NO CHAT"
echo "=========================================================="
echo
echo "--- tamanho e hash ---"
stat -c '%s bytes' GN438_bricked_dump.bin 2>/dev/null || wc -c < GN438_bricked_dump.bin
sha256sum GN438_bricked_dump.bin
echo
echo "--- cabecalho HLKJ (0x000000) ---"
xxd -s 0 -l 64 GN438_bricked_dump.bin
echo
echo "--- tabela de particoes (0x00D000)  <<< O QUE IMPORTA ---"
xxd -s 0xD000 -l 128 GN438_bricked_dump.bin
echo
echo "--- inicio da FIRM (0x00E000) ---"
xxd -s 0xE000 -l 48 GN438_bricked_dump.bin
echo
echo "=========================================================="
