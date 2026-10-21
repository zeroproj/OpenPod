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
