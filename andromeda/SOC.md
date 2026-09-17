# ANDROMEDA — SOC

## Identificação do System-on-Chip do GN-438

---

## 1. Resumo executivo

| Propriedade | Valor | Confiança |
|---|---|---|
| Marcação física do chip | Jointbees MP3 V57J21B6A0 | CONFIRMADO (leitura do silício) |
| SoC interno | SL6801 | PROVÁVEL com alta confiança |
| SoC alternativo | SL6806 | DESCARTADO para este aparelho |
| Fabricante | Shenzhen Shenju Technology (Smartlink / Jointbees) | CONFIRMADO |
| SDK público | **NÃO EXISTE** | CONFIRMADO (ausência de fontes) |
| Datasheet público | **NÃO EXISTE** | CONFIRMADO (ausência de fontes) |

---

## 2. Evidências

### 2.1 Marcação física do chip

Leitura direta do silício no GN-438 (dispositivo aberto):

```text
Jointbees MP3
V57J21B6A0
```

Informações adicionais do encapsulamento/PCB:

```text
K: 43667840 | T: 72355145
Modelo: JLR-80852
Código de fábrica: F004226
Código do lote: 6/26
```

A marcação **"Jointbees MP3"** identifica a linha de SoCs de áudio da Shenzhen Shenju Technology. O código do die é **V57J21B6A0**. O **JLR-80852** parece ser a designação da placa/modelo do aparelho, não do chip em si.

### 2.2 String no bootloader

```text
0x0000C184  "SL6801"
```

Essa string é usada como marca de compatibilidade no pacote `update.up` (`docs/SDUPDATE_ANALYSIS.md` §4).

### 2.2 Correspondência USB

O aparelho enumera como:

```text
VID:PID       301a:2801
Manufacturer  SmartlinkTechnology
Product       USB2.0 Device
Serial        20201111000001
```

O `smartlink_flash` documenta para SL6801 em modo card reader:

```text
Card reader: id = 301a:2801,
             inquiry = "SMTLINK CARDREADER 1.00",
             serial  = 20201111000001
```

Correspondência **exata** de VID:PID, inquiry e serial.

### 2.3 String no próprio firmware

```text
0x00046FBF  "SMTLINK CARDREADER      1.00"
```

O dispositivo declara a mesma identificação que o upstream associa ao SL6801.

### 2.4 Ferramenta upstream

O repositório `ilyakurdyukov/smartlink_flash` mantém `payload/sl6801_sys.h` para esta família.

---

## 3. Por que não é CONFIRMADO

Nenhuma das evidências inspeciona o silício fisicamente. A string `SL6801` pode ser:
- um identificador de compatibilidade de build;
- uma marca de chip;
- um campo herdado de um SDK compartilhado.

A confirmação definitiva exigiria:
- leitura da marcação física do chip;
- correspondência de registradores com um datasheet;
- ou execução de código que leia registradores de ID do CPU/SoC.

---

## 4. Tentativas de obter documentação

Conforme `docs/EXTERNAL_RESEARCH.md` §5.5:

| Tentativa | Resultado |
|---|---|
| Contato com fabricante por e-mail | Sem resposta |
| Contato telefônico | Provável barreira de idioma (chinês) |
| Busca por SDK/documentação vazada | Nada encontrado |
| Contato com comunidade `smartlink_flash` | Sem documentação disponível |

---

## 5. Implicações para ANDROMEDA

A ausência de SDK/datasheet é uma barreira séria:

- **Drivers**: qualquer sistema alternativo precisaria de drivers escritos do zero a partir de reverse engineering.
- **Periféricos**: endereços de registradores, clocks, DMA e pinos precisariam ser descobertos por análise do firmware original.
- **Rockbox**: sem um target similar conhecido, o porte seria um projeto grande de engenharia reversa.

Isso não torna o projeto impossível, mas eleva o custo de qualquer implementação.

---

## 6. Leads não esgotados

| # | Lead | Por quê | Custo |
|---|---|---|---|
| 1 | Contatar `bunkaich` diretamente | Fez patch em firmware YP3; pode ter informação | Baixo |
| 2 | Fóruns chineses (`52pojie`, Baidu Tieba) com `云P3` | Ecossistema local | Médio |
| 3 | Comprar outro aparelho SL6801/SL6806 com atualização publicada | Garante um `update.up` real | Alto |
| 4 | Vazamento de SDK | Fora de controle | — |

---

## 7. Classificação

| Afirmação | Classe |
|---|---|
| Marcação física é Jointbees MP3 V57J21B6A0 | CONFIRMADO |
| SoC interno é SL6801 | PROVÁVEL com alta confiança |
| Fabricante é Shenzhen Shenju / Smartlink / Jointbees | CONFIRMADO |
| Não existe datasheet/SDK público | CONFIRMADO (por ausência de fontes) |
