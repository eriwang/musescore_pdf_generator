import os
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

_SCOPES = ['https://www.googleapis.com/auth/drive']
_TOKEN_FILENAME = 'token.pickle'


def get_credentials():
    credentials = _load_token_file(_TOKEN_FILENAME) if os.path.exists(_TOKEN_FILENAME) else None
    if credentials is not None and credentials.valid:
        return credentials

    if credentials is not None and credentials.expired and credentials.refresh_token is not None:
        credentials.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', _SCOPES)
        credentials = flow.run_local_server(port=0)

    _dump_token_file(credentials, _TOKEN_FILENAME)
    return credentials


def _load_token_file(filename):
    with open(filename, 'rb') as token:
        return pickle.load(token)


def _dump_token_file(credentials, filename):
    with open(filename, 'wb') as token:
        pickle.dump(credentials, token)
