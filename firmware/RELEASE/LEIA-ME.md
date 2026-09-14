# firmware/RELEASE/ — os kits publicados

Uma pasta por versão. Cada uma traz:

```
<versao>.up              pacote para o cartão SD — instala de qualquer versão
<versao>_<setor>.bin     um arquivo POR SETOR, para gravar por cabo
base_<setor>.bin         os mesmos setores no estado ANTERIOR, para reverter
flash_<versao>.sh        o gravador
diag.sh                  diagnóstico                    SÓ LEITURA
recovery_check_linux.sh  confere a ferramenta           SÓ LEITURA
LEIA-ME.txt              o que mudou, e os sha de tudo
```

Gerados por `tools/make_install_kit.py`, que calcula endereços, tamanhos
e hashes **a partir das imagens** — nada é transcrito à mão. Foi uma
constante transcrita à mão que corrompeu a tabela de partições em
12/09/2026.

Releases anteriores à 1.4 estão em `historico/releases/`, e os kits
intermediários em `historico/kits/`.

## ⚠️ Os kits anteriores à Core 1.0 têm um bug no script de gravação

Descoberto em 14/09, ao tentar gravar a Core 1.0 por cabo:

```
flash_OpenPod Core 1.0.sh: 19: Core: not found
```

O gerador escrevia `WORK=$(pwd)/openpod_flash_OpenPod Core 1.0` **sem
aspas**, e os nomes de setor chegavam sem aspas no `ck_file` e no `wr`.
Qualquer versão com **espaço no nome** — ou seja, da 1.4 à 3.1 — carrega
a falha no seu `flash_*.sh`.

Ficou latente porque essas versões sempre foram instaladas pelo **cartão
SD**, e a única instalada por cabo (`v044`) não tinha espaço no nome.

**Corrigido no gerador a partir da Core 1.0**: os arquivos usam
`OpenPod_Core_1.0` (com sublinhado) e toda interpolação em posição de
argumento de shell é citada.

Os kits antigos **não foram regerados** — são artefatos publicados, e
mexer neles apagaria o que eles de fato foram. Para gravar um deles por
cabo, regenere com `tools/make_install_kit.py`, ou use o `.up` da pasta,
que não depende do script.

---

> Para voltar ao firmware de fábrica não use nada daqui: use
> `recovery/RECOVERY.sh`.
