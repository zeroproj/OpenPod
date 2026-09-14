# update/ — pacotes `.up` para o cartão SD

Este é o caminho oficial de instalação do OpenPod: o aparelho se atualiza
sozinho, sem cabo.

```
1. copie o .up para a RAIZ do cartão, com o nome  update.up
2. no aparelho: Configurar → Atualizar por SD → Sim
3. ele reinicia e se atualiza
4. APAGUE o update.up do cartão
```

O `.up` **não confere estado**: reescreve a imagem inteira, então funciona
a partir de qualquer versão. Não existe "gravar o pacote errado".

Formato, decodificado e validado contra o arquivo oficial da Shenju:

```
0x00  "CONFIG"
0x06  u32   0x100     offset do payload
0x10  u32   tamanho do payload
0x14  u16   CRC-16/CCITT-FALSE do payload
0x16  "SL6801"
0xFE  55 AA
0x100 payload — cópia literal da flash a partir de 0
```

Gerar: `python3 tools/gera_up.py --in <imagem> --out <pacote.up>`
Mecanismo por dentro: `docs/UPDATE_MECHANISM.md`, `docs/SDUPDATE_ANALYSIS.md`

> ⚠️ Um `.up` **nunca** é passado para o `write_flash` — ele tem 0x100
> bytes de cabeçalho, que cairiam em cima do bootloader. Ele é lido pelo
> **bootloader**, a partir do cartão.
