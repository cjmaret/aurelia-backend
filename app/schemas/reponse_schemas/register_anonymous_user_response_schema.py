
from pydantic import BaseModel


class RegisterAnonymousUserResponse(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str
    userId: str
    userSecret: str