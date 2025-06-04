from app.services.database_service import get_user_by_id, update_user_details_in_db, get_user_by_email
from app.services.email_service import send_email_change_notification, send_change_email_verification
from fastapi import HTTPException
from app.schemas.reponse_schemas.user_details_response_schema import UserDetailsResponseSchema
from app.schemas.request_schemas.user_details_request_schema import UserDetailsRequestSchema
from app.services.database_service import get_user_by_id, update_user_details_in_db
from app.utils.auth_utils import create_email_verification_token, decode_email_verification_token, verify_password


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


def request_email_change(user_id: str, new_email: str):
    if get_user_by_email(new_email):
        raise HTTPException(status_code=400, detail="Email already in use")

    token = create_email_verification_token(user_id, new_email)

    send_change_email_verification(new_email, token)

    return {"success": True, "message": "Verification email sent to new address. Please verify to complete the change."}


def change_user_email(token: str, password: str):

    user_id, email = decode_email_verification_token(token)

    if get_user_by_email(email):
        raise HTTPException(status_code=400, detail="Email already in use")

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect password")

    update_user_details_in_db(user_id, {
        "userEmail": email,
        "emailVerified": True
    })

    send_email_change_notification(email)

    return {"success": True, "message": "Email address updated and verified."}
