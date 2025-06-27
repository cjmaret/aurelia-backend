import random
import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from app.config import Config
from app.services.database_service import add_verification_code, get_verification_code, store_refresh_token

SECRET_KEY = Config.SECRET_KEY
ALGORITHM = Config.ALGORITHM

ACCESS_TOKEN_EXPIRE_MINUTES = Config.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = Config.REFRESH_TOKEN_EXPIRE_DAYS

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_and_return_auth_tokens(user_id: str):
    access_token = create_access_token(data={"sub": str(user_id)})
    refresh_token = create_refresh_token(data={"sub": str(user_id)})

    # store refresh token in database
    store_refresh_token(user_id, refresh_token)

    return {
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "tokenType": "bearer"
    }


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user_from_token(token: str = Depends(oauth2_scheme)):
    return decode_token(token)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password):
    return pwd_context.hash(password)


def generate_verification_code(length=6):
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])


def create_email_verification_code(user_id: str, email: str = None, expires_minutes: int = 10) -> str:

    code = generate_verification_code()
    expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)

    add_verification_code(user_id, code, expires_at,
     'email_verification', email)

    return code


def verify_email_verification_code(user_id: str, code: str, email: str = None) -> bool:
    verification_code = get_verification_code(user_id, 'email_verification')

    if not verification_code or verification_code['code'] != code or verification_code['expiresAt'] < datetime.utcnow():
        return False
    
    if email is not None and verification_code.get('email') != email.strip().lower():
        return False

    return True


def create_password_reset_code(user_id: str, expires_minutes: int = 10) -> str:
    code = generate_verification_code()
    expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)
    add_verification_code(user_id, code, expires_at, 'password_reset')
    return code


def verify_password_reset_code(user_id: str, code: str) -> bool:
    verification_code = get_verification_code(user_id, 'password_reset')
    if (
        not verification_code or
        verification_code['code'] != code or
        verification_code['expiresAt'] < datetime.utcnow()
    ):
        return False
    return True

##
##
##
##

# # TODO: remove the two below
# def create_email_verification_token(user_id: str, email: str, expires_minutes: int = 60) -> str:
#     to_encode = {
#         "sub": user_id,
#         "email": email,
#         "type": "email_verification"
#     }
#     expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt


# def decode_email_verification_token(token: str):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

#         if payload.get("type") != "email_verification":
#             raise HTTPException(status_code=401, detail="Invalid token type")
#         user_id: str = payload.get("sub")
#         email: str = payload.get("email")

#         if user_id is None or email is None:
#             raise HTTPException(status_code=401, detail="Invalid token")

#         return user_id, email

#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Token has expired")
#     except jwt.InvalidTokenError:
#         raise HTTPException(status_code=401, detail="Invalid token")

def generate_apple_client_secret():
    headers = {
        "kid": Config.APPLE_KEY_ID,
        "alg": "ES256"
    }
    payload = {
        "iss": Config.APPLE_TEAM_ID,
        "iat": int(datetime.utcnow().timestamp()),
        "exp": int((datetime.utcnow() + timedelta(days=180)).timestamp()),
        "aud": "https://appleid.apple.com",
        "sub": Config.APPLE_CLIENT_ID,
    }
    client_secret = jwt.encode(
        payload,
        Config.APPLE_PRIVATE_KEY,
        algorithm="ES256",
        headers=headers
    )
    return client_secret
