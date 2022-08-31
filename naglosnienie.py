import datetime
import time
import threading
import THutils
import wzmacniacze
import Kodi
import os
from MojLogger import MojLogger
import liriki
import playlista
import radia
import ulubione
import spotify_odtwarzacz
import spotify_klasa
import constants
from copy import deepcopy
#TODO to deepcopy usunac i porownywac na biezaco

ADRES_KODI = 'http://127.0.0.1:8088/jsonrpc'
CZAS_ODSWIEZANIA_STANU_ODTWARZACZA = 1
LICZBA_ODSWIEZEN_DO_STATUSU = 8
CZAS_PRZERWY_MIEDZY_PROBAMI_ODTWARZANIA = 10  # w sekundach
CZAS_WYLACZENIA_PO_NIEAKTYWNOSCI = 10800 #3 godziny, podane w sekundach


# NAZWA_PLIKU_DZWONKA = constants.KATALOG_GLOWNY + '/doorbell.mp3'
# GLOSNOSC_PRZY_DZWONKU = 90


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


class BiezacyStan:
    def __init__(self):
        self.totaltime = 0
        self.tytul = ''
        self.currenttime = 0
        self.pauza = True
        self.interkom = False
        self.nazwa_playlisty = ''
        self.ts_playlisty = 0
        self.ts_ulubionych = 0
        self.ts_wzmacniaczy = 0
        self.ts_radii = 0
        self.ts_historii = 0
        self.ts = 0
        self.czy_gra_denon = False
        #TODO denona usunac z calego programu
        self.czy_aktualnie_gra = False
        self.aktualna_pozycja = playlista.PozycjaPlaylisty() # type: playlista.PozycjaPlaylisty
        self.percentage = 0
        self.ktorykolwiek_wlaczony = False
        self.wzmacniacze = {}
        self.link = ''

    def biezacyStanDoTuple(self):
        return {
                constants.POLE_INTERKOM: self.interkom,
                constants.POLE_CZY_AKTUALNIE_GRA: self.czy_aktualnie_gra,
                constants.POLE_PAUZA: self.pauza,
                constants.POLE_TIMESTAMP_PLAYLISTY: self.ts_playlisty,
                constants.POLE_TIMESTAMP_ULUBIONYCH: self.ts_ulubionych,
                constants.POLE_TIMESTAMP_WZMACNIACZY: self.ts_wzmacniaczy,
                constants.POLE_TIMESTAMP_RADII: self.ts_radii,
                constants.POLE_TIMESTAMP_HISTORII: self.ts_historii,
                constants.POLE_TIMESTAMP_NAGLOSNIENIA: self.ts,
                constants.POLE_AKTUALNA_POZYCJA: self.aktualna_pozycja.pozycja_do_listy(),
                #TODO usunac pola link oraz tytul z biezacego stanu, sa w aktualnej pozycji
                constants.POLE_TYTUL: self.tytul, constants.POLE_CZY_GRA_DENON: self.czy_gra_denon,
                constants.POLE_TOTALTIME: self.totaltime, constants.POLE_CURRENTTIME: self.currenttime,
                constants.POLE_PERCENTAGE: self.percentage,
                #constants.TS: self.ts
                }

    #def biezacy_stan_odpowiedzV2(self):
    #    return THutils.skonstruuj_odpowiedzV2OK(constants.RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA,
    #                                            self.biezacyStanDoTuple())

    def wzmacniacze_stan_odpowiedzV2(self):
        return THutils.skonstruuj_odpowiedzV2OK(constants.RODZAJ_KOMUNIKATU_STAN_WZMACNIACZE,
                                                self.wzmacniacze, constants.OBSZAR_NAGL)

class Naglosnienie:
    def __init__(self, logger):
        self.logger = logger    #type: MojLogger
        self.obszar = constants.OBSZAR_NAGL
        self.logger.info(self.obszar, "Zaczynam inicjalizowac Naglosnienie.")

        self.wzmacniacze = wzmacniacze.Wzmacniacze(self.logger)
        self.odczytaj_konf()

        # self.glosnosc_przy_dzwonku = GLOSNOSC_PRZY_DZWONKU
        # self.czas_odczytu_konfiguracji = CZAS_ODCZYTU_KONFIGURACJI
        #self.plik_dzwonka = ''
        self.liryki = liriki.Liriki(self.logger, self.obszar)
        self.ic_trwa = False  # czy interkom jest aktywny
        self.IC_czy_gralo = False  # jesli przed interkomem gralo to True
        self.lock_aktualizacji_statusu = threading.Lock()
        self.aktualna_playlista = playlista.Playlista(self.obszar, self.logger, przy_starcie=True)
        self.ulub = ulubione.Ulubione(self.obszar, self.logger)
        self.czas_ostatniego_polecenia_odtwarzania = datetime.datetime.now()
        self.katalog_radii = radia.Radia(self.obszar, self.logger)
        self.katalog_radii.pobierz_radia_cyklicznie()
        self.biezacy_stan = BiezacyStan()
        self.licznik_delay_odswiezania = 0
        self._czas_maksymalnego_braku_aktywnosci = CZAS_WYLACZENIA_PO_NIEAKTYWNOSCI

        self.spoti = spotify_odtwarzacz.SpotifyOdtwarzacz(self.obszar, self.logger)
        self.kodi = Kodi.Kodi(self.logger, ADRES_KODI)
        self.odtwarzacz = self.kodi

        self.pauza = True
        self.czas_ostatniej_aktywnosci = datetime.datetime.now()

        #self.notyfikacja_firebase = firebasenotification.Firebasenotification()
        self.aktualizuj_status_odtwarzacza()
        self.aktualizuj_cyklicznie_stan_odtwarzacza()
        self.logger.info(self.obszar, 'Zakonczylem konstruktora klasy naglosnienie.')

    def procesuj_polecenie(self, **params):
        if constants.KOMENDA in params:
            if params[constants.KOMENDA] == constants.RODZAJ_KOMUNIKATU_ULUBIONE:
                return self.ulub.wyslij_ulubione()
            elif params[constants.KOMENDA] == constants.RODZAJ_KOMUNIKATU_KATALOG_RADII:
                return self.katalog_radii.wyslij_katalog_radii()
            elif params[constants.KOMENDA] == constants.RODZAJ_KOMUNIKATU_PLAYLISTA:
                return THutils.skonstruuj_odpowiedzV2OK(constants.RODZAJ_KOMUNIKATU_PLAYLISTA,
                                                        self.aktualna_playlista.wyslij_playliste(pelna=False), constants.OBSZAR_NAGL)
            elif params[constants.KOMENDA] == constants.RODZAJ_KOMUNIKATU_HISTORIA:
            # TODO liczba linii historii do parametrow
                poz = {constants.TS: self.biezacy_stan.ts_historii,
                      constants.POZYCJE: self.aktualna_playlista.odczytaj_historie()}
                return THutils.skonstruuj_odpowiedzV2OK(constants.RODZAJ_KOMUNIKATU_HISTORIA, poz, constants.OBSZAR_NAGL)
            elif params[constants.KOMENDA] == constants.RODZAJ_KOMUNIKATU_STAN_WZMACNIACZE:
                return THutils.skonstruuj_odpowiedzV2OK(constants.RODZAJ_KOMUNIKATU_STAN_WZMACNIACZE, self.wzmacniacze.do_listy(), constants.OBSZAR_NAGL)
            elif params[constants.KOMENDA] == constants.KOMENDA_GLOSNOSC_DELTA:  # wykorzystuje delte a nie bezwgledna wartosc glosnosci
                if constants.POLE_GLOSNOSC in params:
                    if constants.NAZWA in params:
                        if self.wzmacniacze.set_glosnosc_delta_nazwa(params[constants.NAZWA], int(params[constants.POLE_GLOSNOSC])):
                            self.kasuj_czas_ostatniej_aktywnosci()                        
                            #self.przekaz_stan_wzmacniaczy_do_garazu()
                            self.aktualizuj_status_odtwarzacza(wymus=True)
            elif params[constants.KOMENDA] == constants.KOMENDA_GLOSNOSC:
                if constants.POLE_GLOSNOSC in params:
                    if constants.NAZWA in params:
                        try:
                            if self.wzmacniacze.set_glosnosc_nazwa(params[constants.NAZWA], int(params[constants.POLE_GLOSNOSC])):
                                self.kasuj_czas_ostatniej_aktywnosci()
                                #self.przekaz_stan_wzmacniaczy_do_garazu()
                                self.aktualizuj_status_odtwarzacza(wymus=True)
                        except ValueError as serr:
                            self.logger.warning(self.obszar, 'Podano glosnosc nie jako liczbe: ' + str(params[constants.POLE_GLOSNOSC]) + ' dla wzmacniacza: ' +
                                                params[constants.NAZWA] + ". Blad: " + str(serr))
            elif params[constants.KOMENDA] == constants.KOMENDA_DZWONEK:
                self.logger.info(self.obszar, 'Dzwonek do drzwi.')
                if not self.ic_trwa:
                    threading.Thread(target=self.odtworz_z_pliku, args=(self.plik_dzwonka,)).start()
            elif params[constants.KOMENDA] == constants.RODZAJ_KOMUNIKATU_LIRYKI:
                # self.liryki.odczytaj_liryki(self.aktualna_playlista.aktualna_pozycja().artist,
                #                            self.aktualna_playlista.aktualna_pozycja().title)
                # if lir is not None:
                #    return THutils.skonstruuj_odpowiedzV2(constants.RODZAJ_KOMUNIKATU_LIRYKI, lir, constants.STATUS_OK)
                # else:
                #    return THutils.skonstruuj_odpowiedzV2(constants.RODZAJ_KOMUNIKATU_LIRYKI, '', constants.STATUS_NOK)
                return THutils.skonstruuj_odpowiedzV2OK(constants.RODZAJ_KOMUNIKATU_LIRYKI,
                                                        {constants.RODZAJ_KOMUNIKATU_LIRYKI: self.liryki.tekstPiosenki}, constants.OBSZAR_NAGL)
            #elif params[constants.KOMENDA] == 'SPOTIFY':
            #    if parametr1 == 'L+01':
            #        threading.Thread(target=self.aktualna_playlista.dodaj_z_linku_spotify, args=(parametr2,)).start()
                    #thread.start_new_thread(self.aktualna_playlista.dodaj_z_linku_spotify, (parametr2,))
            elif params[constants.KOMENDA] == 'ODTWARZAJ_SPOTIFY':
                if constants.POLE_WARTOSC in params:
                    threading.Thread(target=self.odtwarzaj_ze_spotify_uri, args=(params[constants.POLE_WARTOSC],)).start()
            elif params[constants.KOMENDA] == 'QUERY_SPOTIFY':
                if constants.QUERY in params:
                    if constants.NEXT in params:
                        spot = spotify_klasa.SpotifyKlasa(self.logger, self.obszar)
                        odp = spot.szukaj_zdalnie(params[constants.QUERY], next = params[constants.NEXT])
                        return THutils.skonstruuj_odpowiedzV2OK(constants.RODZAJ_KOMUNIKATU_SPOTIFY_QUERY, odp, constants.OBSZAR_NAGL)
            elif params[constants.KOMENDA] == 'SPOTIFY_NEXT':
                if constants.POLE_WARTOSC in params:
                    spot = spotify_klasa.SpotifyKlasa(self.logger, self.obszar)
                    odp = spot.nastepny(params[constants.POLE_WARTOSC])
                    return THutils.skonstruuj_odpowiedzV2OK(constants.RODZAJ_KOMUNIKATU_SPOTIFY_NEXT, odp, constants.OBSZAR_NAGL)
            elif params[constants.KOMENDA] == 'SPOTIFY_ROZWINIECIE':
                if constants.URI in params:
                    if constants.SPOTIFY_RODZAJ in params:
                        spot = spotify_klasa.SpotifyKlasa(self.logger, self.obszar)
                        odp = spot.rozwin(params[constants.SPOTIFY_RODZAJ], params[constants.URI])
                        return THutils.skonstruuj_odpowiedzV2OK(constants.RODZAJ_KOMUNIKATU_SPOTIFY_ROZWIN, odp, constants.OBSZAR_NAGL)
#            elif komenda == 'RO':
                #thread.start_new_thread(self.odtwarzaj_z_radii_po_nazwie, (parametr1, parametr2))
#                self.odtwarzaj_z_radii_po_nazwie(parametr1, parametr2)
            elif params[constants.KOMENDA] == 'RO_ID':
                if constants.POLE_NAZWA_SERVICU_RADIOWEGO in params:
                    if constants.POLE_ID_STACJI in params:
                        self.odtwarzaj_z_radii_po_id(params[constants.POLE_NAZWA_SERVICU_RADIOWEGO],
                                                     params[constants.POLE_ID_STACJI])
            elif params[constants.KOMENDA] == 'NAST':
                self.nastepny()
            elif params[constants.KOMENDA] == 'POPR':
                self.poprzedni()
            elif params[constants.KOMENDA] == 'GOTO':
                if constants.POLE_WARTOSC in params:
                    #threading.Thread(target=self.idz_do, args=(int(params[constants.POLE_WARTOSC]),)).start()
                    self.idz_do(int(params[constants.POLE_WARTOSC]))
                    self.aktualizuj_status_odtwarzacza(wymus=True)
            elif params[constants.KOMENDA] == 'rodzaj_odtwarzania':
                # 1 oznacza po kolei
                # 2 ozncza losowo
                if constants.POLE_WARTOSC in params:
                    self.aktualna_playlista.jak_odtwarza = int(params[constants.POLE_WARTOSC])
#            elif params[constants.KOMENDA] == 'LINK':
#                self.odtwarzaj_z_linku_zeruj_playliste(parametr2, '')
            elif params[constants.KOMENDA] == 'ULUB':
                # TODO sprawdzic ktore jeszcze mozna zrezygnowac z osobnego threadu
                if constants.POLE_WARTOSC in params:
                    self.odtwarzaj_ulubione_numer(int(params[constants.POLE_WARTOSC]))
                if constants.NAZWA in params:
                    self.odtwarzaj_ulubione_nazwa(params[constants.NAZWA])
            elif params[constants.KOMENDA] == 'ULU-':
                if constants.POLE_WARTOSC in params:
                    self.ulub.usun_ulubione(params[constants.POLE_WARTOSC])
            elif params[constants.KOMENDA] == 'ULU+':
                if constants.POLE_WARTOSC in params:
                    threading.Thread(target=self.dodaj_do_playlisty_z_ulubionego, args=(int(params[constants.POLE_WARTOSC]),)).start()
            #TODO numery ulucbioych a intami czy longami
            elif params[constants.KOMENDA] == 'HIST':
                if constants.HASH in params:
                    dodanie = False
                    if constants.POLE_STAN in params:
                        dodanie = params[constants.POLE_STAN]
                    threading.Thread(target=self.odtworz_z_historii, args=(params[constants.HASH],dodanie)).start()
            elif params[constants.KOMENDA] == 'LIS+':
                if constants.POLE_WARTOSC in params:
                    threading.Thread(target=self.ulub.zapisz_playliste_w_ulubionych,
                                     args=(self.aktualna_playlista, params[constants.POLE_WARTOSC])).start()
            elif params[constants.KOMENDA] == 'PLAY':
                if constants.POLE_WARTOSC in params:
                    self.logger.info(self.obszar, 'Odtwarzam z playlisty pozycje nr: ' + str(params[constants.POLE_WARTOSC]))
                    self.odtwarzaj_z_playlisty(nr_poz=int(params[constants.POLE_WARTOSC]))
            elif params[constants.KOMENDA] == 'L+01':
                if constants.POLE_WARTOSC in params:
                    threading.Thread(target=self.aktualna_playlista.dodaj_z_linku,
                                     args=(params[constants.POLE_WARTOSC], "")).start()
            elif params[constants.KOMENDA] == 'L-01':
                if constants.POLE_WARTOSC in params:
                    nr_pozycji = int(params[constants.POLE_WARTOSC])
                    if self.aktualna_playlista.usun_pozycje_z_playlisty(nr_pozycji):
                        self.odtwarzaj_z_playlisty()
            elif params[constants.KOMENDA] == 'WZ_TOGGLE':
                if constants.NAZWA in params:
                    self.toggle_wzmacniacz_nazwa(params[constants.NAZWA])
                    self.aktualizuj_status_odtwarzacza(wymus=True)
        self.aktualizuj_status_odtwarzacza()
        return THutils.skonstruuj_odpowiedzV2OK(constants.RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA,
                                                self.biezacy_stan.biezacyStanDoTuple(), constants.OBSZAR_NAGL)

    def odtworz_z_historii(self, hash_historii, dodaj=False):
        hist = self.aktualna_playlista.odczytaj_historie()
        poz = None
        for a in hist:
            if str(a[constants.HASH]) == str(hash_historii):
                poz = a
                break
        if poz:
            pozy = self.aktualna_playlista.pozycja_z_json(poz[constants.POZYCJA])
            if dodaj:
                self.logger.info(self.obszar, "Dodaje do playlisty z historii: " + str(poz[constants.POZYCJA]))
                self.aktualna_playlista.pozycje.append(pozy)
                self.aktualna_playlista.zapisz_playliste()
            else:
                self.logger.info(self.obszar, "Odtwarzam z historii: " + str(poz[constants.POZYCJA]))
                self.aktualna_playlista.zeruj()
                self.aktualna_playlista.pozycje.append(pozy)
                self.aktualna_playlista.zapisz_playliste()
                self.odtwarzaj_z_playlisty(zapisuj_historie=False)
        else:
            self.logger.warning(self.obszar, "Nie odnalazlem pozycji historii dla has: " + str(hash_historii))

    def odtworz_z_pliku(self, plik, usuwac_plik=False):
        self.ic_trwa = True
        # zapamietanie glosnosci i aktualnej pozycji
        self.logger.info(self.obszar, 'Odtwarzam z pliku: ' + str(plik))
        k_stan = self.wzmacniacze.wzmacniacz_po_nazwie(wzmacniacze.NAZWA_WZMACNIACZA_KUCHNIA).stan
        k_gl = self.wzmacniacze.wzmacniacz_po_nazwie(wzmacniacze.NAZWA_WZMACNIACZA_KUCHNIA).glosnosc
        l_stan = self.wzmacniacze.wzmacniacz_po_nazwie(wzmacniacze.NAZWA_WZMACNIACZA_LAZIENKA).stan
        l_gl = self.wzmacniacze.wzmacniacz_po_nazwie(wzmacniacze.NAZWA_WZMACNIACZA_LAZIENKA).glosnosc
        t_stan = self.wzmacniacze.wzmacniacz_po_nazwie(wzmacniacze.NAZWA_WZMACNIACZA_TARAS).stan
        t_gl = self.wzmacniacze.wzmacniacz_po_nazwie(wzmacniacze.NAZWA_WZMACNIACZA_TARAS).glosnosc
#        glosnosci = {}
#        for j in self.wzmacniacze.wzmacniacze:
#            glosnosci.append(j)
        #for j in self.wzmacniacze.wzmacniacze:
        #    glosnosci.append(j.glosnosc)

        percent = int(self.odtwarzacz.percentage)

        # IC_czy_gralo - jesli True to znaczy, ze poprzednio gralo i mamy wznowic
        self.IC_czy_gralo = self.wzmacniacze.czy_ktorykolwiek_wlaczony()
        self.logger.warning(self.obszar, 'IC-zlecam stop')
        self.stop()
        #self.pauza()
        licznik = 0
        while self.odtwarzacz.aktualnie_gra:
            self.logger.warning(self.obszar, 'IC-jeszcze gra czekam w loopie, do skutku')
            self.odtwarzacz.aktualizuj_stan()
            time.sleep(0.5)
            licznik = licznik + 1
            if licznik > 100:
                self.logger.warning(self.obszar, 'IC-licznik przy STOP sie przekrecil')
                break
        #while odtwarzacz gra to czekamy i liczymy do stu albo wiecej, bez timesleep
        self.logger.warning(self.obszar, 'IC-podmieniam odtwarzacz na KODI')
        self.odtwarzacz = self.kodi


        # ustawienie wlaczenia wszystkich wzmacniaczy i ich glosnosci
        for j in self.wzmacniacze.wzmacniacze:
            j.ustaw_glosnosc(self.glosnosc_przy_dzwonku)
        self.wzmacniacze.wlacz_wylacz_wszystkie(True)

        # odtwarzanie za pomoca kodi, zakladamy, ze kodi jest juz ustawione jako odtwarzacz
        self.odtwarzacz.odtwarzaj_z_linku(plik)
        self.odtwarzacz.aktualnie_gra = True
        licznik = 0
        self.logger.warning(self.obszar, 'IC-rozpoczynam loop czekania az skonczy odtwarzac')
        while self.odtwarzacz.aktualnie_gra:
            licznik = licznik + 1
            if licznik > 100:
                self.logger.warning(self.obszar, 'IC-licznik przy odtwarzaniu sie przekrecil')
                break
            time.sleep(2)
            self.odtwarzacz.aktualizuj_stan()
        self.logger.warning(self.obszar, 'IC-zakonczylem loop czekania na odwtorzenie dzownka')

        # usuniecie pliku z interkomem
        if usuwac_plik:
            os.remove(plik)

        # odtworzenie stanu przekaznikow i glosnosci
        '''self.wzmacniacze.wlacz_wylacz_wszystkie(False)
        a = 0
        for j in self.wzmacniacze.wzmacniacze:
            j.ustaw_glosnosc(glosnosci[a])
            a = a + 1'''
        self.wzmacniacze.wzmacniacz_po_nazwie(wzmacniacze.NAZWA_WZMACNIACZA_KUCHNIA).wlacz_wylacz(k_stan)
        self.wzmacniacze.set_glosnosc_nazwa(wzmacniacze.NAZWA_WZMACNIACZA_KUCHNIA, k_gl)
        self.wzmacniacze.wzmacniacz_po_nazwie(wzmacniacze.NAZWA_WZMACNIACZA_TARAS).wlacz_wylacz(t_stan)
        self.wzmacniacze.set_glosnosc_nazwa(wzmacniacze.NAZWA_WZMACNIACZA_TARAS, t_gl)
        self.wzmacniacze.wzmacniacz_po_nazwie(wzmacniacze.NAZWA_WZMACNIACZA_LAZIENKA).wlacz_wylacz(l_stan)
        self.wzmacniacze.set_glosnosc_nazwa(wzmacniacze.NAZWA_WZMACNIACZA_LAZIENKA, l_gl)

        if self.IC_czy_gralo:
            self.logger.warning(self.obszar, 'IC-gralo poprzednio, odtwarzam z playlisty')
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

    #def zwroc_status_arduino(self, nazwa):
    #    if self.wzmacniacze.stan_wzmacniacza_po_nazwie(nazwa):
    #        a = '1'
    #    else:
    #        a = '0'
    #    return 'S' + a + \
    #           'G' + str("{0:0=3d}".format(self.wzmacniacze.wzmacniacz_po_nazwie(nazwa).glosnosc))

    def aktualizuj_cyklicznie_stan_odtwarzacza(self):
        #TODO ten licznik_delay nie jest potrzebny
        if self.licznik_delay_odswiezania == LICZBA_ODSWIEZEN_DO_STATUSU:
            self.licznik_delay_odswiezania = 0
        else:
            self.licznik_delay_odswiezania += 1

        if self.wzmacniacze.czy_ktorykolwiek_wlaczony():
            self.licznik_delay_odswiezania = 0

        if self.licznik_delay_odswiezania == 0:
            self.aktualizuj_status_odtwarzacza()

        # odtwarzanie kolejnego utworu
        if not self.ic_trwa:
            # TODO pauza powinna byc jednoznaczna z ktorykolwiek wlaczony=false
            if self.wzmacniacze.czy_ktorykolwiek_wlaczony() and self.pauza is False:
                if not self.odtwarzacz.aktualnie_gra:
                    # delta ma sluzyc temu aby co 0,5 sekundy nie probowac kazac kodi odtwarzac tego samego
                    delta = datetime.datetime.now() - self.czas_ostatniego_polecenia_odtwarzania
                    if delta.total_seconds() > CZAS_PRZERWY_MIEDZY_PROBAMI_ODTWARZANIA:
                        self.aktualna_playlista.oblicz_kolejny_do_grania()
                        threading.Thread(target=self.odtwarzaj_z_playlisty).start()
                #for j in self.wzmacniacze.wzmacniacze:
                #    j.ustaw_glosnosc(j.glosnosc)

        self.automatyczne_wylaczanie_przy_braku_aktywnosci()
        threading.Timer(CZAS_ODSWIEZANIA_STANU_ODTWARZACZA, self.aktualizuj_cyklicznie_stan_odtwarzacza).start()

    def przekaz_stan_naglosnienia_do_garazu(self):
        THutils.przekaz_polecenie_V2_JSONRPC(constants.get_HOST_I_PORT_GARAZ_v2(),
                                             constants.OBSZAR_NAGL, self.logger,
                                             {constants.RODZAJ_KOMUNIKATU: constants.RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA,
                                              constants.RESULT: self.biezacy_stan.biezacyStanDoTuple()})

    #def przekaz_stan_wzmacniaczy_do_garazu(self):
    #    self.biezacy_stan.ts_wzmacniaczy = self.wzmacniacze.ts
    #    THutils.przekaz_polecenie_V2_JSONRPC(constants.get_HOST_I_PORT_GARAZ_v2(),
    #                                         constants.OBSZAR_STAT, self.logger,
    #                                         {constants.RODZAJ_KOMUNIKATU: constants.RODZAJ_KOMUNIKATU_STAN_WZMACNIACZE,
    #                                         constants.RESULT: self.wzmacniacze.do_listy()})
    #    #self.przekaz_stan_naglosnienia_do_garazu()

    def aktualizuj_status_odtwarzacza(self, wymus=False):  #, force_kodi=False):
        if self.ic_trwa:
            self.logger.warning(self.obszar, 'Nie aktualizuje stanu odtwarzacza bo trwa IC')
            return
        fire = wymus
        self.lock_aktualizacji_statusu.acquire()
        poprzedni_stan = deepcopy(self.biezacy_stan)
        self.odtwarzacz.aktualizuj_stan()

        self.biezacy_stan.wzmacniacze = self.wzmacniacze.do_listy()
        self.biezacy_stan.interkom = self.ic_trwa
        self.biezacy_stan.czy_aktualnie_gra = self.odtwarzacz.aktualnie_gra
        self.biezacy_stan.pauza = self.pauza
        self.biezacy_stan.nazwa_playlisty = self.aktualna_playlista.nazwa
        self.biezacy_stan.liczba_pozycji_playlisty = self.aktualna_playlista.liczba_pozycji()
        self.biezacy_stan.ts_playlisty = self.aktualna_playlista.ts
        self.biezacy_stan.ts_ulubionych = self.ulub.ts
        self.biezacy_stan.ts_wzmacniaczy = self.wzmacniacze.ts
        self.biezacy_stan.ts_radii = self.katalog_radii.ts
        self.biezacy_stan.ts_historii = self.aktualna_playlista.ts_historii

        #odczytanie tytulu z Kodi albo z drugiego odtwarzacza
        tytul = ''
        poz = self.aktualna_playlista.aktualna_pozycja()    # type: playlista.PozycjaPlaylisty
        if poz is not None:
            # TODO czy nie mozna przejsc zawsze na self.odtwarzacz.tytul?
            if poz.typ == playlista.TYP_RADIO:
                if poz.serwis_radiowy == radia.NAZWA_SERWISU_OPENFM:
                    if poz.ts_stop < time.time()*1000:
                        if self.wzmacniacze.czy_ktorykolwiek_wlaczony():
                            artysta, album, tytul_utworu, ts_konca = self.katalog_radii.odswiez_co_grane_openfm(poz.id_stacji_radiowej)
                            poz.album = album
                            poz.artist = artysta
                            poz.title = tytul_utworu
                            tytul = tytul_utworu
                            # kontrola nie za czestego odczytywania co grane
                            if ts_konca < time.time()*1000:
                                poz.ts_stop = time.time()*1000 + radia.INTERWAL_ODCZYTU_CO_GRANE
                            else:
                                poz.ts_stop = ts_konca
                else:
                    tytul = self.odtwarzacz.tytul
            else:
                tytul = THutils.xstr(poz.title)
            self.biezacy_stan.aktualna_pozycja = poz
            self.biezacy_stan.nazwa_playlisty = self.aktualna_playlista.nazwa

        #TODO ta zmienna do usuniecia w API i androdi
        self.biezacy_stan.czy_gra_denon = False
        self.biezacy_stan.totaltime = self.odtwarzacz.totaltime
        self.biezacy_stan.currenttime = self.odtwarzacz.currenttime
        self.biezacy_stan.percentage = self.odtwarzacz.percentage
        self.biezacy_stan.ktorykolwiek_wlaczony = self.wzmacniacze.czy_ktorykolwiek_wlaczony()
        
        if self.biezacy_stan.tytul != tytul:
            if not self.ic_trwa:
                self.biezacy_stan.tytul = tytul
                fire = True
        else:
            self.biezacy_stan.tytul = tytul
        try:
            link = self.aktualna_playlista.aktualna_pozycja().link
        except AttributeError:
            link = ''
        try:
            if self.biezacy_stan.link != link:
                if not self.ic_trwa:
                    fire = True
        except AttributeError:
            self.logger.warning(self.obszar, "Brak sekcji [aktualna_pozycja]: " + str(self.biezacy_stan.aktualna_pozycja.pozycja_do_listy()))
        self.biezacy_stan.link = link
        
        #resetowanie ts tylko kiedy stan rozni sie od poprzedniego, wybrane elementy
        if self.biezacy_stan.czy_aktualnie_gra != poprzedni_stan.czy_aktualnie_gra:
            fire = True
        if self.biezacy_stan.tytul != poprzedni_stan.tytul:
            fire = True
        if self.biezacy_stan.totaltime != poprzedni_stan.totaltime:
            fire = True
        #if self.biezacy_stan.ktorykolwiek_wlaczony != poprzedni_stan.ktorykolwiek_wlaczony:
        #    fire = True
        #if self.biezacy_stan.wzmacniacze != poprzedni_stan.wzmacniacze:
        #    fire = True
        if self.biezacy_stan.nazwa_playlisty != poprzedni_stan.nazwa_playlisty:
            fire = True
        #if self.biezacy_stan.liczba_pozycji_playlisty != poprzedni_stan.liczba_pozycji_playlisty:
        #    fire = True
        if self.biezacy_stan.ts_playlisty != poprzedni_stan.ts_playlisty:
            fire = True
        if self.biezacy_stan.ts_ulubionych != poprzedni_stan.ts_ulubionych:
            fire = True
        if self.biezacy_stan.ts_radii != poprzedni_stan.ts_radii:
            fire = True
        if self.biezacy_stan.ts_historii != poprzedni_stan.ts_historii:
            fire = True
        
        #if poprzedni_stan.biezacyStanDoTuple() != self.biezacy_stan.biezacyStanDoTuple():
        #    self.biezacy_stan.ts = int(time.time())
        #    self.przekaz_stan_naglosnienia_do_garazu()

        if fire:
            self.biezacy_stan.ts = time.time()*1000
            self.przekaz_stan_naglosnienia_do_garazu()

        #if self.biezacy_stan.ts_wzmacniaczy != poprzedni_stan.ts_wzmacniaczy:
        #    self.biezacy_stan.ts = int(time.time())

        self.lock_aktualizacji_statusu.release()

    def odtwarzaj_ulubione_numer(self, numer_ulubionego):
        ul = self.ulub.ulubiony_po_numerze(numer_ulubionego)
        if not ul:
            self.logger.warning(self.obszar, 'Odtwarzaj-ulub_numer, nie ma takiego numeru: ' +
                                str(numer_ulubionego))
            return
        self.kasuj_czas_ostatniej_aktywnosci()
        self.stop()
        self.aktualna_playlista.inicjalizuj_playliste_z_pliku(ul.get_plik())
        self.odtwarzaj_z_playlisty(0)
        self.logger.info(self.obszar, 'Odtwarzam ulubione nr: ' + str(numer_ulubionego) +
                         " : " + ul.get_nazwa())

    def odtwarzaj_ulubione_nazwa(self, nazwa_ulubionego):
        ul = self.ulub.ulubiony_po_nazwie(nazwa_ulubionego)
        if not ul:
            self.logger.warning(self.obszar, 'Odtwarzaj-ulub_numer, nie ma takiego numeru: ' +
                                str(nazwa_ulubionego))
            return
        self.kasuj_czas_ostatniej_aktywnosci()
        self.stop()
        self.aktualna_playlista.inicjalizuj_playliste_z_pliku(ul.get_plik())
        self.odtwarzaj_z_playlisty(0)
        self.logger.info(self.obszar, 'Odtwarzam ulubione nr: ' + str(nazwa_ulubionego))

    def dodaj_do_playlisty_z_ulubionego(self, numer_ulubionego):
        ul = self.ulub.ulubiony_po_numerze(numer_ulubionego)
        if not ul:
            self.logger.warning(self.obszar, 'Dodaj-ulub_numer, nie ma takiego numeru: ' +
                                str(numer_ulubionego))
            return
        #if ul.typ == playlista.TYP_RADIO:
        #    return
        self.kasuj_czas_ostatniej_aktywnosci()
        self.aktualna_playlista.inicjalizuj_playliste_z_pliku(ul.get_plik(), zeruj=False)

    def odtwarzaj_z_radii_po_id(self, nazwa_serwisu, idstacji):
        self.logger.info(self.obszar, 'Odtwarzam z radii: ' + nazwa_serwisu + ' ' + str(idstacji))
        a = self.katalog_radii.znajdz_stacje_po_nazwie_i_id(nazwa_serwisu, idstacji)
        if not a:
            self.logger.warning(self.obszar, 'Nie odnalazlem takiego radia po id: ' + nazwa_serwisu + ' ' + idstacji)
            return
        self.odtwarzaj_z_radii(a)

    def odtwarzaj_z_radii_po_nazwie(self, nazwa_serwisu, nazwa_stacji):
        self.logger.info(self.obszar, 'Odtwarzam z radii: ' + nazwa_serwisu + ' ' + nazwa_stacji)
        a = self.katalog_radii.znajdz_stacje_po_nazwie_i_serwisie(nazwa_serwisu, nazwa_stacji)
        if not a:
            self.logger.warning(self.obszar, 'Nie odnalazlem takiego radia: ' + nazwa_serwisu + ' ' + nazwa_stacji)
            return
        self.odtwarzaj_z_radii(a)

    def odtwarzaj_z_radii(self, radio):
        # radio to stacja radiowa
        self.stop()
        self.aktualna_playlista.zeruj()
        self.aktualna_playlista.nazwa = radio.nazwa_serwisu + ' - ' + radio.nazwa_radia
        ts_konca = 0
        link = radio.link
        artysta = album = ''
        if radio.nazwa_serwisu == radia.NAZWA_SERWISU_TUNEIN:
            link = self.katalog_radii.tunein_dekoduj_stream_stacji(radio.link)
        #elif radio.nazwa_serwisu == radia.NAZWA_SERWISU_OPENFM:
            # zwraca artyste, album, tytul oraz timestamp konca
        #    artysta, album, tytul, ts_konca = self.katalog_radii.odswiez_co_grane_openfm(int(radio.id_radia))
        self.aktualna_playlista.dodaj_pozycje_z_polami(artist=artysta, album=album, title=radio.nazwa_radia,
                                                       link=link, typ=playlista.TYP_RADIO, fanart=radio.logo,
                                                       serwis_radiowy=radio.nazwa_serwisu,
                                                       stacja_radiowa=radio.nazwa_radia,
                                                       id_stacji_radiowej=radio.id_radia,
                                                       ts_konca=ts_konca)
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
        #self.kasuj_czas_ostatniej_aktywnosci()
        self.czas_ostatniego_polecenia_odtwarzania = datetime.datetime.now()
        self.pauza = not self.pauza

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
        self.odtwarzacz.idz_do(czas)

    def stop(self):
        self.kasuj_czas_ostatniej_aktywnosci()
        self.odtwarzacz.stop()

    def odtwarzaj_z_playlisty(self, nr_poz=None, zapisuj_historie=True):
        if self.aktualna_playlista.liczba_pozycji() == 0:
            self.logger.warning(self.obszar, 'odtwarzaj z plalisty: pusta playlista')
            return

        if nr_poz is not None:
            self.aktualna_playlista.nr_pozycji_na_playliscie = nr_poz

        if zapisuj_historie:
            try:
                self.aktualna_playlista.zapisz_w_historii(
                    self.aktualna_playlista.pozycje[self.aktualna_playlista.nr_pozycji_na_playliscie])
            except IndexError:
                pass
        self.czas_ostatniego_polecenia_odtwarzania = datetime.datetime.now()
        self.podmien_odtwarzacz()
        self.odtwarzacz.odtwarzaj_z_linku(self.aktualna_playlista.aktualnie_grane_link())
        self.aktualna_playlista.zapisz_playliste()
        if isinstance(self.odtwarzacz, spotify_odtwarzacz.SpotifyOdtwarzacz):
            artysta = self.aktualna_playlista.aktualna_pozycja().artist
            piosenka = self.aktualna_playlista.aktualna_pozycja().title
            threading.Thread(target=self.liryki.odczytaj_liryki, args=(artysta, piosenka)).start()

    def podmien_odtwarzacz(self):
        if self.aktualna_playlista.aktualna_pozycja() is not None:
            if self.aktualna_playlista.aktualna_pozycja().typ == playlista.TYP_SPOTIFY:
                self.spoti.aktualizuj_stan()
                self.odtwarzacz = self.spoti
                self.logger.warning(self.obszar, 'podmienilem odtwarzacz na spotify')
            else:
                self.kodi.aktualizuj_stan()
                self.odtwarzacz = self.kodi
                self.logger.warning(self.obszar, 'podmienilem odtwarzacz na kodi')

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
        if self.wzmacniacze.toggle_wzmacniacz_nazwa(nazwa):
            self.ts = time.time()*1000
            self.kasuj_czas_ostatniej_aktywnosci()
            
            # pauza jesli wszystko beda wylaczone
            if self.wzmacniacze.czy_ktorykolwiek_wlaczony():
                if self.pauza:
                    self.play_pause()
            else:        
                self.play_pause()
            self.aktualizuj_status_odtwarzacza(wymus=True)

    def automatyczne_wylaczanie_przy_braku_aktywnosci(self):
        roznica = datetime.datetime.now() - self.czas_ostatniej_aktywnosci
        if roznica.total_seconds() > self._czas_maksymalnego_braku_aktywnosci:
            if self.wzmacniacze.czy_ktorykolwiek_wlaczony():
                self.wzmacniacze.wlacz_wylacz_wszystkie(False)  # wylacz_wszystkie_wzmacniacze()
                self.play_pause()
                self.aktualizuj_status_odtwarzacza()
                self.logger.info(self.obszar, 'Wylaczam wzmacn przy braku aktywnosci. Czas ostatn aktywn: ' +
                                 str(self.czas_ostatniej_aktywnosci))
        # threading.Timer(CZAS_SPRAWDZANIA_OSTATNIEJ_AKTYWNOSCI,
        #                self.automatyczne_wylaczanie_przy_braku_aktywnosci).start()

