import datetime
from asgi_csrf import asgi_csrf
from fastapi import Body, Depends, FastAPI, HTTPException
from starlette.authentication import requires
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from common.backends import SessionAuthBackend
from common.config import settings
from common.models import OAuth2Client, OAuth2Token, Task
from .forms import OAuth2ClientTokenRequestForm, OAuth2ClientRefreshTokenRequestForm
from .validation import (
    Message,
    OAuth2TokenResponse,
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskList,
)


app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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


app.add_middleware(
    asgi_csrf,  # Thanks @simonw!
    signing_secret=settings.CSRF_KEY,
    always_set_cookie=True,
    skip_if_scope=bypass_csrf,
)


app.add_middleware(AuthenticationMiddleware, backend=SessionAuthBackend())


app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE,
    max_age=settings.SESSION_EXPIRE_SECONDS,
    same_site=settings.SESSION_SAME_SITE,
    https_only=False,
)


@app.get("/", include_in_schema=False)
async def home():
    return {
        "description": "api-first example application",
        "documentation": {"swagger": "/docs", "redoc": "/redoc"},
    }


@app.get("/clients", include_in_schema=False)
@requires("app_auth")  # Note the app_auth scope on this one
async def clients(request: Request):
    """This is not currently used but is exposed for the sake of potentially fetching
    the client credentials via ajax rather than in the console view code.

    I find it questionable to expose these in the API via client credential/token
    authentication, thus I have marked the required scope to be app_auth, and have
    removed this from the docs.
    """
    clients = OAuth2Client.get_for_user(request.user)
    return {clients: clients}


@app.get("/tasks", response_model=TaskList)
@requires("api_auth")
async def get_tasks(request: Request):
    """Get the list of tasks. Returns all tasks for the user associated with the
    client credentials, or the currently authenticated user in the UI.
    """
    return {"tasks": Task.for_user(request.user)}


@app.post("/tasks", response_model=TaskResponse, status_code=201)
@requires("api_auth")
async def create_task(request: Request, task: TaskCreate):
    """Create a new task."""
    return Task.create(request.user, task.description)


@app.put(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    responses={404: {"model": Message, "description": "The item was not found"}},
)
@requires("api_auth")
async def update_task(request: Request, task_id: str, data: TaskUpdate):
    """Update the given tasks. Only superusers may update other users' tasks."""
    task = Task.table.get(task_id)
    if task is None:
        raise HTTPException(status_code=404)
    if task.user == request.user or request.user.superuser:
        return task.update(**data.dict())
    else:
        raise HTTPException(status_code=404)


@app.post("/token", response_model=OAuth2TokenResponse)
async def token(form_data: OAuth2ClientTokenRequestForm = Depends()):
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

    Due to ephemeral persistence of tokens in this implementation, you may see 403
    errors, e.g. if the application is restarted. Deleting the client's .key file
    should fix this (or run the command `tasks.py reset`).
    """
    client = OAuth2Client.get(form_data.client_id)
    if client is None:
        raise HTTPException(status_code=401)
    if (
        client.client_secret != form_data.client_secret
    ):  # TODO: secret should probably be hashed
        raise HTTPException(status_code=401)
    token = OAuth2Token.create_for_client(client, form_data.grant_type, scope="api")
    expires = (token.access_token_expires_at - datetime.datetime.utcnow()).seconds
    return OAuth2TokenResponse(
        access_token=token.access_token,
        refresh_token=token.refresh_token,
        expires_in=expires,
    )


@app.post("/token-refresh", response_model=OAuth2TokenResponse)
async def refresh_token(form_data: OAuth2ClientRefreshTokenRequestForm = Depends()):
    """Refresh OAuth token. Should be posted as form data with the fields:
     * grant_type (must be set to "refresh_token")d
     * refresh_token (the refresh token of your active credentials)

    Due to ephemeral storage of tokens in this implementation, you may get a KeyError,
    e.g. if the application is restarted. This is analagous to a refresh token being
    revoked with client credentials left intact, thus clients should simply retry with
    the original ID/secret credentials.

    As far as I can tell, providing a refresh endpoint is optional, and primarily
    serves the purpose of avoiding passing the primary credentials around any more
    than necessary.

    As implemented, refresh tokens do not expire. It is not clear to me if there is
    a concept of refresh-token timeout in the spec.
    """
    token = OAuth2Token.refresh(form_data.refresh_token)
    expires = (token.access_token_expires_at - datetime.datetime.utcnow()).seconds
    return OAuth2TokenResponse(
        access_token=token.access_token,
        refresh_token=token.refresh_token,
        expires_in=expires,
    )
