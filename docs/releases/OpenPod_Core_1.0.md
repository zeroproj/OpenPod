# OpenPod Core 1.0 — relatório de versão

```
Base       firmware ORIGINAL de fabrica
           b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f
Receita    tools/build.py --receita core1.0      5 passos
Gerada     2026-09-14
Status     EXPERIMENTAL — NAO TESTADA NO APARELHO
Kit        firmware/RELEASE/OpenPod Core 1.0/
```

> **Status é EXPERIMENTAL e continua assim até o mantenedor dizer o
> contrário depois de ver o aparelho.** Regra §22 do prompt-mestre: na
> dúvida, EXPERIMENTAL, nunca STABLE.

---

## 1. Por que esta versão é tão pequena

Ela não é a interface do OpenPod. É a **fundação** da linha Core: o
mínimo que prova que sabemos construir, validar, empacotar e instalar uma
imagem a partir do firmware de fábrica, por uma receita declarada.

O valor dela é ser pequena o bastante para que qualquer defeito tenha
causa óbvia. Sai do ORIGINAL, não da cadeia manual de 100 imagens.

**Consequência aceita, dita na cara:** visualmente é um **recuo** em
relação à 2.4 e à 3.0. A home volta à **grade 3×3 de fábrica**, sem faixa
superior, sem título por tela, sem a tabela de tema do Saturno. Tudo isso
continua inteiro na receita `interface` e volta na **Core 2.0**.

---

## 2. O que entrou

| # | item | ferramenta | onde se vê |
|---|---|---|---|
| 1 | **Logo do OpenPod na abertura** | `patch_logo.py` | tela de boot |
| 2 | **Tabela do português na área livre** | `relocate_lang_table.py` | pré-requisito do item 3 |
| 3 | **Textos revisados em português do Brasil** | `aplica_textos.py` | menus inteiros |
| 4 | **'Vídeo' com maiúscula** | `patch_menu_text.py` | home |
| 5 | **Item "Atualizar por SD"** | `patch_update_sd.py` | Configurar |
| 6 | **Versão na tela Informações** | `patch_versao.py`, pelo kit (R7) | Configurar → Informações |

A tela Informações mostra, em duas linhas:

```
OpenPod Core 1.0        102 px
GN-438                   43 px
```

> O prompt (§18.2) pede quatro linhas — `OpenPod`, `OpenPod Core`,
> `Version 1.0`, `GN-438`. **Cabem duas.** A camada VIEW tem um defeito
> de layout que sobrepõe a partir da terceira, ainda não localizado.
> Duas linhas é o que se pode entregar sem abrir um segundo assunto
> dentro desta versão. **Pendência registrada, não esquecida.**

## 3. O que ficou de fora, de propósito

Home em lista, faixa superior, título por tela, Saturno (S1–S12), cor de
seleção, submenu Extras, chevrons, navegação alternativa.

O **Extras** merece nota: `patch_extras` + `_fix` + `_fix2` são três
patches empilhados no mesmo ponto e os seis itens continuam sem abrir.
Ficam fora com o motivo escrito no `build.py`. **Nada na receita finge
funcionar.**

---

## 4. Validação

### 4.1 Estrutural

```
validate_firmware.py        21 OK, 1 falha
```

A falha é o **CRC da FIRM** — e é o resultado esperado. A regra R1 manda
não regravar o setor `0x00D000`, então o campo fica desatualizado de
propósito. Confirmado no hardware em 13/09: o aparelho boota com a tabela
de fábrica sobre uma FIRM diferente. As imagens v073, v077 e v101, que
bootaram, acusam a mesma linha.

### 4.2 Binary diff contra a base

```
bytes alterados        9.143
setores                    8
menor offset      0x048798

  0x048000      3 B     ponteiro de texto
  0x0CC000   1985 B     logo — paleta
  0x0CD000   3335 B     logo — pixels + paleta dos icones
  0x109000      7 B     item novo em Configurar
  0x10A000      3 B     literal da versao, repontado
  0x121000      3 B     gancho de texto
  0x1A3000   1619 B     area livre: update SD, 'Video'
  0x1A4000   2188 B     area livre: tabela de idioma, textos, versao
```

```
setor 0x00D000 tocado          NAO      <- regra R1
algo abaixo de 0x00D000        NAO      <- bootloader intocado
PSMP (0x1FC000+) tocada        NAO      <- configuracoes preservadas
```

### 4.3 Verificações dirigidas

```
logo 0x0CC7C4..0x0CDD50 byte a byte igual ao da V007, que rodou   SIM
cabecalho lv_img_dsc intocado                                     SIM
'Atualizar por SD' em 0x1A324C                                    SIM
tabela do portugues em 0x1A3600, ids legiveis:
    0 Portugues · 1 Musica · 2 Livro digital · 3 Video
    4 Imagem    · 5 Gravacao
texto da tela Informacoes em 0x1A4928: 'OpenPod Core 1.0\nGN-438'
```

### 4.4 O pacote `.up`

```
magic        CONFIG
chip         SL6801
payload      1.724.416 B  (0x1A5000)
CRC          gravado 0x69FF  ==  calculado 0x69FF
assinatura   55 AA
payload identico a imagem[0:0x1A5000]        SIM
PSMP fora do payload                         SIM
```

### 4.5 Reprodutibilidade

`tools/build.py --receita core1.0` é determinística: executada mais de
uma vez a partir do ORIGINAL, sai sempre
`f0db84232c16c18a4d13356ba6814d10415b474925ad5385862b570b692cb6c9`.

---

## 5. Hashes

```
imagem (sem carimbo)  f0db84232c16c18a4d13356ba6814d10415b474925ad5385862b570b692cb6c9
imagem (carimbada)    e42be52362bd0f22980f56def0a67d87f5390b16c799f4a35037648eb1f37f55
pacote .up            a299d2344b157d0fd604ce27c09a56178ef62e169d4e55601ae85d915666230c
```

Setores do kit:

```
0x048000  41308534ac9a54ca3960d82de64dcef4959c85b9278d2a1c82eac5c1ed5afd5b
0x0CC000  ef8ffb2966867c44f8a87315ad7469a97018d0b7367ce864c19ffa102a8ba165
0x0CD000  99d56432ede44c31aa9fc2b928c7965db70129bd8e4bc3f3a9b00b82abd4554e
0x109000  3bc16bacee418a50f79df0aa7c3f5604241fc55f126ee8d7bec7d802849312c2
0x10A000  59c1e2e2b2a76131daeb2dbe1fe19d9f362903a36c45fa2782fdb0b1b223c856
0x121000  5a210420e87bf0f9da73338e0f0ddac91018e0715207660cbeda881e02828c90
0x1A3000  a8d62682b5a02eb5a2287e58a4754385d579a16e05b2c23de5821b458dad074f
0x1A4000  eaa94bfe5d728697d74a3cff501b1068db3fe7fdbc8af02a50c6370d14ca82f7
```

Os `base_*.bin` do kit são os mesmos setores **no firmware de fábrica** —
é por eles que se desfaz a instalação sem precisar do recovery completo.

---

## 6. Como instalar

**Pelo cartão SD** — o caminho oficial:

```
1. copie  firmware/RELEASE/OpenPod Core 1.0/OpenPod Core 1.0.up
   para a RAIZ do cartao, com o nome  update.up
2. no aparelho: Configurar -> Atualizar por SD -> Sim
3. ele reinicia e se atualiza
4. APAGUE o update.up do cartao
```

O `.up` não confere estado: reescreve a imagem inteira e funciona a
partir de qualquer versão.

> **Mas o aparelho está de fábrica agora**, e no firmware de fábrica
> **não existe caminho pela interface para o update por SD** — o flag só
> é armado pelo console de depuração (`docs/UPDATE_TRIGGER.md`, §1,
> CONFIRMADO). O item "Atualizar por SD" é justamente uma das coisas que
> esta versão traz.
>
> Então a **primeira** instalação tem de ser por cabo, pelo kit de
> setores — 8 setores, 32 KiB:
>
> ```
> sudo sh "flash_OpenPod Core 1.0.sh" /opt/smartlink_flash
> ```
>
> Da Core 1.0 em diante, o cartão resolve.

**Para voltar atrás:** `recovery/RECOVERY.sh`, validado em hardware, ou
os `base_*.bin` do próprio kit.

---

## 7. O que testar no aparelho

Em ordem de valor — cada item responde uma pergunta que a análise
estática não responde:

1. **Boot.** Aparece a **logo do OpenPod** em vez do GENAI?
2. **Configurar → Informações.** Diz `OpenPod Core 1.0` e `GN-438`, em
   duas linhas, sem sobrepor?
3. **Configurar.** O item **"Atualizar por SD"** está lá? Abre?
4. **Textos.** Os menus estão em português, sem caixa alta errada,
   sem texto cortado? `Vídeo` com V maiúsculo na home?
5. **Nada quebrou?** Música toca, rádio abre, pastas navegam, o aparelho
   desliga normalmente.
6. **Atualizar por SD funciona de verdade?** Só dá para testar com um
   `.up` seguinte — fica para a Core 1.1.

Se algo falhar, o kit tem os `base_*.bin` e o recovery está pronto.

---

## 8. Pendências que esta versão deixa registradas

| # | pendência |
|---|---|
| 1 | a tela Informações só cabe **2 linhas**; o prompt pede 4. Defeito de layout na camada VIEW, não localizado |
| 2 | `patch_versao.py` ainda aloca sozinho na área livre (caiu em `0x1A4928`, dentro do lote do `aplica_textos`). É a última ferramenta fora do MAPA |
| 3 | o **binary diff** e a **validação** ainda não são passos do `build.py` — rodam à mão |
| 4 | "Atualizar por SD" não pode ser exercitado nesta versão: precisa de uma versão seguinte para atualizar |
