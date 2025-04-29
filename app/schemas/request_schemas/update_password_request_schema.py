from pydantic import BaseModel


class UpdatePasswordRequest(BaseModel):
    currentPassword: str
    newPassword: str
