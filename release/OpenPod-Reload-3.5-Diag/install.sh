#!/bin/sh
# Reload 3.5 Diag — instalador / installer
set -eu
export LC_ALL=C

HERE=$(cd "$(dirname "$0")" && pwd)
UP="$HERE/OpenPod_OpenPodReload3.5Diag.up"

[ -f "$UP" ] || { echo "OpenPod_OpenPodReload3.5Diag.up nao encontrado / not found"; exit 1; }

echo "OpenPod — Reload 3.5 Diag"
echo
echo "1) Cartao / card:"
echo "   copie OpenPod_OpenPodReload3.5Diag.up para a raiz do cartao como update.up"
echo "   copy OpenPod_OpenPodReload3.5Diag.up to the card root as update.up"
echo
echo "2) Windows:"
echo "   grave o .up com o Flashloader da Shenju (SL-DEV)"
echo "   flash the .up with the Shenju Flashloader (SL-DEV)"
echo
echo "3) Confira / check:"
echo "   Configurar -> Informacoes = Reload 3.5 Diag"
echo "   Settings   -> Information  = Reload 3.5 Diag"
echo
echo "Depois de atualizar, APAGUE o update.up do cartao."
echo "After updating, DELETE update.up from the card."
