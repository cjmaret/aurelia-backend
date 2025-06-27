from pydantic import BaseModel


class VerifyEmailRequestSchema(BaseModel):
    code: str
