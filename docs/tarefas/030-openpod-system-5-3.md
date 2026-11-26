# Ficha 030 — o OpenPod System passa de "Reload 3.5" para 5.3 (só a renumeração)

Decisão do decisor (D51, 26/11/2026): *"o Reload 3.5 deveria ser 5.3"*, para **nivelar com o OpenPod RockBox 5.x**.
As funções são **as mesmas** da 3.5. **Não é uma versão nova**: é a mesma imagem, com outro carimbo.

## O que já está provado (CONFIRMADO, pela coordenação, em 26/11/2026)

- A receita **`reload_3.5b`** reproduz a imagem publicada da 3.5 **byte a byte**: sha `ba56813d9c15d53f27dc684b21b4e1a92b094f0fd9f0db2bb4e7e122289d40f`.
  Duas compilações seguidas deram o **mesmo sha** (o build é determinístico).
- `firmware/WORKING/reload_3.5.bin` é essa imagem **sem** carimbo; `firmware/WORKING/reload_3.5_carimbado.bin` é a mesma **com** o carimbo.
- A diferença entre as duas é de **14 bytes**, em **2 setores**:

  | Endereço | O que é | Na 3.5 carimbada |
  |---|---|---|
  | `0x1A4F00..0x1A4F0A` | o **texto** do carimbo, em ASCII | `"Reload 3.5\0"` (11 bytes) |
  | `0x10A59C..0x10A59E` | o **ponteiro** que o aparelho usa para achar esse texto | `0x00C4EA8B` → `0x00DA4F00` |

  O endereço virtual do texto é `0xC00000 + 0x1A4F00 = 0x00DA4F00`. A string de fábrica `yp3_2.0.43`
  (em `0x04EA8B`) **fica intacta** — é a regra do `patch_versao.py`.
- O `patch_versao.py` já faz isso: com `--em 0x1A4F00` e `--texto "5.3"`, ele escreve o texto novo,
  reponta o literal e **relê pelo ponteiro** para conferir. O ponteiro fica **igual** se o endereço não muda.

**Consequência importante:** o novo texto (`OpenPod 5.3`, 11 caracteres) cabe no mesmo endereço
`0x1A4F00`, então **o ponteiro não muda** e **só os bytes do texto mudam** — a imagem nova difere da
3.5 carimbada em **12 bytes** (`0x1A4F00..0x1A4F0B`), todos dentro do carimbo. Se o texto fosse maior
e não coubesse, o endereço mudaria e os 3 bytes do ponteiro mudariam junto.

## O que fazer

1. **O nome na tela é escolhido pelo decisor** (a coordenação já perguntou). O texto exato vem na seção
   "Texto do carimbo" desta ficha. **Não invente um nome.**
2. **Compile a imagem sem carimbo** com a mesma receita:
   ```
   python3 tools/build.py --receita reload_3.5b --saida firmware/WORKING/openpod_5_3.bin
   ```
   Confirme que o sha é `ba56813d9c15d53f27dc684b21b4e1a92b094f0fd9f0db2bb4e7e122289d40f`.
   Se **não** for, **PARE** e escale: a receita mudou.
3. **Carimbe** com o `patch_versao.py` (é ele que carimba; o `gera_versao.py` **não**):
   ```
   python3 tools/patch_versao.py --in firmware/WORKING/openpod_5_3.bin \
     --out firmware/WORKING/openpod_5_3_carimbado.bin --texto "<TEXTO>" --em 0x1A4F00
   ```
   O `--em` é **obrigatório**: sem ele a ferramenta aloca sozinha e o endereço passa a depender da ordem.
4. **Gere o kit** com o `gera_versao.py`:
   ```
   python3 tools/gera_versao.py --imagem firmware/WORKING/openpod_5_3_carimbado.bin \
     --versao OpenPod-5.3 --nome-tela "<TEXTO>"
   ```
   Isso cria `firmware/RELEASE/OpenPod 5.3/` (interno) e **`release/OpenPod-5.3/`** (público).
   Escreva à mão o "New in 5.3" no `README.md` do kit (o modelo tem `{TELA}`/`{CURTO}`/`{BETA}`;
   confira que nenhum marcador sobrou).
5. **O pacote do Tune** (é o repositório do OpenPod-instalador, não este):
   ```
   cd OpenPod-instalador && python3 pacotes/gera_pacotes.py --system "<o .up do release/OpenPod-5.3/>" \
     --versao 5.3 --saida "<OpenPod>/_local/publicar/pacotes" --indice <indice-temporario.json>
   ```
   Isso gera **`openpod-system-5.3.tar.gz`**, assinado. Depois **funda** o trecho do índice no
   `OpenPod/_local/publicar/pacotes/index.json`, com `system` = `5.3`, conferindo o sha256 à mão.
   **O pacote da 3.5 sai de circulation** (o `index.json` aponta para o novo; o antigo pode ficar na pasta,
   mas o índice é a fonte).
6. **O site** (`docs/index.html`), **PT e EN**:
   - o **card** do OpenPod System passa a **5.3** (é a linha do `<figcaption>` do System, e o
     `<span class="ver">` do cabeçalho de cada idioma);
   - no **histórico**, entra uma linha nova **acima** da da 3.5:
     `5.3 · 26/11/2026` → *"Renumeração da 3.5, mesmas funções; atualize pelo cartão (.up) ou Recovery"*
     (e a equivalente em inglês);
   - as **próximas versões** do System passam a **5.x**: a antiga **"3.6 · 10/01/2027"** (jogos novos + bichinho
     virtual) vira **"5.4 · 10/01/2027"**;
   - o texto que diz *"a versão do OpenPod (começa com `Reload`)"* (o passo a passo de instalação,
     PT e EN) **precisa mudar**: o carimbo novo **não** começa com "Reload", e sim com **"OpenPod 5.3"**.
     Ajuste para o que faz sentido na frase (por exemplo, *"começa com `OpenPod`"*);
   - **não** mexa no card do RockBox (já está em 5.3) nem no histórico do RockBox.
7. **Registre** em `docs/tarefas/030-analise.md` o que foi conferido, com CONFIRMADO / PROVÁVEL / HIPÓTESE.

## O que provar (é a conferência da coordenação, mas o desenvolvedor tem que deixar isso pronto)

1. **A imagem nova só difere da 3.5 nos bytes do carimbo.** Compare `openpod_5_3_carimbado.bin` com
   `reload_3.5_carimbado.bin` **byte a byte**, e diga:
   - quantos bytes mudaram e **em quais endereços** — tem de ser **12 bytes, em `0x1A4F00..0x1A4F0B`**;
   - que **o ponteiro em `0x10A59C` NÃO mudou** (tem de continuar `0x00DA4F00`);
   - que **nenhum outro byte** da imagem mudou.
2. **A string lida pelo aparelho é a nova.** Releia o texto pelo ponteiro (o `patch_versao.py` já imprime
   isso, mas confirme) e diga o que o aparelho mostra em Config → Informações: tem de ser
   **`OpenPod 5.3`**, e o `patch_versao.py` tem de dizer **72 px** (a tela aceita 113 px).
3. **O ORIGINAL intacto:** `shasum -a 256 firmware/ORIGINAL/GN438_original.bin` =
   `b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f`.
4. **As regras de byte:** nada abaixo de `0xE000`; o setor `0xD000` e a PSMP (`0x1FC000+`) intocados.
   (O `build.py` já confere; anote o resultado.)
5. **O kit:** o `.up` é igual à imagem pedida, com o CRC16 certo, e a PSMP fora.
6. **O pacote:** a assinatura Ed25519 confere, o SHA256SUMS bate, e o `expect` do MANIFEST
   (bootloader e tabela) é o de sempre.

## O que NÃO fazer

- **Não mexa no código do firmware.** A renumeração é só o carimbo. Nenhuma função, nenhum gancho, nenhuma
  receita nova. Se parecer que precisa de mais, **escale**.
- **Não crie uma receita nova** (`reload_5_3`): a 3.5b já serve e é a que reproduz a imagem publicada.
- **Não grave no aparelho** e **não publique** (o `publica_release.py` só roda com o "pode" do decisor,
  e a coordenação é quem publica).
- **Não altere `firmware/ORIGINAL`.**
- **Não use** as linhas antigas (Core, Alphas, Betas).

## Regras de sempre

- O diretório atual JÁ É a raiz do repositório: use caminhos relativos a partir dela. **Sem `cd` para caminho
  absoluto** (o caminho tem espaço), **sem `../`**, **sem `/tmp`** (use `.tmp/` dentro do repositório),
  **sem `git stash`**. Nada fora do repositório (não leia `~/.cargo`).
- Commits pequenos, em português.
- `sh tools/ci.sh` verde.
- Classifique o que afirmar como CONFIRMADO / PROVÁVEL / HIPÓTESE.

Sinal: `PRONTO-030` ou `ESCALADA-030` sozinho numa linha.

---

## Texto do carimbo

**DEFINIDO PELO DECISOR: `OpenPod 5.3`** (D51, 26/11/2026).

É esse texto que o aparelho mostra em **Config → Informações**. São 12 bytes (11 caracteres + o `\0`):

```
OpenPod 5.3\0
```

- O **endereço** é `0x1A4F00` (o mesmo da 3.5) → o **ponteiro em `0x10A59C` NÃO muda**, e a imagem nova
  difere da 3.5 carimbada em **exatamente 12 bytes**, todos em `0x1A4F00..0x1A4F0B`.
- Como o texto novo é **1 byte mais longo** que `"Reload 3.5"`, o `\0` final fica em `0x1A4F0B` (na 3.5
  ele estava em `0x1A4F0A`, e `0x1A4F0B` era `0xFF`). A diferença é **só o texto**; **nada mais** na imagem muda.
- A largura do texto é conferida pelo `patch_versao.py` (a tela Informacao aceita **113 px** por linha e
  **não quebra linha**). O "OpenPod 5.3" mede **72 px**: cabe com folga.

> **Valores de referência (medidos pela coordenação em 26/11/2026, com o `reload_3.5b`):**
>
> | | valor |
> |---|---|
> | sha da imagem nova carimbada | (o desenvolvedor anota; **não** é `ba56813d…`, porque o carimbo mudou) |
> | bytes diferentes da 3.5 carimbada | **12**, em `0x1A4F00..0x1A4F0B` |
> | o ponteiro `0x10A59C` | **inalterado** (`0x00DA4F00`) |
> | a string de fábrica `0x04EA8B` | **intacta** |
>
> Se a conferência der **outro** número de bytes, ou mexer no ponteiro, **PARE** e escale.

> **Se o `patch_versao.py` recusar** (texto largo demais, ou `0x1A4F00` não virgem por algum motivo),
> **PARE e escale** (`ESCALADA-030`). Não escolha outro endereço por conta própria: mudar o endereço
> mudaria o ponteiro, e a conferência da coordenação espera **só 12 bytes** de diferença.
