import odtwarzacz
import spotify_klasa
import spotipy
import requests
import json
# NAZWA_KLIENTA_SPOTIFY = 'Kodi Strych'  # taka sama podane w definicji klienta connect


class SpotifyOdtwarzacz(odtwarzacz.Odtwarzacz):
    def __init__(self, logger):
        odtwarzacz.Odtwarzacz.__init__(self)
        self.logger = logger
        self.odswiez_klienta_spotify()

    def odswiez_klienta_spotify(self):
        self.spot = spotify_klasa.SpotifyKlasa(self.logger)

    def stop(self):
        odtwarzacz.Odtwarzacz.stop(self)
        try:
            #spot = spotify_klasa.SpotifyKlasa(self.logger)
            self.spot.klient.pause_playback(device_id=self.spot.get_dev_id())
        except (spotipy.SpotifyException, AttributeError, requests.exceptions.ConnectionError) as serr:
            self.logger.warning('Blad spotify stop: ' + str(serr))
            self.odswiez_klienta_spotify()
        return

    def aktualizuj_stan(self):
        odtwarzacz.Odtwarzacz.aktualizuj_stan(self)
        try:
            pl = self.spot.klient.current_playback()
        except (spotipy.SpotifyException, TypeError, requests.exceptions.ConnectionError,
                requests.exceptions.ConnectTimeout, AttributeError, ValueError, Exception) as serr:
            blad = str(serr)
            if 'The access token expired' in blad:
                self.odswiez_klienta_spotify()
            else:
                self.logger.warning('Blad spotify aktualizuj_stan: ' + blad)
                self.odswiez_klienta_spotify()
            try:
                pl = self.spot.klient.current_playback()
            except (spotipy.SpotifyException, TypeError, requests.exceptions.ConnectionError,
                    requests.exceptions.ConnectTimeout, AttributeError, ValueError, Exception) as serr:
                self.logger.warning('Ponowny blad spotify aktualizuj_stan: ' + str(serr))
                self.spot.resetuj_raspotify()
                return
        try:
            if pl is not None:
                self.aktualnie_gra = pl['is_playing']
                self.tytul = pl['item']['name']
                self.totaltime = int(pl['item']['duration_ms'] / 1000)
                self.currenttime = int(pl['progress_ms'] / 1000)
                self.percentage = int(self.currenttime * 100 / self.totaltime)
        except (TypeError, AttributeError, ValueError, Exception) as serr:
            self.logger.warning('Blad spotify aktualizuj_stan type error: ' + str(serr))
        return

    def odtwarzaj_z_linku(self, link):
        odtwarzacz.Odtwarzacz.odtwarzaj_z_linku(self, link)
        try:
            dev_id = self.spot.get_dev_id()
            powrot = self.spot.klient.start_playback(device_id=dev_id, uris=[link])
            self.spot.klient.volume(100, device_id=dev_id)
        except (spotipy.SpotifyException, AttributeError, requests.exceptions.ConnectionError) as serr:
            self.logger.warning('Blad spotify odtwarzaj_z_linku: ' + str(serr))
            self.odswiez_klienta_spotify()
        return

    def idz_do(self, czas):
        odtwarzacz.Odtwarzacz.idz_do(self, czas)
        try:
            #spot = spotify_klasa.SpotifyKlasa(self.logger)
            dev_id = self.spot.get_dev_id()
            ms = int(czas * self.totaltime) * 10
            result = self.spot.klient.seek_track(ms, device_id=dev_id)
        except (spotipy.SpotifyException, AttributeError, requests.exceptions.ConnectionError) as serr:
            self.logger.warning('Blad spotify odtwarzaj_z_linku: ' + str(serr))
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
        except (spotipy.SpotifyException, AttributeError, requests.exceptions.ConnectionError) as serr:
            self.logger.warning('Blad spotify play_pause: ' + str(serr))
            self.odswiez_klienta_spotify()
        return
