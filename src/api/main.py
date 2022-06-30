import datetime
from asgi_csrf import asgi_csrf
from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel
from starlette.authentication import requires
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from common.backends import CSRFMiddleware, SessionAuthBackend
from common.config import settings
from common.models import OAuth2Client, OAuth2Token, Task


app = FastAPI(debug=True)

app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:8000"],
            #    str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )


def bypass_csrf(scope):
    """Used only for development. In order to enable interactive Swagger docs, set
    the BYPASS_API_CSRF configuration setting to True. This can be done by setting the
    BYPASS_API_CSRF environment variable.

    Because this disables CSRF protection on API calls, it is not recommended to allow
    this bypass in deployment.
    """
    return settings.BYPASS_API_CSRF
    

app.add_middleware(asgi_csrf, signing_secret=settings.CSRF_KEY, always_set_cookie=True, skip_if_scope=bypass_csrf)


app.add_middleware(
    AuthenticationMiddleware,
    backend=SessionAuthBackend())


app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE,
    max_age=settings.SESSION_EXPIRE_SECONDS,
    same_site=settings.SESSION_SAME_SITE,
    https_only=False)


@app.get("/")
async def home():
    return { "description": "api-first example application" }


@app.get("/clients")
@requires("api_auth")
async def clients(request:Request):
    clients = OAuth2Client.get_for_user(request.user)
    return { clients: clients }


@app.get("/tasks")
@requires("api_auth")
async def get_tasks(request:Request):
    tasks = Task.for_user(request.user)
    return { "tasks": tasks }


# TODO: factor into a schema module

class NewTask(BaseModel):
    """Based on these docs: https://fastapi.tiangolo.com/tutorial/body-multiple-params/#singular-values-in-body
    it is expected that we can simply define a description parameter that defaults to Body(),
    however this does not seem to work, so we provide an input Task validator without an id.
    """
    description: str


class UpdateTask(BaseModel):
    id: str
    description: str
    done: bool


class ReturnTask(BaseModel):

    id: str
    user: str
    description: str
    done: bool

    @classmethod
    def from_task(cls, task):
        d = task.asdict()
        d["user"] = d["user"]["username"]
        return cls(**d)


@app.post("/tasks")
@requires("api_auth")
async def create_task(request:Request, task:NewTask):
    print("CREATING TASK IN API")
    task = Task.create(request.user, task.description)
    return ReturnTask.from_task(task) # TODO: status 201


@app.put("/tasks/{task_id}")
@requires("api_auth")
async def update_task(request:Request, task_id:str, task:UpdateTask):
    orig = Task.table[task_id]
    if orig.user == request.user or request.user.superuser:
        Task.update(task)
        return task
    else:
        raise HTTPException(status_code=404)


from fastapi import Form, Depends

class OAuth2ClientTokenRequestForm:

    def __init__(
        self,
        grant_type: str = Form(None, regex="client_credentials"),
        client_id: str = Form(...),
        client_secret: str = Form(...)
    ):
        self.grant_type = grant_type
        self.scopes = ["api"]
        self.client_id = client_id
        self.client_secret = client_secret


class OAuth2ClientRefreshTokenRequestForm:

    def __init__(
        self,
        grant_type: str = Form(None, regex="refresh_token"),
        refresh_token: str = Form(...)
    ):
        self.grant_type = grant_type
        self.refresh_token = refresh_token

    
@app.post("/token")
async def token(form_data: OAuth2ClientTokenRequestForm=Depends()):
    """Get new OAuth token
    Fetches a new authorization token for the client. Request should be posted as
    form data with the fields:
     * grant_type (must be set to "client_credentials")
     * token_type (Optional. Set to "Bearer")
     * client_id  (your client application ID)
     * client_secret (your client application secret)
    The returned access token value can then be passed to subsequent requests until the
    time provided by access_token_expires_at. The token should be passed as the
    authorization header in the format:
    ```
    Bearer TOKEN
    ```
    """
    client = OAuth2Client.get(form_data.client_id)
    if client is None:
        raise HTTPException(status_code=401)
    if client.client_secret != form_data.client_secret: # TODO: secret should probably be hashed
        raise HTTPException(status_code=401)
    token = OAuth2Token.create_for_client(client, form_data.grant_type, scope="api")
    expires = (token.access_token_expires_at - datetime.datetime.utcnow()).seconds
    return {
        'access_token': token.access_token,
        'token_type': 'bearer',
        'refresh_token': token.refresh_token,
        'expires_in': expires
    }
