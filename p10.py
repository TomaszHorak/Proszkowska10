#!/usr/bin/python
from __future__ import print_function

import time
import THutils
import constants
import os
import sys
import firebasenotification
import wejsciawyjscia
import petlaczasowa
import sauna
import pyjsonrpc
from MojLogger import MojLogger
import requests

#PIN_PRZERWANIA_MCP = 12

class RequestHandlerDlaJSONRPC(pyjsonrpc.HttpRequestHandler):

    #potrzebne aby serwer nielogowal kazdego komunikatu w pliku err
    def log_message(self, format, *args):
        return

    def weryfikuj_apki_key(self, key):
        if key == API_KEY:
            return None
        else:
            return THutils.skonstruuj_odpowiedzV2_NOK(str('Podane APIKEY: ' + key + ' jest nieprawidlowe.'))

    @pyjsonrpc.rpcmethod
    def oswi(self, **params):
#        wer = self.weryfikuj_apki_key(apikey)
#        if wer is not None:
#            return wer
        return oswietlenie.procesuj_polecenie(**params)

    @pyjsonrpc.rpcmethod
    def sauna(self, **params):
        #        wer = self.weryfikuj_apki_key(apikey)
        #        if wer is not None:
        #            return wer
        return sauna.procesuj_polecenie(**params)

#TODO API key wylaczylem zupelnie, powrocic
    @pyjsonrpc.rpcmethod
    def ogrz(self, **params):
#        wer = self.weryfikuj_apki_key(apikey)
#        if wer is not None:
#            return wer
        return ogrzewanie.procesuj_polecenie(**params)

    @pyjsonrpc.rpcmethod
    def stat(self, **params):
#        wer = self.weryfikuj_apki_key(apikey)
#        if  wer is not None:
#            return wer
        global status_naglosnienia
        #global status_wzmacniaczy
        odp = {constants.RESULT: constants.STATUS_OK}
        if moje_ip == os.getenv(constants.IP_GARAZ):
            if constants.KOMENDA in params:
                if params[constants.KOMENDA] == constants.KOMENDA_STAT_RESET_GARAZ:
                    # odp = resetuj()
                    pass
                #TODO usuwamy przetwarzanie komunikatu status_wzmacniaczy w stat
                elif params[constants.KOMENDA] == constants.RODZAJ_KOMUNIKATU_STATUS_SKROCONY:
                    odp = wyslij_status_skrocony()
                elif params[constants.KOMENDA] == constants.RODZAJ_KOMUNIKATU_STAN_LOG_GARAZ:
                    if constants.POLE_LICZBA_LINII not in params:
                        liczba_linii = 100
                    else:
                        liczba_linii = int(params[constants.POLE_LICZBA_LINII])
                    plik_logu = THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_P10,
                                                                       'PLIK_LOGU', None)
                    od = odczytaj_log(plik_logu, liczba_linii)
                    odp = THutils.skonstruuj_odpowiedzV2OK(params[constants.KOMENDA], od, constants.OBSZAR_STAT)
                elif params[constants.KOMENDA] == constants.RODZAJ_KOMUNIKATU_STAN_LOG_TEMPERATURY:
                    if constants.POLE_LICZBA_LINII not in params:
                        liczba_linii = 100
                    else:
                        liczba_linii = int(params[constants.POLE_LICZBA_LINII])
                    plik_logu = THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_TEMP,
                                                                       'plik_logu_temp', None)
                    od = odczytaj_log(plik_logu, liczba_linii)
                    odp = THutils.skonstruuj_odpowiedzV2OK(params[constants.KOMENDA], od, constants.OBSZAR_STAT)
                elif params[constants.KOMENDA] == constants.RODZAJ_KOMUNIKATU_STAN_LOG_NAGLOSNIENIE:
                    na = przekaz_polecenie_V2_JSONRPC('http://192.168.5.92', constants.OBSZAR_NAGL, logger, params)
                    odp =  THutils.skonstruuj_odpowiedzV2OK(constants.RODZAJ_KOMUNIKATU_STAN_LOG_NAGLOSNIENIE, na, constants.OBSZAR_STAT)
                elif params[constants.KOMENDA] == constants.KOMENDA_WYSYLANIE_FIREBASE:
                    if constants.POLE_STAN in params:
                        THutils.zapisz_parametr_konfiguracji(constants.OBSZAR_P10, 'wysylanie_firebase',
                                                             params[constants.POLE_STAN], logger)
                else:
                    odp = wyslij_status_skrocony()
        else: #sekcja dla strychu
            if constants.KOMENDA in params:
                if params[constants.KOMENDA] == constants.KOMENDA_STAT_RESET_STRYCH:
                    #odp = resetuj()
                    pass
                #elif params[constants.KOMENDA] == constants.RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA:
                #    odp = naglosnienie.biezacy_stan.biezacy_stan_odpowiedzV2()
                #elif params[constants.KOMENDA] == constants.RODZAJ_KOMUNIKATU_STAN_WZMACNIACZE:
                #    odp = naglosnienie.biezacy_stan.wzmacniacze_stan_odpowiedzV2()
                elif params[constants.KOMENDA] == constants.RODZAJ_KOMUNIKATU_STAN_LOG_NAGLOSNIENIE:
                    plik_logu = THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_P10,
                                                                       'PLIK_LOGU', None)
                    if constants.POLE_LICZBA_LINII not in params:
                        liczba_linii = 100
                    else:
                        liczba_linii = int(params[constants.POLE_LICZBA_LINII])
                    od = odczytaj_log(plik_logu, liczba_linii)
                    odp = THutils.skonstruuj_odpowiedzV2OK(params[constants.KOMENDA], od, constants.OBSZAR_STAT)
                else:
                    odp = naglosnienie.biezacy_stan.biezacy_stan_odpowiedzV2()
        return odp


    @pyjsonrpc.rpcmethod
    def ster(self, **params):
        #wer = self.weryfikuj_apki_key(apikey)
        #if wer is not None:
#            return wer
        return sterowanie.procesuj_polecenie(**params)

    @pyjsonrpc.rpcmethod
    def szak(self, **params):
        # wer = self.weryfikuj_apki_key(apikey)
        # if wer is not None:
        #            return wer
        return szybkieAkcje.procesuj_polecenie(**params)

    @pyjsonrpc.rpcmethod
    def podl(self, **params):
#        wer = self.weryfikuj_apki_key(apikey)
#        if wer is not None:
#            return wer
        return podlewaj.procesuj_polecenie(**params)

    @pyjsonrpc.rpcmethod
    def temp(self, **params):
#        wer = self.weryfikuj_apki_key(apikey)
#        if wer is not None:
#            return wer
        return temper.procesuj_polecenie(**params)


    @pyjsonrpc.rpcmethod
    def nagl(self, **params):
        global status_naglosnienia
        if moje_ip == os.getenv(constants.IP_GARAZ):
            if constants.RODZAJ_KOMUNIKATU in params: #tutaj procesujemy status z strychu
                if params[constants.RODZAJ_KOMUNIKATU] == constants.RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA:
                    status_naglosnienia = params[constants.RESULT]
                    odp =  THutils.skonstruuj_odpowiedzV2OK(constants.RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA, params[constants.RESULT], constants.OBSZAR_NAGL)
            if constants.KOMENDA in params:
                odp = przekaz_polecenie_V2_JSONRPC('http://192.168.5.92', constants.OBSZAR_NAGL, logger,  params)
        else:
            odp = naglosnienie.procesuj_polecenie(**params)
        return odp

def przekaz_polecenie_V2_JSONRPC(adres, obszar, logger, params):
    # ========== konwersja ze starej wersji do flaskowej na strychu, nowe api, bez JSONRPC ==============
    na = {}
    nas = {constants.RESULT: ''}
    _logger = logger    #type: MojLogger
    komenda = ''
    if constants.KOMENDA in params:
        komenda = params[constants.KOMENDA]
    endpoint = '/getcurrentstatus'
    par = {}
    rodzaj_odpowiedzi = constants.RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA
    if komenda == constants.RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA:
        endpoint = '/getcurrentstatus'
    elif komenda == constants.KOMENDA_TOGGLE_WZMACNIACZ:
        nazwa = params[constants.NAZWA]
        if nazwa is not None:
            endpoint = '/togglewzmacniacz/' + nazwa
    elif komenda == constants.RODZAJ_KOMUNIKATU_STAN_WZMACNIACZE:
        endpoint = '/getwzmacniaczestatus'
        rodzaj_odpowiedzi = constants.RODZAJ_KOMUNIKATU_STAN_WZMACNIACZE
    elif komenda == 'GOTO':
        endpoint = '/seek/' + str(params[constants.POLE_WARTOSC])
    elif komenda == constants.KOMENDA_GLOSNOSC:
        endpoint = '/volume/' + params[constants.NAZWA] + '/' + str(params[constants.POLE_GLOSNOSC])
    elif komenda == constants.KOMENDA_GLOSNOSC_DELTA:
        endpoint = '/volumedelta/' + params[constants.NAZWA] + '/' + str(params[constants.POLE_GLOSNOSC])
    elif komenda == 'NAST':
        endpoint = '/next'
    elif komenda == 'POPR':
        endpoint = '/previous'
    elif komenda == 'PLAY':
        if constants.POLE_WARTOSC in params:
            endpoint = '/playfromcurrentplaylist/' + str(params[constants.POLE_WARTOSC])
    elif komenda == constants.RODZAJ_KOMUNIKATU_PLAYLISTA:
        endpoint = '/currentplaylist'
        rodzaj_odpowiedzi = constants.RODZAJ_KOMUNIKATU_PLAYLISTA
    elif komenda == constants.KOMENDA_DZWONEK:
        endpoint = '/dzwonek'
    elif komenda == constants.RODZAJ_KOMUNIKATU_STAN_LOG_NAGLOSNIENIE:
        if constants.POLE_LICZBA_LINII not in params:
            liczba_linii = 100
        else:
            liczba_linii = int(params[constants.POLE_LICZBA_LINII])
        endpoint = '/getlog/' + str(liczba_linii)
        rodzaj_odpowiedzi = constants.RODZAJ_KOMUNIKATU_STAN_LOG_NAGLOSNIENIE
    elif komenda == constants.RODZAJ_KOMUNIKATU_ULUBIONE:
        endpoint = '/getfavourites'
        rodzaj_odpowiedzi = constants.RODZAJ_KOMUNIKATU_ULUBIONE
    elif komenda == constants.RODZAJ_KOMUNIKATU_KATALOG_RADII:
        endpoint = '/getradios'
        rodzaj_odpowiedzi = constants.RODZAJ_KOMUNIKATU_KATALOG_RADII
    elif komenda == 'refreshfavourites':
        endpoint = '/refreshfavourites'
        rodzaj_odpowiedzi = constants.RODZAJ_KOMUNIKATU_ULUBIONE
    elif komenda == 'queryradios':
        if constants.POLE_WARTOSC in params:
            endpoint = '/queryradios/' + str(params[constants.POLE_WARTOSC])
            rodzaj_odpowiedzi = 'queryradios'
    elif komenda == 'playitem':
        if constants.POLE_WARTOSC in params:
            endpoint = '/playitem'
            par = {constants.POLE_WARTOSC : str(params[constants.POLE_WARTOSC])}
    elif komenda == 'ULUB':
        endpoint = '/playfavourite'
        if constants.POLE_WARTOSC in params:
            par = {constants.POLE_WARTOSC : int(params[constants.POLE_WARTOSC])}
        if constants.NAZWA in params:
            par = {constants.NAZWA: params[constants.NAZWA]}
    elif komenda == 'ODTWARZAJ_SPOTIFY':
        #import urllib
        #arg = urllib.quote(str(params[constants.POLE_WARTOSC]), safe='')
        endpoint = '/playspotifylink'
        par = {constants.POLE_WARTOSC: str(params[constants.POLE_WARTOSC])}
    else:
        endpoint = '/getcurrentstatus'
    #_logger.warning(obszar, 'stat', 'Przekazuje do strychu ' + adres + endpoint + ' ' + str(params))
    try:
        na = requests.get(adres+endpoint, params=par).json() #post(adres, json=tu).json()
        #_logger.warning(obszar, 'stat', 'Odpowiedz ze strychu ' + ' ' + str(na))
        #nas = na[constants.RESULT]
    except:
        e = sys.exc_info()[0]
        if logger:
            _logger.warning(obszar, 'stat', 'Blad przy przekazywaniu do ' + adres + endpoint +
                          '. Blad: ' + str(e) + ': obszar, kome parms: ' + str(obszar) + ' ' + str(params))
    return THutils.skonstruuj_odpowiedzV2OK(rodzaj_odpowiedzi, na, obszar)



def resetuj():
    logger.info("P10", 'status', 'Resetuje program....')
    os.execv('sudo',  os.path.realpath(__file__) + constants.PLIK_RESETU)
    #httpd.server_close()
    #time.sleep(5)
    #logger.info('Resetuje program. Uruchamiam ponownie ...')
    #os.execv('sudo ' + constants.KATALOG_GLOWNY + '/odpal.sh')
    #os.execv(__file__, sys.argv)
    return 'RESET'

def wyslij_firebase_ze_statusem(rodzaj_komunikatu, dane):
    if THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_P10, 'wysylanie_firebase') in ['True', 'true', 'TRUE']:
        #TODO uwaga dane nie sa wysylane tylko 'blabla'
        #threading.Thread(target=notyfikacja_firebase.notify,
        #                 args=(THutils.skonstruuj_odpowiedzV2OK(rodzaj_komunikatu, "blabla"),)).start()
        #notyfikacja_firebase.notify(THutils.skonstruuj_odpowiedzV2OK(rodzaj_komunikatu, "blabla", ''))
        #sprawdzamy, ktory TS jest najnowszy i go wysylamy
        #global najnowszy_ts
        statpr = generuj_stat_prosty()
        if THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_P10, constants.LOGUJ_FIREBASE) in ['True', 'true',
                                                                                                      'TRUE']:
            # logger.info(constants.OBSZAR_P10, 'Wyslalem firebase ' + str(rodzaj_komunikatu) + ': ' + str(dane))
            logger.info(constants.OBSZAR_P10, 'Wyslalem firebase ' + str(statpr))
        #notyfikacja_firebase.notify(najnowszy_ts)
        notyfikacja_firebase.notify(statpr)

    return

# ---------------------------------------------
# - wyslanie statusu zlozonego
# ---------------------------------------------
#def wyslij_status_zlozony(self):
#    return THutils.skonstruuj_odpowiedzV2(constants.RODZAJ_KOMUNIKATU_STATUS_ZLOZONY, self.status_zlozony,
#                                          constants.STATUS_OK)

def wyslij_status_skrocony():
    return THutils.skonstruuj_odpowiedzV2OK(constants.RODZAJ_KOMUNIKATU_STATUS_SKROCONY, generuj_stat_prosty(), constants.OBSZAR_STAT)

def generuj_stat_prosty():
    global status_naglosnienia
    tsnagl = tsradii = tsplaylisty = tsulub = tshistorii = 0
    try:
        tsnagl = status_naglosnienia[constants.POLE_TIMESTAMP_NAGLOSNIENIA]
        tsradii = status_naglosnienia[constants.POLE_TIMESTAMP_RADII]
        tsplaylisty = status_naglosnienia[constants.POLE_TIMESTAMP_PLAYLISTY]
        tshistorii = status_naglosnienia[constants.POLE_TIMESTAMP_HISTORII]
        tsulub = status_naglosnienia[constants.POLE_TIMESTAMP_ULUBIONYCH]
    except (KeyError, TypeError) as serr:
        logger.warning(constants.OBSZAR_P10, 'stat',
                       'Nie moge odczytac statusu z naglosnienia, zmienna nie ustawiona: ' + str(serr))

    stat_prosty = {constants.POLE_TIMESTAMP_NAGLOSNIENIA: tsnagl,
                   constants.POLE_TIMESTAMP_RADII: tsradii,
                   constants.POLE_TIMESTAMP_ULUBIONYCH: tsulub,
                   constants.POLE_TIMESTAMP_HISTORII: tshistorii,
                   constants.POLE_TIMESTAMP_PLAYLISTY: tsplaylisty,
                   constants.POLE_TIMESTAMP_PODLEWANIA: podlewaj.get_ts(),
                   constants.POLE_TIMESTAMP_STEROWANIA: sterowanie.get_ts(),
                   constants.POLE_TIMESTAMP_TEMPERATURY: temper.get_ts(),
                   constants.POLE_TIMESTAMP_OSWIETLENIA: oswietlenie.get_ts(),
                   constants.POLE_TIMESTAMP_SZAKCJI: szybkieAkcje.get_ts(),
                   constants.POLE_TIMESTAMP_OGRZEWANIA: ogrzewanie.get_ts(),
                   constants.POLE_TIMESTAMP_SAUNY: sauna.get_ts()}
    # global najnowszy_ts
    najnowszy_ts = tsnagl
    if tsradii > najnowszy_ts:
        najnowszy_ts = tsradii
    if tsulub > najnowszy_ts:
        najnowszy_ts = tsulub
    if tshistorii > najnowszy_ts:
        najnowszy_ts = tshistorii
    if tsplaylisty > najnowszy_ts:
        najnowszy_ts = tsplaylisty
    if podlewaj.get_ts() > najnowszy_ts:
        najnowszy_ts = podlewaj.get_ts()
    if sterowanie.get_ts() > najnowszy_ts:
        najnowszy_ts = sterowanie.get_ts()
    if temper.get_ts() > najnowszy_ts:
        najnowszy_ts = temper.get_ts()
    if oswietlenie.get_ts() > najnowszy_ts:
        najnowszy_ts = oswietlenie.get_ts()
    if szybkieAkcje.get_ts() > najnowszy_ts:
        najnowszy_ts = szybkieAkcje.get_ts()
    if ogrzewanie.get_ts() > najnowszy_ts:
        najnowszy_ts = ogrzewanie.get_ts()
    if sauna.get_ts() > najnowszy_ts:
        najnowszy_ts = sauna.get_ts()
    return stat_prosty

def odczytaj_log(plik_logu, liczba_wierszy):
    zawartosc_log = THutils.odczytaj_log_plik(plik_logu, int(liczba_wierszy))
    odp = []
    for x in zawartosc_log:
        odp.append(x.rstrip())
    return {constants.RODZAJ_KOMUNIKATU: constants.RODZAJ_KOMUNIKATU_STAN_LOG_GARAZ, constants.RESULT: odp}


print('Zaczynamy ...')

from dotenv import load_dotenv
load_dotenv()

reload(sys)
sys.setdefaultencoding('utf-8')

#Ignore SIG_PIPE and don't throw exceptions on it... (http://docs.python.org/library/signal.html)
#signal(SIGPIPE,SIG_DFL)

logger = MojLogger(constants.NAZWA_LOGGERA,
                   THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_P10, 'PLIK_LOGU', None))


logger.info(constants.OBSZAR_P10, 'stat', "Rozpoczynam program glowny.")
moje_ip = THutils.moje_ip('eth0')
czas_odswiezania_statusu_zlozonego = int(THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_P10,
                                                                                'CZAS_ODSWIEZANIA_STATUSU_ZLOZONEGO',
                                                                                logger))
# NAZWA_PLIKU_IC = THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_OGOLNE, 'NAZWA_PLIKU_IC', self.logger)


if moje_ip == os.getenv(constants.IP_GARAZ):
    import podlewanie
    from oswietlenie import Oswietlenie
    from temperatura import Temperatura
    from ogrzewanie import Ogrzewanie
    from szybkie_akcje import Szybkie_Akcje
    import sterowanie

    logger_temp = MojLogger(constants.NAZWA_LOGGERA_TEMPERATUR,
                            THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_TEMP, 'plik_logu_temp', None))
    najnowszy_ts = time.time() * 1000
    notyfikacja_firebase = firebasenotification.Firebasenotification(logger)
    wewy = wejsciawyjscia.WejsciaWyjscia(logger, wejsca=True, wyjscia=True)
    petla = petlaczasowa.PetlaCzasowa(logger)

    status_naglosnienia = przekaz_polecenie_V2_JSONRPC('http://192.168.5.92',
                                                       constants.OBSZAR_NAGL, logger,
                                                       {constants.KOMENDA: constants.RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA}) #THutils.zapytaj_o_status_zdalnie(constants.get_HOST_I_PORT_STRYCH_v2(), constants.OBSZAR_NAGL, constants.RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA, logger)
    if status_naglosnienia is not None:
        status_naglosnienia = status_naglosnienia[constants.RESULT]
    logger.info(constants.OBSZAR_NAGL, 'status inicjalny', 'Status uzyskany z naglosnienia przy uruchamianiu' +
                str(status_naglosnienia))
    #status_wzmacniaczy = THutils.zapytaj_o_status_zdalnie(constants.get_HOST_I_PORT_STRYCH_v2(), constants.OBSZAR_STAT, constants.RODZAJ_KOMUNIKATU_STAN_WZMACNIACZE, logger)
    oswietlenie = Oswietlenie(wewy, petla, logger, firebase_callback=wyslij_firebase_ze_statusem)
    temper = Temperatura(wewy, petla, logger, logger_temp,firebase_callback=wyslij_firebase_ze_statusem)
    podlewaj = podlewanie.Podlewanie(wewy, petla, logger, firebase_callback=wyslij_firebase_ze_statusem)
    sterowanie = sterowanie.Sterowanie(wewy, petla, logger, firebase_callback=wyslij_firebase_ze_statusem)
    sauna = sauna.Sauna(logger, petla=petla, firebase_callback=wyslij_firebase_ze_statusem)
    ogrzewanie = Ogrzewanie(wewy, petla, logger, logger_temp)

    szybkieAkcje = Szybkie_Akcje(logger)

    #startujemy przetwarzanei w obszarach
    temper.start()
    petla.petlaStart()
else:
    import naglosnienie
    naglosnienie = naglosnienie.Naglosnienie(logger)

try:
    API_KEY = os.getenv(constants.APIKEY)
    http_server = pyjsonrpc.ThreadingHttpServer(
        server_address=(moje_ip, int(os.getenv(constants.PORT_SERWERA_V2))),
        RequestHandlerClass=RequestHandlerDlaJSONRPC)

    print ("Starting HTTP server ...")
    http_server.serve_forever()
except:
    e = sys.exc_info()[0]
    logger.warning(constants.OBSZAR_P10, 'stat', 'Nieobslugiwany blad servera: ' + str(e))





