# Revisão dos textos em português — proposta

> Gerado por `tools/propoe_textos.py`. **Nada foi gravado no firmware.**
>
> Revise a coluna **proposto**. O que você mudar, eu aplico com `patch_menu_text.py`,
> que grava a string nova na área livre e repõe o ponteiro — nunca edita no lugar.

- **175 de 216** textos com proposta de mudança
- cabem em 113 px: **121 hoje → 176 depois**
- motivos: `pt-BR` regionalismo · `erro` tradução errada · `curto` não cabe na tela

---

| id | motivo | atual | px | **proposto** | px | en |
|---:|---|---|---:|---|---:|---|
| 0 |   | Português | 57 | — |   | English |
| 1 |   | Música | 39 | — |   | Music |
| 2 |   | Livro digital | 62 | — |   | Ebook |
| 3 |   | Vídeo | 31 | — |   | Video |
| 4 |   | Imagem | 46 | — |   | Pictures |
| 5 |   | Gravação | 52 | — |   | Recorder |
| 6 |   | Rádio | 33 | — |   | FM |
| 7 |   | Despertador | 69 | — |   | Alarm |
| 8 | pt-BR | Ver pastas | 59 | **Pastas** | 39 | Folder |
| 9 |   | Bluetooth | 52 | — |   | Bluetooth |
| 10 |   | Configurar | 58 | — |   | Settings |
| 11 |   | Dicionário | 56 | — |   | Dictionary |
| 12 |   | Todas as músicas | 103 | — |   | All songs |
| 13 | erro | Última jogada | 77 | **Últimas tocadas** | 90 | Last played |
| 14 | erro | Em curso play | 78 | **Tocando agora** | 83 | Playing Now |
| 15 |   | Artista | 34 | **Artistas** | 41 | Artists |
| 16 |   | Álbum | 35 | **Álbuns** | 38 | Albums |
| 17 |   | Meu favorito | 65 | **Favoritas** | 50 | Favorites |
| 18 |   | Pesquisa | 53 | **Procurando** | 64 | Searching |
| 19 |   | Iniciar a gravação | 96 | **Iniciar gravação** | 86 | Start Voice Recording |
| 20 | curto | Biblioteca de Gravação | 126 | **Gravações** | 59 | Recordings library |
| 21 |   | Gravação | 52 | **Gravando** | 53 | In Recording |
| 22 |   | Pausa de gravação | 106 | **Pausar** | 40 | Pause |
| 23 | curto | Despertador(Abrir/Fechado) | 153 | **Ativar alarme** | 71 | Alarm On/Off |
| 24 |   | Hora do alarme | 86 | **Definir alarme** | 78 | Add Alarm |
| 25 |   | Relógio despertador | 113 | **Repetição** | 56 | Alarm Cycle |
| 26 |   | Tempo único | 72 | **Uma vez** | 47 | Once |
| 27 |   | Todos os dias | 79 | — |   | Daily |
| 28 |   | Dias úteis | 56 | — |   | Working day |
| 29 |   | Bluetooth | 52 | — |   | Bluetooth |
| 30 | curto | Nome do equipamento | 127 | **Nome** | 34 | Device name |
| 31 | curto | Dispositivos emparelhados | 152 | **Pareados** | 54 | Paired Device |
| 32 | curto | Dispositivo de pesquisa | 133 | **Procurar** | 47 | Search Device |
| 33 |   | Emparelhamento | 96 | **Pareando** | 54 | Pairing |
| 34 | curto | Dispositivo de pesquisa | 133 | **Procurando** | 64 | Searching |
| 35 | curto | Dispositivos disponíveis | 134 | **Disponíveis** | 65 | Available Devices |
| 36 |   | Hora e data | 64 | — |   | Date & time |
| 37 | pt-BR | Língua | 38 | **Idioma** | 38 | Language |
| 38 |   | Informação | 62 | **Informações** | 69 | Information |
| 39 | curto | Opções de actualização | 131 | **Atualização** | 62 | Update Options |
| 40 | curto | Configuração de fábrica | 131 | **Restaurar** | 55 | Factory Settings |
| 41 |   | Definir a data | 73 | **Data** | 26 | Set The Date |
| 42 |   | Definir a hora | 74 | **Hora** | 27 | Set The Time |
| 43 | curto | Informações sobre o equipamento | 190 | **Sobre o aparelho** | 95 | Device Information |
| 44 |   | Número da versão | 102 | **Versão** | 39 | Version No. |
| 45 |   | Actualização do PC | 105 | **Atualizar por PC** | 87 | PC Upgrade |
| 46 | curto | Actualização do cartão SD | 142 | **Atualizar por SD** | 87 | Update the firmware from native storage |
| 47 | curto | Não foram detectados dispositivos de armazenamento | 301 | **Sem armazenamento** | 119 | No Memory Device Detected |
| 48 | curto | Não foram detectados ficheiros de música | 233 | **Nenhuma música encontrada** | 164 | No Music Files Detected |
| 49 | curto | Nenhum ficheiro de ebook detectado | 202 | **Nenhum e-book encontrado** | 154 | No Ebooks Detected |
| 50 | curto | Não foram detectados ficheiros de vídeo | 221 | **Nenhum vídeo encontrado** | 145 | No Videos Detected |
| 51 | curto | Não foi detectado nenhum ficheiro de imagem | 254 | **Nenhuma imagem encontrada** | 169 | No Pictures Detected |
| 52 | curto | Ficheiro não detectado | 125 | **Nenhum arquivo encontrado** | 156 | No Files Detected |
| 53 | curto | Dados do dicionário não detectados | 199 | **Sem dados de dicionário** | 138 | No Dictionary Data Detected |
| 54 |   | “Favorito”Sem canções | 127 | **Sem favoritas** | 75 | Loved / No Songs Found |
| 55 | pt-BR | Transferir ficheiros | 103 | **Transferir arquivos** | 103 | Charge & Transfer |
| 56 | erro | Apenas cobrar | 80 | **Apenas carregar** | 91 | Charge & Play |
| 57 |   | Pesquisa da estação | 117 | **Buscando estações** | 110 | Radio Searching |
| 58 | curto | Não foi detectada nenhuma informação do álbum | 272 | **Nenhum álbum encontrado** | 151 | No Albums Retrieved |
| 59 | curto | Nenhuma informação do cantor foi detectada | 247 | **Nenhum artista encontrado** | 150 | No Artits Retrieved |
| 60 | pt-BR | Ficheiros de música não suportados | 202 | **Áudio não suportado** | 114 | Music Files Not Supported |
| 61 | erro | Todos removidos"Favorito"Canção | 190 | **Favoritas removidas** | 111 | All/ Favorite / Removed |
| 62 | curto | O ficheiro de gravação não foi encontrado | 227 | **Nenhuma gravação encontrada** | 173 | No Recording Files Found |
| 63 |   | Formato de imagem não suportado | 195 | **Imagem não suportada** | 129 | Image Formats Not Supported |
| 64 |   | Formato de vídeo não suportado | 178 | **Vídeo não suportado** | 114 | Video Formats Not Supported |
| 65 |   | Ligação falhou | 81 | **Falha na conexão** | 97 |   |
| 66 |   | Erro desconhecido #101 | 135 | — |   | Unknown error #101 |
| 67 |   |   | 3 | — |   |   |
| 68 |   | Não encontrado | 88 | — |   | Not Found |
| 69 |   | Ano | 21 | — |   | YY |
| 70 |   | Mês | 23 | — |   | MM |
| 71 |   | Dia | 19 | — |   | DD |
| 72 |   | Hora | 27 | — |   | HH |
| 73 | erro | Ramo | 34 | **Min** | 19 | MM |
| 74 |   | Segundo | 50 | **Seg** | 22 | SS |
| 75 |   | Carregamento | 80 | **Carregando** | 66 | Loading |
| 76 |   | Nenhuma palavra encontrada | 163 | **Palavra não encontrada** | 130 | This word cannot be found |
| 77 |   | Ligar | 28 | **Conectar** | 50 | Connect |
| 78 |   | Desligar | 47 | **Desconectar** | 70 | Disconnect |
| 79 | erro | Desajustar | 61 | **Desparear** | 59 | Unpair |
| 80 | curto | Por favor, desligue o dispositivo ligado primeiro | 260 | **Desconecte o aparelho atual** | 158 | Please Disconnect the Device at First |
| 81 |   | Dispositivos disponíveis | 134 | **Disponíveis** | 65 | Available Devs |
| 82 |   | Configuração emparelhada | 151 | **Pareados** | 54 | Paired Devs |
| 83 |   | Ligado | 38 | **Conectado** | 60 | Connected |
| 84 |   | Na ligação | 59 | **Conectando** | 67 | Connecting |
| 85 |   | Desligado | 57 | **Desconectado** | 80 | Disconnected |
| 86 |   | Desconectar | 70 | **Desconectando** | 87 | Disconnecting |
| 87 | curto | Desligamento sem carga | 140 | **Desligar sozinho** | 93 | Idle Shutdown |
| 88 | curto | Definir o tempo de paragem inactiva | 198 | **Tempo para desligar** | 115 | Set the Idle Shutdown Time |
| 89 | curto | Por favor, desligue o dispositivo ligado primeiro | 260 | **Desconecte o aparelho atual** | 158 | Please Disconnect the Connected Device at First |
| 90 |   | Configuração de fábrica | 131 | **Padrão de fábrica** | 97 | Factory settings |
| 91 | curto | Restaurar as configurações de fábrica | 210 | **Restaurar padrões** | 104 | Restore factory settings |
| 92 |   | Sim | 22 | — |   | Yes |
| 93 |   | Não | 23 | — |   | No |
| 94 | curto | Seleccionar o tipo de ligação | 158 | **Tipo de conexão** | 90 | Connection Options |
| 95 | curto | Bateria fraca , Por favor, carregue ! | 187 | **Bateria fraca. Carregue!** | 130 | Low Power! Please Recharge! |
| 96 | curto | Potência abaixo10%% , Por favor, carregue ! | 241 | **Bateria abaixo de 10%%** | 134 | Power is Lower than 10%%, Please Recharge! |
| 97 | pt-BR | Configuração do ecrã | 118 | **Tempo de tela** | 79 | Backlight Timer |
| 98 | pt-BR | Definir o tempo de repouso do ecrã | 194 | **Tempo até apagar** | 101 | Set Backlight Time |
| 99 | pt-BR | O ecrã está sempre ligado | 146 | **Sempre ligada** | 81 | Always ON |
| 100 |   | Equalizador | 65 | — |   | Equalizer |
| 101 |   | Normal | 41 | — |   | Normal |
| 102 |   | Popular | 43 | **Pop** | 22 | Pop |
| 103 | erro | Rocha | 36 | **Rock** | 28 | Rock |
| 104 | erro | Senhor | 40 | **Jazz** | 23 | Jazz |
| 105 |   | Clássico | 49 | — |   | Classical |
| 106 |   | Música de dança | 93 | **Dance** | 36 | Dance |
| 107 | erro | Rural | 30 | **Country** | 42 | Country |
| 108 | pt-BR | Apagar o ficheiro | 92 | **Apagar arquivo** | 82 | Delete Files |
| 109 |   | Gravar a gravação | 99 | **Salvar gravação?** | 94 | Save or Not |
| 110 | pt-BR | Formato de ficheiro não suportado | 189 | **Arquivo não suportado** | 123 | Unsupported Files |
| 111 |   | Gravação de alta qualidade | 150 | **Alta qualidade** | 78 | High Quality |
| 112 |   | Despertador ligado,Desligar ou não? | 204 | **Alarme ativo. Desligar?** | 127 | The alarm is on, continue to turn off the mp3 player? |
| 113 | curto | Carregamento de dados, Espere um pouco | 239 | **Carregando, aguarde** | 118 | Loading, Please Wait |
| 114 |   | Pasta vazia | 62 | — |   | The Folder is Empty |
| 115 |   | Ligar, Tenta mais tarde | 127 | **Conectando, aguarde** | 119 | Connecting, please try again later |
| 116 | erro,curto | Configuração do tempo de reprodução automática | 276 | **Virar página a cada** | 106 | Set the Auto Page Turn Time |
| 117 |   | Cor de fundo | 71 | — |   | Background color |
| 118 | curto | Selecção do número da página | 172 | **Ir para página** | 76 | Select Page |
| 119 |   | Opções de favoritos | 109 | **Marcadores** | 65 | Bookmark |
| 120 |   | Preto | 29 | — |   | Black |
| 121 |   | Branco | 39 | — |   | White |
| 122 |   | Amarelo | 46 | — |   | Yellow |
| 123 |   | Apagar o favorito | 91 | **Apagar marcador** | 95 | Delete Bookmarks |
| 124 |   | Voltar à página inicial | 117 | **Voltar ao início** | 80 | Back to the Main Page |
| 125 | curto | Reprodução de velocidade variável | 191 | **Velocidade** | 61 | Variable Speed Playback |
| 126 | erro | Junta-te ao meu favorito | 131 | **Favoritar** | 47 | Add to Playlist |
| 127 |   | Remover dos favoritos | 123 | **Desfavoritar** | 66 | Remove from Playlist |
| 128 |   | Repetir a reprodução | 116 | **Modo** | 30 | Play mode |
| 129 |   | Circulação unitária | 103 | **Repetir uma** | 68 | Loop Single |
| 130 |   | Repetir tudo | 67 | — |   | Loop All |
| 131 |   | Aleatório | 48 | — |   | Shuffle |
| 132 |   | Velocidade dupla | 95 | **Velocidade** | 61 | Speed |
| 133 | curto | Predefinições estação de rádio | 171 | **Estações salvas** | 91 | Preset FM Stations |
| 134 | curto | Faixa de radiofrequência | 135 | **Faixa de FM** | 65 | Radio Bands |
| 135 |   | Banda Japonesa | 94 | **Japão** | 34 | Japan |
| 136 |   | Banda Europeia | 89 | **Europa** | 40 | Europe |
| 137 | curto | Banda de frequência comum | 159 | **Padrão** | 40 | Normal |
| 138 | curto | Apagar Predefinições estação de rádio | 213 | **Apagar estações** | 93 | Delete the Presets |
| 139 | curto | Os dados de digitalização do cartão SD falharam, Substituir o cartão SD | 393 | **Falha ao ler o cartão SD** | 132 | SD card data scanning failed, please replace it and try again! |
| 140 |   | A abertura de imagens vai parar a música,⏎⏎ Continuar? | 232 | **Isso vai parar a música.⏎⏎Continuar?** | 131 | Music would be stopped if you open the picture, continue? |
| 141 |   | Registo de qualidade normal | 160 | **Qualidade normal** | 99 | Normal Record |
| 142 |   | Detecção de voz | 89 | — |   | VAD |
| 143 |   | Brilho | 32 | — |   | Brightness |
| 144 | pt-BR | Actualizar a lista de reprodução | 171 | **Atualizar biblioteca** | 102 | Update Playlist |
| 145 |   | Pesquisa automática | 117 | **Busca automática** | 99 | Auto Search FM |
| 146 | curto | Pesquisa automática de canais concluída | 230 | **Busca concluída** | 91 | Auto Search FM done |
| 147 | curto | Vazio Predefinições estação de rádio | 203 | **Estações apagadas** | 111 | Clear All Preset FM |
| 148 | curto | Ligar auscultadores como antena de rádio | 233 | **Conecte o fone: ele é a antena** | 167 | Please Insert Earphone as FM Antenna. |
| 149 |   | Entrar na pasta | 84 | **Abrir pasta** | 59 | Enter Directory |
| 150 | pt-BR,erro | Digitalizar o ficheiro | 107 | **Lendo arquivos** | 85 | File Sanning |
| 151 |   | Sair da pasta | 73 | **Voltar** | 31 | Leave Directory |
| 152 |   | Criar índice | 63 | — |   | Build Index |
| 153 |   | Criar dados completos | 126 | **Concluído** | 56 | Finished |
| 154 | pt-BR,erro | Digitalizar o ficheiro,⏎Não desligue nem desligue | 110 | **Lendo arquivos.⏎Não desligue nem remova o cartão.** | 88 | Do not remove the card or power off while file scanning. |
| 155 |   | Desligar | 47 | — |   | Power Off |
| 156 |   | TP version: | 61 | — |   | TP version: |
| 157 | curto | Melhorar após manter energia suficiente | 222 | **Carregue antes de atualizar** | 152 | Please keep the battery enough before upgrading |
| 158 | curto | Cartão SD cheio, Não é possível criar dados, Libertem algum espaço | 380 | **Cartão SD cheio. Libere espaço.** | 178 | SD is full, can not build up db |
| 159 | pt-BR | Aplicação | 53 | **Aplicativos** | 58 | APP |
| 160 | pt-BR | Protector de Ecrã | 94 | **Protetor de tela** | 83 | Screen Saver |
| 161 |   | Carrega primeiro⏎Utilizar após 10 minutos | 94 | **Carregue por 10 minutos⏎antes de usar** | 138 | Please charge it for 10 minutes before using it |
| 162 |   | cancelar | 47 | **Cancelar** | 50 | Cancel |
| 163 | pt-BR | Tempo do protector de ecrã | 151 | **Tempo do protetor** | 101 | Screen Saver Time |
| 164 |   | Gravar a taxa de bits | 111 | **Taxa de bits** | 66 | Recording bit rate |
| 165 |   | Cena de gravação | 100 | **Ambiente** | 52 | Recording scene |
| 166 | curto | Segmentação do registo | 135 | **Dividir gravação** | 87 | Recording segment |
| 167 | curto | Gravação por voz controlada | 154 | **Ativada por voz** | 80 | Voice-activated recording |
| 168 | curto | Monitorização dos registos | 147 | **Monitorar gravação** | 104 | Recording monitor |
| 169 | curto | Gravação cronometrada | 132 | **Gravação agendada** | 111 | Timing recording |
| 170 |   | fechar | 34 | **Desligado** | 57 | Closure |
| 171 |   | entrevista | 53 | **Entrevista** | 54 | Interview |
| 172 |   | reunião | 42 | **Reunião** | 47 | Meeting |
| 173 |   | estação | 44 | **Estação** | 45 | Station |
| 174 |   | ensino | 38 | **Aula** | 24 | Teaching |
| 175 | curto | Configuração da gravação | 144 | **Gravação** | 52 | The recording setting |
| 176 |   | hora de início | 74 | **Início** | 29 | start time |
| 177 |   | Hora final | 53 | **Fim** | 21 | finish time |
| 178 |   | Ciclo de temporização | 122 | **Repetição** | 56 | timing cycle |
| 179 |   | Modo de música | 91 | **Modo música** | 74 | music mode |
| 180 |   | Modo de chamada | 102 | **Modo chamada** | 85 | phone mode |
| 181 |   | Ligue o Bluetooth | 96 | **Ative o Bluetooth** | 90 | Please turn on bluetooth |
| 182 | curto | Insira o fone de ouvido para monitorar a gravação | 271 | **Conecte o fone para monitorar** | 167 | Please plug in headphones for recording monitoring |
| 183 |   | Chamar | 45 | **Chamada recebida** | 106 | incoming call |
| 184 | erro | Programa de demonstração | 155 | **Teste de desempenho** | 125 | benchmark |
| 185 |   | a ligação falhou | 87 | **Falha na conexão** | 97 | Connection failed |
| 186 | pt-BR | remover pastas | 86 | **Apagar pastas** | 80 | Delete folders |
| 187 | curto | A estação predefinida está vazia | 176 | **Nenhuma estação salva** | 134 | The preset station is empty |
| 188 | curto | Desligamento cronometrado | 158 | **Desligar programado** | 118 | Timed shutdown |
| 189 | curto | Definir a hora de encerramento agendada | 230 | **Hora para desligar** | 103 | Set timed shutdown time |
| 190 |   | Reprodução sequencial | 132 | **Em ordem** | 58 | Sequential play |
| 191 | erro | Luz-chave | 55 | **Luz dos botões** | 84 | Key light |
| 192 |   | Som externo | 69 | — |   | External sound |
| 193 |   | fechado | 44 | **Desligado** | 57 | OFF |
| 194 |   | abrir | 25 | **Ligado** | 38 | ON |
| 195 | curto | Estado do armazenamento | 149 | **Armazenamento** | 90 | Storage status |
| 196 | curto | Capacidade total： | 105 | **Total:** | 30 | Total capacity: |
| 197 | curto | Capacidade restante： | 127 | **Livre:** | 29 | Remaining capacity: |
| 198 |   | Senha ligada | 73 | **Senha ao ligar** | 80 | Power-on password |
| 199 |   | Mudar a Senha | 83 | **Mudar senha** | 72 | Change password |
| 200 |   | Erro da senha | 78 | **Senha incorreta** | 87 | Wrong password |
| 201 |   | Gravação gravada | 99 | **Gravação salva** | 84 | Record saved |
| 202 | curto | O rádio precisa ser conectado como uma antena | 268 | **O fone é a antena do rádio** | 145 | The radio needs to be plugged in as an antenna |
| 203 | curto | Por favor, não desligue o conector USB durante a transferência de arquivos | 411 | **Não desconecte o USB durante a transferência** | 258 | Do not remove the USB port while transferring files |
| 204 | curto | Nenhuma página encontrada | 161 | **Página não encontrada** | 128 | The page cannot be found |
| 205 |   | Senha original： | 92 | **Senha atual:** | 69 | Original password: |
| 206 |   | Nova senha： | 78 | **Nova senha:** | 69 | New password: |
| 207 | pt-BR | Introduza novamente a nova senha： | 203 | **Repita a nova senha:** | 116 | Please enter the new password again: |
| 208 |   | Erro de entrada! | 88 | **Entrada inválida** | 88 | Input error! |
| 209 | pt-BR | Introduza por favor uma senha： | 178 | **Digite a senha:** | 83 | Please enter the password: |
| 210 | curto | Erro de reprodução de vídeo | 155 | **Erro ao abrir o vídeo** | 110 | Error playing video |
| 211 |   | Formatar o cartão sd | 114 | **Formatar cartão SD** | 107 | Formatting an SD Card |
| 212 |   | Formatação concluída | 122 | **Concluído** | 56 | Formatting completed |
| 213 | curto | Formatando o cartão sd, não desconecte o cartão ou desligue | 340 | **Formatando. Não remova o cartão nem desligue.** | 269 | The SD card is being formatted, Do not remove or power off the card |
| 214 | curto | Formatação falhou por favor, vá para o pc e tente | 265 | **Falha ao formatar. Tente no PC.** | 174 | Formatting fails. Try it on the PC |
| 215 |   | SD card error | 73 | **Erro no cartão SD** | 97 | SD card error |
