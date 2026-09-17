# ANDROMEDA — RISKS

## Riscos técnicos do SD Boot / Rockbox no GN-438

---

## 1. Escala de risco

| Nível | Significado |
|---|---|
| LOW | Risco conhecido e mitigável |
| MEDIUM | Risco real, requer atenção, mas não bloqueia |
| HIGH | Pode bloquear ou causar perda significativa |
| CRITICAL | Pode destruir o dispositivo ou inviabilizar o projeto |

---

## 2. Riscos identificados

| # | Risco | Nível | Descrição | Mitigação |
|---|---|---|---|---|
| R1 | Brick por modificação do bootloader | **CRITICAL** | O bootloader é a única rede de segurança. Corrompê-lo pode tornar o aparelho irrecuperável. | Não modificar o bootloader nesta fase; usar hook na FIRM se possível |
| R2 | Brick por gravação direta por USB | **CRITICAL** | `write_flash` pode atingir o bootloader. Documentado na comunidade. | Usar apenas SD update; nunca USB write |
| R3 | Tamanho da RAM desconhecido | **HIGH** | Sem saber a RAM total, não é possível dimensionar um sistema SD. | Medir RAM via payload ou documentação |
| R4 | Ausência de SDK/datasheet | **HIGH** | Drivers de periféricos teriam de ser escritos por RE. | RE gradual; priorizar periféricos essenciais |
| R5 | Comportamento anômalo da flash | **HIGH** | Flash pode restaurar bits `0 → 1` sem erase (90% eficiência). | Sempre verificar por releitura; usar erase antes de write |
| R6 | Audio — codec/driver desconhecido | **HIGH** | Rockbox sem áudio não é player. | Identificar codec e barramento (I2S?) |
| R7 | LCD/driver desconhecido | **MEDIUM** | Display 128×160 RGB565, mas driver pode ser GC9106 ou ST7789S. | Testar ambos; usar inicialização do firmware original |
| R8 | Botões — mapeamento parcial | **MEDIUM** | Botões M, ◀◀, ▶▶, ▶Ⅱ mapeados, mas remapeamento exige cuidado. | RE da tabela de key_id se necessário |
| R9 | SD controller desconhecido | **MEDIUM** | FatFs existe, mas camada física não está mapeada. | Reusar driver do firmware original |
| R10 | Bluetooth — chip/stack desconhecidos | **MEDIUM** | Não bloqueia primeira avaliação, mas afeta funcionalidade. | P2 — investigar depois |
| R11 | FM — chip sintonizador desconhecido | **LOW** | Não bloqueia SD Boot. | P2/P3 |
| R12 | USB — modo recovery não testado | **MEDIUM** | Modo "update from pc" existe, mas não foi exercitado. | Testar somente leitura antes de qualquer gravação |
| R13 | Time-to-market | **MEDIUM** | Porte Rockbox é projeto grande. | Fasear; MARTE continua independente |
| R14 | Licenciamento Rockbox | **LOW** | Rockbox é GPL; derivados devem ser open source. | Compatível com objetivos do OpenPod |

---

## 3. Riscos críticos detalhados

### R1 — Brick por modificação do bootloader

O bootloader ocupa `0x000000`–`0x0000D000`. O `sdupdate` nunca grava essa faixa, o que o preserva durante updates oficiais. Se um patch para SD Boot modificar o bootloader e falhar:

- O aparelho pode não enumerar por USB.
- O modo "update from pc" pode não funcionar.
- Recuperação pode exigir acesso físico à flash (SPI).

**Recomendação:** NÃO modificar o bootloader na primeira fase. Preferir um hook na FIRM.

### R2 — Brick por gravação USB

Conforme `docs/EXTERNAL_RESEARCH.md` §5.3:

> *"There are cases where devices no longer boot, even in bootloader mode, if you erase the entire flash or if there's invalid content."*

O `smtlink_dump` oferece `write_flash`, `erase_flash`, `write_mem`, `exec`. Qualquer um deles pode destruir o bootloader.

**Recomendação:** Proibir uso desses comandos durante ANDROMEDA.

### R3 — Tamanho da RAM desconhecido

O stack pointer inicial (`0x0083BE90`) indica uso de pelo menos ~244 KiB acima de `0x00800000`, mas o tamanho físico pode ser 256 KiB, 384 KiB ou outro valor. Sem isso, não se sabe quanto de código pode ser carregado do SD.

**Recomendação:** Determinar RAM total antes de qualquer arquitetura de SD Boot.

### R5 — Flash anômala

Conforme `docs/EXTERNAL_RESEARCH.md` §5.2:

> *"All is fine with 1 → 0, but flash can somehow restore 0 → 1 with 90% efficiency without erasing."*

Isso significa que gravação pode parecer funcionar mas deixar bits errados. O `sdupdate` faz releitura + CRC, o que é uma resposta a essa característica.

---

## 4. Matriz de risco × decisão

| Decisão | R1 | R2 | R3 | R4 | R5 | Risco agregado |
|---|---|---|---|---|---|---|
| Patch no bootloader para SD Boot | CRITICAL | — | HIGH | HIGH | HIGH | **CRITICAL** |
| Hook na FIRM para SD Boot | MEDIUM | — | HIGH | HIGH | MEDIUM | **HIGH** |
| Apenas MARTE (sem Rockbox) | LOW | LOW | LOW | LOW | LOW | **LOW** |
| Rockbox via SD (futuro) | HIGH | HIGH | HIGH | HIGH | HIGH | **HIGH** |

---

## 5. Recomendação de gestão de risco

Para ANDROMEDA, os riscos são aceitáveis **enquanto a pesquisa permanecer offline**:

- Nenhum risco de brick enquanto não houver gravação.
- A pesquisa pode continuar em paralelo com MARTE.
- A decisão de implementação deve esperar:
  1. Tamanho da RAM.
  2. Método seguro de patch.
  3. Confirmação de que a recuperação funciona.
