from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from app.config import Config
from app.controllers.auth_controller import login_user, process_google_user, refresh_user_token, register_user, request_email_verification, request_password_reset, reset_password, update_user_password, delete_user, verify_email
from app.schemas.request_schemas.refresh_token_request_schema import RefreshTokenRequest
from app.schemas.request_schemas.request_password_reset_request_schema import RequestPasswordResetRequest
from app.schemas.request_schemas.update_password_request_schema import UpdatePasswordRequest
from app.schemas.request_schemas.reset_password_request_schema import ResetPasswordRequest
from app.schemas.request_schemas.verify_email_request_schema import VerifyEmailRequestSchema
from app.services.oauth_service import oauth
from app.schemas.request_schemas.login_request_schema import LoginRequest
from app.schemas.request_schemas.register_request_schema import RegisterRequest
from app.utils.auth_utils import get_current_user_from_token


router = APIRouter()


@router.post("/login")
def login(request: LoginRequest):
    return login_user(request.userEmail, request.password)


@router.post("/register")
def register(request: RegisterRequest):
    return register_user(request.userEmail, request.password)


@router.post("/auth/request-email-verification")
def request_email_verification_route(
    user_id: str = Depends(get_current_user_from_token)
):
    return request_email_verification(user_id)


@router.post("/auth/verify-email")
def verify_email_route(request: VerifyEmailRequestSchema):
    return verify_email(request.token)


@router.delete("/delete-user")
def delete_user_account(
    user_id: str = Depends(get_current_user_from_token)
):
    return delete_user(user_id)


@router.post("/auth/refresh")
def refresh_token(request: RefreshTokenRequest):
    return refresh_user_token(request.refreshToken)


@router.post("/auth/update-password")
def update_password(
    passwordRequestBody: UpdatePasswordRequest,
    user_id: str = Depends(get_current_user_from_token)
):
    return update_user_password(user_id, passwordRequestBody.currentPassword, passwordRequestBody.newPassword)


@router.post("/auth/request-password-reset")
def request_password_reset_route(request: RequestPasswordResetRequest):
    return request_password_reset(request.userEmail)


@router.post("/auth/reset-password")
def reset_password_route(request: ResetPasswordRequest):
    return reset_password(request.token, request.newPassword)

# user first clicks to sign in with google


@router.get("/auth/login/google")
async def login_with_google(request: Request):
    redirect_uri = Config.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)

# user is redirected back to this endpoint after authentication


@router.get("/auth/callback/google")
async def google_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")  # retrieve user info from the token
        if not user_info:
            raise HTTPException(
                status_code=400, detail="Failed to retrieve user info")

        access_token = process_google_user(user_info)
        redirect_uri = f"com.aureliaai.myapp:/auth/google-callback?token={access_token}"
        return RedirectResponse(redirect_uri)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
