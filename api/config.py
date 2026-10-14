import os

class Config:
    DB_HOST = os.environ.get("DB_HOST", "db")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DB_NAME = os.environ.get("DB_NAME", "labdb")
    DB_USER = os.environ.get("DB_USER", "labuser")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "labpassword123")

    REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
    REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))