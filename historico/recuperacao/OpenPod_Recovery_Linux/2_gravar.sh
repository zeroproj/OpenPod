#!/usr/bin/env bash
# GRAVA NA FLASH. So rode depois de o Claude conferir o dump.
# Uso:  ./2_gravar.sh CONFIRMO
set -u
cd "$(dirname "$0")"
[ "${1:-}" = "CONFIRMO" ] || {
  echo "Este script ESCREVE na flash do aparelho."
  echo "Rode apenas depois de mandar o dump para o Claude e receber o OK."
  echo
  echo "  ./2_gravar.sh CONFIRMO"
  exit 1; }

SMT="${SMT:-}"
if [ -z "$SMT" ]; then
  if [ -x ferramenta/smtlink_dump ]; then SMT=ferramenta/smtlink_dump
  else SMT=ferramenta/smtlink_dump_linux_x86_64; fi
fi

echo "conferindo o arquivo de origem..."
sha256sum -c <<'SUM' || { echo "ARQUIVO DE ORIGEM CORROMPIDO. ABORTADO."; exit 1; }
b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f  GN438_original.bin
SUM
echo
echo "gravando o setor 0x00D000 (4096 bytes)..."
sudo "$SMT" init write_flash 0xD000 0 0x1000 ptable_D000_original.bin || exit 1
echo
echo "relendo para conferir..."
sudo "$SMT" init read_flash 0xD000 0x1000 conferencia_D000.bin || exit 1
echo
sha256sum ptable_D000_original.bin conferencia_D000.bin
echo
if cmp -s ptable_D000_original.bin conferencia_D000.bin; then
  echo "CONFERE. Desplugue e ligue o aparelho."
else
  echo "NAO CONFERE. NAO desplugue. Avise o Claude."
fi
