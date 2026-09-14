# RESTART_PLAN — reinício do OpenPod como **OpenPod Core**

> Escrito em 2026-09-14, a pedido do mantenedor (Master Development
> Prompt, §34–§35). **Nada foi modificado, nada foi gravado.** Este
> documento é o resultado da ETAPA 1 à ETAPA 10: análise do que existe,
> medição do que funciona, e o plano do Core 1.0.
>
> Toda afirmação abaixo carrega classe: **CONFIRMADO** (evidência direta
> nesta sessão ou no hardware), **PROVÁVEL**, **HIPÓTESE**,
> **DESCONHECIDO**.

---

## 1. Estado atual do projeto

### 1.1 O que existe no disco

```
firmware/ORIGINAL/    GN438_original.bin  — 2 MiB, modo 444, sha confere
firmware/WORKING/     ~100 imagens, cadeia v001..v101 + build
firmware/VENDOR/      Flashloader SL-DEV oficial da Shenju + B27_251112.up
firmware/READBACK/    releitura do aparelho (2026-09-12)
tools/                88 arquivos — 26 na receita, 25 declarados fora
docs/                 46 documentos
historico/kits/       82 kits de setores
historico/releases/   OpenPod 1.0 .. 1.3
historico/recuperacao/ kit de recuperação + RECUPERAR.md
OpenPod 1.4 .. 3.1/   13 pastas de release, cada uma com .up e setores
marte/                estudo NanoClone: referência, paleta, adaptados
```

### 1.2 Onde o aparelho está

| versão | interno | situação |
|---|---|---|
| **OpenPod 2.4** | V077 | **última gravada e testada** — melhor resultado até agora |
| OpenPod 3.0 | V100 | primeira imagem por receita declarada — **nunca gravada** |
| OpenPod 3.1 | V101 | 3.0 + 3 ferramentas que a medição mostrou faltando — **nunca gravada** |

**CONFIRMADO nesta sessão:** `firmware/WORKING/GN438_build.bin`,
`GN438_openpod_v101.bin` e a base do kit `OpenPod 3.1/` são **a mesma
imagem** (sha `ab98ef39…`). A 3.1 é, portanto, exatamente a saída de
`tools/build.py` de hoje.

### 1.3 Defeitos abertos herdados (da 2.1/2.2, ver `ESTADO_ATUAL.md`)

| # | defeito | situação |
|---|---|---|
| 1 | faixa clara vazia sob o título | causa provável identificada; hipótese do fundo branco **derrubada pelo aparelho** |
| 2 | título colide com contador na Música | contador **não localizado** |
| 5 | vão de 5 px nas 14 telas sem lista | diagnosticado, correção pronta, **não aplicada** |
| 6 | barra da home no descanso de tela | não há página de descanso |
| — | **Extras: os 6 itens não abrem** | 3 patches empilhados falharam; **fora da receita de propósito** |

---

## 2. Conhecimentos já adquiridos — o que está fechado

Medido, não suposto (`docs/COBERTURA.md`):

| dimensão | cobertura |
|---|---|
| estrutura do arquivo (partições, CRC, `.up`, gravação) | **~100%** |
| camada de interface (o que o OpenPod mexe) | **alta** |
| firmware inteiro (áudio, BT, rádio, vídeo, USB, FS) | **~15–20%** |

### 2.1 O mapa físico — CONFIRMADO

```
0x000000  bootloader          51.532 B   (HLKJ, headerCrc, loadCrc)
0x00D000  tabela de partições     64 B   <- o setor que matou o 1º aparelho
0x00E000  FIRM             1.647.984 B   XIP em 0x00C00000
0x1A1000  TONE                 8.248 B
0x1A3038  ÁREA LIVRE         364.488 B   100% 0xFF no original — VERIFICADO hoje
0x1FC000  PSMP                16.384 B   configurações do usuário
```

**Verificado nesta sessão:** entre `0x1A3038` e `0x200000` o firmware de
fábrica só tem bytes não-`0xFF` **dentro da PSMP** (15 trechos, 2.081 B).
A área livre é virgem de verdade.

### 2.2 Integridade — CONFIRMADO no hardware

- `.up`: cabeçalho `CONFIG`, payload a partir de `0x100`,
  **CRC-16/CCITT-FALSE**, chip `SL6801`, assinatura `55 AA`.
- **O CRC da FIRM não é verificado por nada** (regra R1,
  `PROTOCOLO_GRAVACAO.md`): confirmado no aparelho em 2026-09-13,
  bootando com tabela de fábrica sobre uma FIRM diferente.
- Consequência: o setor `0x00D000` **saiu do projeto**. A construtora de
  hoje não o toca — verificado: menor offset alterado é `0x048000`.
- Não há criptografia, não há assinatura.

### 2.3 Recuperação — CONFIRMADA no hardware

```
USB conectado  ->  segure VOLUME ↓  ->  aperte RESET     => 301a:2800
```

ROM de máscara, roda antes de qualquer coisa que gravemos. Foi assim que
o aparelho voltou depois do incidente da V028. **Este hardware é
recuperável por software.**

### 2.4 Arquitetura de interface

LVGL v8, display 128×160, 83 páginas mapeadas, 412 símbolos recuperados,
tecla única em `0x00D47654` (`0x81`=VOL, `0xA0`=M), atualização por SD
via `HAL_pmu_sd_update_flag_set` (`0x00CF6CA0`, órfã no firmware de
fábrica, hoje chamada pelo item "Atualizar por SD").

---

## 3. O que pode ser reaproveitado — medido nesta sessão

### 3.1 `tools/build.py` — a receita. **APROVADO**

Executado duas vezes do zero nesta sessão:

```
26 passos, do ORIGINAL à imagem final
confere o sha do ORIGINAL antes de começar
cada passo em arquivo próprio, em diretório temporário
para no primeiro erro, mostra a saída da ferramenta
MAPA da área livre: cada ferramenta recebe --em <endereço> e o pipeline
  RECUSA escrita fora do lote declarado
saída: ab98ef39...  nas DUAS execuções  => DETERMINÍSTICO
tempo: ~5 s
```

Isto resolve o problema estrutural que o próprio cabeçalho documenta: o
**alocador incremental**, em que o endereço de uma rotina emergia da
ordem histórica. Hoje o endereço é declarado. **É a peça mais valiosa do
projeto e deve ser a fundação do Core.**

### 3.2 Validação — APROVADA, com uma ressalva de instrumento

| ferramenta | resultado na imagem construída hoje |
|---|---|
| `validate_firmware.py` | **21 OK, 1 "FALHA"** |
| `audita_chrome.py` | **sem divergências** |
| `gera_up.py --autoteste` | **byte-idêntico** ao `.up` de referência |

A "falha" é o CRC da FIRM — **o comportamento correto e desejado** pela
regra R1. As imagens v073 (que boota), v077 (que boota) e v101 acusam a
mesma linha.

> **Dívida de instrumento:** um validador que grita FALHA no caso normal
> ensina a ignorar falhas. Isso é exatamente o hábito que custou o
> primeiro aparelho. **Ação no Core 1.0:** o CRC da FIRM passa a ser
> reportado como `ESPERADO (R1)` quando a tabela for a de fábrica, e
> FALHA de verdade só se a tabela tiver sido alterada.

### 3.3 Empacotamento `.up` — APROVADO

Conferidos nesta sessão, campo a campo e CRC recalculado:

| arquivo | payload | CRC | veredito |
|---|---|---|---|
| `OpenPod 3.1/OpenPod 3.1.up` | 1.732.608 B | `0x6FC6` | **OK** |
| `OpenPod v044/update.up` | 1.720.320 B | `0xF309` | **OK** |
| `firmware/WORKING/update_restore_original.up` | 1.716.280 B | `0x77F5` | **OK** |

### 3.4 Kit de setores — APROVADO

`make_install_kit.py` calcula tudo das imagens (nada transcrito à mão),
gera setores de reversão para o estado anterior, e aplica a regra R7
(carimbo de versão). Nasceu do incidente de 2026-09-12.

### 3.5 Estudo Marte / NanoClone — PRONTO, não implementado

`docs/PROJETO_MARTE.md` está completo: paleta extraída bitmap a bitmap,
9 dos 10 ícones cabem em 128 px sem redesenho, barra de progresso já
remontada em `marte/adaptado/`, fonte decodificada, licença CC BY-SA 3.0
registrada em `ATRIBUICAO.md`. **É insumo pronto para a fase de
interface — e não entra no Core 1.0.**

---

## 4. O que deve ser tratado apenas como referência

| item | por quê |
|---|---|
| **Saturno (S1–S12)** | funciona e está na receita, mas é **revestimento**, não fundação: depende de `patch_chrome_padrao` e `patch_cor_texto_lista`. Carrega os defeitos 1, 2, 5, 6 em aberto |
| **`patch_extras` + `_fix` + `_fix2`** | três patches no mesmo ponto, os 6 itens continuam sem abrir. Fora da receita **de propósito** |
| **A cadeia v001..v101** | 100 imagens em `firmware/WORKING/`. Valem como **arquivo de evidência** (o logo do OpenPod, por exemplo, só existe ali), não como base de construção |
| **`patch_navegacao`** | revertido na 1.8: o padrão de fábrica (M sem função, VOL volta) é **decisão de produto**, confirmada por censo de 41 de 49 telas |
| **`crc_neutralize.py`** | correto e disponível, mas **desnecessário** desde R1 |
| **Kits `historico/kits/`** | recuperação de versões antigas, não desenvolvimento |

---

## 5. Ferramentas confiáveis

Critério: rodou nesta sessão, ou foi confirmada no hardware.

| ferramenta | evidência |
|---|---|
| `build.py` | 26/26 passos, determinística, 2 execuções idênticas |
| `validate_firmware.py` | 21 verificações OK (ver ressalva §3.2) |
| `audita_chrome.py` | sem divergências; **acusa a V070 e aprova a V071** — o teste discrimina |
| `gera_up.py` | autoteste byte-idêntico ao `.up` oficial |
| `make_update_up.py` | mesmo algoritmo do upstream `fwhelper dump2fw` |
| `make_install_kit.py` | kits gravados com sucesso da 1.4 à 2.4 |
| `afere_fora.py` | mede o efeito real de cada ferramenta excluída; já corrigiu 4 erros de classificação minha |
| `fw_common.py` | base dos validadores |
| `asm.py` (clang) | substituiu montagem à mão, origem dos 2 piores bugs de encoding |

---

## 6. Ferramentas experimentais / não confiáveis

| ferramenta | classe |
|---|---|
| `patch_extras*.py` (3) | **falha conhecida no aparelho** |
| `patch_sonda.py` | instrumento de diagnóstico; a leitura saiu **ambígua** |
| `patch_fundo_display.py` | **hipótese derrubada pelo aparelho** |
| `patch_chevron.py` | aborta fora do contexto histórico; redesenharia os chevrons |
| `patch_scrollbar` / `2` | superados pelo `3` |
| `patch_bar_height`, `patch_raio_selecao`, `patch_respiro_lista`, `patch_lista_sistema`, `patch_home_padrao` | superados pelo Saturno |
| `patch_home_icon`, `patch_fonte_negrito`, `patch_largura_barra`, `patch_battery_y`, `patch_selecao_criacao` | experimentos |
| `make_v030.py` | rede de segurança, aplicada à parte |

---

## 7. Pipeline atual — e onde ele está incompleto

O que roda hoje:

```
ORIGINAL (sha conferido)
   -> build.py            26 passos declarados, mapa de área livre imposto
   -> validate_firmware   estrutura, headerCrc, loadCrc, partições
   -> audita_chrome       divergências de tema tela a tela
   -> make_install_kit    setores + reversão + carimbo de versão
   -> gera_up             .up com CRC-16/CCITT-FALSE
   -> [AUTORIZAÇÃO]       -> hardware
```

**Lacunas CONFIRMADAS hoje:**

| # | lacuna | consequência |
|---|---|---|
| L1 | **não há passo de binary diff no pipeline** | o diff existe como `--verificar` e à mão; §12 do prompt exige que toda versão seja comparada com a base, com offsets e regiões registrados |
| L2 | **não há testes de regressão automáticos** | `audita_chrome` cobre o tema; nada cobre título, textos, `.up`, área livre |
| L3 | **`build.py` não valida nem empacota** | a cadeia depende de o operador lembrar dos passos seguintes na ordem |
| L4 | **contradição dentro do `build.py`** | `patch_status_bar.py` e `fix_status_bar.py` estão **na RECEITA (linhas 165-166) e na lista FORA (259-260) ao mesmo tempo**. A lista FORA é a documentação da intenção — e hoje ela mente |
| L5 | **`ROADMAP.md` diz "22 passos"; a receita tem 26** | deriva de documentação |
| L6 | **o projeto NÃO está sob controle de versão** | `git ls-files` na pasta OpenPod retorna **0 arquivos**. O repositório é a pasta-mãe, em outro branch, com outro conteúdo |

L6 é a mais grave para as regras §33 (observabilidade) e §32
(recuperabilidade): hoje não existe histórico de `docs/` e `tools/`, só
dos binários que sobreviveram em pastas.

---

## 8. Problemas encontrados anteriormente — e a regra que cada um gerou

| problema | custo | regra permanente |
|---|---|---|
| `write_flash` gravava do offset 0 do arquivo, não do offset da flash | **tabela de partições corrompida, 1º aparelho brickado** (V028) | **R1** — `0x00D000` nunca mais é gravado. Um arquivo **por setor**, sempre `0` no 2º argumento |
| Premissa "gravar só acima de `0x00D000` mantém a recuperação" nunca verificada | o brick | **R5** — toda regra de segurança carrega premissa, verificação e data. Evidência contrária abre revisão imediata |
| `WROTE` contado antes da escrita | estado do setor ficou **DESCONHECIDO** | **R3** — verificação por releitura, nunca por hash do arquivo no PC |
| Alocador incremental de área livre | a cadeia só compunha na ordem histórica exata | **endereço é parâmetro (`--em`), nunca emergente** |
| `FORA` montada lendo descrição, não medindo | a 3.0 saiu **sem "OpenPod" no boot e sem título na home** | **`afere_fora.py`**: suposição não é medição |
| "M deveria voltar, como no iPod" | 1 versão inteira | **censo antes de chamar de defeito**: 41 de 49 telas é decisão de produto |
| Um caminho corrigido, outro esquecido (V016, V027, V031) | 3 versões | ao mudar a aparência de um objeto, **enumerar todos** os pontos que o criam ou repintam |
| Montagem Thumb-2 à mão + verificador feito da mesma suposição | 2 piores bugs de encoding | montar com **clang** (`asm.py`), iterar até convergir, falhar alto |
| Extras: 3 patches empilhados no mesmo ponto | 3 versões, ainda quebrado | **não empilhar correção sobre correção**: ou acha a causa, ou sai da receita |

---

## 9. Estratégia de Recovery

### 9.1 O que já está pronto — CONFIRMADO

**Camada 0 — ROM de máscara.** Modo download (`301a:2800`), acessível
com a flash destruída. Testado em condições reais.

**Camada 1 — `update_restore_original.up`.** Verificado byte a byte
nesta sessão:

```
payload 1.716.280 B = 0x000000..0x1A3038
IDÊNTICO ao GN438_original.bin nesse intervalo    <- verificado hoje
cabeçalho CONFIG / SL6801 / 55AA, CRC 0x77F5 confere
```

**Camada 2 — kit de setores**, com arquivos de reversão ao estado
anterior em cada release.

### 9.2 As três lacunas do Recovery

| # | lacuna | classe | proposta |
|---|---|---|---|
| **REC-1** | o `.up` de restauração cobre `0..0x1A3038`. As rotinas do OpenPod na **área livre** (`0x1A3038..0x1FC000`) **permanecem gravadas** | CONFIRMADO | inofensivo — a FIRM de fábrica não tem gancho algum para elas. Mas **não é estado de fábrica**. Gerar um `recovery/` que também apague a área livre, e declarar qual dos dois é o oficial |
| **REC-2** | a ferramenta de recuperação do Mac vive em **`/tmp/smtlink_mac`** | CONFIRMADO (existe agora; `/tmp` é volátil) | mover para `recovery/ferramenta/`, com fonte, e conferir o sha no kit |
| **REC-3** | `RECUPERAR.md` aponta para `firmware/READBACK/GN438_bricked_dump.bin`, que **não existe** — é o roteiro de um incidente | CONFIRMADO | separar **roteiro de emergência** de **registro de incidente**; o roteiro não deve citar arquivo de um evento específico |

### 9.3 Regra de Recovery para o Core

> **Antes da primeira gravação do Core 1.0**, a pasta `recovery/` tem de
> existir, ser autossuficiente (ferramenta + original + `.up` + passo a
> passo + sha de tudo) e ter sido **conferida por leitura** no aparelho
> (`read_flash`, que não escreve nada).

---

## 10. Estratégia do OpenPod Core

Três decisões de fundo, nesta ordem:

**D1 — A receita é a única fonte da imagem.** Nenhuma imagem de release
sai de `firmware/WORKING/` editada à mão. `build.py` é a definição do que
o OpenPod é. Corrigiu um passo? Reconstrói.

**D2 — Baseline é declaração do mantenedor, não consequência do
número.** Uma versão só vira base depois de um "está OK, pode usar como
base". A receita registra, no topo, qual baseline ela reproduz.

**D3 — Uma versão, um objetivo.** O que não serve ao objetivo da versão
sai — mesmo funcionando, mesmo pronto. O Extras é o precedente: **nada na
receita finge funcionar**.

E uma consequência prática de §9 do prompt (*toda versão é um firmware
completo e independente*): o `.up` já satisfaz isso hoje — reescreve a
imagem inteira e não confere estado anterior. **CONFIRMADO** pelo uso da
1.4 à 2.4. O caminho oficial de instalação do Core é o **cartão SD**.

---

## 11. Plano do OpenPod Core 1.0

### 11.1 Base

```
Base:   firmware/ORIGINAL/GN438_original.bin   (sha b7cd5eb9…)
Meio:   tools/build.py, receita PODADA
Status alvo: EXPERIMENTAL até o mantenedor declarar STABLE
```

**Por que do ORIGINAL e não da 2.4:** a 2.4 é ponta de uma cadeia manual
de 100 imagens; a receita é a única base auditável que temos. E ela já
foi exercitada: a 3.1 é a saída dela.

### 11.2 O que entra (e só isso)

| # | item | ferramenta | situação |
|---|---|---|---|
| 1 | **Update por SD** | `patch_update_sd.py` | **pronta, na receita** |
| 2 | **Informações do produto** (`OpenPod` / `OpenPod Core 1.0` / `GN-438`) | `patch_versao.py` + textos | pronta; **rever o texto** para o formato pedido em §18.2 |
| 3 | **Logo OpenPod 128×35 no boot** | **NÃO EXISTE** | ver §11.3 |
| 4 | **Português do Brasil** | `relocate_lang_table.py` + `aplica_textos.py` | prontas, na receita (175 textos revisados) |

### 11.3 A lacuna concreta do Core 1.0 — o logo

**CONFIRMADO nesta sessão:**

- o slot é `0x0CC7C4` (`lv_img_dsc` + paleta BGRA em `0x0CC7D0`, 1024 B +
  pixels em `0x0CCBD0`, 4480 B = 128×35 `INDEXED_8`);
- `assets/OpenLogo.png` tem **exatamente 128×35** — sem redimensionar;
- a receita de hoje **não toca no logo**: 0 bytes diferentes em
  `0x0CC7C4..0x0CDD50` entre o ORIGINAL e a imagem construída. A 3.0 e a
  3.1 bootam com o logo **GENAI** de fábrica;
- a ferramenta que fez isso na V007 **não existe mais** em `tools/`;
- **mas os bytes existem**: `GN438_openpod_v007.bin` difere da v006
  exatamente em `0x0CC7C4..0x0CDD50` (5.322 B, dos quais 2 são o CRC em
  `0x00D01C`, que **não** deve ser copiado).

> **Tarefa do Core 1.0:** escrever `tools/patch_logo.py`, que converte
> um PNG 128×35 para `INDEXED_8` no formato do slot e recebe `--em`.
> Critério de aceite: aplicado sobre o ORIGINAL, produz em
> `0x0CC7C4..0x0CDD50` **os mesmos bytes da v007** (ou uma conversão
> declaradamente melhor, com o erro por canal medido).

### 11.4 O que fica FORA do Core 1.0

Saturno (S1–S12), `patch_chrome_padrao`, `patch_cor_texto_lista`,
`patch_cor_selecao`, `patch_titulos`, `make_list_home`, `patch_home_keys`,
`patch_barra_selecao`, `patch_scrollbar3`, `make_extras_menu`,
`patch_status_bar` / `fix_status_bar`, `patch_menu_text`.

**Nada disso é descartado** — tudo continua na receita completa, que
passa a se chamar *linha de interface* e volta na **Core 2.0**. Sai do
**1.0** porque §19 do prompt é explícito e porque o valor do 1.0 é ser
pequeno o bastante para que um defeito tenha causa óbvia.

> ⚠️ **Consequência a aceitar de olhos abertos:** o Core 1.0 terá a home
> em **grade 3×3 de fábrica** e sem a identidade visual das versões 1.4+.
> Visualmente é um **recuo** em relação à 2.4. Isso é o preço declarado
> de uma fundação auditável. Se o mantenedor preferir não recuar, a
> alternativa honesta está em §13.

### 11.5 Ordem de execução

```
0. recovery/ montado e conferido por LEITURA              (bloqueante)
1. git init no OpenPod, primeiro commit do estado atual   (bloqueante)
2. tools/patch_logo.py + critério de aceite contra a v007
3. build.py --receita core1.0  (4 passos + logo)
4. validate_firmware (com o CRC da FIRM reclassificado)
5. binary diff contra o ORIGINAL — setores, offsets, bytes, registrado
6. gera_up + verificação do .up gerado
7. make_install_kit (caminho alternativo, Linux)
8. RELATÓRIO -> revisão do mantenedor
9. [AUTORIZAÇÃO EXPLÍCITA] -> gravação por cartão SD
10. teste no aparelho -> STABLE ou EXPERIMENTAL
```

Os passos 0 e 1 são bloqueantes por decisão de engenharia, não por
formalidade: sem eles não há como responder *"se falhar, conseguimos
voltar?"* (§32) nem *"qual era a base?"* (§4).

---

## 12. Riscos conhecidos

| risco | classe | mitigação |
|---|---|---|
| **Gravação interrompida** (a causa nunca determinada do V028) | CONFIRMADO que acontece | R6: bateria cheia, USB direto, cabo conhecido; `.up` pelo SD em vez de cabo |
| **Perder o trabalho de `docs/` e `tools/`** — sem controle de versão | **CONFIRMADO** | `git init`, passo bloqueante |
| **Ferramenta de recuperação em `/tmp`** | **CONFIRMADO** | REC-2 |
| Validador que grita FALHA no caso normal | **CONFIRMADO** | reclassificar o CRC da FIRM (§3.2) |
| **Toda a imagem gerada hoje nunca foi ao aparelho** (3.0 e 3.1) | CONFIRMADO | o Core 1.0 é menor que ambas: menos superfície na primeira gravação da nova linha |
| Regressão silenciosa em subsistema não mapeado (áudio, BT, FS) | PROVÁVEL | cobertura de ~15–20% fora da GUI; o Core 1.0 só toca logo, textos e um item de menu |
| `patch_titulos` exige 4 KiB virgens em `0x1A5000` | CONFIRMADO | fora do Core 1.0; volta com o mapa da área livre declarado |
| Licença CC BY-SA 3.0 do NanoClone contamina derivados | CONFIRMADO | `ATRIBUICAO.md` + crédito na tela Sobre; **não entra no 1.0** |
| Brick | **deixou de ser fatal** (R0, ROM de máscara) | recovery conferido antes de gravar |

---

## 13. Próximos passos

### Imediatos (não precisam de autorização, não tocam no aparelho)

1. `git init` na pasta OpenPod + `.gitignore` para os binários grandes
   (`firmware/WORKING/*.bin` são ~200 MB); commit inicial de `docs/`,
   `tools/`, `marte/`, `assets/` e das pastas de release.
2. Montar `recovery/` autossuficiente (REC-1, REC-2, REC-3).
3. Corrigir a contradição `RECEITA` × `FORA` no `build.py` (L4) e a
   deriva "22 passos" no `ROADMAP.md` (L5).
4. Reclassificar o CRC da FIRM no `validate_firmware.py` (§3.2).
5. Escrever `tools/patch_logo.py` com o critério de aceite da §11.3.
6. Acrescentar ao `build.py` os passos de diff e validação (L1, L3).

### Decisão que só o mantenedor toma

**Qual é a base do Core 1.0?** As duas leituras são defensáveis:

| | **A — do ORIGINAL** (o que o prompt pede) | **B — da 2.4** |
|---|---|---|
| fundação | receita auditável, 5 passos | cadeia manual de 100 imagens |
| aparência | **recua** para a home de fábrica | mantém o que já agrada |
| defeitos abertos | nenhum (não há interface nova) | herda os 4 |
| risco na 1ª gravação | mínimo | já é conhecido |

**Recomendo A**, exatamente pelo motivo do §3 do prompt: o que quebrou o
projeto anterior não foi a interface, foi não saber mais o que havia
dentro da imagem. O recuo visual é temporário — a linha de interface
inteira volta na Core 2.0, e ela **já está construída e mede limpa**.

### Não fazer agora

Gravar qualquer coisa no aparelho. Implementar Marte. Retomar o Extras.
Aplicar as correções dos defeitos 1, 2 e 5 — elas pertencem à linha de
interface, não à fundação.
