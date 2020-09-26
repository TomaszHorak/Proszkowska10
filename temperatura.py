#!/usr/bin/python
import constants
from THutils import odczytaj_parametr_konfiguracji

try:
    import threading
    import time
    import datetime
    from multiprocessing.connection import Listener
    import atexit
    #import DHT22
    import pigpio
    import MySQLdb
    #import Adafruit_DHT
    from multiprocessing.connection import Client
    import THutils
    import json
    import firebasenotification
    import thread
    import logging
    import przekazniki_BCM
    from copy import deepcopy
except (ImportError) as serr:
    pass
PORT_LOKALNY = 6050

class temperatura:
    def __init__(self, mcp, firebase_callback=None):
        self.mcp = mcp
        self.temp_out = -99.9
        self.wilg_out = 0
        self.temp_in = -99.9
        self.wilg_in = 0
        self.wilg_gleby = 0
        self.ts = 0
        self.firebase_callback = firebase_callback
        self.stan_temperatury = {}
        # self.pi = pigpio.pi()
        self.logger = logging.getLogger(constants.NAZWA_LOGGERA)
        self.nr_pinu = 4 #pozniej w konfiguracji jest odczytywana wartosc z pliku
 #       GPIO.setmode(GPIO.BCM)
        self.odstep_odczytu_temperatury = 180
        # odstep w godzinach co ile ma byc odswiezana konfiguracja z bazy
        self.czas_odczytu_konfig = 24
        self.MOJE_IP = THutils.moje_ip('eth0')
        self.odczytaj_konf()
        #self.odczytaj_konfiguracje_cyklicznie()
        self.aktualizuj_stan_temperatury()
        #self.nr_pinu = int(odczytaj_konfiguracje.odczytaj_konfiguracje_z_bazy('TEMP', 'PIN_PI_TEMPERATURA'))
        #self.odstep_odczytu_temperatury = int(odczytaj_konfiguracje.odczytaj_konfiguracje_z_bazy('OGOLNE', 'ODST_ODCZ_TEMP'))
        self.s = sensor(self.nr_pinu, power=8)
        THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_TEMP, 'CZAS_ODLACZANIA_CZUJNIKOW')
        self.pobieraj_temperature_cyklicznie()
        self.resetuj_czujniki_temperatury_cyklicznie()

    def procesuj_polecenie(self,komenda, parametr1, parametr2):
        # self.aktualizuj_stan_temperatury()
        return THutils.skonstruuj_odpowiedzV2(constants.RODZAJ_KOMUNIKATU_STAN_TEMPERATURY,
                                              self.stan_temperatury, constants.STATUS_OK)

    def aktualizuj_stan_temperatury(self):
        dane = {}
        dane['T_zewnatrz'] = self.temp_out
        dane['W_zewnatrz'] = self.wilg_out
        dane['T_wewnatrz'] = self.temp_in
        dane['W_wewnatrz'] = self.wilg_in
        dane['W_gleby'] = self.wilg_gleby
        dane[constants.TS] = self.ts
        self.stan_temperatury = dane

    def zwroc_temperatury(self):
        return self.stan_temperatury

    def uruchom_serwer(self):
        address = ('localhost', PORT_LOKALNY)  # family is deduced to be 'AF_INET'
        listener = Listener(address, authkey='secret password')
        while True:
            conn = listener.accept()
            msg = conn.recv()
            if msg == 'close':
                conn.close()
            if msg == 'TEMP':
                self.odczytaj_temperature()
                conn.send(self.zwroc_temperatury())

    def odczytaj_konf(self):
        self.nr_pinu = int(THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_TEMP, 'PIN_PI_TEMPERATURA', self.logger))
        self.odstep_odczytu_temperatury = int(THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_TEMP, 'ODST_ODCZ_TEMP', self.logger))
        self.czas_odczytu_konfig = int(THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_TEMP, 'CZAS_ODCZYTU_KONFIG', self.logger))
        self.logger.info('Odczytalem konfiguracje temperatura.')

    '''def odczytaj_konfiguracje_cyklicznie(self):
        self.odczytaj_konf()
        now = datetime.datetime.now()
        run_at = now + datetime.timedelta(hours=self.czas_odczytu_konfig)
        delay = (run_at - now).total_seconds()
        # TODO aktywowac odczytywanie konfiguracji temperatury na nowo?
        # threading.Timer(delay, self.odczytaj_konf).start()'''

    def resetuj_czujniki_temperatury_cyklicznie(self):
        #czas_odlaczania_czujnikow = int(odczytaj_parametr_konfiguracji(constants.OBSZAR_TEMP, 'CZAS_ODLACZANIA_CZUJNIKOW')) * 60
        # TODO z jakichs powodow nie odczytuje poprawnie powyzszego parametru z konfiguracji
        czas_odlaczania_czujnikow = 38 * 60
        threading.Timer(czas_odlaczania_czujnikow, self.resetuj_czujniki_temperatury_cyklicznie, []).start()
        self.resetuj_czujniki_temperatury()

    def resetuj_czujniki_temperatury(self):
        # odlacza na 5 sekund czujniki temperatury, zasilanie
        nr_pinu = int(odczytaj_parametr_konfiguracji(constants.OBSZAR_TEMP, 'PIN_PI_ODLACZANIE_ZASILANIA_CZUJNIKOW'))
        przekaz = przekazniki_BCM.PrzekaznikiBCM(self.mcp)
        nazwa_przek = 'Reset czujn temp'
        przekaz.dodaj_przekaznik(nazwa_przek, nr_pinu)
        # TODO przerobic ten time.sleep na threading
        # TODO chyba wlacz_na_czas nie dziala
        # przekaz.wlacz_na_czas(0, 3)
        przekaz.ustaw_przekaznik_nazwa(nazwa_przek, True)
        time.sleep(2)
        przekaz.ustaw_przekaznik_nazwa(nazwa_przek, False)

    def zapisz_temp_do_bazy(self):
        try:
            db = MySQLdb.connect(host = "localhost", user = "root", passwd = constants.PWD_BAZY, db = "stacja_pogodowa")
            cur = db.cursor()
            cur.execute("""INSERT INTO stacja_pogodowa.temperatura(outside,wilgotnosc_out,inside,wilgotnosc_in,wilgotnosc_gleby) VALUES (%s, %s, %s, %s, %s)""", (self.temp_out, self.wilg_out, self.temp_in, self.wilg_in, self.wilg_gleby))
            db.commit()
            cur.close()
            db.close()
        except MySQLdb._mysql.OperationalError as serr:
            self.logger.warning('Blad zapisu temperatury do bazy danych: ' + str(serr))

    def odczytaj_temperature(self):
        # self.wilg, self.temp = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 4)
        # while 1:
        #time.sleep(3)
        self.temp_out = -99.9
        self.wilg_out = 0
        self.s.trigger()
        #oryginalnie bylo 0.2
        #TODO time.sleep do przemyslenia
        time.sleep(0.3)
        self.wilg_out = self.s.humidity()
        self.temp_out = self.s.temperature()
        if self.temp_out is None:
            self.wilg_out = 0
            self.temp_out = -99.9

    def pobieraj_temperature_cyklicznie(self):
        temp = deepcopy(self.temp_out)
        #temp = self.temp_out
        self.odczytaj_temperature()

        self.aktualizuj_stan_temperatury()
        #TODO tutaj trzeba przeniesc cykliczne resetowanie czujnika temperatury z mysocket do temperatury
        if int(round(temp)) != int(round(self.temp_out)):
            self.ts = int(time.time())
	    self.aktualizuj_stan_temperatury()
            # self.logger.info("Zmiana w temperaturze, informuje klientow za pomoca Firebase. Poprzednio bylo: "
            #                + str(temp) + " a teraz jest " + str(self.temp_out))

            #notyfikacja_firebase = firebasenotification.Firebasenotification()
            #notyfikacja_firebase.notify(constants.OBSZAR_TEMP, str(round(self.temp_out)))
            if self.firebase_callback is not None:
                #oo = THutils.skonstruuj_odpowiedzV2(constants.RODZAJ_KOMUNIKATU_STAN_TEMPERATURY,
                #                                    self.stan_temperatury, constants.STATUS_OK)
                self.logger.info('Odpalam firebase z temperatury: ' + str(self.temp_out))
                self.firebase_callback()
                #print 'fire z temperatury'

        self.zapisz_temp_do_bazy()
        threading.Timer(self.odstep_odczytu_temperatury, self.pobieraj_temperature_cyklicznie).start()



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