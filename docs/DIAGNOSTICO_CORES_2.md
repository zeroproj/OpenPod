# Diagnóstico de cores 2 — o que o aparelho respondeu

> 2026-09-14. Instrumento gravado sobre a Core 2.2, com cada campo da
> tabela numa cor inconfundível. Três fotos.

```
cor_tela VERMELHO · cor_faixa VERDE · cor_separador AMARELO
cor_texto AZUL · cor_texto_sel MAGENTA · cor_selecao CIANO
```

---

## 1. Os cinco campos funcionam — CONFIRMADO

Na tela **Configurar**:

| elemento | ficou | logo lê |
|---|---|---|
| faixa superior | **VERDE** | `cor_faixa` |
| título | **AZUL** | `cor_texto` |
| fundo dos itens | **VERMELHO** | `cor_tela` |
| barra de seleção | **CIANO** | `cor_selecao` |
| texto do item selecionado | **MAGENTA** | `cor_texto_sel` |

**A linha lê `cor_tela`.** O patch `patch_fundo_lista` está certo.

> **Isto evitou um erro.** Eu ia escrever um patch mandando a linha ler
> `cor_faixa`, por causa do cinza. Teria quebrado o que estava certo. O
> instrumento custou uma gravação e evitou uma versão errada.

## 2. `cor_separador` está MORTO

O amarelo **não aparece em lugar nenhum** nas três fotos. Coerente: a
largura da borda da linha foi a zero na 2.2, e o traço da faixa vem de
outro objeto. O campo existe e ninguém o lê.

## 3. A home ignora a tabela — CONFIRMADO

Na foto da home, com `cor_tela = VERMELHO`, **o fundo dos itens continuou
BRANCO**. Faixa verde, texto azul, seleção ciano — mas o fundo, não.

**A home não lê `cor_tela`.** Quarta evidência independente de que ela
pinta por conta própria, e a primeira medida no aparelho.

## 4. A "tela que fica branca" — EXPLICADA

A foto da tela de **relógio** (Hora e data) responde:

```
fundo          VERMELHO   -> cor_tela, correto
digitos        BRANCOS    -> NAO e cor_texto (que estava AZUL)
```

**Os dígitos do relógio têm cor branca fixa, no código.** No tema claro
`cor_tela` é branco, e **branco sobre branco é invisível**.

Não era falha de redesenho: é um elemento que **some**. O mantenedor
relatou "tem hora que a tela em Configurações fica branca" — era esta.

> **E isto abre uma classe que o censo de fundo não pegava.** Além dos 84
> pontos que pintam **fundo**, há elementos com **cor de texto branca
> fixa**, que eram legíveis no tema escuro e desaparecem no claro.
> O tema claro não os quebrou — ele os revelou.

---

## 5. O que fica sabido, e o que fica aberto

**Sabido:**

```
os 5 campos de cor da tabela governam as 36 telas de lista
a home pinta o fundo por fora da tabela
cor_separador nao tem leitor
elementos com branco fixo somem no tema claro
```

**Aberto:**

- **o "cinza" atrás do texto.** O diagnóstico prova que **não é a
  tabela** — a linha é `cor_tela`. Sobra: um dos pontos de pintura fora
  da tabela, ou efeito do LCD. Não decidido, e **não vou escolher sem
  evidência**;
- quantos elementos têm branco fixo, e onde.

---

## 6. O que isto muda no plano

O tema claro do nano exige **duas varreduras**, não uma:

| varredura | o que | tamanho |
|---|---|---|
| **fundo** | 84 pontos de `set_style_bg_color`; a tabela governa 5 | medido |
| **texto claro fixo** | elementos brancos que somem no branco | **não medido ainda** |

Nenhuma das duas é uma versão pequena, e nenhuma se resolve patch a
patch — foi exatamente o que o `CLAUDE.md` §31 proíbe, e o que eu estava
começando a fazer antes deste instrumento.
