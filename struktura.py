from os import listdir, path, stat, listdir, walk
from constants import PREFIX_MNT, FOLDER_THUMB, POLE_KATALOG, POLE_TS
from sqlalchemy import Column, Integer, String, Boolean
from db import baza as db
from flask import Blueprint, request

structure_blueprint = Blueprint('structure', __name__, template_folder='templates')

@structure_blueprint.route("/generuj_strukture_katalogow/")
@structure_blueprint.route("/generuj_strukture_katalogow/<path:katalog>")
def generuj_strukture_katalogow(katalog=''):
    #struktura = {}
    strukt = Struktura()
    strukt.generateStructureUpdateDatabase()
    return 'Struktura wygenerowana.'
    '''strukt.clearTable()
    for root, dirs, files in walk(path.join(constants.PREFIX_MNT, katalog)):
        if path.basename(constants.FOLDER_THUMB) not in root:  # omijanie folderu thumb
            #TODO zamiast tylko folderthumb musimy mojac wzystkie z kropka
            pliczki = []
            for file in files:
                pliczki.append(Plik(path.join(root, file)).getPlikJSON())
            for katy in dirs:
                pliczki.append(Plik(path.join(root, katy)).getPlikJSON())
            kat = root.replace(constants.PREFIX_MNT, '')
            strukt.save_single(kat, int(path.getmtime(root)))
            struktura[kat] = pliczki
    #strukt = {constants.POLE_TS: int(time.time()), constants.POLE_STRUKTURA_KATALOGOW: struktura}
    #with open(constants.STR_KAT, "w") as outfile:
    #    json.dump(struktura, outfile)
    #return strukt'''

@structure_blueprint.route("/genstrvideo")
@structure_blueprint.route("/genstrvideo/<path:startFolder>")
def generuj_strukture_video(startFolder=''):
    from videoFileStructure import VideoFileStructure
    return VideoFileStructure().generateWEBMFileStructureUpdateDatabase(startFolder=startFolder)

@structure_blueprint.route("/genstr")
@structure_blueprint.route("/genstr/<path:startFolder>")
def generuj_strukture(startFolder=''):
    from fileStructure import FileStructure
    return FileStructure().generateFileStructureUpdateDatabase(startFolder=startFolder)

@structure_blueprint.route("/strukturavideo")
@structure_blueprint.route("/strukturavideo/<path:startFolder>")
def strukturaVideo(startFolder=''):
    from videoFileStructure import VideoFileStructure
    return VideoFileStructure().getStructureJSON(startFolder=startFolder)

@structure_blueprint.route("/strukturafoldercontent/")
@structure_blueprint.route("/strukturafoldercontent/<path:folder>")
def strukturaFolderContent(folder=''):
    from fileStructure import FileStructure
    return FileStructure().getFolderContent(folder)


@structure_blueprint.route("/zwroczlisty")
def zwrzlisty():
    from fileStructure import FileStructure
    lista=['tmp']
    return FileStructure().zwroczlisty(lista)

@structure_blueprint.route("/struktura")
@structure_blueprint.route("/struktura/<path:startFolder>")
def struktura(startFolder=''):
    #zwraca pelna strukture plikow
    #jezeli w query jest parametr 'onlyfolders' wtedy zwraca skrocona wersje tylko z folderami
    #jezeli w query jest parametr 'onlyfiles' wtedy zwraca pelna wersje ale bez folderow
    #jezeli w query jest parametr 'ts' z wartoscia timestampu to zwraca tylko rekordy nowsze niz ten ts
    #jezeli w query jest parametr 'nothumbpath' to nie zwraca sciezki do thumba
    #jezeli w query jest parametr 'short' to zwraca tylko fullPath i ts'a
    from fileStructure import FileStructure
    ts=0
    tsArg = request.args.get('ts')
    if tsArg is not None:
        ts = int(tsArg)
    
    onlyFolders=False
    if request.args.get('onlyfolders') is not None:
        onlyFolders = True
    
    onlyFiles=False
    if request.args.get('onlyfiles') is not None:
        onlyFiles = True
        
    noThumbPath=False
    if request.args.get('nothumbpath') is not None:
        noThumbPath = True    
    
    short=False
    if request.args.get('short') is not None:
        short = True
  
    return FileStructure().getStructureJSON(startFolder=startFolder, tsSynchro=ts, onlyFolders=onlyFolders, noThumbPath=noThumbPath, short=short, onlyFiles=onlyFiles)


'''
def __szukaj_w_strukturze(katalog, tekst):
    struktura = __odczytaj_strukture()
    if constants.POLE_STRUKTURA_KATALOGOW in struktura:
        strukt = struktura[constants.POLE_STRUKTURA_KATALOGOW]
        katalog = katalog.strip("/")
        wynik = []
        tekst2 = tekst.replace(" ", "|")
        # return tekst2
        for kat in strukt:
            if kat.startswith(katalog):
                for poz in strukt[kat]:
                    # if tekst.lower() in poz[0].lower(): #strukt.items(): #return jsonify(strukt[kat])
                    if re.search(tekst2, poz[0], re.IGNORECASE):  # strukt.items(): #return jsonify(strukt[kat])
                        wynik.append(poz)
            # return jsonify(kat)
    return wynik
'''

