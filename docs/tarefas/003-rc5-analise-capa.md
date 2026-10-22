# 003 — RC5, análise: capa do álbum (de dentro do MP3) na Tocando Agora

- Tipo: Comum (análise; nenhuma imagem gravável muda)
- Engenheiro: Claude Opus 5.5
- Depende de: decisão D05 (capa embutida, ID3v2 `APIC`)
- Status: em andamento — 1ª rodada estática feita em 2026-10-21; faltam 2 experimentos no aparelho

## Objetivo
Responder, com evidência do ORIGINAL, se dá para mostrar a capa embutida no
MP3 na Tocando Agora, quanto custa e onde enganchar, antes de escrever a
ficha de implementação (que será Pesada + Risco).

## Perguntas e respostas (1ª rodada, estática)

| # | Pergunta | Resposta | Confiança |
|---|---|---|---|
| P1 | O firmware lê ID3? | Sim: `0xD71E42` abre o arquivo, `0xD71DA2` detecta v2/v1, `0xD71C94` lê o cabeçalho v2 (synchsafe) e despacha para `0xD719D8` (v2.2) ou `0xD71B34` (v2.3/2.4: só `TALB`, `TPE1`, máx. 256 B). v1 em `0xD71D1C` | CONFIRMADO |
| P2 | Quando ele lê? | **Só ao montar a biblioteca** (`0xD6EDFE`, junto de `0:\DBROOT\db_audio.db`, `db_artist.db`, `db_sort.db`). Na reprodução, não | CONFIRMADO (único chamador) |
| P3 | Qual é o decodificador de JPEG? | **TJpgDec (ChaN)**: tabela `Ipsf` terminando em `0xC50210` seguida do zig-zag em `0xC50212`; `jd_prepare` = `0xD10B20` (`pool` de 0xE00 B), `jd_decomp` = `0xD11090` | CONFIRMADO |
| P4 | Como a fábrica usa o decodificador? | `0xD103D4(caminho, in, out)`: `calloc(0x4180)` (≈16,4 KiB de contexto), `f_open` do caminho, `jd_prepare` com leitor `0xD1036D` (lê ou pula **para a frente** no arquivo); `0xD104B8` faz `jd_decomp` com saída `0xD10229`, que escreve RGB565 em faixas de 40 linhas (`yp3_pic_handle->blocks`) para o visualizador de fotos. `0xD10498` libera | CONFIRMADO (desmontagem) |
| P5 | Dá para decodificar uma imagem que está no meio do MP3? | **Sim, sem mexer no decodificador:** o TJpgDec só lê para a frente; basta `f_lseek` até o início do JPEG do `APIC` antes do `jd_prepare`. O player de vídeo da fábrica já decodifica JPEG dentro de outro arquivo (AVI `00dc`) — pista para reaproveitar | PROVÁVEL (mecanismo); a pista do vídeo é HIPÓTESE |
| P6 | Que JPEG ele aceita? | TJpgDec só faz **baseline**. Capa progressiva → `jd_prepare` falha → fica o fundo de sempre. Redução nativa 1/1, 1/2, 1/4, 1/8; o resto com a nossa saída | CONFIRMADO (limite conhecido do TJpgDec) |
| P7 | Capa em PNG? | Não há decodificador de PNG → ignorada | CONFIRMADO |
| P8 | Memória | RAM total ≈ 240 KiB (`0x800000`..`0x83BE90`, pilha inicial). O `calloc` da fábrica (`0xCF7840`) confere o livre com `0x9E88` antes de alocar e loga `OAL_calloc1 %d failed` se faltar. **Quanto sobra durante a reprodução: desconhecido** | CONFIRMADO o mecanismo; o valor exige o aparelho |
| P9 | Onde fica a Tocando Agora | Página 4: `page_music_play_create` `0xD31E7C` (view), `page4_scr_process` `0xD08A90` (presenter). Os textos chegam por mensagem (`0xD32204`: tipo 3 = texto do rótulo 0..4; tipo 4 = valor) | CONFIRMADO |
| P10 | De onde vem o caminho da faixa atual | Ainda não localizado; começa no presenter `0xD08A90`, que monta o título | a fazer |

## Desenho proposto (HIPÓTESE até os experimentos)
1. **Achar a capa na hora de tocar**, não na biblioteca: uma rotina nossa
   na área livre abre a faixa atual, percorre os quadros ID3v2 (tratando
   v2.3 e v2.4 direito) até o `APIC`, pula o cabeçalho do quadro (codificação,
   MIME, tipo, descrição) e guarda a posição e o tamanho do JPEG. Não mexe no
   leitor de ID3 da biblioteca (P2).
2. **Decodificar** com o TJpgDec da fábrica: `f_lseek` até o JPEG,
   `jd_prepare` com o leitor da fábrica, `jd_decomp` com escala 1/2^n e uma
   saída nossa que reduz até o tamanho final e escreve num buffer RGB565.
3. **Mostrar** como `lv_img` (TRUE_COLOR) na Tocando Agora; sem capa, capa
   progressiva, PNG ou falta de memória → fica como está hoje.
4. Tamanho candidato: 64×64 (8 KiB de buffer) ou 96×96 (18 KiB). A
   geometria atual tem faixa (y 0..21), bloco 128×60 a partir de y=22 e
   progresso perto de y=45 (`docs/TOCANDO_AGORA.md` §1) → a capa precisa de
   reorganização da tela; decidir com foto.

Custo de memória estimado no pico: contexto 16,4 KiB (alocado e liberado a
cada troca de faixa) + buffer da capa (8 a 18 KiB, enquanto a tela estiver
aberta).

## Experimentos no aparelho (decisor, sem gravar nada)
| # | O que fazer | O que responde |
|---|---|---|
| E1 | Tocar uma música, voltar para a home (a música continua?), abrir **Fotos** e abrir um JPG grande (ex.: 1000×1000). Abre? A música engasga? | Se a fábrica já decodifica JPEG **com música tocando**, os ~16 KiB do contexto cabem durante a reprodução (P8) |
| E2 | Foto da Tocando Agora com uma música de título longo | Onde a capa cabe (desenho §4) |

Se E1 falhar (foto não abre com música), a próxima etapa é uma imagem de
diagnóstico (ficha Risco) que mostra a memória livre na tela.

## Próximo passo
Com E1 e E2: P10 (caminho da faixa atual), ponto de gancho no presenter
(troca de faixa) e na view (onde criar o `lv_img`), e então a ficha 004 —
implementação, tipo Pesada + Risco, com testes vermelhos e revisão astra.
