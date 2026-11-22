#!/bin/sh
# empacota_mac.sh — roda NO MAC, na hora da mudanca para o Linux (D30).
# Junta num arquivo so tudo o que o Linux precisa e o GitHub nao guarda:
#   - o projeto inteiro, com o .git (branches locais, kits gerados, o gravador .exe);
#   - a configuracao do opencode e as chaves dele (auth.json: SEGREDO);
#   - a memoria do Claude deste projeto, o CLAUDE.md/RTK.md global e as skills.
# NAO leva o banco do opencode (5 GB de historico de conversa).
#
# USO   sh mudanca/empacota_mac.sh
# SAI   ~/OpenPod-mudanca/OpenPod-mudanca.tar.gz  (copie para o Linux por pendrive/scp)
#       NUNCA suba esse arquivo para o GitHub nem para a nuvem: tem as chaves.
set -eu

PROJ="/Users/zeroproj/Sistemas LWP/OpenPod"
MEM="$HOME/.claude/projects/-Users-zeroproj-Sistemas-LWP-OpenPod/memory"
OUT="$HOME/OpenPod-mudanca"
STAGE="$OUT/staging"

pare() { echo "PAROU: $*"; exit 1; }

# 1. nada rodando: uma ficha no meio se perde
if pgrep -f "opencode run" >/dev/null 2>&1; then
  pare "o opencode ainda esta rodando uma ficha. Espere o PRONTO/ESCALADA."
fi

# 2. nada sem commit, em nenhum worktree
cd "$PROJ"
git worktree list --porcelain | sed -n 's/^worktree //p' | while IFS= read -r wt; do
  if [ -n "$(git -C "$wt" status --porcelain --untracked-files=no)" ]; then
    pare "ha mudanca sem commit em: $wt"
  fi
done

# 3. tudo enviado ao privado (copia de seguranca, alem do arquivo)
git push -q privado privado-completo:main
git push -q privado 'refs/heads/limtistech/*:refs/heads/limtistech/*'
echo "privado atualizado (main + branches das fichas)"

# 4. monta o pacote
rm -rf "$STAGE"; mkdir -p "$STAGE/opencode" "$STAGE/claude/memory" "$STAGE/claude/skills"
cp "$HOME/.config/opencode/opencode.jsonc" "$STAGE/opencode/"
[ -f "$HOME/.local/share/opencode/auth.json" ] && cp "$HOME/.local/share/opencode/auth.json" "$STAGE/opencode/"
cp "$MEM"/*.md "$STAGE/claude/memory/"
# chave secreta que assina os pacotes do instalador (D36): SEGREDO, vai junto e volta com 600
mkdir -p "$STAGE/openpod" && cp -p "$HOME/.openpod/"* "$STAGE/openpod/" 2>/dev/null || true
for f in CLAUDE.md RTK.md; do [ -f "$HOME/.claude/$f" ] && cp "$HOME/.claude/$f" "$STAGE/claude/"; done
cp -RL "$HOME/.claude/skills/." "$STAGE/claude/skills/" 2>/dev/null || true
cp "$PROJ/mudanca/instala_linux.sh" "$OUT/"

echo "empacotando o projeto (uns 800 MB)..."
tar -czf "$OUT/OpenPod-mudanca.tar.gz" \
    --exclude='__pycache__' --exclude='.DS_Store' --exclude='.publicar-tmp' \
    -C "$(dirname "$PROJ")" "$(basename "$PROJ")" \
    -C "$STAGE" opencode claude openpod
chmod 600 "$OUT/OpenPod-mudanca.tar.gz"
rm -rf "$STAGE"

( cd "$OUT" && shasum -a 256 OpenPod-mudanca.tar.gz > OpenPod-mudanca.sha256 )
ls -lh "$OUT"
echo
echo "PRONTO. Copie a pasta $OUT inteira para o Linux e rode la:"
echo "    sh instala_linux.sh"
