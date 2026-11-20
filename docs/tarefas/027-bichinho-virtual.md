# Ficha 027 — Bichinho virtual (Reload 3.5)

Tipo: **Risco + Pesada** (código novo; vai ao aparelho e ao público). Base: a **3.3** publicada (ficha 025).
Desenvolvedor: `opencode/deepseek-v4.1-flash-free`. Decisão D27 (2026-11-20). Prazo da 3.5: **10/12/2026**.
**Começa depois do `PRONTO-025`.** A ordem entre esta ficha e a 026 (caixa-preta) é do decisor. Proposta: a 027 vem antes, porque tem data.

## O que é
Um bichinho virtual **nosso**, como app no menu Aplicativos, junto com os jogos da 3.5. Ele tem fome, alegria, energia, higiene e
saúde, que caem com o tempo. O usuário alimenta, brinca, limpa, põe para dormir e dá remédio. Ele cresce, e se ficar abandonado
adoece. Modelo proposto: `assets/ideias/ideia_bichinho_virtual.png`. As 5 telas são casa, menu (M), precisa de você, status e
dormindo.

## Fonte (licença MIT, com crédito)
`pliashkou/epet`, commit **`347ceaf`** (2026-09-20), MIT, Copyright (c) 2026 Yury Pliashkou.
- Clonar em `referencias/epet` (fora do commit) e fazer `checkout 347ceaf`. **Não executar** nada da referência: ler e portar.
- **Aproveitar só as regras:** `components/epet_core/epet_state.c`, `epet_care.c`, `epet_save.c` e os cabeçalhos deles.
- **Fica de fora:** `epet_sprites.c` (~975 KB, feito para 240×240), Bluetooth, sensor de movimento, módulos, a VM, a atualização sem
  fio e tudo de `main/`.
- Manter o aviso MIT no cabeçalho de cada arquivo portado. Criar `sdk/LICENSE-epet.txt` com o texto completo.
- O projeto é novo (0 estrelas). **Revisar a lógica** antes de confiar nela; os testes dele (`tests/`) servem de referência para os
  nossos testes no computador.

## Regras do projeto que valem aqui
- **Nada de ROM nem de marca de terceiros.** Nos textos públicos o nome é só "bichinho virtual". Os desenhos são nossos, em pixel art
  para 128×160.
- **Dois núcleos (Parte 0 da ficha 025):** o app roda na CPU1. Seguir a regra que a 025 provar para memória. O estado do bichinho é
  alocado **uma vez** e nunca liberado, para continuar vivo ao sair e voltar ao app com o aparelho ligado. Nada de chamada ao kernel
  nem ao cartão a partir da CPU1.
- SDK e compilador da ficha 022: zig 0.13.0, as mesmas flags, sem `.data`/`.bss`, mesmo binário em duas compilações.
- **Botões:** na casa, M abre o menu. No menu, ⏮/⏭ escolhem, Play confirma e M volta. Na casa, M longo sai do app. Confirmar contra
  os códigos já usados pelos jogos da 3.2.

## Etapas
1. **Obrigatória.** O bichinho funcionando, com o estado na RAM enquanto o aparelho está ligado.
   - Fora do app, o tempo é contado pelo contador de ticks do sistema. Ler a variável já basta, sem chamar o kernel. Provar o
     endereço no ORIGINAL.
   - O ritmo é ajustado para uso real: as necessidades caem em horas, não em minutos. Os valores ficam numa tabela em
     `027-analise.md`.
2. **Se provada a tempo.** Salvar no cartão e contar o tempo com o aparelho desligado.
   - (a) Provar o `f_write` no nosso ORIGINAL e gravar **pela CPU0**, como na caixa-preta.
   - (b) HIPÓTESE: o aparelho tem um relógio que continua certo depois de desligado. Provar ou descartar.
   - Sem prova até a véspera de 10/12, a 3.5 sai só com a etapa 1, e o decisor é avisado.

## O que entregar
1. `docs/tarefas/027-analise.md`, com:
   - cada endereço novo e sua prova;
   - o tamanho do código, dos desenhos e do estado;
   - o espaço livre restante na área de patches;
   - a tabela do ritmo das necessidades.
2. Uma receita nova = a da 3.3 + o bichinho + os jogos da 3.5, combinados com a coordenação.
3. Testes no computador da lógica do bichinho, sem o aparelho, e `sh tools/ci.sh` verde.
4. Capturas das 5 telas renderizadas a partir do código, para comparar com o modelo.

Regras de sempre:
- Nunca alterar `firmware/ORIGINAL`, gravar no aparelho, fazer push ou merge.
- Testes protegidos intactos; nada abaixo de `0xE000`; setor `0xD000` e PSMP intocados.
- Classificar tudo como CONFIRMADO, PROVÁVEL ou HIPÓTESE.

Sinal final sozinho numa linha: `PRONTO-027` ou `ESCALADA-027`.
