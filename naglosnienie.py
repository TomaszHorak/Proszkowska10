import constants
from CurrentPlaylist import CurrentPlaylist
from spotify_klasa import SpotifyKlasa
from wzmacniacze import Wzmacniacze
from copy import deepcopy
import THutils
import datetime
from threading import Lock
from CurrentStatus import CurrentStatus
from threading import Timer
from Kodi import Kodi
from favourites import Favourites
from item import Item
from MojLogger import MojLogger

CZAS_ODSWIEZANIA_STANU_ODTWARZACZA = 4
CZAS_PRZERWY_MIEDZY_PROBAMI_ODTWARZANIA = 10  # w sekundach
CZAS_WYLACZENIA_PO_NIEAKTYWNOSCI = 10800  # 3 godziny, podane w sekundach


class Naglosnienie:
    def __init__(self, logger: MojLogger, baseFolder):
        self.logger = logger
        self.obszar = constants.OBSZAR_NAGL
        self.logger.info(self.obszar, "init", "Zaczynam inicjalizowac Naglosnienie.")

        self.wzmacniacze = Wzmacniacze(self.logger)
        self.wzmacniacze.wlacz_wylacz_wszystkie(False)
        self.__odczytaj_konf()

        self.ic_trwa = False  # czy interkom jest aktywny
        self.IC_czy_gralo = False  # jesli przed interkomem gralo to True
        self.lock_aktualizacji_statusu = Lock()
        self.czas_ostatniego_polecenia_odtwarzania = datetime.datetime.now()

        self.currentStatus = CurrentStatus(logger=self.logger)
        self.currentPlaylist = CurrentPlaylist(logger=self.logger)
        self.aktulizuj_stan_wzmacniaczy()
        self._czas_maksymalnego_braku_aktywnosci = CZAS_WYLACZENIA_PO_NIEAKTYWNOSCI

        self.ulub = Favourites(self.obszar, self.logger, baseFolder)

        # TODO odremowac ponizsze i dorobic klasy
        # self.katalog_radii = radia.Radia(self.obszar, self.logger)
        # self.katalog_radii.pobierz_radia_cyklicznie()

        self.kodi = Kodi(self.currentStatus, self.currentPlaylist, logger=self.logger)
        self.spot = SpotifyKlasa(self.logger, baseFolder, self.currentStatus, self.currentPlaylist)
        self.__updateFavouriteFromSpotify()
        self.odtwarzacz = self.kodi
        self.odtwarzacz.stop()
        if self.currentStatus.item.isSpotify():
            self.odtwarzacz = self.spot
            self.odtwarzacz.stop()
        self.czas_ostatniej_aktywnosci = datetime.datetime.now()

        self.aktualizuj_cyklicznie_stan_odtwarzacza()
        self.logger.info(self.obszar, "init", 'Zakonczylem konstruktora klasy naglosnienie.')

    def __updateFavouriteFromSpotify(self):
        pl = self.spot.klient.user_playlists('etp7wlnmmtumornhaxvbmuqwk')
        playlistyTH = pl['items']
        while pl['next']:
            pl = self.spot.klient.next(pl)
            playlistyTH.extend(pl['items'])
        for pl in playlistyTH:
            item = Item()
            item.fromSpotifyPlaylist(pl)
            self.ulub.items.append(item)

        pl = self.spot.klient.current_user_playlists()
        playlistyStrych = pl['items']
        while pl['next']:
            pl = self.spot.klient.next(pl)
            playlistyStrych.extend(pl['items'])
        for pl in playlistyStrych:
            item = Item()
            item.fromSpotifyPlaylist(pl)
            self.ulub.items.append(item)
        self.ulub.resetTS()

    def odtwarzaj_ze_spotify_uri(self, uri):
        # sprawdzamy czy spotify: jest w uri
        # sprawdzamy jaki jest typ: track:album:playlis:artist
        # dodajemy odpowiednio parsujac efekt dalszych zapytan

        graj = False
        if not self.spot.isValidUriOrLink(uri):
            return 'Bledne URI, nie zaczyna sie od spotify:'  # TODO dorobic obsluge bledu

        self.stop()
        self.odtwarzacz = self.spot
        self.spot.odtwarzaj_z_linku(uri)

        '''if self.spot.isTrack(uri):
            track = self.spot.klient.track(uri)
            if 'type' in track:
                if track['type'] == 'track':
                    self.stop()
                    self.odtwarzacz.aktualna_playlista.zeruj()
                    self.odtwarzacz.aktualna_playlista.dodaj_do_playlisty_spotify_track(track)
                    self.odtwarzaj_z_playlisty()
                    return'''

        '''if ':track:' in uri:
            self.aktualna_playlista.__
            procesu track
            return
        if ':album:' in uri:
            procesu album
            return
        if ':artist:' in uri:
            procesuj artist
            return
        if ':playlist:' in uri:
            procesuj playlist
            return
        if not graj:
            return 'Bledne uri, ani nie track ani nie playlista'
        '''

    def aktualizuj_status_odtwarzacza(self, wymus=False):  # , force_kodi=False):
        if self.ic_trwa:
            self.logger.warning(self.obszar, 'stat', 'Nie aktualizuje stanu odtwarzacza bo trwa IC')
            return
        fire = wymus
        self.lock_aktualizacji_statusu.acquire()
        # TODO usunac deepcopy i recznie porownywac
        poprzedni_stan = deepcopy(self.currentStatus)
        self.odtwarzacz.aktualizuj_stan()

        self.currentStatus = self.odtwarzacz.currentStatus
        self.currentStatus.wzmacniacze = self.wzmacniacze.do_listy()
        self.currentStatus.interkom = self.ic_trwa
        self.currentStatus.ts_playlisty = self.currentPlaylist.ts
        self.currentStatus.ts_ulubionych = self.ulub.ts
        # TODO dorobic statusy z playlisty i pozostale jak juz beda zmienne
        self.currentStatus.ts_radii = 0  # self.katalog_radii.ts
        self.currentStatus.ts_historii = 0  # self.aktualna_playlista.ts_historii

        # odczytanie tytulu z Kodi albo z drugiego odtwarzacza
        # TODO duza integracja z katalgiem radii i aktualna playlista wyremowane wszystko
        '''tytul = ''

        poz = self.aktualna_playlista.aktualna_pozycja()  # type: playlista.PozycjaPlaylisty
        if poz is not None:
            # TODO czy nie mozna przejsc zawsze na self.odtwarzacz.tytul?
            if poz.typ == playlista.TYP_RADIO:
                if poz.serwis_radiowy == radia.NAZWA_SERWISU_OPENFM:
                    if poz.ts_stop < int(time.time()):
                        if self.wzmacniacze.czy_ktorykolwiek_wlaczony():
                            artysta, album, tytul_utworu, ts_konca = self.katalog_radii.odswiez_co_grane_openfm(
                                poz.id_stacji_radiowej)
                            poz.album = album
                            poz.artist = artysta
                            poz.title = tytul_utworu
                            tytul = tytul_utworu
                            # kontrola nie za czestego odczytywania co grane
                            if ts_konca < int(time.time()):
                                poz.ts_stop = int(time.time()) + radia.INTERWAL_ODCZYTU_CO_GRANE
                            else:
                                poz.ts_stop = ts_konca
                else:
                    tytul = self.odtwarzacz.tytul
            else:
            tytul = poz.title
            self.currentStatus.aktualna_pozycja = poz
            self.currentStatus.nazwa_playlisty = self.aktualna_playlista.nazwa'''

        '''if self.currentStatus.title != tytul:
            if not self.ic_trwa:
                self.currentStatus.title = tytul
                fire = True
        else:
            self.currentStatus.title = tytul
        try:
            link = self.aktualna_playlista.aktualna_pozycja().link
        except AttributeError:
            link = ''
        try:
            if self.currentStatus.link != link:
                if not self.ic_trwa:
                    fire = True
        except AttributeError:
            self.logger.warning(self.obszar, 'stat', "Brak sekcji [aktualna_pozycja]: " + str(
                self.currentStatus.aktualna_pozycja.pozycja_do_listy()))
        self.currentStatus.link = link'''

        #jesli gra spotify i dobrnelismy do konca playlisty to zaczac od poczatku
        #if not self.currentStatus.aktualnie_gra:
        #    self.spot.klient.next_track(self.spot.dev_id)

        # resetowanie ts tylko kiedy stan rozni sie od poprzedniego, wybrane elementy
        if self.currentStatus.aktualnie_gra != poprzedni_stan.aktualnie_gra:
            fire = True
        if self.currentStatus.item.title != poprzedni_stan.item.title:
            fire = True
        if self.currentStatus.totaltime != poprzedni_stan.totaltime:
            fire = True
        # if self.currentStatus.ktorykolwiek_wlaczony != poprzedni_stan.ktorykolwiek_wlaczony:
        #    fire = True
        # if self.currentStatus.wzmacniacze != poprzedni_stan.wzmacniacze:
        #    fire = True
        #if self.currentStatus.nazwa_playlisty != poprzedni_stan.nazwa_playlisty:
        #    fire = True
        # if self.currentStatus.liczba_pozycji_playlisty != poprzedni_stan.liczba_pozycji_playlisty:
        #    fire = True
        if self.currentStatus.ts_playlisty != poprzedni_stan.ts_playlisty:
            fire = True
        if self.currentStatus.ts_ulubionych != poprzedni_stan.ts_ulubionych:
            fire = True
        if self.currentStatus.ts_radii != poprzedni_stan.ts_radii:
            fire = True
        if self.currentStatus.ts_historii != poprzedni_stan.ts_historii:
            fire = True

        # if poprzedni_stan.biezacyStanDoTuple() != self.currentStatus.biezacyStanDoTuple():
        #    self.currentStatus.ts = int(time.time())
        #    self.przekaz_stan_naglosnienia_do_garazu()

        #if fire:
            #self.currentStatus.ts = THutils.getCurrentTimeStamp()
            # TODO to przekazywanie przerobic na nowe API jak juz bedize w garazu
        THutils.przekaz_polecenie_do_garazu(constants.OBSZAR_NAGL, self.logger,
                                            {
                                                'rodzaj_komunikatu': constants.RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA,
                                                'result': self.currentStatus.getCurrentStatus()})
        self.lock_aktualizacji_statusu.release()

    '''def nastepny(self):
        # TODO kasuj czas ostatniej akt przeniesc z powrtotem do naglosnienia
        # self.kasuj_czas_ostatniej_aktywnosci()
        if not self.odtwarzacz.currentStatus.aktualnie_gra:
            return
        if self.odtwarzacz.aktualna_playlista.nastepny():
            self.odtwarzaj_z_playlisty()

    def poprzedni(self):
        # self.kasuj_czas_ostatniej_aktywnosci()
        if not self.odtwarzacz.currentStatus.aktualnie_gra:
            return
        if self.odtwarzacz.aktualna_playlista.poprzedni():
            self.odtwarzaj_z_playlisty()'''

    def odtwarzaj_ulubione_nazwa(self, nazwa_ulubionego):
        # TODO sprawdzic czy ktokolwiek uzywa ulubionego po nazwie czy tylko po numerze, jesli tylko po nazwie to po co jest numer?
        ul = self.ulub.ulubiony_po_nazwie(nazwa_ulubionego)
        if not ul:
            self.logger.warning(self.obszar, 'ulubione', 'Odtwarzaj-ulub_numer, nie ma takiego numeru: ' +
                                str(nazwa_ulubionego))
            return
        self.__playUlubioneItem(ul)

    def odtwarzaj_ulubione_numer(self, numer_ulubionego):
        ul: Item = self.ulub.ulubiony_po_numerze(numer_ulubionego)
        if not ul:
            self.logger.warning(self.obszar, 'ulubione', 'Odtwarzaj-ulub_numer, nie ma takiego numeru: ' +
                                str(numer_ulubionego))
            return
        self.__playUlubioneItem(ul)

    def __playUlubioneItem(self, item: Item):
        self.__kasuj_czas_ostatniej_aktywnosci()
        self.stop()
        self.odtwarzacz.currentStatus.setCurrentItem(item)
        if item.isRadio():
            self.odtwarzacz = self.kodi
            self.currentStatus.totaltime = 0
            self.currentStatus.currenttime = 0
            self.currentStatus.percentage = 0
            self.odtwarzacz.odtwarzaj_z_linku(item.link)
        if item.isSpotify():
            self.odtwarzacz = self.spot
            self.spot.updateCurrentPlaylistFromContextUri(self.currentStatus.item.contexturi)
            self.spot.klient.start_playback(self.spot.dev_id, context_uri=item.contexturi)
        self.currentStatus.resetujTS()
        self.logger.info(self.obszar, 'odtworz', 'Odtwarzam ulubione ' + item.name)
        self.aktualizuj_status_odtwarzacza()
        #TODO w kazdej funkcji ktora wplywa na naglosnienie trzeba zrobic reset tsa i aktualizowac status

    def toggle_wzmacniacz_nazwa(self, nazwa):
        wasOff = not self.wzmacniacze.czy_ktorykolwiek_wlaczony()
        if self.wzmacniacze.toggle_wzmacniacz_nazwa(str(nazwa)):
            self.currentStatus.resetujTS()
            self.__kasuj_czas_ostatniej_aktywnosci()
            self.aktulizuj_stan_wzmacniaczy()

            #jezeli pierwszy wlaczony to graj z biezacej pozycji
            if wasOff:
                self.odtwarzacz.resume()

            #jezeli zaden nie wlaczony to rob stop
            if not self.wzmacniacze.czy_ktorykolwiek_wlaczony():
                self.odtwarzacz.stop()

            self.aktualizuj_status_odtwarzacza(wymus=True)

    def aktulizuj_stan_wzmacniaczy(self):
        self.currentStatus.statusWzmacniacze = self.wzmacniacze.do_listy()
        self.currentStatus.resetujTS()

    def aktualizuj_cyklicznie_stan_odtwarzacza(self):
        self.aktualizuj_status_odtwarzacza()
        self.automatyczne_wylaczanie_przy_braku_aktywnosci()
        Timer(CZAS_ODSWIEZANIA_STANU_ODTWARZACZA, self.aktualizuj_cyklicznie_stan_odtwarzacza).start()

    def __odtwarzaj_z_linku(self, link, fanartlink=None):
        # TODO dorobic weryfikacje czy link nie jest pusty, wtedy nie wylacz pazu jesli jest
        if self.odtwarzacz.aktualna_playlista.aktualna_pozycja().isRadio():
            self.stop()
        elif self.odtwarzacz.aktualna_playlista.aktualna_pozycja().isSpotify():
            self.spot.stop()

        self.odtwarzacz.aktualna_playlista.zeruj()
        self.odtwarzacz.aktualna_playlista.dodaj_z_linku(link, fanartlink, zmien_nazwe=True)
        self.odtwarzaj_z_playlisty(0)
        self.pauza = False
        # self.odtwarzacz.odtwarzaj_z_linku(link)
        # self.aktualizuj_status_odtwarzacza()

    def odtwarzaj_z_playlisty(self, nr_poz=None):
        self.czas_ostatniego_polecenia_odtwarzania = datetime.datetime.now()
        if self.currentStatus.item.isSpotify():
            self.spot.playFromCurrentPlaylist(nr_poz)

    def stop(self):
        self.__kasuj_czas_ostatniej_aktywnosci()
        self.odtwarzacz.stop()

    def __kasuj_czas_ostatniej_aktywnosci(self):
        self.czas_ostatniej_aktywnosci = datetime.datetime.now()

    def automatyczne_wylaczanie_przy_braku_aktywnosci(self):
        roznica = datetime.datetime.now() - self.czas_ostatniej_aktywnosci
        if roznica.total_seconds() > self._czas_maksymalnego_braku_aktywnosci:
            if self.wzmacniacze.czy_ktorykolwiek_wlaczony():
                self.wzmacniacze.wlacz_wylacz_wszystkie(False)  # wylacz_wszystkie_wzmacniacze()
                self.aktulizuj_stan_wzmacniaczy()
                self.odtwarzacz.stop()
                self.aktualizuj_status_odtwarzacza()
                self.logger.info(self.obszar, "cisza",
                                 'Wylaczam wzmacniacze przy braku aktywnosci. Czas ostatniej aktywnosci: ' +
                                 str(self.czas_ostatniej_aktywnosci))

    def __odczytaj_konf(self):
        # TODO porzadek z konfiguracja
        # self.plik_dzwonka = path.dirname(path.realpath(__file__)) + '/' + \
        #                    THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_NAGL, 'PLIK_DZWONKA',
        #                                                           self.logger)
        self.plik_dzwonka = ''
        self.glosnosc_przy_dzwonku = int(THutils.odczytaj_parametr_konfiguracji(
            constants.OBSZAR_NAGL, 'GLOSNOSC_PRZY_DZWONKU', 95, logger=self.logger))

        self._czas_maksymalnego_braku_aktywnosci = int(THutils.odczytaj_parametr_konfiguracji(
            constants.OBSZAR_NAGL, 'CZAS_MAKSYMALNEGO_BRAKU_AKTYWNOSCI', CZAS_WYLACZENIA_PO_NIEAKTYWNOSCI,
            logger=self.logger))
