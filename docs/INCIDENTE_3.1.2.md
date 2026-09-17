# INCIDENTE — Core 3.1 / 3.1.2: o Extras não abre nada

> Aberto em 2026-09-17, depois de o mantenedor relatar, com a **3.1.2
> gravada no aparelho**: *"nada abre no extra"*.
>
> Este documento é o laudo. A ferramenta que ele produziu é
> `tools/check_branch_targets.py`.

---

## 1. Resumo

A 3.1.2 tem **três defeitos**, e dois deles danificaram código que não
tem relação nenhuma com o Extras. O sintoma na tela é um só — nada abre —
mas a causa é acumulada: a 3.1 quebrou, a 3.1.1 remendou a 3.1, e a
3.1.2 remendou a 3.1.1 **escrevendo por cima de código vivo nas três
vezes**.

| # | Defeito | Classe | Versão que introduziu |
|---|---|---|---|
| 1 | Cinco destinos de desvio de `page1_process` viraram `nop` | CONFIRMADO | 3.1.2 |
| 2 | O índice do item selecionado nunca é escrito → sempre 0 | CONFIRMADO | 3.1.2 |
| 3 | A saída do handler do Extras (`0x00D2F01A`) virou `nop` | CONFIRMADO | 3.1 |
| 4 | `current_page` provavelmente nunca vira `0x53` | PROVÁVEL | 3.1.2 |

**A 3.1.2 não é consertável com um patch pequeno.** O caminho de volta
passa por código que não existe mais na imagem.

---

## 2. Defeito 1 — cinco destinos de desvio apagados  · CONFIRMADO

A 3.1.2 escreveu o "mini-handler da Gravação" em `0x00D012E2` e preencheu
com `nop` até `0x00D01301` (32 bytes). O CHANGELOG da 3.1.2 descreve essa
faixa como *"o slot 9 da home (vago)"*.

**A faixa não estava vaga.** Era o corpo de cinco casos de um switch, e
`page1_process` desvia para lá cinco vezes:

```text
0x00D00F46  bne.w #0xD012FC    ; cmd != 6        -> AGORA É NOP
0x00D00F66  bne.w #0xD012F6    ; sub != 2        -> AGORA É NOP
0x00D00FA6  bne.w #0xD012F0    ;                 -> AGORA É NOP
0x00D00FAE  bne.w #0xD012EA    ;                 -> AGORA É NOP
0x00D00FB6  bhi.w #0xD012E2    ; índice fora     -> AGORA É NOP
```

Os dois primeiros são as **saídas de falha de guarda**: antes registravam
o erro e retornavam limpo. O último é o **caso default** da verificação de
faixa — não um slot vago.

Hoje os cinco caem em `nop` e escorregam para `0x00D01302`, que é o corpo
do caso seguinte seguido do pool de literais.

> **Como foi encontrado:** desmontagem comparada de
> `GN438_original.bin` e `GN438_core_3.1.2.bin` com capstone, e depois
> varredura de todos os desvios da FIRM com destino dentro das faixas
> reescritas.

---

## 3. Defeito 2 — o índice do item é sempre 0  · CONFIRMADO

O handler de clique do Extras lê o item selecionado do global
`0x00823D84`:

```asm
0x00D2EFF8  ldr  r2, [pc, #0x94]   ; &0x00823D84
0x00D2EFFA  ldrb r2, [r2]          ; índice selecionado
0x00D2EFFC  adr  r3, #0xc          ; tabela em 0x00D2F00C
0x00D2EFFE  ldrb r2, [r3, r2]      ; destino = tabela[índice]
```

Varredura da imagem inteira: **`0x00823D84` é lido em 2 lugares e escrito
em nenhum.** O único `strb` que o escrevia ficava em `0x00D2F016`, e o
patch da 3.1.2 escreveu por cima dele.

No firmware de fábrica o índice era calculado comparando o ponteiro do
objeto clicado contra a lista de botões (`ldr r3,[r4]` / `[r4,#4]` /
`[r4,#8]`), e **depois** gravado nesse global para lembrar a seleção.
A 3.1.2 manteve a leitura e apagou a escrita.

Consequência: `tabela[0] = 0x09` para os **seis** itens. Todos despacham
para o mesmo destino.

---

## 4. Defeito 3 — a saída do handler virou nop  · CONFIRMADO

Introduzido pela **3.1**, não pela 3.1.2.

`0x00D2F01A` era o `pop {r4, r5, r6, pc}` que encerra o handler. Dois
desvios apontam para ele:

```text
0x00D2EF7C  bne #0xD2F01A   -> AGORA É NOP
0x00D2F046  bne #0xD2F01A   -> AGORA É NOP
```

É o caminho "o objeto clicado não é um dos meus botões, retorne". Hoje
cai em `nop` e escorrega para `0x00D2F024`, que é o corpo da função
seguinte.

---

## 5. Defeito 4 — a página corrente  · PROVÁVEL

O stub em `0x00D0F218` chamava `bl 0xD0CC0C`, o handler de fábrica da
página `0x53`. A 3.1.2 trocou por `bl 0xDA5920` (o módulo novo na área
livre).

O único ponto da FIRM que grava `0x53` em `current_page` está em
`0x00D0CDC4`, dentro dessa função que acabou de ser desconectada.

Se for esse o caso, a guarda de `page1_process`

```asm
0x00D00F4C  ldrh r2, [r4, #8]    ; msg->page  (= 0x53, enviado pelo Extras)
0x00D00F4E  ldrb r0, [r3, #0xa]  ; current_page
0x00D00F50  cmp  r2, r0
0x00D00F54  beq  #0xD00F62       ; segue só se forem iguais
```

falha **sempre**, e o desvio de falha vai para `0xD012F6` — que o
Defeito 1 transformou em `nop`.

**Isso descreve exatamente o sintoma observado: nada abre, sem mensagem
de erro.**

> Classificado como PROVÁVEL e não CONFIRMADO porque não determinei os
> limites exatos da função que começa em `0xD0CC0C`; `0xD0CDC4` pode
> pertencer à função seguinte. **Como confirmar:** mapear o fim de
> `0xD0CC0C` e verificar se `0xD0CDC4` está dentro dela.

---

## 6. A ferramenta que faltava

`tools/check_branch_targets.py` responde a pergunta que a verificação
byte a byte, o CRC e a releitura do aparelho **não respondem**:

> *Algum desvio do firmware original aponta para dentro de uma faixa que
> o meu patch sobrescreveu?*

Rodada versão a versão, ela isola as duas culpadas sozinha:

```text
2.4    vs 2.3     -> 0 desvios novos   APROVADO
3.0    vs 2.4     -> 0 desvios novos   APROVADO
3.1    vs 2.4     -> 2 desvios novos   REPROVADO   <- Defeito 3
3.1.1  vs 3.1     -> 0 desvios novos   APROVADO
3.1.2  vs 3.1.1   -> 5 desvios novos   REPROVADO   <- Defeito 1
```

**Se ela existisse, a 3.1 nunca teria chegado ao cartão.**

### Sobre falsos positivos

A ferramenta varre cada alinhamento de 2 bytes e tenta decodificar uma
instrução. Em cima de dados isso inventa desvios. Ela erra **para o lado
de reclamar demais**, de propósito: é uma trava, não um relatório.

Dois mecanismos controlam o ruído:

1. Faixas que não desmontam de ponta a ponta são classificadas como
   **dados** e ignoradas.
2. `--baseline <imagem boa>` reporta só o que é **novo** em relação a uma
   versão que funciona. Contra a 2.4, a 3.1.2 sai com 7 achados e **zero
   ruído**.

Sem baseline, a 1.0.1 — que funciona no aparelho — reporta 1 achado.
É falso positivo. **Use sempre `--baseline`.**

---

## 7. A regra que fica

> **Nenhum patch escreve por cima de código sem antes listar todos os
> desvios que apontam para aquela faixa.**

A checagem leva 5 segundos e teria evitado os três defeitos.

O erro de raciocínio que se repetiu nas três versões foi supor que uma
região era "vaga" ou "morta" porque a função ao redor parecia terminar
ali. Em Thumb-2 com switch compilado, **os casos de um switch ficam
depois do fim aparente da função**, e o `bhi.w` do default aponta para
eles.

---

## 7-bis. Achado colateral: a 3.1.1 e a 3.1.2 escrevem no setor `0x00D000`

Descoberto em 2026-09-17, ao validar o kit da 3.0.1.

| Versão | CRC da FIRM na tabela | Setor `0x00D000` |
|---|---|---|
| 1.0.1, 2.4, 3.0, 3.0.1, 3.1 | mantido em `0x49A6` (o de fábrica) | **intacto** |
| **3.1.1, 3.1.2** | reescrito (`0x940B`, `0x8548`) | **escrito** (`0x0D01C`–`0x0D01D`) |

A 3.1.1 e a 3.1.2 recalcularam o CRC da FIRM e gravaram o valor novo na
tabela de partições. Isso obriga a regravar o setor `0x00D000`.

**É exatamente o que `tools/crc_neutralize.py` existe para evitar.** Esse
setor guarda, 8 bytes antes do campo de CRC, o ponteiro que o bootloader
segue para achar o firmware (`ptable + 0x14 = 0x0000E000`). Flash NOR não
grava 2 bytes: apaga 4096 e reescreve. Foi nessa janela que a gravação do
V028 falhou e o primeiro GN-438 do projeto morreu
(`docs/INCIDENTE_V028.md`).

Todas as versões anteriores deixavam o CRC gravado no valor de fábrica e
simplesmente não batiam — e bootavam do mesmo jeito, o que é evidência de
que **o bootloader não verifica o CRC da partição FIRM no boot**
(CONFIRMADO por observação: 1.0.1, 1.4 e 2.3 rodaram na tela com CRC
divergente).

> A 3.1.2 já foi gravada e o aparelho sobreviveu. O risco não é o estado
> em que ele está — é cada nova instalação desses dois pacotes.

---

## 8. Recomendação

1. **Voltar para a Core 2.4** pelo cartão — a última estável.
2. Refazer o Extras **uma vez só**, partindo da 2.4, com:
   - a ViewTask mapeada (`analysis/ui/UI_TASK_ARCHITECTURE.md`);
   - o orçamento do heap LVGL medido — 40 KiB, `0x00876000`–`0x00880000`;
   - `check_branch_targets.py --baseline` obrigatório antes de empacotar.
3. **Não** tentar consertar a 3.1.2 com mais um patch. Seria o quarto
   remendo em cima do mesmo código danificado.

---

## 9. Classificação

| Afirmação | Classe |
|---|---|
| 5 destinos de desvio de `page1_process` apagados | CONFIRMADO |
| `0x00823D84` lido em 2 pontos, escrito em 0 | CONFIRMADO |
| `0x00D2F01A` (saída do handler) virou nop na 3.1 | CONFIRMADO |
| `current_page` nunca vira `0x53` | PROVÁVEL |
| A 3.1.2 não é consertável por patch pequeno | PROVÁVEL |

---

## Referências

- `tools/check_branch_targets.py`
- `docs/FIRMWARE_MAP.md` — faixas da FIRM e base XIP `0x00C00000`
- `docs/PLANO_EXTRAS.md` — o aviso, escrito antes e ignorado
- `analysis/ui/UI_TASK_ARCHITECTURE.md` — ViewTask
- `andromeda/MEMORY.md` — heap LVGL
