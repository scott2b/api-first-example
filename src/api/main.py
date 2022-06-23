from fastapi import FastAPI, Body
from pydantic import BaseModel
from starlette.authentication import requires
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from common.backends import SessionAuthBackend
from common.config import settings
from common.models import OAuth2Client, Task


app = FastAPI(debug=True)

app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:8000"],
            #    str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

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
    tasks = Task.table
    return { "tasks": tasks }


class NewTask(BaseModel):
    """Based on these docs: https://fastapi.tiangolo.com/tutorial/body-multiple-params/#singular-values-in-body
    it is expected that we can simply define a description parameter that defaults to Body(),
    however this does not seem to work, so we provide an input Task validator without an id.
    """
    description: str


@app.post("/tasks")
async def create_task(task:NewTask):
    task = Task.create(task.description)
    #Task.table.append(task)
    return task  # TODO: status 201


@app.put("/tasks/{task_id}")
async def update_task(task_id:str, task:Task):
    Task.update(task)
    return task


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
    return await token_machine.create_token(form_data)
