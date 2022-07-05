import odtwarzacz
import spotify_klasa
from MojLogger import MojLogger

class SpotifyOdtwarzacz(odtwarzacz.Odtwarzacz):
    def __init__(self, obszar, logger):
        odtwarzacz.Odtwarzacz.__init__(self)
        self.logger = logger    #type: MojLogger
        self.obszar = obszar
        self.odswiez_klienta_spotify()

    def odswiez_klienta_spotify(self):
        self.spot = spotify_klasa.SpotifyKlasa(self.logger, 'SPOT_ODTWZRZACZ')

    def stop(self):
        odtwarzacz.Odtwarzacz.stop(self)
        try:
            #spot = spotify_klasa.SpotifyKlasa(self.logger)
            self.spot.klient.pause_playback(device_id=self.spot.get_dev_id())
        except Exception as serr:
            self.logger.warning(self.obszar, 'Blad spotify stop: ' + str(serr))
            self.odswiez_klienta_spotify()
        return

    def aktualizuj_stan(self):
        odtwarzacz.Odtwarzacz.aktualizuj_stan(self)
        try:
            pl = self.spot.klient.current_playback()
        except Exception as serr:
            blad = str(serr)
            if 'The access token expired' in blad:
                self.odswiez_klienta_spotify()
            else:
                self.logger.warning(self.obszar, 'Blad spotify aktualizuj_stan: ' + blad)
                self.odswiez_klienta_spotify()
            try:
                pl = self.spot.klient.current_playback()
            except Exception as serr:
                self.logger.warning(self.obszar, 'Ponowny blad spotify aktualizuj_stan: ' + str(serr))
                #TODO ostatnio wyremowane niech  nie resetuje tak latwo
                #self.spot.resetuj_raspotify()
                return
        try:
            if pl is not None:
                self.aktualnie_gra = pl['is_playing']
                self.tytul = pl['item']['name']
                self.totaltime = int(pl['item']['duration_ms'] / 1000)
                self.currenttime = int(pl['progress_ms'] / 1000)
                self.percentage = int(self.currenttime * 100 / self.totaltime)
        except Exception as serr:
            self.logger.warning(self.obszar, 'Blad spotify aktualizuj_stan type error: ' + str(serr))
        return

    def odtwarzaj_z_linku(self, link):
        odtwarzacz.Odtwarzacz.odtwarzaj_z_linku(self, link)
        try:
            dev_id = self.spot.get_dev_id()
            powrot = self.spot.klient.start_playback(device_id=dev_id, uris=[link])
            self.spot.klient.volume(100, device_id=dev_id)
        except Exception as serr:
            self.logger.warning(self.obszar, 'Blad spotify odtwarzaj_z_linku: ' + str(serr))
            self.odswiez_klienta_spotify()
        return

    def idz_do(self, czas):
        odtwarzacz.Odtwarzacz.idz_do(self, czas)
        try:
            #spot = spotify_klasa.SpotifyKlasa(self.logger)
            dev_id = self.spot.get_dev_id()
            ms = int(czas * self.totaltime) * 10
            result = self.spot.klient.seek_track(ms, device_id=dev_id)
        except Exception as serr:
            self.logger.warning(self.obszar, 'Blad spotify odtwarzaj_z_linku: ' + str(serr))
            self.odswiez_klienta_spotify()
        return

    def play_pause(self, start=False):
        odtwarzacz.Odtwarzacz.play_pause(self)
        try:
            #spot = spotify_klasa.SpotifyKlasa(self.logger)
            dev_id = self.spot.get_dev_id()
            if start:
                self.spot.klient.start_playback(device_id=dev_id)
            else:
                self.spot.klient.pause_playback(device_id=dev_id)
        except Exception as serr:
            self.logger.warning(self.obszar, 'Blad spotify play_pause: ' + str(serr))
            self.odswiez_klienta_spotify()
        return
