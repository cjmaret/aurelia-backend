from pydantic import BaseModel


class LoginRequest(BaseModel):
    userEmail: str
    password: str
