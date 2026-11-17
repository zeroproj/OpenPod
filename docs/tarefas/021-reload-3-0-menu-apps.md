# Ficha 021 — OpenPod Reload 3.0: o menu Apps

Tipo: **Risco** (mexe na navegação da home; vai ao aparelho e ao público). Base: `privado-completo`. Desenvolvedor:
`opencode/deepseek-v4.1-flash-free`.

Decisão do decisor (2026-11-17): ligar o menu Apps escondido e lançar como **Reload 3.0**. Os jogos do SDK do SL6801_player (D15)
entram depois, em outra ficha, **dentro** deste menu.

Antes de começar, ler:
- `docs/tarefas/020-analise.md` inteiro, em especial §4 e §9.
- `docs/tarefas/006-rc6-home-moldura.md`: como a home foi alterada (moldura, rótulos, tabela de posições).
- `tools/fab_home_moldura.py`, `tools/fab_textos.py` e o `aplica_textos`, se existir.
- `tools/desenha_icones_home.py` (estilo `escuro_colorido`) e `tools/fab_icones_home.py`.
- A receita `reload_2.2.1` em `tools/build.py`.

## O que já se sabe (020, conferido pela coordenação)
- A página **Apps = 0x52**: `page_home_menu_create` em `0xD2F0A0`, chamada em `0xD23CF8` pelo `view_page_create`.
  - Monta 3 itens com os títulos da tabela em XIP `0xC486E8` = `[7, 4, 11]`: **Despertador, Imagem, Dicionário**.
- A home tem 9 posições. A tabela de rótulos em XIP `0xC486C4` (a linha do meio começa em `0xC486D4` = `[2,4,9]`) põe o **índice 5 =
  Imagem** (string 4), que abre a página **0x15**.
- **Falta achar:** onde o índice do ícone da home vira a página de destino, o ponto que leva o índice 5 à 0x15.

## O que a 3.0 faz
1. **Na home, o ícone de Imagem vira Apps**:
   - o rótulo do índice 5 aponta para um texto novo "Apps" (pt: "Apps"; en: "Apps"), embora a home do OpenPod não mostre nomes,
     porque o título pode aparecer em outras telas;
   - o destino do índice 5 passa a ser a **0x52**, no lugar da 0x15.
2. **O desenho do ícone:** na folha `escuro_colorido`, o glifo de Imagem do índice 5 vira um glifo de **Apps**: 4 quadradinhos
   arredondados em grade 2×2, na cor verde do ícone atual `(120,220,120)`, com o mesmo fundo escuro.
   - Gerar com `desenha_icones_home.py` (`ESTILO=escuro_colorido`, glifo novo só nessa posição).
   - **Prévia obrigatória** em `docs/previas/` antes do kit.
3. **O menu Apps (0x52)** fica como a fábrica fez: Despertador, Imagem e Dicionário.
   - Descrever, com uma imagem montada a partir do firmware, como a tela 0x52 aparece com o tema do OpenPod (fundo preto, barra,
     fonte), sem mudar nada.
   - Se o Dicionário abrir uma tela de erro sem `0:/dict/`, registrar. Ele sai na ficha dos jogos.
4. **Imagem continua acessível** pelo menu Apps.

## Perguntas
1. O ponto índice → página da home: endereço, instrução e tabela no ORIGINAL e na 2.2.1. O menor patch possível.
2. Ao voltar do Apps (Esc), a home volta com a moldura no índice 5? Ao voltar do Despertador e da Imagem, volta ao Apps?
   - Provar pela pilha de navegação da fábrica (`0xCEEAFC`/`0xCEEFE0` na referência; achar os nossos).
3. O presenter do Apps aceita os 3 índices (Despertador, Imagem, Dicionário)? Para onde cada um leva?

## O que entregar
1. `docs/tarefas/021-analise.md`.
2. Receita `reload_3.0` = `reload_2.2.1` + o patch do destino + o texto "Apps" + a folha com o glifo Apps.
   - Diferença contra a 2.2.1 só nesses pontos e no carimbo.
3. Testes em `tests/test_reload_3_0.py`:
   - o índice 5 leva à 0x52;
   - os outros 8 ícones continuam com o destino da fábrica;
   - a folha muda só no ícone 5;
   - bit Thumb; nada abaixo de `0xE000`, nem no setor `0xD000`, nem na PSMP.
4. Prévia da home e do menu Apps em `docs/previas/`.
5. Kit por `gera_versao` **com a base padrão (ORIGINAL)**:
   - carimbo **`Reload 3.0`**;
   - `release/OpenPod-Reload-3.0/` no formato da 2.2.1, com o Flashloader em `windows/`, copiado de `firmware/VENDOR`;
   - README com "New in 3.0 / Novo na 3.0": menu Apps na tela inicial, com Despertador e Imagem;
   - texto neutro, compatibilidade SL6801 como na 2.2.1.
6. `TESTAR.txt`:
   - abrir Apps, Despertador e Imagem e voltar com Esc;
   - a moldura no lugar certo;
   - os outros 8 ícones abrem o mesmo de antes;
   - a capa continua aparecendo;
   - volta de segurança: 2.2.1.
7. Entrada no `docs/CHANGELOG.md`.

**Não publicar.** Commit obrigatório antes do sinal.

Regras de sempre:
- Nunca alterar `firmware/ORIGINAL`, gravar no aparelho, fazer push ou merge.
- Testes protegidos intactos; `sh tools/ci.sh` verde.
- Todo destino de `bx`/`blx` com bit Thumb; tabelas alinhadas; XIP só leitura.
- Não usar `cd` nem caminho absoluto; nada em `/tmp`.

Sinal final sozinho numa linha: `PRONTO-021` ou `ESCALADA-021`.
