
import telnetlib
import json
from socket import error as SocketError
import threading
import logging

class Denon():

    def __init__(self, logger):
        self.heosurl = 'heos://'
        self.host = '192.168.5.60'
        self.heos_port = '1255'
        self.port = '23'
        self.pid = '-349597980'
        self.telnet_timeout = 10
        self.logger = logger
        try:
            self.telnet = telnetlib.Telnet(self.host, 1255)
        except SocketError as serr:
            self.logger.warning('Blad telenta Denon: ' + str(serr))
        #parametry Denona
        self.current_ispwon = False
        self.current_volume = '20'
        self.current_source = 'CBL/SAT'
        self.percentage = 0
        # TODO to powinno wskazywac czy gra czy nie a nie ispwon
        # self.current_isplaying = False

        """try:
            self.tel = telnetlib.Telnet(self.host, self.port, timeout=self.telnet_timeout)
            self.heos_tel = telnetlib.Telnet(self.host, self.heos_port, timeout=self.telnet_timeout)
        except SocketError as serr:
            self.logger.warning('Brak kontaktu z Denon przy inicjalizacji: ' + str(serr))"""

        #self.inicjuj_nasluchiwanie()
        #self.heos_inicjuj_nasluchiwanie()
        self.aktualizuj_stan()
        self.logger.info('Zakonczyle konstruktora klasy Denon.')
        # self.heos_get_volume()
        return

    def aktualizuj_stan(self):
        try:
            v = int(self.heos_get_volume())
            self.current_volume = v
        except TypeError as serr:
            self.logger.warning('Nie udalo sie pobrac glosnosci: ' + str(serr))
            self.current_volume = 0
        if self.heos_get_play_state() == 'play':
            self.current_ispwon = True
        else:
            self.current_ispwon = False
        """self.get_pwr_status()
        self.get_volume()
        self.get_source()"""
        return


    def heos_procesuj_odpowiedz(self, response):
        try:
            response = json.loads(response.decode("utf-8"))
        except ValueError:
            #THutils.zapisz_do_logu_plik('E', 'Odpowiedz Denona nie moze byc przekonwetowana na JSON.')
            self.logger.warning('Odpowiedz Denona nie moze byc przekonwertowana na JSON.')
            return
        message = response.get("heos", {}).get("message", "")
        if response.get("result") == "fail":
            #THutils.zapisz_do_logu_plik('E', 'Bledna odpowiedz HEOS z Denona.')
            self.logger.warning('Bledna odpowiedz HEOS z Denona.')
        #print  message
        return

    def heos_current_percentage_play(self):
        komenda = 'player/get_now_playing_media?pid=' + str(self.pid)
        odpowiedz = ''
        try:
            odpowiedz = self.heos_telnet_request(komenda)
            odpowiedz = self.heos_parse_message(odpowiedz['heos']['message'])
        except KeyError as serr:
            self.logger.warning('Brak odpow Denon current percent play: ' + str(serr))
        return odpowiedz

    def heos_stop(self):
        # TODO dorobic
        return

    def heos_idz_do(self, percent):
        # TODO dorobic
        return

    def heos_play_url(self, url_to_play):
        komenda = 'browse/play_stream?pid=' + str(self.pid) + '&url=' + url_to_play
        # print url_to_play
        odpowiedz = self.heos_telnet_request(komenda)
        wyn = {}
        if odpowiedz:
            try:
                wyn = self.heos_parse_message(odpowiedz['heos'])
            except KeyError as serr:
                self.logger.warning('Brak odpow Denon current percent play: ' + str(serr))
        return wyn



    """ def heos_status(self):
        s = {"general": [], "player": []}
        s["general"].append(self.heos_telnet_request("system/heart_beat"))
        s["general"].append(self.heos_telnet_request("system/check_account"))
        s["general"].append(self.heos_telnet_request("browse/get_music_sources"))
        s["general"].append(self.heos_telnet_request("player/get_players"))
        s["general"].append(self.heos_telnet_request("group/get_groups"))
        if self.pid:
            s["player"].append(self.heos_telnet_request("player/get_play_state?pid={0}".format(self.pid)))
            s["player"].append(self.heos_telnet_request("player/get_player_info?pid={0}".format(self.pid)))
            s["player"].append(self.heos_telnet_request("player/get_volume?pid={0}".format(self.pid)))
            s["player"].append(self.heos_telnet_request("player/get_mute?pid={0}".format(self.pid)))
            s["player"].append(self.heos_telnet_request('player/get_now_playing_media?pid={0}'.format(self.pid)))
        return s

        return"""

    def heos_get_play_state(self):
        komenda = 'player/get_play_state' + '?pid=' + self.pid
        try:
            odpowiedz = self.heos_telnet_request(komenda)
            odpowiedz = self.heos_parse_message(odpowiedz['heos']['message'])
            odpowiedz = odpowiedz['state']
        except (KeyError, TypeError) as serr:
            self.logger.warning('Brak odpow Denon get_play_state: ' + str(serr))
        return odpowiedz

    def heos_set_play_state(self, stan):
        #stan moze byc: play, pause, stop
        komenda = 'player/set_play_state' + '?pid=' + self.pid + '&state=' + stan
        odpowiedz = self.heos_telnet_request(komenda)
        wyn = {}
        if odpowiedz:
            try:
                wyn = self.heos_parse_message(odpowiedz['heos']['result'])
            except KeyError as serr:
                self.logger.warning('Brak odpow Denon set_play_state: ' + str(serr))
        return wyn

    def heos_set_volume(self, procent):
        komenda = 'player/set_volume' + '?pid=' + self.pid + '&level=' + str(procent)
        self.logger.info('Ustawienie glosnosci Denona HEOS na: ' + str(procent))
        return self.heos_telnet_request(komenda)

    def heos_get_volume(self):
        komenda = 'player/get_volume?pid=' + self.pid
        try:
            odpowiedz = self.heos_telnet_request(komenda)
            odpowiedz = self.heos_parse_message(odpowiedz['heos']['message'])
            odpowiedz = odpowiedz['level']
        except KeyError as serr:
            self.logger.warning('Brak odpow Denon zapyt o volume: ' + str(serr))
        if (len(odpowiedz)==3):
            try:
                odp = odpowiedz[2:]
                return odp
            except TypeError as serr:
                self.logger.warning('Format odpow Denon zly: ' + str(serr) + '. ' + str(odpowiedz))
        else:
            return odpowiedz

    def heos_telnet_request(self, command, wait=True):
        """Execute a `command` and return the response(s)."""
        command = self.heosurl + command
        # logging.debug("telnet request {}".format(command))
        try:
            self.telnet.write(command.encode('ascii') + b'\n')
            response = b''
            # logging.debug("starting response loop")
            while True:
                response += self.telnet.read_some()
                try:
                    response = json.loads(response.decode("utf-8"))
                    if not wait:
                        self.logger.info("HEOS: I accept the first response: {}".format(response))
                        break
                    # sometimes, I get a response with the message "under
                    # process". I might want to wait here
                    message = response.get("heos", {}).get("message", "")
                    if "command under process" not in message:
                        # self.logger.info("HEOS: I assume this is the final response: {}".format(response))
                        break
                    # self.logger.info("HEOS: Wait for the final response")
                    response = b''  # forget this message
                except (ValueError, TypeError) as serr:
                    # self.logger.warning("HEOS 1:... unfinished response: {}".format(response) + " serr: " + str(serr))
                    # response is not a complete JSON object
                    pass
        except (SocketError, AttributeError) as serr:
            self.logger.warning('HEOS broken pipe: ' + str(serr))
            return None
        if response.get("result") == "fail":
            self.logger.warning("HEOS: blad odpowiedzi " + response)
            return None

        return response

    def heos_parse_message(self, message):
        " parse message "
        if message:
            try:
                return dict(elem.split('=') for elem in message.split('&'))
            except (ValueError, AttributeError) as exc:
                #THutils.zapisz_do_logu_plik('I', 'Blad parsingu odpowiedzi heos: ' + str(message))
                self.logger.info('Blad parsingu odpowiedzi heos: ' + str(message) + " Blad: " + str(exc))
        return {}


    def decode_volume(self, volume):
        try:
            v = volume[:2]
            vol = int(v)
        except ValueError as e:
            return 0
        return vol

    def get_source(self):
        self.wyslij(self.tel, 'SI?') #source
        return

    def get_volume(self):
        self.wyslij(self.tel, 'MV?')  # master volume
        return

    def set_volume(self, procent):
        komenda = 'MV' + str(procent)
        self.wyslij(self.tel, komenda)
        #THutils.zapisz_do_logu_plik('I', 'Ustawienie glosnosci Denona na: ' + str(procent))
        self.logger.info('Ustawienie glosnosci Denona na: ' + str(procent))
        return

    def get_pwr_status(self):
        self.wyslij(self.tel, 'PW?')  # power status
        return

    """def set_pwr_status(self, status):
        if status == 1:
            self.wyslij(self.tel, 'PWON')
        elif status == 0:
            self.wyslij(self.tel, 'PWSTANDBY')
        return"""

    def wyslij(self, tele, komenda):
        try:
            tele.write(komenda.encode('ascii') + b'\n')
        except SocketError as e:
            #THutils.zapisz_do_logu_plik('E', 'Blad przy wysylaniu telneta: ' + str(e))
            self.logger.warning('Blad przy wysylaniu telneta: ' + str(e))
        return

    """def inicjuj_nasluchiwanie(self):
        response = b''
        try:
            resp = self.tel.read_some()
            response += resp
        except SocketError as e:
            pass
            #self.logger.warning('Blad przy odczytywaniu odpowiedzi z telneta: ' + str(e))
        self.procesuj_odpowiedz(response)
        threading.Timer(0.2, self.inicjuj_nasluchiwanie).start()
        return"""

    """def heos_inicjuj_nasluchiwanie(self):
        response = b''
        try:
            resp = self.heos_tel.read_some()
            response += resp
        except SocketError as e:
            pass
            #self.logger.warning('Blad przy odczytywaniu odpowiedzi z telneta Heos: ' + str(e))
        self.heos_procesuj_odpowiedz(response)
        threading.Timer(0.2, self.inicjuj_nasluchiwanie).start()
        return"""

    """def procesuj_odpowiedz(self, response):
        try:
            odpowiedz = response.split('\r')
        except ValueError as exc:
            #THutils.zapisz_do_logu_plik('I', 'Blad parsingu odpowiedzi: ' + str(response))
            self.logger.info('Blad parsingu odpowiedzi: ' + str(response))
        #print odpowiedz
        for komenda in odpowiedz:
            kom = komenda[:2]
            if kom == 'SI':
                if komenda[2:] != '?':
                    self.current_source = komenda[2:]
            elif kom == 'PW':
                if komenda[2:] == 'ON':
                    self.current_ispwon = True
                else:
                    self.current_ispwon = False
            elif kom == 'MV':
                if len(komenda[2:]) <= 3:
                    self.current_volume = self.decode_volume(komenda[2:])
            elif kom == '':
                break
            #else:
            #    print 'inna komenda' + komenda
        return"""