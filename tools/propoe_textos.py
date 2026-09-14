#!/usr/bin/env python3
"""
propoe_textos.py — Gera o markdown de revisao dos textos em portugues,
                   com a proposta ao lado do atual e a largura medida.

CRITERIOS DA REVISAO

    1. **Portugues do Brasil.** ficheiro->arquivo, ecra->tela,
       Actualizar->Atualizar, seleccionar->selecionar, Lingua->Idioma.
    2. **Consertar traducao automatica quebrada.** Ha erros que invertem
       o sentido: 'Senhor' para Jazz, 'Rocha' para Rock, 'Ramo' para
       minutos, 'Apenas cobrar' para Charge & Play.
    3. **Caber na tela.** 94 dos 215 passam de 113 px e sao truncados nas
       listas. Encurtar sem perder sentido -- frequentemente adotando o
       criterio que os outros idiomas ja usaram.
    4. **Consistencia.** Mesma acao, mesma palavra, em todas as telas.

USO
    python3 tools/propoe_textos.py \
        --in  firmware/WORKING/GN438_openpod_v043.bin \
        --out docs/TEXTOS_REVISAO.md
"""

import argparse
import struct
import sys

XIP = 0x00C00000
POOL_PT = 0x00121104
EN = 0x00052AA4
TBL, CMAP, N_GLIFOS = 0x00086C44, 0x000A27E6, 7098
LIM = 113

P = {
 8:'Pastas', 13:'Últimas tocadas', 14:'Tocando agora', 15:'Artistas',
 16:'Álbuns', 17:'Favoritas', 18:'Procurando', 19:'Iniciar gravação',
 20:'Gravações', 21:'Gravando', 22:'Pausar', 23:'Ativar alarme',
 24:'Definir alarme', 25:'Repetição', 26:'Uma vez', 30:'Nome',
 31:'Pareados', 32:'Procurar', 33:'Pareando', 34:'Procurando',
 35:'Disponíveis', 37:'Idioma', 38:'Informações', 39:'Atualização',
 40:'Atualizar por SD', 41:'Data', 42:'Hora', 43:'Sobre o aparelho',
 44:'Versão', 45:'Atualizar por PC', 46:'Atualizar por SD',
 47:'Sem armazenamento', 48:'Nenhuma música encontrada',
 49:'Nenhum e-book encontrado', 50:'Nenhum vídeo encontrado',
 51:'Nenhuma imagem encontrada', 52:'Nenhum arquivo encontrado',
 53:'Sem dados de dicionário', 54:'Sem favoritas',
 55:'Transferir arquivos', 56:'Apenas carregar', 57:'Buscando estações',
 58:'Nenhum álbum encontrado', 59:'Nenhum artista encontrado',
 60:'Áudio não suportado', 61:'Favoritas removidas',
 62:'Nenhuma gravação encontrada', 63:'Imagem não suportada',
 64:'Vídeo não suportado', 65:'Falha na conexão', 73:'Min', 74:'Seg',
 75:'Carregando', 76:'Palavra não encontrada', 77:'Conectar',
 78:'Desconectar', 79:'Desparear', 80:'Desconecte o aparelho atual',
 81:'Disponíveis', 82:'Pareados', 83:'Conectado', 84:'Conectando',
 85:'Desconectado', 86:'Desconectando', 87:'Desligar sozinho',
 88:'Tempo para desligar', 89:'Desconecte o aparelho atual',
 90:'Padrão de fábrica', 91:'Atualizar o sistema\npelo cartão SD?', 94:'Tipo de conexão',
 95:'Bateria fraca. Carregue!', 96:'Bateria abaixo de 10%%',
 97:'Tempo de tela', 98:'Tempo até apagar', 99:'Sempre ligada',
 102:'Pop', 103:'Rock', 104:'Jazz', 106:'Dance', 107:'Country',
 108:'Apagar arquivo', 109:'Salvar gravação?', 110:'Arquivo não suportado',
 111:'Alta qualidade', 112:'Alarme ativo. Desligar?',
 113:'Carregando, aguarde', 115:'Conectando, aguarde',
 116:'Virar página a cada', 118:'Ir para página', 119:'Marcadores',
 123:'Apagar marcador', 124:'Voltar ao início', 125:'Velocidade',
 126:'Favoritar', 127:'Desfavoritar', 128:'Modo', 129:'Repetir uma',
 132:'Velocidade', 133:'Estações salvas', 134:'Faixa de FM',
 135:'Japão', 136:'Europa', 137:'Padrão', 138:'Apagar estações',
 139:'Falha ao ler o cartão SD',
 140:'Isso vai parar a música.\n\nContinuar?',
 141:'Qualidade normal', 144:'Atualizar biblioteca', 145:'Busca automática',
 146:'Busca concluída', 147:'Estações apagadas',
 148:'Conecte o fone: ele é a antena', 149:'Abrir pasta',
 150:'Lendo arquivos', 151:'Voltar', 153:'Concluído',
 154:'Lendo arquivos.\nNão desligue nem remova o cartão.',
 157:'Carregue antes de atualizar', 158:'Cartão SD cheio. Libere espaço.',
 159:'Aplicativos', 160:'Protetor de tela',
 161:'Carregue por 10 minutos\nantes de usar', 162:'Cancelar',
 163:'Tempo do protetor', 164:'Taxa de bits', 165:'Ambiente',
 166:'Dividir gravação', 167:'Ativada por voz', 168:'Monitorar gravação',
 169:'Gravação agendada', 170:'Desligado', 171:'Entrevista',
 172:'Reunião', 173:'Estação', 174:'Aula', 175:'Gravação',
 176:'Início', 177:'Fim', 178:'Repetição', 179:'Modo música',
 180:'Modo chamada', 181:'Ative o Bluetooth',
 182:'Conecte o fone para monitorar', 183:'Chamada recebida',
 184:'Teste de desempenho', 185:'Falha na conexão', 186:'Apagar pastas',
 187:'Nenhuma estação salva', 188:'Desligar programado',
 189:'Hora para desligar', 190:'Em ordem', 191:'Luz dos botões',
 193:'Desligado', 194:'Ligado', 195:'Armazenamento', 196:'Total:',
 197:'Livre:', 198:'Senha ao ligar', 199:'Mudar senha',
 200:'Senha incorreta', 201:'Gravação salva',
 202:'O fone é a antena do rádio',
 203:'Não desconecte o USB durante a transferência',
 204:'Página não encontrada', 205:'Senha atual:', 206:'Nova senha:',
 207:'Repita a nova senha:', 208:'Entrada inválida',
 209:'Digite a senha:', 210:'Erro ao abrir o vídeo',
 211:'Formatar cartão SD', 212:'Concluído',
 213:'Formatando. Não remova o cartão nem desligue.',
 214:'Falha ao formatar. Tente no PC.', 215:'Erro no cartão SD',
}

MOTIVO = {
 'pt-BR': [8,37,55,60,97,98,99,108,110,144,150,154,159,160,163,186,207,209],
 'erro':  [13,14,56,61,73,79,103,104,107,116,126,150,154,184,191],
 'curto': [20,23,30,31,32,34,35,39,40,43,46,47,48,49,50,51,52,53,58,59,62,
           80,87,88,89,91,94,95,96,113,116,118,125,133,134,137,138,139,146,
           147,148,157,158,166,167,168,169,175,182,187,188,189,195,196,197,
           202,203,204,210,213,214],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    a = ap.parse_args()
    d = open(a.src, "rb").read()
    base = struct.unpack_from("<I", d, POOL_PT)[0] - XIP
    cmap = struct.unpack_from("<%dH" % N_GLIFOS, d, CMAP)
    idx = {c: i for i, c in enumerate(cmap)}

    def w(t):
        s = 0
        for ch in t.split("\n")[0]:
            g = idx.get(ord(ch))
            if g is None:
                return None
            s += struct.unpack_from("<I", d, TBL + g * 16 + 4)[0]
        return s

    def ler(off, i):
        p = struct.unpack_from("<I", d, off + i * 4)[0]
        o = p - XIP
        e = d.find(b"\0", o)
        return d[o:e].decode("utf-8", "replace") if 0 <= e - o < 200 else ""

    faltando, cabe_agora, cabe_depois, mudados = [], 0, 0, 0
    linhas = []
    for i in range(216):
        at = ler(base, i)
        if not at:
            continue
        nv = P.get(i)
        wa, wn = w(at), w(nv) if nv else None
        if nv:
            mudados += 1
            for ch in nv:
                if ch != "\n" and ord(ch) not in idx and ch not in faltando:
                    faltando.append(ch)
        if (wa or 0) <= LIM:
            cabe_agora += 1
        if ((wn if nv else wa) or 0) <= LIM:
            cabe_depois += 1
        mot = [k for k, v in MOTIVO.items() if i in v]
        linhas.append((i, at, wa, nv, wn, ",".join(mot), ler(EN, i)))

    with open(a.dst, "w", encoding="utf-8") as f:
        f.write("# Revisão dos textos em português — proposta\n\n")
        f.write("> Gerado por `tools/propoe_textos.py`. "
                "**Nada foi gravado no firmware.**\n>\n"
                "> Revise a coluna **proposto**. O que você mudar, eu aplico "
                "com `patch_menu_text.py`,\n"
                "> que grava a string nova na área livre e repõe o ponteiro — "
                "nunca edita no lugar.\n\n")
        f.write(f"- **{mudados} de {len(linhas)}** textos com proposta de mudança\n")
        f.write(f"- cabem em {LIM} px: **{cabe_agora} hoje → "
                f"{cabe_depois} depois**\n")
        f.write("- motivos: `pt-BR` regionalismo · `erro` tradução errada · "
                "`curto` não cabe na tela\n\n")
        if faltando:
            f.write(f"> ⚠ caracteres fora da fonte: {faltando}\n\n")
        f.write("---\n\n")
        f.write("| id | motivo | atual | px | **proposto** | px | en |\n")
        f.write("|---:|---|---|---:|---|---:|---|\n")
        for i, at, wa, nv, wn, mot, en in linhas:
            def e(s):
                return (s or "").replace("|", "\\|").replace("\n", "⏎") or " "
            mark = "" if not nv else "**"
            f.write(f"| {i} | {mot or ' '} | {e(at)} | {wa or '?'} | "
                    f"{mark}{e(nv) if nv else '—'}{mark} | "
                    f"{wn if wn is not None else ' '} | {e(en)} |\n")
    print(f"gerado: {a.dst}")
    print(f"  {mudados} propostas de {len(linhas)} textos")
    print(f"  cabem em {LIM} px: {cabe_agora} -> {cabe_depois}")
    if faltando:
        print(f"  ATENCAO caracteres fora da fonte: {faltando}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
