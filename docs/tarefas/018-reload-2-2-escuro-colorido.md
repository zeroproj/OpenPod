# Ficha 018 — OpenPod Reload 2.2: ícones escuros com símbolos coloridos

Tipo: **Leve** (só imagem; o código é o da 2.0/2.1). Base: `privado-completo`. Desenvolvedor: `opencode/deepseek-v4.1-flash-free`.
Decisão: **D14** (`docs/decisoes.md`), aprovada pelo decisor em 2026-11-15. Ela substitui o grafite da 2.1.
O decisor autorizou a publicação depois da conferência.

Modelo: a ficha 017 (`docs/tarefas/017-reload-2-1-grafite.md`), o mesmo caminho com outro estilo.

## O desenho aprovado (exato)
O script da prévia está em `docs/previas/2026-11-15_desenho_opcao_A.py`. É o `desenha_icones_home.py` com:
- `CORES` = `((50,50,54),(26,26,28))` nos 9 ícones;
- furos internos `(214,30,70)` e `(110,116,126)` → `(38,38,41)`;
- **cor do símbolo por ícone** = o tom claro (o 1º) do degradê original de cada ícone, na ordem da folha:
  `(255,94,98) (255,176,64) (255,82,82) (90,200,250) (255,190,70) (120,220,120) (70,150,255) (160,166,176) (90,190,255)`.

## O que fazer
1. No `desenha_icones_home.py`, criar `ESTILO=escuro_colorido` com exatamente isso, glifo por ícone incluído.
   - Sem `ESTILO`, e com `ESTILO=grafite`, a saída tem de continuar byte a byte a de hoje.
   - Gerar `assets/IconesHome_escuro_colorido.png`, que tem de ser **idêntico** ao PNG da prévia:
     `python3 docs/previas/2026-11-15_desenho_opcao_A.py <saída> <ampliada>` dá a referência.
2. `fab_icones_home.py` e as premissas das outras ferramentas: acrescentar os sha da variante nova às listas de aprovados, como na 017.
3. Receita `reload_2.2` = a lista da `reload_2.1` com `--png assets/IconesHome_escuro_colorido.png`.
   Teste `tests/test_reload_2_2.py`:
   - a diferença 2.2 × 2.1 (sem carimbo) fica só na folha (`0x0CDD5C..0x0D315C`);
   - nenhum byte de código muda;
   - nada abaixo de `0xE000`, nem no setor `0xD000`, nem na PSMP.
4. Prévia a partir da **imagem construída**: `docs/previas/2026-11-15_reload22_da_imagem.png`.
5. Kit por `gera_versao` **com a base padrão (ORIGINAL)**:
   - carimbo **`Reload 2.2`**;
   - pasta `release/OpenPod-Reload-2.2/` no formato da 2.1, com o Flashloader em `windows/`, copiado de `firmware/VENDOR`;
   - README com "New in 2.2 / Novo na 2.2: ícones escuros com símbolos coloridos", texto neutro.
6. `TESTAR.txt` curto (como o da 2.1, volta de segurança = 2.1) e entrada no `docs/CHANGELOG.md`.

**Não publicar** (a coordenação publica). Commit obrigatório antes do sinal.

## Entrega (ficha 018)

- **`desenha_icones_home.py`**: `ESTILO=escuro_colorido` aplica o desenho da
  D14 (degradê `(50,50,54)`→`(26,26,28)`, furos `(38,38,41)`, símbolo de
  cada ícone no tom claro do degradê original). Sem `ESTILO` o sha continua
  `fbdd1dc7…`; com `grafite`, `1493e2a4…`. `assets/IconesHome_escuro_colorido.png`
  versionado (sha `5eff7463…`), **idêntico byte a byte** ao PNG gerado por
  `docs/previas/2026-11-15_desenho_opcao_A.py`.
- **`fab_icones_home.py`**: a lista de PNGs aprovados ganhou o sha novo.
  Nada mais mudou no que ele grava nem nas conferências.
- **Premissas das ferramentas seguintes**: cada uma ganhou o sha da variante
  2.2 — `fab_textos` `35e9e891…`, `fab_home_moldura` `d1de3ce8…`,
  `fab_capa_album` `ddb32347…`, `fab_diag_b4` `cacaef88…`,
  `fab_diag_b6` `6fd6ddb7…`, `fab_diag_b7` `3062de54…`. Os shas antigos
  (2.0, 2.1) continuam aceitos.
- **`reload_2.2`**: a mesma lista da `reload_2.1`; a única diferença é o
  `fab_icones_home.py` com `--png assets/IconesHome_escuro_colorido.png`.
  Sem carimbo, sha `4fdd31c03ad6672ca0b15b141345b7559b2517afca19f54de0d73753f842f769`.
- **Teste**: `tests/test_reload_2_2.py` (6 testes OK) — diferença 2.2 × 2.1
  só na folha (`0x0CDD5C..0x0D315C`), código intacto, nada abaixo de `0xE000`,
  setor `0xD000` e PSMP intocados. `sh tools/ci.sh` verde.
- **Prévia**: `docs/previas/2026-11-15_reload22_da_imagem.png`, montada
  decodificando a folha da própria imagem 2.2 e reaplicando a barra e a
  moldura branca da prévia da 2.1.
- **Kit**: `gera_versao` sem `--base` (base padrão ORIGINAL), carimbo
  `Reload 2.2` em `0x1A4F00`. Imagem carimbada `7f14440a…`; `.up` 1.749.248 B,
  CRC `0x7147`, sha `73231573…`. `release/OpenPod-Reload-2.2/` no formato da
  2.1, com README (seção nova) e TESTAR curto.
- **Pendente**: o `FlashloaderSL-DEV-6.9.5.exe` não está em `firmware/VENDOR`
  neste worktree (arquivo ignorado pelo git), então `windows/` ficou só com
  o `LEIA-ME.txt`, como no kit versionado da 2.1. Falta o teste do decisor no
  aparelho. Não publicado.
- **Danos notados e não cobertos**: nenhum novo; a folha é só arte e o código
  é byte a byte o da 2.1.


Regras de sempre:
- Nunca alterar `firmware/ORIGINAL`, gravar no aparelho, fazer push ou merge.
- Testes protegidos intactos; `sh tools/ci.sh` verde.
- Não usar `cd` nem caminho absoluto; nada em `/tmp`.

Sinal final sozinho numa linha: `PRONTO-018` ou `ESCALADA-018`.
