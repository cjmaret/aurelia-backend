from pydantic import BaseModel, EmailStr


class UpgradeAnonymousUserRequest(BaseModel):
    userId: str
    userSecret: str
    userEmail: str
    password: str
