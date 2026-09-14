# RECOVERY OFICIAL do GN-438

> **Validado em hardware em 2026-09-14**, num GN-438 que rodava a
> OpenPod 3.0. Resultado: 37 setores regravados, área livre zerada,
> releitura idêntica à de fábrica, PSMP intocada.
>
> Se o aparelho **não liga e não enumera**, o roteiro é o outro:
> **`RECUPERAR.md`**. Ele assume que nada pode ser analisado antes.

---

## Os dois alvos

| situação | comando |
|---|---|
| o aparelho deu defeito e você quer **o OpenPod de volta**, funcionando | `sudo sh RECOVERY.sh --alvo core` |
| o OpenPod é o suspeito, ou você quer o aparelho **como saiu de fábrica** | `sudo sh RECOVERY.sh` |
| não sabe | **fábrica** — é o padrão |

**Por que fábrica é o padrão.** É o único artefato deste projeto cuja
correção **não depende de trabalho nosso**. Se um dia a baseline do Core
estiver errada de um jeito que ainda não percebemos, um recovery que só
restaura o Core não salva — ele reinstala o problema.

O recovery para o Core é **conveniência**. O recovery para a fábrica é
**garantia**. Os dois moram no mesmo kit; detalhe em `imagens/ALVOS.md`.

---

## Em um comando

```sh
cd recovery
sh CONFERIR.sh                 # confere o kit — só leitura
# USB conectado → segure VOLUME ↓ → aperte RESET
sudo sh RECOVERY.sh            # ou: sudo sh RECOVERY.sh --alvo core
```

E só. O script faz tudo em sequência, pedindo confirmação uma vez:

```
1. confere a imagem de fábrica pelo sha256
2. confere que o aparelho está em 301a:2800 (e recusa se estiver em 2801)
3. LÊ os 2 MiB e guarda a fotografia do estado anterior
4. compara e mostra o que vai mudar, setor a setor
5. pede que você digite GRAVAR
6. grava  0x000000..<até onde a imagem do alvo tem conteúdo>
7. apaga  dali até 0x1FC000 — o que sobrou da versão anterior
8. relê os 2 MiB e confere as três regiões
9. diz o que o aparelho tinha antes e o que tem agora
```

**A PSMP (`0x1FC000..0x200000`), que guarda suas configurações, nunca é
tocada.**

### Variações

```sh
sudo sh RECOVERY.sh --alvo core           # volta ao OpenPod Core STABLE
sudo sh RECOVERY.sh --so-analise          # SÓ LÊ. Não escreve nada
sudo sh RECOVERY.sh --manter-area-livre   # não apaga o que sobrou
```

Os modificadores combinam: `--alvo core --so-analise` mostra o que uma
volta ao Core faria, sem escrever nada.

O `--so-analise` é a forma segura de descobrir o que está no aparelho:
ele lê, mostra a lista de setores divergentes e para antes de escrever.

---

## Antes de rodar

**Condições físicas** (regra R6, comprada com um aparelho): bateria
cheia, USB **direto na placa-mãe, sem hub**, cabo que você sabe que
transmite dados — há cabos que só carregam —, e a máquina sem suspender
no meio.

**A ferramenta roda nesta máquina?**

```sh
./ferramenta/smtlink_dump_linux_x86_64 2>&1 | head -3
```

Se reclamar de arquitetura ou de biblioteca faltando:

```sh
sh 0_COMPILAR.sh
```

Compila a partir do fonte que está aqui. Precisa de `build-essential` e
`libusb-1.0-0-dev`; o script mostra a linha certa para Debian/Ubuntu,
Fedora e Arch. O `RECOVERY.sh` passa a usar o binário compilado sozinho.

---

## As duas coisas que parecem perigosas e não são

### Gravar o sistema inteiro endereça `0x00D000`

A tabela de partições é o setor que brickou o primeiro aparelho do
projeto, e a regra R1 manda nunca escrevê-lo. Mas o `write_flash` compara
cada bloco de 4 KiB **antes** de apagar:

```c
if (!m2) continue;   // same data
```

Bloco que já está correto não é apagado nem regravado. Na validação de
14/09, dos 420 setores do sistema, **383 foram pulados** e a tabela ficou
intocada. Ainda assim o script confere e avisa em bloco separado se ela
divergir — a garantia só vale enquanto a premissa valer.

### Apagar o que sobra da área livre

Parece destrutivo e é o contrário: essa região é **`0xFF` no firmware de
fábrica**. Voltar para `0xFF` é restaurar.

**O limite não é constante** — depende do alvo. O `fabrica` termina na
TONE; o `core` **usa** a área livre, porque é lá que moram as rotinas e
os textos do OpenPod. O script calcula: último byte que não é `0xFF`,
nunca antes do fim da TONE, arredondado para cima:

```
fabrica      0x1A3038  ->  grava ate 0x1A4000, apaga 352 KiB
core 1.0.1   0x1A493B  ->  grava ate 0x1A5000, apaga 348 KiB
```

Assim o alvo fica exato: nem sobra byte de uma versão anterior, nem se
apaga o que a versão nova precisa.

O cuidado está no **setor de fronteira**, aquele em que o conteúdo da
imagem acaba no meio. Apagá-lo levaria junto o que vem antes. Por isso a
gravação vai até o limite **alinhado para cima**: esse setor recebe o
conteúdo da imagem inteiro, `0xFF` do rabo incluso, e o apagamento começa
no setor seguinte.

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

## Depois

Desplugue e ligue.

| alvo | deve abrir com |
|---|---|
| fabrica | logotipo **GENAI** e home em **grade 3×3** |
| core | logo do **OpenPod sobre preto** |

Se abrir com a outra coisa, a gravação não pegou — **não desligue**,
avise.

A fotografia do estado anterior fica em `leitura/antes_AAAAMMDD_HHMMSS.bin`.
É a única cópia do que havia no aparelho — guarde antes de rodar o
recovery de novo, porque cada execução gera a sua.

---

## Se algo der errado no meio

**Não desplugue e não desligue.** O modo download está na ROM de máscara,
no silício: ele responde mesmo com a flash destruída, e é por ele que a
correção entra. Rode `sh 1_LER.sh` — que não escreve nada — e mande o
resultado.

| sintoma | o que fazer |
|---|---|
| `Waiting for connection` | saiu do modo download. Refaça: VOLUME ↓ e RESET |
| `lsusb` mostra `301a:2801` | é o modo normal. Segure VOLUME ↓ **antes** do reset |
| nada no `lsusb` | refaça segurando a tecla com firmeza |
| `LIBUSB_ERROR_TIMEOUT` | cabo ou porta. USB direto na placa, sem hub |
| permissão negada no USB | rode com `sudo`, ou crie a regra udev para `301a:2800` |
| silêncio total, aparelho apagado | pode ser **bateria no fundo**, não brick — os sintomas são iguais. Carregador de parede por 1 h e tente de novo |

---

## O que tem nesta pasta

```
RECOVERY.sh            O RECOVERY OFICIAL                ESCREVE (pede GRAVAR)
  recovery.py          o miolo dele
CONFERIR.sh            confere o kit                     SÓ LEITURA
0_COMPILAR.sh          compila a ferramenta do fonte     não fala com o aparelho
1_LER.sh               lê 2 MiB e imprime diagnóstico    SÓ LEITURA
VOLTAR_AO_ORIGINAL.md  este roteiro
RECUPERAR.md           emergência: aparelho sem responder
SHA256SUMS             sha de cada arquivo
imagens/               os dois alvos + ALVOS.md, .up de restauração, ptable
ferramenta/            binários Linux x86-64 e macOS arm64, fonte, payload
leitura/               criada no uso: fotografias do aparelho
```
