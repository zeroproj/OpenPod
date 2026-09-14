# Recuperar o GN-438 — passo a passo

> ⛔ **DOCUMENTO OBSOLETO E PERIGOSO — não siga o Passo 3.**
> Em 2026-09-14 foi verificado no codigo-fonte do `smtlink_dump` que o
> comando `write_flash 0 0 0x1A3038 ... .up` grava o cabecalho CONFIG do
> `.up` em cima do `HLKJ` do bootloader. Nunca foi executado.
> **Use `recovery/RECUPERAR.md`.** Este arquivo fica como registro.

Abra o **Terminal.app** (não o Claude Code) e siga na ordem.

---

## Passo 0 — pôr o aparelho em modo download

```
USB conectado no Mac  →  segure VOLUME ↓  →  aperte RESET
```

Se aparecer no Mac a janela *"O disco inserido não é legível"*, clique em **Ignorar**.

---

## Passo 1 — conferir que está no modo certo

```
ioreg -p IOUSB -w0 -l | grep -E '"(idVendor|idProduct)"'
```

Tem que aparecer `12314` e `10240`. Se não aparecer, repita o Passo 0.

---

## Passo 2 — LER a flash (não escreve nada)

```
sudo /tmp/smtlink_mac init flash_id read_flash 0 2M "/Users/zeroproj/Documents/Lucas Matheus/OpenPod/firmware/READBACK/GN438_bricked_dump.bin"
```

Pede a senha do Mac. Demora 1 a 2 minutos.

Esperado: `flash_id: 0x14851485`

**Pare aqui e me avise.** Eu leio o arquivo e confiro o setor `0x00D000` antes
de qualquer escrita.

---

## Passo 3 — GRAVAR o original (só depois do meu OK)

⚠️ Não rode este passo por conta própria.

```
sudo /tmp/smtlink_mac init write_flash 0 0 0x1A3038 "/Users/zeroproj/Documents/Lucas Matheus/OpenPod/firmware/WORKING/update_restore_original.up"
```

---

## Passo 4 — conferir e ligar

```
sudo /tmp/smtlink_mac init read_flash 0 2M "/Users/zeroproj/Documents/Lucas Matheus/OpenPod/firmware/READBACK/GN438_depois.bin"
```

Depois desplugue e ligue normalmente.

---

## Se algo der errado

- **"Waiting for connection"** → o aparelho saiu do modo download. Refaça o Passo 0.
- **sudo pede senha e não aceita** → tem que ser no Terminal.app, não no Claude Code.
- **Nada aparece no ioreg** → refaça o Passo 0 segurando a tecla com firmeza antes de apertar o reset.
