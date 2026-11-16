# Ficha 019 — OpenPod Reload 2.2.1: limite de tamanho da capa

Tipo: **Risco** (código no caminho da capa; vai ao aparelho e ao público). Base: `privado-completo`.
Desenvolvedor: `opencode/deepseek-v4.1-flash-free`. Decisão do decisor (2026-11-15): "criar a 2.2.1 com limite… é a melhor solução".

Antes de começar, ler:
- `docs/processo.md` (o fim: relatos do GN-408).
- `docs/tarefas/015-analise.md` e `016-analise.md`.
- `007-rc7-capa-album.md` §3: o contrato do `carrega_capa`.
- `tools/diag_b7.s`, `tools/fab_diag_b7.py`, `tools/fab_capa_album.py`.
- As receitas `reload_2.2` e `reload_1.0_rc7_diag_b7b` em `tools/build.py`.

## Problema (aparelho, relato de usuário)
- **Músicas:** 208 MP3 do SpotiFLAC, que embute **capas em alta resolução**.
- **Sintomas na 2.0:** o play começa **7–8 s** depois; na troca de faixa **trava e desliga**, em geral depois que a capa carrega.
- O GN-408 roda a ROM do 438 perfeitamente; a RC6, sem capa, também.
- **HIPÓTESE:** o TJpgDec decodifica o Huffman da imagem inteira mesmo com `s=3`. Uma capa de 1500–3000 px leva segundos na PreTask, que
  segura o fluxo do play.
- No decisor, com 300 músicas de capas pequenas, nunca falhou.

## O que a 2.2.1 faz
Recusar cedo a capa grande, **antes do trabalho pesado**, e mostrar o quadrado cinza na hora:
1. **Limite em bytes:** se o tamanho da imagem no quadro `APIC` passar de `LIMITE_BYTES`, cinza, sem ler a imagem.
2. **Limite em pixels:** depois do `jd_prepare`, que só lê cabeçalhos e é rápido, se `w > LIMITE_PX` ou `h > LIMITE_PX`, cinza, **sem**
   chamar o `jd_decomp`.
3. Valores iniciais: `LIMITE_PX = 1000`, `LIMITE_BYTES = 512 KiB`.
   - Os dois ficam em **constantes** fáceis de mudar na ferramenta e na receita: o decisor vai medir no aparelho e pode pedir outro valor.
   - O resto do comportamento é idêntico à 2.2: yield, mensagens, guardas.
4. Liberar tudo e fechar o arquivo nesses caminhos novos, como nos outros caminhos de falha.

## Perguntas (só leitura e emulador)
1. Onde, no `carrega_capa` (`0xDAA256`, código da RC7 que está na 2.2), ficam:
   - o tamanho da imagem no `APIC`;
   - o retorno do `jd_prepare` com `w`/`h` (`jd+0x1C`/`+0x1E`, conferir).
   Mostrar os endereços e o menor patch: um desvio para uma rotina nova na área livre, com bit Thumb, e a volta para o caminho do cinza
   que já existe.
2. Medir no emulador as instruções do `carrega_capa` com `jd_prepare` e `jd_decomp`, para capas baseline de 640, 1000, 1500, 2000 e
   3000 px.
   - Gerar os MP3 de teste **dentro do teste**, sem versionar arquivos grandes, com um gerador no repositório como o `gera_mp3.py`:
     JPEG q95, 4:4:4, com textura.
   - Comparar com as capas atuais de 300 e 500 px, que no aparelho levam menos de 1 s. Mostrar a razão.
3. Confirmar que, com o limite, a capa de 3000 px vira cinza depois de **poucas** instruções. Medir.

## O que entregar
1. `docs/tarefas/019-analise.md`, curto: endereços, a medição e a tabela por tamanho.
2. Receita `reload_2.2.1` = `reload_2.2` + o passo novo do limite.
   - Diferença contra a 2.2 só no lote do código da capa e no carimbo.
   - Folha de ícones e telas iguais à 2.2.
3. Testes em `tests/test_reload_2_2_1.py`:
   - bit Thumb e alinhamento;
   - capa ≤ limite igual à 2.2, com os mesmos pixels;
   - capa > limite em px → cinza sem `jd_decomp`;
   - capa > limite em bytes → cinza sem ler a imagem;
   - nada vaza: `tmp` e FIL liberados, arquivo fechado;
   - nada abaixo de `0xE000`, nem no setor `0xD000`, nem na PSMP.
4. Kit por `gera_versao` **com a base padrão (ORIGINAL)**:
   - carimbo **`Reload 2.2.1`**;
   - `release/OpenPod-Reload-2.2.1/` no formato da 2.2, com o Flashloader em `windows/`, copiado de `firmware/VENDOR`;
   - README com "New in 2.2.1 / Novo na 2.2.1": capas muito grandes (mais de 1000 px ou de 512 KB) mostram o quadrado cinza, para a
     música começar na hora. Dica neutra: reduzir as capas para ~300 px com um editor de etiquetas.
5. `TESTAR.txt`:
   - os 5 MP3 de capa grande (640..3000 px) e a música 01 de teste;
   - medir o atraso do play;
   - trocar de faixa várias vezes;
   - volta de segurança: 2.2.
6. Entrada no `docs/CHANGELOG.md`.

**Não publicar.** Commit obrigatório antes do sinal.

Regras de sempre:
- Nunca alterar `firmware/ORIGINAL`, gravar no aparelho, fazer push ou merge.
- Testes protegidos intactos; `sh tools/ci.sh` verde.
- Todo destino de `bx`/`blx` com bit Thumb; tabelas alinhadas; XIP só leitura.
- Não usar `cd` nem caminho absoluto; nada em `/tmp`.

Sinal final sozinho numa linha: `PRONTO-019` ou `ESCALADA-019`.
