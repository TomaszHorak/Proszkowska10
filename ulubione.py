import os
import logging
import THutils
import playlista
import shutil


class PozycjaUubionego:
    def __init__(self, numer, nazwa, plik, typ, fanart, czas, liczbapozycji):
        self._nr = numer
        self._nazwa = nazwa
        self._plik = plik
        self._typ = typ
        self._fanart = fanart
        self._czas = czas
        self._liczba_pozycji = liczbapozycji
        return

    def pozycja_do_listy(self):
        pozycja = {'nr': self._nr, 'nazwa': self._nazwa, 'plik': self._plik, 'typ': self._typ,
                   'fanart': self._fanart, 'czas': self._czas,
                   'liczba_pozycji': self._liczba_pozycji}
        return pozycja

    def get_numer(self):
        return self._nr

    def get_plik(self):
        return self._plik

    def get_nazwa(self):
        return self._nazwa


class Ulubione:
    def __init__(self):
        self.logger = logging.getLogger('proszkowska')
        self.ulubione = []
        self.pobierz_ulubione()
        return

    """def get_plik_po_numerze(self, nr_ulubionego):
        for a in self.ulubione:
            if a.get_numer() == nr_ulubionego:
                return a.get_plik()
        return None"""

    """def get_index_po_numerze(self, nr_ulubionego):
        i = 0
        for a in self.ulubione:
            if a.get_numer() == nr_ulubionego:
                return i
            i = i + 1
        return 0"""

    def ulubiony_po_numerze(self, nr_ulubionego):
        for a in self.ulubione:
            if a.get_numer() == nr_ulubionego:
                return a
        return None

    """def get_nazwa_po_numerze(self, nr_ulubionego):
        for a in self.ulubione:
            if a.get_numer() == nr_ulubionego:
                return a.get_nazwa()"""

    """def czy_jest_ulubiony_po_numerze(self, nr_ulubionego):
        for a in self.ulubione:
            if a.get_numer() == nr_ulubionego:
                return True
        return False"""

    def usun_ulubione(self, link):
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
        self.logger.info('Usunalem ulubione: ' + str(link))
        self.pobierz_ulubione()
        return

    def ulubione_do_listy(self):
        pozy = []
        for p in self.ulubione:
            pozy.append(p.pozycja_do_listy())
        return pozy

    def wyslij_ulubione(self):
        dane = {'Ulubione': self.ulubione_do_listy()}
        return dane

    def arduino_wyslij_ulubione(self):
        dane = ''
        for a in self.ulubione:
            dane += a.get_nazwa()
            dane += "|"
        return dane

    def pobierz_ulubione(self):
        katalog_ulubionych = str(THutils.odczytaj_parametr_konfiguracji('NAGL', 'KATALOG_ULUBIONYCH', self.logger))
        if katalog_ulubionych == '':
            return
        self.ulubione = []
        numer = 0
        self.logger.info('Rozpoczynam pobieranie ulubionych z katalogu: ' + katalog_ulubionych)
        filenames = os.listdir(katalog_ulubionych)
        for f in filenames:
            p = katalog_ulubionych + '/' + f
            if os.path.isdir(p):
                continue
            pl = playlista.Playlista(plik=str(p))
            numer = numer + 1
            # pl.inicjalizuj_playliste_z_pliku(nazwa_pliku=str(p))
            if len(pl.pozycje) > 0:
                fanart = pl.pozycje[0].fanart
                czas = pl.pozycje[0].czas
                typ = pl.pozycje[0].typ
                self.ulubione.append(PozycjaUubionego(numer, str(f), str(p), typ, fanart, czas, pl.liczba_pozycji()))
        self.logger.info('Pobralem ulubione. Liczba ulubionych: ' + str(len(self.ulubione)))
