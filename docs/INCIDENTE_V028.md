# OpenPod — Incidente do V028: escrita falhou em `0x00D000`, aparelho sem resposta

> 2026-09-13. Documento aberto **durante** o incidente, com o estado real
> e não com a conclusão desejada. Será atualizado quando houver dados.

---

## 1. O que aconteceu, na ordem

```text
1ª execução do flash_v028.sh
  [1/6] arquivos de setor conferidos          OK
  [2/6] aparelho detectado 301a:2801          OK
  [2b/6] recovery check: leu 2 MiB inteiros   OK
  [3/6] estado ANTES conferido por SHA-256    OK  (boot, ptable, FIRM, TONE)
  [4/6 1/3] gravando 0xD000
            *** write_flash em 0xD000 FALHOU
            *** WROTE = 1 (contador incrementado ANTES da escrita)

2ª execução
  [2b/6] recovery check: leitura de 2 MiB     LIBUSB_ERROR_TIMEOUT
            *** abortou, nada gravado

Depois disso: o aparelho não liga e não enumera. Silêncio absoluto no USB.
```

## 2. O estado do setor `0x00D000` é DESCONHECIDO

O contador `WROTE` é incrementado **antes** da escrita, de propósito
(decisão da Sessão 24). "1 setor" significa **tentativa**, não sucesso.
As três possibilidades:

| Estado | SHA-256 do setor |
|---|---|
| V027 — nada escrito | `9d11ad554a6559450aa2e1739d4a156fc54fa35bdd1b92bd8e03bea6337a0340` |
| V028 — escrita completou | `4b8957eed9e7136ab409bf6bc023cecaa6325233d10c7569d805b64ff69debdf` |
| qualquer outro | escrita **parcial** — tabela de partições corrompida |

`0x00D000` é a **tabela de partições**, que contém o CRC da FIRM.

## 3. ⚠️ A premissa do projeto que pode estar errada

Desde a Sessão 20 o projeto repetiu que gravar **somente a partir de
`0x00D000`** mantinha a recuperação garantida, porque o bootloader ficava
intocado e o modo card reader continuaria vivo.

**Essa premissa nunca foi verificada de verdade.** E na Sessão 39, ao
desenhar o teste de execução do V020, eu encontrei evidência contra ela:

```text
"CARDREADER"  em  0x00046FC7   ->  dentro da FIRM, NAO no bootloader
bootloader (0x60..0xC94C)      ->  nenhuma string de USB
```

Eu registrei isso em `MENU_HIERARQUIA.md` §8.2, **usei** para escolher uma
cobaia segura para aquele teste, e **não voltei para reavaliar a regra
geral de segurança do projeto.** Classifiquei o risco como pequeno e
segui.

> Se o card reader depende da FIRM rodar, e uma tabela de partições
> corrompida impede o boot, então **a rede de segurança do projeto não
> cobre exatamente o setor mais perigoso que ele grava.**
>
> **Classe: PROVÁVEL.** Consistente com o silêncio observado, mas ainda
> não distinguível de bateria descarregada.

Na Sessão 25 a recuperação funcionou com a tabela corrompida — mas
naquele caso a FIRM provavelmente ainda bootava, porque ela é achada em
`0x0000E000` por cabeçalho próprio. Não é o mesmo caso.

## 4. O que está bloqueando o diagnóstico

**Silêncio absoluto no USB com o aparelho apagado é indistinguível entre
bateria no fundo e aparelho travado.** Nenhum teste separa os dois sem
antes carregar.

Ordem acordada com o mantenedor:

1. confirmar que o cabo transmite dados (testar em outro aparelho);
2. carregador de parede por 1 h, após segurar `▶Ⅱ` por 30 s;
3. só então tentar ligar e rodar `lsusb`.

## 5. Caminhos de recuperação, se o USB não voltar

Ainda **não investigados a fundo**, listados para não se perderem:

| Caminho | O que se sabe |
|---|---|
| `sdupdate` pelo cartão | o bootloader tem código de cartão SD (`sdio(i):uSdCardInf`). A Sessão 24 concluiu que **não há gatilho** a partir da FIRM — mas o comportamento do bootloader **sozinho**, com a FIRM inválida, nunca foi analisado |
| modo de descarga forçado | comum nesta classe de SoC, tipicamente com tecla segurada no boot. **NÃO DETERMINADO** neste aparelho |
| gravador SPI no chip | último recurso, exige abrir |

## 6. O que muda daqui para a frente, independentemente do desfecho

1. **Nenhuma gravação que toque `0x00D000` sem antes provar, no
   aparelho, que o card reader sobrevive à FIRM inválida.** A prova não
   existe hoje.
2. **Ter o `.up` de restauração no cartão antes de gravar**, para que
   exista um caminho que não dependa do USB.
3. **Registrar evidência contrária a uma premissa de segurança como
   revisão da premissa**, não como nota de rodapé de outra análise. Foi
   exatamente o que eu não fiz na Sessão 39.

---

## 6. Análise do bootloader — o que ele faz ao ligar (CONFIRMADO)

Desmontagem de `firmware/ORIGINAL/GN438_original.bin`, região do bootloader
(0x60..0xC94C), viés de RAM `0x0081FB60`. Nada disto é hipótese: são as
instruções que o aparelho executa ao ligar.

### 6.1 A função `boot_main` — 0x008204EC (arquivo 0x00098C)

```
  bl  0x827BF2            -> lê o flag de update no PMU
      printf("boot--->is_pmu_pc_update_flag_set %x")
  bl  0x827C02            -> flag == 7 ?
      se SIM  -> limpa o flag, bl 0x820448 = "update from pc"  (USB)
  bl  0x827C0A            -> flag == 6 ?
      se SIM  -> limpa o flag, init de hardware + LCD,
                 printf("Finding file..."),
                 bl 0x00823CA0 = boot sdupdate  (CARTÃO SD)
  senão   -> printf("boot--->load firmware disp.")
             bl 0x820418  (startup_main)
             bl 0x820DA8  (lê cabeçalho + tabela de partições)
             bl 0x820470  (carrega e SALTA para a FIRM)
             se 0x820470 retornar -> bl 0x820448 = "update from pc"
```

### 6.2 O flag de update mora no PMU, não na flash

`0x00828490` monta um valor de 3 bits a partir de dois registradores do PMU
(lidos por I2C, `0x00820BD0`):

```
    flag = ((reg[0x23] >> 6) << 1) | (reg[0x00] & 1)

    flag == 7  ->  update por USB   (0x008284AE)
    flag == 6  ->  update por SD    (0x008284C0)
```

`HAL_pmu_sd_update_flag_set` (0x0082844C) é quem grava esses bits — e o
**único** lugar que o chama no bootloader é a linha que o LIMPA depois de
usar. Quem SETA o flag é a FIRM, antes de reiniciar.

> **CONFIRMADO:** o `boot sdupdate` existe, está íntegro e é completo
> (FatFs, `0:\update.up`, header `CONFIG`, marca `SL6801`, erase, CRC),
> **mas não é alcançável sem um firmware vivo para armar o flag no PMU.**
> A conclusão da Sessão 24 ("não há gatilho a partir da FIRM") estava
> incompleta, e a esperança de que o bootloader entrasse sozinho em
> sdupdate está **refutada**.

### 6.3 Por que o aparelho morreu — cadeia CONFIRMADA

`0x00820DA8` (arquivo 0x001248) faz, nesta ordem:

```
  memcpy(0x0082C8D0, flash 0x000000, 0x60)     ; cabeçalho HLKJ
  r3 = [hdr + 0x20]                            ; ponteiro da tabela de partições
  se r3 == 0 ou não alinhado em 4 KiB -> r3 = 0x3000
  memcpy(0x0082C92C, r3,            0x100)     ; TABELA DE PARTIÇÕES  <-- 0x00D000
  memcpy(0x0082CA2C, [ptable+0x14], 0x30)      ; descritor de boot
```

E `0x00820470` usa esse descritor:

```
  [0x10] = 0x00804C00   endereço de carga
  [0x14] = 0x00804C01   entry point (Thumb)
  [0x18] = 0x00001000   tamanho
  memcpy(carga, flash, tamanho)  ;  blx entry
```

O setor que a gravação do V028 deixou indeterminado é **exatamente
0x00D000** — a tabela de partições. Com ela corrompida, `[ptable+0x14]`
não aponta mais para 0x0000E000, o `memcpy` lê lixo e o `blx` salta para
um endereço inválido. Isso acontece **antes** de qualquer inicialização
de USB, o que explica o silêncio absoluto no barramento.

Note o detalhe cruel: se `0x00820470` **retornasse**, o bootloader cairia
no modo "update from pc" e o aparelho seria recuperável por USB. Mas ele
não retorna — ele salta para o lixo e trava.

### 6.4 Situação das rotas de recuperação

| rota | estado | custo |
|---|---|---|
| cartão SD com `update.up` | **refutada** — exige flag 6 no PMU, que só a FIRM arma | zero, vale testar mesmo assim |
| USB (`smartlink_flash`) | indisponível — o aparelho trava antes do USB subir | — |
| modo download da ROM de máscara (combinação de teclas) | **NÃO DETERMINADO** — não há evidência no firmware; é comportamento do SoC | zero, vale testar |
| programador SPI externo (CH341A + clipe SOIC8) | **certa** — regrava `GN438_original.bin` byte a byte | abrir o aparelho + ~R$40 |

---

## 7. Veredito: o aparelho não é recuperável (13/09/2026)

### 7.1 Inspeção física da placa

Placa `T90198-MP01-V2`, data `2024-01-02`. As duas faces foram
fotografadas e a área sob a bateria foi inspecionada.

| face | componentes |
|---|---|
| A | SoC QFN `Jointbees MP3 / V57J21B6A0`, slot microSD, USB-C, jack P2, FPC do display, pads `B+`/`B-`/`ADC`, testes `DM`/`DP`/`5V`/`CP` |
| B | 5 domes de botão, FPC `SX177C001-20-P7`, CI `XS4150 82065`, CI `5807M TPB12`, cristal, jack, USB-C |
| sob a bateria | nada — apenas o display |

Os dois únicos CIs de 8 pernas foram identificados: `XS4150` (provável
driver de backlight / amplificador) e `5807M` (provável carga /
conversor). **Nenhum traz `25` na marcação**, convenção universal da
família NOR SPI.

> **CONFIRMADO:** não existe chip de memória externo nesta placa.
> **PROVÁVEL:** a flash de 2 MiB está empilhada dentro do encapsulamento
> do SoC — coerente com a família `SL6801`, que o próprio bootloader
> declara em `0x00C184`.

### 7.2 Todas as rotas, fechadas

| rota | estado final |
|---|---|
| USB (`smartlink_flash`) | o protocolo de escrita mora na FIRM (`"CARDREADER"`, `0x00046FC7`), que não roda |
| USB do bootloader (`update from pc`) | exige flag 7 no PMU, que só a FIRM arma |
| cartão SD (`boot sdupdate`) | exige flag 6 no PMU, idem — testado no aparelho, tela permaneceu apagada |
| programador SPI | **impossível** — não há chip externo para acessar |

O aparelho passa a ser peça de estudo. O que ainda pode render
conhecimento é ligar UART nos pads: o bootloader é muito verboso
(`boot--->load firmware disp.`, `boot--->load_flash_addr= %x`) e isso
confirmaria empiricamente a cadeia de boot reconstruída na §6.

### 7.3 A consequência que importa para o projeto

Se a flash é interna ao SoC, **o aparelho novo não terá rede de
segurança de hardware nenhuma**. Não existe plano B físico.

A única recuperação concebível é armar o flag 6 no PMU e deixar o
bootloader ler `0:\update.up` do cartão — exatamente o que
`HAL_pmu_sd_update_flag_set` (`0x00CF6CA0`, presente na FIRM e nunca
chamada) permite fazer.

Isso reclassifica a **V030 de precaução para pré-requisito**: nenhum
patch cosmético entra no aparelho novo antes de a recuperação por cartão
estar provada funcionando. Ver `docs/PROTOCOLO_GRAVACAO.md`.

---

## 8. Modo bootloader USB (`301a:2800`) — testado e descartado

O README do `smartlink_flash` (ilyakurdyukov) descreve dois modos USB:
card reader `301a:2801` e **bootloader `301a:2800`**, e diz que se entra
nele "turn off the device and hold down the boot key when connecting to
USB", com a ressalva: *"The boot key can be any key, it varies from
device to device."*

Isso levantou a hipótese de que a ROM de máscara do SoC aceitaria a
tecla independentemente do conteúdo da flash — o que tornaria o aparelho
recuperável.

### Evidência estática

| ponto | resultado |
|---|---|
| FIRM chama algum `*_update_flag_set`? | **não** — zero `bl`, zero ponteiro, varredura de 0x0E000 a 0x1A0570 |
| bootloader lê tecla? | **não** — entrada `0x00820000` só zera registradores, ajusta SP, limpa BSS e chama `boot_main`; `boot_main` só lê os flags do PMU |

Ou seja: **este modelo não implementa tecla de boot em software.** A
ressalva do README ("varia de aparelho para aparelho") se explica: em
outros modelos essa lógica mora no firmware. No GN-438, não existe.

### Evidência empírica

Com `udevadm monitor --udev --subsystem-match=usb` rodando, testadas as
teclas `M`, `Vol`, `Play/Pause`, `|<<`, `>>|`, o botão de reset e
combinações, além de um teste de base sem tecla nenhuma:

```
nenhum evento USB, em nenhuma tentativa
```

O aparelho não tenta sequer enumerar. Coerente com a falha em
`blx entry` dentro de `0x00820470`, que ocorre antes de qualquer
inicialização de USB.

> **VEREDITO FINAL: o aparelho não é recuperável.** Todas as rotas
> conhecidas foram verificadas e descartadas com evidência, não com
> suposição.

### O que fica para o aparelho novo

Testar `301a:2800` **enquanto o firmware está vivo** é o primeiro item da
lista, antes de qualquer gravação. Se alguma tecla levar ao modo
bootloader neste hardware, essa é a rede de segurança — de fábrica,
melhor e mais barata que a V030. Se não levar, fica confirmado que este
hardware não tem, e a V030 passa de recomendável a obrigatória.

---

## 9. RESOLVIDO — o aparelho voltou (2026-09-13)

### O que estava quebrado, com dado e não com suposição

Leitura da flash pelo modo download da ROM (`docs/MODO_DOWNLOAD.md`):

```
cabeçalho HLKJ  0x000000   IGUAL ao original          ✅
tabela partições 0x00D000  4096 bytes de 0xFF         ❌  <- o único dano
descritor boot   0x00E000  IGUAL ao original          ✅
```

Das três hipóteses da §2, era a **primeira**: o `write_flash` apagou o
setor e falhou antes de gravar. A tabela nunca recebeu conteúdo.

Assinatura inequívoca: no original esse setor **não tem um único byte
0xFF** — é 0x00 com a tabela nos primeiros 0x40. Encontrar 4096 bytes de
0xFF só pode ser "apagado e não regravado".

### A correção

4096 bytes. Um setor. `ptable_D000_original.bin` gravado em `0x00D000`,
relido e comparado — confere.

O resto da flash (2.093.056 bytes) estava intacto o tempo todo, como o
dump provou. Nada de reescrever 1,7 MB.

### O achado que vale mais que o conserto

O aparelho voltou **rodando OpenPod V027**, não o firmware de fábrica.
A tabela que gravamos é a original, com `CRC da FIRM = 0x49A6` (valor de
fábrica). A FIRM no aparelho é a V027, cujo CRC é outro.

```
tabela diz        CRC = 0x49A6
FIRM real         CRC ≠ 0x49A6
resultado         BOOTOU NORMALMENTE
```

> **CONFIRMADO NO HARDWARE: o CRC da FIRM não é verificado por nada.**

É a regra R1 do `PROTOCOLO_GRAVACAO.md`, respondida empiricamente. O teste
que eu planejei para o aparelho novo e que nunca foi feito em 14
gravações — o aparelho respondeu sozinho ao ser consertado.

**Consequência: `0x00D000` sai do projeto para sempre.** Não precisa nem
do truque de compensação de CRC. O setor que matou o aparelho nunca mais
é tocado por nenhuma versão.

### O erro de julgamento, registrado

Eu declarei "VEREDITO FINAL: o aparelho não é recuperável" na §7, com
tabela de rotas fechadas. Estava errado.

A desmontagem estava correta — a FIRM não arma flag, o bootloader não lê
tecla. O erro foi de **escopo**: concluí sobre o sistema inteiro a partir
das duas camadas que eu conseguia ler, e tratei a terceira (a ROM no
silício) como "não existe" na prática, enquanto no papel eu a classificava
como NÃO DETERMINADO. São coisas diferentes e eu as confundi.

O mantenedor insistiu depois de eu ter encerrado, e trouxe a thread do
Reddit que levou ao manual da Shenju. Foi isso que achou a porta.

**Lição, e ela é a mais cara do projeto:** "não encontrei caminho" nunca
é "não existe caminho". Quando uma camada do sistema é inacessível à
análise, o veredito honesto é NÃO DETERMINADO — e NÃO DETERMINADO não
autoriza declarar nada como final.
