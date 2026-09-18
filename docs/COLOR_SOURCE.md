# OpenPod — De onde vêm as cores da interface

> Investigação estática de 2026-09-12, feita para decidir se o OpenPod
> pode inverter para fundo claro (Design System §8). **Nenhuma operação
> no hardware.**

---

## 1. A resposta

> ~~**Não existe tema central.**~~ **CORRIGIDO na §10** — existe um tema
> central mínimo, de duas funções. O que segue descreve a camada que fica
> **por cima** dele: cores definidas inline, por ponto de chamada.

São **~155 pontos de chamada** identificados:

| Setter | Endereço | prop | Chamadores |
|---|---|---|---|
| `lv_obj_set_style_bg_color` | `0x00D4D092` | `0x20` | **79** |
| `..._text_color` (provável) | `0x00D4D10A` | `0x457` | **56** |
| `..._border_color` | `0x00D4D0C8` | `0x30` | **20** |

---

## 2. Como foi determinado

**Passo 1 — `lv_style_set_prop` localizada em `0x00D58D38`.**
A função referencia o próprio nome (`__func__` em `0x0CDF681`, usado no
assert do `lv_style.c` linha `0x8e`). Assinatura confere:
`r0`=style, `r1`=prop, `r2`=value.

**Passo 2 — apenas 3 chamadores diretos.** A máquina de estilos é
centralizada em `0x00D4C000`–`0x00D4D200`.

**Passo 3 — 54 pontos de entrada mapeados** nessa região: são os setters
gerados da LVGL, cada um com um `prop` fixo, fazendo *tail call* para
`0x00D4CAC4`.

**Passo 4 — os setters de COR se distinguem pelo `bfi`:**

```asm
0x00D4D092  push   {r0, r1, r2, r4}
0x00D4D098  bfi    r4, r3, #0x10, #0x10
0x00D4D09C  bfi    r4, r1, #0, #0x10     ; <- empacota 16 bits
0x00D4D0A4  movs   r1, #0x20             ; <- LV_STYLE_BG_COLOR
0x00D4D0B0  b.w    #0xd4cac4
```

Os setters de valor escalar passam `r1` direto (`mov r2, r1`); os de cor
empacotam um valor de **16 bits** — que é o tamanho de `lv_color_t` em
RGB565. É essa a assinatura que os identifica.

**Passo 5 — os valores foram extraídos** de cada chamador, resolvendo
tanto imediatos (`movw`) quanto *literal pools* (`ldr r1, [pc, #n]`).

> **Nota de método:** o disassembly linear achou **zero** chamadores — o
> quarto falso negativo deste tipo no projeto. Os *literal pools*
> dessincronizam o decodificador. A varredura por **padrão de bits** dos
> `BL` achou os 155. Já é regra: neste firmware, contagem de chamadas se
> faz por padrão de bits, nunca por varredura linear.

---

## 3. O que isso significa para o projeto

### Não é camada 3 nem camada 6

| Hipótese anterior | Veredito |
|---|---|
| Tabela de estilos em dados → barato | ❌ **falso** |
| Imediato Thumb-2 dentro de `page_*_create` → caro | ❌ também falso |
| **Constante de 16 bits no ponto de chamada** | ✅ **é isto** |

Mudar uma cor é **trocar uma constante de 16 bits** — em *literal pool*
ou imediato `movw`. Não exige escrever código ARM novo. O ferramental que
já temos (arquivo por setor, CRC recalculado, verificação byte a byte)
cobre isso sem nenhuma adaptação.

### A consequência boa

**Dá para mudar uma tela sem tocar em nenhuma outra.** Como não há tema
compartilhado, não existe efeito colateral entre telas — o oposto do que
aconteceu com a paleta dos ícones, onde índices compartilhados impediram
consertar o "Image" sozinho.

Isso casa com a filosofia incremental do projeto: uma tela por vez,
verificável, reversível.

### A consequência ruim

**Inverter o sistema inteiro para fundo claro são ~155 patches
individuais**, não uma mudança. E cada um precisa ser atribuído
corretamente à tela certa — errar a atribuição significa mudar a cor
errada em algum lugar que só aparece em uso.

---

## 4. Atribuição às telas — PARCIAL

Atribuir cada chamada à sua `page_*` foi feito por proximidade ao
literal `__func__` mais próximo. Funciona, mas é grosseiro: **47 dos 79**
chamadores de `bg_color` não foram atribuídos com confiança.

Atribuições com confiança razoável:

| Tela | Chamadas | Cores |
|---|---|---|
| `page_top_layer_event_reply` | 4 | `#000080`, branco |
| `page_sys_layer_event_reply` | 3 | `#001CC0`, `#C8E8E8`, branco |
| `page_bt_menu_btn_process` | 3 | tons escuros |
| `page_ebook_read_event_cb` | 3 | `#001CF8` |
| `page_alarm_time_create` | 2 | `#000040` |

**Branco (`0xFFFF`) é o valor mais comum** — 17 de 79 em fundo, 13 de 56
em texto.

**Para atribuir com precisão** é preciso detectar fronteiras de função de
verdade (prólogo/epílogo), não proximidade de literal. É trabalho
adicional, estático, sem risco.

---

## 5. Classificação

| Afirmação | Classe |
|---|---|
| Não há tema central; cor é inline por ponto de chamada | **CONFIRMADO** |
| `lv_style_set_prop` em `0x00D58D38` | **CONFIRMADO** |
| Setter de `bg_color` em `0x00D4D092`, prop `0x20` | **CONFIRMADO** |
| Setters de cor se distinguem pelo `bfi` de 16 bits | **CONFIRMADO** |
| `0x00D4D10A` é `text_color` | **PROVÁVEL** (prop `0x457`, não conferido contra o enum) |
| Mudar uma cor = trocar constante de 16 bits | **CONFIRMADO** |
| Qual chamada pertence a qual tela | **PARCIAL** — 47 de 79 não atribuídos |
| Inversão global para tema claro é viável | **PROVÁVEL, mas laboriosa** — ~155 patches |

---

## 6. Recomendação

**Não tentar a inversão global.** O custo é ~155 patches atribuídos
corretamente, e o modo de falhar é silencioso: uma cor errada numa tela
que só aparece em uso.

**Fazer uma tela por vez**, começando pela mais usada (Configurações),
depois de melhorar a atribuição. Cada tela vira um patch pequeno,
verificável e reversível — exatamente o formato que já provamos três
vezes.

---

## 7. ⚠️ Correção — duas leituras da §4 estavam erradas

A extração automática de valores usava "último `ldr`/`mov` em `r1` antes
da chamada". Isso produziu **dois falsos positivos** que ficaram
registrados na §4 e estão corrigidos aqui:

| Reportado | Real |
|---|---|
| `page_home_create` bg = `0xE951` rosa | **preto** — `movs r2,#0; mov r1,r2` |
| `page_home_event_cb` texto = `0x4399` azul | não é cor — `0x00CD4399` é ponteiro para **string** |

A heurística capturava `ldr r1, [pc, ...]` de instruções anteriores sem
relação e mascarava para 16 bits. **A contagem por ponto de chamada
(§1) continua válida**; os *valores* extraídos em massa na §4, não.

> **Regra:** valor de cor só é confiável lido no disassembly do ponto de
> chamada. Extração em massa serve para **contar e localizar**, nunca
> para afirmar a cor.

---

## 8. A tela principal, mapeada com precisão

Feita a detecção de fronteiras de função de verdade (todo alvo de `BL` é
um início de função; nome pelo `__func__` no corpo), a home saiu completa.

**Duas fontes de cor, ambas por chamada de função:**

| Fonte | Retorna | Uso | Chamadas |
|---|---|---|---|
| `0x00D2E948` | `-1` → `0xFFFF` **branco** | rótulos **não** selecionados | 5 |
| `0x00D57B48` = `lv_palette_main(12)` | **`LV_PALETTE_YELLOW`** | rótulo **selecionado** | 2 |

`LV_PALETTE_YELLOW` é exatamente `12` no enum da LVGL v8. O padrão do
código é idêntico nos dois casos:

```asm
bl   #0xd2e948     ; ou  movs r0,#0xc / bl #0xd57b48
movs r2, #0        ; selector
mov  r1, r0        ; r1 = cor retornada
bl   #0xd4d10a     ; set_style_text_color
```

### O helper de branco é EXCLUSIVO da home — CONFIRMADO

`0x00D2E948` tem **5 chamadores, todos** em `page_home_event_cb` (4) e
`page_home_create` (1). **Patchá-lo não afeta nenhuma outra tela.**

`lv_palette_main` (`0x00D57B48`), ao contrário, tem **47 chamadores** em
todo o firmware — mas o que varia é o índice, e os 2 sites da home são
identificáveis individualmente.

Índices em uso no firmware: `GREY` 11×, `BLUE` 11×, `GREEN` 10×,
`YELLOW` 4×, `RED` 3×, `BLUE_GREY` 2×, `ORANGE` 2×, `CYAN` 1×, `AMBER` 1×.

### O patch cabe — CONFIRMADO

```text
0x12E948:  4f f0 ff 30   mov.w r0, #-1   → movw r0, #cor   (4 bytes, encaixe exato)
0x12EB3E:  0c 20         movs  r0, #12   → movs r0, #n     (1 byte)
0x12EDAE:  0c 20         movs  r0, #12   → movs r0, #n     (1 byte)
```

`movw r0, #imm16` (T3) ocupa os mesmos 4 bytes de `mov.w r0, #-1` (T2) —
substituição direta, sem deslocar nada.

**Os três endereços caem no mesmo setor de `0x12E000`.** Com o setor do
CRC (`0x0D000`), um patch de cor da tela principal são **2 setores,
8 KiB** — o menor patch do projeto até agora.

### Por que isso importa

O `bg_color` da home é preto, mas **não é ele que se vê**: a folha de
ícones é 128×160, do tamanho exato da tela, e **cobre o fundo inteiro**.
Foi por isso que o V002 e o V003 mudaram a cara do menu mexendo só na
paleta da imagem.

Ou seja, a tela principal tem **duas alavancas independentes**:

| Alavanca | O que controla | Custo |
|---|---|---|
| Paleta da folha (`0x0CDD5C`) | fundo e os 9 ícones | 3–4 setores |
| Constantes em `0x12E000` | cor dos rótulos e da seleção | 2 setores |

Juntas, cobrem **tudo que se vê** no menu principal.

---

## 9. ⚠️ REGRA — o display usa RGB565 com bytes trocados (`LV_COLOR_16_SWAP`)

**CONFIRMADO em hardware em 2026-09-12**, por experimento controlado
(V004 → V005).

> **Toda constante de cor escrita à mão no firmware precisa ser
> PRÉ-INVERTIDA.** Para obter a cor `0xRRGG` em RGB565 padrão,
> grave `0xGGRR`.

### Como foi provado

**V004** gravou `movw r0, #0xA514` — cinza neutro em RGB565 padrão
(R=20/31, G=40/63, B=20/31, proporcionalmente iguais).
**Na tela saiu VERDE.**

A troca de bytes explica exatamente:

```text
escrito     0xA514   R=0.65  G=0.63  B=0.65   neutro
display lê  0x14A5   R=0.06  G=0.59  B=0.16   VERDE ESCURO
```

**V005** gravou `movw r0, #0x14A5` — o mesmo valor pré-invertido.
**Na tela saiu CINZA NEUTRO.** Previsão confirmada.

### Confirmação cruzada — o swap está DENTRO da LVGL

As cores vindas de `lv_palette_main()` **não** precisam de inversão, e
isso é verificável pelo que **não** aconteceu:

| Cor | Se o swap fosse depois da LVGL | Observado |
|---|---|---|
| `LV_PALETTE_CYAN` `#00BCD4` → `0x05DA` | swap → `0xDA05` = **vermelho** | **azul-ciano** ✅ |
| `LV_PALETTE_YELLOW` `#FFEB3B` → `0xFF47` | swap → `0x47FF` = **ciano-verde** | **amarelo** ✅ |

Nenhuma das duas virou o que viraria se o swap fosse externo. Logo o
swap está na configuração da LVGL (`LV_COLOR_16_SWAP=1`) e ela já
entrega o formato certo.

**Consequência prática:**

| Origem da cor | Precisa pré-inverter? |
|---|---|
| `lv_palette_main(n)` | **não** — a LVGL cuida |
| Constante crua (`movw`, literal pool) | **SIM** |
| Paleta de imagem `INDEXED_8` (BGRA) | **não** — formato próprio, já validado no V002/V003 |

### Por que isso quase passou despercebido

O branco (`0xFFFF`) e o preto (`0x0000`) são **simétricos**: a troca de
bytes não os altera. Como o firmware original usa quase só esses dois
para texto, o defeito só apareceu quando escrevemos a primeira cor
intermediária.

> **Lição:** um bug que só se manifesta fora dos valores triviais pode
> ficar invisível por muito tempo. O primeiro valor não-trivial que se
> escreve num sistema é um teste de calibragem, e vale tratá-lo como tal.

---

## 10. ✅ CORREÇÃO — existe, sim, um tema central

**Descoberto em 2026-09-12, depois da §1.** Eu havia concluído que não
havia tema central. **Estava errado** — eu não tinha descido fundo o
bastante na cadeia de chamadas.

O caminho: `page_set_menu_create` tem **uma única** chamada de cor (fundo
preto). A aparência da lista vem de helpers do aplicativo, e estes
consultam **duas funções getter**:

```asm
0x00D21384:  mov.w r0, #-1   ; bx lr   ->  0xFFFF = BRANCO   (TEXTO)
0x00D2138A:  mov.w r0, #0    ; bx lr   ->  0x0000 = PRETO    (FUNDO)
```

| Getter | Devolve | Chamadores diretos |
|---|---|---|
| `0x00D21384` | texto branco | **17** |
| `0x00D2138A` | fundo preto | **7** |

Consumidos pelos helpers de UI do aplicativo — `0x00D216F0` (52
chamadores) e `0x00D21764` (39) — que por sua vez são usados por **51
funções intermediárias**.

**São 6 bytes cada, e `mov.w r0, #imm` (T2) tem exatamente o tamanho de
`movw r0, #imm16` (T3).** Substituição direta.

### Alcance — medido no aparelho, não na análise

A análise estática **não** conseguiu listar as telas afetadas: a cadeia é
mais profunda que dois níveis e só 91 das 3.365 funções têm nome
recuperável. Ficou **NÃO DETERMINADO** por esse caminho.

**Foi resolvido empiricamente pelo V006**, que trocou o getter de texto
de branco para cinza e usou o próprio aparelho como oráculo:

| Tela | Texto após o V006 | Conclusão |
|---|---|---|
| **Configurações** | **cinza** | ✅ usa o tema central |
| Menu principal (rótulos) | cinza | já vinha do patch V005 |

> **Lição de método:** com um pipeline de gravação provado, verificado e
> reversível, **o hardware responde mais rápido que a análise estática**.
> Gastar horas rastreando a cadeia de chamadas era mais caro que um patch
> de 6 bytes que mostra a resposta na tela.

### O que isso destrava

O getter de **fundo** (`0x00D2138A`, preto) continua intocado. Trocá-lo
por um tom claro é a alavanca única para o tema claro do nano 2G —
**4 bytes**, não os ~155 patches que a §3 estimava.

Risco conhecido: telas que definam texto claro **por conta própria**
ficariam ilegíveis sobre fundo claro. O mapa de alcance precisa ser
completado antes.


---

# A pré-inversão, CONFIRMADA NA TELA (2026-09-18)

A regra deste documento estava no projeto desde setembro **deduzida de
um único caso**: a bateria fraca usa `0x00F8`, que pré-invertido dá
`0xF800` = vermelho puro.

Nunca tinha sido verificada na tela.

## O teste — DIAG 8

A casca da bateria foi pintada com `0x07E0`, que é inequívoco dos dois
lados:

```text
lido direto      RGB(  0,255,  0)   VERDE puro
pré-invertido    RGB(230,  0, 57)   VERMELHO
```

**Resultado no aparelho: a casca ficou VERMELHA.**

## O que isso fecha

A pré-inversão **existe**, e portanto toda cor que o projeto escreveu
está correta na convenção: a seleção azul da Core 1.2, a faixa cinza da
2.4, o verde da barra, o prateado da casca.

| Afirmação | Classe |
|---|---|
| As cores são gravadas pré-invertidas | **CONFIRMADO** (visto na tela, DIAG 8) |

> Antes disso, a regra era PROVÁVEL apoiada num caso. Custou uma
> gravação para virar CONFIRMADO — e ela valia, porque a regra sustenta
> todas as cores do projeto.
