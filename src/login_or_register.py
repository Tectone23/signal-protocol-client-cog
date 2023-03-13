import os
import time

import requests
import json


from signal_protocol import curve, identity_key, state, storage

username = args[0]
email = args[1]

SERVER_URL = os.getenv('SERVER_URL') or "http://20.26.15.16:8000"
USER = os.getenv('USERNAME') or "admin"
PASSWORD = os.getenv('PASSWORD') or "reset123"

session = requests.Session()
session.auth = (USER, PASSWORD)


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
        return session.get(f"{SERVER_URL}/users/{user_id}/").json()
    if os.path.exists("user.json"):
        with open("user.json") as json_file:
            _user_details = json.load(json_file)
            return _user_details
    resp = session.get(f"{SERVER_URL}/users/", params={'username': username}).json()
    if resp['count']:
        with open("user.json", 'w+') as json_file:
            json.dump(resp['results'][0], json_file)
    return resp['results'][0] if resp['count'] else None


user_details = get_user_details(user_id=None)
print(user_details)
if not user_details or user_details["username"] != username:
    data = {
        "username": username,
        "email": email,
    }
    print("inside user details:")
    print(data)
    resp = session.post(f"{SERVER_URL}/users/", data=data)
    print(resp.text)
    resp.raise_for_status()
    user_details = resp.json()
    with open("user.json", 'w+') as json_file:
        json.dump(user_details, json_file)
identity_key_pair = identity_key.IdentityKeyPair.generate()

with open(f"{username}.txt", "wb") as binary_file:
    # Write bytes to file
    binary_file.write(identity_key_pair.serialize())

registration_id, pre_key_id, signed_pre_key_id = user_details['id'], 10222, 23223

pre_key_pair = curve.KeyPair.generate()
with open(f"{username}_pre_key_pair.txt", "wb") as binary_file:
    # Write bytes to file
    binary_file.write(pre_key_pair.private_key().serialize())

store = storage.InMemSignalProtocolStore(identity_key_pair, registration_id)

signed_pre_key_pair = curve.KeyPair.generate()
serialized_signed_pre_pub_key = signed_pre_key_pair.public_key().serialize()
signed_pre_key_signature = (
    store.get_identity_key_pair().private_key()
            .calculate_signature(serialized_signed_pre_pub_key)
)
with open(f"{username}_signed_pre_key_pair.txt", "wb") as binary_file:
    # Write bytes to file
    binary_file.write(signed_pre_key_pair.private_key().serialize())

pre_key_record = state.PreKeyRecord(pre_key_id, pre_key_pair)
store.save_pre_key(pre_key_id, pre_key_record)

signed_prekey = state.SignedPreKeyRecord(
    signed_pre_key_id,
    42,
    signed_pre_key_pair,
    signed_pre_key_signature,
)
store.save_signed_pre_key(signed_pre_key_id, signed_prekey)
# import sys
# print(sys.getdefaultencoding())
# print(store.get_identity_key_pair().identity_key().serialize() == str(store.get_identity_key_pair().identity_key().serialize(), 'iso-8859-1').encode('iso-8859-1'))
# print({
#     "identity_key":  store.get_identity_key_pair().identity_key().serialize().decode('iso-8859-1'),
#     "pre_key": pre_key_pair.public_key().serialize().decode('iso-8859-1'),
#     "pre_key_sig": signed_pre_key_pair.serialize().decode('iso-8859-1'),
#     "one_time_pre_key": signed_pre_key_signature.decode('iso-8859-1'),
#     "user": user_details['id']
# })
resp = session.post(f"{SERVER_URL}/bundles/", data={
    "identity_key":  store.get_identity_key_pair().identity_key().serialize().decode('iso-8859-1'),
    "pre_key": pre_key_pair.public_key().serialize().decode('iso-8859-1'),
    "pre_key_sig": signed_pre_key_pair.serialize().decode('iso-8859-1'),
    "one_time_pre_key": signed_pre_key_signature.decode('iso-8859-1'),
    "user": user_details['id']
}).json()

print(resp)
assert identity_key_pair.identity_key().serialize() == store.get_identity_key_pair().identity_key().serialize()
assert resp["identity_key"].encode("iso-8859-1") == store.get_identity_key_pair().identity_key().serialize()
assert resp["pre_key"].encode("iso-8859-1") == pre_key_pair.public_key().serialize()
assert resp["pre_key_sig"].encode("iso-8859-1") == signed_pre_key_pair.serialize()
assert resp["one_time_pre_key"].encode("iso-8859-1") == signed_pre_key_signature
return user_details
