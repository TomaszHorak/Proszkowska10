import przekazniki_BCM
import tda8425

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
    def __init__(self, mcp, logger):
        """tab = [{'numer': NR_WZMACNIACZA_KUCHNIA, 'nazwa': NAZWA_WZMACNIACZA_KUCHNIA, 'pin': 7},
               {'numer': NR_WZMACNIACZA_TARAS, 'nazwa': NAZWA_WZMACNIACZA_TARAS, 'pin': 6},
               {'numer': NR_WZMACNIACZA_LAZIENKA, 'nazwa': NAZWA_WZMACNIACZA_LAZIENKA, 'pin': 5},
               {'numer': NR_WZMACNIACZA_SYPIALNIA, 'nazwa': NAZWA_WZMACNIACZA_SYPIALNIA, 'pin': 3},
               {'numer': NR_WZMACNIACZA_BALKON, 'nazwa': NAZWA_WZMACNIACZA_BALKON, 'pin': 4}]"""
        self.przek = przekazniki_BCM.PrzekaznikiBCM(mcp)
        self.przek.dodaj_przekaznik(NAZWA_WZMACNIACZA_KUCHNIA, PIN_WZMACNIACZA_KUCHNIA)
        self.przek.dodaj_przekaznik(NAZWA_WZMACNIACZA_TARAS, PIN_WZMACNIACZA_TARAS)
        self.przek.dodaj_przekaznik(NAZWA_WZMACNIACZA_LAZIENKA, PIN_WZMACNIACZA_LAZIENKA)
        self.przek.dodaj_przekaznik(NAZWA_WZMACNIACZA_SYPIALNIA, PIN_WZMACNIACZA_SYPIALNIA)
        self.przek.dodaj_przekaznik(NAZWA_WZMACNIACZA_BALKON, PIN_WZMACNIACZA_BALKON)

        self.wzmacniacze = []
        self.wzmacniacze.append(tda8425.TDA8425(NR_WZMACNIACZA_KUCHNIA, NAZWA_WZMACNIACZA_KUCHNIA))
        self.wzmacniacze.append(tda8425.TDA8425(NR_WZMACNIACZA_TARAS, NAZWA_WZMACNIACZA_TARAS))
        self.wzmacniacze.append(tda8425.TDA8425(NR_WZMACNIACZA_LAZIENKA, NAZWA_WZMACNIACZA_LAZIENKA))
        self.wzmacniacze.append(tda8425.TDA8425(NR_WZMACNIACZA_SYPIALNIA, NAZWA_WZMACNIACZA_SYPIALNIA))
        self.wzmacniacze.append(tda8425.TDA8425(NR_WZMACNIACZA_BALKON, NAZWA_WZMACNIACZA_BALKON))
        self.logger = logger
        return

    def do_listy(self):
        temp = {}
        for i in self.wzmacniacze:
            temp1 = {"Glosnosc": i.glosnosc,
                     "Nr_wejscia": i.nr_wejscia,
                     "Stan": self.przek.stan_przekaznika_nazwa(i.nazwa)}
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
        if self.przek.stan_przekaznika_nazwa(nazwa):
            wzm.ustaw_glosnosc(glosnosc)

    def set_glosnosc_delta_nazwa(self, nazwa, liczba_krokow):
        if self.przek.przekaznik_po_nazwie(nazwa).get_stan():
            wzm = self.wzmacniacz_po_nazwie(nazwa)
            wzm.ustaw_glosnosc(int(wzm.glosnosc + liczba_krokow))

    # TODO do usuniecia jak mysocket usuniete zostanie ST -> GL
    def wzmacniacz_po_numerze(self, nr):
        for j in self.wzmacniacze:
            if j.numer == nr:
                return j
        return None

    def wzmacniacz_po_nazwie(self, nazwa):
        for j in self.wzmacniacze:
            if j.nazwa == nazwa:
                return j
        return None
