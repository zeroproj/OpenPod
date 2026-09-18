# OpenPod — Beta 1

Uma interface inspirada no **iPod nano 2G** para o player **Iigenai
GN-438** (Smartlink/YP3, firmware `yp3_2.0.43`).

> ⚠️ **Beta.** Funciona no aparelho do autor. Não foi testada em outros.
> Leia a seção **Riscos** antes de gravar.

---

## Comece por aqui

```sh
sh instalar.sh
```

Ele pergunta como você quer instalar e conduz o resto. Se preferir fazer
à mão, os dois caminhos estão descritos abaixo.

---

## O que muda em relação ao firmware de fábrica

| | Antes | Agora |
|---|---|---|
| Tela inicial | grade 3×3 com 9 ícones | **lista de 4 itens**: Música, Vídeo, Extras, Configurar |
| Extras | não existia | submenu com Gravação, Rádio, Livro digital, Imagem, Bluetooth, Pastas |
| Seleção | cor de texto | **barra azul** de borda a borda |
| Faixa superior | altura variando por tela | **16 px em todas**, com relógio e título |
| Altura de linha | 15 px na home, 22 px nas outras | **16 px em todas** |
| Textos | tradução automática | **português do Brasil revisado** |
| Bateria | glifo branco | casca prateada |

Tudo isso são **patches sobre o firmware original** — o OpenPod não
substitui o sistema, ele o modifica.

---

## Caminho 1 — pelo cartão microSD (recomendado)

Serve se o aparelho liga e você chega em Configurar.

1. Copie `OpenPod_Beta1.up` para a **raiz** do cartão, com o nome
   `update.up`
2. `Configurar` → `Atualizar por SD` → `Sim`
3. Não desligue nem tire o cartão durante o processo
4. Ao reiniciar, **apague o `update.up`** do cartão
5. Confira em `Configurar` → `Informações`: deve dizer `OpenPod Core 5.7`

---

## Caminho 2 — por cabo USB

Serve se o aparelho não liga, travou, ou está no firmware de fábrica sem
a opção de atualizar por SD.

### A ferramenta não vem junto

O gravador é o **smartlink_flash**, de **Ilya Kurdyukov**:

```sh
git clone https://github.com/ilyakurdyukov/smartlink_flash
cd smartlink_flash && make
```

Ele não é redistribuído aqui porque **não traz arquivo de licença** —
sem concessão explícita, não temos direito de incluí-lo. Baixe da fonte.

Precisa de `libusb-1.0-dev` (Linux) ou `brew install libusb` (macOS).

### Modo de gravação

```text
USB conectado  →  SEGURE VOLUME (↓)  →  aperte RESET  →  solte
```

A tela fica **apagada**. É o esperado. Esse modo vive na ROM do chip e
roda antes de qualquer firmware — funciona mesmo com o aparelho
destruído.

---

## Riscos

**O que o instalador NÃO toca:**
- o bootloader (`0x000000`–`0x00D000`)
- a área de configuração (PSMP)
- a tabela de partições

**O que pode dar errado:**
- falta de energia durante a gravação
- cabo USB só de carga (o erro mais comum)

**Se o aparelho não ligar depois:** o modo de gravação continua
disponível pela ROM. O firmware de fábrica está preservado no
repositório do projeto, em `recovery/`.

---

## O que ainda não funciona

| | |
|---|---|
| **Pastas** | abre e navega, mas só volta depois de entrar numa pasta |
| **Bateria** | a casca é prateada; o miolo ainda não fica verde |
| **Rádio pelo Extras** | funciona, mas foi pouco testado |

Detalhes em `docs/PASTAS_ABERTO.md` e `docs/BATERIA_VERDE_ABERTO.md`.

---

## Arquivos desta pasta

| | |
|---|---|
| `instalar.sh` | **o instalador** — comece por ele |
| `OpenPod_Beta1.up` | a imagem, para o caminho do cartão |
| `flash_OpenPod_Beta1.sh` | a gravação por cabo |
| `OpenPod_Beta1_*.bin` | os setores, usados pelo script de cabo |
| `base_*.bin` | os mesmos setores **de fábrica**, para reverter |
| `diag.sh` | diagnóstico, só leitura |
| `recovery_check_linux.sh` | confere a ferramenta, só leitura |

---

## Créditos

- **iPod nano** é marca da Apple. Este projeto **não usa código nem
  arte da Apple** — só reproduz princípios de interface.
- O gravador `smartlink_flash` é de **Ilya Kurdyukov**.
- A direção visual toma como referência o tema **NanoClone**, de
  **Billy Blair** (CC-BY-SA 3.0). Até esta versão, **apenas cores
  medidas** foram usadas — nenhum pixel foi copiado.
