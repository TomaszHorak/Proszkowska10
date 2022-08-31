from __future__ import print_function

import THutils
from Obszar import Obszar
import constants
from time import time
from THutils import zapisz_temp_w_logu
from THutils import odczytaj_parametr_konfiguracji
from THutils import skonstruuj_odpowiedzV2OK

DEFAULT_TEMP_MIN = 17.0
DEFAULT_TEMP_MAX = 25.0
CZAS_OPOZNIENIA_PRZYJMOWANIA_01_STOPNIA = 30*60  # w sekundach
HISTEREZA = 0.5
CZAS_DO_ALARMU = 50*60 #liczba sekund bez zmiany stanu temp do podniesienia alarmu

OGRZ_ZOSIA = 'ogrz_zosia'
OGRZ_ZOSIA_PIN = 17
OGRZ_SALON = 'ogrz_salon'
OGRZ_SALON_PIN = 16
OGRZ_STROZOWKA = 'ogrz_strozowka'
OGRZ_STROZOWKA_PIN = 15
OGRZ_POM_NAD_GARAZEM = 'ogrz_pom_nad_garaz'
OGRZ_POM_NAD_GARAZEM_PIN = 18
OGRZ_PIOTREK = 'ogrz_piotrek'
OGRZ_PIOTREK_PIN = 19
OGRZ_GARAZ = 'ogrz_garaz'
OGRZ_GARAZ_PIN = 20
OGRZ_SYPIALNIA = 'ogrz_sypialnia'
OGRZ_SYPIALNIA_PIN = 21

TRYB_WAKACJE = 'wakacje'
PETLA_STERUJ_CYKLICZNIE = 'steruj_cyklicznie'



''' Dokumentacja API

every command structure:
'komenda' - command -> constants.KOMENDA 
'parametry' - additional parameters

KOMENDA_ZADAJ_TEMP: constants.KOMENDA_ZADAJ_TEMP
zadaj temperature, do ktorej ma dazyc ogrzewanie w danym pomieszczeniu
constants.NAZWA = name of the pomieszczenies
constants.POLE_TEMP_ZADANA = zadana temperatura, typ double np. 21.1

KOMENDA_PODAJ_TEMP: constants.KOMENDA_PODAJ_TEMP
podaje aktualna temperature z danego pomieszczenia
constants.NAZWA = name of the pomieszczenie
constants.POLE_TEMP_AKTUALNA = aktualna temperatura odczytana w danym pomieszczeniu

KOMENDA_STATUS_POMIESZCZENIA: constants.KOMENDA_STATUS_POMIESZCZENIA
zwraca status wybranego pomieszczenia, razem z cyklami
constants.NAZWA = name of the pomieszczenie

KOMENDA_WAKACJE: constants.KOMENDA_WAKACJE:
ustawia tryb wakacje
POLE_WAKACJE = json z definicja wakacji
'''




class Ogrzewanie(Obszar):
    def __init__(self, wewy, petla, logger, log_temp):
        Obszar.__init__(self, constants.OBSZAR_OGRZ,
                        logger,
                        petla=petla,
                        wewy=wewy,
                        #callback_przekaznika_wyjscia=self.resetuj_ts,
                        rodzaj_komunikatu=constants.RODZAJ_KOMUNIKATU_STAN_OGRZEWANIA,
                        dzialanie_petli=self.dzialanie_petli)

        self.log_temp = log_temp

        self.__czas_do_alarmu = int(float(odczytaj_parametr_konfiguracji(self.obszar, constants.CZAS_DO_ALARMU, self.logger)))
        if not self.__czas_do_alarmu:
            self.__czas_do_alarmu = CZAS_DO_ALARMU

        self.__min_temp_pomieszczenia = float(odczytaj_parametr_konfiguracji( self.obszar, constants.MIN_TEMP_POMIESZCZENIA, self.logger))
        if not self.__min_temp_pomieszczenia:
            self.__min_temp_pomieszczenia = DEFAULT_TEMP_MIN

        self.__histereza = float(odczytaj_parametr_konfiguracji(self.obszar, constants.HISTEREZA, self.logger))
        if not self.__histereza:
            self.__histereza = HISTEREZA

        self.__max_temp_pomieszczenia = float(odczytaj_parametr_konfiguracji(self.obszar, constants.MAX_TEMP_POMIESZCZENIA, self.logger))
        if not self.__max_temp_pomieszczenia:
            self.__max_temp_pomieszczenia = DEFAULT_TEMP_MAX

        ogrzakt = bool(odczytaj_parametr_konfiguracji(self.obszar, constants.OGRZEWANIE_AKTYWNE, self.logger))
        self.__ogrzewanie_aktywne = False
        if ogrzakt in ['True', 'true', 'TRUE']:
            self.__ogrzewanie_aktywne = True

        self._tabela = []
        self._tabela.append(Pomieszczenie(self.obszar, OGRZ_ZOSIA, self.__min_temp_pomieszczenia, self.__max_temp_pomieszczenia,
                                          czas_do_alarmu=self.__czas_do_alarmu, logger=self.logger))
        self._tabela.append(Pomieszczenie(self.obszar, OGRZ_SALON, self.__min_temp_pomieszczenia, self.__max_temp_pomieszczenia,
                                          czas_do_alarmu=self.__czas_do_alarmu, logger=self.logger))
        self._tabela.append(Pomieszczenie(self.obszar, OGRZ_STROZOWKA, self.__min_temp_pomieszczenia, self.__max_temp_pomieszczenia,
                                          czas_do_alarmu=self.__czas_do_alarmu, logger=self.logger))
        self._tabela.append(Pomieszczenie(self.obszar, OGRZ_PIOTREK, self.__min_temp_pomieszczenia, self.__max_temp_pomieszczenia,
                                          czas_do_alarmu=self.__czas_do_alarmu, logger=self.logger))
        self._tabela.append(Pomieszczenie(self.obszar, OGRZ_GARAZ, self.__min_temp_pomieszczenia, self.__max_temp_pomieszczenia,
                                          czas_do_alarmu=self.__czas_do_alarmu, logger=self.logger))
        self._tabela.append(Pomieszczenie(self.obszar, OGRZ_SYPIALNIA, self.__min_temp_pomieszczenia, self.__max_temp_pomieszczenia,
                                          czas_do_alarmu=self.__czas_do_alarmu, logger=self.logger))
        self._tabela.append(Pomieszczenie(self.obszar, OGRZ_POM_NAD_GARAZEM, self.__min_temp_pomieszczenia, self.__max_temp_pomieszczenia,
                                          czas_do_alarmu=self.__czas_do_alarmu, logger=self.logger))
        self.dodaj_przekaznik(OGRZ_ZOSIA, OGRZ_ZOSIA_PIN)
        self.dodaj_przekaznik(OGRZ_SALON, OGRZ_SALON_PIN)
        self.dodaj_przekaznik(OGRZ_STROZOWKA, OGRZ_STROZOWKA_PIN)
        self.dodaj_przekaznik(OGRZ_PIOTREK, OGRZ_PIOTREK_PIN)
        self.dodaj_przekaznik(OGRZ_GARAZ, OGRZ_GARAZ_PIN)
        self.dodaj_przekaznik(OGRZ_SYPIALNIA, OGRZ_SYPIALNIA_PIN)
        self.dodaj_przekaznik(OGRZ_POM_NAD_GARAZEM, OGRZ_POM_NAD_GARAZEM_PIN)

        #sprawdzenie w petli czy nie sa zaplanowane wakacje, jak sa to odczytac ta pozycje jak nie to zerujemy wakacje
        a = self.petla.pozycja_po_obszarze_nazwie(self.obszar, TRYB_WAKACJE)
        if a:
            self.wakacje_trwaja = a.get_stan()
            self.wakacje_zaplanowane = True
            self.wakacje_ts_start = a.get_tsstart()
            self.wakacje_ts_stop = a.get_tsstop()
        else:
            self.wakacje_trwaja = False
            self.wakacje_zaplanowane = False
            self.wakacje_ts_start = int(time())
            self.wakacje_ts_stop = int(time())
#TODO powyzsze powtarzac za kazdym przebiegiem bo moga byc wakazcje w kolejncyh zaplanowaniach


    def dzialanie_petli(self, nazwa, stan, pozycjapetli):
        if nazwa == TRYB_WAKACJE:
            #self.logger.info('Ustawiane sa wakacje z petli: ' + str(stan) + '. tylko ts: ' + str(tylko_aktualizuj_ts))
            if stan:
                for j in self._tabela:  # type: Pomieszczenie
                    self.petla.aktywuj_pozycje_nazwa(self.obszar, j.get_nazwa(), False)
                    j.zadaj_temp(j.get_temp_min())
                self.logger.info(self.obszar, 'Uruchamiam wakacje')
                self.wakacje_trwaja = True
            else:
                for j in self._tabela:  # type: Pomieszczenie
                    self.petla.aktywuj_pozycje_nazwa(self.obszar, j.get_nazwa(), True)
                self.logger.info(self.obszar, 'Koniec wakacji')
                self.wakacje_trwaja = False
                self.wakacje_zaplanowane = False
            self.logger.info(self.obszar, 'Resetuje TS w dzialanie petli WAKACJE')
            self.resetuj_ts()
            return
        if nazwa == PETLA_STERUJ_CYKLICZNIE:
            if stan:
                self.steruj_cyklicznie(stan)
            return
        if stan:
            #czyli trzeba ustawic temperature
            pom = self.pomieszczenie_po_nazwie(nazwa)   # type: Pomieszczenie
            pom.zadaj_temp(pozycjapetli.get_wartosc())
            pom.doczasu = str(pozycjapetli.do_ktorej_godziny())
            pom.odczasu = str(pozycjapetli.od_ktorej_godziny())
            self.logger.info(self.obszar, 'Zadalem temperature ' + str(nazwa) + ' na ' + str(pozycjapetli.get_wartosc()))

    def steruj_cyklicznie(self, stan):
        #funckja ma byc wywolywana z petli, o nazwie 'steruj_cyklicznie'
        if not self.__ogrzewanie_aktywne:
            for a in self._tabela:  # type: Pomieszczenie
                #self.logger.info(self.obszar, 'Wylaczam wszystkie bo ogrzewanie nieaktywne')
                self.wewy.wyjscia.ustaw_przekaznik_nazwa(a.get_nazwa(), False)
            return
        for a in self._tabela:  # type: Pomieszczenie
            #sprawdza czy trzeba grzac
            if a.steruj(histereza=self.__histereza):
                if not self.wewy.wyjscia.stan_przekaznika_nazwa(a.get_nazwa()):
                    self.wewy.wyjscia.ustaw_przekaznik_nazwa(a.get_nazwa(), True)  # wlacza ogrzewanie
                    self.logger.info(self.obszar, 'Wlaczam grzanie: ' + a.get_nazwa() + ' temp.akt: ' + str(a.get_temp_aktualna()) +
                                     ' temp.zadana: ' + str(a.get_temp_zadana()))
                    self.resetuj_ts()
            else:
                if self.wewy.wyjscia.stan_przekaznika_nazwa(a.get_nazwa()):
                    self.wewy.wyjscia.ustaw_przekaznik_nazwa(a.get_nazwa(), False)  # wylacza ogrzewanie
                    self.logger.info(self.obszar, 'Wylaczam grzanie: ' + a.get_nazwa() + ", przy temp. " + str(a.get_temp_aktualna()))
                    self.resetuj_ts()

    def procesuj_polecenie(self, **params):
        rodzaj = Obszar.procesuj_polecenie(self, **params)
        if rodzaj == constants.KOMENDA:
            if params[constants.KOMENDA] == constants.KOMENDA_ZADAJ_TEMP:
                #szukamy ktore to pomieszczenie, w parametr 1
                #w parametr 2 ma byc zadana temperatura
                #resetujemy TS ogrzewania
                for j in self._tabela:  # type: Pomieszczenie
                    if constants.NAZWA in params:
                        if constants.POLE_TEMP_ZADANA in params:
                            if j.get_nazwa() == params[constants.NAZWA]:
                                if j.zadaj_temp(params[constants.POLE_TEMP_ZADANA]):
                                    self.resetuj_ts()
            elif params[constants.KOMENDA] == constants.KOMENDA_PODAJ_TEMP:
                #szukamy ktore to pomieszczenie, w parametr 1
                #w parametr 2 ma byc odczytana przez NodeMCU temperatura
                #resetujemy TS ogrzewania
                if constants.NAZWA in params:
                    pom = self.pomieszczenie_po_nazwie(params[constants.NAZWA])
                    if pom:
                        if constants.POLE_TEMP_AKTUALNA in params:
                            if pom.podaj_temp(params[constants.POLE_TEMP_AKTUALNA]):
                                self.resetuj_ts()
                                zapisz_temp_w_logu(self.log_temp, pom.get_nazwa(), pom.get_temp_aktualna())
            elif params[constants.KOMENDA] == constants.KOMENDA_STATUS_POMIESZCZENIA:
                # przygotowanie statusu tylko z jednym pomieszczeniem ale jednoczesnie caly
                if constants.NAZWA in params:
                    self.aktualizuj_biezacy_stan(odbiornik_pomieszczenie=params[constants.NAZWA])
                    self.procesuje.release()
                    return skonstruuj_odpowiedzV2OK(constants.KOMENDA_STATUS_POMIESZCZENIA, self._biezacy_stan, constants.OBSZAR_OGRZ)
            elif params[constants.KOMENDA] == constants.KOMENDA_WAKACJE:
                if constants.POLE_WAKACJE in params:
                    self.ustaw_tryb_wakacje(params[constants.POLE_WAKACJE])
                self.logger.info(self.obszar, 'Resetuje TS bo jest komenda wakacje ale nie ma pola wakacje: ' + str(params))
                self.resetuj_ts()
            elif params[constants.KOMENDA] == constants.KOMENDA_AKTYWUJ_OGRZEWANIE:
                if constants.POLE_STAN in params:
                    if params[constants.POLE_STAN]:
                        self.__ogrzewanie_aktywne = True
                    else:
                        self.__ogrzewanie_aktywne = False
                    self.logger.info(self.obszar, 'Aktywacja ogrzewania: ' + str(self.__ogrzewanie_aktywne))
                    self.steruj_cyklicznie(self.__ogrzewanie_aktywne)
                    self.resetuj_ts()
                    THutils.zapisz_parametr_konfiguracji(self.obszar, constants.OGRZEWANIE_AKTYWNE,
                                                         self.__ogrzewanie_aktywne, self.logger)
        return Obszar.odpowiedz(self)


    def ustaw_tryb_wakacje(self, polecenie):
        try:
            stan = polecenie[constants.POLE_WAKACJE]
            od = polecenie[constants.POLE_WAKACJE_OD_CZASU]
            do = polecenie[constants.POLE_WAKACJE_DO_CZASU]
        except (KeyError, AttributeError) as serr:
            self.logger.warning(self.obszar, 'Bledna komenda ogrzewania wakacje: ' + str(polecenie))
            #TODO rturn bledu powinien wracac jako return JSON-RPC
            return
        if stan:    #ustawiamy tryb wakacji
            self.wakacje_ts_start = od
            self.wakacje_ts_stop = do
            self.logger.info(self.obszar, 'Otrzymalem polecenie ustawienia wakacji, od: ' + str(od) + " do " + str(do))
            self.petla.aktywuj_pozycje_nazwa(self.obszar, TRYB_WAKACJE, False)  #usuniecie poprzedniego wpisu
            self.petla.dodaj_jednorazowy_od_godz_do_godz(TRYB_WAKACJE, self.obszar, od, do, dzialanie=self.dzialanie_petli)
            self.wakacje_zaplanowane = True
        else:   #deaktywujemy tryb wakacji
            self.logger.info(self.obszar, 'Usuwam wakacje z petli')
            self.petla.aktywuj_pozycje_nazwa(self.obszar, TRYB_WAKACJE, False)
            self.wakacje_zaplanowane = False

    def pomieszczenie_po_nazwie(self, nazwa):
        for j in self._tabela:
            if j.get_nazwa() == nazwa:
                return j
        return None

    #def get_biezacy_stan(self):
    #    self.aktualizuj_biezacy_stan()
    #    return self._biezacy_stan

    def aktualizuj_biezacy_stan(self, odbiornik_pomieszczenie=None):
        #TODO zaimplementowac limitowanie po odbiorniku w pozostalych obszarach
        pozycje = []
        for j in self._tabela:  # type: Pomieszczenie
            if odbiornik_pomieszczenie:
                if j.get_nazwa() == odbiornik_pomieszczenie:
                    pozycje.append(j.do_listy())
            else:
                pozycje.append(j.do_listy())
        self._biezacy_stan = {constants.TS: self.get_ts(),
                              constants.OGRZEWANIE_AKTYWNE: self.__ogrzewanie_aktywne,
                              constants.CZAS: self.godzina_minuta(),
                              constants.DATA: self.zwroc_date(),
                              constants.POLE_WAKACJE: self.wakacje_trwaja,
                              constants.POLE_WAKACJE_ZAPLANOWANE: self.wakacje_zaplanowane,
                              constants.POLE_WAKACJE_OD_CZASU: self.wakacje_ts_start,
                              constants.POLE_WAKACJE_DO_CZASU: self.wakacje_ts_stop,
                              constants.CYKLE: self.petla.pozycje_do_listy(obszar=self.obszar,
                                                                           odbiornik_pomieszczenie=odbiornik_pomieszczenie),
                              constants.POLE_POMIESZCZENIA: pozycje}

class Pomieszczenie:

    def __init__(self, obszar, nazwa, temp_min, temp_max, czas_do_alarmu=CZAS_DO_ALARMU, logger=None):
        self.__obszar = obszar
        self.__nazwa = nazwa
        self.__tempMin = temp_min
        self.__tempMax = temp_max
        self.__tempZadana = temp_min
        self.__tempAktualna = temp_max
        self.__blad_czujnika = False    #true jesli przez godzine nie bylo zmiany stanu
        self.__ts_aktualnej = 0    #ostatnie odczyt podany przez czujnik
        self.__czas_do_alarmu = czas_do_alarmu
        self.doczasu = ""     #tylko informacyjnie ustawia petla czasowa, pole tekstowe
        self.odczasu = ""  # tylko informacyjnie ustawia petla czasowa, pole tekstowe
        self.__grzeje = False #true jest aktualnie grzeje, czyli przekaznik wlaczony
        self.__logger = logger

    def steruj(self, histereza=HISTEREZA):   #steruje zaworami w zaleznosci od zadanej i aktualnej temperatury
        #zwraca true jesli trzeba otworzyc zawor

        # aktualizacja bledu, jesli przez jakis czas nie bylo zmiany temp to znaczy, ze czujnik nie podaje
        if int(self.__ts_aktualnej + self.__czas_do_alarmu) < int(time()):
            if not self.__blad_czujnika:
                if self.__logger:
                    self.__logger.warning(self.__obszar, 'Blad czujnika temperatury: ' + self.__nazwa)
            self.__blad_czujnika = True

            self.__grzeje = False
            return self.__grzeje  # jesli jest blad czujnika to wylacz ogrzewanie
        else:
            self.__blad_czujnika = False
        # sprawdzamy czy aktualna jest nizsza, jak tak to otwieramy wewy
        if self.__tempAktualna >= self.__tempZadana:
            self.__grzeje = False
            #print (self.__nazwa + ', zadana: ' + str(
            #    self.__tempZadana) + ', aktualna: ' + str(self.__tempAktualna) + 'Nie trzeba grzac')
        else:
            if self.__grzeje:
                return self.__grzeje
            if self.__tempAktualna + histereza < self.__tempZadana:
                self.__grzeje = True
        return self.__grzeje

    def podaj_temp(self, temp,):
        # zwraca Tru jesli przyjal nowa temperature
        wej = round(float(temp), 1)
        if wej == self.__tempAktualna:
            return False    #taka sama temperatura wiec nie ustawiam nowej, nie zmieniam TSa
        if round(abs(wej-self.__tempAktualna)*10) == 1:
            c = int(time()) - self.__ts_aktualnej
            if  c < CZAS_OPOZNIENIA_PRZYJMOWANIA_01_STOPNIA:
                return False    #mniejsza lub rowna 0.1 stopnia i nie minela minuta
        self.__ts_aktualnej = int(time())
        self.__tempAktualna = round(float(temp), 1)
        return True

    def zadaj_temp(self, temp_zadana):
        #sprawdzic czy wieksza niz max i czy mnijesza niz min
        a = round(float(temp_zadana),1)
        if a > self.__tempMax:
            return False
        if a < self.__tempMin:
            return False
        #jesli w granicach to przypisac do self.tempZadana
        if self.__logger:
            self.__logger.info(self.__obszar, 'Zadalem temperature ' + self.__nazwa + ' na ' + str(temp_zadana))
        self.__tempZadana = a
        return True

    def get_nazwa(self):
        return self.__nazwa

    def get_temp_min(self):
        return self.__tempMin

    def get_temp_max(self):
        return self.__tempMax

    def get_temp_aktualna(self):
        return self.__tempAktualna

    def get_temp_zadana(self):
        return self.__tempZadana

    def get_ts_podania_temperatury(self):
        return self.__ts_aktualnej

    def do_listy(self):
        return {constants.NAZWA: self.__nazwa,
                constants.POLE_TEMP_MIN: self.__tempMin,
                constants.POLE_TEMP_MAX: self.__tempMax,
                constants.POLE_TEMP_GRZEJE: self.__grzeje,
                constants.POLE_TEMP_AKTUALNA: self.__tempAktualna,
                constants.POLE_TEMP_ZADANA: self.__tempZadana,
                #constants.POLE_TS_AKTUALNEJ: self.__ts_aktualnej,
                constants.POLE_OD_CZASU: self.odczasu,
                constants.POLE_DO_CZASU: self.doczasu,
                constants.POLE_BLAD_CZUJNIKA: self.__blad_czujnika
                }
