import constants
from MojLogger import MojLogger
import time
import THutils
import petlaczasowa
import wejsciawyjscia
import datetime
import threading

#TODO dorobic metode odczytywania na nowo parametrow i inicjacji, ma to sluzyc temu aby nie trzeba bylo resetowac calej apki
#TODO dodatkowa komenda: zaktualizuj parametry


''' Dokumentacja API

every command structure:
'komenda' - command -> constants.KOMENDA 
'parametry' - additional parameters

AKTYWACJA SCHEMATU: constants.AKTYWACJA_SCHEMATU
aktywuje schemat w petli dla danego obszaru oraz wszystkich wystapien danego odbiornika
constants.NAZWA = name of the schema/odbiornik/nazwa petli
constants.POLE_STAN = true or false:

ODBIORNIK_NA_CZAS: constants.ODBIORNIK_NA_CZAS
wlacza podany odbiornik na okreslony czas w sekundach. Wlaczenie od teraz w petli, nie wlacza bezposrednio.
Ddodaje jednorazowy wpis do petli.
constants.NAZWA = name of the schema/odbiornik/nazwa petli
constants.CZAS = czas na jaki ma zalaczyc odbiornik w sekundach

TOGGLE_ODBIORNIK_NAZWA: constants.TOGGLE_ODBIORNIK_NAZWA
przelacza (toggle) odbiornik po nazwie
constants.NAZWA = name of the odbiornik

KOMENDA_AKTUALIZUJ_CYKL: constants.KOMENDA_AKTUALIZUJ_CYKL
aktualizuje cykl w petli czasowej
constants.CYKL = json z definicja cyklu

KOMENDA_DODAJ_CYKL: constants.KOMENDA_DODAJ_CYKL
dodaje cykl do petli czasowej
constants.CYKL = json z definicja cyklu

KOMENDA_USUN_CYKL: constants.KOMENDA_USUN_CYKL
usuwa cykl wedlug hasha
constants.HASH = numer hash cyklu do usuniecia

'''


class Obszar:
    def __init__(self,
                 obszar,
                 logger,
                 petla=None,  # type: petlaczasowa.PetlaCzasowa
                 wewy=None,  # type: wejsciawyjscia.WejsciaWyjscia
                 firebase_callback=None,
                 rodzaj_komunikatu='',
                 callback_przekaznika_wyjscia=None,
                 callback_wejscia=None,
                 dzialanie_petli=None):
        self.logger = logger    #type: MojLogger
        self._biezacy_stan = {}
        self.__callback_przekaznika_wyjscia = callback_przekaznika_wyjscia
        self.__callback_wejsica = callback_wejscia
        self.wewy = wewy
        self.__firebase_callback = firebase_callback
        self.__ts = time.time()*1000
        self.procesuje = threading.Lock() #jesli tru to blokuj podawanie statusu
        self.petla = petla
        self._dzialanie_petli = dzialanie_petli
        if petla is not None:
            self.petla.rejestruj_dzialanie(obszar, self._dzialanie_petli)
        self.obszar = obszar
        self.__rodzaj_komunikatu = rodzaj_komunikatu
        #self.resetuj_ts()

    def odswiez_konfiguracje(self):
        #TODO zaimplementowac we wszystkich dzidziczonych klasach: odswiezanie konfiguracji z pliku ini
        return

    def dodaj_przekaznik(self, nazwa, pin, def_czas_zalaczenia=0, impuls=False, czas_impulsu=1):
        if self.wewy is not None:
            self.wewy.wyjscia.dodaj_przekaznik(nazwa, pin,
                                               callbackfunction=self.__callback_przekaznika_wyjscia,
                                               obszar=self.obszar,
                                               impuls=impuls,
                                               czas_impulsu=czas_impulsu,
                                               def_czas_zalaczenia=def_czas_zalaczenia)

    def dodaj_wejscie(self, nazwa, pin):
        if self.wewy is not None:
            self.wewy.wejscia.dodaj_wejscie(nazwa, pin,
                                            callback=self.__callback_wejsica)

    def resetuj_ts(self):
        #self.logger.info(self.obszar, 'Resetuje ts')
        self.__ts = time.time()*1000
        self.aktualizuj_biezacy_stan()

    def get_ts(self):
        return self.__ts

    def procesuj_polecenie(self, **params):
        #zwraca albo constants.komenda jesli w params byla komenda
        #albo rodzaj komunikatu jesli byl w pramas
        #None jesli byl bledne params
        self.procesuje.acquire()

        if constants.RODZAJ_KOMUNIKATU in params:
            return constants.RODZAJ_KOMUNIKATU

        if constants.KOMENDA in params: #przetwarza komende
            if params[constants.KOMENDA] == constants.AKTYWACJA_SCHEMATU:  # odbiornik w petli sterowanie, aktywacja schematu
                if self.petla is not None:
                    if constants.HASH not in params:
                        self.logger.warning(self.obszar, 'Brak parametru HASH w poleceniu aktywacji schematu: ' + str(params))
                        return
                    if constants.POLE_STAN not in params:
                        self.logger.warning(self.obszar, 'Brak parametru STAN w poleceniu aktywacji schematu: ' + str(params))
                        return
                    self.petla.aktywuj_pozycje_hash(params[constants.HASH], params[constants.POLE_STAN])
                    self.resetuj_ts()
                    self.logger.info(self.obszar, 'Aktywacja petli: ' + str(params[constants.HASH]) +
                                     '. Stan: ' + str(params[constants.POLE_STAN]))
            elif params[constants.KOMENDA] == constants.ODBIORNIK_NA_CZAS:
                if self.petla is not None:
                    if constants.NAZWA not in params:
                        return
                    if constants.CZAS not in params:
                        return
                    tim = time.time()*1000
                    self.petla.dodaj_jednorazowy_od_godz_do_godz(params[constants.NAZWA], self.obszar, ts_start=tim,
                                                                 ts_stop=tim+int(params[constants.CZAS]),
                                                                 dzialanie=self.dzialanie_petli)
                    self.logger.info(self.obszar, 'Odbiornik ' + str(params[constants.NAZWA]) +
                                     ', na czas: ' + str(params[constants.CZAS]))
                    self.resetuj_ts()
                    #self.odpal_firebase()
                else:
                    self.logger.warning(self.obszar, "Chciano wlaczyc na czas odbiornik ale nie ma petli w obszarze.")
            elif params[constants.KOMENDA] == constants.TOGGLE_ODBIORNIK_NAZWA:  # wlacz po nazwie
                if constants.NAZWA not in params:
                    return
                if self.wewy is not None:
                    self.wewy.wyjscia.toggle_przekaznik_nazwa(params[constants.NAZWA])
                    self.logger.info(self.obszar, 'Kliknieto odbiornik: ' + str(params[constants.NAZWA]))
                    #self.resetuj_ts()
                    #self.odpal_firebase()
            elif params[constants.KOMENDA] == constants.KOMENDA_AKTUALIZUJ_CYKL:
                if self.petla is not None:
                    if constants.CYKL not in params:
                        self.logger.warning(self.obszar, 'Brak definicji cyklu w komendzie aktualizacji cyklu: ' + str(params))
                        return
                    if self.petla.aktualizuj_pozycje(params[constants.CYKL]):
                        self.resetuj_ts()
                        self.logger.info(self.obszar, 'Zaktualizowano cykl: ' + str(params))
                else:
                    self.logger.warning(self.obszar, "Chciano wlaczyc na czas odbiornik ale nie ma petli w obszarze.")
            elif params[constants.KOMENDA] == constants.KOMENDA_DODAJ_CYKL:
                if self.petla is not None:
                    if constants.CYKL not in params:
                        return
                    self.petla.dodaj_nowy_cykl(params[constants.CYKL], self._dzialanie_petli)
                    self.resetuj_ts()
                else:
                    self.logger.warning(self.obszar, "Chciano wlaczyc na czas odbiornik ale nie ma petli w obszarze.")
            elif params[constants.KOMENDA] == constants.KOMENDA_USUN_CYKL:
                if self.petla is not None:
                    if constants.HASH not in params:
                        return
                    self.petla.usun_cykl_po_hashu(params[constants.HASH])
                    self.resetuj_ts()
                else:
                    self.logger.warning(self.obszar, "Chciano wlaczyc na czas odbiornik ale nie ma petli w obszarze.")
            return constants.KOMENDA
        self.logger.warning(self.obszar, 'Brak parametru KOMENDA lub RODZAJ KOMUNIKATU w poleceniu: ' + str(params))
        return None

    def odpowiedz(self):
        #self.aktualizuj_biezacy_stan()
        self.procesuje.release()
        return THutils.skonstruuj_odpowiedzV2OK(self.__rodzaj_komunikatu, self.get_biezacy_stan(), self.obszar)

    def godzina_minuta(self):
        now = datetime.datetime.now()
        return str(now.hour) + ":" + str(now.minute).zfill(2)

    def zwroc_date(self):
        return datetime.datetime.today().strftime('%d.%m.%Y')

    def aktualizuj_biezacy_stan(self, odbiornik_pomieszczenie=None):
        #odbiornik_pomiesznie jesli nie None to limitujemy liste odbiornikow i cykli tylko do tego jednego
        #self.logger.info(self.obszar, 'Aktualizuj biez stan z klasy matki')
        pass

    def dzialanie_petli(self, nazwa, stan, wartosc):
        return

    def wejscie_callback(self, pin, nazwa, stan):
        return

    def odpal_firebase(self):
        if self.__firebase_callback is not None:
            self.__firebase_callback(self.__rodzaj_komunikatu, self._biezacy_stan)

    def get_biezacy_stan(self):
        #pass
        return self._biezacy_stan