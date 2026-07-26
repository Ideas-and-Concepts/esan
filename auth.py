import hashlib


def hash_password(password):

    return hashlib.sha256(
        password.encode()
    ).hexdigest()



def verify_password(password, password_hash):

    return (
        hash_password(password)
        == password_hash
    )