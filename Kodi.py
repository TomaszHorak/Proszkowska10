# klasa obslugi KODI, cyklicznie odczytuje stan odtwarzacza, zwraca tytul, czasy itd
import jsonrpclib
import threading
import THutils
import requests
import json
import odtwarzacz
from constants import OBSZAR_NAGL

CZAS_INICJALIZOWANIA_KODI = 300


class Kodi(odtwarzacz.Odtwarzacz):
    def __init__(self, logger, adres):
        odtwarzacz.Odtwarzacz.__init__(self)
        self.logger = logger
        self.adres_kodi = adres
        self.__inicjalizuj_kodi()
        return

    def aktualizuj_stan(self):
        odtwarzacz.Odtwarzacz.aktualizuj_stan(self)
        player = self.__get_aktywny_player_kodi()
        if player is not None:
            par = {"playerid": player,
                   "properties": ['file', 'album']}
            player_item = self.__ask_kodi("Player.GetItem", par)
            par = {"playerid": player,
                   "properties": ['speed', 'time', 'percentage', 'position', 'totaltime']}
            player_properties = self.__ask_kodi("Player.GetProperties", par)
        else:
            player_item = player_properties = None

        self.aktualnie_gra = False
        if player_properties:
            if int(player_properties['speed']) == 1:
                self.aktualnie_gra = True
        if player_item:
            self.tytul = THutils.xstr(player_item['item']['label'])
        else:
            self.tytul = ''

        if player_properties is not None:
            proc = 0
            try:
                self.totaltime = int((player_properties['totaltime']['hours'] * 60 * 60) +
                                     (player_properties['totaltime']['minutes'] * 60) +
                                     player_properties['totaltime']['seconds'])
                self.currenttime = int((player_properties['time']['hours'] * 60 * 60) +
                                       (player_properties['time']['minutes'] * 60) +
                                       player_properties['time']['seconds'])
                proc = int(player_properties['percentage'])
            except TypeError as serr:
                self.logger.warning(OBSZAR_NAGL, 'kodi', 'Blad odczytu player_properties KODI: ' + str(serr))
            if proc > 100:
                proc = 100
            self.percentage = proc
        else:
            self.totaltime = 0
            self.currenttime = 0
            self.percentage = 0
        return

    def odtwarzaj_z_linku(self, link):
        odtwarzacz.Odtwarzacz.odtwarzaj_z_linku(self, link)
        if link == '':
            self.logger.warning(OBSZAR_NAGL, 'kodi', 'Blad z funkcji odtwarzaj_z_linku: link pusty')
            return
        par = {"item": {"file": link}}
        self.__ask_kodi("Player.Open", par)

    def stop(self):
        odtwarzacz.Odtwarzacz.stop(self)
        player = self.__get_aktywny_player_kodi()
        if player is None:
            return
        par = {"playerid": player}
        self.__ask_kodi("Player.Stop", par)

    def idz_do(self, czas):
        odtwarzacz.Odtwarzacz.idz_do(self, czas)
        player = self.__get_aktywny_player_kodi()
        if player is None:
            return
        par = {"playerid": player,
               "value": int(czas)}
        self.__ask_kodi("Player.Seek", par)

    def play_pause(self, start=False):
        odtwarzacz.Odtwarzacz.play_pause(self)
        player = self.__get_aktywny_player_kodi()
        if player is None:
            return
        par = {"playerid": player}
        # TODO teraz stop, ale do przerobienia na pauze jak ogarne czemu Leia nieakceptuje pauzy
        self.__ask_kodi("Player.PlayPause", par)

    def __ask_kodi(self, method, params):
        zapytanie = {"jsonrpc": "2.0",
                     "method": method,
                     "params": params,
                     "id": method}
        odp = ''
        try:
            odp = requests.post(self.adres_kodi + '?request=', data=json.dumps(zapytanie)).text
        except Exception as serr:
            self.logger.warning(OBSZAR_NAGL, 'kodi', 'Blad wysylania post do KODI, zapyt:' + str(method) + str(params) + ')' + str(serr))
            return None
        try:
            nag = json.loads(str(odp))
            if nag['id'] != method:
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
            self.logger.warning(OBSZAR_NAGL, 'kodi', 'Bledna odpowiedz KODI (zapyt:'+ str(method) + str(params) + ')' + str(serr))
            self.logger.warning(OBSZAR_NAGL, 'kodi', 'Wynik bledu:' + str(nag))
        return wynik

    def __get_aktywny_player_kodi(self):
        par = {}
        akt_player = self.__ask_kodi("Player.GetActivePlayers", par)
        if akt_player is not None:
            if len(akt_player) > 0:
                return akt_player[0]['playerid']
        # self.logger.warning('Brak info o aktywnym playerze Kodi.')
        return None

    def __inicjalizuj_kodi(self):
        par = {"volume": 100}
        self.__ask_kodi("Application.SetVolume", par)
        threading.Timer(CZAS_INICJALIZOWANIA_KODI, self.__inicjalizuj_kodi).start()

"""    def __player_get_properties_kodi(self):
        player = self.__get_aktywny_player_kodi()
        if player is None:
            return None
        par = {"playerid": player,
               "properties": ['speed', 'time', 'percentage', 'position', 'totaltime']}
        return self.__ask_kodi("Player.GetProperties", par)

    def __player_get_item_kodi(self):
        player = self.__get_aktywny_player_kodi()
        if player is None:
            return None
        par = {"playerid": player,
               "properties": ['file', 'album']}
        return self.__ask_kodi("Player.GetItem", par)"""
