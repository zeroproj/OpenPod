# M-b — a home vira lista. O plano, antes do código

> Aberto em 2026-09-14, depois da Core 1.4. É o **marco** da tabela do
> Marte: a home é a única tela que não usa a carcaça, e por isso a única
> que não obedece nada que já funciona nas outras 39.
>
> **Este documento é plano, não relatório.** Nada dele foi implementado.

---

## 1. O que está CONFIRMADO, e é a base de tudo

### 1.1 A home é a exceção do firmware

```
CRIA_FAIXA      0x00D216F0    52 chamadas   home: NAO USA
CRIA_CONTEINER  0x00D21690    59 chamadas   home: NAO USA
CRIA_LINHA      0x00D21764    39 chamadas   home: NAO USA
```

Ela desenha **nove rótulos soltos**, posicionados por coordenada
absoluta, com um objeto de quadro/ícone irmão por item. Não há linha, não
há contêiner. Detalhe em `CARCACA_PADRAO.md` §2.

### 1.2 Desenho e navegação são DESACOPLADOS — a descoberta que barateia tudo

```
00D2E96E  cmp r0, #0xd        LV_EVENT_KEY
00D2E97C  cmp r2, #0x1b       e daí os codigos de tecla: 1B 13 14 0B 09 0A
00D2EB2E  cmp r1, #8          indice de 0 a 8 — NOVE itens, ja de fabrica
00D2EB32  strb r1, [0x00823D83]   o indice mora num global
```

**A home roteia por TECLA e por ÍNDICE, nunca por objeto clicado.** Logo,
trocar *como* os itens são desenhados **não toca na navegação**.

### 1.3 A seleção é achada pelo índice, no array B

```
00D2EB3A  add.w r3, r5, r3, lsl #2     r5 = page_p ; r3 = indice
00D2EB40  ldr   r6, [r3, #0x24]        array B[indice] = O ROTULO
00D2EB42  bl    palette_main(0xC)
00D2EB4C  bl    set_style_text_color(r6, cor, 0)
```

**Se o array B continuar guardando o rótulo, todo o código de seleção
existente continua funcionando sem ser tocado.**

### 1.4 A linha da carcaça faz layout sozinha — confirmado na Core 1.4

Ao zerar o texto do rótulo de ícone (M-e), os irmãos **encostaram na
esquerda sozinhos**. A linha usa flex. Consequência direta: o novo laço
**não precisa calcular coordenada de filho**.

---

## 2. A conta de alocação — a preocupação que CAI

Eu havia registrado, em `CARCACA_PADRAO.md` §4, que adotar o molde exigiria
um **terceiro array** e `malloc 0x54 → 0x70`. Isso era verdade para o molde
do Configurar, que guarda **três** objetos por item:

```
CONFIGURAR   +0x00 linha    +0x28 texto    +0x50 icone
```

**Mas a home do Marte não tem ícone** — o M-e já estabeleceu que
decoração de linha sai. Então ela precisa de **dois**:

```
HOME (hoje)  +0x00 quadro/icone   +0x24 rotulo
HOME (nova)  +0x00 A LINHA        +0x24 rotulo   <- mesmos slots
```

```
malloc 0x54    FICA
memset 0x54    FICA
zero bytes de alocacao
```

> **Isto elimina a única classe de risco grave deste trabalho.** Aritmética
> de ponteiro e heap foi o que quebrou o `make_extras_menu`, e corrupção de
> heap **não aparece** na verificação byte a byte pós-gravação.

---

## 3. Orçamento de espaço

```
regiao reescrevivel   0x00D2EC42 .. 0x00D2ED8E   = 332 bytes
   (comeca na carga da tabela de COORDENADAS, que deixa de existir)

molde do Configurar   conteiner+setup  136 B
                      laco 3 objetos   204 B
                                       -------
                                       340 B
   menos o icone (criar + fonte + texto + guardar)   ~ -40 B
                                       -------
   estimativa                          ~300 B      CABE em 332
```

**Sem gancho, sem área livre, sem realocação.** O código novo mora no lugar
do antigo.

---

## 4. O desenho proposto

```
r7 = a tela ; r8 = page_p

  cont = CRIA_CONTEINER(tela)              0x00D21690
         altura / alinhamento / scroll      como o Configurar faz
  ids  = 0x00C486C4                        tabela de ids da home, 9 itens
  sl   = r8 - 4 ; i = 0

  laco, 9 voltas:
      linha  = CRIA_LINHA(cont)            0x00D21764
               altura = tela_h / 7          0xD4A1EA
               y      = (tela_h/7)*i - 1    0xD4A3A2
               add_event_cb(linha, ...)     0xD47064

      rotulo = CRIA_ROTULO(linha)          0x00D5E2E8
               set_width(tela_w - 0xF)      0xD4A1BA
               set_long_mode(rotulo, 4)     0xD5EF04
               set_text(get_string(ids[i]))

      [sl+0x04]! = linha                   <- array A, papel novo
      [sl+0x24]  = rotulo                  <- array B, papel INALTERADO
      i += 1
```

**Nenhum ícone é criado.** O texto encosta na esquerda por flex (§1.4).

---

## 5. A seleção: duas etapas, e a primeira é conservadora

### Etapa 1 — não mexer na seleção

O código existente pinta `array B[indice]` com cor de texto. Como o array
B continua sendo o rótulo, **a seleção continua funcionando exatamente como
hoje**: o texto do item selecionado muda de cor.

Fica feio para o alvo — o Marte quer **barra**. Mas é a etapa que prova a
conversão **sem mexer em mais nada**, e é ela que vai ao aparelho primeiro.

### Etapa 2 — a barra, depois de a etapa 1 rodar

Trocar, no caminho de repintura, `array B` por `array A` e
`set_style_text_color` por `set_style_bg_color`. São dois pontos
(`0x00D2EB40`/`0x00D2EB4C` e o par que despinta o anterior).

**Etapa separada, versão separada, teste separado.** Juntar as duas seria
repetir o erro da 2.x.

---

## 6. Riscos declarados, e o que fazer com cada um

| # | risco | mitigação |
|---|---|---|
| 1 | o código novo não cabe em 332 bytes | medir ao montar; se estourar, cortar o `add_event_cb` (a navegação é por tecla, talvez nem precise) |
| 2 | a home usa `r4` (o objeto principal, guardado em `+0x48`) em código posterior | **não tocar** em `+0x48`; o novo laço preserva o que já estava lá |
| 3 | a folha de imagem da home continua desenhando a grade por baixo | medir: se aparecer, é o item que o antigo `patch_saturno_s5` resolvia. **Não incluir preventivamente** — só se a tela mostrar |
| 4 | o `cmp r1,#8` limita a 9 itens | é o que queremos; a home tem 9 |
| 5 | brick | nenhum byte abaixo de `0x00D000`; volta pela 1.4 por cartão; `recovery/` intacto |

---

## 7. Como isso será validado, em ordem

```
1. autoteste da ferramenta, com guarda-corpo de contexto
2. desmontagem da imagem gerada, instrucao por instrucao
3. validate_firmware  — 21 OK + a falha de CRC da R1
4. diff contra a 1.4  — so a regiao 0x12E000, nada mais
5. GRAVAR e OLHAR
```

**O passo 5 é o único que decide.** Os quatro primeiros só impedem de
gravar bobagem.

---

## 8. O que este plano NÃO faz

- não mexe na faixa superior (M-c);
- não mexe em degradê (M-h) nem na bateria (M-g);
- não mexe na alocação;
- não cria nada na área livre;
- não junta a barra de seleção na mesma versão.

**Uma coisa por vez, testada na tela, sem carona.**
