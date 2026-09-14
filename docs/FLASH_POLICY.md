# OpenPod — FLASH_POLICY

Política de gravação do projeto. **Decidida pelo mantenedor em 2026-09-12.**

> Este documento é **normativo**. Não é análise — é a regra que rege
> qualquer operação de gravação no GN-438 daqui em diante.

---

> ## ⚠️ REVISÃO — 2026-09-12 (Sessão 24)
>
> **A Regra 1 não é aplicável a este aparelho.** Não porque esteja
> errada, mas porque **não há como acionar o `sdupdate` nesta build**:
>
> - `set_flag_SD` tem **um único chamador** — a tabela de comandos do
>   console de debug (`0x049F80`). Nenhum caminho na interface.
> - O menu Configurações, enumerado item a item pelo usuário no
>   aparelho, **não tem** a opção de atualização por SD.
> - Um `update.up` na raiz do cartão não produziu efeito: o aparelho
>   ligou normalmente.
>
> A Regra 1 continua sendo a política **para aparelhos onde o gatilho
> exista**. Aqui, a gravação do V001 vai por `write_flash` em modo card
> reader — caminho já validado em hardware (Sessão 20: gravou, conferiu,
> apagou, restaurou, **0 bytes alterados**).
>
> **A propriedade de segurança do §2 é preservada por escolha
> explícita:** `tools/flash_v001.sh` grava a partir de `0x00D000` e
> nunca endereça o bootloader. Verificado: uma única chamada executável
> de `write_flash`, em `0xD000` e `0xCE000`.
>
> A Regra 2 (original como base de recuperação) permanece **integral**.

---

## 1. A política

### Regra 1 — O `update.up` é o único método de gravação normal

Toda alteração de firmware é entregue ao aparelho como pacote
`update.up` pelo cartão microSD. **`write_flash` por USB não é usado para
gravação normal.**

### Regra 2 — O firmware original é a base de recuperação

`firmware/ORIGINAL/GN438_original.bin` é preservado intocado
(SHA-256 `b7cd5eb9…4b36f`, permissão 444) e é a referência para qualquer
restauração.

---

## 2. Por que — a justificativa técnica

A razão **não** é que o `update.up` valide melhor. Ele valida pouco: sem
assinatura, e sem sequer conferir o CRC do payload antes de gravar
(`UPDATE_MECHANISM.md` §3, §4).

A razão é **estrutural e verificada por disassembly**:

> **O `sdupdate` apaga e grava exclusivamente a partir de `0x00D000`.
> A faixa `0x000000`–`0x00D000` — cabeçalho `HLKJ` e bootloader completo —
> nunca é tocada.**

O bootloader é o único caminho de recuperação que existe. O caminho SD o
mantém fora do alcance da operação **por construção**. O `write_flash` por
USB aceita qualquer endereço, inclusive `0x0`, e foi o que produziu os
bricks relatados na comunidade (`EXTERNAL_RESEARCH.md` §5.3).

| | SD update | USB write |
|---|---|---|
| Bootloader protegido | **sim, por construção** | **não** |
| Verify após escrita | sim (CRC por releitura) | não |
| Erase antes de write | sim | não necessariamente |
| Brick documentado | — | sim |

---

## 3. ⚠️ A exceção obrigatória — leia antes de aplicar a Regra 1

**A Regra 1 não pode valer para recuperação.** Isto não é uma brecha: é
uma consequência do mecanismo.

O `sdupdate` só roda se o flag do PMU (`reg 0x23`, bits [2:0] == 6)
estiver ligado. Quem liga esse flag é a **aplicação**, pela função
`0x00CF9D3C` (`UPDATE_MECHANISM.md` §2).

```text
FIRM corrompida
   ↓
a aplicação não inicia
   ↓
ninguém liga o flag do PMU
   ↓
o sdupdate NÃO PODE SER ACIONADO
   ↓
só resta o caminho USB
```

O bootloader tem um fallback automático — se a FIRM não carregar, ele cai
em `"update from pc"` (`0x00820626 → 0x00820512`), que é **exatamente** um
caminho de gravação por USB.

### Redação correta da política

> **Gravação normal: sempre por `update.up`/SD.**
> **USB reservado exclusivamente para recuperação**, e apenas a partir do
> original verificado.

Banir o USB por completo tornaria o projeto **menos** seguro, não mais:
seria abrir mão da única rede de proteção disponível.

---

## 4. Artefatos de recuperação — prontos antes de serem necessários

| Arquivo | SHA-256 | Uso |
|---|---|---|
| `firmware/ORIGINAL/GN438_original.bin` | `b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f` | fonte de verdade; restauração por USB |
| `firmware/WORKING/update_restore_original.up` | `82f0ae8c71a604f900c8d4aa235c046b91250f346e9623835daf8aecb29c35c8` | restauração pelo cartão, **se o aparelho ainda iniciar** |

O pacote de restauração foi gerado **antes** de qualquer teste, de
propósito: criar a rede de segurança depois do acidente não funciona.

Validação: 11 verificações OK, 0 falhas · CRC do payload `0x77F5` ·
payload byte a byte idêntico a `flash[0 : 0x1A3038]` do original.

> **Limitação registrada:** o pacote de restauração só serve enquanto o
> aparelho ainda iniciar a aplicação — porque é ela que liga o flag.
> Se a FIRM estiver corrompida, este arquivo **não ajuda**; só o USB.

---

## 5. Procedimento padrão de gravação

```text
 1. partir de firmware/ORIGINAL/GN438_original.bin   (nunca editá-lo)
 2. editar uma cópia de trabalho
 3. tools/rebuild_firmware.py      regenera todos os CRCs
 4. tools/validate_firmware.py     22+ verificações
 5. fwhelper <img> scan            validação independente de terceiros
 6. tools/make_update_up.py        gera o pacote
 7. conferir: pacote idêntico ao do fwhelper dump2fw
 8. copiar o .up para a raiz do cartão
 9. acionar a atualização pelo menu do aparelho
10. acompanhar pela UART, se disponível
```

Nenhuma etapa pode ser pulada. As etapas 5 e 7 são validações
**independentes** do nosso próprio código — é o que pega um erro
sistemático nas nossas ferramentas.

---

## 6. Proibições permanentes

```text
NUNCA  editar, sobrescrever ou regenerar firmware/ORIGINAL/GN438_original.bin
NUNCA  erase_flash de chip inteiro
NUNCA  write_flash por USB em endereço < 0x00D000, salvo restauração
       explicitamente autorizada a partir do original verificado
NUNCA  gravar sem ter confirmado antes que o aparelho enumera por USB
NUNCA  gravar um pacote que não tenha passado pelas etapas 3–7 do §5
```

---

## 7. Pré-requisito — ✅ ATENDIDO em 2026-09-12

> **A rede de segurança foi exercitada e funciona.**
>
> ```text
> lsusb           Bus 003 Device 067: ID 301a:2801 SmartlinkTechnology
> flash_id        0x14851485
> read_flash      dump_flash: 0x00000000, target: 0x200000, read: 0x200000
> ```
>
> Conferência por região contra o original: **todas as regiões críticas
> idênticas**; só a `PSMP` divergiu, o que é legítimo e agora está
> explicado em `docs/PSMP_FORMAT.md`.
>
> Evidência: `firmware/READBACK/GN438_readback_2026-09-12.bin` (444) e o
> log da sessão.
>
> **Isto prova três coisas:** o aparelho enumera e responde por USB; a
> flash pode ser lida por completo; e o `GN438_original.bin` preservado é
> **cópia fiel do aparelho**, não uma suposição.
>
> ### ✅ E a ESCRITA também foi validada — 2026-09-12
>
> A leitura sozinha não bastava: a recuperação exige **escrita**. Um teste
> controlado no setor `0x1D0000` (área livre) confirmou que
> `write_flash` e `erase_flash` funcionam e que a ferramenta respeita o
> endereço. **Zero bytes alterados em toda a flash ao fim do teste.**
>
> Detalhes em `docs/WRITE_TEST_RESULT.md`.
>
> **Com isso, o único risco irrecuperável do projeto deixou de existir.**

### Texto original, mantido para referência

**A rede de segurança nunca foi exercitada.** O modo `"update from pc"`
existe no código, mas não sabemos se enumera na prática —
`UPDATE_MECHANISM.md` §10, incógnita 5.

> Antes da primeira gravação: conectar por USB, confirmar a enumeração e
> fazer um `read_flash` de teste. **Leitura pura.** Se isso não funcionar,
> **não gravar** — a Regra 2 depende de o USB responder, e a §3 mostra que
> em caso de FIRM corrompida ele é o único caminho.

**Procedimento completo:** `docs/RECOVERY_CHECK.md` — ~10 minutos, sem
risco. Ferramenta de conferência: `tools/verify_device_readback.py`.

---

## 8. Classificação

| Afirmação | Classe |
|---|---|
| O `sdupdate` não toca `0x0`–`0xD000` | **CONFIRMADO** |
| Por isso o caminho SD é mais seguro que o USB | **CONFIRMADO** |
| O `sdupdate` exige o flag do PMU, ligado pela aplicação | **CONFIRMADO** |
| Logo, FIRM corrompida ⇒ SD indisponível para recuperação | **CONFIRMADO** |
| O boot cai em `"update from pc"` se a FIRM não carregar | **CONFIRMADO** |
| Esse modo enumera de fato por USB | **NÃO DETERMINADO** |
| O pacote de restauração serve com o aparelho funcionando | **PROVÁVEL** |
