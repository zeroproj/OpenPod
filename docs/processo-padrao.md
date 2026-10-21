# Processo padrão de desenvolvimento com agentes de IA — OpenPod

> Adaptação do processo padrão v1.4 (out/2026) para um projeto de
> **firmware**. Adotado em 2026-10-21 (D01, `docs/decisoes.md`).
> Onde o padrão fala de banco, rota, npm ou preview, aqui vale o
> equivalente de firmware descrito em cada seção.

## 1. Princípios

- **Qualidade por trava, não por memória.** O que a máquina verifica vai
  para `tools/ci.sh` e bloqueia a entrega.
- **O dano é especificado, não descoberto.** Toda ficha diz quais bytes
  pode tocar; os testes reprovam qualquer byte fora disso.
- **Quem implementa não revisa.** Ficha: Claude. Implementação: MiniMax.
  Revisão: Codex.
- **Todo achado vira regra permanente**: teste de regressão + item em
  `docs/seguranca.md`.
- **O decisor aprova evidência, não código**: pacote de entrega + teste no
  aparelho.
- **Catraca.** Número de testes e versões reprodutíveis só sobem. Uma RC
  aprovada no aparelho vira teste (`sha256` reprodutível) e nunca muda.
- **Só o firmware de fábrica é fonte.** Ferramentas da linha Core e das
  Alphas não entram em receita nova (exceção registrada: `patch_update_sd.py`,
  aprovado no aparelho na RC1 — D02).

## 2. Papéis

| Papel | Quem | Faz | Não faz |
|---|---|---|---|
| Decisor | Lucas | Aprova fichas, prioridades e publicação; grava no aparelho e relata | Ler código |
| Engenheiro | Claude Opus 5.5 | Análise do ORIGINAL, ficha, testes vermelhos, despacho, pacote de entrega, kit, merge com aprovação, docs | Implementar o que vai revisar |
| Desenvolvedor | MiniMax (OpenCode) | Implementa até os testes ficarem verdes; commits no próprio branch; escreve a Entrega | Alterar testes protegidos; merge |
| Analista | Codex (gpt-6-astra / gpt-6-sol) | Revisa a ficha e o diff; relatório ≤ 15 linhas | Alterar código |
| Porteiro | `tools/ci.sh` (local) | ORIGINAL intacto, protegidos, sintaxe, testes, segredos | — |
| Orquestrador | Orca | Worktree e terminal por tarefa | Escolher modelo |

## 3. Fase atual: 0 (local)

Não há CI remoto: o repositório do código é **só local** (o remoto
`zeroproj/OpenPod` é PÚBLICO e recebe apenas kit e página). O porteiro é
`sh tools/ci.sh`, rodado pelo desenvolvedor antes do "terminei" e pelo
engenheiro antes do merge. Bloqueio de merge: **por regra**.

| Fase | Pré-requisito | Passa a valer |
|---|---|---|
| 0 | nenhum | ficha, testes vermelhos, revisão astra, `ci.sh` local, métricas |
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

| Etapa | Comum | Risco / Pesada |
|---|---|---|
| Ficha + testes vermelhos | Claude Opus 5.5 | Claude Opus 5.5 |
| Revisão da ficha | — | `gpt-6-astra`, esforço high |
| Implementação | MiniMax M3.1 Flash Preview | MiniMax M3 |
| Análise do diff | `gpt-6-sol`, medium | `gpt-6-astra`, high |
| Pacote, kit, merge | Claude Opus 5.5 | Claude Opus 5.5 |

O modelo do desenvolvedor vai no `opencode.json` **do worktree** (nunca
commitado). Codex fixado na 0.156.1.

## 6. Ciclo de uma ficha

```
1 ENGENHEIRO  análise do ORIGINAL → ficha + testes vermelhos (protegidos) no branch principal
2 ASTRA       revisa a ficha: "que dano não está coberto?"            [Risco/Pesada]
3 DECISOR     aprova a ficha
4 ORCA        worktree tarefa-NNN; engenheiro grava o modelo no opencode.json
  MINIMAX     implementa; dúvida → PERGUNTA NNN
5 MINIMAX     sh tools/ci.sh verde + Entrega na ficha → "TERMINEI NNN"
6 ENGENHEIRO  ci.sh do branch principal contra o branch da tarefa
7 CODEX       analisa o diff → achado vira teste novo → R1 (máx. R2)
8 ENGENHEIRO  merge local, gera_versao (kit cabo + .up), pacote de entrega
9 DECISOR     grava no aparelho e preenche o roteiro manual
10            aprovado → catraca (sha da RC vira teste), docs e métricas
11 ORCA       apaga worktree e branch
```

Escalada após R2: dividir a ficha, reescrever a especificação ou trocar o
modelo. Nunca uma terceira tentativa igual.

## 7. Modelo de ficha

`docs/tarefas/NNN-nome.md` — cabeçalho (Tipo, Desenvolvedor, Analista,
Depende de, Status), Objetivo, Escopo, Evidência no ORIGINAL (offset,
bytes, desmontagem), Critérios de aceite (cada um com teste), **Danos
possíveis** (o equivalente dos casos de abuso), Bytes permitidos, Arquivos
protegidos, Revisão da ficha, Entrega, Rodadas.

## 8. Travas (`tools/ci.sh`)

| Trava | Bloqueia quando |
|---|---|
| ORIGINAL | sha256 diferente de `b7cd5eb9…` |
| Protegidos | hash de `tests/PROTEGIDOS.sha256` mudou |
| Sintaxe | `py_compile` falha em `tools/` ou `tests/` |
| Testes | qualquer teste falha (inclui catraca das RCs aprovadas) |
| Segredos | gitleaks acusa (quando instalado) |
| Guardas do `build.py` | byte abaixo de `0xE000`, setor `0xD000`, PSMP, área livre não declarada |

## 9. Achados

Cada achado do Codex gera teste de regressão + linha em `docs/seguranca.md`.

## 10. Pacote de entrega

```
## Pacote — Ficha NNN / Reload 1.0 RCn
- Fase: 0
- ci.sh: <resultado>   Análise Codex (<modelo>): <n> achados → <n> corrigidos
- Imagem / .up: <sha256> · setores tocados: <lista>
- Danos cobertos: <lista em linguagem simples>
- Roteiro no aparelho (decisor preenche ✔/✘): <passos>
- Riscos aceitos: <lista>
- Rodadas: R<n>   Recomendação: aprovar | com ressalva | não aprovar
```

## 11. Métricas

`docs/metricas.md`, uma linha por ficha.

## 12. Sempre

- O ORIGINAL nunca é modificado. Nenhum agente grava no aparelho.
- Nada é publicado no repositório público sem o decisor.
- O desenvolvedor só escreve no próprio worktree.
- Do decisor: publicar, gravar no aparelho, escopo, aceitar risco.

## 15. Configuração do projeto

```yaml
projeto: OpenPod — firmware do Iigenai GN-438 (yp3_2.0.43)
fase_atual: 0
repositorio_codigo: local, branch privado-completo (sem remoto privado ainda)
repositorio_publico: zeroproj/OpenPod — SÓ kit e página
codex_versao_fixada: 0.156.1
comando_ci: sh tools/ci.sh
regras_do_projeto_no_despacho:
  - Responda em português.
  - NUNCA modifique firmware/ORIGINAL/. NUNCA grave no aparelho (smtlink_dump, write_flash).
  - NUNCA use ferramentas da linha Core/Alphas listadas em tests/test_rc2.py (PROIBIDAS).
  - NUNCA faça git push. NUNCA altere a configuração do git.
  - Ferramenta nova segue o padrão de tools/: docstring com propósito, uso, dependências, limitações; --in/--out/--dry-run; confere premissa no binário antes de escrever; recusa se não bater.
permissoes_desenvolvedor:
  escrita: [worktree da tarefa]
  trava: opencode.json → permission.external_directory = deny
```

## 16. Despacho

```sh
sed -n '/^<!-- inicio:desenvolvedor -->$/,/^<!-- fim:desenvolvedor -->$/p' docs/processo-padrao.md
sed -n '/^<!-- inicio:analista -->$/,/^<!-- fim:analista -->$/p' docs/processo-padrao.md
```

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
- fazer merge, push ou mexer em outros branches; commitar `opencode.json`;
- escrever fora dos bytes permitidos pela ficha;
- sair do escopo. Melhorias vão como sugestão na Entrega.

Dúvida: pare e escreva

    PERGUNTA NNN: <pergunta objetiva>
    Opções que vejo: A) ... B) ...
    Bloqueia: sim | não

Ao terminar: rode `sh tools/ci.sh` (tudo verde); confira
`git diff --stat` contra o branch base; preencha a seção Entrega da ficha
(o que foi feito, decisões, pendências, danos notados e não cobertos);
commit; escreva `TERMINEI NNN`.

Correções (R1/R2): você recebe testes novos. Corrija a causa; todos os
testes precisam passar. Registre a rodada na ficha.
<!-- fim:desenvolvedor -->

<!-- inicio:analista -->
## 18. Papel: Analista

Você só lê: nunca altera arquivos nem faz commit. Recebe a ficha e, no
modo DIFF, o diff.

MODO FICHA: que dano ao aparelho ou ao firmware a ficha e os testes não
cobrem? Considere: byte escrito fora do declarado; premissa não conferida
antes de escrever; bootloader, setor 0xD000, PSMP; CRC/cabeçalho do `.up`;
desvio Thumb mal codificado; ponteiro XIP errado; paleta/formato de
imagem; regressão de algo já aprovado no aparelho; código de projeto
antigo entrando escondido.

MODO DIFF: procure bugs no código alterado e confira se cada dano da ficha
está tratado no código, não só testado.

Formato (máximo 15 linhas):

    ANÁLISE NNN — MODO: FICHA | DIFF — MODELO: <modelo>
    VEREDITO: APROVADO | APROVADO COM RESSALVAS | REPROVADO
    [ALTA]  arquivo:linha — problema — consequência — correção
    [MÉDIA] ...
    [BAIXA] ...
    Teste sugerido: <o que o teste de regressão deve verificar>

ALTA: pode brickar, apagar bootloader/PSMP ou gravar imagem errada.
MÉDIA: quebra uma tela ou função. BAIXA: robustez.
Sem achados: `VEREDITO: APROVADO` e nada mais.
<!-- fim:analista -->
