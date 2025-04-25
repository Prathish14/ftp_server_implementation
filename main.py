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

user_event_info = {}

class AuthenticationHandler(DummyAuthorizer):
    def validate_authentication(self, username, password, handler):
        try:
            if not username or not password:
                raise KeyError
            
            ftp_user_id,event_id,event_user_id = FotoowlInternalApis.verify_user_given_credentials(user_id=username, password=password)

            if not event_id:
                raise KeyError
            else:
                self.add_user(username, '', "./image_storage", perm='elradfmwMT')
                user_event_info[username] = {
                    "username": username,
                    "event_id": event_id,
                    "event_user_id": event_user_id
                }

            print(f"Not raising error, i am allowing you, username:{username} and password: {password}!!!!")

        except KeyError:
            raise AuthenticationFailed


# It only handles control connections + Data connections
class MyHandler(TLS_FTPHandler):

    def on_connect(self):
        print("%s:%s connected" % (self.remote_ip, self.remote_port))

    def on_disconnect(self):
        print(f"this user got disconnected on disconnect: {self.username}")
        self.authorizer.remove_user(self.username)
        del user_event_info[self.username]

    def on_login(self, username):
        pass

    def on_logout(self, username):
        print(f"this user got disconnected on logout: {self.username}")
        self.authorizer.remove_user(self.username)
        del user_event_info[self.username]
        pass

    def on_file_received(self, file):
        event_id = user_event_info[self.username].get("event_id")
        event_user_id = user_event_info[self.username].get("event_user_id")
        filename = Path(file).name
        mime_type, encoding = mimetypes.guess_type(file)
        

        with open(file, 'rb') as file_data:
            binary_data = file_data.read()
            print(binary_data)

        content = binascii.b2a_base64(binary_data).decode("utf8")
        content = binascii.a2b_base64(content)
        jpg_as_np = np.frombuffer(content, dtype=np.uint8)
        img = cv.imdecode(jpg_as_np, flags=1)
        img_width = img.shape[1]
        img_height = img.shape[0]

        raw_id,file_path = BotoB2.upload_ftp_uploaded_image_to_event_bucket(content=binary_data, content_type=mime_type, file_name=filename,
                                                         event_id=event_id, event_user_id=event_user_id)
        
        if raw_id and file_path:
            FotoowlInternalApis.send_uploded_image_info_to_event_picture_process(event_id=event_id, image_name=filename, mime_type=mime_type,
                                                                                 b2_id=raw_id, path=filename, user_id=event_user_id, 
                                                                                 height=img_height, width=img_width)
        os.remove(file)


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
    logging.basicConfig(level=logging.DEBUG)

    server = ThreadedFTPServer(('0.0.0.0', 2121), handler)
    server.serve_forever()

if __name__ == "__main__":
    main()