# Voltar o GN-438 ao firmware ORIGINAL — retorno planejado

> Para quando **o aparelho está funcionando** e você quer devolvê-lo ao
> firmware de fábrica de propósito — por exemplo, para começar uma nova
> linha de versões a partir de uma base limpa.
>
> Se o aparelho **não liga ou não responde**, o roteiro é o outro:
> **`RECUPERAR.md`**.
>
> A diferença não é de tom, é de método: com o aparelho vivo dá para
> **ler primeiro e gravar só o que está diferente**. Menos escrita, e
> cada byte gravado com motivo conhecido.

**Feito para Linux.** Os scripts também rodam no macOS, mas o Linux é o
caminho testado — foi por ele que o aparelho voltou em 13/09.

---

## Antes de tudo

```sh
cd recovery
sh CONFERIR.sh
```

Só leitura: confere que os arquivos deste kit estão íntegros.

**Condições físicas** (regra R6, comprada com um aparelho): bateria
cheia, USB **direto na placa-mãe, sem hub**, cabo que você sabe que
transmite dados (há cabos que só carregam), e a máquina sem suspender no
meio.

---

## A regra que manda em tudo aqui

```
O write_flash grava A PARTIR DO BYTE 0 DO ARQUIVO.
O 2º argumento NÃO é o deslocamento dentro do arquivo — é sempre 0.
```

Verificado no código-fonte (`ferramenta/smtlink_dump.c`): `src_offs`
entra no cálculo do tamanho, mas o ponteiro de dados é `mem[i + j]`, com
`i` começando em zero.

> ⚠️ **NUNCA passe um `.up` para o `write_flash`.** O `.up` tem 0x100
> bytes de cabeçalho `CONFIG`, que cairiam em cima do `HLKJ` do
> bootloader, com tudo 256 bytes adiantado. O `.up` é para o **cartão
> SD**, onde quem lê e interpreta o cabeçalho é o bootloader.

---

## Passo 0 — a ferramenta roda nesta máquina?

```sh
./ferramenta/smtlink_dump_linux_x86_64 2>&1 | head -3
```

Se reclamar de arquitetura ou de biblioteca faltando:

```sh
./0_COMPILAR.sh
```

Ele compila `ferramenta/smtlink_dump` a partir do fonte que está aqui.
Precisa de `build-essential` e `libusb-1.0-0-dev` (o script mostra a
linha certa para Debian/Ubuntu, Fedora e Arch). Os outros scripts passam
a usar o binário compilado sozinhos.

---

## Passo 1 — pôr o aparelho em modo download

```
USB conectado  →  segure VOLUME ↓  →  aperte RESET
```

Este modo vive na **ROM de máscara do SoC** — roda antes de qualquer
coisa que a gente tenha gravado. É a razão de este hardware ser sempre
recuperável por software.

---

## Passo 2 — LER a flash  (não escreve nada)

```sh
./1_LER.sh
```

O script, em ordem: escolhe o binário certo, confere que o aparelho está
em `301a:2800` (e **recusa** se estiver em `2801`, que é o modo normal),
lê os 2 MiB, e imprime um bloco pronto para colar no chat com:

- tamanho e SHA-256 do dump;
- o hash do firmware de fábrica ao lado — se forem iguais, o aparelho já
  está original e não há nada a gravar;
- o cabeçalho `HLKJ` em `0x000000`;
- a **tabela de partições** em `0x00D000`, que é o que mais importa;
- o início da FIRM em `0x00E000`;
- a string de versão que aparece na tela Informações.

O dump fica em:

```
recovery/leitura/GN438_antes_recovery.bin
```

> **PARE AQUI.** Esse arquivo é a única fotografia do estado atual do
> aparelho — depois de gravar, ele não existe mais. Mande o bloco
> impresso, e o arquivo se der.

O que a análise responde, e nenhum outro passo responde: qual versão está
**realmente** no aparelho, **quais setores** diferem de fábrica
(normalmente algumas dezenas, não os 512), se a tabela de partições está
íntegra, e o que sobrou na área livre.

---

## Passo 3 — gravar só o que está diferente

Da análise sai um kit com **um arquivo por setor divergente** e um
script que, para cada um:

1. grava o setor — `write_flash <endereço> 0 0x1000 <arquivo_do_setor>`;
2. **relê aquele mesmo setor** do aparelho e compara o SHA-256;
3. só então passa para o próximo.

Duas ordens que não são preferência, são regra paga com aparelho:

| regra | o quê |
|---|---|
| **R2** | a tabela de partições (`0x00D000`) é **o último** setor da sessão, se é que precisa ser gravada. Depois de cada escrita individual o aparelho tem de continuar bootável |
| **R3** | conferência é por **releitura do aparelho**, nunca por hash de arquivo no PC |

O formato de cada linha é sempre este — o exemplo real que recuperou o
aparelho em 13/09, quando um único setor precisou voltar:

```sh
sudo ./ferramenta/smtlink_dump_linux_x86_64 init write_flash 0xD000 0 0x1000 ptable_D000_original.bin
```

---

## Passo 3-alternativo — gravar tudo, se não houver análise

```sh
./9_GRAVAR_TUDO.sh CONFIRMO
```

Grava `0x000000..0x1A3038` direto da imagem de 2 MiB — onde o byte 0 do
arquivo já é o byte 0 da flash, e é isso que torna a linha correta. Ele
confere o SHA-256 da imagem de origem antes de começar, e relê os 2 MiB
no fim para comparar.

Isto **reescreve também o bootloader**. É aceitável porque o modo
download está no silício e responde mesmo que a escrita falhe no meio —
mas é bem mais escrita do que o necessário. **Prefira o Passo 3.**

---

## Passo 4 — conferir

O `9_GRAVAR_TUDO.sh` já confere sozinho. Para conferir à mão a qualquer
momento:

```sh
sudo ./ferramenta/smtlink_dump_linux_x86_64 init read_flash 0 2M leitura/GN438_depois.bin

python3 - <<'EOF'
a = open('imagens/GN438_original.bin','rb').read()
b = open('leitura/GN438_depois.bin','rb').read()
dif = [i for i in range(0x1A3038) if a[i] != b[i]]
print("bytes diferentes de fabrica em 0x000000..0x1A3038:", len(dif))
print("primeiro em 0x%06X" % dif[0] if dif else "IDENTICO ao de fabrica.")
EOF
```

**O que fica de fora da comparação, de propósito:**

```
0x1A3038 .. 0x1FC000   área livre — pode ter rotinas do OpenPod, inertes
0x1FC000 .. 0x200000   PSMP — suas configurações de usuário
```

Nenhuma das duas é tocada por este procedimento. Explicação na seção
final do `RECUPERAR.md`.

---

## Passo 5 — ligar

Desplugue e ligue normalmente. Deve abrir com o logotipo **GENAI** de
fábrica e a home em **grade 3×3**. Se abrir com a logo do OpenPod, a
gravação não pegou — **não desligue**, avise.

---

## Se algo der errado no meio

**Não desplugue e não desligue.** O modo download está na ROM de máscara:
responde mesmo com a flash destruída, e é por ele que a correção entra.
Rode `./1_LER.sh` de novo — ele não escreve nada — e mande o resultado.

| sintoma | o que fazer |
|---|---|
| `Waiting for connection` | saiu do modo download. Refaça o Passo 1 |
| `lsusb` mostra `301a:2801` | é o modo normal, não o download. Segure VOLUME ↓ **antes** do reset |
| nada no `lsusb` | refaça o Passo 1 segurando a tecla com firmeza |
| `LIBUSB_ERROR_TIMEOUT` | cabo ou porta. USB direto na placa, sem hub |
| permissão negada no USB | rode com `sudo` (os scripts já fazem), ou crie a regra udev para `301a:2800` |
| silêncio total, aparelho apagado | pode ser **bateria no fundo**, não brick — os dois sintomas são iguais. Carregador de parede por 1 h e tente de novo |

---

## O que tem nesta pasta

```
CONFERIR.sh            confere o kit                      SO LEITURA
0_COMPILAR.sh          compila a ferramenta do fonte      nao fala com o aparelho
1_LER.sh               le 2 MiB e imprime o diagnostico   SO LEITURA
9_GRAVAR_TUDO.sh       restauracao completa               ESCREVE  (pede CONFIRMO)
VOLTAR_AO_ORIGINAL.md  este roteiro
RECUPERAR.md           o roteiro de emergencia
SHA256SUMS             sha de cada arquivo
imagens/               original 2 MiB, .up de restauracao, ptable de fabrica
ferramenta/            binarios Linux x86-64 e macOS arm64, fonte, payload
```
