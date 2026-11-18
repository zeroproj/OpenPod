# OpenPod — OpenPod Reload 3.1c

A new firmware for players with the **Smartlink SL6801** chip: clean, modern
look, focused on music, built from the stock system (`yp3_2.0.43`).
Compatible with the **Ligenai GN-438** (tested) and the **GN-408** (tested by users).

*Um firmware novo para players com chip **Smartlink SL6801**: visual limpo e moderno, foco em música, feito a partir do sistema de fábrica. Compatível com o **Ligenai GN-438** (testado) e o **GN-408** (testado por usuários).*

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
OpenPod_OpenPodReload3.1c.up       the firmware / o firmware
windows/               Windows -> start here / comece aqui
  LEIA-ME.txt
cabo/                  USB cable path, used by install.sh
  flash_OpenPod_OpenPodReload3.1c.sh
  setores/             66 sector files / arquivos de setor
```

You do not need to open `cabo/` by hand — `install.sh` does it.

*Não precisa abrir a pasta `cabo/` na mão — o `install.sh` faz isso.*

---

## New in 3.1c / Novo na 3.1c

**Controls fixed for the GN-438.** The player has no Up/Down key; the
games now use the buttons it really has. Prev/Next move, M is the extra
action, Play confirms, Back twice returns to the menu.

*Controles corrigidos para o GN-438. O aparelho não tem cima/baixo; os
jogos agora usam os botões que ele tem de verdade. ⏮/⏭ movem, M é a ação
extra, Play confirma e Back duas vezes volta ao menu.*

**Applications menu.** Home icon 5 (Aplicativos) keeps Alarm and Images
and adds three games. The order is Alarm, Images, Flutter, Mp3tris,
Cobrinha.

*Menu Aplicativos. O ícone 5 da home (Aplicativos) mantém Despertador e
Imagem e acrescenta três jogos. A ordem é Despertador, Imagem, Flutter,
Mp3tris, Cobrinha.*

**Flutter.** A side-scrolling flying game: guide a small bird through gaps
between crystal pillars. M or Play flaps; Back twice in a row returns to
the menu. *No sound.*

*Flutter. Um jogo de voo com rolagem lateral: conduza um pássaro pequeno
pelos vãos entre pilares de cristal. M ou Play bate as asas; Back duas
vezes seguidas volta ao menu. Sem som.*

**Mp3tris.** A falling-block puzzle: move and rotate the pieces, clear
lines, and keep the stack under control. ⏮/⏭ move (holding repeats), M
rotates, Play drops one row, holding M drops the piece to the bottom.
Back twice returns to the menu. *No sound.*

*Mp3tris. Um quebra-cabeça de blocos que caem: mova e gire as peças, limpe
linhas e mantenha a pilha sob controle. ⏮/⏭ movem (segurar repete), M
gira, Play desce uma linha, segurar M derruba a peça até o fundo. Back
duas vezes volta ao menu. Sem som.*

**Cobrinha (Snake).** A classic snake game: steer with ⏮/⏭, eat the red
food, grow, and speed up. Hitting the wall or yourself ends the round.
Play starts, pauses and resumes (and restarts after game over); Back
twice returns to the menu. The name and the messages follow the player
language: **Cobrinha** in Portuguese and **Snake** in the others.
*No sound.*

*Cobrinha. O clássico jogo da cobrinha: vire com ⏮/⏭, coma a comida
vermelha, cresça e acelere. Bater na parede ou nela mesma termina a
rodada. Play começa, pausa e continua (e recomeça no fim de jogo); Back
duas vezes volta ao menu. O nome e as mensagens seguem o idioma do
aparelho: **Cobrinha** em português e **Snake** nos outros idiomas.
Sem som.*

**Version screen.** `Settings → Information` shows **Reload 3.1c**.

*Tela de versão. `Configurar → Informações` mostra **Reload 3.1c**.*

The games are silent in this release. Music, if it is playing, is not
stopped when an app opens.

*Os jogos são silenciosos nesta versão. A música, se estiver tocando, não é
parada quando um app abre.*

---

## Credits / Créditos

The in-app overlay SDK and the three games are based on the
**SL6801_player SDK by Dmitry Brant**, used with permission:
<https://github.com/dbrant/SL6801_player>.

*O SDK de overlay e os três jogos são baseados no **SL6801_player SDK, de
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

- The games have no sound in 3.1c.
- Music is not stopped when an app or game opens (decision for this
  release). Test with music playing and note whether animation or audio
  stutters.

*Os jogos não têm som na 3.1c.
A música não é parada quando um app ou jogo abre (decisão desta versão).
Teste com música tocando e anote se a animação ou o áudio engasga.*
