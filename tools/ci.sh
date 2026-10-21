#!/bin/sh
# ci.sh — o "npm run ci" do OpenPod. Para no primeiro erro.
# NAO ALTERAR sem o arquiteto (hash em tests/PROTEGIDOS.sha256).
# Uso: sh tools/ci.sh        Rode antes de dizer "terminei".
set -e
cd "$(dirname "$0")/.."
echo "== 1. ORIGINAL intacto"
echo "b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f  firmware/ORIGINAL/GN438_original.bin" | shasum -a 256 -c -
echo "== 2. arquivos protegidos"
shasum -a 256 -c tests/PROTEGIDOS.sha256
echo "== 3. sintaxe das ferramentas"
python3 -m py_compile tools/*.py tests/*.py
echo "== 4. testes"
python3 tests/test_roundtrip.py
python3 tools/patch_icones_home.py --autoteste
python3 tests/test_rc2.py
echo "== 5. segredos"
if command -v gitleaks >/dev/null; then gitleaks detect --no-banner --redact -q; else echo "gitleaks ausente (pulado)"; fi
echo "CI OK"
