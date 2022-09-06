#!/usr/bin/python
import constants
import petlaczasowa
import wejsciawyjscia
import threading
from THutils import odczytaj_parametr_konfiguracji
from THutils import zapisz_temp_w_logu

import time
import atexit
import pigpio
import MySQLdb
import THutils
import os
from MojLogger import MojLogger
from Obszar import Obszar
from copy import deepcopy

PRZEKAZNIK_RESETU_CZUJNIKA_TEMPERATURY = 'reset_czujn_temp'
NAZWA_CYKLU_ODCZYTUJ_TEMPERATURE = 'odczytuj_temperature'

POLE_T_ZEWN = 'T_zewnatrz'
POLE_W_ZEWN = 'W_zewnatrz'
POLE_T_WEWN = 'T_wewnatrz'
POLE_W_WEWN = 'W_wewnatrz'
POLE_WILG_GLEBY = 'W_gleby'

class Temperatura(Obszar):
    def __init__(self,
                 wewy,  # type: wejsciawyjscia.WejsciaWyjscia
                 petla,  # type: petlaczasowa.PetlaCzasowa
                 logger,    #type: MojLogger
                 logger_temperatury,    #type: MojLogger
                 firebase_callback=None):

        Obszar.__init__(self, constants.OBSZAR_TEMP,
                        logger,
                        petla=petla,
                        wewy=wewy,
                        firebase_callback=firebase_callback,
                        rodzaj_komunikatu=constants.RODZAJ_KOMUNIKATU_STAN_TEMPERATURY,
                        callback_przekaznika_wyjscia=self.resetuj_ts,
                        #                        callback_wejscia=self.wejscie_callback,
                        dzialanie_petli=self.dzialanie_petli
                        )
        nr_pinu = int(odczytaj_parametr_konfiguracji(self.obszar, 'PIN_PI_ODLACZANIE_ZASILANIA_CZUJNIKOW'))
        #self.nazwa_przek = 'Reset czujn temp'
        #self.dodaj_wejscie(PRZEKAZNIK_RESETU_CZUJNIKA_TEMPERATURY, nr_pinu)

        self.dodaj_przekaznik(PRZEKAZNIK_RESETU_CZUJNIKA_TEMPERATURY, nr_pinu)
        self.temp_out = -99.9
        self.wilg_out = 0
        self.temp_in = -99.9
        self.wilg_in = 0
        self.wilg_gleby = 0
        self.nr_pinu = 4 #pozniej w konfiguracji jest odczytywana wartosc z pliku
        #TODO nr pinu ujednolicic jest w self i dalej dodawany przekanik, nie potrzeba w self
        self.log_temp = logger_temperatury
        # odstep w godzinach co ile ma byc odswiezana konfiguracja z bazy
        # self.czas_odczytu_konfig = 24
        self.odczytaj_konf()
        self.aktualizuj_biezacy_stan()
        self.s = sensor(self.nr_pinu, power=8)
        self.__odczytaj_temp_i_loguj()
        #THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_TEMP, 'CZAS_ODLACZANIA_CZUJNIKOW')

    def dzialanie_petli(self, nazwa, stan, pozycjapetli):
        if nazwa == PRZEKAZNIK_RESETU_CZUJNIKA_TEMPERATURY:
            self.wewy.wyjscia.ustaw_przekaznik_nazwa(nazwa, stan)
        if nazwa == NAZWA_CYKLU_ODCZYTUJ_TEMPERATURE:
            if stan:
                self.__odczytaj_temp_i_loguj()
                #self.logger.info(self.obszar,'Odczytywanie temparatury sterowane z petli')
                #self.logger.info(self.obszar,'Temperatura: dzialanie na zasialniu etmperatury')
        #if tylko_aktualizuj_ts:
        #    self.resetuj_ts()

    def procesuj_polecenie(self,**params):
        Obszar.procesuj_polecenie(self, **params)
        return Obszar.odpowiedz(self)

    def aktualizuj_biezacy_stan(self, odbiornik_pomieszczenie=None):
        self._biezacy_stan = {POLE_T_ZEWN: self.temp_out,
                              POLE_W_ZEWN: self.wilg_out,
                              POLE_T_WEWN: self.temp_in,
                              POLE_W_WEWN: self.wilg_in,
                              POLE_WILG_GLEBY: self.wilg_gleby,
                              constants.TS: self.get_ts()}

    def odczytaj_konf(self):
        self.nr_pinu = int(THutils.odczytaj_parametr_konfiguracji(self.obszar, 'PIN_PI_TEMPERATURA', self.logger))
        #self.czas_odczytu_konfig = int(THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_TEMP, 'CZAS_ODCZYTU_KONFIG', self.logger))
        self.logger.info(self.obszar, 'Odczytalem konfiguracje temperatura.')

    '''def __resetuj_czujniki_temperatury_cyklicznie(self):
        #czas_odlaczania_czujnikow = int(odczytaj_parametr_konfiguracji(constants.OBSZAR_TEMP, 'CZAS_ODLACZANIA_CZUJNIKOW')) * 60
        # TODO z jakichs powodow nie odczytuje poprawnie powyzszego parametru z konfiguracji
        czas_odlaczania_czujnikow = 38 * 60
        threading.Timer(czas_odlaczania_czujnikow, self.__resetuj_czujniki_temperatury_cyklicznie, []).start()
        #self.__resetuj_czujniki_temperatury()'''

    '''def __zapisz_temp_do_bazy(self):
        try:
            db = MySQLdb.connect(host = "localhost", user = "root", passwd = os.getenv(constants.PWD_BAZY), db = "stacja_pogodowa")
            cur = db.cursor()
            cur.execute("""INSERT INTO stacja_pogodowa.temperatura(outside,wilgotnosc_out,inside,wilgotnosc_in,wilgotnosc_gleby) VALUES (%s, %s, %s, %s, %s)""", (self.temp_out, self.wilg_out, self.temp_in, self.wilg_in, self.wilg_gleby))
            db.commit()
            cur.close()
            db.close()
        except MySQLdb._mysql.OperationalError as serr:
            self.logger.warning(self.obszar, 'Blad zapisu temperatury do bazy danych: ' + str(serr))
'''

    def __odczytaj_temperature_z_czujnika(self):
        self.temp_out = -99.9
        self.wilg_out = 0
        self.s.trigger()
        #oryginalnie bylo 0.2
        #TODO time.sleep do przemyslenia
        time.sleep(0.3)
        self.wilg_out = self.s.humidity()
        self.temp_out = round(float(self.s.temperature()),1)
        #self.logger.info('Odczytalem temp z czujnika' + str(self.temp_out))
        if self.temp_out is None:
            self.wilg_out = 0
            self.temp_out = -99.9

    def __odczytaj_temp_i_loguj(self):
        temp = deepcopy(self.temp_out)
        self.__odczytaj_temperature_z_czujnika()
        # self.aktualizuj_biezacy_stan()
        #if int(round(temp)) != int(round(self.temp_out)):
        if temp != self.temp_out:
            self.resetuj_ts()
            zapisz_temp_w_logu(self.log_temp, POLE_T_ZEWN, self.temp_out)
            self.odpal_firebase()
        self.aktualizuj_biezacy_stan()
        #self.__zapisz_temp_do_bazy()

class sensor:

   def __init__(self, nr_pinu, LED=None, power=None):
      # self.pi = pi
      self.pi = pigpio.pi()
      self.nr_pinu = nr_pinu
      self.LED = LED
      self.power = power

      if power is not None:
         self.pi.write(power, 1) # Switch sensor on.
         time.sleep(2)

      self.powered = True

      self.cb = None

      atexit.register(self.cancel)

      self.bad_CS = 0 # Bad checksum count.
      self.bad_SM = 0 # Short message count.
      self.bad_MM = 0 # Missing message count.
      self.bad_SR = 0 # Sensor reset count.

      # Power cycle if timeout > MAX_TIMEOUTS.
      self.no_response = 0
      self.MAX_NO_RESPONSE = 2

      self.rhum = -999
      self.temp = -999

      self.tov = None

      self.high_tick = 0
      self.bit = 40

      self.pi.set_pull_up_down(nr_pinu, pigpio.PUD_OFF)

      self.pi.set_watchdog(nr_pinu, 0) # Kill any watchdogs.

      self.cb = self.pi.callback(nr_pinu, pigpio.EITHER_EDGE, self._cb)

   def _cb(self, gpio, level, tick):
      """
      Accumulate the 40 data bits.  Format into 5 bytes, humidity high,
      humidity low, temperature high, temperature low, checksum.
      """
      diff = pigpio.tickDiff(self.high_tick, tick)

      if level == 0:

         # Edge length determines if bit is 1 or 0.

         if diff >= 50:
            val = 1
            if diff >= 200: # Bad bit?
               self.CS = 256 # Force bad checksum.
         else:
            val = 0

         if self.bit >= 40: # Message complete.
            self.bit = 40

         elif self.bit >= 32: # In checksum byte.
            self.CS  = (self.CS<<1)  + val

            if self.bit == 39:

               # 40th bit received.

               self.pi.set_watchdog(self.nr_pinu, 0)

               self.no_response = 0

               total = self.hH + self.hL + self.tH + self.tL

               if (total & 255) == self.CS: # Is checksum ok?

                  self.rhum = ((self.hH<<8) + self.hL) * 0.1

                  if self.tH & 128: # Negative temperature.
                     mult = -0.1
                     self.tH = self.tH & 127
                  else:
                     mult = 0.1

                  self.temp = ((self.tH<<8) + self.tL) * mult

                  self.tov = time.time()

                  if self.LED is not None:
                     self.pi.write(self.LED, 0)

               else:

                  self.bad_CS += 1

         elif self.bit >=24: # in temp low byte
            self.tL = (self.tL<<1) + val

         elif self.bit >=16: # in temp high byte
            self.tH = (self.tH<<1) + val

         elif self.bit >= 8: # in humidity low byte
            self.hL = (self.hL<<1) + val

         elif self.bit >= 0: # in humidity high byte
            self.hH = (self.hH<<1) + val

         else:               # header bits
            pass

         self.bit += 1

      elif level == 1:
         self.high_tick = tick
         if diff > 250000:
            self.bit = -2
            self.hH = 0
            self.hL = 0
            self.tH = 0
            self.tL = 0
            self.CS = 0

      else: # level == pigpio.TIMEOUT:
         self.pi.set_watchdog(self.nr_pinu, 0)
         if self.bit < 8:       # Too few data bits received.
            self.bad_MM += 1    # Bump missing message count.
            self.no_response += 1
            if self.no_response > self.MAX_NO_RESPONSE:
               self.no_response = 0
               self.bad_SR += 1 # Bump sensor reset count.
               if self.power is not None:
                  self.powered = False
                  self.pi.write(self.power, 0)
                  time.sleep(2)
                  self.pi.write(self.power, 1)
                  time.sleep(2)
                  self.powered = True
         elif self.bit < 39:    # Short message receieved.
            self.bad_SM += 1    # Bump short message count.
            self.no_response = 0

         else:                  # Full message received.
            self.no_response = 0

   def temperature(self):
      """Return current temperature."""
      return self.temp

   def humidity(self):
      """Return current relative humidity."""
      return self.rhum

   def staleness(self):
      """Return time since measurement made."""
      if self.tov is not None:
         return time.time() - self.tov
      else:
         return -999

   def bad_checksum(self):
      """Return count of messages received with bad checksums."""
      return self.bad_CS

   def short_message(self):
      """Return count of short messages."""
      return self.bad_SM

   def missing_message(self):
      """Return count of missing messages."""
      return self.bad_MM

   def sensor_resets(self):
      """Return count of power cycles because of sensor hangs."""
      return self.bad_SR

   def trigger(self):
      """Trigger a new relative humidity and temperature reading."""
      if self.powered:
         if self.LED is not None:
            self.pi.write(self.LED, 1)

         self.pi.write(self.nr_pinu, pigpio.LOW)
         time.sleep(0.017) # 17 ms
         self.pi.set_mode(self.nr_pinu, pigpio.INPUT)
         self.pi.set_watchdog(self.nr_pinu, 200)

   def cancel(self):
      """Cancel the DHT22 sensor."""

      self.pi.set_watchdog(self.nr_pinu, 0)

      if self.cb is not None:
         self.cb.cancel()
         self.cb = None

#----------------------------------------------
#glowny program
#----------------------------------------------
"""temp = temperatura()
temp.pobieraj_temperature_cyklicznie()
temp.uruchom_serwer()"""