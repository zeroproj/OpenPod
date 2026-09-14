# OpenPod

Transformar o **Iigenai GN-438** — um player YP3/Smartlink de baixo custo
— num player com a experiência de um iPod, progressivamente, sem
reescrever o firmware do zero.

> **Estado em 2026-09-14:** projeto reiniciado como **OpenPod Core**. O
> aparelho está com o **firmware de fábrica**, por decisão, para a nova
> linha começar de uma base conhecida.
>
> Entrada obrigatória: **[`docs/RESTART_PLAN.md`](docs/RESTART_PLAN.md)**.

---

## Por onde começar

| quero... | leia |
|---|---|
| entender o estado e o plano | `docs/RESTART_PLAN.md` |
| saber o que está no aparelho | `docs/ESTADO_ATUAL.md` |
| as regras do projeto | `CLAUDE.md` |
| voltar o aparelho ao de fábrica | `recovery/VOLTAR_AO_ORIGINAL.md` |
| como gravar, e o que já custou caro | `docs/PROTOCOLO_GRAVACAO.md` |
| o firmware por dentro | `docs/FIRMWARE_ANALYSIS.md`, `docs/ARQUITETURA.md` |
| a referência visual | `docs/PROJETO_MARTE.md`, `docs/OpenPod_Design_System.md` |

---

## Estrutura

```
firmware/
  ORIGINAL/     GN438_original.bin — sagrado, modo 444, sha b7cd5eb9…
  WORKING/      a cadeia v001..v101 e as saídas de build
  RELEASE/      os kits publicados: OpenPod 1.4 .. 3.1, v044
  VENDOR/       Flashloader SL-DEV oficial da Shenju
  READBACK/     leituras feitas do aparelho

recovery/       O RECOVERY OFICIAL — autossuficiente, copiável inteiro
                `sudo sh RECOVERY.sh`, validado em hardware

update/         pacotes .up para atualizar pelo cartão SD

tools/          a receita e as ferramentas. `build.py` é o centro
tests/          testes que não falam com o aparelho
experiments/    diagnósticos e sondas — nunca viram release
patches/        patches avulsos
analysis/       varreduras, disassembly, mapas
extracted/      gráficos, fontes e recursos extraídos
assets/         a logo do OpenPod e material de referência
marte/          o estudo NanoClone: paleta, ícones adaptados, mockups
docs/           46 documentos; `reports/` guarda os relatórios longos
historico/      kits e releases antigos, e o material da recuperação
```

---

## Como a imagem é construída

Não é mais uma corrente de patches aplicados à mão. É uma **receita
declarada**:

```sh
python3 tools/build.py --receita core1.0   --saida firmware/WORKING/core10.bin
python3 tools/build.py --receita interface --saida firmware/WORKING/iface.bin
python3 tools/build.py --so-lista
```

O `build.py` confere o sha do ORIGINAL antes de começar, roda cada passo
num arquivo próprio, impõe um **mapa de endereços da área livre** (cada
ferramenta recebe `--em` e é recusada se escrever fora do seu lote), e é
**determinístico** — a mesma receita dá a mesma imagem, byte a byte.

Depois:

```sh
python3 tools/validate_firmware.py <imagem>     # estrutura, CRCs, partições
python3 tools/audita_chrome.py     <imagem>     # divergências de tema
python3 tools/gera_up.py --in <imagem> --out <pacote.up>
python3 tools/make_install_kit.py  --base ... --alvo ...   # kit de setores
```

---

## As regras que custaram caro

Cada uma tem um preço já pago; estão inteiras em
`docs/PROTOCOLO_GRAVACAO.md`.

- **O firmware ORIGINAL nunca é modificado.** É a âncora de tudo.
- **`write_flash` grava a partir do byte 0 do arquivo.** O 2º argumento é
  sempre `0`. Ler isso errado corrompeu a tabela de partições e brickou o
  primeiro aparelho.
- **Nunca passe um `.up` para o `write_flash`.** O `.up` é para o cartão
  SD, onde o bootloader interpreta o cabeçalho.
- **O setor `0x00D000` não é gravado.** O CRC da FIRM não é verificado
  por nada — confirmado no aparelho.
- **Conferência é por releitura do aparelho**, nunca por hash de arquivo
  no PC.
- **Aparência se decide pela referência, não por gosto.** Sempre o Marte
  — `marte/mockups/marte_completo.png` e `marte/paleta/nanoclone.json` —
  ou os próprios objetos do NanoClone em `marte/adaptado/`. A regra e o
  porquê em [`docs/MARTE_ALVO.md`](docs/MARTE_ALVO.md) §0.
- **Nada de hipótese apresentada como fato.** Cada afirmação carrega
  classe: CONFIRMADO, PROVÁVEL, HIPÓTESE, DESCONHECIDO.

---

## Hardware

```
Iigenai GN-438      firmware yp3_2.0.43      USB 301a:2801
flash 2 MiB         SoC SL6801              XIP em 0x00C00000
display 128×160     LVGL v8                 sem cripto, sem compressão
modo download       301a:2800, na ROM de máscara — sempre recuperável
```

---

## Crédito

A referência visual vem do tema **NanoClone**, de Billy Blair, sob
CC BY-SA 3.0. Detalhes e obrigações em [`ATRIBUICAO.md`](ATRIBUICAO.md).
