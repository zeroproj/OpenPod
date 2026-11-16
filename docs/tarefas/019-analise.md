# Ficha 019 — análise: limite de tamanho da capa (Reload 2.2.1)

Base: Reload 2.2 sem carimbo, sha
`4fdd31c03ad6672ca0b15b141345b7559b2517afca19f54de0d73753f842f769`.
Resultado sem carimbo:
`e477c1e78ac1c88db58d29b030f35d7f11c8d90f45ec695a9b63392ea9936402`.
A diferença contra a 2.2 fica em **58 bytes**: dois desvios de 4 bytes no
lote da capa e duas rotinas de 28 bytes na área livre do mesmo lote.

## 1. Onde o `carrega_capa` mede

`carrega_capa` em `0xDAA256`; `procura_apic` a partir de `0xDAA598`.
O quadro `APIC` termina em `fp = r5 + r8` (`0xDAA7D4`), com `r8` = tamanho
do quadro. O código de fábrica faz duas medidas:

| ponto | arquivo | bytes de fábrica | o que é | falha |
|---|---|---|---|---|
| bytes | `0x1AA882` (`0xDAA882`) | `ab eb 05 00` = `sub.w r0, fp, r5` | tamanho restante da imagem, logo antes de ler `FF D8` | `0xDAA8D6` |
| px | `0x1AA334` (`0xDAA334`) | `5f f0 00 0b` = `movs.w fp, #0` | depois do `jd_prepare` (`0xD10B20`), com `w` em `r0` (`[r8+0x1C]`) e `h` em `r1` (`[r8+0x1E]`) | `0xDAA3C6` |

O `sub.w r0, fp, r5` de `0xDAA858` é **outro**: fica dentro do laço do
cabeçalho estendido e não é tocado. O ponto certo é o de `0xDAA882`,
seguido de `cmp r0, #2` e da leitura de `FF D8` em `0xDAA89C..0xDAA8AA`.

Os dois destinos de falha são os caminhos de cinza que já existem:
`0xDAA8D6` devolve `r0 = 0`; `0xDAA3C6` libera o que foi alocado e
devolve `0`. Assim os caminhos novos não precisam de código de limpeza
próprio.

### Patch

- `0x1AA882`: `00 f0 05 fb` = `bl 0xDAAE90` (Thumb).
- `0x1AA334`: `00 f0 c4 fd` = `bl 0xDAAEC0` (Thumb).
- Rotinas em `0x1AAE90` (bytes) e `0x1AAEC0` (px), na área zerada
  `0x1AAE82..0x1AB000`. O lote continua `0x1A8000..0x1AB000`; nada abaixo
  de `0xE000`, setor `0xD000` e PSMP intocados.

## 2. Rotinas

### Bytes (`0x1AAE90`, 28 B)

```asm
sub.w r0, fp, r5        ; refaz o tamanho restante
movw  r1, #0x0000       ; 524288 = 0x80000
movt  r1, #0x0008
cmp   r0, r1
bhi   falha             ; imagem > 512 KiB
bx    lr                ; segue para 0xDAA886
falha:
movw  ip, #0xA8D7       ; 0xDAA8D6 | Thumb
movt  ip, #0x00DA
bx    ip
```

### Pixels (`0x1AAEC0`, 28 B)

```asm
movw  r2, #0x03E8       ; 1000
cmp   r0, r2
bhi   falha             ; w > 1000
cmp   r1, r2
bhi   falha             ; h > 1000
movs.w fp, #0           ; repõe o que a fábrica fazia
bx    lr                ; segue para 0xDAA338
falha:
movw  ip, #0xA3C7       ; 0xDAA3C6 | Thumb
movt  ip, #0x00DA
bx    ip
```

Os limites são `LIMITE_PX = 1000` e `LIMITE_BYTES = 512 * 1024`
(`524288`), constantes em `tools/limite_capa_asm.py` e passadas
explicitamente pela receita `reload_2.2.1`. A comparação é `>`: 1000 px
e 524288 B ainda passam.

## 3. Medição no emulador

Método: `carrega_capa` chamado direto em `0xDAA256`, com MP3 montado por
`tests/gera_mp3.py` (JPEG q95, 4:4:4, textura) e áudio de 6 s. A contagem
é de **instruções executadas**, com hook de bloco do Unicorn e cada bloco
decodificado pelo capstone; não é tempo de CPU. Uma execução por tamanho.

### 2.2, sem limite

| capa | JPEG | instruções | razão vs 300 | razão vs 500 | tempo* |
|---|---:|---:|---:|---:|---:|
| 300 px | 90.991 B | 24.047.828 | 1,00 | 0,61 | 1,78 s |
| 500 px | 176.492 B | 39.698.912 | 1,65 | 1,00 | 3,93 s |
| 640 px | 163.672 B | 41.189.341 | 1,71 | 1,04 | 4,29 s |
| 1000 px | 386.597 B | 102.000.622 | 4,24 | 2,57 | 10,98 s |
| 1500 px | 657.663 B | 191.145.821 | 7,95 | 4,82 | 20,50 s |
| 2000 px | 991.610 B | 308.828.110 | 12,84 | 7,78 | 33,30 s |
| 3000 px | 1.690.980 B | 600.251.999 | 24,96 | 15,12 | 59,48 s |

\* tempo de parede no host, só para ordem de grandeza.

300 e 500 px são as capas existentes de `tests/assets/rc7`; 640 px em
diante é gerado. O custo cresce muito mais que o número de pixels porque
o TJpgDec percorre o Huffman da imagem inteira, mesmo reduzindo a escala.

### 2.2.1, com limite

| capa | JPEG | instruções | resultado |
|---|---:|---:|---|
| 1000 px | 386.597 B | 102.000.635 | capa normal; mesmos pixels da 2.2 |
| 1200 px | 506.409 B | 10.817 | cinza; passou pelo `jd_prepare`, **sem** `jd_decomp` |
| 1500 px | 657.663 B | 766 | cinza; recusada **antes** de ler a imagem |
| 3000 px | 1.690.980 B | 766 | cinza; recusada **antes** de ler a imagem |

A capa de 1200 px tem 494,5 KiB: passa no limite de bytes e é recusada
pelo limite de pixels, depois do `jd_prepare`. As de 1500 e 3000 px
passam de 512 KiB e caem no primeiro limite, sem `jd_prepare`. O caminho
de recusa custa 766 instruções (1500/3000) e 10.817 (1200), contra
191.145.821 e 600.251.999 da 2.2.

### Aparelho (relato do decisor, 2026-11-15)

| capa | tamanho | resultado na 2.2 |
|---|---:|---|
| 640 px | ~173 KB | toca; o contador de tempo engasga enquanto a capa carrega |
| 1000 px | ~392 KB | toca; também engasga |
| 1500 px | ~842 KB | trava tudo |

Confirma a hipótese: 1000 px / 392 KB passa nos dois limites e é o maior
caso que ainda toca; 1500 px / 842 KB é recusado pelo limite de bytes.
O MP3 de 1500 px gerado aqui tem 642,2 KiB e também é recusado. O limite
não promete sumir com o engasgo de 1000 px; promete não travar.

## 4. Efeito e decisão

- **1000 px / 512 KiB** mantidos. Aceita o maior caso que toca no
  aparelho; recusa o caso que trava.
- 640 px e 1000 px continuam com os **mesmos pixels** da 2.2
  (`test_05`). A capa de 500 px não é comparada à referência de fábrica
  porque o B7 usa escala mínima 56 (s=3), enquanto a referência usa 64
  (s=2); a 2.2.1 é comparada com a 2.2.
- 1200 px, abaixo de 512 KiB, é recusada pelo limite de pixels: é
  intencional, para capas largas/altas com poucos bytes.
- O caminho de recusa usa os destinos de cinza existentes; `tmp` e FIL
  são liberados e o arquivo é fechado como nos outros caminhos de falha
  (conferido em `carrega`, usado pelos testes 05–07).

## 5. Testes e entrega

- `tests/test_reload_2_2_1.py`: 7 testes OK — bit Thumb/alinhamento,
  diferença só no lote da capa, capa dentro do limite com os mesmos
  pixels, acima em px, acima em bytes, vazamento e regiões proibidas.
- `tests/gera_mp3.py`: gera os JPEGs e MP3s dentro do teste, sem
  versionar arquivos grandes.
- Receita `reload_2.2.1` = `reload_2.2` + `fab_limite_capa.py`.
- Kit `release/OpenPod-Reload-2.2.1/`: base ORIGINAL, carimbo
  `Reload 2.2.1` em `0x1A4F00`; imagem carimbada `3a0236f5…`; `.up`
  1.749.248 B, CRC `0x03CF`, sha `0305cc2e…`. README e `TESTAR.txt`
  próprios.

## 6. Pendências e riscos

- **[BAIXA]** O `FlashloaderSL-DEV-6.9.5.exe` não está em
  `firmware/VENDOR/` (só os READMEs). O `windows/` do kit fica só com o
  `LEIA-ME.txt`, como já acontecia na 2.2; é pendência herdada da 018.
- **[BAIXA]** O limite é de segurança, não de desempenho: uma capa de
  1000 px ainda pode engasgar o contador no aparelho. A dica do README é
  reduzir as capas para ~300 px.
- **[BAIXA]** A contagem do emulador é de instruções, não de tempo real;
  o tempo de parede varia com o host e serve só para ordem de grandeza.
