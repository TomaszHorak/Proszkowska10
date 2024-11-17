from MojLogger import MojLogger
from THutils import getCurrentTimeStamp
import constants
import json
from item import Item


class Favourites:
    def __init__(self, obszar, logger, baseFolder):
        self.logger = logger  # type: MojLogger
        self.obszar = obszar
        self.__baseFolder = baseFolder
        self.items = []
        self.__readFavouritesFromFile()
        self.resetTS()

    def resetTS(self):
        self.ts = getCurrentTimeStamp()

    def getUlubioneList(self) -> [Item]:
        return self.items

    def zapisz_playliste_w_ulubionych(self, playl, nazwa_pliku):
        playl.zapisz_playliste_w_ulubionych(nazwa_pliku)
        self.__readFavouritesFromFile()

    def ulubiony_po_numerze(self, nr_ulubionego):
        if nr_ulubionego is None:
            return None
        for a in self.items:
            if a.nr == int(nr_ulubionego):
                return a
        return None

    def ulubiony_po_nazwie(self, name):
        if name is None:
            return None
        for a in self.items:
            if a.name == name:
                return a
        return None

    def usun_ulubione(self, nrulubionego):
        ul = self.ulubiony_po_numerze(nrulubionego)
        if ul is None:
            self.logger.warning(self.obszar, 'ulubione',
                                'Prosba o usuniecie ulubionego, ktory nie istnieje: ' + str(nrulubionego))
            return
        self.items.remove(ul)
        self.resetTS()

    def __saveFavourites(self):
        plik = open(constants.PLIK_ULUBIONYCH, 'w')
        plik.write(json.dumps(self.__favouritesToDict()))
        plik.close()

    def __favouritesToDict(self):
        pozy = []
        for p in self.items:
            pozy.append(p.__dict__)
        return pozy

    def wyslij_ulubione(self):
        dane = {constants.POLE_TS: self.ts,
                constants.POZYCJE: self.__favouritesToDict()}
        return dane

    def __readFavouritesFromFile(self):
        ulub = []
        try:
            poz = json.load(open(constants.PLIK_ULUBIONYCH, 'r'))
            for p in poz:
                ul = Item(**p)
                ulub.append(ul)
        except Exception as serr:
            self.logger.warning(self.obszar, 'ulubione', 'Blad odczytu pliku z ulubionymi, blad JSON: ' + str(serr))
            return None
        self.items = ulub
        self.resetTS()
