# O índice do Extras — um bug, quatro sintomas

> Levantado em 2026-09-20 por leitura do firmware de fábrica.
> **Causa confirmada. Conserto ESCRITO na Beta 14 (2026-09-21),
> aguardando teste no aparelho.**

---

## O mecanismo

Na tela inicial **de fábrica**, cada item passa o **próprio índice** como
parâmetro (`r2`) para a abertura da página. Confirmado em três pontos
onde o valor é explícito:

```asm
0x00D012D6   movs r3, #0x23 ; movs r2, #6     Bluetooth, índice 6
0x00D0123A   movs r3, #0x28 ; movs r2, #7     Configurar, índice 7
0x00D012DC   movs r3, #0x1E ; movs r2, #11    página 30, índice 11
```

Os itens que têm rotina de preparação **não escrevem `r2`**: eles
terminam saltando para `0x00D01036`, que faz

```asm
ldrh r2, [r4, #0xc]     ; lê o índice DA MENSAGEM
ldrh r1, [r4, #0xa]
ldrh r0, [r4, #8]
b    0xd011f2           ; pop e abre a página
```

Vindo da home, esse índice é o índice na home. **Vindo do nosso Extras,
é o índice no nosso menu.**

---

## A tabela de tradução — COMPLETA

| nosso índice | item | página | `sub` de fábrica | origem |
|---|---|---|---|---|
| 0 | Gravação | 24 | **2** | entrada 2 da TBH |
| 1 | Rádio | 26 | **3** | entrada 3 da TBH |
| 2 | Livro digital | 12 | **4** | entrada 4 da TBH |
| 3 | Imagem | 21 | **5** | entrada 5 da TBH |
| 4 | Bluetooth | 35 | **6** | `movs r2,#6` explícito |
| 5 | Pastas | 34 | **0** | `movs r2,#0` explícito em `0x00D00A90` |

Hoje o despacho passa **`0` para os seis**.

A TBH da home está em `0x00D00FBA` (`cmp r3, #0xb`, 12 entradas). Cada
entrada foi mapeada para a página que abre.

---

## O que isso explica

| item | `sub` passado | efeito |
|---|---|---|
| **Pastas** | 0, e o certo é 0 | **acerta por acidente** — abre bem; o defeito de voltar é outro |
| **Gravação, Rádio** | errado | funcionam mesmo assim — essas páginas ignoram o parâmetro |
| **Imagem, Livro digital** | errado | **a biblioteca não atualiza, a tela fica vazia** |
| **Bluetooth** | errado | **reinicia o aparelho** |

**Não são quatro defeitos. É um.**

---

## Por que o conserto da Beta 10 não resolveu

A Beta 10 forçou `r2=6` **na cauda do despacho** (`0x00DA6230`). Mas para
Imagem e Livro digital a cauda **nunca executa**: a preparação deles
salta direto para `0x00D01036` e abre a página de lá.

O conserto alcançava metade dos itens. E, por motivo ainda desconhecido,
**quebrou os seis** — ver `BLUETOOTH_REINICIA.md`.

---

## O conserto correto — ESCRITO na Beta 14

Reescrever o campo `[r4, #0xc]` da mensagem **antes** de chamar a
preparação, usando uma tabela de 6 bytes na área livre:

```asm
; logo após  mov r5, r2  em 0x00DA6206
ldr  r3, =tabela_sub
ldrb r3, [r3, r5]
strh r3, [r4, #0xc]
```

Assim vale para os **dois** caminhos — o que passa pela cauda e o que
salta de `0x00D01036`. É menor e mais central que o da Beta 10.

### Implementação (Beta 14, `tools/patch_extras_indice.py`)

Dois pontos, um campo:

1. **Inserção em `0x00DA6206`** (4 bytes: `mov r5,r2 ; movs r0,#0x53`
   viram `b.w 0x00DA6114`). A rotina na área livre reproduz os dois
   bytes e faz a reescrita: `ldr r3,[pc,#8] ; ldrb r3,[r3,r5] ;
   strh r3,[r4,#0xc] ; b.w 0x00DA620A`. Tabela `[2,3,4,5,6,0]` em
   `0x00DA6124`.
2. **Cauda em `0x00DA6230`**: `movs r2,#0` → `ldrh r2,[r4,#0xc]`.
   Dois bytes, in-place, sem salto.

Detalhes verificados na escrita:

- A cauda serve Gravação, Rádio (a preparação **retorna**), Bluetooth
  e Pastas. O trampolim serve Livro e Imagem. Os dois caminhos leem o
  campo corrigido.
- Nada entre `0x00DA6206` e as preparações lê `[r4,#0xc]` esperando o
  índice nosso: as tabelas A/B usam `r5`, que fica intacto.
- `r1` **não é propagado** pela primitiva `0x00D0DAE0` (só aparece no
  ramo de erro) — por isso o conserto não toca nele. O `movs r1,#2`
  da Beta 10 era inócuo e inútil.
- 28 bytes, um único setor (`0x1A6000`). `check_branch_targets` e
  `check_pilha` APROVADOS (baseline = Beta 12).

> ✅ **Beta 13 respondida em 2026-09-21: resultado (a).** Os seis itens
> abrem na B13 (relato do mantenedor: Livro abre e escaneia, Imagem abre
> vazia, BT abre e ativa). O salto e a área livre estão bons; o erro da
> Beta 10 estava na **lógica** (`cmp r5,#4` / `r1=2,r2=6`). **Conserto
> da tabela LIBERADO para escrita.**

---

## Confirmação em campo — Beta 12, 2026-09-21

Relato do mantenedor, sintoma por sintoma:

| observação | explicação |
|---|---|
| Livro digital, 1ª entrada: **fez a checagem e travou tudo** (não saía do Extras, não entrava em nada) | biblioteca vazia → ramo da varredura (`0x9A`) disparou; origem errada gravada → guarda `msg->page == página corrente` falha para sempre (mesmo padrão da 4.0). **Só reboot destrava** |
| Livro digital, após reboot: **arquivos apareceram** | o banco da varredura persiste no cartão; 2ª entrada abre direto com dados |
| Imagem: **"não tem nenhuma imagem"** | a varredura nunca disparou → banco vazio. Agravante: na home 5.x não há outro caminho para a Imagem — só o conserto destrava |
| Bluetooth: **reinicia ao entrar nas opções, mas ativa** | refina o sintoma documentado ("reinicia ao entrar"): ativar funciona, o crash é nas **opções** internas |

Todos os quatro são o mesmo bug do `sub`. O conserto da tabela também
resolve o travamento: com os argumentos certos, a origem gravada passa
a ser a correta.
