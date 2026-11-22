# Ficha 028b — o nome da música no cartão da home (Reload 3.5)

Base: a 3.5 Diag, da ficha 028, que o decisor testou no aparelho em 2026-11-22.
Teste do decisor: "está tudo certo; só o player da tela inicial não mostra o nome da música".
- A grade junta, a moldura e o cartão estão certos, e nada travou.
- O cartão mostra **"♪ 31/165"**: o contador da fila, e não o título.

## Diagnóstico (PROVÁVEL)
- Com a home aberta, a mensagem tipo 3 que chega à `page_home_label_process` (`0xD2EEC4`) traz o **contador da fila** ("31/165") em
  `msg+0x14`, e não o título.
- O gancho da home (`fw_player_title_hook_home`) copia qualquer tipo 3 como título.
- Consequência boa: a home recebe mensagens com a música tocando, e o contador muda a cada faixa. É um sinal de troca de faixa que já
  temos na CPU1.

## O que fazer
1. **O título só vem do gancho do player** (`0xD3225E`, que já filtra `[view+0]`). O gancho da home deixa de gravar o título e passa a
   guardar o texto como **contador** (campo novo no estado).
2. **O cartão mostra só o nome da música** (decisor, D37: "vamos lançar a 3.5 só com o nome da música"). O contador **não aparece**; ele só serve de sinal de troca de faixa. Sem título conhecido, ou com o título antigo descartado, mostra "Nada tocando". Modelo: `assets/ideias/previa_35.png`.
3. **O título com a home aberta.** Este é o ponto que falta provar. Quando o contador muda e o título não veio, o título é de outra faixa.
   - Prove no ORIGINAL de onde a CPU0 tira o título na troca de faixa. Candidatos:
     - o presenter `0xD08448` (ficha 007, A3);
     - o buffer de onde o player copia o texto do tipo 3.
   - Se houver uma **cópia na RAM que a CPU1 pode só ler**, a home lê o título dali quando o contador muda.
   - Se não houver prova, o título antigo **some** quando o contador muda, e o cartão fica só com o contador até o player ser aberto. Nunca
     mostre o título de outra faixa.
4. Os testes no unicorn com a função real (lição da 025/028). Gere o kit **"Reload 3.5 Diag 2"**, carimbado.
5. Registre em `docs/tarefas/028b-analise.md` o que foi provado (CONFIRMADO / PROVÁVEL / HIPÓTESE).

Regras de sempre:
- nada abaixo de 0xE000; 0xD000 e PSMP intocados;
- CPU1 só lê memória e usa LVGL;
- sem gravar no aparelho, sem push nem merge;
- `sh tools/ci.sh` verde.

Sinal: `PRONTO-028b` ou `ESCALADA-028b` sozinho numa linha.
