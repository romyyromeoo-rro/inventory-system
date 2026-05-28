import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY is not set")

    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES", 15
    ))
    ALGORITHM = os.getenv("ALGORITHM")
    REDIS_URL = os.getenv("REDIS_URL")
    CACHE_KEY = os.getenv("CACHE_KEY")
    DB_PATH = os.getenv("DB_PATH")

config = Config()
