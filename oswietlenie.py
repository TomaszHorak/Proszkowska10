import time
from MojLogger import MojLogger
import petlaczasowa
import constants
import wejsciawyjscia
from Obszar import Obszar

#TODO dodac punkt swietlny przy holu na dole, ledy

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

class Oswietlenie(Obszar):
    def __init__(self,
                 wewy,  # type: wejsciawyjscia.WejsciaWyjscia
                 petla,  # type: petlaczasowa.PetlaCzasowa
                 logger,    #type: MojLogger
                 firebase_callback=None):

        Obszar.__init__(self, constants.OBSZAR_OSWI,
                        logger,
                        petla=petla,
                        wewy=wewy,
                        firebase_callback=firebase_callback,
                        rodzaj_komunikatu=constants.RODZAJ_KOMUNIKATU_STAN_OSWIETLENIA,
                        callback_przekaznika_wyjscia=self.resetuj_ts, #TODO ten call back zawsze jest usawiony na resetuj ts
                        callback_wejscia=self.wejscie_callback,
                        dzialanie_petli=self.dzialanie_petli)

        self.dodaj_przekaznik(NAZWA_ZIMOWE, PIN_ZIMOWE)
        self.dodaj_przekaznik(NAZWA_OGNISKO, PIN_OGNISKO)
        self.dodaj_przekaznik(NAZWA_SMIETNIK, PIN_SMIETNIK, def_czas_zalaczenia=500)
        self.dodaj_przekaznik(NAZWA_JADALNIA, PIN_JADALNIA)

        self.dodaj_wejscie(WEJSCIE_WLACZNIK_SMIETNIK_WIATROLAP, PIN_WL_SMIETNIK_WIATROLAP)
        self.dodaj_wejscie(WEJSCIE_WLACZNIK_SMIETNIK_GARAZ4, PIN_WL_SMIETNIK_GARAZ4)

        self.wewy.wyjscia.ustaw_przekaznik_nazwa(NAZWA_SMIETNIK, False)
        self.wewy.wyjscia.ustaw_przekaznik_nazwa(NAZWA_ZIMOWE, False)
        self.wewy.wyjscia.ustaw_przekaznik_nazwa(NAZWA_OGNISKO, False)
        self.wewy.wyjscia.ustaw_przekaznik_nazwa(NAZWA_JADALNIA, False)

        self.aktualizuj_biezacy_stan()
        self.logger.info(self.obszar, 'oswietlenie', 'Zainicjowalem klase oswietlenie.')

    def wejscie_callback(self, pin, nazwa, stan):
        if nazwa == WEJSCIE_WLACZNIK_SMIETNIK_WIATROLAP:
            if stan == 0:
                self.logger.info(self.obszar, 'wiatrolap', 'Wcisnieto przycisk Smietnik Wiatrolap.')
                self.wlacz_smietnik_samodzielny()
        elif nazwa == WEJSCIE_WLACZNIK_SMIETNIK_GARAZ4:
            if stan == 0:
                self.logger.info(self.obszar, 'garaz', 'Wcisnieto przycisk Smietnik Garaz.')
                self.wlacz_smietnik_samodzielny()
        else:
            return
        self.resetuj_ts()
        #self.logger.info(self.obszar, 'Resetuje ts z wejscie callbak')
        return

    #TODO procesuj polecenie w klasie corce jesli nie ma logiki to nie musi byc w ogole wolany
    def procesuj_polecenie(self,**params):
        Obszar.procesuj_polecenie(self, **params)
        return Obszar.odpowiedz(self) #skonstruuj_odpowiedzV2OK(constants.RODZAJ_KOMUNIKATU_STAN_OSWIETLENIA, self.stan_oswietlenia)

    def dzialanie_petli(self, nazwa, stan, pozycjapetli):
        self.logger.info(self.obszar, nazwa, 'Jest dzialanie petli, stan ' + str(stan))
        if self.wewy.wyjscia.ustaw_przekaznik_nazwa(nazwa, stan):
            self.logger.info(self.obszar, nazwa, 'Zmiana stanu na: ' + str(stan))
            #self.resetuj_ts()
            #self.aktualizuj_biezacy_stan()
            self.odpal_firebase()

    def wlacz_smietnik_samodzielny(self):
        przek_smie = self.wewy.wyjscia.przekaznik_po_nazwie(NAZWA_SMIETNIK)
        if not przek_smie.get_stan(): #self.prze.stan_przekaznika_nazwa(NAZWA_SMIETNIK):
            tim = time.time()
            self.petla.dodaj_jednorazowy_od_godz_do_godz(przek_smie.get_nazwa(), self.obszar, ts_start=tim,
                                                         ts_stop=tim+int(przek_smie.get_defczaszalaczenia()),
                                                         dzialanie=self.dzialanie_petli)
            #self.petla.dodaj_jednorazowy_na_czas_od_teraz(przek_smie.get_nazwa(),
#                                                          przek_smie.get_defczaszalaczenia(),
#                                                          obszar=self.obszar,
#                                                          dzialanie=self.dzialanie_petli)
            self.logger.info(self.obszar, 'smietnik', 'Wlaczylem oswietlenie nad smietnikiem.')
        return

    def aktualizuj_biezacy_stan(self, odbiornik_pomieszczenie=None):
        #TODO dorobic tutaj i w pozostalych limitowanie do wybranego odbionika_pomieszczenia
        #self.logger.info(self.obszar, 'Aktualizuje biezacy stan z corki')
        self._biezacy_stan = {constants.CYKLE: self.petla.pozycje_do_listy(obszar=self.obszar),
                              constants.ODBIORNIKI: self.wewy.wyjscia.pozycje_do_listy(self.obszar),
                              constants.TS: self.get_ts()}
