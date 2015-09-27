import json
import urllib
import webbrowser

import gevent
import requests

import charges
from helpers import log_response

CLIENT_ID = '2667'
CLIENT_SECRET = 'srDrmU3yf452HuFF63HqHEt25pa5DexZ'
BASE_URL = "https://api.venmo.com/v1"
PAYMENTS_BASE_URL = "{base_url}/payments".format(base_url=BASE_URL)

DB_FILE = 'db.json'


def authorization_url():
    scopes = [
        'make_payments',
        'access_feed',
        'access_profile',
        'access_email',
        'access_phone',
        'access_balance',
        'access_friends',
    ]
    params = {
        'client_id': CLIENT_ID,
        'scope': " ".join(scopes),
        'response_type': 'code',
    }
    return "{base_url}/oauth/authorize?{params}".format(
        base_url=BASE_URL,
        params=urllib.urlencode(params)
    )


def payments_url_with_params(params):
    return "{payments_base_url}?{params}".format(
        payments_base_url=PAYMENTS_BASE_URL,
        params=urllib.urlencode(params),
    )


def get_code():
    webbrowser.open(authorization_url())
    return raw_input("Code: ")


def get_access_token():
    try:
        return read_access_token_from_db()
    except IOError:
        write_access_token_to_db()
        return read_access_token_from_db()


def read_access_token_from_db():
    with open(DB_FILE, 'r') as data_file:
        data = json.load(data_file)
        return data.get('access_token')


def write_access_token_to_db():
    authorization_code = get_code()
    access_token = access_token_from_code(authorization_code)
    with open(DB_FILE, 'w') as data_file:
        db = {
            'access_token': access_token
        }
        data_file.write(json.dumps(db))


def access_token_from_code(authorization_code):
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": authorization_code,
    }
    url = "{}/oauth/access_token".format(BASE_URL)
    response = requests.post(url, data)
    response_dict = response.json()
    return response_dict['access_token']


def create_rent_charge(access_token, user):
    params = {
        'access_token': access_token,
        'note': 'Rent',
        'audience': 'private',
    }
    params.update(user)
    response = requests.post(
        payments_url_with_params(params)
    )
    log_response(response)


if __name__ == '__main__':
    access_token = get_access_token()
    jobs = [gevent.spawn(create_rent_charge,
                         access_token,
                         roommate)
            for roommate in charges.roommates]
    gevent.joinall(jobs)
