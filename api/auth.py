"""
JWT Authentication for Simple LMS API
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional
from django.conf import settings
from django.contrib.auth.models import User
from ninja.errors import HttpError


# JWT Configuration
SECRET_KEY = getattr(settings, 'SECRET_KEY', 'django-insecure-dev-key')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE = 60  # minutes
REFRESH_TOKEN_EXPIRE = 60 * 24 * 7  # 7 days in minutes


def create_access_token(user_id: int) -> tuple:
    """Create JWT access token."""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE)
    payload = {
        'user_id': user_id,
        'exp': expire,
        'type': 'access'
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, ACCESS_TOKEN_EXPIRE * 60


def create_refresh_token(user_id: int) -> tuple:
    """Create JWT refresh token."""
    expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE)
    payload = {
        'user_id': user_id,
        'exp': expire,
        'type': 'refresh'
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, REFRESH_TOKEN_EXPIRE * 60


def create_tokens(user_id: int) -> dict:
    """Create both access and refresh tokens."""
    access_token, access_expires = create_access_token(user_id)
    refresh_token, refresh_expires = create_refresh_token(user_id)
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'bearer',
        'expires_in': ACCESS_TOKEN_EXPIRE * 60
    }


def verify_token(token: str, token_type: str = 'access') -> dict:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get('type') != token_type:
            raise HttpError(401, "Invalid token type")
        
        # Check expiration
        exp = payload.get('exp')
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            raise HttpError(401, "Token has expired")
        
        return payload
    except jwt.ExpiredSignatureError:
        raise HttpError(401, "Token has expired")
    except jwt.InvalidTokenError:
        raise HttpError(401, "Invalid token")


def get_user_from_token(token: str) -> User:
    """Get user from JWT token."""
    payload = verify_token(token, 'access')
    user_id = payload.get('user_id')
    
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        raise HttpError(401, "User not found")


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password."""
    try:
        user = User.objects.get(username=username)
        if user.check_password(password):
            return user
    except User.DoesNotExist:
        pass
    return None