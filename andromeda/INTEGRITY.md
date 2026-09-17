# ANDROMEDA — INTEGRIDADE / CHECKSUM

## Validação do firmware GN-438

---

## 1. Resumo executivo

| Propriedade | Valor | Confiança |
|---|---|---|
| Algoritmo de checksum | **CRC-16/CCITT-FALSE** | CONFIRMADO |
| Polinômio | `0x1021` | CONFIRMADO |
| Valor inicial | `0xFFFF` | CONFIRMADO |
| Reflexão (in/out) | Não | CONFIRMADO |
| XOR final | `0x0000` | CONFIRMADO |
| Bootloader validado | Sim, por CRC no header HLKJ | CONFIRMADO |
| Partições validadas | FIRM, TONE (PSMP não verificada) | CONFIRMADO |

---

## 2. Header HLKJ

O firmware começa com o header `HLKJ` de 96 bytes (`0x60`):

```text
0x00000000: 4A4B4C48  ("HLKJ")
0x00000004: 0081FBC0  (endereço de carga do bootloader em RAM)
0x00000008: 00820001  (entry point do bootloader em RAM + 1, Thumb)
0x0000000C: 00000060  (tamanho do header / offset do payload)
0x00000010: 0000C8EC  (tamanho do payload do bootloader)
0x00000014: 0000759D  (CRC-16/CCITT-FALSE do payload)  ✓
0x00000018: 00000009  (campo desconhecido, possivelmente versão/flags)
0x0000001C: 00000400  (tamanho do bloco FIRM stage carregado para RAM)
0x00000020: 0000D000  (offset da tabela de partições na flash)
...
0x0000005C: 000034DB  (campo desconhecido)
```

### Validação do bootloader

```text
CRC-16/CCITT-FALSE(0x00000060 .. 0x0000C94C) = 0x759D
```

Isso bate exatamente com o campo em `0x00000014`.

> O campo `0x5C` (`0x34DB`) ainda não foi identificado. Não é CRC-16/CCITT-FALSE de ranges óbvios (tabela de partições, header completo, padding, etc.).

---

## 3. Tabela de partições

Local: `0x0000D010`

Cada entrada tem 16 bytes:

```text
+0x00: nome (4 bytes ASCII)
+0x04: offset da partição na flash
+0x08: tamanho da partição
+0x0C: CRC-16/CCITT-FALSE da partição
```

| Entrada | Nome | Offset | Tamanho | CRC16 | CRC calculado |
|---|---|---|---|---|---|
| 0 | FIRM | `0x0000E000` | `0x00192570` | `0x49A6` | **0x49A6** ✓ |
| 1 | TONE | `0x001A1000` | `0x00002038` | `0x9177` | **0x9177** ✓ |
| 2 | PSMP | `0x001FC000` | `0x00004000` | `0x0000` | `0x5684` (não usado?) |
| 3 | — | `0x00000000` | `0x00000000` | `0x0000` | — |
| 4 | — | `0x00000000` | `0x00000000` | `0x0000` | — |

### Nota sobre PSMP

A partição PSMP tem CRC declarado `0x0000`, mas o CRC-16/CCITT-FALSE calculado é `0x5684`. Isso indica que:

1. O CRC da PSMP não é verificado pelo bootloader, **ou**
2. A PSMP é modificada em runtime e seu CRC é recalculado depois, **ou**
3. O campo de 0x0C na PSMP tem outro significado.

> A PSMP é uma área de configuração/NVRAM; é esperado que seu conteúdo mude entre dispositivos.

---

## 4. Cálculo do CRC-16/CCITT-FALSE

Implementação de referência em Python:

```python
def crc16_ccitt_false(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc
```

Equivalente em C:

```c
uint16_t crc16_ccitt_false(const uint8_t *data, size_t len) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < len; i++) {
        crc ^= data[i] << 8;
        for (int j = 0; j < 8; j++) {
            if (crc & 0x8000)
                crc = (crc << 1) ^ 0x1021;
            else
                crc <<= 1;
        }
    }
    return crc;
}
```

---

## 5. Implicação para rebuild

Para modificar o firmware com segurança:

1. **Manter o header HLKJ** intacto, exceto se o bootloader for modificado.
2. **Recalcular o CRC do bootloader** se qualquer byte entre `0x60` e `0xC94C` for alterado.
3. **Recalcular o CRC das partições FIRM e TONE** se seus conteúdos forem alterados.
4. **Não alterar offsets/tamanhos** na tabela de partições sem garantir que o espaço caiba.
5. **Tratar PSMP com cuidado**: melhor preservar seu conteúdo original.

### Exemplo de workflow de rebuild

```text
firmware_original.bin
    ├── HLKJ header (0x00-0x5F) — preservar
    ├── Bootloader payload (0x60-0xC94B) — recalcular CRC em 0x14 se modificado
    ├── Padding (0xC94C-0xD00F) — preservar
    ├── Partition table (0xD010-0xD04F) — atualizar CRCs se modificar partições
    ├── FIRM (0xE000-0x1A056F) — recalcular CRC em tabela
    ├── TONE (0x1A1000-0x1A3037) — recalcular CRC em tabela
    ├── Área livre (0x1A3038-0x1FBFFF) — pode ser usada com cuidado
    └── PSMP (0x1FC000-0x1FFFFF) — preservar
```

---

## 6. Próximo patch seguro

O patch mais seguro agora é:

1. Modificar um **texto** dentro da partição FIRM (strings são fáceis de localizar).
2. Recalcular o CRC da partição FIRM.
3. Validar o firmware resultante.

Isso prova que conseguimos **extrair, modificar e reconstruir** o firmware.

---

## 7. Classificação

| Afirmação | Classe |
|---|---|
| Algoritmo CRC-16/CCITT-FALSE | CONFIRMADO |
| CRC do bootloader em 0x14 | CONFIRMADO |
| CRC das partições em 0x0C da tabela | CONFIRMADO |
| Significado do campo 0x5C | NÃO RESOLVIDO |
| Método de rebuild viável | PROVÁVEL |

---

## Referências

- `andromeda/MEMORY.md`
- `andromeda/BOOT.md`
- `andromeda/RISKS.md`
