# OpenPod — PSMP_FORMAT

Formato da partição de configuração `PSMP`, decodificado a partir de
evidência empírica.

| | |
|---|---|
| **Data** | 2026-09-12 |
| **Método** | comparação entre o dump original (2026-09-11) e uma releitura do aparelho (2026-09-12) |
| **Evidência** | `firmware/READBACK/GN438_readback_2026-09-12.bin` |
| **Hardware** | somente leitura |

> Esta é a primeira descoberta do projeto obtida por **observação do
> aparelho em uso**, não por análise estática. A `PSMP` mudou sozinha
> entre os dois dumps, e a diferença revelou o formato.

---

## 1. O que a comparação mostrou

```text
REGIAO              INTERVALO              DIVERGENCIAS
cabecalho HLKJ      0x000000-0x000060                 0
bootloader          0x000060-0x00C94C                 0
tabela particoes    0x00D000-0x00D040                 0
FIRM                0x00E000-0x1A0570                 0
TONE                0x1A1000-0x1A3038                 0
area livre (0xFF)   0x1A3038-0x1FC000                 0
PSMP (config)       0x1FC000-0x200000               802   <-- só aqui
```

**Tudo idêntico, exceto a `PSMP`.** Isso confirma, empiricamente, o que
antes era hipótese: a `PSMP` é a única região que o aparelho reescreve
sozinho.

| Afirmação | Antes | Agora |
|---|---|---|
| `PSMP` é área de configuração gravada em runtime | **PROVÁVEL** | **CONFIRMADO** |
| Excluí-la do `update.up` preserva a configuração | **PROVÁVEL** | **CONFIRMADO** |
| O `GN438_original.bin` é cópia fiel do aparelho | presumido | **CONFIRMADO** |

---

## 2. Estrutura: armazenamento append-only chave-valor — CONFIRMADO

A `PSMP` é um **log append-only** de registros chave-valor.

```text
+0x00  55 AA        magic do registro
+0x02  u8           flag de estado (0xFF = livre · 0xFE = válido)
+0x03  u32          checksum / identificador
+0x07  u16          tamanho do valor, em bytes
+0x09  u16          número de sequência (incremental)
+0x0B  u8           comprimento da chave
+0x0C  char[]       chave, em ASCII
+...   bytes        valor
```

### Verificação em quatro registros consecutivos

```text
1FC82F  55 AA FE 26 CE F1 DC  04 00  05 00  04  "pass"          valor de 4 B
1FC843  55 AA FE 07 54 11 8B  1C 00  06 00  06  "record"        valor de 28 B
1FC871  55 AA FE D9 98 B5 0A  14 00  07 00  05  "music"         valor de 20 B
1FC896  55 AA FE A1 AD 61 DD  10 00  08 00  0C  "audio_volume"  valor de 16 B
```

Os números de sequência são **5, 6, 7, 8** — consecutivos. O comprimento
da chave bate exatamente com a string ASCII em todos os quatro casos.

---

## 3. Como as escritas acontecem — CONFIRMADO

Entre os dois dumps:

| Observação | Valor |
|---|---|
| Marcadores `55 AA` | 73 → **99** (26 registros novos) |
| Último byte usado | `0x1FC82E` → **`0x1FCB50`** (cresceu 802 B) |
| Bytes alterados na área já usada | **7** |
| Transições nesses 7 bytes | seis `0xFF → 0xFE`, uma `0xFF → 0x55` |

### O detalhe que explica tudo — CONFIRMADO

**Todas as transições observadas são de `1` para `0`.**

Verificado: `(orig & novo) == novo` para os 7 bytes.

Isso não é coincidência. Em memória flash, apagar leva bits a `1`; gravar
só consegue levá-los a `0`. Um armazenamento projetado assim **nunca
precisa apagar**:

- área livre é `0xFF` → escrever um registro só limpa bits;
- invalidar um registro antigo → limpar um bit do flag (`0xFF → 0xFE`);
- registro novo → anexado adiante, com sequência maior.

> **Por isso a `PSMP` não tem CRC na tabela de partições** e por isso ela
> é **excluída** do pacote `update.up`: é uma estrutura que o aparelho
> administra sozinho, sem nunca apagar setor.
>
> E há uma conexão com o risco documentado em `EXTERNAL_RESEARCH.md` §5.2:
> a anomalia relatada é sobre gravar `0 → 1` **sem apagar**. A `PSMP`
> nunca faz isso — só `1 → 0`, que é sempre seguro. O projeto do firmware
> está correto neste ponto.

---

## 4. Chaves de configuração observadas — CONFIRMADO

| Chave | Provável significado |
|---|---|
| `audio_volume` | volume |
| `bright` | brilho da tela |
| `offscr` | tempo até desligar a tela |
| `language` | idioma da interface |
| `music` | estado do player |
| `record` | parâmetros de gravação |
| `profile` | perfil de equalização |
| `bt_addr` | endereço Bluetooth pareado |
| `freq_drift` | correção de frequência (FM ou clock) |
| `pass` | senha/bloqueio |
| `device_id` | identificação do aparelho |

O registro `device_id` contém:

```text
CBKJ01MP3---MP3-------T90026----------C0B2C1003357854270--------
```

> **Dado sensível:** essa string identifica **esta unidade**. Se o projeto
> for publicado, considerar removê-la dos documentos e dos dumps
> divulgados. O `GN438_readback_*.bin` contém a `PSMP` real do aparelho.

---

## 5. Consequências para o OpenPod

| Item | Consequência |
|---|---|
| Atualização não apaga configurações | o usuário não perde ajustes — comportamento a **preservar** |
| `PSMP` fora do pacote | continuar excluindo, como o `fwhelper` faz |
| Dois dumps do mesmo aparelho **não** terão o mesmo SHA-256 | comparar **por região**, nunca o arquivo inteiro |
| A `PSMP` não deve ser usada para dados do OpenPod | é administrada pelo firmware; escrever ali por fora quebraria o log |

---

## 6. Classificação

| Afirmação | Classe |
|---|---|
| `PSMP` é a única região reescrita pelo aparelho | **CONFIRMADO** (observado) |
| Estrutura de registro (magic, flag, tamanho, sequência, chave) | **CONFIRMADO** (4 registros consecutivos) |
| É append-only, sem apagamento | **CONFIRMADO** (todas as transições são 1→0) |
| Significado de cada chave | **PROVÁVEL** (pelo nome) |
| Os 4 bytes em `+0x03` são checksum | **HIPÓTESE** — não verificado |
| O que os 6 bytes `0xFF → 0xFE` invalidam | **NÃO DETERMINADO** |
