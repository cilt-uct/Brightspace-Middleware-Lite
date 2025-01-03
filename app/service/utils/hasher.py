import bcrypt

class Hasher():
    # Hash a password using bcrypt
    @staticmethod
    def get_password_hash(password):
        pwd_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
        return hashed_password

    # Check if the provided password matches the stored password (hashed)
    @staticmethod
    def verify_password(plain_password, hashed_password):
        if not plain_password or not hashed_password:
            return False

        if isinstance(plain_password, (bytes, bytearray)):
            password_byte_enc = plain_password
        else:
            password_byte_enc = plain_password.encode('utf-8')

        if isinstance(hashed_password, (bytes, bytearray)):
            hashed_password_byte_enc = hashed_password
        else:
            hashed_password_byte_enc = hashed_password.encode('utf-8')

        return bcrypt.checkpw(password = password_byte_enc , hashed_password = hashed_password_byte_enc)
