# Ficha 030 — análise do desenvolvedor

Renumeração do OpenPod System: **Reload 3.5 → OpenPod 5.3** (D51, 26/11/2026).
As funções são as mesmas; muda só o carimbo da tela Informação.

## 1. Compilação da imagem sem carimbo — CONFIRMADO

```
python3 tools/build.py --receita reload_3.5b --saida firmware/WORKING/openpod_5_3.bin
```

- sha256 de `firmware/WORKING/openpod_5_3.bin`:
  `ba56813d9c15d53f27dc684b21b4e1a92b094f0fd9f0db2bb4e7e122289d40f`
- É o mesmo sha de `firmware/WORKING/reload_3.5.bin` e o sha de referência da
  coordenação. **CONFIRMADO.**
- O `build.py` terminou com as travas verdes: nada abaixo de `0x00D000`,
  setor `0x00D000` intocado (R1) e PSMP (`0x1FC000+`) intocada.

## 2. Carimbo — CONFIRMADO

```
python3 tools/patch_versao.py \
  --in  firmware/WORKING/openpod_5_3.bin \
  --out firmware/WORKING/openpod_5_3_carimbado.bin \
  --texto "OpenPod 5.3" --em 0x1A4F00
```

Saída da ferramenta (trechos):

- texto novo `'OpenPod 5.3'` = **72 px** (a tela Informação aceita 113 px por
  linha). **CONFIRMADO** — o `patch_versao.py` imprime a medida.
- alterações: `0x1A4F00` (12 B, o texto) e `0x10A59C` (4 B, o literal
  `0x00C4EA8B → 0x00DA4F00`).
- conferência relendo **pelo ponteiro**: `'OpenPod 5.3'  OK`.
- a string de fábrica `yp3_2.0.43` em `0x04EA8B` fica intacta.

## 3. Diferença byte a byte contra a 3.5 carimbada — CONFIRMADO

Comparação de `firmware/WORKING/openpod_5_3_carimbado.bin` com
`firmware/WORKING/reload_3.5_carimbado.bin` (ambas 2 097 152 B):

- **12 bytes diferentes**, exatamente em
  `0x1A4F00 0x1A4F01 0x1A4F02 0x1A4F03 0x1A4F04 0x1A4F05
   0x1A4F06 0x1A4F07 0x1A4F08 0x1A4F09 0x1A4F0A 0x1A4F0B`
  (faixa `0x1A4F00..0x1A4F0B`).
- **O ponteiro em `0x10A59C` NÃO mudou:** continua `00 4F DA 00`
  (`0x00DA4F00`) nas duas imagens.
- Nenhum outro byte da imagem mudou.
- Texto na 3.5: `b'Reload 3.5\x00\xff\xff\xff\xff\xff'`.
  Texto na 5.3: `b'OpenPod 5.3\x00\xff\xff\xff\xff'`.
- A string de fábrica em `0x04EA8B` é idêntica nas duas: `b'yp3_2.0.43\x00'`.

> Observação: o `patch_versao.py` reporta **15 bytes** porque a comparação dele
> é contra a imagem **sem** carimbo (`openpod_5_3.bin`): 12 do texto + 3 do
> ponteiro que ainda estava de fábrica. Contra a 3.5 **carimbada**, são os
> **12** bytes do texto — que é a conferência pedida.

sha256 de `firmware/WORKING/openpod_5_3_carimbado.bin`:
`8551ea02f16f17847dd9928dcdc3f2b2afa8cd833a12486ed85d97b8e74e30e1`
(novo, como esperado: o carimbo mudou).

## 4. ORIGINAL e regras de byte — CONFIRMADO

- `firmware/ORIGINAL/GN438_original.bin`:
  `b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f`
  (confere; o `sh tools/ci.sh` também confere).
- Menor offset alterado da imagem nova contra o ORIGINAL: `0x0486A0` — **nada
  abaixo de `0xE000`**.
- Setor `0xD000` intocado; bootloader (`< 0xD000`) intocado; PSMP
  (`0x1FC000+`) intocada.

## 5. Kit — CONFIRMADO

`python3 tools/gera_versao.py --imagem firmware/WORKING/openpod_5_3_carimbado.bin
--versao OpenPod-5.3 --nome-tela "OpenPod 5.3"` criou:

- interno: `firmware/RELEASE/OpenPod 5.3/`
- público: `release/OpenPod-5.3/` (`.up`, `README.md`, `install.sh`,
  `cabo/flash_...sh`, `cabo/setores/`, `windows/LEIA-ME.txt`)

Conferência independente do `.up` (`release/OpenPod-5.3/OpenPod_OpenPod5.3.up`):

- cabeçalho `CONFIG` / `SL6801`; offset `0x100`; cobertura `0x1AF000`.
- CRC16 do payload = `0xD5DF` = CRC do cabeçalho. **CONFIRMADO.**
- payload idêntico a `firmware/WORKING/openpod_5_3_carimbado.bin[:0x1AF000]`.
- PSMP fora da cobertura (`0x1AF000 < 0x1FC000`).
- bootloader e setor `0xD000` dentro do `.up` iguais ao ORIGINAL.
- sha256 do `.up`:
  `63520f82154902a0611a56d94bdf2246c434645506d17a60f6c1ffa9b6160a29`.
- `README.md` do kit: seção **“New in 5.3 / Novidades da 5.3”** escrita à mão;
  nenhum marcador `{TELA}` / `{CURTO}` / `{BETA}` / `{UP}` sobrou.

## 6. Site (`docs/index.html`, PT e EN) — CONFIRMADO

- cabeçalho: `<span class="ver">Reload 3.5</span>` → `5.3`, data `26/11/2026`.
- card do OpenPod System: `Reload 3.5` → `5.3` (e o `alt` da imagem).
- histórico: linha nova acima da 3.5:
  `5.3 · 26/11/2026` — “Renumeração da 3.5, mesmas funções; atualize pelo
  cartão (.up) ou Recovery” (e a equivalente em inglês).
- próximas versões do System: `3.6 · 10/01/2027` → `5.4 · 10/01/2027`;
  por coerência com “as próximas versões do System passam a 5.x”, a antiga
  `4.0 · previsto` virou `5.5 · previsto` (mesmo recurso). **PROVÁVEL** que a
  coordenação queira esse ajuste; se não, é uma linha para reverter.
- referências ao bichinho virtual “previsto para a 3.6” nos créditos (PT/EN)
  passaram a `5.4`.
- passo a passo de instalação (PT/EN): “começa com `Reload`” → “começa com
  `OpenPod`”.
- card e histórico do RockBox **não** foram tocados.

## 7. Pacote do Tune (`openpod-system-5.3.tar.gz`) — NÃO EXECUTADO AQUI

O passo 5 da ficha manda rodar `pacotes/gera_pacotes.py` de dentro de
`OpenPod-instalador`, que é **outro repositório**, fora desta raiz. As regras
desta sessão proíbem `../` e qualquer caminho fora do repositório; a
`docs/COORDENACAO-AGENTES.md` §2 também diz que o despacho é sempre de dentro
do repositório certo e que a coordenação **empacota e assina**. Por isso:

- **não** gerei o `openpod-system-5.3.tar.gz`;
- **não** alterei `_local/publicar/pacotes/index.json` (continua com `system: 3.5`);
- a assinatura Ed25519, o `SHA256SUMS` e o `expect` do MANIFEST (item 6 de “O
  que provar”) ficam para a sessão de `OpenPod-instalador` / coordenação.

O `.up` e a imagem que o pacote deve consumir estão prontos e conferidos em
`release/OpenPod-5.3/OpenPod_OpenPod5.3.up`.

## 8. Testes

`sh tools/ci.sh` → **CI OK** (ORIGINAL intacto, arquivos protegidos, sintaxe,
testes, catraca, segredos).

## Resumo das classificações

| Afirmação | Classificação |
|---|---|
| `reload_3.5b` reproduz `ba56813d…` | CONFIRMADO |
| carimbo `OpenPod 5.3` em `0x1A4F00`, 72 px | CONFIRMADO |
| 12 bytes de diferença, `0x1A4F00..0x1A4F0B` | CONFIRMADO |
| ponteiro `0x10A59C` inalterado (`0x00DA4F00`) | CONFIRMADO |
| string de fábrica `0x04EA8B` intacta | CONFIRMADO |
| ORIGINAL com o sha esperado; regras de byte | CONFIRMADO |
| `.up` = imagem, CRC `0xD5DF`, PSMP fora | CONFIRMADO |
| site PT/EN atualizado | CONFIRMADO |
| `4.0 → 5.5` no site | PROVÁVEL (decisão de coerência) |
| pacote do Tune `openpod-system-5.3.tar.gz` | PENDENTE (outro repositório) |
