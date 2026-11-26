APROVADO COM RESSALVAS

# Revisão da ficha 030 — OpenPod System 5.3

Intervalo revisado: `7d0bfae..13d1c01`. Ficha, análise do desenvolvedor e conferência da coordenação lidas. Verificação independente em 26/11/2026: receita recompilada em `.tmp/` (sem tocar código, testes, kits nem imagens versionadas). Nenhuma alteração de arquivo além deste parecer.

## Provas — todas CONFIRMADO

1. **Diferença byte a byte (foco 1).** `openpod_5_3_carimbado.bin` vs `reload_3.5_carimbado.bin` (ambos 2 097 152 B): **12 bytes diferentes**, exatamente `0x1A4F00..0x1A4F0B`; nenhum outro byte. O ponteiro em `0x10A59C` é `00 4F DA 00` (`0x00DA4F00`) nas duas imagens — **inalterado**. A string de fábrica em `0x04EA8B` é `yp3_2.0.43\0` nas duas.
2. **Texto lido pelo ponteiro (foco 2).** `ptr = 0x00DA4F00` → offset `0x1A4F00` → `b'OpenPod 5.3\x00\xff\xff\xff\xff'`. O `patch_versao.py` reporta **72 px** (tela aceita 113 px) e imprime `relido pelo ponteiro -> 'OpenPod 5.3' OK`.
3. **Travas de byte (foco 3).** ORIGINAL = `b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f`. Contra ele: **0** bytes alterados abaixo de `0xE000`, **0** no setor `0xD000`, **0** em `0x1FC000+`; bootloader `0x0..0xD000` idêntico; menor offset alterado `0x486A0`. O `build.py` repetiu as três travas verdes em `.tmp/`.
4. **Kit (foco 4).** `release/OpenPod-5.3/OpenPod_OpenPod5.3.up`: `CONFIG`/`SL6801`, offset `0x100`, cobertura `0x1AF000` (< `0x1FC000`, PSMP fora). CRC16 calculado sobre o payload = `0xD5DF` = CRC gravado em `0x14`. Payload idêntico a `openpod_5_3_carimbado.bin[:0x1AF000]` (**0** diferenças). Prova extra: o `.up` novo difere do `.up` publicado da 3.5 em **14 bytes** — os 12 do carimbo (em `0x1A5000..0x1A500B`, = `0x100 + 0x1A4F00`) e os 2 do CRC (`0x14`: `7D C2` → `DF D5`). Nada mais.
5. **Site (foco 5).** PT/EN conferidos: `<span class="ver">` do cabeçalho = `5.3` (linhas 149, 440); `<figcaption>` do System = `· 5.3` (157, 448); histórico com `5.3 · 26/11/2026` acima da 3.5 (220, 513); `3.6 · 10/01/2027` → `5.4 · 10/01/2027` (236, 529); passo a passo "começa com `OpenPod`" (321, 614). Os 6 payloads base64 são **idênticos** aos de `7d0bfae` — só o `alt` do card do System mudou de `3.5` para `5.3`; as linhas do card e do histórico do RockBox aparecem no diff apenas como contexto, sem nenhuma alteração.
6. **Arquivos proibidos (foco 6).** O diff toca só `docs/index.html`, `docs/tarefas/030-analise.md` e arquivos novos de kit (`firmware/RELEASE/OpenPod 5.3/`, `release/OpenPod-5.3/`). Nenhum `tools/`, nenhum código de firmware, nenhuma ferramenta das listas `PROIBIDAS` (`tests/test_rc*.py`, `tests/test_reload_*.py`). `sh tools/ci.sh` → **CI OK** (10 + 29 + 1 testes, catraca e segredos).
7. **Reprodutibilidade.** `build.py --receita reload_3.5b` em `.tmp/` deu `ba56813d…d40f8`; `patch_versao.py --texto "OpenPod 5.3" --em 0x1A4F00` sobre ele deu `8551ea02…e30e1`, sha **igual** ao de `firmware/WORKING/openpod_5_3_carimbado.bin`.

## Achado

### BAIXA — renumeração `4.0 → 5.5` extrapolou a ficha e segue sem decisão do decisor

- **Arquivo:** `docs/index.html:237` (PT) e `docs/index.html:530` (EN).
- **Prova:** o diff `7d0bfae..13d1c01` troca `<tr><td>4.0 · previsto</td>` por `<tr><td>5.5 · previsto</td>` nas duas tabelas de "Próximas versões". A ficha 030, item 6 (`docs/tarefas/030-openpod-system-5-3.md:67-68`), pediu explicitamente só `3.6 → 5.4`; o desenvolvedor marcou o `4.0 → 5.5` como **PROVÁVEL** (`docs/tarefas/030-analise.md:101-103`) e a coordenação encaminhou a escolha ao decisor sem decisão registrada (`docs/tarefas/030-conferencia.md:91-100`). A mudança conexa nos créditos (`3.6 → 5.4`, linhas 382 e 675) é coerente com o que a ficha pediu e **não** é achado.
- **Cenário concreto:** se o decisor quiser preservar o marco "4.0 · previsto" (jogos pelo cartão SD + kit aberto para a comunidade), a página irá ao ar anunciando "5.5 · previsto" sem autorização da ficha 030; basta reverter essas duas linhas antes do "pode". Não afeta imagem, firmware, kit, pacote nem nenhuma trava de byte — por isso BAIXA, não ALTA.

## Fora do diff / do foco desta revisão

- Pacote do Tune (`openpod-system-5.3.tar.gz`): pertence a outro repositório; a coordenação executou e conferiu em `docs/tarefas/030-conferencia.md:59-69` (sha `612d015b…`, Ed25519 válida, SHA256SUMS e `expect` de sempre). Não está no intervalo `7d0bfae..13d1c01`.
- Gravação no aparelho e publicação: dependem do teste e do "pode" do decisor (`docs/tarefas/030-conferencia.md:104-115`). Nada foi gravado ou publicado.

REVISAO-030
