#!/bin/sh
# OpenPod — instalador da Beta 1
#
# Dois caminhos. O primeiro nao precisa de computador nem de ferramenta
# nenhuma; o segundo e para quem esta no firmware de fabrica ou travado.
#
#   sh instalar.sh            mostra o menu
#   sh instalar.sh --cartao   so as instrucoes do cartao
#   sh instalar.sh --cabo     vai direto para a gravacao por cabo

set -eu
export LC_ALL=C

AQUI=$(cd "$(dirname "$0")" && pwd)
UP="$AQUI/OpenPod_Beta1.up"
DEV=301a:2801
UPSTREAM=https://github.com/ilyakurdyukov/smartlink_flash

azul()  { printf '\033[1;36m%s\033[0m\n' "$*"; }
verde() { printf '\033[1;32m%s\033[0m\n' "$*"; }
vermelho() { printf '\033[1;31m%s\033[0m\n' "$*"; }
titulo() { echo; azul "=============================================================="; azul " $*"; azul "=============================================================="; }
morre() { echo; vermelho "ERRO: $*"; exit 1; }

caminho_cartao() {
titulo "CAMINHO 1 — pelo cartao microSD   (o mais simples)"
cat <<'TXT'

  Serve se o aparelho LIGA e voce consegue chegar em Configurar.
  Nao precisa de computador conectado, nem de ferramenta nenhuma.

  1. Copie o arquivo  OpenPod_Beta1.up  para a RAIZ do cartao,
     renomeando para:

         update.up

     A raiz e a pasta principal do cartao, nao dentro de outra pasta.

  2. Ponha o cartao no aparelho e ligue.

  3. No aparelho:   Configurar  ->  Atualizar por SD  ->  Sim

     A tela vai mostrar o progresso. NAO DESLIGUE e nao tire o cartao.

  4. Quando reiniciar, APAGUE o update.up do cartao.
     Se ele ficar la, o aparelho tenta atualizar toda vez que liga.

  5. Confira em:   Configurar  ->  Informacoes
     Deve aparecer:  OpenPod Beta 1

TXT
verde "  Pronto. Se funcionou, voce nao precisa do caminho 2."
echo
}

acha_ferramenta() {
    for c in "$AQUI/smtlink_dump" "$AQUI/smartlink_flash/smtlink_dump" \
             /opt/smartlink_flash/smtlink_dump "$(command -v smtlink_dump || true)"; do
        [ -n "$c" ] && [ -x "$c" ] && { echo "$c"; return 0; }
    done
    return 1
}

ensina_ferramenta() {
titulo "A ferramenta de gravacao nao foi encontrada"
cat <<TXT

  O OpenPod nao distribui o gravador junto. Ele e um projeto separado,
  de Ilya Kurdyukov, e nao traz licenca que nos permita redistribuir.

  Baixar e compilar leva um minuto:

      git clone $UPSTREAM
      cd smartlink_flash
      make

  Depois rode este instalador de novo. Ele procura o smtlink_dump em:

      ./smtlink_dump
      ./smartlink_flash/smtlink_dump
      /opt/smartlink_flash/smtlink_dump
      qualquer lugar do seu PATH

  No Linux voce vai precisar de libusb-1.0-dev.
  No macOS:  brew install libusb

TXT
}

modo_recovery() {
titulo "Pondo o aparelho em modo de gravacao"
cat <<'TXT'

  Este modo vive na ROM do chip. Ele roda ANTES de qualquer firmware,
  entao funciona mesmo com o aparelho travado ou sem imagem.

      1. Conecte o cabo USB no computador
      2. SEGURE o botao de VOLUME  (o de baixo da roda)
      3. Sem soltar, aperte RESET
      4. Solte o VOLUME

  O aparelho fica com a tela APAGADA. Isso e o esperado.

  No macOS pode aparecer "O disco inserido nao e legivel" — clique
  em IGNORAR. No Linux nao aparece nada.

TXT
}

caminho_cabo() {
    titulo "CAMINHO 2 — por cabo USB"
    echo
    echo "  Serve se o aparelho nao liga, esta travado, ou esta no"
    echo "  firmware de fabrica sem a opcao de atualizar por SD."
    echo

    TOOL=$(acha_ferramenta) || { ensina_ferramenta; exit 1; }
    verde "  ferramenta encontrada: $TOOL"

    modo_recovery
    printf '  Quando o aparelho estiver no modo de gravacao, tecle ENTER: '
    read -r _

    echo
    echo "  procurando o aparelho..."
    if ! "$TOOL" --id "$DEV" flash_id >/dev/null 2>&1; then
        echo
        vermelho "  Nao encontrei o aparelho."
        cat <<'TXT'

  Confira, nesta ordem:
    - o cabo e de DADOS, nao so de carga? (troque de cabo, e comum)
    - a sequencia foi VOLUME segurado ANTES do RESET?
    - no Linux, talvez precise de sudo, ou de uma regra udev
    - tente outra porta USB, de preferencia direto no computador

TXT
        exit 1
    fi
    verde "  aparelho encontrado."

    titulo "Ultima confirmacao"
    cat <<'TXT'

  A proxima etapa REESCREVE o firmware do aparelho.

    - nao toca no bootloader
    - nao toca na area de configuracao (PSMP)
    - e reversivel: o firmware de fabrica esta em recovery/

  Se faltar energia no meio, o aparelho pode precisar do modo de
  gravacao de novo. Nao desconecte o cabo.

TXT
    printf '  Digite  GRAVAR  para continuar: '
    read -r R
    [ "$R" = "GRAVAR" ] || morre "cancelado."

    [ -f "$AQUI/flash_OpenPod_Beta1.sh" ] || \
        morre "falta o flash_OpenPod_Beta1.sh nesta pasta."
    sh "$AQUI/flash_OpenPod_Beta1.sh" "$(dirname "$TOOL")"
}

[ -f "$UP" ] || morre "nao achei o OpenPod_Beta1.up nesta pasta."

case "${1:-}" in
  --cartao) caminho_cartao; exit 0 ;;
  --cabo)   caminho_cabo;   exit 0 ;;
esac

titulo "OpenPod — Beta 1"
cat <<'TXT'

  Uma interface inspirada no iPod nano para o player GN-438.

  COMO VOCE QUER INSTALAR?

    1) Pelo cartao microSD   — o aparelho liga e voce chega em Configurar
                               NAO precisa de computador. Recomendado.

    2) Por cabo USB          — o aparelho nao liga, esta travado, ou
                               esta no firmware de fabrica

    3) Sair

TXT
printf '  Escolha [1/2/3]: '
read -r OP
case "$OP" in
  1) caminho_cartao ;;
  2) caminho_cabo ;;
  *) echo; echo "  ate logo."; exit 0 ;;
esac
