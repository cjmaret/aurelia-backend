from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class VerificationCodeSchema(BaseModel):
    userId: str
    code: str
    purpose: str 
    expiresAt: datetime
    createdAt: datetime
    purpose: str
    email: Optional[str] = None