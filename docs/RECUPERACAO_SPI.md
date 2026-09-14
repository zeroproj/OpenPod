# Recuperação do GN-438 por SPI — Raspberry Pi 3B + clipe SOIC8

> Rota escolhida depois que as rotas por USB e por cartão SD foram
> refutadas. Ver `docs/INCIDENTE_V028.md` §6.4.
>
> Hardware: **Raspberry Pi 3B** (GPIO 3,3 V nativo) + **clipe SOIC8**.
> Nenhum programador dedicado é necessário.

## 0. Regra de ouro

**Nunca conecte 5 V em nada.** A flash é 3,3 V. Use o pino 1 ou 17 do
header do Pi, jamais os pinos 2 e 4.

## 1. Preparar o Pi (pode ser feito antes do clipe chegar)

```bash
sudo raspi-config     # Interface Options -> SPI -> Enable
sudo reboot

sudo apt update && sudo apt install -y flashrom
ls -l /dev/spidev0.0  # tem que existir
flashrom --version
```

## 2. Identificar o chip

O chip de flash é um CI de 8 pernas perto do SoC, marcação tipo
`25Q16`, `25L16`, `P25Q16` etc. O ponto ou chanfro marca o **pino 1**.

Não é preciso decifrar a serigrafia: o próprio `flashrom` identifica o
chip ao sondar (passo 4). Mas confirme que o encapsulamento é **SOIC8**
(pernas visíveis dos lados). Se for WSON/USON (sem pernas, só contatos
embaixo), o clipe não prende e o caminho muda — avise antes de tentar.

## 3. Ligação

Numeração do SOIC8, com o pino 1 no canto do chanfro, anti-horário:

| pino da flash | sinal | pino FÍSICO do header do Pi |
|---|---|---|
| 1 | /CS   | **24** (CE0, GPIO8) |
| 2 | DO    | **21** (MISO, GPIO9) |
| 3 | /WP   | **17** (3,3 V) |
| 4 | GND   | **25** (GND) |
| 5 | DI    | **19** (MOSI, GPIO10) |
| 6 | CLK   | **23** (SCLK, GPIO11) |
| 7 | /HOLD | **17** (3,3 V) |
| 8 | VCC   | **1** (3,3 V) |

Pinos 3 e 7 vão os dois para 3,3 V — é o que libera escrita e impede o
chip de ficar em espera.

**Antes de prender o clipe:** desconecte a bateria do aparelho. Alimentar
a flash pelo clipe alimenta parte da placa junto, e isso é a causa mais
comum de leitura instável.

## 4. Sondar — leitura pura, risco zero

```bash
sudo flashrom -p linux_spi:dev=/dev/spidev0.0,spispeed=512
```

Sem operação, ele só detecta e reporta o chip. Se disser "No EEPROM/flash
device found", reposicione o clipe (é quase sempre contato ruim) e tente
de novo. Se detectar múltiplos candidatos, anote os nomes e pergunte
antes de seguir — escolher o errado pode dar escrita malformada.

## 5. Ler o estado atual — TRÊS vezes

```bash
sudo flashrom -p linux_spi:dev=/dev/spidev0.0,spispeed=512 -r dump1.bin
sudo flashrom -p linux_spi:dev=/dev/spidev0.0,spispeed=512 -r dump2.bin
sudo flashrom -p linux_spi:dev=/dev/spidev0.0,spispeed=512 -r dump3.bin
sha256sum dump1.bin dump2.bin dump3.bin
```

**Os três hashes têm que ser idênticos.** Se divergirem, o contato está
ruim ou a velocidade está alta demais — baixe para `spispeed=256` e
repita. **Não grave nada enquanto as três leituras não baterem.**

Cada dump tem que ter 2.097.152 bytes.

> Mande `dump1.bin` para análise antes de gravar. É ele que mostra o que
> realmente sobrou no setor `0x00D000` e fecha o incidente com dado em vez
> de suposição.

## 6. Gravar o original

```bash
sudo flashrom -p linux_spi:dev=/dev/spidev0.0,spispeed=512 \
              -w GN438_original.bin
```

O `flashrom` já apaga, grava e **verifica sozinho**. Espere ele terminar
sem interromper.

## 7. Conferir antes de fechar

```bash
sudo flashrom -p linux_spi:dev=/dev/spidev0.0,spispeed=512 -r depois.bin
sha256sum depois.bin
# tem que dar exatamente:
# b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f
```

Só com esse hash batendo o aparelho está restaurado ao estado de fábrica,
bit a bit. Tire o clipe, reconecte a bateria, ligue.

## 8. Se a leitura não estabilizar

Sinal de que a placa está drenando o barramento. Em ordem de esforço:

1. baixar `spispeed` para 256 ou 128;
2. garantir bateria desconectada;
3. segurar o SoC em reset durante a operação (requer achar o pino);
4. dessoldar a flash, gravar fora da placa, ressoldar.

Chegando no 3, pare e documente antes de continuar.
