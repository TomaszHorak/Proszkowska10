import constants
from THutils import getCurrentTimeStamp
from item import Item
import json

''' Dokumentacja API

every command structure:
'komenda' - command -> constants.KOMENDA 
'parametry' - additional parameters


            elif params[constants.KOMENDA] == 'NAST':
                self.nastepny()
            elif params[constants.KOMENDA] == 'POPR':
                self.poprzedni()
            elif params[constants.KOMENDA] == 'GOTO':


NASTEPNY UTWOR: 'NAST'
odtworz nastepny utwor na playliscie

POPRZEDNI UTWOR: 'POPR'
odtworz poprzedni utwor na playliscie

IDZ DO POZYCJI: 'GOTO'
Idzie do pozycji (procentowo) w obecnie granym utworze
constants.WARTOSC = procentowo podana wartosc gdzie ma ustawic odtwarzacz

ODTWORZ_POZYCJE_Z_PLAYLISTY: 'PLAY'
Odtwarzam z playlisty pozycje nr:
constants.POLE_WARTOSC: numer pozycji na playliscie, zaczyna sie od zera

'''
class CurrentStatus:
    def __init__(self, logger=None):
        self.logger = logger
        self.item = self.__readCurrentItemFromFile()
        self.aktualnie_gra = False
        self.totaltime = 0  #w sekundach
        self.currenttime = 0 #w sekundach
        self.interkom = False
        self.ts_playlisty = 0
        self.ts_ulubionych = 0
        self.ts_wzmacniaczy = 0
        self.ts_radii = 0
        self.ts_historii = 0
        self.ts = 0
        self.interkom = False
        self.percentage = 0
        self.statusWzmacniacze = {}

    def setCurrentItem(self, item:Item):
        self.item = item
        self.__saveCurrentItem()

    def __readCurrentItemFromFile(self) -> Item:
        item = None
        try:
            poz = json.load(open(constants.PLIK_BIEZACY_ITEM, 'r'))
            item = Item(**poz)
        except Exception as serr:
            if self.logger is not None:
                self.logger.warning(constants.OBSZAR_NAGL, 'ulubione', 'Blad odczytu pliku z biezacym itemem, blad JSON: ' + str(serr))
        if item is None:
            item = Item()
        return item

    def __saveCurrentItem(self):
        plik = open(constants.PLIK_BIEZACY_ITEM, 'w')
        plik.write(json.dumps(self.item.__dict__))
        plik.close()

    def resetujTS(self):
        self.ts = getCurrentTimeStamp()

    def getCurrentStatus(self):
        return {
            constants.POLE_INTERKOM: self.interkom,
            constants.POLE_CZY_AKTUALNIE_GRA: self.aktualnie_gra,
            constants.POLE_TIMESTAMP_PLAYLISTY: self.ts_playlisty,
            constants.POLE_TIMESTAMP_ULUBIONYCH: self.ts_ulubionych,
            constants.POLE_TIMESTAMP_RADII: self.ts_radii,
            constants.POLE_TIMESTAMP_HISTORII: self.ts_historii,
            constants.POLE_TIMESTAMP_NAGLOSNIENIA: self.ts,
            constants.POLE_TOTALTIME: self.totaltime,
            constants.POLE_CURRENTTIME: self.currenttime,
            constants.POLE_PERCENTAGE: self.percentage,
            #constants.PLAYLIST_ITEMS_COUNT: self.liczba_pozycji_playlisty,
            constants.ITEM: self.item.__dict__,
            'wzmacniacze': self.statusWzmacniacze}
    #TODO powyzsza aktualna pozycja do usuniecia, jest tylko tymczosowo dopoki nie przejdziemy na nowe api zupelnie
