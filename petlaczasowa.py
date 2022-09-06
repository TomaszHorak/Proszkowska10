from __future__ import print_function
import datetime
import time
from random import getrandbits

import constants
import json
import THutils
import threading
from MojLogger import MojLogger

CZAS_URUCHOMIENIA_PETLI = 1.5
PLIK_Z_CYKLAMI = '/cykle.ini'

# TODO jednorazowy nie ma patrzec na dni, miesiace tylko jak jest zadany to odlicza brakujace sekundy
class PetlaCzasowa:
    def __init__(self, logger):
        self._logger = logger #type: MojLogger
        self._tabela = []
        self._petla_w_trakcie_przebiegu = threading.Lock()  # jesli tru to blokuj dodawanie
        self._odczytaj_cykle_z_konfiguracji()
        # self._odczytaj_cykle_z_konfiguracji_cyklicznie()
        # self._petlaStart()

    def rejestruj_dzialanie(self, obszar, dzialanie):
        for a in self._tabela:
            if a.get_obszar() == obszar:
                a.rejestruj_dzialanie(dzialanie)

    def pozycja_po_obszarze_nazwie(self, obszar, nazwa):
        # TODO zwraca pierwsza pozycje, ale nie wedlug czasu startu
        for a in self._tabela:  # type: PozycjaPetli
            if a.get_nazwa() == nazwa:
                if a.get_obszar() == obszar:
                    return a
        return None

    def __interwalowy_dzialaj(self, a ):
        teraz = int(time.time())
        roznica_czasu = teraz - a._ts_zalaczenia_interwalu

        if a.get_stan():
            if roznica_czasu >= a.get_czas_zalaczenia_w_interwalowym():
                # nalezy wylaczyc
                a._dzialalem_w_poprzednim_przebiegu = True
                a._ts_zalaczenia_interwalu = teraz
                a._dzialaj_na_pozycji(False)
        else:
            if roznica_czasu >= a.get_czas_przerwy_miedzy_interwalami():
                # nalezy wlaczyc
                a._ts_zalaczenia_interwalu = teraz
                a._dzialalem_w_poprzednim_przebiegu = True
                a._dzialaj_na_pozycji(True)
        return

    def petlaStart(self):
        self._petla_w_trakcie_przebiegu.acquire()
        if len(self._tabela) > 0:
            for a in self._tabela:  # type: PozycjaPetli
                if a.is_active():
                    if a._czy_czas_pasuje():
                        if a.get_czas_zalaczenia_w_interwalowym() > 0:
                            self.__interwalowy_dzialaj(a)
                        else:
                            if not a.get_stan():
                                if not a._dzialalem_w_poprzednim_przebiegu:
                                    a._dzialaj_na_pozycji(True)
                                    a._dzialalem_w_poprzednim_przebiegu = True
                    else:
                        a._dzialalem_w_poprzednim_przebiegu = False
                        if a.get_czy_jednorazowy():
                            #TODO sprawdzi kiedy_koniec czy na pewno obsluguje tsstart i stop i godziny
                            #TODO statla typ jednorazwoy permanty do usuniecia
                            if a.get_kiedy_koniec() <= int(time.time()):
                                self._usun_z_tabeli_nazwa_jednorazzowy_w_przebiegu(a.get_nazwa())
                        if a.get_stan():
                            a._dzialaj_na_pozycji(False)

                else:
                    if a.get_czy_jednorazowy():
                        self._usun_z_tabeli_nazwa_jednorazzowy_w_przebiegu(a.get_nazwa())
                    if a.get_stan():
                        a._dzialaj_na_pozycji(False)

                # if a.get_czas_do_konca() != 0:
                #    if a.get_stan():
                #        a._dzialaj_na_pozycji(False, tylko_aktualizuj_ts=True)

        self._petla_w_trakcie_przebiegu.release()
        t = threading.Timer(CZAS_URUCHOMIENIA_PETLI, self.petlaStart)
        t.start()

    def usun_cykl_po_hashu(self, hash):
        self._petla_w_trakcie_przebiegu.acquire()
        for i in range(len(self._tabela) - 1, -1, -1):
            if str(self._tabela[i].get_hash()) == hash:
                del self._tabela[i]
        self._zapisz_cykle_w_konfiguracji()
        self._petla_w_trakcie_przebiegu.release()

    def dodaj_nowy_cykl(self, poz, dzialanie):
        p = self.pozycja_z_json(poz)  # type: PozycjaPetli
        if not p:
            self._logger.warning(constants.OBSZAR_PETLA, 'Nie moge stworzyc nowego cyklu: ' + str(poz))
            return
        p.rejestruj_dzialanie(dzialanie)
        p._hash = getrandbits(32)
        self._petla_w_trakcie_przebiegu.acquire()
        self._tabela.append(p)
        self._zapisz_cykle_w_konfiguracji()
        self._petla_w_trakcie_przebiegu.release()

    def dzialaj_na_wszystkich_pozycjach(self, obszar, stan):
        self._petla_w_trakcie_przebiegu.acquire()
        for a in self._tabela:
            if a.get_obszar == obszar:
                a._dzialaj_na_pozycji(stan)
        self._petla_w_trakcie_przebiegu.release()

    def aktualizuj_pozycje(self, poz):
        # poz jest typu tuple bo pochodzi z API
        p = self.pozycja_z_json(poz)  # type: PozycjaPetli
        if not p:
            self._logger.warning(constants.OBSZAR_PETLA,
                               'Chciano zaktualizowac pozycje petli ale byla pusta')
            return
        self._petla_w_trakcie_przebiegu.acquire()
        czy_byla_aktualizacja = False
        for a in self._tabela:  # type: PozycjaPetli
            if a.get_hash() == p.get_hash():
                try:
                    a._godz_wl = p._godz_wl
                    a._godz_wyl = p._godz_wyl
                    a._minu_wl = p._minu_wl
                    a._minu_wyl = p._minu_wyl
                    a._sek_wl = p._sek_wl
                    a._sek_wyl = p._sek_wyl
                    a._miesiace = p._miesiace
                    a._dni = p._dni
                    a._czas_przerwy_miedzy_interwalami = p._czas_przerwy_miedzy_interwalami
                    a._czas_zalaczenia_w_interwalowym = p._czas_zalaczenia_w_interwalowym
                    a._wartosc = p.get_wartosc()
                    a.aktywuj(p.is_active())
                    a.resetuj_ts()
                    self._zapisz_cykle_w_konfiguracji()
                    czy_byla_aktualizacja = True
                except (KeyError, AttributeError) as serr:
                    self._logger.warning(constants.OBSZAR_PETLA,
                                       'Brak klucza w poleceniu zmiany cykli: ' + str(serr))
        if not czy_byla_aktualizacja:
            self._logger.warning(constants.OBSZAR_PETLA, 'Probowano zaktualizowac cykl ale sie nie udalo: ' + str(poz))
        self._petla_w_trakcie_przebiegu.release()
        return czy_byla_aktualizacja
    '''    def dodaj_jednorazowy_na_czas_od_teraz(self, nazwa, czas, obszar='', dzialanie=None, wartosc=0):
        # uzywamy ts_start i ts_stop a nie godzin
        self._petla_w_trakcie_przebiegu.acquire()
        tim = int(time.time())
        self._tabela.append(PozycjaPetli(nazwa, obszar=obszar,
                                         ts_start=tim, ts_stop=tim + czas,
                                         aktywne=True, wartosc=wartosc, dzialanie=dzialanie))
        self._zapisz_cykle_w_konfiguracji()
        self._petla_w_trakcie_przebiegu.release()'''

    def dodaj_jednorazowy_od_godz_do_godz(self, nazwa, obszar, ts_start, ts_stop, dzialanie=None, wartosc=0):
        self._petla_w_trakcie_przebiegu.acquire()
        self._tabela.append(PozycjaPetli(nazwa, obszar=obszar, ts_start=ts_start,
                                         ts_stop=ts_stop, aktywne=True, wartosc=wartosc, dzialanie=dzialanie))
        self._logger.info(constants.OBSZAR_PETLA, 'Dodaje jednorazowy z TSami, obszar ' +
                           obszar + ', nazwa ' + nazwa + ' ' + str(ts_start) + ' ' + str(ts_stop))
        self._zapisz_cykle_w_konfiguracji()
        self._petla_w_trakcie_przebiegu.release()

    def _odczytaj_cykle_z_konfiguracji(self):
        # if not self.obszar:
        #    self.logger.warning('Pusty obszar przy odczycie cykli z konfiguracji.')
        result = THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_PETLA,
                                                        'cykle',
                                                        plik=PLIK_Z_CYKLAMI)
        try:
            c = json.loads(result)
        except Exception as e:
            self._logger.warning(constants.OBSZAR_PETLA, 'Nie potrafie odczytac cykli ' + ' :' + str(e))
            return

        self._petla_w_trakcie_przebiegu.acquire()
        try:
            for item in c:
                if constants.PETLA_DNI in item:
                    dni = item[constants.PETLA_DNI]
                else:
                    dni = None
                if constants.PETLA_MIESIACE in item:
                    miesiace = item[constants.PETLA_MIESIACE]
                else:
                    miesiace = None

                #interwaly
                czas_interwalu = 0
                czas_miedzy_interwalami = 0
                try:
                    czas_interwalu = item[constants.PETLA_CZAS_INTERWALU]
                    czas_miedzy_interwalami = item[constants.PETLA_CZAS_MIEDZY_INTERWALAMI]
                except (KeyError, AttributeError) as serr:
                    self._logger.warning(constants.OBSZAR_PETLA,
                                       'Brak klucza w odczycie cykli: ' + str(serr))

                hash = 0
                try:
                    hash = item[constants.HASH]
                except (KeyError, AttributeError) as serr:
                    self._logger.warning(constants.OBSZAR_PETLA,
                                       'Brak klucza w odczycie cykli: ' + str(serr))
                try:
                    wartosc = item[constants.PETLA_WARTOSC]
                except (KeyError, AttributeError) as serr:
                    wartosc = 0

                try:
                    ts_start = item[constants.PETLA_TS_START]
                    #ts_stop = item[constants.PETLA_TS_STOP]
                except (KeyError, AttributeError) as serr:
                    ts_start = 0
                    ts_stop = 0

                self._tabela.append(
                    PozycjaPetli(item[constants.PETLA_NAZWA],
                                 obszar=item[constants.OBSZAR],
                                 #typ=item[constants.PETLA_TYP],
                                 godz_wl=item[constants.PETLA_GODZ_WL],
                                 minu_wl=item[constants.PETLA_MINU_WL],
                                 sek_wl=item[constants.PETLA_SEK_WL],
                                 godz_wyl=item[constants.PETLA_GODZ_WYL],
                                 minu_wyl=item[constants.PETLA_MINU_WYL],
                                 sek_wyl=item[constants.PETLA_SEK_WYL],
                                 aktywne=item[constants.PETLA_AKTYWNE],
                                 dni=dni,
                                 miesiace=miesiace,
                                 czas_interwalu=czas_interwalu,
                                 czas_miedzy_interwalami=czas_miedzy_interwalami,
                                 hash=hash,
                                 ts_start=ts_start,
                                 #ts_stop=ts_stop,
                                 wartosc=wartosc))
        except AttributeError as serr:
            self._logger.warning(constants.OBSZAR_PETLA,
                               'Blad procesowania cykli: ' + '. ' + str(serr))

        self._petla_w_trakcie_przebiegu.release()
        self._logger.info(constants.OBSZAR_PETLA, 'Odswiezylem cykle.')

    def _zapisz_cykle_w_konfiguracji(self):
        result = json.dumps(self.pozycje_do_listy())
        THutils.zapisz_parametr_konfiguracji(constants.OBSZAR_PETLA,
                                             constants.OBSZAR_KONFIGURACJI_CYKLE, result, self._logger,
                                             plik=PLIK_Z_CYKLAMI)

    def _usun_z_tabeli_nazwa_jednorazzowy_w_przebiegu(self, nazwa):
        # zabezpieczone aby usuwalo wylaczznie jednorazowe
        for i in range(len(self._tabela) - 1, -1, -1):
            if self._tabela[i].get_nazwa() == nazwa:
                if self._tabela[i].get_czy_jednorazowy():
                    del self._tabela[i]
        self._zapisz_cykle_w_konfiguracji()


    def aktywuj_pozycje_nazwa(self, obszar, nazwa, stan, tylko_jednorazowe=False):
        for a in self._tabela:
            if a.get_obszar() == obszar:
                if a.get_nazwa() == nazwa:
                    if tylko_jednorazowe:
                        if a.get_czy_jednorazowy():
                            a.aktywuj(stan)
                    else:
                        a.aktywuj(stan)
        self._zapisz_cykle_w_konfiguracji()

    def aktywuj_pozycje_hash(self, hash, stan):
        for a in self._tabela:
            if a.get_hash() == hash:
                a.aktywuj(stan)
                self._zapisz_cykle_w_konfiguracji()

    def aktywuj_wszystkie_pozycja_w_obszarze(self, obszar, stan):
        for a in self._tabela:
            if a.get_obszar() == obszar:
                a.aktywuj(stan)

    def pozycje_do_listy(self, obszar='', wylacznie_permanetne=False, odbiornik_pomieszczenie=None):
        pozycje = []
        for j in self._tabela:  # type: PozycjaPetli
            if j.get_obszar() == obszar or obszar == '':
                if wylacznie_permanetne:
                    if not j.get_czy_jednorazowy():
                        if odbiornik_pomieszczenie:
                            if j.get_nazwa() == odbiornik_pomieszczenie:
                                pozycje.append(j._do_listy())
                        else:
                            pozycje.append(j._do_listy())
                else:
                    if odbiornik_pomieszczenie:
                        if j.get_nazwa() == odbiornik_pomieszczenie:
                            pozycje.append(j._do_listy())
                    else:
                        pozycje.append(j._do_listy())
        return pozycje

    def pozycja_z_json(self, poz):
        #poz = json.loads(pozy)
        try:
            nazwa = poz[constants.PETLA_NAZWA]
            obszar = poz[constants.OBSZAR]
            #typ = poz[constants.PETLA_TYP]
            aktywne = poz[constants.PETLA_AKTYWNE]
        except (KeyError, AttributeError) as serr:
            self._logger.warning(constants.OBSZAR_PETLA, 'Petla: brak klucza w pozycje_z_json: ' + str(serr))
            return None
        try:
            godz_wl = poz[constants.PETLA_GODZ_WL]
            godz_wyl = poz[constants.PETLA_GODZ_WYL]
            minu_wl = poz[constants.PETLA_MINU_WL]
            minu_wyl = poz[constants.PETLA_MINU_WYL]
            sek_wl = poz[constants.PETLA_SEK_WL]
            sek_wyl = poz[constants.PETLA_SEK_WYL]
            miesiace = poz[constants.PETLA_MIESIACE]
            dni = poz[constants.PETLA_DNI]
        except (KeyError, AttributeError) as serr:
            godz_wl = 0
            godz_wyl = 0
            minu_wl = 0
            minu_wyl = 0
            sek_wl = 0
            sek_wyl = 0
            miesiace = []
            dni = []

        try:
            czas_przerwy_miedzy_interwalami = poz[constants.PETLA_CZAS_MIEDZY_INTERWALAMI]
            czas_zalaczenia_w_interwalowym = poz[constants.PETLA_CZAS_INTERWALU]
        except (KeyError, AttributeError) as serr:
            czas_przerwy_miedzy_interwalami = 0
            czas_zalaczenia_w_interwalowym = 0

        # wartosc = 0
        # hash = 0
        try:
            wartosc = poz[constants.PETLA_WARTOSC]
        except (KeyError, AttributeError) as serr:
            wartosc = 0
        try:
            hash = poz[constants.HASH]
        except (KeyError, AttributeError) as serr:
            hash = 0

        try:
            ts_start = poz[constants.PETLA_TS_START]
            ts_stop = poz[constants.PETLA_TS_STOP]
        except (KeyError, AttributeError) as serr:
            ts_start = 0
            ts_stop = 0

        p = PozycjaPetli(nazwa, obszar=obszar, miesiace=miesiace, dni=dni, godz_wl=godz_wl, minu_wl=minu_wl,
                         sek_wl=sek_wl, godz_wyl=godz_wyl, minu_wyl=minu_wyl, sek_wyl=sek_wyl,
                         aktywne=aktywne, czas_interwalu=czas_zalaczenia_w_interwalowym,
                         czas_miedzy_interwalami=czas_przerwy_miedzy_interwalami, wartosc=wartosc,
                         hash=hash, ts_start=ts_start, ts_stop=ts_stop)
        return p


class PozycjaPetli:
    def __init__(self, nazwa, obszar='', miesiace=None, dni=None, godz_wl=0, minu_wl=0, sek_wl=0,
                 godz_wyl=0, minu_wyl=0, sek_wyl=0, aktywne=False, czas_interwalu=0, czas_miedzy_interwalami=0,
                 hash=0,
                 wartosc=0, ts_start=0, ts_stop=0,
                 dzialanie=None):  # wartosc to oczekiwana wartosc dla pozycji petli, np. ogrzewanie, petla jej nie modyfikuje
        # akt - 1 aktywne (mozna wlaczac/wylacza), 0 - deaktywowane
        self._nazwa = nazwa
        self._obszar = obszar
        #self._typ = typ  # typ - J jednorazowe, P permanentne
        self._dzialanie = dzialanie
        self._ts = int(time.time())
        self._ts_start = ts_start  # ts_start i stop sa uzywane jako jednorazowy, czyli jesli wartosc <>0 to znaczy ze jednorazowy i usuwac
        self._ts_stop = ts_stop
        self._wartosc = wartosc
        self._aktywne = aktywne
        if hash == 0:
            self._hash = getrandbits(32)
        else:
            self._hash = hash
        self._kiedy_koniec = 0  # epoch time do konca dzialania
        self._dzialalem_w_poprzednim_przebiegu = False  # jesli false to przebieg petli powinien ustawic na true
        self._stan = False  # stan mowi o tym, ze gdy pasowal czas to wykonano dzialajNaPozycji
        self._czas_zalaczenia_w_interwalowym = czas_interwalu  # czas w sekundach ile bedzie zalaczony w cykluinterwalowym
        self._ts_zalaczenia_interwalu = 0
        self._czas_przerwy_miedzy_interwalami = czas_miedzy_interwalami
        self._miesiace = miesiace  # lista miesiecy
        self._dni = dni  # lista dni
        self._godz_wl = int(godz_wl)
        self._minu_wl = int(minu_wl)
        self._sek_wl = int(sek_wl)
        self._godz_wyl = int(godz_wyl)
        self._minu_wyl = int(minu_wyl)
        self._sek_wyl = int(sek_wyl)
        return

    def resetuj_ts(self):
        self._ts = int(time.time())

    def rejestruj_dzialanie(self, dzialanie):
        self._dzialanie = dzialanie

    def _dzialaj_na_pozycji(self, stan):
        self.ustaw_stan(stan)
        if self._dzialanie:
            self._dzialanie(self._nazwa, stan, self)  # TODO po co przekazywac self do dzialania

    def _do_listy(self):
        #TODO usunac typ, zamiast niego sa ts start albo tsstop, zmienic w android
        do_listy = {constants.PETLA_NAZWA: self._nazwa,
                    constants.OBSZAR: self._obszar,
                    constants.PETLA_AKTYWNE: self._aktywne,
                    constants.KIEDY_KONIEC_DZIALANIA: self._kiedy_koniec,
                    constants.PETLA_GODZ_WL: self._godz_wl,
                    constants.PETLA_MINU_WL: self._minu_wl,
                    constants.PETLA_SEK_WL: self._sek_wl,
                    constants.PETLA_GODZ_WYL: self._godz_wyl,
                    constants.PETLA_MINU_WYL: self._minu_wyl,
                    constants.PETLA_SEK_WYL: self._sek_wyl,
                    #constants.PETLA_TYP: 'P',
                    constants.HASH: self._hash,
                    constants.TS: self._ts,
                    constants.PETLA_WARTOSC: self._wartosc
                    }
        if self._ts_start != 0:
            do_listy[constants.PETLA_TS_START] = self._ts_start

        #if self._ts_stop !=0:
        #    do_listy[constants.PETLA_TS_STOP] = self._ts_stop

        if self._czas_zalaczenia_w_interwalowym != 0:
            do_listy[constants.PETLA_CZAS_MIEDZY_INTERWALAMI] = self._czas_przerwy_miedzy_interwalami
            do_listy[constants.PETLA_CZAS_INTERWALU] = self._czas_zalaczenia_w_interwalowym

        if self._dni:
            do_listy[constants.PETLA_DNI] = self._dni
        if self._miesiace:
            do_listy[constants.PETLA_MIESIACE] = self._miesiace
        return do_listy

    def _czy_czas_pasuje(self):
        if self._ts_start == 0:  # przypadke kiedy jest cykliczne a nie od ts do tsa
            t = datetime.datetime.now()
            # sprawdzanie godzin i minut
            gstart = t.replace(hour=self._godz_wl, minute=self._minu_wl, second=self._sek_wl)
            gstop = t.replace(hour=self._godz_wyl, minute=self._minu_wyl, second=self._sek_wyl)
            t = datetime.datetime.now()

            czas_pasuje = False
            dni_pasuja = False
            miesiace_pasuja = False

            if gstart < t:
                if gstop > t:
                    czas_pasuje = True

            if self._dni is None:
                dni_pasuja = True
            elif len(self._dni) == 0:
                dni_pasuja = True
            else:
                if t.weekday() in self._dni:
                    dni_pasuja = True

            if self._miesiace is None:
                miesiace_pasuja = True
            elif len(self._miesiace) == 0:
                miesiace_pasuja = True
            else:
                if t.month in self._miesiace:
                    miesiace_pasuja = True

            # obliczenie pozostalego czasu i powrot
            self.resetuj_ts()
            if czas_pasuje and dni_pasuja and miesiace_pasuja:
                # self._kiedy_koniec = gstop.timestamp()   #(gstop - t).total_seconds()
                self._kiedy_koniec = (gstop - datetime.datetime(1970, 1,
                                                                1)).total_seconds()  # TODO po przejsciu na pyt 3 dodac tmestamp
                # TODO obliczenie pozostalego czasu tylko raz przy starcie, nie aktualizuejmy ts juz wiecej
                return True
            else:
                self._kiedy_koniec = 0  #int(time.time())
                return False
        else:  # przypadek kiedy mamy cykl jednorazowy od ts do ts
            # TODO zaktualizowac kedy koniec, nawet w przypadku jednorazowego, ale bez aktualizowania tsa
            t = int(time.time())
            self._kiedy_koniec = self._ts_stop  # - t
            if t >= self._ts_start:
                if t <= self._ts_stop:
                    self.resetuj_ts()
                    return True
        return False

    def ustaw_stan(self, stan):
        self._stan = stan
        if not stan:
            #self._kiedy_koniec = int(time.time())
            self.resetuj_ts()

    def get_czas_zalaczenia_w_interwalowym(self):
        return self._czas_zalaczenia_w_interwalowym

    def get_czas_przerwy_miedzy_interwalami(self):
        return self._czas_przerwy_miedzy_interwalami

    def get_czy_jednorazowy(self):
        if self._ts_start != 0:
            return True
        return False

    def get_nazwa(self):
        return self._nazwa

    def get_hash(self):
        return self._hash

    def get_stan(self):
        return self._stan

    def get_obszar(self):
        return self._obszar

    def get_kiedy_koniec(self):  # epoch time konca dzialania
        return self._kiedy_koniec

    def get_tsstop(self):
        return self._ts_stop

    def get_tsstart(self):
        return self._ts_start

    def do_ktorej_godziny(self):
        # TODO a jesli nie ma godziny startu tylko jest ts startu i stopu to dodac po ekstrakcji z epocha
        return str(self._godz_wyl).zfill(2) + ":" + str(self._minu_wyl).zfill(2)

    def od_ktorej_godziny(self):
        # TODO a jesli nie ma godziny startu tylko jest ts startu i stopu to dodac po ekstrakcji z epocha
        return str(self._godz_wl).zfill(2) + ":" + str(self._minu_wl).zfill(2)

    def get_wartosc(self):
        return self._wartosc

    def aktywuj(self, aktywne):
        self._aktywne = aktywne
        self.resetuj_ts()
        self._dzialalem_w_poprzednim_przebiegu = False

    def is_active(self):
        return self._aktywne
        #if self._aktywne:
        #    return True
        #return False
