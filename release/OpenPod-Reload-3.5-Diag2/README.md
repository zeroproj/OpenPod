# OpenPod — Reload 3.5 Diag 2

Firmware de **diagnóstico** da ficha 028b (o nome da música no cartão da
home). A base é a **3.5 Diag** (kit anterior, testada pelo decisor em
22/11/2026); este kit existe para o decisor medir se o cartão da home
agora mostra **o nome da música** e não o contador da fila.

Imagem 3.5 Diag 2 (sem carimbo): `ba56813d…` · imagem carimbada:
`65fad72f…`. O `.up` cobre a imagem inteira
(`OpenPod_OpenPodReload3.5Diag2.up`, 1.765.632 B, CRC `0xC5C9`, sha
`3c71a462…`); o carimbo **"Reload 3.5 Diag 2"** fica em `0x1A4F00` e o
literal da tela Informações é repontado. A string original da fábrica
fica intacta.

O kit de **cabo** (`cabo/`) parte da 3.5 Diag e grava 5 setores
(20 KiB) — só o lote do SDK mudou. O `install.sh` conduz o caminho
Linux/macOS. O `.up` é o caminho do cartão/Flashloader.

## O que muda

- **O cartão da home mostra o nome da música.** Na 3.5 Diag o cartão
  mostrava `♪ 31/165`: o contador da fila. A causa está provada no
  ORIGINAL (ver `docs/tarefas/028b-analise.md`): a mensagem tipo 3 da
  fábrica traz o **índice do elemento** em `msg+4` — 1 é o título da
  faixa, 0 é o contador da fila — e a 3.5 copiava qualquer tipo 3 como
  título, de modo que o contador (que a fábrica manda logo **depois** do
  título) ficava por cima.
- O gancho da home passa a separar os dois: `msg+4 == 1` é o título,
  `msg+4 == 0` é o contador. O contador **não aparece** no cartão: ele
  só serve de sinal de troca de faixa.
- O gancho do título (o do player) filtra `[view+4]`, que é o rótulo do
  **título**; antes filtrava `[view+0]`, que é o rótulo do **contador**.
- **Nunca** o título de outra faixa: quando o contador muda e nenhum
  título novo chega, o título que temos é de outra faixa e some (o
  cartão volta a "Nada tocando").
- Fora disso, **é a 3.5 Diag byte a byte**: a grade mais junta, o
  cartão `112x22` em `(8,136)`, a capa do álbum do player, os jogos.

## O que NÃO entra

- A capa do álbum no cartão (etapa 3 da 028).
- ▶/❚❚, tempo restante e barra (etapa 2; depende de provar a semântica
  de play/pause/stop).
- O kit público da 3.5: só depois do teste do decisor.

## Instalar

1. **Cartão:** copie `OpenPod_OpenPodReload3.5Diag2.up` para a raiz do
   cartão, renomeando para `update.up`, e use a atualização por SD; **ou**
2. **Windows:** grave o `.up` com o Flashloader da Shenju (veja
   `windows/LEIA-ME.txt`); **ou**
3. **Linux/macOS:** `sh install.sh` (caminho de cabo, 5 setores).

Depois de atualizar, **apague o `update.up` do cartão**.
Confira `Configurar -> Informações`: **Reload 3.5 Diag 2**.

As configurações do aparelho (volume, EQ, idioma) são apagadas; a música do
cartão não é tocada.

## Testar

Siga o `TESTAR.txt`. O ponto novo é o **cartão da home**: com a música
tocando, ele deve mostrar **o nome da faixa**, e não `♪ 31/165`. Os
outros pontos continuam válidos da 3.5 Diag (a capa do álbum ainda
aparece no player; trocar de faixa na home não trava).

## Segurança

- Nada abaixo de `0xE000`; setor `0xD000` e PSMP (`0x1FC000+`) intocados.
- O `.up` cobre até `0x1AF000`; a PSMP fica fora. CRC do payload: `0xC5C9`.
- O kit de cabo usa 5 setores e a reversão para a 3.5 Diag como base.

## Arquivos

```text
README.md                              este arquivo
TESTAR.txt                             roteiro de teste
install.sh                             Linux/macOS (cabo)
OpenPod_OpenPodReload3.5Diag2.up       o firmware carimbado
LEIA-ME.txt                            o caminho de cabo (gerado)
cabo/flash_OpenPod_OpenPodReload3.5Diag2.sh   grava os setores
cabo/setores/                          5 setores novos + base da 3.5 Diag
windows/LEIA-ME.txt                    o caminho Windows (Flashloader)
diag.sh / recovery_check_linux.sh      diagnóstico e conferência (só leitura)
```
