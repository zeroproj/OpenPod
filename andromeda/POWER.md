# ANDROMEDA — POWER

## Subsistema de energia do GN-438

---

## 1. Resumo executivo

| Propriedade | Valor | Confiança |
|---|---|---|
| PMU | Integrada ao SoC | PROVÁVEL |
| Reguladores | coreldo, dcdc | CONFIRMADO |
| Mutexes | `pmu_bus_mutex`, `pmu_reg_mutex` | CONFIRMADO |
| Detecção VBUS | Sim | CONFIRMADO |
| Detecção de carga | `pmu charging in status` | CONFIRMADO |
| Nível de bateria | `pmu vol percent` | CONFIRMADO |
| Estados de energia | poweroff / sleep / wake up / idle | CONFIRMADO |
| Timer de carga | CHARGE_IN / CHARGE_OUT / CHARGE_CHECK | CONFIRMADO |
| Shutdown por bateria baixa | Sim | CONFIRMADO |
| Registradores PMU | Não mapeados | NÃO RESOLVIDO |

---

## 2. Evidências

### PMU e reguladores

```text
enable coreldo
pmu int mask:%x-%x-%x
creat pmu_bus_mutex fail
creat pmu_reg_mutex fail
```

### VBUS e carga

```text
vbus in
vbus out
vbus mid in
vbus mid out
vbus sta:%x-%u
-pmu vbus in status : %x
-pmu charging in status : %x
-pmu vol percent : %d
```

### Estados de energia

```text
enter poweroff mode
sleep
-pmu sleepa ....
-pmu wakeup ....
do_poweroff_mode
lowpoweroff
-status to sleep
-power key press status to poweroff
-power key long start status to poweroff
-power short release status to WakeUp !
-key status is WakeUp
-key status is poweroff !
```

### Timers de carga

```text
-stimer CHARGE_OUT %d
-stimer CHARGE_IN%d
-stimer CHARGE_CHECK %d
pmutimer
-charge: %d
-charge_cal1 %d
```

### Eventos PMU

```text
-pmu event power key press
-pmu event power key release
-pmu event power key long press
-pmu event charge in
```

### Mensagens de interface

```text
Low Power! Please Recharge!
Power is Lower than 10%%, Please Recharge!
Power Off
Please charge it for 10 minutes before using it
Charge & Transfer
Charge & Play
Idle Shutdown
```

---

## 3. Gerenciamento de energia

O firmware possui gerenciamento de energia completo:

- Detecção de bateria baixa.
- Desligamento automático por inatividade.
- Sleep com wakeup por tecla ou PMU.
- Carga da bateria via USB VBUS.
-Calibração de carga (`charge_cal1`).

---

## 4. Não resolvido

- Endereço base do PMU.
- Registradores de carga/bateria.
- Tipo de bateria e capacidade.
- Pinout do conector USB/carga.

---

## 5. Implicação para OpenPod

O gerenciamento de energia deve ser preservado intacto. Mudanças na interface podem incluir:

- Indicador de bateria mais visível.
- Telas de bateria baixa mais limpas.
- Opções de idle shutdown mais acessíveis.

---

## Classificação

| Afirmação | Classe |
|---|---|
| PMU integrada | PROVÁVEL |
| VBUS e carga detectados | CONFIRMADO |
| Nível de bateria reportado | CONFIRMADO |
| Estados sleep/wake/poweroff | CONFIRMADO |
| Registradores PMU mapeados | NÃO RESOLVIDO |

---

## Referências

- `docs/FIRMWARE_ANALYSIS.md`
- `andromeda/USB.md`
- `andromeda/INPUT.md`
