# Teste — gravar o OpenPod com o Flashloader da Shenju (Windows)

> **Estado: NÃO TESTADO.** O formato está conferido, a gravação não.
> Este documento é o roteiro do primeiro teste. Depois de rodar,
> substitua a seção "Resultado" pelo que aconteceu de verdade.

## O que se quer provar

Que o `Flashloader SL-DEV 6.9.5` — a ferramenta oficial do fabricante do
SoC — grava um `.up` **nosso** no GN-438.

Se provar, o OpenPod ganha um caminho de instalação para **Windows**, sem
compilar nada. Hoje o Windows não tem caminho nenhum: o cartão exige
`Atualizar por SD`, que o firmware de fábrica não tem, e o cabo exige
Linux mais a compilação do `smartlink_flash`.

---

## Já verificado, antes de encostar no aparelho

Tudo isto foi conferido em 2026-09-18 sobre o arquivo que vai ser gravado,
`release/OpenPod-Core-5.7-Public-Beta-1/OpenPod_Beta1.up`:

| o quê | resultado |
|---|---|
| magic / marca / fim de cabeçalho | `CONFIG` · `SL6801` · `55 AA` — igual ao arquivo oficial da Shenju |
| CRC-16/CCITT-FALSE do payload | gravado `0xCEDB`, calculado `0xCEDB` — **confere** |
| cobertura | `0x000000 .. 0x1A7000` (1.732.608 B) |
| PSMP (`0x1FC000`, configurações do usuário) | **fora da cobertura** — as suas configurações sobrevivem |
| os 44 setores do kit de cabo | **todos os 44 batem byte a byte** com o `.up` |
| região do bootloader (`0x0..0xD000`) | **idêntica à de fábrica** dentro do `.up` |
| diferença contra o firmware de fábrica | exatamente **44 setores**, de `0x48000` a `0x1A6000` |

Ou seja: o `.up` e o kit de cabo são o **mesmo firmware**. O que muda é só
como ele chega no aparelho.

---

## A diferença de risco, dita sem rodeio

O kit de cabo **não endereça** o bootloader. O `.up` cobre a imagem desde
`0x000000`, então o Flashloader vai apagar e reescrever também os setores
do bootloader — com **os mesmos bytes**, mas vai reescrever.

Consequência prática: se faltar energia no meio, o aparelho pode ficar sem
bootloader. Com o kit de cabo isso não acontece.

**Mas isso é recuperável.** O modo de download da ROM de máscara roda
antes de qualquer firmware e já foi confirmado no hardware com a flash
destruída (`docs/MODO_DOWNLOAD.md`). O aparelho volta.

Não é motivo para não testar. É motivo para não testar em notebook sem
bateria nem em cabo ruim.

---

## Antes de começar

- [ ] Notebook **na tomada** (ou com bateria boa). A gravação é de 1,7 MB.
- [ ] Cabo USB de **dados**, não de carga. É o erro mais comum.
- [ ] Aparelho com **carga**.
- [ ] `firmware/VENDOR/B27.zip` extraído → `SetupFlashloaderSL-DEV(6.9.5).exe`
- [ ] O arquivo `OpenPod_Beta1.up` copiado para o Windows.
- [ ] Ter à mão o `docs/MODO_DOWNLOAD.md`, caso precise recuperar.

> ⚠️ **Nunca selecione o `B27_251112.up`.** É o firmware de outro produto.
> Um usuário no Reddit brickou o dele exatamente assim. O único `.up` que
> pode ser gravado neste aparelho é um gerado do dump deste aparelho.

---

## Como remontar a pasta `windows/` do pacote

O `.exe` do Flashloader **não está no git** — são 40 MB de software
proprietário da Shenju, e o `B27.zip` de onde ele sai já estava fora
(`.gitignore`, regra `*.zip`). Para reconstruir:

```sh
R="release/OpenPod-Core-5.7-Public-Beta-1"
mkdir -p "$R/windows"
unzip -o -j firmware/VENDOR/B27.zip "SetupFlashloaderSL-DEV(6.9.5).exe" -d "$R/windows"
mv "$R/windows/SetupFlashloaderSL-DEV(6.9.5).exe" "$R/windows/FlashloaderSL-DEV-6.9.5.exe"
```

SHA-256 do `.exe`:

```text
7dbb5dcd884af4f4af22e9784f5a0873d939ccdb4c8379cee75ae744d110e168
```

> ⚠️ Extraia **só o `.exe`**. O `B27.zip` também contém o
> `B27_251112.up` — firmware de outro produto. Ele não pode acabar na
> mesma pasta onde o usuário escolhe um `.up`.

O `windows/LEIA-ME.txt`, esse sim, está no git.

---

## Procedimento

### 1. Instalar e abrir

Instale o `SetupFlashloaderSL-DEV(6.9.5).exe` e abra.

**Deixe "automatic download" DESMARCADO.** Com essa caixa marcada o
programa grava sozinho em todo dispositivo que aparecer — inclusive antes
de você conferir se selecionou o arquivo certo.

### 2. Selecionar o firmware

Botão **"Select a firmware file"** → `OpenPod_Beta1.up`.

**Confira o nome na tela antes de seguir.** Tem que dizer `OpenPod_Beta1`.

### 3. Pôr o aparelho em modo de gravação

Mesma sequência que o `install.sh` ensina:

```
1. conecte o USB no computador
2. SEGURE o botão VOLUME PARA BAIXO
3. SEM soltar, pressione RESET (o furinho lateral)
4. solte o VOLUME
```

A tela fica **apagada** — é o esperado. No Windows deve aparecer uma
**letra de unidade** nova. O manual da Shenju diz exatamente isso:
*"a disk character will appear"*.

> Se o Windows oferecer **formatar** a unidade: **NÃO**. Isso escreve na
> flash. Feche a caixa de diálogo.

### 4. Ler a flash ANTES  ← não pule

Clique com o **botão direito** no dispositivo → opção de **leitura**.
Salve como `antes.bin`.

Esse arquivo é o seu retorno. Se algo sair errado, ele é o que devolve o
aparelho ao estado de agora. Sem ele o teste vira aposta.

Se a leitura **não funcionar**, pare e me diga — dá para tirar o backup
pelo Linux com o `smtlink_dump` antes de tentar de novo.

### 5. Gravar

Botão direito no dispositivo → **burn**.

**Não desconecte nada.** Deve levar alguns minutos.

### 6. Ler a flash DEPOIS

Mesma leitura do passo 4, salve como `depois.bin`.

### 7. Conferir

Traga `antes.bin` e `depois.bin` de volta para o Mac e rode:

```sh
python3 tools/confere_flashloader.py --antes antes.bin --depois depois.bin
```

Ele diz se o aparelho ficou exatamente igual ao `.up`, quais setores
mudaram e se a PSMP foi preservada.

### 8. Ligar

Desconecte, aperte RESET e deixe ligar.

Confira em **Configurar → Informações**: tem que dizer `OpenPod Beta 1`.

---

## O que anotar

Para o resultado valer alguma coisa, registre:

1. O Flashloader **reconheceu** o aparelho? Apareceu letra de unidade?
2. A **leitura** funcionou? Quantos bytes saíram?
3. A gravação terminou **sem erro**? Quanto tempo levou?
4. O `confere_flashloader.py` passou?
5. O aparelho **ligou**? A tela de Informações diz `OpenPod Beta 1`?
6. As configurações que você tinha (volume, EQ, idioma) **sobreviveram**?

O item 6 é o que prova na prática que a PSMP ficou de fora.

---

## Se der errado

**Não desligue o aparelho.** Anote a mensagem exata.

O aparelho não ligar **não** é o fim: o modo de download da ROM de máscara
roda antes de tudo e já foi confirmado com a flash destruída. Sequência em
`docs/MODO_DOWNLOAD.md`. Com o `antes.bin` em mãos, o caminho de volta é
gravar ele de novo.

---

## Resultado

> A preencher depois do teste. Enquanto esta seção disser isto, o
> caminho do Flashloader **não entra em nenhum pacote público**.

- data:
- funcionou:
- observações:
