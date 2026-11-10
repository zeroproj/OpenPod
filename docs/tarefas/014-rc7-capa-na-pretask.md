# Ficha 014 — RC7: ler e decodificar a capa na PreTask (degraus B6a e B6b)

Tipo: **Risco**. Base: `privado-completo`. Desenvolvedor: `opencode/deepseek-v4.1-flash-free` (fluxo em teste, `docs/processo.md`).

Antes de começar, ler:
- `docs/tarefas/013-analise.md` inteiro: resultados do B5a/B5b e as referências no fim.
- `013-revisao.md`.
- `012-analise.md`.
- `007-rc7-capa-album.md` §3: o contrato da capa.
- `010-analise.md` D2 a D5.
- `tools/diag_b4.s`, `tools/fab_diag_b4.py`, `tools/diag_b5.s`, `tools/fab_diag_b5.py`.

## Fato (aparelho)
| Versão | Quem abre arquivo | Resultado |
|---|---|---|
| B | ViewTask (`get_path` dentro do `label_process`) | Reinicia |
| B4 | **PreTask** (o `get_path` da fábrica na rajada) + mensagem tipo 5 | **Toca; "No data"; tudo normal** |
| B5a | ViewTask: `f_open` + 10 B + `f_close` no tipo 5 | Trava ao selecionar e reinicia |
| B5b | ViewTask: `carrega_capa` no tipo 5, monitor desligado | Abre o player, trava, reinicia (às vezes na hora, às vezes ~24 s) |

**Regra que sai disso: a ViewTask não pode tocar em arquivo.** A PreTask abre o banco a cada play, durante a música, sem travar.
A fábrica decodifica fotos numa tarefa própria (`_pic_proc_`) e para a música para abrir foto (`0xC5CFC7`).

## Perguntas (só leitura do ORIGINAL)
Classificar cada resposta como CONFIRMADO, PROVÁVEL ou HIPÓTESE, com endereço e instrução em cada afirmação.

1. **Monitor:** a PreTask é monitorada? `0xD46BEC` registra o id 9 ("manager") e o id 3 (view). Qual tarefa é o id 9? Se for a PreTask, o
   decode nela precisa do mesmo par desregistrar/registrar (`0xD6AE38(9)`, `0xD46ACC`, `0xD46A20(desc+0x50)`), com volta em todos os caminhos.
2. **Pilha:** a PreTask tem pilha `0x800`.
   - Quanto já está em uso no ponto da rajada (`0xCFF0A8` chamado de `0xD0ED0C`)?
   - Quanto o `carrega_capa` (`0xDAA256`) mais `jd_prepare`/`jd_decomp` usam no pior caso?
   - Medir no emulador: SP mínimo, com capa 500×500 e 1000×1000, baseline.
   - Exigir folga de pelo menos 512 B. Se não couber: **ESCALADA-014**.
3. **Por que a fábrica para a música para abrir foto:** o `JpegDec*`/`_pic_proc_` (libjpeg) disputa algo com o decodificador de áudio (memória,
   hardware)? O TJpgDec da RC7 (`0xD10B20`/`0xD11090`) é outro decodificador. Ele depende do mesmo recurso? Responder com prova ou "não dá para
   saber".
4. **Entrega dos pixels à view sem estado compartilhado.** Avaliar, com prova, e escolher:
   - (i) **Mensagens em pedaços:** 8 mensagens classe 3 tipo 6 de 1024 B cada (64×64×2 = 8192 B).
     - A view copia cada pedaço para `ext+0x210+offset` e, no último, faz `img_set_src(img, ext)`.
     - O comprimento vai em `msg+0xA` sem `strlen` (os pixels têm zeros).
     - Conferir o limite da mensagem (`0x414`) e o espaço no ring da view (15360 B, `010-analise`).
   - (ii) **Ponteiro com dono:** a PreTask aloca o buffer e manda o ponteiro; a view copia e libera.
     - Provar que o buffer é liberado em TODOS os casos, inclusive quando a página não é o player ou a mensagem não chega ao `label_process`.

   Sem prova de liberação, (ii) é proibido. Proibido também: RAM nova sem prova; flash XIP como variável; a PreTask escrever na ext da view.

## O que entregar
1. `docs/tarefas/014-analise.md`, curto: respostas e o que não dá para saber.
2. **Duas** imagens, ambas = B4 exata (imagem sem carimbo `39bea488…`), com o trabalho de arquivo **só na PreTask**, dentro do `envia_path`
   (`0xDAAC00`), depois do `get_path`. A ViewTask **não** chama nenhuma função de arquivo.
   - **B6a — só abrir, na PreTask.**
     - No caminho válido: `f_open(caminho, 1)`, `f_read` de 10 B, `f_close`, free.
     - Começou com `"ID3"` → envia o tipo 5 com o caminho, como o B4. A view já mostra "No data".
     - Qualquer falha → envia o tipo 5 vazio (cinza).
     - **A view fica idêntica à do B4.**
   - **B6b — capa completa, na PreTask.**
     - Alocar um contexto temporário com o layout da ext da RC7 (`0x2210` B, `calloc`) e copiar o caminho para `+0x110`.
     - Chamar o `carrega_capa(tmp)` da RC7, intacto. Com o monitor, se a pergunta 1 mandar.
     - No sucesso, entregar os pixels de `tmp+0x210` pelo mecanismo da pergunta 4. Liberar o `tmp` em todos os caminhos.
     - Na falha: tipo 5 vazio (cinza).
     - A view só copia pixels de mensagem para a ext e faz `img_set_src`. Nenhuma função de arquivo.
3. Receitas `reload_1.0_rc7_diag_b6a` e `reload_1.0_rc7_diag_b6b`, premissas de entrada conferidas, testes em `tests/test_diag_trava.py`:
   - Bit Thumb; tabelas alinhadas; XIP só leitura.
   - Pilha medida (pergunta 2).
   - Nenhuma chamada de arquivo saindo do código da view, por teste estático: `f_open`/`f_read`/`f_lseek`/`f_close`/`carrega_capa` só são
     alcançáveis a partir do `envia_path`.
   - Capa válida/progressiva/PNG/sem capa/sem tag; página que não é o player; liberação de memória em todos os caminhos.
4. Kits por `gera_versao` **com a base padrão (ORIGINAL)**:
   - Carimbos `RC7 diag B6a`/`RC7 diag B6b`, com `patch_versao --em 0x1A4F00`.
   - Pastas `release/OpenPod-Reload-1.0-RC7-Diag-B6a`/`-B6b`, cada uma com `TESTAR.txt` curto, com a contagem de bytes contra o B4 medida
     entre imagens carimbadas.

Ordem no aparelho (decisor): **B6a primeiro**. Ela prova que abrir arquivo na PreTask, durante a música, não trava. Depois, a B6b.

Regras de sempre:
- Nunca alterar `firmware/ORIGINAL`, gravar no aparelho, fazer push ou merge.
- Testes protegidos intactos; ferramenta nova ≤ 350 linhas.
- Nada abaixo de `0xE000`; setor `0xD000` e PSMP intocados; `sh tools/ci.sh` verde.
- Todo destino de `bx`/`blx` com bit Thumb; o lr salvo por `bl` chega com bit0=1.
- Não usar `cd` nem caminho absoluto; arquivos temporários só dentro deste diretório e fora do commit.

Sinal final sozinho numa linha: `PRONTO-014` ou `ESCALADA-014`.
