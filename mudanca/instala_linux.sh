#!/bin/sh
# instala_linux.sh — roda NO LINUX (Ubuntu 22.04 ou mais novo), na pasta onde esta o
# OpenPod-mudanca.tar.gz gerado pelo empacota_mac.sh (D30).
# Monta tudo em ~/OpenPod: projeto, Python com as versoes certas, zig do SDK,
# gravador por cabo (smartlink_flash), opencode e Claude Code, e roda o CI.
#
# USO   sh instala_linux.sh
# Pede a senha do sudo (pacotes do sistema e /opt/smartlink_flash).
set -eu

AQUI=$(cd "$(dirname "$0")" && pwd)
PAC="$AQUI/OpenPod-mudanca.tar.gz"
DEST="$HOME/OpenPod"
VENV="$HOME/.venvs/openpod"
SMARTLINK_COMMIT=e5c62a8
ORIGINAL_SHA=b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f

passo() { printf '\n\033[1;36m== %s\033[0m\n' "$*"; }
pare()  { printf '\033[1;31mPAROU: %s\033[0m\n' "$*"; exit 1; }

[ -f "$PAC" ] || pare "nao achei $PAC"
[ -e "$DEST" ] && pare "$DEST ja existe; mova ou apague antes (nada foi mexido)"

passo "1. conferindo o pacote"
( cd "$AQUI" && sha256sum -c OpenPod-mudanca.sha256 ) || pare "o pacote chegou corrompido; copie de novo"

passo "2. pacotes do sistema"
if command -v apt-get >/dev/null; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq git python3 python3-venv python3-pip build-essential \
       libusb-1.0-0-dev perl curl sqlite3 ca-certificates
  # o gh so vem no Ubuntu 23.04+; no 22.04 usa o repositorio oficial do GitHub
  if ! command -v gh >/dev/null && ! sudo apt-get install -y -qq gh; then
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg status=none
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null
    sudo apt-get update -qq && sudo apt-get install -y -qq gh
  fi
else
  echo "Sem apt-get. Instale a mao: git gh python3 (com venv) gcc make libusb-1.0 (dev) perl curl sqlite3"
fi

passo "3. projeto em $DEST"
TMPX=$(mktemp -d)
tar -xzf "$PAC" -C "$TMPX"
mv "$TMPX/OpenPod" "$DEST"
git -C "$DEST" worktree prune        # os worktrees do Mac nao existem aqui; as branches ficam
echo "$ORIGINAL_SHA  $DEST/firmware/ORIGINAL/GN438_original.bin" | sha256sum -c - \
  || pare "o ORIGINAL nao confere!"

passo "4. Python do projeto ($VENV)"
python3 -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q unicorn==2.1.4 capstone==5.0.9 pillow numpy ziglang==0.13.0
for rc in "$HOME/.bashrc" "$HOME/.profile"; do
  grep -q 'venvs/openpod/bin' "$rc" 2>/dev/null || \
    printf '\n# OpenPod: python3 do projeto (unicorn, capstone, zig 0.13)\nexport PATH="$HOME/.venvs/openpod/bin:$HOME/.local/bin:$PATH"\n' >> "$rc"
done
PATH="$VENV/bin:$HOME/.local/bin:$PATH"; export PATH

passo "5. gravador por cabo em /opt/smartlink_flash (nosso fork, commit $SMARTLINK_COMMIT)"
SL=$(mktemp -d)
git clone -q https://github.com/zeroproj/smartlink_flash "$SL"
git -C "$SL" checkout -q "$SMARTLINK_COMMIT"
make -C "$SL" -s
sudo mkdir -p /opt/smartlink_flash
sudo cp -r "$SL"/. /opt/smartlink_flash/
[ -x /opt/smartlink_flash/smtlink_dump ] || pare "o smtlink_dump nao compilou"
rm -rf "$SL"

passo "6. opencode (config e chaves)"
command -v opencode >/dev/null || curl -fsSL https://opencode.ai/install | bash
mkdir -p "$HOME/.config/opencode" "$HOME/.local/share/opencode"
cp "$TMPX/opencode/opencode.jsonc" "$HOME/.config/opencode/"
if [ -f "$TMPX/opencode/auth.json" ]; then
  cp "$TMPX/opencode/auth.json" "$HOME/.local/share/opencode/"
  chmod 600 "$HOME/.local/share/opencode/auth.json"
fi

passo "7. Claude Code (memoria do projeto, CLAUDE.md, skills)"
command -v claude >/dev/null || curl -fsSL https://claude.ai/install.sh | bash
CHAVE=$(printf '%s' "$DEST" | sed 's/[^A-Za-z0-9]/-/g')
mkdir -p "$HOME/.claude/projects/$CHAVE/memory" "$HOME/.claude/skills"
cp "$TMPX/claude/memory/"*.md "$HOME/.claude/projects/$CHAVE/memory/"
for f in CLAUDE.md RTK.md; do
  [ -f "$TMPX/claude/$f" ] && [ ! -f "$HOME/.claude/$f" ] && cp "$TMPX/claude/$f" "$HOME/.claude/"
done
cp -rn "$TMPX/claude/skills/." "$HOME/.claude/skills/" 2>/dev/null || true
rm -rf "$TMPX"

passo "8. CI do projeto"
( cd "$DEST" && sh tools/ci.sh ) || echo "O CI falhou: abra o Claude em $DEST e peca para ele olhar."

passo "FALTA SO VOCE (precisa do navegador):"
cat <<EOF
  1) GitHub, as duas contas (escolha SSH e deixe o gh criar a chave):
       gh auth login        (entre com zeroproj)
       gh auth login        (de novo, com limtistech)
       ssh -T git@github.com
  2) Claude Code:  cd ~/OpenPod && claude     (faz o login na primeira vez)
  3) Feche e abra o terminal (para o PATH novo valer).
Gravar por cabo:  sudo sh release/<versao>/cabo/flash_*.sh   (o gravador ja esta em /opt/smartlink_flash)
EOF
