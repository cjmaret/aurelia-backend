from pydantic import BaseModel


class UpgradeAnonymousUserResponse(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str
    userId: str
