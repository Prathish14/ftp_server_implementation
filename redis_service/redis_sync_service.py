import redis
import os
import logging
from threading import Lock

class RedisClient:
    _instance = None
    _lock = Lock()  # To make it thread-safe

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:  # Double-checked locking
                    cls._instance = super(RedisClient, cls).__new__(cls)
                    cls._instance._initialize(*args, **kwargs)
        return cls._instance

    def _initialize(self):
        self.redis_url = os.environ.get("REDIS_URL")
        self.redis_client = None
        self._connect()

    def _connect(self):
        if not self.redis_client:
            try:
                self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
                self.redis_client.ping()
                logging.info("[RedisClient] Connected to Redis.")
            except redis.RedisError as e:
                logging.error(f"[RedisClient] Redis connection failed: {e}", exc_info=True)
                raise

    def store_upload_info(self, filename: str, info: dict, ttl_seconds: int = None):
        key = f"upload:{filename}"
        try:
            for k, v in info.items():
                self.redis_client.hset(key, k, str(v))
            if ttl_seconds:
                self.redis_client.expire(key, ttl_seconds)
            logging.info(f"[RedisClient] Stored upload info: {key}")
        except redis.RedisError as e:
            logging.error(f"[RedisClient] Failed to store HSET: {e}", exc_info=True)

    def get_upload_info(self, filename: str):
        key = f"upload:{filename}"
        try:
            data = self.redis_client.hgetall(key)
            if data:
                logging.info(f"[RedisClient] Retrieved data for: {key}")
                return data
            else:
                logging.info(f"[RedisClient] No data found for: {key}")
                return None
        except redis.RedisError as e:
            logging.error(f"[RedisClient] Failed to get data: {e}", exc_info=True)
            return None

    def delete_upload_info_hash_set(self, filename: str) -> bool:
        hash_key = f"upload:{filename}"
        try:
            result = self.redis_client.delete(hash_key)
            if result == 1:
                logging.info(f"[RedisClient] Deleted hash_key: '{hash_key}'")
                return True
            else:
                logging.info(f"[RedisClient] hash_key: '{hash_key}' not found to delete")
                return False
        except redis.RedisError as e:
            logging.error(f"[RedisClient] Failed to delete hash_key '{hash_key}': {e}", exc_info=True)
            return False

    def store_user_info(self, username: str, info: dict, ttl_seconds: int = None):
        key = f"userinfo:{username}"
        try:
            for k, v in info.items():
                self.redis_client.hset(key, k, str(v))
            if ttl_seconds:
                self.redis_client.expire(key, ttl_seconds)
            logging.info(f"[RedisClient] Stored user info: {key}")
        except redis.RedisError as e:
            logging.error(f"[RedisClient] Failed to store HSET: {e}", exc_info=True)

    def get_user_info(self, username: str) -> str:
        key = f"userinfo:{username}"
        try:
            data = self.redis_client.hgetall(key)
            if data:
                logging.info(f"[RedisClient] Retrieved data for: {key}")
                return data
            else:
                logging.info(f"[RedisClient] No data found for: {key}")
                return None
        except redis.RedisError as e:
            logging.error(f"[RedisClient] Failed to get data: {e}", exc_info=True)
            return None

    def delete_user_info_hash_set(self, username: str) -> bool:
        hash_key = f"userinfo:{username}"
        try:
            result = self.redis_client.delete(hash_key)
            if result == 1:
                logging.info(f"[RedisClient] Deleted hash_key: '{hash_key}'")
                return True
            else:
                logging.info(f"[RedisClient] hash_key: '{hash_key}' not found to delete")
                return False
        except redis.RedisError as e:
            logging.error(f"[RedisClient] Failed to delete hash_key '{hash_key}': {e}", exc_info=True)
            return False