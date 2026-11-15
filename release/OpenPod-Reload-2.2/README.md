# OpenPod — OpenPod Reload 2.2

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
OpenPod_OpenPodReload2.2.up       the firmware / o firmware
windows/               Windows -> start here / comece aqui
  LEIA-ME.txt
  FlashloaderSL-DEV-6.9.5.exe
cabo/                  USB cable path, used by install.sh
  flash_OpenPod_OpenPodReload2.2.sh
  setores/             changed sectors + rollback copies / setores alterados + volta
```

You do not need to open `cabo/` by hand — `install.sh` does it.

*Nao precisa abrir a pasta `cabo/` na mao — o `install.sh` faz isso.*

---

## New in 2.2 / Novo na 2.2: ícones escuros com símbolos coloridos

**Dark icons with coloured symbols.** The nine home icons now have a
near-black gradient, and each symbol keeps the light tone of its original
colour. The white rounded frame stays on the selected icon. Everything
else is the same as Reload 2.1.

*Ícones escuros com símbolos coloridos. Os nove ícones da home passam a
ter um degradê quase preto, e cada símbolo mantém o tom claro da sua cor
original. A moldura branca continua no ícone selecionado. O resto é igual
à Reload 2.1.*

## New in 2.1 / Novo na 2.1: ícones da tela inicial em grafite

**Home icons in graphite.** The nine home icons now use the same graphite
gradient, with the white rounded frame on the selected icon. Everything
else is the same as Reload 2.0.

*Ícones da tela inicial em grafite. Os nove ícones da home passam a usar o
mesmo degradê grafite, com a moldura branca no ícone selecionado. O resto é
igual à Reload 2.0.*

## New in 2.0 / Novo na 2.0

**Album art on Now Playing.** The cover is read from the MP3 tag
(embedded **baseline JPEG**) and appears without interrupting playback.
The rest is the same as Reload 1.0 RC6.

*Capa do álbum na tela Tocando Agora, lida da etiqueta do MP3
(**JPEG baseline** embutido), sem engasgar a música. O resto é igual à
Reload 1.0 RC6.*

- The cover changes when the track changes — including when the track
  ends and the next one starts automatically.

*A capa troca quando a faixa muda — inclusive no avanço automático, quando
a música acaba e a próxima começa sozinha.*

### Cover limitations / Limitações da capa

- Only **baseline JPEG** embedded in the MP3 tag. Progressive JPEG, PNG,
  no cover or no tag → **gray square**.
- Covers smaller than **56 px** → gray square.
- Grayscale JPEG shows; CMYK JPEG → gray square.

*Só **JPEG baseline** embutido na etiqueta do MP3. JPEG progressivo, PNG,
sem capa ou sem etiqueta → **quadrado cinza**. Capa menor que **56 px** →
cinza. JPEG em escala de cinza aparece; CMYK → cinza.*

---

## What changes / O que muda

| | Stock / Fábrica | OpenPod |
|---|---|---|
| Home / Tela inicial | 3×3 grid, icons with names | dark icons with coloured symbols, no names, centred grid, white rounded frame on the selected icon |
| Now Playing / Tocando Agora | no cover | album cover (64×64) from the MP3 tag |
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
