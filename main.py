import os
from fastapi import FastAPI, Depends, HTTPException, Request, status, Header
from sqlalchemy.orm import Session
import models
from schemas import (
    UserCreate,
    LoginRequest,
)
from util import (
    add_to_blacklist,
    get_current_user,
    get_user_from_token,
    hash_password,
    is_token_blacklisted,
    send_telegram_message,
    verify_password,
    create_access_token,
)
from models import User
from database import engine, Base, get_db
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated, List, Optional
from datetime import datetime

# Get the current time
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SECRET_KEY")


# Dependency to check API key
async def api_key_header(api_key: Optional[str] = Header(default=None)):
    if api_key is None or api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return api_key


# Create the database tables
Base.metadata.create_all(bind=engine)


@app.post("/users/", tags=["Authentication"])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = hash_password(user.password)
    db_user = User(name=user.name, email=user.email, password=hashed_password)

    # Check if user already exists
    user_exists = db.query(User).filter(User.email == user.email).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Send Telegram message
    message = f"New user registered:\nName: {user.name}\nEmail: {user.email}"
    send_telegram_message(message)

    return {"message": "User created successfully", "user": db_user}


@app.post("/login/", tags=["Authentication"])
def login_user(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    if not verify_password(request.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    # Send Telegram message
    message = f"User logged in:\nEmail: {user.email}\nTime: {current_time}"
    send_telegram_message(message)

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/logout/", tags=["Authentication"])
def logout_user(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if auth_header is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    # Extract the token from the Authorization header
    token = auth_header.split(" ")[1]

    # Check if the token is blacklisted
    if not is_token_blacklisted(token, db):
        add_to_blacklist(token, db)

    # Get the user information from the token
    user_info = get_user_from_token(token)
    user_name = user_info.get(
        "name", "Unknown User"
    )  # Get the user's name from the decoded token

    # Get the current logout time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Prepare the logout message
    message = (
        f"User logged out:\nName: {user_name}\nToken: {token}\nTime: {current_time}"
    )
    send_telegram_message(message)

    return {"message": "Logged out successfully"}
