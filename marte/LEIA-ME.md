# marte/ — material do Projeto Marte

**Nada aqui foi implementado.** É estudo. Marte só começa quando o
mantenedor disser; o Saturno ainda tem defeitos abertos.

A análise está em **`docs/PROJETO_MARTE.md`**. Comece por ela.

## O que tem aqui

| pasta | conteúdo |
|---|---|
| `referencia/` | os 16 bitmaps do NanoClone convertidos para PNG, só para olhar |
| `paleta/` | `nanoclone.json` — as cores extraídas dos bitmaps, com RGB565 |
| `adaptado/` | **ativos já na nossa medida** — faixa, seleção, barra de progresso e 30 quadros de ícone |
| `mockups/` | `comparacao.png`, `marte_completo.png` e `marte_tocando_agora.png` |

Os arquivos originais do tema continuam intocados em
`assets/referencia/NanoClone/`.

## Estudo COMPLETO (2026-09-14)

Tudo o que havia para estudar no Marte está em `docs/PROJETO_MARTE.md`:

| § | assunto |
|---|---|
| 1–4 | tema, licença, paleta, degradê |
| 5 | tela Tocando Agora (`.wps`) |
| 9 | a moldura (`.sbs`) — a faixa em todas as telas |
| 10 | os ícones que **já temos** (Font Awesome no firmware) |
| 11 | as fontes |

## As três coisas que você precisa saber antes de decidir

1. **A tela é outra** — 176×132 (paisagem) contra 128×160 (retrato) —
   mas **9 dos 10 bitmaps cabem**: os ícones do Rockbox são pequenos.
   Só a barra de progresso (162 px) precisou ser remontada. E o degradê
   da faixa é vertical, então adaptar 176→128 é **sem perda**.

2. **O iPod nano é tema CLARO** — texto preto em fundo branco, seleção
   azul. O OpenPod hoje é escuro. Marte inverte o tema inteiro.

3. **Por causa do Saturno, essa inversão são 12 bytes** na tabela de
   `0x001A5400`, sem uma linha de código. Veja `marte/mockups/comparacao.png`.

4. **Play, pause, anterior, próxima, aleatório e volume já existem no
   firmware** como Font Awesome (o conjunto padrão do LVGL). Esses
   ícones não precisam vir do NanoClone — e ficam fora do share-alike.

## Licença — decidido

NanoClone 5.2, de Billy Blair, sob **CC-BY-SA 3.0**. O mantenedor
autorizou usar os pixels, com crédito. Isso está registrado em
**`ATRIBUICAO.md`**, na raiz do projeto.

Consequência a não esquecer: share-alike. Os ativos derivados em
`adaptado/`, e o que os incorporar, saem sob CC BY-SA 3.0. A atribuição
também precisa aparecer na tela **Sobre** quando Marte for implementado
— isso é item de implementação, ainda não feito.
