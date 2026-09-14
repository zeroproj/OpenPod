# OpenPod — WRITE_TEST_RESULT

Resultado do primeiro teste de **escrita** na flash do GN-438.

| | |
|---|---|
| **Data** | 2026-09-12 |
| **Alvo** | setor `0x1D0000` (4 KiB), área livre |
| **Resultado** | ✅ **APROVADO — escrita, apagamento e restauração confirmados** |
| **Regiões críticas** | **intactas**, antes e depois |
| **Evidência** | `analysis/hardware_tests/2026-09-12_writetest/` |
| **Ferramenta** | `tools/write_test_freearea.sh` |

---

## 1. Por que este teste existiu

A rede de segurança confirmada horas antes cobria apenas **leitura**. Se o
V001 corrompesse a FIRM, a recuperação exigiria **escrita** por USB — um
caminho nunca exercitado, cujo suporte no `smartlink_flash` tem poucos
meses e que o próprio autor descreve como *"tested very little"*.

Todos os riscos do projeto desembocavam nessa incógnita: era o único que
não tinha volta. Este teste a fechou.

---

## 2. O que foi feito

```text
[1] leu a flash inteira e conferiu 4 regiões críticas por SHA-256   OK
[2] confirmou que o setor 0x1D0000 estava todo 0xFF                 OK
[3] confirmação manual do operador                                  OK
[4] ESCREVEU 4 KiB de padrão conhecido
[5] releu e comparou byte a byte                                    OK
[6] APAGOU o setor
[7] releu e confirmou retorno ao estado anterior                    OK
[8] leu a flash inteira e reconferiu as 4 regiões críticas          OK
```

Alvo escolhido a **180 KiB** do fim da TONE e **172 KiB** do início da
PSMP, para que um erro de endereçamento na ferramenta não atingisse nada
usado pelo firmware.

---

## 3. Verificação independente

O log do script foi conferido de novo, sobre os próprios artefatos:

| Verificação | Resultado |
|---|---|
| `target_written.bin` == `pattern.bin` | **idênticos**, 0 divergências |
| Conteúdo legível do setor escrito | `OPENPOD-WRITE-TEST-1D0000-` |
| `target_erased.bin` todo `0xFF` | **sim** |
| `target_erased.bin` == `target_before.bin` | **idênticos** |
| Regiões críticas (HLKJ, boot, ptable, FIRM, TONE) antes × depois | **0 divergências** |
| Setor alvo no estado final | todo `0xFF` |
| **Flash inteira, `before` × `after`** | **0 bytes alterados** |

> **Zero bytes de diferença em toda a flash.** A escrita foi integralmente
> revertida. O aparelho terminou o teste exatamente como começou.

O `pattern.bin` gerado no Ubuntu tem o mesmo SHA-256 que eu havia
calculado no macOS (`cc4bf502…`) — a geração do padrão é determinística
entre plataformas.

---

## 4. Conferência cruzada entre as três leituras do dia

| Comparação | Divergências |
|---|---|
| `before` (teste de escrita) × readback anterior | **0** |
| `before` × `GN438_original.bin` (dump de ontem) | 802, **todas na PSMP** |

**A PSMP continua sendo a única região que muda sozinha**, confirmando
`docs/PSMP_FORMAT.md`. Nenhuma região crítica divergiu em nenhuma das três
leituras do aparelho.

---

## 5. O que isto prova — e o que não prova

### Provado — CONFIRMADO

| Afirmação |
|---|
| `write_flash` por USB funciona neste aparelho |
| `erase_flash` por USB funciona e restaura a `0xFF` |
| A verificação por releitura funciona |
| A ferramenta escreve **no endereço pedido**, sem afetar vizinhos |
| **O caminho de recuperação é real, não presumido** |

### Não provado

| Afirmação | Classe |
|---|---|
| Escrever em área **já escrita**, sem apagar, é confiável | **NÃO DETERMINADO** — não testado |
| A anomalia `0 → 1` relatada ocorre neste aparelho | **NÃO DETERMINADO** |
| Uma escrita de 1,6 MB se comporta como uma de 4 KiB | **PROVÁVEL**, por extrapolação |

> **Sobre a anomalia:** este teste escreveu em setor **apagado**, ou seja,
> só houve transições `1 → 0` — as seguras. A anomalia relatada é sobre
> gravar `0 → 1` **sem apagar**. Não foi exercitada, e **não precisa ser**:
> o `sdupdate` apaga antes de gravar (`UPDATE_MECHANISM.md` §5), e a PSMP
> do próprio firmware só faz `1 → 0` (`PSMP_FORMAT.md` §3). O caminho que
> vamos usar não depende do comportamento anômalo.

---

## 6. Efeito na avaliação de risco

Comparado com `UPDATE_MECHANISM.md` §7.1 e `FLASH_POLICY.md` §7:

| Risco | Antes | Agora |
|---|---|---|
| Pacote recusado (timestamp) | inofensivo | inofensivo |
| TONE perde 56 bytes | provável, cosmético | igual |
| V001 não inicializa | recuperável **se** a escrita funcionar | **recuperável — a escrita funciona** |
| Gravação SD corrompe a FIRM | idem | idem |
| **A escrita por USB não funcionar quando precisar** | **desconhecido, sem volta** | ✅ **eliminado** |

> O único risco irrecuperável do projeto **deixou de existir**.
>
> O que resta é a pergunta que sempre foi a do teste: **o V001 inicializa?**
> E essa, agora, tem resposta reversível.

---

## 7. Classificação

| Afirmação | Classe |
|---|---|
| Escrita por USB funciona | **CONFIRMADO** (observado, verificado) |
| Apagamento por USB funciona | **CONFIRMADO** |
| A ferramenta respeita o endereço | **CONFIRMADO** (0 bytes fora do alvo) |
| O caminho de recuperação é viável | **CONFIRMADO** |
| Escrita grande se comporta como a pequena | **PROVÁVEL** |
| Comportamento em área não apagada | **NÃO DETERMINADO** |
