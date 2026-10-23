# OpenPod Reload 1.0 — refeito do ORIGINAL, em degraus

> Aberto em 2026-09-24. Base: `GN438_original.bin` sha `b7cd5eb9...`
>
> **As Alphas 0.1 e 0.2 estão descartadas** — pedido do mantenedor:
> "não use as versões que foram geradas Alpha, essas coisas que estão
> bugadas". Nenhuma imagem, kit ou receita `reload_alpha*` entra na 1.0.
> `docs/RELOAD_ALPHA.md` fica só como histórico.

---

## 1. O que a 1.0 entrega

| # | Pedido | Ferramenta | Já rodou no aparelho? |
|---|---|---|---|
| 1 | Update por cartão SD | `patch_update_sd.py` | sim, linha Core |
| 2 | Logo do OpenPod na abertura | `patch_logo.py` | sim, V007 (autoteste reproduz byte a byte) |
| 3 | Fundo preto nas telas | `patch_fundo_display.py`, `patch_fundo_abertura.py`, `patch_fundo_preto.py` | só o `fundo_preto` (Beta 12); os outros dois nasceram nas Alphas |
| 4 | Barra superior com "OpenPod" | `patch_nome_faixa.py` | só nas Alphas — revisar |
| 5 | Degradê na barra | `patch_faixa_degrade.py` | só nas Alphas — revisar |
| 6 | Ícones da tela principal | `patch_icones_home.py` (novo) | não |
| 7 | Bateria casca prata + miolo verde | `patch_bateria_casca/verde/miolo.py` | sim, Beta 12 |

Fora da 1.0, de propósito: textos revisados (`aplica_textos.py`),
volume/brilho, e qualquer coisa da linha Core (Saturno, Marte, Extras).

## 2. Os degraus

Uma imagem por degrau. **O próximo só é gerado depois que o anterior
foi gravado e relatado.** Se algo quebrar, sabemos qual passo foi.

| Degrau | Receita | Conteúdo | Estado |
|---|---|---|---|
| RC1 | `reload_1.0_rc1` | 1 | **APROVADA no aparelho em 2026-10-21** (Flashloader, Windows; update por SD testado) |
| RC2 | `reload_1.0_rc2` | + 2, 3 | **APROVADA no aparelho em 2026-10-21** (pelo cartão). Imagem `fcca5fdc…`, carimbada `da3398d1…`, `.up` `2adb53ed…` CRC 0x91F1 |
| RC3 | `reload_1.0_rc3` | + 4, 5 (ferramentas novas da ficha 002) | RC3 gravada 2026-10-23 (degradê e título ok; pedido de alinhamento → R1). **RC3.1**: imagem `286e8ba8…`, carimbada `3b76b307…` (carimbo `--em 0x1A4F00`), `.up` `98aa9c9d…` CRC 0x1E32 — **APROVADA no aparelho 2026-10-23** ("ficou alinhado"); catraca em `tests/test_rc4.py` |
| RC4 | `reload_1.0_rc4` | + 6 (ícones) e barra no meio (pedido 2026-10-23); a bateria (7) fica para depois | **kit gerado 2026-10-23, aguardando gravação.** Imagem `74e8cb31…`, carimbada `08ad6043…`, `.up` `633768fb…` CRC 0x8750 — rodando no aparelho 2026-10-23 (foto); catraca em `tests/test_rc5.py` |
| RC5 | `reload_1.0_rc5` | + textos revisados e nomes curtos na home (ficha 005) | **kit gerado 2026-10-23, aguardando gravação.** Imagem `f9f2e059…`, carimbada `19afbbf3…`, `.up` `0d4843f8…` CRC 0xD4C4 — rodando no aparelho 2026-10-23 (foto); catraca em `tests/test_rc6.py` |
| RC6 | `reload_1.0_rc6` | + home sem nomes, grade centralizada, moldura no selecionado (ficha 006) | **kit gerado 2026-10-23, aguardando gravação.** Imagem `af3a2b6d…`, carimbada `21769bd4…`, `.up` `e70a8938…` CRC 0xA64D |
| RC7 | — | + capa do álbum (de dentro do MP3) na Tocando Agora — semana que vem | **pedido 2026-10-21; caminho escolhido (D05); análise em `docs/tarefas/003-rc5-analise-capa.md`** (ver §6) |

Instalação: **1ª gravação por cabo**; todo kit leva também o `.up` para as
seguintes pelo cartão.

## 3. RC1

```sh
python3 tools/build.py --receita reload_1.0_rc1 --saida firmware/WORKING/GN438_reload_1.0_rc1.bin
python3 tools/patch_versao.py --in firmware/WORKING/GN438_reload_1.0_rc1.bin \
        --out firmware/WORKING/GN438_reload_1.0_rc1_carimbado.bin --texto "Reload 1.0 RC1"
python3 tools/gera_versao.py --imagem firmware/WORKING/GN438_reload_1.0_rc1_carimbado.bin \
        --versao OpenPod-Reload-1.0-RC1 --nome-tela "Reload 1.0 RC1"
```

| | sha256 |
|---|---|
| `GN438_reload_1.0_rc1.bin` | `a427c62ec7da0170ef4296ebda6a55ec5d287c4058d3c5a9e80e645f28e5c3f2` |
| `GN438_reload_1.0_rc1_carimbado.bin` | `a423e7ad9d94b80a68a6ac8adf081fd5341af598728de14ca4864d2bd694ab72` |
| `OpenPod_OpenPodReload1.0RC1.up` (CRC 0x7515) | `c4974029b45611b6d133ab17b851a02a2fe198ac3af2ffc17a4e4f04f91a6654` |

Diff contra o ORIGINAL: 77 B em 3 setores (`0x053000`, `0x109000`,
`0x1A3000`) + carimbo 18 B (`0x10A000`, `0x1A3000`). Validação: só a
falha esperada da R1. Bootloader, `0x00D000` e PSMP intocados.

**Atenção:** o script do cabo confere os setores `base_*` do ORIGINAL. Se
o aparelho estiver com Beta 12 ou Alpha, gravar antes
`release/OpenPod-Fabrica/` ou refazer o kit com `--base`.

## 4. Ícones da tela principal

A home desenha uma folha única INDEXED_8 128×160 em `0x0CDD50` com os
nove ícones em grade 3×3, 30 px cada (`docs/IMAGENS.md` §3). Centros
medidos na folha de fábrica: x = 22,5 · 63,5 · 104,5; y = 31,5 · 79,5 ·
127,5. A navegação é por índice (`docs/PLANO_HOME.md` §1.2) — trocar a
folha não toca nela.

Estilo aprovado pelo mantenedor em 2026-09-24, depois de três rodadas
(círculo prata+verde → quadrado → cores): **"Apple-like moderno"** —
squircle, degradê por função, símbolo branco, sem brilho. Desenho
próprio, em código; nenhum pixel da Apple nem da fábrica.

```sh
GLIFO=255,255,255 python3 tools/desenha_icones_home.py assets/IconesHome.png /tmp/ampliada.png
python3 tools/patch_icones_home.py --autoteste
python3 tools/patch_icones_home.py --in <entrada.bin> --out <saida.bin>
```

Autoteste: relido pelo cabeçalho == quantização; 0 bytes fora do slot;
242 cores; erro médio 1,23 por canal. Escreve 20.954 B em
`0x0CD000`–`0x0D3000` (7 setores), cabeçalho intocado.

Em aberto: Tocando agora e Livro estão ambos laranja (aprovado assim).

## 5. Pendências

- **Quais defeitos as Alphas mostraram** — decide se `patch_nome_faixa`,
  `patch_faixa_degrade`, `patch_fundo_display` e `patch_fundo_abertura`
  são reaproveitados ou reescritos antes da RC2/RC3.
- A barra com "OpenPod" fixo tira o ícone de cartão SD do centro.

## 6. RC5 — capa do álbum (pedido do mantenedor, 2026-10-21)

Varredura rápida do ORIGINAL (2026-10-21):

| | Evidência | Confiança |
|---|---|---|
| decodificador JPEG | `JpegDecInit/Decoder/Release` (`0x4FCAE`) + mensagens de libjpeg (`0x51680`…) | CONFIRMADO que existe |
| decodificador BMP | `BmpDecInit/Decoder/Release` (`0x4FC75`) | CONFIRMADO que existe |
| leitura de capa embutida (ID3 `APIC`) | nenhuma string `APIC`/`PIC`/`covr`; os `ID3` achados são de outro contexto | **não há evidência** |
| objeto de imagem na Tocando Agora | papel de parede `0x0C73B8` é `lv_img` (`docs/IMAGENS.md`) | CONFIRMADO |

Dois caminhos, do mais barato ao mais caro:
1. **`cover.jpg` da pasta do álbum** — reaproveita o decodificador que o
   visualizador de Imagem já usa; falta medir como ele entrega os pixels e
   quanta RAM sobra durante a reprodução.
2. **Capa embutida no MP3 (ID3 APIC)** — exige um leitor de ID3 novo na
   área livre, além do item 1.

Tipo: **Pesada** (código novo, várias partes). Primeiro passo: ficha de
análise (sem imagem gravável) que responda RAM, saída do JpegDec e onde
enganchar na Tocando Agora.

### 6.1 Decisão: capa de dentro do MP3 (D05)

O decisor escolheu o caminho 2. Segunda varredura (2026-10-21) achou que a
fábrica **já tem leitor de ID3**, o que barateia o caminho:

| Endereço | O que faz | Confiança |
|---|---|---|
| `0xD71C94` | lê o cabeçalho ID3v2 (10 B), tamanho synchsafe; versão 2 → `0xD719D8`, versões 3–4 → `0xD71B34`, outra → `-1` | CONFIRMADO (desmontagem) |
| `0xD71B34` | percorre os quadros de 10 B: `TALB` → buffer+0 (máx. 256 B, tamanho em +0x104); `TPE1` → buffer+0x108 (tamanho em +0x20C); outro quadro → pula com seek | CONFIRMADO |
| `0xD719D8` | o mesmo para ID3v2.2 (quadros de 3 letras) | PROVÁVEL |
| `0xD71D1C` | lê ID3v1 (últimos 128 B) | PROVÁVEL |
| `0xD76854` / `0xD76C0A` | leitura / posicionamento no arquivo (assinaturas de `f_read`/`f_lseek`) | PROVÁVEL |
| único chamador de `0xD71B34` | `0xD71D16` | CONFIRMADO (varredura de `bl`) |

Observação: o tamanho do quadro é lido como inteiro comum (correto na
v2.3; na v2.4 o certo seria synchsafe). Capas grandes em v2.4 podem ser
puladas errado — HIPÓTESE a medir.

Plano de alto nível (HIPÓTESE até a ficha de análise):
1. Gancho no ramo "outro quadro" de `0xD71B34`: se for `APIC`, guardar
   posição e tamanho da imagem no arquivo (não copiar), e seguir pulando.
2. Na Tocando Agora, se houver posição guardada e for JPEG: ler, decodificar
   com o `JpegDec` da fábrica, reduzir para o tamanho do quadro e desenhar
   no lugar do papel de parede; sem capa → papel de parede de sempre.
3. Perguntas da ficha de análise: RAM livre durante a reprodução; o
   `JpegDec` aceita memória ou só arquivo, e em que formato entrega os
   pixels; tamanho máximo de capa aceitável; onde a Tocando Agora monta a
   imagem; capas PNG (sem decodificador → ignoradas).
