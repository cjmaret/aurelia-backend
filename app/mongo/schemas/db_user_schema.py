from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class DbUserSchema(BaseModel):
    userId: str
    username: str
    userEmail: Optional[str] = None
    emailVerified: bool = False
    targetLanguage: str
    appLanguage: str
    createdAt: datetime
    setupComplete: bool = False
    password: Optional[str]
    oauthProvider: Optional[str] = None 
    oauthUserId: Optional[str] = None
    refreshToken: Optional[str] = None
    isAnonymous: bool = False
    anonUserSecret: Optional[str] = None