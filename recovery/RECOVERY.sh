#!/bin/sh
# RECOVERY.sh — O RECOVERY OFICIAL DO OPENPOD.
#
# Devolve o GN-438 ao firmware de fabrica, do comeco ao fim, num comando:
#
#     le -> analisa -> confirma -> grava o sistema -> apaga a area livre
#        -> rele -> confere -> diz o que o aparelho tinha antes
#
# A PSMP (0x1FC000, suas configuracoes de usuario) nunca e tocada.
#
# USO
#     sudo sh RECOVERY.sh                        recovery completo
#     sudo sh RECOVERY.sh --so-analise           SO LE, nao escreve nada
#     sudo sh RECOVERY.sh --manter-area-livre    nao apaga a area livre
#
# ANTES
#     1. sh CONFERIR.sh                          confere este kit
#     2. USB conectado -> segure VOLUME BAIXO -> aperte RESET
#     3. bateria cheia, USB direto na placa, sem hub          (regra R6)
set -u
cd "$(dirname "$0")"

[ "$(id -u)" = "0" ] || { echo "Rode como root:  sudo sh RECOVERY.sh $*"; exit 1; }

# --- qual binario
if [ -n "${SMT:-}" ]; then :
elif [ -x ferramenta/smtlink_dump ]; then SMT=./ferramenta/smtlink_dump
elif [ "$(uname -s)" = "Darwin" ]; then SMT=./ferramenta/smtlink_dump_macos_arm64
else SMT=./ferramenta/smtlink_dump_linux_x86_64
fi
[ -x "$SMT" ] || { echo "ERRO: $SMT nao existe. Rode  sh 0_COMPILAR.sh"; exit 1; }

# --- o aparelho esta em modo download?
if command -v lsusb >/dev/null 2>&1; then
  if lsusb | grep -qi "301a:2801"; then
    echo "O aparelho esta em 301a:2801 (modo normal), nao em 2800 (download)."
    echo "Refaca:  USB conectado -> segure VOLUME BAIXO -> aperte RESET"
    exit 1
  fi
  lsusb | grep -qi 301a || {
    echo "Nenhum aparelho 301a encontrado no USB."
    echo "Ponha em modo download:  USB -> segure VOLUME BAIXO -> RESET"
    exit 1; }
fi

export SMT
exec python3 recovery.py "$@"
