# Recuperar o GN-438 — Linux

Todos os comandos num terminal normal. **Os passos 1 e 2 não escrevem nada
no aparelho.**

---

## Passo 0 — pôr o aparelho em modo download

```
USB conectado  →  segure VOLUME ↓  →  aperte RESET
```

---

## Passo 1 — confirmar o modo

```bash
lsusb | grep -i 301a
```

Esperado:

```
Bus ... Device ...: ID 301a:2800 ...
```

`2800` é modo bootloader (é o que queremos).
`2801` é card reader — refaça o Passo 0.

Se não aparecer nada, repita o Passo 0 segurando a tecla com firmeza
**antes** de apertar o reset.

---

## Passo 2 — achar a ferramenta

```bash
find ~ -name smtlink_dump -type f 2>/dev/null
```

Anote o caminho. Nos comandos abaixo troque `SMT` por ele.

Se não achar, compile (precisa de `libusb-1.0-dev`):

```bash
cd ~ && git clone https://github.com/ilyakurdyukov/smartlink_flash
cd smartlink_flash && make
```

---

## Passo 3 — LER a flash (não escreve nada)

```bash
sudo SMT init flash_id read_flash 0 2M ~/GN438_bricked_dump.bin
```

Esperado: `flash_id: 0x14851485`, e um arquivo de 2.097.152 bytes.

---

## Passo 4 — me mandar o resultado

Não precisa transferir o arquivo. Rode isto e **cole a saída no chat**:

```bash
ls -l ~/GN438_bricked_dump.bin
sha256sum ~/GN438_bricked_dump.bin
echo "--- setor 0x00D000 (tabela de particoes) ---"
xxd -s 0xD000 -l 128 ~/GN438_bricked_dump.bin
echo "--- cabecalho HLKJ ---"
xxd -s 0 -l 64 ~/GN438_bricked_dump.bin
```

Isso me diz exatamente o que sobrou no setor que matou o aparelho.

**Pare aqui.** Não rode o Passo 5 antes do meu OK.

---

## Passo 5 — GRAVAR o original (só depois do meu OK)

Precisa do firmware no Linux. Copie do Mac:

```
/Users/zeroproj/Documents/Lucas Matheus/OpenPod/firmware/ORIGINAL/GN438_original.bin
```

Confira depois de copiar:

```bash
sha256sum GN438_original.bin
# tem que dar:
# b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f
```

O comando de gravação eu passo depois de ver o dump — a sintaxe exata do
`write_flash` depende do que estiver corrompido.

---

## Passo 6 — conferir

```bash
sudo SMT init read_flash 0 2M ~/GN438_depois.bin
sha256sum ~/GN438_depois.bin
```

Depois desplugue e ligue normalmente.

---

## Problemas

| sintoma | causa |
|---|---|
| `Waiting for connection` | saiu do modo download — refaça o Passo 0 |
| `LIBUSB_ERROR_ACCESS` | falta `sudo` |
| `lsusb` mostra `2801` | está em card reader, não bootloader |
| nada no `lsusb` | refaça o Passo 0 |
