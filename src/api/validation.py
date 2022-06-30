from pydantic import BaseModel


class Message(BaseModel):
    message: str


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

