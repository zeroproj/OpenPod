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

## Passo 3 — reinstalar o sistema

```sh
sudo ./2_RESTAURAR.sh
```

Ele grava **a imagem inteira de fábrica**, `0x000000..0x1A3038` —
bootloader, tabela de partições, FIRM e TONE. É um reinstalar, não um
remendo do que mudou.

Antes de escrever, o script:

1. lê os 2 MiB e compara com o de fábrica;
2. mostra **quantos dos 420 setores serão de fato regravados** e quantos
   serão pulados;
3. avisa, em bloco separado, se a **tabela de partições** estiver
   diferente — é o setor que brickou o primeiro aparelho do projeto;
4. só então pede que você digite `GRAVAR`.

Depois de gravar, relê os 2 MiB e compara byte a byte.

### Gravar tudo não é apagar tudo

O `write_flash` compara cada bloco de 4 KiB **antes** de apagar:

```c
if (!m2) continue;   // same data
```

Bloco que já está correto não é apagado nem regravado. Então mandar a
imagem inteira toca fisicamente só o que difere — inclusive deixando a
tabela de partições intacta quando ela já é a de fábrica, que é o caso
deste aparelho.

### O que não é tocado

```
0x1A3038 .. 0x1FC000   área livre — pode ter rotinas do OpenPod, inertes
0x1FC000 .. 0x200000   PSMP — suas configurações de usuário
```

Inertes porque a FIRM de fábrica não tem nenhum gancho para elas: aquela
área sempre foi `0xFF` de fábrica, então o firmware não depende do que
está lá.

---

## Passo 3b — zerar também a área livre  (OPCIONAL)

```sh
sudo ./9b_APAGAR_AREA_LIVRE.sh CONFIRMO
```

Só se você quiser a flash **literalmente** igual à de fábrica. Não é
necessário: depois do Passo 3 o aparelho já é um GN-438 de fábrica.

Ele reescreve o setor misto `0x1A3000` — que tem a cauda da TONE mais o
começo da área livre, e por isso não pode ser simplesmente apagado — e
depois apaga `0x1A4000..0x1FC000`.

> ⚠️ É o único passo de todo o kit que usa um comando **nunca exercitado
> neste projeto** (`erase_flash`). Rode depois de o Passo 3 ter
> conferido, e só se quiser mesmo.

---

## Passo 4 — conferir

O `2_RESTAURAR.sh` já confere sozinho. Para conferir à mão a qualquer
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
CONFERIR.sh              confere o kit                     SO LEITURA
0_COMPILAR.sh            compila a ferramenta do fonte     nao fala com o aparelho
1_LER.sh                 le 2 MiB e imprime o diagnostico  SO LEITURA
2_RESTAURAR.sh           reinstala o sistema de fabrica    ESCREVE (pede GRAVAR)
  restaurar.py           o miolo do 2_RESTAURAR.sh
9b_APAGAR_AREA_LIVRE.sh  zera a area livre — OPCIONAL      ESCREVE (pede CONFIRMO)
VOLTAR_AO_ORIGINAL.md    este roteiro
RECUPERAR.md           o roteiro de emergencia
SHA256SUMS             sha de cada arquivo
imagens/               original 2 MiB, .up de restauracao, ptable de fabrica
ferramenta/            binarios Linux x86-64 e macOS arm64, fonte, payload
```
