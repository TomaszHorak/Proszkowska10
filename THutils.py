#!/usr/bin/python

import MySQLdb
import constants
import socket
import fcntl
import struct
import datetime
import json
import os
import logging
import logging.handlers
from multiprocessing.connection import Client
import configparser
import requests
import sys

#TODO plik logi chyba trzeba przerobic na logger
# PLIK_LOGU = '/home/pi/python/system_podlewania/mysocket.log'
PLIK_CONFIGU = '/config.ini'
HOST_BAZY_DANYCH = "192.168.5.99"

def ustaw_loggera(nazwaloggera, plik_logu):
    logger = logging.getLogger(nazwaloggera)
    formatter = logging.Formatter('%(asctime)-15s %(levelname)-8s %(message)s')
    logger.setLevel(logging.DEBUG)
    filehandler = logging.handlers.RotatingFileHandler(plik_logu, maxBytes=1000000, backupCount=50)
    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)
    return logger

def zapisz_parametr_konfiguracji(nazwa_sekcji, nazwa_parametru, wartosc, logger=None):
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(os.path.dirname(os.path.realpath(__file__)) + PLIK_CONFIGU)
    try:
        config.set(nazwa_sekcji, nazwa_parametru, str(wartosc))
        with open(os.path.dirname(os.path.realpath(__file__)) + PLIK_CONFIGU, 'wb') as configfile:
            config.write(configfile)
        configfile.close()
    except(KeyError,configparser.NoOptionError, configparser.NoSectionError) as e:
        if logger is not None:
            logger.warning('Nie moge zaktualizowac parametru w konfiguracji. Sekcja: ' + nazwa_sekcji +
                           ' Parametr: ' + nazwa_parametru + ' Wartosc: ' + str(wartosc))
        return
    #if logger is not None:
#        logger.info('Zaktualizowalem parametr w konfiguracji. Sekcja: ' + nazwa_sekcji +
#                           ' Parametr: ' + nazwa_parametru + ' Wartosc: ' + str(wartosc))
    #TODO uzyc tej funkcji tam gdzie potrzeba przejrzec caly kod
    return

def skonstruuj_odpowiedzV2(rodzaj_komunikatu, result, status):
    return {constants.RODZAJ_KOMUNIKATU: rodzaj_komunikatu,
            constants.RESULT: result,
            constants.STATUS: status}

    # ---------------------------------------------
    # - przekazanie requestu i zwrotka do/z strychu, dzial tylko w garazu
    # ---------------------------------------------
def przekaz_polecenie_V2_JSONRPC(adres, obszar, komenda, parametr1, parametr2, logger=None):
    na = {}
    nas = ''
    try:
        aa = {constants.KOMENDA: komenda, constants.PARAMETR1: parametr1, constants.PARAMETR2: parametr2}
        tu = {'method': obszar, 'params': aa,
              "jsonrpc": "2.0", "id": 1}

        na = requests.post(adres, json=tu)
        nas = json.loads(na.text)[constants.RESULT]
    except:
        e = sys.exc_info()[0]
        if logger:
            logger.warning('Blad przy przekazywaniu do ' + adres + '. Blad: ' + str(e) + ': obszar, kome par1 par2: ' +
                                str(obszar) + ' ' + str(komenda) + ' ' +
                                str(parametr1 + ' ' + str(parametr2)))
    return nas

def odczytaj_parametr_konfiguracji(nazwa_sekcji, nazwa_parametru, logger=None):
    config = configparser.ConfigParser()
    config.read(os.path.dirname(os.path.realpath(__file__)) + PLIK_CONFIGU)
    zwrotka = ''
    try:
        zwrotka = config.get(nazwa_sekcji, nazwa_parametru)
    except (KeyError,configparser.NoOptionError, configparser.NoSectionError) as e:
        if logger is not None:
            logger.warning('Nie moge odczytac z konfiguracji parametru: ' + nazwa_parametru)
    return zwrotka

def odczytaj_temp_z_socketa():
    PORT_LOKALNY = 6050
    templ = ""
    try:
        addresso = ('localhost', PORT_LOKALNY)
        conno = Client(addresso, authkey='secret password')
        conno.send('TEMP')
        templ = conno.recv()
        conno.close()
        return templ
    except Exception, e:
        # zapisz_do_logu_plik('E', 'Exception przy odczycie temperatury z socketa: ' + str(e))
        return templ

def zwroc_baze():
    try:
        my_db = MySQLdb.connect(host=HOST_BAZY_DANYCH, user="root", passwd="west1west1", db="stacja_pogodowa")
        return my_db
    except MySQLdb, e:
        print "Blad podlaczenia do bazy"
        return None


def odczytaj_cala_tabele(nazwa_tabeli):
    try:
        db = zwroc_baze()
        cur = db.cursor()
        statement = "SELECT * FROM " + nazwa_tabeli
        # cur.execute("""SELECT * FROM %s""", (nazwa_tabeli))
        cur.execute(statement)
        result = cur.fetchall()
        cur.close()
        db.close()
        return result
    except Exception, e:
        return None


def odczytaj_konfiguracje_z_bazy_druga_wartosc(obszar, parametr):
    try:
        db = zwroc_baze()
        cur = db.cursor()
        cur.execute("""SELECT wartosc2 FROM stacja_pogodowa.konfiguracja WHERE obszar = %s AND parametr = %s""",
                    (obszar, parametr))
        result = cur.fetchone()
        cur.close()
        db.close()
        return result[0]
    except Exception, e:
        return ""

def godziny_minuty_sekundy_z_sekund(sekundy):
    sek = sekundy % (24 * 3600)
    hou = sek // 3600
    sek %= 3600
    minu = sek // 60
    sek %= 60
    return int(hou), int(minu), int(sek)

def odczytaj_ulubione_z_bazy():
    try:
        db = zwroc_baze()
        cur = db.cursor()
        cur.execute("""SELECT nr, nazwa, link, typ FROM stacja_pogodowa.naglo_ulubione""")
        result = cur.fetchall()
        cur.close()
        db.close()
        return result
    except Exception, e:
        return ""


def odczytaj_konfiguracje_z_bazy(obszar, parametr):
    try:
        db = zwroc_baze()
        cur = db.cursor()
        cur.execute("""SELECT wartosc FROM stacja_pogodowa.konfiguracja WHERE obszar = %s AND parametr = %s""",
                    (obszar, parametr))
        result = cur.fetchone()
        cur.close()
        db.close()
        return result[0]
    except Exception, e:
        return ""


def odczytaj_cala_konfiguracje_z_bazy():
    try:
        db = zwroc_baze()
        cur = db.cursor()
        cur.execute("""SELECT obszar, parametr, wartosc, wartosc2 FROM stacja_pogodowa.konfiguracja""")
        result = cur.fetchall()
        cur.close()
        db.close()
        return result
    except Exception, e:
        return ""


def wyslij_konfiguracje():
    config = configparser.ConfigParser()
    config.read(os.path.dirname(os.path.realpath(__file__)) + PLIK_CONFIGU)
    sekcje = config.sections()
    pozycje = []
    for option in sekcje:
        odp = config.items(option)
        for poz in odp:
            pozycja = {'Obszar': option,
                       'Parametr': poz[0],
                       'Wartosc1': poz[1],
                       'Wartosc2': ''}
            pozycje.append(pozycja)
    odpo = json.dumps({'Konfiguracja':pozycje})
    return odpo

def wyslij_konfiguracje_z_bazy():
    konf = odczytaj_cala_konfiguracje_z_bazy()
    pozycje = []
    for a in konf:
        pozycja = {'Obszar': a[0],
                   'Parametr': a[1],
                   'Wartosc1': a[2],
                   'Wartosc2': a[3]}
        pozycje.append(pozycja)
    odp = json.dumps({'Konfiguracja':pozycje})
    return odp

def xstr(s):
    if s is None:
        return ''
    return str(s)


def odczytaj_biezaca_temperature_z_bazy():
    try:
        # print "odczytue temperature"
        # threading.Timer(200, self.odczytaj_biezaca_temperature_z_bazy).start()
        # db = MySQLdb.connect(host="localhost", user="root", passwd="west1west1", db="stacja_pogodowa")
        db = zwroc_baze()
        cur = db.cursor()
        cur.execute(
            """SELECT * FROM stacja_pogodowa.temperatura WHERE timestamp IN (SELECT max(timestamp) FROM stacja_pogodowa.temperatura)""")
        result = cur.fetchone()
        # print "byLO: " + str(self.temp) + "  i wilgotnosc " + str(self.wilg)
        # self.temp = result[2]
        # self.wilg = result[5]  # odczytujemy wilgotnosc gleby a nie wilgotnosc powietrza
        # print "jest: " + str(self.temp) + "  i wilgotnosc " + str(self.wilg)
        cur.close()
        db.close()
        return (result[1], result[3], result[2], result[4], result[5])
    except Exception, e:
        return


'''def zapisz_do_logu_plik(kategoria, tekst):
    # kategorie: E-error, W-warning, I-information
    try:
        plik = open(PLIK_LOGU, 'a')
        tk = str(datetime.datetime.now()) + ' : ' + kategoria + ': ' + tekst
        plik.write(tk + "\n")
        plik.close()
    except IOError as serr:
        print 'Nie moge zapisac logu do pliku ...'
'''

def odczytaj_log_plik(plik, liczba_linii):
    with open(plik, 'r') as f:
        #f.seek(0, 2)
        #fsize = f.tell()
        #f.seek(max(fsize - 10240, 0), 0)
        lines = f.readlines()
    lines = lines[-liczba_linii:]
    #odp = []
    #for x in lines:
    #    odp.append(x)
    return lines


def zapisz_do_logu_baza(kto_lp, obszar_lp, kategoria_lp, wartosc_lp):
    try:
        # db = MySQLdb.connect(host="localhost", user="root", passwd="west1west1", db="stacja_pogodowa")
        db = zwroc_baze()
        cur = db.cursor()
        cur.execute("""INSERT INTO stacja_pogodowa.log(kto,obszar,kategoria, wartosc) VALUES (%s, %s, %s, %s)""",
                    (kto_lp, obszar_lp, kategoria_lp, wartosc_lp))
        db.commit()
        cur.close()
        db.close()
    except Exception, e:
        return


def odczytaj_caly_log_z_bazy():
    try:
        # db = MySQLdb.connect(host="localhost", user="root", passwd="west1west1", db="stacja_pogodowa")
        db = zwroc_baze()
        cur = db.cursor()
        cur.execute("""SELECT * FROM stacja_pogodowa.log ORDER BY czas DESC LIMIT 100""")
        result = cur.fetchall()
        cur.close()
        db.close()
        return result
    except Exception, e:
        return




def check_time(time_to_check, on_time, off_time, dzien):
    DAY, NIGHT = 1, 2

    if str(datetime.datetime.today().weekday()) not in dzien:
        return None, False

    if on_time > off_time:
        if time_to_check > on_time or time_to_check < off_time:
            return NIGHT, True
    elif on_time < off_time:
        if time_to_check > on_time and time_to_check < off_time:
            return DAY, True
    elif time_to_check == on_time:
        return None, True
    return None, False


def moje_ip(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])
