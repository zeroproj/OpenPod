# Revisão 011 — NVIDIA (segundo revisor)

**APROVADO**

---

## Achados

### BAIXA — tools/fab_diag_b3.py:127-183 — Premissa da área livre não verifica limite superior do lote
**Evidência**: `confere_premissas` verifica que `BLOB:BLOB+BLOB_MAX` (0x1AAA00..0x1AB000) está virgem (0xFF), mas não verifica se o `copia_path` montado (46 bytes) cabe efetivamente no espaço até o fim do lote da RC7. O `BLOB_MAX = 0x600` (1536 bytes) é generoso; o código novo tem 46 bytes.
**Cenário**: Se o lote da RC7 crescer e invadir 0x1AAA00, a premissa de "área livre virgem" falharia, mas o teste `test_42_diff_exato` pegaria bytes fora do patch.

### BAIXA — tools/diag_b3.s:10-33 — `copia_path` não preserva `r2` (caller-saved, correto mas implícito)
**Evidência**: A função usa `r2` como ponteiro de destino e o incrementa no loop (`strb r1, [r2, r3]` com `r3` índice). `r2` é caller-saved (AAPCS), logo o chamador (TITULO em 0x1AA140: `r2 = ext+0x110`) não espera que volte intacto.
**Cenário**: Nenhum — a convenção ARM permite. Documentado só para rastreabilidade.

---

## O que conferiu e está certo

### 1. Patch em 0x1AA144 (GET/TÍTULO) — 10 bytes
- **RC7**: `movw/movt ip, #0xCFEFC5` + `blx ip` → chama `get_path` (0xCFEFC4)
- **B3**: `ldr r0, [r6, #8]` + `ldr r0, [r0, #0x24]` + `bl copia_path` + `nop`
- **Correto**: Lê o rótulo 2 (caminho) de `[r6+8]`, pega o texto em `[rótulo+0x24]` (onde `lv_label_set_text` grava), chama `copia_path` que copia para `ext+0x110` (já em `r2` desde 0x1AA140). O `nop` alinha para 10 bytes.

### 2. Patch em 0x1AA174 (CAPA — sucesso) — 8 bytes
- **RC7**: `movw/movt r1, #0xDA8000` + `blx lv_img_set_src` → mostra quadrado cinza
- **B3**: `movs r1, #0` + 3 `nop` → `src = NULL`, **sem quadrado cinza** no sucesso
- **Correto**: O cinza da falha em 0x1AA1BE **não é tocado** (continua cinza para caminho inválido).

### 3. Patch em 0x1AA188 (CARREGA_CAPA) — 4 bytes
- **RC7**: `bl carrega_capa` (0xDAA256)
- **B3**: `movs r0, #0` + `nop` → retorna 0, pula `carrega_capa` sem `f_open`/JPEG/heap
- **Correto**: Mantém o fluxo (o `cmp r0,#0` / `beq` seguinte trata como falha).

### 4. Código novo em 0x1AAA00 (BLOB) — 46 bytes
- **RC7**: Todo 0xFF (área livre)
- **B3**: `copia_path` — copia até 0xFF bytes, valida prefixo `0:` + `/` ou `\`, retorna 1 se válido, 0 caso contrário
- **Correto**: Aceita ambas as barras (teste: `0:/A/B.mp3` e `0:\A.mp3`). Cabe em `BLOB_MAX=0x600`.

### 5. Premissas conferidas ANTES de escrever (`fab_diag_b3.py:127-183`)
- 2 MiB + sha256 da RC7 exata (`3af97713...`)
- Tabela de entradas do lote (CRIA/TITULO/APAGA) no lugar
- Captura 0x1088D8 ainda é `bl 0xD084F8` de fábrica
- Estrutura do TITULO da RC7 (inclui `[r6+8]` = rótulo 2) intacta
- `lv_label_set_text` grava/lé `[r4+0x24]` (offset 0x24 confirmado em 0xD5EDA0/0xD5EDC2)
- `carrega_capa` com prólogo único e `bl` em 0x1AA188
- Área livre 0x1AAA00..0x1AB000 virgem (0xFF)
- Código novo ≤ `BLOB_MAX` e tem as 4 validações (`cmp r1, #'0'/':'/'/'/'\\'`)

### 6. Testes (`tests/test_diag_trava.py:633-894`) cobrem:
- `test_46_emulacao_copia_path`: caminho válido (`0:/...`, `0:\...`) → retorna 1, copia; inválido (`lixo`, vazio) → retorna 0
- `test_47_emulacao_titulo`: 
  - Caminho válido → chama `label_set_text` + `img_set_src(src=0)`, **sem** `get_path`, `calloc`, `free`, `f_open`; copia para `ctx+0x110` e `ctx+0x10`
  - Caminho inválido/vazio → `img_set_src(src=PH_DSC)` (cinza da falha), `ctx+0x10` vazio
  - Rótulo 1 (título) **nunca** lido como caminho (teste com título=`0:/TITULO`, caminho=`0:/MUSICA` → copia `0:/MUSICA`)
- `test_48_emulacao_xip_rom`: escrita em XIP → erro detectado
- `test_42_diff_exato`: só bytes nos 4 patches (GET 10B, CAPA 8B, CARREGA 4B, BLOB 46B); nada abaixo de 0xE000, setor 0xD000, PSMP
- `test_44_recusas`: RC6, truncada, B3 já patcheada, `--em` errado, `--out` = entrada/symlink/hardlink
- `test_45_premissas`: entrada RC7 passa; RC6, B3, captura corrompida, TITULO corrompido, área livre suja, `carrega_capa` já patcheado → recusam

### 7. Kit e receita (`tools/build.py:632-692`)
- Receita `reload_1.0_rc7_diag_b3` adicionada com `--em 0x1a8000`
- Ferramenta **não** entra no `MAPA` (patcha dentro do lote da RC7)
- `test_49_mapa_e_receita` confirma: receita existe, passo correto, `fab_diag_b3.py` fora do MAPA e da catraca

### 8. Imagem B3 construída — SHA conferidos
- B3 (sem carimbo): `3e9b8fa138c79f129bcfbd6cee1ed6f73634ce1e0be624ea89db3998340a5dd4`
- B3 carimbado: `5e86077b88ad8cb45a5f7347a3e664508cdd27879e116427be9ac6c63d0dee3e`
- `.up`: `e0d5594f2c4c496a7847caddc3491d0e29656608d8118a139cd33834c1a9c8f4` (CRC 0xD9DB)
- `sh tools/ci.sh` verde (validado na build)

---

**Nenhum achado ALTA ou MÉDIA.** O B3 implementa exatamente o descrito na análise 011: tira o `get_path` da ViewTask lendo o caminho do rótulo 2 (que a MainTask já preencheu via mensagem 0xD084F8), valida o formato, copia para a RAM que o `get_path` usava, mostra o cinza **só na falha**, e não toca `f_open`/JPEG/heap/bootloader/PSMP.