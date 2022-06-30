import secrets
from pydantic import BaseSettings


class Settings(BaseSettings):
    BYPASS_API_CSRF: bool = False
    CSRF_KEY: str = "supersecretcsrf" # must be the same in the console and the api for csrf middleware to work
    SECRET_KEY: str = "supersecretsecret" # must be the same in the console and the api for sessions to work
    SESSION_COOKIE: str = 'session'
    SESSION_EXPIRE_SECONDS: int = 60 * 60 * 24 * 10

    #SESSION_SAME_SITE: str = 'lax' # lax, strict, or none
    # Starlette defaults to lax, but I'm not sure why. strict seems to be working for our purposes
    SESSION_SAME_SITE: str = 'strict'

    CORS_ORIGINS: list[str] = []
    ACCESS_TOKEN_TIMEOUT_SECONDS: int = 60 * 60


settings = Settings()
