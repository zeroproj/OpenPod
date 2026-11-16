# OpenPod — OpenPod Reload 2.2.1

A new firmware for the **Iigenai GN-438** player: clean, modern look,
focused on music, built from the stock system (`yp3_2.0.43`).

*Um firmware novo para o **Iigenai GN-438**: visual limpo e moderno, foco em música, feito a partir do sistema de fábrica.*

> ⚠️ **Stable release, tested on one device only.**
> *Versão estável, testada em um único aparelho.*

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
OpenPod_OpenPodReload2.2.1.up       the firmware / o firmware
windows/               Windows -> start here / comece aqui
  LEIA-ME.txt
  FlashloaderSL-DEV-6.9.5.exe
cabo/                  USB cable path, used by install.sh
  flash_OpenPod_OpenPodReload2.2.1.sh
  setores/             88 sector files / arquivos de setor
```

You do not need to open `cabo/` by hand — `install.sh` does it.

*Nao precisa abrir a pasta `cabo/` na mao — o `install.sh` faz isso.*

---

## New in 2.2.1 / Novo na 2.2.1: cover size limit

**A cover that is too large no longer freezes the player.** Before
decoding an embedded cover, OpenPod now checks its size: an image wider
or taller than **1000 px**, or larger than **512 KiB**, is skipped. The
player shows the grey cover and keeps playing. Reload 2.2 tried to decode
anything, and a 1500 px / 842 KiB cover froze the device. Everything else
is the same as Reload 2.2.

*Uma capa grande demais não trava mais o aparelho. Antes de decodificar
a capa embutida, o OpenPod confere o tamanho: imagem com mais de **1000
px** de largura ou altura, ou com mais de **512 KiB**, é ignorada. O
aparelho mostra a capa cinza e continua tocando. A Reload 2.2 tentava
decodificar tudo, e uma capa de 1500 px / 842 KiB travava o aparelho. O
resto é igual à Reload 2.2.*

**Tip:** shrink embedded covers to about **300 px** with a tag editor
(such as Mp3tag). They load instantly and take far less space.

*Dica: reduza as capas embutidas para cerca de **300 px** com um editor
de etiquetas (como o Mp3tag). Elas carregam na hora e ocupam bem menos
espaço.*

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
- Visual direction references the **NanoClone** theme by **Billy Blair**
  (CC-BY-SA 3.0). Only **measured colour values** were used —
  no pixels were copied.
