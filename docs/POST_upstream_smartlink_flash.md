# Does the SL6801 mask ROM have a USB download mode? (bricked device, full analysis + 2 MiB dump of yp3_2.0.43 offered)

<!--
  Rascunho para publicar em github.com/ilyakurdyukov/smartlink_flash/issues
  Revise antes de enviar. Tudo aqui foi verificado por desmontagem nesta
  sessão; nada é suposição não marcada.
-->

Hi — first, thanks for `smartlink_flash`. It's the only public technical
resource on this platform, and it's what made all of the analysis below
possible.

I bricked a device and, in the process of trying to recover it, I
disassembled the bootloader fairly completely. I'm posting what I found in
case it's useful to you or to others, and to ask two specific questions
that only you are likely to be able to answer.

**I also have a full, verified 2 MiB dump of `yp3_2.0.43`** — see the last
section; this may be what #4 is looking for.

---

## Device

| | |
|---|---|
| Product | Iigenai GN-438 |
| Board | `T90198-MP01-V2`, dated `2024-01-02` |
| SoC | `Jointbees MP3` / `V57J21B6A0` (QFN) |
| Firmware | `yp3_2.0.43` |
| USB | `301a:2801`, `SMTLINK CARDREADER 1.00` |
| Flash | 2 MiB, `flash_id = 0x14851485` |
| Display | 128×160, ST7789S, LVGL v8 |

No external flash chip exists on this board. Both sides and the area under
the battery were inspected: the only 8-pin ICs are `XS4150` (mono audio
amp) and `5807M`. **The 2 MiB appears to be in-package with the SoC**, which
rules out SPI programmers, SOIC clips, and the usual "ground the flash DO
pin at power-up" trick.

## What I did to brick it

A `write_flash` to sector `0x00D000` (the partition table) failed
mid-operation. Since then the device is completely silent on USB — no
enumeration, not even a transient event (checked with `udevadm monitor` on
Linux and `ioreg -p IOUSB` on macOS). The board *does* have power.

## Boot chain (disassembled, bootloader RAM bias `0x0081FB60`)

The header at flash `0x0` is `HLKJ`:

```
load address 0x0081FBC0   entry 0x00820001   offset 0x60
length       0x0000C8EC   crc   0x759D       ptable @ [0x20] = 0x0000D000
```

`0x00820DA8` then does:

```
memcpy(0x0082C8D0, flash 0x000000, 0x60)     ; HLKJ header
r3 = [hdr + 0x20]                            ; partition table pointer
if r3 == 0 or not 4K-aligned -> r3 = 0x3000
memcpy(0x0082C92C, r3,            0x100)     ; partition table  <-- the sector I killed
memcpy(0x0082CA2C, [ptable+0x14], 0x30)      ; boot descriptor
```

and `0x00820470` uses that descriptor:

```
[0x10] = 0x00804C00   load address
[0x14] = 0x00804C01   entry (Thumb)
[0x18] = 0x00001000   length
memcpy(load, flash, length) ; blx entry
```

**No CRC is verified anywhere on this path.** With `ptable+0x14`
corrupted, the `blx` jumps to garbage — which happens before any USB
initialisation, explaining the total silence.

## `boot_main` (`0x008204EC`) — the mode selection

```
bl 0x827BF2                     ; printf("boot--->is_pmu_pc_update_flag_set %x")
bl 0x827C02                     ; flag == 7 ?
    yes -> clear flag; bl 0x820448  = "boot--->update from pc"
bl 0x827C0A                     ; flag == 6 ?
    yes -> clear flag; hw+LCD init; printf("Finding file...");
           bl 0x00823CA0 = boot sdupdate
else -> printf("boot--->load firmware disp.")
        bl 0x820418 ; bl 0x820DA8 ; bl 0x820470   ; loads FIRM and jumps
        if 0x820470 returns -> bl 0x820448 ("update from pc")
```

The flag is **not in flash** — it is assembled from two PMU registers read
over the two-wire interface (`0x00820BD0`):

```
flag = ((reg[0x23] >> 6) << 1) | (reg[0x00] & 1)

flag == 7  ->  update from PC   (0x008284AE)
flag == 6  ->  update from SD   (0x008284C0)
```

`boot sdupdate` itself (`0x00827850`) is complete: FatFs mount, looks for
`0:\update.up`, checks a `CONFIG` header and an `SL6801` mark, erases
sector by sector (`"erase %d / %d"`) and compares CRC (`"crc cmp %x %x"`).

## The two findings that led to my questions

**1. Nothing in this firmware ever arms an update flag.**

`HAL_pmu_sd_update_flag_set` exists in FIRM at `0x00CF6CA0`, and
`HAL_pmu_uart_update_flag_set` at `0x00CF6C48`. Both are complete and
correct. A scan of the whole FIRM region (`0x0E000`–`0x1A0570`) for `BL`
encodings and for pointers finds **zero callers of either**. They are dead
code.

**2. Nothing in this firmware reads a boot key.**

The bootloader entry is just:

```asm
00820000  zero r0..lr
00820028  sp = 0x0083BE90
0082002C  clear BSS (0x0082C4AC .. 0x0083BA90)
0082003C  bl boot_main
```

No GPIO read, and `boot_main` only reads the PMU flags.

So on **this** device, the README's "hold down the boot key when connecting
to USB" cannot be implemented by anything in flash. I tried every key and
combination (`M`, `Vol`, `Play/Pause`, `|<<`, `>>|`, reset, and pairs) on
both Linux and macOS, plus a no-key baseline: no USB event of any kind.

---

## Questions

1. **Is the boot key handled by the SoC's mask ROM, or by device
   firmware?** Your README says it "varies from device to device", which
   would fit firmware-level handling — and this firmware has none. If it is
   mask-ROM level, do you know what it checks (a GPIO, a strap pin, a
   specific pad)?

2. **Does the SL6801 mask ROM have a USB download mode that is reachable
   regardless of flash contents?** The chip must be programmable when the
   flash is blank, so some path has to exist. Is it entered by strap pin,
   by invalid `HLKJ` header, or only with factory equipment before
   assembly?

3. Is there any known way to set the PMU update flags (reg `0x23` bits 7:6,
   reg `0x00` bit 0) from outside — externally accessible two-wire bus, or
   a test pad?

4. Minor, but useful for anyone patching these: **is the FIRM CRC at
   `ptable + 0x0C` checked by anything?** The bootloader's load path
   doesn't verify it. If nothing does, `0x00D000` never needs to be written
   at all — which would have saved my device.

---

## What I can contribute

- A **verified 2 MiB dump of `yp3_2.0.43`** (`GN438_original.bin`,
  sha256 `b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f`).
  @Dogolitesnap (#4) — this may be what you need, if your device is the
  same model. Note that flashing another unit's dump is not risk-free;
  compare board and SoC markings first.
- Disassembly notes for the bootloader: boot chain, PMU flag logic,
  `boot sdupdate`, the partition table format, and the `HLKJ` header
  fields.
- A CRC-16 observation that may help others avoid my mistake: CRC-16 is
  affine over GF(2), so after patching FIRM you can restore the *original*
  CRC value by adjusting 2 bytes of dead padding inside FIRM — which means
  the partition-table sector never has to be rewritten. This firmware has a
  133,602-byte run of `0x00` at `0x018A8E`, which is more than enough.

Happy to send any of it in whatever form is useful, or to open a PR with
notes if you'd want them in the repo.
