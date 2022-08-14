
#from pyfcm import FCMNotification
import pyfcm
import requests
import constants
import json


class Firebasenotification:

    def __init__(self, logger):
        #self.push_service = pyfcm.FCMNotification(api_key=os.getenv('MY_FIREBASE_API_KEY'))
        #initialize_app(credential=credentials.Certificate(os.getenv('FIREBASE_JSON')))
        self.logger = logger
        return

    def notify(self, dane=''):

        parametry = {
            "Content-Type": "application/json",
            "Authorization": "key=AAAA0FewZwk:APA91bFG2zaE077_ztGG6g9oFd3jDUJCu3GbvM2XiJpDn2Fxjii5CkEZMkvADSQ0KAVK_7bfVwpGb_p6zeDznoRgJ_4sefLE3oBbTOWlk57Dl3ESsggfQ2Liiuk0RS47M3jJ1KSB2Rfn"
        }

        body = {"to": "/topics/temat","data" : {constants.FIREBASE_DANE: dane}}

        try:
            response = requests.post('https://fcm.googleapis.com/fcm/send', data=json.dumps(body), headers=parametry, timeout=15)
        except Exception as serr:
            self.logger.error('firebase', 'Nie udalo sie wyslac firebase: ' + str(serr))

	if response.status_code != 200:
            self.logger.error('firebase', 'Bledny kod powrotu z firebase po post: ' + str(response.status_code))

