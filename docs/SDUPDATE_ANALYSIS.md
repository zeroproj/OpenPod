# OpenPod — SDUPDATE_ANALYSIS

Engenharia reversa da rotina `boot sdupdate` do bootloader do GN-438.

| | |
|---|---|
| **Data** | 2026-09-12 |
| **Alvo** | bootloader, `firmware/WORKING/GN438_analysis.bin` |
| **Método** | disassembly ARM Thumb-2 (capstone 5.0.7) |
| **Hardware** | **nenhuma operação** — análise estática apenas |
| **Pacote de atualização** | **NÃO criado** — o formato ainda não está 100 % comprovado (§9) |

### Convenção de confiança

- **CONFIRMADO** — lido diretamente no disassembly, instrução por instrução.
- **PROVÁVEL** — inferido de assinaturas de chamada ou de literais, coerente
  com o resto, mas sem prova direta.
- **HIPÓTESE** — explicação plausível ainda não comprovada.
- **NÃO RESOLVIDO** — investigado e não determinado.

### Mapeamento de endereços usado

```text
bootloader:  addr = offset_no_arquivo + 0x0081FB60
             (payload em 0x60 carregado para 0x0081FBC0)
```

Ferramenta: `tools/disasm.py` (criada nesta sessão).

---

## 1. Resumo executivo

| Pergunta | Resposta | Confiança |
|---|---|---|
| Nome do arquivo | **`update.up`**, na raiz do cartão | CONFIRMADO |
| Caminho literal | `0:\update.up` | CONFIRMADO |
| Filesystem | FatFs, `f_mount` → `f_stat` → `f_open` modo 1 (leitura) | CONFIRMADO |
| Magic do cabeçalho | `"CONFI"` nos primeiros **5** bytes | CONFIRMADO |
| Marca do chip | `"SL6801"` no offset **0x16** | CONFIRMADO |
| Campo em +0x06 | `codeOffsetInByte` (u32, **desalinhado**) | CONFIRMADO |
| Verificação de assinatura | **NÃO EXISTE** | CONFIRMADO |
| Verificação de CRC do pacote | **NÃO EXISTE antes de gravar** | CONFIRMADO |
| CRC existente | comparação **pós-gravação** arquivo × releitura da flash | CONFIRMADO |
| Rejeição por timestamp | **sim** — rejeita se o timestamp for **IGUAL** ao instalado | CONFIRMADO |
| Área gravada | de `parition_start` (0x0000D000) até o fim | CONFIRMADO |
| Bootloader é sobrescrito? | **NÃO** — `0x0`–`0xD000` nunca é apagado nem gravado | CONFIRMADO |
| Como é disparado | **flag no PMU reg `0x23`, bits[2:0] == 6** | CONFIRMED |

> **O achado mais importante para o OpenPod:** o bootloader **rejeita** um
> pacote cujo `timestamp` seja igual ao do firmware já instalado. Um rebuild
> byte-a-byte do original — exatamente o que a Fase 0.5 produziu — seria
> **recusado** com código `0xFC`. O campo de timestamp **precisa** ser
> alterado. Ver §6.

---

## 2. Localização no binário

| Item | Offset | Endereço |
|---|---|---|
| Função central de sdupdate | `0x07CF0` | `0x00827850` |
| Função que abre `update.up` | `0x03FA8` | `0x00823B08` |
| Leitura de flash `flash_read(dst, addr, len)` | `0x00F04` | `0x00820A64` |
| Acumulador de CRC `crc_acc(crc, buf, len)` | `0x02424` | `0x00821F84` |
| Gravação de página de flash | `0x0249C` | `0x00821FFC` |
| Apagamento de setor | `0x02580` | `0x008220E0` |

A identificação de `0x00820A64` como **leitura de flash** é CONFIRMADA pelo
uso: a mesma função é usada para reler da flash os dados recém-gravados no
laço de verificação (§7).

---

## 3. Abertura do arquivo — CONFIRMADO

Disassembly em `0x00823B08`:

```asm
00823B30  bl   #0x826ab8              ; f_mount(0)
00823B36  cbz  r0, #0x823b52          ; 0 = sucesso
00823B38  ldr  r0, ... "f_mount err(%d)"
00823B52  ldr  r0, ... "f_mount success."
00823B58  mov.w r0, #0x120            ; aloca 0x120 bytes (FILINFO)
00823B64  ldr  r0, ... "0:\update.up"
00823B66  bl   #0x8263e2              ; f_stat("0:\update.up", &finfo)
00823B6C  cbnz r0, #0x823bb8          ; != 0 -> não encontrado
00823B76  ldr  r0, ... "file name:%s  altner name:%s"
00823B82  movs r2, #1                 ; modo = 1  (FA_READ)
00823B84  ldr  r1, ... "0:\update.up"
00823B88  bl   #0x826464              ; f_open(fil, path, FA_READ)
00823B8E  ldr  r0, ... "f_open failed."
00823B9E  ldr  r0, ... "Not find file!"
```

**Fatos:**

- o caminho é o literal `0:\update.up` — **raiz** do volume 0;
- `f_open` usa modo `1` = **somente leitura**: o bootloader nunca escreve
  no cartão;
- antes de abrir, faz `f_stat` e imprime nome longo e nome curto 8.3;
- o cartão precisa montar (`f_mount`) — FAT32 ou exFAT, conforme
  `docs/FIRMWARE_ANALYSIS.md` §14.

> A extensão `.up` e o nome são fixos. Não há varredura de diretório nem
> nome alternativo.

---

## 4. Cabeçalho do pacote — CONFIRMADO

O bootloader lê os primeiros **0x200 bytes** do arquivo e valida dois
campos.

```asm
0082789C  blx  r6                     ; f_read(fil, buf, 0x200, &br)
0082789E  movs r2, #5                 ; <-- 5 bytes
008278A0  ldr  r1, ... "CONFIG"
008278A2  mov  r0, r5                 ; buf + 0
008278A4  bl   #0xc54                 ; memcmp(buf, "CONFIG", 5)
008278AA  bne.w #0x827bb8             ; falha -> retorna 0xFE
008278AE  ldr  r0, ... "boot sdupdate--->header pass"

008278B4  movs r2, #6                 ; <-- 6 bytes
008278B6  ldr  r1, ... "SL6801"
008278B8  add.w r0, r5, #0x16         ; buf + 0x16
008278BC  bl   #0xc54                 ; memcmp(buf+0x16, "SL6801", 6)
008278C4  bne.w #0x827bca             ; falha -> retorna 0xFA
008278C8  ldr  r0, ... "boot sdupdate--->mark pass"

008278EA  ldr.w sb, [r5, #6]          ; codeOffsetInByte = u32 em buf+0x06
```

### Estrutura conhecida do cabeçalho

| Offset | Tam. | Campo | Valor exigido | Status |
|---|---|---|---|---|
| `0x00` | 5 | magic | `"CONFI"` | CONFIRMADO |
| `0x05` | 1 | — | **não verificado** | CONFIRMADO |
| `0x06` | 4 | `codeOffsetInByte` (u32 LE, desalinhado) | qualquer | CONFIRMADO |
| `0x0A` | 12 | — | não lido aqui | NÃO RESOLVIDO |
| `0x16` | 6 | marca do chip | `"SL6801"` | CONFIRMADO |
| `0x1C`… | — | — | não lido aqui | NÃO RESOLVIDO |

### Duas observações precisas

**(a) O magic é comparado com 5 bytes, não 6.** O literal é `"CONFIG"`
(6 caracteres), mas `r2 = 5`. O sexto byte (`'G'`) **não é verificado**.
Isso é o que o código faz; não é interpretação.

**(b) `codeOffsetInByte` é lido em offset ímpar** (`ldr.w sb, [r5, #6]`).
Leitura desalinhada de 32 bits — permitida em ARMv7-M. Confirma que o
cabeçalho **não** é uma struct alinhada trivial.

> A string `"SL6801"` em `0x0000C184` — marcada como indício na Fase 0 —
> tem agora **função conhecida**: é a marca de compatibilidade de chip
> exigida no pacote de atualização. O bootloader deste aparelho só aceita
> pacotes marcados `SL6801`. Isso reforça a identificação do SoC, mas
> continua sem inspecionar o silício.

---

## 5. Leitura dos parâmetros de destino — CONFIRMADO (com uma lacuna)

```asm
008278E8  movs r1, #0x20
008278EE  bl   #0x820a64              ; flash_read(&parition_start, 0x20, 4)
008278F4  ldr  r0, ... "parition_start= %x"
00827904  ldr  r3, [sp, #0x18]
00827906  cbnz r3, #0x82790e
00827908  mov.w r3, #0x3000           ; fallback se for 0
0082790C  str  r3, [sp, #0x18]
```

`parition_start` vem de **`flash[0x20]`** — isto é, o campo `+0x20` do
cabeçalho `HLKJ`. Na imagem atual esse campo vale **`0x0000D000`**, que é
exatamente o offset da tabela de partições.

> Isso **confirma por disassembly** a inferência da Fase 0 de que o campo
> `+0x20` do cabeçalho `HLKJ` é o offset da tabela de partições. Se o campo
> for zero, o bootloader assume `0x3000`.

Em seguida:

```asm
0082791A  blx  r1                     ; f_lseek(fil, parition_start + codeOffsetInByte)
00827930  blx  r6                     ; f_read(fil, buf, 0x80, &br)
00827934  ldr  r2, [r5, #0x10]        ; ponteiro interno = buf[0x10]
0082793C  blx  r1                     ; f_lseek(fil, buf[0x10])
0082794A  blx  r6                     ; f_read(fil, buf, 0x80, &br)
0082794E  ldr  r6, [r5, #4]           ; fileStamp = buf[0x04]  <-- timestamp do novo firmware
00827956  bl   #0x820a64              ; flash_read(&A, parition_start+0x10, 4)
00827962  bl   #0x820a64              ; flash_read(&old_len, parition_start+0x18, 4)
0082796E  bl   #0x820a64              ; flash_read(&cur_stamp, A+4, 4)
```

**O que está CONFIRMADO:**

- o pacote é percorrido com `f_lseek`/`f_read`, em blocos de 0x80 bytes;
- o segundo bloco lido é um **cabeçalho de imagem** cujo campo `+0x04` é o
  `fileStamp` — o mesmo offset do `timestamp` no cabeçalho `FIRM`
  (`docs/FIRMWARE_MAP.md` §4);
- `old firmwareStartLen` vem de `flash[parition_start + 0x18]`. Na imagem
  atual isso é `0xD018` = **`0x00192570`**, exatamente o tamanho da
  partição FIRM. A correspondência é exata e sustenta a leitura.

**O que NÃO está resolvido:**

A terceira leitura usa `flash[parition_start + 0x10]` como se fosse um
**ponteiro**, e lê `+4` a partir dele. Na imagem atual `flash[0xD010]`
contém o nome `"FIRM"` (`0x4D524946`), que não é endereço válido.

Ou o layout de entrada da tabela assumido pelo bootloader difere do
observado, ou `flash_read` trata endereços fora de faixa de modo não
determinado nesta análise. **NÃO RESOLVIDO** — resolver exige rastrear
`0x00820A64` até os registradores SPI, ou observar em execução.

> Isto **não** invalida a conclusão do §6: a *semântica da comparação*
> está confirmada por disassembly, independentemente de qual endereço
> exato fornece o valor comparado.

---

## 6. Decisão de aceitar ou rejeitar — CONFIRMADO

Este é o trecho decisivo:

```asm
00827984  ldr  r3, [sp, #0x1c]        ; timestamp ATUAL (lido da flash)
00827986  cmp  r3, r6                 ; r6 = fileStamp (do pacote)
00827988  beq.w #0x827bce             ; IGUAIS -> rejeita
0082798C  ldr  r0, ... "boot sdupdate--->time is not same"
0082798E  bl   print                  ; DIFERENTES -> prossegue
...
00827BCE  movs r6, #0xfc              ; código de retorno 0xFC
00827BD0  b    #0x827bba              ; fecha arquivo, libera buffer, retorna
```

### A semântica é o inverso do que a string sugere

A mensagem `"time is not same"` é impressa no caminho que **prossegue** com
a atualização. O caminho que **aborta** (`beq`) é o dos timestamps
**iguais**, e não imprime nada.

```text
fileStamp == timestamp instalado   ->  ABORTA, retorna 0xFC
fileStamp != timestamp instalado   ->  imprime "time is not same" e GRAVA
```

Ler apenas as strings levaria à conclusão oposta. Só o disassembly resolve.

### Códigos de retorno — CONFIRMADO

| Código | Origem | Significado |
|---|---|---|
| `0x00` | fim normal | gravação concluída |
| `0xFA` | `0x00827BCA` | marca do chip ≠ `"SL6801"` |
| `0xFC` | `0x00827BCE` | **timestamp igual ao instalado** |
| `0xFE` | `0x00827BB8` | magic ≠ `"CONFI"` |
| `0xFF` | `0x0082786C` | falha de alocação (`fil` ou `updateBuff` nulo) |

### Consequência direta para o OpenPod

> ⚠️ **CORRIGIDO em 2026-09-12.** O parágrafo abaixo era afirmativo demais.
> A análise byte a byte contra o `fwhelper`
> (`docs/UPDATE_UP_REFERENCE.md` §12.3) mostrou que **a origem dos dois
> valores comparados não está resolvida** — sob a leitura mais provável,
> ambos são espúrios, e a verificação talvez **nunca dispare**.
>
> Continua **CONFIRMADO**: a estrutura do desvio (`beq` → `0xFC`).
> Passa a **NÃO RESOLVIDO**: se ele dispara, e sobre quais valores.
> A previsão abaixo, portanto, **não se sustenta**.

~~Um pacote construído a partir de um rebuild byte-a-byte do firmware
original **seria rejeitado com `0xFC`**, porque o `timestamp`
(`0x8F20F1C2`) seria idêntico ao instalado.~~

> Para que um firmware OpenPod seja aceito, o campo de timestamp do
> cabeçalho da imagem **tem de ser alterado**. Isso não é uma proteção
> criptográfica — é um controle anti-regravação redundante. Mas é
> **bloqueante**, e teria custado um ciclo de depuração confuso se
> descoberto só na prática.

---

## 7. Apagamento, gravação e verificação — CONFIRMADO

### Comparação de tamanho

```asm
008279A0  ldr  r3, [sp, #0x24]        ; old firmwareStartLen
008279A2  cmp  r3, r8                 ; r8 = tamanho do arquivo
008279A4  bhs  #0x827a54              ; old >= arquivo -> "totalDataLength<=firmwareStartLen"
008279A6  ldr  r0, ... "totalDataLength>firmwareStartLen"
```

Ambos os caminhos prosseguem; a diferença é apenas qual comprimento é
usado para dimensionar o apagamento.

### Apagamento

```asm
008279AC  ldr  r6, [sp, #0x18]        ; parition_start
008279AE  sub.w r6, r8, r6            ; tamanho - parition_start
008279B2  lsrs r6, r6, #0xc           ; / 4096
008279B4  adds r6, #1                 ; + 1 setor
...
00827A5E  ldr  r0, ... "erase %d / %d"
00827A68  ldr  r0, [sp, #0x18]
00827A6A  movs r1, #1
00827A6C  add.w r0, r0, r7, lsl #12   ; parition_start + n*4096
00827A70  bl   #0x8220e0              ; erase_sector(addr, 1)
```

**Setores de 4 KiB, a partir de `parition_start`**, quantidade
`((tamanho − parition_start) >> 12) + 1`.

### Gravação

```asm
00827AFE  blx  r6                     ; f_read(fil, buf, 0x200, &br)
00827B0A  bl   #0x821f84              ; crc_arquivo = crc_acc(crc_arquivo, buf, 0x200)
00827B20  mov.w r2, #0x100
00827B2C  bl   #0x821ffc              ; flash_write(buf, parition_start + n*512, 0x100, ...)
00827B3A  add.w r1, r1, #0x100
00827B4? bl   #0x821ffc               ; segunda página de 256 bytes
```

Lê **512 bytes** do arquivo por vez e grava como **duas páginas de 256
bytes**. Acumula CRC do que veio do arquivo.

### Verificação pós-gravação

```asm
00827B98  ldr  r1, [sp, #0x18]
00827B9E  add.w r1, r1, r3, lsl #9    ; parition_start + n*512
00827BA4  bl   #0x820a64              ; flash_read(buf, addr, 0x200)   <- relê da FLASH
00827BB0  bl   #0x821f84              ; crc_flash = crc_acc(crc_flash, buf, 0x200)
...
00827A30  ldr  r0, ... "crc cmp %x %x"
00827A36  cmp  r8, r6                 ; crc_arquivo vs crc_flash
00827A38  bne  #0x827a50              ; divergiu -> termina sem a etapa final
00827A42  vldr s0, ...                ; progresso 100%
00827A48  mov.w r0, #0x3e8            ; 1000
00827A4C  bl   #0x822f7c
```

Ambos os acumuladores são inicializados com **`0xFFFF`**
(`movw r8, #0xffff`, `movw r6, #0xffff`) — consistente com o
**CRC-16/CCITT-FALSE** já identificado no resto do firmware (PROVÁVEL:
não foi desmontado `0x00821F84` para confirmar o polinômio).

> **Natureza do CRC:** compara o que foi lido do **arquivo** com o que foi
> relido da **flash**. É **verificação de gravação**, não validação do
> pacote. Um pacote corrompido no cartão seria gravado tal como está e
> passaria — o CRC só detecta falha de escrita.

---

## 8. Recuperação — CONFIRMADO

Tanto o apagamento quanto a gravação começam em **`parition_start`**
(`0x0000D000` nesta imagem) e seguem para cima.

**A faixa `0x00000000`–`0x0000D000` nunca é tocada.** Ela contém:

- o cabeçalho `HLKJ`;
- o payload inteiro do bootloader (`0x60`–`0xC94C`).

Portanto, **o bootloader sobrevive a uma atualização malsucedida**. Se a
gravação falhar no meio, o aparelho fica sem aplicação válida, mas o
bootloader continua capaz de montar o cartão e reprocessar `update.up`.

> Este é o mecanismo de recuperação do dispositivo, e reduz muito o risco
> de brick **desde que** a atualização seja feita por este caminho. Ele
> **não** protege contra gravação direta por USB (`write_flash`), que pode
> atingir o bootloader.

**Ressalva:** que o bootloader realmente reprocesse `update.up` depois de
uma falha depende do mecanismo de disparo, que **não foi determinado**
(§9). O raciocínio acima é **PROVÁVEL**, não CONFIRMADO.

---

## 9. Lacunas — o que impede criar um pacote agora

Conforme instruído, **nenhum pacote de atualização foi criado**. O formato
não está completamente comprovado. Faltam:

| # | Lacuna | Por que bloqueia |
|---|---|---|
| 1 | **Como o sdupdate é disparado** | Nenhum `bl` direto nem ponteiro em pool literal aponta para `0x00827850`. A chamada é indireta. Sem isso não se sabe como fazer o aparelho entrar em atualização. Pistas: `HAL_pmu_sd_update_flag_set %d`, `is_pmu_pc_update_flag_set %x`, `update set sd and restart ...` (esta última na FIRM, offset `0x0004A7A8`) sugerem um flag no PMU gravado pela aplicação antes de reiniciar. |
| 2 | **Bytes 0x0A–0x15 e 0x1C–0x1FF do cabeçalho** | Não são lidos por esta função. Podem ser exigidos por outra etapa. |
| 3 | **Onde `codeOffsetInByte` posiciona o conteúdo** | Confirmado que existe e é usado em `f_lseek`, mas o valor correto para um pacote novo não é derivável sem um pacote de exemplo. |
| 4 | **O ponteiro de `parition_start+0x10`** (§5) | O timestamp instalado é lido através dele. Sem entender, não dá para prever com certeza o valor comparado. |
| 5 | **Polinômio de `0x00821F84`** | PROVÁVEL CCITT-FALSE pelo init `0xFFFF`, não confirmado. |
| 6 | **Um pacote `update.up` real de referência** | Resolveria 2, 3 e 4 de uma vez. |

> **Recomendação:** o caminho mais rápido e seguro para fechar estas lacunas
> é obter um `update.up` oficial de qualquer aparelho da família YP3/SL6801
> e compará-lo com este mapa. Isso é muito mais barato do que desmontar o
> restante, e não envolve risco algum para o aparelho.

---

## 10. Mapa do formato, até onde está provado

```text
update.up  (raiz do cartão SD, FAT32/exFAT)
│
├─ 0x0000  "CONFI"              5 bytes verificados      CONFIRMADO
├─ 0x0005  ?                    não verificado           CONFIRMADO
├─ 0x0006  codeOffsetInByte     u32 LE desalinhado       CONFIRMADO
├─ 0x000A  ?                    NÃO RESOLVIDO
├─ 0x0016  "SL6801"             6 bytes verificados      CONFIRMADO
├─ 0x001C  ?                    NÃO RESOLVIDO
│
├─ (parition_start + codeOffsetInByte)
│      └─ bloco de 0x80 bytes
│           └─ +0x10 : ponteiro para o próximo cabeçalho  CONFIRMADO
│
├─ (valor do ponteiro acima)
│      └─ bloco de 0x80 bytes
│           └─ +0x04 : fileStamp (timestamp)              CONFIRMADO
│
└─ (parition_start + codeOffsetInByte) em diante
       └─ imagem gravada na flash a partir de parition_start
```

---

## 11. Regras que continuam valendo

```text
Nenhuma gravação no GN-438 foi feita nem está autorizada.
Nenhum pacote update.up foi criado.
firmware/ORIGINAL/GN438_original.bin permanece intocado.

Antes de qualquer gravação, ainda é necessário:
  1. determinar como o sdupdate é disparado;
  2. obter ou comprovar o formato completo do pacote;
  3. confirmar que o timestamp foi alterado (senão: rejeição 0xFC).
```

---

## 12. Referências cruzadas

| Assunto | Documento |
|---|---|
| Layout da flash, cabeçalhos, CRC | `docs/FIRMWARE_MAP.md` |
| Análise geral do firmware | `docs/FIRMWARE_ANALYSIS.md` |
| Round-trip do rebuild | `docs/REBUILD_VALIDATION.md` |
| Obtenção do firmware | `docs/FIRMWARE_DUMP.md` |
| Ferramenta de disassembly | `tools/disasm.py` |


---

# PARTE II — Cadeia de acionamento (2026-09-12)

## 13. ⚠️ Correção: a chamada NÃO é indireta

A §9 deste documento afirmava que nenhum `bl` direto aponta para
`0x00827850` e que a chamada seria indireta.

**Errado.** Existe um `bl` direto, em **`0x00823CCC`**.

A varredura que usei percorria o bootloader linearmente a partir de um
offset fixo; ela **dessincroniza** ao atravessar pools literais e nunca
chegou àquela instrução. Foi um **falso negativo do método**, não uma
propriedade do código.

> Lição: desassemblagem linear de um binário sem símbolos produz falsos
> negativos. Conclusões de ausência exigem outro método — varredura a
> partir de cada alinhamento, ou busca por padrão de bits do `bl`.

---

## 14. Cadeia completa de acionamento — CONFIRMED

```text
[1] aplicação (FIRM) quer atualizar
       HAL_pmu_sd_update_flag_set(1)      0x0082844C
       grava no registrador 0x23 do PMU   (persiste no reset)
       strings correspondentes na FIRM:
         "-update set sd and restart ...."   0x0004A7A8
         "-update set pc and restart ...."   0x0004A786
              ↓  reset
[2] bootloader — main em 0x008204EC
       bl 0x00827C02  -> flag de PC?   -> caminho "update from pc"
       bl 0x00827C0A  -> flag de SD?
              ↓ (flag de SD ligada)
[3] bl 0x00827BFC     limpa a flag  (evita laço infinito)
    bl 0x00820418     inicialização de hardware
              ↓
[4] "---------------_hardware_init_begin---------------"
    ... init de clock, LCD, SD ...
              ↓
[5] exibe "Finding file..."          0x00829CBC
    delay 1000 ms
              ↓
[6] bl 0x00823CA0    monta a vtable de I/O e chama o núcleo
       └─ bl 0x00827850   ← SDUPDATE  (§2–§8)
              ↓
[7] exibe "Update finish!"           0x00829CEE
    delay 1000 ms, desliga
```

### Leitura da flag — CONFIRMED

```asm
008284C0  push {r3, lr}
008284C2  bl   #0x828490        ; lê registrador 0x23 do PMU
008284C6  and  r0, r0, #7       ; bits [2:0]
008284CA  subs r3, r0, #6
008284CC  rsbs r0, r3, #0
008284CE  adcs r0, r3           ; retorna (valor & 7) == 6
```

**A flag de atualização por SD é: PMU registrador `0x23`, bits [2:0] = `6`.**

Escrita em `0x0082844C` (`HAL_pmu_sd_update_flag_set`), que usa
`0x00820BD0` (ler registrador do PMU) e `0x00820B68` (escrever).

> **Consequência para o OpenPod:** o `sdupdate` **não** é acionado por
> combinação de teclas nem por presença do arquivo. É acionado por um
> **flag persistente gravado pela própria aplicação** antes de um reset.
> Sem a aplicação cooperar — ou sem gravar o PMU de outra forma — o
> bootloader nunca procura `update.up`.

---

## 15. Tabela de operações de arquivo — CONFIRMED

`0x00823CA0` monta em pilha uma tabela de 8 ponteiros e a passa ao núcleo.
Isso explica todas as chamadas `[r4]`/`[r3+N]` da §2–§7.

| Slot | Endereço | Função | Evidência |
|---|---|---|---|
| `+0x00` | `0x00823B09` | **abrir** | `f_mount` → `f_stat("0:\update.up")` → `f_open` modo 1 |
| `+0x04` | `0x00823BFD` | fechar | — |
| `+0x08` | `0x00823C11` | **ler** | string `"sd_read result = %d!"` |
| `+0x0C` | `0x00823C29` | **posicionar** | string `"sd_seek result = %d"` |
| `+0x10` | `0x00823A75` | **tamanho** | `ldrd r0, r1, [r0, #0x10]` — 64 bits do objeto FatFs |
| `+0x14` | `0x00823C41` | — | NÃO RESOLVIDO |
| `+0x18` | `0x00823A7D` | **progresso** | recebe `float` em `s0`; usa `"0123456789Update...100%"` |
| `+0x1C` | `0x00823C45` | finalizar / erro | string `"Err num %d"` |

### Detalhe de chamada — CONFIRMED

`lseek` recebe o offset como **inteiro de 64 bits em `r2:r3`**, com `r1`
usado apenas como preenchimento de alinhamento AAPCS:

```asm
00827910  ldr  r2, [sp, #0x18]   ; offset baixo
00827912  ldr  r1, [r3, #0xc]    ; ponteiro da função (ocupa r1)
00827914  add  r2, sb
00827916  movs r3, #0            ; offset alto = 0
0082791A  blx  r1
```

---

## 16. Caminho alternativo: falha no boot normal — CONFIRMED

```asm
00820610  "boot--->load firmware disp."
00820616  bl 0x00820418        ; init de hardware
0082061A  bl 0x00820DA8
0082061E  bl 0x00820470        ; carrega a FIRM
00820622  cmp r0, #0
00820624  bne 0x0082060A       ; sucesso -> segue
00820626  b   0x00820512       ; FALHA   -> "update from pc"
```

Se o carregamento normal da FIRM falhar, o bootloader cai no modo de
**atualização por PC**. É uma segunda rede de proteção, independente do
cartão SD.

> Combinado com a §8 (a faixa `0x0`–`0xD000` nunca é gravada pelo
> `sdupdate`), isso significa que uma FIRM corrompida **por esse caminho**
> leva o aparelho ao modo de recuperação por USB, não a um tijolo.
> Continua valendo o aviso de `EXTERNAL_RESEARCH.md` §5.3 sobre gravação
> direta por USB atingindo o bootloader.

---

## 17. O "check de timestamp" — reavaliação — PROBABLE

A §6 descreve a estrutura do desvio. Esta seção responde *o que* é
comparado, que era o ponto em aberto.

### O conflito, em uma linha

O `sdupdate` lê `ptable+0x10` e usa o valor como **offset de arquivo**.
Na imagem real, `ptable+0x10` contém o **nome** `"FIRM"` (`0x4D524946`).

### Teste das duas hipóteses de layout

| Campo lido | Layout real `{name,off,len,crc}` | Layout alternativo `{off,len,crc,name}` |
|---|---|---|
| `ptable+0x10` | `"FIRM"` — **inválido** como offset | `0x0000E000` — **offset válido**, e `+4` cai exatamente em `FIRM+0x04` = timestamp |
| `ptable+0x18` | `0x00192570` = tamanho da FIRM — **bate** com o rótulo `firmwareStartLen` | seria o CRC — **não bate** com o rótulo |

Uma única mudança de hipótese (layout alternativo) torna **dois** fatos
coerentes de uma vez: o `lseek` passa a ser válido **e** a leitura de
timestamp cai no offset exato onde o timestamp realmente está.

Contra ela pesa apenas um **rótulo de string** — e este bootloader já
provou que seus rótulos enganam: `"time is not same"` é impresso no
caminho de **sucesso** (§6).

### Conclusão — PROBABLE

> O caminho de `sdupdate` deste bootloader espera um **layout de entrada
> de partição diferente** do que a imagem instalada usa. Ele lê os campos
> com deslocamento de 4 bytes e, portanto, compara **valores espúrios**.

Consequências:

| Afirmação | Classificação |
|---|---|
| A estrutura `beq → 0xFC` existe | **CONFIRMED** |
| O layout esperado difere do da imagem | **PROBABLE** |
| Os valores comparados são espúrios nesta imagem | **PROBABLE** |
| A verificação **não** é proteção contra downgrade/reflash | **PROBABLE** |
| A verificação nunca dispara na prática | **HYPOTHESIS** |
| O que exatamente `0x00820A64` faz com endereço fora de faixa | **UNKNOWN** |

> **Isto não é boa notícia disfarçada.** Uma verificação que opera sobre
> lixo é **imprevisível**: pode aceitar um pacote ruim e pode recusar um
> bom. Continua sendo o item a resolver antes de qualquer gravação — mas
> a resposta agora é "provavelmente inerte", não "é uma trava".
