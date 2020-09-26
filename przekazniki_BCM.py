import threading
import logging
import time
from copy import deepcopy
import constants
import THutils
import json

class Przekaznik:
    def __init__(self, nazwa, pin, mcp, impuls=False, czas_impulsu=1, callback=None, def_czas_zalaczenia=0):
        self.nazwa = nazwa
        self.__mcp = mcp
        self._stan = False
        self.pin = pin
        self._def_czas_zalaczenia = def_czas_zalaczenia
        self._impuls = impuls
        self.czas_impulsu = czas_impulsu
        self.__callback = callback
        self.__mcp.config(pin, self.__mcp.OUTPUT)
        self.__mcp.output(pin, 1)
        return

    def get_defczaszalaczenia(self):
        return self._def_czas_zalaczenia

    def set_stan(self, stan):
        self._stan = stan
        if stan:
            self.__mcp.output(self.pin, 0)
            if self._impuls:
                t = threading.Timer(int(self.czas_impulsu), self.set_stan, args=[False])
                t.start()
        else:
            self.__mcp.output(self.pin, 1)
        if self.__callback is not None:
            self.__callback()

    def get_stan(self):
        return self._stan

    def get_nazwa(self):
        return self.nazwa

    def do_listy(self):
        a = {constants.NAZWA: self.nazwa,
             constants.PRZEKAZNIK_STAN: self._stan,
             constants.PRZEKAZNIK_IMPULS: self._impuls,
             constants.PRZEKAZNIK_CZAS_IMPULSU: self.czas_impulsu,
             constants.PRZEKAZNIK_DEF_CZAS_ZAL: self._def_czas_zalaczenia,
             #constants.PRZEKAZNIK_PIN: self.pin
            }
        return a

#TODO dorobic wszedzie, glownie w oswietleniu callbacka
class PrzekaznikiBCM:
    def __init__(self, mcp, callback=None, obszar=None):
        # tabela pin zawiera wszystkei przekazniki w danej implementacji klasy
        self.__pin = []
        self.__mcp = mcp
        self._obszar = obszar
        self.__callback = callback
        self.logger = logging.getLogger(constants.NAZWA_LOGGERA)

    def odczytaj_przekazniki_z_konfiguracji(self):
        result = THutils.odczytaj_parametr_konfiguracji(self._obszar, constants.ODBIORNIKI)
        try:
            c = json.loads(result)
        except Exception as e:
            if self.logger:
                self.logger.warning('Nie potrafie odczytac przekaznikow ' + str(self._obszar) +
                                    ' :' + str(e))
            return
        #self._petla_w_trakcie_przebiegu.acquire()
        self.__pin = []
        try:
            for item in c:
                if constants.NAZWA in item:
                    nazwa = item[constants.NAZWA]
                else:
                    nazwa = None
                if constants.PRZEKAZNIK_IMPULS in item:
                    impuls = item[constants.PRZEKAZNIK_IMPULS]
                else:
                    impuls = None
                if constants.PRZEKAZNIK_DEF_CZAS_ZAL in item:
                    def_czas = item[constants.PRZEKAZNIK_DEF_CZAS_ZAL]
                else:
                    def_czas = None
                if constants.PRZEKAZNIK_CZAS_IMPULSU in item:
                    czas_imp = item[constants.PRZEKAZNIK_CZAS_IMPULSU]
                else:
                    czas_imp = None
                if constants.PRZEKAZNIK_PIN in item:
                    pin = item[constants.PRZEKAZNIK_PIN]
                else:
                    pin = None

                self.dodaj_przekaznik(nazwa, pin, impuls=impuls, czas_impulsu=czas_imp, def_czas_zalaczenia=def_czas)

        except AttributeError as serr:
            if self.logger is not None:
                self.logger.warning('Blad procesowania dodawania przekaznikow: ' + self._obszar +
                                    '. ' + str(serr))
        #self._petla_w_trakcie_przebiegu.release()
        if self.logger is not None:
            self.logger.info('Odswiezylem odbiorniki: ' + self._obszar)


    def pozycje_do_listy(self):
        pozycje = []
        for j in self.__pin:
            pozycje.append(j.do_listy())
        return pozycje

    def dodaj_przekaznik(self, nazwa, pin, impuls=False, czas_impulsu=1, def_czas_zalaczenia=0):
        # nr pinu na szynie GPIO | stan przekaznika
        self.__pin.append(Przekaznik(nazwa, pin, self.__mcp, impuls=impuls, czas_impulsu=czas_impulsu,
                                     callback=self.__callback, def_czas_zalaczenia=def_czas_zalaczenia))

    def przekaznik_po_nazwie(self, nazwa):
        for j in self.__pin:
            if j.nazwa == nazwa:
                return j
        return None

    # TODO usunac wszystkie przekazniki po numerze
    def ustaw_przekaznik_nr(self, nr_przekaznika, stan):
        if stan:
            self.__mcp.output(self.__pin[nr_przekaznika].pin, 0)
        else:
            self.__mcp.output(self.__pin[nr_przekaznika].pin, 1)
        self.__pin[nr_przekaznika].set_stan(stan)

    def stan_przekaznika_nazwa(self, nazwa):
        # zwraca stan pierwszego przekaznika o danej nazwie
        for j in self.__pin:
            if j.nazwa == nazwa:
                return j.get_stan()
        return False

    def zwroc_stan_przekaznikow(self):
        odbi = {}
        for j in self.__pin:
            odbi[j.get_nazwa()] = j.get_stan()
        return odbi

    def toggle_przekaznik_nazwa(self, nazwa):
        przek = self.przekaznik_po_nazwie(nazwa)
        self.ustaw_przekaznik_nazwa(nazwa, not przek.get_stan())

    def ustaw_przekaznik_nazwa(self, nazwa, stan):
        a = False
        for j in self.__pin:
            if j.nazwa == nazwa:
                a = True
                '''if stan:
                    if j.impuls:
                    self.__mcp.output(j.pin, 0)
                else:
                    self.__mcp.output(j.pin, 1)'''
                j.set_stan(stan)
        if not a:
            self.logger.warning('przekazniki_BCM, nie ma odbiornika o nazwie: ' + str(nazwa))

    def wylacz_wszystkie_przekazniki(self):
        for j in self.__pin:
            self.ustaw_przekaznik_nazwa(j.nazwa, False)

    def wlacz_wszystkie_przekazniki(self, przekazniki, wlacz):
        # jesli wlacz=True to wlacza wszystkie i zwraca stan przed wlaczeniem
        # jesli wlacz=False to odtwarza stan przekaznikow z parametru przekazniki
        if wlacz:
            x = deepcopy(self.__pin)
            for a in self.__pin:
                self.ustaw_przekaznik_nazwa(a.get_nazwa(), True)
                # a.set_stan(True)
                # time.sleep(0.05)
            # for j in range(len(self.pin)):
            #    self.ustaw_przekaznik_nr(j, True)
            return x
        else:
            # a = 0
            for x in przekazniki:
                self.ustaw_przekaznik_nazwa(x.get_nazwa(), x.get_stan())
                time.sleep(0.05)
            # for x in self.pin:
            #                x.set_stan(przekazniki[a].get_stan)
            # for j in range(len(self.pin)):
            #    self.ustaw_przekaznik_nr(j, przekazniki[a].get_stan)
            #               a = a + 1
            return przekazniki

    '''def wlacz_na_czas(self, nr_przekaznika, czas):
        # TODO usunac wlaczanie po numerze, w ogole numer przekaznika odpada
        if czas == 0:
            return
        self.ustaw_przekaznik_nr(nr_przekaznika, True)
        t = threading.Timer(czas, self.ustaw_przekaznik_nr, [nr_przekaznika, False])
        t.start()'''

    def wlacz_na_czas_nazwa(self, nazwa, czas):
        if czas == 0:
            return
        self.ustaw_przekaznik_nazwa(nazwa, True)
        t = threading.Timer(czas, self.ustaw_przekaznik_nazwa, args=[nazwa, False])
        t.start()

    def czy_ktorykolwiek_wlaczony(self):
        for j in self.__pin:
            if j.get_stan():
                return True
        return False
