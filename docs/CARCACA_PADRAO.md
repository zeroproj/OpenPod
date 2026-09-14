# A CARCAÇA PADRÃO — o design de lista que o firmware já tem

> Aberto em 2026-09-14, a pedido do mantenedor:
>
> *"em configuração do produto ele já cria uma espécie de lista, ou seja é
> nativo do firmware, vamos aproveitar ela certo!! ELA É UMA CARCAÇA PARA
> O PRODUTO, UMA ESPÉCIE DE DESIGN PADRÃO QUE TODOS SE BASEIEM NELA? PQ AÍ
> FICA MAIS FÁCIL DE RESOLVERMOS A HOME. Aí criarmos uma home com base na
> forma que a config é criada. Mais fácil a manutenção."*

**A premissa está CONFIRMADA por medição.** Este documento é a prova e o
molde.

---

## 1. A carcaça existe, e não é pequena

Três rotinas compartilhadas, contadas por **padrão de bits dos `BL`** no
firmware ORIGINAL (regra §3 do projeto — nunca por desmontagem linear):

```
CRIA_FAIXA      0x00D216F0    52 chamadas
CRIA_CONTEINER  0x00D21690    59 chamadas
CRIA_LINHA      0x00D21764    39 chamadas
```

Não são helpers esquecidos: são **o idioma do próprio firmware** para
montar tela de lista. 39 telas já constroem suas linhas com a mesma
rotina.

> **Consequência prática:** o que se muda dentro de `CRIA_LINHA` muda em
> 39 telas de uma vez. Foi assim que o separador entre itens virou um
> patch de **1 byte** (ver `MARTE_ALVO.md` §2, item M-a).

---

## 2. Configurar USA a carcaça. A home NÃO. — CONFIRMADO

Medido varrendo os chamadores e filtrando por faixa de endereço:

```
CONFIGURAR  (page_set_menu, pagina 0x28, 0x00D3A428)
  CRIA_FAIXA      USA   1x   0x00D3A66C
  CRIA_CONTEINER  USA   1x   0x00D3A720
  CRIA_LINHA      USA   1x   0x00D3A7AA     <- dentro do laco
  CRIA_ROTULO     USA   3x   0xD3A69E  0xD3A80E  0xD3A826
  get_string      USA   1x   0x00D3A84C

HOME  (page_home_create, 0x00D2EBB8)
  CRIA_FAIXA      NAO USA
  CRIA_CONTEINER  NAO USA
  CRIA_LINHA      NAO USA
  CRIA_ROTULO     1x    0x00D2ED26   <- rotulo SOLTO, sem linha
  get_string      1x    0x00D2ED30
```

**A home é a exceção do firmware, não a regra.** É por isso que ela não
obedece nada que funciona nas outras telas — não há objeto de linha onde
a regra pudesse pegar.

---

## 3. O MOLDE — o laço do Configurar, decodificado

Desmontado de `0x00D3A700` a `0x00D3A876`.

### 3.1 Antes do laço

```
0x00D3A720   r5 = CRIA_CONTEINER(tela)
             altura, alinhamento               0xD4A1EA / 0xD4A3A2
             flag 0x10                         0xD49204
             direcao de rolagem = 0xC          0xD4B2FE
             borda 0, raio 0                   0xD4D0F4 / 0xD4D064

0x00D3A77E   r7 = 0x00C4879C     <- TABELA DE IDS, 10 entradas
             os 10 ids sao copiados para a pilha (ldm/stm: 4+4+2)

             r8 = r6 - 4         <- base dos arrays de ponteiro
             r7 = 0              <- indice do laco
```

### 3.2 O laço — `0x00D3A7A8` … `0x00D3A874`, **10 voltas** (`cmp r7,#0xa`)

```
r4 = CRIA_LINHA(r5)                         <- 1o objeto: A LINHA
     altura = tela_h / 7                       0xD4A1EA
     flag 0x8000                               0xD49204
     y = (tela_h / 7) * r7 - 1                 0xD4A3A2   (r1=2, r2=0, r3=y)
     add_event_cb(r4, 0x00D3A429, 0x0D)        0xD47064
     0xD4751C(grupo, r4)

fp = CRIA_ROTULO(r4)                        <- 2o objeto: O ICONE
     set_style_text_font(fp, 0x00CA671C)       0xD4D12E   fonte de icones
     set_text(fp, 0x00C5D622)                  0xD5ED94

sb = CRIA_ROTULO(r4)                        <- 3o objeto: O TEXTO
     set_width(tela_w - 0xF)                   0xD4A1BA
     set_long_mode(sb, 4)                      0xD5EF04
     set_text(sb, get_string(ids[r7]))         0xD2108C / 0xD5ED94

0xD51704(r4, 0, 0, 2)

r7 += 1
guarda:  [r8+0x04]! = r4   (linha)
         [r8+0x28]  = sb   (texto)
         [r8+0x50]  = fp   (icone)
```

### 3.3 O que faz esse molde funcionar

**O ícone e o texto são FILHOS da linha.** Não são irmãos posicionados
por coordenada — estão dentro de um objeto que tem altura, borda, evento
e estado próprios.

É isso que dá a propriedade que o mantenedor descreveu: **mexeu na linha,
mexeu em tudo que está nela** — e, como a linha vem de `CRIA_LINHA`,
mexeu nas 39 telas.

---

## 4. ⚠️ O PONTO ONDE ISSO PODE DAR ERRADO — e ele é barato

### 4.1 As estruturas têm larguras diferentes

```
CONFIGURAR   3 arrays de ponteiro, 10 itens cada
  [r8+0x04]! = r4   LINHA
  [r8+0x28]  = sb   texto        espacamento 0x28 = 10 x 4
  [r8+0x50]  = fp   icone

HOME         2 arrays de ponteiro, 9 itens cada
  [sl+0x04]! = sb                espacamento 0x24 = 9 x 4
  [sl+0x24]  = r6
                                 NAO EXISTE TERCEIRO ARRAY
```

A home guarda **dois** ponteiros por item. O molde produz **três** — a
linha também precisa ser guardada.

**Adotar o molde na home exige um terceiro array: +36 bytes (0x24).**

Isso é aritmética de alocação — a mesma classe que quebrou o
`make_extras_menu`, e que **não aparece na verificação byte a byte
pós-gravação**, porque corrupção de heap não muda os bytes gravados.

### 4.2 Mas a home aloca num lugar só, e o tamanho é um imediato

```
00D2EBBC  5420      movs r0, #0x54      <- 84 bytes
00D2EBBE  9db0      sub  sp, #0x74
00D2EBC0  bl        0xD58188            <- malloc
00D2EBC4  mov       r8, r0
00D2EBC6  cbnz      r0, 0xD2EBDA        <- CONFERE a falha
00D2EBC8            "page_home_create page_p malloc failed"
00D2EBDA  5422      movs r2, #0x54      <- memset(p, 0, 84)
00D2EBDC  0021      movs r1, #0
00D2EBDE  bl        0x8114A0
```

**Duas coisas boas:**

1. O tamanho aparece em **dois imediatos de 8 bits** — `0x00D2EBBC` e
   `0x00D2EBDA`. `0x54` → `0x78` cabe folgado em `movs r0,#imm8`
   (máximo 255). **Dois bytes.**
2. **O firmware já confere a falha de alocação** e sai limpo, registrando
   no log. Não é um `malloc` cego.

```
0x54 =  84 = 2 arrays x 9 x 4  (72)  +  12 de outros campos
0x78 = 120 = 3 arrays x 9 x 4  (108) +  12
```

> **Isto é HIPÓTESE, não CONFIRMADO.** Os 12 bytes restantes precisam ser
> mapeados campo a campo antes de mexer no tamanho — se algum campo mora
> *depois* dos arrays, mover o terceiro array para o fim não basta, e os
> deslocamentos `0x24` espalhados pelo código teriam de mudar junto.
>
> **Essa medição é pré-requisito do trabalho na home.**

---

## 5. Correção a um registro meu, do mesmo dia

Em `GUI_ANALYSIS.md` PARTE IV §22 eu escrevi que converter a home **não
encosta em alocação**, apoiado em:

```
page_home_event_cb        NENHUMA chamada de alocacao
page_home_menu_event_cb   NENHUMA chamada de alocacao
```

As duas linhas são verdadeiras, mas a conclusão não: **quem aloca é
`page_home_create`**, e ele aloca — `movs r0,#0x54` em `0x00D2EBBC`.

A conclusão correta: **converter a home MEXE em alocação, sim — mas num
único ponto, com tamanho em imediato, e com checagem de falha já
existente.** É risco conhecido e localizado, não risco difuso.

---

## 6. As tabelas de id e coordenada moram lado a lado

```
0x00C4867C   coordenadas da home
0x00C486A0   coordenadas da home
0x00C486C4   ids de texto da HOME          9 itens
0x00C4879C   ids de texto do CONFIGURAR   10 itens
```

Reescrever a home pelo molde significa **manter a tabela de ids
`0x00C486C4`** e trocar o laço que a consome — as coordenadas
(`0x00C4867C` / `0x00C486A0`) deixam de ser usadas, porque a posição
passa a vir de `(tela_h/7) * indice`.

---

## 7. Ordem de trabalho derivada

| passo | o que | por quê | custo |
|---|---|---|---|
| **1** | **M-a** — separador some | mexe DENTRO de `CRIA_LINHA`: uma mudança, 39 telas. É a carcaça provando que funciona | **1 byte** |
| **2** | mapear os 12 bytes restantes de `0x54` | pré-requisito medido do passo 3. Sem isso, mexer no tamanho é chute | medição |
| **3** | home sobre o molde | o marco: a home deixa de ser exceção | código novo + 2 bytes de alocação |

**O passo 1 é também a validação da tese.** Se um byte dentro de
`CRIA_LINHA` mudar as 39 telas ao mesmo tempo, a carcaça está provada na
prática — e aí o passo 3 se apoia em algo visto, não deduzido.
