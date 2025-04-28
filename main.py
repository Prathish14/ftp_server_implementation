from pyftpdlib.handlers import FTPHandler, DTPHandler, TLS_FTPHandler
from pyftpdlib.servers import ThreadedFTPServer
from pyftpdlib.authorizers import DummyAuthorizer, AuthenticationFailed
from password_encoding_service.password_encoding import PasswordEncoding
from fotoowl_internal_apis.fotoowl_internal_apis import FotoowlInternalApis
from upload_service.b2_uploader import BotoB2
import logging
import os
import hashlib
from pathlib import Path
import mimetypes
import binascii
import numpy as np
import cv2 as cv

CERTFILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "ftpd.crt")
)

KEYFILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "ftpd.key")
)

public_ip_of_ftp_server = os.environ.get("PUBLIC_IP_OF_FTP_SERVER")

class AuthenticationHandler(DummyAuthorizer):
    def validate_authentication(self, username, password, handler):
        try:
            if not username or not password:
                raise KeyError
            
            encrypted_password = PasswordEncoding.encrypt_the_ftp_user_password(password=password)
            event_id = FotoowlInternalApis.verify_user_given_credentials(user_id=username, password=encrypted_password)

            if not event_id:
                raise KeyError
            else:
                self.add_user(username, '', "./image_storage", perm='elradfmwMT')

            print(f"Not raising error, i am allowing you, username:{username} and password: {password}!!!!")

        except KeyError:
            raise AuthenticationFailed



class MyHandler(TLS_FTPHandler):

    def on_connect(self):
        print("%s:%s connected" % (self.remote_ip, self.remote_port))

    def on_disconnect(self):
        try:
            print(f"this user got disconnected on disconnect: {self.username}")
            self.authorizer.remove_user(self.username)
        except Exception as e:
            print(f"while disconnecting some error occured!!!, error:{e}")

    def on_login(self, username):
        pass

    def on_logout(self, username):
        print(f"this user got disconnected on logout: {self.username}")
        self.authorizer.remove_user(self.username)

    def on_file_received(self, file):
        filename = Path(file).name
        print(filename)
        FotoowlInternalApis.send_image_info_to_fotoowl_for_processing(ftp_user_id=self.username, image_path=filename)

    def on_incomplete_file_received(self, file):
        os.remove(file)
    


def main():
    authorizer = DummyAuthorizer()
    authorizer.add_user('user', '12345', homedir='./image_storage', perm='elradfmwMT')
    #authorizer.add_anonymous(homedir='.',perm='elradfmwMT')

    handler = MyHandler
    handler.certfile = CERTFILE
    handler.keyfile = KEYFILE
    handler.authorizer = AuthenticationHandler()

    handler.banner = "fotoowl.ai ftp server is ready for use!!!"
    #handler.masquerade_address = public_ip_of_ftp_server 
    #handler.passive_ports = range(60000, 65535)

    logging.basicConfig(level=logging.DEBUG)

    server = ThreadedFTPServer(('0.0.0.0', 2121), handler)

    server.max_cons = 100
    server.max_cons_per_ip = 5

    server.serve_forever()

if __name__ == "__main__":
    main()