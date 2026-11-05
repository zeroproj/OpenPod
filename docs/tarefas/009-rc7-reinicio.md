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
