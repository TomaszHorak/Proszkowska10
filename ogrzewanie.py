from __future__ import print_function
from Obszar import Obszar
import constants
import threading

CZAS_PRZERWY_DZIALANIA = 5  #w sekundach
DEFAULT_TEMP_MIN = 17.0
DEFAULT_TEMP_MAX = 24.5

HISTEREZA = 0.2

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

#TODO komendy do conactants
ZADAJ_TEMP = 'zadaj_temp'
PODAJ_TEMP = 'podaj_temp'   #temperatura odczytana przez NodeMCU i przeslana do Raspberry
TRYB_WAKACJE = 'wakacje'
PETLA_STERUJ_CYKLICZNIE = 'steruj_cyklicznie'
#TODO parametry do pliku ini

class Ogrzewanie(Obszar):
    def __init__(self, wewy, petla):
        Obszar.__init__(self, wewy, petla, constants.OBSZAR_OGRZ,
                        rodzaj_komunikatu=constants.RODZAJ_KOMUNIKATU_STAN_OGRZEWANIA,
                        dzialanie_petli=self.dzialanie_petli)
        self._tabela = []
        self._tabela.append(Pomieszczenie(OGRZ_ZOSIA, DEFAULT_TEMP_MIN, DEFAULT_TEMP_MAX))
        self._tabela.append(Pomieszczenie(OGRZ_SALON, DEFAULT_TEMP_MIN, DEFAULT_TEMP_MAX))
        self._tabela.append(Pomieszczenie(OGRZ_STROZOWKA, DEFAULT_TEMP_MIN, DEFAULT_TEMP_MAX))
        self._tabela.append(Pomieszczenie(OGRZ_PIOTREK, DEFAULT_TEMP_MIN, DEFAULT_TEMP_MAX))
        self._tabela.append(Pomieszczenie(OGRZ_GARAZ, DEFAULT_TEMP_MIN, DEFAULT_TEMP_MAX))
        self._tabela.append(Pomieszczenie(OGRZ_SYPIALNIA, DEFAULT_TEMP_MIN, DEFAULT_TEMP_MAX))

        self.dodaj_przekaznik(OGRZ_ZOSIA, OGRZ_ZOSIA_PIN)
        self.dodaj_przekaznik(OGRZ_SALON, OGRZ_SALON_PIN)
        self.dodaj_przekaznik(OGRZ_STROZOWKA, OGRZ_STROZOWKA_PIN)
        self.dodaj_przekaznik(OGRZ_PIOTREK, OGRZ_PIOTREK_PIN)
        self.dodaj_przekaznik(OGRZ_GARAZ, OGRZ_GARAZ_PIN)
        self.dodaj_przekaznik(OGRZ_SYPIALNIA, OGRZ_SYPIALNIA_PIN)

        self.wakacje = False

#        self.steruj_cyklicznie()
        return

    def dzialanie_petli(self, nazwa, stan, pozycjapetli, tylko_aktualizuj_ts=False):
        if nazwa == TRYB_WAKACJE:
            self.ustaw_tryb_wakacje(stan)
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

    def steruj_cyklicznie(self, stan):
        #funckja ma byc wywolywana z petli, o nazwie 'steruj_cyklicznie'
        #print("Wywolalem steruj cyklicznie: " + str(stan))
        for a in self._tabela:  # type: Pomieszczenie
            if a.steruj():
                if not self.wewy.wyjscia.stan_przekaznika_nazwa(a.get_nazwa()):
                    self.wewy.wyjscia.ustaw_przekaznik_nazwa(a.get_nazwa(), True)  # wlacza ogrzewanie
                    self.logger.info('Wlaczam grzanie: ' + a.get_nazwa() + ' temp.akt: ' + str(a.get_temp_aktualna()) +
                                     ' temp.zadana: ' + str(a.get_temp_zadana()))
                    self.resetuj_ts()
            else:
                if self.wewy.wyjscia.stan_przekaznika_nazwa(a.get_nazwa()):
                    self.wewy.wyjscia.ustaw_przekaznik_nazwa(a.get_nazwa(), False)  # wylacza ogrzewanie
                    self.logger.info('Wylaczam grzanie: ' + a.get_nazwa())
                    self.resetuj_ts()
#        t = threading.Timer(CZAS_PRZERWY_DZIALANIA, self.steruj_cyklicznie)
#        t.start()


    def procesuj_polecenie(self, komenda, parametr1, parametr2):
        if komenda == ZADAJ_TEMP:
            #szukamy ktore to pomieszczenie, w parametr 1
            #w parametr 2 ma byc zadana temperatura
            #resetujemy TS ogrzewania
            for j in self._tabela:  # type: Pomieszczenie
                if j.get_nazwa() == parametr1:
                    j.zadaj_temp(parametr2)
                self.resetuj_ts()
        elif komenda == PODAJ_TEMP:
            #szukamy ktore to pomieszczenie, w parametr 1
            #w parametr 2 ma byc odczytana przez NodeMCU temperatura
            #resetujemy TS ogrzewania
            for j in self._tabela:  # type: Pomieszczenie
                if j.get_nazwa() == parametr1:
                    j.podaj_temp(parametr2)
                self.resetuj_ts()
        elif komenda == TRYB_WAKACJE:
            #TODO usunac wszystkie 1 i 0 oraz wlacz wylacz i przejsc na true|false
            self.ustaw_tryb_wakacje(parametr1)
            self.resetuj_ts()
        self.aktualizuj_biezacy_stan()
        return Obszar.procesuj_polecenie(self, komenda, parametr1, parametr2)

    def ustaw_tryb_wakacje(self, stan):
        if stan == constants.PARAMETR_WLACZ:
            self.petla.aktywuj_wszystkie_pozycja_w_obszarze(self.obszar, False)
            for j in self._tabela:  # type: Pomieszczenie
                j.zadaj_temp(j.get_temp_min())
            self.wakacje = True
        elif stan == constants.PARAMETR_WYLACZ:
            self.wakacje = False
            self.petla.aktywuj_wszystkie_pozycja_w_obszarze(self.obszar, True)

    def pomieszczenie_po_nazwie(self, nazwa):
        for j in self._tabela:
            if j.get_nazwa() == nazwa:
                return j
        return None

    def aktualizuj_biezacy_stan(self):
        pozycje = []
        for j in self._tabela:  # type: Pomieszczenie
            pozycje.append(j.do_listy())
        self._biezacy_stan = {
            #constants.CYKLE: self.petla.pozycje_do_listy(obszar=self.obszar),
                              constants.POLE_POMIESZCZENIA: pozycje,
                              constants.TS: self.ts,
                              constants.CZAS: self.godzina_minuta(),
                              constants.POLE_WAKACJE: self.wakacje}

class Pomieszczenie:
    def __init__(self, nazwa, temp_min, temp_max):
        self.__nazwa = nazwa
        self.__tempMin = temp_min
        self.__tempMax = temp_max
        self.__tempZadana = temp_min
        self.__tempAktualna = temp_max
        self.doczasu = ""     #tylko informacyjnie ustawia petla czasowa, pole tekstowe
        self.odczasu = ""  # tylko informacyjnie ustawia petla czasowa, pole tekstowe
        self.__grzeje = False #true jest aktualnie grzeje, czyli przekaznik wlaczony

    def steruj(self):   #steruje zaworami w zaleznosci od zadanej i aktualnej temperatury
        #zwraca true jesli trzeba otworzyc zawor
        # sprawdzamy czy aktualna jest nizsza, jak tak to otwieramy wewy
        if self.__tempAktualna >= self.__tempZadana:
            self.__grzeje = False
            #print (self.__nazwa + ', zadana: ' + str(
            #    self.__tempZadana) + ', aktualna: ' + str(self.__tempAktualna) + 'Nie trzeba grzac')
        else:
            if self.__grzeje:
                return self.__grzeje
            if self.__tempAktualna + HISTEREZA < self.__tempZadana:
                self.__grzeje = True
        return self.__grzeje

    def podaj_temp(self, temp):
        self.__tempAktualna = round(float(temp), 1)

    def zadaj_temp(self, temp_zadana):
        #sprawdzic czy wieksza niz max i czy mnijesza niz min
        a = round(float(temp_zadana),1)
        if a > self.__tempMax:
            return False
        if a < self.__tempMin:
            return False

        #jesli w granicach to przypisac do self.tempZadana
        self.__tempZadana = a

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

    def do_listy(self):
        return {constants.NAZWA: self.__nazwa,
                constants.POLE_TEMP_MIN: self.__tempMin,
                constants.POLE_TEMP_MAX: self.__tempMax,
                constants.POLE_TEMP_GRZEJE: self.__grzeje,
                constants.POLE_TEMP_AKTUALNA: self.__tempAktualna,
                constants.POLE_TEMP_ZADANA: self.__tempZadana,
                constants.POLE_OD_CZASU: self.odczasu,
                constants.POLE_DO_CZASU: self.doczasu
                }
