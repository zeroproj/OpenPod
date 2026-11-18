# Ficha 022 — OpenPod Reload 3.1 (parte 1): o SDK em C e os jogos

Tipo: **Risco + Pesada** (código novo grande; vai ao aparelho e ao público). Base: `privado-completo` (Reload 3.0).
Desenvolvedor: `opencode/deepseek-v4.1-flash-free`.

Decisão do decisor (2026-11-17): a 3.1 traz **os jogos** (esta ficha) e a **capa numa tarefa própria** (ficha 023).
**Permissão do autor (D15):** o código do `SL6801_player` pode entrar no OpenPod, com crédito a **Dmitry Brant** no site e nos
READMEs.

Antes de começar, ler:
- `docs/tarefas/020-analise.md` inteiro: §1 camada de SO, §2 regra da tarefa de UI, §8 SDK em C, §9 Apps.
- `docs/tarefas/021-analise.md` inteiro: Apps = página 0x53, criador `0xD2F0A0`, evento `0xD2EF5C`, itens [7,4,11].
- `docs/decisoes.md` D15.
- A referência em `referencias/SL6801_player/`, no commit `0361e2c`: `README.md`, `sdk/` inteiro, `sdk/include/fw.h`,
  `sdk/app.ld`, `sdk/build.py`, `sdk/patches.json`, `sdk/apps/`.
  - Clonar com `git clone https://github.com/dbrant/SL6801_player.git referencias/SL6801_player` e `git -C … checkout 0361e2c`.
  - Fica fora do commit (`referencias/` no `.gitignore`).
  - **Não executar** nenhum script da referência; ler e portar.

## Compilador (fixo)
- `python3 -m ziglang cc` com **ziglang 0.13.0** (pip), já instalado na máquina.
- Flags no espírito da referência: `-target thumb-freestanding-eabi -mcpu=cortex_m4 -mfloat-abi=soft -Os -ffreestanding -fno-builtin
  -nostdlib`, sem `.data`/`.bss`.
- **A mesma fonte tem de dar o mesmo binário, byte a byte**, em duas compilações: teste.
- Registrar a versão e as flags em `tools/` e no `CHANGELOG`.

## Mudança do decisor (2026-11-17)
Sem menu ou tela "Jogos": os jogos entram **direto como itens do menu Aplicativos**, como na referência. A ordem é Despertador, Imagem, Flutter, Mp3tris. O Dicionário sai se der com segurança; senão, fica no fim. O item 2 abaixo vale com essa mudança.

## O que fazer
1. **Portar o `fw.h` para o GN-438.**
   - Para **cada** função do firmware que o SDK e os apps usam, achar o endereço **no nosso ORIGINAL**: strings de assert/log, padrão
     de prólogo, quem chama. O endereço da referência não serve: é outra compilação.
   - Tabela em `docs/tarefas/022-analise.md` com: nome, endereço da referência, nosso endereço, evidência, CONFIRMADO/PROVÁVEL.
   - Função **sem prova não entra**: o app que depende dela fica de fora e vai para o registro.
2. **Gancho no menu Aplicativos (0x53).**
   - O 3º item (hoje Dicionário, página 0x37) vira **"Jogos"** (pt) / **"Games"** (en e os outros idiomas).
   - O texto é posto pelo nosso código no rótulo do item, depois que o criador de fábrica (`0xD2F0A0`) monta a tela; as tabelas de
     idioma não mudam.
   - O ENTER nesse item **não** navega para a 0x37: abre a nossa tela de jogos, uma lista com Flutter e Mp3tris, como overlay sobre a
     página, no padrão do SDK.
   - Esc volta ao menu Aplicativos.
   - Despertador e Imagem continuam iguais.
3. **Os jogos:** Flutter e Mp3tris, portados.
   - **Teclas** pelo grupo/`event_cb` do LVGL, nunca lendo o driver.
   - **Desenho** só na tarefa de UI.
   - **Tudo liberado** no `LV_EVENT_DELETE`.
4. **Som:**
   - **Só se fechar com prova as regras de segurança** (020 §2 e a referência): tocar e fechar numa **tarefa própria**; fechar só com o
     anel vazio; nunca escrever no áudio pela tarefa da UI; não abrir o áudio se a música estiver tocando.
   - **Na dúvida, os jogos saem sem som nesta versão**: escolher o caminho seguro e registrar.
5. **Local:** código na área livre `0x1AB000..0x1FC000`, num lote declarado no `MAPA` do `tools/build.py`. Os ganchos são `bl`
   conferidos, com o alvo original esperado, como os `patches.json` da referência.
6. **Degraus:**
   - **3.1a diag:** só o "Teste de teclas", da referência, no lugar dos jogos. Prova SDK, gancho, overlay, teclas e volta.
   - **3.1b:** os jogos.
   - Duas receitas: `reload_3.1a_diag` e `reload_3.1b`, ambas = `reload_3.0` + o SDK.

## O que entregar
1. `docs/tarefas/022-analise.md`: a tabela de funções, o gancho, a decisão do som e o que ficou de fora.
2. Fonte do SDK portado em `sdk/` deste repositório, com o cabeçalho de crédito:
   "baseado no SL6801_player de Dmitry Brant, usado com permissão".
   - Fonte, receitas e testes em `tests/test_reload_3_1.py`:
     - compilação reproduzível;
     - bit Thumb em todo ponteiro de função;
     - sem `.data`/`.bss`;
     - código dentro do lote;
     - cada endereço do `fw.h` aponta para um prólogo esperado no ORIGINAL;
     - ganchos conferidos;
     - a 3.0 continua igual fora do lote e dos ganchos;
     - nada abaixo de `0xE000`, nem no setor `0xD000`, nem na PSMP.
3. Kits por `gera_versao` **com a base padrão (ORIGINAL)**:
   - `release/OpenPod-Reload-3.1a-Diag`, carimbo `Reload 3.1a diag`;
   - `release/OpenPod-Reload-3.1b`, carimbo `Reload 3.1b`;
   - cada um com `TESTAR.txt` curto, e o Flashloader copiado de `firmware/VENDOR` para `windows/`.
4. README do pacote com a seção "New in 3.1" e o **crédito ao Dmitry Brant** (link do repositório). Texto neutro.
5. Entrada no `docs/CHANGELOG.md`.

**Não publicar.** Commit obrigatório antes do sinal.

Regras de sempre:
- Nunca alterar `firmware/ORIGINAL`, gravar no aparelho, fazer push ou merge.
- Testes protegidos intactos; `sh tools/ci.sh` verde.
- A ViewTask não toca em arquivo nem espera; todo destino de `bx`/`blx` com bit Thumb.
- Não usar `cd` nem caminho absoluto; nada em `/tmp`.

Sinal final sozinho numa linha: `PRONTO-022` ou `ESCALADA-022`.
