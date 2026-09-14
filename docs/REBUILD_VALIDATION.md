# OpenPod — REBUILD_VALIDATION

Validação do ciclo `ORIGINAL → PARSE → REBUILD → ORIGINAL` (Fase 0.5).

| | |
|---|---|
| **Data** | 2026-09-11 |
| **Origem** | `firmware/ORIGINAL/GN438_original.bin` (aberto somente para leitura) |
| **Saída** | `firmware/WORKING/GN438_rebuilt_original.bin` |
| **Resultado** | ✅ **APROVADO — 0 bytes divergentes** |
| **Hardware** | nenhuma operação; nenhum flash, erase, write ou exec |

---

## 1. Resultado

```text
SHA-256 ORIGINAL  b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f
SHA-256 REBUILT   b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f
                  ───────────────────────────────────────────────────────────────
                  IDÊNTICOS

byte differences  0
tamanho           2.097.152 / 2.097.152 bytes
MD5 (cruzado)     324fde1bf1c610a16e10822284d68fa2  (ambos)
cmp(1)            exit 0 — arquivos idênticos
validate_firmware 26 verificações OK, 0 falhas
test_roundtrip    3 testes, todos aprovados
```

---

## 2. Comandos executados

```bash
# 1. rebuild
python3 tools/rebuild_firmware.py \
    --in   firmware/ORIGINAL/GN438_original.bin \
    --out  firmware/WORKING/GN438_rebuilt_original.bin \
    --json analysis/reports/rebuild_recipe.json

# 2. validação independente + comparação byte a byte
python3 tools/validate_firmware.py \
    firmware/WORKING/GN438_rebuilt_original.bin \
    --compare firmware/ORIGINAL/GN438_original.bin \
    --expect-sha256 b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f

# 3. testes de regressão (identidade, regeneração de CRC, sensibilidade)
python3 tools/test_roundtrip.py

# 4. confirmação com ferramentas do sistema, independentes do meu código
cmp      firmware/ORIGINAL/GN438_original.bin firmware/WORKING/GN438_rebuilt_original.bin
cmp -l   firmware/ORIGINAL/GN438_original.bin firmware/WORKING/GN438_rebuilt_original.bin | wc -l
shasum -a 256 firmware/ORIGINAL/GN438_original.bin firmware/WORKING/GN438_rebuilt_original.bin
md5           firmware/ORIGINAL/GN438_original.bin firmware/WORKING/GN438_rebuilt_original.bin
```

### Ferramentas criadas nesta fase

| Arquivo | Papel |
|---|---|
| `tools/fw_common.py` | CRC-16/CCITT-FALSE e layout dos cabeçalhos, em um lugar só |
| `tools/rebuild_firmware.py` | desmonta e remonta o container |
| `tools/validate_firmware.py` | validação independente + comparação byte a byte |
| `tools/test_roundtrip.py` | testes de regressão, incluindo controle negativo |

`fw_common.py` existe para que rebuild e validação **não possam divergir
em silêncio**: ambos usam a mesma implementação de CRC e a mesma política.

---

## 3. O que foi regenerado e o que foi preservado

Esta distinção é o cerne do teste. O rebuild **não copia o arquivo**.

### REGENERADO — recalculado a partir dos dados

| Campo | Local | Valor obtido |
|---|---|---|
| Cabeçalho HLKJ completo | `0x000000`–`0x000060` | reemitido campo a campo |
| `loadCrc` do bootloader | `+0x14` | `0x759D` |
| `headerCrc` | `+0x5C` | `0x34DB` |
| Tabela de partições | `0x00D000` | nomes, offsets, tamanhos |
| CRC da `FIRM` | entrada +0x0C | `0x49A6` |
| CRC da `TONE` | entrada +0x0C | `0x9177` |
| Cabeçalho da imagem FIRM | `0x00E000`–`0x00E030` | reemitido campo a campo |
| `loadCrc` da FIRM | `0x00E01C` | `0x68E1` |
| Todas as lacunas | 4 regiões | a partir do byte de preenchimento |

### PRESERVADO — conteúdo opaco, copiado textualmente

| Item | Motivo |
|---|---|
| Payload do bootloader (51.436 B) | código executável, não derivável |
| Corpo das partições FIRM / TONE / PSMP | conteúdo, não derivável |
| `+0x18 = 0x00000009` | **NÃO IDENTIFICADO** |
| `+0x1C = 0x00000400` | **NÃO IDENTIFICADO** |
| `+0x2C = 0x00000001` | **NÃO IDENTIFICADO** |
| `timestamp` da FIRM = `0x8F20F1C2` | não derivável do conteúdo |

> **Limite honesto do teste.** Um round-trip bem-sucedido prova que o
> *container* foi entendido. Ele **não** prova que os três campos acima
> foram compreendidos — eles foram copiados, não regenerados.

---

## 4. Estrutura reconstruída

```text
0x000000  cabeçalho HLKJ — 0x60 B                    REGENERADO
          magic HLKJ · loadToRam 0x0081FBC0
          runFromRam 0x00820001 (Thumb)
          headerLen 0x60 · loadLength 0xC8EC
          loadCrc 0x759D · headerCrc 0x34DB
          ptableOff 0x0000D000
0x000060  payload do bootloader — 51.436 B           preservado
0x00C94C  lacuna — 1.716 B de 0x00                   REGENERADO
0x00D000  tabela de partições — 3 entradas           REGENERADO
0x00D040  lacuna — 4.032 B de 0x00                   REGENERADO
0x00E000  FIRM — 1.647.984 B · CRC 0x49A6            REGENERADO (cabeçalho+CRC)
          ├ cabeçalho 0x30 B · loadToRam 0x00804C00
          │  runFromRam 0x00804C01 · loadLength 0x1000
          │  loadCrc 0x68E1
          └ corpo 1.647.936 B                        preservado
0x1A0570  lacuna — 2.704 B de 0x00                   REGENERADO
0x1A1000  TONE — 8.248 B · CRC 0x9177                REGENERADO (CRC)
0x1A3038  lacuna — 364.488 B de 0xFF                 REGENERADO
0x1FC000  PSMP — 16.384 B · CRC 0x0000               preservado
0x200000  fim
```

Todas as 4 lacunas foram verificadas como preenchimento **uniforme** —
condição necessária para regenerá-las. Se alguma contivesse dados
variados, o rebuilder pararia, pois haveria conteúdo fora do mapa.

---

## 5. CRCs — todos verificados

Algoritmo: **CRC-16/CCITT-FALSE** — `poly=0x1021`, `init=0xFFFF`,
`refin=false`, `refout=false`, `xorout=0x0000`.

| # | Região | Intervalo | Gravado | Calculado | |
|---|---|---|---|---|---|
| 1 | headerCrc | `0x000000`–`0x00005C` | `0x34DB` | `0x34DB` | ✅ |
| 2 | Payload do bootloader | `0x000060`–`0x00C94C` | `0x759D` | `0x759D` | ✅ |
| 3 | Estágio RAM da FIRM | `0x00E030`–`0x00F030` | `0x68E1` | `0x68E1` | ✅ |
| 4 | Partição FIRM | `0x00E000`–`0x1A0570` | `0x49A6` | `0x49A6` | ✅ |
| 5 | Partição TONE | `0x1A1000`–`0x1A3038` | `0x9177` | `0x9177` | ✅ |
| 6 | Partição PSMP | `0x1FC000`–`0x200000` | `0x0000` | seria `0x5684` | política |

### Descoberta nova desta fase: `headerCrc` em `+0x5C`

Na Fase 0 o campo `+0x5C = 0x000034DB` estava marcado como
**NÃO IDENTIFICADO**. Foi resolvido por varredura de CRC acumulado:

```text
CRC-16/CCITT-FALSE sobre os bytes [0x00 : 0x5C] = 0x34DB
```

Ou seja, **o cabeçalho carrega um CRC de si mesmo**, cobrindo os 92 bytes
anteriores ao próprio campo. Isso reduz os campos desconhecidos do
cabeçalho HLKJ de quatro para três.

**Consequência prática:** qualquer alteração em *qualquer* campo do
cabeçalho exige recalcular também o `headerCrc`. Se isso tivesse passado
despercebido, o primeiro firmware modificado poderia falhar no boot por
um motivo difícil de diagnosticar.

---

## 6. Testes de regressão

Um round-trip idêntico, sozinho, **não prova nada**: uma ferramenta que
apenas copiasse o arquivo passaria no mesmo teste. Por isso foram
escritos três testes em `tools/test_roundtrip.py`.

### T1 — Identidade ✅

`original → parse → build` reproduz o original. 0 bytes divergentes.

### T2 — Regeneração de CRC (controle negativo) ✅

Zeram-se **na entrada** o `headerCrc`, o `loadCrc` do bootloader, os CRCs
das três partições e o `loadCrc` da FIRM. Resultados:

- o `parse` **denunciou 5 problemas**, identificando cada campo inválido;
- o `build` **reconstruiu todos os CRCs corretos**;
- a saída ficou **byte a byte igual ao original**, apesar de a entrada
  estar adulterada.

> Este é o resultado mais forte do relatório. Se os CRCs estivessem
> sendo copiados, a saída teria saído com os campos zerados.

### T3 — Sensibilidade ao conteúdo ✅

Alterou-se um byte em `0x0010E030`, dentro do corpo da FIRM e fora dos
4 KiB carregados em RAM:

| Efeito | Observado |
|---|---|
| CRC da FIRM na tabela | `0x49A6` → **`0x5034`** |
| Novo CRC corresponde ao novo conteúdo | ✅ |
| `loadCrc` da FIRM | inalterado (`0x68E1`), como esperado |
| Saída difere do original | ✅ |

Prova que o CRC acompanha os dados, e não um valor memorizado.

---

## 7. Defeito encontrado e corrigido

O teste T2 **reprovou na primeira execução**, expondo um defeito real no
rebuilder antes que ele pudesse gerar um firmware ruim.

### O defeito

```python
# ERRADO — a decisão vinha do dado de entrada
novos_crc[p.name] = 0 if p.crc == 0 else fw.crc16(blob)
```

E, no `parse`:

```python
# ERRADO — um CRC zerado era aceito em silêncio
if crc != 0 and calc != crc:
    problemas.append(...)
```

### Por que era grave

A intenção era preservar o zero legítimo do PSMP. Mas a regra estava
escrita como *"se a entrada tem zero, emita zero"*, o que significa:

1. um firmware entregue com o CRC da FIRM zerado faria o rebuilder
   **emitir zero**, produzindo uma imagem inválida;
2. o `parse` **não reclamaria** — um CRC zerado era indistinguível de
   "partição não verificada".

Na imagem original o efeito era invisível, porque o PSMP realmente tem
zero. O defeito só apareceria depois, em um firmware modificado.

### A correção

A decisão virou **política explícita**, declarada em um lugar só:

```python
# fw_common.py
PARTICOES_SEM_CRC = {b"PSMP"}
```

Agora o `build` nunca consulta o valor da entrada, e o `parse` denuncia
tanto um CRC zerado onde deveria haver um, quanto um CRC presente onde a
política diz que deveria haver zero.

> **Ressalva registrada:** a lista `PARTICOES_SEM_CRC` foi derivada da
> observação de **uma** imagem. **Não** foi confirmado por disassembly
> que o bootloader ignora o CRC do PSMP. É uma suposição declarada, não
> um fato.

---

## 8. Divergências encontradas

**Nenhuma divergência byte a byte.**

Registram-se as duas observações de processo desta fase:

| # | Observação | Situação |
|---|---|---|
| 1 | Defeito da política de CRC (seção 7) | **corrigido** e coberto por teste |
| 2 | Campo `+0x5C` era desconhecido | **identificado** como CRC do cabeçalho |

---

## 9. Conclusão sobre a confiabilidade do rebuild

### O que está provado

- O **container** do firmware foi entendido: cabeçalhos, tabela de
  partições, lacunas e **todos os seis campos de integridade**.
- O rebuild é **determinístico** e reproduz a imagem original **byte a
  byte**, confirmado por quatro métodos independentes (comparação em
  Python, `cmp`, SHA-256, MD5).
- Os CRCs são **genuinamente calculados**, provado pelo controle negativo
  em que a entrada foi adulterada e a saída saiu correta.
- O CRC **acompanha o conteúdo**, provado pelo teste de mutação.
- As ferramentas **recusam** entradas inconsistentes em vez de corrigi-las
  em silêncio.

### O que NÃO está provado

- Que os campos `+0x18`, `+0x1C` e `+0x2C` foram compreendidos — foram
  **copiados**, não regenerados.
- Que o bootloader ignora o CRC do PSMP — é suposição.
- Que o bootloader não verifica **nada além** dos CRCs. Pode haver
  validações adicionais não descobertas.
- Que uma imagem **modificada** inicializa. Este teste valida o
  container, não o comportamento em execução.
- Qual é o formato do pacote `boot sdupdate` — ainda o bloqueador para
  qualquer gravação.

### Veredito

> O processo de rebuild é **confiável para alterações que não mudam
> tamanhos nem offsets** — substituir ícones, imagens, glifos ou textos
> in-place.
>
> Alterações que mudem tamanhos exigem entender os campos `+0x18` e
> `+0x1C` antes, já que não se sabe o que eles descrevem.
>
> **Isto não autoriza gravação.** O caminho de flash e o método de
> recuperação continuam não determinados.

---

## 10. Estado ao fim da Fase 0.5

```text
firmware/ORIGINAL/GN438_original.bin          b7cd5eb9…4b36f  ✅ intacto, 444
firmware/WORKING/GN438_analysis.bin           b7cd5eb9…4b36f  ✅ idêntico
firmware/WORKING/GN438_rebuilt_original.bin   b7cd5eb9…4b36f  ✅ idêntico

GN438_openpod_v001.bin                        NÃO CRIADO (correto)
Logo substituída                              NÃO (correto)
Operações em hardware                         NENHUMA (correto)
```

Fase 0.5 **aprovada**. O próximo passo autorizado é o primeiro patch —
mas só depois de decidir, com você, o alvo e o método de gravação.
