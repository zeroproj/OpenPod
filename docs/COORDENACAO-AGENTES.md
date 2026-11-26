# Como a coordenação trabalha com os agentes (OpenPod)

Atualizado em 26/11/2026. Quem coordena: **`opencode-go/minimax-m3`**. Leia também `docs/COMO-RETOMAR.md`, o documento de entrada.

## 1. Os papéis

| Papel | Agente no opencode | Modelo | Faz |
|---|---|---|---|
| **Decisor** | — | Lucas | Decide, testa no aparelho, **grava no aparelho** e dá o **"pode"** para publicar. |
| **Coordenação** | a sessão principal | `opencode-go/minimax-m3` | Escreve as fichas, despacha, **confere byte a byte**, manda revisar, empacota, assina e publica **só com o "pode"**. **Não desenvolve as fichas ela mesma.** |
| **Desenvolvedor** | `desenvolvedor` | `opencode/deepseek-v4.1-flash-free` (grátis) | Implementa a ficha e termina com `PRONTO-NNN` ou `ESCALADA-NNN`. |
| **Desenvolvedor reserva** | `desenvolvedor-go` | `opencode-go/deepseek-v4.1-flash` (plano Go) | O mesmo, usado **quando a cota do grátis acabar**. |
| **Revisor** | `revisor` | `opencode/big-pickle` (grátis) | Só lê; escreve `NNN-revisao.md` com APROVADO / APROVADO COM RESSALVAS / REPROVADO e termina com `REVISAO-NNN`. |

Os agentes estão definidos em `.opencode/agents/` **nos dois repositórios** (`OpenPod/` e `OpenPod-instalador/`). Confira com
`opencode agent list` (aparecem `desenvolvedor`, `desenvolvedor-go`, `revisor`). As regras de cada um estão no próprio arquivo.

## 2. O ciclo de uma ficha
1. **Coordenação escreve a ficha**: OpenPod em `docs/tarefas/NNN-*.md`; Tune em `OpenPod-instalador/docs/openpod/NNN-*.md`.
   Ela tem: objetivo, o que provar, arquivos que pode mexer, critérios de aceitação, e o sinal `PRONTO-NNN` / `ESCALADA-NNN`.
   Decisões que só o decisor pode tomar ficam numa seção **"Pendente com o decisor"**: pergunte antes de despachar.
2. **Despacho**, num terminal separado (Orca), **sempre de dentro do repositório certo** (o opencode recusa caminhos fora dele):
   ```
   cd "/Users/zeroproj/Sistemas LWP/OpenPod-instalador" && opencode run --agent desenvolvedor "Faça a ficha docs/openpod/NNN-xxx.md. Leia inteira antes. Termine com PRONTO-NNN ou ESCALADA-NNN."
   ```
   Com Orca: `orca terminal create --worktree "path:<repo>" --title "OpenCode NNN" --command "<o comando acima>"`.
   Para retomar a mesma sessão: `opencode run -s <session_id> --agent desenvolvedor "continue…"`.
3. **Um agente por repositório por vez.** Nunca dois `opencode run` ao mesmo tempo (eles travam o banco de dados do opencode).
4. **Acompanhar** (o opencode **não avisa** quando para): a cada ~15 min, veja o `max(time_created)` da tabela `part` em
   `~/.local/share/opencode/opencode.db` (**só leitura**) e procure `stream error` / `quota` / `429` em
   `~/.local/share/opencode/log/opencode.log`.
5. **Conferência da coordenação** (nunca pule):
   - rode os testes (`sh tools/ci.sh` no OpenPod; `cargo test` no Tune; builds do Windows e do Linux quando mexer no Tune);
   - firmware: compile 2 vezes (sha igual), `firmware/ORIGINAL` intacto, **desmonte todo gancho** (push/pop, LR, `b.w` em função folha);
   - Tune: as regras de escrita (janela `0xE000..0x1FC000`, bootloader e tabela conferidos), a assinatura, e **o que ele apaga**;
   - escreva `NNN-conferencia.md`. Se falhou, devolva ao desenvolvedor com a lista exata.
6. **Revisão**: `opencode run --agent revisor "Revise a ficha NNN: leia a ficha, NNN-conferencia.md e o diff <base>..HEAD. Termine com REVISAO-NNN."`
   REPROVADO → volta ao passo 2 com os achados.
7. **Teste do decisor** (kit "Diag" ou pacote de teste em `_local/`), depois o **"pode"**, depois a **publicação** (receita no
   `COMO-RETOMAR.md` §5) e a **conferência online** (sha do `index.json`, downloads com HTTP 200).
8. **Feche o terminal** do Orca quando a ficha acabar (pedido do decisor). Atualize `COMO-RETOMAR.md` (§4 e §8) e `docs/decisoes.md`.

## 3. Quando a cota acaba (troca de modelo)
- Sinais: o terminal fica parado sem resposta, nenhum `part` novo no banco há mais de 15 min, ou `stream error`/`429`/`quota` no log.
- **Ordem de troca do desenvolvedor:**
  1. `desenvolvedor` (DeepSeek grátis) →
  2. `desenvolvedor-go` (DeepSeek do plano Go) →
  3. se o Go também acabar: **avise o decisor** (a reserva paga `minimax/MiniMax-M3` só com o aval dele).
- Para trocar sem perder o trabalho: **mate o processo parado**, veja `git log`/`git status` do repositório, e retome a **mesma sessão**
  com o outro agente: `opencode run -s <session_id> --agent desenvolvedor-go "Continue a ficha NNN de onde parou."`.
- O revisor (`big-pickle`) é grátis; se ele parar, espere ou avise o decisor. **Nunca** revise você mesmo a ficha que você conferiu.

## 4. Travas conhecidas do opencode (e o que dizer ao agente)
- `external_directory` / recusa de caminho: lembre "o diretório atual já é a raiz; use caminhos relativos; sem `cd` absoluto (o caminho
  tem espaço), sem `../`, sem `/tmp` (use `.tmp/`), sem `~/.cargo`".
- `git stash` é proibido (o stash é compartilhado entre árvores de trabalho).
- Se o agente "termina" sem `PRONTO-NNN`, ele não terminou: confira o que falta e retome a sessão.

## 5. O que a coordenação NUNCA faz
- gravar no aparelho; alterar `firmware/ORIGINAL/GN438_original.bin`;
- publicar sem o **"pode"** do decisor (vale para site, pacotes, StorePod e repositórios públicos);
- pôr código-fonte do OpenPod em repositório público (só a parte Rockbox/GPL, D35);
- colocar a chave `~/.openpod/chave-pacotes-ed25519.pem` em repositório, log ou teste;
- usar as linhas antigas Core/Alpha/Beta;
- textos públicos com Apple/iPod; o NanoClone128 nunca é público.

## 6. Como falar com o decisor
- Português simples, curto. Classifique o que afirmar: **CONFIRMADO / PROVÁVEL / HIPÓTESE**.
- Quando precisar dele: diga **o que** decidir, **as opções** e **a sua recomendação**.
- Registre toda decisão dele em `docs/decisoes.md` (próxima: **D50**), com a frase dele entre aspas.
