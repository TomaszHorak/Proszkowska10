import requests
import json
import logging
import constants
import os

MUSIXMATCH_API_KEY = 'MUSIXMATCH_API_KEY'
API_URL = 'https://api.musixmatch.com/ws/1.1/'
method_track_search = 'track.search'
method_track_lyrics_get = 'track.lyrics.get'
method_matcher_lyrics_get = 'matcher.lyrics.get'

class Liriki:
    def __init__(self):
        self.logger = logging.getLogger(constants.NAZWA_LOGGERA)
        self.api_key = os.getenv(MUSIXMATCH_API_KEY)
        self.tekstPiosenki = ''
        pass

    @staticmethod
    def __odczytajodpowiedz(message):
        odp = message['message']
        if odp['header']['status_code'] == 200:
            zwrotka = True
            body = odp['body']
        else:
            zwrotka = False
            body = None
        return zwrotka, body

    def odczytaj_liryki(self, artysta, piosenka):
        self.logger.info('Odczytuje liryki dla artysta: ' + artysta + ', oraz piosenki: ' + piosenka)
        dane = {'format': 'json',
                'q_track': piosenka,
                'q_artist': artysta,
                'apikey': self.api_key}

        r = requests.get(API_URL + method_matcher_lyrics_get, params=dane)
        odp = json.loads(r.text)

        zwrotka, message = self.__odczytajodpowiedz(odp)

        if zwrotka:
            '''track_list = message['track_list']
            track_id = 0
            for a in track_list:
                track = a['track']
                if track['has_lyrics'] == 1:
                    track_id = a['track']['track_id']
                    break
    
            dane = {'format': 'json',
                    'track_id': track_id,
                    'apikey': API_KEY}
    
            r = requests.get(api_ur + method_track_lyrics_get, params=dane)
            odp = json.loads(r.text)
            zwrotka, message = odczytajodpowiedz(odp)
    
            if zwrotka:
                print(message['lyrics']['lyrics_body'])
            else:
                print('Nie ma lyrikow....')'''
            #print (message['lyrics']['lyrics_body'])
            self.tekstPiosenki =  message['lyrics']['lyrics_body']
        else:
            self.logger.warning('Brak liryk dla artysta: ' + artysta + ', oraz piosenki: ' + piosenka)
            self.tekstPiosenki = ''