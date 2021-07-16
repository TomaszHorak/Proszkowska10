import radia
import time

rad = radia.Radia()

#a = rad.odswiez_co_grane_openfm(25)
#print a

rad.dodaj_stacje_openfm()
#rad.dodaj_stacje_polskieradio()
#rad.dodaj_stacje_rmf()
#rad.dodaj_stacje_tunein()
a = rad.wyslij_katalog_radii()
print 'koniec'