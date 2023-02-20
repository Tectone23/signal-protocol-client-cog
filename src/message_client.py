"""Client wrapper to talk to message server"""
import os

import requests

SERVER_URL = os.getenv('SERVER_URL') or "http://localhost:8000"
USER = os.getenv('USERNAME') or "admin"
PASSWORD = os.getenv('PASSWORD') or "reset123"


def send_get_request(uri, params=None) -> dict:
    session = requests.Session()
    session.auth = (USER, PASSWORD)
    resp = session.get(f"{SERVER_URL}/{uri}", params=params)
    resp.raise_for_status()
    return resp.json()


def send_post_request(uri, data: dict = None) -> dict:
    session = requests.Session()
    session.auth = (USER, PASSWORD)
    resp = session.post(f"{SERVER_URL}/{uri}",
                        data=data)
    resp.raise_for_status()
    return resp.json()


def send_put_request(uri, data: dict = None) -> dict:
    session = requests.Session()
    session.auth = (USER, PASSWORD)
    resp = session.put(f"{SERVER_URL}/{uri}", data=data)
    resp.raise_for_status()
    return resp.json()


def send_patch_request(uri, data: dict = None) -> dict:
    session = requests.Session()
    session.auth = (USER, PASSWORD)
    resp = session.patch(f"{SERVER_URL}/{uri}", data=data)
    resp.raise_for_status()
    return resp.json()


def get_bundle(recipient_address):
    user_details = send_get_request('users/', params={'username': recipient_address})
    if user_details['count']:
        return send_get_request('bundle/', params={'user': user_details[0]['id']})
    else:
        raise ValueError("User not found not")
