import datetime
from pydantic import BaseModel


class UserResponse(BaseModel):
    userId: str
    userEmail: str
    createdAt: datetime