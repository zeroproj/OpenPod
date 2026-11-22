# OpenPod — Reload 3.5 Diag

Firmware de **diagnostico** da ficha 028 (player na tela inicial). A base e
a **3.3 publicada** (sha `368a7c8c…`); este kit existe para o decisor testar
a grade mais junta e o cartao fixo antes de qualquer kit publico.

O `.up` e a imagem carimbada com **"Reload 3.5 Diag"** na tela Informacoes.
O carimbo fica em `0x1A4F00` e o literal da tela e repontado; a string
original da fabrica fica intacta.

## O que muda

- Os 9 icones da home ficam um pouco mais juntos: faixas em `19..52`,
  `58..93` e `97..132`; a tabela das molduras acompanha.
- Embaixo, um cartao fixo de `112x22` em `(8,136)` com o nome da musica.
  Sem musica, mostra **"Nada tocando"** (portugues) ou **"Nothing playing"**.
- O cartao nao e selecionavel e nao entra no grupo: a navegacao e as teclas
  da home nao mudam.
- O titulo chega pela propria CPU1 (ViewTask), sem presenter da CPU0 e sem
  slot fixo de RAM; o estado mora no `user_data` de um timer do LVGL.

## O que NAO entra

- A capa do album (etapa 3).
- ▶/❚❚, tempo restante e barra (etapa 2; depende de provar a semantica de
  play/pause/stop).
- O kit publico da 3.5: so depois do teste do decisor.

## Instalar

1. Copie `OpenPod_OpenPodReload3.5Diag.up` para a raiz do cartao,
   renomeando para `update.up`, e use a atualizacao por SD; **ou**
2. grave o `.up` com o Flashloader da Shenju no Windows.
3. Depois de atualizar, **apague o `update.up` do cartao**.
4. Confira `Configurar -> Informacoes`: **Reload 3.5 Diag**.

As configuracoes do aparelho (volume, EQ, idioma) sao apagadas; a musica do
cartao nao e tocada.

## Testar

Siga o `TESTAR.txt`. O ponto que precisa de medicao e o **stop**: o cartao
mostra o ultimo nome ou "Nada tocando"? O codigo da 3.5 nao tem prova de que
o titulo antigo deva sumir no stop; o decisor mede.

## Seguranca

- Nada abaixo de `0xE000`; setor `0xD000` e PSMP (`0x1FC000+`) intocados.
- O `.up` cobre ate `0x1AF000`; a PSMP fica fora.
- CRC do payload conferido na geracao: `0xF2E8`.

## Arquivos

```text
README.md                              este arquivo
TESTAR.txt                             roteiro de teste
OpenPod_OpenPodReload3.5Diag.up        o firmware carimbado
install.sh                             instrucoes de instalacao
```
