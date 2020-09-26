import pafy
import urlparse
import os
import json
from random import randint
import logging
import datetime
import sys
from random import getrandbits
import spotify_klasa
import constants
import time
from copy import deepcopy

TYP_RADIO = 1
TYP_MP3 = 2
TYP_YOUTUBE = 3
TYP_SPOTIFY = 4

SUFFIX_ULUBIONYCH_PLIKI = '-files'
PO_KOLEI = 1
LOSOWO = 2
LINK_YOUTUBE = 'YOUTUBEVIDEO'
LINK_YOUTUBEPLAYLISTA = 'YOUTUBEPLAYLISTA'
LINK_INNE = 'INNE'
LINK_SPOTIFY = 'SPOTIFY'

DLUGOSC_HISTORII = 100
NAZWA_PLIKU_HISTORIA = 'historia'
NAZWA_PLIKU_AKTUALNA_PLAYLISTA = 'aktualna_playlista'


# NAZWA_PLIKU_Z_AKTUALNA_PLAYLISTA = constants.KATALOG_GLOWNY + '/' + NAZWA_PLIKU_AKTUALNA_PLAYLISTA
# NAZWA_PLIKU_Z_HISTORIA = constants.KATALOG_GLOWNY + '/' + NAZWA_PLIKU_HISTORIA


class PozycjaPlaylisty:
    def __init__(self, artist='', album='', title='', link='', link_youtube='',
                 typ=TYP_RADIO, fanart='', czas='', serwis_radiowy='', stacja_radiowa='', uri_spotify=''):
        # TODO przerobic nazwy zmiennych na _ i gettery settery, przejrzec caly kod
        self.artist = artist
        self.album = album
        self.title = title
        self.link = link
        self.typ = typ
        self.link_youtube = link_youtube
        # TODO spraedzic czy w ogole ta zmienna jets potrzebna bo wystarczy sprawdzac jaki jest typ
        self.uri_spotify = uri_spotify
        self.fanart = fanart
        self.czas = czas
        self.serwis_radiowy = serwis_radiowy
        self.stacja_radiowa = stacja_radiowa
        return

    def pozycja_do_listy(self, pelna=True):
        pozycja = {'title': self.title,
                   'typ': self.typ,
                   'fanart': self.fanart,
                   }
        if self.typ == TYP_YOUTUBE:
            pozycja['link_youtube'] = self.link_youtube
            pozycja['artist'] = self.artist
            pozycja['album'] = self.album
            pozycja[constants.CZAS] = self.czas
        elif self.typ == TYP_SPOTIFY:
            pozycja['uri_spotify'] = self.uri_spotify
            pozycja['artist'] = self.artist
            pozycja['album'] = self.album
            pozycja[constants.CZAS] = self.czas
        elif self.typ == TYP_RADIO:
            pozycja['serwis_radiowy'] = self.serwis_radiowy
            pozycja['stacja_radiowa'] = self.stacja_radiowa
        if pelna:
            pozycja['link'] = self.link
        return pozycja

    def porownaj_pozycje(self, pozycja):
        # TODO dorobic porownywanie pozycji, jakie pola ma wziasc pod uwage
        # zwraca True jesli takie same z biezaca
        if pozycja.link == self.link:
            return True
        return False


class Playlista(object):
    def __init__(self, nazwa='', pozycje=[], jak_odtwarza=PO_KOLEI, przy_starcie=False, plik=''):
        self.logger = logging.getLogger(constants.NAZWA_LOGGERA)
        self.nazwa = nazwa
        self.pozycje = pozycje
        self.jak_odtwarza = jak_odtwarza
        self.nr_pozycji_na_playliscie = 0
        # katbierzacy = os.path.dirname(os.path.realpath(__file__))
        #self.katalog_ulubionych = katbierzacy + PODKATALOG_ULUBIONYCH
        self.katalog_ulubionych = constants.KATALOG_ULUBIONYCH
        #self.nazwa_pliku_z_aktualna_playlista = katbierzacy + '/' + NAZWA_PLIKU_AKTUALNA_PLAYLISTA
        self.nazwa_pliku_z_aktualna_playlista = constants.KATALOG_GLOWNY + '/' + NAZWA_PLIKU_AKTUALNA_PLAYLISTA
        #self.nazwa_pliku_z_historia = katbierzacy + '/' + NAZWA_PLIKU_HISTORIA
        self.nazwa_pliku_z_historia = constants.KATALOG_GLOWNY + '/' + NAZWA_PLIKU_HISTORIA
        self.ts = int(time.time())
        self.ts_historii = int(time.time())
        if przy_starcie:
            self.inicjalizuj_playliste_z_pliku(self.nazwa_pliku_z_aktualna_playlista)
        else:
            self.inicjalizuj_playliste_z_pliku(plik)
        return

    def get_nazwa(self):
        return self.nazwa

    def odczytaj_historie(self):
        try:
            poz = json.load(open(self.nazwa_pliku_z_historia, 'r'))
        except Exception as serr:
            self.logger.warning('Blad odczytu pliku z historia, blad JSON: ' + str(serr))
            return None
        return poz

    def zapisz_w_historii(self, pozycja):
        if not pozycja:
            return
        stara = self.odczytaj_historie()
        if not stara:
            stara = []
        try:
            # TODO dorobic kontrole czy juz takiej pozycji kiedys nie bylo, usuwac najstarszy?
            # for a in stara:
            #    poz = PozycjaPlaylisty()
            #    poz.inicjalizuj_z_listy(a)
            #    if
            plik = open(self.nazwa_pliku_z_historia, 'w+')
            # pozycja = self.pozycje[nr_pozycji].pozycja_do_listy()
            linia = {constants.CZAS: str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                     constants.HASH: str(getrandbits(64)),
                     constants.POZYCJA: pozycja.pozycja_do_listy()}
            stara.append(linia)

            while len(stara) > DLUGOSC_HISTORII:
                del stara[0]

            plik.write(json.dumps(stara))
            plik.close()
            # self.logger.info('Zapisalem historie w pliku.')
        except Exception as serr:
            self.logger.warning(
                'Nie moglem zapisac historii w pliku. Blad: ' + str(serr))
        self.ts_historii = int(time.time())
        return

    def dodaj_z_linku(self, link, fanartlink, zmien_nazwe=False):
        rodzaj_linku = self.__sprawdz_rodzaj_linku(link)
        nazwa = ''
        if rodzaj_linku == LINK_YOUTUBE:
            nazwa = self.dodaj_z_linku_youtube(link)
        elif rodzaj_linku == LINK_YOUTUBEPLAYLISTA:
            nazwa = self.dodaj_playliste_youtube(link)
        elif rodzaj_linku == LINK_SPOTIFY:
            nazwa = self.dodaj_z_linku_spotify(link)
        elif rodzaj_linku == LINK_INNE:
            nazwa = self.dodaj_pozycje_z_polami(artist='', album='', title=str(os.path.basename(link)),
                                                link=link, typ=TYP_RADIO, fanart=fanartlink, czas='')
        if zmien_nazwe:
            self.nazwa = nazwa
        self.zapisz_playliste()

    def dodaj_z_linku_spotify(self, link, zmien_nazwe=False):
        spot = spotify_klasa.SpotifyKlasa(self.logger)
        poz = link.rfind('/') + 1
        sub = link[poz:]
        id = sub[0:22]
        dodatek = sub[-22:]
        if "spotify:" in link:
            id = dodatek
        nazwa_playlisty = ''
        if ("open.spotify.com/artist" in link) or ("spotify:artist:" in link):
            se = spot.zapytanie('artist', id, dodatek)
            try:
                for a in se['tracks']:
                    self.__dodaj_do_playlisty_spotify_track(a)
                nazwa_playlisty = se['tracks'][0]['artists'][0]['name']
            except (IndexError, KeyError, TypeError) as serr:
                self.logger.warning("Blad dodania playlisty z artysty: " + str(serr))
        elif ("open.spotify.com/playlist" in link) or ("spotify:playlist" in link):
            playlista = spot.zapytanie('playlist', id, dodatek)
            self.__dodaj_do_playlisty_spotify_playlist(playlista)
            nazwa_playlisty = playlista['name']
            next = playlista['tracks']['next']
            if (next is not None):
                if next != '':
                    kolejne = spot.nastepny(playlista['tracks']['next'])
                    self.__dodaj_do_playlisty_spotify_playlist(kolejne['kolejne'])
                    while kolejne['kolejne']['next'] is not None:
                        kolejne = spot.nastepny(kolejne['kolejne']['next'])
                        self.__dodaj_do_playlisty_spotify_playlist(kolejne['kolejne'])

        elif "open.spotify.com/user/" in link:
            se = spot.zapytanie('user_playlist', id, dodatek)
            for a in se['tracks']['items']:
                self.__dodaj_do_playlisty_spotify_track(a['track'])
            nazwa_playlisty = se['name']
        elif ("open.spotify.com/track" in link) or ("spotify:track:" in link):
            track = spot.zapytanie('track', link, dodatek)
            self.__dodaj_do_playlisty_spotify_track(track)
            nazwa_playlisty = track['artists'][0]['name']
        elif ("open.spotify.com/album" in link) or ("spotify:album" in link):
            album = spot.zapytanie('album', id, dodatek)
            self.__dodaj_do_playlisty_spotify_album(album)
            nazwa_playlisty = album['artists'][0]['name'] + ' - ' + album['name']

        if zmien_nazwe:
            self.nazwa = nazwa_playlisty
        self.zapisz_playliste()
        return nazwa_playlisty

    def __dodaj_do_playlisty_spotify_playlist(self, playlista):
        pl = []
        try:
            if 'tracks' in playlista:
                pl = playlista['tracks']['items']
            else:
                pl = playlista['items']
            for a in pl:
                self.__dodaj_do_playlisty_spotify_track(a['track'])
        except (KeyError, TypeError) as serr:
            self.logger.warning("Blad dodania pozycji playlisty spotify: " + str(serr))

    def __dodaj_do_playlisty_spotify_album(self, album):
        album_name = album['name']
        fanart = album['images'][0]['url']
        for a in album['tracks']['items']:
            self.dodaj_pozycje_z_polami(artist=a['artists'][0]['name'],
                                        album=album_name,
                                        title=a['name'],
                                        link=a['uri'],
                                        link_youtube='',
                                        typ=TYP_SPOTIFY,
                                        fanart=fanart,
                                        czas=str(datetime.timedelta(seconds=a['duration_ms'] / 1000)),
                                        uri_spotify=a['uri'])

    def __dodaj_do_playlisty_spotify_track(self, track):
        fanart = ''
        try:
            fanart = track['album']['images'][0]['url']
        except (IndexError, KeyError) as serr:
            self.logger.warning('Brak obrazu dla track: ' + str(track))
        artist = ''
        try:
            artist = track['artists'][0]['name']
        except (IndexError, KeyError) as serr:
            self.logger.warning('Brak artysty dla track: ' + str(track))
        album = ''
        try:
            album = track['album']['name']
        except (IndexError, KeyError, TypeError) as serr:
            self.logger.warning('Brak albumu dla track: ' + str(track))
        self.dodaj_pozycje_z_polami(artist=artist,
                                    album=album,
                                    title=track['name'],
                                    link=track['uri'],
                                    link_youtube='',
                                    typ=TYP_SPOTIFY,
                                    fanart=fanart,
                                    czas=str(datetime.timedelta(seconds=track['duration_ms'] / 1000)),
                                    uri_spotify=track['uri'])

    def dodaj_z_linku_youtube(self, link):
        try:
            self.logger.info('Rozwijam z linku youtube: ' + link)
            video = pafy.new(link)
            bestaudio = video.getbestaudio()
            if video.bigthumbhd != '':
                fanart = video.bigthumbhd
            else:
                fanart = video.bigthumb
            self.logger.info('Zakonczylem rozwijanie z linku youtube: ' + link)
            dostepny = True
        except (ValueError, IOError, RuntimeError) as serr:
            self.logger.warning('Pafy blad: ' + str(serr) + ' Link: ' + link)
            return ''
        if dostepny:
            self.dodaj_pozycje_z_polami(artist=video._author, album='', title=video.title,
                                        link=bestaudio._url, link_youtube=link, typ=TYP_YOUTUBE, fanart=fanart,
                                        czas=video.duration)
        self.zapisz_playliste()
        if video._author:
            return video._author
        else:
            return ''

    def dodaj_playliste_youtube(self, link):
        parsed = urlparse.urlparse(link)
        l2 = urlparse.parse_qs(parsed.query)['list']
        l2 = 'https://www.youtube.com/playlist?list=' + l2[0]
        try:
            lista = pafy.get_playlist(l2)
        except (ValueError, IOError, RuntimeError) as serr:
            self.logger.warning('Playlista youtube niedostepna, link: ' + link + ' Blad: ' + str(serr))
            return ''
        # TODO dorobic pobieranie nazwy
        nazwa = ''
        for a in lista['items']:
            li = a['pafy'].watchv_url
            self.dodaj_z_linku_youtube(li)
        self.zapisz_playliste()
        return nazwa

    def __sprawdz_rodzaj_linku(self, link):
        if "https://youtu.be/" in link or "https://www.youtube.com" in link or "http://www.youtu" in link:
            if "&list=" in link or 'playlist?list=' in link:
                return LINK_YOUTUBEPLAYLISTA
            return LINK_YOUTUBE
        if "open.spotify.com/" in link:
            return LINK_SPOTIFY
        if "spotify:" in link:
            return LINK_SPOTIFY
        self.logger.warning("Przyszedl link, ktory nie jest ani playlista ani video: " + str(link))
        return LINK_INNE

    def inicjalizuj_playliste_z_pliku(self, nazwa_pliku, zeruj=True):
        if nazwa_pliku == '':
            return
        try:
            try:
                pl = json.load(open(nazwa_pliku, 'r'))
            except Exception as serr:
                self.logger.warning('Blad inicjalizowanie playlisty z pliku: ' + nazwa_pliku +
                                    ', blad JSON: ' + str(serr))
                return

            if zeruj:
                nagl = pl['Naglowek']
                self.zeruj()
                self.nazwa = nagl[constants.NAZWA]
                self.jak_odtwarza = int(nagl['Jak_odtwarza'])
                self.nr_pozycji_na_playliscie = nagl['Numer_pozycji']

            # TODO czy nie dorobic do JSONa pojedynczej pozycji i potem skladac
            for p in pl[constants.POZYCJE]:
                self.pozycje.append(self.pozycja_z_json(p))
        except (Exception, IOError) as ser:
            self.logger.warning('Blad przy dodawaniu do playlisty z pliku: ' + nazwa_pliku + '. Kod bledu: ' + str(ser))
            return

    def dodaj_z_json(self, p):
        self.pozycje.append(self.pozycja_z_json(p))
        return

    def pozycja_z_json(self, p):
        artist = album = title = link = fanart = czas = serwisr = stacjar = link_youtube = uri_spotify = ''
        typ = TYP_YOUTUBE
        try:
            artist = p['artist']
        except KeyError:
            pass
        try:
            album = p['album']
        except KeyError:
            pass
        try:
            title = p['title']
        except KeyError:
            pass
        try:
            link = p['link']
        except KeyError:
            pass
        try:
            link_youtube = p['link_youtube']
        except KeyError as serr:
            pass
        try:
            typ = int(p['typ'])
        except KeyError:
            pass
        try:
            fanart = p['fanart']
        except KeyError:
            pass
        try:
            czas = p[constants.CZAS]
        except KeyError:
            pass
        try:
            serwisr = p['serwis_radiowy']
        except KeyError:
            pass
        try:
            stacjar = p['stacja_radiowa']
        except KeyError:
            # self.logger.warning('Brak klucza w playliscie: ' + str(serr))
            pass
        try:
            uri_spotify = p['uri_spotify']
        except KeyError:
            pass

        return PozycjaPlaylisty(artist=artist, album=album, title=title,
                                link=link, link_youtube=link_youtube, typ=typ, fanart=fanart,
                                czas=czas, serwis_radiowy=serwisr, stacja_radiowa=stacjar, uri_spotify=uri_spotify)

    def dodaj_pozycje_z_polami(self, artist='', album='', title='', link='', link_youtube='',
                               typ=TYP_RADIO, fanart='', czas='', serwis_radiowy='', stacja_radiowa='', uri_spotify=''):
        self.pozycje.append(PozycjaPlaylisty(artist=artist, album=album, title=title,
                                             link=link, link_youtube=link_youtube, typ=typ, fanart=fanart, czas=czas,
                                             serwis_radiowy=serwis_radiowy, stacja_radiowa=stacja_radiowa,
                                             uri_spotify=uri_spotify))
        return artist

    def zapisz_playliste_w_ulubionych(self, nazwa_ulubionego):
        # uwaga ! ta funkcja jest uruchamiana w osobnym watku
        # nazwa_ulubionego oznacza nazwe ulubionego do ktorego pliki trzeba sciagnac
        self.logger.info('Rozpoczynam zapisywanie w ulubionych: ' + nazwa_ulubionego)
        usun_pliki = False
        for a in self.pozycje:
            if a.typ == TYP_YOUTUBE:
                usun_pliki = True
                if self.katalog_ulubionych in a.link:
                    self.zapisz_playliste(nazwa=nazwa_ulubionego)
                    continue
                nazwa_katalogu = self.katalog_ulubionych + '/' + nazwa_ulubionego + SUFFIX_ULUBIONYCH_PLIKI
                if not os.path.isdir(nazwa_katalogu):
                    try:
                        os.mkdir(nazwa_katalogu)
                        self.logger.info('Stworzylem katalog na sciaganie plikow z youtube: ' + nazwa_ulubionego)
                    except OSError as serr:
                        self.logger.warning('Blad tworzenia katalogu na ulubiony: ' + str(serr))
                try:
                    video = pafy.new(a.link_youtube)
                    bestaudiox = video.getbestaudio()
                    # bestaudiox = video.getbestaudio(preftype="mp4")
                    nazwa_pliku = bestaudiox.filename
                    docelowa_nazwa_pliku = nazwa_katalogu + '/' + nazwa_pliku
                    a.link = docelowa_nazwa_pliku
                    if not os.path.isfile(docelowa_nazwa_pliku):
                        bestaudiox.download(docelowa_nazwa_pliku, quiet=True)
                        self.logger.info('Sciagnalem plik: ' + str(docelowa_nazwa_pliku))
                # except (ValueError, IOError, RuntimeError, RuntimeError) as serr:
                except Exception:
                    self.logger.warning('Video niedostepne, link: ' + a.link + ' Blad: ' + str(sys.exc_info()[0]))
                    continue
        self.zapisz_playliste(nazwa=nazwa_ulubionego)

        # usuwanie zbednych plikow, ktorych nie ma na liscie a mogly byc w katalogu
        # TODO dorobic usuwanie plikow, ktorych juz nie ma na liscie, uwaga KODI blokuje dostep do plikow
        """if usun_pliki:
            # for poz in self.pozycje:
            #    if os.path.isfile(poz.link):
                    
            try:
                nazwa_katalogu = KATALOG_ULUBIONYCH + '/' + self.nazwa + SUFFIX_ULUBIONYCH_PLIKI
                filenames = os.listdir(nazwa_katalogu)
            except OSError:
                self.logger.warning('Nie moge wylistowac katalogu: ' + str(nazwa_katalogu))
            for f in filenames:
                # sprawdzic czy plik jest na liscie, jak nie ma to usuwamy
                jest_na_liscie = False
                for poz in self.pozycje:
                    if poz.link == f:
                        jest_na_liscie = True
                if jest_na_liscie == False:
                    try:
                        os.remove(f)
                    except OSError:
                        self.logger.warning('Nie moge usunac pliku: ' + str(f))"""
        self.logger.info('Zakonczylem zapisywanie w ulubionych: ' + nazwa_ulubionego)
        return

    def zapisz_playliste(self, nazwa=''):
        self.ts = int(time.time())
        if self.liczba_pozycji() == 0:
            return
        dane = deepcopy(self.wyslij_playliste())
        if nazwa != '':
            nazwa_pliku = self.katalog_ulubionych + '/' + nazwa
            dane['Naglowek'][constants.NAZWA] = nazwa
        else:
            nazwa_pliku = self.nazwa_pliku_z_aktualna_playlista
        try:
            plik = open(nazwa_pliku, 'w')
            # TODO przerobic na JSON wysylanego z funkcji wyslij_playl.._JSON, konieczne przerob.danych w katalogu ulub
            plik.write(json.dumps(dane))
            plik.close()
            # self.logger.info('Zapisalem playliste w pliku: ' + nazwa_pliku)
        except [IOError, SystemError] as serr:
            self.logger.warning(
                'Nie moglem zapisac playlisty w pliku, nazwa playlisty: ' + nazwa_pliku + ' Blad: ' + str(serr))
            return
        return

    def wyslij_playliste(self, pelna=True):
        dane = {}
        # TODO przeniesc do contants ponize hardcody
        dane['Naglowek'] = {constants.NAZWA: self.nazwa,
                            'Jak_odtwarza': str(self.jak_odtwarza),
                            'Liczba_pozycji': int(self.liczba_pozycji()),
                            'Numer_pozycji': int(self.nr_pozycji_na_playliscie),
                            constants.TS: self.ts}
        pozy = []
        # TODO czy nie dorobic do JSONa pojedynczej pozycji i potem skladac
        for p in self.pozycje:
            pozy.append(p.pozycja_do_listy(pelna=pelna))
        dane[constants.POZYCJE] = pozy
        # return {constants.RODZAJ_KOMUNIKATU: constants.RODZAJ_KOMUNIKATU_PLAYLISTA,
        #        constants.RESULT: dane}
        return dane

    def oblicz_kolejny_do_grania(self):
        li = self.liczba_pozycji()
        if self.jak_odtwarza == PO_KOLEI:
            if self.nr_pozycji_na_playliscie == li - 1:
                self.nr_pozycji_na_playliscie = 0
            else:
                self.nr_pozycji_na_playliscie += 1
        else:
            self.nr_pozycji_na_playliscie = randint(0, li - 1)
        self.zapisz_playliste()

    def aktualnie_grane_link(self):
        try:
            return self.pozycje[self.nr_pozycji_na_playliscie].link
        except IndexError as serr:
            self.logger.warning('Odtwarzaj_z_playlisty, zly numer pozycji: ' + str(self.nr_pozycji_na_playliscie) +
                                ' --> dlugosc playlisty: ' + str(self.liczba_pozycji()) + ' blad: ' + str(serr))
        return ''

    def aktualna_pozycja(self):
        if self.liczba_pozycji() <= 0:
            return None
        try:
            poz = self.pozycje[self.nr_pozycji_na_playliscie]
        except IndexError:
            return None
        return poz

    def nastepny(self):
        # zwraca false jesli playlista pusta
        # zwraca true jesli obliczyl kolejny do grania i zaktualizowal czygra
        if self.liczba_pozycji() == 0:
            return False
        if self.nr_pozycji_na_playliscie == self.liczba_pozycji() - 1:
            self.nr_pozycji_na_playliscie = 0
        else:
            self.nr_pozycji_na_playliscie = self.nr_pozycji_na_playliscie + 1
        return True

    def poprzedni(self):
        # zwraca false jesli playlista pusta
        # zwraca true jesli obliczyl kolejny do grania i zaktualizowal czygra
        if self.liczba_pozycji() == 0:
            return False
        if self.nr_pozycji_na_playliscie == 0:
            self.nr_pozycji_na_playliscie = self.liczba_pozycji() - 1
        else:
            self.nr_pozycji_na_playliscie = self.nr_pozycji_na_playliscie - 1
        return True

    def zeruj(self):
        self.nr_pozycji_na_playliscie = 0
        self.nazwa = ''
        self.jak_odtwarza = PO_KOLEI
        self.pozycje = []

    def usun_pozycje_z_playlisty(self, nr_pozycji):
        # zwraca True jesli usuwana pozycja jest ta sama co obecna, False jesli inna
        if self.liczba_pozycji() == 1:
            return True
        self.pozycje.pop(nr_pozycji)
        self.logger.info("Usunalem z playlisty pozycje nr " + str(nr_pozycji))

        if nr_pozycji == self.nr_pozycji_na_playliscie:
            self.nastepny()
            self.zapisz_playliste()
            return True
        else:
            self.zapisz_playliste()
            return False

    def liczba_pozycji(self):
        return len(self.pozycje)
