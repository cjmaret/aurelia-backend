from authlib.integrations.starlette_client import OAuth

from app.config import Config
from app.utils.auth_utils import generate_apple_client_secret

Config.validate()

oauth = OAuth()

# Google OAuth
oauth.register(
    name="google",
    client_id=Config.GOOGLE_CLIENT_ID,
    client_secret=Config.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"}
)


# Apple OAuth
oauth.register(
    name="apple",
    client_id=Config.APPLE_CLIENT_ID,
    client_secret=generate_apple_client_secret(),
    authorize_url="https://appleid.apple.com/auth/authorize",
    access_token_url="https://appleid.apple.com/auth/token",
    api_base_url="https://appleid.apple.com",
    client_kwargs={
        "scope": "name email",
        "response_mode": "form_post",
        "response_type": "code",
    },
)
