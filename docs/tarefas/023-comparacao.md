# Comparação de desenvolvedores — ficha 023 (Reload 3.1c: controles do GN-438 e a Cobrinha)

Decisão D18. **Mesmo texto, mesma hora (11:40, 2026-11-18)**, cada modelo no seu worktree, sem ver o do outro. A coordenação
conferiu os dois resultados no ORIGINAL e no código.

| Critério | DeepSeek V4.1 Flash (grátis) | MiniMax M3.1 Flash (API direta) |
|---|---|---|
| Tempo até o sinal | **~13 min** (11:40 → 11:53) | ~28 min (11:40 → 12:08) |
| Custo | **US$ 0,00** | US$ 0,90 |
| Interrupções (limite/erro) | nenhuma | nenhuma |
| Regras (bit Thumb, sem `.data`/`.bss`, kit base ORIGINAL, reprodutível, diff só no lote + `bl`) | ✅ todas | ✅ todas |
| Controles do GN-438 (`0xA0`/`0xA2`/`0x13`/`0x14`/`0x87`/`0x89`/`0x0A`/`0x81`, sem `0x11`/`0x12`) | ✅ como aprovado | ✅ como aprovado |
| Idioma (byte `0x823D06`, via `0xD0E2B8`, provado no ORIGINAL) | ✅ | ✅ (prova mais detalhada) |
| **Cobrinha jogável** | ✅ correta: cresce, acelera, colisão, pausa e recomeço | ❌ **GRAVE:** o comprimento diminui 1 a cada passo sem comida; a cobra some em 3 passos (simulado pela coordenação) |
| Achados extras | — | ✅ **defeito real latente** no `dec_bl` do `fab_sdk_jogos.py` (`I = NOT(J)` em vez de `NOT(J XOR S)`; 16.971 `bl` para trás decodificados errado; não afetava imagens) |
| Defeitos menores | texto "/>>" sem o "<<"; mensagens mistas pt/en; comentário com "Aplicação" em vez de "Aplicativos" | mensagens mistas pt/en |
| Tamanho da análise | 158 linhas | 324 linhas (mais provas) |

## Resultado
- **Entra o trabalho do DeepSeek**, que é a Cobrinha correta, mais rápida e grátis.
- Entra também **a correção do `dec_bl` achada pelo MiniMax**, uma combinação justificada pela D18.
- O DeepSeek aplica os ajustes de texto na mesma rodada.

## Leitura
- **Para escrever código**, o DeepSeek grátis foi melhor nesta ficha: entregou o jogo certo, em metade do tempo e sem custo.
- **O MiniMax mostrou mais olho de auditor:** achou um defeito real numa ferramenta, que ninguém tinha pedido para olhar. Mas
  errou a lógica central do jogo.
- **Sugestão para a próxima comparação:** usar o MiniMax como **revisor**, que é onde ele brilhou, e não como desenvolvedor.
