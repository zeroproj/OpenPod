# Ficha 013 — RC7: abrir o MP3 e desenhar a capa (degraus B5a e B5b)

Tipo: **Risco**. Base: `privado-completo`. Desenvolvedor: `opencode/deepseek-v4.1-flash-free` (fluxo em teste, `docs/processo.md`).

Antes de começar, ler:
- `docs/tarefas/012-analise.md` inteiro, com "Resultado do B4 no aparelho".
- `012-revisao.md`.
- `007-rc7-capa-album.md`: o contrato da capa (ID3v2/APIC/JPEG baseline 64×64).
- `010-analise.md` D2 a D5: watchdog e monitor.
- `tools/diag_b4.s` e `tools/fab_diag_b4.py`: o B5 parte do B4.

## Fato (aparelho)
| Versão | O que tem | Resultado |
|---|---|---|
| B | TITULO chama `get_path` dentro do `label_process` | Reinicia |
| B2 | B + monitor neutralizado | **Congela ~15 s** e reinicia: trava de verdade, não lentidão |
| B3 | TITULO lê o rótulo 2 | Toca, cinza (o rótulo 2 não é caminho) |
| B4 | A rajada envia o caminho (classe 3, tipo 5); a view aplica | **Toca; o cinza vira "No data"** (`img_set_src(NULL)`, só no caminho válido). Troca de faixa, parar, sair e entrar: tudo normal |

O caminho completo já chega à view. Falta abrir o arquivo e desenhar a capa sem travar.

## Perguntas (só leitura do ORIGINAL)
Classificar cada resposta como CONFIRMADO, PROVÁVEL ou HIPÓTESE, com endereço e instrução em cada afirmação.

1. **Em que tarefa roda a rajada?** A `012-analise` afirma ViewTask. Provar subindo do `0xD0EED0` e do `page4_media_cb` `0xD088B4` até a função de
   entrada de uma tarefa criada pela fábrica, com o nome da tarefa. Dizer também se, nesse momento, o `label_process` `0xD32204` e o
   `lv_task_handler`/LVGL podem estar rodando ao mesmo tempo, na mesma tarefa ou em outra.
2. **Por que o B travou?** O `get_path` (`0xCFEFC4` → `0xD6D1B4` → `0xD6F138` → `0xD777CC` f_open) chamado de dentro do `label_process`
   congelou (B2). Pontos a responder:
   - Que trava ele pega: o mutex do banco `[0x81DC00]+0x5C` (`0x80DB48`/`0x80DB6E`), o `ff_req_grant` do FatFs `0xD77EA4`, ou outra.
   - Quem pode estar segurando essa trava enquanto espera algo da view.
   - Se a fábrica chama o mesmo `get_path` na rajada sem travar, qual é a diferença de contexto.
   - A resposta decide **onde** abrir o MP3.
3. **Onde abrir o MP3 e decodificar**, avaliando nesta ordem e com prova:
   a. **No contexto da rajada** (`envia_path`, depois do `get_path`), se for a mesma tarefa da view e fora do processamento do LVGL. Nesse caso,
      decodificar direto na ext da view atual (`[[0x81CE2C]+0xAC]+0x30`, com as mesmas guardas de nulo) e a mensagem tipo 5 só faz o
      `img_set_src(img, &ext->dsc)`.
   b. **No tratamento do tipo 5** (dentro do `label_process`), se a pergunta 2 provar que o `f_open` do MP3 não pega a trava que travou o B.
   c. Outro ponto da fábrica que já abre arquivo na mesma tarefa sem travar.

   Se nada fechar com segurança: **ESCALADA-013**.
4. **Watchdog:**
   - Estimar quanto tempo leva `f_open` + ID3 + `jd_prepare` + `jd_decomp` com escala `s`, para uma capa de 500×500 e de 1000×1000.
   - Comparar com o prazo do monitor (`010-analise` D2).
   - Se passar do prazo, usar o mesmo mecanismo da fábrica para tirar a tarefa do monitor durante o trabalho (`0xCFCA0E`/`0xCFCBC8`) e
     devolver depois, também nos erros. Provar que a volta acontece em todos os caminhos.

## O que entregar
1. `docs/tarefas/013-analise.md`, curto: as respostas e o que não dá para saber.
2. **Duas** imagens, ambas = B4 exata (o `.up` `16c4cf05…`, imagem sem carimbo `39bea488…`) + o ponto escolhido na pergunta 3:
   - **B5a — só abrir:** no caminho válido, `f_open(caminho, leitura)`, ler os 10 bytes do cabeçalho, `f_close`.
     - Cabeçalho começa com `"ID3"` → `img_set_src(img, NULL)` ("No data").
     - Qualquer falha → cinza.
     - Sem JPEG. Serve para provar que abrir o arquivo nesse ponto não trava.
   - **B5b — capa completa:** o contrato inteiro de `007-rc7-capa-album.md` §3, reaproveitando o código da RC7, que já está na imagem
     (`carrega_capa` `0xDAA256` e o que ele chama).
     - Mesmo caminho do último → não faz nada (`ext+0x10`, como a RC7).
     - Sucesso → `img_set_src(img, &ext->dsc)`. Qualquer falha → cinza.
     - Tudo liberado e o arquivo fechado em todos os caminhos.
3. Receitas `reload_1.0_rc7_diag_b5a` e `reload_1.0_rc7_diag_b5b`, premissas de entrada conferidas, testes em `tests/test_diag_trava.py`:
   - Bit Thumb em todo `bx`/`blx`; tabelas alinhadas; XIP só leitura no emulador.
   - Caminho válido/inválido; arquivo sem ID3; capa válida; capa progressiva, PNG ou pequena → cinza.
   - Monitor devolvido em todos os caminhos.
4. Kits por `gera_versao`:
   - Carimbos `RC7 diag B5a` e `RC7 diag B5b`, com `patch_versao --em 0x1A4F00`.
   - Pastas `release/OpenPod-Reload-1.0-RC7-Diag-B5a` e `release/OpenPod-Reload-1.0-RC7-Diag-B5b`.
   - Cada uma com `TESTAR.txt` curto: toca? aparece a capa? trocar de faixa; música sem capa; volta de segurança: RC6.
   - Contagem de bytes contra o B4.

Ordem no aparelho (decisor): **B5b primeiro**. Se travar ou reiniciar, o B5a separa "abrir o arquivo" de "decodificar".

Regras de sempre:
- Nunca alterar `firmware/ORIGINAL`, gravar no aparelho, fazer push ou merge.
- Testes protegidos intactos; ferramenta nova ≤ 350 linhas.
- Nada abaixo de `0xE000`; setor `0xD000` e PSMP intocados; `sh tools/ci.sh` verde.
- A flash XIP (`0xC00000..0xDFFFFF`) é só leitura.
- Não usar `cd` nem caminho absoluto; arquivos temporários só dentro deste diretório e fora do commit.

Sinal final sozinho numa linha: `PRONTO-013` ou `ESCALADA-013`.
