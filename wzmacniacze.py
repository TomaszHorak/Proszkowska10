import constants
import time
import max9744
import RPi.GPIO as GPIO

NAZWA_WZMACNIACZA_KUCHNIA = "Kuchnia"
NAZWA_WZMACNIACZA_TARAS = "Taras"
NAZWA_WZMACNIACZA_LAZIENKA = "Lazienka"

#piny wzmacniacza oznaczaja pin na plycie raspberry podlaczony do MUTE w max9744
PIN_WZMACNIACZA_KUCHNIA = 17
PIN_WZMACNIACZA_TARAS = 27
PIN_WZMACNIACZA_LAZIENKA = 22

class Wzmacniacze:
    def __init__(self, logger):
        #ustawienie wyjsc sterujacych MUTem
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(PIN_WZMACNIACZA_TARAS, GPIO.OUT)  # set a port/pin as an output
        GPIO.setup(PIN_WZMACNIACZA_KUCHNIA, GPIO.OUT)  # set a port/pin as an output
        GPIO.setup(PIN_WZMACNIACZA_LAZIENKA, GPIO.OUT)  # set a port/pin as an output

        self.wzmacniacze = []   #type: [max9744.MAX9744]
        self.wzmacniacze.append(max9744.MAX9744(NAZWA_WZMACNIACZA_KUCHNIA, max9744.MAX9744_I2CADDR_4A, PIN_WZMACNIACZA_KUCHNIA, GPIO))
        self.wzmacniacze.append(max9744.MAX9744(NAZWA_WZMACNIACZA_LAZIENKA, max9744.MAX9744_I2CADDR_49, PIN_WZMACNIACZA_LAZIENKA, GPIO))
        self.wzmacniacze.append(max9744.MAX9744(NAZWA_WZMACNIACZA_TARAS, max9744.MAX9744_I2CADDR_4B, PIN_WZMACNIACZA_TARAS, GPIO))
        self.logger = logger
        self.ts = time.time()*1000
        return

    def czy_ktorykolwiek_wlaczony(self):
        for j in self.wzmacniacze:
            if j.stan:
                return True
        return False

    def do_listy(self):
        temp = {constants.TS: self.ts}
        for i in self.wzmacniacze:
            temp1 = {constants.POLE_GLOSNOSC: i.glosnosc,
                     constants.POLE_STAN: self.wzmacniacz_po_nazwie(i.nazwa).stan}
            temp[i.nazwa] = temp1
        return temp

    def set_glosnosc_nazwa(self, nazwa, glosnosc):
        wzm = self.wzmacniacz_po_nazwie(nazwa)
        if wzm:
            wzm.ustaw_glosnosc(glosnosc)
            self.ts = time.time()*1000
            return True
        return False

    def set_glosnosc_delta_nazwa(self, nazwa, liczba_krokow):
        wzm = self.wzmacniacz_po_nazwie(nazwa)
        if wzm:
            wzm.ustaw_glosnosc(int(wzm.glosnosc + liczba_krokow))
            self.ts = time.time()*1000
            return True
        return False

    def wlacz_wylacz_wszystkie(self, stan):
        for j in self.wzmacniacze:
            j.wlacz_wylacz(stan)
        self.ts = time.time()*1000

    def stan_wzmacniacza_po_nazwie(self, nazwa):
        wzm = self.wzmacniacz_po_nazwie(nazwa)
        return wzm.stan

    def wlacz_wylacz(self, nazwa, stan):
        a = self.wzmacniacz_po_nazwie(nazwa)    #type: [max9744.MAX9744]
        if a:
            a.wlacz_wylacz(stan)
            self._zmiana_stanu(nazwa, stan)
            return True
        return False

    def toggle_wzmacniacz_nazwa(self, nazwa):
        a = self.wzmacniacz_po_nazwie(nazwa)    #type: [max9744.MAX9744]
        if a:
            if a.stan:
                a.wlacz_wylacz(False)
                self._zmiana_stanu(nazwa, False)
            else:
                a.wlacz_wylacz(True)
                self._zmiana_stanu(nazwa, True)
            return True
        return False

    def _zmiana_stanu(self, nazwa, stan):
            self.logger.info(constants.OBSZAR_NAGL, 'Zmiana stanu wzmacniacza ' + str(nazwa) + ' na ' + str(stan))
            self.ts = time.time()*1000

    def wzmacniacz_po_nazwie(self, nazwa):
        for j in self.wzmacniacze:
            if j.nazwa == nazwa:
                return j
        return None
