# ANDROMEDA — BLUETOOTH

## Subsistema Bluetooth do GN-438

---

## 1. Resumo executivo

| Propriedade | Valor | Confiança |
|---|---|---|
| Stack | Próprio / baseado em camadas HCI/L2CAP/RFCOMM | PROVÁVEL |
| Profiles | A2DP (src + snk), AVRCP, HFP | CONFIRMADO |
| Estados | disconnected / pairing / paired / connected | CONFIRMADO |
| Lista de pareados | Armazenada em NV | CONFIRMADO |
| Máximo de pareados | Limitado ("paired num max") | CONFIRMADO |
| Entrada A2DP source | `spark_bt_a2dp_src_entry` | CONFIRMADO |
| Controlador BT físico | Não mapeado | NÃO RESOLVIDO |

---

## 2. Evidências

### Profiles

Strings indicam suporte a:

```text
-a2dp src open 0x%x, handle:0x%x
-a2dp snk open 0x%x, handle:0x%x
-a2dp src close 0x%x, handle:0x%x
-a2dp snk close 0x%x, handle:0x%x
-avrcp btn 0x%x, %d
-hfp sco codec ,%x 
```

### Estados de conexão

```text
-disconnected 0x%x
-pairing 0x%x
-paired 0x%x
-paired in paired list
-add a new paired dev error! paired num max!!
-unpaired 0x%x
-remove pair dev idx %d over %d
-paired dev num: %d
```

### Camadas de protocolo

```text
a2dp
l2cap
rfcomm
avrcp
```

### Strings de interface

```text
Paired Device
Pairing
Available Devices
Connection failed!
Connect
Disconnect
Unpair
```

---

## 3. Armazenamento de pareamento

Os dispositivos pareados são armazenados em NV (non-volatile memory), provavelmente em uma área reservada da flash interna.

---

## 4. Não resolvido

- Controlador Bluetooth físico (UART? SPI? USB?).
- Endereço base do HCI/controller.
- Versão do Bluetooth (3.0? 4.0? 5.0?).
- Se há BLE.

---

## 5. Implicação para OpenPod

A funcionalidade Bluetooth pode ser mantida inalterada na Fase 1. A melhoria seria principalmente de interface:

- Lista de dispositivos disponíveis.
- Gerenciamento de pareados.
- Indicadores de conexão.
- Controles AVRCP (play/pause/next/prev).

---

## Classificação

| Afirmação | Classe |
|---|---|
| A2DP source/sink | CONFIRMADO |
| AVRCP | CONFIRMADO |
| HFP | CONFIRMADO |
| Gerenciamento de pareamento | CONFIRMADO |
| Armazenamento em NV | PROVÁVEL |
| Controlador físico mapeado | NÃO RESOLVIDO |

---

## Referências

- `docs/FIRMWARE_ANALYSIS.md`
- `andromeda/AUDIO.md`
