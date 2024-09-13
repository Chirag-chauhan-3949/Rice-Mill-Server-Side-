import os
from fastapi import FastAPI, Depends, HTTPException, Request, status, Header
from sqlalchemy.orm import Session
import models
from schemas import (
    AddRiceMillBase,
    AddUserBase,
    DhanAwakBase,
    PermissionsUpdateRequest,
    UpdateDhanAwakBase,
    UpdateRiceMillBase,
    UserCreate,
    RoleBase,
    RiceMillResponse,
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
from models import Add_Rice_Mill, Dhan_Awak, Permission, User, Role
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
def create_user(user: AddUserBase, db: Session = Depends(get_db)):
    hashed_password = hash_password(user.password)
    db_user = User(
        name=user.name,
        email=user.email,
        password=hashed_password,
        role=user.role,  # Use the role from AddUserBase
    )

    # Check if user already exists
    user_exists = db.query(User).filter(User.email == user.email).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Send Telegram message
    message = f"New user registered:\nName: {user.name}\nEmail: {user.email}\nRole: {user.role}"
    send_telegram_message(message)

    return {"message": "User created successfully", "user": db_user}


# Create Role
@app.post("/create-role/", tags=["Authentication"])
def create_role(
    role: RoleBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role_exists = db.query(Role).filter(Role.role_name == role.role_name).first()
    if role_exists:
        raise HTTPException(status_code=400, detail="Role already exists")

    # Create the role and associate it with the user
    db_role = Role(role_name=role.role_name, user_id=current_user.id)

    db.add(db_role)
    db.commit()
    db.refresh(db_role)

    message = f"New user Role Created:\nRole Name: {role.role_name}"
    send_telegram_message(message)

    return {"message": "Role created successfully", "role": db_role}


# To get all roles data
@app.get("/get-roles-data", response_model=List[RoleBase], tags=["Get Form"])
async def get_all_roles(db: Session = Depends(get_db)):
    # Retrieve all rice mills
    roles = db.query(Role).all()

    return roles


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

    return {"access_token": access_token, "token_type": "bearer", "role": user.role}


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


@app.get("/roles-and-permissions")
def get_roles_and_permissions(db: Session = Depends(get_db)):
    roles = db.query(Role).all()
    permissions = db.query(Permission).all()
    permissions_dict = {perm.role_id: perm.permissions for perm in permissions}
    return {"roles": roles, "permissions": permissions_dict}


@app.post("/update-permissions")
def update_permissions(
    request: PermissionsUpdateRequest, db: Session = Depends(get_db)
):
    for role_id, perms in request.permissions.items():
        permission = db.query(Permission).filter(Permission.role_id == role_id).first()
        if permission:
            db.execute(
                Permission.__table__.update()
                .where(Permission.role_id == role_id)
                .values(permissions=perms)
            )
        else:
            new_permission = Permission(role_id=role_id, permissions=perms)
            db.add(new_permission)
    db.commit()
    return {"message": "Permissions updated successfully"}


# Add Rice Mill
@app.post("/add-rice-mill/", response_model=AddRiceMillBase, tags=["Add Form"])
async def add_rice_mill(
    addricemill: AddRiceMillBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check if a rice mill with the same name exists
    if (
        db.query(Add_Rice_Mill)
        .filter(Add_Rice_Mill.rice_mill_name == addricemill.rice_mill_name)
        .first()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rice Mill with this name already exists",
        )

    # Create and add the new rice mill entry
    db_about_rice_mill = Add_Rice_Mill(
        gst_number=addricemill.gst_number,
        rice_mill_name=addricemill.rice_mill_name,
        mill_address=addricemill.mill_address,
        phone_number=addricemill.phone_number,
        rice_mill_capacity=addricemill.rice_mill_capacity,
        user_id=current_user.id,
    )
    db.add(db_about_rice_mill)
    db.commit()
    db.refresh(db_about_rice_mill)

    # Prepare and send the message
    message = (
        f"User {current_user.name} added a new rice mill:\n"
        f"Name: {db_about_rice_mill.rice_mill_name}\n"
        f"Data: {dict(gst_number=db_about_rice_mill.gst_number, rice_mill_name=db_about_rice_mill.rice_mill_name, mill_address=db_about_rice_mill.mill_address, phone_number=db_about_rice_mill.phone_number, rice_mill_capacity=db_about_rice_mill.rice_mill_capacity)}"
    )
    send_telegram_message(message)

    return db_about_rice_mill


# To get specific rice mill data
@app.get(
    "/get-rice-mill/{rice_mill_id}", response_model=AddRiceMillBase, tags=["Get Form"]
)
async def get_rice_mill(rice_mill_id: int, db: Session = Depends(get_db)):
    # Retrieve the rice mill by ID
    rice_mill = (
        db.query(Add_Rice_Mill)
        .filter(Add_Rice_Mill.rice_mill_id == rice_mill_id)
        .first()
    )

    # Check if the rice mill exists
    if not rice_mill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rice Mill not found",
        )

    return rice_mill


# To get all rice mill data
@app.get("/get-all-rice-mills", response_model=List[AddRiceMillBase], tags=["Get Form"])
async def get_all_rice_mills(db: Session = Depends(get_db)):
    # Retrieve all rice mills
    rice_mills = db.query(Add_Rice_Mill).all()

    return rice_mills


# Update Rice Mill
@app.put(
    "/update-rice-mill/{rice_mill_id}",
    response_model=UpdateRiceMillBase,
    tags=["Update Form"],
)
async def update_rice_mill(
    rice_mill_id: int,
    update_data: UpdateRiceMillBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Retrieve the rice mill by ID
    rice_mill = (
        db.query(Add_Rice_Mill)
        .filter(Add_Rice_Mill.rice_mill_id == rice_mill_id)
        .first()
    )

    # Check if the rice mill exists
    if not rice_mill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rice Mill not found",
        )

    # Update the rice mill data
    rice_mill.gst_number = update_data.gst_number
    rice_mill.rice_mill_name = update_data.rice_mill_name
    rice_mill.mill_address = update_data.mill_address
    rice_mill.phone_number = update_data.phone_number
    rice_mill.rice_mill_capacity = update_data.rice_mill_capacity

    db.commit()
    db.refresh(rice_mill)

    # Prepare and send the message
    message = (
        f"User {current_user.name} updated the rice mill:\n"
        f"Name: {rice_mill.rice_mill_name}\n"
        f"Updated Data: {dict(gst_number=rice_mill.gst_number, rice_mill_name=rice_mill.rice_mill_name, mill_address=rice_mill.mill_address, phone_number=rice_mill.phone_number, rice_mill_capacity=rice_mill.rice_mill_capacity)}"
    )
    send_telegram_message(message)

    return rice_mill


# Delete Rice Mill
@app.delete(
    "/delete-rice-mill/{rice_mill_id}", response_model=dict, tags=["Delete Form"]
)
async def delete_rice_mill(
    rice_mill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Find the rice mill by ID
    rice_mill = (
        db.query(Add_Rice_Mill)
        .filter(Add_Rice_Mill.rice_mill_id == rice_mill_id)
        .first()
    )

    # If rice mill not found, raise an exception
    if not rice_mill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rice Mill not found",
        )

    # Delete the rice mill entry
    db.delete(rice_mill)
    db.commit()

    # Prepare and send the message
    message = (
        f"User {current_user.name} deleted the rice mill: {rice_mill.rice_mill_name}"
    )
    send_telegram_message(message)

    return {"message": "Rice Mill deleted successfully"}


# Create Dhan Awak
@app.post("/create-dhanawak", response_model=DhanAwakBase, tags=["Create Form"])
async def create_dhanawak(
    dhanawak_data: DhanAwakBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Create a new DhanAwak instance
    new_dhanawak = Dhan_Awak(**dhanawak_data.dict())

    # Add the new DhanAwak to the session
    db.add(new_dhanawak)
    db.commit()
    db.refresh(new_dhanawak)

    # Prepare and send the message
    message = (
        f"User {current_user.name} created a new DhanAwak record:\n"
        f"ID: {new_dhanawak.dhan_awak_id}\n"
        f"Data: {dhanawak_data.dict()}"
    )
    send_telegram_message(message)

    return new_dhanawak


# Get Specific Dhan Awak Data
@app.get("/get-dhanawak/{dhan_awak_id}", response_model=DhanAwakBase, tags=["Get Form"])
async def get_dhanawak(dhan_awak_id: int, db: Session = Depends(get_db)):
    # Retrieve the DhanAwak by ID
    dhanawak = (
        db.query(Dhan_Awak).filter(Dhan_Awak.dhan_awak_id == dhan_awak_id).first()
    )

    # Check if the DhanAwak exists
    if not dhanawak:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DhanAwak not found",
        )

    return dhanawak


# Get all Dhan Awak Data
@app.get("/get-all-dhanawak", response_model=List[DhanAwakBase], tags=["Get Form"])
async def get_all_dhanawak(db: Session = Depends(get_db)):
    # Retrieve all DhanAwak records
    dhanawak_records = db.query(Dhan_Awak).all()

    return dhanawak_records


# Update Dhan Awak
@app.put(
    "/update-dhanawak/{dhan_awak_id}",
    response_model=UpdateDhanAwakBase,
    tags=["Update Form"],
)
async def update_dhanawak(
    dhan_awak_id: int,
    update_data: UpdateDhanAwakBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Retrieve the DhanAwak by ID
    dhanawak = (
        db.query(Dhan_Awak).filter(Dhan_Awak.dhan_awak_id == dhan_awak_id).first()
    )

    # Check if the DhanAwak exists
    if not dhanawak:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DhanAwak not found",
        )

    # Update the DhanAwak data
    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(dhanawak, key, value)

    db.commit()
    db.refresh(dhanawak)

    # Prepare and send the message
    message = (
        f"User {current_user.name} updated the DhanAwak record:\n"
        f"ID: {dhanawak.dhan_awak_id}\n"
        f"Updated Data: {update_data.dict()}"
    )
    send_telegram_message(message)

    return dhanawak


# Delete Dhan Awak
@app.delete(
    "/delete-dhanawak/{dhan_awak_id}", response_model=dict, tags=["Delete Form"]
)
async def delete_dhanawak(
    dhan_awak_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Find the DhanAwak by ID
    dhanawak = (
        db.query(Dhan_Awak).filter(Dhan_Awak.dhan_awak_id == dhan_awak_id).first()
    )

    # If DhanAwak not found, raise an exception
    if not dhanawak:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DhanAwak not found",
        )

    # Delete the DhanAwak entry
    db.delete(dhanawak)
    db.commit()

    # Prepare and send the message
    message = f"User {current_user.name} deleted the DhanAwak record with ID: {dhanawak.dhan_awak_id}"
    send_telegram_message(message)

    return {"message": "DhanAwak deleted successfully"}
