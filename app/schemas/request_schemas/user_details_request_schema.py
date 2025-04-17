from pydantic import BaseModel, Field
from typing import Optional


class UserDetailsRequestSchema(BaseModel):
    username: Optional[str] = Field(None, description="The name of the user")
    userEmail: Optional[str] = Field(None, description="The email of the user")
    targetLanguage: Optional[str] = Field(
        None, description="The language the user is learning")
    appLanguage: Optional[str] = Field(
        None, description="The language the app communicates in")
    setupComplete: Optional[bool] = Field(
        None, description="Whether the user has completed the setup process")
