# Segurança do firmware — checklist de danos

Todo patch, antes de virar RC:
- [ ] confere a premissa (bytes de fábrica no endereço) e recusa se não bater
- [ ] escreve só nos bytes declarados na ficha
- [ ] nada abaixo de `0xE000`; setor `0xD000` (regra R1) e PSMP (`0x1FC000+`) intocados
- [ ] desvio Thumb decodificado de volta e conferido
- [ ] cabeçalho de imagem intocado quando só paleta/pixels mudam
- [ ] RCs aprovadas no aparelho continuam reprodutíveis (catraca)
- [ ] nenhuma ferramenta da linha Core/Alphas, salvo exceção registrada em `docs/decisoes.md`
- [ ] cabeçalho de imagem conferido **inteiro** (inclusive `always_zero` e reservados), não só campos (achado 001-R1)
- [ ] saída recusada se for a própria entrada, inclusive por symlink/hardlink (`os.path.samefile`) (achado 001-R1)
- [ ] o `gera_versao` para se a imagem ou o `.up` tocarem o setor `0xD000` ou a PSMP (achado 004-R0, ALTA)
- [ ] o payload do `.up` é a imagem pedida byte a byte e cobre a última mudança (achado 006-R0, ALTA)
- [ ] ferramenta que só vale sobre uma RC exige o **sha256 da entrada** (achado 005-R0, ALTA: RC1–RC3 passavam nas outras premissas)
- [ ] premissas conferem a faixa inteira (primeiro/último byte), não um byte de amostra (achado 002-R0)
- [ ] texto novo: mesmos especificadores `%`, todo caractere com glifo, nunca mais largo que o de fábrica além de 113 px (005)
- [ ] premissas cobrem o que a RC anterior deixou e que a ferramenta depende (fonte/ponteiro/texto do título, achado 004-R0)
- [ ] imagem: erro máximo por pixel, não só a média (achado 004-R0: glifo apagado passava)
