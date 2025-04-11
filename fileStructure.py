from os import listdir, path, stat, listdir, walk, remove
from constants import PREFIX_MNT, FOLDER_THUMB, POLE_FULL_PATH, POLE_TS, POLE_THUMB_PATH
from sqlalchemy import Column, Integer, String, Boolean
from db import baza as db
import uuid
import narzedzia
from thumb import Thumb


'''
def odczytaj_katalog(struktura, nazwa_katalogu):
    pelen_katalog = nazwa_katalogu #.encode('utf8')
    
    lista = listdir(pelen_katalog) 
    
    for plik in lista:
        pelenplik = path.join(pelen_katalog, plik)
        struktura[pelen_katalog].add(plik)
        #filestats = stat(pelenplik)
        #czy_katalog = path.isdir(pelenplik)
        #print (plik)
        
        if plik != path.basename(FOLDER_THUMB):    #omijanie folderu thumb        
            if path.isdir(pelenplik):
                #print (pelenplik)
                odczytaj_katalog(pelenplik)  
'''

'''def generuj_strukture(katalog):
    struktura = {}
    #odczytaj_katalog(struktura, PREFIX_MNT + '/zdjecia/01-Ludzie/Iwka')
    for root, dirs, files in walk('/mnt/sda1/zdjecia/test') #os.path.join(PREFIX_MNT, katalog)):
        if path.basename(FOLDER_THUMB) not in root:    #omijanie folderu thumb        
            struktura[root] = files
    return struktura
    #for name in files:
        #print(path.join(root, name))
        #print (root)
'''     
    
class FileStructure:
   
    def getStructureJSON(self, startFolder=''):
        wszystkie = FileStructureDefinition.query.all()
        tok = []
        if wszystkie:
            for t in wszystkie:
                if t.fullPath.startswith(startFolder):
                    tok.append(t.serialize())
        return tok
   
    def getThumbPathByFileName(self, fileName):
        fsd = FileStructureDefinition.query.filter_by(fullPath=fileName).first()
        if fsd:
            return fsd.thumbPath 
        return None
   
    def saveSingle(self, fullPath, ts, thumbPath):
        struktFolder = FileStructureDefinition(fullPath, ts, thumbPath)
        db.session.merge(struktFolder)
        db.session.commit()    
    
    def __clearTable(self):
        db.session.query(FileStructureDefinition).delete()
        db.session.commit()    
        
    def generateFileStructureUpdateDatabase(self, startFolder=''):
        from constants import PREFIX_MNT, FOLDER_THUMB
        #self.__clearTable()
        
        #sprawdzamy czy plik nadal istnieje, jak nie to usuwamy z bazy
        strukt = FileStructureDefinition.query.all()
        for plik in strukt:
            if plik.fullPath.startswith(startFolder):
                if not path.exists(narzedzia.add_prefix_mnt(plik.fullPath)):
                    db.session.delete(plik)
                    try:
                        remove( path.join(FOLDER_THUMB, plik.thumbPath) )
                    except FileNotFoundError:
                        continue
        db.session.commit()
        
        #potem przelatujemy przez walk i dla każdego jezeli go nie ma to dodajemy rekord i robimy thumbsa
        #a jak jest to sprawdzamy ts i jak jest inny niz ten w bazie, bo si eplik zmienił to aktualizujemy w bazie oraz tworzymy nowego thumsa 
        
        for root, dirs, files in walk(path.join(PREFIX_MNT, startFolder)):
            if path.basename(FOLDER_THUMB) not in root:  # omijanie folderu thumb
                for file in files:
                    katal = root.replace(PREFIX_MNT, '')
                    fullPath = path.join(katal, file)
                    fileStr = self.__updateFileInStructure(fullPath)
                    if fileStr:
                        Thumb(fileStr.fullPath).generateThumbSmall(fileStr.thumbPath)
                for kat in dirs:
                    katal = root.replace(PREFIX_MNT, '')
                    fullPath = path.join(katal, kat)
                    fileStr = self.__updateFileInStructure(fullPath)

        db.session.commit()

    def __updateFileInStructure(self, file):
        #return FileStructureDefinition if newly added or changed -> update thumb
        #return None if no changes done
        fileStr = FileStructureDefinition.query.filter_by(fullPath=file).first()
        zPrefixem = narzedzia.add_prefix_mnt(file)
        ts = int(path.getmtime(zPrefixem))
        if not fileStr:
            urlIkony, nazwaIkony = narzedzia.determinuj_ikone(file)
            if nazwaIkony != '':
                thumbPath = nazwaIkony
            else:
                thumbPath = str(uuid.uuid4())
            newFS = FileStructureDefinition(file, ts, thumbPath)
            db.session.add(newFS)
            db.session.commit()
            return newFS
        if fileStr.ts != ts:
            fileStr.ts = ts
            db.session.commit()
            return fileStr
        return None
        
class FileStructureDefinition(db.Model):

    __tablename__ = "filestructure"
    __table_args__ = {'extend_existing': True}

    fullPath = Column(String, primary_key=True)
    ts = Column(Integer)
    thumbPath = Column(String)

    def __init__(self, fullPath, ts, thumbPath):
        self.fullPath = fullPath
        self.ts = ts
        self.thumbPath = thumbPath
    
    def serialize(self):
        return {POLE_FULL_PATH: self.fullPath, POLE_TS : self.ts, POLE_THUMB_PATH: self.thumbPath}