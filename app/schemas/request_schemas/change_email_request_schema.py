from pydantic import BaseModel


class ChangeEmailRequestSchema(BaseModel):
    token: str
    password: str
