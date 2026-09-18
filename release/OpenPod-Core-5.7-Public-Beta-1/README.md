# OpenPod — Beta 1

An iPod nano–inspired interface for the **Iigenai GN-438** player
(Smartlink/YP3, stock firmware `yp3_2.0.43`).

*Uma interface inspirada no iPod nano para o player **Iigenai GN-438**.*

> ⚠️ **Beta.** Tested on one device only.
> *Testada em um único aparelho.*

---

## Install / Instalar

```sh
sh install.sh
```

It asks for your language first, then walks you through it. The
flashing script speaks the same language.

*Ele pergunta o idioma antes de tudo e conduz o resto. O script de
gravação fala a mesma língua.*

---

## What changes / O que muda

| | Stock / Fábrica | OpenPod |
|---|---|---|
| Home / Tela inicial | 3×3 grid, 9 icons | list of 4 — Music, Video, Extras, Settings |
| Extras | — | Recording, Radio, eBook, Images, Bluetooth, Folders |
| Selection / Seleção | text colour | full-width blue bar |
| Top bar / Faixa | height varied per screen | 16 px everywhere, clock + title |
| Row height / Altura de linha | 15 px / 22 px | 16 px everywhere |
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

The cable needs the flashing tool, which is **not bundled**: a separate
project by **Ilya Kurdyukov**, with no license that allows redistribution.

*O cabo precisa da ferramenta de gravação, que **não vem junto**.*

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
| **Battery / Bateria** | shell is silver; the inner level is not green yet |

---

## Credits / Créditos

- **iPod nano** is an Apple trademark. This project uses **no Apple code
  or artwork** — it reproduces interface principles only.
- Flashing tool: **smartlink_flash**, by **Ilya Kurdyukov**.
- Visual direction references the **NanoClone** theme by **Billy Blair**
  (CC-BY-SA 3.0). Only **measured colour values** were used —
  no pixels were copied.
