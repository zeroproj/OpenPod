# Sessão da ficha (Claude no worktree da tarefa) — OpenPod

Adaptado de `core-dev-kit/prompts/sessao-da-ficha.md` (D06). A coordenação (conversa com o
decisor) abre e entrega a ficha; a sessão roda o ciclo até o pacote e para. Ver processo §13.

```sh
orca worktree create --repo id:da7285e1-1206-4860-a117-a0bd595b71da --name tarefa-NNN-<nome> \
     --base-branch privado-completo --setup skip --no-parent --json
orca terminal create --worktree id:<repo>::<wt> --title "CL | Tarefa NNN" \
     --command "claude --permission-mode bypassPermissions" --json
orca terminal list          # pegue o handle do terminal do Claude
orca terminal send --terminal <handle> --enter --wait-submit 20 --text "<pedido abaixo>"
```

Pedido (texto simples, sem crases):
```
Voce e a SESSAO DA FICHA NNN do OpenPod (papel: engenheiro, so desta ficha). Responda em portugues. Leia CLAUDE.md,
AGENTS.md, docs/processo-padrao.md (secoes 5, 6, 13, 14 e 16), docs/seguranca.md e a ficha docs/tarefas/NNN-*.md.
ESTADO: <o que ja foi feito: R0, testes vermelhos, handle do desenvolvedor se houver>. SEU TRABALHO: gravar o
opencode.json (MiniMax M3, skip-worktree) e o DESPACHO-NNN.md, abrir o terminal OpenCode e despachar o desenvolvedor;
acompanhar ate FIM-NNN ou PERGUNTA NNN (responda o que a ficha decide; o resto escreva PERGUNTA-DECISOR NNN sozinho
numa linha e pare); rodar sh tools/ci.sh no branch; 1a analise do diff pelo Codex Sol high (diff com tres pontos
privado-completo...HEAD); achado vira teste novo protegido + linha em docs/seguranca.md; correcoes pelo desenvolvedor,
revisadas por voce numa tarefa separada de saida curta; conferencia final pelo Astra medium so no diff desde a 1a
analise. Depois de 2 reprovacoes com MEDIO, escreva ESCALADA-NNN sozinho numa linha e pare. NUNCA: firmware/ORIGINAL,
gravar no aparelho, merge em privado-completo, gerar kit, publicar, push, imprimir segredos. Ao fim: secao Pacote na
ficha (o que muda, sha da imagem da receita, setores, revisoes e vereditos, custo do Codex), commit no branch da
tarefa e escreva sozinho numa linha: PRONTO-NNN
```

A coordenação vigia o terminal até `PRONTO-NNN`, `ESCALADA-NNN` ou `PERGUNTA-DECISOR NNN`;
depois faz o merge, o carimbo (`--em 0x1A4F00`), o `gera_versao`, entrega o kit ao decisor e
fecha: `orca terminal close --worktree id:<repo>::<wt> --all`,
`orca worktree rm --worktree id:<repo>::<wt> --force`.

**Limite de uso:** a sessão da ficha e a coordenação gastam do mesmo plano do Claude. Bateu o
limite → a sessão para; reenvie quando o limite voltar. A coordenação não trabalha pesado
enquanto a ficha roda.
