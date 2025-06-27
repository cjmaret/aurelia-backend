import secrets
from app.services.database_service import create_user
import logging
from app.config import Config
from app.services.email_service import send_email_verification, send_email_verified_notification, send_password_change_notification, send_password_reset_email
from app.utils.auth_utils import create_and_return_auth_tokens, create_email_verification_code, create_password_reset_code, verify_email_verification_code, verify_password_reset_code, ALGORITHM, SECRET_KEY, verify_password, hash_password
from app.services.database_service import delete_corrections_by_user_id, delete_user_by_id, update_user_details_in_db, get_user_by_email, create_user, get_user_by_id, get_user_by_refresh_token, update_user_password_in_db
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
import jwt
from jose import jwt
from app.services.oauth_service import oauth


def register_anonymous_user():
    user_secret = secrets.token_urlsafe(32)

    user_id = create_user(
        user_email=None,
        hashed_password=None,
        email_verified=True,
        initial_verification_email_sent=True,
        oauth_provider=None,
        oauth_user_id=None,
        is_anonymous=True,
        anon_user_secret=user_secret
    )
    response = create_and_return_auth_tokens(user_id)
    response.update({
        "userId": user_id,
        "userSecret": user_secret
    })
    return response


def restore_anonymous_user(user_id: str, user_secret: str):
    user = get_user_by_id(user_id)
    if not user or not user.get("isAnonymous"):
        raise HTTPException(status_code=404, detail="Anonymous user not found")
    if user.get("anonUserSecret") != user_secret:
        raise HTTPException(status_code=403, detail="Invalid user secret")
    return create_and_return_auth_tokens(user_id)


def upgrade_anonymous_user(user_id: str, user_secret: str, user_email: str, password: str):
    user = get_user_by_id(user_id)
    if not user or not user.get("isAnonymous"):
        raise HTTPException(status_code=404, detail="Anonymous user not found")
    if user.get("anonUserSecret") != user_secret:
        raise HTTPException(status_code=403, detail="Invalid user secret")
    if get_user_by_email(user_email):
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = hash_password(password)
    update_user_details_in_db(
        user_id,
        {
            "userEmail": user_email.strip().lower(),
            "password": hashed_password,
            "isAnonymous": False,
            "anonUserSecret": None,
            "emailVerified": False,
        }
    )
    response = create_and_return_auth_tokens(user_id)
    response.update({
        "userId": user_id,
    })
    return response


def login_user(user_email: str, password: str):
    if not user_email or not password:
        raise HTTPException(
            status_code=400, detail="Email and password are required"
        )

    # get user from database
    user = get_user_by_email(user_email)

    if user and user.get("oauthProvider") == "google":
        raise HTTPException(
            status_code=405, detail="This account uses Google sign-in. Please use 'Sign in with Google' instead.")

    if not user or not verify_password(password, user["password"]):
        raise HTTPException(
            status_code=401, detail="Invalid email or password"
        )

    # return access and refresh tokens
    return create_and_return_auth_tokens(user["userId"])


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
    if user and user.get("oauthProvider") == "google":
        raise HTTPException(
            status_code=400, detail="Google sign-in users cannot set or reset their email.")

    code = create_email_verification_code(user_id)

    send_email_verification(user["userEmail"], code)

    return {"success": True, "message": "Verification email sent to your address."}


def verify_email(user_id: str, code: str):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_email_verification_code(user_id, code):
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    update_user_details_in_db(user_id, {"emailVerified": True})

    send_email_verified_notification(user["userEmail"])

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

    return create_and_return_auth_tokens(user["userId"])


def update_user_password(user_id: str, current_password: str, new_password: str):

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.get("oauthProvider") == "google":
        raise HTTPException(
            status_code=403, detail="Google sign-in users cannot set or reset a password.")

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
    if user and user.get("oauthProvider") == "google":
        raise HTTPException(
            status_code=403,
            detail="This account uses Google sign-in. Please use 'Sign in with Google' to access your account."
        )

    if not user:
        return {"success": True, "message": "If this email is registered, a reset link has been sent."}

    reset_code = create_password_reset_code(user["userId"])
    send_password_reset_email(user_email, reset_code)

    return {"success": True, "message": "If this email is registered, a reset link has been sent."}


def reset_password(email: str, code: str, new_password: str):
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.get("oauthProvider") == "google":
        raise HTTPException(
            status_code=400, detail="This account uses Google sign-in. Use 'Sign in with Google' instead.")
    if len(new_password) < 8:
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters long")

    if not verify_password_reset_code(user["userId"], code):
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    hashed_password = hash_password(new_password)
    update_result = update_user_password_in_db(user["userId"], hashed_password)

    if update_result.modified_count == 0:
        raise HTTPException(
            status_code=500, detail="Failed to reset the password. Please try again later.")

    send_password_change_notification(user["userEmail"])

    return {"success": True, "message": "Password has been reset successfully"}


logger = logging.getLogger("google_auth")


async def login_with_google(request):
    logger.info("Starting Google OAuth login flow")
    logger.debug(f"Session before Google login: {request.session}")
    logger.debug(
        f"Session keys before Google login: {list(request.session.keys())}")
    redirect_uri = Config.GOOGLE_REDIRECT_URI
    logger.debug(f"Redirect URI for Google OAuth: {redirect_uri}")
    response = await oauth.google.authorize_redirect(request, redirect_uri)
    logger.debug(
        f"Session keys after Google login: {list(request.session.keys())}")
    return response


async def google_callback(request):
    logger.info("Google OAuth callback received")
    logger.debug(f"Session at Google callback: {request.session}")
    logger.debug(
        f"Session keys at Google callback: {list(request.session.keys())}")
    try:
        token = await oauth.google.authorize_access_token(request)
        request.session.clear()
        logger.debug(f"Token received from Google: {token}")
        user_info = token.get("userinfo")
        if not user_info:
            logger.error("No user_info found in Google response")
            raise HTTPException(
                status_code=400, detail="Failed to retrieve user info")

        tokens = process_google_user(user_info)
        access_token = tokens["accessToken"]
        refresh_token = tokens["refreshToken"]

        redirect_uri = (
            f"{Config.AURELIA_REDIRECT_URI}/google-callback"
            f"?accessToken={access_token}&refreshToken={refresh_token}"
        )
        logger.info(f"Redirecting to: {redirect_uri}")
        return RedirectResponse(redirect_uri)
    except Exception as e:
        request.session.clear()
        logger.exception("Google OAuth callback error")
        print("Google OAuth callback error:", e)
        raise HTTPException(status_code=400, detail=str(e))


def process_google_user(user_info: dict):
    logger.info("Processing Google user")
    user_email = user_info.get("email")
    oauth_user_id = user_info.get("sub")
    logger.debug(f"user_email: {user_email}, oauth_user_id: {oauth_user_id}")
    if not user_email or not oauth_user_id:
        logger.error("Google account did not return required information.")
        raise HTTPException(
            status_code=400, detail="Google account did not return required information."
        )

    user = get_user_by_email(user_email)
    logger.debug(f"User found by email: {user}")

    if user:
        if not user.get("oauthProvider"):
            logger.warning(
                "Account exists with this email but not with Google OAuth")
            raise HTTPException(
                status_code=400,
                detail="An account with this email already exists. Please log in with your password."
            )
        logger.info("Returning tokens for existing Google user")
        return create_and_return_auth_tokens(user["userId"])

    logger.info("Creating new Google user")
    create_user(
        user_email=user_email,
        hashed_password=None,
        email_verified=True,
        oauth_provider="google",
        oauth_user_id=oauth_user_id,
    )

    user = get_user_by_email(user_email)
    logger.info("Returning tokens for newly created Google user")
    return create_and_return_auth_tokens(user["userId"])
##
##
##
##
##


logger = logging.getLogger("apple_auth")


async def login_with_apple(request):
    logger.info("Starting Apple OAuth login flow")
    logger.debug(f"Session before Apple login: {request.session}")
    logger.debug(
        f"Session keys before Apple login: {list(request.session.keys())}")
    redirect_uri = Config.APPLE_REDIRECT_URI
    logger.debug(f"Redirect URI for Apple OAuth: {redirect_uri}")
    response = await oauth.apple.authorize_redirect(request, redirect_uri)
    logger.debug(
        f"Session keys after Apple login: {list(request.session.keys())}")
    return response


async def apple_callback(request):
    logger.info("Apple OAuth callback received")
    form = await request.form()
    logger.debug(f"Apple callback POST data: {form}")
    logger.debug(f"Session at Apple callback: {request.session}")
    logger.debug(
        f"Session keys at Apple callback: {list(request.session.keys())}")
    try:
        token = await oauth.apple.authorize_access_token(request)
        request.session.clear()
        logger.debug(f"Token received from Apple: {token}")
        id_token = token.get("id_token")
        if not id_token:
            logger.error("No id_token found in Apple response")
            raise HTTPException(
                status_code=400, detail="Failed to retrieve id_token from Apple.")

        # Decode the id_token (JWT) to get user info
        user_info = jwt.get_unverified_claims(id_token)
        logger.debug(f"Decoded user_info from id_token: {user_info}")
        user_email = user_info.get("email")
        oauth_user_id = user_info.get("sub")
        if not user_email or not oauth_user_id:
            logger.error("Missing email or sub in Apple id_token")
            raise HTTPException(
                status_code=400, detail="Apple account did not return required information.")

        tokens = process_apple_user(user_info)
        access_token = tokens["accessToken"]
        refresh_token = tokens["refreshToken"]

        redirect_uri = (
            f"{Config.AURELIA_REDIRECT_URI}/apple-callback"
            f"?accessToken={access_token}&refreshToken={refresh_token}"
        )
        logger.info(f"Redirecting to: {redirect_uri}")
        return RedirectResponse(redirect_uri)
    except Exception as e:
        request.session.clear()
        logger.exception("Apple OAuth callback error")
        print("Apple OAuth callback error:", e)
        raise HTTPException(status_code=400, detail=str(e))


def process_apple_user(user_info: dict):
    logger.info("Processing Apple user")
    user_email = user_info.get("email")
    oauth_user_id = user_info.get("sub")
    if not user_email or not oauth_user_id:
        logger.error("Apple account did not return required information.")
        raise HTTPException(
            status_code=400, detail="Apple account did not return required information."
        )

    user = get_user_by_email(user_email)
    logger.debug(f"User found by email: {user}")

    if user:
        if not user.get("oauthProvider"):
            logger.warning(
                "Account exists with this email but not with Apple OAuth")
            raise HTTPException(
                status_code=400,
                detail="An account with this email already exists. Please log in with your password."
            )
        logger.info("Returning tokens for existing Apple user")
        return create_and_return_auth_tokens(user["userId"])

    create_user(
        user_email=user_email,
        hashed_password=None,
        email_verified=True,
        oauth_provider="apple",
        oauth_user_id=oauth_user_id,
    )

    user = get_user_by_email(user_email)
    logger.info("Returning tokens for newly created Apple user")
    return create_and_return_auth_tokens(user["userId"])
