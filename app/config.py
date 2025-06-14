import os
from dotenv import load_dotenv

if os.path.exists(".env.development"):
    load_dotenv(dotenv_path=".env.development")
elif os.path.exists(".env.production"):
    load_dotenv(dotenv_path=".env.production")


class Config:
    ENV = os.getenv("ENV", "production")
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    MONGO_URI = os.getenv("MONGO_URI")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))
    TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    AURELIA_REDIRECT_URI = os.getenv("AURELIA_REDIRECT_URI")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
    APPLE_TEAM_ID = os.getenv("APPLE_TEAM_ID")
    APPLE_CLIENT_ID = os.getenv("APPLE_CLIENT_ID")
    APPLE_KEY_ID = os.getenv("APPLE_KEY_ID")
    APPLE_PRIVATE_KEY = os.getenv("APPLE_PRIVATE_KEY")
    APPLE_REDIRECT_URI = os.getenv("APPLE_REDIRECT_URI")

    @staticmethod
    def validate():
        required_vars = ["TOGETHER_API_KEY", "SECRET_KEY",
                         "GOOGLE_CLIENT_ID", "GOOGLE_REDIRECT_URI"]
        for var in required_vars:
            if not getattr(Config, var):
                raise EnvironmentError(
                    f"Missing required environment variable: {var}")
