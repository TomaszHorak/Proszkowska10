#!/usr/bin/python
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
except (ImportError) as serr:
    pass
PORT_LOKALNY = 6050

FIREBASE_OBSZAR_TEMPERATURA = 'temperatura'
FIREBASE_KOMUNIKAT_TEMPERATURA = 'zmiana_temperatury'



class temperatura:
    def __init__(self):
        self.temp_out = -99.9
        self.wilg_out = 0
        self.temp_in = -99.9
        self.wilg_in = 0
        self.wilg_gleby = 0
        self.pi = pigpio.pi()
        self.logger = logging.getLogger('proszkowska')
        self.nr_pinu = 4
 #       GPIO.setmode(GPIO.BCM)
        self.odstep_odczytu_temperatury = 180
        # odstep w godzinach co ile ma byc odswiezana konfiguracja z bazy
        self.czas_odczytu_konfig = 24
        self.MOJE_IP = THutils.moje_ip('eth0')
        self.notyfikacja_firebase = firebasenotification.Firebasenotification()
        self.odczytaj_konf()
        #self.nr_pinu = int(odczytaj_konfiguracje.odczytaj_konfiguracje_z_bazy('TEMP', 'PIN_PI_TEMPERATURA'))
        #self.odstep_odczytu_temperatury = int(odczytaj_konfiguracje.odczytaj_konfiguracje_z_bazy('OGOLNE', 'ODST_ODCZ_TEMP'))
        self.s = sensor(self.pi, self.nr_pinu, power=8)
        #self.odczytaj_temperature()
        self.pobieraj_temperature_cyklicznie()

    def zwroc_temperatury(self):
        dane = {}
        dane['T_zewnatrz'] = self.temp_out
        dane['W_zewnatrz'] = self.wilg_out
        dane['T_wewnatrz'] = self.temp_in
        dane['W_wewnatrz'] = self.wilg_in
        dane['W_gleby'] = self.wilg_gleby
        return dane

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
                """dane = {}
                dane['T_zewnatrz'] = self.temp_out
                dane['W_zewnatrz'] = self.wilg_out
                dane['T_wewnatrz'] = self.temp_in
                dane['W_wewnatrz'] = self.wilg_in
                dane['W_gleby'] = self.wilg_gleby
                odp = dane"""
                conn.send(self.zwroc_temperatury())

    def odczytaj_konf(self):
        self.nr_pinu = int(THutils.odczytaj_parametr_konfiguracji('TEMP', 'PIN_PI_TEMPERATURA', self.logger))
        self.odstep_odczytu_temperatury = int(THutils.odczytaj_parametr_konfiguracji('TEMP', 'ODST_ODCZ_TEMP', self.logger))
        self.czas_odczytu_konfig = int(THutils.odczytaj_parametr_konfiguracji('TEMP', 'CZAS_ODCZYTU_KONFIG', self.logger))
        self.logger.info('Odczytalem konfiguracje temperatura.')
        now = datetime.datetime.now()
        run_at = now + datetime.timedelta(hours=self.czas_odczytu_konfig)
        delay = (run_at - now).total_seconds()
        # TODO aktywowac odczytywanie konfiguracji temperatury na nowo?
        # threading.Timer(delay, self.odczytaj_konf).start()


    def zapisz_temp_do_bazy(self):
        db = MySQLdb.connect(host = "localhost", user = "root", passwd = "west1west1", db = "stacja_pogodowa")
        cur = db.cursor()
        cur.execute("""INSERT INTO stacja_pogodowa.temperatura(outside,wilgotnosc_out,inside,wilgotnosc_in,wilgotnosc_gleby) VALUES (%s, %s, %s, %s, %s)""", (self.temp_out, self.wilg_out, self.temp_in, self.wilg_in, self.wilg_gleby))
        db.commit()
        cur.close()
        db.close()

    def odczytaj_temperature(self):
        # self.wilg, self.temp = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 4)
        # while 1:
        #time.sleep(3)
        self.temp_out = -99.9
        self.wilg_out = 0
        self.s.trigger()
        #oryginalnie bylo 0.2
        time.sleep(0.3)
        self.wilg_out = self.s.humidity()
        self.temp_out = self.s.temperature()
        if self.temp_out is None:
            self.wilg_out = 0
            self.temp_out = -99.9

    def pobieraj_temperature_cyklicznie(self):
        temp = self.temp_out
        self.odczytaj_temperature()
        #TODO tutaj trzeba przeniesc cykliczne resetowanie czujnika temperatury z mysocket do temperatury
        if int(round(temp)) != int(round(self.temp_out)):
            # self.logger.info("Zmiana w temperaturze, informuje klientow za pomoca Firebase. Poprzednio bylo: "
            #                + str(temp) + " a teraz jest " + str(self.temp_out))
            thread.start_new_thread(self.notyfikacja_firebase.notify, (FIREBASE_OBSZAR_TEMPERATURA, FIREBASE_KOMUNIKAT_TEMPERATURA))
        self.zapisz_temp_do_bazy()
        threading.Timer(self.odstep_odczytu_temperatury, self.pobieraj_temperature_cyklicznie).start()



class sensor:

   def __init__(self, pi, gpio, LED=None, power=None):
      self.pi = pi
      self.gpio = gpio
      self.LED = LED
      self.power = power

      if power is not None:
         pi.write(power, 1) # Switch sensor on.
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

      pi.set_pull_up_down(gpio, pigpio.PUD_OFF)

      pi.set_watchdog(gpio, 0) # Kill any watchdogs.

      self.cb = pi.callback(gpio, pigpio.EITHER_EDGE, self._cb)

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

               self.pi.set_watchdog(self.gpio, 0)

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
         self.pi.set_watchdog(self.gpio, 0)
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

         self.pi.write(self.gpio, pigpio.LOW)
         time.sleep(0.017) # 17 ms
         self.pi.set_mode(self.gpio, pigpio.INPUT)
         self.pi.set_watchdog(self.gpio, 200)

   def cancel(self):
      """Cancel the DHT22 sensor."""

      self.pi.set_watchdog(self.gpio, 0)

      if self.cb != None:
         self.cb.cancel()
         self.cb = None

#----------------------------------------------
#glowny program
#----------------------------------------------
"""temp = temperatura()
temp.pobieraj_temperature_cyklicznie()
temp.uruchom_serwer()"""