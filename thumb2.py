import constants
from os import path, makedirs
from PIL import Image, ImageOps, ImageDraw, ImageFont
import narzedzia

#TODO thumbnaile dla PDFa dorobić: from pdf2image import convert_from_path

class Thumb:
    def __init__(self, nazwa_pliku, instance_path):
        self.nazwa_pliku = nazwa_pliku
        self.__instance_path = instance_path
        self.nazwa_pliku_z_MNT = narzedzia.add_prefix_mnt(self.nazwa_pliku)
        self.plik = path.basename(self.nazwa_pliku)
        self.sciezka_z_MNT = narzedzia.add_prefix_mnt(path.dirname(self.nazwa_pliku))
        self.sciezka_folderu_thumb = path.join(self.sciezka_z_MNT, constants.FOLDER_THUMB)
        self.sciezka_folderu_thumb_small = path.join(self.sciezka_z_MNT, constants.FOLDER_THUMB_SMALL)
        self.nazwa_pliku_thumb_small, nazwa_ikony = narzedzia.determinuj_ikone(nazwa_pliku)
        self.nazwa_pliku_thumb = self.nazwa_pliku_thumb_small
        self.__create_thumb = False  #wskazuje czy tworzyc plik z thumbem, jesli false to znaczy ze wziasc ikone
        self.__tworz_katalogi()
        
        if narzedzia.is_video(nazwa_pliku):
            self.nazwa_pliku_thumb_small = path.join(self.sciezka_folderu_thumb_small, self.plik) + ".png"
            self.nazwa_pliku_thumb = path.join(self.sciezka_folderu_thumb, self.plik) + ".png"
            self.__create_thumb = True
            return

        if narzedzia.is_picture(nazwa_pliku):
            self.nazwa_pliku_thumb_small = path.join(self.sciezka_folderu_thumb_small, self.plik)
            self.nazwa_pliku_thumb = path.join(self.sciezka_folderu_thumb, self.plik)
            self.__create_thumb = True
            return
            
        #self.nazwa_pliku_thumb_small = "./templates/ikona_plik.png"
        #self.nazwa_pliku_thumb = "./templates/ikona_plik.png"            

    
    def get_thumb_big(self):
        if not self.__create_thumb:
            return self.nazwa_pliku_thumb
        return self.__get_thumb(self.nazwa_pliku_thumb, constants.THUMB_SIZE)
    
    def get_thumb_small(self,):
        if not self.__create_thumb:
            return self.nazwa_pliku_thumb_small
        return self.__get_thumb(self.nazwa_pliku_thumb_small, constants.THUMB_SMALL_SIZE)
          
    def __get_thumb(self, cel, rozmiar ):
        #jesli nie ma thumba to tworzymy
        if not path.exists(cel):
            if narzedzia.is_picture(self.nazwa_pliku):
                self.__tworz_thumb_picture(cel, rozmiar)
            if narzedzia.is_video(self.nazwa_pliku):
                self.__tworz_thumb_video(self.nazwa_pliku_z_MNT, cel)
        return cel

    def __tworz_thumb_picture(self, cel, rozmiar):
        img = Image.open(self.nazwa_pliku_z_MNT)
        img = ImageOps.exif_transpose(img)
        img.thumbnail((rozmiar, rozmiar))
        img.save(cel, format="jpeg", dpi=(600,600))
        
    def __tworz_thumb_video(self, zrodlo, cel):
        import subprocess
        subprocess.call(['ffmpeg', '-i', zrodlo, '-ss', '00:00:00.000', '-vframes', '1', '-s', '400x400', cel])
        #dlugosc = subprocess.check_output(['ffprobe', '-i', zrodlo, '-show_format', '-v', 'quiet', '|', 'grep', 'duration='])
        #parametry_video = subprocess.check_output(['ffprobe', '-i', zrodlo.encode('utf8'), '-show_format', '-v', 'quiet'])
        parametry_video = subprocess.check_output(['ffprobe', '-i', zrodlo, '-show_format', '-v', 'quiet'])
        dlugosc = int(float(str(parametry_video).split('duration=',1)[1][:8]))
        from datetime import timedelta
        
        self.__dodaj_tekst_dlugosc(str(timedelta(seconds=dlugosc)), cel)
        #f = open(self.nazwa_pliku_txt_dl_filmu, "w")
        #f.write(str(dlugosc))
        #f.close()
        #print (dlugosc)
   
    def __dodaj_tekst_dlugosc(self, dlugosc, plik):
        img = Image.open(plik)
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(path.join(self.__instance_path, "arial.ttf"), 30)
        width, height = img.size
        x, y = (50, 50)
        w, h = font.getsize(dlugosc)
        draw.rectangle((x-10, y-10, x + w +10 , y + h + 10), fill='black')
        draw.text((x, y), dlugosc, fill='white', font=font)
        img.save(plik, quality=100)
    
    def __tworz_katalogi(self):
        try:
            if not path.exists(self.sciezka_folderu_thumb):
                makedirs(self.sciezka_folderu_thumb)
            if not path.exists(self.sciezka_folderu_thumb_small):
                makedirs(self.sciezka_folderu_thumb_small)
        except:
            pass
