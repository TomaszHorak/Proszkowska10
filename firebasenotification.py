
#from pyfcm import FCMNotification
import pyfcm
import requests
import logging
import constants
#import firebase_admin
#from firebase_admin import messaging
MY_API_KEY="AAAA0FewZwk:APA91bFG2zaE077_ztGG6g9oFd3jDUJCu3GbvM2XiJpDn2Fxjii5CkEZMkvADSQ0KAVK_7bfVwpGb_p6zeDznoRgJ_4sefLE3oBbTOWlk57Dl3ESsggfQ2Liiuk0RS47M3jJ1KSB2Rfn"

class Firebasenotification():
    #cred = firebase_admin.credentials.Certificate(constants.KATALOG_GLOWNY + "/proszkowska10-firebase.json")
    #default_app = firebase_admin.initialize_app(cred)

    def __init__(self):
        self.push_service = pyfcm.FCMNotification(api_key=MY_API_KEY)
        self.logger = logging.getLogger(constants.NAZWA_LOGGERA)
        return

    def notify(self, obszar, komunikat, dane=''):

        """nagl = {'Content-Type': 'application/json',
            #'Authorization': 'Bearer ' + MY_API_KEY
            'Authorization': 'key='+MY_API_KEY }"""

        data = {
            #"to": "/topics/temat",
            #"notification": {
            #    "title": "tytul",
            #    "body": "tresc"
            #},
            #"message": "widomosc",
            #"data": {
            constants.OBSZAR: obszar,
            constants.RODZAJ_KOMUNIKATU: komunikat,
            constants.FIREBASE_DANE: dane
        #}
        }
        #result = messaging.send(message, app=self.default_app)

        #pierwsze ID jest emulatoa, drugie moje SONY
        #tokencli = ['c7Z8_l4XD3w:APA91bEz0fULKXriSHb6iVWC_CzuZz0Gp4DDRKYLOQ_3B6oPoYGIcMQGxu53A62dnonDZdAOJibvJ66I8Fc3UoOhfJbUc90IhntzwRlRldCvEIhkDlR7BhK1fk6DdD92Zx7eQBBOccvf',
        #'fYiAFSGvQeA:APA91bFXVeRxzPzxRJQeVZ1KVA9dKrSUxIhxc7hQSuVkKTw6ZQN6ABKL3w9iXuvviJU6Ki25hkGnUUsx1LgLflvUtcnYdXAJ-yh3Wy9OHH6i_nR5j7D1sU42VbXL-OpjYG9-vYnRIhsY']
        try:
            result = self.push_service.notify_topic_subscribers(topic_name='temat', data_message=data, time_to_live=100000)
            #emulator = 'c7Z8_l4XD3w:APA91bEz0fULKXriSHb6iVWC_CzuZz0Gp4DDRKYLOQ_3B6oPoYGIcMQGxu53A62dnonDZdAOJibvJ66I8Fc3UoOhfJbUc90IhntzwRlRldCvEIhkDlR7BhK1fk6DdD92Zx7eQBBOccvf'
            #result = self.push_service.multiple_devices_data_message(registration_ids=tokencli, data_message=data)
            #result = self.push_service.send_request(payloads=data)
            #result = self.push_service.topic_subscribers_data_message(topic_name='temat', data_message=data)
                #notify_single_device(registration_id=emulator, data_message=data)
            #url = 'https://fcm.googleapis.com/fcm/send'
            #url = 'https://gcm-http.googleapis.com/gcm/send'
            #result = requests.post(url, data=json.dumps(data), headers=nagl)
            # self.logger.info('Wysylam powiadomienie firebase: ' + obszar + ', ' + komunikat + '. Rezultat: ' + str(result))
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout
                , pyfcm.errors.FCMServerError) as serr:
            #TODO ten error pyfcm.errors.FCMServerError nie wystepuje tak bezposrednio, wzialem go z opisu bledu w logu
            self.logger.warning('Blad wysylania firebasenotification: ' + str(serr))
        # TODO dorobic kontrole zwrotki, ktora jest w JSON, jesli jest blad to zwrocic false
        return
