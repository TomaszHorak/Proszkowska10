# klasa obslugi KODI, cyklicznie odczytuje stan odtwarzacza, zwraca tytul, czasy itd
from playlista import Playlista
import requests
import json
from constants import OBSZAR_NAGL
from CurrentStatus import CurrentStatus
from CurrentPlaylist import CurrentPlaylist

CZAS_INICJALIZOWANIA_KODI = 300
ADRES_KODI = 'http://127.0.0.1:8080/jsonrpc'

class Kodi():
    def __init__(self, currentStatus:CurrentStatus, currentPlaylist: CurrentPlaylist, logger=None):
        self.logger = logger
        self.currentStatus = currentStatus
        self.currentPlaylist = currentPlaylist
        self.__ask_kodi("Application.SetVolume", {"volume": 100})

    def next(self):
        pass

    def previous(self):
        pass

    def seek(self, position: int):
        pass

    def aktualizuj_stan(self):
        self.currentPlaylist.clear()
        self.currentPlaylist.items.append(self.currentStatus.item)
        if self.currentPlaylist.name != self.currentStatus.item.name:
            self.currentPlaylist.resetTS()
        self.currentPlaylist.name = self.currentStatus.item.name

        player = self.__get_aktywny_player_kodi()
        if player is None:
            self.currentStatus.aktualnie_gra = False
            self.currentStatus.item.title = ''
            return

        par = {"playerid": player,
               "properties": ['file', 'album']}
        player_item = self.__ask_kodi("Player.GetItem", par)
        par = {"playerid": player,
               "properties": ['speed', 'time', 'percentage', 'position', 'totaltime']}
        player_properties = self.__ask_kodi("Player.GetProperties", par)

        #self.currentStatus.aktualnie_gra = False
        if player_properties:
            if int(player_properties['speed']) == 1:
                if not self.currentStatus.aktualnie_gra:
                    self.currentStatus.aktualnie_gra = True
                    self.currentStatus.resetujTS()
        if player_item:
            tyt = player_item['item']['label']
            if tyt is None:
                self.currentStatus.item.title = ''
            else:
                self.currentStatus.item.title = str(tyt)
        else:
            self.currentStatus.item.title = ''

    def resume(self):
        self.odtwarzaj_z_linku(self.currentStatus.item.link)

    def odtwarzaj_z_linku(self, link):
        if link == '':
            if self.logger:
                self.logger.warning(OBSZAR_NAGL, 'kodi', 'Blad z funkcji odtwarzaj_z_linku: link pusty')
            return
        par = {"item": {"file": link}}
        wynik = self.__ask_kodi("Player.Open", par)
        return wynik

    def stop(self):
        player = self.__get_aktywny_player_kodi()
        if player is None:
            return
        par = {"playerid": player}
        self.__ask_kodi("Player.Stop", par)

    def idz_do(self, czas):
        player = self.__get_aktywny_player_kodi()
        if player is None:
            return
        par = {"playerid": player,
               "value": int(czas)}
        self.__ask_kodi("Player.Seek", par)

    '''def play_pause(self, start=False):
        player = self.__get_aktywny_player_kodi()
        if player is None:
            return
        par = {"playerid": player}
        self.__ask_kodi("Player.PlayPause", par)'''


    def __ask_kodi(self, method, params):
        zapytanie = {"jsonrpc": "2.0",
                     "method": method,
                     "params": params,
                     "id": method}
        odp = ''
        try:
            odp = requests.post(ADRES_KODI + '?request=', data=json.dumps(zapytanie)).text
        except Exception as serr:
            if self.logger:
                self.logger.warning(OBSZAR_NAGL, 'kodi', 'Blad wysylania post do KODI, zapyt:' + str(method) + str(params) + ')' + str(serr))
            return None
        try:
            nag = json.loads(str(odp))
            if nag['id'] != method:
                if self.logger:
                    self.logger.warning(OBSZAR_NAGL, 'kodi', 'Odpowiedz KODI na nie to pytanie (zapyt:' + str(method)
                                        + str(params) + '). Odpowiedz: ' + str(nag['id']))
                return None
        except ValueError as serr:
            self.logger.warning(OBSZAR_NAGL, 'kodi', 'Bledna odp KODI konw JSON(zapyt:'+ str(method) + str(params) + ')' + str(serr))
            return None
        wynik = ''
        try:
            wynik = nag['result']
        except KeyError as serr:
            if self.logger:
                self.logger.warning(OBSZAR_NAGL, 'kodi', 'Bledna odpowiedz KODI (zapyt:'+ str(method) + str(params) + ')' + str(serr))
                self.logger.warning(OBSZAR_NAGL, 'kodi', 'Wynik bledu:' + str(nag))
        return wynik

    def __get_aktywny_player_kodi(self):
        #TODO kodi bedzie gralo tylko audio, wiec player zawsze 1???
        par = {}
        akt_player = self.__ask_kodi("Player.GetActivePlayers", par)
        if akt_player is not None:
            if len(akt_player) > 0:
                return akt_player[0]['playerid']
        #self.logger.warning(OBSZAR_NAGL, 'kodi', 'Brak info o aktywnym playerze Kodi.')
        return None

    '''def __inicjalizuj_kodi(self):
        # regularne inicjalizowanie glosnosci KODI
        self.__ask_kodi("Application.SetVolume", {"volume": 100})
        threading.Timer(CZAS_INICJALIZOWANIA_KODI, self.__inicjalizuj_kodi).start()'''

