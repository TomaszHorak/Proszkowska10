import constants
import json
from THutils import odczytaj_parametr_konfiguracji
from MojLogger import MojLogger
from Obszar import Obszar

class Szybkie_Akcje(Obszar):
    def __init__(self, logger):
        Obszar.__init__(self, constants.OBSZAR_SZAK,
                        logger, #type:  MojLogger
                        rodzaj_komunikatu=constants.RODZAJ_KOMUNIKATU_STAN_SZYBKIE_AKCJE,
                       # callback_przekaznika_wyjscia=self.aktualizuj_biezacy_stan,
                        #callback_wejscia=self.wejscie_callback,
                        #dzialanie_petli=self.dzialanie_petli)
                        )

        self._odczytaj_akcje()
        self.aktualizuj_biezacy_stan()
        self.logger.info(self.obszar, 'Zainicjowalem klase szybkie akcje.')

    def _odczytaj_akcje(self):
        sz = odczytaj_parametr_konfiguracji(self.obszar, 'akcje', self.logger)
        #TODO czy odczytaj_parametr_konfiguracji musi miec dwa obszary zawsze?
        self.akcje = []
        try:
            szak = json.loads(sz)
            for akcja in szak:
                self.akcje.append(akcja)
            self.resetuj_ts()
        except Exception as serr:
            self.logger.error(self.obszar, 'Nie potrafie odczytac szybkich akcji: ' + str(serr))

    def procesuj_polecenie(self,**params):
        #TODO odczytac szybkie akcje z configu, dorobic odswiezanie po kazdym poleceniu odczytu, nowa komenda
        #TODO po starcie androida kzdorazowo wyslac takie zapytanie jak wyzej
        rodzaj = Obszar.procesuj_polecenie(self, **params)
        if rodzaj == constants.KOMENDA:
            if params[constants.KOMENDA] == constants.KOMENDA_ODSWIEZ_SZYBKIE_AKCJE:
                self._odczytaj_akcje()
        return Obszar.odpowiedz(self) #skonstruuj_odpowiedzV2OK(constants.RODZAJ_KOMUNIKATU_STAN_OSWIETLENIA, self.stan_oswietlenia)

    def get_biezacy_stan(self):
        self.aktualizuj_biezacy_stan()
        return self._biezacy_stan

    def aktualizuj_biezacy_stan(self, odbiornik_pomieszczenie=None):
        self._biezacy_stan = {constants.OBSZAR_SZAK: self.akcje,
                              constants.TS: self.get_ts()}