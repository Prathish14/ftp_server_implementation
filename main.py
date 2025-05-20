import asyncio
import asyncssh
import os
import logging
import signal
from pathlib import Path
from datetime import datetime
from password_encoding_service.password_encoding import PasswordEncoding
from fotoowl_internal_apis.fotoowl_internal_apis import FotoowlInternalApis
from redis_service.redis_sync_service import RedisClient

logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(levelname)s: %(message)s')

KEYFILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "ssh_host_key.key")
)

ssh_host_key = asyncssh.read_private_key(KEYFILE)

redis_client = RedisClient()

class SSHServerHandler(asyncssh.SSHServer):
    def connection_made(self, conn):
        logging.debug(f"Connection from {conn.get_extra_info('peername')}")
        self.username = None

    def connection_lost(self, exc):
        # Remove user info from redis on disconnect
        if hasattr(self, 'username') and self.username:
            redis_client.delete_user_info_hash_set(username=self.username)
            logging.debug(f"User {self.username} removed from redis on disconnect.")
        logging.debug("Connection closed")

    def begin_auth(self, username):
        self.username = username
        return True

    def password_auth_supported(self):
        return True

    def validate_password(self, username, password):
        encrypted_password = PasswordEncoding.encrypt_the_ftp_user_password(password=password)
        event_id,event_creator_id,collection_id = FotoowlInternalApis.verify_user_given_credentials(username=username, password=encrypted_password)

        if not event_id:
            logging.debug(f"Login failed: {username}")
            return False
        else:
            user_info = {
                "event_id": event_id,
                "event_creator_id": event_creator_id,
                "collection_id": collection_id
            }
            logging.debug(f"Login successful: {username}")
            redis_client.store_user_info(username=username, info=user_info)
            return True

# Custom SFTP Server
class MySFTPServer(asyncssh.SFTPServer):
    def __init__(self, chan):
        super().__init__(chan)
        self.username = chan.get_extra_info('username')
        today_str = datetime.now().strftime('%Y-%m-%d')
        user_info_dict = redis_client.get_user_info(username=self.username)
        event_id = user_info_dict.get("event_id")
        event_creator_id = user_info_dict.get("event_creator_id")
        # Ensure the full custom folder path exists
        inside_folder_path = os.path.join(today_str, str(event_id), str(event_creator_id), "images")
        self.root_dir = os.path.abspath(inside_folder_path)
        os.makedirs(self.root_dir, exist_ok=True)

    def _realpath(self, path):
        if isinstance(path, bytes):
            path = path.decode("utf-8")
        filename = os.path.basename(path)
        full_path = os.path.realpath(os.path.join(self.root_dir, filename))
        print(f"Real path: {full_path}")
        return full_path
        

    async def open(self, path, pflags, attrs):
        if not (pflags & asyncssh.FXF_WRITE or pflags & asyncssh.FXF_CREAT):
            raise PermissionError("Only write access is allowed")
        real_path = self._realpath(path)
        logging.debug(f"User {self.username} opening file: {real_path}")

        # === Duplicate File Handling ===
        if os.path.exists(real_path):
            base = Path(real_path).stem
            ext = Path(real_path).suffix
            parent = Path(real_path).parent

            counter = 1
            while True:
                new_name = f"{base}_{counter}{ext}"
                new_path = parent / new_name
                if not new_path.exists():
                    real_path = str(new_path)
                    break
                counter += 1

            logging.debug(f"Duplicate detected. Renamed to: {real_path}")
        
        #filename = Path(real_path).name
        user_info_dict = redis_client.get_user_info(username=self.username)
        user_info_dict["file_path"] = real_path
        redis_client.store_upload_info(filename=real_path, info=user_info_dict)

        mode = 'r+b' if os.path.exists(real_path) else 'w+b'
        if pflags & asyncssh.FXF_TRUNC:
            mode = 'w+b'
        file_obj = open(real_path, mode)
        return file_obj
    
    # ❌ Block all other unwanted operations
    async def listdir(self, path):
        raise PermissionError("Directory listing not allowed")

    async def stat(self, path):
        raise PermissionError("Stat not allowed")

    async def lstat(self, path):
        raise PermissionError("Lstat not allowed")

    async def remove(self, path):
        raise PermissionError("Delete not allowed")

    async def rename(self, oldpath, newpath):
        raise PermissionError("Rename not allowed")

    async def mkdir(self, path, attrs):
        raise PermissionError("Directory creation not allowed")

    async def rmdir(self, path):
        raise PermissionError("Directory removal not allowed")

"""***********************************************************************"""
server = None  # Global to allow shutdown via signal handler

async def start_server():
    global server
    logging.debug("Starting SFTP server...")

    server = await asyncssh.listen(
        '', 8022,
        server_host_keys=[ssh_host_key],
        server_factory=SSHServerHandler,
        sftp_factory=MySFTPServer
    )

    logging.info("✅ SFTP server running on port 8022")


def shutdown():
    global server
    if server:
        logging.info("🔴 Shutting down SFTP server...")
        server.close()


async def main():
    await start_server()
    await server.wait_closed()
    logging.info("🛑 SFTP server stopped and port released")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown)

    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
        logging.info("🛑 Event loop closed.")
