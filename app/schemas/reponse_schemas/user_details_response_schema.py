from pydantic import BaseModel, Field
from typing import Optional


class UserDetailsResponseSchema(BaseModel):
    userId: str = Field(..., description="The unique ID of the user")
    username: Optional[str] = Field(None, description="The name of the user")
    userEmail: str = Field(..., description="The email of the user")
    emailVerified: bool = Field(
        False, description="Whether the user's email is verified")
    targetLanguage: Optional[str] = Field(
        None, description="The language the user is learning")
    appLanguage: Optional[str] = Field(
        None, description="The language the app communicates in")
    setupComplete: bool = Field(
        False, description="Whether the user has completed the setup process")
    oauth_provider: Optional[str] = Field(
        None, description="The OAuth provider used for authentication (if any)")
