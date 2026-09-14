#!/bin/sh
# 2_RESTAURAR.sh — REINSTALA o sistema de fabrica no GN-438.
#
# ESTE SCRIPT ESCREVE NA FLASH.
#
#   1. le os 2 MiB do aparelho                              (nao escreve)
#   2. mostra quais setores serao de fato regravados        (nao escreve)
#   3. avisa em separado se a tabela de particoes divergir  (nao escreve)
#   4. PEDE que voce digite GRAVAR
#   5. grava 0x000000..0x1A3038 do firmware de fabrica:
#      bootloader + tabela + FIRM + TONE. A imagem inteira.
#   6. rele os 2 MiB e compara byte a byte
#
# Nao toca na area livre (0x1A3038..0x1FC000) nem na PSMP (0x1FC000).
#
# Por que gravar tudo nao e o mesmo que apagar tudo: o write_flash compara
# cada bloco de 4 KiB antes de apagar e PULA os que ja estao corretos
# (`if (!m2) continue;` no smtlink_dump.c). A escrita fisica acontece so
# onde ha diferenca.
#
# Rode como root (o USB precisa):   sudo ./2_RESTAURAR.sh
set -u
cd "$(dirname "$0")"

[ "$(id -u)" = "0" ] || { echo "Rode como root:  sudo ./2_RESTAURAR.sh"; exit 1; }

if [ -n "${SMT:-}" ]; then :
elif [ -x ferramenta/smtlink_dump ]; then SMT=./ferramenta/smtlink_dump
elif [ "$(uname -s)" = "Darwin" ]; then SMT=./ferramenta/smtlink_dump_macos_arm64
else SMT=./ferramenta/smtlink_dump_linux_x86_64
fi
[ -x "$SMT" ] || { echo "ERRO: $SMT nao existe. Rode ./0_COMPILAR.sh"; exit 1; }

export SMT
exec python3 restaurar.py
