# Recuperação do GN-438 — pasta completa para o Linux

Copie **esta pasta inteira** para a máquina Linux. Tudo que é necessário
está aqui dentro; nada mais precisa ser baixado.

---

## Antes de tudo — modo download

```
USB conectado no Linux  →  segure VOLUME ↓  →  aperte RESET
```

Confira:

```bash
lsusb | grep -i 301a
```

- `301a:2800` → **modo bootloader**, é este que queremos
- `301a:2801` → card reader, refaça segurando a tecla com firmeza
- nada → refaça

---

## Passo 1 — ler (NÃO escreve nada)

```bash
cd OpenPod_Recovery_Linux
./1_ler.sh
```

Ele confere o modo, lê os 2 MiB e imprime os hexdumps.

**Copie tudo o que aparecer depois da linha "COLE DAQUI PARA BAIXO NO CHAT"
e mande para o Claude.** Pare aqui.

Se o binário pronto não rodar (Linux ARM, por exemplo):

```bash
./0_compilar.sh
```

Precisa de `build-essential` e `libusb-1.0-0-dev`.

---

## Passo 2 — gravar (SÓ depois do OK do Claude)

```bash
./2_gravar.sh CONFIRMO
```

Grava o setor `0x00D000` (4096 bytes) com o conteúdo original de fábrica,
relê e compara. Sem a palavra `CONFIRMO` ele não faz nada.

Se disser **CONFERE**, desplugue e ligue o aparelho.
Se disser **NÃO CONFERE**, não desplugue e avise.

---

## O que tem nesta pasta

| arquivo | o que é |
|---|---|
| `1_ler.sh` | leitura + hexdumps (seguro) |
| `2_gravar.sh` | gravação do setor, exige `CONFIRMO` |
| `0_compilar.sh` | compila a ferramenta, se o binário pronto não servir |
| `GN438_original.bin` | firmware de fábrica, 2 MiB — **o arquivo sagrado** |
| `ptable_D000_original.bin` | só o setor `0x00D000`, 4 KiB, pronto para gravar |
| `update_restore_original.up` | imagem `.up` completa (plano B, restaura tudo) |
| `ferramenta/` | `smtlink_dump` (binário x86-64 + código-fonte) |
| `SHA256SUMS` | conferência de integridade |

Conferir depois de copiar:

```bash
sha256sum -c SHA256SUMS
```

---

## Por que só 4 KiB

O aparelho não boota porque o setor `0x00D000` — a tabela de partições —
foi corrompido por uma escrita que falhou no meio. O bootloader lê dali o
ponteiro `ptable+0x14 = 0x0000E000` para achar o firmware; sem ele, salta
para lixo e trava antes de o USB subir.

O resto da flash (2.093.056 dos 2.097.152 bytes) está intacto. Por isso a
correção é um setor, não a imagem inteira: menos escrita, menos risco,
mais rápido.

O `.up` completo fica aqui como plano B, caso o dump mostre dano em mais
lugares.

---

## Se der errado

| sintoma | o que fazer |
|---|---|
| `Waiting for connection` | saiu do modo download — VOLUME ↓ + RESET |
| `LIBUSB_ERROR_ACCESS` | faltou `sudo` |
| `lsusb` mostra `2801` | está em card reader — refaça |
| dump menor que 2097152 | leitura interrompida, não vale — repita |
| binário não executa | `./0_compilar.sh` |
