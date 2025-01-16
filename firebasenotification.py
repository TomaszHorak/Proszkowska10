# from pyfcm import FCMNotification
import requests
import constants
import json
import google.auth.transport.requests
from google.oauth2 import service_account
import firebase_admin
from firebase_admin import credentials
from os import environ


# Trzeba ustawic zmienna na serwerze: export GOOGLE_APPLICATION_CREDENTIALS="/home/user/Downloads/service-account-file.json"
# wskazac sciezke do pliku z service-account, ktory jest pobrane z firebase console
# link do instrukcji: https://firebase.google.com/docs/cloud-messaging/migrate-v1#python_1


PROJECT_ID = 'proszkowska10'
BASE_URL = 'https://fcm.googleapis.com'
FCM_ENDPOINT = 'v1/projects/' + PROJECT_ID + '/messages:send'
FCM_URL = BASE_URL + '/' + FCM_ENDPOINT
SCOPES = ['https://www.googleapis.com/auth/firebase.messaging']
SERVICE_ACCOUNT_FILE = '/home/pi/python/system_podlewania/service-account.json'


class Firebasenotification:

    def __init__(self, logger):
        # self.push_service = pyfcm.FCMNotification(api_key=os.getenv('MY_FIREBASE_API_KEY'))
        environ['GOOGLE_APPLICATION_CREDENTIALS'] = SERVICE_ACCOUNT_FILE
        #firebase_admin.initialize_app(credential=credentials.Certificate(SERVICE_ACCOUNT_FILE))
        firebase_admin.initialize_app()
        self.logger = logger
        self.__refresh_access_token()

    def __refresh_access_token(self):
        """Retrieve a valid access token that can be used to authorize requests.
          :return: Access token.
        """
        try:
            credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE
                                                                                , scopes=SCOPES)
            request = google.auth.transport.requests.Request()
            credentials.refresh(request)
            self.__token = credentials.token

        except Exception as err:
            self.logger.error('firebase', 'token', 'Nie moge uzyskac tokeny firebase:' + str(err))
            self.__token = None

    def notify(self, dane=''):

        if self.__token is None:
            self.__refresh_access_token()
        if self.__token is None:
            self.logger.error('firebase', 'wysylanie', 'Proba wyslania firebase przy braku tokenu')
            return
        headers = {
            'Authorization': 'Bearer ' + self.__token,
            'Content-Type': 'application/json; UTF-8',
        }

        body = {
            "message": {
                "topic": "temat",
                #"notification": {
                #    "title": "Breaking News",
                #    "body": "New news story available."
                #},
                "data": {constants.TS: str(dane)}
            }
        }

        try:
            response = requests.post(FCM_URL, data=json.dumps(body), headers=headers)
            # response = requests.post('https://fcm.googleapis.com/v1/projects/proszkowska10/messages:send', data=json.dumps(body), headers=parametry, timeout=15)
            if response.status_code != 200:
                self.logger.error('firebase', 'firebase',
                                  'Bledny kod powrotu z firebase po post: ' + str(response.status_code))

        except Exception as serr:
            self.logger.error('firebase', 'firebase', 'Nie udalo sie wyslac firebase: ' + str(serr))
