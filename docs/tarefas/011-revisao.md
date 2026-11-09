# Revisão 011 — B3 (segunda revisão)

**REPROVADO**

Achados primeiro; nada fora deste documento foi alterado. Verificação por
capstone sobre o `GN438_original.bin` (XIP = arquivo + 0xC00000), imagens B3
reconstruídas com a receita e o arnés `tests/emu_rc7.py`.

---

## Achados

### MÉDIA — tools/fab_diag_b3.py:11-12, 65-66, 192-193 + tools/diag_b3.s:12 — a cadeia `ldr r0,[r6,#8]` → `ldr r0,[r0,#0x24]` → `ldrb r1,[r0,r3]` não tem guarda de NULL, e a premissa "o rótulo 2 já tem o caminho quando o título chega" vale só para 2 dos 4 fluxos do título

**Evidência (fábrica, ORIGINAL):** o construtor do título `0xD08448` tem
**4 chamadores `bl`** — 0xD088E8 (com o `bl 0xD084F8` do caminho justamente
antes, em 0xD088D8), 0xD089A0 (idem, caminho em 0xD0899C) — e **0xD08BE2 e
0xD09014, que enfileiram o título SEM nenhum caminho antes** (varredura
completa do binário; quadro de 0x300 sem um único `bl 0xD084F8`). A mesma
análise que o B3 usa documentou só o par do `page4_media_cb`.

**Mecanismo:** no TITULO (0xDAA114 a guarda `r4 == [r6+4]` passa), o patch
novo lê `[r6+8]`, depois `[rótulo+0x24]` e o `copia_path` lê o byte em
`[texto]`. Se o objeto do rótulo 2 for 0, ou o texto dele mirar em 0 (rótulo
criado e nunca escrito desde a montagem), o `ldrb` mira em 0.

**Emulação (mesmo arnés do test_47):** `[view+8] = 0` e
`[rótulo+0x24] = 0` — nos dois casos a execução para logo após o
`label_set_text`, e o arnés não registra erro nenhum (a morte é silenciosa,
como um fault no aparelho).

**Cenário:** B3 no aparelho; a navegação passa por um manipulador que
manda título sem caminho novo (0xD08BE2/0xD09014) num rótulo 2 recém-criado
→ BusFault → reinício no MEIO do diagnóstico. A ficha lê "Reinicia" como
"o `get_path` (ou não só ele) era a causa" (docs/tarefas/011-analise.md:223):
a leitura sai ambígua e a causa (o próprio `ldrb` do B3) fica mascarada.
Mesmo com texto não-nulo, esses fluxos copiam o caminho VELHO de outra faixa
e a capa mostra como "Toca, sem o quadrado cinza" — leitura também falsa.

**Correção mínima:** 6-8 bytes no código novo (guarda `cmp r0,#0` e/ou do
primeiro byte antes do `ldrb` → caminho de falha, o cinza). Pedir como
degrau B4 (ou ficha adendo) e repatchear antes de qualquer kit.

### BAIXA — docs/tarefas/011-analise.md:203 — "o B3 altera **68 bytes**" conta trechos, não bytes mudos

**Evidência:** diff RC7→B3 reconstruído: **65 bytes mudos** — 0x1AA144
(10), 0x1AA174..0x1AA17B (7), 0x1AA188..0x1AA18B (3), 0x1AAA00..0x1AAA2D
(45). O "68" é a soma dos trechos (10+8+4+46): 0x1AA176, 0x1AA188 e
0x1AAA0C mantêm o valor original. A própria ficha usa 65 em
011-analise.md:214 (contra a base B2 carimbada).

**Cenário:** um congelador futuro exige diff de exatamente 68 bytes e
reprova por diferença que não existe.

---

## O que conferiu e está certo

1. **Recusas e premissas** (`tools/fab_diag_b3.py:127-183`, 230-270,
   314-326): sha da RC7 exata, tabela de entradas do lote, captura
   0x1088D8 intocada, estrutura do TITULO (prólogo, `[r6+4]`, `[r6+0x30]`,
   memset ext+0x110, `[0x81BC84]`, `[r1]/[r1+0x20]`, r2 ext+0x110), o
   `[r4+0x24]` do `lv_label_set_text` (0xD5EDA0/0xD5EDC2), `carrega_capa`
   único e seu `bl`, área livre virgem — tudo conferido ANTES de
   escrever; recusa sem criar saída; `--out` igual/symlink/hardlink da
   entrada recusado; `--dry-run`; diff zero fora do patch; nada abaixo de
   0xE000, setor 0xD000 e PSMP intocados.
2. **Byte a byte do patch** (desmontado da imagem construída):
   0xDAA144 = `ldr r0,[r6,#8]` + `ldr r0,[r0,#0x24]` + `bl 0xDAAA00` + nop;
   0xDAA174 = `movs r1,#0` + 3 nop (o `img_set_src` de fábrica em
   0xDAA17C fica — sucesso sem o quadrado cinza); 0xDAA188 = `movs r0,#0`
   + nop (o fluxo de fábrica depois trata como falha); blob 0xDAAA00 =
   `diag_b3.s` montado, byte a byte, 46 bytes ≤ `BLOB_MAX` (0x600);
   o cinza da falha (0xDAA1BE/0xDAA1C6) e a captura 0xD088D8 intocados.
   Registradores: o `copia_path` usa só r0-r3 (caller-saved) e volta
   `bx lr` — nada de r4-r11 é destruído.
3. **Seção 1b:** desc+0x20 é a prioridade — MainTask 1 (0xCF8068), ViewTask
   sem escrita nenhuma em +0x20 (memset 0xCF8394 cobre o desc todo → 0;
   nenhum strb entre 0xCF8394 e o bl de 0xCF83B8), PreTask 3 (0xCF8174),
   DbsTask 1 (0xD3FD1C), MgrTask 3 (0xD400D0), MediaTask 3, Master 4,
   bt_host 3 (0xD92318/0xD9231A — `strb.w r3,[sp,#0x20]` com r3=3; o id
   4 fica em +0x54); tabela 0x81D68C com entrada de 0x58 e id em +0x54.
4. **Seção 1c:** o `get_path` (0xCFEFC4) tem EXATAMENTE os 6 chamadores
   declarados (`bl` varrido do binário inteiro, decodificador de BL
   verificado contra o capstone): 0xCFF0C0, 0xCFF37C, 0xD0138E, 0xD01624,
   0xD016C2, 0xD017D2. Mutex do banco: literal → 0x0081DC00, take/give
   via `adds r0,#0x5C` + `bl 0x80DB48`/`bl 0x80DB6E` (ROM, conferidos
   pelo lado chamador; a partir de 0xCFEFFE); cadeia MainTask 0xD6D1B4 →
   `bl 0xD6F138` (0xD6D1DC) → `bl 0xD777CC` (0xD6F14C); o wrapper do like
   (0xD6DB90) usa o MESMO mutex (pool 0xD6F1A4 = mesma 0x81DC00); os
   serviços de like (0xCFF0A8) e do 0xCFF354 conferidos.
5. **Seção 2:** 0xD3220C lê o tipo em msg+4 (`ldrh r3,[r4,#4]`); o `tbb`
   (0xD32242, 2 bytes) manda 1 → `[r5+4]` (título) e 2 → `[r5+8]`
   (caminho); `set_text` = 0xD5ED94 (bl em 0xD3225E) com texto = msg+0x14
   (`add.w r6,r0,#0x14` em 0xD3222C); o 0xD08448 grava 1 em msg+4 e o
   0xD084F8 grava 2 (strncpy 0xD9FD54); o getter do nome é 0xCFEE60
   (bl em 0xD08468); no `page4_media_cb` o caminho (0xD088D8) vem ANTES
   do título (0xD088E8) — a ordem que o B3 assume.
6. **`lv_img_set_src` com src NULL não derefere** (classificador
   0xD4DA90: `cbz r0` → UNKNOWN; o caminho NULL só loga 2x e reseta o
   cache do objeto) — sem fault.
7. **Shas e kit:** RC7 reproduzida exata (3af97713...); B3 sem carimbo
   3e9b8fa1...; carimbada (`--em 0x1A4F00`, "RC7 diag B3")
   5e86077b... — igual à da ficha; `.up` e0d5594f... com CRC do payload
   0xD9DB, fw_size 0x1AB000 (fim antes da PSMP) e payload byte a byte
   igual à carimbada (0 divergentes).
8. **Receita** (`tools/build.py:661-662, 688`): `--em 0x1a8000` explícito;
   a ferramenta fora do `MAPA` (test_49).
9. **Testes:** os 10 da classe B3 (`tests/test_diag_trava.py:633-894`)
   verdes; `sh tools/ci.sh` inteiro verde (protegidos, ORIGINAL,
   tamanho 341 ≤ 350).
