#!/bin/sh
# fetch_smartlink_flash.sh — obtem e VERIFICA a versao travada da ferramenta
# usada para extrair o firmware original do GN-438.
#
# PROPOSITO
#   Tornar o processo de dump reproduzivel sem redistribuir codigo de
#   terceiros (o repositorio upstream nao possui arquivo de licenca).
#   Clona o commit exato registrado em smartlink_flash.lock e confere o
#   SHA-256 de cada arquivo rastreado.
#
# USO
#   sh tools/external/fetch_smartlink_flash.sh [destino]
#   sh tools/external/fetch_smartlink_flash.sh --verify-only <destino>
#
#   destino padrao: ./smartlink_flash
#
# DEPENDENCIAS
#   git, shasum (ou sha256sum)
#
# ESTE SCRIPT NAO TOCA NO DISPOSITIVO.
#   Apenas baixa e verifica codigo-fonte. Nenhum comando USB e executado.
#   O dump em si esta documentado em docs/FIRMWARE_DUMP.md e NAO precisa
#   ser repetido: o firmware ja foi extraido.
#
# SAIDA
#   0 se todos os hashes conferirem, 1 caso contrario.

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
LOCK="$SCRIPT_DIR/smartlink_flash.lock"
URL=https://github.com/ilyakurdyukov/smartlink_flash
COMMIT=49d51d17e825afbbbc2be7d91d6367674543c2e3

VERIFY_ONLY=0
if [ "${1:-}" = "--verify-only" ]; then
    VERIFY_ONLY=1
    shift
fi
DEST=${1:-smartlink_flash}

if [ ! -f "$LOCK" ]; then
    echo "ERRO: lock nao encontrado: $LOCK" >&2
    exit 1
fi

sha_of() {
    if command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | cut -d' ' -f1
    else
        sha256sum "$1" | cut -d' ' -f1
    fi
}

if [ "$VERIFY_ONLY" -eq 0 ]; then
    if [ -e "$DEST" ]; then
        echo "ERRO: '$DEST' ja existe. Remova ou informe outro destino." >&2
        exit 1
    fi
    echo "clonando $URL"
    git clone --quiet "$URL" "$DEST"
    ( cd "$DEST" && git checkout --quiet "$COMMIT" )
    echo "commit fixado: $COMMIT"
fi

if [ ! -d "$DEST" ]; then
    echo "ERRO: destino inexistente: $DEST" >&2
    exit 1
fi

echo "verificando hashes contra $LOCK"
FALHAS=0
TOTAL=0
# extrai as linhas "<sha256>  <caminho>" da secao [arquivos]
LISTA=$(sed -n '/^\[arquivos\]/,/^\[artefato_produzido\]/p' "$LOCK" \
        | grep -E '^[0-9a-f]{64}  ')

# le da variavel para que FALHAS sobreviva (evita subshell de pipe)
OLDIFS=$IFS
IFS='
'
for linha in $LISTA; do
    hash=${linha%%  *}
    path=${linha#*  }
    TOTAL=$((TOTAL + 1))
    if [ ! -f "$DEST/$path" ]; then
        echo "  AUSENTE    $path"
        FALHAS=$((FALHAS + 1))
        continue
    fi
    real=$(sha_of "$DEST/$path")
    if [ "$real" != "$hash" ]; then
        echo "  DIVERGENTE $path"
        echo "     esperado $hash"
        echo "     obtido   $real"
        FALHAS=$((FALHAS + 1))
    fi
done
IFS=$OLDIFS

echo
if [ "$FALHAS" -eq 0 ]; then
    echo "OK — $TOTAL arquivo(s) conferem com a versao travada."
else
    echo "FALHA — $FALHAS de $TOTAL arquivo(s) divergem."
    exit 1
fi

cat <<'FIM'

Para compilar (Linux, requer libusb-1.0-dev):
    make                # modo libusb
    make LIBUSB=0       # modo USB serial

LEMBRETE: o firmware do GN-438 JA foi extraido e esta em
firmware/ORIGINAL/GN438_original.bin (SHA-256 b7cd5eb9...4b36f).
Nao repita o dump sem necessidade.
FIM
