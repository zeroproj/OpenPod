# Processo padrão de desenvolvimento com agentes de IA — OpenPod

> Adaptação do processo padrão **v1.8** (core-dev-kit, 2026-10-30) para um
> projeto de **firmware**. Adotado em 2026-10-21 na v1.4 (D01); atualizado
> para a v1.8 em 2026-10-30 (D06, `docs/decisoes.md`). Onde o padrão fala de
> banco, rota, npm ou preview, aqui vale o equivalente de firmware de cada
> seção. Sentry, Context7 e Semgrep do kit **não se aplicam** (sem produção
> online; ferramentas em Python puro + capstone/Pillow; as travas de bytes do
> `ci.sh` fazem o papel do Semgrep).

## 1. Princípios

- **Qualidade por trava, não por memória.** O que a máquina verifica vai
  para `tools/ci.sh` e bloqueia a entrega.
- **O dano é especificado, não descoberto.** Toda ficha diz quais bytes
  pode tocar; os testes reprovam qualquer byte fora disso.
- **Quem implementa não revisa.** Ficha: Claude. Implementação: MiniMax.
  Revisão: Codex (Sol acha o problema, Astra confere no fim).
- **Todo achado vira regra permanente**: teste de regressão + item em
  `docs/seguranca.md`.
- **O decisor aprova evidência, não código**: pacote de entrega + teste no
  aparelho.
- **Catraca.** Número de testes e versões reprodutíveis só sobem. Uma RC
  rodando no aparelho vira teste (`sha256` reprodutível) e nunca muda.
- **Só o firmware de fábrica é fonte.** Ferramentas da linha Core e das
  Alphas não entram em receita nova (exceção registrada: `patch_update_sd.py`,
  aprovado no aparelho na RC1 — D02).
- **Gastar pouco contexto.** Leitura grande vai para fora da conversa
  (Codex ou subagente de resposta curta, §13); uma passada do Codex por
  etapa, nunca por rodada de correção.

## 2. Papéis

| Papel | Quem | Faz | Não faz |
|---|---|---|---|
| Decisor | Lucas | Aprova fichas, prioridades e publicação; grava no aparelho e relata | Ler código |
| Engenheiro | Claude Opus 5.5 | Análise do ORIGINAL, ficha, testes vermelhos, despacho, revisão das correções R1/R2 (só o diff da correção), pacote, kit, merge com aprovação, docs | Implementar o que vai revisar |
| Desenvolvedor | MiniMax M3 (OpenCode, no Orca) | Implementa até os testes ficarem verdes; commits no próprio branch; escreve a Entrega | Alterar testes protegidos; merge |
| Analista | Codex só leitura: **gpt-6-sol** onde é preciso achar o problema (R0 e 1ª análise do diff), **gpt-6-astra** na conferência final curta. **Sem cota:** revisor Claude independente (subagente só leitura) — exceção, avisar o decisor | Revisa a ficha e o diff; veredito na primeira linha | Alterar código |
| Porteiro | `tools/ci.sh` (local) | ORIGINAL intacto, protegidos, sintaxe, tamanho, testes, segredos | — |
| Orquestrador | Orca | Worktree e terminal por tarefa | Escolher modelo |

## 3. Fase atual: 0 (local)

Não há CI remoto: o repositório do código é **só local** (o remoto
`zeroproj/OpenPod` é PÚBLICO e recebe apenas kit e página). O porteiro é
`sh tools/ci.sh`, rodado pelo desenvolvedor antes do `FIM-NNN` e pelo
engenheiro antes do merge. Bloqueio de merge: **por regra**.

| Fase | Pré-requisito | Passa a valer |
|---|---|---|
| 0 | nenhum | ficha, testes vermelhos, R0, `ci.sh` local, métricas |
| 1 | repositório **privado** no GitHub | `ci.sh` no GitHub Actions a cada push |
| 2 | — | (não há preview; a homologação é o aparelho do decisor) |

## 4. Tipos de ficha

| Tipo | Quando |
|---|---|
| Comum | só ferramenta, doc ou análise; nenhuma imagem gravável muda |
| **Risco** | **qualquer mudança em imagem que vai para o aparelho** (risco de brick, de bootloader, de PSMP) |
| Pesada | código novo na área livre, ganchos, várias telas |

Na dúvida, Risco. Toda RC é Risco.

## 5. Mapa de modelos

> **Desde a ficha 007 (D10, D12):** Claude só faz análise do ORIGINAL, ficha e
> testes protegidos. **`opencode-go/glm-5.3`** substitui o Codex em toda
> revisão (R0, 1ª análise, correções, conferência final) e coordena as Fases
> C/D; **`opencode-go/minimax-m3`** implementa. Cada um abre com `opencode -m
> <modelo>` no próprio terminal. Pedido pronto: `docs/prompts/sessao-da-ficha-glm.md`.
> A tabela abaixo (D06) fica como histórico das fichas 001–006.

### Até a ficha 006 (D06 = v1.8/D48 do kit)

| Etapa | Comum | Risco | Pesada |
|---|---|---|---|
| Ficha + testes vermelhos | Claude Opus 5.5 | Claude Opus 5.5 | Claude Opus 5.5 |
| R0 da ficha | — | **gpt-6-sol**, medium | **gpt-6-sol**, high |
| Implementação | MiniMax M3 | MiniMax M3 | MiniMax M3 |
| 1ª análise do diff | gpt-6-astra, medium | **gpt-6-sol**, high | **gpt-6-sol**, high |
| Correções R1/R2: revisar | **engenheiro**, só o diff da correção | idem | idem |
| Conferência final | — | **gpt-6-astra**, medium, só o diff desde a 1ª análise | idem |
| Pacote, kit, merge | Claude Opus 5.5 | Claude Opus 5.5 | Claude Opus 5.5 |

- O M3.1 Flash saiu de uso (D29 do kit); o M3 faz todas as fichas.
- Uma passada do Codex por etapa. 2ª R0 que reprova só com achado pontual e
  correção mínima dada: o engenheiro aplica e confere, sem 3ª passada.
- Custo medido no kit: R0 do Sol 42–72 mil tokens do Codex; revisor Claude
  independente ~1,3 milhão (relê tudo do zero) — só sem cota do Codex.
- Esforço de raciocínio sempre explícito. Codex fixado na 0.156.1.
- O modelo do desenvolvedor vai no `opencode.json` **do worktree**, marcado
  com `git update-index --skip-worktree opencode.json`; o engenheiro confere
  antes do merge que ele (e o `DESPACHO-NNN.md`) não entrou no diff.

```sh
# R0 e 1ª análise do diff (risco/pesada)
codex exec -C <repo> -s read-only -m gpt-6-sol -c model_reasoning_effort=high -o <saida.md> "<pedido>" < /dev/null
# conferência final (só o diff desde a 1ª análise)
codex exec -C <repo> -s read-only -m gpt-6-astra -c model_reasoning_effort=medium -o <saida.md> "<pedido>" < /dev/null
```

As regras fixas de revisão ficam no `AGENTS.md` ("Review guidelines"); o
pedido ao Codex traz só a ficha, o intervalo do diff e o foco.

## 6. Ciclo de uma ficha

```
1  ENGENHEIRO   análise do ORIGINAL → ficha + testes vermelhos (protegidos) no branch principal
2  CODEX SOL    R0: "que dano não está coberto?"                       [Risco/Pesada — não pular]
3  DECISOR      aprova a ficha
4  ORCA         worktree tarefa-NNN; engenheiro grava o modelo (skip-worktree) e despacha
   MINIMAX      implementa; dúvida → PERGUNTA NNN
5  MINIMAX      sh tools/ci.sh verde + Entrega na ficha → linha sozinha "FIM-NNN"
6  ENGENHEIRO   ci.sh do branch principal contra o branch da tarefa
7  CODEX SOL    1ª análise do diff (três pontos: base...tarefa)        [Comum: Astra medium]
                ↳ achado → teste novo + linha em seguranca.md → MiniMax corrige (R1; máx. R2)
                → ENGENHEIRO revisa SÓ o diff da correção (sem Codex)
7b CODEX ASTRA  conferência final: só o diff desde a 1ª análise        [Risco/Pesada]
8  ENGENHEIRO   merge local, carimbo (--em 0x1A4F00), gera_versao (cabo + .up), pacote NA FICHA
9  DECISOR      grava no aparelho e preenche o roteiro manual
10              aprovado → catraca (sha da RC vira teste), docs, métricas
11 ORCA         apaga terminais, worktree e branch
```

**Escalada após R2 — cumprir de verdade.** Achado MÉDIO depois da R2:
pare, divida a ficha ou reescreva o desenho e faça nova R0. Nunca uma
terceira tentativa com o mesmo desenho.

## 7. Modelo de ficha

`docs/tarefas/NNN-nome.md` — cabeçalho (Tipo, Desenvolvedor, Analista,
Depende de, Status), Objetivo, Escopo, Evidência no ORIGINAL (offset,
bytes, desmontagem), Critérios de aceite (cada um com teste), **Danos
possíveis** (o equivalente dos casos de abuso), Riscos aceitos, Roteiro no
aparelho, Bytes permitidos, Arquivos protegidos, Revisão da ficha, Entrega,
Rodadas, **Pacote** (§10).

## 8. Travas (`tools/ci.sh`)

| Trava | Bloqueia quando |
|---|---|
| ORIGINAL | sha256 diferente de `b7cd5eb9…` |
| Protegidos | hash de `tests/PROTEGIDOS.sha256` mudou |
| Sintaxe | `py_compile` falha em `tools/` ou `tests/` |
| Tamanho (D06) | ferramenta **nova** em `tools/` com mais de 350 linhas (as que já passam ficam em `tests/LIMITE_EXCECOES.txt` e saem de lá quando uma ficha as quebrar) |
| Testes | qualquer teste falha (inclui catraca das RCs aprovadas) |
| Segredos | gitleaks acusa (quando instalado) |
| Guardas do `build.py` | byte abaixo de `0xE000`, setor `0xD000`, PSMP, área livre não declarada |
| Guardas do `gera_versao.py` | imagem ou `.up` tocando bootloader, `0xD000` ou PSMP; `.up` ≠ imagem pedida |

Os testes rodam num `TMPDIR` próprio, apagado no fim.

## 9. Achados

Cada achado do Codex gera teste de regressão + linha em `docs/seguranca.md`.

**Auditoria do projeto inteiro (D06):** a cada ~5 RCs ou antes de uma
publicação grande, Codex **Sol** high, só leitura, sobre `tools/build.py`,
`tools/gera_versao.py`, `tools/publica_release.py`, `tools/ci.sh` e as
`fab_*.py` da receita vigente. Relatório privado (fora do repositório
público); cada achado ALTO/MÉDIO vira ficha. Nada é corrigido dentro da
auditoria.

## 10. Pacote de entrega (na ficha)

```
## Pacote — Ficha NNN / Reload 1.0 RCn
- Fase: 0
- ci.sh: <resultado>   Codex: R0 <veredito> · diff <veredito> · final <veredito>
- Imagem / .up: <sha256> · setores tocados: <lista>
- Danos cobertos: <lista em linguagem simples>
- Roteiro no aparelho (decisor preenche ✔/✘): <passos>
- Riscos aceitos: <lista>
- Rodadas: R<n>   Recomendação: aprovar | com ressalva | não aprovar
```

## 11. Métricas

`docs/metricas.md`, uma linha por ficha. A cada 10 fichas o engenheiro
revisa o mapa de modelos com base nelas.

## 12. Sempre

- O ORIGINAL nunca é modificado. Nenhum agente grava no aparelho.
- Nada é publicado no repositório público sem o decisor; publicação só pelo
  `tools/publica_release.py` (branch órfão: só página, `atual/` e kit).
- O desenvolvedor só escreve no próprio worktree.
- Do decisor: publicar, gravar no aparelho, escopo, aceitar risco.
- Página pública: descrição neutra, sem marcas de terceiros (sem "iPod").

## 13. Contexto: sessão por ficha e leitura curta (D06)

O contexto da conversa é reprocessado a cada resposta. Por isso:

- **Sessão de coordenação** (a conversa com o decisor): fichas, decisões,
  kit e publicação. Não lê diff, código nem saída longa.
- **Sessão da ficha — padrão a partir da ficha 007:** Claude aberto no
  worktree roda o ciclo até o pacote (despacho, `ci.sh`, Codex, revisão das
  correções) e termina com `PRONTO-NNN` sozinho numa linha; `ESCALADA-NNN`
  depois de 2 reprovações com MÉDIO; `PERGUNTA-DECISOR NNN` quando só o
  decisor responde. Não faz merge, não gera kit, não publica. Pedido pronto
  e comandos: `docs/prompts/sessao-da-ficha.md`. A coordenação fecha com
  `orca terminal close --all` e `orca worktree rm`.
- **Leitura em subagente de resposta curta:** correção R1/R2 contra o
  achado → "fecha / não fecha" em até 5 linhas; saída de testes → contagem
  e só as falhas.
- **Conversa longa:** retomar pelo "Como retomar" de `docs/processo.md`.

## 14. Lições da prática (cada uma custou um incidente)

- **Vigia do "terminei"** casou com o próprio texto do despacho (falso
  positivo, ficha 002): a linha de fim é `FIM-NNN` **sozinha na linha**, e o
  vigia procura a linha inteira — ou um commit novo no branch.
- **Disco cheio** (4,3 GB de temporários dos testes, ficha 004): `ci.sh`
  usa `TMPDIR` próprio e apaga no fim.
- **Carimbo de versão** alocava sozinho e caiu em cima da rotina da RC3:
  sempre `patch_versao.py --em 0x1A4F00`.
- **Duas ferramentas exigindo o sha exato da entrada** não encadeiam (a 2ª
  nunca recebe a RC anterior, ficha 006): uma ferramenta só, ou o sha da
  saída da 1ª fixado no teste.
- **Gravar em sector 0xD000 / `.up` ≠ imagem** passavam pelo `gera_versao`
  (achados 004 e 006): a guarda agora confere setor e payload byte a byte.
- **Foto do decisor em HEIC** com extensão `.png`: converter com
  `sips -s format jpeg` e girar pelo EXIF antes de medir.
- **Endereço XIP × arquivo**: tabela em `0xC53B84` está no arquivo em
  `0x053B84` (= XIP − `0xC00000`); conferir antes de concluir "não existe".
- **Diff de revisão com três pontos** (`base...tarefa`): com dois, o que
  entrou na base depois aparece como "apagado".

## 15. Configuração do projeto

```yaml
projeto: OpenPod — firmware do Iigenai GN-438 (yp3_2.0.43)
fase_atual: 0
repositorio_codigo: local, branch privado-completo (sem remoto privado ainda)
repositorio_publico: zeroproj/OpenPod — SÓ página, atual/ e kit (publica_release.py)
codex_versao_fixada: 0.156.1
comando_ci: sh tools/ci.sh
docs:
  retomar: docs/processo.md
  decisoes: docs/decisoes.md
  seguranca: docs/seguranca.md
  tarefas: docs/tarefas/
regras_do_projeto_no_despacho:
  - Responda em português.
  - NUNCA modifique firmware/ORIGINAL/. NUNCA grave no aparelho (smtlink_dump, write_flash).
  - NUNCA use ferramentas da linha Core/Alphas listadas nos testes (PROIBIDAS).
  - NUNCA faça git push. NUNCA altere a configuração do git.
  - Ferramenta nova segue o padrão de tools/: docstring com propósito, uso, dependências, limitações; --in/--out/--dry-run; confere premissa no binário antes de escrever; recusa se não bater; até 350 linhas.
permissoes_desenvolvedor:
  escrita: [worktree da tarefa]
  trava: opencode.json → permission.external_directory = deny
```

## 16. Despacho

```sh
sed -n '/^<!-- inicio:desenvolvedor -->$/,/^<!-- fim:desenvolvedor -->$/p' docs/processo-padrao.md
sed -n '/^<!-- inicio:analista -->$/,/^<!-- fim:analista -->$/p' docs/processo-padrao.md
```

1. `orca worktree create --repo <id> --name tarefa-NNN-<nome> --base-branch privado-completo --setup skip --no-parent --json`.
2. No worktree: `opencode.json` com `minimax/MiniMax-M3` +
   `git update-index --skip-worktree opencode.json`; `DESPACHO-NNN.md` com as
   seções 17 + 15 (regras) + o que ler.
3. `orca terminal create --worktree <id>::<wt> --title "OC | Tarefa NNN" --command opencode --json`;
   **confira o handle em `orca terminal list`** antes de mandar.
4. `orca terminal send --terminal <handle> --enter --wait-submit 20 --text "<mensagem>"`:
   texto simples, sem crases; aponta `DESPACHO-NNN.md` e a ficha; termina
   com "Ao terminar escreva sozinho numa linha: FIM-NNN".
5. Vigia: commit novo no branch **ou** `PERGUNTA NNN:` **ou** a linha
   `FIM-NNN` sozinha. Rodadas no mesmo terminal.

<!-- inicio:desenvolvedor -->
## 17. Papel: Desenvolvedor

Sua missão: implementar a ficha até `sh tools/ci.sh` ficar verde. A ficha
é a especificação. Se algo não estiver nela, pergunte; não invente.

Você pode: criar e alterar ferramentas em `tools/` dentro do worktree;
criar testes seus; fazer commits no branch da tarefa.

Você NÃO pode:
- alterar, apagar ou pular arquivo marcado "NÃO ALTERAR sem o arquiteto"
  (o `ci.sh` confere o hash);
- modificar `firmware/ORIGINAL/`, gravar no aparelho ou abrir USB;
- usar ferramentas proibidas pela ficha, nem copiar código delas;
- fazer merge, push ou mexer em outros branches; commitar `opencode.json`
  ou `DESPACHO-NNN.md`;
- escrever fora dos bytes permitidos pela ficha;
- criar ferramenta com mais de 350 linhas (divida em módulos);
- sair do escopo. Melhorias vão como sugestão na Entrega.

Dúvida: pare e escreva

    PERGUNTA NNN: <pergunta objetiva>
    Opções que vejo: A) ... B) ...
    Bloqueia: sim | não

Ao terminar: rode `sh tools/ci.sh` (tudo verde); confira
`git diff --stat` contra o branch base; preencha a seção Entrega da ficha
(o que foi feito, decisões, pendências, danos notados e não cobertos);
commit; escreva sozinho numa linha `FIM-NNN`.

Correções (R1/R2): você recebe testes novos. Corrija a causa; todos os
testes precisam passar. Registre a rodada na ficha.
<!-- fim:desenvolvedor -->

<!-- inicio:analista -->
## 18. Papel: Analista

Você só lê: nunca altera arquivos nem faz commit. Recebe a ficha e, no
modo DIFF, o intervalo do diff. Siga as "Review guidelines" do `AGENTS.md`.

MODO FICHA: que dano ao aparelho ou ao firmware a ficha e os testes não
cobrem? Considere: byte escrito fora do declarado; premissa não conferida
antes de escrever; bootloader, setor 0xD000, PSMP; CRC/cabeçalho do `.up`;
desvio Thumb mal codificado; ponteiro XIP errado; paleta/formato de
imagem; regressão de algo já aprovado no aparelho; código de projeto
antigo entrando escondido.

MODO DIFF: procure bugs no código alterado e confira se cada dano da ficha
está tratado no código, não só testado.

Formato (curto; só achados justificados):

    APROVADO | REPROVADO
    ANÁLISE NNN — MODO: FICHA | DIFF | FINAL — MODELO: <modelo>
    [ALTA]  arquivo:linha — problema — consequência — correção
    [MÉDIA] ...
    [BAIXA] ...
    Teste sugerido: <o que o teste de regressão deve verificar>

A **primeira linha** é só `APROVADO` ou `REPROVADO`; ALTA ou MÉDIA reprova.
ALTA: pode brickar, apagar bootloader/PSMP ou gravar imagem errada.
MÉDIA: quebra uma tela ou função. BAIXA: robustez.
Sem achados: `APROVADO` e nada mais.
<!-- fim:analista -->
