import THutils
import przekazniki_BCM
import petlaczasowa
#import pigpio
import time
import logging
import firebasenotification
import thread
import constants
from copy import deepcopy
from THutils import skonstruuj_odpowiedzV2

WEJSCIE_WLACZNIK_SMIETNIK_WIATROLAP = 'wl_smietnik_WIATROLAP'
WEJSCIE_WLACZNIK_SMIETNIK_GARAZ4 = 'wl_smietnik_GARAZ4'
PIN_WL_SMIETNIK_WIATROLAP = 11
PIN_WL_SMIETNIK_GARAZ4 = 12
CZAS_ZALACZENIA_SMIETNIKA = 300

NAZWA_ZIMOWE = 'Zimowe'
NAZWA_OGNISKO = 'Ognisko'
NAZWA_SMIETNIK = 'Smietnik'
NAZWA_JADALNIA = 'Jadalnia'

PIN_ZIMOWE = 10
PIN_OGNISKO = 8
PIN_SMIETNIK = 11
PIN_JADALNIA = 12


#TODO powyzsze piny do konfiguracji

class Oswietlenie:

    def __init__(self, mcp, mcp_wejscia, firebase_callback=None):
        self.logger = logging.getLogger(constants.NAZWA_LOGGERA)
        self.stan_oswietlenia = {}
        #self.notyfikacja_firebase = firebasenotification.Firebasenotification()
        self.mcp = mcp
        self.firebase_callback = firebase_callback
        self.mcp_wejscia = mcp_wejscia
        self.ts = int(time.time())
        #TODO dodac ponizsze do konfiguracji oswitlenia
        self.prze = przekazniki_BCM.PrzekaznikiBCM(self.mcp, self.aktualizuj_biezacy_stan_oswietlenia)
        self.prze.dodaj_przekaznik(NAZWA_ZIMOWE, PIN_ZIMOWE)
        self.prze.dodaj_przekaznik(NAZWA_OGNISKO, PIN_OGNISKO)
        self.prze.dodaj_przekaznik(NAZWA_SMIETNIK, PIN_SMIETNIK, def_czas_zalaczenia=CZAS_ZALACZENIA_SMIETNIKA)
        self.prze.dodaj_przekaznik(NAZWA_JADALNIA, PIN_JADALNIA)

        ''' self.gpio_pigpio.set_mode(PIN_WL_SMIETNIK_WIATROLAP, pigpio.INPUT)
        self.gpio_pigpio.set_pull_up_down(PIN_WL_SMIETNIK_WIATROLAP, pigpio.PUD_UP)
        self.gpio_pigpio.set_glitch_filter(PIN_WL_SMIETNIK_WIATROLAP, 15000)
        self.gpio_pigpio.callback(PIN_WL_SMIETNIK_WIATROLAP, pigpio.FALLING_EDGE, self.przycisk)

        self.gpio_pigpio.set_mode(PIN_WL_SMIETNIK_GARAZ4, pigpio.INPUT)
        self.gpio_pigpio.set_pull_up_down(PIN_WL_SMIETNIK_GARAZ4, pigpio.PUD_UP)
        self.gpio_pigpio.set_glitch_filter(PIN_WL_SMIETNIK_GARAZ4, 15000)
        self.gpio_pigpio.callback(PIN_WL_SMIETNIK_GARAZ4, pigpio.FALLING_EDGE, self.przycisk)'''

        self.mcp_wejscia.dodaj_wejscie(WEJSCIE_WLACZNIK_SMIETNIK_WIATROLAP, PIN_WL_SMIETNIK_WIATROLAP,
                                       callback=self.wejscie_callback)
        self.mcp_wejscia.dodaj_wejscie(WEJSCIE_WLACZNIK_SMIETNIK_GARAZ4, PIN_WL_SMIETNIK_GARAZ4,
                                       callback=self.wejscie_callback)

        self.glowna_tabela_oswietlenia = petlaczasowa.PetlaCzasowa(constants.OBSZAR_OSWI,
                                                                   self.dzialanie_petli,
                                                                   callback=self.przebieg_petli,
                                                                   logger=self.logger)
        #TODO do parametrow czas_uruchomienia_petli
        # TODO co to jest ponizsze?
        self.czas_odczytu_konfig = 6000
        #self.czas_odswiezania_petli=70000
        self.odczytaj_konf()
        # self.czas_odswiezania_tablicy_oswietlenia = 30
        #self.odczytuj_tablice_oswietlenia_cyklicznie()

        self.prze.ustaw_przekaznik_nazwa(NAZWA_SMIETNIK, False)
        self.prze.ustaw_przekaznik_nazwa(NAZWA_ZIMOWE, False)
        self.prze.ustaw_przekaznik_nazwa(NAZWA_OGNISKO, False)
        self.prze.ustaw_przekaznik_nazwa(NAZWA_JADALNIA, False)

        self.aktualizuj_biezacy_stan_oswietlenia()
        self.glowna_tabela_oswietlenia.aktywuj_petle(True)


        self.logger.info('Zainicjowalem klase oswietlenie.')

    def wejscie_callback(self, pin, nazwa, stan):
        if nazwa == WEJSCIE_WLACZNIK_SMIETNIK_WIATROLAP:
            if stan == 0:
                self.logger.info('Wcisnieto przycisk Smietnik Wiatrolap.')
                self.wlacz_smietnik_samodzielny()
        elif nazwa == WEJSCIE_WLACZNIK_SMIETNIK_GARAZ4:
            if stan == 0:
                self.logger.info('Wcisnieto przycisk Smietnik Garaz.')
                self.wlacz_smietnik_samodzielny()
        else:
            return
        self.ts = int(time.time())
        return


    def procesuj_polecenie(self,komenda, parametr1, parametr2):
        if komenda == constants.TOGGLE_ODBIORNIK_NAZWA:  # wlacz po nazwie
            self.prze.toggle_przekaznik_nazwa(parametr1)
            self.ts = int(time.time())
            self.logger.info('Oswietlenie ' + parametr1 + ' toggle.')
            if self.firebase_callback is not None:
                self.firebase_callback()
        elif komenda == constants.AKTYWACJA_SCHEMATU:  # odbiornik w petli sterowanie, aktywacja schematu
            if parametr2 == constants.PARAMETR_WLACZ:
                wl = True
            else:
                wl = False
            self.glowna_tabela_oswietlenia.aktywuj_pozycje_nazwa(parametr1, wl)
            self.ts = int(time.time())
            #self.zapisz_tablice_oswietlenia_do_ini()
            self.logger.info('Aktywacja petli oswietlenia ' + str(parametr1) + '. Stan: ' + str(wl))
        elif komenda == constants.KOMENDA_ODCZYTAJ_CYKLE_Z_KONFIGURACJI:
            self.glowna_tabela_oswietlenia.odczytaj_cykle_z_konfiguracji()
        self.aktualizuj_biezacy_stan_oswietlenia()
        return skonstruuj_odpowiedzV2(constants.RODZAJ_KOMUNIKATU_STAN_OSWIETLENIA,
                                       self.stan_oswietlenia, constants.STATUS_OK)

    def przebieg_petli(self):
        # wywolywane za kazdym przebiegiem petli, bez wzgledu na to czy byla zmiana stanu czy nie
        if self.glowna_tabela_oswietlenia.czy_ktorykolwiek_wlaczony():
            self.ts = int(time.time())
        self.aktualizuj_biezacy_stan_oswietlenia()

    def dzialanie_petli(self, nazwa, stan):
        stan_poprzzedni = self.prze.stan_przekaznika_nazwa(nazwa)
        self.prze.ustaw_przekaznik_nazwa(nazwa, stan)
        if self.prze.stan_przekaznika_nazwa(nazwa) != stan_poprzzedni:
            self.ts = int(time.time())
            self.logger.info('Oswietlenie ' + nazwa + ', stan: ' + str(stan))
            self.aktualizuj_biezacy_stan_oswietlenia()
            if self.firebase_callback is not None:
                self.firebase_callback()

    def wlacz_smietnik_samodzielny(self):
        przek_smie = self.prze.przekaznik_po_nazwie(NAZWA_SMIETNIK)
        if not przek_smie.get_stan(): #self.prze.stan_przekaznika_nazwa(NAZWA_SMIETNIK):
            #self.glowna_tabela_oswietlenia.dodaj_do_tabeli_jednorazowy_na_czas(NAZWA_SMIETNIK, CZAS_ZALACZENIA_SMIETNIKA)
            self.glowna_tabela_oswietlenia.dodaj_do_tabeli_jednorazowy_na_czas(przek_smie.get_nazwa(),
                                                                               przek_smie.get_defczaszalaczenia())
            self.logger.info('Wlaczylem oswietlenie nad smietnikiem.')
        return

    def aktualizuj_biezacy_stan_oswietlenia(self):
        #temp = deepcopy(self.stan_oswietlenia)
        '''try:
            temp = self.stan_oswietlenia[constants.TS]
        except KeyError:
            temp = 0'''
        self.stan_oswietlenia = {constants.CYKLE: self.glowna_tabela_oswietlenia.pozycje_do_listy(),
                                 constants.ODBIORNIKI: self.prze.pozycje_do_listy(),
                                 constants.TS: self.ts}
        #self.stan_oswietlenia_do_tuple()
        #temp2 = deepcopy(self.stan_oswietlenia)
        #if len(temp) > 0:
        #    temp.pop(constants.CYKLE)
        #temp2.pop(constants.CYKLE)
        '''if temp != self.ts:
            if self.firebase_callback is not None:
                #oo = THutils.skonstruuj_odpowiedzV2(constants.RODZAJ_KOMUNIKATU_STAN_OSWIETLENIA,
                #                                    self.stan_oswietlenia, constants.STATUS_OK)
                self.firebase_callback()
                #print 'fire z osweitlenia'
            #thread.start_new_thread(self.notyfikacja_firebase.notify, (constants.OBSZAR_OSWI, constants.FIREBASE_KOMUNIKAT_OSWIETLENIE))'''
        return

    def odczytaj_konf(self):
        #self.czas_odswiezania_petli = int(THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_OSWI, 'CZAS_ODSWIEZANIA_PETLI', self.logger))
        return
