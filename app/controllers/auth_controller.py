from fastapi import HTTPException
import jwt
from app.services.database_service import get_user_by_email, create_user, get_user_by_refresh_token, store_refresh_token
from app.utils.auth_utils import ALGORITHM, SECRET_KEY, create_access_token, create_refresh_token, verify_password, hash_password


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
