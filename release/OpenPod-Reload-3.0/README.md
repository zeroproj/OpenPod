# OpenPod — OpenPod Reload 3.0

A new firmware for players with the **Smartlink SL6801** chip: clean, modern
look, focused on music, built from the stock system (`yp3_2.0.43`).
Compatible with the **Ligenai GN-438** (tested) and the **GN-408** (tested by users).

*Um firmware novo para players com chip **Smartlink SL6801**: visual limpo e moderno, foco em música, feito a partir do sistema de fábrica. Compatível com o **Ligenai GN-438** (testado) e o **GN-408** (testado por usuários).*

> ⚠️ **Beta.** Tested on the Ligenai GN-438; tested by users on the GN-408.
> *Testada no Ligenai GN-438; testada por usuários no GN-408.*

---

## Install / Instalar

### Windows

Open **`windows/LEIA-ME.txt`** and follow it. Everything you need is in
the `windows/` folder, including the manufacturer's flashing tool.

*Abra **`windows/LEIA-ME.txt`** e siga. Está tudo na pasta `windows/`,
inclusive o gravador do fabricante.*

This is the **recommended path**, and you only need it **once**: with
OpenPod installed the player gets `Settings → Update via SD`, so future
versions go in by card, with no computer.

*É o **caminho recomendado**, e só é preciso **uma vez**: com o OpenPod
instalado o aparelho passa a ter `Configurar → Atualizar por SD`.*

> ⚠️ **Your settings are erased** (volume, EQ, language). Music on the
> card is untouched.
>
> *⚠️ **Suas configurações são apagadas.** A música no cartão não é tocada.*

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
README.md              you are here / voce esta aqui
install.sh             Linux / macOS  -> start here / comece aqui
OpenPod_OpenPodReload3.0.up       the firmware / o firmware
windows/               Windows -> start here / comece aqui
  LEIA-ME.txt
  FlashloaderSL-DEV-6.9.5.exe
cabo/                  USB cable path, used by install.sh
  flash_OpenPod_OpenPodReload3.0.sh
  setores/             58 sector files / arquivos de setor
```

You do not need to open `cabo/` by hand — `install.sh` does it.

*Nao precisa abrir a pasta `cabo/` na mao — o `install.sh` faz isso.*

> **Flashloader / Gravador:** o `.exe` do fabricante nao esta versionado
> neste repositorio (`firmware/VENDOR/` so tem os LEIA-ME). O kit nao foi
> publicado; antes de publicar, coloque o `FlashloaderSL-DEV-6.9.5.exe` em
> `windows/`. O resto da pasta ja esta pronto.
>
> *The manufacturer's `.exe` is not in this source tree. This kit has not
> been published; add `FlashloaderSL-DEV-6.9.5.exe` to `windows/` before
> publishing. The rest of the folder is ready.*

---

## New in 3.0 / Novo na 3.0: Apps menu

**Home icon 5 — formerly Images — is now Apps** (the Portuguese label is
**Aplicativos**, from the stock id 159). It opens a menu with Alarm,
Images and Dictionary. Images stays reachable; Dictionary needs
`0:/dict/` and shows an error without it. The other eight home icons keep
their factory destination. Press Esc from an item to return to Apps, and
Esc from Apps to return home.

*O icone 5 da home — antes Imagem — agora e Apps (o rotulo em portugues e
**Aplicativos**, do id 159 de fabrica). Ele abre um menu com Despertador,
Imagem e Dicionario. A Imagem continua acessivel; o Dicionario precisa de
`0:/dict/` e mostra erro sem ele. Os outros oito icones mantem o destino
de fabrica. Esc de um item volta ao Apps; Esc do Apps volta a home.*

---

## What changes / O que muda

| | Stock / Fábrica | OpenPod |
|---|---|---|
| Home / Tela inicial | 3×3 grid, 9 icons | list of 4 — Music, Video, Extras, Settings |
| Extras | — | Recording, Radio, eBook, Images, Bluetooth, Folders |
| Selection / Seleção | text colour | full-width blue bar |
| Top bar / Faixa | height varied per screen | 16 px everywhere, clock + title |
| Row height / Altura de linha | 15 px / 22 px | 16 px everywhere |
| Battery / Bateria | flat white glyph | silver shell, green level |
| Text / Textos | machine translation | revised Brazilian Portuguese |

These are **patches over the original firmware** — OpenPod modifies the
stock system, it does not replace it.

*São **patches sobre o firmware original** — o OpenPod modifica o sistema
de fábrica, não o substitui.*

---

## Requirements / Requisitos

The first install is **by USB cable**, because a stock GN-438 has no
`Settings → Update via SD`. OpenPod adds it, so every version after this
one goes in by card.

*A primeira instalação é **por cabo USB**, porque o GN-438 de fábrica não
tem `Configurar → Atualizar por SD`. O OpenPod passa a ter — então da
próxima versão em diante é pelo cartão.*

**Windows:** nothing to install by hand — the tool is in `windows/`.

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

| | |
|---|---|
| **Folders / Pastas** | opens and browses, but only goes back after entering a folder |

---

## Credits / Créditos

- Independent project, not affiliated with Smartlink, Shenju or the
  device maker. / Projeto independente, sem ligação com a Smartlink, a
  Shenju ou o fabricante do aparelho.
- Flashing tool (Linux/macOS): **smartlink_flash**, by **Ilya Kurdyukov**.
- Flashing tool (Windows): **Flashloader SL-DEV 6.9.5**, by **Shenju**,
  the chip maker. Redistributed unmodified, as a convenience. Not ours,
  and not part of OpenPod.
