# Ficha 012 — RC7: o caminho completo da faixa vindo da MainTask (degrau B4)

Tipo: **Risco**. Base: `privado-completo`. Desenvolvedor: `opencode/deepseek-v4.1-flash-free` (fluxo em teste, `docs/processo.md`).
Antes: `docs/tarefas/011-analise.md` (inteiro, com "Resultado do B3 no aparelho"), `011-revisao.md`, `011-revisao-nvidia.md`.

## Fato (aparelho)
| Versão | O que tem | Resultado |
|---|---|---|
| B | TITULO chama `get_path` na ViewTask | Reinicia |
| B2 | B + monitor neutralizado | Congela ~15 s e reinicia |
| B0 | `get_path` cortado | Toca, cinza |
| B3 | TITULO lê o texto do rótulo 2 (`[[r6+8]+0x24]`) | **Toca, sem travar, com o cinza**: o texto não começa com `0:/` nem `0:\` |

Conclusão de trabalho: o `get_path` não pode rodar na ViewTask. O caminho completo tem de chegar pronto à view.

## Perguntas (só leitura do ORIGINAL; CONFIRMADO/PROVÁVEL/HIPÓTESE; endereço e instrução em cada afirmação)
1. **O que é o texto do rótulo 2?** O `0xD084F8` recebe `[evento+0x14]` em `0xD088D4`. De onde vem esse campo (quem monta o evento do
   `page4_media_cb` `0xD088B4`) e o que ele contém: nome da pasta, nome do arquivo, caminho com outro prefixo? Que rótulo da tela é esse?
2. **O caminho que a MainTask já calcula.** Em `0xD088DC` a rajada chama `0xCFF2A4` → `0xCFF0A8`, que aloca 0xFF bytes (`0xCF780C`), chama o
   `get_path` (`0xCFF0C0`) e depois libera. Confirmar: roda na MainTask, a cada play, **antes** do título (`0xD088E8`) e também nos fluxos
   `0xD08BE2`/`0xD09014` (que chamam `0xCFF2A8`/`0xCFF23C`)? Qual o formato do caminho devolvido (prefixo, barra)?
3. **Como entregar esse caminho à view sem RAM nova e sem tocar na ext pela MainTask.** Avaliar, com prova, nesta ordem:
   a. Enviar pela fila da view uma mensagem da própria fábrica (a mesma infraestrutura de `0xD084F8`/`0xD0D818`), da MainTask, logo depois do
      `get_path` de `0xCFF0C0`, de um jeito que a view guarde o caminho sem mudar o que aparece na tela (ex.: um rótulo que a Tocando Agora não
      mostra, ou um tipo de mensagem que o hook do TITULO reconheça). Mostrar o tamanho, o tipo e o caminho da mensagem até a ViewTask.
   b. Outro mecanismo da fábrica que leve dados da MainTask à view com cópia (nada de ponteiro para buffer que a MainTask libera).
   Proibido: escrever na ext da view a partir da MainTask; endereço de RAM sem prova de que ninguém usa; flash XIP como variável.
   Se nada fechar com segurança, **ESCALADA-012** com as opções e os riscos.
4. **Ordem e faixa anterior:** o caminho tem de chegar à view antes do título da mesma faixa, em todos os fluxos que montam o título
   (`0xD088E8`, `0xD089A0`, `0xD08BE2`, `0xD09014`). Onde não chegar, o B4 tem de mostrar o cinza, não a faixa anterior.

## O que entregar
1. `docs/tarefas/012-analise.md`, curto, com as respostas e o que não dá para saber.
2. **Uma** imagem **B4** = RC7 exata (`3af97713…`) + o mecanismo escolhido + o TITULO lendo o caminho entregue em vez do rótulo 2, com as
   guardas de nulo e de prefixo do B3. Caminho válido = **sem** o quadrado (src nulo); inválido, vazio ou ausente = cinza. Sem `f_open`, sem JPEG.
   Receita `reload_1.0_rc7_diag_b4`, premissas de entrada conferidas, testes em `tests/test_diag_trava.py` (inclusive XIP só leitura no emulador,
   caminho válido/ inválido/ ausente, e a mensagem da MainTask sem o título depois), kit por `gera_versao`, carimbo `RC7 diag B4` com
   `patch_versao --em 0x1A4F00`, `release/OpenPod-Reload-1.0-RC7-Diag-B4` com `TESTAR.txt` curto (toca? sem o quadrado? trocar de faixa;
   volta de segurança: RC6). Contagem de bytes contra a RC7, não contra outro degrau.

**Não** ligar `f_open`/JPEG nem implementar a correção final. Regras de sempre: nunca alterar `firmware/ORIGINAL`, gravar no aparelho, push, merge;
testes protegidos intactos; ferramenta nova ≤ 350 linhas; nada abaixo de `0xE000`, setor `0xD000` e PSMP intocados; `sh tools/ci.sh` verde.
Não usar `cd` nem caminho absoluto; arquivos temporários só dentro deste diretório e fora do commit.
Sinal final sozinho numa linha: `PRONTO-012` ou `ESCALADA-012`.
