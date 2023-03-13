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


def get_signed_pre_key_pair(username):
    with open(f"{username}_signed_pre_key_pair.txt", "rb") as binary_file:
        return binary_file.read()


def get_pre_key_pair(username):
    with open(f"{username}_pre_key_pair.txt", "rb") as binary_file:
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

sender_address = args[0]
user_details = get_user_details(user_id=None)
registration_id, pre_key_id, signed_pre_key_id = user_details['id'], 10222, 23223
identity_key_pair = identity_key.IdentityKeyPair.from_bytes(user_details['identity_key_pair'])
store = storage.InMemSignalProtocolStore(identity_key_pair, registration_id)
sender_details = req_session.get(f"{SERVER_URL}/users/", params={'username': sender_address}).json()['results'][-1]

sender_address_obj = address.ProtocolAddress(sender_details['username'], 1)

response = req_session.get(f"{SERVER_URL}/messages/",
                           params={'user': user_details['id'], 'from_user': sender_details['id']}).json()
# print(messages)
user_bundle = req_session.get(f"{SERVER_URL}/bundles/", params={'user': user_details['id']}).json()[
        "results"][0]
sender_bundle = req_session.get(f"{SERVER_URL}/bundles/", params={'user': sender_details['id']}).json()[
        "results"][0]
# print(f"sender bundle: {sender_bundle}")
index = 0
message_list = []
for message in response["results"]:
    bob_prekey = state.PreKeyRecord(pre_key_id, curve.KeyPair.from_public_and_private(
        user_bundle["pre_key"].encode("iso-8859-1"), get_pre_key_pair(user_details['username'])))
    store.save_pre_key(pre_key_id+index, bob_prekey)
    signed_prekey = state.SignedPreKeyRecord(
        signed_pre_key_id+index,
        42,
        curve.KeyPair.from_public_and_private(
            user_bundle['pre_key_sig'].encode('iso-8859-1'),
            get_signed_pre_key_pair(user_details["username"])
        ),
        user_bundle['one_time_pre_key'].encode('iso-8859-1'),
    )
    store.save_signed_pre_key(signed_pre_key_id+index, signed_prekey)

    sender_identity_key = identity_key.IdentityKey(sender_bundle['identity_key'].encode("iso-8859-1"))
    sender_bundle_obj = state.PreKeyBundle(
        sender_details['id'],
        1,
        pre_key_id+index,
        curve.PublicKey.deserialize(sender_bundle['pre_key'].encode("iso-8859-1")),
        signed_pre_key_id,
        curve.PublicKey.deserialize(sender_bundle['pre_key_sig'].encode("iso-8859-1")),
        sender_bundle['one_time_pre_key'].encode("iso-8859-1"),
        sender_identity_key,
    )
    # store.load_session(sender_address_obj)
    session.process_prekey_bundle(
        sender_address_obj,
        store,
        sender_bundle_obj,
    )
    # store.load_session(sender_address_obj)
    incoming_message = protocol.PreKeySignalMessage.try_from(message['message'].encode("iso-8859-1"))
    # store.save_identity(sender_address_obj, sender_identity_key)

    bob_plaintext = session_cipher.message_decrypt(
        store,
        sender_address_obj,
        incoming_message,
    )
    message.update({'message': bob_plaintext.decode("utf-8")})

    message_list.append(message)
response.update({'results': message_list})

return response
