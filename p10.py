#!/usr/bin/python
import THutils
import constants
import os
import sys
import firebasenotification
import wejsciawyjscia
import threading
import petlaczasowa
#from jsonrpclib.SimpleJSONRPCServer import PooledJSONRPCServer
import pyjsonrpc
#from jsonrpclib.threadpool import ThreadPool

PIN_PRZERWANIA_MCP = 12

class RequestHandlerDlaJSONRPC(pyjsonrpc.HttpRequestHandler):

    def log_message(self, format, *args):
        return

    def weryfikuj_apki_key(self, key):
        if key == API_KEY:
            return None
        else:
            return THutils.skonstruuj_odpowiedzV2_NOK(str('Podane APIKEY: ' + key + ' jest nieprawidlowe.'))

    @pyjsonrpc.rpcmethod
    def oswi(self, komenda, parametr1, parametr2, apikey=''):
        wer = self.weryfikuj_apki_key(apikey)
        if wer is not None:
            return wer
        return oswietlenie.procesuj_polecenie(komenda, parametr1, parametr2)
        

    @pyjsonrpc.rpcmethod
    def stat(self, komenda, parametr1, parametr2, apikey=''):
        wer = self.weryfikuj_apki_key(apikey)
        if  wer is not None:
            return wer
        global status_naglosnienia
        global status_wzmacniaczy
        if moje_ip == os.getenv(constants.IP_GARAZ):
            if komenda == constants.KOMENDA_STAT_RESET_GARAZ:
                odp = resetuj()
            elif komenda == constants.KOMENDA_STAT_RESET_STRYCH:
                odp = THutils.przekaz_polecenie_V2_JSONRPC(constants.get_HOST_I_PORT_STRYCH_v2(),
                                                           constants.OBSZAR_STAT, komenda, parametr1, parametr2,
                                                           logger=logger)
            elif komenda == constants.RODZAJ_KOMUNIKATU_STAN_OSWIETLENIA:
                odp = THutils.skonstruuj_odpowiedzV2OK(komenda, oswietlenie.get_biezacy_stan())
            elif komenda == constants.RODZAJ_KOMUNIKATU_STAN_STEROWANIA:
                odp = THutils.skonstruuj_odpowiedzV2OK(komenda, sterowanie.stan_sterowania)
            elif komenda == constants.RODZAJ_KOMUNIKATU_STAN_PODLEWANIA:
                odp = THutils.skonstruuj_odpowiedzV2OK(komenda, podlewaj.get_biezacy_stan())
            elif komenda == constants.RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA:
                if len(status_naglosnienia) == 0:
                    odp = THutils.przekaz_polecenie_V2_JSONRPC(constants.get_HOST_I_PORT_STRYCH_v2(),
                                                               constants.OBSZAR_STAT, komenda, parametr1, parametr2)
                else:
                    odp = THutils.skonstruuj_odpowiedzV2OK(komenda, status_naglosnienia)
            elif komenda == constants.RODZAJ_KOMUNIKATU_STAN_WZMACNIACZE:
                if len(status_wzmacniaczy) == 0:
                    odp = THutils.przekaz_polecenie_V2_JSONRPC(constants.get_HOST_I_PORT_STRYCH_v2(),
                                                               constants.OBSZAR_STAT, komenda, parametr1, parametr2)
                else:
                    odp = THutils.skonstruuj_odpowiedzV2OK(komenda, status_wzmacniaczy)
            elif komenda == constants.RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA_PUSH_ZE_STRYCHU_NAGLOSN:
                status_naglosnienia = parametr1
                odp = THutils.skonstruuj_odpowiedzV2OK(constants.RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA,
                                                       constants.STATUS_OK)
                if parametr2 == constants.PARAMETR_JEDEN:
                    wyslij_firebase_ze_statusem(constants.RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA, status_naglosnienia)
            elif komenda == constants.RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA_PUSH_ZE_STRYCHU_WZMACN:
                status_wzmacniaczy = parametr1
                odp = THutils.skonstruuj_odpowiedzV2OK(constants.RODZAJ_KOMUNIKATU_STAN_WZMACNIACZE,
                                                       constants.STATUS_OK)
                #if parametr2 == constants.PARAMETR_JEDEN:
                #    wyslij_firebase_ze_statusem(constants.RODZAJ_KOMUNIKATU_STAN_WZMACNIACZE, status_wzmacniaczy)
            elif komenda == constants.RODZAJ_KOMUNIKATU_STAN_TEMPERATURY:
                odp = THutils.skonstruuj_odpowiedzV2OK(komenda, temper.get_biezacy_stan())
            elif komenda == constants.RODZAJ_KOMUNIKATU_STATUS_SKROCONY:
                odp = wyslij_status_skrocony()
            elif komenda == constants.KOMENDA_STAT_POBIERZ_LOG:
                na = THutils.przekaz_polecenie_V2_JSONRPC(constants.get_HOST_I_PORT_STRYCH_v2(), constants.OBSZAR_STAT,
                                                          komenda, parametr1, parametr2, logger=logger)
                od = {constants.SEKCJA_LOG_GARAZ: odczytaj_log(komenda, parametr1, parametr2)[constants.RESULT],
                       constants.SEKCJA_LOG_NAGLOSNIENIE: na[constants.RESULT]}
                odp =  THutils.skonstruuj_odpowiedzV2OK(constants.RODZAJ_KOMUNIKATU_STAN_LOG, od)
            elif komenda == 'wysylanie_firebase':
                if parametr1 == constants.PARAMETR_WLACZ:
                    zapisz = True
                else:
                    zapisz = False
                THutils.zapisz_parametr_konfiguracji(constants.OBSZAR_KONFIGURACJI_OGOLNE, 'wysylanie_firebase', zapisz, logger)
            else:
                odp = wyslij_status_skrocony()
        else:
            if komenda == constants.KOMENDA_STAT_RESET_STRYCH:
                odp = resetuj()
            elif komenda == constants.RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA:
                odp = naglosnienie.biezacy_stan.biezacy_stan_odpowiedzV2()
            elif komenda == constants.RODZAJ_KOMUNIKATU_STAN_WZMACNIACZE:
                odp = naglosnienie.biezacy_stan.wzmacniacze_stan_odpowiedzV2()
            elif komenda == constants.KOMENDA_STAT_POBIERZ_LOG:
                odp = odczytaj_log(komenda, parametr1, parametr2)
            else:
                odp = naglosnienie.biezacy_stan.biezacy_stan_odpowiedzV2()
        return odp


    @pyjsonrpc.rpcmethod
    def ster(self, komenda, parametr1, parametr2, apikey=''):
        wer = self.weryfikuj_apki_key(apikey)
        if wer is not None:
            return wer
        return sterowanie.procesuj_polecenie(komenda, parametr1, parametr2)

    @pyjsonrpc.rpcmethod
    def podl(self, komenda, parametr1, parametr2, apikey=''):
        wer = self.weryfikuj_apki_key(apikey)
        if wer is not None:
            return wer
        return podlewaj.procesuj_polecenie(komenda, parametr1, parametr2)

    @pyjsonrpc.rpcmethod
    def temp(self, komenda, parametr1, parametr2, apikey=''):
        wer = self.weryfikuj_apki_key(apikey)
        if wer is not None:
            return wer
        return temper.procesuj_polecenie(komenda, parametr1, parametr2)

    @pyjsonrpc.rpcmethod
    def nagl(self, komenda, parametr1, parametr2, apikey=''):
        wer = self.weryfikuj_apki_key(apikey)
        if wer is not None:
            return wer
        if moje_ip == os.getenv(constants.IP_GARAZ):
            odp = THutils.przekaz_polecenie_V2_JSONRPC(constants.get_HOST_I_PORT_STRYCH_v2(), constants.OBSZAR_NAGL,
                                                       komenda, parametr1, parametr2, logger=logger)
        else:
            odp = naglosnienie.procesuj_polecenie(komenda, parametr1, parametr2)
        return odp


def resetuj():
    logger.info('Resetuje program....')
    os.execv('sudo',  os.path.realpath(__file__) + constants.PLIK_RESETU)
    #httpd.server_close()
    #time.sleep(5)
    #logger.info('Resetuje program. Uruchamiam ponownie ...')
    #os.execv('sudo ' + constants.KATALOG_GLOWNY + '/odpal.sh')
    #os.execv(__file__, sys.argv)
    return 'RESET'

def wyslij_firebase_ze_statusem(rodzaj_komunikatu, dane):
    if firebase_mozna_wysylac:
        #TODO uwaga dane nie sa wysylane tylko 'blabla'
        threading.Thread(target=notyfikacja_firebase.notify,
                         args=(THutils.skonstruuj_odpowiedzV2OK(rodzaj_komunikatu, "blabla"),)).start()
    a = THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_KONFIGURACJI_OGOLNE, constants.LOGUJ_FIREBASE)
    if a in ['True', 'true', 'TRUE']:
        logger.info('Wyslalem firebase ' + str(rodzaj_komunikatu) + ': ' + str(dane))
    return

# ---------------------------------------------
# - wyslanie statusu zlozonego
# ---------------------------------------------
#def wyslij_status_zlozony(self):
#    return THutils.skonstruuj_odpowiedzV2(constants.RODZAJ_KOMUNIKATU_STATUS_ZLOZONY, self.status_zlozony,
#                                          constants.STATUS_OK)

def wyslij_status_skrocony():
    tsnagl = tsradii = tsplaylisty = tsulub = tshistorii = tswzmac = 0
    try:
        tsnagl = status_naglosnienia[constants.POLE_TIMESTAMP_NAGLOSNIENIA]
        tsradii = status_naglosnienia[constants.POLE_TIMESTAMP_RADII]
        tsplaylisty = status_naglosnienia[constants.POLE_TIMESTAMP_PLAYLISTY]
        tshistorii = status_naglosnienia[constants.POLE_TIMESTAMP_HISTORII]
        tsulub = status_naglosnienia[constants.POLE_TIMESTAMP_ULUBIONYCH]
        tswzmac = status_naglosnienia[constants.POLE_TIMESTAMP_WZMACNIACZY]
    except (KeyError, TypeError) as serr:
        logger.warning('Nie moge odczytac statusu z naglosnienia, zmienna nie ustawiona: ' + str(serr))
    stat_prosty = {constants.POLE_TIMESTAMP_NAGLOSNIENIA: tsnagl,
                   constants.POLE_TIMESTAMP_RADII: tsradii,
                   constants.POLE_TIMESTAMP_ULUBIONYCH: tsulub,
                   constants.POLE_TIMESTAMP_HISTORII: tshistorii,
                   constants.POLE_TIMESTAMP_PLAYLISTY: tsplaylisty,
                   constants.POLE_TIMESTAMP_PODLEWANIA: podlewaj.ts,
                   constants.POLE_TIMESTAMP_STEROWANIA: sterowanie.ts,
                   constants.POLE_TIMESTAMP_TEMPERATURY: temper.ts,
                   constants.POLE_TIMESTAMP_OSWIETLENIA: oswietlenie.ts,
                   constants.POLE_TIMESTAMP_WZMACNIACZY: tswzmac}
    return THutils.skonstruuj_odpowiedzV2OK(constants.RODZAJ_KOMUNIKATU_STATUS_SKROCONY, stat_prosty)
# ---------------------------------------------
# - Obsluga statusu garaz
# ---------------------------------------------
'''def obsluga_statusu_garaz(self):
    odp = {}
    try:
        odp = {constants.OBSZAR_TEMP:self.temperatura.zwroc_temperatury(),
               constants.OBSZAR_OSWI:self.oswietlenie.stan_oswietlenia,
               constants.OBSZAR_STER:self.sterowanie.stan_sterowania,
               constants.OBSZAR_PODL:self.podlewaj.stan_podlewania}
    except ValueError as serr:
        self.logger.warning('Nie da sie przetworzyc obslugi garazu JSON: ' + str(serr))
    return odp'''

def zapytaj_o_status_strychu(rodzaj_komunikatu):
    odp = THutils.przekaz_polecenie_V2_JSONRPC(constants.get_HOST_I_PORT_STRYCH_v2(),
                                               constants.OBSZAR_STAT, rodzaj_komunikatu,
                                               constants.PARAMETR_ZERO, constants.PARAMETR_ZERO,
                                               logger=logger)
    wynik = ''
    try:
        wynik = odp[constants.RESULT]
    except Exception as serr:
        logger.error('Nie moge odczytac statusu ze strychu: ' + str(serr))
    return wynik
# ---------------------------------------------
# - Obsluga statusu zlozonego, tylko do wykorzystania w garazu
# ---------------------------------------------
'''def aktualizuj_status_zlozony_cyklicznie(self):
    self.aktualizuj_status_zlozony()
    threading.Timer(self.czas_odswiezania_statusu_zlozonego, self.aktualizuj_status_zlozony_cyklicznie).start()
    return

def aktualizuj_status_zlozony(self):
    aa = {constants.KOMENDA: constants.RODZAJ_KOMUNIKATU_STATUS_ZLOZONY,
          constants.PARAMETR1: constants.PARAMETR_ZERO, constants.PARAMETR2: constants.PARAMETR_ZERO}
    tu = {'method': constants.OBSZAR_STAT, 'params': aa,
          "jsonrpc": "2.0", "id": 1}
    try:
        nag = requests.post(constants.HOST_I_PORT_STRYCH_v2, json=tu)
        nag = json.loads(nag.text)[constants.RESULT]
        nag = nag[constants.RESULT]
        self.ts_nagl = nag[constants.POLE_TIMESTAMP_NAGLOSNIENIA]
    except:
        e = sys.exc_info()[0]
        self.logger.warning('Nie moge odczytac statusu ze strychu: ' + str(e))
        nag = ''
    stat_zloz = self.obsluga_statusu_garaz()
    if nag != '':
        stat_zloz.update({constants.OBSZAR_NAGL: nag})
    self.status_zlozony = stat_zloz'''

def odczytaj_log(komenda, parametr1, parametr2):
    plik_logu = THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_KONFIGURACJI_OGOLNE, 'PLIK_LOGU', None)
    zawartosc_log = THutils.odczytaj_log_plik(plik_logu, int(parametr1))
    odp = []
    for x in zawartosc_log:
        odp.append(x.rstrip())
    return {constants.RODZAJ_KOMUNIKATU: constants.RODZAJ_KOMUNIKATU_STAN_LOG, constants.RESULT: odp}


'''    # ---------------------------------------------
# - przekazanie requestu i zwrotka do/z strychu, dzial tylko w garazu
# ---------------------------------------------
def przekaz_na_strych_V2_JSONRPC(self, obszar, komenda, parametr1, parametr2, logger=None):
    na = {}
    try:
        aa = {constants.KOMENDA: komenda, constants.PARAMETR1: parametr1, constants.PARAMETR2: parametr2}
        tu = {'method': obszar, 'params': aa,
              "jsonrpc": "2.0", "id": 1}

        na = requests.post(constants.HOST_I_PORT_STRYCH_v2, json=tu)
        na = json.loads(na.text)[constants.RESULT]
        #na = json.loads(na)
    except:
        e = sys.exc_info()[0]
        if logger:
            logger.warning('Blad przy przekazywaniu na strych: ' + str(e) + ': obszar, kome par1 par2: ' +
                                str(obszar) + ' ' + str(komenda) + ' ' +
                                str(parametr1 + ' ' + str(parametr2)))
    return na
'''



print 'Zaczynamy ...'

from dotenv import load_dotenv
load_dotenv()

reload(sys)
sys.setdefaultencoding('utf-8')

plik_logu = THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_KONFIGURACJI_OGOLNE, 'PLIK_LOGU', None)
logger = THutils.ustaw_loggera(constants.NAZWA_LOGGERA, plik_logu)

logger.info("Rozpoczynam program glowny.")
moje_ip = THutils.moje_ip('eth0')
czas_odswiezania_statusu_zlozonego = int(THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_KONFIGURACJI_OGOLNE,
                                                                                'CZAS_ODSWIEZANIA_STATUSU_ZLOZONEGO',
                                                                                logger))
# NAZWA_PLIKU_IC = THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_OGOLNE, 'NAZWA_PLIKU_IC', self.logger)

# Setup the notification and request pools
# nofif_pool = ThreadPool(max_threads=10, min_threads=0)
'''request_pool = ThreadPool(max_threads=50, min_threads=15, logname=constants.NAZWA_LOGGERA)


# Don't forget to start them
#nofif_pool.start()
request_pool.start()
#self.rpcserwer = PooledJSONRPCServer((self.moje_ip, constants.PORT_SERWERA_V2),
#                                logRequests=False)
self.rpcserwer = PooledJSONRPCServer((self.moje_ip, constants.PORT_SERWERA_V2), thread_pool=request_pool,
                                logRequests=False)
self.rpcserwer.timeout = 10'''


if moje_ip == os.getenv(constants.IP_GARAZ):
    import podlewanie
    from oswietlenie import Oswietlenie
    from temperatura import temperatura
    import sterowanie

    notyfikacja_firebase = firebasenotification.Firebasenotification()
    wewy = wejsciawyjscia.WejsciaWyjscia(wejsca=True, wyjscia=True)
    petla = petlaczasowa.PetlaCzasowa(logger=logger)
    firebase_mozna_wysylac = False
    status_naglosnienia = zapytaj_o_status_strychu(constants.RODZAJ_KOMUNIKATU_STAN_NAGLOSNIENIA)
    status_wzmacniaczy = zapytaj_o_status_strychu(constants.RODZAJ_KOMUNIKATU_STAN_WZMACNIACZE)
    temper = temperatura(wewy, petla, firebase_callback=wyslij_firebase_ze_statusem)
    oswietlenie = Oswietlenie(wewy, petla, firebase_callback=wyslij_firebase_ze_statusem)
    podlewaj = podlewanie.Podlewanie(wewy, petla, firebase_callback=wyslij_firebase_ze_statusem)
    sterowanie = sterowanie.Sterowanie(wewy, petla, firebase_callback=wyslij_firebase_ze_statusem)
    petla.petlaStart()
    '''self.rpcserwer.register_function(self.oswi)
    self.rpcserwer.register_function(self.ster)
    self.rpcserwer.register_function(self.podl)
    self.rpcserwer.register_function(self.temp)
    self.rpcserwer.register_function(self.stat)
    self.rpcserwer.register_function(self.nagl)'''
    a = THutils.odczytaj_parametr_konfiguracji(constants.OBSZAR_KONFIGURACJI_OGOLNE, 'wysylanie_firebase')
    if a in ['True', 'true', 'TRUE']:
        firebase_mozna_wysylac = True
else:
    import naglosnienie
    wewy = wejsciawyjscia.WejsciaWyjscia(wyjscia=True)
    #mcp_wyjscie1 = Adafruit_MCP230xx.Adafruit_MCP230XX(address=0x20, num_gpios=16)
    naglosnienie = naglosnienie.Naglosnienie(wewy)
    '''self.rpcserwer.register_function(self.nagl)
    self.rpcserwer.register_function(self.stat)'''

try:
    '''self.rpcserwer.serve_forever()
    '''
    API_KEY = os.getenv(constants.APIKEY)
    http_server = pyjsonrpc.ThreadingHttpServer(
        server_address=(moje_ip, int(os.getenv(constants.PORT_SERWERA_V2))),
        RequestHandlerClass=RequestHandlerDlaJSONRPC)

    print "Starting HTTP server ..."
    http_server.serve_forever()
except:
    e = sys.exc_info()[0]
    logger.warning('Nieobslugiwany blad servera: ' + str(e))





