# EXPERIMENTO — a home passa a usar CRIA_LINHA

**Não é uma versão.** É a primeira tentativa de levar a home para o
caminho padrão, e ela pode simplesmente não desenhar.

Base: **OpenPod Core 2.3**. Oito bytes, um setor.

## O que mudou

```
0x0012ECF0   bl lv_img_create  ->  bl CRIA_LINHA
0x0012ED24   mov r0, r7        ->  mov r0, sb     (rotulo DENTRO da linha)
0x0012ED7E   bl posiciona      ->  nop ; nop
```

O quadro de ícone de cada item — hoje vazio, porque o S7 escondeu os
ícones — passa a ser uma **linha** criada pelo helper compartilhado, com
fundo de `cor_tela`, altura de `altura_linha` e o estado de seleção das
outras 36 telas. O rótulo passa a morar dentro dela.

A **posição** da linha continua vindo da tabela de coordenadas. Não
dependemos de layout automático — conferido: o `CRIA_CONTEINER` só limpa
o flag de rolagem e zera os pads, não configura flex.

## O que pode dar errado, e é provável

- as nove linhas empilharem umas sobre as outras;
- a linha nascer com largura zero e nada aparecer;
- a seleção continuar sendo pintada no rótulo — **os dois pontos de
  seleção NÃO foram tocados aqui, de propósito.**

Qualquer um é visível na hora.

## Por que só isto

É o primeiro experimento do projeto que troca a **classe** de um objeto
em tela. Mexer também na seleção no mesmo passo tornaria impossível saber
qual das duas coisas quebrou.

## Como usar

```
1. copie  update.up  para a raiz do cartao
2. Configurar -> Atualizar por SD -> Sim
3. fotografe a HOME
4. APAGUE o update.up do cartao
```

## Para voltar

O `.up` da Core 2.3, ou `recovery/RECOVERY.sh --alvo core`.

## O que a foto vai dizer

| a home | significa |
|---|---|
| nove linhas, texto legível, seleção funcionando | **o caminho padrão aceita a home** — e a conversão está quase feita |
| itens empilhados/sobrepostos | a coordenada da imagem não serve para a linha; precisa de posicionamento próprio |
| tela vazia | a linha nasce sem tamanho; precisa de largura explícita |
| seleção estranha | esperado — os dois pontos de seleção ficaram de fora deste passo |
