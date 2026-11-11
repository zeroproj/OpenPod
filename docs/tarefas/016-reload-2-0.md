# Ficha 016 — OpenPod Reload 2.0: a versão estável com a capa do álbum

Tipo: **Risco** (imagem que vai a todos). Base: `privado-completo`. Desenvolvedor: `opencode/deepseek-v4.1-flash-free`.
Nome decidido pelo decisor (2026-11-11): **OpenPod Reload 2.0**.

Antes de começar, ler:
- `docs/processo.md`.
- `015-analise.md`, com o resultado no aparelho.
- `015-revisao.md`.
- `014-analise.md`.
- `release/OpenPod-Reload-1.0-RC6/` inteiro: é o modelo de kit publicado.
- `docs/README_PUBLICO.md`.

## Fato (aparelho)
**Diag B7b**: a capa aparece rápido, sem engasgar a música; troca de faixa, parar, sair e entrar funcionam.

## Regra principal
**O código da 2.0 é byte a byte o do B7b**, que é o que foi provado no aparelho.
- Imagem sem carimbo `26ffa272…`, receita `reload_1.0_rc7_diag_b7b`.
- Muda **só** o carimbo de versão.
- Nada de limpeza, otimização ou "aproveitar para arrumar" no código.

Qualquer defeito encontrado nesta ficha vira **achado registrado**, não correção. A correção, se precisar, é outra ficha.

## Perguntas (só leitura e emulador)
1. **Avanço automático:** quando a música acaba e a próxima começa sozinha, a capa troca?
   - Qual fluxo da fábrica faz o avanço: um dos 5 chamadores da PreTask ou `0xCFF20E`/`0xD00C24`, que o `envia_path` pula?
   - Provar pelo código. Se o avanço não passar pela PreTask, registrar como achado (a capa da faixa anterior fica) e pôr no TESTAR.
2. **Trocas rápidas:** 8 mensagens tipo 6 por capa (8 × `0x414` B), no ring da view de 15360 B. Pular faixas rápido pode encher o ring?
   - Se encher, o `0xD0D818` devolve 0 e o B7b manda o cinza. O que acontece com as **outras** mensagens da fábrica nesse momento (título,
     tempo)?
   - Provar ou dizer "não dá para saber".
3. **Página errada:** sair do player no meio do carregamento. Mostrar que a guarda da view descarta os pedaços e que nada vaza na PreTask
   (o `tmp` é liberado).
4. **Tipos de capa:** baseline, progressiva, PNG, sem capa, sem tag, menor que 56 px, CMYK/escala de cinza.
   - O resultado esperado de cada uma, pelo emulador.

## O que entregar
1. `docs/tarefas/016-analise.md`, curto: as respostas e os achados.
2. Receita `reload_2.0` = **a mesma lista** da `reload_1.0_rc7_diag_b7b` (mesmo sha sem carimbo `26ffa272…`; teste que prova isso).
3. Kit por `gera_versao` **com a base padrão (ORIGINAL)**:
   - Carimbo **`Reload 2.0`** (o texto que aparece em Config → Informações; seguir o padrão da RC6, `"Reload 1.0 RC6"`), com
     `patch_versao --em 0x1A4F00`.
   - Pasta `release/OpenPod-Reload-2.0/` no mesmo formato da RC6: `README.md`, `install.sh`, `.up`, `cabo/`, `windows/`, `TESTAR.txt`.
4. **README público** (`release/OpenPod-Reload-2.0/README.md`):
   - Mesmo formato da RC6, texto **neutro**, sem marcas registradas (nada de "iPod" nem "Apple").
   - Novidade principal: **capa do álbum** na tela de reprodução, lida da etiqueta do MP3 (JPEG baseline embutido). O resto é igual à RC6.
   - Limitações honestas:
     - Só JPEG baseline embutido no MP3; capa progressiva, PNG ou ausente → quadrado cinza.
     - O que a pergunta 1 descobrir sobre o avanço automático.
   - Sem "Beta" se o decisor aprovar o teste; deixar o marcador para a coordenação ajustar.
5. **TESTAR.txt** = roteiro de regressão completo, para o decisor marcar ok/falhou:
   - Boot; home; menus; Música (artistas, álbuns, músicas, pastas); Tocando Agora com capa.
   - Músicas 01..07 de `tests/assets/rc7`; música sem capa; avanço automático; pular faixas rápido; sair e entrar 10 vezes.
   - Rádio FM; Bluetooth (parear e tocar); vídeo; fotos; gravação; eBook.
   - Atualizar por SD; bateria; desligar e ligar; Config → Informações = "Reload 2.0".
   - Volta de segurança: RC6.
6. Entrada no `docs/CHANGELOG.md`.

**Não publicar.** Push, tag e release só depois do teste completo do decisor e do "pode" dele.

Regras de sempre:
- Nunca alterar `firmware/ORIGINAL`, gravar no aparelho, fazer push ou merge.
- Testes protegidos intactos; nada abaixo de `0xE000`; setor `0xD000` e PSMP intocados; `sh tools/ci.sh` verde.
- Não usar `cd` nem caminho absoluto; nada em `/tmp`.

Sinal final sozinho numa linha: `PRONTO-016` ou `ESCALADA-016`.
