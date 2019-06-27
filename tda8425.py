# -*- coding: utf8 -*-
# TDA8425 Sound processor for Raspberry Pi
# Python version version - Andrey Zagorets 27/11/2016
#
# This code is provided to help with programming the TDA chip.

import smbus
import time


MAX_GLOSNOSC = 62
MIN_GLOSNOSC = 38
GLOSNOSC_PRZY_INICJALIZACJI = 43
TDA8425_ADDRESS = 0x41
MULTIPL_ADDRESS = 0x70
# parametry
TDA8425_VOLL = 0b00000000
TDA8425_VOLR = 0b00000001
TDA8425_BASS = 0b00000010
TDA8425_TREBLE = 0b00000011
TDA8425_SWITCH = 0b00001000

VOLUME_MASK = 0x3F
BASS_MASK = 0x0F
SOURCE_MASK = 0x07
SIGNAL_MASK = 0x18

TDA8425_IS_BIT = 0b00000001
TDA8425_ML0_BIT = 0b00000010
TDA8425_ML1_BIT = 0b00000100
TDA8425_STL_BIT = 0b00001000
TDA8425_EFL_BIT = 0b00010000
TDA8425_MU_BIT = 0x20

TDA8425_CHAN_1_STEREO = TDA8425_ML1_BIT | TDA8425_ML0_BIT
TDA8425_CHAN_2_STEREO = TDA8425_ML1_BIT | TDA8425_ML0_BIT | TDA8425_IS_BIT
TDA8425_CHAN_1_A = TDA8425_ML0_BIT
TDA8425_CHAN_1_B = TDA8425_ML1_BIT
TDA8425_CHAN_2_A = TDA8425_ML0_BIT | TDA8425_IS_BIT
TDA8425_CHAN_2_B = TDA8425_ML1_BIT | TDA8425_IS_BIT
TDA8425_MONO = 0x00
TDA8425_LINEAR_STEREO = TDA8425_STL_BIT
TDA8425_PSEUDO_STEREO = TDA8425_EFL_BIT
TDA8425_SPATIAL_STEREO = TDA8425_EFL_BIT | TDA8425_STL_BIT


class TDA8425:
    def __init__(self, nr_przedwz, nazwa, busnum=1):
        # Create I2C device.
        self.bus = smbus.SMBus(busnum)
        self.numer = nr_przedwz
        self.nazwa = nazwa
        self.nr_przedwz = (1 << nr_przedwz)
        self.tda8425_vaules = [0x3C, 0x3C, 0xF6, 0xF6, 0xCE]
        self.nr_wejscia = 1
        # TODO przerobic glosnosc na _glosnosc i setter i getter
        self.glosnosc = 0
        self.init_chip()

    def write_chip(self, param, value):
        try:
            self.bus.write_byte(MULTIPL_ADDRESS, self.nr_przedwz)
            time.sleep(0.01)
            self.bus.write_byte_data(TDA8425_ADDRESS, param, value)
        except (RuntimeError, IOError) as serr:
            # print 'Blad w zapisie do TDA8425: Nr. przewdz->' + str(self.nr_przedwz) + ' Parametr: ' + str(param) +\
            #    ' Wartosc: ' + str(value)
            return

    def init_chip(self):
        # self.write_chip(TDA8425_VOLL, 0x1E)
        # self.write_chip(TDA8425_VOLR, 0x1E)
        self.write_chip(TDA8425_TREBLE, self.tda8425_vaules[2])
        self.write_chip(TDA8425_BASS, self.tda8425_vaules[3])
        self.write_chip(TDA8425_SWITCH, self.tda8425_vaules[4])
        self.ustaw_glosnosc(GLOSNOSC_PRZY_INICJALIZACJI)
        self.select_input(1)
        self.mute_off()

    def set_param(self, param, value):
        if param == TDA8425_VOLL or param == TDA8425_VOLR:
            if value <= VOLUME_MASK:
                self.tda8425_vaules[param] = self.tda8425_vaules[param] & ~VOLUME_MASK
                self.tda8425_vaules[param] = self.tda8425_vaules[param] | value
        elif param == TDA8425_BASS or param == TDA8425_TREBLE:
            if value <= BASS_MASK:
                self.tda8425_vaules[param] = self.tda8425_vaules[param] & ~BASS_MASK
                self.tda8425_vaules[param] = self.tda8425_vaules[param] | value
        self.write_chip(param, self.tda8425_vaules[param])

    def select_input(self, input_selected):
        self.tda8425_vaules[4] = self.tda8425_vaules[4] & ~SOURCE_MASK
        self.tda8425_vaules[4] = self.tda8425_vaules[4] | input_selected
        self.write_chip(TDA8425_SWITCH, self.tda8425_vaules[4])
        self.nr_wejscia = input_selected

    def select_signal(self, input_selected):
        self.tda8425_vaules[4] = self.tda8425_vaules[4] & ~SIGNAL_MASK
        self.tda8425_vaules[4] - self.tda8425_vaules[4] | input_selected
        self.write_chip(TDA8425_SWITCH, self.tda8425_vaules[4])

    def mute_on(self):
        self.tda8425_vaules[4] = self.tda8425_vaules[4] | TDA8425_MU_BIT
        self.write_chip(TDA8425_SWITCH, self.tda8425_vaules[4])

    def mute_off(self):
        self.tda8425_vaules[4] = self.tda8425_vaules[4] & ~TDA8425_MU_BIT
        self.write_chip(TDA8425_SWITCH, self.tda8425_vaules[4])

    def get_param(self, param):
        if param == TDA8425_VOLL or param == TDA8425_VOLR:
            return self.tda8425_vaules[param] & VOLUME_MASK
        elif param == TDA8425_BASS or param == TDA8425_TREBLE:
            return self.tda8425_vaules[param] & BASS_MASK

    def get_input(self):
        return self.tda8425_vaules[4] & SOURCE_MASK

    def get_signal(self):
        return self.tda8425_vaules[4] & SIGNAL_MASK

    def get_mute_state(self):
        return (self.tda8425_vaules[4] & TDA8425_MU_BIT) >> 5

    def procent_do_wymierne_glosnosc(self, glosn):
        # parametr jest podany w procentach, pomiedzy 0 a 100
        # funkcja zwraca wymierna wartosc pomiedzy MIN_GLOSNOSC a MAX_GLOSNOSC
        endv = MAX_GLOSNOSC - MIN_GLOSNOSC
        i = ((endv * glosn) / 100) + MIN_GLOSNOSC
        return int(i)

    def ustaw_glosnosc(self, glosn):
        # print 'Nr wzm: ' +str(self.nr_przedwz) + ' glosn: ' + str(glosn)
        # TODO potenjclanie to jest miejsce w ktorym jest sciszane samodzielnie
        self.glosnosc = int(glosn)
        if self.glosnosc > 100:
            self.glosnosc = 100
        if self.glosnosc < 0:
            self.glosnosc = 0
        i = self.procent_do_wymierne_glosnosc(glosn)
        self.set_param(TDA8425_VOLL, i)
        time.sleep(0.01)
        self.set_param(TDA8425_VOLR, i)
        self.mute_off()
