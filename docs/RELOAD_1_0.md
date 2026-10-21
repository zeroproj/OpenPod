# OpenPod Reload 1.0 — refeito do ORIGINAL, em degraus

> Aberto em 2026-09-24. Base: `GN438_original.bin` sha `b7cd5eb9...`
>
> **As Alphas 0.1 e 0.2 estão descartadas** — pedido do mantenedor:
> "não use as versões que foram geradas Alpha, essas coisas que estão
> bugadas". Nenhuma imagem, kit ou receita `reload_alpha*` entra na 1.0.
> `docs/RELOAD_ALPHA.md` fica só como histórico.

---

## 1. O que a 1.0 entrega

| # | Pedido | Ferramenta | Já rodou no aparelho? |
|---|---|---|---|
| 1 | Update por cartão SD | `patch_update_sd.py` | sim, linha Core |
| 2 | Logo do OpenPod na abertura | `patch_logo.py` | sim, V007 (autoteste reproduz byte a byte) |
| 3 | Fundo preto nas telas | `patch_fundo_display.py`, `patch_fundo_abertura.py`, `patch_fundo_preto.py` | só o `fundo_preto` (Beta 12); os outros dois nasceram nas Alphas |
| 4 | Barra superior com "OpenPod" | `patch_nome_faixa.py` | só nas Alphas — revisar |
| 5 | Degradê na barra | `patch_faixa_degrade.py` | só nas Alphas — revisar |
| 6 | Ícones da tela principal | `patch_icones_home.py` (novo) | não |
| 7 | Bateria casca prata + miolo verde | `patch_bateria_casca/verde/miolo.py` | sim, Beta 12 |

Fora da 1.0, de propósito: textos revisados (`aplica_textos.py`),
volume/brilho, e qualquer coisa da linha Core (Saturno, Marte, Extras).

## 2. Os degraus

Uma imagem por degrau. **O próximo só é gerado depois que o anterior
foi gravado e relatado.** Se algo quebrar, sabemos qual passo foi.

| Degrau | Receita | Conteúdo | Estado |
|---|---|---|---|
| RC1 | `reload_1.0_rc1` | 1 | **APROVADA no aparelho em 2026-10-21** (Flashloader, Windows; update por SD testado) |
| RC2 | `reload_1.0_rc2` | + 2, 3 | ficha `docs/tarefas/001-rc2-logo-fundo.md`, testes vermelhos |
| RC3 | — | + 4, 5 | não gerada |
| RC4 | — | + 6, 7 | não gerada; ferramenta dos ícones pronta |

Instalação: **1ª gravação por cabo**; todo kit leva também o `.up` para as
seguintes pelo cartão.

## 3. RC1

```sh
python3 tools/build.py --receita reload_1.0_rc1 --saida firmware/WORKING/GN438_reload_1.0_rc1.bin
python3 tools/patch_versao.py --in firmware/WORKING/GN438_reload_1.0_rc1.bin \
        --out firmware/WORKING/GN438_reload_1.0_rc1_carimbado.bin --texto "Reload 1.0 RC1"
python3 tools/gera_versao.py --imagem firmware/WORKING/GN438_reload_1.0_rc1_carimbado.bin \
        --versao OpenPod-Reload-1.0-RC1 --nome-tela "Reload 1.0 RC1"
```

| | sha256 |
|---|---|
| `GN438_reload_1.0_rc1.bin` | `a427c62ec7da0170ef4296ebda6a55ec5d287c4058d3c5a9e80e645f28e5c3f2` |
| `GN438_reload_1.0_rc1_carimbado.bin` | `a423e7ad9d94b80a68a6ac8adf081fd5341af598728de14ca4864d2bd694ab72` |
| `OpenPod_OpenPodReload1.0RC1.up` (CRC 0x7515) | `c4974029b45611b6d133ab17b851a02a2fe198ac3af2ffc17a4e4f04f91a6654` |

Diff contra o ORIGINAL: 77 B em 3 setores (`0x053000`, `0x109000`,
`0x1A3000`) + carimbo 18 B (`0x10A000`, `0x1A3000`). Validação: só a
falha esperada da R1. Bootloader, `0x00D000` e PSMP intocados.

**Atenção:** o script do cabo confere os setores `base_*` do ORIGINAL. Se
o aparelho estiver com Beta 12 ou Alpha, gravar antes
`release/OpenPod-Fabrica/` ou refazer o kit com `--base`.

## 4. Ícones da tela principal

A home desenha uma folha única INDEXED_8 128×160 em `0x0CDD50` com os
nove ícones em grade 3×3, 30 px cada (`docs/IMAGENS.md` §3). Centros
medidos na folha de fábrica: x = 22,5 · 63,5 · 104,5; y = 31,5 · 79,5 ·
127,5. A navegação é por índice (`docs/PLANO_HOME.md` §1.2) — trocar a
folha não toca nela.

Estilo aprovado pelo mantenedor em 2026-09-24, depois de três rodadas
(círculo prata+verde → quadrado → cores): **"Apple-like moderno"** —
squircle, degradê por função, símbolo branco, sem brilho. Desenho
próprio, em código; nenhum pixel da Apple nem da fábrica.

```sh
GLIFO=255,255,255 python3 tools/desenha_icones_home.py assets/IconesHome.png /tmp/ampliada.png
python3 tools/patch_icones_home.py --autoteste
python3 tools/patch_icones_home.py --in <entrada.bin> --out <saida.bin>
```

Autoteste: relido pelo cabeçalho == quantização; 0 bytes fora do slot;
242 cores; erro médio 1,23 por canal. Escreve 20.954 B em
`0x0CD000`–`0x0D3000` (7 setores), cabeçalho intocado.

Em aberto: Tocando agora e Livro estão ambos laranja (aprovado assim).

## 5. Pendências

- **Quais defeitos as Alphas mostraram** — decide se `patch_nome_faixa`,
  `patch_faixa_degrade`, `patch_fundo_display` e `patch_fundo_abertura`
  são reaproveitados ou reescritos antes da RC2/RC3.
- A barra com "OpenPod" fixo tira o ícone de cartão SD do centro.
