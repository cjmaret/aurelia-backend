from pydantic import BaseModel

class RegisterRequest(BaseModel):
    userEmail: str
    password: str