# Ficha 009 — RC7: causa do reinício e proposta de correção

Tipo: **Risco**. Base: `privado-completo`. Quem conduz: sessão GLM (D10/D12; decisor: "aqui a gente só
coordena"). Desenvolvedor, se precisar: `minimax/MiniMax-M3`. Antes: `008-rc7-trava.md` (fim),
`008-analise.md`, `007-rc7-capa-album.md`.

## Fato (aparelho)
Diag A (TITULO desviado direto ao `set_text`, rotina pulada) toca normal. Diag B reinicia o aparelho.
B = A + rotina `corpo_titulo` inteira + `get_path` + comparação/guarda do caminho + `set_src` do cinza,
sem heap novo e sem arquivo do usuário.

## Perguntas (classificar CONFIRMADO/PROVÁVEL/HIPÓTESE; só leitura do ORIGINAL)
1. **O que causa REINÍCIO neste aparelho?** Tabela de vetores e handlers de falha (HardFault etc.): reiniciam
   ou laçam? Existe watchdog, quem alimenta e com que prazo? `0x9E3C` e outras regiões fora do dump: dizer o
   que não dá para saber. A `008-analise` assumiu "fault = congela" sem conferir o handler.
2. **`get_path` com a origem real.** O arnês usa origem 2 e um stub. `0xCFEFC4` faz `tbb` em 6 casos e só o
   caso 0 foi descrito em `008-analise` (B1); os outros chamam `0xCFECBC`, `0xD6D414` etc. Quais rodam ao tocar,
   o que exigem de estado/tarefa, e o `ldrb [0x81BC84]`/`[0x81BC84+0x20]` lido pela rotina dá os mesmos valores
   dos getters da fábrica (`0xCFF1A8`, `0xCFF0FC`) nesse momento?
3. **Pilha, sem premissa.** A unidade de `0x1000`/`0x400` em `0xCF83A0` é byte ou palavra? A própria análise
   soma 1216 B no ramo `get_path` e diz que a MainTask (`0x400`) o executa: as duas coisas só fecham em
   palavras, ou a soma está errada. Em qual tarefa roda de fato `page_music_play_label_process` (e com que pilha)?
4. **A rotina real em `tools/capa_album.s`, sem stub:** alvo de chamada com bit Thumb, argumentos, `sp`
   alinhado em 8 na chamada, registradores preservados, tamanho do buffer, retorno, uso de ponteiro quando a
   mensagem chega antes de a view/ext existir ou depois de apagada.

## O que entregar
1. `docs/tarefas/009-analise.md` com as respostas e, se não fechar por estática, **uma** imagem de bisseção
   nova pelas mesmas regras da ficha 008: **B0** = a rotina TITULO ligada com o `get_path` cortado (trata como
   falha → cinza). Separa "a rotina" de "o `get_path`". Kit por `gera_versao`, carimbo `RC7 diag B0` com
   `patch_versao --em 0x1A4F00`, revisão do diff e `sh tools/ci.sh` verde.
2. Proposta de correção curta (ex.: obter o caminho na MainTask, onde a fábrica já chama `get_path`), com
   riscos e o que o aparelho ainda precisa provar: `f_open`/JPEG na tarefa da tela nunca rodaram no aparelho.
   **Não implementar a correção sem resposta do decisor.**

Regras de sempre: nunca alterar `firmware/ORIGINAL`, gravar no aparelho, push, merge; testes protegidos
intactos; ferramenta nova ≤ 350 linhas; nada abaixo de `0xE000`, setor `0xD000` e PSMP intocados.

---

## Entrega (preenchida pelo desenvolvedor — MiniMax M3, API direta)

### O que foi feito

- **`docs/tarefas/009-analise.md`** (novo): as **4 perguntas** respondidas, com
  `CONFIRMADO` / `PROVÁVEL` / `HIPÓTESE` em cada afirmação, o endereço e as
  instruções desmontadas do `firmware/ORIGINAL/GN438_original.bin`, e o que
  **não** dá para saber (a mask ROM, a RAM e o handler de fault ativo estão
  fora do dump). No fim, o **veredito** e a **proposta de correção** (não
  implementada).
- **`tools/stack_rc7.py`** (novo, 340 linhas): mede o quadro de cada função
  (`push` + `sub sp,#imm`) e o **pico** de uma cadeia de chamadas; é o que
  fecha a unidade da pilha e corrige a soma da ficha 008. Traz também
  `--tarefas` (as pilhas declaradas) e `--quem` (quem chama).
- **O degrau B0**: nível novo em `tools/diag_trava_asm.py` e
  `tools/fab_diag_trava.py`, a receita `reload_1.0_rc7_diag_b0` em
  `tools/build.py` e os 2 testes novos em `tests/test_diag_trava.py`
  (**28 testes, verdes**).
- **Os kits** do B0 (interno e público) com o `TESTAR.txt` do roteiro.

### O que a análise mudou (e o que a ficha 008 tinha errado)

| # | a 008 diz | o que a análise confere |
|---|---|---|
| 1 | o `get_path` tem "caso 0 → `0xD6D1B4`" | o `tbb` de `0xCFEFC4` tem **6 casos** e a base da tabela é **`0x00CFEFF2`** (não a alinhada em 4): o caso do banco é o caso **0** só com a base certa — com a base alinhada, 2 dos 6 casos caem em lixo. A tabela de casos está em `009-analise.md` §2.1 |
| 2 | o `get_path` gasta **1216 B** | o pico **medido** é **≥ 2720 B** (e ≥ 3384 B a partir do presenter): a soma esqueceu os quadros de 640/640/528 B do FatFs |
| 3 | a pilha da ViewTask é `0x1000` = **4096 B** | a unidade é **palavra**: `0x1000` = **16 KiB** e `0x400` = **4 KiB**. Fechado por contradição: a MainTask (`0x400`) executa o `get_path` da fábrica e o pico é ≥ 3464 B — em bytes a própria fábrica estouraria a pilha a cada toque |
| 4 | "a MainTask nunca transbordou" com pilha de `0x400` | só fecha em **palavras** (4 KiB). E a **H2 fica refutada**: o caminho da RC7 usa ≈ 3,2 KiB numa pilha de 16 KiB |
| 5 | "a RC7 reinicia" era explicado por H1 (ring cheio → mutex preso) | H1 previa **congelamento**, e o watchdog é alimentado mesmo com tarefas mortas → **H1 não explica o reinício**. O app **nunca pede o reset** (a rotina `NVIC_SystemReset` existe em `0x00C0E6A4` e **ninguém a chama**) |
| 6 | — | **achado novo**: a fábrica tem **1072 `udiv`/`sdiv`** (o `0x00D087F2`, no caminho do play, é um deles). O `div_soft` da ficha 007 foi **desnecessário** (inofensivo) e o H3 da 008 se apoiava numa premissa falsa |

### O veredito

**A causa do reinício não fecha por estática.** O que fecha: o flash visível
não pede reset; o handler "default" **laça** (congela) em vez de reiniciar;
a pilha não é a causa; a RC7 lê **os mesmos** bytes de origem/índice que a
fábrica e roda **o mesmo caso** do `get_path`. A **única** diferença real é a
**tarefa**: a fábrica abre o banco na MainTask, a RC7 abre na **ViewTask**.
O elo que falta (o handler de fault ativo em `0x00804C90` e o driver do
`/dev/wdog`) está **fora do dump** — por isso a imagem B0 é necessária.

### Rodadas

- **Rodada 1 (2026-11-05, MiniMax M3)**: a análise das 4 perguntas, a
  ferramenta de pilha, o degrau B0 (imagem + kits + roteiro) e a proposta de
  correção. `sh tools/ci.sh`: **verde** (`CI OK`); `tests/test_diag_trava.py`:
  **28 testes verdes**.

### Pacote — Ficha 009 / causa do reinício (degrau B0)

- Fase: 0. `sh tools/ci.sh`: **verde** (`CI OK`, rodado depois de todas as
  mudanças). Nenhum teste protegido, `tools/ci.sh`, `firmware/ORIGINAL/` ou
  ferramenta da receita RC7 foi tocado.
- Imagem `reload_1.0_rc7_diag_b0` (2 MiB, build reprodutível): sha256
  `63afb46ab8a9d9f8e0bedddf501c2adc2a4880f85d91d2ad982f73b23fec6cdb`;
  carimbada `61872fc2c87b77eae612f77487cacc5a4f5f54ab6030e7790f240381baa43d62`;
  `.up` `70f5dc1476ddd984fdb25774371c2dfd53896d2e4a0063a68b4a3066f465ac6a`,
  **CRC `0xA27E`**.
- Bytes: **2**, em `0x1AA14C` (`e0 47` → `00 20`): o `blx` da chamada ao
  `get_path` vira `movs r0, #0`. Nada mais, em lugar nenhum. Nada abaixo de
  `0x00E000`; setor `0x00D000` e PSMP (`0x1FC000+`) intocados.
- Kits: `firmware/RELEASE/OpenPod Reload 1.0 RC7 Diag B0/` e
  `release/OpenPod-Reload-1.0-RC7-Diag-B0/` (com o `TESTAR.txt`).
- **Roteiro (decisor)**: gravar o B0 como a RC7 (`.up` no cartão → Config →
  Atualizar por SD), tocar `01_capa_v23.mp3` e trocar de faixa, e anotar:
  **tocou sem reiniciar?** / **reiniciou?**
  - **B0 toca sem reiniciar** → a rotina do TITULO é inocente: a causa é a
    **chamada do `get_path` na ViewTask** (o banco/FatFs pelo lado da view);
    a correção é o presenter mandar o caminho junto com a mensagem.
  - **B0 reinicia** → a causa está na **própria rotina** (o ponteiro do
    contexto, o `lv_img_set_src`, o uso do `sp`): o `get_path` nem chega a
    ser chamado, e a correção muda de alvo.
- **Não implementado**: a correção depende da resposta do decisor (e do
  B0 no aparelho).
