# Ficha 020 — Estudo do projeto SL6801_player (referência externa)

Tipo: **Análise** (só leitura; nenhuma imagem, nenhum patch). Base: `privado-completo`. Desenvolvedor: `opencode/deepseek-v4.1-flash-free`.
Pedido do decisor (2026-11-17): olhar o projeto e, se for bom, trazer as coisas que fazem sentido para o OpenPod.

## A referência
- `github.com/dbrant/SL6801_player` (u/dmitrybrant no r/mp3players). Clonado em `referencias/SL6801_player/` neste worktree, fora do
  commit.
- Outro aparelho da mesma família: chip SL6801, firmware `yp3_2.0.43`, mesmo corpo com a roda do "M". Mas é **outra compilação**:
  - a home tem "Apps" no lugar de Imagens;
  - os endereços são outros: lá `lv_img_set_src` = 0xD3E77C; no GN-438, 0xD5D868.
- **O repositório não tem licença** (todos os direitos reservados): **não copiar código, nem trecho**. Só fatos e ideias.
  Tudo que entrar no OpenPod sai do **nosso** ORIGINAL, com desmontagem própria, como sempre.

## Perguntas
Para cada descoberta dele, dizer:
- se **existe no GN-438**, com o endereço e a instrução **no nosso ORIGINAL**, achados por strings, padrões ou chamadas;
- **CONFIRMADO, PROVÁVEL ou HIPÓTESE**;
- se é útil para o OpenPod, com risco e custo.

1. **Camada do sistema (OS):** `fw_os_sleep(ms)`, `fw_task_create`, semáforos, `fw_os_calloc/free`.
   - Achar os equivalentes no GN-438. A ficha 015 não achou o "dormir".
   - Isso permitiria pausas reais no decode da capa ou uma tarefa própria para a capa.
2. **Tarefa da tela:** ele mediu que mexer em `/dev/audio0` dentro da tarefa da UI trava ~10 s e reinicia.
   - Comparar com as nossas fichas 011–014 (arquivo na ViewTask trava).
   - Há uma causa comum que dê para provar?
3. **Vídeo espelhado:** o player de vídeo dele espelha a imagem na horizontal.
   - O GN-438 tem o mesmo código? Onde se decide o sentido da cópia da imagem do JPEG (libjpeg) para a tela?
   - Existe correção de poucos bytes?
4. **Funções escondidas:** senha ao ligar (0x4F/0x50), dicionário (0x37/0x38), luz das teclas (0x4B), "expand home" (0x51).
   - Existem no GN-438?
   - O que custaria ligar cada uma num menu? Nenhuma implementação agora.
5. **Fonte:** caracteres que faltam na fonte da UI (`°`, `¡`, `¿` e letras polonesas e romenas). Quais faltam no GN-438? Algum aparece
   nos nossos textos em português?
6. **Regras do vídeo:** extensão `.avi`, MJPEG, exatamente 128×160, áudio estéreo, blocos ≤ 30 KB. Valem no GN-438? Servem para uma
   seção de ajuda no site.
7. **ROM do chip:** ele sugere `smtlink_dump init read_mem 0 0x10000 rom.bin`.
   - Avaliar o risco: é só leitura?
   - O que ela responderia das nossas perguntas abertas: o mutex, o tick, o `0x80DB48`?
   - **Ninguém executa nada no aparelho**: isso fica para o decisor.
8. **SDK em C:** ele compila C que roda direto da flash livre, chamando o firmware por endereço.
   - Comparar com o nosso assembly: vantagens, riscos e reprodutibilidade (compilador com versão fixa).
   - Recomendação para as próximas fichas.

## O que entregar
1. `docs/tarefas/020-analise.md`:
   - uma tabela "descoberta → existe no GN-438? (endereço nosso) → classe → vale para o OpenPod? → risco/custo";
   - as recomendações em ordem de valor.
2. Nada mais. Sem patch, sem imagem, sem kit.
   - O `.gitignore` do worktree passa a ignorar `referencias/`.
   - Commit só da análise e do `.gitignore`.

Regras: nunca alterar `firmware/ORIGINAL`, nunca gravar no aparelho, nunca copiar código da referência. Não usar `cd` nem caminho
absoluto; nada em `/tmp`.

Sinal final sozinho numa linha: `PRONTO-020` ou `ESCALADA-020`.
