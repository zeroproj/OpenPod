# Ficha 008 — RC7 trava ao tocar (diagnóstico)

Tipo: **Risco** (a Tocando Agora do aparelho). Base: `privado-completo` com a RC7
(imagem `3af97713…`, ficha 007). Quem conduz: sessão GLM (D10/D12, a pedido do decisor:
"aqui a gente só coordena"). Desenvolvedor: `minimax/MiniMax-M3`.

## Sintoma (decisor, aparelho, 2026-11-01)
"quando eu coloco para tocar ele trava. Às vezes ele abre o player só que não toca a
música, mas também não mostra a capa." → CONFIRMADO no aparelho. O decisor volta à RC6.

Leitura: a ViewTask (ou o sistema inteiro) para **dentro do TITULO, antes do `set_src` da
capa**, e o áudio também não começa. O arnês (`tests/emu_rc7.py`) passa porque troca por
stubs exatamente o que não foi exercitado de verdade: heap, FatFs, `get_path` e LVGL.

## Hipóteses (nenhuma confirmada; classificar ao investigar)
- **H1 — trava entre tarefas (HIPÓTESE, a mais forte).** O TITULO roda na ViewTask e chama
  `get_path` `0xCFEFC4` → `0xD6D1B4`, que **pega um mutex do banco** (`[[pc+0x3c]]+0x5C` via
  `0x80DB48`, solta em `0x80DB6E`, código em RAM) e depois o FatFs (`fs+0x14`). Na fábrica
  quem chama `get_path` é a MainTask (presenter). Se a MainTask/tarefa do áudio segura esse
  mutex (ou o do FatFs, ou a trava da LVGL) e espera a ViewTask → ABBA. Conferir: quem pega
  `+0x5C`, se `0x80DB48` espera para sempre, se a MainTask manda a mensagem do título e espera
  a ViewTask (envio síncrono), e a ordem de travas da fábrica.
- **H2 — pilha da ViewTask (HIPÓTESE).** Os 392 B medidos não contam o `get_path` real
  (quadro `0x238` + `0xD6F138`…) nem o `f_open` real (LFN). Somar a profundidade real no
  ponto do `label_process`.
- **H3 — falha de CPU (HIPÓTESE).** A fábrica tem zero `udiv` em 1,75 MiB → o núcleo pode
  não ser ARMv7-M comum (ex.: v7-A/R) e checar alinhamento. Procurar acesso desalinhado e
  qualquer instrução do lote que a fábrica nunca usa.
- **H4 — interface real diferente do stub (HIPÓTESE).** Tamanho do FIL (≤ `0x25C` era
  PROVÁVEL), `f_lseek` 64 bits em `r2:r3`, formato do caminho, retorno de `get_path`.

## O que entregar
1. Análise estática (só leitura do ORIGINAL) de H1..H4 com CONFIRMADO/PROVÁVEL/HIPÓTESE.
2. **Imagens de bisseção pelo cartão**, cada uma com um degrau a mais, a partir da RC7, sem tocar
   nada fora dos bytes da RC7, cada uma com `.up` (via `gera_versao`) e carimbo próprio
   (`patch_versao --em 0x1A4F00`, "RC7 diag A" etc.):
   - **A:** TITULO só faz o `set_text` (CRIA fica: quadrado cinza);
   - **B:** A + `get_path` (sem arquivo);
   - **C:** B + `f_open`/`f_close`;
   - **D:** a RC7 inteira (já existe).
   Se a análise confirmar a causa antes, propor direto a correção (ex.: tirar `get_path`/FatFs
   da ViewTask) em vez da bisseção, e perguntar ao decisor.
3. Roteiro curto para o decisor gravar A→B→C e dizer onde trava.
4. Nada de mexer nos testes protegidos; receitas novas são de diagnóstico (não entram na
   catraca). Ferramentas novas ≤ 350 linhas. `sh tools/ci.sh` verde.
