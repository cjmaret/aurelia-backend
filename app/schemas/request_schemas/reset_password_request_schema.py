from pydantic import BaseModel

class ResetPasswordRequest(BaseModel):
    userEmail: str
    code: str
    newPassword: str
