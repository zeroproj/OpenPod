# RECUPERAR o GN-438 — procedimento de emergência

> Esta pasta é **autossuficiente**: tem a ferramenta, o firmware de
> fábrica, o pacote de restauração e este roteiro. Copie a pasta inteira
> para onde precisar. Não depende do resto do projeto.
>
> **Antes de qualquer coisa:** `sh CONFERIR.sh` — só leitura, confere que
> os arquivos do kit estão íntegros.

---

## Quando usar

O aparelho não liga, não mostra imagem, trava no logo, ou ficou sem
resposta depois de uma gravação.

**Não entre em pânico e não grave nada ainda.** O passo 2 (leitura) não
escreve absolutamente nada e sempre vale a pena fazer primeiro.

---

## Passo 0 — pôr o aparelho em modo download

```
USB conectado no computador  →  segure VOLUME ↓  →  aperte RESET
```

Este modo vive na **ROM de máscara do SoC**. Ele roda antes de qualquer
coisa que a gente tenha gravado, então funciona **mesmo com o firmware
destruído**. Foi assim que o primeiro aparelho do projeto voltou.

No Mac pode aparecer *"O disco inserido não é legível"* — clique em
**Ignorar**.

---

## Passo 1 — confirmar que está no modo certo

**macOS**

```
ioreg -p IOUSB -w0 -l | grep -E '"(idVendor|idProduct)"'
```

Tem de aparecer `12314` e `10240` (que são `0x301a` e `0x2800`).

**Linux**

```
lsusb | grep 301a
```

Tem de aparecer `301a:2800`.

> `2800` é o modo download. `2801` é o aparelho funcionando normalmente —
> se aparecer `2801`, ele não entrou no modo; repita o Passo 0.

---

## Passo 2 — LER a flash antes de escrever  (não grava nada)

Este passo é obrigatório. Ele dá duas coisas: a prova de que a
comunicação funciona, e uma cópia do estado quebrado, que é a única
chance de descobrir **o que** deu errado.

**macOS**

```
sudo ./ferramenta/smtlink_dump_macos_arm64 init flash_id read_flash 0 2M ./leitura_antes.bin
```

**Linux**

```
sudo ./ferramenta/smtlink_dump_linux_x86_64 init flash_id read_flash 0 2M ./leitura_antes.bin
```

Esperado: `flash_id: 0x14851485`, e 1 a 2 minutos de leitura.

> **Pare aqui e guarde `leitura_antes.bin`.** Se houver alguém
> acompanhando o caso, é este arquivo que responde a pergunta "o que
> aconteceu?". Depois da regravação ele não existe mais.

---

## Passo 3 — GRAVAR

> ⚠️ **NUNCA passe o `.up` para o `write_flash`.** Versões antigas deste
> roteiro traziam a linha
> `write_flash 0 0 0x1A3038 ... restaura_original.up`, e ela está
> **ERRADA**. O `.up` tem 0x100 bytes de cabeçalho `CONFIG`; o
> `write_flash` grava **a partir do byte 0 do arquivo**, então esse
> cabeçalho cairia em cima do `HLKJ` do bootloader e tudo ficaria 256
> bytes adiantado. Seria um brick novo, pior que o original.
>
> Verificado no código-fonte (`ferramenta/smtlink_dump.c`): a função
> `write_flash` calcula o tamanho com o 2º argumento mas indexa o arquivo
> com `mem[i + j]` — o deslocamento **nunca** chega ao ponteiro de dados.
>
> **O `.up` serve para o outro caminho**, o do cartão SD, em que é o
> próprio bootloader que lê e interpreta o cabeçalho.

**A regra:** o arquivo passado ao `write_flash` tem de conter, **já no
byte 0**, exatamente o que vai para o endereço de destino. E o 2º
argumento é sempre `0`.

### 3a — o caminho preferido: só o que está diferente

Mande a `leitura_antes.bin` do Passo 2 para quem estiver acompanhando o
caso. Comparando com `imagens/GN438_original.bin`, sai um kit com **um
arquivo por setor divergente**, na ordem certa — tabela de partições por
último, e releitura conferida depois de cada escrita.

É o caminho que de fato recuperou o aparelho em 13/09: naquele caso um
único setor precisou voltar.

```
sudo ./ferramenta/smtlink_dump_macos_arm64 init write_flash 0xD000 0 0x1000 ptable_D000_original.bin
```

(esse é o exemplo real; o setor e o arquivo dependem do que a leitura
mostrar)

### 3b — o caminho completo, quando não dá para analisar

Grava tudo de fábrica, do endereço 0 até o fim da TONE, **direto da
imagem de 2 MiB** — onde o byte 0 do arquivo já é o byte 0 da flash,
que é o que torna a linha correta:

```
sudo ./ferramenta/smtlink_dump_macos_arm64 init write_flash 0 0 0x1A3038 ./imagens/GN438_original.bin
```

Isto **reescreve também o bootloader**. É aceitável porque o modo
download vive na ROM de máscara, no silício — ele continua respondendo
mesmo que essa escrita falhe no meio. Mas é mais escrita do que o
necessário: prefira o 3a sempre que der.

## Passo 4 — conferir e ligar

```
sudo ./ferramenta/smtlink_dump_macos_arm64 init read_flash 0 2M ./leitura_depois.bin
```

Confira que o trecho gravado bate com o de fábrica:

```
python3 - <<'EOF'
a=open('imagens/GN438_original.bin','rb').read()[:0x1A3038]
b=open('leitura_depois.bin','rb').read()[:0x1A3038]
print("IGUAL" if a==b else "DIVERGE — NAO desligue, peca ajuda")
EOF
```

Depois desplugue e ligue normalmente.

---

## O que o restaura_original.up cobre — e o que ele não cobre

```
0x000000 .. 0x1A3038   bootloader + tabela + FIRM + TONE   <- RESTAURADO
0x1A3038 .. 0x1FC000   area livre                          <- NAO tocado
0x1FC000 .. 0x200000   PSMP (suas configuracoes)           <- NAO tocado
```

Verificado byte a byte: o payload é **idêntico** ao
`GN438_original.bin` no intervalo que ele cobre.

**Sobre a área livre.** Se o aparelho tinha OpenPod, as rotinas do
projeto continuam gravadas ali depois da restauração. Isso é **decisão
declarada**, não esquecimento:

- a FIRM restaurada é a de fábrica, e ela não tem nenhum gancho para
  essas rotinas — nada as chama. **Classe: PROVÁVEL** (o firmware de
  fábrica sempre rodou com essa área apagada, então não depende do
  conteúdo dela);
- apagá-las exigiria um pacote maior que qualquer um já testado neste
  aparelho. **Esta pasta não carrega artefato não testado** — é
  exatamente a pasta em que isso não pode acontecer;
- se um dia for preciso mesmo zerar a área livre, é trabalho para
  `tools/`, com teste próprio, e não pelo caminho de emergência.

O resultado prático: o aparelho volta a ser um GN-438 de fábrica, com
alguns bytes inertes numa região que o firmware de fábrica nunca lê.

---

## Se algo der errado

| sintoma | o que fazer |
|---|---|
| `Waiting for connection` | o aparelho saiu do modo download. Refaça o Passo 0 |
| nada aparece no `ioreg` / `lsusb` | refaça o Passo 0 segurando a tecla com firmeza **antes** de apertar o reset |
| `sudo` não aceita a senha | tem de ser num terminal de verdade (Terminal.app), não dentro de outra ferramenta |
| silêncio total no USB, aparelho apagado | pode ser **bateria no fundo**, não brick. Carregador de parede por 1 h, depois tente de novo. Os dois sintomas são indistinguíveis |
| leitura falha com `LIBUSB_ERROR_TIMEOUT` | cabo ou porta. USB direto na máquina, sem hub; teste o cabo em outro aparelho (há cabos que só carregam) |

---

## Se a ferramenta não rodar na sua máquina

Os dois binários aqui são **macOS arm64** e **Linux x86-64**. O
código-fonte está em `ferramenta/` — `smtlink_dump.c` mais o `payload/`.
Para recompilar:

```
cd ferramenta && make
```

Depende de `libusb`. Origem: projeto `smartlink_flash` (upstream).

---

## Conteúdo desta pasta

```
CONFERIR.sh                      confere o kit (SO LEITURA)
SHA256SUMS                       sha de cada arquivo
RECUPERAR.md                     este roteiro
imagens/
  GN438_original.bin             firmware de fabrica, 2 MiB
                                 sha b7cd5eb952be5328cbaa926099cf8d88
                                     168633c1fab6d0f31f3a283c9e24b36f
  restaura_original.up           pacote de restauracao (CONFIG/SL6801)
  ptable_D000_original.bin       tabela de particoes de fabrica, 4 KiB
ferramenta/
  smtlink_dump_macos_arm64       binario macOS
  smtlink_dump_linux_x86_64      binario Linux
  smtlink_dump.c, Makefile, payload/   fonte, para recompilar
```
