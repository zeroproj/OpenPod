# OpenPod — FIRMWARE_DUMP

Procedimento de obtenção do firmware original do Iigenai GN-438.

| | |
|---|---|
| **Operação** | **SOMENTE LEITURA** |
| **Data do dump** | anterior a 2026-09-11 (executado pelo mantenedor) |
| **Documentado em** | 2026-09-12 |
| **Artefato** | `firmware/ORIGINAL/GN438_original.bin` |
| **Escritas no dispositivo** | **nenhuma** — ver seção 6 |

> Este documento **descreve** um procedimento já realizado. Nada aqui foi
> reexecutado: o firmware já está extraído e verificado, e repetir o dump
> não traria benefício algum.

---

## 1. Ferramenta utilizada

| | |
|---|---|
| **Projeto** | `smartlink_flash` |
| **Repositório** | https://github.com/ilyakurdyukov/smartlink_flash |
| **Autor** | Ilya Kurdyukov |
| **Binário** | `smtlink_dump` |
| **Commit travado** | `49d51d17e825afbbbc2be7d91d6367674543c2e3` (branch `main`) |
| **Data do commit** | 2026-01-27 |
| **Verificado em** | 2026-09-12 |
| **Plataforma usada** | Ubuntu Linux, conexão USB |

A versão exata está travada por hash em
[`tools/external/smartlink_flash.lock`](../tools/external/smartlink_flash.lock),
com SHA-256 de cada um dos 15 arquivos rastreados.

### Por que o código não foi copiado para dentro do OpenPod

O repositório upstream **não possui arquivo de licença**. O cabeçalho de
`smtlink_dump.c` traz apenas uma cláusula de isenção de garantia
("AS IS"), **sem concessão explícita de direito de redistribuição**.

Copiar esse código para dentro do OpenPod — que pode vir a ser publicado —
criaria uma ambiguidade jurídica desnecessária. A alternativa adotada
entrega a mesma reprodutibilidade sem esse risco:

- o commit exato fica registrado;
- o SHA-256 de cada arquivo fica registrado;
- um script obtém e **verifica** essa versão específica.

> Se você preferir versionar uma cópia local mesmo assim, é uma decisão
> sua — basta pedir. O caminho atual é o mais conservador.

### Obtendo e verificando a ferramenta

```bash
# clona o commit travado e confere o hash de cada arquivo
sh tools/external/fetch_smartlink_flash.sh

# ou, se você já tem uma cópia, apenas verifica
sh tools/external/fetch_smartlink_flash.sh --verify-only /caminho/da/copia
```

Saída esperada:

```text
OK — 15 arquivo(s) conferem com a versao travada.
```

O script foi testado em ambos os caminhos: ele aprova uma cópia íntegra e
**reprova** uma cópia adulterada, identificando arquivo ausente e arquivo
divergente.

### Compilação

```bash
cd smartlink_flash
make                # modo libusb  (requer libusb-1.0-dev)
make LIBUSB=0       # modo USB serial, apenas Linux
```

`Makefile` do upstream, para referência:

```make
LIBUSB = 1
CFLAGS = -O2 -Wall -Wextra -std=c99 -pedantic
CFLAGS += -DUSE_LIBUSB=$(LIBUSB)
APPNAME = smtlink_dump
```

---

## 2. Identificação do dispositivo

O GN-438 foi conectado ao Ubuntu via USB e enumerou como:

```text
VID:PID       301a:2801
Manufacturer  SmartlinkTechnology
Product       USB2.0 Device
Serial        20201111000001
```

### Correspondência com a tabela do upstream

O README do `smartlink_flash` documenta, para o **SL6801** em modo
*card reader*:

```text
Card reader: id = 301a:2801,
             inquiry = "SMTLINK CARDREADER 1.00",
             serial  = 20201111000001
```

**Os três valores batem exatamente** com o dispositivo do projeto.

E há uma terceira confirmação, independente: a análise do firmware
encontrou a string `SMTLINK CARDREADER      1.00` no offset `0x00046FBF`
do próprio dump — isto é, o dispositivo declara a mesma identificação que
o upstream associa ao SL6801.

> **Sobre a identificação do SoC.** O `CLAUDE.md` §3 exige que SL6801 não
> seja assumido sem evidência. Hoje existem **três** indícios convergentes:
>
> 1. a string `SL6801` no bootloader (offset `0x0000C184`);
> 2. a correspondência exata de VID:PID + inquiry + serial com a tabela
>    SL6801 do upstream;
> 3. o próprio upstream mantém `payload/sl6801_sys.h` para essa família.
>
> Isso eleva a confiança de **PROVÁVEL** para **PROVÁVEL com alta
> confiança**. Ainda **não é CONFIRMADO**: nenhuma dessas evidências
> inspeciona o silício. A confirmação definitiva exigiria a marcação
> física do chip ou a correspondência de registradores com o datasheet.

### Modos de operação do chip

O upstream documenta dois modos. Saber a diferença importa para a segurança:

| Modo | VID:PID | Como entrar | Observação |
|---|---|---|---|
| **Card reader** | `301a:2801` | conectar normalmente, com cartão inserido | **foi o modo usado** |
| Bootloader | `301a:2800` | desligar e segurar a tecla de boot ao conectar | exige `init`; **não foi usado** |

O dump foi feito em **modo card reader**, sem o comando `init` — que o
upstream avisa explicitamente para **não** usar nesse modo ("it will hang
quickly").

---

## 3. Identificação da flash

```bash
sudo ./smtlink_dump --id 301a:2801 flash_id
```

Resultado:

```text
flash_id: 0x14851485
```

> **Cuidado com a interpretação.** O `CLAUDE.md` §3 adverte que
> `0x14851485` sozinho **não** determina o SoC nem a arquitetura. No
> código do upstream, `flash_id` emite o opcode `CMD_SL_READID` e lê
> 4 bytes — é um identificador do **chip de flash**, não do SoC. O padrão
> repetido (`1485` duas vezes) sugere que o valor de 16 bits `0x1485` é
> ecoado, o que é comum nesses controladores. Permanece
> **NÃO IDENTIFICADO** a qual fabricante/modelo de flash corresponde.

---

## 4. Comando exato do dump

```bash
sudo ./smtlink_dump --id 301a:2801 flash_id read_flash 0 2M GN438_original.bin
```

Decomposição:

| Parte | Significado |
|---|---|
| `sudo` | necessário sem regras udev (ver seção 8) |
| `--id 301a:2801` | seleciona o dispositivo em modo card reader |
| `flash_id` | lê o ID da flash (leitura) |
| `read_flash 0 2M GN438_original.bin` | lê 2 MiB a partir do endereço 0 |

Resultado:

```text
2.097.152 bytes (2 MiB)
faixa 0x00000000 – 0x001FFFFF
```

Este é exatamente o comando documentado pelo upstream para modo card
reader — não houve improviso de sintaxe.

---

## 5. Verificação do artefato

```bash
shasum -a 256 firmware/ORIGINAL/GN438_original.bin
```

```text
b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f
```

| Propriedade | Valor | Estado |
|---|---|---|
| Tamanho | 2.097.152 bytes (2 MiB exatos) | ✅ |
| SHA-256 | `b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f` | ✅ confere |
| Permissões | `-r--r--r--` (444) | ✅ somente leitura |
| Modificações | nenhuma | ✅ |

O hash foi verificado em cada sessão do projeto: na organização inicial,
antes e depois de mover o arquivo, ao criar as cópias de trabalho e ao fim
da Fase 0.5. Continua idêntico.

---

## 6. O procedimento foi READ-ONLY — evidência

Esta seção não repete a afirmação: ela mostra a evidência.

A ferramenta `smtlink_dump` **possui** comandos destrutivos. Os opcodes do
boot ROM, definidos em `smtlink_dump.c`, são:

| Opcode | Constante | Natureza |
|---:|---|---|
| 0 | `CMD_SL_READID` | leitura |
| 2 | `CMD_SL_WRITEPAGE` | **ESCRITA em flash** |
| 3 | `CMD_SL_ERASE4K` | **APAGAMENTO** |
| 4 | `CMD_SL_ERASE32K` | **APAGAMENTO** |
| 5 | `CMD_SL_ERASE64K` | **APAGAMENTO** |
| 6 | `CMD_SL_ERASECHIP` | **APAGA O CHIP INTEIRO** |
| 7 | `CMD_SL_READ` | leitura |
| 8 | `CMD_SL_FASTREAD` | leitura |
| 9 | `CMD_SL_WRITERAM` | **ESCRITA em RAM** |
| 10 | `CMD_SL_RUNRAM` | **EXECUÇÃO** |
| 0x81 | `CMD_SL_INIT` | inicialização |
| 0x82 | `CMD_SL_CRC` | leitura |
| 0x83 | `CMD_SL_RESET` | reset |

O comando utilizado invocou **apenas dois** deles:

- `flash_id` → emite `CMD_SL_READID` (opcode 0);
- `read_flash` → chama `dump_flash()`, que emite **somente**
  `CMD_SL_READ` (opcode 7) em laço, conforme a linha 557 de
  `smtlink_dump.c`.

Portanto, **nenhum** dos seguintes foi executado:

```text
write_flash    NÃO
erase_flash    NÃO
write_mem      NÃO
exec           NÃO
simple_exec    NÃO
init           NÃO
reset          NÃO
```

### Um detalhe que vale registrar

Alguns comandos da ferramenta — `read_mem` e `read_mem2` — **precisam
carregar um payload na RAM do dispositivo** para funcionar, apesar de
"read" no nome. Ou seja, nem todo comando de leitura é isento de escrita.

`read_flash`, porém, **não** é um deles: o upstream o lista entre os
"basic commands supported by the chip's boot ROM", e a leitura do código
confirma que ele não emite `CMD_SL_WRITERAM` nem `CMD_SL_RUNRAM`.

**Conclusão: o dump não escreveu nem na flash nem na RAM do dispositivo.**

---

## 7. Reprodutibilidade

Para reproduzir o procedimento em outro GN-438 — **não é necessário para
este projeto**, o firmware já está extraído:

```bash
# 1. obter e verificar a versão exata da ferramenta
sh tools/external/fetch_smartlink_flash.sh
cd smartlink_flash

# 2. compilar (Ubuntu: sudo apt install libusb-1.0-0-dev)
make

# 3. conectar o GN-438 com um cartão inserido e confirmar a enumeração
lsusb | grep 301a

# 4. identificar a flash
sudo ./smtlink_dump --id 301a:2801 flash_id

# 5. dump somente leitura
sudo ./smtlink_dump --id 301a:2801 flash_id read_flash 0 2M GN438_novo.bin

# 6. verificar
shasum -a 256 GN438_novo.bin
ls -l GN438_novo.bin        # deve ter exatamente 2097152 bytes
```

> Um GN-438 de outra unidade pode produzir um **hash diferente** e isso
> ser normal: a partição `PSMP` guarda configuração gravada em runtime
> (ver `docs/FIRMWARE_MAP.md` §7). Compare as partições `FIRM` e `TONE`,
> não o arquivo inteiro.

---

## 8. Notas operacionais do upstream

### Usar sem `sudo`

Criar `/etc/udev/rules.d/80-smtlink.rules`:

```text
SUBSYSTEMS=="usb", ATTRS{idVendor}=="301a", ATTRS{idProduct}=="2800", MODE="0666", TAG+="uaccess"
SUBSYSTEMS=="usb", ATTRS{idVendor}=="301a", ATTRS{idProduct}=="2801", MODE="0666", TAG+="uaccess"
```

### Modo USB serial (`make LIBUSB=0`, apenas Linux)

```bash
sudo modprobe ftdi_sio
echo 301a 2800 | sudo tee /sys/bus/usb-serial/drivers/generic/new_id
```

### Avisos do upstream

- *"THE SOFTWARE IS PROVIDED AS IS, WITHOUT WARRANTY OF ANY KIND, USE AT
  YOUR OWN RISK!"*
- Não usar `init` em modo card reader — trava.
- Não carregar o payload em modo card reader — resultado imprevisível,
  provavelmente trava o aparelho.
- A tecla de boot varia de aparelho para aparelho; descobre-se por
  tentativa e erro.

---

## 9. Regras que continuam valendo

```text
firmware/ORIGINAL/GN438_original.bin é INTOCÁVEL
    não alterar · não substituir · não regenerar · não sobrescrever

Nenhuma gravação no GN-438 até que estejam resolvidos:
    1. o formato do pacote de boot sdupdate
    2. o método de recuperação em caso de falha

Comandos PROIBIDOS nesta fase do projeto:
    write_flash · erase_flash · write_mem · exec · simple_exec · init
```

---

## 10. Referências cruzadas

| Assunto | Documento |
|---|---|
| Layout da flash e partições | `docs/FIRMWARE_MAP.md` |
| Análise completa do firmware | `docs/FIRMWARE_ANALYSIS.md` |
| Prova de round-trip do rebuild | `docs/REBUILD_VALIDATION.md` |
| Proveniência resumida do dump | `firmware/ORIGINAL/README.txt` |
| Versão travada da ferramenta | `tools/external/smartlink_flash.lock` |
