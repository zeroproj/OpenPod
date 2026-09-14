# Modo de download da ROM de máscara — CONFIRMADO no hardware

> 2026-09-13. Descoberto depois de o primeiro GN-438 ter sido brickado.
> **Este documento é o mais importante do projeto.** Ele descreve o único
> caminho de recuperação que funciona quando o firmware está destruído.

## A sequência

```
1. conecte o USB no computador
2. SEGURE o botão VOLUME PARA BAIXO
3. SEM soltar, pressione o botão RESET (o furinho lateral)
```

O aparelho enumera no computador **como disco**. Não como `301a:2800`,
não como card reader — como armazenamento em massa.

**Não é preciso abrir o aparelho nem desconectar a bateria.** O botão de
reset provoca um power-on reset, e é nesse instante que a ROM amostra o
pino de strap.

> ⚠️ **No macOS, se aparecer "O disco inserido não é legível", clique em
> IGNORAR.** Nunca em Inicializar — isso escreve na flash.

## Por que funciona (e por que demoramos a achar)

O manual do `Flashloader SL-DEV` da Shenju (fabricante do SoC) diz:

> "Press the hardware **PB9** button to keep the PB9 low level and
> **power on at the same time**."
>
> 按下硬件 PB9 按钮，保持 PB9 低电平，**同时上电**。

Duas coisas que erramos nos testes anteriores:

1. **"上电 / power on" não é "plugar o USB".** Com a bateria conectada, o
   SoC já está energizado; plugar USB não gera reset. O botão de reset é
   o que provoca o power-on de verdade.
2. **Procurávamos `301a:2800`.** O modo de download enumera como **disco**
   ("a disk character will appear"), não com aquele PID.

A tecla ligada ao PB9 neste aparelho é **VOLUME PARA BAIXO**. Em outros
modelos da mesma família relatam VOLUME UP — varia por placa.

## O que isto prova

| | |
|---|---|
| a ROM de máscara tem modo de download | **CONFIRMADO** — empiricamente |
| ele é alcançável com a flash corrompida | **CONFIRMADO** — o aparelho brickado entrou |
| não depende da FIRM nem do bootloader | **CONFIRMADO** — ambos estão quebrados neste aparelho |

Ou seja: **este hardware é recuperável por software, sempre.** A premissa
que guiou o projeto inteiro — "sem chip externo não há recuperação" —
estava errada.

## Consequências para o projeto

1. **A V030 deixa de ser pré-requisito.** A rede de segurança é de
   fábrica, está na ROM, e é melhor que qualquer patch. A V030 continua
   sendo uma conveniência boa (recuperar sem PC, só com cartão), mas não
   é mais a última linha de defesa.
2. **Gravar volta a ser reversível.** Toda regra do
   `PROTOCOLO_GRAVACAO.md` continua valendo — elas reduzem a chance de
   precisar da recuperação — mas o custo de errar deixou de ser o
   aparelho.
3. **O primeiro GN-438 pode voltar.**

## Ferramenta

`firmware/VENDOR/B27.zip` — `Flashloader SL-DEV 6.9.5`, oficial da Shenju.
Aplicativo Python empacotado com PyInstaller, **só Windows**. Grava NOR
Flash interna e externa a partir de arquivos `.up`.

Formato `.up` confirmado idêntico ao nosso:

| arquivo | magic | marca | tamanho |
|---|---|---|---|
| `update_restore_original.up` (nosso) | `CONFIG` | `SL6801` | `0x1A3038` |
| `B27_251112.up` (oficial) | `CONFIG` | `SL6801` | `0x1DA038` |

> ⚠️ **Nunca gravar o firmware do B27 neste aparelho.** É outro produto.
> Na thread do Reddit, um usuário brickou o dele exatamente assim.
> Só o nosso dump.

## Estado

Sequência confirmada no aparelho brickado em 2026-09-13. Falta identificar
o que exatamente enumera (VID/PID, nó de disco) e determinar se dá para
ler/gravar direto no macOS/Linux, ou se é preciso a ferramenta Windows.
