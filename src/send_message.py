import json
import os
import requests

from signal_protocol import curve, identity_key, state, storage, session, address, protocol
from signal_protocol import session_cipher


def write_identity_key_to_localfile(key, user='unknown'):
    with open(f"{user}.txt", "wb") as binary_file:
        # Write bytes to file
        binary_file.write(key)


def get_identity_key_pair(username):
    with open(f"{username}.txt", "rb") as binary_file:
        return binary_file.read()


def get_user_details(user_id=None):
    if user_id:
        _user_details = session.get(f"{SERVER_URL}/users/{user_id}/").json()
    else:
        with open("user.json") as json_file:
            _user_details = json.load(json_file)
        _user_details['identity_key_pair'] = get_identity_key_pair(_user_details['username'])
        return _user_details


SERVER_URL = os.getenv('SERVER_URL') or "http://20.26.15.16:8000"
USER = os.getenv('USERNAME') or "admin"
PASSWORD = os.getenv('PASSWORD') or "reset123"

req_session = requests.Session()
req_session.auth = (USER, PASSWORD)

recipient_address, message = args
user_details = get_user_details(user_id=None)
registration_id, pre_key_id, signed_pre_key_id = user_details['id'], 10222, 23223
identity_key_pair = identity_key.IdentityKeyPair.from_bytes(user_details['identity_key_pair'])
store = storage.InMemSignalProtocolStore(identity_key_pair, registration_id)
recipient_details = req_session.get(f"{SERVER_URL}/users/", params={'username': recipient_address}).json()['results'][0]

recipient_address_obj = address.ProtocolAddress(recipient_address, 1)
if recipient_details:
    recipient_bundle = req_session.get(f"{SERVER_URL}/bundles/", params={'user': recipient_details['id']}).json()[
        "results"][0]
else:
    raise ValueError("User not found not")
recipient_bundle_obj = state.PreKeyBundle(
    recipient_details['id'],
    1,
    pre_key_id,
    curve.PublicKey.deserialize(recipient_bundle['pre_key'].encode("iso-8859-1")),
    signed_pre_key_id,
    curve.PublicKey.deserialize(recipient_bundle['pre_key_sig'].encode("iso-8859-1")),
    recipient_bundle['one_time_pre_key'].encode("iso-8859-1"),
    identity_key.IdentityKey(recipient_bundle['identity_key'].encode("iso-8859-1")),
)
session.process_prekey_bundle(
    recipient_address_obj,
    store,
    recipient_bundle_obj,
)
ss = store.load_session(recipient_address_obj)
ciphertext = session_cipher.message_encrypt(store, recipient_address_obj, message.encode('utf8'))
message_res = req_session.post(f"{SERVER_URL}/messages/", data={
    "message": ciphertext.serialize().decode("iso-8859-1"),
    "user": recipient_details['id'],
    "from_user": user_details['id']
}).json()
assert message_res['message'].encode("iso-8859-1") == ciphertext.serialize()
return message_res
