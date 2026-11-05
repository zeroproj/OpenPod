# Ficha 010 — RC7: imagem B1 (Diag B com o bug do ring da fábrica corrigido)

Tipo: **Risco**. Base: `privado-completo`. Desenvolvedor: `minimax/MiniMax-M3`. Antes: fim de
`docs/tarefas/009-analise.md` (seções "Conferência da coordenação" e "Resultado no aparelho").

## Fato (aparelho)
A toca. B0 toca com o cinza. B reinicia. Hipótese principal: o `get_path` deixa a ViewTask lenta, o ring da view enche,
o envio sai sem soltar o mutex, a MainTask para e o watchdog deixa de ser alimentado.

## O que entregar
1. **Imagem B1 = imagem Diag B + exatamente 2 bytes no ORIGINAL do envio ao ring:**
   arquivo `0xF843A`: `fa e7` (`b 0xCF8432`) vira `f7 e7` (`b 0xCF842C`). Com o ring cheio, o caminho
   `movs r4,#0` passa pelo give do mutex em `0xCF842C..0xCF8431` e devolve 0 (mensagem descartada).
   Nada mais muda. Receita `reload_1.0_rc7_diag_b1`, nível novo em `tools/fab_diag_trava.py` e
   `tools/diag_trava_asm.py`, com as mesmas premissas e conferência de saída dos outros degraus (recusa se os bytes
   de entrada não forem os esperados; o diff final contra o Diag B é exatamente esses 2 bytes).
2. **Testes** em `tests/test_diag_trava.py`: diff de 2 bytes contra o B; decodificação em `0xCF8438`; recusa de entrada
   errada; imagem já patcheada recusada. `sh tools/ci.sh` verde.
3. **Kit** por `gera_versao`, carimbo `RC7 diag B1` com `patch_versao --em 0x1A4F00`, em
   `release/OpenPod-Reload-1.0-RC7-Diag-B1`, com `TESTAR.txt` curto: toca sem reiniciar? título, tempos e barra
   normais? trocar de faixa, sair e entrar 10 vezes. Quadrado cinza é o esperado. A volta de segurança é sempre a **RC6**.
4. **`docs/tarefas/010-analise.md`, curto, só estática, com endereços e instruções:**
   capacidade do ring (onde é criado e com que tamanho), quantas mensagens e bytes tem a rajada do play, e a quem
   mais o caminho "ring cheio" afeta. Se algo não der para saber, diga. Depois, a leitura do resultado:
   - B1 toca: elo do ring provado; próximo degrau é C + correção.
   - B1 reinicia: o ring não é a causa, ou não é a única.
   Registre os sha da imagem, da carimbada e do `.up`, e o CRC.

**Não** implementar a correção final nem mexer em `tools/capa_album.s`.

Regras de sempre: nunca alterar `firmware/ORIGINAL`, testes protegidos ou `tools/ci.sh`; nunca gravar no aparelho,
push, merge; ferramenta ≤ 350 linhas; nada abaixo de `0xE000`, setor `0xD000` e PSMP intocados.
