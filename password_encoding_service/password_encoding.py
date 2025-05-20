from cryptography.fernet import Fernet
import os

fernet_key = os.environ.get("FERNET_KEY")
fernet_key = str.encode(fernet_key)

class PasswordEncoding:
    @staticmethod
    def encrypt_the_ftp_user_password(password: str):
        encrypted_password = Fernet(fernet_key).encrypt(password.encode())
        encrypted_password = str(encrypted_password).split("'")
        return encrypted_password[1]
