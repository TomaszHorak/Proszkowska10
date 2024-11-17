import constants
from random import getrandbits

NAME = 'name'
URI = 'uri'
IMAGES = 'images'
URL = 'url'
ALBUM = 'album'
ARTIST = 'artist'
ARTISTS = 'artists'
TYPE = 'type'
FANART = 'fanart'
SERWISRADIOWY = 'serwisRadiowy'
STACJARADIOWA = 'stacjaRadiowa'
IS_PLAYING = 'isPlaying'

class Item:
    def __init__(self, name='', type=1, fanart='', link='', uri='', contexturi='',
                 title='', artist='', album='', isPlaying=False, serwisRadiowy='', stacjaRadiowa='', nr=0):
        self.name = name    #nazwa ulubionego, lub playlisty
        self.type = type
        self.fanart = fanart
        self.link= link
        self.uri = uri
        self.contexturi = contexturi
        self.title = title #tytul aktualnie granego, lub odczytane z Kodi nadawane przez radio
        self.artist = artist
        self.album = album
        self.isPlaying = isPlaying
        self.serwisRadiowy = serwisRadiowy
        self.stacjaRadiowa = stacjaRadiowa
        if nr == 0:
            self.nr = getrandbits(32)
        else:
            self.nr = nr

    def __iter__(self):
        for key in self.__dict__:
            yield key, getattr(self, key)

    def isRadio(self):
        if self.type == constants.GRA_RADIO:
            return True
        return False

    def isSpotify(self):
        if self.type == constants.GRA_SPOTIFY:
            return True
        return False

    def fromSpotifyPlaylist(self, playlist):
        self.name = playlist[NAME]
        self.type = constants.GRA_SPOTIFY
        if playlist[IMAGES]:
            self.fanart = playlist[IMAGES][0][URL]
        #else:
        #    self.fanart = ''
        #self.link = ''
        if playlist[URI]:
            self.uri = playlist[URI]
            self.contexturi = self.uri  # zrownujemy contexturi z uri bo uri zawsze bedzie playlista
        #else:
        #    self.uri = ''

    def fromSpotifyTrack(self, track):
        #tutaj poprawic nazwy pol
        self.name = track[NAME]
        self.type = constants.GRA_SPOTIFY
        if track[ALBUM][IMAGES][0][URL]:
            self.fanart = track[ALBUM][IMAGES][0][URL]
        #else:
        #    self.fanart = ''
        #self.link = ''
        if track[URI]:
            self.uri = track[URI]
        #else:
        #    self.uri = ''
        if track[ALBUM]:
            self.album = track[ALBUM][NAME]
        if track[ARTISTS]:
            self.artist = track[ARTISTS][0][NAME]

    def fromFileStructure(self, filestruct):
        if filestruct[ALBUM]:
            self.album = filestruct[ALBUM]
        if filestruct[ARTIST]:
            self.artist = filestruct[ARTIST]

        if filestruct[NAME]:
            self.name = filestruct[NAME]
        #else:
        #    self.name = ''
        if filestruct[SERWISRADIOWY]:
            self.serwisRadiowy = filestruct[SERWISRADIOWY]
        if filestruct[STACJARADIOWA]:
            self.stacjaRadiowa = filestruct[STACJARADIOWA]

        if filestruct[TYPE]:
            self.type = filestruct[TYPE]
        #else:
        #    self.type = constants.GRA_RADIO
        if filestruct[FANART]:
            self.fanart = filestruct[FANART]
        #else:
        #    self.fanart = ''