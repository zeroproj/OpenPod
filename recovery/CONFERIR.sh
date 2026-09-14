#!/bin/sh
# CONFERIR.sh — confere que este kit de recuperacao esta integro.
# SO LEITURA. Nao fala com o aparelho, nao grava nada, nao precisa de sudo.
set -e
cd "$(dirname "$0")"

if command -v sha256sum >/dev/null 2>&1; then SHA="sha256sum -c"
else SHA="shasum -a 256 -c"; fi

echo "conferindo os arquivos do kit..."
$SHA SHA256SUMS
echo
echo "kit INTEGRO. Procedimento em RECUPERAR.md"
