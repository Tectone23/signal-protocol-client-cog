import json

import time
from typing.io import BinaryIO

from signal_protocol import curve, identity_key, state, storage, session, address
from signal_protocol import session_cipher

from src import message_client


def write_identity_key_to_localfile(key, user='unknown'):
    with open(f"{user}.txt", "wb") as binary_file:
        # Write bytes to file
        binary_file.write(key)


def login_or_register(username, email):
    user_details = message_client.send_get_request('users/', params={'username': username})
    if user_details['count'] == 0:
        user_details = message_client.send_post_request('users/', data={
            'username': username,
            'email': email,
        })
    else:
        user_details = user_details['results'][0]
    with open("user.json", 'w+') as json_file:
        identity_key_pair = identity_key.IdentityKeyPair.generate()
        json.dump(user_details, json_file)
        write_identity_key_to_localfile(identity_key_pair.serialize(), username)
    return "success"


def get_identity_key_pair(username):
    with open(f"{username}.txt", "rb") as binary_file:
        return binary_file.read()


def get_user_details(user_id=None):
    if user_id:
        return message_client.send_get_request(f'users/{user_id}/')
    with open("user.json") as json_file:
        user_details = json.load(json_file)
        user_details['identity_key_pair'] = get_identity_key_pair(user_details['username'])
        return user_details


def generate_and_store_pre_key():
    user_details = get_user_details(user_id=None)
    registration_id, pre_key_id, signed_pre_key_id = user_details['id'], user_details['id'] + 10, user_details[
        'id'] + 33
    identity_key_pair = identity_key.IdentityKeyPair.from_bytes(user_details['identity_key_pair'])
    pre_key_pair = curve.KeyPair.generate()
    store = storage.InMemSignalProtocolStore(identity_key_pair, registration_id)

    signed_pre_key_pair = curve.KeyPair.generate()
    serialized_signed_pre_pub_key = signed_pre_key_pair.public_key().serialize()
    signed_pre_key_signature = (
        store.get_identity_key_pair().private_key()
            .calculate_signature(serialized_signed_pre_pub_key)
    )

    pre_key_record = state.PreKeyRecord(pre_key_id, pre_key_pair)
    store.save_pre_key(pre_key_id, pre_key_record)

    signed_prekey = state.SignedPreKeyRecord(
        signed_pre_key_id,
        int(time.time()),
        signed_pre_key_pair,
        signed_pre_key_signature,
    )
    store.save_signed_pre_key(signed_pre_key_id, signed_prekey)
    message_client.send_post_request('bundles/', data={
        "identity_key": identity_key_pair.identity_key().serialize(),
        "pre_key": pre_key_pair.public_key().serialize(),
        "pre_key_sig": signed_pre_key_pair.serialize(),
        "one_time_pre_key": signed_pre_key_signature,
        "user": user_details['id']
    })
    return store


def create_or_get_session():
    pass


def send_message(recipient_address, device_id, message):
    user_details = get_user_details(user_id=None)
    registration_id, pre_key_id, signed_pre_key_id = user_details['id'], user_details['id'] + 10, user_details[
        'id'] + 33
    identity_key_pair = identity_key.IdentityKeyPair.from_bytes(user_details['identity_key_pair'])
    store = storage.InMemSignalProtocolStore(identity_key_pair, registration_id)

    recipient_address = address.ProtocolAddress(recipient_address, device_id)
    recipient_details = message_client.send_get_request('users', params={'username': recipient_address})['results'][0]
    recipient_bundle = message_client.get_bundle(recipient_address)
    session.process_prekey_bundle(
        recipient_address,
        store,
        recipient_bundle,
    )
    ciphertext = session_cipher.message_encrypt(store, recipient_address, message.encode('utf8'))
    message_client.send_post_request('messages/', data={
        "message": ciphertext,
        "user": user_details['id'],
        "from_user": recipient_details[id]
    })


def get_users():
    return message_client.send_get_request('users/')


if __name__ == '__main__':
    # print(login_or_register('test1', 'test@gnmail.org'))
    print(generate_and_store_pre_key())
    print(get_users())
