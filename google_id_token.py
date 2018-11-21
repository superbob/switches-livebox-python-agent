#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import json
import sys
import time

import jwt
import requests

GOOGLE_TOKEN_ENDPOINT_URL = 'https://www.googleapis.com/oauth2/v4/token'


def _generate_jwt(service_account_file, target_audience):
    """Generates a signed JSON Web Token using a Google API Service Account."""
    now = int(time.time())

    with io.open(service_account_file, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

    payload = {
        'iss': data['client_email'],
        'sub': data['client_email'],
        'aud': GOOGLE_TOKEN_ENDPOINT_URL,
        'exp': now + 3600,
        'iat': now,
        'target_audience': target_audience
    }

    additional_headers = {'kid': data['private_key_id']}
    signed_jwt = jwt.encode(payload, data['private_key'], headers=additional_headers, algorithm='RS256')
    return signed_jwt


def get_id_token(service_account_file, audience):
    """Obtains a Google ID token using a signed JWT."""
    data = {'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'assertion': _generate_jwt(service_account_file, audience)}

    res = requests.post(GOOGLE_TOKEN_ENDPOINT_URL, data=data).json()

    return res['id_token']


if __name__ == '__main__':
    if (len(sys.argv)) < 3:
        print('Missing arguments')
        print("Usage: {file} <service_account_file> <target_audience>".format(file=sys.argv[0]))
        sys.exit(1)
    id_token = get_id_token(sys.argv[1], sys.argv[2])
    print('The following Google ID token has been generated')
    print(id_token)
