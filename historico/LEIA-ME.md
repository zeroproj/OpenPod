# histórico

Kits de instalação antigos e material de recuperação. **Nada aqui é para
gravar** — o kit atual fica na raiz do projeto, na pasta `OpenPod 1.0/`.

## `kits/`

Um kit por versão interna (V001 a V042), mais os `.zip` correspondentes.
Cada um grava **a partir de uma versão específica** e se recusa a rodar se
o estado do aparelho não bater (confere o SHA-256 antes). Por isso não há
risco em tê-los aqui: se você rodar o errado, ele aborta.

Guardados porque documentam a cadeia inteira e permitem reproduzir
qualquer estado passado.

## `recuperacao/`

`OpenPod_Recovery_Linux/` — a pasta que recuperou o primeiro aparelho
depois do incidente da V028. Contém `smtlink_dump`, o firmware de fábrica,
o setor `0x00D000` isolado e os scripts.

Procedimento completo em `docs/MODO_DOWNLOAD.md`. O resumo:

```
USB conectado  ->  segure VOLUME ↓  ->  aperte RESET
```

O aparelho enumera como `301a:2800` e a flash inteira fica acessível,
mesmo com o firmware destruído.
