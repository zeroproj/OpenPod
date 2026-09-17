# ANDROMEDA — CPU

## Arquitetura do processador do GN-438

---

## 1. Resumo executivo

| Propriedade | Valor | Confiança |
|---|---|---|
| Família | ARM Cortex-M | CONFIRMADO |
| Arquitetura | ARMv7-M | CONFIRMADO |
| Conjunto de instruções | Thumb-2 | CONFIRMADO |
| FPU | Presente (instruções VFP) | CONFIRMADO |
| Endianness | Little-endian | CONFIRMADO |
| Núcleo exato (M4F / M7 / M33) | **Provável M4F** | PROVÁVEL |
| Frequência | **NÃO IDENTIFICADO** | NÃO RESOLVIDO |
| MPU | **NÃO IDENTIFICADO** | NÃO RESOLVIDO |
| FPU versão | VFPv3/v4 (CP10/CP11) | PROVÁVEL |

---

## 2. Evidências

### 2.1 Tabela de vetores no estilo Cortex-M

No payload do bootloader (`0x00000060`):

```text
0x00000060  90 BE 83 00   →  0x0083BE90  (stack pointer inicial)
0x00000064  01 00 82 00   →  0x00820001  (reset handler, bit Thumb ligado)
```

Isso é o layout padrão de vetores Cortex-M.

### 2.2 Confirmação via toolchain upstream

O repositório `ilyakurdyukov/smartlink_flash` compila payloads para o SL6801 com:

```textn.arch armv7-m
.code 16
```

Isso confirma oficialmente que o SL6801 é um **ARMv7-M**.

### 2.3 Instruções Thumb-2 de 32 bits

- `4F F0 FF 30` → `mov.w r0, #0xFFFFFFFF`
- `DF E8 00 F0` → `tbb [pc, r0]`

Ambas são exclusivas de ARMv7-M ou superior.

### 2.4 Instruções VFP

Prefixos `0xEC`, `0xED`, `0xEE` em `0x00E030`–`0x018A90`:
- `vldr`
- `vstr`
- `operações de coprocessador VFP`

Isso indica unidade de ponto flutuante.

### 2.5 Habilitação da FPU via CPACR

Em `0x00CF5B66` o firmware executa:

```asm
ldr  r0, [pc, #0x28]      ; r0 = 0xE000ED88 (CPACR)
ldr  r1, [r0]
orr  r1, r1, #0xF00000    ; CP10=0b11, CP11=0b11
str  r1, [r0]
dsb  sy
isb  sy
```

Esse é o padrão clássico de habilitação da FPU VFP em ARMv7-M. Bits 20-23 de `CPACR` concedem acesso pleno aos coprocessadores 10 e 11 (VFP).

### 2.6 Indicação de núcleo Cortex-M4F

A combinação de:
- arquitetura ARMv7-M;
- instruções Thumb-2 de 32 bits (`tbb`, `mov.w`);
- presença de FPU VFP;
- habilitação de CP10/CP11 via `CPACR`;
- suporte a hard-float no ABI;

aponta fortemente para um **ARM Cortex-M4F**, embora a leitura do registrador `CPUID` ainda não tenha sido rastreada explicitamente.

### 2.5 Endianness

Little-endian é consistente com:
- Decodificação dos campos de cabeçalho.
- Ponteiros na tabela de partições.
- CRCs que conferem sob interpretação LE.

---

## 3. Implicações para Rockbox

O Rockbox suporta oficialmente targets ARM de várias gerações (ARM7TDMI, ARM9, ARM11, Cortex-A, etc.). Para um target Cortex-M, o trabalho seria:

1. Criar um porte "nativo" (não hosted).
2. Implementar camada de HAL para os periféricos do SL6801.
3. Compilar com toolchain ARM (gcc-arm-none-eabi).
4. Linkar para o endereço de RAM onde o bootloader carrega.

A arquitetura ARMv7-M Thumb-2 é **teoricamente compatível** com o Rockbox, mas não existe target similar comprovado que sirva como modelo direto.

---

## 4. Lacunas

| Pergunta | Status | Como confirmar |
|---|---|---|
| Núcleo exato (M4F/M7/M33)? | PROVÁVEL (M4F) | Confirmar leitura de `CPUID` em `0xE000ED00`; ler `MVFR0`/`MVFR1` |
| Frequência? | NÃO RESOLVIDO | Medir clock ou encontrar constantes de PLL no bootloader (string `core pll:%u, cpu pll:%u...` em `0x00C4A415`) |
| MPU presente? | NÃO RESOLVIDO | Procurar acessos a `0xE000ED90` (MPU_TYPE) |
| FPU versão? | PROVÁVEL (VFPv3/v4) | CPACR `0xE000ED88` habilita CP10/CP11; confirmar via `MVFR0`/`MVFR1` |
| ABI (AAPCS, hard-float?)? | PROVÁVEL (AAPCS, hard-float) | As chamadas VFP sugerem hard-float |

---

## 5. Classificação

| Afirmação | Classe |
|---|---|
| CPU é ARM Cortex-M | CONFIRMADO |
| Arquitetura é ARMv7-M Thumb-2 | CONFIRMADO |
| Endianness é little-endian | CONFIRMADO |
| Existe FPU | CONFIRMADO |
| Núcleo exato | PROVÁVEL (Cortex-M4F) |
| Frequência | NÃO RESOLVIDO |
| Compatibilidade geral com Rockbox (CPU) | PROVÁVEL |
