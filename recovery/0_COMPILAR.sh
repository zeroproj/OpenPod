#!/bin/sh
# 0_COMPILAR.sh — so e necessario se o binario pronto nao rodar.
# NAO fala com o aparelho. Nao precisa de sudo (so o apt/dnf precisa).
set -eu
cd "$(dirname "$0")/ferramenta"

echo "Dependencias:"
echo "  Debian/Ubuntu: sudo apt install build-essential libusb-1.0-0-dev"
echo "  Fedora:        sudo dnf install gcc make libusb1-devel"
echo "  Arch:          sudo pacman -S base-devel libusb"
echo

make

echo
echo "OK: ferramenta/smtlink_dump"
echo "Os scripts 1_LER.sh e 9_GRAVAR_TUDO.sh usam este binario automaticamente."
