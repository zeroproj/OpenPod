# OpenPod — prompt de continuação

> Para quem assumir o projeto. Escrito em 2026-09-20, depois de dois
> dias de trabalho que renderam sete melhorias e três regressões.
> As regressões ensinaram mais que as melhorias, e estão todas aqui.

---

## 1. Leia isto primeiro, nesta ordem

```text
CLAUDE.md                    as regras do projeto. NÃO são sugestões
docs/ESTADO_ATUAL.md         onde tudo parou
docs/EXTRAS_INDICE.md        a causa de três dos defeitos abertos
docs/BLUETOOTH_REINICIA.md   a pergunta que trava tudo
docs/PROTOCOLO_GRAVACAO.md   o que já custou um aparelho
```

---

## 2. O estado em uma tela

**No aparelho do mantenedor:** Beta 12, funcionando.
**No site:** Beta 7. Nada publicado depois.

```text
release/OpenPod-Core-5.7-Public-Beta-12/   a boa
release/OpenPod-Core-5.7-Public-Beta-13/   um teste, não uma versão
release/OpenPod-Fabrica/                   o firmware original
```

---

## 3. A PRIMEIRA COISA A FAZER

**Peça ao mantenedor para gravar a Beta 13 e relatar o resultado.**

Ela responde a única pergunta que bloqueia o resto:

A Beta 10 aplicou um conserto de 26 bytes que passou em **toda**
verificação estática — desmontagem instrução a instrução, codificação
dos `b.w` conferida bit a bit, tabelas e pools intactos, área de destino
comprovadamente livre, `check_branch_targets` aprovado — e **quebrou os
seis itens do Extras**. A causa é desconhecida.

A Beta 13 é a Beta 12 com **o mesmo salto**, mas a rotina de destino faz
*exatamente* o que a cauda original fazia. É um no-op deliberado.

```text
tudo funciona  ->  o salto e a área livre estão bons.
                   O erro estava na lógica, e o conserto de
                   docs/EXTRAS_INDICE.md é seguro.

nada funciona  ->  o problema é o SALTO em si, ou aquela região não
                   executar como se presume. Isso derruba uma premissa
                   usada em TODAS as rotinas de área livre do projeto,
                   inclusive as que funcionam hoje.
```

**Não escreva nenhum conserto no despacho do Extras antes dessa
resposta.** Foi exatamente o que eu fiz, e custou três gravações.

---

## 4. O conserto que está pronto para escrever, depois

`docs/EXTRAS_INDICE.md` tem a causa e a tabela completas.

**Um bug, quatro sintomas.** O Extras passa o índice do *nosso* menu
onde a fábrica passa o índice *dela*:

| nosso | item | página | `sub` correto |
|---|---|---|---|
| 0 | Gravação | 24 | 2 |
| 1 | Rádio | 26 | 3 |
| 2 | Livro digital | 12 | 4 |
| 3 | Imagem | 21 | 5 |
| 4 | Bluetooth | 35 | 6 |
| 5 | Pastas | 34 | 0 |

Hoje passa `0` para os seis. Por isso Imagem e Livro digital não
atualizam a biblioteca, e o Bluetooth reinicia. Pastas acerta por
acidente.

O conserto: reescrever `[r4, #0xc]` **antes** de chamar a preparação,
com uma tabela de 6 bytes. Vale para os dois caminhos de abertura.

---

## 5. As três lições que custaram caro

**1. Varredura por forma sempre perde alguém, e não avisa.**

```text
bateria verde       varri por assinatura   achei 4 de 7 escritores
altura de linha     varri por valor fixo   achei 1 de 6 sítios
```

Desmonte e procure o **padrão** — registrador qualquer, vizinhança
qualquer. `tools/patch_linha16_geral.py` é o exemplo certo: varre por
significado **e varre de novo depois de gravar**, abortando se sobrar
sítio.

**2. Verificação estática não basta neste firmware.**

As duas ferramentas (`check_pilha.py`, `check_branch_targets.py`) olham
pilha e alvos de desvio. Nenhuma diz se o aparelho ainda funciona. A
Beta 10 passou nas duas.

E atenção: `check_pilha.py` procura ganchos **do firmware para a área
livre**. Uma rotina alcançada de dentro da própria área livre **não é
verificada** — ele reporta "0 ganchos" e aprova.

**3. Conclusão larga de teste estreito.**

A Beta 9 reverteu "a região do Bluetooth" (`0x00D28000`–`0x00D2B000`) e
o defeito continuou; concluí "não é nosso". Aquela faixa contém **seis
páginas diferentes** — o teste nunca testou o que eu disse que testava.

---

## 6. Como trabalhar aqui

**Toda imagem entregue é uma Beta numerada**, no formato de
`release/OpenPod-Core-<v>-Public-Beta-<N>/`, com um `TESTAR.txt` na raiz
dizendo o que olhar e quais resultados são possíveis. Nada de arquivo
solto com nome próprio.

```sh
python3 tools/patch_versao.py --in <base> --out <novo> --texto "OpenPod 5.7 B14"
python3 tools/gera_versao.py --imagem <novo> --versao OpenPod-Core-5.7-Public-Beta-14 \
        --nome-tela "OpenPod 5.7 B14"
python3 tools/publica_release.py --versao OpenPod-Core-5.7-Public-Beta-14 --push
```

**O nome na tela corta em 113 px.** Meça antes: `"OpenPod 5.7 Beta 10"`
dá 117 e fica cortado; `"OpenPod 5.7 B10"` dá 97.

**Publicar exige autorização do mantenedor, sempre.** Gerar e commitar é
livre. O repositório público distribui **só** os binários e a página —
nunca `tools/`, `analysis/`, `firmware/`, `docs/`, `CLAUDE.md`.

**O projeto vive em `~/Documents`, sincronizado pelo iCloud**, que cria
cópias de conflito `nome 2.bin`. Antes de empacotar:
`find <pasta> -name "* [0-9].bin" -delete`.

---

## 7. O que NÃO fazer

| | |
|---|---|
| gravar sem entender o mecanismo | três regressões em dois dias vieram daqui |
| tratar "passou na verificação" como "está certo" | a Beta 10 passou em tudo |
| mudar duas coisas na mesma tela num teste | a DIAG 6 já custou isso |
| reabrir o **M-g** (bateria) | está pronto: casca prateada, miolo verde `RGB(180,246,131)` |
| gravar o `B27_251112.up` | é firmware de outro produto |
| reescrever o setor `0x00D000` | matou o primeiro aparelho |

---

## 8. O que o mantenedor valoriza

Ele testa cada versão no aparelho dele e relata com precisão. Quando ele
diz que algo não funciona, **é dado, não opinião** — duas vezes eu
discuti com um relato dele e as duas vezes ele estava certo.

Ele pediu, com razão: *"você precisa ser mais assertivo"*. O que isso
significa na prática — **não mandar gravar aquilo cujo funcionamento não
se sabe explicar.** Cada tentativa custa o tempo dele e um ciclo de
flash do aparelho.

---

## 9. Se o aparelho não ligar

`docs/MODO_DOWNLOAD.md`. O modo de gravação da ROM de máscara roda antes
de qualquer firmware e já foi confirmado funcionando com a flash
destruída:

```text
1. conecte o USB
2. SEGURE o VOLUME PARA BAIXO
3. sem soltar, aperte RESET
```

O aparelho é recuperável por software, sempre.
