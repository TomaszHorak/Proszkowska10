import tda8425
import constants
import time

NR_WZMACNIACZA_KUCHNIA = 0
NR_WZMACNIACZA_TARAS = 1
NR_WZMACNIACZA_LAZIENKA = 2
NR_WZMACNIACZA_SYPIALNIA = 3
NR_WZMACNIACZA_BALKON = 4
NR_WZMACNIACZA_DENON = 5
NAZWA_WZMACNIACZA_KUCHNIA = "Kuchnia"
NAZWA_WZMACNIACZA_TARAS = "Taras"
NAZWA_WZMACNIACZA_LAZIENKA = "Lazienka"
NAZWA_WZMACNIACZA_SYPIALNIA = "Sypialnia"
NAZWA_WZMACNIACZA_BALKON = "Balkon"
NAZWA_WZMACNIACZA_DENON = "Denon"
PIN_WZMACNIACZA_KUCHNIA = 7
PIN_WZMACNIACZA_TARAS = 6
PIN_WZMACNIACZA_LAZIENKA = 5
PIN_WZMACNIACZA_SYPIALNIA = 3
PIN_WZMACNIACZA_BALKON = 4


class Wzmacniacze:
    def __init__(self, wewy, logger):
        """tab = [{'numer': NR_WZMACNIACZA_KUCHNIA, 'nazwa': NAZWA_WZMACNIACZA_KUCHNIA, 'pin': 7},
               {'numer': NR_WZMACNIACZA_TARAS, 'nazwa': NAZWA_WZMACNIACZA_TARAS, 'pin': 6},
               {'numer': NR_WZMACNIACZA_LAZIENKA, 'nazwa': NAZWA_WZMACNIACZA_LAZIENKA, 'pin': 5},
               {'numer': NR_WZMACNIACZA_SYPIALNIA, 'nazwa': NAZWA_WZMACNIACZA_SYPIALNIA, 'pin': 3},
               {'numer': NR_WZMACNIACZA_BALKON, 'nazwa': NAZWA_WZMACNIACZA_BALKON, 'pin': 4}]"""
        self.przek = wewy.wyjscia
        #TODO dodac callback function we wzamcnaiczach
        self.przek.dodaj_przekaznik(NAZWA_WZMACNIACZA_KUCHNIA, PIN_WZMACNIACZA_KUCHNIA, obszar=constants.OBSZAR_NAGL)
        self.przek.dodaj_przekaznik(NAZWA_WZMACNIACZA_TARAS, PIN_WZMACNIACZA_TARAS, obszar=constants.OBSZAR_NAGL)
        self.przek.dodaj_przekaznik(NAZWA_WZMACNIACZA_LAZIENKA, PIN_WZMACNIACZA_LAZIENKA, obszar=constants.OBSZAR_NAGL)
        self.przek.dodaj_przekaznik(NAZWA_WZMACNIACZA_SYPIALNIA, PIN_WZMACNIACZA_SYPIALNIA, obszar=constants.OBSZAR_NAGL)
        self.przek.dodaj_przekaznik(NAZWA_WZMACNIACZA_BALKON, PIN_WZMACNIACZA_BALKON, obszar=constants.OBSZAR_NAGL)

        self.wzmacniacze = []
        self.wzmacniacze.append(tda8425.TDA8425(NR_WZMACNIACZA_KUCHNIA, NAZWA_WZMACNIACZA_KUCHNIA))
        self.wzmacniacze.append(tda8425.TDA8425(NR_WZMACNIACZA_TARAS, NAZWA_WZMACNIACZA_TARAS))
        self.wzmacniacze.append(tda8425.TDA8425(NR_WZMACNIACZA_LAZIENKA, NAZWA_WZMACNIACZA_LAZIENKA))
        self.wzmacniacze.append(tda8425.TDA8425(NR_WZMACNIACZA_SYPIALNIA, NAZWA_WZMACNIACZA_SYPIALNIA))
        self.wzmacniacze.append(tda8425.TDA8425(NR_WZMACNIACZA_BALKON, NAZWA_WZMACNIACZA_BALKON))
        self.logger = logger
        self.ts = self.ts = int(time.time())
        return

    def do_listy(self):
        temp = {}
        temp[constants.TS] = self.ts
        for i in self.wzmacniacze:
            temp1 = {constants.POLE_GLOSNOSC: i.glosnosc,
                     # constants.POLE_NR_WEJSCIA: i.nr_wejscia,
                     constants.POLE_STAN: self.przek.stan_przekaznika_nazwa(i.nazwa)}
            temp[i.nazwa] = temp1
        # odswiezenie wzmacniacza Denon
        # temp2 = {"Nazwa_wejscia": self.den.current_source,
#                 "Glosnosc": int(self.den.current_volume),
 #                "Stan": self.den.current_ispwon}
  #      temp["Denon"] = temp2
        #dane["Wzmacniacze"] = temp
        return temp

    def set_glosnosc_nazwa(self, nazwa, glosnosc):
        wzm = self.wzmacniacz_po_nazwie(nazwa)
        #if self.przek.stan_przekaznika_nazwa(nazwa):
        wzm.ustaw_glosnosc(glosnosc)
        self.ts = int(time.time())

    def set_glosnosc_delta_nazwa(self, nazwa, liczba_krokow):
        #if self.przek.przekaznik_po_nazwie(nazwa).get_stan():
        wzm = self.wzmacniacz_po_nazwie(nazwa)
        wzm.ustaw_glosnosc(int(wzm.glosnosc + liczba_krokow))
        self.ts = int(time.time())

    def wzmacniacz_po_nazwie(self, nazwa):
        for j in self.wzmacniacze:
            if j.nazwa == nazwa:
                return j
        return None
