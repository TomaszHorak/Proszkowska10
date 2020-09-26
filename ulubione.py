import os
import logging
import THutils
import constants
import shutil
import playlista
import time
import glob
from random import getrandbits


class PozycjaUubionego(playlista.Playlista):
    def __init__(self, nazwa, pozycje, plik):
        super(PozycjaUubionego, self).__init__(nazwa=nazwa, pozycje=pozycje)
        # self._nr = numer
        self._nr = getrandbits(32)
        self._plik = plik
        return

    def pozycja_do_listy(self, pelna=False):
        pozycja = {constants.NR: self._nr,
                   'plik': self._plik,
                   constants.POZYCJE: self.wyslij_playliste(pelna=pelna)}
        return pozycja

    def get_numer(self):
        return self._nr

    def get_plik(self):
        return self._plik

    def get_nazwa(self):
        return super(PozycjaUubionego, self).get_nazwa()


class Ulubione:
    def __init__(self):
        self.logger = logging.getLogger(constants.NAZWA_LOGGERA)
        self.ulubione = []
        self.odswiez_ulubione()
        return

    def zapisz_playliste_w_ulubionych(self, playl, nazwa_pliku):
        # TODO tutaj do poprawienia zrobic deepcopy
        '''pl=playlista.Playlista(nazwa=nazwa_pliku,
                                 pozycje=playl.pozycje,
                                 jak_odtwarza=playl.jak_odtwarza)'''
        # tworzenie kopii playlisty bo gdyby sie aktualna zmieniala to nie zdazy zapisac a tak bieze jej snapshot
        #pl = deepcopy(playl)
        playl.zapisz_playliste_w_ulubionych(nazwa_pliku)
        self.odswiez_ulubione()

    def ulubiony_po_numerze(self, nr_ulubionego):
        for a in self.ulubione:
            if a.get_numer() == long(nr_ulubionego):
                return a
        return None

    def usun_ulubione(self, nrulubionego):
        ul = self.ulubiony_po_numerze(nrulubionego)
        if ul is None:
            self.logger.warning('Prosba o usuniecie ulubionego, ktory nie istnieje: ' + str(nrulubionego))
            return
        link = ul.get_plik()
        try:
            os.remove(link)
        except OSError:
            self.logger.warning('Nie udalo sie usunac ulubionego: ' + str(link))
            return
        katalog = link + playlista.SUFFIX_ULUBIONYCH_PLIKI
        if os.path.isdir(katalog):
            try:
                shutil.rmtree(katalog)
            except OSError:
                self.logger.warning('Nie udalo sie usunac katalogu ulubionego: ' + katalog)
        self.logger.info('Usunalem ulubione: ' + str(nrulubionego))
        self.odswiez_ulubione()
        return

    def wyslij_ulubione(self, pelna=False):
        pozy = []
        for p in self.ulubione:
            pozy.append(p.pozycja_do_listy(pelna=pelna))
        dane = {constants.TS: self.ts,
               constants.POZYCJE: pozy}
        return THutils.skonstruuj_odpowiedzV2(constants.RODZAJ_KOMUNIKATU_ULUBIONE, dane, constants.STATUS_OK)

    def arduino_wyslij_ulubione(self):
        dane = ''
        for a in self.ulubione:
            dane += a.get_nazwa()
            dane += "|"
        return dane

    def odswiez_ulubione(self):
        katalog_ulubionych = constants.KATALOG_ULUBIONYCH
        #str(THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_NAGL, 'KATALOG_ULUBIONYCH', self.logger))
        if katalog_ulubionych == '':
            return
        self.ulubione = []
        #numer = 0
        self.logger.info('Rozpoczynam pobieranie ulubionych z katalogu: ' + katalog_ulubionych)
        #filenames = os.listdir(katalog_ulubionych)
        filenames = glob.glob(katalog_ulubionych + '/*')
        filenames.sort(key=os.path.getmtime)
        #print("\n".join(files))
        for f in filenames:
            #p = katalog_ulubionych + '/' + f
            if os.path.isdir(f):
                continue
            pl = playlista.Playlista(plik=str(f))
            #numer = numer + 1
            # pl.inicjalizuj_playliste_z_pliku(nazwa_pliku=str(p))
            if len(pl.pozycje) > 0:
                #fanart = pl.pozycje[0].fanart
                #typ = pl.pozycje[0].typ
                self.ulubione.append(PozycjaUubionego(pl.nazwa, pl.pozycje, f))
        self.ts = int(time.time())
        self.logger.info('Pobralem ulubione. Liczba ulubionych: ' + str(len(self.ulubione)))
