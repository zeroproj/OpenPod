# OpenPod — Semântica real do `write_flash`

> **Comprovado em hardware em 2026-09-12**, ao custo de uma tabela de
> partições corrompida e restaurada. Este documento existe para que
> ninguém repita o erro.

---

## 1. A conclusão, primeiro

```text
write_flash <endereço_na_flash> <ignorado> <tamanho> <arquivo>
                                 ▲
                                 └── NÃO é o offset dentro do arquivo
```

**O `write_flash` grava a partir do offset 0 do arquivo.** O segundo
argumento não é honrado como posição no arquivo.

**Consequência prática:** o arquivo passado precisa conter, **já no
offset 0**, exatamente os bytes que devem ir para o endereço de destino.
Não se pode apontar para dentro de uma imagem de 2 MiB.

| Uso | Resultado |
|---|---|
| ❌ `write_flash 0xD000 0xD000 0x1000 imagem_2MiB.bin` | grava `imagem[0x0:0x1000]` — **o cabeçalho HLKJ** |
| ✅ `write_flash 0xD000 0 0x1000 setor_D000.bin` | grava o conteúdo correto |

Passar **`0`** no segundo argumento é a forma robusta: é correto tanto se
o argumento for ignorado (comportamento observado) quanto se for honrado
por alguma variante da ferramenta.

---

## 2. Como foi descoberto

O `flash_v001.sh` v1 chamou:

```sh
write_flash 0xD000 0xD000 0x1000 GN438_openpod_v001.bin
```

A releitura do setor devolveu `5c64eaee…98d61`, que **não** correspondia
a nenhuma hipótese razoável:

| Hipótese | SHA-256 | Bate? |
|---|---|---|
| V001 no setor (esperado) | `c2124ab4…9215c`… | não |
| ORIGINAL (escrita não pegou) | `c3d16a15…507091` | não |
| `orig AND v001` (sem erase) | `794cce19…73ed03` | não |
| tudo `0xFF` (só apagou) | `f47a8ec3…1300c6` | não |
| tudo `0x00` | `ad7facb2…892ca7` | não |

A varredura dos dois arquivos em busca de um bloco de 4096 bytes com
esse hash achou **offset `0x000000` em ambos** — os arquivos são
idênticos nessa faixa.

**Confirmação independente:** os bytes lidos em `0xD01C–0xD01D` eram
`0004`, que são exatamente os bytes `0x1C–0x1D` do **início** do
arquivo (`484c4b4a c0fb8100 01008200 60000000 ecc80000 9d750000
09000000 **0004**0000`).

Duas evidências convergentes, uma delas um SHA-256 exato. **CONFIRMADO.**

---

## 3. Por que o teste da Sessão 20 não pegou isso

O teste de escrita em área livre (`0x1D0000`) usou um arquivo pequeno
criado para o teste, em que o conteúdo desejado **já estava no offset
0**. O comportamento errado era indistinguível do correto naquele caso.

> **Lição de método:** um teste que passa por acidente é pior que um
> teste que falha. O teste da Sessão 20 provou que `write_flash` escreve
> e que a releitura confere — mas **não** provou a semântica dos
> argumentos, e eu tratei como se tivesse provado.

---

## 4. O que salvou o aparelho

| Proteção | O que fez |
|---|---|
| Gravar só a partir de `0x00D000` | o bootloader nunca foi endereçado — o modo card reader continuou vivo, e foi por ele que a correção entrou |
| Conferir cada setor **logo após** gravar | detectou o erro no 1º setor |
| Abortar na primeira divergência | o 2º setor (`0x0CE000`) **nunca foi gravado** |
| `WROTE` incrementado **antes** da escrita | o `die()` avisou corretamente que já havia escrita e mandou não desligar |
| Diagnosticar **lendo**, nunca escrevendo | o estado real foi determinado sem risco adicional |

**A restauração impressa pelo próprio script estava errada** — repetia a
mesma assinatura e teria gravado o cabeçalho outra vez. Foi interceptada
antes de ser executada. Hoje o script imprime a forma correta.

---

## 5. Regra derivada

> **Toda gravação usa um arquivo por setor**, cujo tamanho é exatamente o
> tamanho da região e cujo offset 0 é o conteúdo de destino. O segundo
> argumento do `write_flash` é sempre `0`.

Artefatos gerados a partir das imagens validadas:

| Arquivo | Bytes | SHA-256 |
|---|---|---|
| `v001_D000.bin` | 4096 | `c2124ab4b1c6eebd4b13a3156e9b1482f79385aa855276929ff2ef79dd6a9686` |
| `v001_CE000.bin` | 8192 | `a30962bce6b71e4ad5dc5922ee8e121d58dd8e5db13925318725f3f663d45597` |
| `orig_D000.bin` | 4096 | `c3d16a15b7df6a8feac96169d93da82a5562ae3d17a94bf8906c2d24fc507091` |
| `orig_CE000.bin` | 8192 | `10739e6db5bc6f7647823b187ea6c1f6ad1a1d2b3698b4dac00d22dc2b81780c` |

---

## 6. Nota sobre o `coreutils` em Rust

Na distro usada (Ubuntu recente, `uutils`), o pipeline

```sh
tail -c +N arquivo | head -c M | sha256sum
```

faz o `tail` abortar com `panicked at … BrokenPipe` e `core dumped`.

**O hash produzido ainda é correto** — o `head` recebe seus M bytes antes
do `tail` morrer, e as 4 regiões conferidas assim bateram com os valores
esperados. Mas o ruído no terminal é alarmante e mascara erros reais.

**Todos os scripts do projeto passaram a usar `python3`** para fatiar e
somar, sem `tail`/`head`.

---

## 7. Classificação

| Afirmação | Classe |
|---|---|
| `write_flash` grava a partir do offset 0 do arquivo | **CONFIRMADO** (SHA-256 exato + bytes `0x1C–0x1D`) |
| O 2º argumento é ignorado como posição no arquivo | **CONFIRMADO no código-fonte em 2026-09-14** — ver §8 |
| Passar `0` é seguro nas duas interpretações | **CONFIRMADO** por construção |
| `write_flash` apaga o setor antes de gravar | **PROVÁVEL** — a gravação substituiu o conteúdo, não fez AND |
| Granularidade de erase | **NÃO DETERMINADO** — o bootloader ficou intacto ao gravar em `0xD000`, o que descarta erase de 64 KiB alinhado em `0x0` |


---

## 8. Confirmação no código-fonte (2026-09-14)

Até aqui a semântica era **CONFIRMADA por hardware** e o papel do 2º
argumento ficava **PROVÁVEL**. Lendo `smtlink_dump.c`, função
`write_flash`, o mecanismo aparece inteiro:

```c
size -= src_offs;                  // o offset entra AQUI...
if (src_size) { ... size = src_size; }

for (i = 0; i < size; ) {
    ...
    int old = buf[n2 + j], new = mem[i + j];   // ...mas nunca AQUI
```

`src_offs` participa só do cálculo do tamanho. O ponteiro de dados é
`mem[i + j]`, com `i` começando em zero — **o arquivo é sempre lido do
byte 0**. Não é "ignorado" no sentido de inerte: ele *encurta* a
gravação, o que torna o erro ainda mais traiçoeiro, porque o tamanho
bate e o conteúdo não.

### O que isso pegou

Uma linha que estava no roteiro de recuperação do Mac desde 13/09:

```
write_flash 0 0 0x1A3038  update_restore_original.up      <- ERRADA
```

O `.up` tem 0x100 bytes de cabeçalho. Essa linha gravaria `CONFIG…` em
cima do `HLKJ` do bootloader, com tudo 256 bytes adiantado.

```
no arquivo .up, byte 0:   43 4F 4E 46 49 47   "CONFIG"
o que deve ir ao end. 0:  48 4C 4B 4A         "HLKJ"
```

**Nunca foi executada** — o roteiro dizia "não rode por conta própria", e
a recuperação real de 13/09 usou o caminho certo, um arquivo por setor
(`ptable_D000_original.bin`). Corrigido em `recovery/RECUPERAR.md`; o
roteiro antigo ficou marcado como obsoleto.

> **A regra que isso reforça:** `.up` é para o bootloader ler do cartão,
> onde o cabeçalho é interpretado. Para `write_flash`, só arquivo cujo
> byte 0 já é o conteúdo do endereço de destino — setor avulso, ou a
> imagem de 2 MiB gravada a partir do endereço 0.
