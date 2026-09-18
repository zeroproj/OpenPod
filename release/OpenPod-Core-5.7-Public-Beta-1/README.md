# OpenPod — Beta 1

An iPod nano–inspired interface for the **Iigenai GN-438** player
(Smartlink/YP3, stock firmware `yp3_2.0.43`).

*Uma interface inspirada no iPod nano para o player **Iigenai GN-438**.*

> ⚠️ **Beta.** Tested on one device only.
> *Testada em um único aparelho.*

---

## Install / Instalar

### Windows

Open **`windows/LEIA-ME.txt`** and follow it. Everything you need is in
the `windows/` folder, including the manufacturer's flashing tool.

*Abra **`windows/LEIA-ME.txt`** e siga. Está tudo na pasta `windows/`,
inclusive o gravador do fabricante.*

> ⚠️ **This path has not been tested by us yet.** The firmware file is
> verified byte for byte; the tool writing it is not. The guide says what
> to report back.
>
> *⚠️ **Este caminho ainda não foi testado por nós.***

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
OpenPod_Beta1.up       the firmware / o firmware
windows/               Windows -> start here / comece aqui
  LEIA-ME.txt
  FlashloaderSL-DEV-6.9.5.exe
cabo/                  USB cable path, used by install.sh
  flash_OpenPod_Beta1.sh
  setores/             88 sector files / arquivos de setor
```

You do not need to open `cabo/` by hand — `install.sh` does it.

*Nao precisa abrir a pasta `cabo/` na mao — o `install.sh` faz isso.*

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

Beta 1 installs **by USB cable**. The microSD route needs
`Settings → Update via SD`, which a stock GN-438 does not have — it only
works for a player that is already running OpenPod.

*A Beta 1 instala **por cabo USB**. O caminho do cartão precisa de
`Configurar → Atualizar por SD`, que o GN-438 de fábrica não tem.*

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

- **iPod nano** is an Apple trademark. This project uses **no Apple code
  or artwork** — it reproduces interface principles only.
- Flashing tool (Linux/macOS): **smartlink_flash**, by **Ilya Kurdyukov**.
- Flashing tool (Windows): **Flashloader SL-DEV 6.9.5**, by **Shenju**,
  the chip maker. Redistributed unmodified, as a convenience. Not ours,
  and not part of OpenPod.
- Visual direction references the **NanoClone** theme by **Billy Blair**
  (CC-BY-SA 3.0). Only **measured colour values** were used —
  no pixels were copied.
