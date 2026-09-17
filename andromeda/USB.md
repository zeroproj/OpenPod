# ANDROMEDA — USB

## Subsistema USB do GN-438

---

## 1. Resumo executivo

| Propriedade | Valor | Confiança |
|---|---|---|
| Modo USB | Device-only | CONFIRMADO |
| Classe principal | MSC (Mass Storage Class / card reader) | CONFIRMADO |
| Dispositivo | `/dev/usbd` | CONFIRMADO |
| Modos de operação | reader / charger / select / idle | CONFIRMADO |
| Detecção de conexão | VBUS via PMU | CONFIRMADO |
| VID:PID | `301a:2801` | CONFIRMADO |
| Manufacturer/Product | `SmartlinkTechnology` / `USB2.0 Device` | CONFIRMADO |
| Controlador USB físico | Não mapeado | NÃO RESOLVIDO |

---

## 2. Evidências

### Identificação USB

Conforme documentado em `CLAUDE.md`:

```text
VID:PID      301a:2801
Manufacturer SmartlinkTechnology
Product      USB2.0 Device
Serial       20201111000001
```

### Strings do firmware

```textn/dev/usbd
usbd_cb
usbd_sta
usbd close ret:%d
usbd Ioctl ret:%d
-USB reader mode, ignore record.
-driver_usbd_sd_params_init
-driver_usbd_params_init
-usbd_mw_pc_arrival_detect_init
-register_usb_event_cb
-usbd_register_sd_wr_cb
-driver_usbd_msc_param_deinit -------
-driver_usbd_msc_param_init +++++ 
-usb media start %d
-usb media stop %d
-usbd_msc_cardreader_init ++++++
```

### Estados USB

```text
-usb status is idle
-usb status is usb out
-usb status is usb in <%d>
-usb status is select
-usb status is charger
-usb status is reader <%d>
-pmu vbus is in sendto usb
-pmu vbus is out sendto usb
```

---

## 3. Funcionalidade

O firmware implementa um dispositivo USB MSC que expõe o conteúdo do cartão microSD como uma unidade de armazenamento em massa quando conectado a um PC.

A detecção de conexão/desconexão é feita pelo PMU monitorando o VBUS.

---

## 4. Não resolvido

- Endereço base do controlador USB Device.
- Endereços dos endpoints e DMA.
- Descriptors USB completos no firmware.

---

## 5. Implicação para OpenPod

A funcionalidade USB MSC pode ser mantida inalterada na Fase 1. Futuramente, poderia ser interessante adicionar MTP ou ADB, mas isso exigiria um novo stack USB.

---

## Classificação

| Afirmação | Classe |
|---|---|
| USB Device com MSC | CONFIRMADO |
| VID:PID `301a:2801` | CONFIRMADO |
| Modo card reader | CONFIRMADO |
| Detecção VBUS via PMU | CONFIRMADO |
| Controlador USB mapeado | NÃO RESOLVIDO |

---

## Referências

- `CLAUDE.md` (seção hardware)
- `docs/FIRMWARE_ANALYSIS.md`
