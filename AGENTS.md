# OpenPod

> **Coordenação: comece por `docs/COMO-RETOMAR.md`** (quem é quem, as regras, as pastas, o que está no ar, como publicar e as pendências). Depois, **`docs/COORDENACAO-AGENTES.md`** (os agentes `desenvolvedor`, `desenvolvedor-go` e `revisor`, o ciclo da ficha e a troca de modelo quando a cota acaba).

Firmware do player **Iigenai GN-438** (Smartlink/YP3, `yp3_2.0.43`), modificado
em degraus a partir do firmware de fábrica. ARM Thumb-2, XIP em `0x00C00000`,
flash de 2 MiB, LVGL 8, FreeRTOS. Ferramentas em Python 3 (+ capstone, Pillow).

- Imagem de fábrica (só leitura): `firmware/ORIGINAL/GN438_original.bin`,
  sha256 `b7cd5eb9…`.
- Receitas: `python3 tools/build.py --receita <nome> --saida <arquivo>`.
- Testes e travas: `sh tools/ci.sh`.

## Review guidelines
Regras fixas para quem revisa este projeto (Codex/analista, só leitura). O
pedido de revisão traz só a ficha, o intervalo do diff e o foco.

- Responda em português. **Primeira linha: `APROVADO` ou `REPROVADO`**;
  reprova só com ALTA ou MÉDIA. Depois, achados com severidade,
  `arquivo:linha` e um cenário concreto. Conciso.
- **Bytes:** nenhuma escrita abaixo de `0xE000`; setor `0xD000` e PSMP
  (`0x1FC000+`) intocados; só os bytes que a ficha permite.
- **Premissas:** toda ferramenta confere no binário (bytes de fábrica, alvo
  dos `bl`, lotes `0xFF`, sha da entrada quando a ficha pede) **antes** de
  escrever, e recusa sem criar saída. `--out` igual/symlink/hardlink de
  `--in` é recusado.
- **Código novo na área livre:** endereço e tamanho declarados no `MAPA` de
  `tools/build.py`, sem cruzar outro lote; desvios Thumb decodificados de
  volta e conferidos; registradores preservados.
- **Kit:** `.up` igual à imagem pedida, CRC certo, PSMP fora.
- **Origem:** nenhuma ferramenta ou trecho das linhas Core/Alphas (listas
  PROIBIDAS dos testes), salvo exceção em `docs/decisoes.md`.
- **Testes de aceite** (`NÃO ALTERAR sem o arquiteto`) não podem mudar no
  diff do desenvolvedor.
