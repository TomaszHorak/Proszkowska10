import datetime
import constants
import json
import THutils
import threading

TYP_JEDNORAZOWY = 'J'
TYP_PERMANENTNY = 'P'

CZAS_URUCHOMIENIA_PETLI = 2

class PetlaCzasowa:
    def __init__(self, obszar, dzialanie, callback=None, logger=None):
        #self._czas_uruchomienia_petli = czas_uruchamiania
        self._logger = logger
        self._obszar = obszar
        self._tabela = []
        self._petla_aktywna = False
        self._petla_w_trakcie_przebiegu = threading.Lock() #jesli tru to blokuj dodawanie
        self._callback = callback # callback jest bez parametrow i wywolywany za kazdym przelotem petli
        # dzialanie musi miec dwa parametry: nazwa_odbiornika, stan, wykorzystywane do zmiany stanu
        self._dzialanie = dzialanie
        self._odczytaj_cykle_z_konfiguracji_cyklicznie()
        self._petla()

    def czy_ktorykolwiek_wlaczony(self):
        for a in self._tabela:
            if a.get_stan():
                return True
        return False

    def _petla(self):
        self._petla_w_trakcie_przebiegu.acquire()
        if self._petla_aktywna:
            for a in self._tabela:
                if a.is_active():
                    if a.czy_czas_pasuje():
                        if not a.get_stan():
                            if not a._dzialano:
                                self._dzialaj_na_pozycji(a, True)
                                a._dzialano = True
                    else:
                        a._dzialano = False
                        if a.get_stan():
                            self._dzialaj_na_pozycji(a, False)
                        if a.get_typ() == TYP_JEDNORAZOWY:
                            self._usun_z_tabeli_nazwa(a.get_nazwa())
                else:
                    if a.get_stan():
                        self._dzialaj_na_pozycji(a, False)
                    if a.get_typ() == TYP_JEDNORAZOWY:
                        self._usun_z_tabeli_nazwa(a.get_nazwa())
            if self._callback is not None:
                self._callback()
        self._petla_w_trakcie_przebiegu.release()
        t = threading.Timer(CZAS_URUCHOMIENIA_PETLI, self._petla)
        t.start()

    def _dodaj_do_tabeli(self, nazwa, godz_wl, minu_wl, godz_wyl, minu_wyl, aktywne,
                         dni=None, miesiace=None, typ=TYP_PERMANENTNY):
        self._tabela.append(PozycjaPetli(nazwa, typ=typ, godz_wl=godz_wl, minu_wl=minu_wl,
                                         godz_wyl=godz_wyl, minu_wyl=minu_wyl, aktywne=aktywne,
                                         dni=dni, miesiace=miesiace))

    def _dzialaj_na_pozycji(self, pozycja, stan):
        pozycja.ustaw_stan(stan)
        self._dzialanie(pozycja.get_nazwa(), stan)

    def dzialaj_na_wszystkich_pozycjach(self, stan):
        self._petla_w_trakcie_przebiegu.acquire()
        for a in self._tabela:
            self._dzialaj_na_pozycji(a, stan)
            #a.aktywuj(stan)
            # a._dzialano = False # uwaga umozliwia dzialanie przy kolejnym przebiegu petli
        self._petla_w_trakcie_przebiegu.release()

    def dodaj_do_tabeli_jednorazowy_na_czas(self, nazwa, czas):
        wl = datetime.datetime.now()
        wyl = wl + datetime.timedelta(seconds=czas)
        self._petla_w_trakcie_przebiegu.acquire()
        self._dodaj_do_tabeli(nazwa, wl.hour, wl.minute, wyl.hour, wyl.minute,
                              True, typ=TYP_JEDNORAZOWY)
        self.zapisz_cykle_w_konfiguracji()
        self._petla_w_trakcie_przebiegu.release()

    def odczytaj_cykle_z_konfiguracji(self):
        #if not self.obszar:
        #    self.logger.warning('Pusty obszar przy odczycie cykli z konfiguracji.')
        result = THutils.odczytaj_parametr_konfiguracji(self._obszar, constants.CYKLE)
        try:
            c = json.loads(result)
        except Exception as e:
            if self._logger:
                self._logger.warning('Nie potrafie odczytac cykli ' + str(self._obszar) +
                                    ' :' + str(e))
            return
        self._petla_w_trakcie_przebiegu.acquire()
        self._tabela = []
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
                self._dodaj_do_tabeli(item[constants.PETLA_NAZWA],
                                      item[constants.PETLA_GODZ_WL],
                                      item[constants.PETLA_MINU_WL],
                                      item[constants.PETLA_GODZ_WYL],
                                      item[constants.PETLA_MINU_WYL],
                                      item[constants.PETLA_AKTYWNE],
                                      typ=item[constants.PETLA_TYP],
                                      dni=dni,
                                      miesiace=miesiace)
        except AttributeError as serr:
            if self._logger is not None:
                self._logger.warning('Blad procesowania cykli: ' + self._obszar +
                                    '. ' + str(serr))
        self._petla_w_trakcie_przebiegu.release()
        if self._logger is not None:
            self._logger.info('Odswiezylem cykle: ' + self._obszar)

    def _odczytaj_cykle_z_konfiguracji_cyklicznie(self):
        self.odczytaj_cykle_z_konfiguracji()
        # TODO dorobic cyklicznosc odczytywania

    def zapisz_cykle_w_konfiguracji(self):
        result = json.dumps(self.pozycje_do_listy())
        THutils.zapisz_parametr_konfiguracji(self._obszar, constants.CYKLE, result, self._logger)

    def _usun_z_tabeli_nazwa(self, nazwa, tylko_jednorazowy=True):
        # zabezpieczone aby usuwalo wylaczznie jednorazowe
        for i in range(len(self._tabela) - 1, -1, -1):
            if self._tabela[i].get_nazwa() == nazwa:
                if tylko_jednorazowy:
                    if self._tabela[i].get_typ() == TYP_JEDNORAZOWY:
                        del self._tabela[i]
                else:
                    del self._tabela[i]
        self.zapisz_cykle_w_konfiguracji()

    def aktywuj_pozycje_nazwa(self, nazwa, stan, tylko_jednorazowe=False):
        for a in self._tabela:
            if a.get_nazwa() == nazwa:
                if tylko_jednorazowe:
                    if a.get_typ() == TYP_JEDNORAZOWY:
                        a.aktywuj(stan)
                else:
                    a.aktywuj(stan)
        self.zapisz_cykle_w_konfiguracji()

    '''def czy_pozycja_aktywna(self, nazwa):
        for a in self._tabela:
            if a.get_nazwa() == nazwa:
                if a.is_active():
                    return True
        return False'''

    def aktywuj_petle(self, aktywacja):
        self._petla_aktywna = aktywacja

    '''def zwroc_aktywnosc_pozycji_petli(self):
        pozycje = {}
        for j in self._tabela:
            pozycje[j.get_nazwa()] = j.is_active()
        return pozycje'''

    def pozycje_do_listy(self, wylacznie_permanetne=False):
        pozycje = []
        for j in self._tabela:
            if wylacznie_permanetne:
                if j.get_typ() == TYP_PERMANENTNY:
                    pozycje.append(j.do_listy())
            else:
                pozycje.append(j.do_listy())
        return pozycje

class PozycjaPetli:
    def __init__(self, nazwa, typ=TYP_PERMANENTNY, miesiace=None, dni=None, godz_wl=0, minu_wl=0,
                 godz_wyl=0, minu_wyl=0, aktywne=False):
        # dzien - 0-poniedzialek, 1-wtorek itd.
        # akt - 1 aktywne (mozna wlaczac/wylacza), 0 - deaktywowane
        # typ - J jednorazowe, P permanentne
        self._nazwa = nazwa
        self._typ = typ
        self._aktywne = aktywne
        self._czas_do_konca = 0 # ile sekund zostalo do konca dzialania
        self._dzialano = False # jesli false to przebieg petli powinien ustawic na true
        self._stan = False
        self._miesiace = miesiace # lista miesiecy
        self._dni = dni # lista dni
        self._godz_wl = int(godz_wl)
        self._minu_wl = int(minu_wl)
        self._godz_wyl = int(godz_wyl)
        self._minu_wyl = int(minu_wyl)
        return

    def do_listy(self):
        do_listy = {constants.PETLA_NAZWA: self._nazwa,
                    constants.PETLA_AKTYWNE: self._aktywne,
                    constants.PETLA_CZAS_DO_KONCA: self._czas_do_konca,
                    constants.PETLA_GODZ_WL: self._godz_wl,
                    constants.PETLA_MINU_WL: self._minu_wl,
                    constants.PETLA_GODZ_WYL: self._godz_wyl,
                    constants.PETLA_MINU_WYL: self._minu_wyl,
                    constants.PETLA_MIESIACE: self._miesiace,
                    constants.PETLA_DNI: self._dni,
                    constants.PETLA_TYP: self._typ
                    }
        return do_listy

    def czy_czas_pasuje(self):
        t = datetime.datetime.now()

        #sprawdzanie godzin i minut
        gstart = t.replace(hour=self._godz_wl, minute=self._minu_wl, second=0)
        gstop = t.replace(hour=self._godz_wyl, minute=self._minu_wyl, second=0)

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
            return True
        else:
            self._czas_do_konca = 0
            return False
        # return czas_pasuje and dni_pasuja and miesiace_pasuja

    def ustaw_stan(self, stan):
        self._stan = stan

    def get_typ(self):
        return self._typ

    def get_nazwa(self):
        return self._nazwa

    def get_stan(self):
        return self._stan

    def aktywuj(self, aktywne):
        self._aktywne = aktywne

    def is_active(self):
        if self._aktywne:
            return True
        return False
