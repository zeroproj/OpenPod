# OpenPod — Reload 3.5 Diag

Firmware de **diagnóstico** da ficha 028 (player na tela inicial). A base é a
**3.3 publicada** (sha `368a7c8c…`); este kit existe para o decisor testar a
grade mais junta e o cartão fixo antes de qualquer kit público.

Imagem 3.5 (sem carimbo): `f49c8195…` · imagem carimbada: `95e45cd9…`.
O `.up` cobre a imagem inteira (`OpenPodReload3.5Diag.up`, 1.765.632 B,
CRC `0x9112`, sha `656dca30…`); o carimbo **"Reload 3.5 Diag"** fica em
`0x1A4F00` e o literal da tela Informações é repontado. A string original da
fábrica fica intacta.

O kit de **cabo** (`cabo/`) parte da 3.3 publicada e grava 15 setores
(60 KiB); o `install.sh` conduz o caminho Linux/macOS. O `.up` é o caminho
do cartão/Flashloader.

## O que muda

- Os 9 ícones da home ficam um pouco mais juntos: faixas em `19..52`,
  `58..93` e `97..132`; a tabela das molduras acompanha.
- Embaixo, um cartão fixo de `112x22` em `(8,136)` com o nome da música.
  Sem música, mostra **"Nada tocando"** (português) ou **"Nothing playing"**.
- O cartão não é selecionável e não entra no grupo: a navegação e as teclas
  da home não mudam.
- O título chega pela própria CPU1 (ViewTask), sem presenter da CPU0 e sem
  slot fixo de RAM; o estado mora no `user_data` de um timer do LVGL.
- O gancho da home é um **`b.w`** (não `bl`): o LR da `page_home_label_process`
  sobrevive. O gancho do título termina na cauda do **TITULO da capa**
  (`0xDAA014`), então a capa do álbum continua carregando.

## O que NÃO entra

- A capa do álbum no cartão (etapa 3).
- ▶/❚❚, tempo restante e barra (etapa 2; depende de provar a semântica de
  play/pause/stop).
- O kit público da 3.5: só depois do teste do decisor.

## Instalar

1. **Cartão:** copie `OpenPodReload3.5Diag.up` para a raiz do cartão,
   renomeando para `update.up`, e use a atualização por SD; **ou**
2. **Windows:** grave o `.up` com o Flashloader da Shenju (veja
   `windows/LEIA-ME.txt`); **ou**
3. **Linux/macOS:** `sh install.sh` (caminho de cabo, 15 setores).

Depois de atualizar, **apague o `update.up` do cartão**.
Confira `Configurar -> Informações`: **Reload 3.5 Diag**.

As configurações do aparelho (volume, EQ, idioma) são apagadas; a música do
cartão não é tocada.

## Testar

Siga o `TESTAR.txt`. Os dois pontos novos são **a capa do álbum ainda
aparece no player** e **trocar de faixa estando na home não trava**. O ponto
que precisa de medição é o **stop**: o cartão mostra o último nome ou "Nada
tocando"? O código não tem prova de que o título antigo deva sumir no stop; o
decisor mede.

## Segurança

- Nada abaixo de `0xE000`; setor `0xD000` e PSMP (`0x1FC000+`) intocados.
- O `.up` cobre até `0x1AF000`; a PSMP fica fora. CRC do payload: `0x9112`.
- O kit de cabo usa 15 setores e a reversão da 3.3 como base.

## Arquivos

```text
README.md                              este arquivo
TESTAR.txt                             roteiro de teste
install.sh                             Linux/macOS (cabo)
OpenPodReload3.5Diag.up                o firmware carimbado
LEIA-ME.txt                            o caminho de cabo (gerado)
cabo/flash_OpenPodReload3.5Diag.sh     grava os setores
cabo/setores/                          15 setores novos + base da 3.3
windows/LEIA-ME.txt                    o caminho Windows (Flashloader)
diag.sh / recovery_check_linux.sh      diagnóstico e conferência (só leitura)
```
