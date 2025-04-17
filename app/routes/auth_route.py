from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from app.config import Config
from app.controllers.auth_controller import login_user, process_google_user, refresh_user_token, register_user
from app.schemas.request_schemas.refresh_token_request_schema import RefreshTokenRequest
from app.services.oauth_service import oauth
from app.schemas.request_schemas.login_request_schema import LoginRequest
from app.schemas.request_schemas.register_request_schema import RegisterRequest


router = APIRouter()

@router.post("/login")
def login(request: LoginRequest):
    return login_user(request.userEmail, request.password)

@router.post("/register")
def register(request: RegisterRequest):
    return register_user(request.userEmail, request.password)

@router.post("/auth/refresh")
def refresh_token(request: RefreshTokenRequest):
    return refresh_user_token(request.refreshToken)



#TODO: find out how to get oauth working (maybe needs to be in production)
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
        redirect_uri = f"com.conversantai.myapp:/auth/google-callback?token={access_token}"
        return RedirectResponse(redirect_uri)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
