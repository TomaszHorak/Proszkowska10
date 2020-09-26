import THutils
import przekazniki_BCM
import petlaczasowa
import pigpio
import logging
import firebasenotification
import thread
import constants
import time
from copy import deepcopy

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

class Podlewanie:

    def __init__(self, mcp, firebase_callback=None):
        self.logger = logging.getLogger(constants.NAZWA_LOGGERA)
        self.stan_podlewania = {}
        #self.notyfikacja_firebase = firebasenotification.Firebasenotification()
        self.ts = int(time.time())
        self.firebase_callback = firebase_callback
        self.gpio_pigpio = pigpio.pi()
        #TODO dodac ponizsze do konfiguracji podlewania
        self.prze = przekazniki_BCM.PrzekaznikiBCM(mcp, self.aktualizuj_biezacy_stan_podlewania,
                                                   obszar=constants.OBSZAR_PODL)
        self.prze.dodaj_przekaznik(NAZWA_SEKCJA1, PIN_SEKCJA1, def_czas_zalaczenia=DEF_CZAS_ZALACZENIA_SEKCJI)
        self.prze.dodaj_przekaznik(NAZWA_SEKCJA2, PIN_SEKCJA2, def_czas_zalaczenia=DEF_CZAS_ZALACZENIA_SEKCJI)
        self.prze.dodaj_przekaznik(NAZWA_SEKCJA3, PIN_SEKCJA3, def_czas_zalaczenia=DEF_CZAS_ZALACZENIA_SEKCJI)
        self.prze.dodaj_przekaznik(NAZWA_SEKCJA4, PIN_SEKCJA4, def_czas_zalaczenia=DEF_CZAS_ZALACZENIA_SEKCJI)
        self.prze.dodaj_przekaznik(NAZWA_SEKCJA5, PIN_SEKCJA5, def_czas_zalaczenia=DEF_CZAS_ZALACZENIA_SEKCJI)
        self.prze.dodaj_przekaznik(NAZWA_SEKCJA6, PIN_SEKCJA6, def_czas_zalaczenia=DEF_CZAS_ZALACZENIA_SEKCJI)
        self.prze.dodaj_przekaznik(NAZWA_SEKCJA7, PIN_SEKCJA7, def_czas_zalaczenia=DEF_CZAS_ZALACZENIA_SEKCJI)
        #self.prze.odczytaj_przekazniki_z_konfiguracji()

        self.poprzedni_stan_plywak_studnia = 0
        self.poprzedni_stan_plywak_szambo = 0
        self.plywak_studnia = 0
        self.plywak_szambo = 0

        a = THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_PODL, 'podlewanie_aktywne', self.logger)
        if a in ['True', 'true', 'TRUE']:
            self.podlewanie_aktywne = True
        else:
            self.podlewanie_aktywne = False

        self.glowna_tabela_podlewania = petlaczasowa.PetlaCzasowa(constants.OBSZAR_PODL,
                                                                  self.dzialanie_petli,
                                                                  callback=self.przebieg_petli,
                                                                  logger=self.logger)
        #TODO do parametrow czas_uruchomienia_petli
        # TODO co to jest ponizsze?
        self.czas_odczytu_konfig = 6000
        self.odczytaj_konf()
        self.glowna_tabela_podlewania.aktywuj_petle(True)
        self.prze.wylacz_wszystkie_przekazniki()
        self.aktualizuj_biezacy_stan_podlewania()
        self.logger.info('Zainicjowalem klase podlewanie.')

    def procesuj_polecenie(self,komenda, parametr1, parametr2):
        #TODO pozmieniac nazwy operacji aby byly spojne pomiedzy podlewaniem a oswietleniem i ogrzewaniem
        if komenda == constants.TOGGLE_ODBIORNIK_NAZWA:
            if parametr2 == constants.PARAMETR_WYLACZ:
                self.glowna_tabela_podlewania.aktywuj_pozycje_nazwa(parametr1, False,
                                                                    tylko_jednorazowe=True)
                self.prze.ustaw_przekaznik_nazwa(parametr1, False)
                self.logger.info('Wylaczylem sekcje ' + parametr1)
            else:
                if int(parametr2) == 0 or parametr2 == constants.PARAMETR_WLACZ:
                    czas = self.prze.przekaznik_po_nazwie(parametr1).get_defczaszalaczenia()
                    self.glowna_tabela_podlewania.dodaj_do_tabeli_jednorazowy_na_czas(str(parametr1), czas)
                    self.logger.info('Podlewanie ' + parametr1 + ' wlaczylem na czas: ' + czas)
                else:
                    self.glowna_tabela_podlewania.dodaj_do_tabeli_jednorazowy_na_czas(str(parametr1), int(parametr2))
                    self.logger.info('Podlewanie ' + parametr1 + ' wlaczylem na czas: ' + parametr2)
            self.ts = int(time.time())
            self.odpal_firebase()
        elif komenda == constants.AKTYWACJA_SCHEMATU:  # odbiornik w petli sterowanie, aktywacja schematu
            if parametr2 == constants.PARAMETR_WLACZ:
                wl = True
            else:
                wl = False
            self.glowna_tabela_podlewania.aktywuj_pozycje_nazwa(parametr1, wl)
            self.ts = int(time.time())
            self.logger.info('Aktywacja petli podlewania ' + str(parametr1) + '. Stan: ' + str(wl))
        elif komenda == 'WP':
            if parametr1 == constants.PARAMETR_WLACZ:
                self.aktywuj_podlewania(True)
            else:
                self.aktywuj_podlewania(False)
            self.ts = int(time.time())
        elif komenda == constants.KOMENDA_ODCZYTAJ_CYKLE_Z_KONFIGURACJI:
            self.glowna_tabela_podlewania.odczytaj_cykle_z_konfiguracji()
        self.aktualizuj_biezacy_stan_podlewania()
        return THutils.skonstruuj_odpowiedzV2(constants.RODZAJ_KOMUNIKATU_STAN_PODLEWANIA, self.stan_podlewania,
                                              constants.STATUS_OK)

    def aktywuj_podlewania(self, stan):
        #self.glowna_tabela_podlewania.aktywuj_wszystkie_pozycje(stan)
        # self.prze.wylacz_wszystkie_przekazniki()
        #self.glowna_tabela_podlewania.aktywuj_petle(stan)
        # TODO ponizzssa logika nie dziala, zrobic tak aby tylko kiedy jest deaktywowane to wylaczalor
        if not stan:
            self.glowna_tabela_podlewania.dzialaj_na_wszystkich_pozycjach(stan)
        self.logger.info('Uaktywniono podlewanie: ' + str(stan))
        self.podlewanie_aktywne = stan
        THutils.zapisz_parametr_konfiguracji(constants.OBSZAR_PODL, 'podlewanie_aktywne', stan, self.logger)
        self.aktualizuj_biezacy_stan_podlewania()
        return

    def dzialanie_petli(self, nazwa, stan):
        # wywolywane gdy petla nakazala zmiane stanu
        if self.podlewanie_aktywne:
            stan_poprzzedni = self.prze.stan_przekaznika_nazwa(nazwa)
            self.prze.ustaw_przekaznik_nazwa(nazwa, stan)
            self.ts = int(time.time())
            self.aktualizuj_biezacy_stan_podlewania()
            if self.prze.stan_przekaznika_nazwa(nazwa) != stan_poprzzedni:
                self.logger.info('Podlewanie ' + nazwa + ', stan: ' + str(stan))
                self.ts = int(time.time())
                self.aktualizuj_biezacy_stan_podlewania()
                self.odpal_firebase()

    def przebieg_petli(self):
        # wywolywane za kazdym przebiegiem petli, bez wzgledu na to czy byla zmiana stanu czy nie
        self.odczytaj_stan_plywakow()
        if self.poprzedni_stan_plywak_studnia != self.plywak_studnia:
            self.logger.info('Podlewanie: Plywak Studnia: ' + str(self.plywak_studnia))
            self.poprzedni_stan_plywak_studnia = self.plywak_studnia
            self.ts = int(time.time())
        if self.poprzedni_stan_plywak_szambo != self.plywak_szambo:
            self.logger.info('Podlewanie: Plywak Szambo: ' + str(self.plywak_szambo))
            self.poprzedni_stan_plywak_szambo = self.plywak_szambo
            self.ts = int(time.time())
        if self.glowna_tabela_podlewania.czy_ktorykolwiek_wlaczony():
            self.ts = int(time.time())
        self.aktualizuj_biezacy_stan_podlewania()

    def odczytaj_stan_plywakow(self):
        # TODO pigpio nie ma byc uzywane do odczytu plywakow tylko mcp_wejscia
        self.plywak_studnia = self.gpio_pigpio.read(self.plywak_studnia_pin)
        self.plywak_szambo = self.gpio_pigpio.read(self.plywak_szambo_pin)
        self.aktualizuj_biezacy_stan_podlewania()

    def aktualizuj_biezacy_stan_podlewania(self):
        '''try:
            temp = self.stan_podlewania[constants.TS]
        except KeyError:
            temp = 0'''
        self.stan_podlewania = {'plywak_studnia':THutils.xstr(self.plywak_studnia),
                                'plywak_szambo':THutils.xstr(self.plywak_szambo),
                                'podlewanie_aktywne':self.podlewanie_aktywne,
                                constants.TS: self.ts,
                                constants.CYKLE: self.glowna_tabela_podlewania.pozycje_do_listy(),
                                constants.ODBIORNIKI: self.prze.pozycje_do_listy()}
        '''if temp != self.ts:
            self.odpal_firebase()'''
        return

    def odpal_firebase(self):
        if self.firebase_callback is not None:
            self.firebase_callback()

    def odczytaj_konf(self):
        # self.czas_zmiany_sekcji = int(THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_PODL, 'CZAS_ZMIANY_SEKCJI', self.logger))
        self.max_wilg = int(THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_PODL, 'MAX_WILG', self.logger))
        self.plywak_studnia_pin = int(THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_PODL, 'PLYWAK_STUDNIA_PIN', self.logger))
        self.plywak_szambo_pin = int(THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_PODL, 'PLYWAK_SZAMBO_PIN', self.logger))
        # self.czas_uruchomienia_petli =int(THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_PODL, 'CZAS_URUCHOMIENIA_PETLI', self.logger))
        return