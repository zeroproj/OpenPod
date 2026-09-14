# OpenPod — Política de reversão: volta-se para a BASE, nunca para a fábrica

> Defeito encontrado e corrigido em 2026-09-12, ao gerar o kit do V014.
> Estava latente em **todos os kits desde o V002**.

---

## 1. A conclusão, primeiro

> **Para desfazer um patch, grave os setores do estado ANTERIOR (a base do
> kit). Nunca os setores do ORIGINAL DE FÁBRICA.**

Gravar setores de fábrica sobre um subconjunto da flash **não** devolve o
aparelho à fábrica — devolve um firmware **misturado**, cujo CRC da FIRM
não bate com o conteúdo.

---

## 2. Por que

Um patch toca um subconjunto dos setores. O `flash_<v>.sh` grava só esses.

Se, em caso de erro no meio da gravação, a instrução de socorro mandar
gravar **conteúdo de fábrica** nesses mesmos setores:

```text
flash resultante = base em todo lugar
                 + fábrica nos setores do patch
```

O setor `0x00D000` contém a **tabela de partições**, e nela o **CRC-16 da
FIRM**. Vindo de fábrica, esse campo carrega o CRC do firmware **de
fábrica inteiro** — mas o corpo da FIRM continua majoritariamente no
estado da base. Os dois não se correspondem.

### Medido, não suposto

Experimento sobre o V013 com os 8 setores do V014:

```text
V013 puro                       gravado 0x8A58 / calculado 0x8A58  CONFERE
V013 + 8 setores de fábrica     gravado 0x49A6 / calculado 0xACBB  NÃO CONFERE
```

> Se o bootloader valida esse CRC, a "recuperação" não recupera: piora.
> Se não valida, o aparelho fica com um estado que nenhuma ferramenta do
> projeto sabe reconhecer. Nos dois casos é a pior hora possível para
> descobrir isso — com o aparelho parcialmente escrito.

**Classificação:** que a mistura produz CRC inválido é **CONFIRMADO**
(cálculo direto). Que o bootloader **rejeita** um CRC de FIRM inválido é
**NÃO DETERMINADO** — e é exatamente por não estar determinado que a
regra é conservadora.

---

## 3. A correção

`tools/make_install_kit.py` passou a emitir os setores de reversão a
partir de `--base`:

| Antes | Depois |
|---|---|
| `orig_<SETOR>.bin` ← imagem de fábrica | `base_<SETOR>.bin` ← **estado anterior** |

O argumento `--origem` continua obrigatório, mas agora serve **só** como
referência de hashes de fábrica dentro do `diag.sh`. A reversão nunca o
usa.

**Por que reverter para a base é a resposta certa:** a base é um estado
que **já foi gravado, já foi conferido byte a byte e já bootou no
aparelho**. É a única coisa no projeto com essa credencial.

---

## 4. Verificação da correção (V014)

Teste de ida e volta sobre as imagens, sem tocar no hardware:

```text
setores do kit conferem com as imagens          OK
V013 + setores do kit        == V014            OK
V014 + setores de reversão   == V013            OK
V014 reconstruído   CRC FIRM 0xF5AB / 0xF5AB    CONFERE
V013 revertido      CRC FIRM 0x8A58 / 0x8A58    CONFERE
```

A reversão é **exata**, não aproximada: o arquivo revertido é
byte-idêntico ao V013.

---

## 5. Ressalva sobre os kits antigos

Os kits do **V002 ao V013** (em `other/` e na raiz) trazem
`orig_*.bin` e instruções de socorro apontando para eles.

> **Essas linhas estão erradas.** Não as execute. Para desfazer um
> daqueles patches, gere um kit novo com `--base` = o alvo daquele kit e
> `--alvo` = a versão para onde se quer voltar, ou use o procedimento
> completo de restauração de fábrica, que regrava **todas** as regiões e
> por isso é consistente.

Os kits antigos não foram regerados: eles são registro histórico do que
foi realmente gravado. Regerá-los apagaria essa evidência.

---

## 6. Restauração de fábrica de verdade

Continua existindo e continua válida — mas é outro procedimento, que
regrava a imagem **inteira**, não um subconjunto:

- `firmware/WORKING/update_restore_original.up`
- `docs/RECOVERY_CHECK.md` / `tools/recovery_check_linux.sh`

Consistente porque não mistura estados.

---

## 7. Lição de método

> A rede de segurança deste projeto foi testada **para a frente**
> (a gravação funciona) e nunca **para trás** (a reversão devolve um
> estado válido). Um caminho de recuperação que nunca foi calculado é uma
> hipótese, não uma rede.
>
> É a terceira vez que o mesmo padrão aparece: o erro não estava no que
> foi feito, estava no conselho impresso para a hora em que algo desse
> errado. Da primeira vez (Sessão 25) o script mandava repetir a
> assinatura errada do `write_flash`. Agora mandava misturar fábrica com
> base. **Conselho de emergência precisa ser verificado com o mesmo rigor
> do caminho principal — de preferência antes de existir uma emergência.**
