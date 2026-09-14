# tests/ — testes que não falam com o aparelho

```sh
python3 tests/test_roundtrip.py        # extrair -> modificar -> reconstruir
python3 tests/test_exec_free_area.py   # execução de código na área livre
```

Nenhum deles abre o USB. São verificações de que as ferramentas de
reconstrução preservam o que devem preservar e alteram o que devem
alterar.

Os outros verificadores do projeto moram em `tools/`, porque também são
usados dentro do pipeline:

```
tools/validate_firmware.py   estrutura, headerCrc, loadCrc, partições
tools/audita_chrome.py       divergências de tema, tela a tela
tools/gera_up.py --autoteste reconstrói um .up conhecido e compara
tools/afere_fora.py          mede o efeito real de cada ferramenta excluída
```
