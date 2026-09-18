# Tocando Agora — a tela, o menu e os indicadores

> Levantado em 2026-09-18. Parte por desmontagem, parte **confirmada no
> aparelho** pelo mantenedor.

---

## 1. A tela

```text
página 4 (0x04)
  view        page_music_play_create    0x00D31E7C   2.306 bytes
  presenter   page4_scr_process         0x00D08A90
```

**2.306 bytes.** Para comparar, o menu de Música tem ~400. É a função de
tela mais densa que o projeto abriu até hoje.

### Geometria medida

Sete objetos posicionados, todos com `x=0` e alinhamento 2:

```text
y =   0    faixa superior
y =  22    bloco de 128×60
y =  45    barra de 128×3        a barra de progresso
y = 110    objeto
y = 152    objeto                8 px até a borda de baixo
```

---

## 2. O menu — CONFIRMADO no aparelho

**Com música tocando, o botão `M` abre o menu de ajustes** (página 5,
`page_music_set`, `0x00D3275C`). A abertura está em `0x00D08CD0`, no
tratador de teclas da página 4.

Isso **confirma** o que o `INPUT_MAP_COMPLETE.md` marcava como HIPÓTESE:
o `M` é a tecla de menu/voltar.

### Os seis itens, da tabela `0x00C48728`

| | item | id |
|---|---|---|
| 0 | Voltar ao início | 124 |
| 1 | Velocidade | 125 |
| 2 | Modo | 128 |
| 3 | Marcadores | 119 |
| 4 | Favoritar | 126 |
| 5 | Equalizador | 100 |

Cada um tem página própria: Velocidade → 8, Modo → 9, Marcadores → 10,
Equalizador → 11.

---

## 3. Os indicadores — o que cada um é

| na tela | item do menu | quando aparece |
|---|---|---|
| seta de repetir | **Modo** | quando um modo é escolhido |
| `AB` | **Marcadores** | quando há um trecho marcado |
| coração | **Favoritar** | quando a faixa é favorita — fica **vermelho** |
| `X` | **Velocidade** | quando a velocidade sai do normal |

**Eles são condicionais.** Só aparecem quando algo foi ajustado — não
são quatro ícones permanentes. Confirmado pelo mantenedor.

> ⚠️ **Correção a uma leitura anterior minha.** Eu descrevi a tela como
> tendo "quatro indicadores mudos ocupando a linha de cima" e disse que
> nada avisava que o menu existia. Estava errado nos dois pontos: os
> indicadores aparecem sob demanda, e o `M` é a tecla de menu como em
> qualquer aparelho dessa classe. O problema real é menor — ver §4.

---

## 4. O que realmente falta

O aparelho **não explica os símbolos na primeira vez**. Quem nunca abriu
o menu não tem como saber que `AB` é marcador, ou que `X` é velocidade.

Isso não se resolve com layout: resolve-se com **o menu dizendo o estado**
— "Modo: Aleatório" em vez de só uma seta — ou com o indicador aparecendo
junto de um rótulo quando muda.

---

## 5. O que o Marte pede e esta tela não tem

| | hoje | Marte |
|---|---|---|
| posição na fila | `1/152` | `3 de 52` |
| título | `Artista - Título` numa linha | três linhas: título, artista, álbum |
| tempos | dois absolutos | decorrido e **restante negativo** (`-2:31`) |
| volume | — | barra por 2 s, no lugar do progresso |

**A capa de álbum não cabe como o Marte a desenha.** O mockup é para
176×132 paisagem (ver `nanoclone.json`); esta tela é 128×160 retrato.
Capa de 50 px + texto de ~90 px = 140 px numa tela de 128. Se houver
capa, tem de ficar **acima** do texto, não ao lado.

---

## 6. Achado lateral — Bluetooth ficou de fora do padrão

2026-09-18, reportado pelo mantenedor ao testar a Beta 4: *"Bluetooth
não segue o padrão, tá tudo grande."*

Medido:

| | Bluetooth | padrão OpenPod |
|---|---|---|
| faixa superior | `tela_alt/10` = **16** ✅ | 16 |
| altura da lista | `tela_alt - tela_alt/10` = **144** ✅ | 144 |
| **altura da linha** | `tela_alt/7` = **22** ❌ | 16 |

```text
0x00D28804   movs r2, #7        160 / 7  = 22 px
             sdiv r2, r0, r2
             bl   set_size
```

O conserto é **um byte**: `07` → `0A`, dando `tela_alt/10` = 16.

### Por que escapou

O `patch_faixa_16px.py` procurou altura em **valores fixos**. O
Bluetooth calcula por divisão, não por constante — a varredura passou
por cima.

Mesmo erro da bateria verde: **varredura por assinatura sempre perde
alguém e não avisa.** Lá foram 7 escritores de cor e a varredura achou
4; aqui foram 24 sítios de altura e achou 23.

**Confirmado que é o único:** a sequência `movs r2,#7 / sdiv / set_size`
aparece **uma vez** no firmware inteiro.

Livro digital e Imagem foram conferidos pelo mantenedor na mesma sessão
e **seguem o padrão**.

---

## 7. O byte do título: `r3 = 2` REINICIA o aparelho

> Testado na Beta 9, em 2026-09-18. **Regressão introduzida por mim.**

### O que aconteceu

Troquei `movs r3, #1` por `movs r3, #2` em `0x00D08462`, apostando que
`r3` seria um seletor entre "nome do arquivo" e "tag".

**O aparelho reinicia ao entrar na tela de música.** Não mostra texto
errado: reinicia.

O mantenedor voltou para a Beta 8, que está sã.

### O que isso ensina, e não é pouco

**`r3` importa.** O byte não é inerte — mudá-lo muda o comportamento de
forma drástica. Se fosse ignorado, a tela abriria normal.

**Mas não é um seletor de fonte de texto.** Um seletor inválido daria
texto vazio ou estranho, não reinício. Reinício com watchdog é sintoma
de escrita fora de lugar ou ponteiro inválido.

### A leitura que eu deveria ter feito antes de gravar

```asm
bl    0x00CFF1A8    ; r0 = tipo da fonte
movs  r3, #1        ; <- r3
mov   r2, r5        ; buffer de 255 bytes (malloc(0xff))
mov   r1, r4
bl    0x00CFEE60
```

E dentro de `0x00CFEE60`:

```asm
mov  r5, r3         ; guarda r3
cbnz r2, ...        ; buffer nulo -> retorna 0
cmp  r3, #0
beq  ...            ; r3 == 0 -> retorna 0
tbb  [pc, r7]       ; despacha pela FONTE (r0), nao por r3
...
mov  r3, r5         ; r3 e repassado ao construtor
```

`r3` é **repassado adiante** ao construtor, não consumido ali. E o
buffer tem 255 bytes. A hipótese que sobra, e que eu não testei:

> **`r3` é um tamanho, um índice ou uma contagem** — não um modo. Com
> `1` o construtor escreve uma coisa; com `2`, escreve além do que o
> buffer ou a estrutura comportam.

### Estado

**REFUTADO.** `r3 = 2` não é o caminho. Não tentar `3`, `4` etc. sem
antes ler o que o construtor (`0x00D6DB3C` ou `0x00D6D7F0`) faz com
esse argumento — foi exatamente o passo que eu pulei.

O título continuar mostrando o nome do arquivo **continua ABERTO**.
