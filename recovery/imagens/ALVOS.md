# Os dois alvos do recovery

```
GN438_original.bin        firmware de FABRICA
                          b7cd5eb952be5328cbaa926099cf8d88168633c1fab6d0f31f3a283c9e24b36f
                          o dump do aparelho no inicio do projeto

OpenPod_Core_1.0.1.bin    OpenPod Core 1.0.1, declarada STABLE em 14/09
                          36125f5665b8613e0d96215e2ffcf36170d847068d0c72e572167fe506400c1f
                          logo, PT-BR, "Atualizar por SD", versao na tela
```

## Qual usar

| situação | alvo |
|---|---|
| o aparelho deu defeito e você quer o OpenPod de volta, funcionando | `--alvo core` |
| o OpenPod é o suspeito, ou você quer o aparelho como saiu de fábrica | `--alvo fabrica` (o padrão) |
| não sabe | **fábrica** |

## Por que o de fábrica continua sendo o padrão

É o único artefato deste projeto cuja correção **não depende de trabalho
nosso**. Se um dia a baseline do Core estiver errada de um jeito que a
gente ainda não percebeu, um recovery que só restaura o Core não salva —
ele reinstala o problema.

O recovery para o Core é **conveniência**: poupa reinstalar tudo quando o
defeito é outro. O recovery para a fábrica é **garantia**.

## Trocar a baseline do Core

Quando uma versão nova for declarada STABLE, substitua
`OpenPod_Core_1.0.1.bin` pela imagem dela (o `*_carimbado.bin`), atualize
o nome em `recovery.py` (`ALVOS`) e regere o `SHA256SUMS`.
