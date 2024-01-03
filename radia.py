# TODO urrlib do usuniecia , przejscie na requets
import urllib2
import json
import threading
import constants
import xml.etree.ElementTree
import ConfigParser
import os
import xml.dom.minidom as minidom
from MojLogger import MojLogger
import time
import requests
from THutils import skonstruuj_odpowiedzV2OK

#TODO usunac urllib i przejsc na requests

NAZWA_SERWISU_OPENFM = 'Open FM'
NAZWA_SERWISU_RMFFM = 'RMF FM'
NAZWA_SERWISU_TUNEIN = 'TuneIn'
NAZWA_SERWISU_POLSKIERADIO = 'Polskie Radio'

#TODO API was chenged for OPEN FM and now list of stations is not being updated

INTERWAL_ODCZYTU_CO_GRANE = 120  #w sekundach

SERWIS = 'serwis'
# NAZWA = 'nazwa'
LINK = 'link'
LOGO = 'logo'
GRUPA = 'grupa'

CZAS_POBIERANIA_RADI_CYKLICZNIE = 85000

#struktura danych o stacjach radiowych
#nr - numer serwisu
#id - id stacji
#nazwa - nazwa stacji
#link - link stacji
#logo - link do loga stacji
#grupa - grupy stacji, do ktorych nalezy dana stacja

class Radio:
    def __init__(self, nazwa_serwisu, nazwa_radia, id_radia, link, logo, grupy):
        self.nazwa_serwisu = nazwa_serwisu
        self.grupy = grupy #lista grup
        self.nazwa_radia = nazwa_radia
        self.link = link
        self.logo = logo
        self.id_radia = id_radia

# TODO przejscie na klase radio z metodami typu get_name
class Radia:
    def __init__(self, obszar, logger):
        self.obszar = obszar
        self.stacje_radiowe = []
        self.ts = time.time()*1000
        self._ts_odczytywania_co_grane = 0  #aby nie za czesto odczytywac co grane
        self.logger = logger    #type: MojLogger

    def pobierz_radia_cyklicznie(self):
        threading.Thread(target=self.aktualizuj_stacje).start()
        threading.Timer(CZAS_POBIERANIA_RADI_CYKLICZNIE, self.pobierz_radia_cyklicznie).start()

    def wyslij_katalog_radii(self):
        katalog_radii = []
        for a in self.stacje_radiowe:   # type: Radio
            katalog_radii.append({SERWIS:a.nazwa_serwisu,
                            constants.NAZWA:a.nazwa_radia,
                            GRUPA:a.grupy,
                            LOGO:a.logo,
                            constants.ID:a.id_radia})
        dane = {constants.TS: self.ts,
                constants.POZYCJE: katalog_radii}
        return skonstruuj_odpowiedzV2OK(constants.RODZAJ_KOMUNIKATU_KATALOG_RADII, dane, constants.OBSZAR_NAGL)


    def aktualizuj_stacje(self):
        self.stacje_radiowe = []
        self.dodaj_stacje_openfm()
        self.dodaj_stacje_tunein()
        self.dodaj_stacje_rmf()
        self.dodaj_stacje_polskieradio()
        self.logger.info(self.obszar, 'Zaktualizowalem liste radii. Liczba stacji: ' +
                         str(len(self.stacje_radiowe)))
        self.ts = time.time()*1000
        return

    def znajdz_stacje_po_nazwie_i_serwisie(self, nazwa_serw, nazwa_sta):
        for a in self.stacje_radiowe:   # type: Radio
            if a.nazwa_serwisu == nazwa_serw and a.nazwa_radia == nazwa_sta:
                return a
        return None

    def znajdz_stacje_po_nazwie_i_id(self, nazwa_serw, id_stacji):
        for a in self.stacje_radiowe:   # type: Radio
            if a.nazwa_serwisu == nazwa_serw and a.id_radia == id_stacji:
                return a
        return None

    # TODO wysylajac liste radii to grupy w kazdej pozycji powinny byc arrayem a nie rozkodowanym JSON

    def parse_asf(self, url):
        streams = []
        req = urllib2.Request(url)
        f = urllib2.urlopen(req)
        config = ConfigParser.RawConfigParser()
        config.readfp(f)
        references = config.items('Reference')
        for ref in references:
            streams.append(ref[1])
        f.close()
        return streams

    def parse_asx(self, url):
        streams = []
        try:
            req = urllib2.Request(url)
            f = urllib2.urlopen(req)
            xmlstr = f.read().decode('ascii', 'ignore')
            dom = minidom.parseString(xmlstr)
            asx = dom.childNodes[0]
            for node in asx.childNodes:
                if str(node.localName).lower() == 'entryref' and node.hasAttribute('href'):
                    streams.append(node.getAttribute('href'))
                elif str(node.localName).lower() == 'entryref' and node.hasAttribute('HREF'):
                    streams.append(node.getAttribute('HREF'))
                elif str(node.localName).lower() == 'entry':
                    for subnode in node.childNodes:
                        if str(subnode.localName).lower() == 'ref' and subnode.hasAttribute('href') and not subnode.getAttribute('href') in streams:
                            streams.append(subnode.getAttribute('href'))
                        elif str(subnode.localName).lower() == 'ref' and subnode.hasAttribute('HREF') and not subnode.getAttribute('HREF') in streams:
                            streams.append(subnode.getAttribute('HREF'))
            f.close()
        except Exception as serr:
            self.logger.warning(self.obszar, 'Nie moge parsowac ASX. Blad: ' + str(serr))
        return streams

    def parse_m3u(self, url):
        streams = []
        try:
            req = urllib2.Request(url)
            f = urllib2.urlopen(req)
            for line in f:
                if len(line.strip()) > 0 and not line.strip().startswith('#'):
                    streams.append(line.strip())
            f.close()
        except urllib2.HTTPError as serr:
            #THutils.zapisz_do_logu_plik('E', 'Nie moge parsowac M3U. Blad: ' + str(serr))
            self.logger.warning(self.obszar, 'Nie moge parsowac M3U. Blad: ' + str(serr))
        return streams

    def parse_pls(self, url):
        streams = []
        try:
            req = urllib2.Request(url)
            f = urllib2.urlopen(req)
            config = ConfigParser.RawConfigParser()
            config.readfp(f)
            numentries = config.getint('playlist', 'NumberOfEntries')
            while numentries > 0:
                streams.append(
                    config.get('playlist', 'File' + str(numentries)))
                numentries -= 1
            f.close()
        except (urllib2.URLError, urllib2.HTTPError, ConfigParser.NoSectionError, ConfigParser.NoOptionError, ConfigParser.MissingSectionHeaderError) as serr:
            self.logger.warning(self.obszar, 'Blad podczas parsowania PLS. Link: ' + str(url))
        return streams

    def dodaj_renderjson(self, link):
        return str(link+'&render=json')

    def dodaj_stacje_tunein_zjson(self, nazwa_grupy, lista_stacji):
        # parametrem jest lista obiektow JSON
        for j in lista_stacji:
            try:
                link_stacja = ''
                if j['type'] == 'audio':
                    if j['item'] == 'station':
                        #link_stacja = self.tunein_dekoduj_stream_stacji(j['URL'])
                        link_stacja = j['URL']
                        #if link_stacja == '':
                        #    print 'nie ma linku'
                        #    self.logger.warning('Nie ma linku stacji : ' + str(j))
                        nazwa_stacji = j['text']
                        id_stacji = j['guide_id']
                        logo = j['image']
                        gr = [nazwa_grupy]
                        #self.dodaj_stacje(NAZWA_SERWISU_TUNEIN, id_stacji, nazwa_stacji, link_stacja, logo, gr)

                        # TODO tunein tylko jedna grupa dla stacji do sprawdzenia?
                        #nowa_grupa = GrupaRadii(NAZWA_SERWISU_TUNEIN, nazwa_grupy, '1')
                        #self.grupy_stacji.append(nowa_grupa)
                        stacja = Radio(NAZWA_SERWISU_TUNEIN, nazwa_stacji, id_stacji, link_stacja, logo, [nazwa_grupy])
                        self.stacje_radiowe.append(stacja)
            except KeyError as serr:
                #THutils.zapisz_do_logu_plik('E', 'Blad klucza: ' + str(serr) + ' Stacja: ' + str(j))
                self.logger.warning(self.obszar, 'Blad klucza: ' + str(serr) + ' Stacja: ' + str(j))
        #self.tunein_aktualizuj_stream_dla_wszystkich_stacji()
        return
        #{'serwis': nazwa_serwisu, 'id': id, 'nazwa': nazwa, 'link': link, 'logo': logo, 'grupa': grupa})

    def tunein_dekoduj_stream_stacji(self, link):
        # TODO tutaj trzeba skopiowac i dostosowac funckje tune() z tunein.py
        link_stacja = self.tunein_odczytaj_link_stacji(link)
        (filepath, filename) = os.path.split(link_stacja)
        (shortname, extension) = os.path.splitext(filename)
        # filepath = filepath.lower()
        # filename = filename.lower()
        # shortname = shortname.lower()
        extension = extension.lower().split('?',1)[0]
        m3usy = []
        if extension == '.pls':
            m3usy = self.parse_pls(link_stacja)
        elif extension == '.m3u':
            m3usy = self.parse_m3u(link_stacja)
        elif extension == '.asx':
            m3usy = self.parse_asx(link_stacja)
        elif extension == '.asf':
            m3usy = self.parse_asf(link_stacja)
            # TODO dorobic parsing .st, w logu z dnia 16.11.2018
        else:
            m3usy.append(link_stacja)
        #elif extension == '.mp3':
        #    m3usy.append(link_stacja)
        #elif extension == '.audio':
        #    m3usy.append(link_stacja)
        #else:
            #THutils.zapisz_do_logu_plik('E', 'TuneIn stacja bez linku : ' + str(link_stacja))
        #    self.logger.warning('TuneIn stacja bez linku : ' + str(link_stacja))
        if len (m3usy) == 0:
            self.logger.warning(self.obszar, 'TuneIn stacja bez linku : ' + str(link_stacja))
            return ''
        else:
            return m3usy[0]

    # TODO przekopiowac z tunein.py, jest na pulpicie wszystkie funckje z describe aby dowiadywac sie co aktualnie grane
    # TODO przekopiowac tez searcha

    """def tunein_aktualizuj_stream_dla_wszystkich_stacji(self):
        for j in self.stacje:
            if j['serwis'] == NAZWA_SERWISU_TUNEIN:
                stream = self.tunein_dekoduj_stream_stacji(j['link'])
                if len(stream) > 0:
                    j['link'] = stream
        return"""

    def tunein_odczytaj_liste_grup(self, link):
        try:
            result = str(urllib2.urlopen(link).read())
        except (urllib2.URLError, urllib2.HTTPError) as serr:
            #THutils.zapisz_do_logu_plik('E', 'Blad podczas odczytu glownego linku z TuneIN. Blad: ' + str(serr))
            self.logger.warning(self.obszar, 'Blad podczas odczytu glownego linku z TuneIN. Blad: ' + str(serr))
            return
        js = json.JSONDecoder().decode(result)
        return js

    def dodaj_stacje_tunein(self):
        try:
            lista_grup = self.tunein_odczytaj_liste_grup("http://opml.radiotime.com/Browse.ashx?c=music&render=json&partnerid=HyzqumNX")['body']
            if len(lista_grup) == 0:
                return

            for j in lista_grup:
                # ta sekcja dodaje dodatkowe stacje krajowe z kategorii World Music
                if j['text'] == 'World Music':
                    lista_grup_world = self.tunein_odczytaj_liste_grup(self.dodaj_renderjson(j['URL']))
                    for aa in lista_grup_world['body'][2]['children']:
                        self.dodaj_tunein_outline(aa)
                self.dodaj_tunein_outline(j)
            self.logger.info(self.obszar, 'Dodalem stacje TuneIn.')
        except TypeError as serr:
            self.logger.warning(self.obszar, 'Nie moge odczytac stacji TuneIn: ' + str(serr))
        return

    def dodaj_tunein_outline(self, outline):
        # koniec sekcji dodawania world music
        if outline['type'] == 'link':
            nazwa_grupy = outline['text']
            link_grupa = self.dodaj_renderjson(outline['URL'])
            try:
                # TODO pozbyc sie wszystkich urlopen
                js = requests.get(link_grupa).json()
                lista_stacji = []
                try:
                    for a in js['body']:
                        if a['key'] == 'stations':
                            lista_stacji = a
                            break
                except Exception:
                    self.logger.warning(self.obszar, 'Brak sekcji body: ' + str(js))
                try:
                    self.dodaj_stacje_tunein_zjson(nazwa_grupy, lista_stacji['children'])
                except KeyError as serr:
                    self.logger.warning(self.obszar, 'Brak sekcji children ... ' + str(lista_stacji))
            except Exception as serr:
                self.logger.warning(self.obszar, 'Blad podczas odczytu z tunein.... Blad: ' + str(serr))


    def tunein_odczytaj_link_stacji(self, link):
        link_stacji = ''
        try:
            li = self.dodaj_renderjson(link)
            result = str(urllib2.urlopen(li).read())
            js = json.JSONDecoder().decode(result)
            link_stacji = js['body'][0]['url']
        except (urllib2.URLError, urllib2.HTTPError) as serr:
            self.logger.warning(self.obszar, 'Blad podczas odczytu listy stacji tunein. Link: ' + link + ' Blad: ' + str(serr))
        return link_stacji

    def dodaj_stacje_polskieradio(self):
        API_URL = 'http://moje.polskieradio.pl/api/?key=d590cafd-31c0-4eef-b102-d88ee2341b1a'
        #pobranie listy stacji
        try:
            #req = urllib2.urlopen(API_URL)
            result_object = requests.get(API_URL).json()
        except Exception as serr:
            self.logger.warning(self.obszar, 'Blad odczytu stacji Polskie Radio: ' + str(serr))
            return
        #result_object = json.loads(req.read())
        stacje = result_object["channel"]
        #grupy = result_object["groups"]
        #nazwa_grupy = ''
        for a in stacje:
            id = a[constants.ID]
            nazwa = a['title']
            link = ''
            logo = a['image']
            #grupa = a['category']
            grupa = []
            for j in a['subcategories']:
                grupa.append(j['name'])
                #gr = GrupaRadii(NAZWA_SERWISU_POLSKIERADIO, j['name'], j['id'])
                #self.grupy_stacji.append(gr)
            stream = a['AlternateStationsStreams']
            for i in range(len(stream)):
                if stream[i]["name"] == 'MP3-AAC':
                    link = stream[i]["link"]
            #self.dodaj_stacje(NAZWA_SERWISU_POLSKIERADIO, id, nazwa, link, logo, grupa)
            stacja = Radio(NAZWA_SERWISU_POLSKIERADIO, nazwa, id, link, logo, grupa)
            self.stacje_radiowe.append(stacja)
        #THutils.zapisz_do_logu_plik('I', 'Dodalem stacje Polskie Radio.')
        self.logger.info(self.obszar, 'Dodalem stacje Polskie Radio.')
        return

    def dodaj_stacje_rmf(self):
        API_URL = "http://rmfon.pl/json/stations.txt/"
        STACJA_DETALE = "http://www.rmfon.pl/stacje/flash_aac_"
        STACJA_SUFFIX = ".xml.txt"
        LOGA_URL = "http://www.rmfon.pl/i/logos/100x100/"
        LOGA_SUFFIX = ".png"
        KATEGORIE = "http://rmfon.pl/mobilev3/stations/RMFONANDROID/null-"

        #pobranie listy stacji
        try:
        #    req = urllib2.urlopen(API_URL)
        #except (urllib2.URLError) as serr:
            #THutils.zapisz_do_logu_plik('E', 'Nie moge odczytac linku API_URL. Blad: ' + str(serr))
        #    self.logger.warning('Nie moge odczytac linku API_URL. Blad: ' + str(serr))
        #    return
            st_json = requests.get(API_URL).json()
        except Exception as serr:
            self.logger.warning(self.obszar, 'Blad odczytu z API RMF: ' + str(serr))
        #result_object = self.odczytaj_xml(KATEGORIE)
        try:
            #TODO wymienic url na requests
            req = urllib2.urlopen(KATEGORIE)
        except urllib2.URLError as serr:
            #THutils.zapisz_do_logu_plik('E', 'Nie moge odczytac linku KATEGORIE. Blad: ' + str(serr))
            self.logger.warning(self.obszar, 'Nie moge odczytac linku KATEGORIE. Blad: ' + str(serr))
            return
        result_object = xml.etree.ElementTree.parse(req).getroot()
        stacjex = result_object.find('stations')
        stacje = stacjex.getiterator('station')
        grupyx = result_object.find('categories')
        grupy = grupyx.getiterator('category')
        for j in stacje:
            nazwa_stacji = j.get('name')
            id_stacji = j.get(constants.ID)
            for a in st_json:
                if id_stacji == a['id']:
                    idname = a['idname']
                    break
            link = j.get('stream_aac')
            gr = []
            for i in grupy:
                stac = i.get('stations').split(',')
                if id_stacji in stac:
                    gr.append(i.get('name'))
            #self.dodaj_stacje(NAZWA_SERWISU_RMFFM, id_stacji, nazwa_stacji, link, LOGA_URL + idname + LOGA_SUFFIX, gr)
            stacja = Radio(NAZWA_SERWISU_RMFFM, nazwa_stacji, id_stacji, link, LOGA_URL + idname + LOGA_SUFFIX, gr)
            self.stacje_radiowe.append(stacja)
        self.logger.info(self.obszar, 'Dodalem stacje RMF FM.')
        return

    #TODO usunac wszystkie odwolania do urrlib2 i przejsc na request, w calym kodzie

    def odswiez_co_grane_openfm(self, id_stacji):
        artysta = tytul = album = ''
        ts_konca = 0

        if id_stacji == '':
            self.logger.warning(self.obszar, 'Nie moge odczytac aktualnie grane OpenFM bo ID_STACJI jest puste')
        else:
            URL_API = "https://open.fm/api/api-ext/v2/channels/short.json"
            zwrotka = {}
            try:
                zwrotka = requests.get(URL_API).json()
            except Exception:
                self.logger.warning(self.obszar, 'Blad odczytu z API Open FM')

            try:
                lista_kanalow = zwrotka['channels']
                for a in lista_kanalow:
                    if a['id'] == int(id_stacji):
                        track = a['tracks'][0]['song']
                        tytul = track['title']
                        artysta = track['artist']
                        album = track['album']['title']
                        ts_konca = a['tracks'][0]['end']


            except KeyError as serr:
                self.logger.warning(self.obszar, 'Problem przy odczycie co grane Open FM: ' + str(serr))
            # zwraca artyste, album, tytul oraz timestamp konca
            self.logger.info(self.obszar, 'Odczytalem OPen FM co grane: ' + str(artysta) + ', ' + str(album) + ', ' + str(tytul)
                             + ', ' + str(ts_konca))
        return artysta, album, tytul, ts_konca

    def dodaj_stacje_openfm(self):
        #odczytanie z OPEN FM biezacych definicji stacji i grup
        API_URL = "http://open.fm/api/static/stations/stations.json"
        # TODO dorobic server do grania z IP ktore jest z linku wyzej
        PLAY_URL = "http://stream.open.fm/"
        try:
            result_object = requests.get(API_URL).json()
        except Exception as serr:
            self.logger.warning(self.obszar, 'Blad odczytu z API Open FM: ' + str(serr))
            return
        stacje = result_object["channels"]

        #aktualizacja listy grup
        '''grupy = result_object["groups"]
        for a in grupy:
            nowa_grupa = GrupaRadii(NAZWA_SERWISU_OPENFM, a['name'], a['id'])
            self.grupy_stacji.append(nowa_grupa)'''

        #class Radio:
        #def __init__(self, nazwa_serwisu, nazwa_radia, id_radia, link, logo, grupy):
        for a in stacje:
            logo_url = a['logo']['url']
            logo_url = logo_url.replace("71x71", "300x300")

            grupy = []
            for gr_ids in a['group_ids']:
                for gr in result_object["groups"]:
                    if gr['id'] == str(gr_ids):
                        grupy.append(gr['name'])
            stacja = Radio(NAZWA_SERWISU_OPENFM, a['name'], a['id'], PLAY_URL+a['id'], logo_url, grupy)
            self.stacje_radiowe.append(stacja)

            '''nazwa_grupy = []
            for x in grupy:
                if x['id'] == a['group_id']:
                    nazwa_grupy.append(x['name'])'''

            #self.dodaj_stacje(NAZWA_SERWISU_OPENFM, a['id'], a['name'], PLAY_URL+a['id'], logo_url , nazwa_grupy)
        #THutils.zapisz_do_logu_plik('I', 'Dodalem stacje OpenFM.')
        self.logger.info(self.obszar, 'Dodalem stacje OpenFM.')
        return
