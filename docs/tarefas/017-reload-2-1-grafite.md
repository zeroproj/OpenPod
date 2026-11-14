# Ficha 017 — OpenPod Reload 2.1: ícones da home em grafite

Tipo: **Leve** (só imagem; o código é o da 2.0). Base: `privado-completo`. Desenvolvedor: `opencode/deepseek-v4.1-flash-free`.
Decisão do decisor: D13 (`docs/decisoes.md`). Prévia **aprovada** em 2026-11-14 ("Aprovado.. está ótimo"):
`docs/previas/2026-11-14_reload21_grafite.png`.

Antes de começar, ler:
- `docs/processo.md`.
- `tools/desenha_icones_home.py`, `tools/fab_icones_home.py`, `tools/fab_home_moldura.py`.
- As receitas `RELOAD_1_0_RC4` (onde entra a folha) e `reload_2.0` em `tools/build.py`.
- `release/OpenPod-Reload-2.0/`.

## O desenho aprovado
Na prévia, os ícones foram desenhados pelo próprio `tools/desenha_icones_home.py`, com `GLIFO=255,255,255`. Mudaram só três coisas:
- `CORES` = o mesmo degradê grafite nos 9 ícones: topo `(84,84,90)` → base `(46,46,50)`;
- o furo do disco de música, `(214,30,70)`, vira `(60,60,66)`;
- o miolo da engrenagem e a linha da pasta, `(110,116,126)`, viram `(60,60,66)`.

Forma, posição, tamanho e glifos continuam iguais.

## O que fazer
1. Parametrizar o `desenha_icones_home.py` com `ESTILO=grafite`, que aplica exatamente as três mudanças acima.
   - **Sem `ESTILO`, a saída tem de continuar byte a byte a de hoje.** Teste: regerar e conferir o sha do `assets/IconesHome.png` atual.
   - Gerar `assets/IconesHome_grafite.png` (128×160) e versionar.
2. `fab_icones_home.py` passa a aceitar também o sha do PNG grafite. Uma lista de PNGs aprovados, cada um com sha preso.
   Nenhuma outra mudança no que ele grava nem nas conferências.
3. Receita `reload_2.1` = **a mesma lista** da `reload_2.0`, com uma única diferença: o `fab_icones_home.py` recebe
   `--png assets/IconesHome_grafite.png`.
   - Teste novo (`tests/test_reload_2_1.py`):
     - a diferença 2.1 × 2.0 (sem carimbo) fica **só** dentro da paleta e dos pixels da folha (`0x0CDD5C..0x0D315C`, e onde a
       `fab_home_moldura` regrava a folha, `0x0CE000..0x0D2000`);
     - nenhum byte de código muda (lote `0x1A6000..0x1AB000`, `0xFF0C4`, `0x132242`);
     - nada abaixo de `0xE000`, nem no setor `0xD000`, nem na PSMP.
4. Prévia da tela a partir da **imagem construída**: decodificar a folha (paleta + índices) da imagem 2.1, montar a home como na
   prévia aprovada e salvar em `docs/previas/2026-11-14_reload21_da_imagem.png`. Ela tem de bater com a aprovada.
5. Kit por `gera_versao` **com a base padrão (ORIGINAL)**:
   - carimbo **`Reload 2.1`** com `patch_versao --em 0x1A4F00`;
   - pasta `release/OpenPod-Reload-2.1/` no formato da 2.0;
   - README da 2.0 com a seção nova "New in 2.1 / Novo na 2.1: ícones da tela inicial em grafite". Texto neutro, sem iPod/Apple.
6. `TESTAR.txt` curto:
   - a home com os 9 ícones grafite e a moldura branca visível;
   - cada ícone abre o app certo e volta;
   - a Tocando Agora com a capa;
   - Config → Informações = "Reload 2.1";
   - volta de segurança: 2.0.
7. Entrada no `docs/CHANGELOG.md`.

**Não publicar.** Commit obrigatório antes do sinal.

## Entrega (ficha 017)

- **`desenha_icones_home.py`**: `ESTILO=grafite` aplica só as três mudanças
  da ficha. Sem `ESTILO`, com `GLIFO=255,255,255`, o sha continua
  `fbdd1dc7…` (o atual). `assets/IconesHome_grafite.png` versionado
  (sha `1493e2a4…`).
- **`fab_icones_home.py`**: passou a aceitar uma lista de PNGs aprovados,
  cada um com sha preso (o de hoje e o grafite). Nada mais mudou.
- **`reload_2.1`**: a mesma lista da `reload_2.0`; a única diferença é o
  `fab_icones_home.py` com `--png assets/IconesHome_grafite.png`.
  Como os passos seguintes prendem o sha da imagem inteira, cada um deles
  (textos, moldura, capa e os diags B4/B6b/B7b) ganhou também o sha exato
  do prefixo 2.1 — a imagem é a mesma, só a folha difere. Eles continuam
  conferindo as próprias regiões; nenhum byte do firmware muda.
- **Teste**: `tests/test_reload_2_1.py` (6 testes OK). `sh tools/ci.sh`
  verde.
- **Prévia**: `docs/previas/2026-11-14_reload21_da_imagem.png`, montada
  decodificando a folha da própria imagem 2.1. Bate com a aprovada
  (diferença média do painel ~0,3/255, só pela quantização da paleta).
- **Kit**: `gera_versao` sem `--base` (base padrão ORIGINAL), carimbo
  `Reload 2.1` em `0x1A4F00`. Imagem `a99288bb…`; `.up` 1.749.248 B, CRC
  `0x9750`, sha `9e5ae4ff…`. `release/OpenPod-Reload-2.1/` no formato da
  2.0, com README (seção nova) e TESTAR curto.
- **Pendente**: teste do decisor no aparelho. Não publicado.

Regras de sempre:
- Nunca alterar `firmware/ORIGINAL`, gravar no aparelho, fazer push ou merge.
- Testes protegidos intactos; `sh tools/ci.sh` verde.
- Não usar `cd` nem caminho absoluto; nada em `/tmp`.

Sinal final sozinho numa linha: `PRONTO-017` ou `ESCALADA-017`.
