# ANDROMEDA — AUDIO

## Subsistema de áudio do GN-438

---

## 1. Resumo executivo

| Propriedade | Valor | Confiança |
|---|---|---|
| Middleware de áudio | `audio_crab` (próprio) | CONFIRMADO |
| Dispositivos | `/dev/audio0`, `/dev/audio1` | CONFIRMADO |
| Codec/DAC externo | Não identificado | NÃO RESOLVIDO |
| Codec integrado ao SoC | Forte hipótese | PROVÁVEL |
| Interface digital | I2S/PCM interna | HIPÓTESE |
| Controle do codec | Registradores do SoC ou I2C não mapeado | NÃO RESOLVIDO |
| Entrada analógica | AMIC1, AMIC2 | CONFIRMADO |
| Saídas | speaker wire, BT, CALL | CONFIRMADO |
| ASRC | Presente | CONFIRMADO |
| Resampling | Presente | CONFIRMADO |
| Equalizador (EQ) | Presente | CONFIRMADO |
| Volumes | speaker wire / BT / CALL separados | CONFIRMADO |

---

## 2. Evidências de `audio_crab`

O firmware usa um middleware chamado `audio_crab`. Ele gerencia:

- play / record / decode / stop / pause / resume
- volume
- seek
- speed_x (velocidade de reprodução)
- bench

Strings encontradas:

```text
-[audio_crab]:speed_x: %d, %d, %d ...
-audio_crab_start = %d, last_error: %d
-audio_crab_admomini_open: %d.
-crab_post_timer_report: sr: %d, ch: %d, len: %d
-[audio_crab _monitor_proc_]: ths instance is in busy...
-[audio_crab]: Auto stoped.
-audio_crab_control wait timeout for call the api.
-[audio_crab]: audio_crab_register failed.
-[audio_crab]: audio_crab_create should be first call.
-[audio_crab]: ths instance is in busy...
-[audio_crab]: crab config volume_type: %d.
-[audio_crab]: load compontents failed: unknown protocol or media format.
-[audio_crab]: begin thread failed.
-[audio_crab]: ready bits is: %d
-[audio_crab]: create failed.
-audio_crab_stop wait timeout for call the api.
-[crab_core]: run CRAB_END by %s.
-[crab_core]: run CRAB_ENOTSUPPORT by %s.
-[audio_crab]: %s loaded.
-[crab_core pin]: OAL_malloc pin struct: %d failed.
```

Path do fonte:

```text
F:\pen133_yp3_mp\spark2\src\middleware\audio_crab\core\crab_pin.c
```

---

## 3. Dispositivos de áudio

O sistema opera com dois dispositivos de caracter:

```text
/dev/audio0
/dev/audio1
```

Referências encontradas em 4/3 locais no firmware. A função de inicialização (`open("/dev/audio0", ...)`) ocorre em torno de `0x00D12784`.

`audio0` provavelmente é o caminho principal de reprodução/gravação; `audio1` pode ser um secundário (monitor, linha BT, etc.).

---

## 4. Codec / DAC

### Não identificado

Não foram encontradas strings com nomes de codec conhecidos como:

- ES8311 / ES8388 / ES9218
- WM8978 / WM8960
- CS42L51 / CS43L22
- AK4376
- PCM5102 / PCM5121
- RT5631 / RT5651
- NS4168

### Hipótese: codec integrado

A ausência de strings I2C/SCCB ou de nome de chip externo, combinada com múltiplas strings de controle de ganho de microfone (`AMIC1_GAIN`, `AMIC2_GAIN`) e saídas distintas (`spk wire`, `BT`, `CALL`), sugere que o codec é **integrado ao SoC SL6801** e controlado por registradores internos.

### Caminhos de saída

Strings de controle de volume:

```text
-spk wire volume 0x%08x set to: %d (x 10000)
-BT volume 0x%08x set to: %d (x 10000)
-CALL volume 0x%08x set to: %d (x 10000)
```

Isso indica mixer interno com pelo menos três caminhos de saída.

---

## 5. ASRC e resampling

Strings encontradas:

```text
asrc init fail!
ASRC addr:%#X, write:%#X, read back:%#X
asrc_idx:%d
need resample.
codec.resample
driver audio _resample_init: aip.io_period=%d, ch=%d, sample_size=%d
```

O firmware possui conversor de taxa de amostragem assíncrono (ASRC) e faz resampling quando necessário.

---

## 6. Equalizador

String encontrada:

```text
-hardware EQ open success, init max sample: %d.
```

O firmware possui equalizador em hardware.

---

## 7. Entradas analógicas

Strings encontradas:

```text
[driver_audio] AMIC1_GAIN set to:%d / AMIC2_GAIN set to:%d
```

Dois canais de microfone analógico são suportados.

---

## 8. Outros recursos

- Detecção de fone de ouvido (`earphone check is %x`, `earphone: %d`).
- Modo FM usa fone como antena (`Please Insert Earphone as FM Antenna`).
- Monitoramento de gravação (`Please plug in headphones for recording monitoring`).
- Gravação de áudio para WAV/ADPCM (`wav save to adpcm`, `wav save to pcm`).

---

## 9. Implicação para Rockbox / OpenPod

### Rockbox

Sem conhecer o codec/DAC e seus registradores, é impossível portar o Rockbox. Rockbox precisa de um driver de áudio que configure o DAC, I2S, DMA e mixer. Sem datasheet do SL6801, isso é inviável.

### OpenPod

Para o OpenPod, a abordagem correta é **manter o firmware YP3 existente** e apenas modificar a GUI, menus, gráficos, etc. O subsistema de áudio permanece inalterado, então a falta de conhecimento do codec não bloqueia a Fase 1 (interface).

---

## 10. Classificação

| Afirmação | Classe |
|---|---|
| Middleware de áudio é `audio_crab` | CONFIRMADO |
| Dispositivos `/dev/audio0` e `/dev/audio1` existem | CONFIRMADO |
| ASRC e resampling presentes | CONFIRMADO |
| EQ de hardware presente | CONFIRMADO |
| Codec é integrado ao SoC | PROVÁVEL |
| Interface do codec é I2S | HIPÓTESE |
| Codec externo identificável | NÃO ENCONTRADO |
| Registradores do codec mapeados | NÃO RESOLVIDO |

---

## Referências

- `docs/FIRMWARE_ANALYSIS.md`
- `andromeda/CPU.md`
- `andromeda/SOC.md`
- `andromeda/MEMORY.md`
