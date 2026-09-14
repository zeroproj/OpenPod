# Textos do sistema — todos os idiomas

> Gerado por `tools/exporta_textos.py` a partir de `GN438_openpod_v073_carimbado.bin`.
> **Este arquivo é para revisão.** Edite a coluna `pt` à vontade; depois eu gero o patch
> com `tools/patch_menu_text.py`, que nunca edita string no lugar — grava a nova na área
> livre e repõe o ponteiro.

> **Atenção:** esta tabela é a **tabela de idiomas**, não é tudo que a tela
> mostra. Das 243 chamadas de texto nas telas, só **35** vêm daqui.
> O restante está em `docs/TEXTOS_FIXOS.md` — inclusive texto em **inglês
> fixo no código** (`Time's up!`, `OK`, `yes`, `no`), que nenhuma tradução
> alcança.

## Como ler

- **px** = largura do texto em português, medida com a fonte real do firmware.
- **CORTA** = passa de 113 px e será truncado nas listas do sistema (Extras, Configurar).
  Na home o limite é 122 px.
- Linha em branco = id não usado naquele idioma.

**38 textos em português passam de 113 px.**

---

| id | px | | pt | en | es | fr | it | de | nl | zh |
|---:|---:|---|---|---|---|---|---|---|---|---|
| 0 | 57 |  | Português | English | Español | Français | Italiano | Deutsch | Nederlands | 中文 |
| 1 | 39 |  | Música | Music | Música | Musique | Musica | Musik | Muziek | 音乐 |
| 2 | 62 |  | Livro digital | Ebook | Libro Electrónico | Ebook | Ebook | E-buch | E-boek | 电子书 |
| 3 | 31 |  | Vídeo | Video | Video | Vidéo | Video | Video | Video | 视频 |
| 4 | 46 |  | Imagem | Pictures | Imágenes | Images | Immagini | Bilder | Foto's | 图片 |
| 5 | 52 |  | Gravação | Recorder | Grabadora | Enregistreur | Registratore | Rekorder | Recorder | 录音机 |
| 6 | 33 |  | Rádio | FM | FM | FM | FM | FM-Radio | Radio | 收音机 |
| 7 | 69 |  | Despertador | Alarm | Alarma | Alarme | Allarme | Wecker | Wekker | 闹钟 |
| 8 | 39 |  | Pastas | Folder | Carpeta | Dossiers | Cartella | Ordner | Mappen | 文件夹 |
| 9 | 52 |  | Bluetooth | Bluetooth | Bluetooth | Bluetooth | Bluetooth | Bluetooth | Bluetooth | 蓝牙 |
| 10 | 58 |  | Configurar | Settings | Ajustes | Paramètres | Impostazioni | Einstellungen | Instellingen | 设置 |
| 11 | 56 |  | Dicionário | Dictionary | Dictionary | Dictionary | Dictionary | Dictionary | Woordenboek | 词典 |
| 12 | 103 |  | Todas as músicas | All songs | Todas Canciones | Toutes les chansons | Tutte le canzoni | Alle Lieder | alle muziek | 所有歌曲 |
| 13 | 90 |  | Últimas tocadas | Last played | Última Reproducción | Dernière lecture | Ultimo riprodotto | Zuletzt gespielt | Laatst afgespeeld | 上一次播放 |
| 14 | 83 |  | Tocando agora | Playing Now | Reproduciendo Ahora | En cours de lecture | Riproduzione in corso | Wird jetzt gespielt | Huidige muziek | 正在播放 |
| 15 | 41 |  | Artistas | Artists | Artistas | Artistes | Artisti | Künstler | Artiesten | 艺术家 |
| 16 | 38 |  | Álbuns | Albums | Álbumes | Albums | Album | Alben | Albums | 专辑 |
| 17 | 50 |  | Favoritas | Favorites | Listas de Reproducción | Listes de lecture | Playlist | Wiedergabelisten | Mijn favorieten | 我的最爱 |
| 18 | 64 |  | Procurando | Searching | Buscando | Recherche | Ricerca | Suche | Zoeken | 搜索中 |
| 19 | 86 |  | Iniciar gravação | Start Voice Recording | Iniciar Grabación de Voz | Démarrer l'enregistrement vocal | Avviare la registrazione vocale | Sprachaufnahme starten | Begin spraakopname | 开始语音录音 |
| 20 | 59 |  | Gravações | Recordings library | Biblioteca de Grabaciones | Bibliothèque d'enregistrement | Libreria di registrazione | Aufnahme-Bibliothek | Opnamebibliotheek | 录音库 |
| 21 | 53 |  | Gravando | In Recording | En Grabación | En cours d'enregistrement | Registrazione in corso | In Aufnahme | Opnemen | 正在录音 |
| 22 | 40 |  | Pausar | Pause | Pausa | Pause | Pausa | Pause | Opname onderbroken | 录音暂停 |
| 23 | 71 |  | Ativar alarme | Alarm On/Off | Alarma(Enc/Apg) | Activation/désactivation de l'alarme | Allarme On/Off | Wecker ein/aus | Alarm aan/uit | 闹钟（开/关） |
| 24 | 78 |  | Definir alarme | Add Alarm | Agregar Alarma | Ajouter une alarme | Aggiungi allarme | Wecker hinzufügen | Tijd wekker | 闹钟时间 |
| 25 | 56 |  | Repetição | Alarm Cycle | Ciclo de alarma | Cycle d'alarme | Ciclo di allarme | Takt der Erinnerung | Alarmcyclus | 闹钟周期 |
| 26 | 47 |  | Uma vez | Once | Una Vez | Une fois | Una volta | Einmal | Een keer | 单次 |
| 27 | 79 |  | Todos os dias | Daily | Diario | Quotidiennement | Quotidiano | Täglich | Dagelijks | 每日 |
| 28 | 56 |  | Dias úteis | Working day | Día Hábil | Jour ouvrables | Giorno lavorativo | Arbeitstag | Werkdagen | 工作日 |
| 29 | 52 |  | Bluetooth | Bluetooth | Bluetooth | Bluetooth | Bluetooth | Bluetooth | Bluetooth | 蓝牙 |
| 30 | 34 |  | Nome | Device name | Nombre del Dispositivo | Nom de l'appareil | Nome del dispositivo | Gerät Name | Naam apparaat | 设备名称 |
| 31 | 54 |  | Pareados | Paired Device | Dispositivo Emparejados | Appareil jumelés | Dispositivo accoppiato | Gekoppeltes Geräte | Gekoppelde apparaten | 已配对设备 |
| 32 | 47 |  | Procurar | Search Device | Buscando Dispositivos | Rechercher un appareil | Cerca dispositivo | Gerät suchen | Zoek apparaat | 搜索设备 |
| 33 | 54 |  | Pareando | Pairing | Emparejando | Jumelage | Abbinamento in corso | Koppeln | Koppelen | 配对中, 请勿退出 |
| 34 | 64 |  | Procurando | Searching | Buscando | Recherche | Cercando | Suchen | Zoeken | 搜索设备中 |
| 35 | 65 |  | Disponíveis | Available Devices | Dispositivos Disponibles | Appareils disponibles | Dispositivi disponibili | Verfügbare Geräte | Beschikbare apparaten | 可用设备 |
| 36 | 64 |  | Hora e data | Date & time | Fecha & Hora | Date & Heure | Data e ora | Datum und Uhrzeit | Tijd en datum | 时间和日期 |
| 37 | 38 |  | Idioma | Language | Idioma | Langues | Lingua | Sprache | Taal | 语言 |
| 38 | 69 |  | Informações | Information | Información | Informations | Informazioni | Informationen | Informatie | 信息 |
| 39 | 62 |  | Atualização | Update Options | Opciones de Actualización | Options de mise à niveau | Opzioni di aggiornamento | Aktualisierungsoptionen | Upgrade-opties | 升级选项 |
| 40 | 87 |  | Atualizar por SD | Factory Settings | Ajustes de Fábrica | Paramètres d'usine | Impostazioni di fabbrica | Werkseinstellungen | Fabrieksinstellingen | 出厂设定 |
| 41 | 26 |  | Data | Set The Date | Establecer la Fecha | Régler la date | Impostare la data | Einstellen des Datums | Instellen datum | 设置日期 |
| 42 | 27 |  | Hora | Set The Time | Establece el Tiempo | Régler l'heure | Impostare l'ora | Einstellen der Uhrzeit | Instellen tijd | 设置时间 |
| 43 | 95 |  | Sobre o aparelho | Device Information | Información del Dispositivo | Informations sur l'appareil | Informazioni sul dispositivo | Geräte-Informationen | Apparaatinformatie | 设备信息 |
| 44 | 39 |  | Versão | Version No. | Versión No. | N° de version | N° di versione | Versions-Nr. | Version No. | 版本号 |
| 45 | 87 |  | Atualizar por PC | PC Upgrade | Actualización de PC | Mise à niveau du PC | Aggiornamento del PC | PC Aktualisieren | PC upgrade | 电脑升级 |
| 46 | 87 |  | Atualizar por SD | Update the firmware from native storage | Actualizar el firmware desde el almacenamiento nativo | Mettre à jour le firmware à partir du stockage natif | Aggiornare il firmware dalla memoria nativa | Aktualisieren der Firmware aus dem nativen Speicher | SD kaart upgrade | 从本机存储器更新固件 |
| 47 | 119 | **CORTA** | Sem armazenamento | No Memory Device Detected | No Se Detectaron Dispositivos de Memoria | Aucun appareil de mémoire détecté | Nessun dispositivo di memoria rilevato | Kein Speichergerät erkannt | Geen geheugenkaart gedetecteerd | 未检测到存储设备 |
| 48 | 164 | **CORTA** | Nenhuma música encontrada | No Music Files Detected | No Se Detectaron Archivos de Música | Aucun fichier musical détecté | Nessun file musicale rilevato | Keine Musikdateien erkannt | Geen muziekbestanden gedetecteerd | 未检测到音乐文件 |
| 49 | 154 | **CORTA** | Nenhum e-book encontrado | No Ebooks Detected | No Se Detectaron Libros Electrónicos | Aucun Ebook n'est détecté | Nessun Ebook rilevato | Keine E-Bücher erkannt | Geen E-book bestanden gedetecteerd | 未检测到电子书文件 |
| 50 | 145 | **CORTA** | Nenhum vídeo encontrado | No Videos Detected | No Se Detectaron Videos | Aucune vidéo n'est détectée | Nessun video rilevato | Keine Videos erkannt | Geen videobestanden gedetecteerd | 未检测到视频文件 |
| 51 | 169 | **CORTA** | Nenhuma imagem encontrada | No Pictures Detected | Archivo de imagen no detectado | Aucun fichier image détecté | Nessun file di immagini rilevato | Keine Bilddateien erkannt | Geen fotobestanden gedetecteerd | 未检测到图片文件 |
| 52 | 156 | **CORTA** | Nenhum arquivo encontrado | No Files Detected | No Se Detectaron Archivos | Aucun fichier détecté | Nessun file rilevato | Keine Dateien erkannt | Geen bestanden gedetecteerd | 未检测到文件 |
| 53 | 138 | **CORTA** | Sem dados de dicionário | No Dictionary Data Detected | No se han detectado datos del diccionario | Aucune donnée du dictionnaire détectée | Dati del dizionario non rilevati | Daten des Wörterbuchs nicht erkannt | Geen woordenboeken gedetecteerd | 未检测到词典数据 |
| 54 | 75 |  | Sem favoritas | Loved / No Songs Found | Favoritos / Canción Vacía | Favoris / Aucune chanson trouvée | Preferito / Nessuna canzone trovata | Favorit / Keine Lieder gefunden | Geen favoriete nummers gevonden | “最爱”歌曲为空 |
| 55 | 103 |  | Transferir arquivos | Charge & Transfer | Transferencia de archivos | Charger & Transférer | Carica e trasferimento | Aufladen & Übertragen | Bestanden overzetten | 传输文件 |
| 56 | 91 |  | Apenas carregar | Charge & Play | Cargar Sólo | Recharge & Lecture | Caricare e riprodurre | Aufladen & Abspielen | Opladen | 仅充电 |
| 57 | 110 |  | Buscando estações | Radio Searching | Buscando Radios | Recherche par radio | Ricerca radio | Radio suchen | Radio zoeken | 电台搜索中 |
| 58 | 151 | **CORTA** | Nenhum álbum encontrado | No Albums Retrieved | No Se Recuperaron Álbumes | Aucun album trouvé | Nessun album recuperato | Keine Alben abgerufen | Geen albums opgehaald | 未检索到专辑信息 |
| 59 | 150 | **CORTA** | Nenhum artista encontrado | No Artits Retrieved | No Se Recuperaron Artistas | Aucun artiste trouvé | Nessun artista recuperato | Keine Singer abgerufen | Geen artiesten opgehaald | 未检索到歌手信息 |
| 60 | 114 | **CORTA** | Áudio não suportado | Music Files Not Supported | Archivos de Música No Compatibles | Fichiers musicaux non pris en charge | File musicali non supportati | Musikdateien werden nicht unterstützt | Muziekbestanden niet ondersteund | 不支持的音乐文件 |
| 61 | 111 |  | Favoritas removidas | All/ Favorite / Removed | Todos / Favoritos / Eliminado | Tous/ Favoris / Supprimés | Tutti / Preferiti / Rimosso | Alle / Favorit / Entfernt | Alle favorieten nummers zijn verwijderd | 已移除所有"最爱"歌曲 |
| 62 | 173 | **CORTA** | Nenhuma gravação encontrada | No Recording Files Found | No Se Encontraron Archivos de Grabación | Aucun fichier d'enregistrement trouvé | Nessun file di registrazione trovato | Keine Aufnahmedateien gefunden | Geen opnamebestanden gevonden | 未找到录音文件 |
| 63 | 129 | **CORTA** | Imagem não suportada | Image Formats Not Supported | Formatos de Imagen No Compatibles | Formats d'image non pris en charge | Formati immagine non supportati | Bildformate werden nicht unterstützt | Afbeeldingsformat wordt niet ondersteund | 不支持的图片格式 |
| 64 | 114 | **CORTA** | Vídeo não suportado | Video Formats Not Supported | Formatos de Video No Compatibles | Formats vidéo non pris en charge | Formati video non supportati | Videoformate werden nicht unterstützt | Videoformat wordt niet ondersteund | 不支持的视频格式 |
| 65 | 97 |  | Falha na conexão |   |   |   |   |   | Verbinding mislukt | 连接失败 |
| 66 | 135 | **CORTA** | Erro desconhecido #101 | Unknown error #101 | No Encontrado | Erreur inconnue # 101 | Errore sconosciuto #101 | Unbekannter Fehler #101 | Onbekende fout #101 | 未知错误 #101 |
| 67 | 3 |  |   |   |   |   |   |   |   |   |
| 68 | 88 |  | Não encontrado | Not Found | No encontrado | Non trouvé | Non trovato | Nicht gefunden | Niet gevonden | 未找到 |
| 69 | 21 |  | Ano | YY | Año | Année | anno | Jahr | Jaar | 年 |
| 70 | 23 |  | Mês | MM | Mes | Mois | mese | Monat | Maand | 月 |
| 71 | 19 |  | Dia | DD | Día | Jour | giorno | Tag | Dag | 日 |
| 72 | 27 |  | Hora | HH | Time | Heure | Tempo | Zeit | Uur | 时 |
| 73 | 19 |  | Min | MM | Puntos | Points | Minute | Zweig | Minuten | 分 |
| 74 | 22 |  | Seg | SS | Segundos | Secondes | Secondi | Sekunde | seconden | 秒 |
| 75 | 66 |  | Carregando | Loading | Cargando | Chargement | Caricando | Ladet | laden | 加载中 |
| 76 | 130 | **CORTA** | Palavra não encontrada | This word cannot be found | Esta palabra no se puede encontrar | Ce mot ne peut être trouvé | Questa parola non può essere trovata | Dieses Wort kann nicht gefunden werden | Geen dergelijk woord gevonden | 查无此词 |
| 77 | 50 |  | Conectar | Connect | Conectar | Connecter | Connetti | Verbinden | Verbinden | 连接 |
| 78 | 70 |  | Desconectar | Disconnect | Desconectar | Déconnecter | Disconnetti | Verbindung trennen | Verbinding verbreken | 断开连接 |
| 79 | 59 |  | Desparear | Unpair | Desemparejar | Annuler le jumelage | Scollegare | Entkoppeln | Koppeling annuleren | 取消配对 |
| 80 | 158 | **CORTA** | Desconecte o aparelho atual | Please Disconnect the Device at First | Por favor, desconecte el dispositivo conectado primero | Veuillez d'abord déconnecter l'appareil | Disconnetti il dispositivo innanzitutto | Bitte trennen Sie zunächst die Verbindung zum Gerät | Koppel het gekoppelde apparaat eerst los | 请先断开已连接设备 |
| 81 | 65 |  | Disponíveis | Available Devs | Dispositivos disponibles | Appareils disponibles | Dispositivi disponibili | Verfügbare Geräte | Beschikbare apparaten | 可用设备 |
| 82 | 54 |  | Pareados | Paired Devs | Dispositivo emparejado | Appareils jumelés | Dispositivi accoppiati | Gekoppelte Geräte | Gekoppelde apparaten | 已配对设备 |
| 83 | 60 |  | Conectado | Connected | Conectado | Connecté | Collegato | Verbunden | Verbonden | 已连接 |
| 84 | 67 |  | Conectando | Connecting | Conectando | Connexion | Connessione in corso | Verbindet | Aan het verbinden | 连接中 |
| 85 | 80 |  | Desconectado | Disconnected | Desconectado | Déconnectés | Disconnesso | Getrennt | Ontkoppeld | 已断开 |
| 86 | 87 |  | Desconectando | Disconnecting | Desconectando | Déconnecté | Disconnessione in corso | Verbindung trennt  | Aan het ontkoppelen | 正在断开 |
| 87 | 93 |  | Desligar sozinho | Idle Shutdown | Apagado Inactivo | Arrêt au repos | Spegnimento inattivo | Leerlaufabschaltung | Automatisch uitschakelen | 闲置关机 |
| 88 | 115 | **CORTA** | Tempo para desligar | Set the Idle Shutdown Time | Configurar el Tiempo de Apagado Inactivo | Définir l'heure d'arrêt de la veille | Imposta il tempo per lo spegnimento inattivo | Leerlaufzeit für das Herunterfahren einstellen | Stel de tijd voor aut. uitschakelen in | 设置闲置关机时间 |
| 89 | 158 | **CORTA** | Desconecte o aparelho atual | Please Disconnect the Connected Device at First | Primero Desconecte el Dispositivo Conectado | Veuillez d'abord déconnecter l'appareil connecté | Disconnetti prima il dispositivo connesso. | Bitte trennen Sie zuerst das angeschlossene Gerät | Koppel het gekoppelde apparaat eerst los | 请先断开已连接设备 |
| 90 | 97 |  | Padrão de fábrica | Factory settings | Ajustes de Fábrica | Paramètres d'usine | Impostazioni di fabbrica | Werkseinstellungen | Fabrieksinstellingen | 出厂设定 |
| 91 | ? | ? | Atualizar o sistema pelo cartão SD? | Restore factory settings | Restaurar la Configuración de Fábrica | Restaurer les paramètres d'usine | Ripristina le impostazioni di fabbrica | Werkseinstellungen wiederherstellen | Terug naar fabrieksinstellingen | 恢复出厂设置 |
| 92 | 22 |  | Sim | Yes | Sí | Oui | Sì | Ja | Ja | 是 |
| 93 | 23 |  | Não | No | No | Non | No | Nein | Nee | 否 |
| 94 | 90 |  | Tipo de conexão | Connection Options | Opciones de Conexión | Options de connexion | Opzioni di connessione | Verbindungsoptionen | Selecteer type verbinding | 选择连接类型 |
| 95 | 130 | **CORTA** | Bateria fraca. Carregue! | Low Power! Please Recharge! | ¡Baja Potencia! ¡Por Favor Recargue! | Faible puissance ! Veuillez recharger ! | Bassa potenza! Ricarica per favore! | Niedrige Leistung! Bitte aufladen! | Batterij bijna leeg, gelieve op te laden! | 电量低 , 请充电 ! |
| 96 | 134 | **CORTA** | Bateria abaixo de 10%% | Power is Lower than 10%%, Please Recharge! | La Potencia es Inferior al 10%%, ¡Recargue! | La puissance est inférieure à 10%%, veuillez recharger ! | La potenza è inferiore al 10%%, ricarica per favore! | Energie ist niedriger als 10%%, bitte aufladen! | Batterijniveau onder 10%, gelieve op te laden! | 电量低于10%% , 请充电 ! |
| 97 | 79 |  | Tempo de tela | Backlight Timer | Temporizador de Luz de Fondo | Minuterie de rétroéclairage | Timer di retroilluminazione | Beleuchtungstimer | Timer achtergrondverlichting | 息屏设置 |
| 98 | 101 |  | Tempo até apagar | Set Backlight Time | Establecer el Tiempo de Luz de Fondo | Régler la durée du rétro-éclairage | Imposta il tempo di retroilluminazione | Beleuchtungszeit einstellen | Stel de tijd van achtergrondverlichting in | 设置息屏时间 |
| 99 | 81 |  | Sempre ligada | Always ON | Siempre Encendido | Toujours allumé | Sempre acceso | Immer an | Scherm altijd aan | 屏幕常亮 |
| 100 | 65 |  | Equalizador | Equalizer | Igualada | Égaliseur | Equalizzatore | Equalizer | Equalizer | 均衡器 |
| 101 | 41 |  | Normal | Normal | Normal | Normal | Normale | Normal | Normaal | 普通 |
| 102 | 22 |  | Pop | Pop | Pop | Pop | Pop | Pop | Pop | 流行 |
| 103 | 28 |  | Rock | Rock | Roca | Rock | Rock | Rock | Rock | 摇滚 |
| 104 | 23 |  | Jazz | Jazz | Jazz | Jazz | Jazz | Jazz | Jazz | 爵士 |
| 105 | 49 |  | Clássico | Classical | Clásico | Classique | Classica | Klassisch | Klassiek | 经典 |
| 106 | 36 |  | Dance | Dance | Danza | Danse | Danza | Tanz | Dance | 舞曲 |
| 107 | 42 |  | Country | Country | Campo | Campagne | Country | Land | Country | 乡村 |
| 108 | 82 |  | Apagar arquivo | Delete Files | Borrar Archivos | Supprimer des fichiers | Elimina i file | Dateien löschen | Verwijder bestand | 删除文件 |
| 109 | 94 |  | Salvar gravação? | Save or Not | Guardar o No | Enregistrer ou non | Salvare o no | Speichern oder nicht | Opname bewaren | 是否保存录音 |
| 110 | 123 | **CORTA** | Arquivo não suportado | Unsupported Files | Formato de archivo no soportado | Fichiers non pris en charge | File non supportati | Nicht unterstützte Dateien | Niet-ondersteunde bestandsformaten | 不支持的文件格式 |
| 111 | 78 |  | Alta qualidade | High Quality | Grabaciones de Alta Calidad | Enregistrements de haute qualité | Registrazioni di alta qualità | Aufnahmen in hoher Qualität | Opname van hoge kwaliteit | 高品质录音 |
| 112 | 127 | **CORTA** | Alarme ativo. Desligar? | The alarm is on, continue to turn off the mp3 player? | La alarma está encendida, ¿continuar apagando el reproductor de mp3? | L'alarme est activée, continuer à éteindre le lecteur ? | L'allarme è acceso, proseguire per spegnere il riproduttore mp3? | Der Wecker ist eingeschaltet, schalten Sie weiterhin den mp3-Player aus? | Alarm is ingeschakeld, doorgaan met uitschakelen? | 闹钟已开启请确认是否关机? |
| 113 | 118 | **CORTA** | Carregando, aguarde | Loading, Please Wait | Cargando, Por Favor Espere | Chargement, veuillez attendre | Caricamento in corso, attendi per favore | Ladet, bitte warten | Gegevens worden geladen, even geduld a.u.b. | 数据加载中, 请稍候 |
| 114 | 62 |  | Pasta vazia | The Folder is Empty | La Carpeta Está Vacía | Le dossier est vide | Cartella è vuota | Der Ordner ist leer | De map is leeg | 该文件夹为空 |
| 115 | 119 | **CORTA** | Conectando, aguarde | Connecting, please try again later | En conexión, por favor inténtelo de nuevo más tarde | Connexion, Veuillez réessayer plus tard | Connecting, riprova più tardi | Verbindung, Bitte versuchen Sie es später. | In verbinding, probeer het later opnieuw | 连接中, 请稍后重试 |
| 116 | 106 |  | Virar página a cada | Set the Auto Page Turn Time | Establecer el Tiempo de Giro Automático de Páginas | Régler le temps de rotation automatique des pages | Imposta il tempo di rotazione automatica della pagina | Einstellen der automatischen Umblätterzeit | Stel pagina omslaan tijd in | 自动播放时间设置 |
| 117 | 71 |  | Cor de fundo | Background color | Color de Fondo | Couleur de fond | Colore dello sfondo | Hintergrundfarbe | Achtergrond kleur | 背景颜色 |
| 118 | 76 |  | Ir para página | Select Page | Seleccionar Página | Sélectionner une page | Seleziona la pagina | Seite auswählen | Pagina selectie | 页数选择 |
| 119 | 65 |  | Marcadores | Bookmark | Marcador | Signet | Segnalibro | Lesezeichen | Bladwijzers | 书签选项 |
| 120 | 29 |  | Preto | Black | Negro | Noir | Nero | Schwarz | Zwart | 经典黑 |
| 121 | 39 |  | Branco | White | Blanco | Blanc | Bianco | Weiß | Wit | 纯白色 |
| 122 | 46 |  | Amarelo | Yellow | Amarillo | Jaune | Giallo | Gelb | Geel | 牛皮黄 |
| 123 | 95 |  | Apagar marcador | Delete Bookmarks | Eliminar Marcadores | Supprimer les signets | Elimina i segnalibri | Lesezeichen löschen | Bladwijzer verwijderen | 删除书签 |
| 124 | 80 |  | Voltar ao início | Back to the Main Page | Volver a la Página Principal | Retour à la page principale | Torna alla pagina principale | Zurück zur Hauptseite | Terug naar de hoofdpagina | 返回主页 |
| 125 | 61 |  | Velocidade | Variable Speed Playback | Reproducción de Velocidad Variable | Lecture à vitesse variable | Riproduzione a velocità variabile | Wiedergabe mit variabler Geschwindigkeit | Afspeelsnelheid | 变速播放 |
| 126 | 47 |  | Favoritar | Add to Playlist | Agregar a la Lista de Reproducción | Ajouter à la liste de lecture | Unisciti ai miei preferiti | Zur Wiedergabeliste hinzufügen | Toevoegen aan favorieten | 加入我的最爱 |
| 127 | 66 |  | Desfavoritar | Remove from Playlist | Quitar de la Lista de Reproducción | Supprimer de la liste de lecture | Togli dai miei preferiti | Aus Wiedergabeliste entfernen | Verwijderen uit favorieten | 从我的最爱中删除 |
| 128 | 30 |  | Modo | Play mode | Modo de juego | Mode de jeu | Modalità di gioco | Spiel-Modus | Afspeelmodus | 播放模式 |
| 129 | 68 |  | Repetir uma | Loop Single | Bucle Único  | Chanson unique | Loop singolo | Einzelzyklus | Herhaal enkel | 单曲循环 |
| 130 | 67 |  | Repetir tudo | Loop All | Bucle en Todo | Répéter tous | Loop tutti | Alles wiederholen | Herhaal alles | 全部重复 |
| 131 | 48 |  | Aleatório | Shuffle | Barajar | Aléatoire | Shuffle | Zufälliges Abspielen | Willekeurig afspelen | 随机播放 |
| 132 | 61 |  | Velocidade | Speed | Velocidad | Vitesse | Velocità | Geschwindigkeit | Snelheid | 倍速 |
| 133 | 91 |  | Estações salvas | Preset FM Stations | Estaciones de FM Preajustes | Stations FM préréglées | Stazioni FM preimpostate | Voreingestellter Radiosender | Vooraf ingestelde zenders | 预设电台 |
| 134 | 65 |  | Faixa de FM | Radio Bands | Bandas de Radio | Bandes radio | Bande radiofoniche | Radiofrequenzband | Radiofrequentie | 电台频段 |
| 135 | 34 |  | Japão | Japan | Japón | Japon | Giappone | Japan | Japanse frequentieband | 日本频段 |
| 136 | 40 |  | Europa | Europe | Europa | Europe | Europa | Europa | Europese frequentieband | 欧洲频段 |
| 137 | 40 |  | Padrão | Normal | Normal | Normal | Normale | Normal | Algemene frequentieband | 普通频段 |
| 138 | 93 |  | Apagar estações | Delete the Presets | Eliminar los Preajustes | Supprimer les présélections | Elimina i preset | Voreinstellungen löschen | Verwijderen van vooringestelde radio zenders | 删除预设电台 |
| 139 | 132 | **CORTA** | Falha ao ler o cartão SD | SD card data scanning failed, please replace it and try again! | Falló el escaneo de datos de la tarjeta SD, reemplácela y vuelva a intentarlo. | L'analyse des données de la carte SD a échoué, veuillez la remplacer et réessayer ! | La scansione dei dati della scheda SD non è riuscita, sostituiscila e riprova! | Die Überprüfung der SD-Karte ist fehlgeschlagen, bitte ersetzen Sie sie und versuchen Sie es erneut! | Sd-kaartgegevens kunnen niet worden gelezen. Vervang de sd-kaart | SD卡数据扫描失败, 请更换SD卡 |
| 140 | ? | ? | Isso vai parar a música.  Continuar? | Music would be stopped if you open the picture, continue? | La música se detendría si abres la imagen, ¿continuar? | La musique s'arrête si vous ouvrez l'image, continuez ? | La musica verrebbe interrotta se si apre l'immagine, continuare? | Die Musik wird gestoppt, wenn Sie das Bild öffnen, weiter? | De muziek stopt bij het bekijken van foto's, doorgaan? | 打开图片将停止音乐,  是否继续? |
| 141 | 99 |  | Qualidade normal | Normal Record | Grabación de Calidad Normal | Enregistrement de qualité normale | Registrazione di qualità normale | Gewöhnliche Aufnahmequalität. | Opname van normale kwaliteit | 普通品质录音 |
| 142 | 89 |  | Detecção de voz | VAD | VAD | VAD | VAD | Vocal-Stimmenerkennung | Stem geactiveerde opname | 声控模式 |
| 143 | 32 |  | Brilho | Brightness | Brillo | Luminosité | Luminosità | Bildschirmintensität | Helderheid | 亮度 |
| 144 | 102 |  | Atualizar biblioteca | Update Playlist | Actualizar Lista de Reproducción | Mise à jour de la liste de lecture | Aggiorna lista di riproduzione | Wiedergabeliste aktualisieren | Update bestanden | 更新播放列表 |
| 145 | 99 |  | Busca automática | Auto Search FM | Búsqueda Automática FM | Recherche automatique FM | Ricerca automatica FM | Auto-Suche FM | Zoeken | 自动搜台 |
| 146 | 91 |  | Busca concluída | Auto Search FM done | Búsqueda Automática de FM Hecho | Recherche automatique FM terminé | Ricerca automatica FM Fatto | Auto-Suche FM Erledigt | De zoekopdracht is voltooid | 自动搜台完成 |
| 147 | 111 |  | Estações apagadas | Clear All Preset FM | Borrar Todos los Preajustes de FM | Effacer toutes les présélections FM | Cancella tutti i preset FM | Alle voreingestellten FM löschen | Wissen vooraf ingestelde zenders | 清空预设电台 |
| 148 | 167 | **CORTA** | Conecte o fone: ele é a antena | Please Insert Earphone as FM Antenna. | Inserte el Auricular como Antena FM. | Veuillez insérer un casque comme antenne FM | Inserisci l'auricolare come antenna FM. | Bitte setzen Sie den Kopfhörer als FM-Antenne ein. | Sluit de hoofdtelefoon aan als radio antenne | 请连接耳机作为收音机天线 |
| 149 | 59 |  | Abrir pasta | Enter Directory | Enter Directory | Entrée dans le Répertoire | Inserisci directory | Verzeichnis eingeben | Toegang tot de catalogus | 进入目录 |
| 150 | 85 |  | Lendo arquivos | File Sanning | Escaneo de Archivos | Créer un index | Scansione dei file | Datei-Scan | Gescande documenten | 扫描文件 |
| 151 | 31 |  | Voltar | Leave Directory | Dejar el Directorio | Quitter le Répertoire | Lascia la cartella | Ordner verlassen | Vertrek uit de catalogus | 离开目录 |
| 152 | 63 |  | Criar índice | Build Index | Generar Índice | Index des constructions | Costruire l'indice | Index erstellen | Opbouw van de index | 构建索引 |
| 153 | 56 |  | Concluído | Finished | Finalizado | Terminé | Finito | Fertiggestellt | Opbouw van de gegevens voltooid | 构建数据完成 |
| 154 | ? | ? | Lendo arquivos. Não desligue nem remova o cartão. | Do not remove the card or power off while file scanning. | No retire la tarjeta ni la apague durante el escaneo de archivos. | Ne retirez pas la carte et ne mettez pas l'appareil hors tension pendant la numérisation des fichiers. | Non rimuovere la scheda o togliere l'alimentazione durante la scansione dei file. | Nehmen Sie die Karte nicht heraus und schalten Sie es nicht aus, während Sie Dateien scannen. | Het document wordt gescand, niet loskoppelen of afsluiten | 正在扫描文件, 请勿拔卡或关机 |
| 155 | 47 |  | Desligar | Power Off | Apagado | Hors tension | Spegnimento | Ausschalten | Uitschakeling | 关机 |
| 156 | 61 |  | TP version: | TP version: | TP version: | TP version: | versione TP: | TP version: | TP version: | TP version: |
| 157 | 152 | **CORTA** | Carregue antes de atualizar | Please keep the battery enough before upgrading | Mantenga la batería completamente cargada antes de actualizar. | Veuillez garder votre batterie complètement chargée avant de la mettre à niveau | Tieni la batteria completamente carica prima di effettuare l'aggiornamento. | Bitte halten Sie Ihre Batterie voll aufgeladen, bevor Sie sie aktualisieren | laad de batterij voldoende op voor de upgrade | 请保持电量充足后升级 |
| 158 | 178 | **CORTA** | Cartão SD cheio. Libere espaço. | SD is full, can not build up db | SD is full, can not build up db | SD is full, can not build up db | SD is full, can not build up db | SD is full, can not build up db | De sd-kaart is vol. Kan geen gegevens opslaan. Maak een deel van de ruimte vrij | SD卡已满, 无法构建数据, 请释放部分空间 |
| 159 | 58 |  | Aplicativos | APP | APP | APP | APP | APP | Toepassing | 应用 |
| 160 | 83 |  | Protetor de tela | Screen Saver | Screen Saver | Screen Saver | Screen Saver | Screen Saver | Screen Saver | 屏保 |
| 161 | ? | ? | Carregue por 10 minutos antes de usar | Please charge it for 10 minutes before using it | Please charge it for 10 minutes before using it | Please charge it for 10 minutes before using it | Please charge it for 10 minutes before using it | Please charge it for 10 minutes before using it | Gelieve 10 minuten opladen voor gebruik | 请先充电10分钟后再使用 |
| 162 | 50 |  | Cancelar | Cancel | Cancel | Cancel | Cancel | Cancel | Annuleren | 取消 |
| 163 | 101 |  | Tempo do protetor | Screen Saver Time | Screen Saver Time | Screen Saver Time | Screen Saver Time | Screen Saver Time | Screen Saver tijd | 屏保时间 |
| 164 | 66 |  | Taxa de bits | Recording bit rate | Recording bit rate | Recording bit rate | Recording bit rate | Recording bit rate | Opname bit rate | 录音比特率 |
| 165 | 52 |  | Ambiente | Recording scene | Recording scene | Recording scene | Recording scene | Recording scene | Opname scène | 录音场景 |
| 166 | 87 |  | Dividir gravação | Recording segment | Recording segment | Recording segment | Recording segment | Recording segment | Opname segment | 录音分段 |
| 167 | 80 |  | Ativada por voz | Voice-activated recording | Voice-activated recording | Voice-activated recording | Voice-activated recording | Voice-activated recording | Stem geactiveerde opname | 声控录音 |
| 168 | 104 |  | Monitorar gravação | Recording monitor | Recording monitor | Recording monitor | Recording monitor | Recording monitor | Monitoring van de registratie | 录音监听 |
| 169 | 111 |  | Gravação agendada | Timing recording | Timing recording | Timing recording | Timing recording | Timing recording | Getimede opname | 定时录音 |
| 170 | 57 |  | Desligado | Closure | Closure | Closure | Closure | Closure | Sluiten | 关闭 |
| 171 | 54 |  | Entrevista | Interview | Interview | Interview | Interview | Interview | Interview | 采访 |
| 172 | 47 |  | Reunião | Meeting | Meeting | Meeting | Meeting | Meeting | Vergadering | 会议 |
| 173 | 45 |  | Estação | Station | Station | Station | Station | Station | Station | 车站 |
| 174 | 24 |  | Aula | Teaching | Teaching | Teaching | Teaching | Teaching | Onderwijs | 教学 |
| 175 | 52 |  | Gravação | The recording setting | Recording settings | Recording settings | Recording settings | Recording settings | Opnameinstellingen | 录音设置 |
| 176 | 29 |  | Início | start time | Starting time | Starting time | Starting time | Starting time | Starttijd | 开始时间 |
| 177 | 21 |  | Fim | finish time | End Time | End Time | End Time | End Time | Eindtijd | 结束时间 |
| 178 | 56 |  | Repetição | timing cycle | Timing period | Timing period | Timing period | Timing period | Tijdscyclus | 定时周期 |
| 179 | 74 |  | Modo música | music mode | Modo de música | Le mode musique | Modelli musicali | Musik mode | Muziekmodus | 音乐模式 |
| 180 | 85 |  | Modo chamada | phone mode | Modo de teléfono | Mode de téléphone | Tipo di telefono | In telefonform | Oproepmodus | 通话模式 |
| 181 | 90 |  | Ative o Bluetooth | Please turn on bluetooth | Por favor, active bluetooth | Veuillez activer le bluetooth | Per piacere apra il bluetooth | Bitte öffne bluetooth | Schakel Bluetooth in | 请打开蓝牙 |
| 182 | 167 | **CORTA** | Conecte o fone para monitorar | Please plug in headphones for recording monitoring | Grabación escuchar por favor inserte los auriculares | Enregistrement écoutez s’il vous plaît insérer des écouteurs | Per le registrazioni audio si prega di inserire le cuffie | Zur aufzeichnung bitte geben sie den kopfhörer ein | Plaats een oortelefoon voor het opnemen van monitoring | 录音监听请插入耳机 |
| 183 | 106 |  | Chamada recebida | incoming call | Llegó la llamada | Au téléphone | Per informazioni | Da ist der anruf | Inkomende oproep | 来电 |
| 184 | 125 | **CORTA** | Teste de desempenho | benchmark | benchmark | benchmark | benchmark | benchmark | Demoprogramma | 演示程序 |
| 185 | 97 |  | Falha na conexão | Connection failed | La conexión falló | La connexion a échoué | Connessione fallita | Verbindung fehlgeschlagen | Verbinding mislukt | 连接失败 |
| 186 | 80 |  | Apagar pastas | Delete folders | Eliminar una carpeta | Supprimer un dossier | Cancella gli schedari | Ordner löschen | Map verwijderen | 删除文件夹 |
| 187 | 134 | **CORTA** | Nenhuma estação salva | The preset station is empty | La estación preestablecida está vacía | Préréglage station vide | La radio è libera | Alles ist bereit | Vooringestelde zender is leeg | 预设电台为空 |
| 188 | 118 | **CORTA** | Desligar programado | Timed shutdown | Apagado cronometrado | Arrêt programmé | Timed shutdown | Zeitliche Abschaltung | Geplande afsluiting | 定时关机 |
| 189 | 103 |  | Hora para desligar | Set timed shutdown time | Establecer el tiempo de apagado | Définir le temps d'arrêt prévu | Imposta tempo di arresto cronometrato | Setzt die Zeit für das Herunterfahren | Geplande afsluittijd instellen | 设置定时关机时间 |
| 190 | 58 |  | Em ordem | Sequential play | Reproducción secuencial | Lecture séquentielle | Gioco sequenziale | Sequentielles Spiel | Sequentieel afspelen | 顺序播放 |
| 191 | 84 |  | Luz dos botões | Key light | Luz de botón | Lampe à clé | Luce chiave | Licht des Schlüssels | Knopverlichting | 按键灯 |
| 192 | 69 |  | Som externo | External sound | Sonido externo | Bruit extérieur | Suono esterno | Externer Klang | Extern geluid | 外响 |
| 193 | 57 |  | Desligado | OFF | Cerrar | Coupez. | chiuso | geschlossen | Uit | 关 |
| 194 | 38 |  | Ligado | ON | Abrir | Vas - y. | aperto | geöffnet | Aan | 开 |
| 195 | 90 |  | Armazenamento | Storage status | Estado de almacenamiento | État de stockage | Stato di archiviazione | Speicherstatus | Opslagstatus | 存储状态 |
| 196 | 30 |  | Total: | Total capacity: | Capacidad total: | Capacité totale: | Capacità totale: | Gesamtkapazität: | Totale capaciteit： | 总容量： |
| 197 | 29 |  | Livre: | Remaining capacity: | Capacidad restante: | Capacité restante: | Capacità residua: | Restkapazität: | Resterende capaciteit： | 剩余容量： |
| 198 | 80 |  | Senha ao ligar | Power-on password | La contraseña | Code de démarrage | Codice di avviamento | Passwort | Wachtwoord inschakelen | 开机密码 |
| 199 | 72 |  | Mudar senha | Change password | La modificación de la contraseña | Changer votre mot de passe | Modifica della password   | Passwort ändern | Wachtwoord wijzigen | 修改密码 |
| 200 | 87 |  | Senha incorreta | Wrong password | Error de contraseña | Mot de passe incorrect | Errore di password | passwort falsch | Wachtwoord fout | 密码错误 |
| 201 | 84 |  | Gravação salva | Record saved | La grabación ha sido guardada | L’enregistrement a été sauvegardé | Registrazioni registrate | Die aufzeichnung ist gespeichert. | Opname opgeslagen | 录音已保存 |
| 202 | 145 | **CORTA** | O fone é a antena do rádio | The radio needs to be plugged in as an antenna | Radio necesita insertar auriculares como antena | La radio doit être branchée dans le casque comme antenne | La radio deve essere collegata come antenna | Das radio braucht kopfhörer als radio | Radio vereist dat de hoofdtelefoon wordt aangesloten als antenne | 收音机需要插入耳机作为天线 |
| 203 | 258 | **CORTA** | Não desconecte o USB durante a transferência | Do not remove the USB port while transferring files | Transferencia de archivos, no desenchufe el conector USB | Transfert de fichier, ne pas débrancher la prise USB | Si prega di non scollegare la presa USB durante il trasferimento dei file | Der usb-port wird übertragen. Bitte ziehen sie nicht den usb-port aus | Haal de USB-connector niet los tijdens het overbrengen van bestanden | 正在传输文件，请勿拔出USB插口 |
| 204 | 128 | **CORTA** | Página não encontrada | The page cannot be found | No hay búsqueda para esta página | Aucune recherche pour cette page | Nessuna pagina trovata | Schau dir die seite aus | Geen dergelijke pagina gevonden | 查无此页 |
| 205 | 69 |  | Senha atual: | Original password: | Contraseña Original: | Mot de passe Original: | Password originale: | Originalpasswort: | Origineel wachtwoord： | 原密码： |
| 206 | 69 |  | Nova senha: | New password: | Nueva contraseña: | Nouveau mot de passe: | Nuova password: | Neues Passwort: | Nieuw wachtwoord： | 新密码： |
| 207 | 116 | **CORTA** | Repita a nova senha: | Please enter the new password again: | Introduzca una nueva contraseña de nuevo: | Veuillez saisir à nouveau le nouveau mot de passe: | Inserisci nuovamente la nuova password: | Bitte geben Sie das neue Passwort erneut ein: | Voer het nieuwe wachtwoord opnieuw in： | 请再次输入新密码： |
| 208 | 88 |  | Entrada inválida | Input error! | ¡Error de entrada! | Erreur d'entrée! | Errore di input! | Eingabefehler! | Invoerfout! | 输入错误! |
| 209 | 83 |  | Digite a senha: | Please enter the password: | Introduzca la contraseña: | Veuillez saisir votre mot de passe: | Inserisci la password: | Bitte geben Sie das Passwort ein: | Voer een wachtwoord in： | 请输入密码： |
| 210 | 110 |  | Erro ao abrir o vídeo | Error playing video | Reproducir video error | Erreur de lecture vidéo | Errori di videoscrittura | Fehler beim videospiel | Fout bij afspelen video | 视频播放错误 |
| 211 | 107 |  | Formatar cartão SD | Formatting an SD Card | Formato tarjeta sd | Formater la carte sd | Formattazione delle carte sd | Die formalisierung der sd | Formatteren van de sd-kaart | 格式化sd卡 |
| 212 | 56 |  | Concluído | Formatting completed | Formateado completo | Le formatage est terminé | Formattazione completa | Formatieren sie es. | Formatteren voltooid | 格式化完成 |
| 213 | 269 | **CORTA** | Formatando. Não remova o cartão nem desligue. | The SD card is being formatted, Do not remove or power off the card | Formatear la tarjeta sd, no desenchufe ni apague la tarjeta | Formater la carte sd, ne pas débrancher ou éteindre | In corso di formattazione delle schede sd | Das schreibt eine sd card. Bleiben sie in der leitung und schalten sie die karte nicht aus | Het formatteren van de sd-kaart, niet loskoppelen of afsluiten | 正在格式化sd卡,请勿拔卡或关机 |
| 214 | 174 | **CORTA** | Falha ao formatar. Tente no PC. | Formatting fails. Try it on the PC | Formateo falló por favor vaya al lado de la pc e intente | Le formatage a échoué s’il vous plaît aller sur le côté pc pour essayer | La formattazione non è riuscita | Fehler bei der formatierung: versuchen sie es am pc | Het formatteren mislukt, probeer het aan de pc | 格式化失败请到pc端尝试 |
| 215 | 97 |  | Erro no cartão SD | SD card error | SD card error | Erreur de carte SD | SD card error | SD card error | SD card error | 存储卡可能存在问题, 请在电脑端尝试修复 |
