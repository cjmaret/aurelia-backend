from pydantic import BaseModel


class RequestEmailChangeRequestSchema(BaseModel):
    newEmail: str
