from os import listdir, path, stat, listdir, walk, remove, scandir
from constants import PREFIX_MNT, FOLDER_THUMB, FOLDER_STATIC, FOLDER_VIDEO, POLE_FULL_PATH, POLE_TS, POLE_THUMB_PATH, POLE_CZY_FOLDER, POLE_KATALOG, POLE_ROZMIAR, POLE_STRUKTURA_KATALOGOW, POLE_NAZWA
from sqlalchemy import Column, Integer, String, Boolean, BigInteger
from db import baza as db
import uuid
import narzedzia
import time



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

#TODO to FileStructureDefiniotion jest wykorystywane tylkow thumbnailach, przeniesc tam

def usuwanie_katalogow_thumb():    
    print ('Rozpoczynam usuwanie katalogów thumb small')
    #tworzenie thumbsmalli
    for root, dirs, files in walk(PREFIX_MNT):
        if path.basename(root) == FOLDER_THUMB:
            print (root)
            rmdir(root)
        '''if path.basename(root) != FOLDER_THUMB:
            continue
        #if path.basename(root) == 'small' and FOLDER_THUMB in root:
        #    continue
        for dir in dirs:
            if dir == 'small':
                for rs, ds, fs in walk(path.join(root, dir)):
                    for f in fs:
                        docelowy = path.join(rs, f)
                        print (docelowy)
                        remove(docelowy)
                print ('Usuwam folder: ' + path.join(root, dir))
                rmdir(path.join(root, dir)) '''   
    
class FileStructure:
   
    def getStructureJSON(self, startFolder='', tsSynchro=0, onlyFolders=False, noThumbPath=False, short=False, onlyFiles=False):
        #short zwraca tylko fullpath i tsa
        #onlyfolders zwraca tylko i wylacznie katalogi, bez zwyczajnych plikow
        #onlyFiles zwraca tylko pliki
        #noThumbPath nie zwraca sciezki do thumbPath
        if onlyFolders:
            wszystkie = FileStructureDefinition.query.filter(FileStructureDefinition.isFolder==True, FileStructureDefinition.ts >= tsSynchro)
        else:    
            wszystkie = FileStructureDefinition.query.filter(FileStructureDefinition.ts >= tsSynchro)
        
        tok = []
        if wszystkie:
            for t in wszystkie:
                if onlyFiles and t.isFolder:
                    continue
                if t.fullPath.startswith(startFolder): #TODO pozniej do przerobienia tak aby query zwracalo od razu zaczynajace sie od start folder
                    tok.append(t.serialize(noThumbPath=noThumbPath, short=short))
        
        ts = StructureTSDefinition.query.first()
        #if not ts:
        #    ts = int(time.time())
        return { POLE_TS: ts.ts, POLE_STRUKTURA_KATALOGOW: tok }
   
    '''def getStructureOnlyFoldersJSON(self, startFolder='', tsSynchro=0):
        wszystkie = FileStructureDefinition.query.filter(FileStructureDefinition.isFolder==True, FileStructureDefinition.ts >= tsSynchro)
        tok = []
        ts_struktury = 123
        if wszystkie:
            for t in wszystkie:
                if t.fullPath.startswith(startFolder):
                    tok.append(t.serialize(short=True))
        return { POLE_TS: ts_struktury, POLE_STRUKTURA_KATALOGOW: tok }'''
   
    def getFolderContent(self, folder):
        wszystkie = FileStructureDefinition.query.filter(FileStructureDefinition.folder == folder)
        tok = []
        for t in wszystkie:
            tok.append(t.serialize(noThumbPath=True))
        return tok
   
    def getThumbPathByFileName(self, fileName):
        fsd = FileStructureDefinition.query.filter_by(fullPath=fileName).first()
        if fsd:
            return fsd.thumbPath 
        return None
    
    '''def getNewerThen(self, tsSynchro):
        fsd = FileStructureDefinition.query.filter_by(ts>tsSynchro).first()
        tok = []
        for t in fsd:
            tok.append(t.serialize())
        return tok'''
    
    def __clearTable(self):
        db.session.query(FileStructureDefinition).delete()
        db.session.commit()    
    
    def purgeThumbsFolder(self):
        #usuwamy pliku thumbs kiedy nie ma ani rekordu w bazie ani nie ma pliku - wazne zawsze te dwa warunki musza byc spelnione
        stru = []
        for st in FileStructureDefinition.query.all():
            stru.append(st.thumbPath)
        for file in listdir(narzedzia.add_prefix_mnt(FOLDER_THUMB)):
            if file == FOLDER_STATIC:
                continue
            if file == FOLDER_VIDEO:
                continue
            if file not in stru:
                f = narzedzia.add_prefix_mnt( path.join(FOLDER_THUMB, file))
                #print(f)
                remove(f)
    
    def generateFileStructureUpdateDatabase(self, startFolder=''):
        #self.__clearTable()
        
        #dodanie glownego folderu
        newStr = FileStructureDefinition.query.filter_by(fullPath="").first()
        ts = int(path.getmtime(PREFIX_MNT))
        size = self.__getDirLength(PREFIX_MNT)
        if not newStr:
            newFS = FileStructureDefinition("", ts, True, narzedzia.determinuj_ikone(PREFIX_MNT, isDir=True), size, "", "")
            db.session.add(newFS)
        else:
            newStr.ts = ts
            newStr.size = size
        db.session.commit()
        
        #potem przelatujemy przez walk i dla każdego jezeli go nie ma to dodajemy rekord
        #a jak jest to sprawdzamy ts i jak jest inny niz ten w bazie, bo sievplik zmienił to aktualizujemy w bazie 
        currentFiles = []
        for entry in self.__scanTree(path.join(PREFIX_MNT, startFolder)):
            if entry.name == FOLDER_THUMB: # omijanie folderu thumb
                continue
            currentFiles.append(entry)
                
        with db.session.no_autoflush:
            for entry in currentFiles:
                    fileStr = self.__updateFileInStructure(entry)                  
        db.session.commit()
        
        '''for root, dirs, files in walk(path.join(PREFIX_MNT, startFolder), followlinks=False):
            if path.basename(FOLDER_THUMB) not in root:  # omijanie folderu thumb
                rootBezMnt = root.replace(PREFIX_MNT, '')
                self.__updateFileInStructure(rootBezMnt, True, rootBezMnt, path.basename(root))
                
                for file in files:
                    fullPath = path.join(rootBezMnt, file)
                    fileStr = self.__updateFileInStructure(fullPath, False, rootBezMnt, file)                  
                    if fileStr:
                        pl.append(fileStr)                    
                for kat in dirs:
                    self.__updateFileInStructure(path.join(rootBezMnt, kat), True, rootBezMnt, kat)'''
        
        #tworzymy thumby dla tych, ktore sa nowe lub nie ma thumba lub zmodyfikowany
        '''from thumb import Thumb
        for struk in pl:
            if FOLDER_STATIC not in struk.thumbPath:
                Thumb(struk.fullPath).generateThumbSmall(struk.thumbPath) ''' 


        #sprawdzamy czy plik nadal istnieje fizycznie, jak nie to usuwamy z bazy oraz odpowiadajacy mu thumbnail
        #najpierw sporzadzamy liste samych fullPathow z bazy
        #strukta = FileStructureDefinition.query.filter(FileStructureDefinition.fullPath.ilike((startFolder+'%'))).all() #.with_entities(FileStructureDefinition.fullPath).all()
        strukt = []
        for st in FileStructureDefinition.query.filter(FileStructureDefinition.fullPath.ilike((startFolder+'%'))).all():
            strukt.append(st.fullPath)
        #return str(strukt)
        #potem sporzadzamy taka sama liste ale z systemu plikow
        curfiles = []
        curfiles.append(startFolder)
        for f in currentFiles:
            curfiles.append(narzedzia.remove_prefix_mnt(f.path))
            
        #wyciagamy delte
        delta = set(strukt) - set(curfiles)
        #return str(delta)
        for f in delta:
            fs = FileStructureDefinition.query.filter_by(fullPath=f).first()
            if FOLDER_STATIC not in fs.thumbPath:
                try:
                    remove( narzedzia.add_prefix_mnt( path.join(FOLDER_THUMB, fs.thumbPath)) )
                    #TODO dodac susuwanie pliku video thumb
                except FileNotFoundError:
                    continue
            db.session.delete(fs)

        
        '''for plik in strukt:
            if plik.fullPath.startswith(startFolder):
                jest = False
                for curfile in currentFiles:
                    if narzedzia.remove_prefix_mnt(curfile.path) == plik.fullPath:
                        jest = True
                if not jest:
                    db.session.delete(plik)
                    db.session.commit()
                    if FOLDER_STATIC not in plik.thumbPath:
                        try:
                            remove( narzedzia.add_prefix_mnt( path.join(FOLDER_THUMB, plik.thumbPath)) )
                            #TODO dodac susuwanie pliku video thumb
                        except FileNotFoundError:
                            continue'''

        #aktualizacja czasu generowania struktury
        StructureTSDefinition.query.delete()
        db.session.add(StructureTSDefinition(int(time.time())))
        db.session.commit()

        self.purgeThumbsFolder()
        
        return 'Struktura wygenerowana'

    def zwroczlisty(self, lista):
        #strukt = FileStructureDefinition.query.filter(FileStructureDefinition.fullPath.in_(('tmp', 'muza/Uriah heep/Wizards'))).all()
        strukt = FileStructureDefinition.query.filter(FileStructureDefinition.fullPath.ilike(('tmp%', 'muza/Uriah he%'))).all()
        tok=[]
        for t in strukt:
            tok.append(t.serialize())
        return tok

    def __updateFileInStructure(self, entry): #file, isDir, folder, fileName):
        #return FileStructureDefinition if newly added or changed -> update thumb
        #return None if no changes done
        fullPathNoMNTPrefix = narzedzia.remove_prefix_mnt(entry.path)
        fileStr = FileStructureDefinition.query.filter_by(fullPath=fullPathNoMNTPrefix).first()
        
        ts = int(entry.stat().st_mtime)
        
        if not fileStr:
            nazwaIkony = narzedzia.determinuj_ikone(fullPathNoMNTPrefix, isDir=entry.is_dir())
            if nazwaIkony != '':
                thumbPath = path.join(FOLDER_STATIC, nazwaIkony)
            else:
                thumbPath = str(uuid.uuid4()) + '.jpg'
            rozmiar = entry.stat().st_size
            if entry.is_dir():
                rozmiar = self.__getDirLength(entry.path)
            newFS = FileStructureDefinition(fullPathNoMNTPrefix, ts, entry.is_dir(), thumbPath, rozmiar, path.dirname(fullPathNoMNTPrefix), entry.name)
            db.session.add(newFS)
            #db.session.commit()
            return newFS
            
        if fileStr.ts != ts:
            fileStr.ts = ts
            if entry.is_dir():
                fileStr.size = self.__getDirLength(entry.path)
            return fileStr
            
        #if not path.exists( narzedzia.add_prefix_mnt(path.join(FOLDER_THUMB, fileStr.thumbPath))):
        #    return fileStr
            
        return None
        
    def __getDirLength(self, folder):
        #folder zawsze razem z prefixwem mnt
        i = 0
        for entry in scandir(folder):
            i = i + 1
        return i
                
                
    def __scanTree(self, folder):
        #entry.name to sama nazwa pliku/katalogu
        #entry.path to pelna sciezka razem z katalogiem MNT
        #is_dir() typ boolean jesli entry jest folderem
        #stat().st_mtime modyfifcation time, czyli nasz TS
        #stat().st_size czyli nasz rozmiar
        for entry in scandir(folder):
            if entry.is_dir(follow_symlinks=False):
                yield entry
                yield from self.__scanTree(entry.path)  
            else:
                yield entry     
        
class StructureTSDefinition(db.Model):
    __tablename__ = "structurets"
    ts = Column(Integer, primary_key=True, default=0)
    def __init__(self, ts):
        self.ts = ts
        
class FileStructureDefinition(db.Model):

    __tablename__ = "filestructure"
    #__table_args__ = {'extend_existing': True}

    fullPath = Column(String, primary_key=True)
    ts = Column(Integer)
    isFolder = Column(Boolean, default=False)
    thumbPath = Column(String)
    size = Column(BigInteger, default=0)
    folder = Column(String)
    fileName = Column(String)

    def __init__(self, fullPath, ts, isFolder, thumbPath, size, katalog, fileName):
        self.fullPath = fullPath
        self.ts = ts
        self.isFolder = isFolder
        self.thumbPath = thumbPath
        self.size = size
        self.folder = katalog
        self.fileName = fileName
    
    def serialize(self, short=False, noThumbPath=False):
        wynik = {}
        wynik[POLE_FULL_PATH] = self.fullPath
        wynik[POLE_TS] = self.ts

        if short:
            return wynik

        wynik[POLE_NAZWA] = self.fileName
        wynik[POLE_CZY_FOLDER] = self.isFolder
        wynik[POLE_ROZMIAR] = self.size
        wynik[POLE_KATALOG] = self.folder
      

        if noThumbPath:
            return wynik
            
        wynik[POLE_THUMB_PATH] = self.thumbPath
        
        return wynik
        