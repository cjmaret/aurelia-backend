from pydantic import BaseModel

class RequestPasswordResetRequest(BaseModel):
    userEmail: str
