# OpenPod — SD_UPDATE_PROCEDURE

Procedimento para instalar um pacote `update.up` no GN-438.

| | |
|---|---|
| **Natureza** | **grava a flash do aparelho** — irreversível sem recuperação |
| **Pré-requisitos** | todos atendidos em 2026-09-12 (§1) |
| **Recuperação** | validada — leitura e escrita por USB confirmadas |

---

## 1. Pré-requisitos — todos ✅

| # | Pré-requisito | Estado |
|---|---|---|
| 1 | Firmware original preservado e verificado | ✅ `b7cd5eb9…`, 444 |
| 2 | Original confere com o aparelho | ✅ regiões críticas idênticas |
| 3 | Leitura por USB funciona | ✅ `RECOVERY_CHECK.md` |
| 4 | **Escrita e apagamento por USB funcionam** | ✅ `WRITE_TEST_RESULT.md` |
| 5 | Pacote validado | ✅ 11 checks + idêntico ao `fwhelper` |
| 6 | Pacote de restauração pronto | ✅ `firmware/SDCARD_restore/` |

---

## 2. ⚠️ O caminho na interface — NÃO LOCALIZADO

> **Estado em 2026-09-12: o gatilho não foi identificado.**
>
> O caminho `Configurações → Opções de actualização → Actualização do
> cartão SD` **não existe** no menu deste aparelho. Verificado pelo
> mantenedor, com e sem cartão.
>
> **Este procedimento está BLOQUEADO do Passo 2 em diante.**
> O Passo 1 (preparar o cartão) e os Passos 4–5 (verificação) continuam
> válidos. Ver `UPDATE_MECHANISM.md` §2.1.

Textos extraídos do firmware (bloco em português, `0x054404`–`0x0544C3`):

```text
Configurações
  └─ Opções de actualização          (0x054425)
       ├─ Actualização do PC          (0x0544AE)
       └─ Actualização do cartão SD   (0x0544C3)   <<< esta
```

Internamente esse item chama a função `0x00CF9D3C` com a string `"sd"`,
que grava o flag no PMU (registrador `0x23`, bits[2:0] = 6) e reinicia —
`UPDATE_MECHANISM.md` §2.

> Se o cartão não estiver presente, o aparelho responde
> **"Não foram detectados dispositivos de armazenamento"** (`0x0544E0`).

---

## 3. ⚠️ Antes de começar

### Carregue a bateria

O próprio firmware avisa, em oito idiomas:

> *"Please keep the battery enough before upgrading"* (`0x05D0FC`)

Uma queda de energia no meio da gravação é o cenário que mais se aproxima
de um brick real. **Carregue até o fim antes.**

### Tenha o cartão de restauração separado

Prepare **dois** cartões, ou um cartão e a pasta de restauração à mão:

| Pasta do projeto | Para quê |
|---|---|
| `firmware/SDCARD_v001/update.up` | instalar o V001 |
| `firmware/SDCARD_restore/update.up` | voltar ao firmware original |

Os dois arquivos já estão **com o nome correto**. Não renomeie.

---

## 4. Procedimento

### Passo 1 — preparar o cartão

```text
1. cartão em FAT32 (ou exFAT)
2. copiar  firmware/SDCARD_v001/update.up  para a RAIZ do cartão
3. conferir: o arquivo tem de se chamar exatamente  update.up
             e estar na raiz, não em subpasta
```

> O bootloader procura o literal `0:\update.up`. Nome diferente, ou dentro
> de pasta, e ele não encontra — **CONFIRMADO** por disassembly.

Conferência opcional do arquivo no cartão:

```bash
shasum -a 256 /Volumes/<cartao>/update.up
# esperado: b45bcf6d5f20f3836b935692f52fb35302536feb2b90edfa5345b8c0224ec314
```

### Passo 2 — inserir e navegar

```text
1. desligar o aparelho
2. inserir o cartão
3. ligar
4. Configurações → Opções de actualização → Actualização do cartão SD
```

### Passo 3 — acompanhar a tela

O aparelho reinicia e o **bootloader** assume. A sequência esperada, pelas
strings do próprio bootloader:

| Tela | Origem |
|---|---|
| `Finding file...` | `0x00829CBC` |
| `Update...  %` / `Update...100%` | `0x00829DBB` / `0x00829CFD` |
| `Update finish!` | `0x00829CEE` |

> **Se a tela não mostrar nada disso**, o `sdupdate` não chegou a começar —
> provavelmente o arquivo não foi encontrado. Nesse caso **nada foi
> gravado**: as validações acontecem antes de qualquer apagamento
> (`UPDATE_MECHANISM.md` §4).

### Passo 4 — verificar

Depois que o aparelho reiniciar normalmente:

```text
1. abrir o menu principal
2. o ícone de Música (disco de vinil, canto superior esquerdo)
   deve estar AZUL em vez de prata — com o miolo vermelho preservado
```

Os outros oito ícones não devem ter mudado.

### Passo 5 — confirmar por leitura (recomendado)

No Ubuntu, leitura pura:

```bash
sudo ./smtlink_dump --id 301a:2801 flash_id read_flash 0 2M after_v001.bin
```

E no projeto:

```bash
python3 tools/verify_device_readback.py after_v001.bin \
    --ref firmware/WORKING/GN438_openpod_v001.bin
```

Esperado: todas as regiões críticas **idênticas ao V001**, com divergência
apenas na `PSMP`.

---

## 5. Se algo der errado

### O aparelho liga normalmente, mas você quer voltar

Use `firmware/SDCARD_restore/update.up` — mesmo procedimento, §4.

### O aparelho não carrega a aplicação

O bootloader cai sozinho em **"update from pc"**
(`UPDATE_MECHANISM.md` §1). Nesse estado o cartão **não resolve**: o
`sdupdate` depende da aplicação ligar o flag do PMU.

Recuperação por USB:

```bash
# 1. confirmar que enumera
lsusb | grep 301a

# 2. regravar a partir do original preservado
sudo ./smtlink_dump --id 301a:2801 \
    write_flash 0 0 0x200000 GN438_original.bin

# 3. conferir
sudo ./smtlink_dump --id 301a:2801 read_flash 0 2M check.bin
python3 tools/verify_device_readback.py check.bin
```

> **A escrita por USB foi validada em 2026-09-12** (`WRITE_TEST_RESULT.md`).
> Não é um caminho teórico.
>
> **Ressalva honesta:** o teste validou uma escrita de 4 KiB em área livre.
> Uma escrita de 2 MiB cobrindo o bootloader é **PROVÁVEL** que funcione
> por extrapolação, mas **não foi exercitada**. Se chegar a esse ponto,
> considere gravar primeiro só a partir de `0x00D000` (preservando o
> bootloader, que estará intacto) antes de tentar a flash inteira.

### O aparelho não liga nem enumera

**NÃO DETERMINADO.** Não há procedimento conhecido. Preserve o estado e
não force nada.

---

## 6. O que este procedimento NÃO garante

| Item | Classe |
|---|---|
| O V001 inicializa | **NÃO DETERMINADO** — é o que o teste descobre |
| A verificação de timestamp não vai recusar | **NÃO DETERMINADO** — se recusar, nada acontece |
| A TONE não perde 56 bytes | **PROVÁVEL** que perca; provavelmente cosmético |
| Uma gravação de 1,6 MB se comporta como a de 4 KiB testada | **PROVÁVEL** |

---

## 7. Resumo em uma tela

```text
□ bateria carregada
□ cartao FAT32, com  update.up  na RAIZ (nome exato)
□ sha256 do arquivo confere
□ cartao de restauracao preparado
□ maquina Ubuntu disponivel, caso precise do USB

  Configuracoes -> Opcoes de actualizacao -> Actualizacao do cartao SD

□ tela mostrou "Finding file..."
□ tela mostrou progresso
□ tela mostrou "Update finish!"
□ aparelho reiniciou
□ icone de Musica esta AZUL
□ leitura de conferencia bate com o V001
```
