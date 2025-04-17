import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.config import Config
from app.routes.auth_route import router as auth_router
from app.routes.user_route import router as user_router
from app.routes.corrections_route import router as corrections_router

app = FastAPI()
 
# middleware required for authlib (Google OAuth)
app.add_middleware(
    SessionMiddleware,
    secret_key=Config.SECRET_KEY,  
    session_cookie="session", 
) 

origins = []

if os.getenv("ENV") == "production":
    origins = ["https://your-production-frontend.com"]
else:
    origins = ["http://localhost:8081"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# home route
@app.get("/")
def home():
    return {"message": "Conversant API is running"}

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(corrections_router)