# from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.client
import spotipy.oauth2 as oauth
import constants
import os
import copy
# import json

NAZWA_KLIENTA_SPOTIFY = 'spotify-strych'  # taka sama podane w definicji klienta connect
QUERY_LIMIT = 50



class SpotifyKlasa:
    def __init__(self, logger):
        self.logger = logger
        #client_credentials_manager = spotipy.oauth2.SpotifyClientCredentials(client_id='eb15bbddb11d45eaacdc60b44a2cc46c',
        #                                                      client_secret='1c8e6e7d309e4a008a4a7714944b098e')
        # tok = client_credentials_manager.get_access_token()
        scope = 'app-remote-control user-modify-playback-state user-read-currently-playing user-read-playback-state'
        uname = 'grm7ho7unmwcfi4k8yak0jogc'
        client_id = 'eb15bbddb11d45eaacdc60b44a2cc46c'
        client_secret = '1c8e6e7d309e4a008a4a7714944b098e'
        redirect_url = 'https://localhost/callback/'
        cache_path = os.path.dirname(os.path.realpath(__file__)) + '/.cache-' + uname
        #sp_cred = oauth.SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        #self.token = sp_cred.get_access_token()
        #self.klient = spotipy.Spotify(auth=self.token)

        """sp_oauth = oauth.SpotifyOAuth(client_id, client_secret, redirect_url,
                                       scope=scope, cache_path=cache_path)
        token_info = sp_oauth.get_cached_token()
        if not token_info:
            auth_url = sp_oauth.get_authorize_url()
            r = requests.get(auth_url, auth=HTTPBasicAuth(uname, 'pass'))
            code = sp_oauth.parse_response_code(r.url)
            token_info = sp_oauth.get_access_token(code)
        if token_info:
            token = token_info['access_token']
            self.klient = spotipy.Spotify(auth=token)
        else:
            self.logger.warning('Nie udalo sie uzyskac tokenu spotify ...')"""

        #token = util.prompt_for_user_token(uname, client_id=client_id,
        #                                   client_secret=client_secret, scope=scope,
        #                                   redirect_uri=redirect_url)
        # self.klient = spotipy.Spotify(auth=token, client_credentials_manager=client_credentials_manager)
        #except EOFError:
        #    self.logger.warning('Nie udalo sie uzyskac tokenu spotify ...')
        sp_oauth = oauth.SpotifyOAuth(client_id, client_secret, redirect_url,
                                      scope=scope, cache_path=cache_path)
        try:
            token_info = sp_oauth.get_cached_token()
        except Exception as serr:
            self.logger.warning('Blad odczytu tokena z cacheu: ' + str(serr))
        if not token_info:
            self.logger.warning('Nie moge uzyskac tokenu Spotify z cachu.')
            return
        self.klient = spotipy.Spotify(auth=token_info['access_token'])
        if self.klient is None:
            self.logger.warning('Klient spotify None')


    def get_dev_id(self):
        dev_id = self.odczytaj_dev_id()
        if dev_id == '':
            self.logger.warning('Nie widac spotify connect w kontekscie uzytkownika spotify. Zrobilem restart: sudo systemctl restart raspotify')
            """my_out = subprocess.Popen(['sudo', 'systemctl', 'restart', 'raspotify'],
                                      stdout = subprocess.PIPE,
                                      stderr = subprocess.STDOUT)
            stdout, stderr = my_out.communicate()"""
            self.resetuj_raspotify()
            dev_id = self.odczytaj_dev_id()
            # self.logger.info('Uruchomilem sudo systemctl restart raspotify: ' + str(stdout) + ' ' + str(stderr))
        return dev_id

    def resetuj_raspotify(self):
        os.system('sudo systemctl restart raspotify')

    def odczytaj_dev_id(self):
        try:
            devices = self.klient.devices()
        except (Exception, ValueError):
            self.logger.warning('JSON decode error podczas odczytywania klientow: spotify')
            return ''
        for a in devices[constants.DEVICES]:
            if a[constants.NAME] == NAZWA_KLIENTA_SPOTIFY:
                return a[constants.ID]
                # self.logger.info('Odczytalem urzadzenie spotify-connect: ' + str(dev_id))
        return ''

    def zapytanie(self, funkcja, item_id, dodatek):
        try:
            if funkcja ==  constants.USER_PLAYLIST:
                return self.klient.user_playlist(dodatek, playlist_id=item_id)
            elif funkcja == constants.TRACK:
                return self.klient.track(item_id)
            elif funkcja == constants.PLAYLIST:
                return self.klient.user_playlist(dodatek, playlist_id=item_id)
            elif funkcja == constants.ALBUM_TRACKS:
                return self.klient.album_tracks(item_id)
            elif funkcja == constants.ALBUM:
                return self.klient.album(item_id)
            elif funkcja == constants.ARTIST:
                return self.klient.artist_top_tracks(item_id, country=constants.COUNTRY)
            elif funkcja == constants.ARTIST_ALBUMS:
                return self.klient.artist_albums(item_id, album_type=constants.ALBUM, country=constants.COUNTRY)
        except Exception as serr:
            self.logger.warning('Blad spotify search:' + str(serr))
            return ''

    def nastepny(self, next):
        odp = {}
        n = {}
        n[constants.NEXT] = next
        odp[constants.KOLEJNE] = self.klient.next(n)
        return odp

    def rozwin(self, rodzaj, id):
        odp = dict()
        odp[constants.ROZWINIECIE] = {}
        od = self.zapytanie(rodzaj, id, id)
        odp[constants.ROZWINIECIE][rodzaj] = od
        if rodzaj == constants.ARTIST:
            od = self.zapytanie(constants.ARTIST_ALBUMS, id, id)
            odp[constants.ROZWINIECIE][constants.ALBUMS] = od
        if rodzaj == constants.ALBUM:
            odp[constants.ROZWINIECIE][constants.ARTISTS] = od[constants.ARTISTS]
        if rodzaj == constants.PLAYLIST:
            artysci = []
            for a in od[constants.TRACKS][constants.ITEMS]:
                for artysta in a[constants.TRACK][constants.ARTISTS]:
                    byl = False
                    for x in artysci:
                        if x[constants.URI] == artysta[constants.URI]:
                            byl = True
                            break
                    if not byl:
                        artysci.append(copy.deepcopy(artysta))
                        # print 'dodalbym' + artysta[constants.NAME]
            #artysci = list(dict.fromkeys(artysci))
            odp[constants.ROZWINIECIE][constants.ARTISTS] = artysci
        return odp

    def szukaj_zdalnie(self, query, next=None, offset=0):
        # TODO czy ten offset zawsze nie jest 0
        odp = dict()
        if len(next) > 1:
            if len(query) > 1:
                #odp[next] = self.klient.search(query, limit=50, offset=int(offset), type=next)
                od = self.zapytanie(next, query, query)
                odp[constants.ROZWINIECIE] = {}
                odp[constants.ROZWINIECIE][next] = od
                return odp
            else:
                n = {}
                n[constants.NEXT] = next
                odp[constants.KOLEJNE] = self.klient.next(n)
                return odp
        else:
            try:
                odp[constants.ARTIST] = self.klient.search(query, limit=50, offset=int(offset), type=constants.ARTIST)
            except Exception as serr:
                self.logger.warning('Blad spotify search:' + str(serr))
            try:
                odp[constants.ALBUM] = self.klient.search(query, limit=50, offset=int(offset), type=constants.ALBUM)
            except Exception as serr:
                self.logger.warning('Blad spotify search:' + str(serr))
            try:
                odp[constants.TRACK] = self.klient.search(query, limit=50, offset=int(offset), type=constants.TRACK)
            except Exception as serr:
                self.logger.warning('Blad spotify search:' + str(serr))
            try:
                odp[constants.PLAYLIST] = self.klient.search(query, limit=50, offset=int(offset), type=constants.PLAYLIST)
            except Exception as serr:
                self.logger.warning('Blad spotify search:' + str(serr))
        odp[constants.QUERY] = query
        #odp['offset'] = int(dodatek)
        return odp
