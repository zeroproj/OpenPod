# OpenPod — RECOVERY_CHECK

Procedimento para confirmar que o caminho de recuperação por USB funciona,
**antes** de qualquer gravação.

| | |
|---|---|
| **Natureza** | **somente leitura** — nenhum byte é escrito no aparelho |
| **Duração** | ~10 minutos |
| **Pré-requisito de** | `docs/FLASH_POLICY.md` §7 |
| **Risco** | nenhum |

---

## 1. O que este teste prova

Um `read_flash` bem-sucedido prova **três coisas de uma vez**:

1. o aparelho **enumera e responde** por USB;
2. a flash pode ser **lida por completo**;
3. o `GN438_original.bin` preservado **confere com o aparelho** — ou seja,
   a rede de segurança é real, não presumida.

> Sem isso, gravar seria apostar que existe volta. É a diferença entre
> experimento e aposta.

---

## 2. ⚠️ Faça no Ubuntu, não no Mac

**Motivo verificado no código-fonte**, não suposição.

`smtlink_dump.c`, linhas 133–145:

```c
err = libusb_kernel_driver_active(dev_handle, i);
if (err > 0) { ... libusb_detach_kernel_driver(...) ... }
err = libusb_claim_interface(dev_handle, i);
if (err < 0) ERR_EXIT("libusb_claim_interface failed : %s\n", ...);
```

No macOS:

- `libusb_kernel_driver_active` devolve `LIBUSB_ERROR_NOT_SUPPORTED`
  (negativo) → o `if (err > 0)` é falso → **o detach nunca acontece**;
- em modo card reader o aparelho é reivindicado pelo driver de
  armazenamento do próprio macOS;
- `libusb_claim_interface` então falha com `LIBUSB_ERROR_ACCESS` e a
  ferramenta aborta.

O README do upstream também só cita **Linux e Windows (MSYS2)** — macOS
não está na lista.

**E há uma razão melhor ainda:** o dump original foi feito no Ubuntu. Usar
a mesma máquina elimina uma variável exatamente no momento em que você
precisa de certeza.

> O Mac continua útil para tudo que é offline: análise, patch, geração e
> validação de pacotes. Só a conversa com o aparelho vai para o Linux.

---

## 2.1 O que levar para o Ubuntu

**Um arquivo só:** `tools/recovery_check_linux.sh`

Ele é **autocontido** — não depende da árvore do projeto. Traz os 15
hashes embutidos, clona a ferramenta no commit travado, confere,
compila, detecta o aparelho e faz a leitura.

```bash
# no Ubuntu, na pasta que quiser
sh recovery_check_linux.sh
```

Pode rodar mesmo que você já tenha o `smartlink_flash` instalado: o script
clona uma cópia própria, verificada, num diretório de trabalho separado
(`./openpod_recovery_check/`). **Não interfere na sua instalação.**

### Sequência de comandos por modo — CONFIRMADO

O script escolhe a sequência conforme o modo detectado, porque **as duas
não são intercambiáveis**:

| Modo | Comando | Motivo |
|---|---|---|
| card reader `301a:2801` | `--id 301a:2801 flash_id read_flash 0 2M` | o upstream avisa que `init` **trava** neste modo |
| bootloader `301a:2800` | `init flash_id read_flash 0 2M` | o upstream exige `init` **antes** neste modo |

> Isto foi corrigido depois de uma revisão: a primeira versão do script
> usava a mesma sequência para os dois modos, o que teria falhado se o
> aparelho entrasse em modo bootloader.

**Não é preciso levar** a pasta `tools/` inteira, nem o
`GN438_original.bin`, nem os pacotes `.up`. Quanto menos o original
circular, melhor.

### O que volta

| Arquivo | Para quê |
|---|---|
| `readback.bin` | 2 MiB lidos do aparelho |
| `readback.log` | registro completo da sessão |

De volta na máquina do projeto:

```bash
python3 tools/verify_device_readback.py readback.bin
```

> O script já compara o SHA-256 com o do original e avisa se bate. A
> conferência **por região** (que distingue divergência legítima em `PSMP`
> de divergência crítica em `FIRM`) é feita na máquina do projeto, onde
> está o arquivo de referência.

### Se você JÁ tem o smartlink_flash instalado e funcionando

**Não há problema — use a sua instalação.** Para **leitura**, a versão é
irrelevante: `flash_id` e `read_flash` são comandos do boot ROM do chip,
estáveis desde a primeira versão da ferramenta.

Use `tools/recovery_check_manual.txt` — um bloco de comandos para copiar e
colar, que roda na sua própria pasta do `smartlink_flash`.

> **Por que registrar a versão mesmo assim.** O bloco começa capturando
> `git log -1` e o SHA-256 do `smtlink_dump.c` da sua cópia. Não é
> burocracia: o suporte a **escrita** só foi adicionado ao upstream em
> 2026-01-27 (commit `fix typo in write_flash` e vizinhos). Saber se a sua
> versão é anterior ou posterior a isso importa **mais tarde**, quando
> formos gravar — não agora, que é só leitura.
>
> Se a sua cópia for anterior, ela provavelmente **nem consegue escrever**
> — o que, nesta fase, é uma vantagem.

### Modo alternativo — manual, do zero

Se preferir fazer à mão, leve `tools/external/fetch_smartlink_flash.sh` e
`tools/external/smartlink_flash.lock` (os dois, o script procura o lock ao
lado dele) e siga as seções 3–5.

---

## 3. Preparação (uma vez) — só se for fazer manualmente

```bash
# 1. obter a versão exata travada no projeto e conferir os hashes
sh tools/external/fetch_smartlink_flash.sh
cd smartlink_flash

# 2. dependências e build
sudo apt install libusb-1.0-0-dev
make

# 3. (opcional) dispensar o sudo
sudo tee /etc/udev/rules.d/80-smtlink.rules >/dev/null <<'RULES'
SUBSYSTEMS=="usb", ATTRS{idVendor}=="301a", ATTRS{idProduct}=="2800", MODE="0666", TAG+="uaccess"
SUBSYSTEMS=="usb", ATTRS{idVendor}=="301a", ATTRS{idProduct}=="2801", MODE="0666", TAG+="uaccess"
RULES
sudo udevadm control --reload
```

A etapa 1 confere o SHA-256 dos 15 arquivos contra
`tools/external/smartlink_flash.lock`. Se algum divergir, **pare**.

---

## 4. Os dois modos do aparelho

| Modo | VID:PID | Como entrar | Observação |
|---|---|---|---|
| **Card reader** | `301a:2801` | conectar normalmente, **com cartão inserido** | foi o modo do dump original |
| **Bootloader** | `301a:2800` | **desligar**, segurar a tecla de boot e conectar | exige o comando `init` antes |

A tecla de boot **varia de aparelho para aparelho** — descobre-se por
tentativa e erro. Se não tiver chave física, um toque longo no power sai
do modo bootloader.

> Para este teste, **card reader basta**. É o modo mais simples e o que já
> funcionou antes.

---

## 5. O teste

```bash
# 5.1 conectar e confirmar a enumeração
lsusb | grep 301a
#   esperado: Bus ... ID 301a:2801 ...

# 5.2 identificar a flash — leitura pura
sudo ./smtlink_dump --id 301a:2801 flash_id
#   esperado: flash_id: 0x14851485

# 5.3 ler a flash inteira para um arquivo novo — leitura pura
sudo ./smtlink_dump --id 301a:2801 flash_id read_flash 0 2M readback.bin
#   esperado: 2.097.152 bytes
```

**Nenhum destes comandos escreve no aparelho.** Verificado por opcode:
`flash_id` emite `CMD_SL_READID` (0) e `read_flash` emite apenas
`CMD_SL_READ` (7). Ver `docs/FIRMWARE_DUMP.md` §6.

### 5.4 Conferir o resultado

De volta ao Mac (ou no próprio Linux, se o projeto estiver lá):

```bash
python3 tools/verify_device_readback.py readback.bin
```

---

## 6. Como ler o resultado

### ✅ Aprovado

```text
RESULTADO: LEITURA POR USB CONFIRMADA
```

Todas as regiões críticas idênticas. O pré-requisito da
`FLASH_POLICY.md` §7 está atendido e o teste do V001 fica liberado.

`PSMP` e a área livre **podem divergir legitimamente** — `PSMP` é a
configuração gravada em runtime pelo próprio aparelho.

### ❌ Divergência em região crítica

```text
RESULTADO: DIVERGENCIA EM REGIAO CRITICA
```

O aparelho **não** contém o firmware que o arquivo de referência diz.
**Não grave nada.** Preserve o `readback.bin`: é evidência, não erro.
Hipóteses a investigar: o aparelho recebeu alguma atualização; o dump
original veio de outra unidade; leitura incompleta.

### ⏱️ O aparelho cai do modo card reader no meio da operação

**Observado pelo mantenedor em 2026-09-12.** O `recovery_check_linux.sh`
"funcionava melhor" para entrar em card reader do que os scripts de
diagnóstico e gravação. A causa não é nenhum comando especial — ele **não
faz nada** para mudar o modo do aparelho.

**É timing.** Entre plugar e o primeiro comando, o `recovery_check` gasta
tempo clonando o repositório, conferindo 15 hashes e compilando. Esse
intervalo é justamente o que o aparelho precisa para estabilizar em card
reader. Os outros scripts exigiam o aparelho já enumerado e o atacavam
imediatamente — daí o `smtlink_dump` ficar "aguardando a conexão" e a
operação falhar.

> **Regra adotada:** todo script que fala com o aparelho **espera
> ativamente** por ele, dá uma folga para estabilizar, **reconfirma** que
> continua enumerado e só então pergunta se pode seguir.

Implementado em `tools/make_install_kit.py` (`bloco_aguardar`), presente
no `diag.sh` e no `flash_vNNN.sh` de todo kit gerado a partir daqui:

```text
ESPERA=180        # segundos até desistir
ESTABILIZA=4      # folga após detectar
```

O fluxo passa a ser: **rodar o script primeiro, conectar depois.**

### ❌ Não acende o raio ao conectar — **causa observada: o cabo**

**2026-09-12, observado.** O aparelho não exibia a tela do raio no Ubuntu
e não enumerava. Não era o Linux, nem a porta, nem o aparelho: **era um
cabo só de energia.** Trocado por um cabo de dados, entrou em card reader
normalmente.

**Diagnóstico de 10 segundos, antes de qualquer outra hipótese:**

```bash
sudo dmesg -w      # conectar o aparelho com isto rodando
```

| `dmesg` | Significado |
|---|---|
| **nenhuma linha** | caminho elétrico — **cabo de carga**, porta fraca ou hub |
| `new high-speed USB device` | USB OK; o problema é outro |

> Cabos de carga são fisicamente idênticos aos de dados e não dão
> nenhum aviso. **Sempre suspeite do cabo primeiro** — é a causa mais
> comum e a mais barata de testar.

Depois do cabo, nesta ordem: porta USB 2.0 **traseira** (direto na placa,
sem hub e sem porta frontal), depois cartão inserido, depois aparelho
desligado ao conectar.

### ❌ Não enumera / `claim_interface` falha

**Pare.** Sem o USB não há rede de segurança, e a `FLASH_POLICY.md` §3
mostra que com a FIRM corrompida o caminho SD fica indisponível — o USB
seria a única saída.

Antes de desistir, tentar: outra porta e outro cabo (muitos cabos são só
de energia); o modo bootloader; regras udev; outra máquina Linux.

---

## 6.1 Comportamento observado do aparelho — 2026-09-12

Registrado durante a execução real, para servir de referência:

| Momento | O que o aparelho faz |
|---|---|
| Ao conectar em modo card reader | exibe uma **tela com o símbolo de raio** (carregando / conectado ao USB) |
| Durante `flash_id` e `read_flash` | permanece nessa tela; não trava nem reinicia |
| Após a leitura | continua normal |

> **Por que isso importa.** O aparelho **dá retorno visual** durante
> operações USB. Isso é uma boa notícia para o teste do `sdupdate`: o
> bootloader tem as strings `"Finding file..."`, `"Update...  %"`,
> `"0123456789Update...100%"` e `"Update finish!"`
> (`docs/SDUPDATE_ANALYSIS.md` §14) — ou seja, **haverá progresso na tela**
> durante a atualização, sem depender da UART.
>
> Se durante um `sdupdate` a tela **não** mostrar nada disso, é sinal de
> que o processo não chegou a começar.

| Afirmação | Classe |
|---|---|
| Tela de raio ao conectar em card reader | **CONFIRMADO** (observado) |
| O aparelho mostra progresso durante o `sdupdate` | **PROVÁVEL** (strings existem; não observado) |

---

## 7. Depois de aprovado

1. Guardar o `readback.bin` como evidência datada.
2. Atualizar `docs/FLASH_POLICY.md` §7 e o painel do `relatorio.md`.
3. Aí sim: o teste do V001 pelo cartão está liberado.

---

## 8. Classificação

| Afirmação | Classe |
|---|---|
| `flash_id` e `read_flash` são somente leitura | **CONFIRMADO** (por opcode) |
| macOS falha em `libusb_claim_interface` em modo card reader | **PROVÁVEL** (mecânica confirmada no código; não testado) |
| Este teste prova que a recuperação por USB funciona | **CONFIRMADO**, se aprovado |
| O modo `"update from pc"` enumera após FIRM corrompida | **NÃO DETERMINADO** — este teste **não** cobre esse caso |

> **Ressalva honesta:** este teste prova que o USB funciona com o aparelho
> **saudável**. Não prova que o modo de recuperação automático
> (`"update from pc"`, acionado quando a FIRM não carrega) enumera. Provar
> isso exigiria corromper a FIRM de propósito — o que não faz sentido
> fazer antes de ter necessidade.
>
> Ainda assim, é a melhor evidência disponível sem correr risco: se o USB
> não responder nem com o aparelho bom, certamente não responderá com ele
> quebrado.
