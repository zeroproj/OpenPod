# ANDROMEDA — STORAGE

## Armazenamento e controlador SD do GN-438

---

## 1. Resumo executivo

| Propriedade | Valor | Confiança |
|---|---|---|
| Interface de storage | microSD (SDIO) | CONFIRMADO |
| Stack de filesystem | FatFs (ChaN) | PROVÁVEL |
| Caminho do SD no firmware | `0:\` | CONFIRMADO |
| Arquivo de update | `0:\update.up` | CONFIRMADO |
| Leitura de blocos | 512 B | PROVÁVEL |
| Escrita de blocos | 256 B (dupla) | PROVÁVEL |
| Controlador físico SDIO | Não mapeado | NÃO RESOLVIDO |
| DMA para SD | Não mapeado | NÃO RESOLVIDO |

---

## 2. Evidências de SDIO

Strings no firmware indicam claramente que o controlador é SDIO:

```text
sdio(i):sd busmode %d
sdio(i):sd ClockDiv = %d
sdio(i):HAL_SD_Init_new errorstate = %d
sdio(i):uSdCardInf[%d].CardType %d, %x ++++++++
sdio(e):rx error[%x,%x]
sdio(e):read_mid_buf malloc fail
sdio(e):write_mid_buf malloc fail
```

A função `HAL_SD_Init_new` indica que o driver segue uma API semelhante à HAL da STM32, mas adaptada para o SoC Smartlink.

---

## 3. Rotina `sdupdate`

A rotina `sdupdate` (documentada em `docs/SDUPDATE_ANALYSIS.md`) prova que o bootloader consegue:

1. Montar o SD (`f_mount`).
2. Abrir um arquivo (`f_open`).
3. Ler cabeçalho (`f_read`).
4. Posicionar (`f_lseek`).
5. Ler blocos de 512 B.
6. Apagar setores de 4 KiB da flash interna.
7. Gravar 256 B de cada vez na flash.
8. Verificar CRC.

Isso demonstra que a **camada de abstração sobre SDIO + FatFs já funciona no bootloader**.

---

## 4. Primitivas exportáveis para SD Boot

| Função | Endereço no bootloader | Papel |
|---|---|---|
| `f_mount` | `0x00826AB8` | Montar filesystem |
| `f_open` | `0x00826464` | Abrir arquivo |
| `f_read` | `0x008263E2` | Ler bytes |
| `f_lseek` | via tabela de I/O | Posicionar no arquivo |
| tamanho do arquivo | via tabela de I/O | Retornar tamanho |
| `flash_read` | `0x00820A64` | Ler da flash interna |
| `flash_write` | `0x00821FFC` | Gravar na flash interna |
| `erase_sector` | `0x008220E0` | Apagar setor de 4 KiB |

A tabela de I/O montada em pilha em `0x00823CA0` abstrai:

- abrir
- fechar
- ler
- posicionar (lseek)
- tamanho
- progresso
- finalizar/erro

---

## 5. Controlador físico SDIO — NÃO RESOLVIDO

Não foi possível determinar:

- Base address do controlador SDIO.
- Mapeamento dos registradores (CLKDIV, ARG, CMD, RESP, DCTRL, DLEN, etc.).
- Se há DMA dedicado ou transferência por polling.
- Se o controlador é compatível com STM32 SDIO / SDMMC.

### Por que isso importa

Para um SD Boot que **reusa o bootloader**, o controlador físico não precisa ser mapeado. Basta chamar as funções FatFs existentes.

Para um **sistema novo** (Rockbox ou OpenPod bare-metal), seria necessário escrever um driver SDIO, o que exige conhecer os registradores.

---

## 6. Implicação para SD Boot

A forma mais segura de implementar SD Boot é:

1. **Não modificar o bootloader.**
2. Criar um payload que é carregado pelo caminho normal da FIRM stage.
3. O payload pode, por sua vez, chamar as funções FatFs do bootloader (se ainda estiverem em RAM) ou implementar seu próprio driver SDIO.

Como o bootloader carrega apenas 4 KiB da FIRM stage para `0x00804C00`, um SD Boot real precisaria:

- Ou aumentar o tamanho carregado (modificar bootloader — arriscado).
- Ou fazer a FIRM stage carregar mais código do SD para RAM (mais seguro).

---

## 7. Classificação

| Afirmação | Classe |
|---|---|
| O dispositivo usa microSD via SDIO | CONFIRMADO |
| O bootloader lê arquivos do SD com FatFs | CONFIRMADO |
| A rotina `sdupdate` grava flash a partir do SD | CONFIRMADO |
| O controlador físico SDIO está mapeado | NÃO RESOLVIDO |
| DMA para SD está mapeado | NÃO RESOLVIDO |
| SD Boot é viável via FIRM stage modificada | PROVÁVEL |

---

## Referências

- `docs/SDUPDATE_ANALYSIS.md`
- `docs/UPDATE_MECHANISM.md`
- `andromeda/BOOT.md`
