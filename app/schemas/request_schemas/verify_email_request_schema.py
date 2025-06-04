from pydantic import BaseModel


class VerifyEmailRequestSchema(BaseModel):
    token: str
