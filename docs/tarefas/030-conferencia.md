# Ficha 030 — conferência da coordenação (2026-11-26)

**OpenPod System: "Reload 3.5" → "OpenPod 5.3"** (D51). Só a renumeração; as funções são as mesmas da 3.5.

Desenvolvedor: `desenvolvedor` (DeepSeek grátis). Entregou com **PRONTO-030**, 3 commits
(`a39756f` kit/release, `b2c3b63` site, `13d1c01` análise). O passo do pacote do Tune (que é de outro
repositório) ficou por conta da coordenação — decisão certa do desenvolvedor, que respeitou a regra de
não sair da raiz.

Intervalo conferido: `7d0bfae..13d1c01`.

---

## Conferido e certo (CONFIRMADO, medido de novo pela coordenação)

### 1. A imagem sem carimbo é a mesma da 3.5 publicada

- `firmware/WORKING/openpod_5_3.bin` → sha `ba56813d9c15d53f27dc684b21b4e1a92b094f0fd9f0db2bb4e7e122289d40f`.
- **Duas compilações** minhas da receita `reload_3.5b` deram **o mesmo sha**, e é o mesmo sha de
  `firmware/WORKING/reload_3.5.bin`. O build é reprodutível e a receita **não** mudou.

### 2. A imagem nova difere da 3.5 **só** nos bytes do carimbo — a prova principal

Comparação byte a byte de `openpod_5_3_carimbado.bin` contra `reload_3.5_carimbado.bin`
(ambos 2 097 152 B):

- **12 bytes diferentes**, em `0x1A4F00..0x1A4F0B`:
  `0x1A4F00 52→4F`, `0x1A4F01 65→70`, `0x1A4F02 6C→65`, `0x1A4F03 6F→6E`, `0x1A4F04 61→50`,
  `0x1A4F05 64→6F`, `0x1A4F06 20→64`, `0x1A4F07 33→20`, `0x1A4F08 2E→35`, `0x1A4F09 35→2E`,
  `0x1A4F0A 00→33`, `0x1A4F0B FF→00` — ou seja, `"Reload 3.5\0"` → `"OpenPod 5.3\0"`.
- **O ponteiro em `0x10A59C` NÃO mudou**: `0x00DA4F00` nas duas imagens.
- **Nenhum outro byte** da imagem mudou.
- A string de fábrica `yp3_2.0.43` (em `0x04EA8B`) está **intacta** nas duas.
- O texto lido **pelo ponteiro** é `OpenPod 5.3`. Largura: **72 px** (a tela aceita 113 px).

> Nota: o `patch_versao.py` reporta "15 bytes alterados" porque ele compara contra a imagem **sem**
> carimbo (12 do texto + 3 do ponteiro, que ainda estava de fábrica). Contra a 3.5 **carimbada** — que
> é a comparação que a ficha pede — são **12**. O desenvolvedor explicou isso na análise, corretamente.

### 3. As travas de byte, contra o ORIGINAL

- `firmware/ORIGINAL/GN438_original.bin` → `b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f`. **Intacto.**
- Bootloader `0x0..0xE000` **igual ao ORIGINAL**.
- Setor `0xD000` **intocado**.
- PSMP (`0x1FC000+`) **intocada**.
- Bytes alterados **abaixo de `0xE000`: 0**.

### 4. O kit

- `release/OpenPod-5.3/OpenPod_OpenPod5.3.up`: cabeçalho `CONFIG` / `SL6801`, offset do payload `0x100`,
  cobertura `0x1AF000` (a PSMP, em `0x1FC000+`, fica **fora**).
- **CRC16 do payload = `0xD5DF` = o CRC gravado no cabeçalho. Confere.**
- O payload é **idêntico à imagem 5.3 carimbada** (`0x1AF000` bytes, **0** diferentes). O `.up` carrega a
  imagem inteira a partir do offset 0 (bootloader e tabela inclusos) — não é um delta.
- `tools/organiza_pacote.py release/OpenPod-5.3 --conferir` → **"pacote conferido: OK"**.
- **A prova mais forte:** o `.up` novo difere do `.up` **publicado da 3.5** em **14 bytes** — os 12 do
  carimbo mais os 2 bytes do CRC16 no cabeçalho (`0x000014`: `7D C2` → `DF D5`). **Nada mais.**

### 5. O pacote do Tune (feito pela coordenação)

- `openpod-system-5.3.tar.gz`, sha `612d015bb98b3c01848dea550cf3dbf5de79ec616d4228ec4522a085cbf8c39a`.
- **Assinatura Ed25519 válida** (chave pública `0cfcee1a…c949`).
- **SHA256SUMS confere** em todos os membros.
- MANIFEST: `linha=system`, `versao=5.3`, e os dois `expect` **de sempre** (bootloader `47fe9ad6…` e
  tabela `ca23eb0c…`) — nada mudou.
- O `update.up` dentro do pacote é **byte a byte** o `.up` do release
  (`63520f82154902a0611a56d94bdf2246c434645506d17a60f6c1ffa9b6160a29`), e o payload dele é a imagem 5.3.
- `_local/publicar/pacotes/index.json` agora aponta `system: 5.3` com o sha **igual** ao do pacote.
  O pacote antigo da 3.5 saiu da pasta.

### 6. O site (`docs/index.html`)

Conferi **todas** as linhas de texto que mudaram (PT e EN):

- Cabeçalho: `Reload 3.5` → `5.3`, data `26/11/2026` (nos dois idiomas).
- Card do OpenPod System: `· Reload 3.5` → `· 5.3` (e o `alt` da imagem).
- Histórico: linha nova **acima** da 3.5 — `5.3 · 26/11/2026` → *"Renumeração da 3.5, mesmas funções;
  atualize pelo cartão (.up) ou Recovery"* (e a equivalente em inglês).
- Próximas versões: `3.6 · 10/01/2027` → **`5.4 · 10/01/2027`**; `4.0 · previsto` → `5.5 · previsto`.
- Créditos do ePet: "previsto para a 3.6" → "previsto para a **5.4**" (PT e EN).
- Passo a passo de instalação: "começa com `Reload`" → "começa com **`OpenPod`**" (PT e EN). **Correto**,
  porque o carimbo novo começa com "OpenPod".
- **O card e o histórico do RockBox NÃO foram tocados.**

### 7. Testes

`sh tools/ci.sh` → **CI OK** (rodei de novo na conferência).

---

## Ponto para o decisor (não é erro, é uma escolha que a ficha não cobria)

O desenvolvedor renumerou também o **`4.0 · previsto`** (jogos pelo cartão SD + kit aberto para a
comunidade) para **`5.5 · previsto`**, por coerência com "as próximas versões do System passam a 5.x".
Ele marcou como **PROVÁVEL** e avisou que dá para reverter com uma linha.

**A minha leitura:** está coerente com o que você pediu (o System passa a ser 5.x, e o 5.4 já é a
ficha 027). Mas o "4.0" era um marco grande, e a ficha 032 fala em "5.x" só para o 5.3/5.4.
**Decisão do decisor:** manter o 5.5 ou voltar para 4.0. (Não publica nada: a página só vai ao ar com
o "pode", e o texto pode ser ajustado antes.)

---

## O que falta (depende do decisor)

1. **O teste no aparelho** — ele é quem grava. O que observar:
   - Config → Informações mostra **`OpenPod 5.3`**;
   - o aparelho **inicia** (o carimbo é lido no boot);
   - o nome da música no cartão da home continua aparecendo (a 3.5 Diag 2);
   - se quiser instalar por cartão: o `update.up` na raiz do cartão + Configurações → Atualizar por SD.
2. **O "pode"** para publicar. Aí eu rodo a receita do `COMO-RETOMAR` §5 com
   `--versao OpenPod-5.3 --nome-tela "OpenPod 5.3"`, e confiro online o sha do `index.json` e o
   download do pacote.

**Nada foi gravado no aparelho. Nada foi publicado.**
