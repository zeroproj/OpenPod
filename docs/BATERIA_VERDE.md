# A bateria verde — RESOLVIDO na Core 5.7

> **Confirmado na tela em 2026-09-18.** O miolo fica verde.
>
> Este documento passou dois dias dizendo o contrário. O relato de
> 2026-09-17 — "não apareceu verde" — estava errado, e eu o registrei
> como fato sem conferir o binário. Fica o registro do erro junto com a
> solução.

---

## 1. O que a imagem que foi gravada realmente carrega

Decodificado direto do `.up` da Beta 1 — os seis `movw` que carregam cor
em `view_set_icon_bat`:

```text
0x00D23686   movw r1, #0x7AC6    -> na tela RGB(197, 206, 213)   casca prateada
0x00D23694   movw r1, #0xB0B7    -> na tela RGB(180, 246, 131)   MIOLO VERDE
0x00D236CA   movw r1, #0x7AC6    -> na tela RGB(197, 206, 213)   casca prateada
0x00D236D6   movw r1, #0xB0B7    -> na tela RGB(180, 246, 131)   MIOLO VERDE
0x00D238E8   movw r1, #0x7AC6    -> na tela RGB(197, 206, 213)   casca prateada
0x00D23912   movw r1, #0x7AC6    -> na tela RGB(197, 206, 213)   casca prateada
```

`RGB(180, 246, 131)` é **exatamente** o miolo do Projeto Marte. Não é
aproximação: bate nos três canais.

## 2. O que fez funcionar

**Varrer por faixa de endereço, não por assinatura.** As tentativas 5.2 a
5.6 falharam porque cada varredura por assinatura achava alguns
escritores e não avisava que tinha perdido outros. A varredura de
`0x00D23600`–`0x00D23960` achou os **sete** de uma vez.

**Pré-inverter a cor.** `LV_COLOR_16_SWAP` está ligado: o valor tem que
entrar com os bytes trocados. `RGB(180,246,131)` = `0xB7B0` cru, gravado
como **`0xB0B7`**.

Isso foi provado em tela pela DIAG 8: a casca pintada com `0x07E0` — que
sem inversão daria verde — saiu **vermelha**. Primeira verificação
empírica da regra do `COLOR_SOURCE.md §9`, que estava no projeto desde
setembro deduzida de um caso só.

## 3. O caminho até aqui

| | O quê | Onde | Resultado |
|---|---|---|---|
| **5.2** | verde na criação do objeto | `0x00D22682` | sem efeito — o atualizador sobrescreve |
| **5.3** | prateado na criação | `0x00D22622` | idem |
| **5.5** | prateado em 1 dos escritores | `0x00D23686` | apareceu **dourado** |
| **5.6** | prateado em 4 escritores | 4 sítios | casca ficou prateada |
| **5.7** | verde nos 2 escritores de fundo | `0x00D23694`, `0x00D236D6` | **miolo ficou verde** ✅ |

A lição das 5.2 e 5.3: **pintar na criação do objeto não adianta.**
`view_set_icon_bat` repinta em tempo de execução, toda vez que o nível
muda. Quem manda é o atualizador, não o construtor.

## 4. O que continua fora

`0x00D236B6` — **instruções sobrepostas**. Os mesmos bytes são decodificados
a partir de dois alinhamentos e servem a dois caminhos de código.
Patchar ali quebra o outro caminho. Continua branco, de propósito.

Não é defeito visível: é um dos estados de nível, e o resultado na tela
está correto.

## 5. O M-g está encerrado

A cor está na tela e está certa. O que restava na tabela do Marte era
trocar a bateria desenhada por um **bitmap com degradê** — refinamento
cosmético sobre um item que já funciona, ao custo do crédito CC-BY-SA.

**Não fazer.** Se alguém reabrir isto, que seja por pedido explícito, não
por item de lista.

## 6. A lição de método

Eu escrevi "não ficou verde" num documento de projeto porque foi o que o
relato dizia, e não abri o binário para conferir. O binário sempre
carregou `0xB0B7`. Um relato de tela e um `movw` decodificado não são a
mesma classe de evidência — e quando discordam, **é o binário que se
confere primeiro**, não o contrário.

Mesma regra do `CLAUDE.md` §7: relato é indício, não confirmação.
