#!/usr/bin/env bash
# So e necessario se o binario pronto nao rodar (outra arquitetura).
set -eu
cd "$(dirname "$0")/ferramenta"
echo "Precisa de: build-essential e libusb-1.0-0-dev"
echo "  Debian/Ubuntu: sudo apt install build-essential libusb-1.0-0-dev"
echo "  Fedora:        sudo dnf install gcc make libusb1-devel"
echo
make
echo
echo "OK: ferramenta/smtlink_dump"
