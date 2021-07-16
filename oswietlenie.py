import petlaczasowa
import constants
import wejsciawyjscia
from Obszar import Obszar

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
                 firebase_callback=None):

        Obszar.__init__(self, wewy,petla, constants.OBSZAR_OSWI, firebase_callback=firebase_callback,
                        rodzaj_komunikatu_firebase=constants.RODZAJ_KOMUNIKATU_STAN_OSWIETLENIA,
                        callback_przekaznika_wyjscia=self.aktualizuj_biezacy_stan,
                        callback_wejscia=self.wejscie_callback,
                        dzialanie_petli=self.dzialanie_petli)

        self.dodaj_przekaznik(NAZWA_ZIMOWE, PIN_ZIMOWE)
        self.dodaj_przekaznik(NAZWA_OGNISKO, PIN_OGNISKO, def_czas_zalaczenia=500)
        self.dodaj_przekaznik(NAZWA_SMIETNIK, PIN_SMIETNIK)
        self.dodaj_przekaznik(NAZWA_JADALNIA, PIN_JADALNIA)

        self.dodaj_wejscie(WEJSCIE_WLACZNIK_SMIETNIK_WIATROLAP, PIN_WL_SMIETNIK_WIATROLAP)
        self.dodaj_wejscie(WEJSCIE_WLACZNIK_SMIETNIK_GARAZ4, PIN_WL_SMIETNIK_GARAZ4)

        self.wewy.wyjscia.ustaw_przekaznik_nazwa(NAZWA_SMIETNIK, False)
        self.wewy.wyjscia.ustaw_przekaznik_nazwa(NAZWA_ZIMOWE, False)
        self.wewy.wyjscia.ustaw_przekaznik_nazwa(NAZWA_OGNISKO, False)
        self.wewy.wyjscia.ustaw_przekaznik_nazwa(NAZWA_JADALNIA, False)

        self.aktualizuj_biezacy_stan()
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
        self.resetuj_ts()
        return

    def procesuj_polecenie(self,komenda, parametr1, parametr2):
        #if komenda == constants.KOMENDA_ODCZYTAJ_CYKLE_Z_KONFIGURACJI:
        #    self.petla.odczytaj_cykle_z_konfiguracji()
        #self.aktualizuj_biezacy_stan_oswietlenia()
        return Obszar.procesuj_polecenie(self, komenda, parametr1, parametr2) #skonstruuj_odpowiedzV2OK(constants.RODZAJ_KOMUNIKATU_STAN_OSWIETLENIA, self.stan_oswietlenia)

    def dzialanie_petli(self, nazwa, stan, tylko_aktualizuj_ts=False):
        if tylko_aktualizuj_ts:
            self.resetuj_ts()
            self.aktualizuj_biezacy_stan()
            return
        stan_poprzzedni = False
        if self.wewy.wyjscia.stan_przekaznika_nazwa(nazwa):
            stan_poprzzedni = True
        self.wewy.wyjscia.ustaw_przekaznik_nazwa(nazwa, stan)
        if self.wewy.wyjscia.stan_przekaznika_nazwa(nazwa) != stan_poprzzedni:
            self.resetuj_ts()
            self.logger.info('Oswietlenie ' + nazwa + ', stan: ' + str(stan))
            self.aktualizuj_biezacy_stan()
            self.odpal_firebase()

    def wlacz_smietnik_samodzielny(self):
        przek_smie = self.wewy.wyjscia.przekaznik_po_nazwie(NAZWA_SMIETNIK)
        if not przek_smie.get_stan(): #self.prze.stan_przekaznika_nazwa(NAZWA_SMIETNIK):
            self.petla.dodaj_do_tabeli_jednorazowy_na_czas(przek_smie.get_nazwa(),
                                                                               przek_smie.get_defczaszalaczenia(),
                                                                               obszar=self.obszar,
                                                                               dzialanie=self.dzialanie_petli)
            self.logger.info('Wlaczylem oswietlenie nad smietnikiem.')
        return

    def aktualizuj_biezacy_stan(self):
        self._biezacy_stan = {constants.CYKLE: self.petla.pozycje_do_listy(obszar=self.obszar),
                                        constants.ODBIORNIKI: self.wewy.wyjscia.pozycje_do_listy(self.obszar),
                                        constants.TS: self.ts}

    '''def aktualizuj_biezacy_stan_oswietlenia(self):
        Obszar.aktualizuj_biezacy_stan(self,{constants.CYKLE: self.petla.pozycje_do_listy(obszar=self.obszar),
                                        constants.ODBIORNIKI: self.wewy.wyjscia.pozycje_do_listy(self.obszar),
                                        constants.TS: self.ts})'''
