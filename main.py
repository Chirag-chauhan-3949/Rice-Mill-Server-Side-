from fastapi import FastAPI, Depends, HTTPException, Request, status, Header
from sqlalchemy.orm import Session
import models
from schemas import (
    AddNewUserCreate,
    UserCreate,
    LoginRequest,
    AddRiceMillBase,
    AddNewUserResponse,
    RoleBase,
)
from util import (
    add_to_blacklist,
    get_current_user,
    hash_password,
    is_token_blacklisted,
    verify_password,
    create_access_token,
)
from models import Add_New_User, Add_Rice_Mill, User
from database import engine, Base, get_db
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated, List, Optional


# Secret key for JWT generation (should be kept secret)
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

API_KEY = "your_secret_api_key"


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
    return {"message": "User created successfully", "user": db_user}


@app.post("/login/", tags=["Authentication"])
def login_user(request: LoginRequest, db: Session = Depends(get_db)):
    # Check credentials in the User table
    user = db.query(User).filter(User.email == request.email).first()

    # Check credentials in the Add_New_User table if not found in User
    if not user:
        user = (
            db.query(Add_New_User).filter(Add_New_User.email == request.email).first()
        )

    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # Verify password for the user found
    if not verify_password(request.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/logout/", tags=["Authentication"])
def logout_user(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if auth_header is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = auth_header.split(" ")[1]  # Assumes "Bearer <token>"

    if not is_token_blacklisted(token, db):
        add_to_blacklist(token, db)

    return {"message": "Logged out successfully"}


@app.post("/role", tags=["Authentication"])
def create_role(
    request: RoleBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # Get the logged-in user
):
    # Create a role and associate it with the current user
    role_data = models.Role(role_name=request.role_name, user_id=current_user.id)

    db.add(role_data)
    db.commit()
    db.refresh(role_data)

    return role_data


@app.post("/add-new-user/", response_model=AddNewUserResponse, tags=["Authentication"])
def add_new_user(
    user: AddNewUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Ensure the user is authenticated
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    # Check if the new user already exists
    user_exists = (
        db.query(Add_New_User).filter(Add_New_User.email == user.email).first()
    )
    if user_exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create the new user
    hashed_password = hash_password(user.password)
    db_user = Add_New_User(
        name=user.name,
        email=user.email,
        password=hashed_password,
        user_id=current_user.id,  # Ensure user_id field is present in the model
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


"""
Adding Rice Mill Form
"""


# Add Rice Mill
@app.post("/add-rice-mill/", response_model=AddRiceMillBase, tags=["Add Form"])
async def add_rice_mill(
    addricemill: AddRiceMillBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check if a rice mill with the same name already exists
    existing_rice_mill = (
        db.query(Add_Rice_Mill)
        .filter(Add_Rice_Mill.rice_mill_name == addricemill.rice_mill_name)
        .first()
    )

    if existing_rice_mill:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rice Mill with this name already exists",
        )

    # Create new rice mill entry
    db_about_rice_mill = Add_Rice_Mill(
        gst_number=addricemill.gst_number,
        rice_mill_name=addricemill.rice_mill_name,
        mill_address=addricemill.mill_address,
        phone_number=addricemill.phone_number,
        rice_mill_capacity=addricemill.rice_mill_capacity,
        user_id=current_user.id,  # Associate the rice mill with the current user
    )

    db.add(db_about_rice_mill)
    db.commit()
    db.refresh(db_about_rice_mill)

    return db_about_rice_mill
