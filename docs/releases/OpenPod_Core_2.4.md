# OpenPod Core 2.4 — a carcaça, em tema escuro

```
Base       OpenPod Core 1.0.1 (STABLE, o que estava no aparelho)
Receita    tools/build.py --receita carcaca      31 passos
Gerada     2026-09-14
Status     EXPERIMENTAL
Diff       8.921 bytes em 37 setores
```

---

## 1. O que ela é, e por que agora

Pedido do mantenedor: *"todas as telas tinham que ser 17px para combinar
com o nano. Tem como configurar isso universal? Não faz retrabalho uma
carcaça com essas definições?"*

**Tem, e ela já existia.** É exatamente o que a carcaça faz:

```
tabela de tema, 0x001A5400
   +0C  altura_faixa   17 px
   +0D  altura_linha   16 px    <- UM BYTE governa 38 pontos em 28 telas
   +0E  inicio_lista   19 px
```

Antes do S11 o aparelho tinha **duas** alturas de linha ao mesmo tempo:
25 pontos com o imediato `10`, 3 com `set_size(w,10)`, e 10 calculando
`160/10 = 16`. Agora os 38 leem a tabela.

**16 px é a medida do nano** — a tinta real da fonte de 18 px são 16.
Decidido pelo mantenedor: *"usa o padrão do nano, 16, é melhor"*.

---

## 2. Tema ESCURO — e isso não é recuo

A Core 2.4 é a receita `marte` **menos os dez bytes de paleta**.

O tema claro foi descartado por **limitação de hardware medida**, não por
gosto: as faixas horizontais no fundo claro vêm do LCD, isoladas por
eliminação (`docs/MARTE_ALVO.md` §0-bis). A carcaça é independente da
paleta — o que não serviu foram dez bytes de cor.

```
cor_tela      0x0000 preto        cor_texto      0xFFFF branco
cor_faixa     0x8208              cor_texto_sel  0xFFFF
cor_separador 0xC731              cor_selecao    0xFA05 ciano
```

---

## 3. O que entra além da carcaça

Tudo o que foi validado no aparelho e **não depende de claro/escuro**:

| | |
|---|---|
| `fix_barra_selecao_criacao` | a "segunda seleção" da home — defeito real, causa medida |
| `patch_fundo_lista` | fundo da linha e do contêiner vêm da tabela |
| `patch_sem_separador` | sem traço entre itens, como o nano |
| `patch_texto_branco_fixo` | 8 pontos de branco fixo passam a ler a tabela |

**Fica de fora, por decisão:** todo o código experimental da home
(`exp_home_linha` e derivados). Ele bugou o menu no aparelho, e o
mantenedor o descartou.

---

## 4. Sobre o `patch_chrome_padrao` — auditado a pedido

É pré-requisito de tudo, e se sustenta:

- **resolve problema medido:** a faixa é `160/divisor`, e o divisor era
  constante por tela — **51 das 52 divergiam da home**;
- **as rotinas estão vivas:** 92 chamadas a seis thunks em
  `0x00DA5300..0x00DA5344`. É sobre eles que a tabela foi montada;
- **recusa tudo se uma tela não for localizada** — aplicar em parte
  repetiria o remendo que ele existe para acabar;
- **desmonta cada rotina que monta**, conferindo instrução por instrução;
- não caiu na armadilha óbvia: o divisor também alimenta o espaçador
  inferior, e trocá-lo cobriria a lista.

Duas coisas declaradas: a faixa virou **cor sólida** no tom do meio (o
degradê de três faixas é imperceptível neste LCD), e ele **não mexe** nas
telas com faixa e sem lista — o que o S9, também nesta receita, cobre.

---

## 5. Validação

```
validate_firmware   21 OK + a falha de CRC da R1, a esperada
audita_chrome       SEM DIVERGENCIAS
diff contra 1.0.1   8.921 bytes, 37 setores, menor offset 0x04867C
OK  nada abaixo de 0x00D000   OK  0x00D000 intocado   OK  PSMP intocada
imagem  6fb28b380b25891c19c9d70769834f01697b3ec5a92d02a6f738f8bed2b3f158
```

---

## 6. O que olhar

1. **Todas as listas com a mesma altura de linha?** Era o pedido. Compare
   Configurar, Música, Rádio e Pastas.
2. **A home virou lista**, com barra de seleção de borda a borda?
3. **Título próprio na faixa** de cada subtela?
4. **Só uma seleção?** Entre numa tela, volte, navegue — nenhuma letra de
   outra cor sobrando.
5. **As telas sem lista** (Despertador, Brilho) — a faixa está na mesma
   altura das outras?
6. Nada quebrou: música, rádio, pastas, Bluetooth.

---

## 7. O que ela **não** faz

A home continua desenhando por conta própria — ela entra na carcaça em
geometria e cor, mas não no **caminho de desenho**. A conversão para
`CRIA_LINHA`, como o Configurar faz, é a etapa seguinte, e vai ser escrita
do zero pelo padrão do Configurar — **não** reaproveitando o experimental.

O `docs/CONVERTER_HOME.md` tem o laço do Configurar decodificado, a
tabela de ids da home (`0x0486C4`) e o que ainda falta: a base dos arrays
de ponteiro.
