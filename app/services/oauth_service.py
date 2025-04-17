from authlib.integrations.starlette_client import OAuth

from app.config import Config

Config.validate()

oauth = OAuth()

# this is an instance of Google OAuth
oauth.register(
    name="google",
    client_id=Config.GOOGLE_CLIENT_ID,
    client_secret=Config.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"}
)
