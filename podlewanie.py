import THutils
import wejsciawyjscia
import petlaczasowa
import pigpio
import constants
from Obszar import Obszar

NAZWA_SEKCJA1 = 'Sekcja1'
NAZWA_SEKCJA2 = 'Sekcja2'
NAZWA_SEKCJA3 = 'Sekcja3'
NAZWA_SEKCJA4 = 'Sekcja4'
NAZWA_SEKCJA5 = 'Sekcja5'
NAZWA_SEKCJA6 = 'Sekcja6'
NAZWA_SEKCJA7 = 'Sekcja7'

PIN_SEKCJA1 = 0
PIN_SEKCJA2 = 1
PIN_SEKCJA3 = 2
PIN_SEKCJA4 = 3
PIN_SEKCJA5 = 4
PIN_SEKCJA6 = 5
PIN_SEKCJA7 = 6

DEF_CZAS_ZALACZENIA_SEKCJI = 3600


class Podlewanie(Obszar):
    def __init__(self,
                 wewy,  # type: wejsciawyjscia.WejsciaWyjscia
                 petla,  # type: petlaczasowa.PetlaCzasowa
                 firebase_callback=None):

        Obszar.__init__(self, wewy, petla, constants.OBSZAR_PODL, firebase_callback=firebase_callback,
                        rodzaj_komunikatu_firebase=constants.RODZAJ_KOMUNIKATU_STAN_PODLEWANIA,
                        callback_przekaznika_wyjscia=self.aktualizuj_biezacy_stan,
                        dzialanie_petli=self.dzialanie_petli)

        self.gpio_pigpio = pigpio.pi()
        # TODO pigpio usunac, powinno byc w wewy

        self.dodaj_przekaznik(NAZWA_SEKCJA1, PIN_SEKCJA1, def_czas_zalaczenia=DEF_CZAS_ZALACZENIA_SEKCJI)
        self.dodaj_przekaznik(NAZWA_SEKCJA2, PIN_SEKCJA2, def_czas_zalaczenia=DEF_CZAS_ZALACZENIA_SEKCJI)
        self.dodaj_przekaznik(NAZWA_SEKCJA3, PIN_SEKCJA3, def_czas_zalaczenia=DEF_CZAS_ZALACZENIA_SEKCJI)
        self.dodaj_przekaznik(NAZWA_SEKCJA4, PIN_SEKCJA4, def_czas_zalaczenia=DEF_CZAS_ZALACZENIA_SEKCJI)
        self.dodaj_przekaznik(NAZWA_SEKCJA5, PIN_SEKCJA5, def_czas_zalaczenia=DEF_CZAS_ZALACZENIA_SEKCJI)
        self.dodaj_przekaznik(NAZWA_SEKCJA6, PIN_SEKCJA6, def_czas_zalaczenia=DEF_CZAS_ZALACZENIA_SEKCJI)
        self.dodaj_przekaznik(NAZWA_SEKCJA7, PIN_SEKCJA7, def_czas_zalaczenia=DEF_CZAS_ZALACZENIA_SEKCJI)
        # self.prze.odczytaj_przekazniki_z_konfiguracji()

        self.poprzedni_stan_plywak_studnia = 0
        self.poprzedni_stan_plywak_szambo = 0
        self.plywak_studnia = 0
        self.plywak_szambo = 0

        a = THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_PODL, 'podlewanie_aktywne', self.logger)
        if a in ['True', 'true', 'TRUE']:
            self.podlewanie_aktywne = True
        else:
            self.podlewanie_aktywne = False

        self.odczytaj_konf()

        self.wewy.wyjscia.wylacz_wszystkie_przekazniki(constants.OBSZAR_PODL)
        self.aktualizuj_biezacy_stan()
        self.logger.info('Zainicjowalem klase podlewanie.')

    def procesuj_polecenie(self, komenda, parametr1, parametr2):
        # TODO pozmieniac nazwy operacji aby byly spojne pomiedzy podlewaniem a oswietleniem i ogrzewaniem
        if komenda == 'WP':
            if parametr1 == constants.PARAMETR_WLACZ:
                self.aktywuj_podlewania(True)
            else:
                self.aktywuj_podlewania(False)
            self.resetuj_ts()
        #elif komenda == constants.KOMENDA_ODCZYTAJ_CYKLE_Z_KONFIGURACJI:
        #    self.petla.odczytaj_cykle_z_konfiguracji()
        self.aktualizuj_biezacy_stan()
        return Obszar.procesuj_polecenie(self, komenda, parametr1, parametr2)

    def aktywuj_podlewania(self, stan):
        # TODO ponizzssa logika nie dziala, zrobic tak aby tylko kiedy jest deaktywowane to wylaczalor
        self.petla.aktywuj_wszystkie_pozycja_w_obszarze(self.obszar, stan)
        if not stan:
            self.petla.dzialaj_na_wszystkich_pozycjach(self.obszar, stan)
        self.logger.info('Uaktywniono podlewanie: ' + str(stan))
        self.podlewanie_aktywne = stan
        THutils.zapisz_parametr_konfiguracji(self.obszar, 'podlewanie_aktywne', stan, self.logger)
        self.aktualizuj_biezacy_stan()

    def dzialanie_petli(self, nazwa, stan, tylko_aktualizuj_ts=False):
        if tylko_aktualizuj_ts:
            self.resetuj_ts()
            self.aktualizuj_biezacy_stan()
            self.aktualizuj_plywaki()
            return
        # wywolywane gdy petla nakazala zmiane stanu
        if self.podlewanie_aktywne:
            stan_poprzzedni = self.wewy.wyjscia.stan_przekaznika_nazwa(nazwa)
            self.wewy.wyjscia.ustaw_przekaznik_nazwa(nazwa, stan)
            self.resetuj_ts()
            self.aktualizuj_biezacy_stan()
            if self.wewy.wyjscia.stan_przekaznika_nazwa(nazwa) != stan_poprzzedni:
                self.logger.info('Podlewanie ' + nazwa + ', stan: ' + str(stan))
                self.resetuj_ts()
                self.aktualizuj_biezacy_stan()
                self.odpal_firebase()

    def aktualizuj_plywaki(self):
        # wywolywane za kazdym przebiegiem petli, bez wzgledu na to czy byla zmiana stanu czy nie
        self.odczytaj_stan_plywakow()
        if self.poprzedni_stan_plywak_studnia != self.plywak_studnia:
            self.logger.info('Podlewanie: Plywak Studnia: ' + str(self.plywak_studnia))
            self.poprzedni_stan_plywak_studnia = self.plywak_studnia
            self.resetuj_ts()
        if self.poprzedni_stan_plywak_szambo != self.plywak_szambo:
            self.logger.info('Podlewanie: Plywak Szambo: ' + str(self.plywak_szambo))
            self.poprzedni_stan_plywak_szambo = self.plywak_szambo
            self.resetuj_ts()
        self.aktualizuj_biezacy_stan()

    def odczytaj_stan_plywakow(self):
        # TODO pigpio nie ma byc uzywane do odczytu plywakow tylko mcp_wejscia
        self.plywak_studnia = self.gpio_pigpio.read(self.plywak_studnia_pin)
        self.plywak_szambo = self.gpio_pigpio.read(self.plywak_szambo_pin)
        self.aktualizuj_biezacy_stan()

    def aktualizuj_biezacy_stan(self):
        self._biezacy_stan = {'plywak_studnia': THutils.xstr(self.plywak_studnia),
                                              'plywak_szambo': THutils.xstr(self.plywak_szambo),
                                              'podlewanie_aktywne': self.podlewanie_aktywne,
                                              constants.TS: self.ts,
                                              constants.CYKLE: self.petla.pozycje_do_listy(
                                                  obszar=constants.OBSZAR_PODL),
                                              constants.ODBIORNIKI: self.wewy.wyjscia.pozycje_do_listy(
                                                  constants.OBSZAR_PODL)}

    def odczytaj_konf(self):
        self.max_wilg = int(THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_PODL, 'MAX_WILG', self.logger))
        self.plywak_studnia_pin = int(
            THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_PODL, 'PLYWAK_STUDNIA_PIN', self.logger))
        self.plywak_szambo_pin = int(
            THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_PODL, 'PLYWAK_SZAMBO_PIN', self.logger))
