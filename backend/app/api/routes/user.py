from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
import bcrypt
import jwt
import traceback
import re
from datetime import datetime, timedelta
from pydantic import BaseModel

from ...db.session import get_db
from ...db.models import User
from ...core.config import settings
from ...core.firebase_admin import verify_firebase_token

router = APIRouter()

# Pydantic models for request/response
class UserCreate(BaseModel):
    email: str
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# OAuth2 setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/users/token")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    print(f"Attempting to authenticate user with token: {token[:10]}...")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Check if this is a Firebase token (they're typically longer than JWT tokens)
    if len(token) > 500:  # Firebase tokens are usually very long
        print("Token appears to be a Firebase token, attempting Firebase verification")
        try:
            firebase_data = verify_firebase_token(token)
            if firebase_data:
                print(f"Firebase token verified for: {firebase_data.get('email', 'unknown')}")
                
                # Try to find user by email
                firebase_email = firebase_data.get("email")
                if not firebase_email:
                    print("No email in Firebase token")
                    raise credentials_exception
                    
                user = db.query(User).filter(User.email == firebase_email).first()
                
                # If user doesn't exist in our DB but has valid Firebase auth, create them
                if not user:
                    print(f"Auto-creating user for verified Firebase user: {firebase_email}")
                    # Generate a username based on email (before the @)
                    email_username = re.sub(r'[^a-zA-Z0-9]', '', firebase_email.split('@')[0])
                    # Make sure username is unique
                    base_username = email_username
                    count = 1
                    while db.query(User).filter(User.username == email_username).first():
                        email_username = f"{base_username}{count}"
                        count += 1
                        
                    user = User(
                        email=firebase_email,
                        username=email_username,
                        # We don't have a password for Firebase users, but we need something in the column
                        # Generate a random hash that can't be used for login through the standard method
                        hashed_password=get_password_hash(f"FIREBASE_USER_{datetime.utcnow().timestamp()}")
                    )
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                    print(f"Created new user: {user.username} for Firebase authentication")
                
                return user
            else:
                print("Firebase token verification failed")
        except Exception as e:
            print(f"Firebase auth error: {str(e)}")
            # If Firebase verification fails, continue to try JWT verification
    
    # Standard JWT token verification
    try:
        print("Proceeding with JWT token verification")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        print(f"Extracted user_id: {user_id}")
        if user_id is None:
            print("No user_id found in token")
            raise credentials_exception
    except jwt.PyJWTError as e:
        print(f"JWT decode error: {str(e)}")
        raise credentials_exception
        
    print(f"Querying database for user with ID: {user_id}")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        print(f"No user found with ID: {user_id}")
        raise credentials_exception
    print(f"User found: {user.username}")
    return user

@router.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user_email = db.query(User).filter(User.email == user.email).first()
    if db_user_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user_username = db.query(User).filter(User.username == user.username).first()
    if db_user_username:
        raise HTTPException(status_code=400, detail="Username already taken")
        
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.options("/users/token")
async def options_token(request: Request):
    # Handle OPTIONS request specifically for the token endpoint
    origin = request.headers.get("origin", "")
    print(f"OPTIONS request for token endpoint from origin: {origin}")
    
    # Create response with appropriate CORS headers
    response = Response(content="", status_code=200)
    
    # Always allow the Cloudflare domain - more permissive to allow any origin during testing
    response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept, Origin, User-Agent"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Max-Age"] = "86400"  # 24 hours
    
    print("Sending OPTIONS response with headers:", response.headers)
    return response

@router.post("/users/token", response_model=Token)
async def login_for_access_token(request: Request, response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        print(f"Login attempt for user: {form_data.username}")
        
        # Get origin header for CORS
        origin = request.headers.get("origin", "")
        print(f"Request origin: {origin}")
        
        # Always add CORS headers for login endpoint - critical for login to work
        response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            print(f"Authentication failed for user: {form_data.username}")
            # Even for errors, maintain CORS headers
            error_response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Incorrect username or password"},
            )
            error_response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
            error_response.headers["Access-Control-Allow-Credentials"] = "true"
            error_response.headers["WWW-Authenticate"] = "Bearer"
            return error_response
        
        # Generate access token
        access_token = create_access_token(data={"sub": user.id})
        print(f"Token generated for user: {user.username}")
        
        # Return in correct format
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        print(f"Login error traceback: {traceback.format_exc()}")
        # For exceptions, make sure we return CORS headers too
        error_response = JSONResponse(
            status_code=500,
            content={"detail": str(e)},
        )
        error_response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
        error_response.headers["Access-Control-Allow-Credentials"] = "true"
        return error_response

@router.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# New endpoint to validate Firebase tokens directly
@router.post("/users/validate-firebase-token")
async def validate_firebase_token(request: Request, response: Response):
    try:
        # Get the authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing Firebase token"}
            )
        
        token = auth_header.split(" ")[1]
        firebase_data = verify_firebase_token(token)
        
        if firebase_data:
            return {"valid": True, "user_info": {
                "email": firebase_data.get("email"),
                "uid": firebase_data.get("uid")
            }}
        else:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"valid": False, "detail": "Invalid Firebase token"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"valid": False, "detail": str(e)}
        )