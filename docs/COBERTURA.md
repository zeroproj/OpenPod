# COBERTURA — o que sabemos do firmware, medido

Escrito em 2026-09-14, respondendo *"de 0 a 100%, o que se sabe do
firmware?"*. Todos os números vêm de varredura, não de impressão.

---

## 1. O mapa físico — este está fechado

| região | offset | tamanho | % |
|---|---|---|---|
| bootloader | `0x000000` | 53.248 | 2,5% |
| tabela de partições | `0x00D000` | 64 | 0,0% |
| *lacuna* | `0x00D040` | 4.032 | 0,2% |
| **FIRM** | `0x00E000` | 1.647.984 | **78,6%** |
| *lacuna* | `0x1A0570` | 2.704 | 0,1% |
| TONE | `0x1A1000` | 8.248 | 0,4% |
| **ÁREA LIVRE** | `0x1A3038` | 364.488 | **17,4%** |
| PSMP | `0x1FC000` | 16.384 | 0,8% |

Confirmado por classificação de conteúdo: os blocos `0x1B0000` a
`0x1F0000` são **100% `0xFF`** — realmente vazios. É onde moram todas as
nossas rotinas.

**Estrutura: ~100%.** Sabemos particionar, reconstruir, calcular o CRC,
gerar `.up` e gravar com segurança. Isso não é pouco — foi o que custou
um aparelho para aprender.

---

## 2. Onde o conhecimento está concentrado

582 endereços distintos citados em `docs/` e `tools/`. Distribuição por
bloco de 64 KiB:

```
0x100000  ####################################### 100
0x120000  ####################################### 202
0x140000  ######################  44
0x1A0000  ########################  48   <- nossa area livre
0x0F0000  #########################  50
0x050000  ###########  23
0x000000  ##########  21
```

**317 dos 582 (54%) estão em `0x100000`–`0x140000`** — a camada de GUI.
É onde vivem as 83 páginas, os criadores de faixa/contêiner/linha, o
despachante de estilo e a tabela do Saturno.

**Nove blocos de 64 KiB não têm um único endereço documentado.** Cinco
deles são a área livre (vazios). Sobram quatro de código real que nunca
tocamos: `0x060000`, `0x070000`, `0x090000`, `0x110000`, `0x180000`.

---

## 3. Os subsistemas — pelo nome que o próprio firmware carrega

Contagem de nomes de função nas strings de depuração:

| subsistema | nomes | o que sabemos |
|---|---|---|
| **GUI (telas)** | 367 | **bem** — 83 páginas mapeadas, despacho, navegação |
| **GUI (processos)** | 121 | **bem** — `pstr_*`, tratadores de tecla |
| Bluetooth | 79 | `hci`, `host`, `sdp`, `a2dp`, `channel`, `sta` — **nada** |
| Áudio | 47 | `audio`, `volume`, `media` — **nada** |
| LVGL | 47 | **bem** — v8, estilos, fontes, objetos |
| Armazenamento | 31 | `block`, `disk` — **nada** |
| Relógio/alarme | 30 | `watch` — só a tela |
| Drivers | 16 | `dev`, `pwm`, `kadc` — **nada** |
| Energia | 8 | `pmu` — **nada** |
| Vídeo | 4 | `avi` — **nada** |
| não classificados | 615 | inclui `tlsf` (heap), `indev`, `timer` |

---

## 4. A resposta honesta, em três números

| dimensão | cobertura |
|---|---|
| **estrutura do arquivo** (partições, CRC, `.up`, gravação) | **~100%** |
| **camada de interface** (o que o OpenPod mexe) | **alta** |
| **firmware inteiro** (áudio, BT, rádio, vídeo, USB, FS) | **~15–20%** |

E é assim de propósito. O `CLAUDE.md` diz: *"não jogar fora o firmware
YP3 e criar outro, e sim entendê-lo e transformá-lo progressivamente"*.
Para redesenhar a interface não é preciso entender o codec de MP3 — e não
entendemos mesmo.

O risco de não saber aparece quando encostamos em algo dessas áreas. Já
aconteceu duas vezes: o cartão SD no `patch_titulos` e o despacho de
página no Extras.

---

## 5. O que a 2.2 exercita, e por isso importa testar

| defeito corrigido | camada | confiança antes do teste |
|---|---|---|
| Extras (guarda `[0x0a]`) | **despacho de página** | análise estática só |
| altura de linha (S11) | GUI/estilo | **não verificável sem tela** |
| fundo da 0x18 (S12) | GUI/estilo | alta |

O S11 é o que mais me preocupa: mudei 38 pontos em 28 telas e **nenhuma
ferramenta estática diz se ficou bonito**.
