# Ficha 011 — RC7: por que o `get_path` na ViewTask para o aparelho, e o caminho sem ele

Tipo: **Risco**. Base: `privado-completo`. Desenvolvedor: `minimax/MiniMax-M3`. Antes: `docs/tarefas/010-analise.md`
(a partir de "Conferência da coordenação", D1 a D5) e `docs/tarefas/009-analise.md` (seção "Conferência da coordenação").
As partes dessas análises marcadas como corrigidas não valem: use a conferência.

## Fato (aparelho)
| Versão | O que tem | Resultado |
|---|---|---|
| A | Rotina do título pulada | Toca |
| B0 | Rotina ligada, `get_path` cortado | Toca, quadrado cinza |
| B | Rotina ligada, com `get_path` | Reinicia |
| B2 | B + teste de tarefa morta do monitor neutralizado (`0x146B30` nop) | Congela ~15 s sem mostrar o player e reinicia sozinho; repetiu |

## Perguntas (só leitura do ORIGINAL; classificar CONFIRMADO/PROVÁVEL/HIPÓTESE; endereço e instrução em cada afirmação)
1. **O que para o refresh no B2?** Investigar cada item e dizer qual sobra:
   a. **De onde vem o comando de timer** que leva a MainTask a `0xCF7FBE` → `0xD46B14`. Quem o envia, em que tarefa ou timer?
      Se a origem depender da ViewTask ou do laço do LVGL, a MainTask pode estar viva e mesmo assim sem refresh.
   b. **Prioridades.** O descritor em `0xCF8030` (MainTask) grava 1 em `sp+0x54`; o de `0xCF8384` (ViewTask) grava 3.
      Confirmar em `0xD6ACAC` qual campo é a prioridade (e se número maior é mais prioritário) para todas as tarefas
      de `tools/stack_rc7.py --tarefas`. Se a ViewTask estiver acima da MainTask, procurar laço de espera ativa sem ceder a CPU
      na cadeia `0xCFEFC4` → `0xD6D1B4` → `0xD6F138` → `0xD777CC`, `0xD76C0A`, `0xD76854`, `0xD77C9C`.
   c. **Ciclo de travas.** A trava do banco é `[ctx]+0x5C` (`0xD6D1D0`/`0xD6D1E4`), e todas as funções do banco a usam, sobre o mesmo
      objeto de arquivo em `[ctx]+0x60`. Quem a pega, em que tarefa, e alguém a segura enquanto espera a view ou enquanto o play começa?
      Alguma tarefa espera a ViewTask de modo síncrono no play (semáforo, fila, mutex da tela)?
   d. Algum outro caminho até o reset que não passe pelo refresh, e o que dá ou não dá para saber fora do dump.
   e. Algo que explique ~15 s (prazo do wdog com `0x14`, timeout, repetição). Sem resposta é uma resposta válida: diga.
2. **O caminho do arquivo sem o banco.** Como a fábrica chega do play à abertura do arquivo de áudio? Quem chama `0xCFEFC4` e em que
   tarefa (lista completa)? **Já existe um global com o caminho da faixa atual** (o decodificador precisa dele)? Com que endereço,
   quando ele é escrito em relação à mensagem de título, e é seguro lê-lo na ViewTask? Se não existir, qual o melhor ponto na MainTask
   para capturar o caminho e entregá-lo à view, contando que a pilha da MainTask é pequena (`get_path` ≥ 2720 B, ver 009).
3. **A fábrica lê o cartão na ViewTask?** Evidência direta em fotos, e-book ou outra tela (`f_open`/`f_read` no contexto da view). Isso diz se o
   próximo passo, abrir o MP3 e decodificar o JPEG, tem chance na ViewTask. Se a fábrica tira a view do monitor nesse trecho (`0xD46ACC`/`0xD46A20`),
   mostrar como.

## O que entregar
1. `docs/tarefas/011-analise.md`, curto, com as respostas e o que não dá para saber.
2. **Uma** imagem de degrau, **B3**: a rotina do título obtém o caminho **sem chamar o `get_path` na ViewTask**, pelo caminho da pergunta 2, confere que ele
   parece um caminho (ex.: começa com `0:\` ou o formato real encontrado) e continua mostrando o cinza. Se o caminho não for válido, cinza também.
   Sem `f_open`, sem JPEG, sem heap novo. É o mais perto possível da correção final, para o resultado valer para ela.
   Mesmas regras dos degraus anteriores: receita `reload_1.0_rc7_diag_b3` a partir da imagem certa, premissas de entrada conferidas, testes em
   `tests/test_diag_trava.py`, kit por `gera_versao`, carimbo `RC7 diag B3` com `patch_versao --em 0x1A4F00`,
   `release/OpenPod-Reload-1.0-RC7-Diag-B3` com `TESTAR.txt` curto (toca? o que acontece? trocar de faixa; quadrado cinza é o esperado; volta de segurança: **RC6**).
   Se a estática não fechar um caminho seguro para o B3, **não invente**: entregue a análise e sinalize `ESCALADA-011`.

**Não** implementar a correção final nem ligar `f_open`/JPEG. Regras de sempre: nunca alterar `firmware/ORIGINAL`, gravar no aparelho, push, merge;
testes protegidos intactos; ferramenta nova ≤ 350 linhas; nada abaixo de `0xE000`, setor `0xD000` e PSMP intocados; `sh tools/ci.sh` verde.
Não usar `cd` nem caminho absoluto. Sinal final sozinho numa linha: `PRONTO-011` ou `ESCALADA-011`.
