# OpenPod — OpenPod Reload 3.1a Diag

A new firmware for players with the **Smartlink SL6801** chip: clean, modern
look, focused on music, built from the stock system (`yp3_2.0.43`).
Compatible with the **Ligenai GN-438** (tested) and the **GN-408** (tested by users).

*Um firmware novo para players com chip **Smartlink SL6801**: visual limpo e moderno, foco em música, feito a partir do sistema de fábrica. Compatível com o **Ligenai GN-438** (testado) e o **GN-408** (testado por usuários).*

**Diagnostic build.** This release checks the Applications menu and the key
test only. The games are in **OpenPod Reload 3.1b**.

*Build de diagnóstico. Esta versão serve para conferir o menu Aplicativos e o
teste de teclas. Os jogos estão na **OpenPod Reload 3.1b**.*

---

## Install / Instalar

### Windows

Open **`windows/LEIA-ME.txt`** and follow it. The manufacturer's flashing
tool (`FlashloaderSL-DEV-6.9.5.exe`) is placed in `windows/` by the
coordination before publishing.

*Abra **`windows/LEIA-ME.txt`** e siga. O gravador do fabricante
(`FlashloaderSL-DEV-6.9.5.exe`) é colocado em `windows/` pela coordenação
antes da publicação.*

This is the **recommended path**, and you only need it **once**: with
OpenPod installed the player gets `Settings → Update via SD`, so future
versions go in by card, with no computer.

*É o **caminho recomendado**, e só é preciso **uma vez**: com o OpenPod
instalado o aparelho passa a ter `Configurar → Atualizar por SD`.*

> **Your settings are erased** (volume, EQ, language). Music on the
> card is untouched.
>
> *Suas configurações são apagadas (volume, EQ, idioma). A música no
> cartão não é tocada.*

### Linux / macOS

```sh
sh install.sh
```

It asks for your language first, then walks you through it. The
flashing script speaks the same language.

*Ele pergunta o idioma antes de tudo e conduz o resto. O script de
gravação fala a mesma língua.*

---

## What is in here / O que tem aqui

```text
README.md              you are here / você está aqui
install.sh             Linux / macOS  -> start here / comece aqui
OpenPod_OpenPodReload3.1aDiag.up   the firmware / o firmware
windows/               Windows -> start here / comece aqui
  LEIA-ME.txt
cabo/                  USB cable path, used by install.sh
  flash_OpenPod_OpenPodReload3.1aDiag.sh
  setores/             62 sector files / arquivos de setor
```

You do not need to open `cabo/` by hand — `install.sh` does it.

*Não precisa abrir a pasta `cabo/` na mão — o `install.sh` faz isso.*

---

## New in 3.1 / Novo na 3.1

**Applications menu.** Home icon 5 (Aplicativos) keeps Alarm and Images and
adds a key test as the third row. The menu order is Alarm, Images, Key test.

*Menu Aplicativos. O ícone 5 da home (Aplicativos) mantém Despertador e
Imagem e acrescenta o teste de teclas como terceira linha. A ordem é
Despertador, Imagem, Teste de teclas.*

**Key test.** It shows the code of each button on screen. Esc, or Back twice
in a row, returns to the menu.

*Teste de teclas. Mostra na tela o código de cada botão. Esc, ou Back duas
vezes seguidas, volta ao menu.*

**Version screen.** `Settings → Information` shows **Reload 3.1a diag**.

*Tela de versão. `Configurar → Informações` mostra **Reload 3.1a diag**.*

This build has no games and no game sound.

*Esta versão não tem jogos nem som nos jogos.*

---

## Credits / Créditos

The in-app overlay SDK used by this release is based on the
**SL6801_player SDK by Dmitry Brant**, used with permission:
<https://github.com/dbrant/SL6801_player>.

*O SDK de overlay usado nesta versão é baseado no **SL6801_player SDK, de
Dmitry Brant**, usado com permissão: <https://github.com/dbrant/SL6801_player>.*

The firmware is a set of patches over the stock system. It does not replace
the stock firmware.

*O firmware é um conjunto de patches sobre o sistema de fábrica. Ele não
substitui o firmware original.*

---

## Requirements / Requisitos

The first install is **by USB cable**, because a stock GN-438 has no
`Settings → Update via SD`. OpenPod adds it, so every version after this
one goes in by card.

*A primeira instalação é **por cabo USB**, porque o GN-438 de fábrica não
tem `Configurar → Atualizar por SD`. O OpenPod passa a ter — então da
próxima versão em diante é pelo cartão.*

**Windows:** the tool is in `windows/` after the coordination adds it.

**Linux / macOS:** needs `smtlink_dump`, which is **not bundled**: a
separate project by **Ilya Kurdyukov**, with no license that allows
redistribution.

*Linux/macOS: precisa do `smtlink_dump`, que **não vem junto**.*

```sh
git clone https://github.com/ilyakurdyukov/smartlink_flash
cd smartlink_flash && make
```

Linux: `libusb-1.0-dev` · macOS: `brew install libusb`

---

## Risks / Riscos

**Not touched / Não é tocado:** bootloader, settings area, partition table.

**Can go wrong / Pode dar errado:** power loss during flashing; a
charge-only USB cable (the most common mistake).

**If it will not boot / Se não ligar:** the chip ROM flashing mode is
still available — `USB → hold VOLUME → press RESET`. It runs before any
firmware.

---

## Known issues / Problemas conhecidos

- This is a diagnostic build; the games are not included.
- No game sound in 3.1. Music, if playing, is not stopped when an app
  opens (decision for this release).

*Esta é uma versão de diagnóstico; os jogos não estão incluídos.
Não há som nos jogos na 3.1. A música, se estiver tocando, não é parada
quando um app abre (decisão desta versão).*
