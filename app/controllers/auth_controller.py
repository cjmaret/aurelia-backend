from app.services.email_service import send_email_verification, send_email_verified_notification, send_password_change_notification, send_password_reset_email
from app.utils.auth_utils import create_email_verification_token, decode_email_verification_token, decode_password_reset_token
from app.services.database_service import delete_corrections_by_user_id, delete_user_by_id, update_user_details_in_db
from fastapi import HTTPException
import jwt
from app.services.database_service import get_user_by_email, create_user, get_user_by_id, get_user_by_refresh_token, store_refresh_token, update_user_password_in_db
from app.utils.auth_utils import ALGORITHM, SECRET_KEY, create_access_token, create_password_reset_token, create_refresh_token, verify_password, hash_password


def login_user(user_email: str, password: str):
    if not user_email or not password:
        raise HTTPException(
            status_code=400, detail="Email and password are required"
        )

    print(f"Attempting to log in user with email: {user_email}")
    # get user from database
    user = get_user_by_email(user_email)
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(
            status_code=401, detail="Invalid email or password"
        )

    # generate tokens
    access_token = create_access_token(data={"sub": str(user["userId"])})
    refresh_token = create_refresh_token(data={"sub": str(user["userId"])})

    # store refresh token in database
    store_refresh_token(user["userId"], refresh_token)

    if not user['emailVerified'] and not user['initialVerificationEmailSent']:
        token = create_email_verification_token(
            user["userId"], user["userEmail"])
        send_email_verification(user['userEmail'], token)
        print('Sent initial verification email, preparing to update user record.')
        update_user_details_in_db(
            user["userId"], {"initialVerificationEmailSent": True})
    # return access and refresh tokens
    return {
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "tokenType": "bearer"
    }


def register_user(user_email: str, password: str):
    user = get_user_by_email(user_email)
    if user:
        raise HTTPException(status_code=400, detail="email already exists")

    # hash token
    hashed_password = hash_password(password)
    create_user(user_email, hashed_password)

    return {"message": "User registered successfully"}


def request_email_verification(user_id: str):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = create_email_verification_token(user_id, user["userEmail"])
    send_email_verification(user["userEmail"], token)
    return {"success": True, "message": "Verification email sent to your address."}


def verify_email(token: str):
    # returns a tuple, both must be unpacked
    user_id, email = decode_email_verification_token(token)
    user = get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_user_details_in_db(user_id, {"emailVerified": True})
    send_email_verified_notification(email)
    return {"success": True, "message": "Email address verified!"}


def delete_user(user_id: str):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    delete_corrections_by_user_id(user_id)

    delete_result = delete_user_by_id(user_id)
    if not delete_result:
        raise HTTPException(
            status_code=500, detail="Failed to delete user account")

    return {"success": True, "message": "User account deleted successfully"}


def refresh_user_token(refresh_token: str):
    # validate refresh token
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=401, detail="Invalid refresh token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401, detail="Refresh token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # check if refresh token exists in database
    user = get_user_by_refresh_token(refresh_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # generate access and refresh tokens
    new_access_token = create_access_token({"sub": user["userId"]})
    new_refresh_token = create_refresh_token({"sub": user["userId"]})

    # store refresh token in database
    store_refresh_token(user["userId"], new_refresh_token)

    return {
        "accessToken": new_access_token,
        "refreshToken": new_refresh_token,
        "tokenType": "bearer"
    }


def update_user_password(user_id: str, current_password: str, new_password: str):

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(current_password, user["password"]):
        raise HTTPException(
            status_code=403, detail="Current password is incorrect")

    if len(new_password) < 8:
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters long")

    if verify_password(new_password, user["password"]):
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current password")

    hashed_password = hash_password(new_password)

    update_result = update_user_password_in_db(user_id, hashed_password)

    # Check if the update was successful
    if update_result.modified_count == 0:
        raise HTTPException(
            status_code=500, detail="Failed to update the password. Please try again later."
        )

    send_password_change_notification(user["userEmail"])

    return {"success": True, "message": "Password updated successfully"}


def request_password_reset(user_email: str):
    user = get_user_by_email(user_email)
    if not user:
        return {"success": True, "message": "If this email is registered, a reset link has been sent."}

    reset_token = create_password_reset_token(user["userId"])

    send_password_reset_email(user_email, reset_token)

    return {"success": True, "message": "If this email is registered, a reset link has been sent."}


def reset_password(token: str, new_password: str):
    user_id = decode_password_reset_token(token)
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if len(new_password) < 8:
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters long")

    hashed_password = hash_password(new_password)
    update_result = update_user_password_in_db(user_id, hashed_password)

    if update_result.modified_count == 0:
        raise HTTPException(
            status_code=500, detail="Failed to reset the password. Please try again later.")

    send_password_change_notification(user["userEmail"])

    return {"success": True, "message": "Password has been reset successfully"}


# TODO: deal with this
def process_google_user(user_info: dict):
    user_email = user_info["userEmail"]
    user = get_user_by_email(user_email)

    if not user:
        create_user(
            userEmail=user_email,
            hashed_password=None,
            user_id=user_info["sub"],
            email_verified=True,
        )

    # Generate token for the user
    access_token = create_access_token(data={"userEmail": user_email})
    return {"access_token": access_token, "token_type": "bearer"}
