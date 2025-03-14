#ogolne
PROTOCOL_VERSION = "HTTP/1.1"
NAZWA_LOGGERA = 'proszkowska'
NAZWA_LOGGERA_TEMPERATUR = 'temperatury_log'
KATALOG_GLOWNY = 'KATALOG_GLOWNY'
KATALOG_ULUBIONYCH = '/home/pi/python/system_podlewania/Ulubione'
PORT_SERWERA_GARAZ_v1 = 8089
PORT_SERWERA_NAGLOSNIENIE_v1 = 8090
PORT_SERWERA_V2 = 'PORT_SERWERA_V2'
IP_GARAZ = 'IP_GARAZ'
IP_STRYCH = 'IP_STRYCH'
IP_SAUNA = 'IP_SAUNA'
PWD_BAZY = 'PWD_BAZY'
LOGUJ_FIREBASE = 'loguj_firebase'
# HOST_I_PORT_STRYCH_v1 = 'http://' + IP_STRYCH + ':' + str(PORT_SERWERA_NAGLOSNIENIE_v1) + '/?'
# HOST_I_PORT_STRYCH_v2 = 'http://' + IP_STRYCH + ':' + str(PORT_SERWERA_V2)
# HOST_I_PORT_GARAZ_v1 = 'http://' + IP_GARAZ + ':' + str(PORT_SERWERA_GARAZ_v1) + '/?'

def get_HOST_I_PORT_STRYCH_v2():
    from os import getenv
    return 'http://' + getenv(IP_STRYCH)

def get_HOST_I_PORT_GARAZ_v2():
    from os import getenv
    return 'http://' + getenv(IP_GARAZ) + ':' + getenv(PORT_SERWERA_V2)

def get_HOST_I_PORT_SAUNA():
    from os import getenv
    return 'http://' + getenv(IP_SAUNA)


PLIK_RESETU = '/resetuj.sh'

KOMENDA = 'komenda'
APIKEY = 'apikey'
OBSZAR = 'obszar'

OBSZAR_P10 = 'p10'
OBSZAR_TEMP = 'temp'
OBSZAR_STER = 'ster'
OBSZAR_NAGL = 'nagl'
OBSZAR_OSWI = 'oswi'
OBSZAR_STAT = 'stat'
OBSZAR_PODL = 'podl'
OBSZAR_OGRZ = 'ogrz'
OBSZAR_SZAK = 'szak'    #szybkie akcje
OBSZAR_SAUNA = 'sauna'
OBSZAR_PETLA = 'petla'  #techniczny obszar do logowania zdarzen petli
OBSZAR_KONFIGURACJI_CYKLE = 'cykle'

RODZAJ_KOMUNIKATU = 'rodzaj_komunikatu'
RODZAJ_KOMUNIKATU_STATUS_SKROCONY = 'status_skrocony'
RODZAJ_KOMUNIKATU_BLAD = 'blad'
RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA = 'stan_naglosnienia'
RODZAJ_KOMUNIKATU_STAN_WZMACNIACZE = 'stan_wzmacniacze'
RODZAJ_KOMUNIKATU_STAN_PODLEWANIA = 'stan_podlewania'
RODZAJ_KOMUNIKATU_STAN_OSWIETLENIA = 'stan_oswietlenia'
RODZAJ_KOMUNIKATU_STAN_SZYBKIE_AKCJE = 'stan_szybkie_akcje'
RODZAJ_KOMUNIKATU_STAN_STEROWANIA = 'stan_sterowania'
RODZAJ_KOMUNIKATU_STAN_TEMPERATURY = 'stan_temperatury'
RODZAJ_KOMUNIKATU_STAN_OGRZEWANIA = 'stan_ogrzewania'
RODZAJ_KOMUNIKATU_STAN_SAUNY = 'stan_sauny'
RODZAJ_KOMUNIKATU_STAN_LOG_GARAZ = 'log'
RODZAJ_KOMUNIKATU_STAN_LOG_NAGLOSNIENIE = 'log_nagl'
RODZAJ_KOMUNIKATU_STAN_LOG_TEMPERATURY = 'log_temp'
RODZAJ_KOMUNIKATU_ULUBIONE = 'ulubione'
RODZAJ_KOMUNIKATU_PLAYLISTA = 'playlista'
RODZAJ_KOMUNIKATU_KATALOG_RADII = 'katalog_radii'
RODZAJ_KOMUNIKATU_HISTORIA = 'historia'
RODZAJ_KOMUNIKATU_SPOTIFY_QUERY = 'spotify_query'
RODZAJ_KOMUNIKATU_SPOTIFY_NEXT = 'spotify_next'
RODZAJ_KOMUNIKATU_SPOTIFY_ROZWIN = 'spotify_rozwin'
RODZAJ_KOMUNIKATU_LIRYKI = 'liryki'

KOMENDA_WYSYLANIE_FIREBASE = 'wysylanie_firebase'

#pola ogrzewania
POLE_POMIESZCZENIA = 'pomieszczenia'
POLE_TEMP_MIN ='temp_min'
POLE_TEMP_MAX = 'temp_max'
POLE_TEMP_ZADANA = 'temp_zadana'
POLE_TEMP_AKTUALNA = 'temp_aktualna'
POLE_TS_AKTUALNEJ = 'ts_aktual'
POLE_TEMP_GRZEJE = 'grzeje'
POLE_WAKACJE = 'wakacje'
POLE_WAKACJE_OD_CZASU = 'wakacje_od'
POLE_WAKACJE_DO_CZASU = 'wakacje_do'
POLE_WAKACJE_ZAPLANOWANE = 'wakacje_plan'
POLE_OD_CZASU = 'od_czasu'
POLE_DO_CZASU = 'do_czasu'
POLE_BLAD_CZUJNIKA = 'blad_czujnika'

#pola sauny
KOMENDA_SAUNA_ZADAJ_TEMP = 'zadaj_temperature'
KOMENDA_SAUNA_WLACZ_SWIATLO = 'wlacz_swiatlo'
POLE_WLACZONA = 'wlaczona'
POLE_GRZEJE = 'grzeje'
POLE_SWIATLO_WEW = 'swiatlo_wew'
POLE_SWIATLO_ZEW = 'swiatlo_zew'
POLE_SWIATLO_SCIEZKA = 'swiatlo_sciezka'
PETLA_ODCZYTAJ_STATUS_SAUNY = 'odczytaj_status_sauny'
POLE_TS_KONCA = 'ts_konca'


# pola timestampy
POLE_TIMESTAMP_RADII = 'ts_radii'
POLE_TIMESTAMP_PLAYLISTY = 'ts_playlisty'
POLE_TIMESTAMP_ULUBIONYCH = 'ts_ulubionych'
POLE_TIMESTAMP_WZMACNIACZY = 'ts_wzmacniaczy'
POLE_TIMESTAMP_PODLEWANIA = 'ts_podlewania'
POLE_TIMESTAMP_SZAKCJI = 'ts_szak'
POLE_TIMESTAMP_STEROWANIA = 'ts_sterowania'
POLE_TIMESTAMP_HISTORII = 'ts_historii'
POLE_TIMESTAMP_NAGLOSNIENIA = 'ts_naglosnienia'
POLE_TIMESTAMP_OSWIETLENIA = 'ts_oswietlenia'
POLE_TIMESTAMP_TEMPERATURY = 'ts_temperatura'
POLE_TIMESTAMP_OGRZEWANIA = 'ts_ogrzewania'
POLE_TIMESTAMP_SAUNY = 'ts_sauny'


#STAT
KOMENDA_STAT_RESET_GARAZ = 'RESET_GARAZ'
KOMENDA_STAT_RESET_STRYCH = 'RESET_STRYCH'
KOMENDA_AKTUALIZUJ_CYKL = 'AKTUAL_CYKL'
KOMENDA_DODAJ_CYKL = 'DODAJ_CYKL'
KOMENDA_USUN_CYKL = 'USUN_CYKL'

KOMENDA_ODSWIEZ_SZYBKIE_AKCJE = 'ODSZAK'

RESULT = 'result'
STATUS = 'status'
STATUS_OK = 'OK'
STATUS_NOK = 'NOK'

POLE_STAN = 'stan'  #ma miec wartosc typu boolean

POLE_LICZBA_LINII = 'liczba_linii'

POLE_WARTOSC = 'wartosc'    #TODO wszystkie pola wartosciowe powinny miec to ID lub przejsc na NUMER
#PARAMETR_ZERO = '0'
#PARAMETR_JEDEN = '1'
#PARAMETR_WLACZ = 'WLACZ'
#PARAMETR_WYLACZ = 'WYLACZ'
CYKL = 'cykl'

ODBIORNIKI = 'Odbiorniki'
CYKLE = 'Cykle'
TS = 'ts'
NR = 'nr'
NAZWA = 'nazwa'

#FIREBASE
FIREBASE_DANE = 'dane'

#odbiornik-przekaznik
PRZEKAZNIK_IMPULS = 'IMPULS'
PRZEKAZNIK_PIN = 'PIN'
#PRZEKAZNIK_CZAS_IMPULSU = 'CZAS_IMPULSU'
PRZEKAZNIK_DEF_CZAS_ZAL = 'DEF_CZAS_ZAL'

#================ podlewanie ======================
PODLEWANIE_AKTYWNE = 'podlewanie_aktywne'

#================ petla czasowa =====================
#TODO pole nazwa juz istnieje wczesniej
PETLA_NAZWA = 'NAZWA'
PETLA_MIESIACE = 'MIESIACE'
PETLA_DNI = 'DNI'
PETLA_TYP = 'TYP'
PETLA_AKTYWNE = 'AKTYWNE'
KIEDY_KONIEC_DZIALANIA = 'KIEDY_KONIEC'
#TODO zmienic czas_do_konca na kiedy koniec
PETLA_GODZ_WL = 'GODZ_WL'
PETLA_MINU_WL = 'MINU_WL'
PETLA_SEK_WL = 'SEK_WL'
PETLA_GODZ_WYL = 'GODZ_WYL'
PETLA_MINU_WYL = 'MINU_WYL'
PETLA_SEK_WYL = 'SEK_WYL'
PETLA_WARTOSC = 'WART'
PETLA_TS_START = 'TS_START'
PETLA_TS_STOP = 'TS_STOP'
PETLA_CZAS_INTERWALU = 'CZAS_INTERW'
PETLA_CZAS_MIEDZY_INTERWALAMI = 'CZAS_MIEDZY_INTERW'
AKTYWACJA_SCHEMATU = 'AS'
TOGGLE_ODBIORNIK_NAZWA = 'TN'
ODBIORNIK_NA_CZAS = 'ODB_CZAS'

#KOMENDA_ODCZYTAJ_CYKLE_Z_KONFIGURACJI = 'OC'
POZYCJE = 'pozycje'
HASH = 'hash'
POZYCJA = 'Pozycja'
CZAS = 'czas'
DATA = 'data'

POLE_OPIS_BLEDU = "opis_bledu"
POLE_WZMACNIACZE = "Wzmacniacze"
POLE_INTERKOM = "Interkom"
POLE_CZY_AKTUALNIE_GRA = "Czy_aktualnie_gra"
POLE_PAUZA = "Pauza"
# POLE_NAZWA_PLAYLISTY = "Nazwa_playlisty"
POLE_NR_POZ_NA_PLAYL = "Nr_pozycji_na_playliscie"
#POLE_LICZBA_POZ_PLAYL = "Liczba_pozycji_playlisty"

#====== naglosnienie ==========================
POLE_AKTUALNA_POZYCJA = "Aktualna_pozycja"
POLE_TYTUL = "Tytul"
POLE_CZY_GRA_DENON = "Czy_gra_denon"
POLE_TOTALTIME = "Totaltime"
POLE_CURRENTTIME = "Currenttime"
POLE_PERCENTAGE = "Percentage"
POLE_GLOSNOSC = "Glosnosc"
POLE_NR_WEJSCIA = "Nr_wejscia"
POLE_ID_STACJI = 'id_stacji'
POLE_NAZWA_SERVICU_RADIOWEGO = 'nazwa_servicu'

KOMENDA_GLOSNOSC_DELTA = 'gl_delta'
KOMENDA_GLOSNOSC = 'gl'
KOMENDA_TOGGLE_WZMACNIACZ = 'WZ_TOGGLE'

#============== OGRZEWANIE ======================
MAX_TEMP_POMIESZCZENIA = 'max_temp_pomieszczenia'
MIN_TEMP_POMIESZCZENIA = 'min_temp_pomieszczenia'
HISTEREZA = 'histereza'
CZAS_DO_ALARMU = 'czas_do_alarmu'
OGRZEWANIE_AKTYWNE = 'ogrzewanie_aktywne'
KOMENDA_AKTYWUJ_OGRZEWANIE = 'aktywuj_ogrzewanie'
KOMENDA_ZADAJ_TEMP = 'zadaj_temp'
KOMENDA_PODAJ_TEMP = 'podaj_temp'   #temperatura odczytana przez NodeMCU i przeslana do Raspberry
KOMENDA_WAKACJE = 'wakacje'
KOMENDA_STATUS_POMIESZCZENIA = 'status_pomieszczenia'
#============== SPOTIFY ====================
USER_PLAYLIST = 'user_playlist'
TRACK = 'track'
TRACKS = 'tracks'
PLAYLIST = 'playlist'
ALBUM_TRACKS = 'album_tracks'
ALBUM = 'album'
TITLE= 'title'
LINK = 'link'
ALBUMS = 'albums'
FANART = 'fanart'
ARTIST = 'artist'
ARTISTS = 'artists'
ARTIST_ALBUMS = 'artist_albums'
COUNTRY = 'PL'
ITEMS = 'items'
ROZWINIECIE = 'rozwiniecie'
NEXT = 'next'
KOLEJNE = 'kolejne'
DEVICES = 'devices'
NAME = 'name'
ID = 'id'
URI = 'uri'
QUERY = 'query'
SPOTIFY_RODZAJ = 'rodzaj'

#sterowanie
KOMENDA_DZWONEK = 'dzwonek'