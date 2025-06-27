from app.services.database_service import get_user_by_id, update_user_details_in_db, get_user_by_email
from app.services.email_service import send_email_change_notification, send_change_email_verification
from fastapi import HTTPException
from app.schemas.reponse_schemas.user_details_response_schema import UserDetailsResponseSchema
from app.schemas.request_schemas.user_details_request_schema import UserDetailsRequestSchema
from app.services.database_service import get_user_by_id, update_user_details_in_db
from app.utils.auth_utils import create_email_verification_code, verify_email_verification_code


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
        oauthProvider=user.get("oauthProvider", None),
        isAnonymous=user.get("isAnonymous", False),
    )


def update_user_details(user_id: str, user_details: UserDetailsRequestSchema):
    # convert pydantic model to dictionary
    user_details_dict = user_details.dict(exclude_unset=True)

    updated = update_user_details_in_db(user_id, user_details_dict)
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
        oauthProvider=updated_user.get("oauthProvider", None),
        isAnonymous=updated_user.get("isAnonymous", False),
    )


def request_email_change(user_id: str, new_email: str):
    user = get_user_by_id(user_id)
    if user.get("oauthProvider") == "google":
        raise HTTPException(
            status_code=400, detail="Google sign-in users cannot set or reset a password.")

    normalized_email = new_email.strip().lower()
    if get_user_by_email(normalized_email):
        raise HTTPException(status_code=400, detail="Email already in use")

    code = create_email_verification_code(user_id, normalized_email)
    send_change_email_verification(normalized_email, code)

    return {"success": True, "message": "Verification code sent to new address. Please verify to complete the change."}


def change_user_email(user_id: str, new_email: str, code: str):
    if not verify_email_verification_code(user_id, code, new_email):
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    normalized_email = new_email.strip().lower()
    if get_user_by_email(normalized_email):
        raise HTTPException(status_code=400, detail="Email already in use")

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_user_details_in_db(user_id, {
        "userEmail": normalized_email,
        "emailVerified": True
    })

    send_email_change_notification(normalized_email)

    return {"success": True, "message": "Email address updated and verified."}
