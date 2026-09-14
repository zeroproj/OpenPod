# OpenPod Core 1.4 — a linha 1.1→1.4, seis bytes rumo ao Marte

```
Base       OpenPod Core 1.0.1 (STABLE)
Receita    tools/build.py --receita core1.0      10 passos
Gerada     2026-09-14
Status     ✅ CONFIRMADA NO APARELHO
Kit        firmware/RELEASE/OpenPod Core 1.4/
Diff       6 bytes contra a 1.0.1
```

Quatro itens do alvo do Marte, um por versão, **cada um testado na tela
antes do seguinte**.

---

## 1. A linha, e o que cada byte comprou

| versão | item | custo | onde |
|---|---|---|---|
| **1.1** | **M-a** sem separador entre itens | 1 byte | `0x0012179E` dentro de `CRIA_LINHA` |
| **1.2** | **M-f** seleção no azul do Marte | 2 bytes | `0x000DF082`, paleta[5] da LVGL |
| **1.3** | **M-d** sem barra de rolagem | 1 byte | `0x0014967E`, o portão do `DRAW_POST` |
| **1.4** | **M-e** sem ícone decorativo | 2 bytes | `0x000D3261` e `0x0005D622` |

**Seis bytes.** Nenhum deles aloca, nenhum usa a área livre, nenhum cria
objeto. E nenhum é pré-requisito de outro — qualquer um pode sair da
receita sem quebrar os demais.

> Isso é resposta direta ao que afundou a linha 2.x, onde
> `patch_chrome_padrao` era pré-requisito declarado de doze passos.

## 2. O que a 1.4 faz, e o que ela deliberadamente NÃO faz

```
U+F0C9  "tres tracinhos"   21 telas   DECORACAO   sai
U+F013  engrenagem          2 telas   DECORACAO   sai
------------------------------------------------- 23 telas
U+F00C  tique / check      10 telas   FUNCIONAL   FICA
U+F028  volume              2 telas   FUNCIONAL   FICA
U+F294  bluetooth           1 tela    FUNCIONAL   FICA
U+F095  telefone            1 tela    FUNCIONAL   FICA
```

**O tique fica, e não é negociável.** Em Idioma, ele é o que diz qual
idioma está ativo. A ferramenta **recusa rodar** se algum dos quatro
glifos funcionais não estiver intacto.

## 3. ✅ Confirmado no aparelho — 2026-09-14

Mantenedor: *"Deu tudo certo os três pontos estão corretos"*.

```
engrenagens e tracinhos sumiram              OK
o texto ENCOSTOU NA ESQUERDA, sem buraco     OK
o tique continua marcando o idioma ativo     OK
```

### A dúvida em aberto, fechada: a linha usa FLEX

Eu havia declarado no kit que não sabia prever se o texto encostaria na
esquerda ou se ficaria um buraco. **Encostou.** O rótulo do ícone, com
texto vazio, colapsa e os irmãos se reorganizam sozinhos.

> **Conhecimento reaproveitável, e vale além deste item:** filhos de uma
> linha da carcaça se reorganizam sozinhos. Qualquer trabalho futuro que
> remova ou acrescente um filho **não precisa mexer em coordenada** — o
> que barateia a conversão da home.

## 4. Validação

```
build.py --receita core1.0
  imagem  45780be578edb173ba9150bcc832f3107c8e3c2583590f241233530acd998617
  validate_firmware   21 OK + a falha de CRC da R1, a esperada

diff contra a Core 1.0.1
  6 bytes, em 5 setores: 0x05D000 0x0D3000 0x0DF000 0x121000 0x149000
  OK  nada abaixo de 0x00D000   OK  0x00D000 intocado   OK  PSMP intocada

pacote  OpenPod_Core_1.4.up   CRC 0xE7CC
        f907322a7c38467610a1f1e33f4a146f791f2f68a52c30cc3b40049670985613
```

## 5. O que esta linha ensinou sobre o método

**Três vezes eu declarei que um item exigia gancho na área livre ou
engenharia reversa profunda. Nas três havia caminho de 1–2 bytes.**

| item | minha estimativa | custo real |
|---|---|---|
| M-f | "origem não localizada, RE do tema da LVGL" | 2 bytes numa tabela |
| M-d | "precisa de gancho na área livre" | 1 byte num comparador |
| M-e | "sem portão — 37 pontos ou gancho" | 2 bytes em duas strings |

O erro não foi de medição: foi de **parada**. Tratei o fim da minha
busca como o fim do que existe.

**A regra que fica:** antes de dizer que um item exige infraestrutura,
procurar o **portão** — o ponto único e compartilhado onde a coisa é
decidida. Este firmware tem portão para quase tudo.

**E o corolário, que veio do M-e:** o binário diz *quantos* e *onde*.
Ele não diz o que é **decoração** e o que é **informação**. Essa é
pergunta de produto, e quem responde é quem olha a tela.

## 6. Onde estamos no alvo

```
M-a  separador        FEITO
M-f  selecao (cor)    FEITO      falta o degrade, que e o M-h
M-d  rolagem          FEITO
M-e  icone de linha   FEITO
-----------------------------
M-b  A HOME           o marco — grade 3x3, deveria ser lista
M-c  titulo na faixa
M-h  degrade da faixa e da selecao
M-g  bateria colorida
M-j  luminancia       DESVIO ACEITO, nao fazer
```

**As 39 telas de lista estão perto do alvo. A home não mudou nada** — ela
não usa a carcaça, e é a próxima frente. O terreno está preparado:
molde do Configurar decodificado (`CARCACA_PADRAO.md` §3), estrutura
mapeada com 8 bytes de folga no fim (§4.3), e agora também a confirmação
de que a linha faz layout sozinha.
