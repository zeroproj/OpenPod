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
ESTABILIZA=4      # segundos de folga apos detectar
aguardar_aparelho() {
    U=$(lsusb | grep -i "301a:2801" || true)
    if [ -n "$U" ]; then
        log "        ja conectado: $U"
    else
        log ""
        log "        >>> CONECTE O GN-438 AGORA (com o cartao inserido)."
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
    ('bootloader', 0, 51532, [('861184003923634be0f2ae9883456035b40d1ea72f97682890238edfae3acb31','ORIGINAL'), ('861184003923634be0f2ae9883456035b40d1ea72f97682890238edfae3acb31','ANTES esperado'), ('861184003923634be0f2ae9883456035b40d1ea72f97682890238edfae3acb31','ALVO V003')]),
    ('ptable', 53248, 64, [('9f93d4435e7cb819b2dad2f38edf91fb0a0af44654c4d9fcd3df174bf3380a2d','ORIGINAL'), ('5cba69808576a5a94f34016576c2c5566e004a1191ab90389b61e64c1aa0038d','ANTES esperado'), ('93450a066ef27e0c3f22d91accea08eade810f116b9417e1b8ff151eba4be4d9','ALVO V003')]),
    ('FIRM', 57344, 1647984, [('e2a7b86339030b94268dac7d562a167613a3e769c866790353b4921cad85dbdc','ORIGINAL'), ('a3e73c7d62622b311063b75a91ee9e78081d9a287f5b2072c5942f17fc9b85cf','ANTES esperado'), ('d4b16947a7cab225e19e6db8c93197ab006f2fd0e2a69f719733d335400c0092','ALVO V003')]),
    ('TONE', 1708032, 8248, [('7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace','ORIGINAL'), ('7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace','ANTES esperado'), ('7f2882af95534ec56c6261ac14c74ddcf9a83c8deb4b5e97e333b2ee3f8b4ace','ALVO V003')]),
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
