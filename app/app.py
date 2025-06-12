import logging
from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware
from app.config import Config
from app.routes.auth_route import router as auth_router
from app.routes.user_route import router as user_router
from app.routes.corrections_route import router as corrections_router

app = FastAPI()

logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level to INFO
    format="%(asctime)s [%(levelname)s] %(message)s",  # Log format
    datefmt="%Y-%m-%d %H:%M:%S",  # Date format
)
 
# middleware required for authlib (Google OAuth)
app.add_middleware(
    SessionMiddleware,
    secret_key=Config.SECRET_KEY,  
    session_cookie="session",
    https_only=True,
    # same_site="none",
    # domain=".aurelialabs.net",
) 


@app.middleware("http")
async def log_cookies(request: Request, call_next):
    cookies = request.cookies
    logging.debug(f"Incoming cookies: {cookies}")
    response = await call_next(request)
    return response

# home route
@app.get("/")
def home():
    return {"message": "Aurelia API is running"}

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(corrections_router)