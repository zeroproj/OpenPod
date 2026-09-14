#!/usr/bin/env python3
"""
build.py — constroi a imagem do OpenPod a partir do ORIGINAL, numa
           sequencia DECLARADA.

POR QUE ISTO EXISTE

    Ate hoje o firmware era uma CORRENTE: v070 -> v071 -> v072 -> v073,
    cada passo aplicado a mao sobre o anterior. Sao 90 imagens em
    `firmware/WORKING/`. Consequencias:

      - para corrigir um patch antigo era preciso refazer todos os
        seguintes, ou remendar o resultado (foi o que aconteceu com o
        `patch_extras` -> `patch_extras_fix` -> e agora um terceiro);
      - ninguem sabia dizer, sem ler o CHANGELOG inteiro, **o que** esta
        dentro da imagem;
      - patches superados (tres versoes de `scrollbar`, `bar_height`
        contra `status_bar`) continuavam na historia sem estar na lista.

    Aqui a imagem passa a ser uma RECEITA. Mudou um passo? Reconstroi.

O QUE O PIPELINE DESCOBRIU — e por que ele PARA no passo 7

    Rodando, ele bateu tres vezes em dependencia escondida e na quarta
    achou a causa de fundo.

    As tres primeiras eram erros de contabilidade minha:

      1. `patch_home_keys.py` nao estava em lugar nenhum — nem na receita,
         nem na lista de excluidos. Eu tinha perdido ele de vista.
      2. `patch_chrome_padrao.py` NAO e superado pelo Saturno: e
         PRE-REQUISITO. A tabela de tema foi retrofitada em cima das
         rotinas que ele cria. Eu vinha descrevendo o Saturno como
         fundacao; ele e revestimento.
      3. `patch_cor_texto_lista.py`, idem: o S10 reescreve o gancho que
         ele criou.

    A quarta e estrutural, e nenhuma reordenacao resolve:

        # patch_cor_selecao.py, e varios outros
        f = LIVRE_INI
        for i in range(LIVRE_INI, LIVRE_INI + 0x4000):
            if d[i] != 0xFF:
                f = i + 1
        return (f + 3) & ~3

    E um ALOCADOR INCREMENTAL. Cada patch se encaixa logo depois do
    ultimo byte ocupado. Logo **o endereco de uma rotina nao e escolhido:
    ele emerge de tudo que rodou antes**. E os patches seguintes fixam
    esse endereco no proprio codigo.

    Medida: depois dos 6 primeiros passos desta receita, a area livre
    comeca em 0x001A4041. Mas `patch_cor_texto_lista` exige a rotina em
    0x001A3518 — 2.857 bytes ANTES. Na historia real aquele patch rodou
    mais cedo, com menos coisa ocupada.

    **Conclusao: a corrente so compoe na ordem historica exata**, patches
    mortos inclusive. Uma receita limpa e impossivel com as ferramentas
    como estao.

O CAMINHO PARA A 3.0

    O conserto nao e reordenar: e tirar dos patches a decisao de onde
    morar. Cada ferramenta que aloca deve receber o endereco como
    PARAMETRO (`--em 0x1A5300`), e a receita declara o mapa da area
    livre. Ai:

      - o endereco deixa de depender da historia;
      - a receita passa a ser reordenavel e podavel;
      - um patch corrigido nao move os outros.

    E trabalho delimitado: ~12 ferramentas alocam assim.

O QUE ELE **NAO** FAZ

    Nao reproduz a historia. A receita declara o que queremos HOJE, na
    ordem certa — patches superados ficam de fora de proposito.

    Por isso `--verificar` existe: comparando a saida com uma imagem
    conhecida (a 2.2, que boota), a diferenca mostra **o que a corrente
    tem e a receita nao** — que e exatamente a pergunta do mantenedor
    ("acho que vem com muita coisa errada").

USO
    python3 tools/build.py --saida firmware/WORKING/GN438_build.bin
    python3 tools/build.py --so-lista
    python3 tools/build.py --verificar firmware/WORKING/GN438_openpod_v073_carimbado.bin

SEGURANCA
    - le o ORIGINAL e confere o sha256 antes de comecar;
    - cada passo roda em arquivo proprio dentro de um diretorio temporario;
    - para no primeiro erro e mostra a saida da ferramenta que falhou;
    - nao grava nada no aparelho e nao gera kit.
"""

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = os.path.join(RAIZ, "firmware/ORIGINAL/GN438_original.bin")
SHA_ORIGINAL = ("b7cd5eb952be5328cbaa926099cf8d88168633c1"
                "fab6d0f31f3a283c9e24b36f")

# ---------------------------------------------------------------------------
# O MAPA DA AREA LIVRE
#
# Cada ferramenta que aloca recebe `--em` e passa a ter lugar FIXO. Sem
# isto o endereco emergia da ordem (ver o cabecalho), e a corrente so
# compunha na sequencia historica exata.
#
# O pipeline CONFERE, depois de cada passo, que a ferramenta escreveu
# apenas dentro de lotes DECLARADOS. Escrever no proprio lote e obvio;
# escrever no lote de um passo anterior tambem e legitimo (o
# `aplica_textos`, por exemplo, atualiza os ponteiros da tabela que o
# `relocate_lang_table` moveu). O que o pipeline recusa e escrever em
# area livre NAO declarada — que e exatamente o alocador incremental
# voltando pela porta dos fundos.
#
# Abaixo de 0x001A5000 ficam os lotes alocados; de 0x001A5000 em diante
# ficam as rotinas de endereco FIXO (titulos, Saturno, Extras), que ja
# eram bem-comportadas e nao mudam.
# ---------------------------------------------------------------------------
MAPA = {
    # 0x001A3038..0x001A3040 e a string "OpenPod" do patch_status_bar,
    # em endereco FIXO na ferramenta. Os lotes comecam depois dela.
    "patch_texto_branco_fixo.py": (0x001A6000, 0x0010),
    "patch_barra_selecao.py":  (0x001A3040, 0x0100),
    "patch_scrollbar3.py":     (0x001A3140, 0x0100),
    "patch_update_sd.py":      (0x001A3240, 0x0100),
    "patch_menu_text.py":      (0x001A3340, 0x00D8),
    # 0x001A3518 NAO e escolha nossa: o `patch_cor_texto_lista` fixou
    # esse endereco no proprio codigo e recusa se a rotina nao estiver
    # exatamente ali. Divida tecnica herdada.
    "patch_cor_selecao.py":    (0x001A3518, 0x00E8),
    "relocate_lang_table.py":  (0x001A3600, 0x0700),
    "aplica_textos.py":        (0x001A3D00, 0x1200),
    # 0x001A4F00..0x001A5000 e do CARIMBO DE VERSAO (`patch_versao.py`,
    # aplicado pelo `make_install_kit`, regra R7). Ele nao roda nesta
    # receita, mas o slot fica reservado aqui para nao ser dado a
    # ninguem: a constante vive em make_install_kit.EM_VERSAO.
    #
    # 0x001A5000..0x001A6000 e reservado: o `patch_titulos` exige esses
    # 4 KiB virgens. O que nao cabe antes vai para depois dele.
    "make_extras_menu.py":     (0x001A6000, 0x0400),
}
AREA_INI, AREA_FIM = 0x001A3040, 0x001A8000


# ---------------------------------------------------------------------------
# A RECEITA. Uma linha por passo: (ferramenta, argumentos extras, por que).
# A ordem importa: quem cria area livre vem antes de quem a usa; a tabela
# de tema vem antes dos ganchos que a leem.
# ---------------------------------------------------------------------------
INTERFACE = [
    # --- estrutura da home e dos menus
    ("patch_logo.py",          [], "a logo do OpenPod na tela de abertura"),
    # ANDA JUNTO com a logo, nao e opcional: a logo tem fundo preto e a
    # tela de abertura tem fundo claro. Sem isto fica um retangulo escuro
    # no meio de uma tela branca — relatado no aparelho em 14/09, ao
    # gravar a Core 1.0.
    ("patch_fundo_abertura.py", [], "o fundo da abertura fica preto (V008)"),
    ("make_list_home.py",      [], "home deixa de ser grade 3x3 e vira lista"),
    ("patch_home_keys.py",     [], "ramos de navegacao da home: pula 6 -> pula 8"),
    # A FAIXA SUPERIOR vem cedo, e nao e opcional.
    #
    # Eu havia excluido estes dois como "superados pelo Saturno". Erro:
    # o Saturno substitui a APARENCIA da faixa, mas quem grava a string
    # "OpenPod" em 0x001A3038 e o `patch_status_bar` — e ela e usada no
    # BOOT e no titulo da home. A 3.0 saiu sem as duas coisas.
    #
    # Medido por `tools/afere_fora.py`, nao suposto.
    ("patch_status_bar.py",    [], "faixa superior + a string 'OpenPod' em 0x1A3038"),
    ("fix_status_bar.py",      [], "corrige os dois defeitos do V016 na faixa"),

    # MEDIDAS, nao supostas: `tools/afere_fora.py` mostrou que estas tres
    # estao APLICADAS na 2.4 (recusam la, porque ja la estao) e faltavam
    # aqui. Eu as tinha classificado como "superadas" ou "experimento"
    # lendo a descricao. A 3.0 saiu com os chevrons grandes de fabrica
    # por causa disso.
    ("patch_barra_selecao.py", [], "a selecao da home vira BARRA"),
    ("patch_scrollbar3.py",    [], "esconde a barra de rolagem no conteiner"),

    # A tabela e realocada ANTES do submenu: o `make_extras_menu`
    # acrescenta o id 216 ("Extras"), e se a realocacao vier depois o
    # ponteiro dele fica para tras.
    # `--add Extras` cria o id 216. A tabela do portugues tem 216 ids
    # (0..215) e EMENDA direto na do espanhol — sem realocar, um id 216
    # leria "Español". Por isso o submenu exigiu mover a tabela primeiro.
    ("relocate_lang_table.py", ["--add", "Extras"],
     "tabela do portugues para a area livre, + id 216 'Extras'"),
    ("make_extras_menu.py",    [], "home com 4 itens + submenu Extras com 6"),

    # --- textos
    ("aplica_textos.py",       [], "textos revisados em portugues"),
    # DEPOIS do `aplica_textos`: ele reescreve a tabela inteira a partir
    # da revisao e reverteria o id 3 para 'vídeo' minusculo.
    ("patch_menu_text.py", ["--set", "pt:3=Vídeo"],
     "'Vídeo' com maiuscula (o original e minusculo)"),
    ("patch_update_sd.py",     [], "item 'Atualizar por SD' em Configurar"),

    # O titulo vem ANTES do chrome: ele exige 4 KiB virgens a partir de
    # 0x001A5000, e o Saturno ocupa parte dessa faixa. Historicamente foi
    # a 1.5, antes do 1.9/2.0 — a ordem nao e preferencia, e requisito.
    ("patch_titulos.py",       [], "titulo na faixa de 37 telas"),

    # --- chrome e Saturno
    #
    # DESCOBERTA DO PIPELINE: o `patch_saturno` NAO cria as rotinas do
    # zero — ele reescreve os thunks que o `patch_chrome_padrao` (2.0)
    # deixou em 0x1A5300..0x1A5344. Eu tinha marcado o chrome_padrao como
    # "superado pelo Saturno"; e o contrario: ele e PRE-REQUISITO.
    # Numa 3.0 limpa os dois deveriam virar um passo so.
    ("patch_cor_selecao.py",   [], "1.9: cor de selecao das listas (rotina em 0x1A3518)"),
    ("patch_cor_texto_lista.py", [], "1.9: cria a rotina de cor da linha em 0x1A5200"),
    ("patch_chrome_padrao.py", [], "2.0: cria as rotinas de chrome na area livre"),
    ("patch_saturno.py",       [], "S1+S2: poe uma tabela de tema por tras delas"),
    ("patch_saturno_s3.py",    [], "S3: a carcaca pinta tudo explicitamente"),
    ("patch_saturno_s4.py",    [], "S4: a home entra na carcaca"),
    ("patch_saturno_s5.py",    [], "S5: a folha de imagem sai do caminho"),
    ("patch_saturno_s6.py",    [], "S6: fecha os pontos deixados pelo S3"),
    ("patch_saturno_s7.py",    [], "S7: icones das listas viram campo da tabela"),
    ("patch_saturno_s8.py",    [], "S8: o recuo do texto vem da tabela"),
    ("patch_saturno_s9.py",    [], "S9: as 14 telas com faixa e sem lista"),
    ("patch_saturno_s10.py",   [], "S10: a cor do texto vem da tabela"),
    ("patch_saturno_s11.py",   [], "S11: a altura da linha vem da tabela"),
    ("patch_saturno_s12.py",   [], "S12: fundo lido do campo de fundo"),

    # --- titulo e roteamento
]


# ---------------------------------------------------------------------------
# OPENPOD CORE 1.0 — deliberadamente pequena.
#
# Esta receita produz a **OpenPod Core 1.0.1**, declarada STABLE pelo
# mantenedor em 2026-09-14 depois de rodar no aparelho: logo sobre preto,
# tela Informacoes certa, e instalada PELO CARTAO — o que confirmou o
# caminho de atualizacao inteiro.
#
#     imagem      7312fbd066b1a31e508a51c9c44c5e203e17e6d1e1b9719c0df7e37e7b250d34
#     carimbada   36125f5665b8613e0d96215e2ffcf36170d847068d0c72e572167fe506400c1f
#
# E a BASELINE da linha Core: versoes novas podem partir dela.
#
# Base decidida pelo mantenedor em 2026-09-14: o firmware ORIGINAL.
#
# O objetivo desta versao nao e parecer melhor: e ser uma fundacao em que
# um defeito tenha causa obvia. Por isso NAO entram home em lista, faixa
# superior, titulos, Saturno, Extras, cor de selecao — tudo isso continua
# na receita `interface`, inteiro, e volta na Core 2.0.
#
# Consequencia aceita: a Core 1.0 tem a home em grade 3x3 de fabrica.
# ---------------------------------------------------------------------------
CORE_1_0 = [
    ("patch_logo.py",          [], "a logo do OpenPod na tela de abertura"),
    ("patch_fundo_abertura.py", [], "o fundo da abertura fica preto (V008)"),
    # A tabela do portugues sai para a area livre ANTES de ser reescrita:
    # a de fabrica emenda direto na do espanhol e nao tem folga.
    ("relocate_lang_table.py", [], "tabela do portugues para a area livre"),
    ("aplica_textos.py",       [], "textos revisados em portugues do Brasil"),
    ("patch_menu_text.py", ["--set", "pt:3=Vídeo"],
     "'Vídeo' com maiuscula (o original e minusculo)"),
    ("patch_update_sd.py",     [], "item 'Atualizar por SD' em Configurar"),
]


# ---------------------------------------------------------------------------
# CORE 2.0 — a carcaca da interface.
#
# E a receita `interface` MENOS o submenu Extras. Motivo medido, nao
# preferencia: o `make_extras_menu` esconde 6 itens da home atras da
# pagina 0x53, e quem faz o Enter dela rotear e o `patch_extras` — que
# esta FORA porque nao funcionou no aparelho. Com um e sem o outro, os
# seis itens ficariam so de enfeite, e a pagina 0x53 e uma lista MORTA de
# 3 itens no firmware de fabrica.
#
# Sem o submenu, a home vira lista com TODOS os itens: nada se esconde,
# nada deixa de abrir. Menos parecido com o nano, e honesto.
# ---------------------------------------------------------------------------
CORE_2_0 = [p for p in INTERFACE
            if p[0] not in ("make_extras_menu.py",)]
# O `--add Extras` do `relocate_lang_table` FICA. Tentei tirar junto, e o
# `patch_titulos` recusou: "id 216 (pagina 0x53) aponta fora da imagem".
# Ele usa esse id como TITULO da pagina 0x53. Medido, nao suposto.

# ---------------------------------------------------------------------------
# CORE 2.1 — Marte M1. A carcaca da 2.0 mais doze bytes de cor.
#
# Sai separada da 2.0 de proposito: juntas, um defeito na tela nao diria
# se foi a carcaca ou a paleta. Separada, e reversivel em 12 bytes e
# responde uma pergunta so — o tema claro do nano agrada neste aparelho?
# ---------------------------------------------------------------------------
CORE_2_1 = CORE_2_0 + [
    # Entra JUNTO com a paleta, e nao numa 2.2, por um motivo: sem ele a
    # home mostra DUAS selecoes — o item pintado na criacao fica com cor
    # de letra, e a barra anda sem limpa-lo. Com o tema claro esse item
    # ficaria azul sobre branco, contaminando justamente a pergunta que a
    # 2.1 existe para fazer. A 2.1 nao chegou a ser gravada.
    ("fix_barra_selecao_criacao.py", [], "a segunda selecao da home, 4 B"),
    ("patch_marte_paleta.py", [], "Marte M1: o tema claro do iPod nano"),
    # Descoberto na tela, com a 2.1 gravada: os rotulos das listas sumiam.
    # Os dois criadores compartilhados pintavam fundo com PRETO FIXO, e a
    # tabela tinha o campo `cor_tela` praticamente morto. Enquanto o tema
    # era escuro os dois davam no mesmo; o Marte separou.
    ("patch_fundo_lista.py", [], "o fundo do conteiner e da linha vem da tabela"),
]

# ---------------------------------------------------------------------------
# CORE 2.2 — chegar ao alvo: marte/mockups/marte_completo.png
#
# A lista do nano e branca e LIMPA: sem traco entre os itens. O traco de
# 1 px EMBAIXO da faixa fica — sao objetos diferentes, e a ferramenta
# confere os dois.
# ---------------------------------------------------------------------------
CORE_2_2_MARTE = CORE_2_1 + [
    ("patch_sem_separador.py", [], "sem traco entre os itens, como o nano"),
    # O diagnostico de cores mostrou: ha texto com BRANCO FIXO no codigo,
    # que some no tema claro. Censo: 8 pontos, todos com r1. Nao e o
    # relogio — esse vem de um dos 24 de origem nao identificada.
    ("patch_texto_branco_fixo.py", [], "8 pontos de branco fixo passam a ler a tabela"),
]

# ---------------------------------------------------------------------------
# CORE 2.2 — O CAMINHO PADRAO.
#
# Decisao do mantenedor em 2026-09-14, depois de ver a segunda selecao na
# tela: "nao quero herdar nada da criacao anterior que esta bugado. A
# base e o Marte, vamos usar o padrao e nos adaptar."
#
# Entao esta receita NAO leva nenhum remendo da home. Ficam de fora, e
# nao por acaso — sao exatamente os que existem para consertar o desenho
# PROPRIO da home, que e a causa da classe de defeito:
#
#     make_list_home              a home vira lista, por tabela de coords
#     patch_home_keys             ramos de navegacao da home
#     patch_barra_selecao         a selecao da home vira barra
#     fix_barra_selecao_criacao   o ponto gemeo que ficou para tras
#     patch_status_bar/fix_       a faixa pintada na folha da home
#     patch_saturno_s4/s5         a home entra na carcaca; a folha sai
#
# O que fica: o caminho que o firmware JA usa em 36 telas — CRIA_FAIXA,
# CRIA_CONTEINER, CRIA_LINHA — mais a tabela de tema e a paleta do nano.
#
# Consequencia aceita: a HOME continua a grade 3x3 de fabrica, escura,
# enquanto as 36 telas ficam claras. Feio e temporario. O passo seguinte
# e levar a home para o MESMO caminho — o molde esta no proprio firmware,
# em `page_home_menu_event_cb` (pagina 0x53), que monta a lista dela com
# os tres helpers.
#
# MEDIDO: dos 16 passos do caminho padrao, 14 aplicam sobre a Core 1.0.1
# sem tocar na home. As duas recusas foram
#   patch_titulos      exige o id 216 -> resolvido com `--add Extras`
#   patch_saturno_s5   mexe na folha da home -> e home, sai daqui
# ---------------------------------------------------------------------------
CORE_2_2 = [
    ("patch_logo.py",           [], "a logo do OpenPod na tela de abertura"),
    ("patch_fundo_abertura.py", [], "o fundo da abertura fica preto (V008)"),
    ("relocate_lang_table.py",  ["--add", "Extras"],
     "tabela do portugues para a area livre, + id 216 (titulo da 0x53)"),
    ("aplica_textos.py",        [], "textos revisados em portugues do Brasil"),
    ("patch_menu_text.py", ["--set", "pt:3=Vídeo"], "'Vídeo' com maiuscula"),
    ("patch_update_sd.py",      [], "item 'Atualizar por SD' em Configurar"),
    # --- daqui para baixo, o CAMINHO PADRAO
    ("patch_scrollbar3.py",     [], "esconde a barra de rolagem no conteiner"),
    ("patch_titulos.py",        [], "titulo na faixa de 37 telas"),
    ("patch_cor_selecao.py",    [], "cor de selecao das listas"),
    ("patch_cor_texto_lista.py",[], "cor do texto das listas"),
    ("patch_chrome_padrao.py",  [], "as rotinas de chrome na area livre"),
    ("patch_saturno.py",        [], "S1+S2: a tabela de tema por tras delas"),
    ("patch_saturno_s3.py",     [], "S3: a carcaca pinta tudo explicitamente"),
    ("patch_saturno_s6.py",     [], "S6: fecha os pontos deixados pelo S3"),
    ("patch_saturno_s7.py",     [], "S7: icones das listas viram campo da tabela"),
    ("patch_saturno_s8.py",     [], "S8: o recuo do texto vem da tabela"),
    ("patch_saturno_s9.py",     [], "S9: as 14 telas com faixa e sem lista"),
    ("patch_saturno_s10.py",    [], "S10: a cor do texto vem da tabela"),
    ("patch_saturno_s11.py",    [], "S11: a altura da linha vem da tabela"),
    ("patch_saturno_s12.py",    [], "S12: fundo lido do campo de fundo"),
    ("patch_marte_paleta.py",   [], "Marte M1: o tema claro do iPod nano"),
]

# ---------------------------------------------------------------------------
# CARCACA ESCURA — 2026-09-14.
#
# Decisao do mantenedor depois do teste em hardware: o tema CLARO nao
# serve NESTE PAINEL (docs/MARTE_ALVO.md §0-bis — as faixas sao do LCD,
# isoladas por eliminacao). Mas a CARCACA e independente da paleta.
#
# Esta receita e a `marte` MENOS os dez bytes de cor. Fica tudo o que foi
# validado no aparelho e nao depende de claro/escuro:
#
#     fix_barra_selecao_criacao   a "segunda selecao" — defeito real
#     patch_fundo_lista           fundo da linha e do conteiner pela tabela
#     patch_sem_separador         sem traco entre itens, como o nano
#     patch_texto_branco_fixo     8 pontos de branco fixo lendo a tabela
#
# A tabela nasce com altura_linha = 16 px, que e a medida do nano — um
# byte governa 38 pontos em 28 telas (S11). Era isso que o mantenedor
# pediu: definir a altura em UM lugar, sem retrabalho tela a tela.
# ---------------------------------------------------------------------------
CARCACA = [p for p in CORE_2_2_MARTE if p[0] != "patch_marte_paleta.py"]

RECEITAS = {
    "interface": INTERFACE,
    "core1.0":   CORE_1_0,
    "core2.0":   CORE_2_0,
    "core2.1":   CORE_2_1,
    "core2.2":   CORE_2_2,
    "marte":     CORE_2_2_MARTE,
    "carcaca":   CARCACA,
}

# Patches deliberadamente FORA da receita, e por que.
FORA = [
    # O CHEVRON FICA FORA — o mantenedor lembrou, e a medicao confirmou.
    #
    # Eu o inclui porque `afere_fora.py` mostrou "RECUSA" na 2.4 e eu li
    # isso como "ja aplicada". **Recusa tambem pode ser incompativel**, e
    # era esse o caso: ele aborta na 2.4 porque calcula faixa livre de
    # 0 px. Na 2.4 os chevrons estao APAGADOS (indice de fundo 0x01);
    # incluir esta ferramenta os REDESENHAVA, com indice 0x00.
    #
    # Falha do meu instrumento de medicao, nao da ferramenta.
    ("patch_chevron.py",          "os chevrons ficam APAGADOS, nao menores"),
    # --- O EXTRAS FICA DE FORA, e isto e decisao, nao esquecimento.
    #
    # `patch_extras` + `_fix` + `_fix2` sao TRES patches empilhados no
    # mesmo ponto, e mesmo assim os seis itens nao abrem no aparelho. A
    # sonda (`patch_sonda.py`) tentou medir o indice que chega e a
    # leitura saiu ambigua — o titulo so e atualizado quando o rotulo e
    # recriado, e ele nem sempre e.
    #
    # Sem o patch, o Extras volta ao comportamento de fabrica: os tres
    # primeiros itens abrem (Despertador, Imagem, Dicionario) e os outros
    # tres nao fazem nada. E pior em funcao, melhor em honestidade: nada
    # na receita finge funcionar.
    ("patch_extras.py",           "Extras nao funciona; ver docs/ESTADO_ATUAL.md"),
    ("patch_extras_fix.py",       "idem"),
    ("patch_extras_fix2.py",      "idem — msg[0x0a]=2 nao mudou o sintoma"),
    # --- diagnostico e teoria derrubada
    ("patch_sonda.py",            "instrumento de diagnostico, nao produto"),
    ("patch_fundo_display.py",    "hipotese DERRUBADA pelo aparelho: o fundo "
                                  "branco do display nao e a causa da faixa"),
    ("patch_titulo_orfao.py",     "INCORPORADO ao patch_titulos"),
    ("patch_scrollbar.py",        "superado pelo scrollbar3"),
    ("patch_scrollbar2.py",       "superado pelo scrollbar3"),
    ("patch_bar_height.py",       "superado pelo Saturno (altura_faixa)"),
    # patch_status_bar / fix_status_bar SAIRAM desta lista em 2026-09-14:
    # estavam nos DOIS lugares ao mesmo tempo (RECEITA e FORA). A receita
    # e que esta certa — `afere_fora.py` mostrou que o `patch_status_bar`
    # grava a string "OpenPod" em 0x1A3038, usada no BOOT e no titulo da
    # home, e a 3.0 saiu sem as duas coisas por causa desta linha.
    ("patch_raio_selecao.py",     "tentativa falha; ver fix_raio_selecao"),
    ("fix_raio_selecao.py",       "superado pelo Saturno (campo raio)"),
    ("patch_respiro_lista.py",    "superado pelo Saturno (inicio_lista)"),
    ("patch_lista_sistema.py",    "superado pelo Saturno"),
    ("patch_home_padrao.py",      "superado pelo S4"),
    ("patch_navegacao.py",        "REVERTIDO na 1.8 — o padrao de fabrica vale"),
    ("patch_versao.py",           "aplicado pelo make_install_kit (regra R7)"),
    ("patch_home_icon.py",        "experimento de icone unico"),
    ("patch_fonte_negrito.py",    "experimento"),
    ("patch_largura_barra.py",    "experimento"),
    ("patch_battery_y.py",        "experimento"),
    ("patch_selecao_criacao.py",  "experimento"),
    ("make_v030.py",              "rede de seguranca, aplicada a parte"),
]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def valida(img):
    """validate_firmware.py, com a falha de CRC da R1 reclassificada.

    A FIRM tem um campo de CRC na tabela de particoes, e a regra R1 manda
    NUNCA regravar esse setor — entao o campo fica desatualizado de
    proposito, e o validador acusa. Confirmado no aparelho em 13/09: ele
    boota com a tabela de fabrica sobre uma FIRM diferente.

    Um validador que grita FALHA no caso normal ensina a ignorar falhas.
    Aqui essa linha vira ESPERADO, e qualquer OUTRA falha e falha mesmo.
    """
    print("\n  VALIDACAO ESTRUTURAL")
    r = subprocess.run([sys.executable,
                        os.path.join(RAIZ, "tools/validate_firmware.py"), img],
                       capture_output=True, text=True, cwd=RAIZ)
    reais = []
    for ln in r.stdout.splitlines():
        if "[FALHA]" not in ln:
            continue
        if "particao FIRM: CRC" in ln:
            print("    ESPERADO  CRC da FIRM desatualizado (regra R1)")
        else:
            reais.append(ln.strip())
    ok = [ln for ln in r.stdout.splitlines() if "RESULTADO" in ln]
    if ok:
        print("    " + ok[0].strip())
    if reais:
        print("\n  FALHAS REAIS:")
        for ln in reais:
            print("    " + ln)
        return False
    print("    nenhuma falha alem da esperada   OK")
    return True


def diferenca(img, base, receita):
    """binary diff contra a base, com as guardas do projeto.

    Nao e enfeite: §12 do prompt-mestre exige que toda versao seja
    comparada com sua base, e que alteracao inesperada PARE o processo.
    As tres guardas abaixo sao as que ja custaram aparelho ou versao.
    """
    print(f"\n  BINARY DIFF contra {os.path.basename(base)}")
    A = open(os.path.join(RAIZ, base), "rb").read()
    B = open(img, "rb").read()
    if len(A) != len(B):
        print(f"    PARE: tamanhos diferentes, {len(A)} e {len(B)}")
        return False
    dif = [i for i in range(len(A)) if A[i] != B[i]]
    if not dif:
        print("    nenhuma diferenca — a receita nao mudou nada?")
        return True
    secs = {}
    for i in dif:
        secs[i // 0x1000 * 0x1000] = secs.get(i // 0x1000 * 0x1000, 0) + 1
    print(f"    {len(dif)} bytes em {len(secs)} setores, "
          f"menor offset 0x{min(dif):06X}")
    for s in sorted(secs):
        print(f"      0x{s:06X}  {secs[s]:6d} B")

    guardas = [
        ("nada abaixo de 0x00D000 (bootloader)", min(dif) >= 0x00D000),
        ("setor 0x00D000 intocado (regra R1)",
         not any(0xD000 <= i < 0xE000 for i in dif)),
        ("PSMP intocada (0x1FC000+)",
         not any(i >= 0x1FC000 for i in dif)),
    ]
    print()
    falhou = False
    for texto, passou in guardas:
        print(f"    {'OK  ' if passou else 'PARE'}  {texto}")
        falhou |= not passou
    if falhou:
        print("\n    PARE: a receita tocou onde nao devia. Investigue "
              "antes de seguir.")
        return False
    return True


def main():
    ap = argparse.ArgumentParser(description="constroi o OpenPod do ORIGINAL")
    ap.add_argument("--saida", default="firmware/WORKING/GN438_build.bin")
    ap.add_argument("--so-lista", action="store_true",
                    help="mostra a receita e sai")
    ap.add_argument("--verificar", metavar="IMAGEM",
                    help="compara a saida com uma imagem de referencia")
    ap.add_argument("--ate", metavar="FERRAMENTA",
                    help="para depois deste passo")
    ap.add_argument("--base", metavar="IMAGEM",
                    help="imagem de referencia do binary diff "
                         "(padrao: o ORIGINAL)")
    ap.add_argument("--sem-validar", action="store_true",
                    help="nao roda validacao nem diff ao final")
    ap.add_argument("--receita", default="interface",
                    choices=sorted(RECEITAS),
                    help="qual receita construir (padrao: interface)")
    a = ap.parse_args()

    RECEITA = RECEITAS[a.receita]

    print()
    print(f"  RECEITA DO OPENPOD — {a.receita}")
    print()
    for i, (t, extra, por) in enumerate(RECEITA, 1):
        print(f"   {i:2d}. {t:26s} {por}")
    print(f"\n  fora da receita de proposito: {len(FORA)} ferramentas")
    if a.so_lista:
        for t, por in FORA:
            print(f"       {t:26s} {por}")
        return 0

    if sha(ORIGINAL) != SHA_ORIGINAL:
        sys.exit("PARE: o sha256 do ORIGINAL nao confere")
    print(f"\n  ORIGINAL conferido ({SHA_ORIGINAL[:16]}...)")

    tmp = tempfile.mkdtemp(prefix="openpod_build_")
    atual = os.path.join(tmp, "000_original.bin")
    shutil.copy(ORIGINAL, atual)
    print(f"  area de trabalho: {tmp}\n")

    for i, (t, extra, por) in enumerate(RECEITA, 1):
        prox = os.path.join(tmp, f"{i:03d}_{t.replace('.py','')}.bin")
        cam = os.path.join(RAIZ, "tools", t)
        if not os.path.exists(cam):
            print(f"   {i:2d}. {t:26s} FERRAMENTA NAO EXISTE")
            return 1
        args = list(extra)
        if t in MAPA:
            args += ["--em", hex(MAPA[t][0])]
        r = subprocess.run([sys.executable, cam, "--in", atual,
                            "--out", prox] + args,
                           capture_output=True, text=True, cwd=RAIZ)
        if r.returncode or not os.path.exists(prox):
            print(f"   {i:2d}. {t:26s} FALHOU")
            print("       ---- saida da ferramenta ----")
            for ln in (r.stdout + r.stderr).splitlines()[-25:]:
                print("       " + ln)
            print(f"\n  parou no passo {i}. Imagem ate aqui: {atual}")
            return 1
        # confere que a ferramenta respeitou o proprio lote
        if t in MAPA:
            A, B = open(atual, "rb").read(), open(prox, "rb").read()
            declarado = set()
            for bb, tt in MAPA.values():
                declarado |= set(range(bb, bb + tt))
            fora = [x for x in range(AREA_INI, AREA_FIM)
                    if A[x] != B[x] and x not in declarado]
            if fora:
                print(f"   {i:2d}. {t:26s} ESCREVEU FORA DO MAPA")
                print(f"       lote declarado: 0x{MAPA[t][0]:06X}"
                      f"..0x{MAPA[t][0]+MAPA[t][1]:06X}")
                print(f"       escreveu tambem em 0x{min(fora):06X}"
                      f"..0x{max(fora):06X}  ({len(fora)} bytes)")
                return 1
        atual = prox
        nota = f"  [0x{MAPA[t][0]:06X}]" if t in MAPA else ""
        print(f"   {i:2d}. {t:26s} ok{nota}")
        if a.ate and t == a.ate:
            break

    dst = os.path.join(RAIZ, a.saida)
    shutil.copy(atual, dst)
    print(f"\n  gravado: {a.saida}")
    print(f"  sha256 : {sha(dst)}")

    if not a.sem_validar:
        if not valida(dst):
            return 1
        if not diferenca(dst, a.base or ORIGINAL, RECEITA):
            return 1

    if a.verificar:
        ref = os.path.join(RAIZ, a.verificar)
        A, B = open(dst, "rb").read(), open(ref, "rb").read()
        dif = [i for i in range(min(len(A), len(B))) if A[i] != B[i]]
        secs = sorted({i // 0x1000 * 0x1000 for i in dif})
        print(f"\n  COMPARACAO com {os.path.basename(ref)}")
        print(f"    bytes diferentes: {len(dif)}   setores: {len(secs)}")
        for s in secs:
            n = sum(1 for i in dif if s <= i < s + 0x1000)
            print(f"      0x{s:06X}  {n} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
