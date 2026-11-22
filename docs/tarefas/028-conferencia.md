# 028 — conferência da coordenação (2026-11-22): REPROVADO

Imagem conferida: `reload_3.5` `f0faee10…`. Duas compilações dão o mesmo sha. O kit difere da imagem só no carimbo. O ORIGINAL está intacto.
Desmontagem feita na imagem real com capstone.

## CRÍTICO 1 — o gancho da home destrói o LR (a ViewTask entra em laço)
- A `page_home_label_process` (`0xD2EEC4`) é uma função **folha**: não tem `push` e sai com `bx lr` em `0xD2EEFC`.
  Ela também sai pelos `b.w` de cauda em `0xD2EEDA`.
- A 3.5 troca `0xD2EEE4` (`ldr r3,[pc]; ldrb r3,[r3]`) por **`bl 0xDAB700`**. O `bl` grava `LR = 0xD2EEE9`, e o LR de quem chamou se perde.
- O wrapper faz `push {r0-r4,lr}` / `pop {r0-r4,lr}` e devolve esse mesmo LR já estragado.
- Resultado: o `bx lr` de `0xD2EEFC`, ou a volta da cauda em `0xD2EEDA`, salta para `0xD2EEE8`. Ali o `cmp r3,#3`/`bne` leva de novo ao `bx lr` →
  **laço infinito na ViewTask**, sempre que chega uma mensagem tipo 3 com a home aberta. A troca de faixa com o usuário na home trava a interface.
- **Erro a mais:** o original faz `r3 = byte [0x823EB0]`, e o wrapper deixa `r3 = 0x00823EB0`, o endereço, sem o `ldrb`.
  O `cmp r3,#3` muda de resultado.

## CRÍTICO 2 — o gancho do título pula o TITULO da capa (a capa some)
- Na 3.3, `0xD3225E` é `b.w 0xDAA014`: a entrada **TITULO** da capa (ficha 007), que vai para `0xDAA0E6` e carrega a capa a cada título.
- A 3.5 troca por `b.w 0xDAB600`, e o `fw_player_title_hook` termina em `bx 0xD5ED95` (`lv_label_set_text`) → **a capa do álbum nunca mais
  carrega**. É uma regressão da 2.0.
- O frame em si está certo: `push {r4,r5,r7,lr}`/`pop` e saída por cauda com o LR de quem chamou.

## Por que os testes passaram
Os testes não executam a `page_home_label_process` real a partir de um chamador real, nem o caminho título → TITULO. É a mesma lição da 025.

## ALTA — a análise exagera a resposta (a)
A home **trata** o tipo 3 (`0xD2EEDE`). Isso mostra que ela *pode* receber a mensagem, não que a CPU0 a *mande* com a página 4 fechada.
Classificar como **PROVÁVEL**. O kit Diag responde no aparelho, no passo "deixar a música avançar sozinha na home".
