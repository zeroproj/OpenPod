#!/bin/sh
# diag.sh — OpenPod. GERADO por tools/make_install_kit.py.
# SOMENTE LEITURA. Nao grava nada no aparelho.
#
# USO   sudo sh diag.sh [/opt/smartlink_flash]

set -eu
export LC_ALL=C
TOOLDIR=${1:-/opt/smartlink_flash}
TOOL="$TOOLDIR/smtlink_dump"
[ -x "$TOOL" ] || { echo "smtlink_dump nao encontrado em $TOOLDIR" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "falta python3" >&2; exit 1; }

log() { printf "%s\n" "$*"; }
die() { printf "\n*** %s\n" "$*" >&2; exit 1; }

# --- espera ativa pelo aparelho ---------------------------------
# O aparelho precisa de alguns segundos entre plugar e o primeiro
# comando, senao cai do modo card reader no meio da operacao.
ESPERA=180        # segundos ate desistir
ESTABILIZA=8      # segundos de folga apos detectar
aguardar_aparelho() {
    U=$(lsusb | grep -i "301a:2801" || true)
    if [ -n "$U" ]; then
        log "        ja conectado: $U"
    else
        log ""
        log "        >>> CONECTE O GN-438 AGORA (com o cartao inserido)."
        log "        >>> ATENCAO: o caminho MAIS CONFIAVEL e o contrario —"
        log "        >>> plugar, esperar ~10s e SO ENTAO rodar o script."
        log "        >>> Observado em 2026-09-12: conectando agora, o aparelho"
        log "        >>> costuma re-enumerar logo depois (muda o Device N)."
        log "        >>> Aguardando ate ${ESPERA}s..."
        i=0
        while [ "$i" -lt "$ESPERA" ]; do
            U=$(lsusb | grep -i "301a:2801" || true)
            [ -n "$U" ] && break
            i=$((i + 1)); sleep 1
        done
        [ -n "$U" ] || die "aparelho nao apareceu em ${ESPERA}s."
        log "        detectado: $U"
    fi
    log "        aguardando ${ESTABILIZA}s para estabilizar..."
    sleep "$ESTABILIZA"
    V=$(lsusb | grep -i "301a:2801" || true)
    [ -n "$V" ] || die "o aparelho caiu durante a estabilizacao. Reconecte e rode de novo."
    log "        continua conectado — OK"
}
aguardar_aparelho
log ""
printf "A tela mostra o raio e o aparelho esta estavel? [s/N] "
read -r OK
case "$OK" in [sSyY]*) ;; *) die "abortado pelo operador" ;; esac
# ----------------------------------------------------------------

echo "=== lendo a flash inteira (SO LEITURA) ==="
"$TOOL" --id 301a:2801 read_flash 0 2M diag.bin || { echo "leitura falhou" >&2; exit 1; }
echo

python3 - <<'PYEOF'
import hashlib
d = open('diag.bin','rb').read()
print("tamanho lido: %d bytes (esperado 2097152)" % len(d))
if len(d) != 2097152:
    print("!! tamanho errado — o relatorio abaixo nao e confiavel")
print()
# lista de (hash, rotulo) — NUNCA um dict: hashes iguais colapsariam
# e a regiao intacta seria rotulada com o ultimo estado inserido.
reg = [
    ('bootloader', 0, 51532, [('861184003923634be0f2ae9883456035b40d1ea72f97682890238edfae3acb31','ORIGINAL'), ('861184003923634be0f2ae9883456035b40d1ea72f97682890238edfae3acb31','ANTES esperado'), ('861184003923634be0f2ae9883456035b40d1ea72f97682890238edfae3acb31','ALVO V037')]),
    ('ptable', 53248, 64, [('9f93d4435e7cb819b2dad2f38edf91fb0a0af44654c4d9fcd3df174bf3380a2d','ORIGINAL'), ('9f93d4435e7cb819b2dad2f38edf91fb0a0af44654c4d9fcd3df174bf3380a2d','ANTES esperado'), ('9f93d4435e7cb819b2dad2f38edf91fb0a0af44654c4d9fcd3df174bf3380a2d','ALVO V037')]),
    ('FIRM', 57344, 1647984, [('e2a7b86339030b94268dac7d562a167613a3e769c866790353b4921cad85dbdc','ORIGINAL'), ('d6798281b863afe123978cbec540961f4f9106f562f26b2c0b07b5541eae3e97','ANTES esperado'), ('e24c8f335e654324e3c406e12c6be3f874070f0427ad03ad4a15667f5182c8b3','ALVO V037')]),
    ('TONE', 1708032, 8248, [('7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace','ORIGINAL'), ('7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace','ANTES esperado'), ('7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace','ALVO V037')]),
]
print("%-11s %-18s %s" % ("REGIAO","SHA-256 (16)","ESTADO"))
print("-" * 60)
for n, o, t, pares in reg:
    g = hashlib.sha256(d[o:o+t]).hexdigest()
    hits = [lab for h, lab in pares if h == g]
    if not hits:            est = '??? DESCONHECIDO'
    elif len(hits) == len(pares): est = 'INTACTA (igual em todos)'
    else:                   est = ' / '.join(hits)
    print("%-11s %-18s %s" % (n, g[:16], est))
print()
print("=== cabecalho HLKJ ===")
print("  ", d[0:8].hex(), "(deve comecar com 484c4b4a)")
PYEOF

echo
echo "=== pronto. envie TODO o texto acima. diag.bin ficou salvo aqui. ==="
