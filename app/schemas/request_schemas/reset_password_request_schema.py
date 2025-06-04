from pydantic import BaseModel

class ResetPasswordRequest(BaseModel):
    token: str
    newPassword: str
