from dataclasses import dataclass
import shortuuid


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
    }


@dataclass
class Task:

    id: str
    description: str
    done: bool = False

    @classmethod
    def create(cls, description):
        _id = shortuuid.uuid()[:5]
        task = cls(id=_id, description=description)
        cls.table[_id] = task
        return task

    @classmethod
    def update(cls, task):
        cls.table[task.id] = task
        return task
        

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
        for client in cls.table.values():
            if client.user.id == user.id:
                _.append(client)
        return _

"""
Here we bootstrap each user with a given client. Presumably, however, there would be
a UI for creating and deleting client credentials. A given user might have multiple
clients.
"""
OAuth2Client.table = {}
for user in User.table.values():
    client = OAuth2Client(
        user=user,
        client_id=secrets.token_urlsafe(32),
        client_secret=secrets.token_urlsafe(32)
    )
    OAuth2Client.table[client.client_id] = client

import datetime

@dataclass
class OAuth2Token:
    """An access token."""

    user: User # denormalized for convenience
    client: OAuth2Client
    token: str
    expires_at: datetime.datetime

OAuth2Token.table = {}
