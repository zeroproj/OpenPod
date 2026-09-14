# OpenPod Core 1.0.1 — relatório de versão

```
Base       OpenPod Core 1.0, gravada e testada no aparelho
Receita    tools/build.py --receita core1.0      6 passos
Gerada     2026-09-14
Status     STABLE  <- declarado pelo mantenedor em 2026-09-14,
                      depois de ver o aparelho
Kit        firmware/RELEASE/OpenPod Core 1.0.1/
Baseline   e a base valida para a Core 1.1 em diante
```

> **STABLE não é um carimbo de qualidade: é uma autorização.** Quer dizer
> que esta imagem pode ser usada como base de versões seguintes, sem
> reconstruir tudo a partir do ORIGINAL. Regra §6 do prompt-mestre.

Versão de **correção**. Mesmo objetivo da 1.0; conserta os dois defeitos
que o aparelho mostrou.

---

## 1. O que o teste da 1.0 disse

Relato do mantenedor, 14/09, com a 1.0 rodando:

| | |
|---|---|
| ligou | **sim** |
| menus em português | **"atualizados perfeito"** |
| "Atualizar por SD" em Configurar | **apareceu** |
| nada quebrado até o momento do teste | **confirmado** |
| **tela de abertura** | ❌ fundo branco com a logo de fundo preto |
| **tela Informações** | ❌ tudo sobreposto numa linha só |

Quatro dos seis itens do roteiro passaram na primeira gravação da linha
Core. Os dois que falharam são estes.

---

## 2. Defeito 1 — o retângulo preto na abertura

A logo do OpenPod tem fundo preto; a tela de abertura, fundo claro. Com o
logotipo GENAI de fábrica o problema não aparecia — ele é claro, igual à
tela.

**As duas funções que desenham a logo** (`0x00D22794` e `0x00D228A0`)
consultam um getter de cor **clara** (`0x00D21384`). Existe ao lado um
getter de **preto** (`0x00D2138A`).

```
0x0012285C   93 -> 96    redireciona o BL da 1a funcao
0x001228E6   4E -> 51    redireciona o BL da 2a funcao
```

Muda **para onde a chamada aponta**, não o valor que ela devolve.

> **Por que não escurecer o getter:** ele é sobrecarregado — devolve uma
> "cor clara" que umas telas usam como **texto** e outras como **fundo**.
> Escurecê-lo deixaria o texto de Configurar invisível.

**Procedência:** é o patch da **V008**, de 12/09, que já rodou na tela
("logo do OpenPod sobre preto, sem faixa e sem moldura clara"). A
ferramenta tinha se perdido quando a construção virou receita declarada —
a mesma história do `patch_logo.py`. Voltou como
`tools/patch_fundo_abertura.py`, e o `--autoteste` confere byte a byte
contra a V008.

**A logo e o fundo andam juntos.** Na receita, `patch_fundo_abertura` vem
logo depois de `patch_logo`, e não é opcional.

---

## 3. Defeito 2 — a tela Informações sobreposta

**A causa era uma afirmação minha, errada, nunca verificada.**

O `patch_versao.py` dizia no cabeçalho que o rótulo aceita `\n`, porque a
tabela de idiomas tem strings assim (ids 140, 154, 161). Aqueles ids vão
para um **rótulo LVGL comum**. A tela Informações **não**: `page_info`
monta uma **mensagem** (descritor em `0x008238F0`, entregue a
`0x00D0D818`), e esse caminho **não quebra linha**.

Gravada com `"OpenPod Core 1.0\nGN-438"`, o aparelho desenhou os dois
textos **um sobre o outro**. **CONFIRMADO na tela.**

### O que se sabe agora sobre essa tela

Ela tem **dois espaços de texto**, e os dois funcionam:

```
titulo        get_string(43) -> "Sobre o aparelho"
linha de baixo  literal apontado por 0x0010A59C
```

O id 43 tem **um único chamador** — medido por varredura de `BL` com
janela de 6 instruções, não por disassembly linear. É esta tela e mais
nada.

Cada espaço aceita **uma linha**, limite **113 px**:

```
'OpenPod Core 1.0'          102 px
'OpenPod Core 1.0.1'        112 px
'Core 1.0 - GN-438'         100 px
'OpenPod Core 1.0 GN-438'   148 px   NAO CABE
```

### A correção

**Decisão do mantenedor:** voltar ao que funcionava da 1.4 à 3.0 — título
intocado, linha de baixo numa linha só.

```
Sobre o aparelho
OpenPod Core 1.0.1
```

O modelo `GN-438` não aparece. Pô-lo lá exigiria trocar o título (opção
descartada) ou fazer a camada de mensagem quebrar linha — que é
**investigação em aberto**, registrada para a 1.1, não coisa de uma
versão de correção.

---

## 4. Validação

```
validate_firmware        21 OK + a falha de CRC da R1, a esperada
```

**Diff contra a Core 1.0 — o que está no aparelho:**

```
10 bytes, 2 setores

  0x122000    2 B    os dois BL da logo
  0x1A4000    8 B    o texto da tela Informacoes
```

**Diff contra o ORIGINAL:**

```
9.140 bytes, 9 setores, menor offset 0x048798
0x00D000 tocado          NAO
abaixo de 0x00D000       NADA
PSMP                     INTOCADA
```

**Pacote `.up`:** 1.724.672 B, CRC do payload `0x67AB`.

**Verificações dirigidas:**

```
0x12285C  93 -> 96   confere com a V008
0x1228E6  4E -> 51   confere com a V008
texto da tela Informacoes: 'OpenPod Core 1.0.1'   (112 px, cabe)
```

---

## 5. Hashes

```
imagem (sem carimbo)  7312fbd066b1a31e508a51c9c44c5e203e17e6d1e1b9719c0df7e37e7b250d34
imagem (carimbada)    36125f5665b8613e0d96215e2ffcf36170d847068d0c72e572167fe506400c1f
```

---

## 6. Como instalar

**Pelo cartão SD** — e desta vez isso também **testa** o recurso que a
1.0 trouxe:

```
1. copie  firmware/RELEASE/OpenPod Core 1.0.1/OpenPod_Core_1.0.1.up
   para a RAIZ do cartao, com o nome  update.up
2. no aparelho: Configurar -> Atualizar por SD -> Sim
3. ele reinicia e se atualiza
4. APAGUE o update.up do cartao
```

> **Se funcionar, fecha o último item do roteiro da 1.0** — "Atualizar
> por SD funciona de verdade?", que não dava para testar sem uma versão
> seguinte. Agora dá.

**Por cabo**, se preferir: o kit tem **2 setores, 8 KiB**. Ele confere o
estado ANTES por SHA-256 e **recusa se o aparelho não estiver na Core
1.0** — a base deste kit é ela, não o firmware de fábrica.

```
cd "firmware/RELEASE/OpenPod Core 1.0.1"
sudo sh flash_OpenPod_Core_1.0.1.sh /opt/smartlink_flash
```

---

## 7. ✅ Confirmado no aparelho — 2026-09-14

Relato do mantenedor: **"Tudo funcionou."**

```
abertura                  logo sobre PRETO, sem moldura clara        OK
Configurar > Informacoes  duas linhas, sem sobrepor                  OK
Atualizar por SD          instalada PELO CARTAO, funcionou           OK
resto                     igual a 1.0                                OK
```

### O que o item 3 fecha, e não é pouco

A instalação por cartão funcionou **de ponta a ponta**, numa imagem
gerada pelo nosso pipeline:

```
build.py -> gera_up.py -> update.up no cartao
   -> Configurar > Atualizar por SD
      -> HAL_pmu_sd_update_flag_set (0x00CF6CA0, orfa de fabrica)
         -> reboot -> bootloader le 0:/update.up
            -> grava -> boota na versao nova
```

Cada elo desse caminho era, até hoje, **análise estática**. Agora é
**CONFIRMADO**. A partir daqui toda versão instala sem cabo, sem abrir o
aparelho, sem modo download.

---

## 7-bis. Nota de reprodutibilidade — leia antes de regerar

A 1.0.1 publicada foi gerada **antes** de o carimbo de versão ganhar
endereço fixo (pendência 2 desta lista, fechada logo depois). Naquela
build o `patch_versao.py` alocou sozinho, caindo em `0x001A4928`; a
partir da 1.1 ele mora sempre em `0x001A4F00`.

**Consequência:** regerar a 1.0.1 com as ferramentas de hoje **não**
reproduz a imagem publicada.

```
imagem carimbada publicada (a que esta no aparelho)
    36125f5665b8613e0d96215e2ffcf36170d847068d0c72e572167fe506400c1f

a mesma receita hoje, com o carimbo em 0x1A4F00
    6ff2716d6d7796305181cd82783b88e002633e0716cfc45a6ac52401add2ee92

    diferenca: 40 bytes em 2 setores (0x10A000 e 0x1A4000) — o texto
    mudou de lugar e o literal que aponta para ele acompanhou. Nenhuma
    mudanca de comportamento.
```

A **imagem sem carimbo continua reproduzível byte a byte**:
`tools/build.py --receita core1.0` sai sempre em `7312fbd066b1a31e...`.

Os artefatos publicados **não foram regerados**: são o que foi gravado e
testado, e reescrevê-los apagaria o que eles de fato foram. A correção
vale da 1.1 em diante.

## 8. Pendências

| # | pendência |
|---|---|
| 1 | a camada de **mensagem** (`0x00D0D818`) não quebra linha; mostrar nome e modelo em linhas separadas exige entendê-la. Aberto para a 1.1 |
| 2 | ~~`patch_versao.py` aloca sozinho~~ ✅ **fechada** — endereço fixo `0x001A4F00`, declarado no MAPA. Vale da 1.1 em diante (ver §7-bis) |
| 3 | ~~binary diff e validação fora do `build.py`~~ ✅ **fechada** — os dois são passos do pipeline agora, com teste negativo |
