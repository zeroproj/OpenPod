# A bateria verde — ABERTO

> Confirmado na tela em 2026-09-18, na Core 5.7: **o miolo não fica
> verde.** As demais mudanças da 5.7 estão boas.

---

## 1. O que foi tentado

| | O quê | Onde | Resultado |
|---|---|---|---|
| **5.2** | verde na criação do objeto | `0x00D22682` | sem efeito — o atualizador sobrescreve |
| **5.3** | prateado na criação | `0x00D22622` | idem |
| **5.5** | prateado em 1 dos escritores | `0x00D23686` | apareceu **dourado** |
| **5.6** | prateado em 4 escritores | 4 sítios | casca ainda branca |
| **5.7** | verde-limão nos 2 escritores de fundo | `0x00D2369A`, `0x00D236DC` | **miolo não ficou verde** |

## 2. O que está CONFIRMADO

**A pré-inversão existe.** A DIAG 8 pintou a casca com `0x07E0`: sem
inversão daria verde, com inversão dá vermelho. **Ficou vermelha.**
Primeira verificação em tela da regra do `COLOR_SOURCE.md §9`.

**Os sete escritores de cor do ícone**, achados por varredura da faixa
`0x00D23600`–`0x00D23960`:

```text
0x00D2366C  BG_COLOR    vermelho            bateria fraca
0x00D2367A  TEXT_COLOR  vermelho            bateria fraca
0x00D2368C  TEXT_COLOR  prateado            Core 5.6
0x00D2369A  BG_COLOR    verde-limão         Core 5.7
0x00D236B6  TEXT_COLOR  BRANCO              instruções sobrepostas — intocável
0x00D236CE  TEXT_COLOR  prateado            Core 5.6
0x00D236DC  BG_COLOR    verde-limão         Core 5.7
```

## 3. O que NÃO está medido

1. **Existe um oitavo escritor fora da faixa varrida?** A varredura
   cobriu `0x00D23600`–`0x00D23960`. `view_set_icon_bat` pode chamar
   outra função que pinta.
2. **O `lv_bar` tem a parte certa?** `BG_COLOR` com `r2 = 0x20000`
   (`LV_PART_INDICATOR`) pinta o indicador. Se a barra estiver com
   `bg_opa = 0` no indicador, a cor não aparece — e ninguém verificou a
   opacidade.
3. **O nível está em 100%?** Com a bateria cheia o indicador ocupa a
   largura toda; se o `set_value` não estiver sendo chamado, a barra
   pode ter largura zero e nenhuma cor apareceria.

> O item 2 é o candidato mais forte e o mais barato de testar: a
> `GUI_ANALYSIS` já registra que **um rótulo nasce com fundo
> transparente** e que ligar `bg_opa` é obrigatório — foi a armadilha da
> barra de seleção, documentada no PADRÃO de 13/09.

## 4. A próxima tentativa deve MEDIR

Cinco tentativas, cinco hipóteses. O método que funcionou hoje — e que
fechou o voltar do Extras e a pré-inversão — é **gastar uma gravação
para eliminar uma hipótese**, não para tentar um conserto.

Sugestão: pintar o indicador com `bg_opa = 255` explícito e uma cor
berrante. Se aparecer, era opacidade. Se não, o escritor está fora da
faixa varrida.

## 5. Classificação

| Afirmação | Classe |
|---|---|
| As cores são gravadas pré-invertidas | **CONFIRMADO** (DIAG 8) |
| Há sete escritores na faixa varrida | CONFIRMADO |
| Pintar na criação não basta | CONFIRMADO |
| O verde no `BG_COLOR` do indicador resolve | **REFUTADO** (Core 5.7) |
| Por que o miolo não fica verde | **NÃO RESOLVIDO** |
