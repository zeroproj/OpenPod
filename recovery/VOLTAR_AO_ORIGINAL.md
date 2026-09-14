# Voltar o GN-438 ao firmware ORIGINAL — retorno planejado

> Este documento é para o caso em que **o aparelho está funcionando** e
> você quer devolvê-lo ao firmware de fábrica de propósito — por exemplo,
> para começar uma nova linha de versões a partir de uma base limpa.
>
> Se o aparelho **não liga ou está sem resposta**, use o outro roteiro:
> **`RECUPERAR.md`**. Ele é de emergência e assume que nada pode ser
> analisado antes.
>
> A diferença prática: aqui dá para **ler primeiro e gravar só o que está
> diferente**. É menos escrita, menos risco, e cada byte gravado tem
> motivo conhecido.

---

## A regra que manda em tudo aqui

```
O write_flash grava A PARTIR DO BYTE 0 DO ARQUIVO.
O 2º argumento NÃO é o deslocamento dentro do arquivo — é sempre 0.
```

Verificado no código-fonte (`ferramenta/smtlink_dump.c`): `src_offs`
entra no cálculo do **tamanho**, mas o ponteiro de dados é `mem[i + j]`,
com `i` começando em zero.

> ⚠️ **NUNCA passe um `.up` para o `write_flash`.** O `.up` tem 0x100
> bytes de cabeçalho `CONFIG`, que cairiam em cima do `HLKJ` do
> bootloader, com tudo 256 bytes adiantado. O `.up` é para o **cartão
> SD**, onde é o bootloader que lê e interpreta o cabeçalho.

---

## Antes de começar

```
sh CONFERIR.sh
```

Só leitura. Confere que os arquivos deste kit estão íntegros.

Condições físicas (regra R6, comprada com um aparelho): **bateria cheia**,
USB direto na máquina — **sem hub** —, cabo que você sabe que transmite
dados, e a máquina sem suspender no meio.

---

## Passo 1 — pôr o aparelho em modo download

```
USB conectado no Mac  →  segure VOLUME ↓  →  aperte RESET
```

Se o macOS mostrar *"O disco inserido não é legível"*, clique em
**Ignorar**.

---

## Passo 2 — confirmar que está no modo certo

Tudo daqui em diante roda no **Terminal.app**, não dentro de outra
ferramenta: o `sudo` precisa de um terminal de verdade para pedir a
senha.

```
ioreg -p IOUSB -w0 -l | grep -E '"(idVendor|idProduct)"'
```

| aparece | significa |
|---|---|
| `12314` e `10240` | `301a:2800` — **modo download**, é este que queremos |
| `12314` e `10241` | `301a:2801` — aparelho normal; ele **não** entrou no modo |
| nada | refaça o Passo 1, segurando a tecla com firmeza **antes** do reset |

No Linux o equivalente é `lsusb | grep 301a`.

---

## Passo 3 — LER a flash  (não escreve nada)

```
cd "/Users/zeroproj/Documents/Lucas Matheus/OpenPod/recovery"

sudo ./ferramenta/smtlink_dump_macos_arm64 init flash_id read_flash 0 2M \
     "../firmware/READBACK/GN438_antes_recovery.bin"
```

Esperado: `flash_id: 0x14851485`, e 1 a 2 minutos de leitura.

Confira o tamanho:

```
ls -l ../firmware/READBACK/GN438_antes_recovery.bin     # 2097152 bytes
```

> **PARE AQUI.** Este dump é a única fotografia do estado atual do
> aparelho. Depois de gravar, ele não existe mais. Mande-o para análise
> antes de seguir.

O que a análise responde, e que nenhum outro passo responde:

- qual versão está realmente no aparelho (e não qual a gente acha que
  está);
- **quais setores** diferem do firmware de fábrica — normalmente são
  poucas dezenas, não os 512;
- se a tabela de partições em `0x00D000` está íntegra;
- se sobrou alguma coisa na área livre.

---

## Passo 4 — gravar só o que está diferente

Da análise sai um kit com **um arquivo por setor divergente**, e um
script que, para cada um:

1. grava o setor (`write_flash <end> 0 0x1000 <arquivo_do_setor>`);
2. **relê aquele mesmo setor** e compara o SHA-256;
3. só então passa para o próximo.

Duas ordens que não são preferência, são regra:

| regra | o quê |
|---|---|
| **R2** | a tabela de partições (`0x00D000`) é **o último** setor da sessão, se é que precisa ser gravada. Depois de cada escrita individual o aparelho tem de continuar bootável |
| **R3** | conferência é por **releitura do aparelho**, nunca por hash de arquivo no PC |

O formato de cada linha é sempre este — o do exemplo real que recuperou
o aparelho em 13/09, quando um único setor precisou voltar:

```
sudo ./ferramenta/smtlink_dump_macos_arm64 init write_flash 0xD000 0 0x1000 ptable_D000_original.bin
```

### Se não houver como analisar o dump

Existe o caminho completo, que grava tudo de fábrica do endereço 0 até o
fim da TONE, direto da imagem de 2 MiB — onde o byte 0 do arquivo já é o
byte 0 da flash, e é isso que torna a linha correta:

```
sudo ./ferramenta/smtlink_dump_macos_arm64 init write_flash 0 0 0x1A3038 ./imagens/GN438_original.bin
```

Isto **reescreve também o bootloader**. É aceitável porque o modo
download vive na ROM de máscara, no silício, e responde mesmo que essa
escrita falhe no meio. Mas é bem mais escrita do que o necessário —
prefira o caminho dos setores sempre que der.

---

## Passo 5 — conferir

```
sudo ./ferramenta/smtlink_dump_macos_arm64 init read_flash 0 2M ./leitura_depois.bin
```

```
python3 - <<'EOF'
a = open('imagens/GN438_original.bin','rb').read()
b = open('leitura_depois.bin','rb').read()
dif = [i for i in range(0x1A3038) if a[i] != b[i]]
print("bytes diferentes de fabrica em 0x000000..0x1A3038:", len(dif))
if dif:
    print("primeiro em 0x%06X" % dif[0])
    print("NAO desligue. Peca analise antes de qualquer outra escrita.")
else:
    print("IDENTICO ao de fabrica. Pode desplugar e ligar.")
EOF
```

**O que fica de fora da comparação, de propósito:**

```
0x1A3038 .. 0x1FC000   área livre — pode ter rotinas do OpenPod, inertes
0x1FC000 .. 0x200000   PSMP — suas configurações de usuário
```

Nenhuma das duas é tocada por este procedimento. Explicação em
`RECUPERAR.md`, seção final.

---

## Passo 6 — ligar

Desplugue e ligue normalmente. O aparelho deve abrir com o logotipo
**GENAI** de fábrica e a home em grade 3×3. Se abrir com a logo do
OpenPod, a gravação não pegou — **não desligue**, avise.

---

## Se algo der errado no meio

**Não desplugue e não desligue.** O modo download está na ROM de
máscara: ele responde mesmo com a flash destruída, e é por ele que a
correção entra. Leia de novo (`read_flash`, que não escreve nada), guarde
o resultado, e peça análise.

A tabela de problemas comuns — `Waiting for connection`, `sudo`,
`LIBUSB_ERROR_TIMEOUT`, silêncio no USB — está em `RECUPERAR.md`.
