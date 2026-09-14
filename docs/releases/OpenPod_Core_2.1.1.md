# OpenPod Core 2.1.1 — o fundo da lista vem da tabela

```
Base       OpenPod Core 2.1
Gerada     2026-09-14
Status     EXPERIMENTAL — instrumento, como a 2.1
Diff       8 bytes em 1 setor
```

---

## 1. O que o aparelho mostrou

Com a 2.1 gravada, o mantenedor fotografou:

| tela | o que aparece |
|---|---|
| **home** | tema claro **perfeito** — fundo branco, texto preto, barra azul, os 9 itens legíveis |
| **Configurar** | os rótulos **sumiram**. Linhas escuras, texto preto. Só o item selecionado aparece, porque a barra azul o destaca |

**A pergunta que a 2.1 existia para fazer está respondida: o tema claro do
nano funciona neste display.** A home é a prova.

E a mesma foto expôs o defeito seguinte.

---

## 2. A causa — a sexta vez do mesmo padrão

Os dois criadores compartilhados pintam fundo com **preto fixo, vindo do
código**:

```
0x001216D0   CRIA_CONTEINER   bl 0xD2138A ; set_style_bg_color
0x0012177C   CRIA_LINHA       bl 0xD2138A ; set_style_bg_color

0x00D2138A   mov.w r0,#0 ; bx lr        <- preto, constante
```

A tabela de tema **tem** o campo para isso — `cor_tela`, em `+0x00` — e
ele estava praticamente morto: **um único leitor**, o thunk do S12 na
página 0x18. O `ESTADO_ATUAL.md` já registrava isso como "descoberta
colateral grave", meses antes, sem que a consequência fosse tirada.

Enquanto o tema era escuro, preto fixo e `cor_tela` preto **davam no
mesmo**, e ninguém notou. O Marte separou os dois.

> É a sexta vez: V016, V027, V031, a barra de rolagem, a segunda seleção,
> e agora o fundo. Sempre a mesma forma — **um valor existe na tabela e
> um caminho não o lê**.

---

## 3. O conserto — 8 bytes, sem rotina nova

A rotina que lê `cor_tela` **já existia**, e tem a mesma assinatura do
getter de preto:

```
0x00D2138A   mov.w r0,#0                  ; bx lr
0x00DA5A20   ldr r0,=TAB ; ldrh r0,[r0]   ; bx lr
```

Substituição direta. Dois `bl` redirecionados, 4 bytes cada.

**`cor_tela` deixa de ser campo morto** e passa a pintar o fundo de 36
telas de lista mais o contêiner de todas.

### O que NÃO foi tocado, e por quê

O getter `0x00D2138A` tem **12 chamadores**. Dois são a tela de abertura
— `0x0012285A` e `0x001228E4` — para onde o `patch_fundo_abertura` mandou
as funções da logo **de propósito**, porque a logo tem fundo preto.

Por isso a ferramenta troca **dois pontos nomeados**, nunca o getter. E
confere, ao final, que os dois pontos da logo continuam apontando para o
preto — se algum tiver mudado, ela aborta.

```
0x12285A  a logo do boot  -> 0x00D2138A  INTOCADA (preto)
0x1228E4  a logo do boot  -> 0x00D2138A  INTOCADA (preto)
```

---

## 4. Validação

```
validate_firmware   21 OK + a falha de CRC da R1
diff contra a 2.1   8 bytes em 1 setor, menor offset 0x1216D0
OK  nada abaixo de 0x00D000   OK  0x00D000 intocado   OK  PSMP intocada
imagem              78cfe765f2932375e3fdbae26793a16a56cce829c7fb6044582cbfd79d067a0c
kit                 2 setores, 8 KiB
```

---

## 5. O que olhar

1. **Configurar** — os rótulos voltaram? Texto preto sobre fundo claro?
2. **Todas as listas** — Música, Rádio, Pastas, Imagem: mesma coisa?
3. **A logo do boot** continua sobre **preto**? (é o ponto que a
   ferramenta protegeu; vale confirmar na tela)
4. **O separador entre as linhas** ainda aparece, agora que o fundo é
   claro? `cor_separador` é `0x5B0D`, um cinza escuro — deve aparecer.
5. **O texto do item selecionado** — na foto da home ele parecia
   **escuro** sobre a barra azul, não branco. O campo `cor_texto_sel`
   está em `0xFFFF`. Se continuar escuro, é mais um caminho que não lê a
   tabela — e aí eu meço antes de mexer.
