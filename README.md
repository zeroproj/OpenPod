# OpenPod — Reload Alpha

**Site:** https://zeroproj.github.io/OpenPod/ — fonte em `docs/index.html`.
Para publicar: *Settings → Pages → Source: main, pasta `/docs`*. O `.nojekyll`
ao lado impede o Jekyll de tentar processar os `.md` da análise.

Melhorar o **Iigenai GN-438** — um player YP3/Smartlink de baixo custo
— mantendo o que já funciona e corrigindo o que incomoda, sem reescrever
o firmware do zero e sem copiar outro aparelho.

> **Estado em 2026-09-23:** **OpenPod Reload Alpha 0.1** — reset limpo no
> ORIGINAL (`yp3_2.0.43`), 3 mudanças só: fundo preto em todas as telas,
> barra principal Data · OpenPod · Bateria e atualização por cartão SD.
> Receita `reload_alpha` em `tools/build.py`. Detalhes em
> [`docs/RELOAD_ALPHA.md`](docs/RELOAD_ALPHA.md).
>
> A linha Core (1.0.1, Saturno, Marte) fica como referência histórica —
> não é base para a Alpha.
>
> Entrada obrigatória: **[`docs/ESTADO_ATUAL.md`](docs/ESTADO_ATUAL.md)**.

---

> **Assumindo o projeto?** Leia **[`CONTINUAR.md`](CONTINUAR.md)** primeiro.
> Ele tem o estado, a primeira coisa a fazer, o conserto que está pronto
> para escrever e as três lições que custaram caro.

## Por onde começar

| quero... | leia |
|---|---|
| entender o estado e o que está no aparelho | `docs/ESTADO_ATUAL.md` |
| as regras do projeto | `CLAUDE.md` |
| voltar o aparelho ao de fábrica | `recovery/VOLTAR_AO_ORIGINAL.md` |
| como gravar, e o que já custou caro | `docs/PROTOCOLO_GRAVACAO.md` |
| o firmware por dentro | `docs/FIRMWARE_ANALYSIS.md`, `docs/ARQUITETURA.md` |
| a proposta da Reload Alpha | `docs/RELOAD_ALPHA.md` |
| a referência visual anterior | `docs/PROJETO_MARTE.md`, `docs/OpenPod_Design_System.md` |

---

## Estrutura

```
firmware/
  ORIGINAL/     GN438_original.bin — sagrado, modo 444, sha b7cd5eb9…
  WORKING/      imagens de trabalho (GN438_reload_alpha_v001.bin)
  RELEASE/      kits históricos (Core 1.0.1)
  release/      pacotes publicados (Reload Alpha 0.1)
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
marte/          estudo anterior NanoClone — histórico, não é base da Alpha
docs/           o entendimento do firmware; `RELOAD_ALPHA.md` é a entrada atual
```

---

## Como a imagem é construída

Não é mais uma corrente de patches aplicados à mão. É uma **receita
declarada**:

```sh
python3 tools/build.py --receita reload_alpha --saida firmware/WORKING/GN438_reload_alpha_v001.bin
python3 tools/build.py --so-lista
```

**Receita atual: `reload_alpha`, 5 passos** (update SD + 3 fundos + barra).
A `core1.0` segue existindo como referência. Ver `docs/RELOAD_ALPHA.md`.

O `build.py` confere o sha do ORIGINAL antes de começar, roda cada passo
num arquivo próprio, impõe um **mapa de endereços da área livre** (cada
ferramenta recebe `--em` e é recusada se escrever fora do seu lote), e é
**determinístico** — a mesma receita dá a mesma imagem, byte a byte.

Depois:

```sh
python3 tools/validate_firmware.py <imagem>     # estrutura, CRCs, partições
python3 tools/gera_up.py --in <imagem> --out <pacote.up>
python3 tools/make_install_kit.py  --base firmware/ORIGINAL/GN438_original.bin --alvo <imagem> --versao "OpenPod Reload Alpha 0.1" --saida release/OpenPod-Reload-Alpha-0.1
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
- **Aparência se decide pelo que melhora o uso, não por gosto.** Na Reload
  Alpha a referência é o próprio firmware: fundo preto resolve fresta branca,
  barra Data·OpenPod·Bateria organiza o topo. Sem copiar outro aparelho.
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

Reload Alpha não copia interface de outro aparelho. O estudo anterior
NanoClone (Billy Blair, CC BY-SA 3.0) fica como histórico em `marte/` e
`ATRIBUICAO.md` — não é base da Alpha.
