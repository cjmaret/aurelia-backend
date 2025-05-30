from app.services.database_service import delete_corrections_by_user_id, delete_user_by_id
from fastapi import HTTPException
import jwt
from app.services.database_service import get_user_by_email, create_user, get_user_by_id, get_user_by_refresh_token, store_refresh_token, update_user_password_in_db
from app.utils.auth_utils import ALGORITHM, SECRET_KEY, create_access_token, create_refresh_token, verify_password, hash_password
from app.utils.email_utils import send_email


def login_user(userEmail: str, password: str):
    # get user from database
    user = get_user_by_email(userEmail)
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(
            status_code=401, detail="Invalid email or password"
        )

    # generate tokens
    access_token = create_access_token(data={"sub": str(user["userId"])})
    refresh_token = create_refresh_token(data={"sub": str(user["userId"])})

    # store refresh token in database
    store_refresh_token(user["userId"], refresh_token)

    # return access and refresh tokens
    return {
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "tokenType": "bearer"
    }


def register_user(userEmail: str, password: str):
    normalized_email = userEmail.strip().lower()
    user = get_user_by_email(normalized_email)
    if user:
        raise HTTPException(status_code=400, detail="email already exists")

    # hash token
    hashed_password = hash_password(password)
    create_user(normalized_email, hashed_password)
    return {"message": "User registered successfully"}


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


def update_user_password(user_id: str, currentPassword: str, newPassword: str):

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(currentPassword, user["password"]):
        raise HTTPException(
            status_code=403, detail="Current password is incorrect")

    if len(newPassword) < 8:
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters long")

    if verify_password(newPassword, user["password"]):
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current password")

    hashed_password = hash_password(newPassword)

    update_result = update_user_password_in_db(user_id, hashed_password)

    print('update_result', update_result)

    # Check if the update was successful
    if update_result.modified_count == 0:
        raise HTTPException(
            status_code=500, detail="Failed to update the password. Please try again later."
        )

    # notify user about password change
    send_password_change_notification(user["userEmail"])

    return {"success": True, "message": "Password updated successfully"}


def send_password_change_notification(email: str):
    send_email(
        to=email,
        subject="Your Password Has Been Changed",
        body="Your password was successfully updated. If you did not make this change, please contact support immediately."
    )


# TODO: deal with this
def process_google_user(user_info: dict):
    userEmail = user_info["userEmail"]
    user = get_user_by_email(userEmail)

    if not user:
        create_user(
            userEmail=userEmail,
            hashed_password=None,
            user_id=user_info["sub"],
            email_verified=True,
        )

    # Generate token for the user
    access_token = create_access_token(data={"userEmail": userEmail})
    return {"access_token": access_token, "token_type": "bearer"}
