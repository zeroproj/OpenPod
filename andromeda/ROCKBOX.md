# ANDROMEDA — ROCKBOX

## Arquitetura do Rockbox relevante ao GN-438

---

## 1. O que é o Rockbox

Rockbox é um firmware de áudio open source que substitui o firmware original de players de música. Ele possui:

- Motor de áudio com gapless playback.
- Mais de 20 codecs de áudio.
- Sistema de skins (.wps, .sbs, .cfg).
- Banco de dados de tags.
- Plugins e jogos.
- Suporte a microSD.

---

## 2. Tipos de porte

O Rockbox distingue duas grandes categorias:

| | NATIVE | HOSTED |
|---|---|---|
| **Como roda** | Bare-metal, substitui o firmware original | Roda como aplicação sobre Linux/SDL/outro OS |
| **Performance** | Geralmente mais rápida | Depende do SO subjacente |
| **Boot** | Próprio bootloader | Usa SO existente |
| **Drivers** | Escritos para o hardware | Reusa drivers do SO |
| **Exemplos** | iPod Classic, Sansa Clip, FiiO M3K | Android, SDL, AGPtEK Rocker (parcialmente) |

Para o GN-438, o caminho seria **NATIVE**, pois não há Linux rodando no aparelho.

---

## 3. Componentes de um porte native

Um porte native do Rockbox exige:

| Camada | O quê | No GN-438 |
|---|---|---|
| **CPU** | Arquitetura suportada | ARMv7-M Thumb-2 — compatível |
| **Bootloader** | Carrega Rockbox da flash/SD para RAM | Teria de ser criado |
| **Memory map** | Linker script com endereços de RAM | RAM desconhecida |
| **Interrupts / timers** | Systick, IRQs | Não mapeado |
| **LCD** | Driver de display | GC9106/ST7789S — parcial |
| **Buttons** | Leitura de botões | Parcialmente mapeado |
| **Storage** | Driver de SD/microSD | FatFs existe, camada física não mapeada |
| **Audio** | Codec, I2S/DAC, DMA | Não mapeado |
| **Power** | PMU, bateria, sleep | Não mapeado |
| **USB** | USB stack | Não mapeado |
| **RTC** | Relógio de tempo real | Não mapeado |

---

## 4. Requisitos de memória

Esta é a questão mais crítica.

### 4.1 Targets conhecidos do Rockbox e suas RAMs

| Target | RAM | Observação |
|---|---|---|
| Archos Jukebox | 2 MB | Target original; monocromático, feature set limitado |
| Archos Recorder v2 | 2 MB | Target clássico |
| Sansa Clip+ | ~8 MB | Colorido, baixa resolução |
| iPod Nano 2G | 32 MB | Colorido, 176×132 |
| AGPtEK Rocker | 32 MB | Ingenic X1000 |
| FiiO M3K | 32 MB | Ingenic X1000 |
| GN-438 (hipótese) | 512 KiB | Muito abaixo de qualquer target conhecido |

### 4.2 Implicação para GN-438

A investigação do ANDROMEDA encontrou evidência forte de que o GN-438 possui **512 KiB de RAM** (heap LVGL em `0x00876000`, 40 KiB, terminando em `0x00880000`).

Isso está **muito abaixo** do target com menos RAM documentado no Rockbox (Archos Jukebox com 2 MB). Não foi encontrada fonte primária do Rockbox citando 1 MB como mínimo absoluto, mas 512 KiB é um quarto do menor target conhecido.

Mesmo com:
- Todos os plugins removidos.
- Banco de dados desativado.
- Apenas um codec.
- UI simplificada.

Ainda seria necessário espaço para:
- Buffer de áudio (dezenas de KB).
- Stack.
- Heap.
- Código executável.
- Framebuffer (128×160×2 = 40 KB).

---

## 5. Tamanho do binário

O tamanho do Rockbox varia muito com a configuração:

| Configuração | Tamanho típico |
|---|---|
| Bootloader apenas | ~30–100 KB |
| Rockbox mínimo (sem plugins, poucos codecs) | ~300–600 KB |
| Rockbox completo | 1–3 MB |

O GN-438 tem 2 MiB de flash interna. Teoricamente, um Rockbox mínimo poderia caber na flash. Mas:

- Precisaria de drivers para todos os periféricos.
- Sem SDK, cada driver exigiria reverse engineering.
- A RAM é o gargalo, não a flash.

---

## 6. Estratégias de redução de memória

Se a RAM for pequena, algumas estratégias poderiam ser tentadas:

| Estratégia | Economia | Custo |
|---|---|---|
| Remover plugins | centenas de KB | perde funcionalidade |
| Remover codecs, deixar apenas MP3 | dezenas de KB | perde formatos |
| Desativar banco de dados | dezenas de KB | perde navegação por tag |
| Executar código da flash (XIP) | ~300–400 KB | requer flash mapeada; SD não é XIP |
| Carregar recursos sob demanda do SD | variável | complexidade alta |

Mesmo com todas essas otimizações, 512 KiB ainda está abaixo do menor target conhecido do Rockbox (Archos Jukebox com 2 MB).

---

## 7. Conclusão sobre Rockbox

| Aspecto | Avaliação |
|---|---|
| CPU | Compatível (ARMv7-M Thumb-2) |
| Flash | 2 MiB — caberia um Rockbox mínimo |
| RAM | **Provavelmente insuficiente** (hipótese 512 KiB) |
| Drivers | Inexistentes; requerem RE extensiva |
| SDK | Inexistente |
| Esforço | Muito alto |

A viabilidade do Rockbox no GN-438 depende **primariamente do tamanho da RAM e da ausência de drivers**. Mesmo 512 KiB estão abaixo do menor target documentado (2 MB), e não há drivers para codec, DMA, display ou GPIO. O esforço de porte completo é impraticável no estado atual.

---

## 8. Alternativa: subset do Rockbox

Se o Rockbox completo não couber, uma alternativa seria:

- Usar apenas o **motor de áudio** do Rockbox (`libfirmware.a`, codecs).
- Escrever uma UI nova e minimalista.
- Executar da flash com XIP.

Isso não seria "Rockbox" no sentido tradicional, mas reaproveitaria código testado de decodificação e DSP.

Mesmo essa alternativa exige:
- Mapear o codec/DAC e I2S do GN-438.
- Entender o DMA de áudio.
- Portar ou reescrever o driver de áudio.
