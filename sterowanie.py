import przekazniki_BCM
# import RPi.GPIO as gpio
#import pigpio
import time
import THutils
import petlaczasowa
import datetime
import requests
import logging
import firebasenotification
import thread
from copy import deepcopy
import constants

WEJSCIE_BRAMA = 'we_brama'
WEJSCIE_MANIPULATOR = 'we_manipul'
WEJSCIE_DZWONEK = 'we_dzwonek'
PIN_CZUJNIK_BRAMA_GARAZ = 15
PIN_PRZEKAZNIK_MANIPULATOR_GARAZ = 14
PIN_DZWONEK = 13

BRAMA_ZAMKNIETA = 'Brama zamknieta'
BRAMA_OTWARTA = 'Brama otwarta'
BRAMA_OTWARCIE = 'Brama_otwarcie'
PIN_BRAMA_OTWARCIE = 9

CENTRALNY = 'CENTRALNY'

ZALUZJE_CENTRALNY_DOL = 'Zaluzje centralny DOL'
ZALUZJE_CENTRALNY_GORA = 'Zaluzje centralny GORA'
PIN_ZALUZJE_GORA = 14
PIN_ZALUZJE_DOL = 15
CZAS_IMPULSU_ZALUZJI = 1

WYSYLANIE_SMS = 'wysylanie_sms'
STAN_BRAMY = 'stan_bramy'
NIEUDANYCH_PROB_OTWARCIA = 'nieudanych_prob_otwarcia'
DATA_OSTATNIEJ_NIEUDANEJ_PROBY_OTWARCIA = 'data_ostatniej_nieudanej_proby_otwarcia'
DATA_OSTATNIEJ_UDANEJ_PROBY_OTWARCIA = 'data_ostatniej_udanej_proby_otwarcia'
BLOKADA_MANIPULATORA = 'blokada_manipulatora'

POMPA_OBIEGOWA = 'pompa_obiegowa'
PIN_POMPA_OBIEGOWA = 13

RUCH_GORA = 1
RUCH_DOL = 0

class Sterowanie:
    def __init__(self, mcp_wyjscia, mcp_wejscia, firebase_callback=None):
        self.mcp = mcp_wyjscia
        self.mcp_wejscia = mcp_wejscia
        self.firebase_callback = firebase_callback
        self.wysylaj_sms = True
        self.logger = logging.getLogger(constants.NAZWA_LOGGERA)
        self.stan_bramy = BRAMA_ZAMKNIETA
        self.ts = int(time.time())

        self.prze = przekazniki_BCM.PrzekaznikiBCM(self.mcp, self.aktualizuj_biezacy_stan_sterowania)
        self.prze.dodaj_przekaznik(ZALUZJE_CENTRALNY_DOL, PIN_ZALUZJE_DOL, impuls=True, czas_impulsu=1)
        self.prze.dodaj_przekaznik(ZALUZJE_CENTRALNY_GORA, PIN_ZALUZJE_GORA, impuls=True, czas_impulsu=1)
        self.prze.dodaj_przekaznik(BRAMA_OTWARCIE, PIN_BRAMA_OTWARCIE, impuls=True, czas_impulsu=1)
        self.prze.dodaj_przekaznik(POMPA_OBIEGOWA, PIN_POMPA_OBIEGOWA)

        # self.ruch_bramy(PIN_CZUJNIK_BRAMA_GARAZ)
        self.mcp_wejscia.dodaj_wejscie(WEJSCIE_BRAMA, PIN_CZUJNIK_BRAMA_GARAZ, callback=self.wejscie_callback)
        self.mcp_wejscia.dodaj_wejscie(WEJSCIE_MANIPULATOR, PIN_PRZEKAZNIK_MANIPULATOR_GARAZ, callback=self.wejscie_callback)
        self.mcp_wejscia.dodaj_wejscie(WEJSCIE_DZWONEK, PIN_DZWONEK, callback=self.wejscie_callback)

        self.blokada_manipulatora = False    # czy jest mozliwe otwieranie bramy z manipulatora
        self.licznik_nieudanych_prob_otwarcia_bramy = 0
        self.data_ostatniej_nieudanej_proby = 0
        self.data_ostatniej_udanej_proby = 0
        self.glowna_tabela_sterowania = petlaczasowa.PetlaCzasowa(constants.OBSZAR_STER,
                                                                  self.dzialanie_petli,
                                                                  callback=self.przebieg_petli,
                                                                  logger=self.logger)

        # TODO czy na pewno ma byc cyklicznie, na razie wylaczylem
        # TODO w ogole cyklicznosc pobierania czegos do petli musi byc ogarnieta w petli a nie poza nia
        #self.odczytuj_tablice_sterowania_cyklicznie()
        self.glowna_tabela_sterowania.aktywuj_petle(True)

        self.odczytaj_konf()
        self.aktualizuj_biezacy_stan_sterowania()
        self.logger.info('Zainicjowalem klase sterowanie.')
        return

    def wejscie_callback(self, pin, nazwa, stan):
        #self.logger.info('Wejscia callback, nazwa: ' + str(nazwa) + ', stan: ' + str(stan))
        if nazwa == WEJSCIE_BRAMA:
            self.ruch_bramy(stan)
        elif nazwa == WEJSCIE_MANIPULATOR:
            if stan == 0:
                self.wpisano_poprawny_kod(stan)
        elif nazwa == WEJSCIE_DZWONEK:
            if stan == 0:
                self.dzwonek_do_drzwi(stan)
        else:
            return
        self.ts = int(time.time())
        return

    def procesuj_polecenie(self, komenda, parametr1, parametr2):
        # TODO przejrzec gdzie i kiedy jest aktualizowany stan i zrobic porzadek
        # TODO chyba 'OK' nie jest wykorzystywane
        if komenda == 'OK':
            # odczytaj konfiguracje
            return THutils.wyslij_konfiguracje()
        elif komenda == constants.TOGGLE_ODBIORNIK_NAZWA:  # wlacz po nazwie
            self.prze.toggle_przekaznik_nazwa(parametr1)
            self.ts = int(time.time())
            self.odpal_firebase()
        elif komenda == constants.AKTYWACJA_SCHEMATU:  # odbiornik w petli sterowanie, aktywacja schematu
            if parametr2 == constants.PARAMETR_WLACZ:
                wl = True
            else:
                wl = False
            self.glowna_tabela_sterowania.aktywuj_pozycje_nazwa(parametr1, wl)
            self.ts = int(time.time())
            #self.zapisz_tabice_sterowania_do_ini()
            self.logger.info('Aktywacja petli sterowanie ' + str(parametr1) + '. Stan: ' + str(wl))
        elif komenda == 'BR':  # brama
            if parametr1 == 'BLOCK':
                self.blokada_manipulatora = True
                self.ts = int(time.time())
                THutils.zapisz_parametr_konfiguracji(constants.OBSZAR_STER, 'BLOKADA_MANIPULATORA',
                                                     self.blokada_manipulatora, self.logger)
            elif parametr1 == 'UNBLOCK':
                self.blokada_manipulatora = False
                self.ts = int(time.time())
                THutils.zapisz_parametr_konfiguracji(constants.OBSZAR_STER, 'BLOKADA_MANIPULATORA',
                                                     self.blokada_manipulatora, self.logger)
            #elif parametr1 == 'STER':
            #    self.akcja_na_bramie() #kierunek=int(parametr2))
            elif parametr1 == 'SMS':
                if parametr2 == constants.PARAMETR_JEDEN:
                    sms = True
                else:
                    sms = False
                self.set_wysylaj_sms(sms)
                self.ts = int(time.time())
                THutils.zapisz_parametr_konfiguracji(constants.OBSZAR_STER, 'BRAMA_SMS', sms, self.logger)
        elif komenda == 'ST':
            pass
        self.aktualizuj_biezacy_stan_sterowania()
        return THutils.skonstruuj_odpowiedzV2(constants.RODZAJ_KOMUNIKATU_STAN_STEROWANIA, self.stan_sterowania,
                                              constants.STATUS_OK)

    '''def zmiana_stanu(self, pin, level, tick):
        #inx = self.gpio_pigpio.read(pin)
        if pin == PIN_DZWONEK:
            inx = self.gpio_pigpio.read(PIN_DZWONEK)
            #self.logger.info('Odczytano z przycisku dzwonka: ' + str(inx))
            if inx == 0:
                self.dzwonek_do_drzwi(inx)
        elif pin == PIN_PRZEKAZNIK_MANIPULATOR_GARAZ:
            inx = self.gpio_pigpio.read(PIN_PRZEKAZNIK_MANIPULATOR_GARAZ)
            #self.logger.info('Odczytano z przekaznika manipulatora: ' + str(inx))
            if inx == 0:
                self.wpisano_poprawny_kod(inx)
        elif pin == PIN_CZUJNIK_BRAMA_GARAZ:
            inx = self.gpio_pigpio.read(PIN_CZUJNIK_BRAMA_GARAZ)
            #self.logger.info('Odczytano z przekaznika ruchu bramy: ' + str(inx))
            self.ruch_bramy(inx)
        return'''

    def odczytaj_konf(self):
        a = (THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_STER, 'BRAMA_SMS', self.logger))
        if a in ['True', 'true', 'TRUE']:
            self.wysylaj_sms = True
        else:
            self.wysylaj_sms = False
        a = THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_STER, 'BLOKADA_MANIPULATORA', self.logger)
        if a in ['True', 'true', 'TRUE']:
            self.blokada_manipulatora = True
        else:
            self.blokada_manipulatora = False

    def set_wysylaj_sms(self, mozna_wysylac):
        self.wysylaj_sms = mozna_wysylac
        #self.aktualizuj_biezacy_stan_sterowania()

    def akcja_na_bramie(self): #, kierunek=None):
        if self.blokada_manipulatora:
            self.licznik_nieudanych_prob_otwarcia_bramy = self.licznik_nieudanych_prob_otwarcia_bramy + 1
            self.data_ostatniej_nieudanej_proby = datetime.datetime.now()
            self.logger.warning('Proba otwarcia bramy, ale zablokowane.')
            return
        '''if kierunek == RUCH_GORA and self.stan_bramy == BRAMA_OTWARTA:
            return
        if kierunek == RUCH_DOL and self.stan_bramy == BRAMA_ZAMKNIETA:
            return'''
        self.prze.ustaw_przekaznik_nazwa(BRAMA_OTWARCIE, True)
        self.data_ostatniej_udanej_proby = datetime.datetime.now()
        #self.aktualizuj_biezacy_stan_sterowania()
        self.logger.info('Akcja na bramie.')
        return

    def dzwonek_do_drzwi(self, odczyt):
        # if pin == PIN_DZWONEK:
        # time.sleep(0.05)
        # inx = gpio.input(PIN_DZWONEK)
        # inx = self.gpio_pigpio.read(PIN_DZWONEK)

        if odczyt == 0:
            self.logger.info('Przycisnieto przycisk dzwonka do drzwi.')
            THutils.przekaz_polecenie_V2_JSONRPC(constants.HOST_I_PORT_STRYCH_v2, constants.OBSZAR_NAGL,
                                                 constants.KOMENDA_DZWONEK, constants.PARAMETR_ZERO,
                                                 constants.PARAMETR_ZERO, logger=self.logger)
            '''tu = {constants.KOMENDA: constants.KOMENDA_DZWONEK, constants.PARAMETR1: '0', constants.PARAMETR2: '0',
                  constants.OBSZAR: constants.OBSZAR_NAGL}
            # ciag = constants.HOST_I_PORT_STRYCH_v1  + urllib.urlencode(tu)
            try:
                requests.post(constants.HOST_I_PORT_STRYCH_v2, json=tu)
                thread.start_new_thread(self.notyfikacja_firebase.notify,
                                            (constants.OBSZAR_STER, constants.FIREBASE_KOMUNIKAT_DZWONEK, 'Dzwonek'))
            except (requests.exceptions.RequestException, requests.exceptions.Timeout, socket.error) as e:
                self.logger.error('Blad przy requescie do wlaczenia dzwonka: ' + str(e))'''
        return

    def wpisano_poprawny_kod(self, odczyt):
        # if pin == PIN_PRZEKAZNIK_MANIPULATOR_GARAZ:
        #time.sleep(0.05)
        # inx = gpio.input(PIN_PRZEKAZNIK_MANIPULATOR_GARAZ)
        # inx = self.gpio_pigpio.read(PIN_PRZEKAZNIK_MANIPULATOR_GARAZ)

        if odczyt == 0:
            self.logger.info('Wpisano poprawny kod na manipulatorze.')
            self.akcja_na_bramie()
        return

    def ruch_bramy(self, odczyt):
        if odczyt == 1:
            if self.stan_bramy == BRAMA_OTWARTA:
                return
            self.logger.info(BRAMA_OTWARTA)
            self.stan_bramy = BRAMA_OTWARTA
            self.aktualizuj_biezacy_stan_sterowania()
            self.odpal_firebase()
        else:
            if self.stan_bramy == BRAMA_ZAMKNIETA:
                return
            self.logger.info(BRAMA_ZAMKNIETA)
            self.stan_bramy = BRAMA_ZAMKNIETA
            self.aktualizuj_biezacy_stan_sterowania()
            self.odpal_firebase()
        self.wyslij_powiadomienie_sms_o_bramie()
        return

    def wyslij_powiadomienie_sms_o_bramie(self):
        if not self.wysylaj_sms:
            return
        body = 'Stan bramy: ' + self.stan_bramy
        dane = {'To': '+48605178846',
                'From': '+48732483422',
                'Body': body}
        try:
            r = requests.post("https://api.twilio.com/2010-04-01/Accounts/AC7799cdc4125e85ef98d34789ee003c8c/Messages.json",
                          data=dane, auth=('AC7799cdc4125e85ef98d34789ee003c8c', '0bdd45c493f6fa6320587424cbbb4826'))
        except requests.exceptions.ConnectionError as serr:
            self.logger.warning('Blad wysylania requestu do twilio: ' + str(serr))
        return

    def dzialanie_petli(self, nazwa, stan):
        stan_poprzzedni = self.prze.stan_przekaznika_nazwa(nazwa)
        self.prze.ustaw_przekaznik_nazwa(nazwa, stan)
        self.aktualizuj_biezacy_stan_sterowania()
        if self.prze.stan_przekaznika_nazwa(nazwa) != stan_poprzzedni:
            self.logger.info('Sterowanie ' + nazwa + ', stan: ' + str(stan))
            self.ts = int(time.time())
            self.odpal_firebase()


    '''def zaluzje(self, kierunek):
        if kierunek == RUCH_GORA:
            self.prze.wlacz_na_czas_nazwa(ZALUZJE_CENTRALNY_GORA, CZAS_IMPULSU_ZALUZJI)
            self.logger.info('Zaluzje centralny w gore.')
        elif kierunek == RUCH_DOL:
            self.prze.wlacz_na_czas_nazwa(ZALUZJE_CENTRALNY_DOL, CZAS_IMPULSU_ZALUZJI)
            self.logger.info('Zaluzje centralny w dol.')
        return'''

    def odpal_firebase(self):
        if self.firebase_callback is not None:
            self.firebase_callback()

    def przebieg_petli(self):
        #if self.glowna_tabela_sterowania.czy_ktorykolwiek_wlaczony():
        #    self.ts = int(time.time())
        # TODO pompa obiegowa wlaczona caly dzien wymuszala aktualizacje ts's, na razie wyremowane
        self.aktualizuj_biezacy_stan_sterowania()

    def aktualizuj_biezacy_stan_sterowania(self):
        self.stan_sterowania = {
            STAN_BRAMY: self.stan_bramy,
            WYSYLANIE_SMS: self.wysylaj_sms,
            NIEUDANYCH_PROB_OTWARCIA: self.licznik_nieudanych_prob_otwarcia_bramy,
            DATA_OSTATNIEJ_NIEUDANEJ_PROBY_OTWARCIA: str(self.data_ostatniej_nieudanej_proby),
            DATA_OSTATNIEJ_UDANEJ_PROBY_OTWARCIA: str(self.data_ostatniej_udanej_proby),
            BLOKADA_MANIPULATORA: self.blokada_manipulatora,
            constants.ODBIORNIKI: self.prze.pozycje_do_listy(),
            constants.CYKLE: self.glowna_tabela_sterowania.pozycje_do_listy(),
            constants.TS: self.ts}
