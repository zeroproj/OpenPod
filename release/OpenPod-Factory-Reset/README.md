# Factory Reset (FR)

**The stock firmware of the Ligenai GN-438 (`yp3_2.0.43`), byte for byte, exactly as it left the factory.**
No OpenPod and no *Update via SD*.

*O firmware de fábrica do Ligenai GN-438 (`yp3_2.0.43`), byte a byte, exatamente como saiu da fábrica. Sem OpenPod e
sem "Atualizar por SD".*

> ⚠️ **Prefer the OpenPod Recovery System.** After a Factory Reset, going back to OpenPod **needs the computer**
> again (the stock firmware has no *Update via SD*).
> *Prefira o OpenPod Recovery System. Depois do Factory Reset, voltar ao OpenPod **exige o computador** de novo.*

## Install / Instalar
**From OpenPod (SD card) / Pelo OpenPod (cartão):** copy `OpenPod_FactoryReset.up` to the root of the card,
renamed to `update.up`, then `Config → Atualizar por SD → Sim`, and delete `update.up` afterwards.

**With a computer / Pelo computador:** `windows/` with the Flashloader, in flashing mode (hold **volume down** and
press **RESET**), choosing this `.up`.

Content SHA-256: `b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f` (the original dump).

## Compatibility / Compatibilidade
Made from the **Ligenai GN-438** dump. On any other model, restore **your own backup** instead.
*Feito a partir do dump do **Ligenai GN-438**. Em outro modelo, use o **seu próprio backup**.*
