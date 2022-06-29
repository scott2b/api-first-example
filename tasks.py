import base64
import dbm
import json
import logging
import os
import sys
import urllib
import urllib.parse
import oauthlib
import requests
import typer
from pathlib import Path
from cryptography.fernet import Fernet
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
from oauthlib.oauth2.rfc6749.errors import MissingTokenError


logger = logging.getLogger("apifirstexample")
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)



class InvalidRequest(Exception):
    ...

class Unauthorized(Exception):
    ...

class MissingToken(Exception):
    ...


KEY_DB = Path(__file__).parent / ".key"


class APIClient:

    API_ROOT = os.environ.get("API_ROOT", "http://localhost:5000")  # localhost for development purposes. Requires
                                                                    # OAUTHLIB_INSECURE_TRANSPORT=1
                                                                    # to be set in the environment
    TOKEN_URL = f"{API_ROOT}/token"
    REFRESH_URL = f"{API_ROOT}/token-refresh"

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        try:
            token = self.load_saved_token()
        except KeyError:
            token = self.fetch_api_token()
            self.token_saver(token)
        self.client = self.create_client_for_token(token)

    def create_client_for_token(self, token: dict) -> OAuth2Session:
        return OAuth2Session(
            self.app_id,
            token=token,
            auto_refresh_url=self.REFRESH_URL,
            auto_refresh_kwargs={},
            token_updater=self.token_saver,
        )

    def fernet(self, key: str) -> Fernet:
        key = key + "=" * (len(key) % 4)
        _key = base64.urlsafe_b64encode(base64.urlsafe_b64decode(key))
        return Fernet(_key)

    def encrypt(self, data: str) -> bytes:
        return self.fernet(self.app_secret).encrypt(data.encode())

    def decrypt(self, data: bytes) -> bytes:
        return self.fernet(self.app_secret).decrypt(data)

    def token_saver(self, token: dict) -> None:
        logger.debug("SAVING TOKEN: %s" % str(token))
        data = json.dumps(token)
        _t = self.encrypt(data)
        with dbm.open(KEY_DB.as_posix(), "c") as db:
            db[self.app_id] = _t

    def load_saved_token(self) -> dict:
        with dbm.open(KEY_DB.as_posix(), "c") as db:
            _token = db[self.app_id]
        token = json.loads(self.decrypt(_token))
        return token

    def fetch_api_token(self) -> dict:
        backend = BackendApplicationClient(client_id=self.app_id)
        oauth = OAuth2Session(client=backend)
        try:
            token = oauth.fetch_token(
                token_url=self.TOKEN_URL,
                client_id=self.app_id,
                client_secret=self.app_secret,
                include_client_id=True,
            )
        except MissingTokenError:
            # oauthlib gives the same error regardless of the problem
            print("Something went wrong, please check your client credentials.")
            raise
        return token

    def clear_saved_token(self) -> None:
        with dbm.open(KEY_DB.as_posix(), "c") as db:
            if self.app_id in db:
                del db[self.app_id]

    def reset(self):
        self.clear_saved_token()
        token = self.fetch_api_token()
        self.token_saver(token)
        self.client = self.create_client_for_token(token)

    ### Dispatch methods ###

    def get(self, path:str, **query) -> requests.Response:
        url = f"{self.API_ROOT}{path}"
        if query:
            querystr = urllib.parse.urlencode(query)
            url = f"{url}?{querystr}"
        logger.debug(f"GETing URL {url}")
        try:
            return self.client.get(url)
        except (oauthlib.oauth2.rfc6749.errors.MissingTokenError, MissingToken):
            self.reset()
            return self.client.get(url)

    def post(self, path:str, data:dict) -> requests.Response:
        url = f"{self.API_ROOT}{path}"
        logger.debug(f"POSTing URL {url}")
        try:
            resp = self.client.post(url, json=data)
            return resp
        except (oauthlib.oauth2.rfc6749.errors.MissingTokenError, MissingToken):
            self.reset()
            resp = self.client.post(url, json=data)
            return resp

    def put(self, path:str, data:dict) -> requests.Response:
        url = f"{self.API_ROOT}{path}"
        logger.debug(f"PUTing URL {url}")
        try:
            resp = self.client.put(url, json=data)
            return resp
        except (oauthlib.oauth2.rfc6749.errors.MissingTokenError, MissingToken):
            self.reset()
            resp = self.client.post(url, json=data)
            return resp

### CLI app

client_id = os.environ["CLIENT_ID"]
client_secret = os.environ["CLIENT_SECRET"]
client = APIClient(client_id, client_secret)
app = typer.Typer()


@app.command()
def list():
    """List tasks."""
    r = client.get("/tasks")
    for i, task in enumerate(r.json()["tasks"], start=1):
        done = "☑" if task["done"] else "☐"
        print(done, f"{i}.", task["description"])


@app.command()
def new(description: str):
    """Create a new task."""
    r = client.post("/tasks", { "description": description })


@app.command()
def do(number: int):
    """Mark a task as done."""
    r = client.get("/tasks")
    tasks = { i:task for i, task in enumerate(r.json()["tasks"], start=1) }
    try:
        task = tasks[number]
    except KeyError:
        print(f"Task #{number} does not exist.")
        return
    task["done"] = True
    r = client.put(f"/tasks/{task['id']}", task)
    
    

if __name__=="__main__":
    #r = client.post("/tasks", { "description": "do this" } )
    app()
