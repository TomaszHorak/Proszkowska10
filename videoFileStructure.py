from os import listdir, path, stat, listdir, walk, remove
from constants import PREFIX_MNT, FOLDER_VIDEO, FOLDER_THUMB, POLE_FULL_PATH, POLE_TS, POLE_THUMB_PATH
from sqlalchemy import Column, Integer, String, Boolean
from db import baza as db
from flask import send_file, send_from_directory
import uuid
import narzedzia
import subprocess
       
class VideoFileStructure:
   
    def getStructureJSON(self, startFolder=''):
        wszystkie = VideoFileStructureDefinition.query.all()
        tok = []
        if wszystkie:
            for t in wszystkie:
                if t.fullPath.startswith(startFolder):
                    tok.append(t.serialize())
        return tok
   
    def getThumbSmall(self, fileName):
        fsd = VideoFileStructureDefinition.query.filter_by(fullPath=fileName).first()
        if fsd:
            return send_file(narzedzia.add_prefix_mnt(path.join(FOLDER_THUMB, path.join(FOLDER_VIDEO, fsd.thumbPath))), download_name=path.basename(fileName))
        return send_from_directory('static', 'icons8_no_image.png')    

    def getThumbPathByFileName(self, fileName, fullPath=False):
        fsd = VideoFileStructureDefinition.query.filter_by(fullPath=fileName).first()
        if fsd:
            if fullPath:
                return path.join(FOLDER_THUMB, path.join(FOLDER_VIDEO, fsd.thumbPath))
            else:    
                return fsd.thumbPath 
        return None
    
    def __clearTable(self):
        db.session.query(VideoFileStructureDefinition).delete()
        db.session.commit()    
    
    def purgeWEBMFolder(self):
        #usuwamy pliku webm kiedy nie ma ani rekordu bazie ani nie ma pliku - wazne zawsze te dwa warunki musza byc spelnione
        stru = []
        for st in VideoFileStructureDefinition.query.all():
            stru.append(st.thumbPath)
        for file in listdir(narzedzia.add_prefix_mnt( path.join(FOLDER_THUMB, FOLDER_VIDEO))):
            if file not in stru:
                f = narzedzia.add_prefix_mnt( path.join(FOLDER_THUMB, path.join(FOLDER_VIDEO, file)))
                remove(f)
    
    def generateWEBMFileStructureUpdateDatabase(self, startFolder=''):
        self.__clearTable()
        
        self.purgeWEBMFolder()            
            
        #sprawdzamy czy plik nadal istnieje, jak nie to usuwamy z bazy oraz odpowiadajacy mu WEBM
        strukt = VideoFileStructureDefinition.query.all()
        for plik in strukt:
            if plik.fullPath.startswith(startFolder):
                if not path.exists(narzedzia.add_prefix_mnt(plik.fullPath)):
                    db.session.delete(plik)
                    db.session.commit()
                    #if FOLDER_STATIC not in plik.thumbPath:
                    try:
                        remove( narzedzia.add_prefix_mnt( path.join(FOLDER_THUMB, path.join(FOLDER_VIDEO, plik.thumbPath))) )
                    except FileNotFoundError:
                        continue
        
        #potem przelatujemy przez walk i dla każdego jezeli go nie ma to dodajemy rekord i robimy WEBM
        #a jak jest to sprawdzamy ts i jak jest inny niz ten w bazie, bo si eplik zmienił to aktualizujemy w bazie oraz tworzymy nowego thumsa 
        pl = []
        for root, dirs, files in walk(path.join(PREFIX_MNT, startFolder)):
            if path.basename(FOLDER_THUMB) not in root:  # omijanie folderu thumb
                for file in files:
                    katal = root.replace(PREFIX_MNT, '')
                    fullPath = path.join(katal, file)
                    if narzedzia.is_video(fullPath):
                        fileStr = self.__updateFileInStructure(fullPath)
                        if fileStr:
                            pl.append(narzedzia.add_prefix_mnt(path.join(FOLDER_THUMB, path.join(FOLDER_VIDEO, fileStr.thumbPath))))
                            subprocess.call(['ffmpeg', '-i', narzedzia.add_prefix_mnt(fileStr.fullPath), '-c:v', 'libvpx-vp9', '-crf', '35', '-b:v', '2000', '-pix_fmt', 'yuv420p', narzedzia.add_prefix_mnt(path.join(FOLDER_THUMB, path.join(FOLDER_VIDEO, fileStr.thumbPath)))])
                            #subprocess.call(['ffmpeg', '-i', zrodlo, '-c:v', 'libvpx-vp9', '-crf', '35', '-b:v', '300k', '-pix_fmt', 'yuv420p', cel])
        db.session.commit()
        return str(pl)
        return 'WEBmy wygenerowane'

    def __updateFileInStructure(self, file):
        #return FileStructureDefinition if newly added or changed -> update thumb
        #return None if no changes done
        fileStr = VideoFileStructureDefinition.query.filter_by(fullPath=file).first()
        zPrefixem = narzedzia.add_prefix_mnt(file)
        ts = int(path.getmtime(zPrefixem))
        if not fileStr:
            thumbPath = str(uuid.uuid4()) + '.webm'
            newFS = VideoFileStructureDefinition(file, ts, thumbPath)
            db.session.add(newFS)
            db.session.commit()
            return newFS
        if fileStr.ts != ts:
            fileStr.ts = ts
            db.session.commit()
            return fileStr
        if not path.exists( narzedzia.add_prefix_mnt(path.join(FOLDER_THUMB, path.join(FOLDER_VIDEO, fileStr.thumbPath)))):
            return fileStr
        return None
        
class VideoFileStructureDefinition(db.Model):

    __tablename__ = "videofilestructure"
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