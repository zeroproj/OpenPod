#!/usr/bin/env python3
"""
bilingue_kit.py — deixa bilingue (EN / pt-BR) um flash_*.sh gerado por
                  tools/make_install_kit.py.

POR QUE EXISTE
    O flash_*.sh e gerado por maquina e sai so em portugues. O pacote
    publico precisa dele em ingles tambem, sem tocar em um unico
    endereco, tamanho ou hash.

COMO FUNCIONA
    1. Injeta, logo antes do banner, uma escolha de idioma e a funcao
       m() — uma tabela de mensagens com as duas linguas.
    2. Troca cada texto em portugues por "$(m <chave>)".
    3. Confere que TODA troca da lista aconteceu (senao aborta) e que
       nenhuma linha com hash/offset mudou.

    O idioma pode vir pronto na variavel OPENPOD_LANG (en|pt). E o que
    o install.sh faz: ele ja perguntou, nao pergunta de novo.

USO
    python3 tools/bilingue_kit.py ENTRADA.sh SAIDA.sh

DEPENDENCIAS
    nenhuma (so a biblioteca padrao)

LIMITACOES
    A tabela de mensagens abaixo casa com o gerador de setembro/2026.
    Se o make_install_kit.py mudar um texto, esta ferramenta aborta
    apontando a chave que nao encontrou — de proposito: e melhor parar
    do que publicar um script meio traduzido.
"""
import re
import sys

# chave -> (ingles, portugues)
MSG = {
    "so_linux":     ("This script is for Linux.", "Este script e para Linux."),
    "tool_falta":   ("smtlink_dump not found in", "smtlink_dump nao encontrado em"),
    "falta":        ("missing:", "faltando:"),
    "p1":           ("[1/6] checking the sector files...",
                     "[1/6] conferindo os arquivos de setor..."),
    "nao_achei":    ("file not found:", "nao encontrei:"),
    "tam_err":      ("wrong size, expected 4096 bytes:",
                     "tamanho errado, esperado 4096 bytes:"),
    "sha_err":      ("SHA-256 does not match:", "SHA-256 nao confere:"),
    "esperado":     ("expected", "esperado"),
    "obtido":       ("got     ", "obtido  "),
    "p2":           ("[2/6] looking for the player...",
                     "[2/6] procurando o aparelho..."),
    "ja_conectado": ("already connected:", "ja conectado:"),
    "conecte1":     (">>> CONNECT THE GN-438 NOW (with the card inserted).",
                     ">>> CONECTE O GN-438 AGORA (com o cartao inserido)."),
    "conecte2":     (">>> NOTE: the MOST RELIABLE way is the other way round —",
                     ">>> ATENCAO: o caminho MAIS CONFIAVEL e o contrario —"),
    "conecte3":     (">>> plug it in, wait ~10s and ONLY THEN run the script.",
                     ">>> plugar, esperar ~10s e SO ENTAO rodar o script."),
    "conecte4":     (">>> Seen on 2026-09-12: connecting now, the player often",
                     ">>> Observado em 2026-09-12: conectando agora, o aparelho"),
    "conecte5":     (">>> re-enumerates right after (the Device N changes).",
                     ">>> costuma re-enumerar logo depois (muda o Device N)."),
    "aguardando":   (">>> Waiting up to", ">>> Aguardando ate"),
    "nao_apareceu": ("the player did not show up in",
                     "o aparelho nao apareceu em"),
    "detectado":    ("detected:", "detectado:"),
    "estab1":       ("waiting", "aguardando"),
    "estab2":       ("to stabilize...", "para estabilizar..."),
    "caiu":         ("the player dropped while stabilizing. Reconnect and run again.",
                     "o aparelho caiu durante a estabilizacao. Reconecte e rode de novo."),
    "continua":     ("still connected — OK", "continua conectado — OK"),
    "raio":         ("Screen shows the bolt and the player is steady? [y/N] ",
                     "A tela mostra o raio e o aparelho esta estavel? [s/N] "),
    "abortado":     ("aborted by the operator", "abortado pelo operador"),
    "p2b":          ("[2b/6] checking the tool first (recovery check)...",
                     "[2b/6] verificacao previa da ferramenta (recovery check)..."),
    "rc_ask":       ("Run the recovery check now? (checks the tool, reads the flash) [Y/n] ",
                     "Rodar o recovery check agora? (confere a ferramenta e le a flash) [S/n] "),
    "rc_skip":      ("SKIPPED at the operator's request",
                     "PULADO a pedido do operador"),
    "rc_run":       ("running — may take a while (clone, 15 hashes, build, read 2 MiB)",
                     "rodando — pode demorar (clona, confere 15 hashes, compila, le 2 MiB)"),
    "rc_fail":      ("recovery check FAILED. DO NOT PROCEED. code",
                     "recovery check FALHOU. NAO PROSSIGA. codigo"),
    "rc_ok":        ("recovery check OK", "recovery check OK"),
    "rc_go":        ("Recovery check passed. Go ahead and write? [y/N] ",
                     "O recovery check passou. Pode seguir para a gravacao? [s/N] "),
    "rc_ausente":   ("recovery_check_linux.sh is not in this folder — skipping",
                     "recovery_check_linux.sh nao esta nesta pasta — pulando"),
    "p3":           ("[3/6] reading the flash, checking the state BEFORE...",
                     "[3/6] lendo a flash e conferindo o estado ANTES..."),
    "le_ini":       ("initial read failed", "leitura inicial falhou"),
    "incompleto":   ("is incomplete", "esta incompleto"),
    "falha":        ("FAIL ", "FALHA"),
    "estado_err":   ("the player is NOT in the expected state. DO NOT PROCEED.",
                     "o aparelho NAO esta no estado esperado. NAO PROSSIGA."),
    "conf1":        (" All checks passed. The next step MODIFIES the firmware.",
                     " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."),
    "conf4":        ("   UNTOUCHED: bootloader, TONE, PSMP",
                     "   NAO toca: bootloader, TONE, PSMP"),
    "palavra":      ("FLASH", "GRAVAR"),
    "digite":       ("Type EXACTLY  FLASH  to continue: ",
                     "Digite EXATAMENTE  GRAVAR  para continuar: "),
    "confirmou":    ("operator confirmed", "operador confirmou"),
    "gravando":     ("writing", "gravando"),
    "wf_falhou":    ("write_flash failed at", "write_flash falhou em"),
    "rel_falhou":   ("re-read failed at", "releitura falhou em"),
    "rel_tam":      ("re-read has the wrong size at", "releitura com tamanho errado em"),
    "setor_err":    ("sector does NOT match after writing:",
                     "setor NAO confere apos gravar:"),
    "setor_ok":     ("OK — sector matches", "OK — setor confere"),
    "p5":           ("[5/6] reading the whole flash, checking the state AFTER...",
                     "[5/6] lendo a flash inteira e conferindo o estado DEPOIS..."),
    "le_fim":       ("final read failed", "leitura final falhou"),
    "res_ok":       ("RESULT: WRITTEN AND VERIFIED", "RESULTADO: GRAVADO E VERIFICADO"),
    "desconecte":   ("   Disconnect and open the main menu.",
                     "   Desconecte e abra o menu principal."),
    "res_err":      ("RESULT: SOME REGION DOES NOT MATCH",
                     "RESULTADO: ALGUMA REGIAO NAO CONFERE"),
    "nao_desligue": ("   DO NOT power off. ROLLBACK to the PREVIOUS state:",
                     "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:"),
    "leve":         ("  keep these: before.bin  after.bin  flash_",
                     "  leve de volta: before.bin  after.bin  flash_"),
    "ja_gravou":    ("*** ALREADY WROTE", "*** JA HAVIA GRAVADO"),
    "ja_gravou2":   ("sector(s). DO NOT POWER THE PLAYER OFF.",
                     "setor(es). NAO DESLIGUE O APARELHO."),
    "reversao":     ("*** ROLLBACK to the PREVIOUS state (this kit's base):",
                     "*** REVERSAO para o estado ANTERIOR (a base deste kit):"),
    "diag":         ("*** Then run diag.sh and check before powering off.",
                     "*** Depois rode diag.sh e confira antes de desligar."),
    "nada":         ("*** Nothing was written.", "*** Nada foi gravado."),
    "escreve":      ("   writes   :", "   grava  :"),
    "muda":         ("   changes  :", "   muda   :"),
    "hdr":          (" OpenPod — writing", " OpenPod — gravacao do"),
    "setores":      ("sectors", "setores"),
    "boot_na":      (" bootloader (0x0..0xD000): NOT ADDRESSED",
                     " bootloader (0x0..0xD000): NAO ENDERECADO"),
}

# (texto que esta no script gerado, texto que entra no lugar, quantas vezes)
TROCAS = [
    ('die "Este script e para Linux."', 'die "$(m so_linux)"', 1),
    ('die "smtlink_dump nao encontrado em $TOOLDIR"',
     'die "$(m tool_falta) $TOOLDIR"', 1),
    ('die "faltando: $c"', 'die "$(m falta) $c"', 1),
    ('log "[1/6] conferindo os arquivos de setor..."', 'log "$(m p1)"', 1),
    ('die "nao encontrei $1"', 'die "$(m nao_achei) $1"', 1),
    ('die "$1 tem $s bytes, esperado 4096"', 'die "$(m tam_err) $1 ($s)"', 1),
    ('die "SHA-256 de $1 nao confere.\n    esperado $2\n    obtido   $g"',
     'die "$(m sha_err) $1\n    $(m esperado) $2\n    $(m obtido) $g"', 1),
    ('log "[2/6] procurando o aparelho..."', 'log "$(m p2)"', 1),
    ('log "        ja conectado: $U"', 'log "        $(m ja_conectado) $U"', 1),
    ('log "        >>> CONECTE O GN-438 AGORA (com o cartao inserido)."',
     'log "        $(m conecte1)"', 1),
    ('log "        >>> ATENCAO: o caminho MAIS CONFIAVEL e o contrario —"',
     'log "        $(m conecte2)"', 1),
    ('log "        >>> plugar, esperar ~10s e SO ENTAO rodar o script."',
     'log "        $(m conecte3)"', 1),
    ('log "        >>> Observado em 2026-09-12: conectando agora, o aparelho"',
     'log "        $(m conecte4)"', 1),
    ('log "        >>> costuma re-enumerar logo depois (muda o Device N)."',
     'log "        $(m conecte5)"', 1),
    ('log "        >>> Aguardando ate ${ESPERA}s..."',
     'log "        $(m aguardando) ${ESPERA}s..."', 1),
    ('die "aparelho nao apareceu em ${ESPERA}s."',
     'die "$(m nao_apareceu) ${ESPERA}s."', 1),
    ('log "        detectado: $U"', 'log "        $(m detectado) $U"', 1),
    ('log "        aguardando ${ESTABILIZA}s para estabilizar..."',
     'log "        $(m estab1) ${ESTABILIZA}s $(m estab2)"', 1),
    ('die "o aparelho caiu durante a estabilizacao. Reconecte e rode de novo."',
     'die "$(m caiu)"', 1),
    ('log "        continua conectado — OK"', 'log "        $(m continua)"', 1),
    ('printf "A tela mostra o raio e o aparelho esta estavel? [s/N] "',
     'printf \'%s\' "$(m raio)"', 1),
    ('die "abortado pelo operador"', 'die "$(m abortado)"', 3),
    ('log "[2b/6] verificacao previa da ferramenta (recovery check)..."',
     'log "$(m p2b)"', 1),
    ('printf "Rodar o recovery check agora? (confere a ferramenta e le a flash) [S/n] "',
     'printf \'%s\' "$(m rc_ask)"', 1),
    ('log "        PULADO a pedido do operador"', 'log "        $(m rc_skip)"', 1),
    ('log "        rodando — pode demorar (clona, confere 15 hashes, compila, le 2 MiB)"',
     'log "        $(m rc_run)"', 1),
    ('die "recovery check FALHOU (codigo $RCST). NAO PROSSIGA."',
     'die "$(m rc_fail) $RCST"', 1),
    ('log "        recovery check OK"', 'log "        $(m rc_ok)"', 1),
    ('printf "O recovery check passou. Pode seguir para a gravacao? [s/N] "',
     'printf \'%s\' "$(m rc_go)"', 1),
    ('log "        recovery_check_linux.sh nao esta nesta pasta — pulando"',
     'log "        $(m rc_ausente)"', 1),
    ('log "[3/6] lendo a flash e conferindo o estado ANTES..."', 'log "$(m p3)"', 1),
    ('die "leitura inicial falhou"', 'die "$(m le_ini)"', 1),
    ('die "before.bin incompleto"', 'die "before.bin $(m incompleto)"', 1),
    ('log "        FALHA $1"', 'log "        $(m falha) $1"', 2),
    ('log "          esperado $4"', 'log "          $(m esperado) $4"', 2),
    ('log "          obtido   $g"', 'log "          $(m obtido) $g"', 2),
    ('die "o aparelho NAO esta no estado esperado. NAO PROSSIGA."',
     'die "$(m estado_err)"', 1),
    ('log " Tudo conferido. A proxima etapa MODIFICA o firmware do aparelho."',
     'log "$(m conf1)"', 1),
    ('log "   NAO toca: bootloader, TONE, PSMP"', 'log "$(m conf4)"', 1),
    ("printf 'Digite EXATAMENTE  GRAVAR  para continuar: '",
     'printf \'%s\' "$(m digite)"', 1),
    ('[ "$R" = "GRAVAR" ]', '[ "$R" = "$(m palavra)" ]', 1),
    ('log "operador confirmou"', 'log "$(m confirmou)"', 1),
    ('log "[$1] gravando $2 a partir de $3..."',
     'log "[$1] $(m gravando) $2 <- $3..."', 1),
    ('die "write_flash em $2 falhou"', 'die "$(m wf_falhou) $2"', 1),
    ('die "releitura de $2 falhou"', 'die "$(m rel_falhou) $2"', 1),
    ('die "releitura de $2 tem $s bytes"', 'die "$(m rel_tam) $2 ($s)"', 1),
    ('die "setor $2 NAO confere apos gravar.\n    esperado $4\n    obtido   $g"',
     'die "$(m setor_err) $2\n    $(m esperado) $4\n    $(m obtido) $g"', 1),
    ('log "        OK — setor confere"', 'log "        $(m setor_ok)"', 1),
    ('log "[5/6] lendo a flash inteira e conferindo o estado DEPOIS..."',
     'log "$(m p5)"', 1),
    ('die "leitura final falhou"', 'die "$(m le_fim)"', 1),
    ('die "after.bin incompleto"', 'die "after.bin $(m incompleto)"', 1),
    ('log "   Desconecte e abra o menu principal."', 'log "$(m desconecte)"', 1),
    ('log "   NAO desligue o aparelho. REVERSAO para o estado ANTERIOR:"',
     'log "$(m nao_desligue)"', 1),
    ('log "  leve de volta: before.bin  after.bin  flash_$VERSAO.log"',
     'log "$(m leve)$VERSAO.log"', 1),
    ('log "*** JA HAVIA GRAVADO $WROTE setor(es). NAO DESLIGUE O APARELHO."',
     'log "$(m ja_gravou) $WROTE $(m ja_gravou2)"', 1),
    ('log "*** REVERSAO para o estado ANTERIOR (a base deste kit):"',
     'log "$(m reversao)"', 1),
    ('log "*** Depois rode diag.sh e confira antes de desligar."',
     'log "$(m diag)"', 1),
    ('log "*** Nada foi gravado."', 'log "$(m nada)"', 1),
    ('log " bootloader (0x0..0xD000): NAO ENDERECADO"', 'log "$(m boot_na)"', 1),
]

# trocas com parte variavel (regex). (padrao, substituicao, quantas)
TROCAS_RE = [
    (r'log " OpenPod — gravacao do (\S+)   \((\d+) setores, (\d+) KiB\)"',
     r'log "$(m hdr) \1   (\2 $(m setores), \3 KiB)"', 1),
    (r'log "   grava  : (\d+) KiB em (\d+) setores"',
     r'log "$(m escreve) \1 KiB / \2 $(m setores)"', 1),
    (r'log "   muda   : (.*)"', r'log "$(m muda) \1"', 1),
    (r'log " \[6/6\] RESULTADO: (\S+) GRAVADO E VERIFICADO"',
     r'log " [6/6] \1 — $(m res_ok)"', 1),
    (r'log " \[6/6\] RESULTADO: ALGUMA REGIAO NAO CONFERE"',
     r'log " [6/6] $(m res_err)"', 1),
]


def bloco_idioma():
    def tabela(i):
        linhas = []
        for chave, par in MSG.items():
            texto = par[i].replace('\\', '\\\\').replace('"', '\\"')
            linhas.append('        %s) echo "%s" ;;' % (chave, texto))
        return "\n".join(linhas)

    return """
# ------------------------------------------------------------------ idioma
# Se o install.sh ja perguntou, ele passa OPENPOD_LANG e nao perguntamos
# de novo. Rodando este script sozinho, a pergunta vem aqui.
OPENPOD_LANG=${OPENPOD_LANG:-}
if [ "$OPENPOD_LANG" != en ] && [ "$OPENPOD_LANG" != pt ]; then
    printf '\\n  1) English     2) Portugues do Brasil\\n  > '
    read -r _IDIOMA
    case "$_IDIOMA" in 1) OPENPOD_LANG=en ;; *) OPENPOD_LANG=pt ;; esac
    echo
fi
m() {
    if [ "$OPENPOD_LANG" = en ]; then
        case "$1" in
%s
        *) echo "$1" ;;
        esac
    else
        case "$1" in
%s
        *) echo "$1" ;;
        esac
    fi
}
# --------------------------------------------------------------------------
""" % (tabela(0), tabela(1))


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    entrada, saida = sys.argv[1], sys.argv[2]
    texto = open(entrada, encoding="utf-8").read()
    original = texto

    faltando = []
    for velho, novo, n in TROCAS:
        achou = texto.count(velho)
        if achou != n:
            faltando.append("  %-60s esperado %d, achei %d" % (velho[:60], n, achou))
            continue
        texto = texto.replace(velho, novo)
    for padrao, sub, n in TROCAS_RE:
        achou = len(re.findall(padrao, texto))
        if achou != n:
            faltando.append("  RE %-57s esperado %d, achei %d" % (padrao[:57], n, achou))
            continue
        texto = re.sub(padrao, sub, texto)

    if faltando:
        print("ABORTADO — o script de entrada nao bate com a tabela:")
        print("\n".join(faltando))
        sys.exit(1)

    # o bloco de idioma entra logo antes do banner
    marca = 'log "======================================================================"'
    i = texto.index(marca)
    texto = texto[:i] + bloco_idioma().lstrip("\n") + "\n" + texto[i:]

    # nenhuma linha com hash ou offset pode ter mudado
    def tecnicas(s):
        return [l for l in s.splitlines()
                if re.search(r"\b[0-9a-f]{64}\b", l) or "write_flash 0x" in l]
    if tecnicas(original) != tecnicas(texto):
        sys.exit("ABORTADO — uma linha com hash/offset mudou. Nao gravei nada.")

    open(saida, "w", encoding="utf-8").write(texto)
    print("ok: %s  (%d linhas, %d mensagens)"
          % (saida, len(texto.splitlines()), len(MSG)))


if __name__ == "__main__":
    main()
