# Referências do OpenPod / OpenPod references

O OpenPod parte do firmware de fábrica do GN-438 (`yp3_2.0.43`) e se apoia no trabalho de outros projetos abertos. Guardamos uma
**cópia (fork)** de cada um na conta [zeroproj](https://github.com/zeroproj). Assim, a versão exata que usamos fica preservada, e o
crédito vai sempre para o projeto original.

*OpenPod starts from the GN-438 stock firmware and builds on other open projects. We keep a **fork** of each one under
[zeroproj](https://github.com/zeroproj), so the exact version we used is preserved. Credit always goes to the original project.*

| Projeto | Autor | Original | Nossa cópia (fork) | Licença | Como o OpenPod usa |
|---|---|---|---|---|---|
| **SL6801_player** | Dmitry Brant | [dbrant/SL6801_player](https://github.com/dbrant/SL6801_player) | [zeroproj/SL6801_player](https://github.com/zeroproj/SL6801_player) | MIT | Os jogos e o kit de apps do menu Aplicativos (desde a 3.1). Ideias da caixa-preta (`crashlog.txt`) e da regra dos dois núcleos. |
| **smartlink_flash** | Ilya Kurdyukov | [ilyakurdyukov/smartlink_flash](https://github.com/ilyakurdyukov/smartlink_flash) | [zeroproj/smartlink_flash](https://github.com/zeroproj/smartlink_flash) | — (sem arquivo de licença no original) | Ler e gravar a flash pelo USB no Linux e no macOS: o backup original do GN-438 e o instalador por cabo. Usado como programa, não entra no firmware. |
| **Rockbox YP3** (port para o SL6801) | Jayden Milne | [jaydens-tasty-slop/rockbox](https://github.com/jaydens-tasty-slop/rockbox) | [zeroproj/rockbox-gn438](https://github.com/zeroproj/rockbox-gn438) | GPL | A base do **OpenPod RockBox**, distribuída sem mudança no código, com o tema OpenPod128. O código exato que distribuímos fica no nosso fork. |
| **rockslop** | Jayden Milne | [jaydens-tasty-slop/rockslop](https://github.com/jaydens-tasty-slop/rockslop) | [zeroproj/rockslop](https://github.com/zeroproj/rockslop) | GPL-2.0-or-later | A camada que fala com o player pelo USB (modo da ROM, cópia de segurança, gravação e conferência) no **OpenPod Tune**, que também é GPL: [zeroproj/openpod-installer](https://github.com/zeroproj/openpod-installer). |
| **Rockbox** | Projeto Rockbox | [rockbox.org](https://www.rockbox.org/) | — | GPL | O firmware livre por trás do OpenPod RockBox: codecs, plugins, temas e idiomas. |
| **Inter** (fonte) | Rasmus Andersson | [rsms/inter](https://github.com/rsms/inter) | — | SIL OFL 1.1 | A fonte do tema OpenPod do RockBox e do Instalador. |
| **ePet** | Yury Pliashkou | [pliashkou/epet](https://github.com/pliashkou/epet) | [zeroproj/epet](https://github.com/zeroproj/epet) | MIT | As regras do bichinho virtual (fome, alegria, energia, cuidados), com desenhos próprios. Previsto para a 3.6. |

## Componentes de fábrica / Stock components

O firmware de fábrica já traz estes componentes abertos, que o OpenPod mantém e aproveita:
- [LVGL](https://lvgl.io/): a interface gráfica;
- [FreeRTOS](https://www.freertos.org/): o sistema que divide as tarefas;
- [TJpgDec](http://elm-chan.org/fsw/tjpgd/), de ChaN: o decodificador de JPEG da capa do álbum.

## Licenças / Licenses

O texto completo da licença MIT de cada projeto usado no firmware vai no `README.md` de cada pacote em `release/`.
O gravador **Flashloader SL-DEV** (Shenju) é proprietário e vem no pacote só para gravar o aparelho.

*The full MIT license text of each project used in the firmware ships in each package's `README.md` under `release/`.*

## Código-fonte / Source code

**Quer estudar o chip ou programar para ele?** Comece pelo [SL6801_player](https://github.com/dbrant/SL6801_player). Ele é
aberto e traz o kit, os exemplos e o mapa do chip. A engenharia reversa e o código do OpenPod System são independentes e não são públicos. O lado RockBox (o Instalador e o Rockbox distribuído) é aberto, em GPL.

*Want to study or program the chip? Start with [SL6801_player](https://github.com/dbrant/SL6801_player). OpenPod System's reverse
engineering and source are independent and not public. The RockBox side (the Installer and the distributed Rockbox) is open, under the GPL.*

## Suporte / Support

Problemas ou dúvidas: [abra uma issue](https://github.com/zeroproj/OpenPod/issues). *Problems or questions: [open an issue](https://github.com/zeroproj/OpenPod/issues).*
