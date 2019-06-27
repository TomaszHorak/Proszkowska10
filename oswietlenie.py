import datetime
import threading
import THutils
import przekazniki_BCM
import petlaczasowa
import RPi.GPIO as gpio
import time
import logging
import firebasenotification
import thread


NAZWA_ZIMOWE = 'Zimowe'
NAZWA_OGNISKO = 'Ognisko'
NAZWA_SMIETNIK = 'Smietnik'
NAZWA_JADALNIA = 'Jadalnia'
NR_ZIMOWE = 0
NR_OGNISKO = 1
NR_SMIETNIK = 2
NR_JADALNIA = 3

CZAS_URUCHOMIENIA_PETLI = 2
CZAS_ZALACZENIA_SMIETNIKA = 300
PIN_WL_SMIETNIK_WIATROLAP = 9
PIN_WL_SMIETNIK_GARAZ4 = 22
#TODO powyzsze piny do konfiguracji

FIREBASE_OBSZAR_OSWIETLENIE = 'oswietlenie'
FIREBASE_KOMUNIKAT_OSWIETLENIE = 'zmiana_oswietlenia'


class Oswietlenie:

    def __init__(self, mcp):
        self.logger = logging.getLogger('proszkowska')
        self.stan_oswietlenia = []
        self.notyfikacja_firebase = firebasenotification.Firebasenotification()
        # self.oswietlenie_zimowe_aktywne = False
        # self.oswietlenie_jadalnia_aktywne = True
        tab = []
        self.mcp = mcp
        #TODO dodac ponizsze do konfiguracji oswitlenia
        tab.append({'numer':NR_ZIMOWE ,'nazwa': NAZWA_ZIMOWE, 'pin': 10})
        tab.append({'numer':NR_OGNISKO ,'nazwa': NAZWA_OGNISKO, 'pin': 8})
        tab.append({'numer':NR_SMIETNIK ,'nazwa': NAZWA_SMIETNIK, 'pin': 11})
        tab.append({'numer':NR_JADALNIA ,'nazwa': NAZWA_JADALNIA, 'pin': 12})
        self.prze = przekazniki_BCM.PrzekaznikiBCM(self.mcp, tab)

        gpio.setmode(gpio.BCM)
        gpio.setup(PIN_WL_SMIETNIK_WIATROLAP, gpio.IN, pull_up_down=gpio.PUD_UP)
        gpio.add_event_detect(PIN_WL_SMIETNIK_WIATROLAP, gpio.FALLING, callback=self.przycisk, bouncetime=200)
        gpio.setup(PIN_WL_SMIETNIK_GARAZ4, gpio.IN, pull_up_down=gpio.PUD_UP)
        gpio.add_event_detect(PIN_WL_SMIETNIK_GARAZ4, gpio.FALLING, callback=self.przycisk, bouncetime=200)

        self.glowna_tabela_oswietlenia = petlaczasowa.PetlaCzasowa(CZAS_URUCHOMIENIA_PETLI, self.wlacz_odb_nazwa)
        #TODO do parametrow czas_uruchomienia_petli
        # TODO co to jest ponizsze?
        self.czas_odczytu_konfig = 6000
        self.czas_odswiezania_petli=70000
        self.odczytaj_konfiguracje()
        # self.czas_odswiezania_tablicy_oswietlenia = 30
        self.odczytuj_tablice_oswietlenia_cyklicznie()
        self.glowna_tabela_oswietlenia.aktywuj_petle(True)

        self.wlacz_odb_nazwa(NAZWA_SMIETNIK, False)
        self.wlacz_odb_nazwa(NAZWA_ZIMOWE, False)
        self.wlacz_odb_nazwa(NAZWA_OGNISKO, False)
        self.wlacz_odb_nazwa(NAZWA_JADALNIA, False)

        self.aktualizuj_biezacy_stan_oswietlenia()
        self.logger.info('Zainicjowalem klase oswietlenie.')

    def procesuj_polecenie(self,komenda, parametr1, parametr2):
        if komenda == 'WN':  # wlacz po nazwie
            if parametr2 == '1':
                st = True
            else:
                st = False
            self.wlacz_odb_nazwa(parametr1, st)
        elif komenda == 'OS':  # odbiornik w petli sterowanie, aktywacja schematu
            if parametr2 == 'WLACZ':
                wl = True
            else:
                wl = False
            self.glowna_tabela_oswietlenia.aktywuj_pozycje_nazwa(parametr1, wl)
            THutils.zapisz_parametr_konfiguracji('OSWIETLENIE', parametr1, wl, self.logger)
            self.logger.info('Aktywacja petli oswietlenia ' + str(parametr1) + '. Stan: ' + str(wl))
        # TODO ponizsze do usuniecia chyba
        elif komenda == 'ST':
            pass
        self.aktualizuj_biezacy_stan_oswietlenia()

    def przycisk(self, pin):
        if pin == PIN_WL_SMIETNIK_WIATROLAP:
            time.sleep(0.05)
            inx = gpio.input(PIN_WL_SMIETNIK_WIATROLAP)
            if inx == 0:
                self.wlacz_smietnik_samodzielny()
        elif pin == PIN_WL_SMIETNIK_GARAZ4:
            time.sleep(0.05)
            inx = gpio.input(PIN_WL_SMIETNIK_GARAZ4)
            if inx == 0:
                self.wlacz_smietnik_samodzielny()
        return

    def wlacz_smietnik_samodzielny(self):
        if not self.prze.stan_przekaznika_nazwa(NAZWA_SMIETNIK):
            wl = datetime.datetime.now()
            wyl = wl + datetime.timedelta(0, CZAS_ZALACZENIA_SMIETNIKA)
            self.glowna_tabela_oswietlenia.dodaj_do_tabeli(NAZWA_SMIETNIK, wl.hour, wl.minute, wyl.hour, wyl.minute,
                                                           '0123456', True, typ='J')
            self.logger.info('Wlaczylem oswietlenie nad smietnikiem.')
        return

    """def wlacz_smietnik(self):
        if self.prze.stan_przekaznika_nazwa(SMIETNIK) == 0:
            wl = datetime.datetime.now()
            wyl = wl + datetime.timedelta(0, CZAS_ZALACZENIA_SMIETNIKA)
            self.glowna_tabela_oswietlenia.dodaj_do_tabeli(SMIETNIK, wl.hour, wl.minute, wyl.hour, wyl.minute,
                                                           '0123456', 1, typ='J')
            THutils.zapisz_do_logu_plik('I', 'Wlaczylem oswietlenie nad smietnikiem.')
        else:
            self.prze.ustaw_przekaznik_nazwa(SMIETNIK, 0)
            THutils.zapisz_do_logu_plik('I', 'Wylaczylem oswietlenie nad smietnikiem.')"""

    """def uruchom_oswietlenie_zimowe(self, wlaczone):
        if wlaczone:
            # self.oswietlenie_zimowe_aktywne = True
            self.glowna_tabela_oswietlenia.aktywuj_pozycje_nazwa(NAZWA_ZIMOWE, True)
        else:
            # self.oswietlenie_zimowe_aktywne = False
            self.glowna_tabela_oswietlenia.aktywuj_pozycje_nazwa(NAZWA_ZIMOWE, False)
        #TODO wspolna czesc konfiguracji albo kazdy plik konfiguracyjny osobny dla garazu i naglo bo aktualizacja parame
        self.aktualizuj_biezacy_stan_oswietlenia()
        return"""

    """def uruchom_oswietlenie_jadalnia(self, wlaczona):
        if wlaczona:
            self.oswietlenie_jadalnia_aktywne = True
            self.glowna_tabela_oswietlenia.aktywuj_pozycje_nazwa(NAZWA_JADALNIA, True)
        else:
            self.oswietlenie_jadalnia_aktywne = False
            self.glowna_tabela_oswietlenia.aktywuj_pozycje_nazwa(NAZWA_JADALNIA, False)
        self.aktualizuj_biezacy_stan_oswietlenia()
        return"""

    def wlacz_odb_nazwa(self, nazwa, stan):
        stan_poprzzedni = self.prze.stan_przekaznika_nazwa(nazwa)
        self.prze.ustaw_przekaznik_nazwa(nazwa, stan)
        if self.prze.stan_przekaznika_nazwa(nazwa) != stan_poprzzedni:
            self.logger.info('Oswietlenie ' + nazwa + ', stan: ' + str(stan))
        self.aktualizuj_biezacy_stan_oswietlenia()

    def wlacz_odbiornik_nr(self, nr_odbiornika, stan):
        if stan == 1:
            st = True
        else:
            st = False
        self.prze.ustaw_przekaznik_nr(nr_odbiornika, st)
        if self.prze.pin[nr_odbiornika].get_stan() != st:
            self.logger.info('Oswietlenie ' + str(nr_odbiornika) + ', stan: ' + str(st))
        self.aktualizuj_biezacy_stan_oswietlenia()

    def aktualizuj_biezacy_stan_oswietlenia(self):
        temp = self.stan_oswietlenia
        odbi = []
        for j in self.prze.pin:
            odbi.append({j.get_nazwa(): j.get_stan()})
        self.stan_oswietlenia = {'zimowe_aktywne': self.glowna_tabela_oswietlenia.czy_pozycja_aktywna(NAZWA_ZIMOWE),
                'jadalnia_aktywna': self.glowna_tabela_oswietlenia.czy_pozycja_aktywna(NAZWA_JADALNIA),
                                 'Ktorykolwiek_wlaczony':self.prze.czy_ktorykolwiek_wlaczony(),
                                 'Odbiorniki': odbi}
        if self.stan_oswietlenia != temp:
            thread.start_new_thread(self.notyfikacja_firebase.notify, (FIREBASE_OBSZAR_OSWIETLENIE, FIREBASE_KOMUNIKAT_OSWIETLENIE))
        return

    """def aktywuj_schematy(self):
        if not self.oswietlenie_zimowe_aktywne:
            self.uruchom_oswietlenie_zimowe(False)
        else:
            self.uruchom_oswietlenie_zimowe(True)
        if not self.oswietlenie_jadalnia_aktywne:
            self.uruchom_oswietlenie_jadalnia(False)
        else:
            self.uruchom_oswietlenie_jadalnia(True)
        return"""

    def odczytuj_tablice_oswietlenia_cyklicznie(self):
        self.odczytaj_tablice_oswietlenia()
        threading.Timer(self.czas_odswiezania_petli, self.odczytuj_tablice_oswietlenia_cyklicznie).start()

    def odczytaj_tablice_oswietlenia(self):
        result = THutils.odczytaj_cala_tabele("stacja_pogodowa.petle")
        if not result:
            self.logger.warning('Blad odczytu tabeli z oswietleniem z bazy danych.')
            return
        self.glowna_tabela_oswietlenia.zeruj_tabele()
        for item in result:
            if item[7] == 'O':
                if item[8] == 1:
                    akt = True
                else:
                    akt = False
                self.glowna_tabela_oswietlenia.dodaj_do_tabeli(item[0], item[2], item[3], item[4], item[5], item[1], akt)
        # self.aktywuj_schematy()
        self.odczytaj_konfiguracje()
        self.logger.info('Odswiezylem tablice oswietlenia.')

    def odczytaj_konfiguracje(self):
        # self.oswietlenie_zimowe_aktywne = False
        # self.oswietlenie_jadalnia_aktywne = True
        a = THutils.odczytaj_parametr_konfiguracji('OSWIETLENIE', NAZWA_JADALNIA, self.logger)
        if a in ['True', 'true', 'TRUE']:
            self.glowna_tabela_oswietlenia.aktywuj_pozycje_nazwa(NAZWA_JADALNIA, True)
            # self.oswietlenie_jadalnia_aktywne = True
        else:
            self.glowna_tabela_oswietlenia.aktywuj_pozycje_nazwa(NAZWA_JADALNIA, False)
            # self.oswietlenie_jadalnia_aktywne = False
        a = THutils.odczytaj_parametr_konfiguracji('OSWIETLENIE', NAZWA_ZIMOWE, self.logger)
        if a in ['True', 'true', 'TRUE']:
            self.glowna_tabela_oswietlenia.aktywuj_pozycje_nazwa(NAZWA_ZIMOWE, True)
            # self.oswietlenie_zimowe_aktywne = True
        else:
            # self.oswietlenie_zimowe_aktywne = False
            self.glowna_tabela_oswietlenia.aktywuj_pozycje_nazwa(NAZWA_ZIMOWE, False)
        self.czas_odswiezania_petli = int(THutils.odczytaj_parametr_konfiguracji('OSWIETLENIE', 'CZAS_ODSWIEZANIA_PETLI', self.logger))
        return
