import secrets
from pydantic import BaseSettings


class Settings(BaseSettings):
    CSRF_KEY: str = secrets.token_urlsafe(32)
    SECRET_KEY: str = "supersecretsecret" # must be the same for the console and the api for sessions to work
    SESSION_COOKIE: str = 'session'
    SESSION_EXPIRE_SECONDS: int = 60 * 60 * 24 * 10
    #SESSION_SAME_SITE: str = 'lax' # lax, strict, or none
    SESSION_SAME_SITE: str = 'strict'


settings = Settings()
