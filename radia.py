# TODO urrlib do usuniecia , przejscie na requets
import urllib2
import requests
import json
import thread
import threading
import constants
import xml.etree.ElementTree
import ConfigParser
import os
import xml.dom.minidom as minidom
import logging
import time
from THutils import skonstruuj_odpowiedzV2

#struktura danych o radiach
#nr - numer serwisu: 0-openfm, 1-rmf fm, 2, tunein
#nazwa - nazwa serwisu np. Open FM

NAZWA_SERWISU_OPENFM = 'Open FM'
NAZWA_SERWISU_RMFFM = 'RMF FM'
NAZWA_SERWISU_TUNEIN = 'TuneIn'
NAZWA_SERWISU_POLSKIERADIO = 'Polskie Radio'

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

# TODO przejscie na klase radio z metodami typu get_name
class Radia:
    def __init__(self):
        self.stacje = []
        self.ts = int(time.time())
        self.logger = logging.getLogger(constants.NAZWA_LOGGERA)
        self.pobierz_radia_cyklicznie()

    def pobierz_radia_cyklicznie(self):
        thread.start_new_thread(self.aktualizuj_stacje, ())
        threading.Timer(CZAS_POBIERANIA_RADI_CYKLICZNIE, self.pobierz_radia_cyklicznie).start()

    def wyslij_katalog_radii(self):
        katalog = []
        for a in self.stacje:
            katalog.append({SERWIS:a[SERWIS],
                            constants.NAZWA:a[constants.NAZWA],
                            GRUPA:a[GRUPA],
                            LOGO:a[LOGO],
                            constants.ID:a[constants.ID]})
        dane = {constants.TS: self.ts,
                constants.POZYCJE: katalog}
        return skonstruuj_odpowiedzV2(constants.RODZAJ_KOMUNIKATU_KATALOG_RADII, dane, constants.STATUS_OK)


    def aktualizuj_stacje(self):
        self.stacje = []
        self.dodaj_stacje_openfm()
        self.dodaj_stacje_tunein()
        self.dodaj_stacje_rmf()
        self.dodaj_stacje_polskieradio()
        self.logger.info('Zaktualizowalem liste radii. Liczba stacji: ' +
                         str(len(self.stacje)))
        self.ts = int(time.time())
        return

    def dodaj_stacje(self, nazwa_serwisu, id, nazwa, link, logo, grupy):
        #js = json.dumps(grupy)
        # TODO self.stacje powinno byc tabela klasy stacja radiowa a nie tuplem
        self.stacje.append({SERWIS: nazwa_serwisu, constants.ID: id, constants.NAZWA: nazwa, LINK: link,
                            LOGO: logo, GRUPA:grupy})
        return

    def znajdz_stacje_po_nazwie_i_serwisie(self, nazwa_serw, nazwa_sta):
        for a in self.stacje:
            if a[SERWIS] == nazwa_serw and a[constants.NAZWA] == nazwa_sta:
                return a
        return None

    def znajdz_stacje_po_nazwie_i_id(self, nazwa_serw, id_stacji):
        for a in self.stacje:
            if a[SERWIS] == nazwa_serw and a[constants.ID] == id_stacji:
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
                if (str(node.localName).lower() == 'entryref' and node.hasAttribute('href')):
                    streams.append(node.getAttribute('href'))
                elif (str(node.localName).lower() == 'entryref' and node.hasAttribute('HREF')):
                    streams.append(node.getAttribute('HREF'))
                elif (str(node.localName).lower() == 'entry'):
                    for subnode in node.childNodes:
                        if (str(subnode.localName).lower() == 'ref' and subnode.hasAttribute('href') and not subnode.getAttribute('href') in streams):
                            streams.append(subnode.getAttribute('href'))
                        elif (str(subnode.localName).lower() == 'ref' and subnode.hasAttribute('HREF') and not subnode.getAttribute('HREF') in streams):
                            streams.append(subnode.getAttribute('HREF'))
            f.close()
        except (Exception) as serr:
            self.logger.warning('Nie moge parsowac ASX. Blad: ' + str(serr))
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
        except (urllib2.HTTPError) as serr:
            #THutils.zapisz_do_logu_plik('E', 'Nie moge parsowac M3U. Blad: ' + str(serr))
            self.logger.warning('Nie moge parsowac M3U. Blad: ' + str(serr))
        return streams

    def parse_pls(self, url):
        streams = []
        try:
            req = urllib2.Request(url)
            f = urllib2.urlopen(req)
            config = ConfigParser.RawConfigParser()
            config.readfp(f)
            numentries = config.getint('playlist', 'NumberOfEntries')
            while (numentries > 0):
                streams.append(
                    config.get('playlist', 'File' + str(numentries)))
                numentries -= 1
            f.close()
        except (urllib2.URLError, urllib2.HTTPError, ConfigParser.NoSectionError, ConfigParser.NoOptionError, ConfigParser.MissingSectionHeaderError) as serr:
            self.logger.warning('Blad podczas parsowania PLS. Link: ' + str(url))
        return streams

    def dodaj_renderjson(self, link):
        return str(link+'&render=json')

    def dodaj_stacje_tunein_zjson(self, nazwa_grupy, lista_stacji):
        # parametrem jest lista obiektow JSON
        for j in lista_stacji:
            try:
                #if j['type'] == 'link' and j['key'] == 'nextStations':
                #    li = self.dodaj_renderjson(j['URL'])
                #    self.dodaj_stacje_tunein_zjson(nazwa_grupy, self.odczytaj_liste_stacji_tunein(li))
                #else:
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
                        gr = []
                        gr.append(nazwa_grupy)
                        self.dodaj_stacje(NAZWA_SERWISU_TUNEIN, id_stacji, nazwa_stacji, link_stacja, logo, gr)
            except KeyError as serr:
                #THutils.zapisz_do_logu_plik('E', 'Blad klucza: ' + str(serr) + ' Stacja: ' + str(j))
                self.logger.warning('Blad klucza: ' + str(serr) + ' Stacja: ' + str(j))
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
            self.logger.warning('TuneIn stacja bez linku : ' + str(link_stacja))
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
            self.logger.warning('Blad podczas odczytu glownego linku z TuneIN. Blad: ' + str(serr))
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
                """if j['type'] == 'link':
                    nazwa_grupy = j['text']
                    link_grupa = self.dodaj_renderjson(j['URL'])
                    try:
                        result = str(urllib2.urlopen(link_grupa).read())
                        js = json.JSONDecoder().decode(result)
                        lista_stacji = js['body'][0]
                        self.dodaj_stacje_tunein_zjson(nazwa_grupy, lista_stacji['children'])
                        #ta sekcja dodaje dodatkowe stacje krajowe z kategorii World Music
                        if nazwa_grupy == 'World Music':
                            lista_stacji = js['body'][2]
                            self.dodaj_stacje_tunein_zjson(nazwa_grupy, lista_stacji['children'])
                        #koniec sekcji dodawania world music
                    except (urllib2.URLError, urllib2.HTTPError) as serr:
                        THutils.zapisz_do_logu_plik('E', 'Blad podczas odczytu z tunein.... Blad: ' + str(serr))"""
            self.logger.info('Dodalem stacje TuneIn.')
        except TypeError as serr:
            self.logger.warning('Nie moge odczytac stacji TuneIn: ' + str(serr))
        return

    def dodaj_tunein_outline(self, outline):
        # koniec sekcji dodawania world music
        if outline['type'] == 'link':
            nazwa_grupy = outline['text']
            link_grupa = self.dodaj_renderjson(outline['URL'])
            try:
                #result = str(urllib2.urlopen(link_grupa).read())
                # TODO pozbyc sie wszystkich urlopen
                result = requests.get(link_grupa).text
                js = json.loads(result)
                lista_stacji = []
                try:
                    for a in js['body']:
                        if a['key'] == 'stations':
                            lista_stacji = a
                            break
                except IndexError:
                    self.logger.warning('Brak sekcji body: ' + str(js))
                try:
                    self.dodaj_stacje_tunein_zjson(nazwa_grupy, lista_stacji['children'])
                except KeyError as serr:
                    #THutils.zapisz_do_logu_plik('E', 'Brak sekcji children ... ' + str(lista_stacji))
                    self.logger.warning('Brak sekcji children ... ' + str(lista_stacji))
            except (urllib2.URLError, urllib2.HTTPError) as serr:
                #THutils.zapisz_do_logu_plik('E', 'Blad podczas odczytu z tunein.... Blad: ' + str(serr))
                self.logger.warning('Blad podczas odczytu z tunein.... Blad: ' + str(serr))


    def tunein_odczytaj_link_stacji(self, link):
        link_stacji = ''
        try:
            li = self.dodaj_renderjson(link)
            result = str(urllib2.urlopen(li).read())
            js = json.JSONDecoder().decode(result)
            link_stacji = js['body'][0]['url']
        except (urllib2.URLError, urllib2.HTTPError) as serr:
            #THutils.zapisz_do_logu_plik('E', 'Blad podczas odczytu listy stacji tunein. Link: ' + link + ' Blad: ' + str(serr))
            self.logger.warning('Blad podczas odczytu listy stacji tunein. Link: ' + link + ' Blad: ' + str(serr))
        return link_stacji

    def dodaj_stacje_polskieradio(self):
        API_URL = 'http://moje.polskieradio.pl/api/?key=d590cafd-31c0-4eef-b102-d88ee2341b1a'
        #pobranie listy stacji
        try:
            req = urllib2.urlopen(API_URL)
        except IOError as serr:
            return
        result_object = json.loads(req.read())
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
            stream = a['AlternateStationsStreams']
            for i in range(len(stream)):
                if stream[i]["name"] == 'MP3-AAC':
                    link = stream[i]["link"]

            self.dodaj_stacje(NAZWA_SERWISU_POLSKIERADIO, id, nazwa, link, logo, grupa)
        #THutils.zapisz_do_logu_plik('I', 'Dodalem stacje Polskie Radio.')
        self.logger.info('Dodalem stacje Polskie Radio.')
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
            req = urllib2.urlopen(API_URL)
        except (urllib2.URLError) as serr:
            #THutils.zapisz_do_logu_plik('E', 'Nie moge odczytac linku API_URL. Blad: ' + str(serr))
            self.logger.warning('Nie moge odczytac linku API_URL. Blad: ' + str(serr))
            return
        st_json = json.loads(req.read())
        #result_object = self.odczytaj_xml(KATEGORIE)
        try:
            req = urllib2.urlopen(KATEGORIE)
        except (urllib2.URLError) as serr:
            #THutils.zapisz_do_logu_plik('E', 'Nie moge odczytac linku KATEGORIE. Blad: ' + str(serr))
            self.logger.warning('Nie moge odczytac linku KATEGORIE. Blad: ' + str(serr))
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
            self.dodaj_stacje(NAZWA_SERWISU_RMFFM, id_stacji, nazwa_stacji, link, LOGA_URL + idname + LOGA_SUFFIX, gr)
        #THutils.zapisz_do_logu_plik('I', 'Dodalem stacje RMF FM.')
        self.logger.info('Dodalem stacje RMF FM.')
        return

    #TODO usunac wszystkie odwolania do urrlib2 i przejsc na request, w calym kodzie

    def dodaj_stacje_openfm(self):
        API_URL = "http://open.fm/api/static/stations/stations.json"
        #PLAY_URL = "http://gr-relay-12.gaduradio.pl/"
        PLAY_URL = "http://stream.open.fm/"
        try:
            req = urllib2.urlopen(API_URL)
        except (urllib2.URLError) as serr:
            return
        result_object = json.loads(req.read())
        stacje = result_object["channels"]
        grupy = result_object["groups"]
        for a in stacje:
            nazwa_grupy = []
            for x in grupy:
                if x['id'] == a['group_id']:
                    nazwa_grupy.append(x['name'])
            logo_url = a['logo']['url']
            logo_url = logo_url.replace("71x71", "300x300")
            self.dodaj_stacje(NAZWA_SERWISU_OPENFM, a['id'], a['name'], PLAY_URL+a['id'], logo_url , nazwa_grupy)
        #THutils.zapisz_do_logu_plik('I', 'Dodalem stacje OpenFM.')
        self.logger.info('Dodalem stacje OpenFM.')
        return


    """def odczytaj_xml(self, link):
        if link == '' or link == None:
            return None
        try:
            req = urllib2.urlopen(link)
        except (urllib2.URLError) as serr:
            THutils.zapisz_do_logu_plik('E', 'Nie moge odczytac linku z XMLa. Link: ' + str(link) + ' Blad: ' + str(serr))
            return None
        return xml.etree.ElementTree.parse(req).getroot()"""

    """def znajdz_link(self, link, tekst):
        result = self.odczytaj_xml(link)
        if result is None:
            return None
        a = result.find('body')
        x = a.getiterator('outline')
        for i in x:
            if i.get('text') == tekst:
                return i.get('URL')"""


    """def aktualizuj_stream_dla_stacji2(self):
        for a in self.stacje:
            if a['serwis'] == 'TuneIn':
                try:
                    ur = urllib2.Request(a['link'])
                    result = urllib2.urlopen(ur).read()
                except (urllib2.URLError, urllib2.HTTPError) as serr:
                    THutils.zapisz_do_logu_plik('E', 'Blad podczas odczytywania listy streamow. Link: ' + str(
                        link_stacja) + 'Blad: ' + str(serr))
                js = json.JSONDecoder().decode(result)['body']
                for stream in js:
                    if stream['is_direct']:
                        self.dodaj_stacje('TuneIn', id_stacji, nazwa_stacji, stream['url'], logo, nazwa_grupy)
                    else:
                        if (not 'playlist_type' in stream):
                            self.dodaj_stacje('TuneIn', id_stacji, nazwa_stacji, stream['url'], logo, nazwa_grupy)
                        else:
                            if stream['playlist_type'] == 'pls':
                                m3usy = self.parse_pls(stream['url'])
                            elif stream['playlist_type'] == 'm3u':
                                m3usy = self.parse_m3u(stream['url'])
                            elif stream['playlist_type'] == 'asx':
                                m3usy = self.parse_m3u(stream['url'])
                                THutils.zapisz_do_logu_plik('E', 'TuneIn napotkalem na rozszerzenie ASX. Link: ' + str(
                                    stream['url']))
                            else:
                                THutils.zapisz_do_logu_plik('E','TuneIn napotkalem na rozszerzenie inne niz PLS czy M3U. Link: ' + str(stream))
                                m3usy.append(stream['url'])
                            if m3usy != None:
                                if len(m3usy) > 0:
                                    self.dodaj_stacje('TuneIn', id_stacji, nazwa_stacji, m3usy[0], logo, nazwa_grupy)
        return"""


    """def odczytaj_liste_stacji_tunein(self, link):
        time.sleep(20)
        lista_stacji = []
        try:
            link_grupa = self.dodaj_renderjson(link)
            result = str(urllib2.urlopen(link_grupa).read())
            js = json.JSONDecoder().decode(result)
            lista_stacji = js['body']
        except (urllib2.URLError, urllib2.HTTPError) as serr:
            THutils.zapisz_do_logu_plik('E', 'Blad podczas odczytu listy stacji tunein. Link: ' + link + ' Blad: ' + str(serr))
        return lista_stacji"""

    """def dodaj_stacje_tunein(self):
        API_URL = "http://opml.radiotime.com/?partnerid=HyzqumNX"
        m_link = self.znajdz_link(API_URL, 'Music')
        muzyka = self.odczytaj_xml(m_link)  # lista grup
        if muzyka == None:
            return
        for grupy in muzyka.getiterator('outline'):  # po grupach
            nazwa_grupy = grupy.get('text')
            stacje = self.odczytaj_xml(grupy.get('URL'))  # lista stacji w ramach grupy
            if stacje == None:
                return
            rodzaje = stacje.find('body')
            for rodzaj in rodzaje:  # po stacjach w ramach grupy, wybieramy rodzaj Stattions tylko
                if rodzaj.get('key') == 'stations':
                    lista_stacji = rodzaj
            for st in lista_stacji:
                if st.get('type') == 'audio':
                    link_stacji = st.get('URL')
                    nazwa_stacji = st.get('text')
                    id_stacji = st.get('guide_id')
                    logo = st.get('image')
                    #if nazwa_grupy == 'College Radio':
                    try:
                        ur = urllib2.Request(link_stacji)
                        f = urllib2.urlopen(ur)
                    except (urllib2.HTTPError) as serr:
                        THutils.zapisz_do_logu_plik('E', 'Blad podczas odczytywania listy streamow. Link: ' + str(link_stacji) + 'Blad: ' + str(serr))
                    m3usy = []
                    for stream in f:
                        stream = stream.rsplit()[0]
                        (filepath, filename) = os.path.split(stream)
                        (shortname, extension) = os.path.splitext(filename)
                        #filepath = filepath.lower()
                        #filename = filename.lower()
                        #shortname = shortname.lower()
                        extension = extension.lower()
                        if extension == '.pls':
                            m3usy = self.parse_pls(stream)
                        elif extension == '.m3u':
                            m3usy = self.parse_m3u(stream)
                        elif extension == '.asx':
                            THutils.zapisz_do_logu_plik('E','TuneIn napotkalem na rozszerzenie ASX. Link: ' + str(stream))
                        else:
                            #THutils.zapisz_do_logu_plik('E','TuneIn napotkalem na rozszerzenie inne niz PLS czy M3U. Link: ' + str(stream))
                            m3usy.append(stream)
                    f.close()
                    if m3usy != None:
                        if len(m3usy) > 0:
                            self.dodaj_stacje('TuneIn', id_stacji, nazwa_stacji, m3usy[0], logo, nazwa_grupy )
        return"""
