import Adafruit_MCP230xx
import pigpio
import time

class MCP_wejscia:
    def __init__(self, address, num_gpios, pin_przerwania_mcp):
        self._wejscia = []
        #ustawienie pinu Raspberry na przerwania z MCP
        gpio_pigpio = pigpio.pi()
        gpio_pigpio.set_mode(pin_przerwania_mcp, pigpio.INPUT)
        gpio_pigpio.set_pull_up_down(pin_przerwania_mcp, pigpio.PUD_UP)
        gpio_pigpio.write(pin_przerwania_mcp, 1)
        #gpio_pigpio.set_glitch_filter(pin_przerwania_mcp, 1500)
        gpio_pigpio.callback(pin_przerwania_mcp, pigpio.FALLING_EDGE, self.odczytaj_stany_wejsc_po_przerwaniu)

        self.mcp_wejscie1 = Adafruit_MCP230xx.Adafruit_MCP230XX(address=address, num_gpios=num_gpios)
        for a in range(0,num_gpios):
            self.mcp_wejscie1.config(a, Adafruit_MCP230xx.Adafruit_MCP230XX.INPUT)
            time.sleep(0.05)
            self.mcp_wejscie1.pullup(a, 1)
        self.mcp_wejscie1.read_caly_rejestr()
        return

    def odczytaj_stany_wejsc_po_przerwaniu(self, pin, level, tick):
        odczyt = self.mcp_wejscie1.read_caly_rejestr()
        for a in self._wejscia:
            a.set_stan((odczyt >> a.get_pin()) & 1)
            #print "Odczytano stan wejscia: " + a.get_nazwa() + ". Stan: " + str(a.get_stan())

    def dodaj_wejscie(self, nazwa, pin, callback=None):
        self._wejscia.append(MCPwejscie(nazwa, pin, callback=callback))

    def wejscie_po_nazwie(self, nazwa):
        for j in self._wejscia:
            if j.get_nazwa() == nazwa:
                return j
        return None

class MCPwejscie:
    def __init__(self, nazwa, pin, callback = None):
        self._nazwa = nazwa
        self._stan = 1
        self._pin = pin
        self._callback = callback # callback musi miec parametr z nazwa, pin  i aktualnym stanem
        return

    def set_stan(self, stan):
        if self._stan == stan:
            return
        self._stan = stan
        if self._callback is not None:
            self._callback(self._pin, self._nazwa, self._stan)

    def get_stan(self):
        return self._stan

    def get_pin(self):
        return self._pin

    def get_nazwa(self):
        return self._nazwa

