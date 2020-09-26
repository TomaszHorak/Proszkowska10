# import RPi.GPIO as GPIO
import time
from threading import Thread

class przekazniki:
    # procedur do inicjowania stanu GPIO na poczatku
    def __init__(self, numery_pinow):
        # tabela pin definiuje numery pinow pod numer przekaznika, wedlug kolejnosci wystepowania w tablicy
        # druga kolumna w tabeli okresla biezacy stan przekaznika
        self.pin = []
        GPIO.setmode(GPIO.BCM)

        # nr pinu na szynie GPIO | stan przekaznika
        for j in numery_pinow:
            self.pin.append([j, 0])

        for j in range(len(self.pin)):
            GPIO.setup(self.pin[j][0], GPIO.OUT, initial=GPIO.HIGH)

    def ustaw_przekaznik(self, nr_przekaznika, stan):
        if stan == 1:
            GPIO.output(self.pin[nr_przekaznika][0], 0)
            self.pin[nr_przekaznika][1] = 1
        else:
            GPIO.output(self.pin[nr_przekaznika][0], 1)
            self.pin[nr_przekaznika][1] = 0

    def wylacz_wszystkie_sekcje(self):
        for j in range(len(self.pin)):
            self.ustaw_przekaznik(j, 0)

    def uaktualnij_stan_przekaznikow(self):
        if self.gpio_bcm == 'GPIO':
            for j in range(len(self.pin)):
                if GPIO.input(self.pin[j][0]) == 1:
                    self.pin[j][1] = 0
                else:
                    self.pin[j][1] = 1

    def wylacz_po_czasie(self, nr_przekaznika, czas):
        self.ustaw_przekaznik(nr_przekaznika, 0)
        time.sleep(czas)
        self.ustaw_przekaznik(nr_przekaznika, 1)

    def wlacz_na_czas(self, nr_przekaznika, czas):
        if czas == 0:
            return self.ustaw_przekaznik(nr_przekaznika, 0)
        thread = Thread(target=self.wylacz_po_czasie, args=(nr_przekaznika, czas))
        thread.start()

    def czy_ktorykolwiek_wlaczony(self):
        #sprawdza czy ktoryklwiek z przekaznikow jest wlaczony, jesli tak to zwraca 1 jesli nie to zwraca 0
        for j in range(len(self.pin)):
            if self.pin[j][1] == 1:
                return 1
        return 0

    def cleanup(self):
        GPIO.cleanup()
