from Obszar import Obszar
import constants
from THutils import zapytaj_o_status_zdalnie
from THutils import przekaz_polecenie_V2_JSONRPC
from MojLogger import MojLogger


class Sauna(Obszar):
    def __init__(self, logger, petla=None, firebase_callback=None):
        Obszar.__init__(self, constants.OBSZAR_SAUNA,
                        logger, #type: MojLogger
                        petla=petla,
                        firebase_callback=firebase_callback,
                        rodzaj_komunikatu=constants.RODZAJ_KOMUNIKATU_STAN_SAUNY,
                        callback_przekaznika_wyjscia=self.resetuj_ts,
                        callback_wejscia=self.wejscie_callback,
                        dzialanie_petli=self.dzialanie_petli)

        self.wlaczona = False
        self.grzeje = False
        self.temp_zadana = 0
        self.temp_aktualna = 0
        self.swiatlo_wew = False
        self.swiatlo_zew = False
        self.swiatlo_sciezka = False
        self.ts_konca = 0   #liczba milisekund do konca saunowania
        self.logger.info(self.obszar, 'Zainicjowalem klase sauna.')

    def procesuj_polecenie(self, **params):
        rodzaj = Obszar.procesuj_polecenie(self, **params)

        if rodzaj == constants.KOMENDA: #jest polecenie do przekazania do sauny
            odp = przekaz_polecenie_V2_JSONRPC(constants.get_HOST_I_PORT_SAUNA(), constants.OBSZAR_SAUNA, self.logger, params)
            #if params[constants.KOMENDA] != constants.RODZAJ_KOMUNIKATU_STAN_SAUNY:
            #    self.logger.info('Przekazalem do sauny: ' + str(params))
            try:
                self.procesuj_status_z_sauny(odp[constants.RESULT])
            except KeyError as serr:
                self.logger.error(self.obszar, 'Brak poprawnej zwrotki z sauny: ' + str(serr))
        elif rodzaj == constants.RODZAJ_KOMUNIKATU:   #mamy zwrotke z sauny na zasadzie push
            if params[constants.RODZAJ_KOMUNIKATU] == constants.RODZAJ_KOMUNIKATU_STAN_SAUNY:
                try:
                    self.procesuj_status_z_sauny(params[constants.RESULT])
                except KeyError as serr:
                    self.logger.error(self.obszar, 'Brak poprawnego statusu z sauny: ' + str(serr))
        return Obszar.odpowiedz(self)

    def procesuj_status_z_sauny(self, status_sauny):
        resetowac_ts = False
        try:
            if self.wlaczona != status_sauny[constants.POLE_WLACZONA]:
                self.wlaczona = status_sauny[constants.POLE_WLACZONA]
                resetowac_ts = True
                self.logger.info(self.obszar, 'Wlaczenie sauny: ' + str(self.wlaczona))
            if self.grzeje != status_sauny[constants.POLE_GRZEJE]:
                self.grzeje = status_sauny[constants.POLE_GRZEJE]
                resetowac_ts = True
                self.logger.info(self.obszar, 'Sauna grzeje: ' + str(self.grzeje))
            if self.temp_zadana != status_sauny[constants.POLE_TEMP_ZADANA]:
                self.temp_zadana = status_sauny[constants.POLE_TEMP_ZADANA]
                resetowac_ts = True
                self.logger.info(self.obszar, 'Sauna temp zadana: ' + str(self.temp_zadana))
            if self.temp_aktualna != status_sauny[constants.POLE_TEMP_AKTUALNA]:
                self.temp_aktualna = status_sauny[constants.POLE_TEMP_AKTUALNA]
                resetowac_ts = True
            if self.swiatlo_wew != status_sauny[constants.POLE_SWIATLO_WEW]:
                self.swiatlo_wew = status_sauny[constants.POLE_SWIATLO_WEW]
                resetowac_ts = True
                self.logger.info(self.obszar, 'Sauna zmiana stanu swiatla ' + constants.POLE_SWIATLO_WEW + str(self.swiatlo_wew))
            if self.swiatlo_zew != status_sauny[constants.POLE_SWIATLO_ZEW]:
                self.swiatlo_zew = status_sauny[constants.POLE_SWIATLO_ZEW]
                resetowac_ts = True
                self.logger.info(self.obszar, 'Sauna zmiana stanu swiatla ' + constants.POLE_SWIATLO_ZEW + str(self.swiatlo_zew))
            if self.swiatlo_sciezka != status_sauny[constants.POLE_SWIATLO_SCIEZKA]:
                self.swiatlo_sciezka = status_sauny[constants.POLE_SWIATLO_SCIEZKA]
                self.logger.info(self.obszar, 'Sauna zmiana stanu swiatla ' + constants.POLE_SWIATLO_SCIEZKA + str(self.swiatlo_sciezka))
                resetowac_ts = True
            if self.ts_konca != status_sauny[constants.POLE_TS_KONCA]:
                self.ts_konca = status_sauny[constants.POLE_TS_KONCA]
                resetowac_ts = True
        except Exception as serr:
            self.logger.error(self.obszar, 'Blad procesowania odpowiedzi z sauny: ' + str(serr))
        if resetowac_ts:
            self.resetuj_ts()
            self.odpal_firebase()
            self.aktualizuj_biezacy_stan()

    def dzialanie_petli(self, nazwa, stan, pozycjapetli):
        if nazwa == constants.PETLA_ODCZYTAJ_STATUS_SAUNY:
            if stan:
                status_sauny = zapytaj_o_status_zdalnie(constants.get_HOST_I_PORT_SAUNA(), constants.OBSZAR_SAUNA,
                                                        constants.RODZAJ_KOMUNIKATU_STAN_SAUNY, self.logger)
                self.procesuj_status_z_sauny(status_sauny)

    def get_biezacy_stan(self):
        self.aktualizuj_biezacy_stan()
        return self._biezacy_stan

    def aktualizuj_biezacy_stan(self, odbiornik_pomieszczenie=None):
        self._biezacy_stan = {constants.TS: self.get_ts(),
                              constants.POLE_WLACZONA: self.wlaczona,
                              constants.POLE_GRZEJE: self.grzeje,
                              constants.POLE_TEMP_AKTUALNA: self.temp_aktualna,
                              constants.POLE_TEMP_ZADANA: self.temp_zadana,
                              constants.POLE_SWIATLO_WEW: self.swiatlo_wew,
                              constants.POLE_SWIATLO_ZEW: self.swiatlo_zew,
                              constants.POLE_TS_KONCA: self.ts_konca,
                              constants.POLE_SWIATLO_SCIEZKA: self.swiatlo_sciezka, }
