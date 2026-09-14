# Protocolo de gravação — regras nascidas do incidente V028

> Escrito depois de brickar o primeiro GN-438 em 13/09/2026.
> Cada regra aqui tem um custo já pago. Não flexibilize nenhuma "só desta vez"
> — foi exatamente esse raciocínio que matou o aparelho.

Contexto completo da falha: `docs/INCIDENTE_V028.md`.

---

## R0 — A rede de segurança JÁ EXISTE, de fábrica  ✅ RESOLVIDA

**O SoC tem modo de download na ROM de máscara**, alcançável mesmo com a
flash destruída:

```
USB conectado  ->  segure VOLUME ↓  ->  aperte RESET
```

O aparelho enumera como `301a:2800` e o `smtlink_dump` lê e grava a flash
inteira. Confirmado no hardware em 2026-09-13, recuperando o aparelho
brickado. Procedimento completo em `docs/MODO_DOWNLOAD.md`; pasta pronta
em `OpenPod_Recovery_Linux/`.

> **Este hardware é recuperável por software, sempre.** Nenhum patch pode
> deixá-lo inacessível: a ROM está no silício e roda antes de qualquer
> coisa que a gente escreva.

As regras abaixo continuam valendo — elas reduzem a chance de precisar da
recuperação — mas **o custo de errar deixou de ser o aparelho**.

### R0-antiga (obsoleta) — programador SPI antes do primeiro patch

Nenhuma gravação no aparelho novo antes de existirem, as duas:

1. **Programador SPI em mãos** (CH341A 3,3 V ou Pi Pico + `flashrom`) e clipe
   SOIC8, TESTADO lendo a flash e conferindo o SHA-256 contra
   `b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f`.
2. **Dump próprio do aparelho novo**, guardado em `firmware/ORIGINAL/`, modo 444.

Com R0 cumprida, brick deixa de ser fatal e vira 20 minutos de chateação.
Sem R0, toda gravação é uma aposta com o aparelho inteiro.

## R1 — 0x00D000 NUNCA MAIS É GRAVADO  ✅ RESOLVIDA

**O CRC da FIRM não é verificado por nada.** CONFIRMADO no hardware em
2026-09-13: o aparelho foi consertado gravando a tabela de partições de
fábrica (`CRC = 0x49A6`) por cima de uma FIRM que é a OpenPod V027, cujo
CRC é outro. **Bootou normalmente.**

Portanto o campo de CRC pode ficar desatualizado para sempre, e o setor
`0x00D000` — que contém o ponteiro de boot e que matou o primeiro
aparelho — **sai do projeto**. Não precisa nem da compensação de CRC do
`tools/crc_neutralize.py` (que continua correta e disponível, mas deixa
de ser necessária).

Todo kit daqui em diante é gerado a partir de uma imagem cuja tabela de
partições é a de fábrica, o que faz o setor sumir da lista de diferenças
automaticamente.

### R1-antiga (cumprida) — o experimento que respondeu isto

A tabela de partições divide setor de 4 KiB com o ponteiro que o bootloader
segue para achar a FIRM (`ptable+0x14 = 0x0000E000`). Apagar 4096 bytes para
mudar 2 bytes de CRC foi a causa direta do brick.

**Primeiro experimento no aparelho novo** (2 setores, 0x00D000 intocado):
gravar uma mudança de 1 byte na FIRM **sem** atualizar o CRC.

- bootou e funcionou -> o CRC não é verificado; **0x00D000 nunca mais é gravado**
- não bootou        -> o CRC é obrigatório; então vale R2 sem exceção

O caminho de carga do bootloader (`0x00820470`) não confere CRC nenhum
(CONFIRMADO por desmontagem). Se algo mais confere é NÃO DETERMINADO — e é
justamente o teste que nunca rodei antes de regravar esse setor 14 vezes.

## R2 — Ordem: setor crítico por último, sempre

Se 0x00D000 precisar mesmo ser gravado, ele é o **último** da sessão. O kit
V028 gravava ele em primeiro lugar (`4/6 1/3`), deixando a janela de risco
aberta durante a gravação inteira. Regra geral:

> Depois de cada `write_flash` individual, o aparelho tem que continuar
> bootável. Se algum estado intermediário não boota, a ordem está errada.

## R3 — Verificação por releitura, não por hash de arquivo

O kit conferia o SHA-256 dos **arquivos no PC**. Isso não prova nada sobre o
que chegou na flash. Todo `write_flash` passa a ser seguido de `read_flash`
do mesmo setor e comparação de hash, **antes** de passar para o próximo.

## R4 — Gravação nunca combina risco novo com setor crítico

Uma versão introduz **ou** um mecanismo novo **ou** uma mudança em setor de
metadados. Nunca os dois na mesma sessão.

## R5 — Evidência contra uma regra de segurança força revisão datada

A regra "nunca gravar abaixo de 0x00D000 mantém a recuperação por USB" tinha
evidência contra ela desde a Sessão 39 (`"CARDREADER"` em `0x00046FC7`, dentro
da FIRM). Usei a evidência localmente e nunca voltei para revisar a regra.

Toda regra de segurança carrega agora: **premissa**, **como foi verificada**,
**data**. Evidência contraditória abre revisão imediata e documentada.

## R6 — Condições físicas da gravação

Bateria cheia, USB direto na placa-mãe (sem hub), nada de suspender a máquina,
cabo conhecido. A gravação da V028 falhou no meio por motivo nunca
determinado — endurecer o que é barato endurecer.

---

## A rede de segurança de software: V030

`HAL_pmu_sd_update_flag_set` **existe dentro da FIRM**, em `0x00CF6CA0`,
completa e funcional — e **nada no firmware inteiro a chama** (zero `bl`, zero
ponteiro; varredura de 0x0E000 a 0x1A0570).

```asm
00CF6CA0  push {r4, lr}
00CF6CA2  mov  r1, r0
00CF6CA4  mov  r4, r0
00CF6CA6  ldr  r0, =0x00C4925F     ; "HAL_pmu_sd_update_flag_set %d"
00CF6CA8  bl   printf
00CF6CAC  movs r0, #0x23
00CF6CAE  cbz  r4, #0xcf6cd4
00CF6CB0  bl   pmu_read            ; reg 0x23
00CF6CB4  orn  r1, r0, #0x3f       ; bits 7:6 <- 11
00CF6CBC  bl   pmu_write
00CF6CC0  movs r0, #0
00CF6CC2  bl   pmu_read            ; reg 0x00
00CF6CCA  and  r1, r0, #0xfe       ; bit 0 <- 0
00CF6CD0  b.w  pmu_write
```

Resultado: `flag = ((reg23>>6)<<1) | (reg00&1) = 6` = **update por cartão SD**.

Chamar `0x00CF6CA0` com `r0 = 1` e reiniciar faz o bootloader entrar em
`boot sdupdate`, procurar `0:\update.up` e regravar a flash — sem PC, sem USB,
sem abrir o aparelho.

### Estado

| item | classificação |
|---|---|
| a função existe e está íntegra na FIRM | CONFIRMADO (desmontagem) |
| ninguém a chama no firmware original | CONFIRMADO (varredura de `bl` e ponteiros) |
| chamá-la arma o flag 6 no PMU | PROVÁVEL (o código é idêntico ao do bootloader) |
| o bootloader então executa o sdupdate | CONFIRMADO (desmontagem de `boot_main`) |
| `update_restore_original.up` é aceito pelo sdupdate | NÃO DETERMINADO — nunca testado num aparelho |

### Plano da V030 — a versão da recuperação, antes de qualquer cosmético

- **V030a** — item "Atualizar por SD" em Configurar: chama `0x00CF6CA0(1)` e
  reinicia. Testa a cadeia inteira com o aparelho sadio e com o `.up` de
  restauração no cartão. Se voltar sozinho ao original, a rede está de pé.
- **V030b** — o mesmo gatilho por **tecla segurada no boot da FIRM**, para
  funcionar mesmo com a GUI quebrada. É essa versão que transforma brick de
  GUI em "põe o cartão e liga".

Só depois disso a V031 retoma a fila cosmética (V028 fundo preto das linhas,
V029 roteamento do Extras), ambas já construídas e validadas.

### A ordem certa, agora explícita

```
programador SPI em mãos  ->  dump do aparelho novo  ->  V030 (recuperação por SD)
    ->  então, e só então, interface
```

Recuperação primeiro. Beleza depois.

---

## R7 — A versão mostrada acompanha a versão publicada

A tela `Configurar → Informações` lê um literal em `0x0010A59C`. Ele
**não** se atualiza sozinho: foi criado na OpenPod 1.0 e continuou
dizendo "1.0" depois da 1.1 ser gravada — o aparelho mentindo sobre si
mesmo. Pego pelo mantenedor, não por mim.

**Toda release roda:**

```bash
python3 tools/patch_versao.py --in <atual> --out <novo> \
    --texto "OpenPod X.Y\nBase: yp3_2.0.43"
```

A ferramenta aceita tanto o literal de fábrica quanto um já repontado.

> Um aparelho que informa a versão errada é pior que um que não informa
> nada: você confia no número e depura a coisa errada.
