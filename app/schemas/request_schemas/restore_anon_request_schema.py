from pydantic import BaseModel

class RestoreAnonymousRequest(BaseModel):
    userId: str
    userSecret: str
