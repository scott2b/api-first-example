import os
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
from oauthlib.oauth2.rfc6749.errors import MissingTokenError

client_id = os.environ["CLIENT_ID"]
client_secret = os.environ["CLIENT_SECRET"]

TOKEN_URL = "http://localhost:5000/token" # For development purposes only. Requires
                                          # OAUTHLIB_INSECURE_TRANSPORT=1
                                          # to be set in the environment

def fetch_api_token() -> dict:
    backend = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=backend)
    try:
        token = oauth.fetch_token(
            token_url=TOKEN_URL,
            client_id=client_id,
            client_secret=client_secret,
            include_client_id=True,
        )
    except MissingTokenError:
        # oauthlib gives the same error regardless of the problem
        print("Something went wrong, please check your client credentials.")
        raise
    return token

token = fetch_api_token()
print(token)
