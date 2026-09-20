#!/bin/sh
# OpenPod 5.7 B10 — installer / instalador
set -eu
export LC_ALL=C

HERE=$(cd "$(dirname "$0")" && pwd)
UP="$HERE/OpenPod_Beta10.up"
DEV=301a:2801
TOOL_SRC=https://github.com/ilyakurdyukov/smartlink_flash

c1() { printf '\033[1;36m%s\033[0m\n' "$*"; }
ok() { printf '\033[1;32m%s\033[0m\n' "$*"; }
er() { printf '\033[1;31m%s\033[0m\n' "$*"; }
hd() { echo; c1 "=============================================================="; c1 " $*"; c1 "=============================================================="; }
die() { echo; er "$*"; exit 1; }

# ------------------------------------------------------------ language
LANG_SEL=""
pick_lang() {
    echo
    echo "  1) English     2) Portugues do Brasil"
    printf '  > '
    read -r L
    case "$L" in 1) LANG_SEL=en ;; *) LANG_SEL=pt ;; esac
}
t() { if [ "$LANG_SEL" = en ]; then echo "$1"; else echo "$2"; fi; }

# ---------------------------------------------------------------- card
by_card() {
hd "$(t 'microSD card' 'cartao microSD')"
if [ "$LANG_SEL" = en ]; then cat <<'TXT'

  Only for a player that ALREADY has  Settings -> Update via SD .
  A GN-438 on the stock firmware does not: use the USB cable.

  1. Copy  OpenPod_Beta10.up  to the ROOT of the card, renamed to:

         update.up

  2. Put the card in the player and turn it on.

  3. On the player:   Settings  ->  Update via SD  ->  Yes

     Do NOT power off and do not remove the card.

  4. After it reboots, DELETE update.up from the card.
     If it stays there, the player tries to update on every boot.

  5. Check under  Settings -> Information :   OpenPod 5.7 B10

TXT
else cat <<'TXT'

  So para aparelho que JA tem  Configurar -> Atualizar por SD .
  O GN-438 de fabrica nao tem: use o cabo USB.

  1. Copie  OpenPod_Beta10.up  para a RAIZ do cartao, renomeando para:

         update.up

  2. Ponha o cartao no aparelho e ligue.

  3. No aparelho:   Configurar  ->  Atualizar por SD  ->  Sim

     NAO desligue e nao tire o cartao.

  4. Ao reiniciar, APAGUE o update.up do cartao.
     Se ficar la, o aparelho tenta atualizar toda vez que liga.

  5. Confira em  Configurar -> Informacoes :   OpenPod 5.7 B10

TXT
fi
ok "  $(t 'Done.' 'Pronto.')"
echo
}

# ---------------------------------------------------------------- cable
find_tool() {
    for c in "$HERE/smtlink_dump" "$HERE/smartlink_flash/smtlink_dump" \
             /opt/smartlink_flash/smtlink_dump "$(command -v smtlink_dump || true)"; do
        [ -n "$c" ] && [ -x "$c" ] && { echo "$c"; return 0; }
    done
    return 1
}

need_tool() {
hd "$(t 'Flashing tool not found' 'Ferramenta de gravacao nao encontrada')"
cat <<TXT

  $(t 'OpenPod does not ship the flashing tool. It is a separate project' \
       'O OpenPod nao distribui o gravador. E um projeto separado')
  $(t 'by Ilya Kurdyukov, and carries no license that lets us bundle it.' \
       'de Ilya Kurdyukov, sem licenca que permita redistribuir.')

      git clone $TOOL_SRC
      cd smartlink_flash
      make

  $(t 'Then run this installer again.' 'Depois rode este instalador de novo.')

  Linux:  libusb-1.0-dev        macOS:  brew install libusb

TXT
}

recovery_mode() {
hd "$(t 'Putting the player in flashing mode' 'Pondo o aparelho em modo de gravacao')"
if [ "$LANG_SEL" = en ]; then cat <<'TXT'

  This mode lives in the chip ROM. It runs before any firmware, so it
  works even if the player is bricked.

      1. Connect the USB cable to the computer
      2. HOLD the VOLUME button (bottom of the wheel)
      3. While holding it, press RESET
      4. Release VOLUME

  The screen stays DARK. That is expected.

TXT
else cat <<'TXT'

  Este modo vive na ROM do chip. Roda antes de qualquer firmware, entao
  funciona mesmo com o aparelho travado.

      1. Conecte o cabo USB no computador
      2. SEGURE o botao de VOLUME (o de baixo da roda)
      3. Sem soltar, aperte RESET
      4. Solte o VOLUME

  A tela fica APAGADA. Isso e o esperado.

TXT
fi
}

by_cable() {
    hd "$(t 'USB cable' 'cabo USB')"
    TOOL=$(find_tool) || { need_tool; exit 1; }
    ok "  $(t 'tool found:' 'ferramenta encontrada:') $TOOL"

    recovery_mode
    printf '  %s ' "$(t 'Press ENTER when the player is in flashing mode:' \
                        'Tecle ENTER quando o aparelho estiver em modo de gravacao:')"
    read -r _

    echo; echo "  $(t 'looking for the player...' 'procurando o aparelho...')"
    if ! "$TOOL" --id "$DEV" flash_id >/dev/null 2>&1; then
        echo; er "  $(t 'Player not found.' 'Nao encontrei o aparelho.')"
        if [ "$LANG_SEL" = en ]; then cat <<'TXT'

    - is the cable a DATA cable, not charge-only? (very common)
    - was VOLUME held BEFORE pressing RESET?
    - on Linux you may need sudo, or a udev rule
    - try another USB port, directly on the computer

TXT
        else cat <<'TXT'

    - o cabo e de DADOS, nao so de carga? (e o erro mais comum)
    - o VOLUME foi segurado ANTES do RESET?
    - no Linux talvez precise de sudo, ou de uma regra udev
    - tente outra porta USB, direto no computador

TXT
        fi
        exit 1
    fi
    ok "  $(t 'player found.' 'aparelho encontrado.')"

    hd "$(t 'Final confirmation' 'Ultima confirmacao')"
    if [ "$LANG_SEL" = en ]; then cat <<'TXT'

  The next step REWRITES the player firmware.

    - it does not touch the bootloader
    - it does not touch the settings area
    - it is reversible

  Do not disconnect the cable during the process.

TXT
    else cat <<'TXT'

  A proxima etapa REESCREVE o firmware do aparelho.

    - nao toca no bootloader
    - nao toca na area de configuracao
    - e reversivel

  Nao desconecte o cabo durante o processo.

TXT
    fi
    printf '  %s ' "$(t 'Type  FLASH  to continue:' 'Digite  GRAVAR  para continuar:')"
    read -r R
    EXPECT=$(t FLASH GRAVAR)
    [ "$R" = "$EXPECT" ] || die "$(t 'cancelled.' 'cancelado.')"

    [ -f "$HERE/cabo/flash_OpenPod_Beta10.sh" ] || \
        die "$(t 'cabo/flash_OpenPod_Beta10.sh is missing.' 'falta o cabo/flash_OpenPod_Beta10.sh.')"
    OPENPOD_LANG="$LANG_SEL" export OPENPOD_LANG
    sh "$HERE/cabo/flash_OpenPod_Beta10.sh" "$(dirname "$TOOL")"
}

# ------------------------------------------------------------------ main
[ -f "$UP" ] || { echo "OpenPod_Beta10.up not found / nao encontrado"; exit 1; }

hd "OpenPod - 5.7 Public Beta 10"
pick_lang

if [ "$LANG_SEL" = en ]; then cat <<'TXT'

  HOW DO YOU WANT TO INSTALL?

    1) USB cable     - coming from the stock firmware. This is the
                       one to use for Beta 10.
    2) microSD card  - ONLY if the player already shows
                       Settings -> Update via SD
                       The stock GN-438 does not offer it.
    3) Quit

TXT
else cat <<'TXT'

  COMO VOCE QUER INSTALAR?

    1) Cabo USB       - vindo do firmware de fabrica. E este o
                        caminho da Beta 10.
    2) Cartao microSD - SO se o aparelho ja mostrar
                        Configurar -> Atualizar por SD
                        O GN-438 de fabrica nao oferece isso.
    3) Sair

TXT
fi
printf '  > '
read -r OP
case "$OP" in
  1) by_cable ;;
  2) by_card ;;
  *) echo; echo "  bye / ate logo."; exit 0 ;;
esac
