# TESTE DA 2.2 — o que olhar e por quê

Cada item existe para responder uma pergunta que a análise estática **não
responde**. Estão em ordem de valor.

---

## 1. EXTRAS — a correção de maior risco

Mexe em **despacho de página**, a classe que já custou três gravações.
Na 2.1 nenhum item funcionava.

Entre em **Extras** e abra os seis, um por um:

| item | deve abrir |
|---|---|
| Vídeo | lista de vídeos |
| Gravação | menu de gravação |
| Rádio | FM |
| Livro digital | lista de e-books |
| Bluetooth | menu Bluetooth |
| Ver pastas | navegador de pastas |

**E o mais importante, que é fácil esquecer:** em cada um, aperte
**voltar**. Tem de retornar ao **Extras**, não à home.

> Por quê: preservar o campo `msg[0x0a]` foi decisão deliberada
> justamente para o voltar funcionar. Se voltar cair na home, eu errei.

Se algum item não abrir ou travar, **me diga qual** — o mapa
`docs/PAGINAS.md` já liga cada um ao seu handler.

---

## 2. DENSIDADE DAS LISTAS — a mudança que eu não consigo conferir

O S11 mudou 28 telas de linha de **10 px para 16 px**. Nenhuma
ferramenta estática diz se ficou bonito.

Olhe **Configurar** e **Música**:

- os itens estão mais espaçados que na 2.1?
- ficou bom, ou **espaçado demais**?
- quantos itens cabem na tela agora? (na 2.1 cabiam mais)

> Se ficar ruim, é **um byte** em `0x001A540D` — não precisa refazer nada.

---

## 3. A FAIXA CLARA — o teste que discrimina

Achei uma causa provável: o fundo do display é **branco**, e aparece onde
a carcaça não cobre (`ARQUITETURA.md` §12).

Mas essa hipótese prevê uma faixa **fina e igual em todas as telas**. E
você relatou fina no Configurar e **grossa (~30 px)** no Despertador.
**Isso a hipótese não explica.**

Então, comparando lado a lado, me diga:

| tela | a faixa está |
|---|---|
| Configurar | fina / grossa / sumiu |
| Despertador | fina / grossa / sumiu |
| Música | fina / grossa / sumiu |
| Definir alarme (ou Brilho) | fina / grossa / sumiu |

**Foto das quatro ajuda mais que descrição.**

> Se for fina e igual em todas: minha hipótese está certa, e a correção é
> fazer o fundo do display ler `cor_tela`.
> Se continuar grossa em algumas: são **dois defeitos diferentes**, e eu
> só achei um.

---

## 4. A TELA TOCANDO AGORA — a pista do contador

Achei `"1/253"` como espaço reservado do contador em
`page_music_play_create`, alinhado no topo, onde o título mora.

Toque uma música e **olhe a tela Tocando Agora**: tem texto se
sobrepondo no alto?

> Isso decide o defeito #2. Eu havia registrado como "lista de Música",
> mas a página 0x04 (Tocando Agora) **não recebe título nosso** — então
> ou a colisão é lá entre elementos da própria tela, ou é outra coisa.

---

## 5. Confirmação rápida do resto

- **Configurar > Informações** diz `OpenPod 2.2`?
- A tela de **Gravação** ainda tem fundo branco? (o S12 devia ter tirado)
- Alguma tela **travou** ou ficou preta?

---

## Se algo der errado

O suspeito número um é o **Extras** — é despacho de página. O Saturno
(S11/S12) só mexe em aparência.

A 2.1 continua gravável: o kit está em `OpenPod 2.1/`.
