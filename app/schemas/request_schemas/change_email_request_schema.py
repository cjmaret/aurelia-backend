from pydantic import BaseModel


class ChangeEmailRequestSchema(BaseModel):
    newEmail: str
    code: str
