import constants
import logging
import time
import THutils
import petlaczasowa
import wejsciawyjscia


class Obszar:
    def __init__(self,
                 wewy,  # type: wejsciawyjscia.WejsciaWyjscia
                 petla, # type: petlaczasowa.PetlaCzasowa
                 obszar,
                 firebase_callback=None,
                 rodzaj_komunikatu_firebase='',
                 callback_przekaznika_wyjscia=None,
                 callback_wejscia=None,
                 dzialanie_petli=None):
        self.logger = logging.getLogger(constants.NAZWA_LOGGERA)
        self._biezacy_stan = {}
        self.__callback_przekaznika_wyjscia = callback_przekaznika_wyjscia
        self.__callback_wejsica = callback_wejscia
        self.wewy = wewy
        self.__firebase_callback = firebase_callback
        self.ts = int(time.time())
        self.petla = petla
        self.petla.rejestruj_dzialanie(obszar, dzialanie_petli)
        self.obszar = obszar
        self.__rodzaj_komunikatu_firebase = rodzaj_komunikatu_firebase

    def dodaj_przekaznik(self, nazwa, pin, def_czas_zalaczenia=0, impuls=False, czas_impulsu=1):
        self.wewy.wyjscia.dodaj_przekaznik(nazwa, pin,
                                           callbackfunction=self.__callback_przekaznika_wyjscia,
                                           obszar=self.obszar,
                                           impuls=impuls,
                                           czas_impulsu=czas_impulsu,
                                           def_czas_zalaczenia=def_czas_zalaczenia)

    def dodaj_wejscie(self, nazwa, pin):
        self.wewy.wejscia.dodaj_wejscie(nazwa, pin,
                                        callback=self.__callback_wejsica)
    def resetuj_ts(self):
        self.ts = int(time.time())

    def procesuj_polecenie(self,komenda, parametr1, parametr2):
        if komenda == constants.AKTYWACJA_SCHEMATU:  # odbiornik w petli sterowanie, aktywacja schematu
            if parametr2 == constants.PARAMETR_WLACZ:
                wl = True
            else:
                wl = False
            self.petla.aktywuj_pozycje_nazwa(self.obszar, parametr1, wl)
            self.resetuj_ts()
            self.logger.info('Aktywacja petli obszar: ' + self.obszar + ' ' + str(parametr1) + '. Stan: ' + str(wl))
        elif komenda == constants.ODBIORNIK_NA_CZAS:
            self.petla.dodaj_do_tabeli_jednorazowy_na_czas(str(parametr1), int(parametr2),
                                                                              obszar=self.obszar,
                                                                              dzialanie=self.dzialanie_petli)
            self.logger.info('Odbiornik na czas: obszar-' + self.obszar + ', odbiornik-' + str(parametr1) +
                             ', na czas: ' + str(parametr2))
            self.resetuj_ts()
            self.odpal_firebase()
        elif komenda == constants.TOGGLE_ODBIORNIK_NAZWA:  # wlacz po nazwie
            self.wewy.wyjscia.toggle_przekaznik_nazwa(parametr1)
            self.logger.info(self.obszar + ', kliknieto odbiornik: ' + str(parametr1))
            self.resetuj_ts()
            self.odpal_firebase()
        elif komenda == constants.KOMENDA_AKTUALIZUJ_CYKL:
            self.petla.aktualizuj_pozycje(parametr1)
            self.resetuj_ts()
        elif komenda == constants.KOMENDA_DODAJ_CYKL:
            self.petla.dodaj_nowy_cykl_permanentny(parametr1)
            self.resetuj_ts()
        elif komenda == constants.KOMENDA_USUN_CYKL:
            self.petla.usun_cykl_po_hashu(parametr1)
            self.resetuj_ts()
        self.aktualizuj_biezacy_stan()
        return THutils.skonstruuj_odpowiedzV2OK(self.__rodzaj_komunikatu_firebase, self._biezacy_stan)

    def aktualizuj_biezacy_stan(self):
        pass

    def dzialanie_petli(self, nazwa, stan, tylko_aktualizuj_ts=False):
        return

    def wejscie_callback(self, pin, nazwa, stan):
        return

    def odpal_firebase(self):
        if self.__firebase_callback is not None:
            self.__firebase_callback(self.__rodzaj_komunikatu_firebase, self._biezacy_stan)

    def get_biezacy_stan(self):
        return self._biezacy_stan