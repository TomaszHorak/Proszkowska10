from flask import url_for, Blueprint, render_template

from auth import token_required
from tokeny import Tokeny
from os import path
from flask import current_app as app
from videoFileStructure import VideoFileStructure
from narzedzia import czy_plik_istnieje_abort

video_blueprint = Blueprint('video', __name__, template_folder='templates')

@video_blueprint.route("/stream_video/<path:nazwa_pliku>") #TODO tutaj powinna byc kontrola autoryzacji dodac pozniej z UUID jest nizej
def streamvideo(nazwa_pliku):
    czy_plik_istnieje_abort(nazwa_pliku)
    thumbPath = VideoFileStructure().getThumbPathByFileName(nazwa_pliku, fullPath=True)
    #return url_for('pliki.zwroc_plik', nazwa_pliku=thumbPath)
    tok: TokenyDefinition = Tokeny().register(thumbPath, admin=False, write=False, download=True, valid_for_days=1)
    return render_template('video.html',
                           plik=url_for('pliki.zwroc_plik_uid', uid_pliku=str(tok.uuid)),
                           nazwa_pliku=path.basename(nazwa_pliku))
    

    #return render_template('video.html',
    #                       plik=url_for('pliki.zwroc_plik_uid', uid_pliku=str(tok.uuid)),url_for('pliki.zwroc_plik_uid', uid_pliku=str(tok.uuid))
    #                       nazwa_pliku=path.basename(path.basename(nazwa_pliku)))
    # plik=url_for('pliki.zwroc_plik', nazwa_pliku=plik_thumb[len(constants.PREFIX_MNT):]))
    
@video_blueprint.route("/stream_videouid/<uuid:uid_katalogu>/<path:nazwa_pliku>") # TOOD dlaczego nazwa katalogu, streamowanie powinno byc z dokladnoscia do pliku z nie katalogu
def stream_videouid(uid_katalogu, nazwa_pliku):
    token = Tokeny().get_one_token(uid_katalogu)
    if not token.is_valid():
        return 'Link wygasl.', 400
    return render_template('video.html',
                           plik=url_for('thumb.returnThumbBigUID', uid_katalogu=uid_katalogu, nazwa_pliku=nazwa_pliku),
                           nazwa_pliku=path.basename(nazwa_pliku))
