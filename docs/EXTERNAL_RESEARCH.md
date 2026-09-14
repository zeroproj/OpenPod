# OpenPod — EXTERNAL_RESEARCH

Dossiê de pesquisa externa sobre a família YP3 / SL6801 / Smartlink.

| | |
|---|---|
| **Criado** | 2026-09-12 |
| **Natureza** | documento vivo — acrescentar novas buscas ao §3 |
| **Escopo** | fontes públicas: web, GitHub, fóruns, redes sociais |
| **Hardware** | nenhuma operação |

> **Por que este arquivo existe.** Resultados de busca envelhecem e se
> perdem. Registrar *o que foi procurado*, *o que foi achado* e —
> principalmente — **o que comprovadamente não existe** evita repetir
> trabalho e evita concluir errado por falta de dado.

---

## 1. Sumário

| Pergunta | Resposta |
|---|---|
| Existe `update.up` público desta família? | **NÃO** — 10 frentes de busca |
| Existe documentação ou SDK do chip? | **NÃO** — múltiplas tentativas de contato falharam |
| Existe ferramenta pública? | **SIM** — `smartlink_flash` (única) |
| Existe especificação do formato de atualização? | **SIM** — código-fonte do `fwhelper` |
| Alguém já modificou este firmware com sucesso? | **SIM** — ver §5, precedente confirmado |
| Existe porte de Rockbox ou firmware alternativo? | **NÃO** — considerado inviável sem SDK |

---

## 2. ⚠️ Correção a documento anterior

`docs/UPDATE_UP_REFERENCE.md` §7 afirma:

> *"Não há registro público de ninguém ter gravado firmware modificado
> nestes aparelhos com sucesso. Se o OpenPod conseguir, será o primeiro."*

**Isso está errado.** A afirmação foi escrita depois de ler apenas os
primeiros comentários da issue #3. Lendo os **25** comentários, aparece um
precedente documentado e confirmado pelo próprio autor da ferramenta
(§5).

A conclusão correta é o oposto e é **boa notícia**: modificar e gravar o
firmware desta família **já foi feito**, inclusive **remapeamento de
botões** — exatamente um dos objetivos do OpenPod.

O documento `UPDATE_UP_REFERENCE.md` será corrigido para apontar aqui.

> Lição de método: ler os primeiros comentários de uma discussão longa e
> concluir a partir deles é uma armadilha. 25 comentários ao longo de 13
> meses contêm mais do que os 6 primeiros.

---

## 3. Registro de buscas

Todas em 2026-09-12.

| # | Consulta | Escopo | Resultado |
|---|---|---|---|
| 1 | `"update.up" firmware YP3 SL6801 MP3 player Smartlink` | web | só `smartlink_flash` |
| 2 | `Jointbees MP3 yp3 firmware update Shenzhen Shenju SL6801 SL6806` | web | nada novo |
| 3 | `github SL6801 yp3 firmware update.up 云P3` | github/gitlab/gitee | só `smartlink_flash` |
| 4 | `MP3 player SD card firmware update "update.up" copy to card root` | web | procedimentos de outras marcas |
| 5 | `"6801_intel_flash.bin" OR "SL6801" official flash tool download` | web | poluída por "Intel"; nada |
| 6 | `mechen.com.cn/firmwareupgrade` e `/M30` | fetch direto | páginas em JS, sem links legíveis |
| 7 | Issues e PRs de `ilyakurdyukov/smartlink_flash` | GitHub API | **fonte principal** — §4 |
| 8 | Issue #3 completa (25 comentários) | GitHub API | **precedente de patch** — §5 |
| 9 | `bunkaich MP3 player firmware patch Codex key remap Bluetooth SL6801` | web | confirma o precedente |
| 10 | `bunkaich github repository AliExpress Codex 中華MP3` | web | **nenhum repositório público** |

### Não indexado / bloqueado

| Alvo | Motivo |
|---|---|
| `xcancel.com/bunkaich/status/2059296280472584682` | CAPTCHA de verificação de navegador |
| `x.com/rohanpaul_ai/status/2059706648261017951` | exige sessão autenticada |
| `mechen.com.cn` | conteúdo renderizado por JavaScript |

---

## 4. Fonte primária: `ilyakurdyukov/smartlink_flash`

| | |
|---|---|
| URL | https://github.com/ilyakurdyukov/smartlink_flash |
| Autor | Ilya Kurdyukov |
| Criado | 2025-04-02 |
| Última atividade | 2026-09-01 |
| Estrelas / forks | 41 / 5 |
| **Licença** | **NENHUMA** (só isenção de garantia "AS IS") |
| Commit travado neste projeto | `49d51d17e825afbbbc2be7d91d6367674543c2e3` (2026-01-27) |

Registro de integridade: `tools/external/smartlink_flash.lock`
(SHA-256 dos 15 arquivos). Obtenção verificada:
`tools/external/fetch_smartlink_flash.sh`.

### O que cada parte entrega

| Componente | Valor para o OpenPod |
|---|---|
| `smtlink_dump.c` | dump e gravação por USB; opcodes do boot ROM |
| **`fwhelper/main.c`** | **especificação completa do formato `update.up`** |
| `payload/` | código para ler a ROM; `sl6801_sys.h` / `sl6806_sys.h` |
| `README.md` | modos do chip, VID:PID, comandos, regras udev |
| **Issues** | **inteligência de campo — §5** |

### Histórico de commits relevante

| Data | Commit | Significado |
|---|---|---|
| 2026-01-27 | `allow clearing bytes without page erase` | relacionado à anomalia da flash (§5) |
| 2026-01-27 | `note about flash memory` | o aviso sobre o comportamento anômalo |
| 2026-01-27 | `skip writing empty pages` | otimização de gravação |
| 2026-01-27 | `fix typo in write_flash` | suporte a escrita é **recente e pouco testado** |

> O suporte a gravação tem **8 meses** e o próprio autor diz que testou
> pouco. Não é código maduro.

---

## 5. Inteligência da comunidade

Issue #3 — *"works, now what?"* — aberta por `koriwi` em 2025-08-25.
**25 comentários, 7 participantes, 13 meses.** É o único fórum técnico
existente sobre estes chips.

Participantes: `ilyakurdyukov` (autor), `koriwi`, `altoensodio`,
`squidink7`, `Robbt`, `jemisa`, `Dogolitesnap`.

### 5.1 ✅ Precedente: o firmware JÁ foi modificado com sucesso

> **`jemisa`, 2026-06-14:**
> *"see https://xcancel.com/bunkaich/status/2059296280472584682 about how
> Codex used this code to patch the firmware."*
>
> **`ilyakurdyukov`, 2026-06-16:**
> *"Just a **remap of the keys** and fixing something with **Bluetooth**.
> But I'm glad that my tool was useful for something."*

Confirmado independentemente pela cobertura do caso:

> *"A developer known as **bunkaich** used Codex […] to reverse engineer a
> cheap MP3 player purchased on AliExpress. Bluetooth kept stuttering. The
> controls felt awkward. There was no dev kit, no clean documentation […]
> he inspected the firmware, mapped the binaries, identified the problem,
> and created a working patch. The result fixed the audio issue and
> **redesigned the button layout**."*

E sobre o método:

> *"He showed Codex a photo of the chip […] Codex guided him to put the MP3
> player into **bootloader mode on a Mac**. In that mode the Mac can read
> the entire firmware."*

**Significado para o OpenPod:**

| Ponto | Consequência |
|---|---|
| Gravação de firmware modificado **funciona** | o caminho existe e não é teórico |
| **Remapeamento de botões foi feito** | é viável apesar da tabela em RAM (`INPUT_MAP_COMPLETE.md` §1) |
| Bluetooth foi alterado | Fase 2 é atingível |
| Modo bootloader por USB no Mac | há um caminho alternativo ao `sdupdate` |
| **Nenhum repositório público** | os detalhes não foram liberados; não dá para copiar |

> Este é o único precedente conhecido. Não invalida nenhuma das nossas
> descobertas — nada foi publicado em nível técnico. Mas remove a dúvida
> sobre **se** é possível.

### 5.2 ⚠️ A flash não se comporta como flash normal

> **`ilyakurdyukov`, 2026-01-27:**
> *"The on-chip flash is acting strange, it can't clear bits one by one.
> It's probably not SLC flash."*
>
> *"All is fine with 1 → 0, but flash can somehow restore 0 → 1 with
> **90 % efficiency without erasing**."*
>
> *"The problem is not that it works, the problem is that it **shouldn't**
> work. The page erase operation sets all bits to 1. This should be the
> only way to change a 0 to a 1. But here it is possible to write a 1 over
> a 0, and this works in most cases (**randomly?**)."*

E:

> *"You don't need to use the erase command before the write command. The
> write command will use it automatically if necessary."*

**Implicação:** gravação pode deixar bits incorretos de forma não
determinística. **Toda gravação exige verificação por releitura.**
O `sdupdate` já faz isso (`SDUPDATE_ANALYSIS.md` §7) — o que agora parece
ser resposta deliberada a essa característica do silício.

### 5.3 ⚠️ Brick além do modo bootloader é documentado

> **`ilyakurdyukov`, 2026-01-27:**
> *"There are cases where devices no longer boot, **even in bootloader
> mode**, if you erase the entire flash or if there's invalid content.
> I don't know how unbreakable these chips are. You can only figure it out
> by trial and error."*

E sobre o alcance real dos testes dele:

> *"I did not try to rewrite the entire firmware, only **64KB in free space
> at the end**. And only for SL6801."*
>
> *"No, I haven't tried changing the firmware."*

**Qualifica a conclusão de `SDUPDATE_ANALYSIS.md` §8:** o bootloader
sobrevive ao caminho do **cartão SD** (que nunca toca `0x0`–`0xD000`), mas
gravação por **USB** pode destruí-lo.

| Caminho | Risco |
|---|---|
| `sdupdate` (cartão SD) | **menor** — bootloader não é tocado |
| `write_flash` por USB | **alto** — brick irrecuperável documentado |

### 5.4 Checksums

> **`ilyakurdyukov`, 2026-01-27:**
> *"keep in mind that the firmware contains a lot of checksums. The
> `fwhelper` tool will tell you if yours are incorrect."*

Coerente com o nosso trabalho: 6 campos de integridade identificados, todos
validados (`REBUILD_VALIDATION.md` §5).

### 5.5 SDK e documentação: inexistentes

> **`ilyakurdyukov`, 2025-08-26:** *"Porting requires a leaked SDK or
> documentation (which I haven't found), otherwise it's too difficult."*
>
> **`koriwi`, 2026-02-25:** (sobre escrever ao fabricante) *"nope. got
> nothing :("*
>
> **`altoensodio`, 2026-02-13:** *"i tried emailing the company that made
> the chips making myself seem like a company, but they didnt answer […]
> there was a phone number […] but probably they only speak chinese"*
>
> **`ilyakurdyukov`, 2026-02-12:** *"I don't believe that you can get
> anything from them. We can only hope for a docs and SDK leak."*

**Pelo menos duas tentativas independentes de contato com o fabricante
falharam.** Porte do Rockbox foi considerado inviável.

> Isso valida a estratégia do OpenPod definida no `CLAUDE.md` §47:
> transformar progressivamente o YP3, **não** escrever um sistema novo.

### 5.6 Bugs conhecidos do firmware original

| Relato | Fonte |
|---|---|
| Trava ao abrir o app de música com mais de ~20 músicas | `squidink7`, 2026-02-12 |
| Bluetooth com falhas de áudio (corrigido por `bunkaich`) | §5.1 |
| Não monta em Linux — a porta USB fecha a conexão | `sanchosk` + autor, issue #2 |
| Fica ligado ignorando a chave após carregar por USB | `Robbt`, 2026-04-30 |

Contorno para o último:

> **`ilyakurdyukov`, 2026-05-01:** *"Sometimes holding the power button for
> a long time (**3-15 sec**) helps turn off the device."*

> Estes são **alvos concretos de valor** para o OpenPod. O bug das ~20
> músicas, em particular, é uma falha funcional real que um usuário
> descreveu e ninguém corrigiu.

### 5.7 Um aviso humano

> **`Dogolitesnap`, issue #4, 2026-09-07:**
> *"I Wrote without dumping, anyone with firmware"* — sem resposta
> até hoje.
>
> E no dia 2026-09-07: *"can you PLEASE send the firmware"*

Alguém gravou **sem ter feito dump antes** e ficou sem firmware. Cinco dias
atrás. Ninguém tinha como ajudar.

> O `GN438_original.bin` deste projeto — verificado, com round-trip
> byte-a-byte provado e permissão 444 — é a diferença entre um
> experimento e um tijolo.

---

## 6. O que comprovadamente NÃO existe

Resultado negativo é resultado. Registrado para não ser reprocurado.

| Item | Status |
|---|---|
| Pacote `update.up` público | não indexado em nenhuma frente |
| Datasheet ou SDK do SL6801/SL6806 | inexistente publicamente |
| Ferramenta oficial de gravação | citada (`6801_intel_flash.bin`) mas não encontrada |
| Firmware oficial de qualquer aparelho da família | nenhum |
| Repositório do patch do `bunkaich` | não publicado |
| Porte de Rockbox ou firmware alternativo | nenhum |
| Segunda ferramenta além de `smartlink_flash` | nenhuma |

---

## 7. Leads não esgotados

| # | Lead | Por quê | Custo |
|---|---|---|---|
| 1 | Contatar `bunkaich` diretamente no X | fez remapeamento de botões — nosso item aberto #1 | baixo |
| 2 | Ler o thread original via mirror sem CAPTCHA | pode ter detalhes técnicos | baixo |
| 3 | Fóruns chineses (`52pojie`, Baidu Tieba) com `云P3` | ecossistema local | médio |
| 4 | Contatar `altoensodio` / `squidink7` | trabalham em CFW para SL6801 | baixo |
| 5 | Comprar aparelho da família com atualização publicada | garante um `update.up` real | alto |
| 6 | Vazamento de SDK | fora de controle | — |

> O lead #1 é o de melhor relação custo/benefício: `bunkaich` já resolveu,
> na prática, o problema que está em aberto no nosso
> `INPUT_MAP_COMPLETE.md` §11.

---

## 8. Como atualizar este documento

1. Acrescentar a consulta ao §3, com data e escopo.
2. Se achar fonte nova, registrar URL, autor, data e licença no §4.
3. Citações da comunidade vão no §5 — **sempre com autor e data**, e
   **verbatim**, nunca parafraseadas.
4. Se um resultado negativo for confirmado, registrar no §6.
5. Se algo contradisser documento anterior, **abrir seção de correção no
   topo**, como o §2 — nunca editar a conclusão antiga em silêncio.
6. Atualizar `docs/CHANGELOG.md` **e** `relatorio.md`.

---

## 9. Fontes

- [ilyakurdyukov/smartlink_flash](https://github.com/ilyakurdyukov/smartlink_flash) — ferramenta, `fwhelper`, issues #2/#3/#4
- [Relato do caso bunkaich (agregador)](https://www.threads.com/@blueviper.ai/post/DZHQ4ciCb_5/a-developer-known-as-bunkaich-used-codex-open-ais-coding-agent-to-reverse/)
- [Rohan Paul sobre o método usado](https://x.com/rohanpaul_ai/status/2059706648261017951) — requer sessão
- [Post original de bunkaich](https://xcancel.com/bunkaich/status/2059296280472584682) — bloqueado por CAPTCHA

## 10. Referências internas

| Assunto | Documento |
|---|---|
| Formato do `update.up` | `docs/UPDATE_UP_REFERENCE.md` |
| Disassembly do `sdupdate` | `docs/SDUPDATE_ANALYSIS.md` |
| Sistema de entrada | `docs/INPUT_MAP_COMPLETE.md` |
| Obtenção do firmware | `docs/FIRMWARE_DUMP.md` |
| Versão travada da ferramenta | `tools/external/smartlink_flash.lock` |
