# Teste de revisores — ficha 022 (Reload 3.1)

Decisão do decisor (2026-11-18): dois revisores grátis revisam **o mesmo estado** da 3.1 (commit `8b3adbe`), **de forma
independente**, e o melhor vira o revisor oficial. Este teste mede **auditoria**. A comparação de **desenvolvimento** (DeepSeek ×
MiniMax) é separada, na ficha 023.

| Revisor | Modelo | Worktree |
|---|---|---|
| A | `opencode/big-pickle` | `tarefa-022`; escreve `022-revisao.md` |
| B | `opencode/mimo-v2.6-flash-free` | `rev-mimo-022`; escreve `022-revisao-mimo.md`; não vê o A; só leitura |

Cada achado precisa ter: severidade, endereço, instrução (bytes e desmontagem), motivo técnico e como validar.
A coordenação verifica cada achado contra o ORIGINAL e classifica como **confirmado**, **plausível** ou **incorreto**
(alucinação ou falso positivo).

## Critérios (pesos do decisor)
| Critério | Peso |
|---|---|
| Problemas reais identificados | 40% |
| Precisão dos endereços e offsets | 25% |
| Baixa taxa de falsos positivos | 20% |
| Qualidade das provas técnicas | 15% |

Checagens específicas esperadas: bit Thumb, alinhamento, endianness, XIP × offset, chamadas indiretas.

## Resultado
(preencher depois das duas revisões)
