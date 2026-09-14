# OpenPod Core 2.0 — relatório de versão

```
Base       OpenPod Core 1.0.1 (STABLE)
Receita    tools/build.py --receita core2.0      27 passos
Gerada     2026-09-14
Status     EXPERIMENTAL — não testada no aparelho
Kit        firmware/RELEASE/OpenPod Core 2.0/
```

**A carcaça da interface.** É o substrato que Marte precisa: sem a tabela
de tema, a inversão de paleta da 2.1 não tem onde escrever.

---

## 1. O que muda na tela

| o quê | de | para |
|---|---|---|
| **home** | grade 3×3 de ícones | **lista**, 9 itens, um por linha |
| **seleção** | fundo do rótulo | **barra** de borda a borda, quadrada |
| **faixa superior** | não existia nas subtelas | título próprio em **37 telas** |
| **altura de linha** | duas: 10 px e 16 px | **uma**, 16 px, vinda da tabela |
| **ícones de lista** | ligados | desligados — igual ao `.cfg` do nano |
| **barra de rolagem** | visível | escondida em **59 telas** |
| **recuo do texto** | constante crua no código | campo da tabela |
| **cores** | espalhadas por ~155 pontos | **uma tabela de 19 bytes** em `0x1A5400` |

A home, lida da imagem construída:

```
itens : 9        rotulo: 116 px, alinhado a esquerda
 0 Musica        39 px     5 Imagem        46 px
 1 Video         31 px     6 Bluetooth     52 px
 2 Gravacao      52 px     7 Configurar    58 px
 3 Radio         33 px     8 Pastas        39 px
 4 Livro digital 62 px
rotulos que estouram a largura: 0
```

---

## 2. Por que sem o submenu Extras

A receita `interface` traz o `make_extras_menu`, que deixa a home com **4
itens** e empurra os outros seis para a página 0x53. **Mas quem faz o
Enter dessa página rotear é o `patch_extras`, que está FORA porque não
funcionou no aparelho.**

Com um e sem o outro, seis funções sumiriam atrás de um menu que não
abre — e a página 0x53 é, de fábrica, uma lista morta de três itens.

```
receita interface   itens: 4     Musica, Imagem, Extras, Configurar
receita core2.0     itens: 9     todos, nada escondido
```

Menos parecida com o nano, que tem submenus. Honesta. O submenu volta
quando o roteamento funcionar.

> O `--add Extras` do `relocate_lang_table` **fica**: o `patch_titulos`
> usa o id 216 como **título** da página 0x53. Tirar os dois juntos fez
> ele recusar.

---

## 3. Validação

```
validate_firmware   21 OK + a falha de CRC da R1, a esperada
audita_chrome       SEM DIVERGENCIAS — todas as telas na tabela
                    icones 0 pontos crus · selecao 0 · recuo 0
                    os tres helpers chamam a carcaca
                    home: faixa do helper sim, geometria da tabela sim
```

**Binary diff contra a Core 1.0.1:**

```
8.875 bytes em 36 setores, menor offset 0x04867C

OK   nada abaixo de 0x00D000 (bootloader)
OK   setor 0x00D000 intocado (regra R1)
OK   PSMP intocada (0x1FC000+)
```

**Pacote `.up`:** 1.728.512 B, CRC `0xCCC3` gravado == calculado, payload
idêntico à imagem, PSMP fora.

**A tabela de tema, já presente e legível em `0x1A5400`:**

```
00 00 08 82 31 C7 FF FF FF FF 05 FA 11 10 13 00 00 01 00
```

É nela que a 2.1 escreve os doze bytes do Marte.

---

## 4. Hashes

```
imagem (sem carimbo)  b3e89c85747e60d345f0eb9fb092adb63ac2b9d8c0513830935b538ae89b65d6
imagem (carimbada)    0698f143e9e245169fc02b843bd933acc17da5be324bf3f94d3a371883ee1cfd
pacote .up            5eff0109e5facd3ad91927da901bed498d7bffe340783620d7df245979767a3e
```

---

## 5. Os quatro defeitos que ela traz — dito antes, não depois

Herdados da 2.1/2.2, **não são regressão nova**: são o estado conhecido
desta camada. Entram porque a carcaça é indivisível — o `fix_status_bar`
recusa sem o `make_list_home`.

| # | defeito | situação |
|---|---|---|
| 1 | faixa clara vazia sob o título | causa provável identificada; a hipótese do fundo branco foi **derrubada pelo aparelho** |
| 2 | título colide com o contador na lista de Música | o contador **não foi localizado** |
| 5 | vão de 5 px nas 14 telas sem lista | **diagnosticado, conserto escrito** — 12 dos 15 contêineres aceitam a correção direta |
| 6 | barra da home no descanso de tela | não existe página de descanso |

Saem na **2.2**. O #5 já tem o conserto pronto.

---

## 6. Como instalar

**Pelo cartão SD:**

```
1. copie  firmware/RELEASE/OpenPod Core 2.0/OpenPod_Core_2.0.up
   para a RAIZ do cartao, com o nome  update.up
2. Configurar -> Atualizar por SD -> Sim
3. APAGUE o update.up do cartao
```

**Por cabo:** o kit tem 36 setores e nasce da **Core 1.0.1** — confere o
estado ANTES e recusa se o aparelho não estiver nela.

### Para voltar

```
sudo sh RECOVERY.sh --alvo core     # devolve a Core 1.0.1 STABLE
```

Ou o `.up` da 1.0.1 pelo cartão, ou os `base_*.bin` do próprio kit. São
três caminhos independentes.

---

## 7. O que olhar

Em ordem de valor:

1. **A home virou lista?** Os 9 itens aparecem, um por linha, com a barra
   de seleção de borda a borda?
2. **As subtelas têm título na faixa?** Entre em Música, Configurar,
   Rádio, Imagem — cada uma deve dizer o próprio nome.
3. **As listas têm todas a mesma altura de linha?** Configurar e Música
   eram as mais apertadas.
4. **Os 9 itens da home abrem?** Nenhum deles passou a depender do
   submenu — este é o ponto que a versão foi desenhada para garantir.
5. **Os quatro defeitos da §5 aparecem?** Principalmente o **vão de 5 px**
   nas telas sem lista (Despertador, Brilho) e a **faixa clara** — a foto
   ajuda mais que a descrição.
6. **Nada quebrou?** Música toca, rádio abre, pastas navegam.

---

## 8. Depois dela

A **2.1 é o Marte M1**: doze bytes na tabela de `0x1A5400`, e o aparelho
inteiro muda de cara — tema claro do iPod nano, seleção azul em degradê,
texto preto sobre branco.

Reversível em doze bytes. É a versão que responde *o tema claro agrada
neste aparelho?* sem arrastar nenhuma outra pergunta junto.
