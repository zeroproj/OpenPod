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

> Para voltar ao firmware de fábrica não use nada daqui: use
> `recovery/RECOVERY.sh`.
