# OpenPod Core 2.1 — Marte M1: o tema claro do iPod nano

```
Base       OpenPod Core 2.0
Receita    tools/build.py --receita core2.1      28 passos
Gerada     2026-09-14
Status     EXPERIMENTAL
Kit        firmware/RELEASE/OpenPod Core 2.1/
Diff       11 bytes em 2 setores
```

**Duas mudanças, e a segunda entrou de propósito** — explicação na §1-bis.

**Dez bytes.** É a versão de maior efeito visível e menor risco do
projeto inteiro.

---

## 1. O que muda

Seis campos de cor da tabela de tema. Nenhum byte de código, nenhuma
rotina nova.

| campo | antes | depois | RGB565 do nano |
|---|---|---|---|
| `cor_tela` | `0x0000` preto | `0xFFFF` | branco |
| `cor_faixa` | `0x8208` | `0x39BE` | `0xBE39` cinza claro |
| `cor_separador` | `0xC731` | `0x0D5B` | `0x5B0D` |
| `cor_texto` | `0xFFFF` branco | `0x0000` | preto |
| `cor_texto_sel` | `0xFFFF` | `0xFFFF` | branco (já estava) |
| `cor_selecao` | `0xFA05` ciano | `0x3B2B` | `0x2B3B` azul do nano |

Dois já estavam no valor do nano — por isso 10 bytes e não 12.

As cores vêm do tema **NanoClone 5.2**, extraídas bitmap a bitmap
(`marte/paleta/nanoclone.json`). Não são escolha nossa.

### O swap, que é fácil errar

O display é RGB565 com os bytes trocados, e a tabela guarda os valores
**pré-invertidos**. A ferramenta recebe RGB565 puro e faz o swap.

Prova de que a tabela é mesmo pré-invertida: a seleção de hoje está
gravada como `0xFA05`, cujo swap é `0x05FA` — R=0, G=47, B=26, o ciano
que se vê na tela. Sem swap, `0xFA05` seria vermelho.

---

## 1-bis. A segunda seleção da home — 1 byte

O mantenedor viu na foto da Core 2.0: **"Configurar" em ciano e "Pastas"
com a barra.** Dois itens realçados ao mesmo tempo, de jeitos diferentes.

A home pinta a seleção em **dois lugares**, e a docstring do
`patch_cor_selecao.py` já os nomeava:

```
0x00D2EB42   navegacao   <- o patch_barra_selecao corrigiu
0x00D2EDB2   criacao     <- ESQUECIDO
```

O `patch_barra_selecao` trocou `set_style_text_color` por
`set_style_bg_color` em `0x0012EB4C`, o ponto da navegação. O gêmeo da
criação, `0x0012EDBC`, continuou pintando **cor de letra**.

Ao entrar na tela, o item selecionado ganha letra ciano. Ao navegar, a
barra anda certo — e a letra ciano fica para trás, porque nada a limpa.
Isso explica as duas fotos: na segunda ele tinha voltado de Configurar, a
home restaurou a seleção nele e pintou a letra, e ele desceu para Pastas.

> **O padrão, agora na quarta vez** — V016, V027, V031 e a barra de
> rolagem. Quando um patch muda a aparência de um objeto, enumerar
> **todos** os pontos que criam ou repintam aquele objeto. Aqui os dois
> estavam escritos, com nome, numa ferramenta do próprio projeto.

**O conserto são 4 bytes** (1 byte de diferença no encoding do `BL`):
`0x0012EDBC` passa a chamar `set_style_bg_color`. O `bg_opa` daquele
caminho já estava ligado — o `patch_barra_selecao` desviou `0x0012ED58`
para a rotina de opacidade, no mesmo trecho de criação.

### Por que não virou uma 2.2

Duas razões, e a segunda é a que decide:

1. **A 2.1 nunca foi gravada** — mudá-la não é reescrever história.
2. Com o tema claro, o item pintado na criação ficaria **azul sobre
   branco**. Seria um artefato bem no meio da tela, contaminando
   justamente a pergunta que a 2.1 existe para fazer: *o tema claro do
   nano agrada?*

## 2. Por que isto pode consertar defeito, e não só recolorir

Fotografado no aparelho com a Core 2.0, em 14/09:

```
home          9 itens, fundo escuro, selecao ciano       OK
Configurar    7 itens, titulo na faixa, separadores      OK
Despertador   3 itens, e um BLOCO BRANCO de ~30 px
              entre o titulo e o primeiro item
Musica vazia  um item, o resto BRANCO
```

O branco **não é item faltando** — a home mostra os nove. É a área do
contêiner que **ninguém pinta**: o fundo do display é branco por padrão
do LVGL, e `cor_tela` tem praticamente um leitor só.

**No tema do nano o conteúdo é branco.** O buraco que hoje parece defeito
passa a ser o fundo certo, e o texto — que hoje é branco e some quando
cai ali — passa a ser preto.

**Classe: PROVÁVEL.** Só o aparelho decide. É justamente o que esta
versão foi feita para perguntar.

---

## 3. Validação

```
validate_firmware   21 OK + a falha de CRC da R1, a esperada
diff contra a 2.0   10 bytes em 1 setor, menor offset 0x1A5400
                    tudo dentro dos 12 bytes de cor da tabela
OK   nada abaixo de 0x00D000    OK   0x00D000 intocado    OK   PSMP intocada
```

A ferramenta **recusa** se a tabela estiver virgem — Marte M1 não
funciona sobre a Core 1.0.x, e ela diz isso em vez de escrever no vazio.

```
imagem   6e286154f69f85f2dd08c2e9652c1a6dd58354a2afae8f88ee2e8c788b62b732
diff     11 bytes em 2 setores — 0x12E000 (1 B) e 0x1A5000 (10 B)
kit      3 setores, 12 KiB
```

---

## 4. Como instalar

```
1. copie  firmware/RELEASE/OpenPod Core 2.1/OpenPod_Core_2.1.up
   para a raiz do cartao como  update.up
2. Configurar -> Atualizar por SD -> Sim
3. apague o update.up do cartao
```

**Para voltar:** o `.up` da 2.0, ou os `base_*.bin` do kit, ou
`RECOVERY.sh --alvo core` para a 1.0.1.

---

## 5. O que olhar

1. **O aparelho ficou claro?** Texto preto sobre branco, seleção **azul**
   em vez de ciano, faixa superior **cinza claro** em vez de escura.
2. **O bloco branco do Despertador sumiu** — no sentido de deixar de ser
   notado, porque agora tudo em volta é branco?
3. **O texto é legível em todas as telas?** Este é o risco real: se
   alguma tela pinta o próprio fundo claro **sem** ler a tabela, o texto
   preto pode sumir ali.
4. **A seleção continua legível?** Texto branco sobre azul.
5. **Há ainda duas seleções?** Entre numa tela, volte, e navegue. Só a
   barra deve marcar — nenhuma letra de outra cor sobrando.
6. **A faixa superior ficou boa** com o relógio e a bateria por cima do
   cinza claro? Os ícones dela são desenhados com glifos, não com a
   tabela — este é o ponto onde eu mais espero surpresa.

---

## 6. O que ela **não** faz

O degradê. A faixa do nano tem 17 px de degradê vertical mais 1 de
separador, e a seleção dele também é em degradê. Aqui as duas são **cor
chapada**. Isso é **M2/M3**, exige rotina nova, e depende de o nosso
LVGL honrar `BG_GRAD_DIR`/`BG_GRAD_COLOR` — **PROVÁVEL, não confirmado**
(§4.1 do estudo). Plano B já escolhido: cor chapada na média do degradê,
`0xDF1C`, que a olho nu quase não difere.
