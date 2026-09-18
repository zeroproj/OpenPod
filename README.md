# OpenPod

**Site:** https://zeroproj.github.io/OpenPod/ — fonte em `docs/index.html`.
Para publicar: *Settings → Pages → Source: main, pasta `/docs`*. O `.nojekyll`
ao lado impede o Jekyll de tentar processar os `.md` da análise.

Transformar o **Iigenai GN-438** — um player YP3/Smartlink de baixo custo
— num player com a experiência de um iPod, progressivamente, sem
reescrever o firmware do zero.

> **Estado em 2026-09-14:** o aparelho está na **OpenPod Core 1.0.1**, a
> única versão STABLE. A linha 2.x (Saturno, chrome, Marte-paleta,
> carcaça) foi **removida** neste dia, a pedido do mantenedor: ela
> acoplava a barra superior a tudo o mais, e mudanças pedidas vinham com
> carona não pedida.
>
> **A referência é a Core 1.0.1 e o que foi desmontado e entendido do
> firmware.** Nada de versão anterior serve como base.
>
> Entrada obrigatória: **[`docs/ESTADO_ATUAL.md`](docs/ESTADO_ATUAL.md)**.

---

## Por onde começar

| quero... | leia |
|---|---|
| entender o estado e o que está no aparelho | `docs/ESTADO_ATUAL.md` |
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
  WORKING/      a cópia de trabalho e a imagem da Core 1.0.1
  RELEASE/      o único kit publicado: OpenPod Core 1.0.1
  VENDOR/       Flashloader SL-DEV oficial da Shenju
  READBACK/     leituras feitas do aparelho

recovery/       O RECOVERY OFICIAL — autossuficiente, copiável inteiro
                `sudo sh RECOVERY.sh`, validado em hardware

update/         pacotes .up para atualizar pelo cartão SD

tools/          a receita e as ferramentas. `build.py` é o centro
tests/          testes que não falam com o aparelho
patches/        patches avulsos
analysis/       varreduras, disassembly, mapas
extracted/      gráficos, fontes e recursos extraídos
assets/         a logo do OpenPod e material de referência
marte/          o estudo NanoClone: paleta, ícones adaptados, mockups
                — A BASE VISUAL do projeto
docs/           o entendimento do firmware; `reports/` guarda os longos
```

---

## Como a imagem é construída

Não é mais uma corrente de patches aplicados à mão. É uma **receita
declarada**:

```sh
python3 tools/build.py --receita core1.0 --saida firmware/WORKING/core101.bin
python3 tools/build.py --so-lista
```

**Existe UMA receita, `core1.0`, de seis passos.** As receitas 2.x foram
removidas em 2026-09-14 — ver `docs/ESTADO_ATUAL.md` §3.

O `build.py` confere o sha do ORIGINAL antes de começar, roda cada passo
num arquivo próprio, impõe um **mapa de endereços da área livre** (cada
ferramenta recebe `--em` e é recusada se escrever fora do seu lote), e é
**determinístico** — a mesma receita dá a mesma imagem, byte a byte.

Depois:

```sh
python3 tools/validate_firmware.py <imagem>     # estrutura, CRCs, partições
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
