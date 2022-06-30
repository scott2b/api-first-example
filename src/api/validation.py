from pydantic import BaseModel


class Message(BaseModel):
    message: str


class OAuth2TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str
    expires_in: int


class TaskCreate(BaseModel):
    """Based on these docs: https://fastapi.tiangolo.com/tutorial/body-multiple-params/#singular-values-in-body
    it is expected that we can simply define a description parameter that defaults to
    Body(), however this does not seem to work always resulting in a 422 validation
    error, so we provide an input Task validator without an id.
    """
    description: str


class TaskUpdate(BaseModel):
    id: str
    description: str
    done: bool


class TaskResponse(BaseModel):

    id: str
    description: str
    done: bool


class TaskList(BaseModel):

    tasks: list[TaskResponse]
