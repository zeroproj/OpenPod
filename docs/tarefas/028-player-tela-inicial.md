# Ficha 028 — Player na tela inicial (Reload 3.5)

Tipo: **Risco + Pesada** (mexe na home, a primeira tela ao ligar; vai ao aparelho e ao público). Base: a **3.3** publicada (ficha 025).
Desenvolvedor: `opencode/deepseek-v4.1-flash-free` (decisor, 2026-11-21). Decisões D26 e D28 (2026-11-20). Prazo da 3.5: **10/12/2026**.
A 3.3 foi testada pelo decisor e publicada em 21/11/2026 (receita `reload_3.3` = só a Parte 0.2 da 025).

## O que é
Na home ficam os **9 ícones**, um pouco mais juntos, e embaixo deles um **cartão fixo e compacto** com a música que está tocando.
Modelo aprovado: `assets/ideias/ideia_9icones_player_menor.png`.
- **Tocando:** capa, nome, ▶/❚❚, artista, tempo restante e barra de progresso.
- **Sem música:** "Nada tocando · Escolha em Música".
- O cartão **só mostra**: não é selecionável e não muda a navegação nem as teclas da home.

## Etapas (D26: a 3.5 sai com o que estiver provado)
1. **Obrigatória.** A grade mais junta, o cartão e o **nome da música**, ou "Nada tocando".
2. **Se provada.** O **▶/❚❚** e o **tempo restante**, com a barra. HIPÓTESE: achar na RAM onde a fábrica guarda o estado e o tempo.
3. **Não entra na 3.5.** A capa no cartão. Fica para depois da 3.3 estável no aparelho e da tarefa própria da capa. No cartão vai o
   desenho de nota musical no lugar da capa.

## O que já sabemos (ler antes)
- `docs/tarefas/021-analise.md`:
  - a home é a página 1 (`page1_process`);
  - os ícones são **uma imagem só**: `INDEXED_8`, 128×160, com paleta própria;
  - a moldura do selecionado vem do `fab_home_moldura.py`, e o `fab_icones_home_apps.py` refaz a folha.
  - Para juntar a grade é preciso redesenhar essa folha e mover as posições da moldura.
- **Dois núcleos** (`025-analise.md`, Parte 0): a home roda na **CPU1**, a ViewTask/LVGL.
  - Na CPU1, nada de chamada ao kernel, ao banco de músicas, ao FatFs nem ao `get_path`. A 013 provou que o `get_path` pega o mutex
    do banco e abre `db_audio.db`.
  - A CPU1 pode **ler memória** e usar LVGL.
- O título já é montado pela fábrica **na PreTask**, a CPU0: o presenter `0xD08448` (ficha 007, A3) manda o tipo 3 / rótulo 1 para a
  página 4. Caminho provável: copiar o texto na CPU0, nesse ponto, para um buffer **nosso**; um timer LVGL na home lê esse buffer e
  atualiza o rótulo.
  - O buffer é alocado uma vez, na CPU0, e nunca liberado.
  - O ponteiro dele fica num lugar **provadamente livre** (ver a ideia do `0x80001C` na ficha 026).
  - O buffer tem um contador de versão, para a home não ler um texto pela metade.
- **A provar:**
  - (a) Esse presenter roda quando a página 4 **não** está aberta, por exemplo quando a música avança sozinha com o usuário na home?
    O `page4_media_cb` está registrado em `0xD0E8F8`, com guarda em `0x0081CDE0`. Se só rodar com a página 4 aberta, achar outro
    ponto na PreTask que veja a troca de faixa.
  - (b) Como saber "nada tocando", e como saber quando a música para.

## Regras do projeto que valem aqui
- Nada de `.data`/`.bss`; lote próprio na área livre; bit Thumb em todo `bx`/`blx`.
- A home **não pode ficar mais lenta**. O timer de atualização roda a no máximo 2 Hz e só troca o texto quando a versão muda.
- O texto longo é cortado com "…" e não rola. Usar a mesma fonte da fábrica.
- Os idiomas: "Nada tocando" / "Nothing playing" / "Escolha em Música" / "Choose in Music", seguindo o idioma do aparelho como os jogos
  da 3.1 fazem. Se não houver prova de como ler o idioma, usar só os símbolos (♪ e —).

## O que entregar
1. `docs/tarefas/028-analise.md`, com:
   - cada endereço novo e sua prova;
   - as respostas de (a) e (b);
   - o tamanho do código e do buffer;
   - o custo de CPU do timer.
2. A receita `reload_3.5` = a da 3.3 + o player na home, e a folha nova dos ícones gerada por ferramenta, com o PNG de referência.
3. **Primeiro um kit de diagnóstico** `Reload 3.5 Diag` para o decisor testar:
   - ligar;
   - tocar e voltar à home;
   - pular rápido estando na home;
   - deixar a música avançar sozinha;
   - pausar;
   - ficar sem música;
   - abrir os jogos.
4. Só depois do teste do decisor: o kit público da 3.5.
5. Testes no computador (estáticos e unicorn) e `sh tools/ci.sh` verde.

Regras de sempre:
- Nunca alterar `firmware/ORIGINAL`, gravar no aparelho, fazer push ou merge.
- Testes protegidos intactos; nada abaixo de `0xE000`; setor `0xD000` e PSMP intocados.
- Classificar tudo como CONFIRMADO, PROVÁVEL ou HIPÓTESE.

Sinal final sozinho numa linha: `PRONTO-028` ou `ESCALADA-028`.
