from eth_account.messages import defunct_hash_message
from utils.get_web3 import get_web3


def validate(signature: str, uuid_session: str):
    w3 = get_web3()
    hash_uuid_session = defunct_hash_message(text=uuid_session)
    signing_address = w3.eth.account.recoverHash(message_hash=hash_uuid_session, signature=signature)
    return signing_address
