import datetime
import time
import threading
import THutils
import wzmacniacze
import Kodi
import os
import logging
import thread
import playlista
import radia
import denon
import ulubione
import spotify_odtwarzacz
import spotify_klasa
import constants
from copy import deepcopy

ADRES_KODI = 'http://127.0.0.1:8088/jsonrpc'
CZAS_ODSWIEZANIA_STANU_ODTWARZACZA = 1
LICZBA_ODSWIEZEN_DO_STATUSU = 8
# CZAS_SPRAWDZANIA_OSTATNIEJ_AKTYWNOSCI = 50
CZAS_PRZERWY_MIEDZY_PROBAMI_ODTWARZANIA = 10  # w sekundach
# CZAS_ODCZYTU_KONFIGURACJI = 500
CZAS_WYLACZENIA_PO_NIEAKTYWNOSCI = 10800


# NAZWA_PLIKU_DZWONKA = constants.KATALOG_GLOWNY + '/doorbell.mp3'
# GLOSNOSC_PRZY_DZWONKU = 90

class BiezacyStan:
    def __init__(self):
        self.totaltime = 0
        self.liczba_pozycji_playlisty = 0
        self.tytul = ''
        self.currenttime = 0
        self.pauza = True
        self.interkom = False
        self.nazwa_playlisty = ''
        self.ts_playlisty = 0
        self.ts_ulubionych = 0
        self.ts_radii = 0
        self.ts_historii = 0
        self.ts = 0
        self.czy_gra_denon = False
        self.czy_aktualnie_gra = False
        # TODO self.aktualnapozycja powinno byc klasy pozycja playlisty a nie tuple
        self.aktualna_pozycja = {}
        self.nr_pozycji_na_playliscie = 0
        self.percentage = 0
        self.ktorykolwiek_wlaczony = False
        self.wzmacniacze = {}
        self.link = ''

    def biezacyStanDoTuple(self):
        return {constants.POLE_WZMACNIACZE: self.wzmacniacze, constants.POLE_INTERKOM: self.interkom,
                constants.POLE_CZY_AKTUALNIE_GRA: self.czy_aktualnie_gra,
                constants.POLE_PAUZA: self.pauza, constants.POLE_NAZWA_PLAYLISTY: self.nazwa_playlisty,
                constants.POLE_NR_POZ_NA_PLAYL: self.nr_pozycji_na_playliscie,
                #TODO liczba_pozycji playlisty nie jest juz potrzebna w androidzie zobaczyc czy nie mozna usunac w pythonie
                constants.POLE_LICZBA_POZ_PLAYL: self.liczba_pozycji_playlisty,
                constants.POLE_TIMESTAMP_PLAYLISTY: self.ts_playlisty,
                constants.POLE_TIMESTAMP_ULUBIONYCH: self.ts_ulubionych,
                constants.POLE_TIMESTAMP_RADII: self.ts_radii,
                constants.POLE_TIMESTAMP_HISTORII: self.ts_historii,
                constants.POLE_TIMESTAMP_NAGLOSNIENIA: self.ts,
                constants.POLE_AKTUALNA_POZYCJA: self.aktualna_pozycja,

                constants.POLE_TYTUL: self.tytul, constants.POLE_CZY_GRA_DENON: self.czy_gra_denon,
                constants.POLE_TOTALTIME: self.totaltime, constants.POLE_CURRENTTIME: self.currenttime,
                constants.POLE_PERCENTAGE: self.percentage,
                constants.TS: self.ts}

    def do_json(self):
        return THutils.skonstruuj_odpowiedzV2(constants.RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA, self.biezacyStanDoTuple(),
                                              constants.STATUS_OK)

class Naglosnienie:
    def __init__(self, mcp):
        self.logger = logging.getLogger(constants.NAZWA_LOGGERA)
        self.logger.info("Zaczynam inicjalizowac Naglosnienie.")

        self.wzmacniacze = wzmacniacze.Wzmacniacze(mcp, self.logger)
        self.odczytaj_konf()

        # self.glosnosc_przy_dzwonku = GLOSNOSC_PRZY_DZWONKU
        # self.czas_odczytu_konfiguracji = CZAS_ODCZYTU_KONFIGURACJI
        #self.plik_dzwonka = ''
        self.ic_trwa = False  # czy interkom jest aktywny
        self.IC_czy_gralo = False  # jesli przed interkomem gralo to True
        self.lock_aktualizacji_statusu = threading.Lock()
        self.aktualna_playlista = playlista.Playlista(przy_starcie=True)
        self.ulub = ulubione.Ulubione()
        self.czas_ostatniego_polecenia_odtwarzania = datetime.datetime.now()
        self.katalog_radii = radia.Radia()
        self.biezacy_stan = BiezacyStan()
        self.licznik_delay_odswiezania = 0
        self.den = denon.Denon(self.logger)
        self._czas_maksymalnego_braku_aktywnosci = CZAS_WYLACZENIA_PO_NIEAKTYWNOSCI

        self.spoti = spotify_odtwarzacz.SpotifyOdtwarzacz(self.logger)
        self.kodi = Kodi.Kodi(self.logger, ADRES_KODI)
        self.odtwarzacz = self.kodi

        self.pauza = True
        self.odtwarzaj_denon = False
        self.czas_ostatniej_aktywnosci = datetime.datetime.now()

        #self.notyfikacja_firebase = firebasenotification.Firebasenotification()
        self.aktualizuj_status_odtwarzacza()
        self.aktualizuj_cyklicznie_stan_odtwarzacza()
        self.logger.info('Zakonczylem konstruktora klasy naglosnienie.')

    def procesuj_polecenie(self, komenda, parametr1, parametr2):
        status_odpowiedzi = constants.STATUS_OK
        if komenda == constants.RODZAJ_KOMUNIKATU_ULUBIONE:
            return self.ulub.wyslij_ulubione()
        elif komenda == constants.RODZAJ_KOMUNIKATU_KATALOG_RADII:
            return self.katalog_radii.wyslij_katalog_radii()
        elif komenda == constants.RODZAJ_KOMUNIKATU_PLAYLISTA:
            return THutils.skonstruuj_odpowiedzV2(constants.RODZAJ_KOMUNIKATU_PLAYLISTA,
                                                 self.aktualna_playlista.wyslij_playliste(pelna=False),
                                                 constants.STATUS_OK)
        elif komenda == constants.RODZAJ_KOMUNIKATU_HISTORIA:
        # TODO liczba linii historii do parametrow
            poz = {constants.TS: self.biezacy_stan.ts_historii,
                  constants.POZYCJE: self.aktualna_playlista.odczytaj_historie()}
            return THutils.skonstruuj_odpowiedzV2(constants.RODZAJ_KOMUNIKATU_HISTORIA, poz, constants.STATUS_OK)
        elif komenda == 'ST':
            if parametr1 == 'AR':
                return self.zwroc_status_arduino(parametr2)
        elif komenda == 'WZ_AR':
            if parametr1 == constants.PARAMETR_JEDEN:
                self.wlacz_wylacz_wzmacniacz_nazwa(parametr2, True)
            else:
                self.wlacz_wylacz_wzmacniacz_nazwa(parametr2, False)
            self.kasuj_czas_ostatniej_aktywnosci()
            return self.zwroc_status_arduino(parametr2)
        elif komenda == 'UL_AR':
            return self.ulub.arduino_wyslij_ulubione()
        elif komenda == 'GL_AR':
            self.kasuj_czas_ostatniej_aktywnosci()
            self.wzmacniacze.set_glosnosc_delta_nazwa(parametr2, int(parametr1))
            return self.zwroc_status_arduino(parametr2)
        elif komenda == 'GL':  # wykorzystuje delte a nie bezwgledna wartosc glosnosci
            self.kasuj_czas_ostatniej_aktywnosci()
            self.wzmacniacze.set_glosnosc_delta_nazwa(parametr2, int(parametr1))
        elif komenda == 'AR_TOGGLE':
            self.kasuj_czas_ostatniej_aktywnosci()
            self.toggle_wzmacniacz_nazwa(parametr2)
            return self.zwroc_status_arduino(parametr2)
        elif komenda == 'GLOSN':
            self.kasuj_czas_ostatniej_aktywnosci()
            self.wzmacniacze.set_glosnosc_nazwa(parametr2, int(parametr1))
        elif komenda == 'GLOSN_DELTA':
            self.kasuj_czas_ostatniej_aktywnosci()
            self.wzmacniacze.set_glosnosc_delta_nazwa(parametr2, int(parametr1))
        elif komenda == constants.KOMENDA_DZWONEK:
            self.logger.info('Dzwonek do drzwi.')
            if not self.ic_trwa:
                thread.start_new_thread(self.odtworz_z_pliku, (self.plik_dzwonka,))
                #self.obsluz_dzwonek_do_drzwi()
        elif komenda == 'DE':
            # obsluga Denona
            if parametr1 == 'GLOSN':
                self.den.heos_set_volume(parametr2)
            elif parametr1 == 'ST':
                self.den.heos_set_play_state(parametr2)
                if parametr2 == 'play':
                    self.den.heos_play_url(self.aktualna_playlista.aktualnie_grane_link())
            elif parametr1 == 'PL':
                self.den.heos_play_url(parametr2)
            elif parametr1 == 'OD':
                if parametr2 == constants.PARAMETR_JEDEN:
                    self.odtwarzaj_denon = True
                    # naglo.wylacz_wszystkie_wzmacniacze()
                    # naglo.odtwarzaj_z_playlisty(naglo.aktualna_playlista.nr_pozycji_na_playliscie)
                    # if stan:
                    #        self.den.heos_set_play_state('play')
                else:
                    self.odtwarzaj_denon = False
                    # naglo.den.heos_set_play_state('stop')
        # elif komenda == 'WE':
        #    naglo.wybor_wejscia(int(parametr1), int(parametr2))
        #    logger.warning('Zmiana wejscia, nr wzm: ' + str(parametr1) + ', nr wejscia: ' + str(parametr2))
        elif komenda == 'IC':
            if parametr1 == constants.PARAMETR_JEDEN:
                self.ic_trwa = True
                self.logger.info('Rozpoczynam interkom.')
        elif komenda == 'OL':
            #thread.start_new_thread(self.odtwarzaj_z_linku_zeruj_playliste, (parametr1, parametr2))
            self.odtwarzaj_z_linku_zeruj_playliste(parametr1, parametr2)
        elif komenda == 'SPOTIFY':
            if parametr1 == 'L+01':
                thread.start_new_thread(self.aktualna_playlista.dodaj_z_linku_spotify, (parametr2,))
            elif parametr1 == 'OD':
                thread.start_new_thread(self.odtwarzaj_ze_spotify_uri, (parametr2,))
        elif komenda == 'QUERY_SPOTIFY':
            spot = spotify_klasa.SpotifyKlasa(self.logger)
            #odp = spot.zapytanie('', parametr1, parametr2)
            odp = spot.szukaj_zdalnie(parametr1, next=parametr2)
            #return {constants.RODZAJ_KOMUNIKATU: constants.RODZAJ_KOMUNIKATU_SPOTIFY_QUERY,
            #        constants.RESULT: odp}
            return THutils.skonstruuj_odpowiedzV2(constants.RODZAJ_KOMUNIKATU_SPOTIFY_QUERY, odp, constants.STATUS_OK)
        elif komenda == 'SPOTIFY_NEXT':
            spot = spotify_klasa.SpotifyKlasa(self.logger)
            odp = spot.nastepny(parametr1)
            return THutils.skonstruuj_odpowiedzV2(constants.RODZAJ_KOMUNIKATU_SPOTIFY_NEXT, odp, constants.STATUS_OK)
        elif komenda == 'SPOTIFY_ROZWINIECIE':
            spot = spotify_klasa.SpotifyKlasa(self.logger)
            odp = spot.rozwin(parametr1, parametr2)
            return THutils.skonstruuj_odpowiedzV2(constants.RODZAJ_KOMUNIKATU_SPOTIFY_ROZWIN, odp, constants.STATUS_OK)
        elif komenda == 'RO':
            #thread.start_new_thread(self.odtwarzaj_z_radii_po_nazwie, (parametr1, parametr2))
            self.odtwarzaj_z_radii_po_nazwie(parametr1, parametr2)
        elif komenda == 'RO_ID':
            #thread.start_new_thread(self.odtwarzaj_z_radii_po_id, (parametr1, parametr2))
            self.odtwarzaj_z_radii_po_id(parametr1, parametr2)
        elif komenda == 'OD':
            if parametr1 == 'PAUS':
                #thread.start_new_thread(self.play_pause, ())
                self.play_pause()
            elif parametr1 == 'NAST':
                #thread.start_new_thread(self.nastepny, ())
                self.nastepny()
            elif parametr1 == 'POPR':
                #thread.start_new_thread(self.poprzedni, ())
                self.poprzedni()
            elif parametr1 == 'GOTO':
                thread.start_new_thread(self.idz_do, (int(parametr2),))
            elif parametr1 == 'RODZ':
                self.aktualna_playlista.jak_odtwarza = int(parametr2)
            elif parametr1 == 'LINK':
                #thread.start_new_thread(self.odtwarzaj_z_linku_zeruj_playliste, (parametr2, ''))
                self.odtwarzaj_z_linku_zeruj_playliste(parametr2, '')
            elif parametr1 == 'ULUB':
                # TODO sprawdzic ktore jeszcze mozna zrezygnowac z osobnego threadu
                status_odpowiedzi = self.odtwarzaj_ulubione_numer(int(parametr2))
            elif parametr1 == 'ULU-':
                #thread.start_new_thread(self.ulub.usun_ulubione, (parametr2,))
                self.ulub.usun_ulubione(parametr2)
            elif parametr1 == 'ULU+':
                thread.start_new_thread(self.dodaj_do_playlisty_z_ulubionego, (int(parametr2),))
            elif parametr1 == 'HIST':
                thread.start_new_thread(self.odtworz_z_historii, (parametr2,))
            elif parametr1 == 'HIST+':
                thread.start_new_thread(self.odtworz_z_historii, (parametr2, True))
            else:
                pass
        elif komenda == 'PL':
            if parametr1 == 'ULUB':
                pass
            elif parametr1 == 'LIS+':
                thread.start_new_thread(self.ulub.zapisz_playliste_w_ulubionych(self.aktualna_playlista, parametr2))
            elif parametr1 == 'LIST':
                pass
            elif parametr1 == 'PLAY':
                #thread.start_new_thread(self.odtwarzaj_z_playlisty, (int(parametr2),))
                self.logger.info('Odtwarzam z playlisty pozycje nr: ' + str(parametr2))
                self.odtwarzaj_z_playlisty(nr_poz=int(parametr2))
            elif parametr1 == 'L+01':
                thread.start_new_thread(self.aktualna_playlista.dodaj_z_linku, (parametr2, ""))
            elif parametr1 == 'L-01':
                nr_pozycji = int(parametr2)
                if self.aktualna_playlista.usun_pozycje_z_playlisty(nr_pozycji):
                    self.odtwarzaj_z_playlisty()
        elif komenda == 'WZ':
            if parametr2 == constants.PARAMETR_JEDEN:
                self.wlacz_wylacz_wzmacniacz_nazwa(parametr1, True)
            else:
                self.wlacz_wylacz_wzmacniacz_nazwa(parametr1, False)
        elif komenda == 'WZ_TOGGLE':
            self.toggle_wzmacniacz_nazwa(parametr1)
        self.aktualizuj_status_odtwarzacza()
        return THutils.skonstruuj_odpowiedzV2(constants.RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA,
                                                    self.biezacy_stan.biezacyStanDoTuple(), status_odpowiedzi)

    def odtworz_z_historii(self, hash_historii, dodaj=False):
        # self.logger.info('Odtwarzam z historii, nr hash: ' + str(hash))
        hist = self.aktualna_playlista.odczytaj_historie()
        poz = None
        for a in hist:
            if str(a[constants.HASH]) == str(hash_historii):
                poz = a
                break
        if poz:
            if dodaj:
                self.logger.info("Dodaje do playlisty z historii: " + str(poz[constants.POZYCJA]))
                self.aktualna_playlista.dodaj_z_json(poz[constants.POZYCJA])
                self.aktualna_playlista.zapisz_playliste()
            else:
                self.logger.info("Odtwarzam z historii: " + str(poz[constants.POZYCJA]))
                self.aktualna_playlista.zeruj()
                self.aktualna_playlista.dodaj_z_json(poz[constants.POZYCJA])
                self.aktualna_playlista.zapisz_playliste()
                self.odtwarzaj_z_playlisty(zapisuj_historie=False)
        else:
            self.logger.warning("Nie odnalazlem pozycji historii dla has: " + str(hash_historii))

    '''def zapisz_playliste_w_ulubionych(self, nazwa_pliku):
        # TODO tutaj do poprawienia zrobic deepcopy
        #pl = playlista.Playlista(nazwa=self.aktualna_playlista.nazwa,
        pl=playlista.Playlista(nazwa=nazwa_pliku,
                                 pozycje=self.aktualna_playlista.pozycje,
                                 jak_odtwarza=self.aktualna_playlista.jak_odtwarza)
        # tworzenie kopii playlisty bo gdyby sie aktualna zmieniala to nie zdazy zapisac a tak bieze jej snapshot
        # pl = deepcopy(self.aktualna_playlista)
        pl.zapisz_playliste_w_ulubionych(nazwa_pliku)
        self.ulub.pobierz_ulubione()'''

    def odtworz_z_pliku(self, plik, usuwac_plik=False):
        self.ic_trwa = True
        # zapamietanie glosnosci i aktualnej pozycji
        self.logger.info('Odtwarzam z pliku: ' + str(plik))
        glosnosci = []
        for j in self.wzmacniacze.wzmacniacze:
            glosnosci.append(j.glosnosc)

        percent = int(self.odtwarzacz.percentage)

        # IC_czy_gralo - jesli True to znaczy, ze poprzednio gralo i mamy wznowic
        # self.IC_czy_gralo = self.odtwarzacz.aktualnie_gra
        self.IC_czy_gralo = self.wzmacniacze.przek.czy_ktorykolwiek_wlaczony()

        self.stop()
        #self.podmien_odtwarzacz() # force_kodi=True)
        self.odtwarzacz = self.kodi
        time.sleep(0.5)

        # ustawienie wlaczenia wszystkich wzmacniaczy i ich glosnosci
        for j in self.wzmacniacze.wzmacniacze:
            j.ustaw_glosnosc(self.glosnosc_przy_dzwonku)
        przek_tymcz = self.wzmacniacze.przek.wlacz_wszystkie_przekazniki(przekazniki=None, wlacz=True)

        # odtwarzanie za pomoca kodi, zakladamy, ze kodi jest juz ustawione jako odtwarzacz
        self.odtwarzacz.odtwarzaj_z_linku(plik)
        self.odtwarzacz.aktualnie_gra = True

        while self.odtwarzacz.aktualnie_gra:
            time.sleep(1)
            self.odtwarzacz.aktualizuj_stan()
            #self.aktualizuj_status_odtwarzacza() # force_kodi=True)

        # usuniecie pliku z interkomem
        if usuwac_plik:
            os.remove(plik)

        # odtworzenie stanu przekaznikow i glosnosci
        self.wzmacniacze.przek.wlacz_wszystkie_przekazniki(przekazniki=przek_tymcz, wlacz=False)
        a = 0
        for j in self.wzmacniacze.wzmacniacze:
            j.ustaw_glosnosc(glosnosci[a])
            a = a + 1

        # odtworzenie tego co bylo odtwarzane przed IC
        self.podmien_odtwarzacz()

        if self.IC_czy_gralo:
            self.odtwarzaj_z_playlisty()
            if self.aktualna_playlista.aktualna_pozycja().typ != playlista.TYP_RADIO:
                licznik = 0
                self.odtwarzacz.aktualizuj_stan()
                while not self.odtwarzacz.aktualnie_gra:
                    time.sleep(0.5)
                    self.odtwarzacz.aktualizuj_stan()
                    licznik = licznik + 1
                    if licznik > 100:
                        break
                self.idz_do(percent)
        self.ic_trwa = False

    def zwroc_status_arduino(self, nazwa):
        if self.wzmacniacze.przek.przekaznik_po_nazwie(nazwa).get_stan():
            a = '1'
        else:
            a = '0'
        return 'S' + a + \
               'G' + str("{0:0=3d}".format(self.wzmacniacze.wzmacniacz_po_nazwie(nazwa).glosnosc))

    def aktualizuj_cyklicznie_stan_odtwarzacza(self):
        if self.licznik_delay_odswiezania == LICZBA_ODSWIEZEN_DO_STATUSU:
            self.licznik_delay_odswiezania = 0
        else:
            self.licznik_delay_odswiezania += 1

        if self.wzmacniacze.przek.czy_ktorykolwiek_wlaczony():
            self.licznik_delay_odswiezania = 0

        if self.licznik_delay_odswiezania == 0:
            self.aktualizuj_status_odtwarzacza()

        # odtwarzanie kolejnego utworu
        if not self.ic_trwa:
            # TODO pauza powinna byc jednoznaczna z ktorykolwiek wlaczony=false
            if self.wzmacniacze.przek.czy_ktorykolwiek_wlaczony() and self.pauza is False:
                if not self.odtwarzacz.aktualnie_gra:
                    # delta ma sluzyc temu aby co 0,5 sekundy nie probowac kazac kodi odtwarzac tego samego
                    delta = datetime.datetime.now() - self.czas_ostatniego_polecenia_odtwarzania
                    if delta.total_seconds() > CZAS_PRZERWY_MIEDZY_PROBAMI_ODTWARZANIA:
                        self.aktualna_playlista.oblicz_kolejny_do_grania()
                        thread.start_new_thread(self.odtwarzaj_z_playlisty, ())
                        #self.odtwarzaj_z_playlisty(self.aktualna_playlista.nr_pozycji_na_playliscie)
                for j in self.wzmacniacze.wzmacniacze:
                    j.ustaw_glosnosc(j.glosnosc)
            # else:
            #    if self.odtwarzacz.aktualnie_gra:
            #        self.play_pause()
                    # self.aktualna_playlista.startuj_od_biezacego = True

        self.automatyczne_wylaczanie_przy_braku_aktywnosci()
        threading.Timer(CZAS_ODSWIEZANIA_STANU_ODTWARZACZA, self.aktualizuj_cyklicznie_stan_odtwarzacza).start()

    def przekaz_stan_do_garazu(self, firebase=False):
        if firebase:
            fire = constants.PARAMETR_JEDEN
        else:
            fire = constants.PARAMETR_ZERO
        THutils.przekaz_polecenie_V2_JSONRPC(constants.HOST_I_PORT_GARAZ_v2,
                                             constants.OBSZAR_STAT,
                                             constants.RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA_PUSH_ZE_STRYCHU,
                                             self.biezacy_stan.biezacyStanDoTuple(), fire)

    def aktualizuj_status_odtwarzacza(self):  #, force_kodi=False):
        przekaz_stan_do_gar = False
        fire = False
        self.lock_aktualizacji_statusu.acquire()
        poprzedni_stan = deepcopy(self.biezacy_stan)
        """if self.ic_trwa:
            self.podmien_odtwarzacz(force_kodi=True)
        else:
            self.podmien_odtwarzacz(force_kodi=force_kodi)"""
        self.odtwarzacz.aktualizuj_stan()
        # self.den.aktualizuj_stan()
        # if self.odtwarzaj_denon:
        #    self.aktualnie_gra = self.den.current_ispwon
        # else:

        self.biezacy_stan.wzmacniacze = self.wzmacniacze.do_listy()
        self.biezacy_stan.interkom = self.ic_trwa
        self.biezacy_stan.czy_aktualnie_gra = self.odtwarzacz.aktualnie_gra
        self.biezacy_stan.pauza = self.pauza
        self.biezacy_stan.nazwa_playlisty = self.aktualna_playlista.nazwa
        self.biezacy_stan.nr_pozycji_na_playliscie = self.aktualna_playlista.nr_pozycji_na_playliscie
        self.biezacy_stan.liczba_pozycji_playlisty = self.aktualna_playlista.liczba_pozycji()
        self.biezacy_stan.ts_playlisty = self.aktualna_playlista.ts
        self.biezacy_stan.ts_ulubionych = self.ulub.ts
        self.biezacy_stan.ts_radii = self.katalog_radii.ts
        self.biezacy_stan.ts_historii = self.aktualna_playlista.ts_historii

        tytul = ''
        p = {}
        poz = self.aktualna_playlista.aktualna_pozycja()
        if poz is not None:
            p = poz.pozycja_do_listy()
            # TODO czy nie mozna przejsc zawsze na self.odtwarzacz.tytul?
            if poz.typ == playlista.TYP_RADIO:
                tytul = self.odtwarzacz.tytul
            else:
                tytul = THutils.xstr(poz.title)
        self.biezacy_stan.aktualna_pozycja = p
        self.biezacy_stan.nazwa_playlisty = self.aktualna_playlista.nazwa
        self.biezacy_stan.czy_gra_denon = self.odtwarzaj_denon
        self.biezacy_stan.totaltime = self.odtwarzacz.totaltime
        self.biezacy_stan.currenttime = self.odtwarzacz.currenttime
        self.biezacy_stan.percentage = self.odtwarzacz.percentage
        a = self.wzmacniacze.przek.czy_ktorykolwiek_wlaczony()
        if self.biezacy_stan.ktorykolwiek_wlaczony != a:
            if not self.ic_trwa:
                #thread.start_new_thread(self.notyfikacja_firebase.notify,
                #                        (constants.OBSZAR_NAGL, constants.FIREBASE_KOMUNIKAT_WZMACNIACZ,))
                #thread.start_new_thread(self.notyfikacja_firebase.notify,
                #                        (constants.OBSZAR_NAGL, constants.FIREBASE_KOMUNIKAT_WZMACNIACZ,
                #                         self.biezacy_stan.biezacyStanDoTuple()))
                przekaz_stan_do_gar = True
                fire = True
                #self.przekaz_stan_do_garazu(firebase=True)
        self.biezacy_stan.ktorykolwiek_wlaczony = a
        if self.biezacy_stan.tytul != tytul:
            if not self.ic_trwa:
                #thread.start_new_thread(self.notyfikacja_firebase.notify,
                #                        (constants.OBSZAR_NAGL, constants.FIREBASE_KOMUNIKAT_TYTUL,
                #                         tytul))
                #thread.start_new_thread(self.notyfikacja_firebase.notify,
                #                        (constants.OBSZAR_NAGL, constants.FIREBASE_KOMUNIKAT_TYTUL,
                #                         self.biezacy_stan.biezacyStanDoTuple()))
                self.biezacy_stan.tytul = tytul
                przekaz_stan_do_gar = True
                fire = True
                #self.przekaz_stan_do_garazu(firebase=True)
        else:
            self.biezacy_stan.tytul = tytul
        try:
            link = self.aktualna_playlista.aktualna_pozycja().link
        except AttributeError:
            link = ''
        try:
            if self.biezacy_stan.link != link:
                if not self.ic_trwa:
                    #thread.start_new_thread(self.notyfikacja_firebase.notify,
                    #                        (constants.OBSZAR_NAGL, constants.FIREBASE_KOMUNIKAT_LINK,
                    #                         link))
                    #thread.start_new_thread(self.notyfikacja_firebase.notify,
                    #                        (constants.OBSZAR_NAGL, constants.FIREBASE_KOMUNIKAT_LINK,
                    #                         self.biezacy_stan.biezacyStanDoTuple()))
                    przekaz_stan_do_gar = True
                    fire = True
                    #self.przekaz_stan_do_garazu(firebase=True)
        except AttributeError:
            self.logger.warning("Brak sekcji [aktualna_pozycja]: " + str(self.biezacy_stan.aktualna_pozycja))
        self.biezacy_stan.link = link
        if poprzedni_stan.biezacyStanDoTuple() != self.biezacy_stan.biezacyStanDoTuple():
            self.biezacy_stan.ts = int(time.time())
            przekaz_stan_do_gar = True
            #self.przekaz_stan_do_garazu()
        if przekaz_stan_do_gar:
            self.przekaz_stan_do_garazu(firebase=fire)
        self.lock_aktualizacji_statusu.release()

    def odtwarzaj_ulubione_numer(self, numer_ulubionego):
        ul = self.ulub.ulubiony_po_numerze(numer_ulubionego)
        if not ul:
            self.logger.warning('Odtwarzaj-ulub_numer, nie ma takiego numeru: ' +
                                str(numer_ulubionego))
            return constants.STATUS_NOK
        self.kasuj_czas_ostatniej_aktywnosci()
        self.stop()
        self.aktualna_playlista.inicjalizuj_playliste_z_pliku(ul.get_plik())
        self.odtwarzaj_z_playlisty(0)
        self.logger.info('Odtwarzam ulubione nr: ' + str(numer_ulubionego) +
                         " : " + ul.get_nazwa())
        return constants.STATUS_OK

    def dodaj_do_playlisty_z_ulubionego(self, numer_ulubionego):
        ul = self.ulub.ulubiony_po_numerze(numer_ulubionego)
        if not ul:
            self.logger.warning('Dodaj-ulub_numer, nie ma takiego numeru: ' +
                                str(numer_ulubionego))
            return
        #if ul.typ == playlista.TYP_RADIO:
        #    return
        self.kasuj_czas_ostatniej_aktywnosci()
        self.aktualna_playlista.inicjalizuj_playliste_z_pliku(ul.get_plik(), zeruj=False)

    def odtwarzaj_z_radii_po_id(self, nazwa_serwisu, idstacji):
        self.logger.info('Odtwarzam z radii: ' + nazwa_serwisu + ' ' + str(idstacji))
        a = self.katalog_radii.znajdz_stacje_po_nazwie_i_id(nazwa_serwisu, idstacji)
        if not a:
            self.logger.warning('Nie odnalazlem takiego radia po id: ' + nazwa_serwisu + ' ' + idstacji)
            return
        self.odtwarzaj_z_radii(a)

    def odtwarzaj_z_radii_po_nazwie(self, nazwa_serwisu, nazwa_stacji):
        self.logger.info('Odtwarzam z radii: ' + nazwa_serwisu + ' ' + nazwa_stacji)
        a = self.katalog_radii.znajdz_stacje_po_nazwie_i_serwisie(nazwa_serwisu, nazwa_stacji)
        if not a:
            self.logger.warning('Nie odnalazlem takiego radia: ' + nazwa_serwisu + ' ' + nazwa_stacji)
            return
        self.odtwarzaj_z_radii(a)

    def odtwarzaj_z_radii(self, radio):
        # radio to stacja radiowa
        self.stop()
        self.aktualna_playlista.zeruj()
        self.aktualna_playlista.nazwa = radio['serwis'] + ' - ' + radio[constants.NAZWA]
        if radio['serwis'] == radia.NAZWA_SERWISU_TUNEIN:
            link = self.katalog_radii.tunein_dekoduj_stream_stacji(radio['link'])
        else:
            link = radio['link']
        self.aktualna_playlista.dodaj_pozycje_z_polami(artist='', album='', title=radio[constants.NAZWA],
                                                       link=link, typ=playlista.TYP_RADIO, fanart=radio['logo'],
                                                       serwis_radiowy=radio['serwis'], stacja_radiowa=radio[constants.NAZWA])
        self.odtwarzaj_z_playlisty()

    def odtwarzaj_z_linku_zeruj_playliste(self, link, fanartlink):
        self.stop()
        self.aktualna_playlista.zeruj()
        self.aktualna_playlista.dodaj_z_linku(link, fanartlink, zmien_nazwe=True)
        self.odtwarzaj_z_playlisty(0)

    def odtwarzaj_ze_spotify_uri(self, uri):
        self.stop()
        self.aktualna_playlista.zeruj()
        self.aktualna_playlista.dodaj_z_linku_spotify(uri, zmien_nazwe=True)
        self.odtwarzaj_z_playlisty()

    def play_pause(self):
        self.kasuj_czas_ostatniej_aktywnosci()
        self.czas_ostatniego_polecenia_odtwarzania = datetime.datetime.now()
        self.pauza = not self.pauza

        # if self.odtwarzaj_denon:
        #    self.den.heos_stop()
        # else:
        if self.aktualna_playlista.liczba_pozycji() > 0:
            if self.aktualna_playlista.pozycje[0].typ == playlista.TYP_RADIO:
                if self.pauza:
                    self.odtwarzacz.stop()
                else:
                    self.odtwarzaj_z_playlisty(zapisuj_historie=False)
            else:
                self.odtwarzacz.play_pause(start=not self.pauza)

    def idz_do(self, czas):
        # czas jest w procentach
        self.kasuj_czas_ostatniej_aktywnosci()
        # if self.odtwarzaj_denon:
        #    self.den.heos_idz_do(czas)
        # else:
        self.odtwarzacz.idz_do(czas)

    def stop(self):
        self.kasuj_czas_ostatniej_aktywnosci()
        # if self.odtwarzaj_denon:
        #    self.den.heos_stop()
        # else:
        self.odtwarzacz.stop()

    def odtwarzaj_z_playlisty(self, nr_poz=None, zapisuj_historie=True):
        if self.aktualna_playlista.liczba_pozycji() == 0:
            return

        if nr_poz:
            self.aktualna_playlista.nr_pozycji_na_playliscie = nr_poz

        if zapisuj_historie:
            try:
                self.aktualna_playlista.zapisz_w_historii(
                    self.aktualna_playlista.pozycje[self.aktualna_playlista.nr_pozycji_na_playliscie])
            except IndexError:
                pass
        # if self.odtwarzaj_denon:
        #    self.den.heos_play_url(link)
        # else:
        self.czas_ostatniego_polecenia_odtwarzania = datetime.datetime.now()
        #self.aktualna_playlista.nr_pozycji_na_playliscie = nr_pozycji
        self.odtwarzacz.stop()
        self.podmien_odtwarzacz()
        #thread.start_new_thread(self.odtwarzacz.odtwarzaj_z_linku,
        #                        (self.aktualna_playlista.aktualnie_grane_link(),))
        self.odtwarzacz.odtwarzaj_z_linku(self.aktualna_playlista.aktualnie_grane_link())
        self.aktualna_playlista.zapisz_playliste()

    def podmien_odtwarzacz(self): #, force_kodi=False):
        """if force_kodi:
            self.kodi.aktualizuj_stan()
            self.odtwarzacz = self.kodi
            return"""
        if self.aktualna_playlista.aktualna_pozycja() is not None:
            if self.aktualna_playlista.aktualna_pozycja().typ == playlista.TYP_SPOTIFY:
                self.spoti.aktualizuj_stan()
                self.odtwarzacz = self.spoti
            else:
                self.kodi.aktualizuj_stan()
                self.odtwarzacz = self.kodi

    def nastepny(self):
        self.kasuj_czas_ostatniej_aktywnosci()
        if not self.odtwarzacz.aktualnie_gra:
            return
        if self.aktualna_playlista.nastepny():
            self.odtwarzaj_z_playlisty()

    def poprzedni(self):
        self.kasuj_czas_ostatniej_aktywnosci()
        if not self.odtwarzacz.aktualnie_gra:
            return
        if self.aktualna_playlista.poprzedni():
            self.odtwarzaj_z_playlisty()

    def kasuj_czas_ostatniej_aktywnosci(self):
        self.czas_ostatniej_aktywnosci = datetime.datetime.now()

    def odczytaj_konf(self):
        # TODO porzadek z konfiguracja
        self.plik_dzwonka = os.path.dirname(os.path.realpath(__file__)) + '/' + \
                            THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_NAGL, 'PLIK_DZWONKA', self.logger)
        self.glosnosc_przy_dzwonku = int(
            THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_NAGL, 'GLOSNOSC_PRZY_DZWONKU', self.logger))
        self.czas_odczytu_konfiguracji = int(
            THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_NAGL, 'CZAS_ODCZYTU_KONFIG', self.logger))
        self._czas_maksymalnego_braku_aktywnosci = int(
            THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_NAGL, 'CZAS_MAKSYMALNEGO_BRAKU_AKTYWNOSCI', self.logger))

        now = datetime.datetime.now()
        run_at = now + datetime.timedelta(hours=self.czas_odczytu_konfiguracji)
        delay = (run_at - now).total_seconds()
        threading.Timer(delay, self.odczytaj_konf).start()

    def toggle_wzmacniacz_nazwa(self, nazwa):
        if self.wzmacniacze.przek.przekaznik_po_nazwie(nazwa).get_stan():
            self.wlacz_wylacz_wzmacniacz_nazwa(nazwa, False)
        else:
            self.wlacz_wylacz_wzmacniacz_nazwa(nazwa, True)

    def wlacz_wylacz_wzmacniacz_nazwa(self, nazwa, stan):
        # stan jest boolean
        self.kasuj_czas_ostatniej_aktywnosci()
        if stan:
            self.logger.info('Wlaczylem wzmacniacz : ' + str(nazwa))
        else:
            self.logger.info('Wylaczylem wzmacniacz : ' + str(nazwa))
        self.wzmacniacze.przek.ustaw_przekaznik_nazwa(nazwa, stan)

        # pauza jesli wszystko beda wylaczone
        if not self.wzmacniacze.przek.czy_ktorykolwiek_wlaczony():
            # if not self.pauza:
            self.play_pause()
            return

        if stan and self.pauza:
            self.play_pause()

    def wylacz_wszystkie_wzmacniacze(self):
        self.wlacz_wylacz_wzmacniacz_nazwa('Kuchnia', False)
        self.wlacz_wylacz_wzmacniacz_nazwa('Taras', False)
        self.wlacz_wylacz_wzmacniacz_nazwa('Lazienka', False)
        self.wlacz_wylacz_wzmacniacz_nazwa('Balkon', False)
        self.wlacz_wylacz_wzmacniacz_nazwa('Sypialnia', False)
        # TODO dorobic Denona do listy ?

    def automatyczne_wylaczanie_przy_braku_aktywnosci(self):
        roznica = datetime.datetime.now() - self.czas_ostatniej_aktywnosci
        if roznica.total_seconds() > self._czas_maksymalnego_braku_aktywnosci:
            if self.wzmacniacze.przek.czy_ktorykolwiek_wlaczony():
                self.wylacz_wszystkie_wzmacniacze()
                # self.play_pause()
                self.logger.info('Wylaczam wzmacn przy braku aktywnosci. Czas ostatn aktywn: ' +
                                 str(self.czas_ostatniej_aktywnosci))
        # threading.Timer(CZAS_SPRAWDZANIA_OSTATNIEJ_AKTYWNOSCI,
        #                self.automatyczne_wylaczanie_przy_braku_aktywnosci).start()
