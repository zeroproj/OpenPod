# OpenPod — Reload 2.0

Melhorar o **Iigenai GN-438**, um player YP3/Smartlink de baixo custo,
mantendo o que já funciona e corrigindo o que incomoda. Nada de reescrever
o firmware do zero nem de copiar outro aparelho.

**Site:** https://zeroproj.github.io/OpenPod/ (fonte em `docs/index.html`).
O repositório público recebe **só a página e o kit** (`tools/publica_release.py`).
O código-fonte e a análise ficam no repositório **privado** `zeroproj/OpenPod-dev` (remoto `privado`).

> **Estado em 2026-11-14:** **OpenPod Reload 2.0 publicada**: a RC6 mais a
> capa do álbum na Tocando Agora. A capa é lida e decodificada na PreTask,
> e os pixels vão para a view por mensagem, cedendo a vez durante o decode.
> Próximo: ícones grafite na 2.1 (`docs/decisoes.md`, D13).
>
> Entrada obrigatória: **[`docs/processo.md`](docs/processo.md)**, que tem o
> estado e o ponto de retomada.

## Por onde começar

| quero... | leia |
|---|---|
| o estado e o que vem a seguir | `docs/processo.md` |
| como uma ficha anda (desenvolvedor, revisão, conferência) | `docs/processo-padrao.md` |
| as regras do projeto | `CLAUDE.md`, `AGENTS.md` |
| as decisões do decisor | `docs/decisoes.md` |
| o histórico das fichas | `docs/tarefas/` |
| voltar o aparelho ao de fábrica | `recovery/VOLTAR_AO_ORIGINAL.md` |
| recuperar com o firmware destruído | `docs/MODO_DOWNLOAD.md`, `docs/NIVEIS_DE_GRAVACAO.md` |
| o firmware por dentro | `docs/FIRMWARE_ANALYSIS.md`, `docs/ARQUITETURA.md`, `docs/GUI_ANALYSIS.md` |

## Estrutura

```
firmware/
  ORIGINAL/     GN438_original.bin: sagrado, sha b7cd5eb9…
  RELEASE/      kits internos: Reload 2.0, RC6 e Recuperacao-pos-B27
  VENDOR/       Flashloader SL-DEV oficial da Shenju
  READBACK/     leituras feitas do aparelho
release/        kits: OpenPod-Reload-2.0 (atual), RC6 (volta segura), Fabrica
recovery/       o recovery oficial, autossuficiente (`sudo sh RECOVERY.sh`)
tools/          a receita (`build.py`) e as ferramentas de cada degrau
tests/          testes sem o aparelho; `tools/ci.sh` roda os protegidos
analysis/       varreduras, disassembly, mapas
assets/         logo e ícones do OpenPod
docs/           o entendimento do firmware, as fichas e as decisões
```

O que saiu na limpeza de 2026-11-14 está em `../OpenPod-arquivo-2026-11-14/`,
fora do projeto: kits antigos, imagens de trabalho velhas, projetos anteriores
e ferramentas da linha antiga. O que estava no git também continua no histórico.

## Como a imagem é construída

A imagem sai de uma **receita declarada**, sempre a partir do ORIGINAL:

```sh
python3 tools/build.py --receita reload_2.0 --saida <imagem>
python3 tools/patch_versao.py --em 0x1A4F00 ...     # carimbo da versão
python3 tools/gera_versao.py ...                    # kit (cabo + .up + Windows), base ORIGINAL
sh tools/ci.sh                                      # antes de dizer "terminei"
```

O `build.py` confere o sha do ORIGINAL, roda cada passo num arquivo próprio,
impõe o mapa de lotes da área livre e é determinístico: a mesma receita dá a
mesma imagem, byte a byte.

## As regras que custaram caro

- **O firmware ORIGINAL nunca é modificado.**
- **Só o decisor grava no aparelho e só ele autoriza publicar** (o "pode").
- **`write_flash` grava a partir do byte 0 do arquivo, e nunca recebe um `.up`.**
- **O setor `0x00D000`, o bootloader e a PSMP não são gravados.**
- **Firmware de outro aparelho nunca é gravado** (o B27 trocou até o bootloader).
- **A ViewTask não toca em arquivo:** abrir arquivo nela trava o aparelho (fichas 011 a 014).
- **Todo destino de `bx`/`blx` leva o bit Thumb.**
- **Nada de hipótese apresentada como fato:** CONFIRMADO, PROVÁVEL ou HIPÓTESE.

## Hardware

```
Iigenai GN-438      firmware yp3_2.0.43      USB 301a:2801
flash 2 MiB         SoC SL6801              XIP em 0x00C00000
display 128×160     LVGL v8, FreeRTOS       sem cripto, sem compressão
modo download       VOLUME↓ + RESET, na ROM de máscara: sempre recuperável
```
