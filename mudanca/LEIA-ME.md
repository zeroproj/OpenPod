# Mudança do projeto para o Linux (D30)

1. **No Mac**, com nenhuma ficha rodando: `sh mudanca/empacota_mac.sh`.
   Gera `~/OpenPod-mudanca/` (projeto inteiro + chaves do opencode + memória do Claude). **Tem segredo: não subir para lugar nenhum.**
2. Copie a pasta `~/OpenPod-mudanca/` para o Linux (pendrive ou `scp`).
3. **No Linux** (Ubuntu/Debian): `sh instala_linux.sh`. Monta tudo em `~/OpenPod` e roda o CI.
4. Faltam só os logins com navegador: `gh auth login` (zeroproj e limtistech) e `claude`.

Pendência antes da mudança (coordenação): o `tools/ci.sh` usa `mktemp -d -t openpod_ci`, que o Linux recusa
(GNU pede `XXXXXX`). Corrigir para `mktemp -d "${TMPDIR:-/tmp}/openpod_ci.XXXXXX"` e atualizar o hash em
`tests/PROTEGIDOS.sha256` no merge da ficha 028 (que também mexe no `ci.sh`).
Depois da mudança: a 3.4 (Ghidra, D21) começa no Linux.
