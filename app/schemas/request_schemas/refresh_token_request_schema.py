from pydantic import BaseModel


class RefreshTokenRequest(BaseModel):
    refreshToken: str
