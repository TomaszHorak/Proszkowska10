import Adafruit_MCP230xx
import pigpio
import time
import logging
import threading
from copy import deepcopy
import constants

PIN_PRZERWANIA_MCP = 12



class WejsciaWyjscia:
    def __init__(self, wejsca=False, wyjscia=False):
        if wyjscia:
            self.wyjscia = self.Wyjscia(address=0x20, num_gpios=16)
        if wejsca:
            self.wejscia = self.Wejscia(address=0x21, num_gpios=16, pin_przerwania_mcp=PIN_PRZERWANIA_MCP)

    class Wejscia:
            def __init__(self, address, num_gpios, pin_przerwania_mcp):
                self._wejscia = []
                # ustawienie pinu Raspberry na przerwania z MCP
                gpio_pigpio = pigpio.pi()
                gpio_pigpio.set_mode(pin_przerwania_mcp, pigpio.INPUT)
                gpio_pigpio.set_pull_up_down(pin_przerwania_mcp, pigpio.PUD_UP)
                gpio_pigpio.write(pin_przerwania_mcp, 1)
                # gpio_pigpio.set_glitch_filter(pin_przerwania_mcp, 1500)
                gpio_pigpio.callback(pin_przerwania_mcp, pigpio.FALLING_EDGE, self.__odczytaj_stany_wejsc_po_przerwaniu)

                self.mcp_wejscie1 = Adafruit_MCP230xx.Adafruit_MCP230XX(address=address, num_gpios=num_gpios)
                for a in range(0, num_gpios):
                    self.mcp_wejscie1.config(a, Adafruit_MCP230xx.Adafruit_MCP230XX.INPUT)
                    time.sleep(0.05)
                    self.mcp_wejscie1.pullup(a, 1)
                self.mcp_wejscie1.read_caly_rejestr()
                return

            def __odczytaj_stany_wejsc_po_przerwaniu(self, pin, level, tick):
                odczyt = self.mcp_wejscie1.read_caly_rejestr()
                for a in self._wejscia:
                    a.set_stan((odczyt >> a.get_pin()) & 1)
                    # print "Odczytano stan wejscia: " + a.get_nazwa() + ". Stan: " + str(a.get_stan())

            def dodaj_wejscie(self, nazwa, pin, callback=None):
                self._wejscia.append(self.MCPwejscie(nazwa, pin, callback=callback))

            '''def wejscie_po_nazwie(self, nazwa):
                for j in self._wejscia:
                    if j.get_nazwa() == nazwa:
                        return j
                return None'''

            class MCPwejscie:
                def __init__(self, nazwa, pin, callback=None):
                    self.__nazwa = nazwa
                    self.__stan = 1
                    self.__pin = pin
                    self.__callback = callback  # callback musi miec parametr z nazwa, pin  i aktualnym stanem
                    return

                def set_stan(self, stan):
                    if self.__stan == stan:
                        return
                    self.__stan = stan
                    if self.__callback is not None:
                        self.__callback(self.__pin, self.__nazwa, self.__stan)

                def get_stan(self):
                    return self.__stan

                def get_pin(self):
                    return self.__pin

                def get_nazwa(self):
                    return self.__nazwa

    class Wyjscia:
        def __init__(self, address, num_gpios):
            # tabela pin zawiera wszystkei przekazniki w danej implementacji klasy
            self.__pin = [] # type: [WejsciaWyjscia.Wyjscia.McpWyjscie]
            self.__mcp = Adafruit_MCP230xx.Adafruit_MCP230XX(address=address, num_gpios=num_gpios)
            self.__logger = logging.getLogger(constants.NAZWA_LOGGERA)

        def pozycje_do_listy(self, obszar):
            pozycje = []
            for j in self.__pin:
                if j.get_obszar() == obszar:
                    pozycje.append(j.do_listy())
            return pozycje

        def dodaj_przekaznik(self, nazwa, pin, obszar='', impuls=False, czas_impulsu=1, def_czas_zalaczenia=0,
                             callbackfunction=None):
            # nr pinu na szynie GPIO | stan przekaznika
            self.__pin.append(
                self.McpWyjscie(nazwa, pin, self.__mcp, obszar=obszar, impuls=impuls, czas_impulsu=czas_impulsu,
                                callback=callbackfunction, def_czas_zalaczenia=def_czas_zalaczenia))

        def przekaznik_po_nazwie(self, nazwa):
            for j in self.__pin:
                if j.get_nazwa() == nazwa:
                    return j
            return None

        def defczas_zalaczenia_po_nazwie(self, nazwa):
            przek = self.przekaznik_po_nazwie(nazwa)
            if przek:
                return przek.get_defczaszalaczenia()
            else:
                return 0

        '''# TODO usunac wszystkie przekazniki po numerze
        def ustaw_przekaznik_nr(self, nr_przekaznika, stan):
            if stan:
                self.__mcp.output(self.__pin[nr_przekaznika].pin, 0)
            else:
                self.__mcp.output(self.__pin[nr_przekaznika].pin, 1)
            self.__pin[nr_przekaznika].set_stan(stan)'''

        def stan_przekaznika_nazwa(self, nazwa):
            # zwraca stan pierwszego przekaznika o danej nazwie
            for j in self.__pin:
                if j.get_nazwa() == nazwa:
                    return j.get_stan()
            return False

        '''def zwroc_stan_przekaznikow(self):
            odbi = {}
            for j in self.__pin:
                odbi[j.get_nazwa()] = j.get_stan()
            return odbi'''

        def toggle_przekaznik_nazwa(self, nazwa):
            # przek = self.przekaznik_po_nazwie(nazwa)
            self.ustaw_przekaznik_nazwa(nazwa, not self.stan_przekaznika_nazwa(nazwa))

        def ustaw_przekaznik_nazwa(self, nazwa, stan):
            a = False
            for j in self.__pin:
                if j.get_nazwa() == nazwa:
                    a = True
                    '''if stan:
                        if j.impuls:
                        self.__mcp.output(j.pin, 0)
                    else:
                        self.__mcp.output(j.pin, 1)'''
                    j.set_stan(stan)
            if not a:
                self.__logger.warning('przekazniki_BCM, nie ma odbiornika o nazwie: ' + str(nazwa))

        def wylacz_wszystkie_przekazniki(self, obszar):
            for j in self.__pin:
                if j.get_obszar() == obszar:
                    self.ustaw_przekaznik_nazwa(j.get_nazwa(), False)

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

        '''def wlacz_na_czas_nazwa(self, nazwa, czas):
            if czas == 0:
                return
            self.ustaw_przekaznik_nazwa(nazwa, True)
            t = threading.Timer(czas, self.ustaw_przekaznik_nazwa, args=[nazwa, False])
            t.start()'''

        def czy_ktorykolwiek_wlaczony(self, obszar):
            for j in self.__pin:
                if j.get_obszar() == obszar:
                    if j.get_stan():
                        return True
            return False

        '''def odczytaj_przekazniki_z_konfiguracji(self):
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
                self.logger.info('Odswiezylem odbiorniki: ' + self._obszar)'''

        class McpWyjscie:
            def __init__(self, nazwa, pin, mcp, obszar='', impuls=False, czas_impulsu=1, callback=None,
                         def_czas_zalaczenia=0):
                self.__nazwa = nazwa
                self.__mcp = mcp
                self.__stan = False
                self.__pin = pin
                self.__obszar = obszar
                self.__def_czas_zalaczenia = def_czas_zalaczenia
                # TODO jesli czas impulsy > 0 to jest impuls a jak =0 to go nie ma, usunac zmienna impuls w Andr i Pyth
                self.__impuls = impuls
                self.__czas_impulsu = czas_impulsu
                self.__callback = callback
                self.__mcp.config(pin, self.__mcp.OUTPUT)
                self.__mcp.output(pin, 1)
                return

            def get_defczaszalaczenia(self):
                return self.__def_czas_zalaczenia

            def set_stan(self, stan):
                self.__stan = stan
                if stan:
                    self.__mcp.output(self.__pin, 0)
                    if self.__impuls:
                        threading.Timer(int(self.__czas_impulsu), self.set_stan, args=[False]).start()
                else:
                    self.__mcp.output(self.__pin, 1)
                if self.__callback is not None:
                    self.__callback()

            def get_stan(self):
                return self.__stan

            def get_nazwa(self):
                return self.__nazwa

            def get_obszar(self):
                return self.__obszar

            def do_listy(self):
                return {constants.NAZWA: self.__nazwa,
                        constants.PRZEKAZNIK_STAN: self.__stan,
                        constants.PRZEKAZNIK_IMPULS: self.__impuls,
                        constants.PRZEKAZNIK_CZAS_IMPULSU: self.__czas_impulsu,
                        constants.PRZEKAZNIK_DEF_CZAS_ZAL: self.__def_czas_zalaczenia,
                        # constants.PRZEKAZNIK_PIN: self.pin
                        }