# Objetos de imagem — MEDIDO E CONFIRMADO

> 2026-09-18. Três itens do Marte estavam parados pela mesma frase —
> *"o layout do descritor de imagem não está medido"*. Está medido.

---

## 1. Por que isso destravou

O aparelho **já desenha imagem**: o papel de parede azul da tela Tocando
Agora é uma `lv_img_dsc_t` posta com `lv_img_set_src`. Se ele desenha, o
descritor está no binário para ser lido — não era preciso medir nada no
hardware.

Desbloqueia de uma vez:

| | |
|---|---|
| **M-g** | bateria em bitmap |
| **M-h** | degradê da faixa |
| **capa** | a arte do álbum na tela Tocando Agora |

---

## 2. O descritor — 12 bytes

```c
typedef struct {            // lv_img_dsc_t, LVGL v8
    uint32_t header;        // +0x00  campo de bits
    uint32_t data_size;     // +0x04  bytes de dados
    const uint8_t *data;    // +0x08  ponteiro XIP (0x00C00000 + offset)
} lv_img_dsc_t;
```

`header`, do bit 0 para o 31:

```text
cf            5 bits    formato de cor
always_zero   3 bits    sempre 0 — é a âncora da busca
reserved      2 bits
w            11 bits    largura
h            11 bits    altura
```

### Tamanho dos dados

```text
TRUE_COLOR          w * h * 2
TRUE_COLOR_CHROMA   w * h * 2       RGB565 com cor-chave
TRUE_COLOR_ALPHA    w * h * 3
INDEXED_8BIT        1024 + w * h    paleta BGRA de 256 entradas, depois 1 byte/px
INDEXED_4BIT          64 + ceil(w/2) * h
ALPHA_8BIT          w * h
```

### Os dados ficam logo depois do descritor

Nas oito imagens de fábrica, sem exceção: `data == descritor + 12`.

---

## 3. As oito imagens do firmware

| descritor | formato | tamanho | dados | o que é |
|---|---|---|---|---|
| `0x0C235C` | TRUE_COLOR_CHROMA | 50×50 | `0x0C2368` | — |
| `0x0C36F0` | TRUE_COLOR_CHROMA | 50×50 | `0x0C36FC` | — |
| `0x0C4A84` | TRUE_COLOR_CHROMA | 50×50 | `0x0C4A90` | — |
| `0x0C5E18` | TRUE_COLOR_CHROMA | 50×50 | `0x0C5E24` | — |
| `0x0C71AC` | TRUE_COLOR_CHROMA | 16×16 | `0x0C71B8` | — |
| `0x0C73B8` | INDEXED_8BIT | 128×160 | `0x0C73C4` | **papel de parede** (swoosh azul) |
| `0x0CC7C4` | INDEXED_8BIT | 128×35 | `0x0CC7D0` | logotipo GENAI |
| `0x0CDD50` | INDEXED_8BIT | 128×160 | `0x0CDD5C` | **folha com os 9 ícones** do menu de fábrica |

---

## 4. Como isso foi confirmado

**Não por autoconsistência.** A varredura (`tools/mede_img_dsc.py`) exige
quatro condições independentes: `always_zero == 0`, formato conhecido,
ponteiro dentro do arquivo, e `data_size` **igual ao previsto** por
largura, altura e formato.

As oito achadas batem exatamente com o inventário que o
`GUI_ANALYSIS.md` já trazia, levantado por outro caminho.

**E a prova final é visual:** o papel de parede foi decodificado
(paleta BGRA → RGB) e renderizado. É o mesmo swoosh azul que aparece na
foto da tela Tocando Agora do aparelho. A folha de ícones rende os nove
ícones circulares da tela inicial de fábrica.

---

## 5. O que isso permite construir

Uma imagem nova é **descritor de 12 B + dados**, na área livre, e uma
chamada a `lv_img_set_src` apontando para o descritor.

Custos, para 128 px de largura:

| alvo | formato | bytes |
|---|---|---|
| faixa 128×16, degradê vertical | INDEXED_4BIT (≤16 tons) | 64 + 1024 = **1.088** |
| faixa 128×16, cores livres | TRUE_COLOR | 4.096 |
| bateria ~15×8 | TRUE_COLOR_CHROMA | 240 |
| capa 50×50 | TRUE_COLOR_CHROMA | 5.000 |

O degradê vertical da faixa tem no máximo 16 tons — um por linha. Cabe
em `INDEXED_4BIT` com folga.

---

## 6. O que continua em aberto

**A capa de álbum não é só isto.** O objeto de imagem resolve *onde
desenhar*. Continuam sem medição:

1. o parser de ID3 do firmware lê o quadro **APIC**, onde a capa mora?
   Não há evidência. **NÃO RESOLVIDO**;
2. o decodificador JPEG (`JpegDecInit`, derivado de libjpeg) escreve
   direto no framebuffer ou num buffer que dê para compor? **NÃO
   RESOLVIDO**;
3. RAM para a decodificação — 50×50 em RGB565 são 5 KB e cabem; uma JPEG
   grande decodificada inteira, não.

**E uma decisão de projeto, não de engenharia:** o degradê do M-h, como
o Marte o define, é **claro**. O OpenPod inverteu a luminância de
propósito (`MARTE_ALVO.md`). Um degradê claro na faixa reintroduz
exatamente o fundo que faz o painel mostrar faixas horizontais.

**E o crédito CC-BY-SA.** Enquanto forem valores de cor medidos, não há
obrigação. O primeiro pixel do NanoClone gravado no firmware obriga o
crédito na tela Sobre.

---

## 7. Ferramenta

```sh
python3 tools/mede_img_dsc.py firmware/ORIGINAL/GN438_original.bin
python3 tools/mede_img_dsc.py <fw> --em 0x000C73B8
```
