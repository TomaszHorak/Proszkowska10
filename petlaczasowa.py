from __future__ import print_function
import datetime
import time
from random import getrandbits

import constants
import json
import THutils
import threading

TYP_JEDNORAZOWY = 'J'
TYP_PERMANENTNY = 'P'

CZAS_URUCHOMIENIA_PETLI = 1

class PetlaCzasowa:
    def __init__(self, logger=None):
        self._logger = logger
        self._tabela = []
        self._petla_w_trakcie_przebiegu = threading.Lock() #jesli tru to blokuj dodawanie
        self._odczytaj_cykle_z_konfiguracji()
        #self._odczytaj_cykle_z_konfiguracji_cyklicznie()
        #self._petlaStart()

    def rejestruj_dzialanie(self, obszar, dzialanie):
        for a in self._tabela:
            if a.get_obszar() == obszar:
                a.rejestruj_dzialanie(dzialanie)

    #def czy_ktorykolwiek_wlaczony(self):
    #    for a in self._tabela:
    #        if a.get_stan():
    #            return True
    #    return False

    def __interwalowy_dzialaj(self, a):
        teraz = int(time.time())
        roznica_czasu = teraz - a._ts_zalaczenia_interwalu

        if a.get_stan():
            if roznica_czasu >= a.get_czas_zalaczenia_w_interwalowym():
                #nalezy wylaczyc
                #if not a._dzialalem_w_poprzednim_przebiegu:
                a._dzialalem_w_poprzednim_przebiegu = True
                a._ts_zalaczenia_interwalu = teraz
                a._dzialaj_na_pozycji(False)
                #print('wylaczaj interwalowy' + str(a._ts_zalaczenia_interwalu))
#            else:
#                a._dzialalem_w_poprzednim_przebiegu = False
        else:
            if roznica_czasu >= a.get_czas_przerwy_miedzy_interwalami():
                # nalezy wlaczyc
#                if not a._dzialalem_w_poprzednim_przebiegu:
                a._ts_zalaczenia_interwalu = teraz
                a._dzialalem_w_poprzednim_przebiegu = True
                #print('wlaczaj' + str(a._ts_zalaczenia_interwalu))
                a._dzialaj_na_pozycji(True)
   #        else:
    #            a._dzialalem_w_poprzednim_przebiegu = False
        return

    def petlaStart(self):
        self._petla_w_trakcie_przebiegu.acquire()
        #if self._petla_aktywna:
        if len(self._tabela) > 0:
            for a in self._tabela: # type: PozycjaPetli
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
                        if a.get_stan():
                            a._dzialaj_na_pozycji(False)
                        if a.get_typ() == TYP_JEDNORAZOWY:
                            self._usun_z_tabeli_nazwa_jednorazzowy_w_przebiegu(a.get_nazwa())
                else:
                    if a.get_stan():
                        a._dzialaj_na_pozycji(False)
                    if a.get_typ() == TYP_JEDNORAZOWY:
                        self._usun_z_tabeli_nazwa_jednorazzowy_w_przebiegu(a.get_nazwa())

                if a.get_czas_do_konca() != 0:
                    a._dzialaj_na_pozycji(False, tylko_aktualizuj_ts=True)

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

    def dodaj_nowy_cykl_permanentny(self, poz):
        p = self.pozycja_z_json(poz)    # type: PozycjaPetli
        if not p:
            return
        p._hash = getrandbits(64)
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
        #poz jest typu tuple bo pochodzi z API
        p = self.pozycja_z_json(poz)    # type: PozycjaPetli
        if not p:
            return
        self._petla_w_trakcie_przebiegu.acquire()
        for a in self._tabela:  # type: PozycjaPetli
            if a.get_hash() == poz[constants.HASH]:
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
                    self._zapisz_cykle_w_konfiguracji()
                except (KeyError, AttributeError) as serr:
                    if self._logger is not None:
                        self._logger.warning('Brak klucza w poleceniu zmiany cykli: ' + str(serr))
        self._petla_w_trakcie_przebiegu.release()

    def dodaj_do_tabeli_jednorazowy_na_czas(self, nazwa, czas, obszar='', dzialanie=None):
        wl = datetime.datetime.now()
        wyl = wl + datetime.timedelta(seconds=czas)
        self._petla_w_trakcie_przebiegu.acquire()
        #self.dodaj_do_tabeli(nazwa, wl.hour, wl.minute, wl.second, wyl.hour, wyl.minute, wyl.second,
        self._tabela.append(PozycjaPetli(nazwa, obszar=obszar, typ=TYP_JEDNORAZOWY, godz_wl=wl.hour,
                                         minu_wl=wl.minute, sek_wl=wl.second,
                                         godz_wyl=wyl.hour, minu_wyl=wyl.minute, sek_wyl=wyl.second,
                                         aktywne=True))
        self.rejestruj_dzialanie(obszar, dzialanie)
        self._zapisz_cykle_w_konfiguracji()
        self._petla_w_trakcie_przebiegu.release()

    def _odczytaj_cykle_z_konfiguracji(self):
        #if not self.obszar:
        #    self.logger.warning('Pusty obszar przy odczycie cykli z konfiguracji.')
        result = THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_KONFIGURACJI_CYKLE,
                                                        constants.OBSZAR_KONFIGURACJI_CYKLE)
        try:
            c = json.loads(result)
        except Exception as e:
            if self._logger:
                self._logger.warning('Nie potrafie odczytac cykli ' + ' :' + str(e))
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
                czas_interwalu = 0
                czas_miedzy_interwalami = 0
                try:
                    czas_interwalu = item[constants.PETLA_CZAS_INTERWALU]
                    czas_miedzy_interwalami = item[constants.PETLA_CZAS_MIEDZY_INTERWALAMI]
                except (KeyError, AttributeError) as serr:
                    if self._logger is not None:
                        self._logger.warning('Brak klucza w odczycie cykli: ' + str(serr))
                hash=0
                try:
                    hash = item[constants.HASH]
                except (KeyError, AttributeError) as serr:
                    if self._logger is not None:
                        self._logger.warning('Brak klucza w odczycie cykli: ' + str(serr))
                self._tabela.append(
                    PozycjaPetli(item[constants.PETLA_NAZWA],
                                 obszar=item[constants.OBSZAR],
                                 typ=item[constants.PETLA_TYP],
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
                                 hash=hash))
        except AttributeError as serr:
            if self._logger is not None:
                self._logger.warning('Blad procesowania cykli: ' + '. ' + str(serr))
        self._petla_w_trakcie_przebiegu.release()
        if self._logger is not None:
            self._logger.info('Odswiezylem cykle.')

    def _zapisz_cykle_w_konfiguracji(self):
        result = json.dumps(self.pozycje_do_listy())
        THutils.zapisz_parametr_konfiguracji(constants.OBSZAR_KONFIGURACJI_CYKLE,
                                             constants.OBSZAR_KONFIGURACJI_CYKLE, result, self._logger)

    def _usun_z_tabeli_nazwa_jednorazzowy_w_przebiegu(self, nazwa):
        # zabezpieczone aby usuwalo wylaczznie jednorazowe
        for i in range(len(self._tabela) - 1, -1, -1):
            if self._tabela[i].get_nazwa() == nazwa:
                if self._tabela[i].get_typ() == TYP_JEDNORAZOWY:
                    del self._tabela[i]
        self._zapisz_cykle_w_konfiguracji()

    def aktywuj_pozycje_nazwa(self, obszar, nazwa, stan, tylko_jednorazowe=False):
        for a in self._tabela:
            if a.get_obszar() == obszar:
                if a.get_nazwa() == nazwa:
                    if tylko_jednorazowe:
                        if a.get_typ() == TYP_JEDNORAZOWY:
                            a.aktywuj(stan)
                    else:
                        a.aktywuj(stan)
        self._zapisz_cykle_w_konfiguracji()

    def aktywuj_wszystkie_pozycja_w_obszarze(self, obszar, stan):
        for a in self._tabela:
            if a.get_obszar() == obszar:
                a.aktywuj(stan)

    def pozycje_do_listy(self, obszar='', wylacznie_permanetne=False):
        pozycje = []
        for j in self._tabela: # type: PozycjaPetli
            if j.get_obszar() == obszar or obszar == '':
                if wylacznie_permanetne:
                    if j.get_typ() == TYP_PERMANENTNY:
                        pozycje.append(j._do_listy())
                else:
                    pozycje.append(j._do_listy())
        return pozycje

    def pozycja_z_json(self, poz):
        try:
            nazwa = poz[constants.PETLA_NAZWA]
            obszar = poz[constants.OBSZAR]
            godz_wl = poz[constants.PETLA_GODZ_WL]
            godz_wyl = poz[constants.PETLA_GODZ_WYL]
            minu_wl = poz[constants.PETLA_MINU_WL]
            minu_wyl = poz[constants.PETLA_MINU_WYL]
            sek_wl = poz[constants.PETLA_SEK_WL]
            sek_wyl = poz[constants.PETLA_SEK_WYL]
            miesiace = poz[constants.PETLA_MIESIACE]
            dni = poz[constants.PETLA_DNI]
            typ = poz[constants.PETLA_TYP]
            aktywne = poz[constants.PETLA_AKTYWNE]
            czas_przerwy_miedzy_interwalami = poz[constants.PETLA_CZAS_MIEDZY_INTERWALAMI]
            czas_zalaczenia_w_interwalowym = poz[constants.PETLA_CZAS_INTERWALU]
            p = PozycjaPetli(nazwa, obszar, typ, miesiace=miesiace, dni=dni, godz_wl=godz_wl, minu_wl=minu_wl,
                             sek_wl=sek_wl, godz_wyl=godz_wyl, minu_wyl=minu_wyl, sek_wyl=sek_wyl,
                             aktywne=aktywne, czas_interwalu=czas_zalaczenia_w_interwalowym,
                             czas_miedzy_interwalami=czas_przerwy_miedzy_interwalami)
            return p
        except (KeyError, AttributeError) as serr:
            if self._logger is not None:
                self._logger.warning('Brak klucza w poleceniu zmiany cykli: ' + str(serr))
            return None

class PozycjaPetli:
    def __init__(self, nazwa, obszar='', typ=TYP_PERMANENTNY, miesiace=None, dni=None, godz_wl=0, minu_wl=0, sek_wl=0,
                 godz_wyl=0, minu_wyl=0, sek_wyl=0, aktywne=False, czas_interwalu=0, czas_miedzy_interwalami=0,
                 hash=0):
        # akt - 1 aktywne (mozna wlaczac/wylacza), 0 - deaktywowane
        self._nazwa = nazwa
        self._obszar = obszar
        self._typ = typ # typ - J jednorazowe, P permanentne
        self._dzialanie = None
        self._ts = int(time.time())
        self._aktywne = aktywne
        if hash == 0:
            self._hash = getrandbits(64)
        else:
            self._hash = hash
        self._czas_do_konca = 0 # ile sekund zostalo do konca dzialania
        self._dzialalem_w_poprzednim_przebiegu = False # jesli false to przebieg petli powinien ustawic na true
        self._stan = False
        self._czas_zalaczenia_w_interwalowym = czas_interwalu #czas w sekundach ile bedzie zalaczony w cykluinterwalowym
        self._ts_zalaczenia_interwalu = 0
        self._czas_przerwy_miedzy_interwalami = czas_miedzy_interwalami
        self._miesiace = miesiace # lista miesiecy
        self._dni = dni # lista dni
        self._godz_wl = int(godz_wl)
        self._minu_wl = int(minu_wl)
        self._sek_wl = int(sek_wl)
        self._godz_wyl = int(godz_wyl)
        self._minu_wyl = int(minu_wyl)
        self._sek_wyl = int(sek_wyl)
        return

    def rejestruj_dzialanie(self, dzialanie):
        self._dzialanie = dzialanie

    def _dzialaj_na_pozycji(self, stan, tylko_aktualizuj_ts=False):
        if not tylko_aktualizuj_ts:
            self.ustaw_stan(stan)
        if self._dzialanie:
            self._dzialanie(self._nazwa, stan, tylko_aktualizuj_ts)

    def _do_listy(self):
        do_listy = {constants.PETLA_NAZWA: self._nazwa,
                    constants.OBSZAR: self._obszar,
                    constants.PETLA_AKTYWNE: self._aktywne,
                    constants.PETLA_CZAS_DO_KONCA: self._czas_do_konca,
                    constants.PETLA_GODZ_WL: self._godz_wl,
                    constants.PETLA_MINU_WL: self._minu_wl,
                    constants.PETLA_SEK_WL: self._sek_wl,
                    constants.PETLA_GODZ_WYL: self._godz_wyl,
                    constants.PETLA_MINU_WYL: self._minu_wyl,
                    constants.PETLA_SEK_WYL: self._sek_wyl,
                    constants.PETLA_MIESIACE: self._miesiace,
                    constants.PETLA_DNI: self._dni,
                    constants.PETLA_TYP: self._typ,
                    constants.HASH: self._hash,
                    constants.TS: self._ts,
                    constants.PETLA_CZAS_MIEDZY_INTERWALAMI: self._czas_przerwy_miedzy_interwalami,
                    constants.PETLA_CZAS_INTERWALU: self._czas_zalaczenia_w_interwalowym
                    }
        return do_listy

    def _czy_czas_pasuje(self):
        t = datetime.datetime.now()

        #sprawdzanie godzin i minut
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
        else:
            if t.weekday() in self._dni:
                dni_pasuja = True

        if self._miesiace is None:
            miesiace_pasuja = True
        else:
            if t.month in self._miesiace:
                miesiace_pasuja = True

        # obliczenie pozostalego czasu i powrot
        if czas_pasuje and dni_pasuja and miesiace_pasuja:
            self._czas_do_konca = (gstop-t).total_seconds()
            self._ts = int(time.time())
            return True
        else:
            self._czas_do_konca = 0
            self._ts = int(time.time())
            return False
        # return czas_pasuje and dni_pasuja and miesiace_pasuja

    def ustaw_stan(self, stan):
        self._stan = stan
        if not stan:
            self._czas_do_konca = 0
            self._ts = int(time.time())

    def get_czas_zalaczenia_w_interwalowym(self):
        return self._czas_zalaczenia_w_interwalowym

    def get_czas_przerwy_miedzy_interwalami(self):
        return self._czas_przerwy_miedzy_interwalami

    def get_typ(self):
        return self._typ

    def get_nazwa(self):
        return self._nazwa

    def get_hash(self):
        return self._hash

    def get_stan(self):
        return self._stan

    def get_obszar(self):
        return self._obszar

    def get_czas_do_konca(self):
        return self._czas_do_konca

    def aktywuj(self, aktywne):
        self._aktywne = aktywne
        self._ts = int(time.time())
        self._dzialalem_w_poprzednim_przebiegu = False

    def is_active(self):
        if self._aktywne:
            return True
        return False
