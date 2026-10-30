# Sessão da ficha com GLM 5.3 (OpenCode Go) — Fases C e D (D10, D11)

Claude fez a análise, a ficha e os testes protegidos (Fases A e B, sinal `FASEB-NNN`). A
coordenação junta a base no branch da tarefa e abre a sessão GLM no mesmo worktree. O GLM
faz o papel que era do Codex (revisor) e da sessão da ficha (coordenação); o MiniMax implementa.

```sh
git -C <wt> merge --no-edit privado-completo          # docs/processo mais recentes no branch
orca terminal create --worktree id:<repo>::<wt> --title "GLM | Tarefa NNN" \
     --command "opencode -m opencode-go/glm-5.3" --json
orca terminal list          # handle do terminal do GLM
orca terminal send --terminal <handle> --enter --wait-submit 20 --text "<pedido abaixo>"
```

Pedido (texto simples, sem crases):
```
Voce e a SESSAO DA FICHA NNN do OpenPod nas Fases C e D (coordenador e revisor; voce NAO implementa). Responda em
portugues. Leia CLAUDE.md, AGENTS.md (Review guidelines), docs/processo-padrao.md (secoes 5, 6, 8, 10, 13, 14, 16, 17,
18), docs/seguranca.md, docs/decisoes.md (D10, D11) e a ficha docs/tarefas/NNN-*.md. FASE C: revise a FICHA e os testes
como analista em MODO FICHA (secao 18): que dano nao esta coberto? Escreva o relatorio em docs/tarefas/NNN-revisao-r0.md
(primeira linha APROVADO ou REPROVADO). Achado ALTA ou MEDIA: escreva a pergunta e embaixo, sozinho numa linha,
PERGUNTA-DECISOR NNN, e pare (a ficha e os testes protegidos so mudam pelo engenheiro). FASE D: abra o desenvolvedor
num terminal proprio com orca terminal create --worktree <este worktree> --title "OC | Tarefa NNN" --command "opencode
-m opencode-go/minimax-m3"; pegue o handle em orca terminal list; escreva DESPACHO-NNN.md com a secao 17 e as regras da
secao 15; mande a mensagem em texto simples terminando em FIM-NNN sozinho numa linha; responda PERGUNTA NNN pela ficha.
Com FIM-NNN: rode sh tools/ci.sh; faca a 1a analise do diff (git diff privado-completo...HEAD, tres pontos) em MODO
DIFF; achado vira pedido de correcao ao desenvolvedor (R1, maximo R2) e voce confere so o diff da correcao; no fim, uma
conferencia final curta so do diff desde a 1a analise. Depois de 2 reprovacoes com MEDIA pare com ESCALADA-NNN. NUNCA:
alterar tests/ protegidos, tools/ci.sh, firmware/ORIGINAL; gravar no aparelho; merge; gerar kit; publicar; git push;
mexer fora deste worktree. AO FIM: secao Pacote na ficha (o que muda, sha da imagem reload_1.0_rcN, setores tocados,
vereditos, roteiro e MP3 de teste), linha em docs/metricas.md, commit no branch da tarefa e, sozinho numa linha, PRONTO-NNN
```

A coordenação vigia `PRONTO-NNN`, `ESCALADA-NNN` ou `PERGUNTA-DECISOR NNN`; depois faz o merge,
o carimbo (`--em 0x1A4F00`), o `gera_versao` e entrega o kit ao decisor; fecha com
`orca terminal close --worktree id:<repo>::<wt> --all` e `orca worktree rm --worktree id:<repo>::<wt> --force`.
