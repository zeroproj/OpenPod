# OpenPod Core 1.1 — o traço entre os itens some

```
Base       OpenPod Core 1.0.1 (STABLE)
Receita    tools/build.py --receita core1.0      7 passos
Gerada     2026-09-14
Status     ✅ CONFIRMADA NO APARELHO
Kit        firmware/RELEASE/OpenPod Core 1.1/
Diff       1 byte contra a 1.0.1
```

Primeira versão depois da limpeza que removeu a linha 2.x. É deliberadamente
mínima: **uma mudança, um byte.**

---

## 1. O que muda

Item **M-a** da tabela do Marte (`docs/MARTE_ALVO.md` §2): a lista do
iPod nano é limpa, sem traço separando um item do outro. O firmware de
fábrica desenhava um, de 1 px, em todas as telas de lista.

```
0x0012179E   01 -> 00

00D2179E  movs r1, #1  ->  movs r1, #0
00D217A0  bl   0xD4D0F4    set_style_border_width (prop 50)
```

Está **dentro de `CRIA_LINHA`** (`0x00D21764`), a rotina compartilhada
que **39 telas** usam para montar cada item.

### Por que zerar a largura, e não caçar a cor

A cor dessa borda vem de `palette_main(0x12)`, não de tabela nenhuma.
Zerar a largura resolve num ponto o que caçar a cor resolveria em vários.

### O que NÃO foi tocado

```
0x001217A8   border_side da LINHA — sem largura, ele nao desenha
```

**E, principalmente, a borda da FAIXA superior.** São objetos diferentes,
e o alvo do Marte **tem** o traço embaixo da faixa (`faixa_separador`,
y=17 do `nanoclone.json`). Eu já havia confundido os dois numa análise
anterior; desta vez a distinção foi declarada antes e **confirmada na
tela**.

---

## 2. ✅ Confirmado no aparelho — 2026-09-14

Instalada **pelo cartão SD**. Foto da tela Configurar enviada pelo
mantenedor: *"Excelente"*.

```
Despertador
Idioma
Hora e data       <- selecionado, barra de borda a borda
Brilho
Tempo de tela
Desligar sozinho
```

```
sem traco entre os itens              OK
traco embaixo da FAIXA preservado     OK   <- a distincao, provada
nada mais mudou                       OK
```

### O que isso prova, e não é pouco

> **A carcaça é real, e é operável.** Um byte dentro de uma rotina
> compartilhada mudou a tela inteira. A tese do mantenedor —
> *"uma carcaça de design padrão que todos se baseiem nela"* — deixou de
> ser dedução e virou observação.
>
> É isso que dá base ao passo seguinte, a conversão da home.

---

## 3. O que a mesma foto mediu de graça

Três itens da tabela do Marte estavam como **A MEDIR** ou inferidos por
construção. A foto resolveu:

| item | o que a tela mostra | consequência |
|---|---|---|
| **M-f** seleção | **já é de borda a borda** — geometria certa. Mas é **ciano chapado**, `palette_main(7)` = RGB(0,190,213) | falta só a COR: o alvo é azul RGB(41,101,222), em degradê |
| **M-d** rolagem | barra fina à direita da lista | confirma o item |
| **M-e** ícones | engrenagem em toda linha | confirma o item |
| **M-c** título | faixa vazia, só a bateria à direita | confirma o item |
| **M-j** tema | escuro, **sem faixas horizontais** | o desvio de §0-bis se sustenta: o painel se comporta no escuro |

**A seleção é a surpresa boa:** metade do M-f já está pronta de fábrica.

---

## 4. Validação

```
build.py --receita core1.0
  imagem sem carimbo  f365e1fdd8a40bbdb38f3f0100cf3644250feb15ad1ebb2bcc969cd98c2d8d69
  imagem carimbada    843577e2f9026e6171ee5401f7136479ba35054334e201893ac8793696f28c6c

validate_firmware   21 OK + a falha de CRC da R1, a esperada

diff contra a Core 1.0.1
  1 byte, 1 setor (0x121000), em 0x0012179E

diff contra o ORIGINAL
  9.119 bytes, 8 setores, menor offset 0x048798
  OK  nada abaixo de 0x00D000    OK  0x00D000 intocado    OK  PSMP intocada

desmontagem da imagem gerada
  00D2179E  movs r1, #0        confere
  00D217A8  movs r1, #1        border_side intacto, como projetado
```

**Pacote `.up`:** 1.724.672 B, CRC do payload `0x4011`,
sha256 `165ab1366bdc0f7e09edbda58008132f2438659ecb1d438c47b8e3ed1107c64e`.

---

## 5. A ferramenta

`tools/patch_sem_separador.py`

- **guarda-corpo:** confere 5 pontos de contexto ao redor do alvo antes
  de escrever. Se a imagem não for este firmware, recusa sem tocar em
  nada;
- **autoteste com teste negativo:** aplicar duas vezes tem de ser
  recusado — e é;
- não aloca, não usa a área livre, não tem `--em`.

**Na receita entra como passo 7, no fim, de propósito:** é independente
de tudo o que vem antes, então pode sair dali sem quebrar nada. Foi
exatamente essa propriedade que faltou na linha 2.x, onde
`patch_chrome_padrao` era pré-requisito de doze outros passos.

---

## 6. Como instalar

```
1. copie  firmware/RELEASE/OpenPod Core 1.1/OpenPod_Core_1.1.up
   para a RAIZ do cartao, com o nome  update.up
2. no aparelho: Configurar -> Atualizar por SD -> Sim
3. ele reinicia e se atualiza
4. APAGUE o update.up do cartao
```

Para voltar: o `.up` da Core 1.0.1, pelo mesmo caminho.

---

## 7. O que vem depois

A home **não mudou** com esta versão, e isso é esperado: ela não usa
`CRIA_LINHA`. É a próxima frente.

O pré-requisito dela foi fechado no mesmo dia — a estrutura de
`page_home_create` está mapeada campo a campo em
`docs/CARCACA_PADRAO.md` §4.3, com **8 bytes de folga no fim** e o custo
da conversão medido em **dois imediatos de 8 bits**.
