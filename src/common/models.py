import datetime
import dbm
import json
import os
import shortuuid
from dataclasses import dataclass, asdict
from common.config import settings


@dataclass
class User:

    id: int
    username: str
    password: str # Demo only. Don't store plain passwords in production
    active: bool = True
    superuser: bool = False

    @classmethod
    def get_by_username(cls, username):
        for user in cls.table.values():
            if user.username == username:
                return user

    @property
    def is_authenticated(self):
        return True


User.table = {
        1: User(id=1, username="ronnie", password="ronnie1"),
        2: User(id=2, username="bobby", password="bobby2"),
        3: User(id=3, username="ricky", password="ricky3", superuser=True),
        4: User(id=4, username="mike", password="mike4", active=False)
    }


@dataclass
class Task:

    id: str
    user: User
    description: str
    done: bool = False

    @classmethod
    def create(cls, user, description):
        _id = shortuuid.uuid()[:5]
        task = cls(id=_id, user=user, description=description)
        cls.table[_id] = task
        return task

    def update(self, **data):
        self.__dict__.update(data)
        return self

    @classmethod
    def for_user(cls, user):
        _ = []
        for task in cls.table.values():
            if task.user == user:
                _.append(task)
        return _

    def asdict(self):
        """Super annoying that Python dataclasses make this a module function instead
        of an object method.
        """
        return asdict(self)
        

Task.table = {}

###

import secrets

@dataclass
class OAuth2Client:
    """Client credentials object for managing programmatic access to the API."""

    user: User
    client_id: str
    client_secret: str

    @classmethod
    def get_for_user(cls, user):
        _ = []
        with dbm.open("client_credentials", "r") as db:
            for key in db.keys():
                data = json.loads(db[key])
                if data["user_id"] == user.id:
                    _.append(cls(user=user, client_id=data["client_id"], client_secret=data["client_secret"]))
        return _

    @classmethod
    def get(cls, client_id):
        with dbm.open("client_credentials", "r") as db:
            data = json.loads(db.get(client_id))
        user = User.table[data["user_id"]]
        client = cls(user=user, client_id=data["client_id"], client_secret=data["client_secret"])
        return client

"""
Here we bootstrap each user with a given client. Presumably, however, there would be
a UI for creating and deleting client credentials. A given user might have multiple
clients, but we create a single client for each user here.

NOTE: This fairly crude shared persistence assumes that the console and api are co-located.
This will not work otherwise, as the separate runtimes will have different credentials.
For a distributed deployment, a real database is needed. This is simply for demo/proof-of-concept
purposes.
"""
if not os.path.exists("client_credentials"):
    with dbm.open("client_credentials", "c") as db:
        for user in User.table.values():
            data = {
                "user_id": user.id,
                "client_id": secrets.token_urlsafe(32),
                "client_secret": secrets.token_urlsafe(32)
            }
            db[data["client_id"]] = json.dumps(data)


@dataclass
class OAuth2Token:
    """An access token."""

    client: OAuth2Client
    access_token: str
    refresh_token: str
    access_token_expires_at: datetime.datetime
    revoked: bool = False


    @classmethod
    def _create(cls, client):
        expires = datetime.datetime.utcnow() + \
            datetime.timedelta(seconds=settings.ACCESS_TOKEN_TIMEOUT_SECONDS)
        token = cls(
            client=client,
            access_token=secrets.token_urlsafe(32),
            refresh_token=secrets.token_urlsafe(32),
            access_token_expires_at=expires
        )
        cls.access_tokens[token.access_token] = token
        cls.refresh_tokens[token.refresh_token] = token
        return token

    @classmethod
    def create_for_client(cls, client, grant_type, scope="api"):
        assert grant_type == "client_credentials" # only client_credentials and api scope currently supported
        assert scope == "api"
        return cls._create(client)

    @classmethod
    def refresh(cls, refresh_token):
        """See:
        https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#refreshing-tokens
        """
        obj = cls.refresh_tokens[refresh_token] 
        client = obj.client
        del cls.access_tokens[obj.access_token]
        del cls.refresh_tokens[refresh_token]
        return cls._create(client)
         

OAuth2Token.access_tokens = {}
OAuth2Token.refresh_tokens = {}
