"""
JWT Authentication for CoreChain
Role-based: admin, researcher, institution
"""
import jwt
import bcrypt
import json
import os
from datetime import datetime, timedelta
from functools import wraps
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.getenv('JWT_SECRET', 'corechain-secret-change-in-prod-2026')
ALGORITHM = 'HS256'
TOKEN_EXPIRE_HOURS = 24

security = HTTPBearer(auto_error=False)


def create_token(user_id: str, role: str) -> str:
    payload = {
        'sub': user_id,
        'role': role,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token expired')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Invalid token')


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail='Authentication required')
    return decode_token(credentials.credentials)


def require_role(*roles):
    """Dependency factory for role-based access"""
    def checker(credentials: HTTPAuthorizationCredentials = Security(security)):
        if not credentials:
            raise HTTPException(status_code=401, detail='Authentication required')
        payload = decode_token(credentials.credentials)
        if payload.get('role') not in roles:
            raise HTTPException(status_code=403, detail=f'Requires role: {roles}')
        return payload
    return checker
