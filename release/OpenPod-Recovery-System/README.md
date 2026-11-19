# OpenPod Recovery System (ORS)

**The stock firmware of the Ligenai GN-438 (`yp3_2.0.43`), with one addition: `Settings → Update via SD`.**
Use it to go back to the original look and features **without losing the easy way back**: to return to OpenPod
later, you only need the SD card.

*O firmware de fábrica do Ligenai GN-438 (`yp3_2.0.43`), com uma única mudança: `Configurar → Atualizar por SD`.
Serve para voltar ao visual e às funções originais **sem perder o caminho fácil de volta**: para voltar ao OpenPod
depois, basta o cartão SD.*

> **Recommended over the Factory Reset.** / **Recomendado no lugar do Factory Reset.**

## What it changes / O que muda
- Everything is stock, byte for byte, except **77 bytes** that add the *Update via SD* menu item.
- *Tudo é de fábrica, byte a byte, menos **77 bytes** que acrescentam o item "Atualizar por SD".*
- Settings (volume, EQ, language) may go back to default. Music on the card is kept.
- *As configurações podem voltar ao padrão. As músicas do cartão continuam lá.*

## Install / Instalar
**From OpenPod (SD card) / Pelo OpenPod (cartão):**
1. Copy `OpenPod_OpenPodRecoverySystem.up` to the root of the card, renamed to `update.up`.
2. `Config → Atualizar por SD → Sim`. Delete `update.up` afterwards.

**If the player doesn't start / Se o aparelho não liga:** use the computer, exactly like the OpenPod first
install (`windows/` with the Flashloader, or `install.sh` on Linux/macOS), choosing this `.up`.

## Back to OpenPod / Voltar ao OpenPod
Download the latest OpenPod `update.up`, copy it to the card and use `Config → Atualizar por SD`.

## Compatibility / Compatibilidade
Made from the **Ligenai GN-438** dump. On any other model, restore **your own backup** instead.
*Feito a partir do dump do **Ligenai GN-438**. Em outro modelo, use o **seu próprio backup**.*
