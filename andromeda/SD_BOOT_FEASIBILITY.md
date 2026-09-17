# ANDROMEDA — SD_BOOT_FEASIBILITY

## A investigação mais importante do ANDROMEDA

---

## 1. Pergunta central

> **É possível usar o bootloader interno do GN-438 para carregar código do microSD, transferi-lo para RAM e executá-lo?**

A arquitetura hipotética é:

```text
┌───────────────────────────┐
│ INTERNAL FLASH            │
│                           │
│ Bootloader (preservado)   │
│    ↓                      │
│ SD Loader (patch?)        │
└────────────┬──────────────┘
             │
             │ read
             ↓
┌───────────────────────────┐
│ MICROSD                   │
│                           │
│ /ANDROMEDA/               │
│   boot.bin                │
│   rockbox.bin             │
│   resources/              │
└────────────┬──────────────┘
             │
             ↓
┌───────────────────────────┐
│ SRAM                      │
│                           │
│ ANDROMEDA / ROCKBOX       │
└────────────┬──────────────┘
             ↓
          EXECUTE
```

Esta é uma **hipótese**. A análise abaixo a testa.

---

## 2. SD UPDATE ≠ SD BOOT

É fundamental distinguir:

| | SD UPDATE | SD BOOT |
|---|---|---|
| Fonte | microSD | microSD |
| Destino | Flash interna | RAM |
| Resultado | firmware reescrito | código executado sem reescrever flash |
| Risco | médio (bootloader preservado) | depende da implementação |
| Existe no GN-438? | **SIM** (`boot sdupdate`) | **NÃO** |

O mecanismo atual prova que o bootloader consegue ler o SD. Não prova que consegue executar código do SD.

---

## 3. O que o bootloader já faz

### 3.1 Boot normal

```text
Flash interna (FIRM)
    ↓
copia 4 KiB para 0x00804C00
    ↓
blx 0x00804C01
```

### 3.2 SD update

```text
microSD → update.up
    ↓
valida cabeçalho
    ↓
apaga setores da flash
    ↓
grava flash
    ↓
verifica CRC
```

### 3.3 O que falta para SD Boot

```text
microSD → boot.bin
    ↓
le para RAM
    ↓
configura stack / vector table
    ↓
blx endereco_ram
```

Não existe função no bootloader que faça isso. Mas as primitivas (`f_read`, buffers de RAM, `blx`) existem.

---

## 4. Análise das etapas necessárias

| Etapa | Bootloader faz? | Evidência | Confiança |
|---|---|---|---|
| 1. Inicializar SD | SIM | `f_mount(0)` no sdupdate | CONFIRMADO |
| 2. Abrir arquivo | SIM | `f_open("0:\update.up")` | CONFIRMADO |
| 3. Ler arquivo | SIM | `f_read` em loop | CONFIRMADO |
| 4. Copiar conteúdo para RAM | PARCIAL | Só copia da flash interna (`flash_read`); não do SD | NÃO DIRETAMENTE |
| 5. Preparar CPU | SIM | Desativa interrupções, limpa caches no boot normal | PROVÁVEL |
| 6. Configurar stack | SIM | Usa SP do vetor da FIRM | CONFIRMADO |
| 7. Configurar vector table | NÃO DIRETAMENTE | Boot normal carrega vetor da FIRM em RAM; não configura VTOR explicitamente | PROVÁVEL |
| 8. Fazer jump para RAM | SIM | `blx r6` para `0x00804C01` | CONFIRMADO |

---

## 5. Arquiteturas possíveis

### Modelo A — Rockbox inteiro no SD, carregado para RAM

```text
SD → rockbox.bin → RAM → executa
```

**Problema:** depende do tamanho da RAM, que ainda não é conhecido. Rockbox completo tipicamente precisa de centenas de KiB a poucos MiB.

### Modelo B — Kernel na RAM, recursos sob demanda

```text
SD → kernel.bin → RAM
RAM → lê recursos do SD conforme necessário
```

**Problema:** exige filesystem no SD acessível pelo novo sistema. Tecnicamente plausível, mas requer drivers.

### Modelo C — Loader pequeno na flash, módulos no SD

```text
Flash: loader mínimo
SD:    múltiplos módulos
RAM:   loader carrega módulos dinamicamente
```

**Problema:** requer modificar o bootloader ou a FIRM para instalar o loader.

### Modelo D — Execução direta do SD (XIP)

```text
SD mapeado como memória executável
```

**Problema:** cartões SD não são memórias mapeadas. XIP de SD não é padrão em Cortex-M. **INVÁVEL** para SD comum.

---

## 6. Fallback desejável

```text
SD presente  → carrega ANDROMEDA
SD ausente   → inicia firmware original
```

Essa arquitetura é **extremamente desejável**, mas requer:
- Um loader no bootloader ou na FIRM.
- Decisão em runtime: SD tem `ANDROMEDA/boot.bin`?
- Se sim, carrega e salta.
- Se não, continua o boot normal.

Não há evidência de que isso seja possível sem modificação.

---

## 7. Tamanho do loader

Um SD loader mínimo precisaria:

| Componente | Tamanho estimado |
|---|---|
| Inicialização | ~50 B |
| SD init (reusar ou reimplementar) | ~1–4 KiB |
| Abrir arquivo (FatFs) | já presente no bootloader |
| Ler arquivo | já presente |
| Cópia para RAM | ~20 B |
| Validação (CRC/magic) | ~100 B |
| Jump | ~10 B |
| **Total** | **~1–5 KiB** se reutilizar funções do bootloader |

Se o loader puder chamar as funções do bootloader por endereço fixo, ele pode ser muito pequeno. Se precisar reimplementar tudo, cresce para dezenas de KiB.

---

## 8. Onde colocar o loader

### Opção 1 — Modificar o bootloader

- **Risco:** alto. Corromper o bootloader pode brickar o aparelho.
- **Vantagem:** controle total do fluxo de boot.
- **Tamanho disponível:** o bootloader ocupa 51.436 bytes; há espaço limitado até `0x0000D000`.

### Opção 2 — Instalar loader na FIRM

- **Risco:** médio. A FIRM pode ser recuperada via SD update.
- **Vantagem:** não toca no bootloader.
- **Mecanismo:** a FIRM modificada, ao iniciar, verifica SD e salta para código carregado.
- **Problema:** não é "SD Boot" puro; é "aplicativo que se auto-substitui".

### Opção 3 — Área livre da flash

- A área `0x001A3038`–`0x001FBFFF` (364 KiB) está livre.
- O bootloader não executa código dessa área no boot normal.
- Seria necessário redirecionar o boot para lá — o que exige modificar o bootloader ou a FIRM.

---

## 9. Veredito preliminar

| Pergunta | Resposta | Confiança |
|---|---|---|
| O GN-438 consegue executar código externo? | SIM, via RAM | CONFIRMADO (boot normal já faz isso) |
| O bootloader consegue acessar o SD? | SIM | CONFIRMADO |
| O bootloader consegue carregar código na RAM? | PARCIAL | As primitivas existem, mas não há caminho pronto |
| O bootloader consegue transferir execução para RAM? | SIM | CONFIRMADO |
| É tecnicamente possível criar um SD loader? | PROVÁVEL | Requer patch no bootloader ou na FIRM |
| É seguro? | DEPENDE | Modificar bootloader = alto risco; modificar FIRM = médio risco |

---

## 10. Conclusão

SD Boot **não existe pronto** no GN-438, mas as peças necessárias estão presentes:

- O bootloader lê arquivos do SD.
- O bootloader copia código para RAM e executa.
- Existe área livre na flash para um loader.
- O mecanismo de recuperação por SD update pode mitigar riscos.

A implementação seria um projeto de engenharia reversa significativo:

1. Determinar tamanho total da RAM.
2. Escolher entre patch no bootloader (mais limpo, mais arriscado) ou hook na FIRM (mais seguro, menos "boot").
3. Implementar/reutilizar drivers de SD.
4. Criar formato de imagem para o SD.
5. Validar em hardware.

Para ANDROMEDA, a classificação é:

> **SD Boot é PROVÁVEL do ponto de vista técnico, mas não trivial e com risco não negligenciável.**
