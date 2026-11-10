# Ficha 015 — RC7: a capa sem engasgar a música (degraus B7a: escala menor; B7b: escala menor + pausas)

Tipo: **Risco**. Base: `privado-completo` (com a ficha 014). Desenvolvedor: `opencode/deepseek-v4.1-flash-free`.

Antes de começar, ler:
- `docs/tarefas/014-analise.md` inteiro, com "Resultado do B6b no aparelho".
- `014-revisao.md`.
- `tools/diag_b6.s`, `tools/fab_diag_b6.py`.
- `007-rc7-capa-album.md` §3.

## Fato (aparelho)
- **B6b mostra a capa.** A PreTask lê e decodifica, e a view recebe 8 mensagens tipo 6.
- **Defeito:** engasgada curta no áudio (< 1 s), só no início, em todas as músicas, enquanto a capa carrega.
- **HIPÓTESE da coordenação:** a PreTask segura a CPU e o cartão durante o `carrega_capa` (`jd_prepare`/`jd_decomp` + leituras). A MediaTask, de
  mesma prioridade (3), não recebe tempo suficiente para manter o buffer de áudio.

## Decisão (decisor, 2026-11-10)
**1. Decodificar menor.** A tela é pequena e simples; a perda não aparece. Hoje o `carrega_capa` escolhe o maior `s` (0..3) com
`w>>s ≥ 64` e `h>>s ≥ 64`. Nova regra: o maior `s` com `w>>s ≥ 56` e `h>>s ≥ 56`, esticando para 64×64 como já faz.
- Exemplos: 500×500 passa a `s=3` (62×62); 300×300 continua `s=2`.
- **PROVÁVEL:** o TJpgDec com `s=3` usa só o coeficiente DC, sem IDCT, e fica muito mais rápido. Confirmar no código `0xD11090`.

**2. Pausas curtas durante o decode** (só no B7b). A PreTask cede a vez periodicamente enquanto lê e decodifica a capa. A capa pode demorar um pouco mais;
a música não pode engasgar. **Não** atrasar o início da capa com espera longa: a PreTask também cuida do título e do tempo.

## Perguntas (só leitura do ORIGINAL)
Classificar cada resposta como CONFIRMADO, PROVÁVEL ou HIPÓTESE, com endereço e instrução em cada afirmação.

1. **A função de dormir da fábrica.** Qual função a fábrica usa para uma tarefa dormir N ticks/ms? Ponto de partida: o loop da ViewTask dorme em
   `0xD2436E` (`b.w 0x811700`); procurar outras chamadas em tarefas da fábrica.
   - Qual é a unidade do argumento e o período do tick? Provar pelo código de configuração do timer/RTOS.
   - É seguro chamá-la da PreTask, sem trava pega (o mutex do banco e o lock do FatFs não podem estar presos no momento da pausa)?
   - Existe também um "ceder a vez" sem dormir (yield)? Qual dos dois deixa a MediaTask rodar, dado que ela tem a mesma prioridade?
2. **Onde pausar.** O `carrega_capa` da RC7 (`0xDAA256`) passa ao TJpgDec uma função de entrada (leitor, perto de `0xDAA9B6`) e uma de saída
   (perto de `0xDAA8E0`).
   - Mostrar os dois ponteiros.
   - Contar quantas vezes cada uma é chamada para capas 300×300, 500×500 e 1000×1000, no emulador.
   - Verificar que nenhuma trava (FatFs, banco) está presa dentro delas.
3. **Quanto pausar.** Escolher N (uma pausa a cada N chamadas) e a duração, para que:
   - nenhum trecho sem pausa passe de ~5 ms de trabalho (estimar pelas contagens);
   - o atraso total somado à capa fique ≤ 500 ms para 500×500.
   - Mostrar a conta.

## O que entregar
1. `docs/tarefas/015-analise.md`, curto: respostas, a conta e o que não dá para saber.
2. **Duas** imagens, ambas = B6b exata (a do commit `a78a169`, `.up` `1c06cbdf…`):
   - **B7a** = B6b + a regra de escala nova (decisão 1). Só isso.
   - **B7b** = B7a + as pausas (decisão 2).

   Medir no emulador o número de instruções do `carrega_capa` para 300/500/1000 px no B6b e no B7a. A conta da pergunta 3 vale para o B7b.
   Detalhes das pausas no B7b:
   - Embrulhar a entrada e/ou a saída do TJpgDec com uma rotina nossa que chama a original e, a cada N chamadas, a pausa da fábrica.
     - Trocar só os ponteiros que o `carrega_capa` passa a `jd_prepare`/`jd_decomp`.
     - Contador em pilha ou no contexto `tmp` (`calloc` da PreTask): nada de RAM nova; flash XIP só leitura.
   - A view só ganha uma guarda: o tipo 6 exige `msg+0xA == 0x408` antes de copiar (BAIXA da `014-revisao`).
   - Tudo o mais igual ao B6b.
3. Receitas `reload_1.0_rc7_diag_b7a` e `reload_1.0_rc7_diag_b7b`, premissas conferidas, testes em `tests/test_diag_trava.py`:
   - Bit Thumb; tabelas alinhadas; XIP só leitura.
   - A pausa é chamada o número esperado de vezes.
   - A pilha continua com folga ≥ 512 B na PreTask.
   - Nenhuma pausa com trava presa.
   - B7b: o resultado em pixels é idêntico ao do B7a.
   - B7a: capa válida em 300/500/1000 px; imagem menor que 56 → cinza.
4. Kit por `gera_versao` **com a base padrão (ORIGINAL)**:
   - Carimbos `RC7 diag B7a`/`RC7 diag B7b`, com `patch_versao --em 0x1A4F00`.
   - Pastas `release/OpenPod-Reload-1.0-RC7-Diag-B7a`/`-B7b`, cada uma com `TESTAR.txt` curto:
     - A música engasga no início?
     - Quanto tempo a capa leva para aparecer?
     - Trocar de faixa; sair e entrar.
     - Volta de segurança: RC6.
   - Contagem de bytes contra o B6b, entre imagens carimbadas.

Ordem no aparelho (decisor): **B7a primeiro**. Se não engasgar, fica a B7a, que é a mais simples.

Regras de sempre:
- Nunca alterar `firmware/ORIGINAL`, gravar no aparelho, fazer push ou merge.
- Testes protegidos intactos; ferramenta nova ≤ 350 linhas.
- Nada abaixo de `0xE000`; setor `0xD000` e PSMP intocados; `sh tools/ci.sh` verde.
- Todo destino de `bx`/`blx` com bit Thumb; lr de `bl` com bit0=1.
- A ViewTask não chama função de arquivo.
- Não usar `cd` nem caminho absoluto; arquivos temporários só dentro deste diretório e fora do commit.

Sinal final sozinho numa linha: `PRONTO-015` ou `ESCALADA-015`.
