# Ficha 021 — Reload 3.0: o menu Apps na home

> Análise da mudança que transforma o ícone 5 da home (hoje **Imagem**)
> em **Apps**, abrindo o menu escondido de fábrica. A ficha escreve
> **0x52**; a medida diz **0x53**. A divergência está na seção 4 e é a
> decisão mais importante deste documento.

## 1. O ponto índice → página da home

A home não guarda a página de cada ícone no objeto. O `page1_process`
recebe o índice selecionado e faz um salto por tabela:

```asm
0x00D00FB8  cmp  r3, #0xB
0x00D00FBA  tbh  [pc, r3, lsl #1]     ; tabela em 0xD00FBE
```

O `tbh` é **PC-relativo e indexado por meia-palavra**:

```text
alvo = 0xD00FBE + 2 * entrada
```

A entrada 5 fica em `0xD00FC8` e vale `0x00F8`:

```text
0xD00FBE + 2 * 0x00F8 = 0xD011AE
```

O bloco de fábrica em `0xD011AE` é o da Imagem:

```asm
0xD011AE  bl   0xCFE714              ; checagem de imagem
0xD011B2  cmp  r0, #0
0xD011B4  beq  0xD01138
...
0xD011EA  movs r3, #0x15             ; página Imagem
0xD011F2  pop.w {r4-r8,lr}
0xD011F6  b.w  0xD0DAE0              ; troca de página
```

O menor patch é trocar os **10 bytes** do começo do bloco por quatro
`movs` e um salto para a cauda comum:

```text
0xD011AE  53 23   movs r3, #0x53      ; página Apps
0xD011B0  00 22   movs r2, #0
0xD011B2  02 21   movs r1, #2
0xD011B4  01 20   movs r0, #1         ; origem 1 (home)
0xD011B6  1C E0   b    0xD011F2
```

O `b` de 16 bits em `0xD011B6` tem PC `0xD011BA`; o imediato `0x1C`
(28 meias-palavras) leva a `0xD011BA + 0x38 = 0xD011F2`, exatamente o
`pop.w + b.w` de fábrica. O resto do bloco antigo (`0xD011B8..0xD011F1`)
fica morto.

### Quem mais entra nesses 10 bytes?

Varredura de branches no ORIGINAL e na 2.2.1:

- `0xD011C8 bne 0xD011D2` — dentro do próprio bloco, não entra no trecho
  trocado;
- `0xD0129E beq 0xD011BE` — cai **depois** dos 10 bytes, no bloco morto;
  continua válido e não foi tocado;
- nenhum `bx`/`blx` e nenhum literal de 32 bits aponta para
  `0xD011AE..0xD011B7`.

O TBH em si (`0xD00FBE..0xD00FC7`) e as entradas 0..4 e 6..8 não mudam.
É o que garante que os outros oito ícones continuam com o destino de
fábrica.

## 2. O texto "Aplicativos" (id 159)

O firmware de fábrica já traz o texto no **id 159** em todas as tabelas
de idioma. A medição no 2.2.1:

| Idioma | Tabela | id 159 |
|---|---|---:|
| PT | `0xC53B84` | `Aplicativos` |
| EN | `0xC52AA4` | `APP` |
| ZH | `0xC523E4` | `应用` |
| FR | `0xC52E04` | `APP` |
| DE | `0xC52744` | `APP` |
| IT | `0xC534C4` | `APP` |
| ES | `0xC53EE4` | `APP` |
| HE | `0xC53164` | texto hebraico |
| NL | `0xC53824` | `Toepassing` |

O vetor de idiomas em `0x48774` tem 10 ponteiros: o primeiro
(`0xC54244`) é o nome PT; os outros nove, em `0x48778..0x48798`, são as
tabelas acima. Todos os 10 apontam para texto com NUL, e o id 159 é um
ponteiro XIP válido em todas as nove tabelas. **Nada é realocado**: não
há tabela nova, string nova, nem literal/vetor repontado.

O rótulo do índice 5 na home é o id 4:

```text
0x000486C4  [1, 3, 5, 6, 2, 4, 9, 10, 8]   (id 5 = 4)
0x000486D8  4 -> 159
```

A tabela de ids é compartilhada pelos idiomas. Os títulos do menu
(`0xC486E8` = `[7, 4, 11]`: Despertador, Imagem, Dicionário) não mudam.

## 3. O desenho do ícone 5

A folha da home é `INDEXED_8`, 128×160, paleta em `0x0CDD5C` e pixels
em `0x0CE15C`. A 2.2 já gravou a paleta escura colorida; a 3.0 **não
refaz a paleta**. A ferramenta `fab_icones_home_apps.py`:

1. confere o sha256 da região paleta+pixels da 2.2
   (`751ca714…`);
2. confere os shas dos dois PNGs:
   `assets/IconesHome_escuro_colorido.png` (`5eff7463…`) e
   `assets/IconesHome_escuro_colorido_apps.png` (`eccc855b…`);
3. confere que os PNGs só diferem dentro da caixa do ícone 5
   (`x 93..115, y 68..90`);
4. remapeia **só** os pixels dessa caixa para a paleta existente, já
   deslocados **+8 linhas**: o `fab_home_moldura.py` move a faixa do meio
   de `y 62..97` para `y 70..105`, e é essa grade final que o binário tem.

Resultado medido: 452 bytes mudam, todos dentro da caixa final
(`x 93..115, y 76..98`); erro médio 1,54 e máximo 13 por canal contra o
PNG (limites 2,0 e 64). A paleta, o cabeçalho e os outros oito ícones
ficam byte a byte iguais aos da 2.2. O deslocamento é o que apaga o
ícone antigo; sem ele sobrava a linha verde da imagem em `y 91..94`.

O PNG novo foi gerado por `desenha_icones_home.py` com
`ESTILO=escuro_colorido GLIFO5=apps` e é **idêntico** a
`docs/previas/2026-11-17_IconesHome_apps_ref.png` (sha `eccc855b…`):
quatro quadrados arredondados 2×2, lado 7,0, vão 3,0, raio 1,8, cor
`(120,220,120)`, centrados no ícone. Sem `GLIFO5`, a saída continua com
o sha antigo (`5eff7463…`); a prévia da home está em
`docs/previas/2026-11-17_reload30_home.png`.

## 4. A página é 0x53, não 0x52 — a divergência com a ficha

A ficha 021 escreve **0x52** em quatro pontos. A medida do
`view_page_create` mostra outra coisa.

O despachante fica em `0xD23B10` e usa um `tbb` em `0xD23B34`, com
tabela em `0xD23B38`, **indexada por página − 1**:

```asm
0xD23B2C  subs r3, r5, #1
0xD23B2E  cmp  r3, #0x52
0xD23B34  tbb  [pc, r3]             ; base 0xD23B38
```

As duas entradas que importam:

```text
índice 0x51 (página 0x52) -> 0xD23CF2 -> bl 0xD3CAA8
                                          page_set_timershut_time_create
índice 0x52 (página 0x53) -> 0xD23CF8 -> bl 0xD2F0A0
                                          page_home_menu_create
```

Ou seja: **0x52 é o "Desligar sozinho"**; **0x53 é o menu Apps**. O
`docs/PLANO_EXTRAS.md` §8.3 já registra o erro da Core 3.0, que abriu a
tela errada justamente por ler o índice da tabela como número de página.

A 021 implementa **0x53** e o teste `tests/test_reload_3_0.py` prova as
duas coisas: a entrada 5 leva a `0xD2F0A0` (0x53) e a entrada 0x51 leva a
`0xD3CAA8` (0x52, desligar). Se o arquiteto exigir o texto literal da
ficha, a decisão é `ESCALADA-021`, porque 0x52 não abre o Apps.

## 5. Voltar: a moldura e a pilha de navegação

A pilha global é `0x00823D05`:

```text
+0x0C  base, entradas de 5 bytes (byte 0 = página, 1..4 = payload)
+0x57  profundidade (máximo 14)
```

Endereços medidos:

```text
0x00D0D9E8  empilha (r0 = página)
0x00D0DA64  desempilha; pilha vazia devolve 1 (home)
0x00D0E138  voltar: desempilha e abre o destino via 0xD0DAE0
0x00D0DC02  cauda compartilhada: guarda a origem e empilha
0x00D0DC1A  único chamador do empilhador
```

### Do Apps para a home

O bloco novo do índice 5 passa `r0 = 1` (origem home) e `r3 = 0x53`
(destino). A cauda `0xD0DC02` empilha a origem 1; o Esc do Apps
desempilha 1 e abre a home. A moldura do índice 5 é restaurada pelo
próprio estado da home; o roteiro de aparelho da ficha 006 ("Abrir/
voltar: moldura no ícone certo", APROVADA em 2026-10-30) cobre
exatamente esse caso. A implementação não muda a moldura nem a pilha.

### Do item do Apps para o Apps

O event callback do menu é `0xD2EF5C` (ponteiro `0xD2EF5D`, com o bit
Thumb). Ele identifica o objeto focado contra os três primeiros itens do
array e despacha:

```asm
0xD2F00A  movs r3, #4
0xD2F00E  mov  r2, r4          ; índice 0/1/2
0xD2F010  movs r0, #0x53       ; origem Apps
0xD2F012  bl   0xD23510
```

A página destino é aberta com origem 0x53; a cauda compartilhada empilha
0x53. O Esc do Despertador ou da Imagem desempilha 0x53 e volta ao Apps,
não à home. O índice selecionado é guardado em `0x00823D84`
(`strb r4, [r3]` em `0xD2F018`), então o Apps reabre no item anterior.

## 6. O presenter aceita os três índices?

Sim. O callback compara o objeto focado com os três primeiros elementos
do array (`0xD2EFF6` item 0, `0xD2EFFC` item 1, `0xD2F002` item 2); um
quarto objeto cai em "nenhum" (`0xD2F006 bne 0xD2F01A`). Os três itens
são os de fábrica:

| Item | Página | Criador/evento de destino | Observação |
|---|---:|---|---|
| Despertador | `0x1E` | `page_alarm_menu_event_cb` `0xD2724C` | menu de alarmes |
| Imagem | `0x15` | `page_pict_list_event_cb` `0xD33AF4` | lista de imagens |
| Dicionário | `0x37` | `page_dict_input_event_cb` `0xD29934` | entrada do dicionário |

A página 0x37 é a entrada do dicionário; a 0x38 é a reprodução. A
análise da ficha 020 dizia 0x36/0x37, mas a tabela do `view_page_create`
mostra 0x37/0x38 (as páginas 0x35 e 0x36 apontam para
`0xD23D08 mov.w r0,#-1`, página inválida). É o mesmo desencontro de
índice × página da seção 4.

Sem `0:/dict/`, o Dicionário abre e não encontra os arquivos; o
comportamento de erro fica registrado para a ficha dos jogos, como a
021 pede. A Imagem continua acessível pelo Apps.

## 7. A diferença contra a 2.2.1

Receita `reload_3.0` = `reload_2.2.1` + dois passos, nesta ordem:

```python
("fab_apps_home.py", [], "indice 5 abre o menu Apps (0x53)")
("fab_icones_home_apps.py",
 ["--png", "assets/IconesHome_escuro_colorido_apps.png"],
 "glifo Apps no indice 5 da folha")
```

Sem carimbo, sha256
`43aaf5d51c364e03f9934aba0348230dda4911c2e7264c34555f69554c36ec32`.
A diferença contra a 2.2.1 é de 463 bytes, só nas regiões:

| Região | Bytes | O que é |
|---|---:|---|
| `0x001011AE..0x001011B8` | 10 | o bloco do índice 5 |
| `0x000486D8..0x000486D9` | 1 | id do rótulo 5: 4 → 159 |
| `0x000CE15C..0x000D315C` | 452 | pixels do ícone 5 (já na grade final) |

Nada abaixo de `0xE000`, nada no setor `0xD000`, nada na PSMP; o
bootloader e o ORIGINAL continuam iguais. O teste confere também que os
outros oito blocos do TBH e o TBH inteiro não mudaram.

## 8. O que fica registrado

- A ficha 021 pede 0x52; a medida é 0x53. Implementado 0x53, com teste
  que prova que 0x52 é o desligar. Se o arquiteto quiser o literal,
  `ESCALADA-021`.
- O Dicionário abre a 0x37 e, sem `0:/dict/`, mostra a falha de leitura;
  isso é da ficha dos jogos.
- O rótulo usa o id 159 de fábrica; nenhuma tabela de idioma foi movida
  ou copiada. A referência do desenho é
  `docs/previas/2026-11-17_desenho_apps_ref.py` e a folha aprovada é
  `docs/previas/2026-11-17_IconesHome_apps_ref.png`.
- A prévia do Apps é uma montagem com a barra e a fonte do firmware; a
  tela real é a `page_home_menu_create` de fábrica, sem patch de layout.
