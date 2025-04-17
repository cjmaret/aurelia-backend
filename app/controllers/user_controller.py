from fastapi import HTTPException
from app.schemas.reponse_schemas.user_details_response_schema import UserDetailsResponseSchema
from app.schemas.request_schemas.user_details_request_schema import UserDetailsRequestSchema
from app.services.database_service import get_user_by_id, update_user_details_in_db


def get_user_details(user_id: str):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserDetailsResponseSchema(
        userId=user["userId"],
        username=user.get("username"),
        userEmail=user["userEmail"],
        emailVerified=user.get("emailVerified", False),
        targetLanguage=user.get("targetLanguage"),
        appLanguage=user.get("appLanguage"),
        setupComplete=user.get("setupComplete", False),
    )


def update_user_details(user_id: str, userDetails: UserDetailsRequestSchema):
    # convert pydantic model to dictionary
    userDetails_dict = userDetails.dict(exclude_unset=True)

    updated = update_user_details_in_db(user_id, userDetails_dict)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    # return updated user details
    updated_user = get_user_by_id(user_id)
    if not updated_user:
        raise HTTPException(
            status_code=404, detail="Failed to fetch updated user details")

    return UserDetailsResponseSchema(
        userId=updated_user["userId"],
        username=updated_user.get("username"),
        userEmail=updated_user["userEmail"],
        emailVerified=updated_user.get("emailVerified", False),
        targetLanguage=updated_user.get("targetLanguage"),
        appLanguage=updated_user.get("appLanguage"),
        setupComplete=updated_user.get("setupComplete", False),
    )
