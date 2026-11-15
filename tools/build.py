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
    "patch_nome_faixa.py":     (0x001A3040, 0x0010),
    "patch_extras.py":         (0x001A3050, 0x0020),
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
    # 0x001A5000..0x001A6000 eram do `patch_titulos` (ferramenta da linha
    # Core, removida em 2026-09-14). A ficha 005 (RC5) tomou o lote para os
    # textos em portugues: 4 KiB virgens, logo depois do carimbo e antes
    # das rotinas de endereco fixo de baixo — e nao cruza nenhum lote acima.
    "fab_textos.py":           (0x001A5000, 0x1000),
    "make_extras_menu.py":     (0x001A6000, 0x0400),
    "patch_faixa_degrade.py": (0x001A6000, 0x0040),
    # Ficha 002 (RC3). A rotina do degradê e a string "OpenPod" recebem
    # endereco FIXO: a primeira e chamada por um `bl` dentro da CRIA_FAIXA e
    # a segunda por um ponteiro dentro do rotulo, entao os dois enderecos
    # estao gravados no proprio codigo da fabrica. 0x1A7000 fica logo depois
    # do ultimo lote acima, e o texto vem colado na rotina (16 bytes) porque
    # sao gravados no mesmo setor do cabo.
    "fab_barra_degrade.py":  (0x001A7000, 0x0040),
    "fab_barra_titulo.py":   (0x001A7040, 0x0010),
    # Ficha 006 (RC6). O lote e das ROTINAS da moldura (DESEL/SEL/CRIA),
    # em endereco FIXO: os oito ganchos da home apontam para elas, e os
    # enderecos ficam gravados no proprio codigo. O lote 0x001A6400 fica
    # logo depois do `make_extras_menu` (que termina em 0x001A6400) e
    # antes do degradê (0x001A7000) — nao cruza nenhum lote acima.
    "fab_home_moldura.py":   (0x001A6400, 0x0080),
    # Ficha 007 (RC7). O lote e das ROTINAS da capa do album (CRIA, TITULO
    # e APAGA), em endereco FIXO: os tres ganchos da Tocando Agora apontam
    # para elas e os enderecos ficam gravados no proprio codigo. O lote
    # 0x001A8000 fica logo depois do `fab_home_moldura` (que termina em
    # 0x001A6480) e nao cruza nenhum lote acima.
    "fab_capa_album.py":      (0x001A8000, 0x3000),
    # Ficha 008 (RC7 trava ao tocar). A ferramenta das BISSECOES
    # (`fab_diag_trava.py`) NAO entra no MAPA de proposito: ela nao aloca
    # nada, so patcha 4/2/2 bytes DENTRO do lote que a RC7 ja montou, e o
    # `tests/test_rc7.py` (protegido, C2) recusa qualquer lote do MAPA que
    # cruze o lote da RC7. O endereco do lote viaja na receita (--em), e a
    # ferramenta recusa se nao for 0x001A8000.
}
AREA_INI, AREA_FIM = 0x001A3040, 0x001AB000


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

    # --- Marte M-a, 2026-09-14. O PRIMEIRO passo rumo ao alvo visual.
    #
    # 1 byte DENTRO de CRIA_LINHA (0x00D21764), a rotina compartilhada
    # que 39 telas usam. Nao aloca, nao usa area livre, nao cria objeto.
    #
    # Entra no FIM da receita de proposito: e independente de tudo o que
    # vem antes, entao pode sair daqui sem quebrar nada. Foi essa
    # propriedade que faltou na linha 2.x.
    ("patch_sem_separador.py", [], "M-a: sem traco entre os itens, como o nano"),

    # Marte M-f. Tambem independente: 2 bytes na TABELA de paletas da
    # LVGL (0x000DF082), nao em codigo. Nao depende do M-a nem de
    # nenhum outro passo, e sair daqui nao quebra nada.
    ("patch_selecao_marte.py", [], "M-f: a selecao ganha o azul do Marte"),

    # Marte M-d. 1 byte no portao do LV_EVENT_DRAW_POST, no tratador de
    # evento compartilhado do lv_obj. Independente dos anteriores.
    ("patch_sem_rolagem.py",   [], "M-d: sem barra de rolagem, como o nano"),

    # Marte M-e. 2 bytes: zera as DUAS strings de glifo DECORATIVO
    # (U+F0C9 e U+F013). Os icones FUNCIONAIS — tique, volume,
    # bluetooth, telefone — ficam. Independente dos anteriores.
    ("patch_sem_icone_linha.py", [], "M-e: sem icone decorativo nas linhas"),

    # Marte M-b, ETAPA 1 — o marco. A home deixa de ser grade 3x3 e vira
    # lista, pela carcaca. Reescreve 0x12EC42..0x12ED8F no lugar; nao
    # aloca, nao usa area livre. Plano em docs/PLANO_HOME.md.
    ("patch_home_lista.py",    [], "M-b: a home vira LISTA, pela carcaca"),

    # Marte M-b, ETAPA 2. DEPENDE do passo anterior: e ele que poe a
    # LINHA no array A (+0x00), e esta etapa pinta o FUNDO dessa linha.
    # Sem ele, os tres `ldr` leriam um array que ainda guarda o quadro
    # de icone. E a UNICA dependencia declarada da receita — as outras
    # dez sao independentes entre si.
    ("patch_home_barra.py",    [], "M-b E2: a selecao da home vira BARRA"),

    # Altura de linha IGUAL em todas as telas: 16 px, a medida do nano.
    # 62 pontos, divisor 7 -> 10. Independente dos anteriores: a home ja
    # calcula a dela a partir de TOPO, e as duas contas convergem em 16.
    ("patch_altura_linha.py",  [], "altura de linha: 16 px em TODAS as telas"),

    # O nome "OpenPod" no lugar do icone de cartao SD, na faixa.
    # Independente: mexe numa rotina propria (0x00D226AC) que so cria
    # aquele rotulo.
    ("patch_nome_faixa.py", ["--em", "0x1A3040"],
     "'OpenPod' no lugar do icone de SD"),

    # A faixa superior deixa de ser preta e vira CINZA, nas 52 telas.
    # 4 bytes dentro da CRIA_FAIXA: o `bl` do getter preto vira um
    # `movw` com a cor. Independente dos anteriores.
    ("patch_faixa_cinza.py",   [], "a faixa vira CINZA, nas 52 telas"),

    # A tela EXTRAS: a pagina 0x52 passa de 3 para 6 itens, e o indice 2
    # da home passa a abri-la. E a classe de mudanca que ja falhou tres
    # vezes aqui — ver o cabecalho da ferramenta e docs/PLANO_EXTRAS.md.
    ("patch_extras.py", ["--em", "0x1A3050"],
     "a tela EXTRAS, 6 itens, e o caminho ate ela"),

    # O roteamento INTERNO do Extras. DEPENDE do passo anterior: e ele
    # que faz a pagina ter 6 itens. Segunda dependencia declarada da
    # receita — as outras 14 sao independentes entre si.
    ("patch_extras_rota.py",  [], "cada item do Extras abre a tela certa"),
]


# ---------------------------------------------------------------------------
# AS RECEITAS 2.x FORAM REMOVIDAS — 2026-09-14, a pedido do mantenedor.
#
# Estavam aqui: `interface`, `core2.0`, `core2.1`, `core2.2`, `marte` e
# `carcaca`. Sairam junto com as 25 ferramentas que so elas usavam.
#
# Motivo, nas palavras dele: "pedi para voce mudar so o menu, voce veio
# com um update 2.4 com alteracao da barra superior que nao pedi".
#
# A causa era ESTRUTURAL, nao desatencao. Aquelas receitas encadeavam ate
# 31 passos em que o `patch_chrome_padrao` — a barra superior — era
# PRE-REQUISITO declarado dos doze passos do Saturno. Mexer em qualquer
# item da lista arrastava a barra junto, porque a receita nao permitia
# separar. O acoplamento foi criado aqui, nao no firmware.
#
# Nada se perdeu: esta tudo no git, no commit anterior a este.
#
# REGRA para quem retomar: volta um passo por vez, testado no aparelho, e
# NUNCA empacotado com algo que nao foi pedido.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# OPENPOD RELOAD ALPHA — reset limpo, 3 features só.
#
# Pedido do mantenedor 2026-09-23: reset no ORIGINAL chamado
# "OpenPod Reload Alpha". Primeira versão entrega:
#   - Update via SD
#   - Fundo preto em todas as telas
#   - Barra principal (Data | OpenPod | Bateria)
#
# Filosofia: mínimo viável, sem carregar acoplamento da linha Core.
# Cada patch é independente (nenhum depende do outro).
# ---------------------------------------------------------------------------
RELOAD_ALPHA = [
    # 1. Update via SD — o aparelho passa a se atualizar pelo cartão
    ("patch_update_sd.py",     [], "Update via SD (Configurar → Atualizar por SD)"),
    # 2. Fundo preto — 3 patches, uma ideia só
    ("patch_fundo_display.py", [], "fundo do display preto (global)"),
    ("patch_fundo_abertura.py",[], "fundo da abertura preto"),
    ("patch_fundo_preto.py",   [], "papel de parede Tocando Agora preto"),
    # 3. Barra principal — Data | OpenPod | Bateria
    #    Data e bateria já existem (relógio + ícone de bateria).
    #    Este patch coloca "OpenPod" no centro, no lugar do ícone de SD.
    ("patch_nome_faixa.py", ["--em", "0x1A3040"], "'OpenPod' na barra (centro)"),
]

RELOAD_ALPHA_0_2 = RELOAD_ALPHA + [
    # 4. Degradê na barra principal (topo RGB 70,75,90 -> base 30,34,40, vertical)
    ("patch_faixa_degrade.py", ["--em", "0x1A6000"], "degradê na barra principal"),
    # 5. Bateria — casca prata + miolo verde (3 patches, uma ideia só)
    ("patch_bateria_casca.py", [], "bateria casca prata"),
    ("patch_bateria_verde.py", [], "bateria nível verde"),
    ("patch_bateria_miolo.py", [], "bateria miolo verde"),
    # 6. Textos corrigidos em pt-BR (relocate + aplica)
    ("relocate_lang_table.py", [], "tabela pt para área livre"),
    ("aplica_textos.py",       ["--em", "0x1A3D00"], "textos revisados pt-BR"),
]

# ---------------------------------------------------------------------------
# OPENPOD RELOAD 1.0 — refeito do ORIGINAL, 2026-09-24.
#
# Pedido do mantenedor: NAO reaproveitar as Alphas (bugadas). A 1.0 sobe
# em degraus, uma imagem por degrau, cada uma testada no aparelho:
#   RC1  update por SD
#   RC2  + logo na abertura + fundo preto
#   RC3  + "OpenPod" na barra + degrade
#   RC4  + icones da tela principal + bateria prata/verde
# ---------------------------------------------------------------------------
RELOAD_1_0_RC1 = [
    ("patch_update_sd.py",     [], "Update via SD (Configurar → Atualizar por SD)"),
]

# ---------------------------------------------------------------------------
# RELOAD 1.0 RC2 — a RC1 mais logo e fundo preto (ficha 001, tipo Risco).
#
# A RC1 (update por SD) ja foi aprovada no aparelho e virou catraca:
# sha256 a427c62e..., em tests/test_rc2.py. Por isso os passos dela vem
# primeiro, na ordem dela, e as ferramentas novas ficam DEPOIS: a RC2 tem
# que conter a RC1 byte a byte.
#
# As duas ferramentas novas nao alocam nada e nao usam area livre: uma
# escreve os 5504 bytes da imagem da abertura (paleta + pixels, cabecalho
# intocado), a outra mexe em 4 bytes de codigo, 2 bytes de imediato e nas
# 256 cores da paleta do papel de parede. Ambas conferem a premissa no
# binario ANTES de escrever e recusam sem criar a saida — logo, nao entram
# no MAPA: nao ha lote alocado para declarar.
#
# A ordem entre elas e a da ficha. As duas recusam rodar duas vezes: a
# premissa de fabrica so existe na primeira passagem.
# ---------------------------------------------------------------------------
RELOAD_1_0_RC2 = RELOAD_1_0_RC1 + [
    ("fab_logo.py",       [], "a logo da abertura passa a ser a do OpenPod"),
    ("fab_fundo_preto.py", [], "fundo preto: abertura, display e papel de parede"),
]

# ---------------------------------------------------------------------------
# RELOAD 1.0 RC3 — a RC2 mais o degradê da barra e o "OpenPod" no centro
# (ficha 002, tipo Risco).
#
# Os passos da RC2 vem primeiro, na ordem dela: a RC2 foi aprovada no
# aparelho em 2026-10-21 e virou catraca (sha fcca5fdc..., em
# tests/test_rc2.py), entao a RC3 tem que conter a RC2 byte a byte.
#
# As duas ferramentas novas escrevem em tres lugares:
#
#     0x121724  o `bl` do gancho, dentro da CRIA_FAIXA (4 bytes)
#     0x1A7000  a rotina do degradê + o texto "OpenPod" (0x50 bytes)
#     0x0CE15C  as 16 linhas da barra da folha da home (2048 bytes)
#     0x1226BA  os quatro pontos do rotulo do cartao (14 bytes)
#
# ORDEM NO KIT: fora do escopo desta receita (o kit e do engenheiro). O
# `gera_versao` monta os setores em ordem crescente de endereco, entao o
# lote 0x1A7000 sai DEPOIS dos setores dos ganchos (0x121000, 0x122000):
# se a gravacao parar no meio, sobram menus com o `bl` apontando para o
# 0xFF do lote. O risco esta na lista de riscos aceitos da ficha e e o
# mesmo da RC1/RC2 — boot, home e recuperacao por cabo nao dependem desses
# setores. Quem confere e o engenheiro, no [4/4] do `gera_versao`.
# ---------------------------------------------------------------------------
RELOAD_1_0_RC3 = RELOAD_1_0_RC2 + [
    ("fab_barra_degrade.py", [],
     "degradê na barra: as 52 telas e a home"),
    ("fab_barra_titulo.py",  [],
     '"OpenPod" no centro da barra da home'),
]

# ---------------------------------------------------------------------------
# RELOAD 1.0 RC4 — a RC3 mais os icones novos da home e a barra centrada
# (ficha 004, tipo Risco).
#
# Os passos da RC3 vem primeiro, na ordem dela: a RC3.1 foi aprovada no
# aparelho em 2026-10-23 e virou catraca (sha 286e8ba8..., em
# tests/test_rc4.py), entao a RC4 tem que conter a RC3 byte a byte.
#
# As duas ferramentas novas nao alocam nada e nao usam area livre:
#
#     0x1217D6  0x1226B6  0x12260E   o y do relogio, do titulo e da
#                                     bateria: 2 -> 0, o centro da barra
#     0x0CDD5C  0x0D315C   a paleta e os pixels da folha da home
#
# ORDEM ENTRE ELAS: a da ficha. Nenhuma das duas depende da outra — a
# primeira mexe em codigo, a segunda em imagem — mas a `fab_icones_home`
# aceita tanto o ORIGINAL quanto a RC3 na premissa, e a
# `fab_barra_centro` aceita SO a RC3. A ordem mantem o porquao legivel.
#
# ORDEM NO KIT: fora do escopo desta receita (o kit e do engenheiro). O
# `gera_versao` monta os setores em ordem crescente de endereco; nesta RC
# os setores novos sao os de codigo (0x121000, 0x122000) e os da folha da
# home (0x0CD000..0x0D3000), e nenhum deles e lido pelo bootloader. O
# risco e o mesmo da RC1/RC2/RC3, e quem confere e o engenheiro, no
# [4/4] do `gera_versao`.
# ---------------------------------------------------------------------------
RELOAD_1_0_RC4 = RELOAD_1_0_RC3 + [
    ("fab_barra_centro.py", [],
     "relogio, 'OpenPod' e bateria no meio da barra"),
    ("fab_icones_home.py",  [],
     "os nove icones novos da home, fundo preto"),
]

# ---------------------------------------------------------------------------
# RELOAD 1.0 RC5 — a RC4 mais os textos em portugues revisados e os nomes
# curtos da home (ficha 005, tipo Risco).
#
# Os passos da RC4 vem primeiro, na ordem dela: a RC4 foi aprovada no aparelho
# em 2026-10-23 e virou catraca (sha 74e8cb31..., em tests/test_rc5.py), entao
# a RC5 tem que conter a RC4 byte a byte.
#
# A ferramenta nova e a UNICA que mexe na tabela de textos, e mexe de um jeito
# que as ferramentas antigas de texto nao faziam: nada e escrito na string de
# fabrica. As strings novas sao gravadas no lote 0x001A5000..0x001A6000 (virgem
# na RC4) e so as entradas da tabela dos ids da lista passam a apontar para
# ca. Isso mantem a RC1 de pe (os ids 40 e 91, "Atualizar por SD", ficam como
# a RC1 os deixou) e nao desfaz nada da RC2 a RC4.
#
# POR QUE NAO DA PARA ESCREVER NO LUGAR: em fabrica tres strings sao
# compartilhadas por dois ids, e em cada par o parceiro esta FORA da lista
# (40/90, 78/155, 9/29). Editar no lugar mudaria um id que a ficha manda
# deixar como esta. O detalhe esta no cabecalho do `fab_textos.py`.
#
# ORDEM NO KIT: fora do escopo desta receita (o kit e do engenheiro). O
# `gera_versao` monta os setores em ordem crescente de endereco; o setor novo
# e o 0x1A5000, o mais alto desta RC, e o nenhum deles e lido pelo bootloader.
# O risco e o mesmo da RC1 a RC4 (interromper entre 0x053000 e 0x1A5000 deixa
# textos lixo), e quem confere e o engenheiro, no [4/4] do `gera_versao`.
# ---------------------------------------------------------------------------
RELOAD_1_0_RC5 = RELOAD_1_0_RC4 + [
    ("fab_textos.py", [],
     "os 180 textos revisados em portugues + os nomes da home"),
]

# ---------------------------------------------------------------------------
# RELOAD 1.0 RC6 — a RC5 mais a home sem nomes, a grade centralizada e a
# moldura branca no icone selecionado (ficha 006, tipo Risco + Pesada).
#
# Os passos da RC5 vem primeiro, na ordem dela: a RC5 foi aprovada no
# aparelho em 2026-10-23 e virou catraca (sha f9f2e059..., em
# tests/test_rc5.py), entao a RC6 tem que conter a RC5 byte a byte.
#
# A ferramenta nova e a UNICA da RC, e ela exige a RC5 EXATA na entrada
# (sha conferido): a RC6 e a RC5 mais ela, e nao ha outro caminho. Ela
# escreve em quatro lugares:
#
#     0x0CE95C..0x0D315C  as linhas 16..159 da folha da home (a grade)
#     0x0486A0..0x0486C4  a tabela de posicoes dos rotulos (as molduras)
#     0x12ED5C..0x12ED60  o tamanho do rotulo (35 x 35 em vez de 40 x 15)
#     0x12E9CA 0x12EA26 0x12EABA 0x12EB12 0x12EB4C 0x12ED30 0x12ED46
#     0x12EDBC              os oito ganchos da selecao (4 bytes cada)
#     0x1A6400..0x1A6480    as rotinas DESEL/SEL/CRIA e a string vazia
#
# ORDEM NO KIT: fora do escopo desta receita (o kit e do engenheiro). O
# `gera_versao` monta os setores em ordem crescente de endereco; o setor
# novo e o 0x1A6000, e nenhum deles e lido pelo bootloader. O risco e o
# mesmo da RC1 a RC5 (interromper entre 0x0D3000 e 0x1A6000 deixa a home
# sem moldura ou com a moldura parada), e quem confere e o engenheiro, no
# [4/4] do `gera_versao`.
# ---------------------------------------------------------------------------
RELOAD_1_0_RC6 = RELOAD_1_0_RC5 + [
    ("fab_home_moldura.py", [],
     "a home sem nomes, a grade centralizada e a moldura no selecionado"),
]

# ---------------------------------------------------------------------------
# RELOAD 1.0 RC7 — a RC6 mais a capa do album na Tocando Agora (ficha 007,
# tipo Risco + Pesada).
#
# Os passos da RC6 vem primeiro, na ordem dela: a RC6 foi aprovada no
# aparelho em 2026-10-30 e virou catraca (sha af3a2b6d..., em
# tests/test_rc7.py), entao a RC7 tem que conter a RC6 byte a byte.
#
# A ferramenta nova e a UNICA da RC, e ela exige a RC6 EXATA na entrada
# (sha conferido): a RC7 e a RC6 mais ela, e nao ha outro caminho. Ela
# escreve em cinco lugares:
#
#     0x131E80..0x131E82  o tamanho da view da Tocando Agora (0x30 -> 0x34)
#     0x131E9E..0x131EA0  o memset da view (0x30 -> 0x34)
#     0x131EB6..0x131EBA  o `bl` do lv_img_create do papel de parede
#     0x13225E..0x132262  o `b.w` do lv_label_set_text das mensagens
#     0x1A8000..0x1AB000  o lote: o quadrado cinza, a tabela de entradas
#                         e as rotinas (CRIA, TITULO e APAGA)
#
# O codigo das rotinas e ASSEMBLY Thumb-2 (tools/capa_album.s, montado
# pelo clang): sem compilador C, para a saida ser reprodutivel (catraca).
#
# ORDEM NO KIT: fora do escopo desta receita (o kit e o engenheiro). O
# `gera_versao` monta os setores em ordem crescente de endereco, entao o
# lote novo (0x1A8000) sai DEPOIS dos setores de codigo (0x131000 e
# 0x132000): se a gravacao parar no meio, sobram menus com o `bl` apontando
# para o 0xFF do lote. O risco esta na lista de riscos aceitos da ficha e e
# o mesmo da RC1-RC6; so a pagina 4 depende dos ganchos.
# ---------------------------------------------------------------------------
RELOAD_1_0_RC7 = RELOAD_1_0_RC6 + [
    ("fab_capa_album.py", [],
     "a capa do album (ID3v2 APIC) na Tocando Agora"),
]

# ---------------------------------------------------------------------------
# RELOAD 1.0 RC7 DIAG A/B/C — as imagens de BISSECAO da ficha 008 (a RC7
# trava ao tocar).
#
# Os passos da RC7 vem primeiro, na ordem dela: a RC7 e a base medida (sha
# 3af97713...), entao cada diag e a RC7 mais UM patch cirurgico no lote
# JA MONTADO — nada e remontado:
#
#     A  4 bytes  a entrada TITULO (0x1AA014) vira b.w para o
#                lv_label_set_text da fabrica (0x00D5ED94)
#     B  2 bytes  o blx da chamada do f_open (0x00D777CD) vira movs r0, #1
#     C  2 bytes  o blx da chamada do jd_prepare (0x00D10B21) vira
#                movs r0, #1
#
# O `--em 0x1a8000` vai na receita (e nao pelo MAPA) porque a ferramenta
# nao aloca nada: ela patcha dentro do lote que a RC7 ja montou, e o
# `tests/test_rc7.py` (protegido) recusa um lote do MAPA que cruze o lote
# da RC7. A ferramenta confere o `--em` de qualquer jeito.
#
# RECETAS DE DIAGNOSTICO: nao entram na catraca (o sha delas e o do
# aparelho, nao o de uma RC aprovada) e nao mexem em teste nenhum.
# ---------------------------------------------------------------------------
RELOAD_1_0_RC7_DIAG_A = RELOAD_1_0_RC7 + [
    ("fab_diag_trava.py", ["--nivel", "a", "--em", "0x1a8000"],
     "diag A: TITULO so set_text"),
]

RELOAD_1_0_RC7_DIAG_B = RELOAD_1_0_RC7 + [
    ("fab_diag_trava.py", ["--nivel", "b", "--em", "0x1a8000"],
     "diag B: A + get_path, sem arquivo"),
]

RELOAD_1_0_RC7_DIAG_C = RELOAD_1_0_RC7 + [
    ("fab_diag_trava.py", ["--nivel", "c", "--em", "0x1a8000"],
     "diag C: B + f_open/f_close"),
]

# ---------------------------------------------------------------------------
# RELOAD 1.0 RC7 DIAG B0 — a ficha 009 (a RC7 REINICIA o aparelho).
#
# O B (ficha 008) ja provou que o defeito esta no que o B liga e o A nao
# liga, mas o B liga DUAS coisas: a rotina TITULO inteira e o `get_path`.
# O B0 separa as duas: a rotina TITULO fica LIGADA (o set_text, a leitura
# da view/ext, a comparacao do caminho e o quadrado cinza) e o `get_path` e
# CORTADO — a chamada vira `movs r0, #0`, ou seja, o get_path "falha" e o
# TITULO cai no caminho que ja existe: caminho guardado vazio e cinza.
#
#     B0  2 bytes  o `blx` da chamada ao get_path (0x00CFEFC5) vira
#                  `movs r0, #0`
#
# Nada e remontado: e a RC7 com 2 bytes trocados dentro do lote que a RC7
# ja montou (o par `movw/movt` + o `blx` da chamada ao get_path).
# ---------------------------------------------------------------------------
RELOAD_1_0_RC7_DIAG_B0 = RELOAD_1_0_RC7 + [
    ("fab_diag_trava.py", ["--nivel", "b0", "--em", "0x1a8000"],
     "diag B0: TITULO ligado, get_path cortado (cinza)"),
]

# ---------------------------------------------------------------------------
# RELOAD 1.0 RC7 DIAG B1 — a ficha 010 (o bug do ring da fabrica).
#
# O B (ficha 008) e o B0 (ficha 009) mediram a ROTINA do TITULO e a
# CHAMADA do get_path na ViewTask. Nenhum dos dois mediu o BUG DA FABRICA
# no envio ao ring: quando o ring da view esta CHEIO, o caminho de erro
# salta o give do mutex e devolve 0 com o mutex `0x81BBCC` PRESO.
#
# O B1 e o Diag B (o nivel B, que e o que REINICIA o aparelho) mais 2 bytes
# no codigo da FABRICA: o `b` de `0x00CF843A` (arquivo `0x00F843A`,
# `fa e7` = `b 0x00CF8432`) vira `f7 e7` (= `b 0x00CF842C`) — o caminho
# "cheio" passa pelo give do mutex e a mensagem e descartada (0).
#
# Sao 2 bytes, e nada mais: o resto do lote e o do Diag B, byte a byte.
# ---------------------------------------------------------------------------
RELOAD_1_0_RC7_DIAG_B1 = RELOAD_1_0_RC7_DIAG_B + [
    ("fab_diag_trava.py", ["--nivel", "b1", "--em", "0x1a8000"],
     "diag B1: B + o bug do ring corrigido (o mutex e solto)"),
]

# ---------------------------------------------------------------------------
# RELOAD 1.0 RC7 DIAG B2 — a ficha 010 (adendo da coordenacao).
#
# O B1 media o BUG DO RING; a conferencia da coordenacao (D1-D4) mostrou que
# o ring tem 15360 B (a rajada do play nao o enche) e que a ViewTask e
# MONITORADA pelo watchdog: se ela nao bate, o monitor retorna sem alimentar
# o watchdog (e o aparelho reinicia).
#
# O B2 neutraliza o monitor: o `bpl` de `0x00D46B30` (arquivo `0x146B30`,
# `1a d5` = `bpl 0x00D46B68`) vira `00 bf` (`nop`). Toda tarefa conta como
# viva e o watchdog e sempre alimentado — assim o aparelho DIZ se o
# `get_path` da ViewTask e so lento (toca) ou se ele trava (congela).
#
# Sao 2 bytes, e nada mais: o resto do Diag B fica byte a byte.
# ---------------------------------------------------------------------------
RELOAD_1_0_RC7_DIAG_B2 = RELOAD_1_0_RC7_DIAG_B + [
    ("fab_diag_trava.py", ["--nivel", "b2", "--em", "0x1a8000"],
     "diag B2: B + o monitor do watchdog neutralizado (sem watchdog)"),
]

# ---------------------------------------------------------------------------
# RELOAD 1.0 RC7 DIAG B3 — a ficha 011 (o caminho sem o get_path).
#
# O B0 mediu a chamada do get_path; o B2 mostrou que o monitor do watchdog
# e o que leva ao reset. O B3 tira o get_path da ViewTask sem inventar RAM:
# o caminho nao esta no r5 do TITULO (esse e o texto do titulo); ele esta
# no rotulo 2, que a mensagem do `0xD084F8` preenche antes do titulo (a
# fila e serial). O B3 le o texto do rotulo 2 com o `lv_label_get_text` da
# fabrica (le `[rotulo+0x24]`, como o `lv_label_set_text` em 0xD5ED94) e
# copia para ext+0x110 (a mesma RAM que o get_path usava). O caminho
# valido NAO mostra o cinza; o invalido continua cinza. A captura
# 0x001088D8 NAO e tocada; o `carrega_capa` fica cortado como no B.
#
#     leitura 10 bytes  o `movw/movt` + `blx` do get_path (0x001AA144)
#                      vira `ldr r0,[r6,#8]` + `ldr r0,[r0,#0x24]` +
#                      `bl copia_path` + `nop`
#     capa     8 bytes  o cinza do sucesso (0x001AA174) vira `movs r1,#0` +
#                      3 `nop` (src nulo: sem o quadrado cinza)
#     carrega  4 bytes  o `bl` do carrega_capa (0x001AA188) vira
#                      `movs r0, #0` + `nop`
#     codigo  46 bytes  o copia_path (0x001AAA00)
#
# A ferramenta NAO entra no MAPA: ela patcha dentro do lote que a RC7 ja
# montou e no codigo da fabrica, e o `tests/test_rc7.py` (protegido, C2)
# recusa um lote do MAPA que cruze o lote da RC7.
# ---------------------------------------------------------------------------
RELOAD_1_0_RC7_DIAG_B3 = RELOAD_1_0_RC7 + [
    ("fab_diag_b3.py", ["--em", "0x1a8000"],
     "diag B3: o caminho da MainTask, sem get_path na ViewTask"),
]

# ---------------------------------------------------------------------------
# o degrau B4 da ficha 012: o caminho completo da MainTask, sem get_path na
# ViewTask e sem trocar a ordem dos `bl`.
#
# A rajada (0x00CFF0A8) passa a enviar, logo depois do get_path, uma
# mensagem da propria fabrica (classe 3, tipo 5), texto = caminho (ou vazio
# se o get_path falhar), pela mesma infra 0xD0D818. A view trata o tipo 5
# no page_music_play_label_process (0x00D32204): copia o texto para
# ext+0x110, valida com as guardas do B3 e aplica na imagem (src nulo no
# sucesso; 0x00DA8000 no invalido/vazio). O TITULO (0x00DAA0E6) volta a
# fazer so o set_text da fabrica.
#
# PATCH (contra a RC7 exata; 5 pontos + o blob):
#     tipo     2 bytes  `cmp r3,#4` (0x0013223E) vira `cmp r3,#5`
#     tbb      4 bytes  o `tbb [pc,r3]` (0x00132242) vira `bl label_dispatch`
#     rajada  12 bytes  0x000FF0C4: `bl envia_path` + 4 `nop`
#     titulo   4 bytes  0x001AA0FE: `b.w 0xDAA1D0` (so o set_text)
#     carrega  4 bytes  0x001AA188: `movs r0,#0` + `nop` (como no B3)
#     codigo 731 bytes  0x001AAA00: label_dispatch (+0) e envia_path (+0x200)
#                       (o `fab_diag_b4.py` confere o `len(cod)` real;
#                        727 + 4 do `bic` do bit0 do lr)
#
# A ferramenta NAO entra no MAPA: ela patcha dentro do lote que a RC7 ja
# montou e no codigo da fabrica, e o `tests/test_rc7.py` (protegido, C2)
# recusa um lote do MAPA que cruze o lote da RC7.
# ---------------------------------------------------------------------------
RELOAD_1_0_RC7_DIAG_B4 = RELOAD_1_0_RC7 + [
    ("fab_diag_b4.py", ["--em", "0x1a8000"],
     "diag B4: o caminho da MainTask no tipo 5; o TITULO so set_text"),
]

# ---------------------------------------------------------------------------
# os degraus B5a e B5b da ficha 013: abrir a capa no tipo 5 da ViewTask.
#
# O B5a so abre o MP3 e le 10 bytes: "ID3" -> img_set_src(img, NULL);
# qualquer falha -> cinza. O B5b compara o caminho com ext+0x10, desliga o
# monitor da ViewTask, chama carrega_capa(ext), religa o monitor e, no
# sucesso, faz img_set_src(img, ext). O envia_path do B4 continua, agora
# em +0x500. Os dois degraus consomem o B4 exato (a receita encadeia).
#
# PATCH (contra o B4; 2 pontos + o blob):
#     tbb      4 bytes  0x00132242: `bl` para o B5a (+0) ou o B5b (+0x200)
#     rajada  12 bytes  0x000FF0C4: `bl envia_path` (+0x500) + 4 `nop`
#     codigo 1536 bytes 0x001AAA00: B5a (+0), B5b (+0x200) e envia (+0x500)
#
# A ferramenta NAO entra no MAPA: ela patcha dentro do lote que a RC7 ja
# montou e no codigo da fabrica, e o `tests/test_rc7.py` (protegido, C2)
# recusa um lote do MAPA que cruze o lote da RC7.
# ---------------------------------------------------------------------------
RELOAD_1_0_RC7_DIAG_B5A = RELOAD_1_0_RC7_DIAG_B4 + [
    ("fab_diag_b5.py", ["--em", "0x1a8000", "--degrau", "a"],
     "diag B5a: abre o MP3 no tipo 5 e so olha o ID3"),
]
RELOAD_1_0_RC7_DIAG_B5B = RELOAD_1_0_RC7_DIAG_B4 + [
    ("fab_diag_b5.py", ["--em", "0x1a8000", "--degrau", "b"],
     "diag B5b: carrega a capa no tipo 5 com o monitor desligado"),
]

# ---------------------------------------------------------------------------
# os degraus B6a e B6b da ficha 014: o trabalho de arquivo sai da ViewTask e
# vai para o envia_path da PreTask (0x00DAAC00), depois do get_path.
#
# O B6a e o B4 exato com f_open(caminho,1), f_read de 10 B, f_close e free
# na PreTask: "ID3" -> tipo 5 com o caminho (a view do B4 mostra "No data");
# qualquer falha -> tipo 5 vazio. O B6b aloca um contexto de 0x2210 B, copia
# o caminho para +0x110, chama o carrega_capa(0xDAA256) da RC7 e manda 8
# mensagens tipo 6 de 1024 B; a view copia os pixels para ext+0x210+offset e
# faz img_set_src(img, ext) no ultimo. Nenhuma funcao de arquivo sai da view.
#
# O `0xD0D818` devolve 0 em falha (ring cheio ou mensagem nula) e != 0 em
# sucesso; o B6b testa `beq` para o caminho de falha. O `0xD0D881` (aviso
# da view) e chamado depois do ultimo send de cada caminho, como a fabrica
# faz em `0xD084D8`.
#
# PATCH (contra o B4; B6a: 2 pontos + o blob; B6b: 3 pontos + o blob):
#     tipo     1 byte   0x0013223E: so no B6b, `cmp r3,#5` vira `cmp r3,#6`
#     tbb      4 bytes  0x00132242: `b.w label_dispatch` (+0) -- NAO `bl`
#     rajada  12 bytes  0x000FF0C4: `bl envia_path` (+0x200) + 4 `nop`
#     codigo 1536 bytes 0x001AAA00: label_dispatch (+0) e envia_path (+0x200)
#
# O `b.w` e obrigatorio: o `label_process` comeca em `0xD32204` e empilha em
# `0xD3220C`; o epilogo `0xD322A0` faz `pop {r4,r5,r6,pc}`. Um `bl` deixaria
# o LR no topo da pilha e o `pop` sairia 4 B deslocado.
#
# A ferramenta NAO entra no MAPA: ela patcha dentro do lote que a RC7 ja
# montou e no codigo da fabrica, e o `tests/test_rc7.py` (protegido, C2)
# recusa um lote do MAPA que cruze o lote da RC7.
# ---------------------------------------------------------------------------
RELOAD_1_0_RC7_DIAG_B6A = RELOAD_1_0_RC7_DIAG_B4 + [
    ("fab_diag_b6.py", ["--em", "0x1a8000", "--degrau", "a"],
     "diag B6a: abre o MP3 na PreTask e so olha o ID3"),
]
RELOAD_1_0_RC7_DIAG_B6B = RELOAD_1_0_RC7_DIAG_B4 + [
    ("fab_diag_b6.py", ["--em", "0x1a8000", "--degrau", "b"],
     "diag B6b: decodifica a capa na PreTask e manda pixels"),
]
# ---------------------------------------------------------------------------
# B7a/B7b da ficha 015 (diagnostico: nao entram na catraca).
#
# O B7a e o B6b exato + a regra de escala nova no carrega_capa (0xDAA256):
# quatro `cmp #0x40` viram `cmp #0x38` (56). 500x500 passa de s=2 (125x125)
# para s=3 (62x62), esticado para 64x64 pelo callback de saida.
#
# O B7b e o B7a + dois wrappers no lote: os callbacks de entrada (0xDAA404)
# e saida (0xDAA476) do TJpgDec chamam o original e depois vPortYield
# (0xC43634), N=1. Nao ha sleep; a primeira pausa e depois da primeira
# leitura, entao o inicio da capa nao atrasa.
#
# PATCH (contra o B6b; B7a: 4 bytes; B7b: 4 + 8 + 4 + 88 + 34 bytes):
#     escala    4 bytes  0x001AA32C, 0x001AA330, 0x001AA346, 0x001AA34E
#     entrada   4 bytes  0x001AA30C: `orr r1,#1` -> ldr literal 0xDAAE01
#     saida     4 bytes  0x001AA376: `orr r1,#1` -> ldr literal 0xDAAE21
#     view      4 bytes  0x001AAABC: cmp.w r3,#0x1c00 -> b.w guarda
#     wrappers 88 bytes  0x001AAE00: codigo + literais em +0x450/+0x454
#     guarda   34 bytes  0x001AAE60: msg+0xA == 0x408 antes de copiar
#
# A ferramenta NAO entra no MAPA, pelo mesmo motivo do B6: patcha dentro do
# lote da RC7 e o `tests/test_rc7.py` (protegido, C2) recusa lote do MAPA
# que cruze 0x1A8000..0x1AB000.
# ---------------------------------------------------------------------------
RELOAD_1_0_RC7_DIAG_B7A = RELOAD_1_0_RC7_DIAG_B6B + [
    ("fab_diag_b7.py", ["--em", "0x1a8000", "--degrau", "a"],
     "diag B7a: escala 56 na capa (500x500 em 62x62)"),
]
RELOAD_1_0_RC7_DIAG_B7B = RELOAD_1_0_RC7_DIAG_B6B + [
    ("fab_diag_b7.py", ["--em", "0x1a8000", "--degrau", "b"],
     "diag B7b: B7a + vPortYield e guarda do tipo 6"),
]
# ---------------------------------------------------------------------------
# reload_2.0 (ficha 016): o codigo e o do B7b, byte a byte.
#
# A receita e a MESMA lista da `reload_1.0_rc7_diag_b7b`, de proposito: o
# que foi provado no aparelho (B7b) e o que vai para a 2.0. A unica
# diferenca e o carimbo de versao, aplicado DEPOIS pelo `patch_versao.py`
# ("Reload 2.0" em 0x1A4F00) quando o kit e gerado. Sem carimbo, o sha e
# `26ffa272…`, igual ao do B7b; o `tests/test_reload_2_0.py` prova isso.
# ---------------------------------------------------------------------------
RELOAD_2_0 = RELOAD_1_0_RC7_DIAG_B7B

# ---------------------------------------------------------------------------
# reload_2.1 (ficha 017): a 2.0 com os icones da home em grafite.
#
# A receita e a MESMA lista da `reload_2.0`, com UMA diferenca: o passo que
# aplica a folha da home (`fab_icones_home.py`) recebe
# `--png assets/IconesHome_grafite.png`. O codigo nao muda; a folha (paleta e
# pixels) e o carimbo de versao sao o que mudam.
# ---------------------------------------------------------------------------
RELOAD_2_1 = [
    (t, (["--png", "assets/IconesHome_grafite.png"]
         if t == "fab_icones_home.py" else extra), por)
    for t, extra, por in RELOAD_2_0
]

# ---------------------------------------------------------------------------
# reload_2.2 (ficha 018): a 2.0 com os icones escuros e os simbolos
# coloridos (D14). Mesma lista da `reload_2.0`, com UMA diferenca: o passo
# `fab_icones_home.py` recebe `--png assets/IconesHome_escuro_colorido.png`.
# O codigo nao muda; a folha (paleta e pixels) e o carimbo sao o que mudam.
# ---------------------------------------------------------------------------
RELOAD_2_2 = [
    (t, (["--png", "assets/IconesHome_escuro_colorido.png"]
         if t == "fab_icones_home.py" else extra), por)
    for t, extra, por in RELOAD_2_0
]

RECEITAS = {
    "core1.0": CORE_1_0,
    "reload_alpha": RELOAD_ALPHA,
    "reload_alpha_0.2": RELOAD_ALPHA_0_2,
    "reload_1.0_rc1": RELOAD_1_0_RC1,
    "reload_1.0_rc2": RELOAD_1_0_RC2,
    "reload_1.0_rc3": RELOAD_1_0_RC3,
    "reload_1.0_rc4": RELOAD_1_0_RC4,
    "reload_1.0_rc5": RELOAD_1_0_RC5,
    "reload_1.0_rc6": RELOAD_1_0_RC6,
    "reload_1.0_rc7": RELOAD_1_0_RC7,
    # as bissecoes da ficha 008 (diagnostico: nao entram na catraca)
    "reload_1.0_rc7_diag_a": RELOAD_1_0_RC7_DIAG_A,
    "reload_1.0_rc7_diag_b": RELOAD_1_0_RC7_DIAG_B,
    "reload_1.0_rc7_diag_c": RELOAD_1_0_RC7_DIAG_C,
    # o degrau B0 da ficha 009 (diagnostico: nao entra na catraca)
    "reload_1.0_rc7_diag_b0": RELOAD_1_0_RC7_DIAG_B0,
    # o degrau B1 da ficha 010 (diagnostico: nao entra na catraca)
    "reload_1.0_rc7_diag_b1": RELOAD_1_0_RC7_DIAG_B1,
    # o degrau B2 da ficha 010 (adendo; diagnostico: nao entra na catraca)
    "reload_1.0_rc7_diag_b2": RELOAD_1_0_RC7_DIAG_B2,
    # o degrau B3 da ficha 011 (diagnostico: nao entra na catraca)
    "reload_1.0_rc7_diag_b3": RELOAD_1_0_RC7_DIAG_B3,
    # o degrau B4 da ficha 012 (diagnostico: nao entra na catraca)
    "reload_1.0_rc7_diag_b4": RELOAD_1_0_RC7_DIAG_B4,
    # os degraus B5a/B5b da ficha 013 (diagnostico: nao entram na catraca)
    "reload_1.0_rc7_diag_b5a": RELOAD_1_0_RC7_DIAG_B5A,
    "reload_1.0_rc7_diag_b5b": RELOAD_1_0_RC7_DIAG_B5B,
    # os degraus B6a/B6b da ficha 014 (diagnostico: nao entram na catraca)
    "reload_1.0_rc7_diag_b6a": RELOAD_1_0_RC7_DIAG_B6A,
    "reload_1.0_rc7_diag_b6b": RELOAD_1_0_RC7_DIAG_B6B,
    # os degraus B7a/B7b da ficha 015 (diagnostico: nao entram na catraca)
    "reload_1.0_rc7_diag_b7a": RELOAD_1_0_RC7_DIAG_B7A,
    "reload_1.0_rc7_diag_b7b": RELOAD_1_0_RC7_DIAG_B7B,
    # a 2.0 e o B7b byte a byte (so muda o carimbo na geracao do kit)
    "reload_2.0": RELOAD_2_0,
    # a 2.1 e a 2.0 com a folha grafite (o resto da lista e igual)
    "reload_2.1": RELOAD_2_1,
    # a 2.2 e a 2.0 com a folha escura de simbolos coloridos (idem)
    "reload_2.2": RELOAD_2_2,
}

# Ferramentas que existem mas NAO entram na receita, e por que.
#
# Esta lista tinha 23 entradas ate 2026-09-14. As outras 22 eram patches
# de interface da linha 2.x — chevron, Extras, sonda, scrollbar, raio,
# respiro, navegacao, e seis marcados so como "experimento". Os arquivos
# foram APAGADOS junto com a linha, a pedido do mantenedor:
#
#     "experiments sao problematicas"
#     "nao podemos usar essas referencias, elas nao sao boas"
#
# Manter a lista descrevendo arquivos inexistentes seria manter o convite
# a reaproveita-los. Esta tudo no git, no commit da limpeza.
FORA = [
    ("patch_versao.py",  "aplicado pelo make_install_kit (regra R7)"),
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
    ap.add_argument("--receita", default="core1.0",
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
