from fastapi import APIRouter, Depends, Request
from app.controllers.auth_controller import google_callback, login_user, login_with_google, refresh_user_token, register_user, request_email_verification, request_password_reset, reset_password, update_user_password, delete_user, verify_email
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


@router.get("/auth/login/google")
async def login_with_google_route(request: Request):
    return await login_with_google(request)


# user is redirected back to this endpoint after authentication
@router.get("/auth/callback/google")
async def google_callback_route(request: Request):
    return await google_callback(request)
