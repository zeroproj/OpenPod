# Decisões

| # | Data | Decisão |
|---|---|---|
| D01 | 2026-10-21 | Adota o processo padrão v1.4 adaptado a firmware (`docs/processo-padrao.md`). Fase 0: CI local `tools/ci.sh`. |
| D02 | 2026-10-21 | RC1 aprovada no aparelho (update por SD funcionou). `patch_update_sd.py` fica como exceção aceita à regra "só fábrica"; nenhuma outra ferramenta antiga entra. |
| D03 | 2026-09-24 | Alphas 0.1/0.2 descartadas. Reload 1.0 em degraus RC1..RC4. |
| D04 | 2026-09-24 | Código-fonte nunca no repositório público; `privado-completo` só local até existir repositório privado. |
| D05 | 2026-10-21 | RC5: capa do álbum **lida de dentro do MP3** (ID3v2 `APIC`), escolha do decisor. `cover.jpg` na pasta fica como possível reserva, não como alvo. |
| D06 | 2026-10-30 | Processo atualizado para a **v1.8** do core-dev-kit (pedido do decisor: "leia e aprimore as técnicas nesse projeto"): Sol na R0 e na 1ª análise do diff, Astra na conferência final, engenheiro revisa R1/R2; veredito na 1ª linha; `AGENTS.md` com Review guidelines; `FIM-NNN` sozinho na linha; limite de 350 linhas para ferramenta nova (trava no `ci.sh`); auditoria periódica do toolchain; sessão por ficha e leitura curta; "Como retomar" em `docs/processo.md`. Sentry, Context7 e Semgrep não se aplicam. |
| D07 | 2026-10-23 | Publicação da RC6 antes do teste no aparelho, com o Flashloader 6.9.5 (Shenju) para download e links fixos `atual/update.up` (decisor: "coloca o FlashloaderSL-DEV 6.9.5 nos arquivos para download", "pode publicar"). Página genérica, sem número de versão e sem marcas de terceiros. |
| D08 | 2026-10-23 | Numeração: RC5 = textos + nomes da home; RC6 = home sem nomes, grade centralizada, moldura no selecionado; **RC7** = capa do álbum (modelo 64×64 no meio da Tocando Agora, `docs/img/rc7_tocando_modelo.png`). |
