# Níveis de gravação — qual ferramenta para qual situação

> Decisão do mantenedor, 2026-09-13: *"vamos usar o software oficial só
> para os métodos de recuperação avançado"*.

Três caminhos, do mais leve ao mais pesado. **Use sempre o mais leve que
resolva.**

## Nível 1 — kit de setores  ·  o normal

```bash
cd "OpenPod 1.0" && sudo sh flash_OpenPod_1.0.sh
```

Grava **só os setores que mudaram**. A OpenPod 1.0 são 7 setores, 28 KiB,
segundos. Confere o estado ANTES por SHA-256 e se recusa a rodar se o
aparelho não estiver na versão esperada — errar de kit não é perigoso,
só dá aviso.

Exige o aparelho **ligando normalmente** (modo card reader, `301a:2801`).

**É este o caminho de instalação. Os outros dois são para quando algo deu
errado.**

## Nível 2 — `smtlink_dump` em modo download  ·  o aparelho não liga

```
USB conectado  ->  segure VOLUME ↓  ->  aperte RESET
lsusb  ->  301a:2800
```

A ROM de máscara do SoC aceita a tecla independentemente do que há na
flash. Foi assim que o primeiro aparelho voltou depois do incidente da
V028 — com o firmware destruído e o USB mudo.

Material pronto em `historico/recuperacao/OpenPod_Recovery_Linux/`.
Procedimento em `docs/MODO_DOWNLOAD.md`.

Ainda dá para gravar **um setor só**: o conserto do primeiro aparelho
foram 4096 bytes.

## Nível 3 — `.up` + Flashloader ou cartão SD  ·  imagem inteira

Gerado por `tools/gera_up.py`, ou por `make_install_kit.py --com-up`.
Formato oficial da Shenju, **validado byte a byte** contra o arquivo de
fábrica (`--autoteste`).

| onde | como |
|---|---|
| Windows | `SetupFlashloaderSL-DEV(6.9.5).exe`, em `firmware/VENDOR/B27.zip` |

O caminho do Flashloader **ainda não foi testado**. Roteiro do primeiro
teste em `docs/TESTE_FLASHLOADER.md`.
| cartão SD | `update.up` na raiz — depende do flag 6 no PMU, que só a V030 daria |

Regrava **1,7 MB**. Por isso não é o padrão: gasta ciclos de flash sem
necessidade quando 28 KiB resolvem.

Vale quando: o estado do aparelho é desconhecido, ou se quer voltar a uma
versão inteira de uma vez, ou se está mandando o firmware para outra
pessoa.

⚠️ **Nunca grave o `B27_251112.up`.** É outro produto. Um usuário no
Reddit brickou o dele exatamente assim.

## A cobertura do `.up`, e por que a nossa é diferente

O `.up` de fábrica cobre `0x000000..0x1A3038` — o fim da partição TONE.
**Não bastaria para o OpenPod:** nossas rotinas e strings vivem na área
livre logo depois. O `gera_up.py` calcula a cobertura até o último byte
usado, arredondado para 4 KiB, e confere que a PSMP (`0x1FC000`, as
configurações do usuário) fica de fora.
