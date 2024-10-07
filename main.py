import os
from fastapi import FastAPI, Depends, HTTPException, Request, status, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
import models
from schemas import (
    AddRiceMillBase,
    TransporterBase,
    AddUserBase,
    # DhanAwakBase,
    PermissionsUpdateRequest,
    TruckBase,
    # UpdateDhanAwakBase,
    UpdateRiceMillBase,
    RoleBase,
    LoginRequest,
    AddRiceMillBase,
    TransporterBase,
    # DhanAwakBase,
    RoleBase,
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
from models import Add_Rice_Mill, Transporter, Permission, User, Role
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
    # allow_origins=["http://mill.dappfolk.com"],  # Replace with your frontend's URL
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


# Get User Data
@app.get("/users/{user_id}", tags=["Authentication"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    # Query the database for the user by ID
    db_user = db.query(User).filter(User.id == user_id).first()

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Return the user details
    return {"name": db_user.name, "email": db_user.email, "role": db_user.role}


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

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id,
    }


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
    # Fetch all roles and permissions
    roles = db.query(Role).all()
    permissions = db.query(Permission).all()

    # Convert roles to a list of role names
    role_names = [role.role_name for role in roles]

    # Create a permissions dictionary with role names as keys
    permissions_dict = {
        role.role_name: {"update": False, "delete": False} for role in roles
    }

    for perm in permissions:
        role_name = next((r.role_name for r in roles if r.id == perm.role_id), None)
        if role_name:
            permissions_dict[role_name] = perm.permissions

    return {"roles": role_names, "permissions": permissions_dict}


@app.post("/update-permissions")
def update_permissions(
    request: PermissionsUpdateRequest, db: Session = Depends(get_db)
):
    for role_name, perms in request.permissions.items():
        # Assuming that `role_name` is the actual name and you can get `role_id` from `role_name`
        role = db.query(Role).filter(Role.role_name == role_name).first()
        if role:
            role_id = role.id
            permission = (
                db.query(Permission).filter(Permission.role_id == role_id).first()
            )
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


# Add Transporter
@app.post("/add-transporter/", response_model=TransporterBase, tags=["Add Form"])
async def add_transporter(
    transporter: TransporterBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check if a transporter with the same name exists
    if (
        db.query(Transporter)
        .filter(Transporter.transporter_name == transporter.transporter_name)
        .first()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transporter with this name already exists",
        )

    # Create and add the new transporter entry
    db_transporter = Transporter(
        transporter_name=transporter.transporter_name,
        transporter_phone_number=transporter.transporter_phone_number,
        user_id=current_user.id,
    )
    db.add(db_transporter)
    db.commit()
    db.refresh(db_transporter)

    # Prepare and send the message
    message = (
        f"User {current_user.name} added a new transporter:\n"
        f"Name: {db_transporter.transporter_name}\n"
        f"Phone: {db_transporter.transporter_phone_number}"
    )
    send_telegram_message(message)

    return db_transporter


@app.get(
    "/get-transporter/{transporter_id}",
    response_model=TransporterBase,
    tags=["Get Form"],
)
async def get_transporter(transporter_id: int, db: Session = Depends(get_db)):
    # Retrieve the transporter by ID
    transporter = (
        db.query(Transporter)
        .filter(Transporter.transporter_id == transporter_id)
        .first()
    )

    # Check if the transporter exists
    if not transporter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transporter not found",
        )

    return transporter


@app.get(
    "/get-all-transporters",
    response_model=List[TransporterBase],
    tags=["Get Form"],
)
async def get_all_transporters(db: Session = Depends(get_db)):
    # Retrieve all transporters
    transporters = db.query(Transporter).all()

    return transporters


@app.put(
    "/update-transporter/{transporter_id}",
    response_model=TransporterBase,
    tags=["Update Form"],
)
async def update_transporter(
    transporter_id: int,
    update_data: TransporterBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Retrieve the transporter by ID
    transporter = (
        db.query(Transporter)
        .filter(Transporter.transporter_id == transporter_id)
        .first()
    )

    # Check if the transporter exists
    if not transporter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transporter not found",
        )

    # Update the transporter data
    transporter.transporter_name = update_data.transporter_name
    transporter.transporter_phone_number = update_data.transporter_phone_number

    db.commit()
    db.refresh(transporter)

    # Prepare and send the message
    message = (
        f"User {current_user.name} updated the transporter:\n"
        f"Name: {transporter.transporter_name}\n"
        f"Updated Phone: {transporter.transporter_phone_number}"
    )
    send_telegram_message(message)

    return transporter


@app.delete(
    "/delete-transporter/{transporter_id}", response_model=dict, tags=["Delete Form"]
)
async def delete_transporter(
    transporter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Find the transporter by ID
    transporter = (
        db.query(Transporter)
        .filter(Transporter.transporter_id == transporter_id)
        .first()
    )

    # If transporter not found, raise an exception
    if not transporter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transporter not found",
        )

    # Delete the transporter entry
    db.delete(transporter)
    db.commit()

    # Prepare and send the message
    message = f"User {current_user.name} deleted the transporter: {transporter.transporter_name}"
    send_telegram_message(message)

    return {"message": "Transporter deleted successfully"}


# # Create Dhan Awak
# @app.post("/create-dhanawak", response_model=DhanAwakBase, tags=["Create Form"])
# async def create_dhanawak(
#     dhanawak_data: DhanAwakBase,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     # Create a new DhanAwak instance
#     new_dhanawak = Dhan_Awak(**dhanawak_data.dict())

#     # Add the new DhanAwak to the session
#     db.add(new_dhanawak)
#     db.commit()
#     db.refresh(new_dhanawak)

#     # Prepare and send the message
#     message = (
#         f"User {current_user.name} created a new DhanAwak record:\n"
#         f"ID: {new_dhanawak.dhan_awak_id}\n"
#         f"Data: {dhanawak_data.dict()}"
#     )
#     send_telegram_message(message)

#     return new_dhanawak


# # Get Specific Dhan Awak Data
# @app.get("/get-dhanawak/{dhan_awak_id}", response_model=DhanAwakBase, tags=["Get Form"])
# async def get_dhanawak(dhan_awak_id: int, db: Session = Depends(get_db)):
#     # Retrieve the DhanAwak by ID
#     dhanawak = (
#         db.query(Dhan_Awak).filter(Dhan_Awak.dhan_awak_id == dhan_awak_id).first()
#     )

#     # Check if the DhanAwak exists
#     if not dhanawak:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="DhanAwak not found",
#         )

#     return dhanawak


# # Get all Dhan Awak Data
# @app.get("/get-all-dhanawak", response_model=List[DhanAwakBase], tags=["Get Form"])
# async def get_all_dhanawak(db: Session = Depends(get_db)):
#     # Retrieve all DhanAwak records
#     dhanawak_records = db.query(Dhan_Awak).all()

#     return dhanawak_records


# # Update Dhan Awak
# @app.put(
#     "/update-dhanawak/{dhan_awak_id}",
#     response_model=UpdateDhanAwakBase,
#     tags=["Update Form"],
# )
# async def update_dhanawak(
#     dhan_awak_id: int,
#     update_data: UpdateDhanAwakBase,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     # Retrieve the DhanAwak by ID
#     dhanawak = (
#         db.query(Dhan_Awak).filter(Dhan_Awak.dhan_awak_id == dhan_awak_id).first()
#     )

#     # Check if the DhanAwak exists
#     if not dhanawak:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="DhanAwak not found",
#         )

#     # Update the DhanAwak data
#     for key, value in update_data.dict(exclude_unset=True).items():
#         setattr(dhanawak, key, value)

#     db.commit()
#     db.refresh(dhanawak)

#     # Prepare and send the message
#     message = (
#         f"User {current_user.name} updated the DhanAwak record:\n"
#         f"ID: {dhanawak.dhan_awak_id}\n"
#         f"Updated Data: {update_data.dict()}"
#     )
#     send_telegram_message(message)

#     return dhanawak


# # Delete Dhan Awak
# @app.delete(
#     "/delete-dhanawak/{dhan_awak_id}", response_model=dict, tags=["Delete Form"]
# )
# async def delete_dhanawak(
#     dhan_awak_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     # Find the DhanAwak by ID
#     dhanawak = (
#         db.query(Dhan_Awak).filter(Dhan_Awak.dhan_awak_id == dhan_awak_id).first()
#     )

#     # If DhanAwak not found, raise an exception
#     if not dhanawak:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="DhanAwak not found",
#         )

#     # Delete the DhanAwak entry
#     db.delete(dhanawak)
#     db.commit()

#     # Prepare and send the message
#     message = f"User {current_user.name} deleted the DhanAwak record with ID: {dhanawak.dhan_awak_id}"
#     send_telegram_message(message)

#     return {"message": "DhanAwak deleted successfully"}


# create the post route for truck
@app.post(
    "/truck/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(api_key_header)],
    tags=["Truck"],
)
async def add_new_truck(
    truck: TruckBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_truck = (
        db.query(models.Truck).filter(models.Truck.truck_id == truck.truck_id).first()
    )

    if existing_truck:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Truck with this Number already exists",
        )
    db_truck = models.Truck(**truck.dict())
    db.add(db_truck)
    db.commit()
    db.refresh(db_truck)
    message = f"New action performed by user.\nName: {payload.get('sub')} "
    send_telegram_message(message)
    return truck


# create the get route for truck
# @app.get("/get-truck/{truck_id}", response_model=TruckBase, tags=["Truck"])
# async def get_truck(truck_id: int, db: Session = Depends(get_db)):
#     # Retrieve the Truck by ID
#     truck = db.query(models.Truck).filter(models.Truck.truck_id == truck_id).first()

#     # Check if the Truck exists
#     if not truck:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Truck not found",
#         )

#     return truck


# # create the update route for truck
# @app.put("/update-truck/{truck_id}", response_model=TruckBase, tags=["Truck"])
# async def update_truck(truck_id: int, Truck: TruckBase, db: Session = Depends(get_db)):
#     # Retrieve the Truck by ID
#     truck = db.query(models.Truck).filter(models.Truck.truck_id == truck_id).first()

#     # Check if the Truck exists
#     if not truck:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Truck not found",
#         )

#     # Update the Truck data in another way
#     truck.transport_id = Truck.transport_id
#     truck.truck_number = Truck.truck_number

#     db.commit()
#     db.refresh(truck)

#     return truck


# # write delete route for truck
# @app.delete("/delete-truck/{truck_id}", tags=["Truck"])
# async def delete_truck(truck_id: int, db: Session = Depends(get_db)):
#     # Retrieve the Truck by ID
#     truck = db.query(models.Truck).filter(models.Truck.truck_id == truck_id).first()

#     # Check if the Truck exists
#     if not truck:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Truck not found",
#         )

#     # Delete the Truck entry
#     db.delete(truck)
#     db.commit()

#     return {"message": "Truck deleted successfully"}


# @app.get(
#     "/trucks/",
#     response_model=List[TruckWithTransporter],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
#     tags=["Truck"],
# )
# async def get_all_truck_data(token: str = Header(None), db: Session = Depends(get_db)):
#     trucks = db.query(models.Truck).all()

#     # Check if the Truck exists
#     if not trucks:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Truck not found",
#         )

#     result = []
#     for truck in trucks:
#         result.append(
#             TruckWithTransporter(
#                 truck_number=truck.truck_number,
#                 transporter_name=truck.transporter.transporter_name,
#                 transport_id=truck.transport_id,
#                 truck_id=truck.truck_id,
#             )
#         )

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return result


# @app.get(
#     "/truck-numbers/",
#     response_model=List[str],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
#     tags=["Truck"],
# )
# async def get_truck_numbers(token: str = Header(None), db: Session = Depends(get_db)):
#     db_truck_numbers = db.query(models.Truck.truck_number).distinct().all()
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return [truck_number[0] for truck_number in db_truck_numbers]


# # Add Society
# @app.post(
#     "/society/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
#     tags=["Society"],
# )
# async def add_society(
#     addsociety: SocietyBase, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     existing_society = (
#         db.query(models.Society)
#         .filter(models.Society.society_id == addsociety.society_id)
#         .first()
#     )
#     if existing_society:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Society with this name already exists",
#         )
#     db_society = models.Society(**addsociety.dict())
#     db.add(db_society)
#     db.commit()
#     db.refresh(db_society)

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_society


# # Get Society Data
# @app.get(
#     "/societies/",
#     response_model=List[SocietyBase],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
#     tags=["Society"],
# )
# async def get_all_society_data(
#     token: str = Header(None), db: Session = Depends(get_db)
# ):
#     societys = db.query(models.Society).distinct().all()
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return societys


# # Get all society name for dropdown options
# @app.get(
#     "/societies-names/",
#     response_model=List[str],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
#     tags=["Society"],
# )
# async def get_all_societyes_names(
#     token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_get_all_societyes_names = db.query(models.Society.society_name).distinct().all()
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return [all_society_name[0] for all_society_name in db_get_all_societyes_names]


# # route to update society data and send telegranm message
# @app.put(
#     "/society/{society_id}",
#     response_model=SocietyBase,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
#     tags=["Society"],
# )
# async def update_society_data(
#     society_id: int,
#     addsociety: SocietyBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db.query(models.Society).filter(models.Society.society_id == society_id).update(
#         addsociety.dict()
#     )
#     db.commit()
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return addsociety


# ##################################
# # route to delete society data and send telegranm message


# @app.delete(
#     "/society/{society_id}",
#     response_model=SocietyBase,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
#     tags=["Society"],
# )
# async def delete_society_data(
#     society_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db.query(models.Society).filter(models.Society.society_id == society_id).delete()
#     db.commit()
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return {"message": "Society deleted successfully"}


# @app.get(
#     "/society-transporting-rate/{society_id}",  # Here will go my truck ID
#     response_model=SocietyTransportingRate,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
#     tags=["Society"],
# )
# async def society_data(
#     society_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     society_transporting = (
#         db.query(models.Society).filter_by(society_id=society_id).all()
#     )

#     society_transporting_data = {
#         "society_transporting": [
#             SocietyBase(**row.__dict__) for row in society_transporting
#         ],
#     }
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return society_transporting_data


# ###################################


# # Add Agreement
# @app.post(
#     "/agreement/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
#     tags=["Agreement"],
# )
# async def add_agreement(
#     addagreement: AgreementBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     existing_agreement = (
#         db.query(models.Agreement)
#         .filter(models.Agreement.agremennt_id == addagreement.agremennt_id)
#         .first()
#     )
#     if existing_agreement:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Agreement with this name already exists",
#         )
#     db_agreement = models.Agreement(**addagreement.dict())
#     db.add(db_agreement)
#     db.commit()
#     db.refresh(db_agreement)

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_agreement


# @app.get(
#     "/agreements/",
#     response_model=List[RiceMillWithAgreement],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
#     tags=["Agreement"],
# )
# async def get_all_agreements_data(
#     token: str = Header(None), db: Session = Depends(get_db)
# ):
#     agreements = (
#         db.query(models.Agreement)
#         .options(joinedload(models.Agreement.addricemill))
#         .all()
#     )

#     result = []
#     for agreement in agreements:
#         result.append(
#             RiceMillWithAgreement(
#                 rice_mill_id=agreement.rice_mill_id,
#                 agreement_number=agreement.agreement_number,
#                 type_of_agreement=agreement.type_of_agreement,
#                 lot_from=agreement.lot_from,
#                 lot_to=agreement.lot_to,
#                 agremennt_id=agreement.agremennt_id,
#                 rice_mill_name=agreement.addricemill.rice_mill_name,
#             )
#         )

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return result


# # route to update aggreements data and send telegram message
# @app.put(
#     "/agreement/{agreement_id}",
#     response_model=AgreementBase,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
#     tags=["Agreement"],
# )
# async def update_agreement_data(
#     agreement_id: int,
#     updated_agreement_data: AgreementBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     existing_agreement = (
#         db.query(models.Agreement)
#         .filter(models.Agreement.agremennt_id == agreement_id)
#         .first()
#     )
#     if not existing_agreement:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Agreement with this id does not exist",
#         )
#     db.query(models.Agreement).filter(
#         models.Agreement.agremennt_id == agreement_id
#     ).update(updated_agreement_data.dict())
#     db.commit()
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return updated_agreement_data


# @app.delete(
#     "/agreement/{agreement_id}",
#     response_model=AgreementBase,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
#     tags=["Agreement"],
# )
# async def delete_agreement_data(
#     agreement_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     existing_agreement = (
#         db.query(models.Agreement)
#         .filter(models.Agreement.agremennt_id == agreement_id)
#         .first()
#     )
#     if not existing_agreement:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Agreement with this id does not exist",
#         )
#     db.query(models.Agreement).filter(
#         models.Agreement.agremennt_id == agreement_id
#     ).delete()
#     db.commit()
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return {"message": "Agreement deleted successfully"}


# # Get all agreements number for dropdown options
# @app.get(
#     "/agreements-number/",
#     response_model=List[int],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
#     tags=["Agreement"],
# )
# async def get_all_agreements_number(
#     token: str = Header(None), db: Session = Depends(get_db)
# ):
#     agreements = (
#         db.query(models.Agreement)
#         .options(joinedload(models.Agreement.agreement_number))
#         .all()
#     )

#     result = []
#     for agreement in agreements:
#         result.append(
#             RiceMillWithAgreement(
#                 rice_mill_id=agreement.rice_mill_id,
#                 agreement_number=agreement.agreement_number,
#                 type_of_agreement=agreement.type_of_agreement,
#                 lot_from=agreement.lot_from,
#                 lot_to=agreement.lot_to,
#                 agremennt_id=agreement.agremennt_id,
#                 rice_mill_name=agreement.addricemill.rice_mill_name,
#             )
#         )

#         payload = get_user_from_token(token)
#         message = f"New action performed by user.\nName: {payload.get('sub')} "
#         send_telegram_message(message)
#         return result


# # @app.post("/create_role/",
# #            tags=["Role "],)
# # def Assign_role(user: RoleBase, token: str = Header(None), db: Session = Depends(get_db)):
# #     hashed_password = hash_password(user.password)
# #     db_user = models.User(name=user.name, email=user.email, password=hashed_password,role=user.role)

# #     # Check if user already exists
# #     user_exists = db.query(models.User).filter(models.User.email == user.email).first()
# #     if  user_exists:
# #         raise HTTPException(status_code=400, detail="Email already registered")

# #     db.add(db_user)
# #     db.commit()
# #     db.refresh(db_user)


# #     # Send Telegram message

# #     payload=get_user_from_token(token)
# #     message = f"New action performed by user.\nName: {payload.get('sub')} "
# #     send_telegram_message(message)
# #     return {"message": "User created successfully", "user": db_user}


# @app.post(
#     "/ware-house-transporting/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
#     tags=["Warehouse"],
# )
# async def add_ware_house(
#     warehouse: WareHouseTransporting,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     existing_warehouse = (
#         db.query(models.ware_house_transporting)
#         .filter(models.ware_house_transporting.ware_house_id == warehouse.ware_house_id)
#         .first()
#     )
#     if existing_warehouse:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Ware House with this transporting rate already exists",
#         )
#     db_add_ware_house = models.ware_house_transporting(**warehouse.dict())
#     db.add(db_add_ware_house)
#     db.commit()
#     db.refresh(db_add_ware_house)

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_add_ware_house


# @app.get(
#     "/get-ware-house-data/",
#     response_model=List[WareHouseTransporting],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
#     tags=["Warehouse"],
# )
# async def get_all_ware_house_data(
#     token: str = Header(None), db: Session = Depends(get_db)
# ):
#     ware_house_db = db.query(models.ware_house_transporting).distinct().all()
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return ware_house_db


# @app.delete(
#     "/delete-ware-house/{ware_house_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
#     tags=["Warehouse"],
# )
# async def delete_ware_house(
#     ware_house_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_ware_house = (
#         db.query(models.ware_house_transporting)
#         .filter_by(ware_house_id=ware_house_id)
#         .first()
#     )
#     if not db_ware_house:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Ware House with this transporting rate not found",
#         )
#     db.delete(db_ware_house)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return {"message": "Deleted successfully"}


# @app.put(
#     "/update-ware-house/{ware_house_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
#     tags=["Warehouse"],
# )
# async def update_ware_house(
#     ware_house_id: int,
#     updated_ware_house: WareHouseTransporting,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_ware_house = (
#         db.query(models.ware_house_transporting)
#         .filter_by(ware_house_id=ware_house_id)
#         .first()
#     )
#     if not db_ware_house:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Ware House with this transporting rate not found",
#         )
#     for key, value in updated_ware_house.dict().items():
#         setattr(db_ware_house, key, value)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return {"message": "Updated successfully"}


# # Kochia
# @app.post(
#     "/kochia/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
#     tags=["Kochia"],
# )
# async def add_kochia(
#     addkochia: KochiaBase, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     existing_kochia = (
#         db.query(models.Kochia)
#         .filter(models.Kochia.kochia_id == addkochia.kochia_id)
#         .first()
#     )
#     if existing_kochia:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Kochia With this id already exists",
#         )

#     db_kochia = models.Kochia(**addkochia.dict())
#     db.add(db_kochia)
#     db.commit()
#     db.refresh(db_kochia)

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_kochia


# @app.get(
#     "/kochia-data/",
#     response_model=List[KochiaWithRiceMill],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
#     tags=["Kochia"],
# )
# async def get_all_kochia_data(token: str = Header(None), db: Session = Depends(get_db)):
#     kochias = (
#         db.query(models.Kochia).options(joinedload(models.Kochia.addricemill)).all()
#     )

#     result = []
#     for kochia in kochias:
#         result.append(
#             KochiaWithRiceMill(
#                 rice_mill_name_id=kochia.rice_mill_name_id,
#                 kochia_name=kochia.kochia_name,
#                 kochia_phone_number=kochia.kochia_phone_number,
#                 kochia_id=kochia.kochia_id,
#                 rice_mill_name=kochia.addricemill.rice_mill_name,
#             )
#         )

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return result


# @app.put(
#     "/kochia/{kochia_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
#     tags=["Kochia"],
# )
# async def update_kochia(
#     kochia_id: int,
#     kochia: KochiaBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     existing_kochia = (
#         db.query(models.Kochia).filter(models.Kochia.kochia_id == kochia_id).first()
#     )
#     if not existing_kochia:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Kochia not found"
#         )

#     existing_kochia.kochia_name = kochia.kochia_name
#     existing_kochia.kochia_phone_number = kochia.kochia_phone_number
#     existing_kochia.rice_mill_name_id = kochia.rice_mill_name_id

#     db.commit()
#     db.refresh(existing_kochia)

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return existing_kochia


# @app.delete(
#     "/kochia/{kochia_id}",
#     status_code=status.HTTP_204_NO_CONTENT,
#     dependencies=[Depends(api_key_header)],
#     tags=["Kochia"],
# )
# async def delete_kochia(
#     kochia_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     existing_kochia = (
#         db.query(models.Kochia).filter(models.Kochia.kochia_id == kochia_id).first()
#     )
#     if not existing_kochia:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Kochia not found"
#         )

#     db.delete(existing_kochia)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)


# # Party
# @app.post(
#     "/party/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
#     tags=["Party"],
# )
# async def add_party(
#     party: PartyBase, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     existing_party = (
#         db.query(models.Party).filter(models.Party.party_id == party.party_id).first()
#     )
#     if existing_party:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Party with this phone number already exists",
#         )
#     db_add_party = models.Party(**party.dict())
#     db.add(db_add_party)
#     db.commit()
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return party


# @app.get(
#     "/party-data/",
#     tags=["Party"],
#     response_model=List[PartyBase],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def get_party_data(token: str = Header(None), db: Session = Depends(get_db)):
#     db_party_data = db.query(models.Party).distinct().all()
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_party_data


# @app.put(
#     "/party/{party_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
#     tags=["Party"],
# )
# async def update_party(
#     party_id: int,
#     party: PartyBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     existing_party = (
#         db.query(models.Party).filter(models.Party.party_id == party_id).first()
#     )
#     if not existing_party:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Party not found"
#         )

#     existing_party.party_name = party.party_name
#     existing_party.party_phone_number = party.party_phone_number
#     existing_party.party_address = party.party_address

#     db.commit()
#     db.refresh(existing_party)

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return existing_party


# @app.delete(
#     "/party/{party_id}",
#     status_code=status.HTTP_204_NO_CONTENT,
#     dependencies=[Depends(api_key_header)],
#     tags=["Party"],
# )
# async def delete_party(
#     party_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     existing_party = (
#         db.query(models.Party).filter(models.Party.party_id == party_id).first()
#     )
#     if not existing_party:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Party not found"
#         )

#     db.delete(existing_party)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)


# # broker
# @app.post(
#     "/broker/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
#     tags=["Broker"],
# )
# async def add_broker(
#     broker: BrokerBase, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     existing_broker = (
#         db.query(models.brokers)
#         .filter(models.brokers.broker_phone_number == broker.broker_phone_number)
#         .first()
#     )
#     if existing_broker:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Broker with this phone number already exists",
#         )
#     db_add_broker = models.brokers(**broker.dict())
#     db.add(db_add_broker)
#     db.commit()
#     db.refresh(db_add_broker)

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_add_broker


# @app.get(
#     "/broker-data/",
#     response_model=List[BrokerBase],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
#     tags=["Broker"],
# )
# async def get_broker_data(token: str = Header(None), db: Session = Depends(get_db)):
#     db_broker_data = db.query(models.brokers).distinct().all()
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_broker_data


# @app.put(
#     "/broker-data/{broker_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
#     tags=["Broker"],
# )
# async def update_broker_data(
#     broker_id: int,
#     broker: BrokerBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     broker_data = (
#         db.query(models.brokers).filter(models.brokers.id == broker_id).first()
#     )
#     if not broker_data:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Broker data not found",
#         )
#     broker_data.broker_name = broker.broker_name
#     broker_data.broker_phone_number = broker.broker_phone_number
#     broker_data.broker_address = broker.broker_address
#     db.commit()
#     db.refresh(broker_data)

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return broker_data


# @app.delete(
#     "/broker-data/{broker_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
#     tags=["Broker"],
# )
# async def delete_broker_data(
#     broker_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     broker_data = (
#         db.query(models.brokers).filter(models.brokers.id == broker_id).first()
#     )
#     if not broker_data:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Broker data not found",
#         )
#     db.delete(broker_data)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)


# # _______________________________________________________
# @app.get(
#     "/rice-agreement-transporter-truck-society-data/",
#     response_model=RiceMillData,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def get_data(token: str = Header(None), db: Session = Depends(get_db)):
#     # Fetch data from different tables
#     rice_mill_data = db.query(models.Add_Rice_Mill).all()
#     agreement_data = db.query(models.Agreement).all()
#     truck_data = db.query(models.Truck).all()
#     society_data = db.query(models.Society).all()

#     response_data = {
#         "rice_mill_data": [AddRiceMillBase(**row.__dict__) for row in rice_mill_data],
#         "agreement_data": [AgreementBase(**row.__dict__) for row in agreement_data],
#         "truck_data": [TruckBase(**row.__dict__) for row in truck_data],
#         "society_data": [SocietyBase(**row.__dict__) for row in society_data],
#     }

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return response_data


# # ADD DO Agreement Number
# @app.get(
#     "/rice-agreement-data/{rice_mill_id}",
#     response_model=AddDoData,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def adddodata(
#     rice_mill_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     rice_mill_data = (
#         db.query(models.Add_Rice_Mill).filter_by(rice_mill_id=rice_mill_id).all()
#     )

#     agreement_data = (
#         db.query(models.Agreement).filter_by(rice_mill_id=rice_mill_id).all()
#     )

#     adddo_data = {
#         "rice_mill_data": [AddRiceMillBase(**row.__dict__) for row in rice_mill_data],
#         "agreement_data": [AgreementBase(**row.__dict__) for row in agreement_data],
#     }

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return adddo_data


# # Add Do
# @app.post(
#     "/add-do/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
# )
# async def add_do(
#     adddo: AddDoBase, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     existing_adddo = (
#         db.query(models.Add_Do)
#         .filter(models.Add_Do.do_number == adddo.do_number)
#         .first()
#     )
#     if existing_adddo:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Do with this Number already exists",
#         )
#     db_add_do = models.Add_Do(**adddo.dict())
#     db.add(db_add_do)
#     db.commit()
#     db.refresh(db_add_do)

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_add_do


# @app.get(
#     "/add-do-data/",
#     response_model=List[AddDoWithAddRiceMillAgreementSocietyTruck],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def get_all_add_do_data(token: str = Header(None), db: Session = Depends(get_db)):
#     Add_Dos = (
#         db.query(models.Add_Do)
#         .options(
#             joinedload(models.Add_Do.addricemill),
#             joinedload(models.Add_Do.agreement),
#             joinedload(models.Add_Do.society),
#             joinedload(models.Add_Do.trucks),
#         )
#         .all()
#     )

#     result = []
#     for Add_Do in Add_Dos:
#         result.append(
#             AddDoWithAddRiceMillAgreementSocietyTruck(
#                 select_mill_id=Add_Do.select_mill_id,
#                 date=Add_Do.date,
#                 do_number=Add_Do.do_number,
#                 select_argeement_id=Add_Do.select_argeement_id,
#                 mota_weight=Add_Do.mota_weight,
#                 mota_Bardana=Add_Do.mota_Bardana,
#                 patla_weight=Add_Do.patla_weight,
#                 patla_bardana=Add_Do.patla_bardana,
#                 sarna_weight=Add_Do.sarna_weight,
#                 sarna_bardana=Add_Do.sarna_bardana,
#                 total_weight=Add_Do.total_weight,
#                 total_bardana=Add_Do.total_bardana,
#                 society_name_id=Add_Do.society_name_id,
#                 truck_number_id=Add_Do.truck_number_id,
#                 created_at=Add_Do.created_at,
#                 rice_mill_name=Add_Do.addricemill.rice_mill_name,
#                 agreement_number=Add_Do.agreement.agreement_number,
#                 society_name=Add_Do.society.society_name,
#                 truck_number=Add_Do.trucks.truck_number,
#                 do_id=Add_Do.do_id,
#             )
#         )

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return result


# @app.put(
#     "/update-do-data/{do_id}",
#     response_model=AddDoWithAddRiceMillAgreementSocietyTruck,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def update_do_data(
#     do_id: int,
#     do: AddDoWithAddRiceMillAgreementSocietyTruck,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_do = db.query(models.Add_Do).filter(models.Add_Do.do_id == do_id).first()
#     if not db_do:
#         raise HTTPException(status_code=404, detail="Do not found")
#     for var, value in vars(do).items():
#         setattr(db_do, var, value) if value else None
#     db.add(db_do)
#     db.commit()
#     db.refresh(db_do)
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_do


# @app.delete(
#     "/delete-do-data/{do_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def delete_do_data(
#     do_id: int,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_do = db.query(models.Add_Do).filter(models.Add_Do.do_id == do_id).first()
#     if not db_do:
#         raise HTTPException(status_code=404, detail="Do not found")
#     db.delete(db_do)
#     db.commit()
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)


# # ________________________________________________________


# @app.get(
#     "/rice-do-number/{rice_mill_id}",
#     response_model=DhanAwakRiceDoNumber,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def rice_do_number_data(
#     rice_mill_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     rice_mill_data = (
#         db.query(models.Add_Rice_Mill).filter_by(rice_mill_id=rice_mill_id).all()
#     )
#     do_number_data = (
#         db.query(models.Add_Do).filter_by(select_mill_id=rice_mill_id).all()
#     )
#     dhan_awak = {
#         "rice_mill_data": [AddRiceMillBase(**row.__dict__) for row in rice_mill_data],
#         "do_number_data": [AddDoBase(**row.__dict__) for row in do_number_data],
#     }
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return dhan_awak


# @app.get(
#     "/rice-do-society-truck-transporter/",
#     response_model=DhanAwakRiceDoSocietyTruckTransporter,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def Dhan_awak_data(token: str = Header(None), db: Session = Depends(get_db)):
#     rice_mill_data = db.query(models.Add_Rice_Mill).all()
#     do_number_data = db.query(models.Add_Do).all()
#     society_data = db.query(models.Society).all()
#     truck_data = db.query(models.Truck).all()
#     transporter_data = db.query(models.Transporter).all()

#     dhan_awak_data = {
#         "rice_mill_data": [AddRiceMillBase(**row.__dict__) for row in rice_mill_data],
#         "do_number_data": [AddDoBase(**row.__dict__) for row in do_number_data],
#         "truck_data": [TruckBase(**row.__dict__) for row in truck_data],
#         "society_data": [SocietyBase(**row.__dict__) for row in society_data],
#         "transporter_data": [
#             TransporterBase(**row.__dict__) for row in transporter_data
#         ],
#     }
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return dhan_awak_data


# # Dhan Awak
# @app.get(
#     "/truck-transporter/{transport_id}",  # Here will go my truck ID
#     response_model=DhanAwakTruckTransporter,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def truck_transporter_data(
#     transport_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     truck_data = db.query(models.Truck).filter_by(transport_id=transport_id).all()
#     transporter_data = (
#         db.query(models.Transporter).filter_by(transporter_id=transport_id).all()
#     )
#     dhan_awak_truck_transporter = {
#         "truck_data": [TruckBase(**row.__dict__) for row in truck_data],
#         "transporter_data": [
#             TransporterBase(**row.__dict__) for row in transporter_data
#         ],
#     }
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return dhan_awak_truck_transporter


# # Dhan Awak
# @app.post(
#     "/dhan-awak/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
# )
# async def add_dhan_awak(
#     dhanawak: DhanAwakBase, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_dhan_awak = models.Dhan_Awak(**dhanawak.dict())
#     db.add(db_dhan_awak)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_dhan_awak


# @app.get(
#     "/dhan-awak-data/",
#     response_model=List[DhanAwakWithRiceDoSocietyTruckTransport],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def get_all_dhan_awak_data(
#     token: str = Header(None), db: Session = Depends(get_db)
# ):
#     dhan_awaks_data = (
#         db.query(models.Dhan_Awak)
#         .options(
#             joinedload(models.Dhan_Awak.addricemill),
#             joinedload(models.Dhan_Awak.add_do),
#             joinedload(models.Dhan_Awak.society),
#             joinedload(models.Dhan_Awak.trucks),
#             joinedload(models.Dhan_Awak.transporter),
#         )
#         .all()
#     )

#     result = []
#     for dhan_awaks in dhan_awaks_data:
#         result.append(
#             DhanAwakWithRiceDoSocietyTruckTransport(
#                 rst_number=dhan_awaks.rst_number,
#                 rice_mill_id=dhan_awaks.rice_mill_id,
#                 date=dhan_awaks.date,
#                 do_id=dhan_awaks.do_id,
#                 society_id=dhan_awaks.society_id,
#                 dm_weight=dhan_awaks.dm_weight,
#                 number_of_bags=dhan_awaks.number_of_bags,
#                 truck_number_id=dhan_awaks.truck_number_id,
#                 transporter_name_id=dhan_awaks.transporter_name_id,
#                 transporting_rate=dhan_awaks.transporting_rate,
#                 transporting_total=dhan_awaks.transporting_total,
#                 jama_jute_22_23=dhan_awaks.jama_jute_22_23,
#                 ek_bharti_21_22=dhan_awaks.ek_bharti_21_22,
#                 pds=dhan_awaks.pds,
#                 miller_purana=dhan_awaks.miller_purana,
#                 kisan=dhan_awaks.kisan,
#                 bardana_society=dhan_awaks.bardana_society,
#                 hdpe_22_23=dhan_awaks.hdpe_22_23,
#                 hdpe_21_22=dhan_awaks.hdpe_21_22,
#                 hdpe_21_22_one_use=dhan_awaks.hdpe_21_22_one_use,
#                 total_bag_weight=dhan_awaks.total_bag_weight,
#                 type_of_paddy=dhan_awaks.type_of_paddy,
#                 actual_paddy=dhan_awaks.actual_paddy,
#                 mill_weight_quintals=dhan_awaks.mill_weight_quintals,
#                 shortage=dhan_awaks.shortage,
#                 bags_put_in_hopper=dhan_awaks.bags_put_in_hopper,
#                 bags_put_in_stack=dhan_awaks.bags_put_in_stack,
#                 hopper_rice_mill_id=dhan_awaks.hopper_rice_mill_id,
#                 stack_location=dhan_awaks.stack_location,
#                 dhan_awak_id=dhan_awaks.dhan_awak_id,
#                 rice_mill_name=dhan_awaks.addricemill.rice_mill_name,
#                 do_number=dhan_awaks.add_do.do_number,
#                 society_name=dhan_awaks.society.society_name,
#                 truck_number=dhan_awaks.trucks.truck_number,
#                 transporter_name=dhan_awaks.transporter.transporter_name,
#             )
#         )

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return result


# # ________________________________________________________
# @app.put(
#     "/dhan-awak-data/{dhan_awak_id}",
#     response_model=DhanAwakWithRiceDoSocietyTruckTransport,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def update_dhan_awak(
#     dhan_awak_id: int,
#     dhan_awak: DhanAwakWithRiceDoSocietyTruckTransport,
#     db: Session = Depends(get_db),
#     token: str = Header(None),
# ):
#     db_dhan_awak = (
#         db.query(models.Dhan_Awak)
#         .filter(models.Dhan_Awak.dhan_awak_id == dhan_awak_id)
#         .first()
#     )
#     if db_dhan_awak is None:
#         raise HTTPException(status_code=404, detail="Dhan awak not found")
#     for var, value in vars(dhan_awak).items():
#         setattr(db_dhan_awak, var, value) if value else None
#     db.add(db_dhan_awak)
#     db.commit()
#     db.refresh(db_dhan_awak)
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_dhan_awak


# @app.delete(
#     "/dhan-awak-data/{dhan_awak_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def delete_dhan_awak(
#     dhan_awak_id: int,
#     db: Session = Depends(get_db),
#     token: str = Header(None),
# ):
#     db_dhan_awak = (
#         db.query(models.Dhan_Awak)
#         .filter(models.Dhan_Awak.dhan_awak_id == dhan_awak_id)
#         .first()
#     )
#     if db_dhan_awak is None:
#         raise HTTPException(status_code=404, detail="Dhan awak not found")
#     db.delete(db_dhan_awak)
#     db.commit()
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)


# # ________________________________________________________
# @app.get(
#     "/rice-truck-party-brokers/",
#     response_model=RiceMillTruckNumberPartyBrokers,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def broken_data(token: str = Header(None), db: Session = Depends(get_db)):
#     rice_mill_data = db.query(models.Add_Rice_Mill).all()
#     truck_data = db.query(models.Truck).all()
#     party_data = db.query(models.Party).all()
#     brokers_data = db.query(models.brokers).all()

#     broken_data = {
#         "rice_mill_data": [AddRiceMillBase(**row.__dict__) for row in rice_mill_data],
#         "truck_data": [TruckBase(**row.__dict__) for row in truck_data],
#         "party_data": [PartyBase(**row.__dict__) for row in party_data],
#         "brokers_data": [BrokerBase(**row.__dict__) for row in brokers_data],
#     }
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return broken_data


# # Other Awak
# @app.post(
#     "/other-awak/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
# )
# async def add_other_awak(
#     otherawak: OtherAwakBase, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_add_other_awak = models.Other_awak(**otherawak.dict())
#     db.add(db_add_other_awak)
#     db.commit()


# @app.get(
#     "/other-awak-data/",
#     response_model=List[OtherAwakWithPartyRiceTruck],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def get_all_other_awak_data(
#     token: str = Header(None), db: Session = Depends(get_db)
# ):
#     other_awaks = (
#         db.query(models.Other_awak)
#         .options(
#             joinedload(models.Other_awak.addricemill),
#             joinedload(models.Other_awak.trucks),
#             joinedload(models.Other_awak.party),
#         )
#         .all()
#     )

#     result = []
#     for other_awak in other_awaks:
#         result.append(
#             OtherAwakWithPartyRiceTruck(
#                 rst_number=other_awak.rst_number,
#                 date=other_awak.date,
#                 rice_mill_name_id=other_awak.rice_mill_name_id,
#                 party_id=other_awak.party_id,
#                 truck_number_id=other_awak.truck_number_id,
#                 material=other_awak.material,
#                 nos=other_awak.nos,
#                 reason=other_awak.reason,
#                 weight=other_awak.weight,
#                 party_name=other_awak.party.party_name,
#                 rice_mill_name=other_awak.addricemill.rice_mill_name,
#                 truck_number=other_awak.trucks.truck_number,
#                 other_awak_id=other_awak.other_awak_id,
#             )
#         )

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return result


# @app.put(
#     "/other-awak-data/{other_awak_id}",
#     response_model=OtherAwakWithPartyRiceTruck,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def update_other_awak_data(
#     other_awak_id: int,
#     other_awak: OtherAwakWithPartyRiceTruck,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_other_awak = (
#         db.query(models.Other_awak)
#         .filter(models.Other_awak.other_awak_id == other_awak_id)
#         .first()
#     )
#     if not db_other_awak:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Other Awak not found",
#         )

#     db_other_awak.rst_number = other_awak.rst_number
#     db_other_awak.date = other_awak.date
#     db_other_awak.rice_mill_name_id = other_awak.rice_mill_name_id
#     db_other_awak.party_id = other_awak.party_id
#     db_other_awak.truck_number_id = other_awak.truck_number_id
#     db_other_awak.material = other_awak.material
#     db_other_awak.nos = other_awak.nos
#     db_other_awak.reason = other_awak.reason
#     db_other_awak.weight = other_awak.weight

#     db.commit()
#     db.refresh(db_other_awak)

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)

#     return db_other_awak


# @app.delete(
#     "/other-awak-data/{other_awak_id}",
#     response_model=OtherAwakWithPartyRiceTruck,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def delete_other_awak_data(
#     other_awak_id: int,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_other_awak = (
#         db.query(models.Other_awak)
#         .filter(models.Other_awak.other_awak_id == other_awak_id)
#         .first()
#     )
#     if not db_other_awak:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Other Awak not found",
#         )

#     db.delete(db_other_awak)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)

#     return db_other_awak


# # ________________________________________________________
# @app.get(
#     "/ware-house-data/{warehouse_id}",  # Corrected the path parameter name
#     response_model=WareHouseTransporting,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def warehouse_data(
#     warehouse_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     warehouse_data = (
#         db.query(models.ware_house_transporting)
#         .filter_by(ware_house_id=warehouse_id)  # Ensure this matches the model
#         .first()
#     )

#     if warehouse_data is None:
#         raise HTTPException(status_code=404, detail="Ware House not found")

#     response_data = {
#         "ware_house_transporting_rate": warehouse_data.ware_house_transporting_rate,
#         "hamalirate": warehouse_data.hamalirate,
#     }
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return response_data


# # Rice Deposti
# @app.get(
#     "/rice-truck-transporter-ware-house/",
#     response_model=RiceDepositRiceTruckTransport,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def rice_deposit_data(token: str = Header(None), db: Session = Depends(get_db)):
#     rice_mill_data = db.query(models.Add_Rice_Mill).all()
#     truck_data = db.query(models.Truck).all()
#     transporter_data = db.query(models.Transporter).all()
#     ware_house_data = db.query(models.ware_house_transporting).all()

#     rice_deposit_data = {
#         "rice_mill_data": [AddRiceMillBase(**row.__dict__) for row in rice_mill_data],
#         "truck_data": [TruckBase(**row.__dict__) for row in truck_data],
#         "transporter_data": [
#             TransporterBase(**row.__dict__) for row in transporter_data
#         ],
#         "ware_house_data": [
#             WareHouseTransporting(**row.__dict__) for row in ware_house_data
#         ],
#     }
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return rice_deposit_data


# # Rice Deposite
# @app.post(
#     "/rice-deposite/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
#     tags=["Rice Deposit"],
# )
# async def rice_deposite(
#     ricedeposite: RiceDepositeBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_rice_depostie = models.Rice_deposite(**ricedeposite.dict())
#     db.add(db_rice_depostie)
#     db.commit()


# @app.get(
#     "/rice-deposite-data/",
#     response_model=List[RiceDepositWithRiceWareTruckTransporter],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def get_all_rice_deposite_data(
#     token: str = Header(None), db: Session = Depends(get_db)
# ):
#     rices_deposite = (
#         db.query(models.Rice_deposite)
#         .options(
#             joinedload(models.Rice_deposite.addricemill),
#             joinedload(models.Rice_deposite.warehousetransporting),
#             joinedload(models.Rice_deposite.trucks),
#             joinedload(models.Rice_deposite.transporter),
#         )
#         .all()
#     )

#     result = []
#     for rice_deposite in rices_deposite:
#         result.append(
#             RiceDepositWithRiceWareTruckTransporter(
#                 rst_number=rice_deposite.rst_number,
#                 date=rice_deposite.date,
#                 lot_number=rice_deposite.lot_number,
#                 ware_house_id=rice_deposite.ware_house_id,
#                 rice_mill_name_id=rice_deposite.rice_mill_name_id,
#                 weight=rice_deposite.weight,
#                 truck_number_id=rice_deposite.truck_number_id,
#                 bags=rice_deposite.bags,
#                 transporting_total=rice_deposite.transporting_total,
#                 transporter_name_id=rice_deposite.transporter_name_id,
#                 transporting_type=rice_deposite.transporting_type,
#                 transporting_status=rice_deposite.transporting_status,
#                 rate=rice_deposite.rate,
#                 variety=rice_deposite.variety,
#                 halting=rice_deposite.halting,
#                 rrga_wt=rice_deposite.rrga_wt,
#                 data_2022_23=rice_deposite.data_2022_23,
#                 data_2021_22=rice_deposite.data_2021_22,
#                 pds=rice_deposite.pds,
#                 old=rice_deposite.old,
#                 amount=rice_deposite.amount,
#                 status=rice_deposite.status,
#                 hamali=rice_deposite.hamali,
#                 rice_mill_name=rice_deposite.addricemill.rice_mill_name,
#                 truck_number=rice_deposite.trucks.truck_number,
#                 ware_house_name=(
#                     rice_deposite.warehousetransporting.ware_house_name
#                     if rice_deposite.warehousetransporting
#                     else "Unknown Warehouse"
#                 ),
#                 transporter_name=rice_deposite.transporter.transporter_name,
#                 rice_depostie_id=rice_deposite.rice_depostie_id,
#             )
#         )

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return result


# # ________________________________________________________
# # Dalali dhaan
# @app.post(
#     "/dalali-dhaan/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
# )
# async def dalali_dhaan(
#     dalalidhaan: DalaliDhaanBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_dalali_dhaan = models.Dalali_dhaan(**dalalidhaan.dict())
#     db.add(db_dalali_dhaan)
#     db.commit()


# @app.get(
#     "/dalali-dhaan-data/",
#     response_model=List[DalaliDhaanWithKochia],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def get_all_dalali_dhaan_data(
#     token: str = Header(None), db: Session = Depends(get_db)
# ):
#     Dalali_dhaans = (
#         db.query(models.Dalali_dhaan)
#         .options(
#             joinedload(models.Dalali_dhaan.kochia),
#             joinedload(models.Dalali_dhaan.trucks),
#         )
#         .all()
#     )

#     result = []
#     for Dalali_dhaan in Dalali_dhaans:
#         result.append(
#             DalaliDhaanWithKochia(
#                 rst_number=Dalali_dhaan.rst_number,
#                 date=Dalali_dhaan.date,
#                 kochia_id=Dalali_dhaan.kochia_id,
#                 vehicale_number_id=Dalali_dhaan.vehicale_number_id,
#                 white_sarna_bags=Dalali_dhaan.white_sarna_bags,
#                 white_sarna_weight=Dalali_dhaan.white_sarna_weight,
#                 ir_bags=Dalali_dhaan.ir_bags,
#                 ir_weight=Dalali_dhaan.ir_weight,
#                 rb_gold_bags=Dalali_dhaan.rb_gold_bags,
#                 rb_gold_weight=Dalali_dhaan.rb_gold_weight,
#                 sarna_bags=Dalali_dhaan.sarna_bags,
#                 sarna_weight=Dalali_dhaan.sarna_weight,
#                 sambha_new_bags=Dalali_dhaan.sambha_new_bags,
#                 sambha_new_weight=Dalali_dhaan.sambha_new_weight,
#                 paddy_type=Dalali_dhaan.paddy_type,
#                 total_bags=Dalali_dhaan.total_bags,
#                 total_weight=Dalali_dhaan.total_weight,
#                 hamali=Dalali_dhaan.hamali,
#                 plastic_bag=Dalali_dhaan.plastic_bag,
#                 jute_bag=Dalali_dhaan.jute_bag,
#                 weight_less_kata_difference=Dalali_dhaan.weight_less_kata_difference,
#                 net_weight=Dalali_dhaan.net_weight,
#                 rate=Dalali_dhaan.rate,
#                 amount=Dalali_dhaan.amount,
#                 kochia_name=Dalali_dhaan.kochia.kochia_name,
#                 truck_number=Dalali_dhaan.trucks.truck_number,
#                 dalali_dhaan_id=Dalali_dhaan.dalali_dhaan_id,
#             )
#         )

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return result


# # ________________________________________________________
# # ________________________________________________________
# # Update Rice Deposited Data
# @app.put(
#     "/dalali-dhaan/{dalali_dhaan_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def update_dalali_dhaan(
#     dalali_dhaan_id: int,
#     dalali_dhaan: DalaliDhaanBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_dalali_dhaan = (
#         db.query(models.Dalali_dhaan)
#         .filter(models.Dalali_dhaan.dalali_dhaan_id == dalali_dhaan_id)
#         .first()
#     )
#     if db_dalali_dhaan is None:
#         raise HTTPException(status_code=404, detail="Dalali Dhaan not found")
#     for var, value in vars(dalali_dhaan).items():
#         setattr(db_dalali_dhaan, var, value) if value else None
#     db.add(db_dalali_dhaan)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return dalali_dhaan


# @app.delete(
#     "/dalali-dhaan/{dalali_dhaan_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def delete_dalali_dhaan(
#     dalali_dhaan_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_dalali_dhaan = (
#         db.query(models.Dalali_dhaan)
#         .filter(models.Dalali_dhaan.dalali_dhaan_id == dalali_dhaan_id)
#         .first()
#     )
#     if db_dalali_dhaan is None:
#         raise HTTPException(status_code=404, detail="Dalali Dhaan not found")
#     db.delete(db_dalali_dhaan)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)


# # FRk
# @app.post(
#     "/frk/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
# )
# async def frk(frk: FrkBase, token: str = Header(None), db: Session = Depends(get_db)):
#     db_frk = models.Frk(**frk.dict())
#     db.add(db_frk)
#     db.commit()


# @app.get(
#     "/frk-data/",
#     response_model=List[FrkWithRiceTruck],
#     status_code=status.HTTP_200_OK,
# )
# async def get_all_add_do_data(token: str = Header(None), db: Session = Depends(get_db)):
#     frks = (
#         db.query(models.Frk)
#         .options(
#             joinedload(models.Frk.addricemill),
#             joinedload(models.Frk.trucks),
#         )
#         .all()
#     )

#     result = []
#     for frk in frks:
#         result.append(
#             FrkWithRiceTruck(
#                 date=frk.date,
#                 party=frk.party,
#                 bags=frk.bags,
#                 weight=frk.weight,
#                 truck_number_id=frk.truck_number_id,
#                 rice_mill_name_id=frk.rice_mill_name_id,
#                 bill_number=frk.bill_number,
#                 rate=frk.rate,
#                 batch_number=frk.batch_number,
#                 rice_mill_name=frk.addricemill.rice_mill_name,
#                 truck_number=frk.trucks.truck_number,
#                 frk_id=frk.frk_id,
#             )
#         )

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return result


# @app.put(
#     "/frk/{frk_id}",
#     status_code=status.HTTP_200_OK,
# )
# async def update_frk(
#     frk_id: int, frk: FrkBase, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_frk = db.query(models.Frk).filter(models.Frk.frk_id == frk_id).first()
#     if db_frk is None:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Frk data not found",
#         )
#     db_frk.date = frk.date
#     db_frk.party = frk.party
#     db_frk.bags = frk.bags
#     db_frk.weight = frk.weight
#     db_frk.truck_number_id = frk.truck_number_id
#     db_frk.rice_mill_name_id = frk.rice_mill_name_id
#     db_frk.bill_number = frk.bill_number
#     db_frk.rate = frk.rate
#     db_frk.batch_number = frk.batch_number
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_frk


# @app.delete(
#     "/frk/{frk_id}",
#     status_code=status.HTTP_200_OK,
# )
# async def delete_frk(
#     frk_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_frk = db.query(models.Frk).filter(models.Frk.frk_id == frk_id).first()
#     if db_frk is None:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Frk data not found",
#         )
#     db.delete(db_frk)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)


# # ________________________________________________________


# # Sauda patrak
# @app.post(
#     "/sauda-patrak/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
# )
# async def sauda_patrak(
#     saudapatrak: SaudaPatrakBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_sauda_patrak = models.Sauda_patrak(**saudapatrak.dict())
#     db.add(db_sauda_patrak)
#     db.commit()


# @app.get(
#     "/sauda-patrak-data/",
#     response_model=List[SaudaPatrakWithTruckNumber],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def get_all_sauda_patrak_data(
#     token: str = Header(None), db: Session = Depends(get_db)
# ):
#     saudas_patrak = (
#         db.query(models.Sauda_patrak)
#         .options(
#             joinedload(models.Sauda_patrak.trucks),
#         )
#         .all()
#     )

#     result = []
#     for sauda_patrak in saudas_patrak:
#         result.append(
#             SaudaPatrakWithTruckNumber(
#                 name=sauda_patrak.name,
#                 address=sauda_patrak.address,
#                 vechicle_number_id=sauda_patrak.vechicle_number_id,
#                 paddy=sauda_patrak.paddy,
#                 bags=sauda_patrak.bags,
#                 weight=sauda_patrak.weight,
#                 rate=sauda_patrak.rate,
#                 amount=sauda_patrak.amount,
#                 truck_number=sauda_patrak.trucks.truck_number,
#                 sauda_patrak_id=sauda_patrak.sauda_patrak_id,
#             )
#         )

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return result


# @app.put(
#     "/sauda-patrak-data/{sauda_patrak_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def update_sauda_patrak(
#     sauda_patrak_id: int,
#     saudapatrak: SaudaPatrakBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_sauda_patrak = db.query(models.Sauda_patrak).filter(
#         models.Sauda_patrak.sauda_patrak_id == sauda_patrak_id
#     )
#     if not db_sauda_patrak.first():
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Sauda patrak not found",
#         )
#     db_sauda_patrak.update(
#         saudapatrak.dict(exclude_unset=True), synchronize_session=False
#     )
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)


# @app.delete(
#     "/sauda-patrak-data/{sauda_patrak_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def delete_sauda_patrak(
#     sauda_patrak_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_sauda_patrak = (
#         db.query(models.Sauda_patrak)
#         .filter(models.Sauda_patrak.sauda_patrak_id == sauda_patrak_id)
#         .first()
#     )
#     if not db_sauda_patrak:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Sauda patrak not found",
#         )
#     db.delete(db_sauda_patrak)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)


# # ________________________________________________________
# # Do Panding
# @app.post(
#     "/do-panding/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
# )
# async def do_panding(
#     dopanding: DoPendingBase, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_do_panding = models.Do_panding(**dopanding.dict())
#     db.add(db_do_panding)
#     db.commit()


# @app.get(
#     "/do-panding-data/",
#     response_model=List[DoPendingWithRiceAddDo],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def get_all_sauda_patrak_data(
#     token: str = Header(None), db: Session = Depends(get_db)
# ):
#     dos_pending = (
#         db.query(models.Do_panding)
#         .options(
#             joinedload(models.Do_panding.addricemill),
#             joinedload(models.Do_panding.add_do),
#         )
#         .all()
#     )

#     result = []
#     for do_pending in dos_pending:
#         result.append(
#             DoPendingWithRiceAddDo(
#                 rice_mill_id=do_pending.rice_mill_id,
#                 do_number_id=do_pending.do_number_id,
#                 date=do_pending.date,
#                 mota=do_pending.mota,
#                 patla=do_pending.patla,
#                 sarna=do_pending.sarna,
#                 Total=do_pending.Total,
#                 rice_mill_name=do_pending.addricemill.rice_mill_name,
#                 do_number=do_pending.add_do.do_number,
#                 do_panding_id=do_pending.do_panding_id,
#             )
#         )

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return result


# @app.put(
#     "/do-panding-data/{do_panding_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def update_do_panding(
#     do_panding_id: int,
#     dopanding: DoPendingBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_do_panding = db.query(models.Do_panding).filter(
#         models.Do_panding.do_panding_id == do_panding_id
#     )
#     if not db_do_panding.first():
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Do panding not found",
#         )
#     db_do_panding.update(dopanding.dict(exclude_unset=True), synchronize_session=False)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)


# @app.delete(
#     "/do-panding-data/{do_panding_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def delete_do_panding(
#     do_panding_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_do_panding = (
#         db.query(models.Do_panding)
#         .filter(models.Do_panding.do_panding_id == do_panding_id)
#         .first()
#     )
#     if not db_do_panding:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Do panding not found",
#         )
#     db.delete(db_do_panding)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)


# # ________________________________________________________
# # Dhan Transporting
# @app.get(
#     "/rice-rst-society-do-truck-transporter/",
#     response_model=RiceRstSocietyDoTruckTransporter,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def dhan_transporting_data(
#     token: str = Header(None), db: Session = Depends(get_db)
# ):
#     rice_mill_data = db.query(models.Add_Rice_Mill).all()
#     rst_data = db.query(models.Dhan_Awak).all()
#     do_number_data = db.query(models.Add_Do).all()
#     society_data = db.query(models.Society).all()
#     truck_data = db.query(models.Truck).all()
#     transporter_data = db.query(models.Transporter).all()

#     dhan_transporting_data = {
#         "rice_mill_data": [AddRiceMillBase(**row.__dict__) for row in rice_mill_data],
#         "rst_data": [DhanAwakBase(**row.__dict__) for row in rst_data],
#         "do_number_data": [AddDoBase(**row.__dict__) for row in do_number_data],
#         "truck_data": [TruckBase(**row.__dict__) for row in truck_data],
#         "society_data": [SocietyBase(**row.__dict__) for row in society_data],
#         "transporter_data": [
#             TransporterBase(**row.__dict__) for row in transporter_data
#         ],
#     }
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return dhan_transporting_data


# @app.get(
#     "/rice-rst-number-do-number/{rice_mill_id}",
#     response_model=RiceMillRstNumber,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def rice_mill_rst_number(
#     rice_mill_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     rice_mill_data = (
#         db.query(models.Add_Rice_Mill).filter_by(rice_mill_id=rice_mill_id).all()
#     )
#     rst_data = db.query(models.Dhan_Awak).filter_by(rice_mill_id=rice_mill_id).all()
#     do_number_data = (
#         db.query(models.Add_Do).filter_by(select_mill_id=rice_mill_id).all()
#     )
#     rice_mill_rst_number = {
#         "rice_mill_data": [AddRiceMillBase(**row.__dict__) for row in rice_mill_data],
#         "do_number_data": [AddDoBase(**row.__dict__) for row in do_number_data],
#         "rst_data": [DhanAwakBase(**row.__dict__) for row in rst_data],
#     }
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return rice_mill_rst_number


# # Dhan Transporting
# @app.post(
#     "/dhan-transporting/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
# )
# async def dhan_transporting(
#     dhantransporting: DhanTransportingBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_dhan_transporting = models.Dhan_transporting(**dhantransporting.dict())
#     db.add(db_dhan_transporting)
#     db.commit()


# @app.get(
#     "/dhan-transporting-data/",
#     response_model=List[DhanTransportingWithRiceDoTruckTransport],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def get_all_sauda_patrak_data(
#     token: str = Header(None), db: Session = Depends(get_db)
# ):
#     dhans_transporting = (
#         db.query(models.Dhan_transporting)
#         .options(
#             joinedload(models.Dhan_transporting.addricemill),
#             joinedload(models.Dhan_transporting.society),
#             joinedload(models.Dhan_transporting.add_do),
#             joinedload(models.Dhan_transporting.trucks),
#             joinedload(models.Dhan_transporting.transporter),
#             joinedload(models.Dhan_transporting.dhanawak),
#         )
#         .all()
#     )

#     result = []
#     for dhan_transporting in dhans_transporting:
#         result.append(
#             DhanTransportingWithRiceDoTruckTransport(
#                 # rst_number_id=dhan_transporting.rst_number_id,
#                 date=dhan_transporting.date,
#                 do_number_id=dhan_transporting.do_number_id,
#                 society_name_id=dhan_transporting.society_name_id,
#                 rice_mill_name_id=dhan_transporting.rice_mill_name_id,
#                 dm_weight=dhan_transporting.dm_weight,
#                 truck_number_id=dhan_transporting.truck_number_id,
#                 transporting_rate=dhan_transporting.transporting_rate,
#                 numbers_of_bags=dhan_transporting.numbers_of_bags,
#                 transporting_total=dhan_transporting.transporting_total,
#                 transporter_name_id=dhan_transporting.transporter_name_id,
#                 status=dhan_transporting.status,
#                 total_pending=dhan_transporting.total_pending,
#                 total_paid=dhan_transporting.total_paid,
#                 # rst_number=dhan_transporting.dhanawak.rst_number,
#                 rst_number=dhan_transporting.rst_number,
#                 rice_mill_name=dhan_transporting.addricemill.rice_mill_name,
#                 society_name=dhan_transporting.society.society_name,
#                 do_number=dhan_transporting.add_do.do_number,
#                 truck_number=dhan_transporting.trucks.truck_number,
#                 transporter_name=dhan_transporting.transporter.transporter_name,
#                 Dhan_transporting_id=dhan_transporting.Dhan_transporting_id,
#             )
#         )

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return result


# @app.put(
#     "/dhan-transporting/{dhan_transporting_id}",
#     status_code=status.HTTP_202_ACCEPTED,
#     dependencies=[Depends(api_key_header)],
# )
# async def update_dhan_transporting(
#     dhan_transporting_id: int,
#     dhantransporting: DhanTransportingBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_dhan_transporting = (
#         db.query(models.Dhan_transporting)
#         .filter(models.Dhan_transporting.Dhan_transporting_id == dhan_transporting_id)
#         .first()
#     )
#     if db_dhan_transporting is None:
#         raise HTTPException(status_code=404, detail="Dhan transporting not found")

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)

#     db_dhan_transporting.date = dhantransporting.date
#     db_dhan_transporting.do_number_id = dhantransporting.do_number_id
#     db_dhan_transporting.society_name_id = dhantransporting.society_name_id
#     db_dhan_transporting.rice_mill_name_id = dhantransporting.rice_mill_name_id
#     db_dhan_transporting.dm_weight = dhantransporting.dm_weight
#     db_dhan_transporting.truck_number_id = dhantransporting.truck_number_id
#     db_dhan_transporting.transporting_rate = dhantransporting.transporting_rate
#     db_dhan_transporting.numbers_of_bags = dhantransporting.numbers_of_bags
#     db_dhan_transporting.transporting_total = dhantransporting.transporting_total
#     db_dhan_transporting.transporter_name_id = dhantransporting.transporter_name_id
#     db_dhan_transporting.status = dhantransporting.status
#     db_dhan_transporting.total_pending = dhantransporting.total_pending
#     db_dhan_transporting.total_paid = dhantransporting.total_paid

#     db.commit()
#     db.refresh(db_dhan_transporting)
#     return db_dhan_transporting


# @app.delete(
#     "/dhan-transporting/{dhan_transporting_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def delete_dhan_transporting(
#     dhan_transporting_id: int,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_dhan_transporting = (
#         db.query(models.Dhan_transporting)
#         .filter(models.Dhan_transporting.Dhan_transporting_id == dhan_transporting_id)
#         .first()
#     )
#     if db_dhan_transporting is None:
#         raise HTTPException(status_code=404, detail="Dhan transporting not found")

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)

#     db.delete(db_dhan_transporting)
#     db.commit()


# # ________________________________________________________
# # Other Jawak
# @app.post(
#     "/other-jawak/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
# )
# async def add_other_jawak(
#     otherjawak: OtherJawakBase, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_add_other_jawak = models.Other_jawak(**otherjawak.dict())
#     db.add(db_add_other_jawak)
#     db.commit()


# @app.get(
#     "/other-jawak-data/",
#     response_model=List[OtherJawakWithPatyTrucksRice],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def get_all_other_jawak_data(
#     token: str = Header(None), db: Session = Depends(get_db)
# ):
#     other_jawaks = (
#         db.query(models.Other_jawak)
#         .options(
#             joinedload(models.Other_jawak.addricemill),
#             joinedload(models.Other_jawak.trucks),
#             joinedload(models.Other_jawak.party),
#         )
#         .all()
#     )

#     result = []
#     for other_jawak in other_jawaks:
#         result.append(
#             OtherJawakWithPatyTrucksRice(
#                 rst_number=other_jawak.rst_number,
#                 date=other_jawak.date,
#                 rice_mill_name_id=other_jawak.rice_mill_name_id,
#                 party_id=other_jawak.party_id,
#                 truck_number_id=other_jawak.truck_number_id,
#                 material=other_jawak.material,
#                 nos=other_jawak.nos,
#                 reason=other_jawak.reason,
#                 weight=other_jawak.weight,
#                 party_name=other_jawak.party.party_name,
#                 rice_mill_name=other_jawak.addricemill.rice_mill_name,
#                 truck_number=other_jawak.trucks.truck_number,
#                 other_jawak_id=other_jawak.other_jawak_id,
#             )
#         )

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return result


# @app.put(
#     "/other-jawak-data/{other_jawak_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def update_other_jawak_data(
#     other_jawak_id: int,
#     other_jawak: OtherJawakBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_get_other_jawak_data = (
#         db.query(models.Other_jawak)
#         .filter(models.Other_jawak.other_jawak_id == other_jawak_id)
#         .first()
#     )
#     if not db_get_other_jawak_data:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Other jawak data not found"
#         )
#     for var, value in vars(other_jawak).items():
#         setattr(db_get_other_jawak_data, var, value) if value else None

#     db.add(db_get_other_jawak_data)
#     db.commit()
#     db.refresh(db_get_other_jawak_data)

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_get_other_jawak_data


# @app.delete(
#     "/other-jawak-data/{other_jawak_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def delete_other_jawak_data(
#     other_jawak_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_get_other_jawak_data = (
#         db.query(models.Other_jawak)
#         .filter(models.Other_jawak.other_jawak_id == other_jawak_id)
#         .first()
#     )
#     if not db_get_other_jawak_data:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Other jawak data not found"
#         )
#     db.delete(db_get_other_jawak_data)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)


# # ________________________________________________________
# # Broken Jawak
# @app.post(
#     "/broken-jawak/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
# )
# async def add_broken_jawak(
#     brokenjawak: BrokenJawak, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_add_broken_jawak = models.broken_jawak(**brokenjawak.dict())
#     db.add(db_add_broken_jawak)
#     db.commit()


# @app.get(
#     "/other-broken-jawak-data/",
#     response_model=List[BrokernJawakWithRicePartyBrokerTruck],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def get_all_other_jawak_data(
#     token: str = Header(None), db: Session = Depends(get_db)
# ):
#     brokens_jawak = (
#         db.query(models.broken_jawak)
#         .options(
#             joinedload(models.broken_jawak.addricemill),
#             joinedload(models.broken_jawak.trucks),
#             joinedload(models.broken_jawak.party),
#             joinedload(models.broken_jawak.brokers),
#         )
#         .all()
#     )

#     result = []
#     for broken_jawak in brokens_jawak:
#         result.append(
#             BrokernJawakWithRicePartyBrokerTruck(
#                 rst_number=broken_jawak.rst_number,
#                 date=broken_jawak.date,
#                 party_id=broken_jawak.party_id,
#                 rice_mill_name_id=broken_jawak.rice_mill_name_id,
#                 broker=broken_jawak.broker,
#                 brokerage_percentage=broken_jawak.brokerage_percentage,
#                 weight=broken_jawak.weight,
#                 rate=broken_jawak.rate,
#                 number_of_bags=broken_jawak.number_of_bags,
#                 truck_number_id=broken_jawak.truck_number_id,
#                 total=broken_jawak.total,
#                 brokerage=broken_jawak.brokerage,
#                 net_recievable=broken_jawak.net_recievable,
#                 loading_date=broken_jawak.loading_date,
#                 recieved_date=broken_jawak.recieved_date,
#                 payment_recieved=broken_jawak.payment_recieved,
#                 number_of_days=broken_jawak.number_of_days,
#                 payment_difference=broken_jawak.payment_difference,
#                 remarks=broken_jawak.remarks,
#                 broken_jawak_id=broken_jawak.broken_jawak_id,
#                 party_name=broken_jawak.party.party_name,
#                 rice_mill_name=broken_jawak.addricemill.rice_mill_name,
#                 broker_name=broken_jawak.brokers.broker_name,
#                 truck_number=broken_jawak.trucks.truck_number,
#             )
#         )

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return result


# # ________________________________________________________
# # Update Broken Jawak


# @app.put(
#     "/broken-jawak/{broken_jawak_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def update_broken_jawak_data(
#     broken_jawak_id: int,
#     broken_jawak: BrokenJawak,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_get_broken_jawak_data = (
#         db.query(models.broken_jawak)
#         .filter(models.broken_jawak.broken_jawak_id == broken_jawak_id)
#         .first()
#     )
#     if not db_get_broken_jawak_data:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Broken jawak data not found"
#         )
#     for var, value in vars(broken_jawak).items():
#         setattr(db_get_broken_jawak_data, var, value) if value else None

#     db.add(db_get_broken_jawak_data)
#     db.commit()
#     db.refresh(db_get_broken_jawak_data)

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_get_broken_jawak_data


# @app.delete(
#     "/broken-jawak/{broken_jawak_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def delete_broken_jawak_data(
#     broken_jawak_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_broken_jawak = (
#         db.query(models.broken_jawak)
#         .filter(models.broken_jawak.broken_jawak_id == broken_jawak_id)
#         .first()
#     )
#     if not db_broken_jawak:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Broken jawak data not found"
#         )
#     db.delete(db_broken_jawak)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)


# # Husk Jawak
# @app.post(
#     "/husk-jawak/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
# )
# async def add_husk_jawak(
#     huskjawak: HuskJawakBase, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_add_husk_jawak = models.husk_jawak(**huskjawak.dict())
#     db.add(db_add_husk_jawak)
#     db.commit()


# @app.get(
#     "/other-husk-jawak-data/",
#     response_model=List[HuskJawakWithPartyRiceBrokerTruck],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def get_all_husk_jawak_data(
#     token: str = Header(None), db: Session = Depends(get_db)
# ):
#     husks_jawak = (
#         db.query(models.husk_jawak)
#         .options(
#             joinedload(models.husk_jawak.addricemill),
#             joinedload(models.husk_jawak.trucks),
#             joinedload(models.husk_jawak.party),
#             joinedload(models.husk_jawak.brokers),
#         )
#         .all()
#     )

#     result = []
#     for husk_jawak in husks_jawak:
#         result.append(
#             HuskJawakWithPartyRiceBrokerTruck(
#                 rst_number=husk_jawak.rst_number,
#                 date=husk_jawak.date,
#                 party_id=husk_jawak.party_id,
#                 rice_mill_name_id=husk_jawak.rice_mill_name_id,
#                 remarks=husk_jawak.remarks,
#                 broker=husk_jawak.broker,
#                 brokerage_percentage=husk_jawak.brokerage_percentage,
#                 weight=husk_jawak.weight,
#                 rate=husk_jawak.rate,
#                 number_of_bags=husk_jawak.number_of_bags,
#                 truck_number_id=husk_jawak.truck_number_id,
#                 total=husk_jawak.total,
#                 brokerage=husk_jawak.brokerage,
#                 net_receivable=husk_jawak.net_receivable,
#                 received_date=husk_jawak.received_date,
#                 loading_date=husk_jawak.loading_date,
#                 payment_received=husk_jawak.payment_received,
#                 number_of_days=husk_jawak.number_of_days,
#                 payment_difference=husk_jawak.payment_difference,
#                 party_name=husk_jawak.party.party_name,
#                 rice_mill_name=husk_jawak.addricemill.rice_mill_name,
#                 broker_name=husk_jawak.brokers.broker_name,
#                 truck_number=husk_jawak.trucks.truck_number,
#                 husk_jawak_id=husk_jawak.husk_jawak_id,
#             )
#         )

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return result


# @app.put(
#     "/other-husk-jawak-data/{husk_jawak_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def update_husk_jawak_data(
#     husk_jawak_id: int,
#     huskjawak: HuskJawakBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_husk_jawak = (
#         db.query(models.husk_jawak)
#         .filter(models.husk_jawak.husk_jawak_id == husk_jawak_id)
#         .first()
#     )
#     if not db_husk_jawak:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Husk Jawak Data not found"
#         )
#     db_husk_jawak.rst_number = huskjawak.rst_number
#     db_husk_jawak.date = huskjawak.date
#     db_husk_jawak.party_id = huskjawak.party_id
#     db_husk_jawak.rice_mill_name_id = huskjawak.rice_mill_name_id
#     db_husk_jawak.remarks = huskjawak.remarks
#     db_husk_jawak.broker = huskjawak.broker
#     db_husk_jawak.brokerage_percentage = huskjawak.brokerage_percentage
#     db_husk_jawak.weight = huskjawak.weight
#     db_husk_jawak.rate = huskjawak.rate
#     db_husk_jawak.number_of_bags = huskjawak.number_of_bags
#     db_husk_jawak.truck_number_id = huskjawak.truck_number_id
#     db_husk_jawak.total = huskjawak.total
#     db_husk_jawak.brokerage = huskjawak.brokerage
#     db_husk_jawak.net_receivable = huskjawak.net_receivable
#     db_husk_jawak.received_date = huskjawak.received_date
#     db_husk_jawak.loading_date = huskjawak.loading_date
#     db_husk_jawak.payment_received = huskjawak.payment_received
#     db_husk_jawak.number_of_days = huskjawak.number_of_days
#     db_husk_jawak.payment_difference = huskjawak.payment_difference
#     db.commit()
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_husk_jawak


# @app.delete(
#     "/other-husk-jawak-data/{husk_jawak_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def delete_husk_jawak_data(
#     husk_jawak_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_husk_jawak = (
#         db.query(models.husk_jawak)
#         .filter(models.husk_jawak.husk_jawak_id == husk_jawak_id)
#         .first()
#     )
#     if not db_husk_jawak:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Husk Jawak Data not found"
#         )
#     db.delete(db_husk_jawak)
#     db.commit()
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)


# # ________________________________________________________


# # nakkhi_jawak
# @app.post(
#     "/nakkhi-jawak/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
# )
# async def add_nakkhi_jawak(
#     nakkhijawak: NakkhiJawakBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_add_nakkhi_jawak = models.nakkhi_jawak(**nakkhijawak.dict())
#     db.add(db_add_nakkhi_jawak)
#     db.commit()


# @app.get(
#     "/other-nakkhi-jawak-data/",
#     response_model=List[NakkhiWithRicePartyBrokerTruck],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def get_all_nakkhi_jawak_data(
#     token: str = Header(None), db: Session = Depends(get_db)
# ):
#     nakkhis_jawak = (
#         db.query(models.nakkhi_jawak)
#         .options(
#             joinedload(models.nakkhi_jawak.addricemill),
#             joinedload(models.nakkhi_jawak.trucks),
#             joinedload(models.nakkhi_jawak.party),
#             joinedload(models.nakkhi_jawak.brokers),
#         )
#         .all()
#     )

#     result = []
#     for nakkhi_jawak in nakkhis_jawak:
#         result.append(
#             NakkhiWithRicePartyBrokerTruck(
#                 rst_number=nakkhi_jawak.rst_number,
#                 date=nakkhi_jawak.date,
#                 party_id=nakkhi_jawak.party_id,
#                 rice_mill_name_id=nakkhi_jawak.rice_mill_name_id,
#                 broker=nakkhi_jawak.broker,
#                 brokerage_percent=nakkhi_jawak.brokerage_percent,
#                 weight=nakkhi_jawak.weight,
#                 rate=nakkhi_jawak.rate,
#                 number_of_bags=nakkhi_jawak.number_of_bags,
#                 truck_number_id=nakkhi_jawak.truck_number_id,
#                 brokerage=nakkhi_jawak.brokerage,
#                 total=nakkhi_jawak.total,
#                 net_recievable=nakkhi_jawak.net_recievable,
#                 loading_date=nakkhi_jawak.loading_date,
#                 recieved_date=nakkhi_jawak.recieved_date,
#                 payment_recieved=nakkhi_jawak.payment_recieved,
#                 number_of_days=nakkhi_jawak.number_of_days,
#                 payment_difference=nakkhi_jawak.payment_difference,
#                 remarks=nakkhi_jawak.remarks,
#                 nakkhi_jawak_id=nakkhi_jawak.nakkhi_jawak_id,
#                 party_name=nakkhi_jawak.party.party_name,
#                 rice_mill_name=nakkhi_jawak.addricemill.rice_mill_name,
#                 broker_name=nakkhi_jawak.brokers.broker_name,
#                 truck_number=nakkhi_jawak.trucks.truck_number,
#             )
#         )

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return result


# @app.put(
#     "/nakkhi-jawak/{nakkhi_jawak_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def update_nakkhi_jawak_data(
#     nakkhi_jawak_id: int,
#     nakkhijawak: NakkhiJawakBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_nakkhi_jawak = (
#         db.query(models.nakkhi_jawak)
#         .filter(models.nakkhi_jawak.nakkhi_jawak_id == nakkhi_jawak_id)
#         .first()
#     )
#     if not db_nakkhi_jawak:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Nakkhi Jawak Data not found"
#         )
#     db_nakkhi_jawak.rst_number = nakkhijawak.rst_number
#     db_nakkhi_jawak.date = nakkhijawak.date
#     db_nakkhi_jawak.party_id = nakkhijawak.party_id
#     db_nakkhi_jawak.rice_mill_name_id = nakkhijawak.rice_mill_name_id
#     db_nakkhi_jawak.remarks = nakkhijawak.remarks
#     db_nakkhi_jawak.broker = nakkhijawak.broker
#     db_nakkhi_jawak.brokerage_percentage = nakkhijawak.brokerage_percentage
#     db_nakkhi_jawak.weight = nakkhijawak.weight
#     db_nakkhi_jawak.rate = nakkhijawak.rate
#     db_nakkhi_jawak.number_of_bags = nakkhijawak.number_of_bags
#     db_nakkhi_jawak.truck_number_id = nakkhijawak.truck_number_id
#     db_nakkhi_jawak.total = nakkhijawak.total
#     db_nakkhi_jawak.brokerage = nakkhijawak.brokerage
#     db_nakkhi_jawak.net_receivable = nakkhijawak.net_receivable
#     db_nakkhi_jawak.received_date = nakkhijawak.received_date
#     db_nakkhi_jawak.loading_date = nakkhijawak.loading_date
#     db_nakkhi_jawak.payment_received = nakkhijawak.payment_received
#     db_nakkhi_jawak.number_of_days = nakkhijawak.number_of_days
#     db_nakkhi_jawak.payment_difference = nakkhijawak.payment_difference
#     db.commit()
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_nakkhi_jawak


# @app.delete(
#     "/nakkhi-jawak/{nakkhi_jawak_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def delete_nakkhi_jawak_data(
#     nakkhi_jawak_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_nakkhi_jawak = (
#         db.query(models.nakkhi_jawak)
#         .filter(models.nakkhi_jawak.nakkhi_jawak_id == nakkhi_jawak_id)
#         .first()
#     )
#     if not db_nakkhi_jawak:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Nakkhi Jawak Data not found"
#         )
#     db.delete(db_nakkhi_jawak)
#     db.commit()
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)


# # ________________________________________________________


# # bran jawak
# @app.post(
#     "/bran-jawak/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
# )
# async def add_bran_jawak(
#     branjawak: BranJawakBase, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_add_bran_jawak = models.bran_jawak(**branjawak.dict())
#     db.add(db_add_bran_jawak)
#     db.commit()


# @app.get(
#     "/other-bran-jawak-data/",
#     response_model=List[BranJawakWithRicePatryBrokerTruck],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def get_all_bran_jawak_data(
#     token: str = Header(None), db: Session = Depends(get_db)
# ):
#     brans_jawak = (
#         db.query(models.bran_jawak)
#         .options(
#             joinedload(models.bran_jawak.addricemill),
#             joinedload(models.bran_jawak.trucks),
#             joinedload(models.bran_jawak.party),
#             joinedload(models.bran_jawak.brokers),
#         )
#         .all()
#     )

#     result = []
#     for bran_jawak in brans_jawak:
#         result.append(
#             BranJawakWithRicePatryBrokerTruck(
#                 rst_number=bran_jawak.rst_number,
#                 date=bran_jawak.date,
#                 party_id=bran_jawak.party_id,
#                 rice_mill_name_id=bran_jawak.rice_mill_name_id,
#                 broker=bran_jawak.broker,
#                 brokerage_percentage=bran_jawak.brokerage_percentage,
#                 weight=bran_jawak.weight,
#                 rate=bran_jawak.rate,
#                 number_of_bags=bran_jawak.number_of_bags,
#                 truck_number_id=bran_jawak.truck_number_id,
#                 total=bran_jawak.total,
#                 brokerage=bran_jawak.brokerage,
#                 net_receivable=bran_jawak.net_receivable,
#                 payment_received=bran_jawak.payment_received,
#                 payment_difference=bran_jawak.payment_difference,
#                 remarks=bran_jawak.remarks,
#                 oil=bran_jawak.oil,
#                 bran_jawak_id=bran_jawak.bran_jawak_id,
#                 party_name=bran_jawak.party.party_name,
#                 rice_mill_name=bran_jawak.addricemill.rice_mill_name,
#                 broker_name=bran_jawak.brokers.broker_name,
#                 truck_number=bran_jawak.trucks.truck_number,
#             )
#         )

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return result


# @app.put(
#     "/bran-jawak/{bran_jawak_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def update_bran_jawak_data(
#     bran_jawak_id: int,
#     branjawak: BranJawakBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_bran_jawak = (
#         db.query(models.bran_jawak)
#         .filter(models.bran_jawak.bran_jawak_id == bran_jawak_id)
#         .first()
#     )
#     if not db_bran_jawak:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Bran Jawak Data not found"
#         )
#     db_bran_jawak.rst_number = branjawak.rst_number
#     db_bran_jawak.date = branjawak.date
#     db_bran_jawak.party_id = branjawak.party_id
#     db_bran_jawak.rice_mill_name_id = branjawak.rice_mill_name_id
#     db_bran_jawak.remarks = branjawak.remarks
#     db_bran_jawak.broker = branjawak.broker
#     db_bran_jawak.brokerage_percentage = branjawak.brokerage_percentage
#     db_bran_jawak.weight = branjawak.weight
#     db_bran_jawak.rate = branjawak.rate
#     db_bran_jawak.number_of_bags = branjawak.number_of_bags
#     db_bran_jawak.truck_number_id = branjawak.truck_number_id
#     db_bran_jawak.total = branjawak.total
#     db_bran_jawak.brokerage = branjawak.brokerage
#     db_bran_jawak.net_receivable = branjawak.net_receivable
#     db_bran_jawak.received_date = branjawak.received_date
#     db_bran_jawak.loading_date = branjawak.loading_date
#     db_bran_jawak.payment_received = branjawak.payment_received
#     db_bran_jawak.number_of_days = branjawak.number_of_days
#     db_bran_jawak.payment_difference = branjawak.payment_difference
#     db.commit()
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_bran_jawak


# @app.delete(
#     "/bran-jawak/{bran_jawak_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def delete_bran_jawak_data(
#     bran_jawak_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_bran_jawak = (
#         db.query(models.bran_jawak)
#         .filter(models.bran_jawak.bran_jawak_id == bran_jawak_id)
#         .first()
#     )
#     if not db_bran_jawak:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Bran Jawak Data not found"
#         )
#     db.delete(db_bran_jawak)
#     db.commit()
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)


# # ________________________________________________________


# # Bhushi
# @app.post(
#     "/bhushi/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
# )
# async def add_bhushi(
#     bhushi: BhushiBase, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_add_bhushi = models.bhushi(**bhushi.dict())
#     db.add(db_add_bhushi)
#     db.commit()


# @app.get(
#     "/other-bhushi-data/",
#     response_model=List[BhushiWithPartyRiceTruck],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def get_all_bhushi_jawak_data(
#     token: str = Header(None), db: Session = Depends(get_db)
# ):
#     bhushiii = (
#         db.query(models.bhushi)
#         .options(
#             joinedload(models.bhushi.addricemill),
#             joinedload(models.bhushi.trucks),
#             joinedload(models.bhushi.party),
#         )
#         .all()
#     )

#     result = []
#     for bhushi in bhushiii:
#         result.append(
#             BhushiWithPartyRiceTruck(
#                 rst_number=bhushi.rst_number,
#                 date=bhushi.date,
#                 party_id=bhushi.party_id,
#                 rice_mill_name_id=bhushi.rice_mill_name_id,
#                 number_of_bags=bhushi.number_of_bags,
#                 weight=bhushi.weight,
#                 truck_number_id=bhushi.truck_number_id,
#                 rate=bhushi.rate,
#                 amount=bhushi.amount,
#                 bhushi_id=bhushi.bhushi_id,
#                 party_name=bhushi.party.party_name,
#                 rice_mill_name=bhushi.addricemill.rice_mill_name,
#                 truck_number=bhushi.trucks.truck_number,
#             )
#         )

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return result


# @app.put(
#     "/bhushi/{bhushi_id}/",
#     status_code=status.HTTP_202_ACCEPTED,
#     dependencies=[Depends(api_key_header)],
# )
# async def update_bhushi(
#     bhushi_id: int,
#     bhushi: BhushiBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_bhushi = (
#         db.query(models.bhushi).filter(models.bhushi.bhushi_id == bhushi_id).first()
#     )
#     if not db_bhushi:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Bhushi not found"
#         )
#     for var, value in vars(bhushi).items():
#         setattr(db_bhushi, var, value) if value else None
#     db.add(db_bhushi)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_bhushi


# @app.delete(
#     "/bhushi/{bhushi_id}/",
#     status_code=status.HTTP_202_ACCEPTED,
#     dependencies=[Depends(api_key_header)],
# )
# async def delete_bhushi(
#     bhushi_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_bhushi = (
#         db.query(models.bhushi).filter(models.bhushi.bhushi_id == bhushi_id).first()
#     )
#     if not db_bhushi:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Bhushi not found"
#         )
#     db.delete(db_bhushi)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)


# # ________________________________________________________


# # paddy sale
# @app.post(
#     "/paddy-sale/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
# )
# async def paddy_sale(
#     paddysale: PaddySaleBase, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_paddy_sale = models.Paddy_sale(**paddysale.dict())
#     db.add(db_paddy_sale)
#     db.commit()


# @app.get(
#     "/paddy-sale-data/",
#     response_model=List[PaddySalesWithDhanawakPartyBrokerTruck],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def get_all_paddy_sale_data(
#     token: str = Header(None), db: Session = Depends(get_db)
# ):
#     paddy_sales = (
#         db.query(models.Paddy_sale)
#         .options(
#             joinedload(models.Paddy_sale.dhanawak),
#             joinedload(models.Paddy_sale.brokers),
#             joinedload(models.Paddy_sale.trucks),
#             joinedload(models.Paddy_sale.party),
#             joinedload(models.Paddy_sale.addricemill),
#         )
#         .all()
#     )

#     result = []
#     for paddy_sale in paddy_sales:
#         result.append(
#             PaddySalesWithDhanawakPartyBrokerTruck(
#                 rst_number_id=paddy_sale.rst_number_id,
#                 rice_mill_name_id=paddy_sale.rice_mill_name_id,
#                 date=paddy_sale.date,
#                 party_id=paddy_sale.party_id,
#                 broker=paddy_sale.broker,
#                 loading_form_address=paddy_sale.loading_form_address,
#                 truck_number_id=paddy_sale.truck_number_id,
#                 paddy_name=paddy_sale.paddy_name,
#                 weight=paddy_sale.weight,
#                 party_weight=paddy_sale.party_weight,
#                 bags=paddy_sale.bags,
#                 rate=paddy_sale.rate,
#                 ammount=paddy_sale.ammount,
#                 plastic=paddy_sale.plastic,
#                 joot_old=paddy_sale.joot_old,
#                 joot_23_24=paddy_sale.joot_23_24,
#                 joot_22_23=paddy_sale.joot_22_23,
#                 average_bag_wt=paddy_sale.average_bag_wt,
#                 paddy_sale_id=paddy_sale.paddy_sale_id,
#                 rst_number=paddy_sale.dhanawak.rst_number,
#                 party_name=paddy_sale.party.party_name,
#                 broker_name=paddy_sale.brokers.broker_name,
#                 truck_number=paddy_sale.trucks.truck_number,
#                 rice_mill_name=paddy_sale.addricemill.rice_mill_name,
#             )
#         )

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return result


# @app.put(
#     "/paddy-sale/{paddy_sale_id}/",
#     status_code=status.HTTP_202_ACCEPTED,
#     dependencies=[Depends(api_key_header)],
# )
# async def update_paddy_sale(
#     paddy_sale_id: int,
#     paddysale: PaddySaleBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_paddy_sale = (
#         db.query(models.Paddy_sale)
#         .filter(models.Paddy_sale.paddy_sale_id == paddy_sale_id)
#         .first()
#     )
#     if not db_paddy_sale:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Paddy Sale not found"
#         )
#     for var, value in vars(paddysale).items():
#         setattr(db_paddy_sale, var, value) if value else None
#     db.add(db_paddy_sale)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_paddy_sale


# @app.delete(
#     "/paddy-sale/{paddy_sale_id}/",
#     status_code=status.HTTP_202_ACCEPTED,
#     dependencies=[Depends(api_key_header)],
# )
# async def delete_paddy_sale(
#     paddy_sale_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_paddy_sale = (
#         db.query(models.Paddy_sale)
#         .filter(models.Paddy_sale.paddy_sale_id == paddy_sale_id)
#         .first()
#     )
#     if not db_paddy_sale:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Paddy Sale not found"
#         )
#     db.delete(db_paddy_sale)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return {"detail": "Paddy Sale deleted"}


# # ________________________________________________________
# # Rice Purchase
# @app.post(
#     "/rice-purchase/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
# )
# async def rice_purchase(
#     ricepurchase: RicePurchaseBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_rice_purchase = models.Rice_Purchase(**ricepurchase.dict())
#     db.add(db_rice_purchase)
#     db.commit()


# @app.get(
#     "/rice-purchase-data/",
#     response_model=List[RicePurchaseWithRiceTruckParty],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def get_all_rice_purchase_data(
#     token: str = Header(None), db: Session = Depends(get_db)
# ):
#     ricepurchases = (
#         db.query(models.Rice_Purchase)
#         .options(
#             joinedload(models.Rice_Purchase.brokers),
#             joinedload(models.Rice_Purchase.trucks),
#             joinedload(models.Rice_Purchase.party),
#             joinedload(models.Rice_Purchase.addricemill),
#         )
#         .all()
#     )

#     result = []
#     for ricepurchase in ricepurchases:
#         result.append(
#             RicePurchaseWithRiceTruckParty(
#                 rst_number=ricepurchase.rst_number,
#                 date=ricepurchase.date,
#                 party_id=ricepurchase.party_id,
#                 broker_id=ricepurchase.broker_id,
#                 truck_number_id=ricepurchase.truck_number_id,
#                 bags=ricepurchase.bags,
#                 mill_weight=ricepurchase.mill_weight,
#                 party_weight=ricepurchase.party_weight,
#                 bill_to_rice_mill=ricepurchase.bill_to_rice_mill,
#                 rice_purchase_id=ricepurchase.rice_purchase_id,
#                 party_name=ricepurchase.party.party_name,
#                 broker_name=ricepurchase.brokers.broker_name,
#                 truck_number=ricepurchase.trucks.truck_number,
#                 rice_mill_name=ricepurchase.addricemill.rice_mill_name,
#             )
#         )

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return result


# @app.put(
#     "/rice-purchase/{rice_purchase_id}/",
#     status_code=status.HTTP_202_ACCEPTED,
#     dependencies=[Depends(api_key_header)],
# )
# async def update_rice_purchase(
#     rice_purchase_id: int,
#     ricepurchase: RicePurchaseBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_rice_purchase = (
#         db.query(models.Rice_Purchase)
#         .filter(models.Rice_Purchase.rice_purchase_id == rice_purchase_id)
#         .first()
#     )
#     if not db_rice_purchase:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Rice Purchase not found"
#         )
#     for var, value in vars(ricepurchase).items():
#         setattr(db_rice_purchase, var, value) if value else None
#     db.add(db_rice_purchase)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_rice_purchase


# @app.delete(
#     "/rice-purchase/{rice_purchase_id}/",
#     status_code=status.HTTP_202_ACCEPTED,
#     dependencies=[Depends(api_key_header)],
# )
# async def delete_rice_purchase(
#     rice_purchase_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_rice_purchase = (
#         db.query(models.Rice_Purchase)
#         .filter(models.Rice_Purchase.rice_purchase_id == rice_purchase_id)
#         .first()
#     )
#     if not db_rice_purchase:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Rice Purchase not found"
#         )
#     db.delete(db_rice_purchase)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return {"detail": "Rice Purchase deleted"}


# # ________________________________________________________
# # Cash in and Cash out
# @app.post(
#     "/cash-in-out/",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_key_header)],
# )
# async def cash_in_out(
#     cash_in_out: CashInCashOutBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_cash_in_out = models.CashInCashOut(**cash_in_out.dict())
#     db.add(db_cash_in_out)
#     db.commit()


# @app.get(
#     "/cash-in-out-data/",
#     response_model=List[CashInCashOutBase],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def cash_in_out_data(token: str = Header(None), db: Session = Depends(get_db)):
#     db_cash_in_out_data = db.query(models.CashInCashOut).distinct().all()
#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_cash_in_out_data


# @app.put(
#     "/cash-in-out/{cash_in_out_id}/",
#     status_code=status.HTTP_202_ACCEPTED,
#     dependencies=[Depends(api_key_header)],
# )
# async def update_cash_in_out(
#     cash_in_out_id: int,
#     cash_in_out: CashInCashOutBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_cash_in_out = (
#         db.query(models.CashInCashOut)
#         .filter(models.CashInCashOut.cash_in_out_id == cash_in_out_id)
#         .first()
#     )
#     if not db_cash_in_out:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Cash In Cash Out not found"
#         )
#     for var, value in vars(cash_in_out).items():
#         setattr(db_cash_in_out, var, value) if value else None
#     db.add(db_cash_in_out)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return db_cash_in_out


# @app.delete(
#     "/cash-in-out/{cash_in_out_id}/",
#     status_code=status.HTTP_202_ACCEPTED,
#     dependencies=[Depends(api_key_header)],
# )
# async def delete_cash_in_out(
#     cash_in_out_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     db_cash_in_out = (
#         db.query(models.CashInCashOut)
#         .filter(models.CashInCashOut.cash_in_out_id == cash_in_out_id)
#         .first()
#     )
#     if not db_cash_in_out:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Cash In Cash Out not found"
#         )
#     db.delete(db_cash_in_out)
#     db.commit()

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return {"detail": "Cash In Cash Out deleted"}


# # Dhan rice societies rate
# @app.post("/dhan-rice-societies-rate/", status_code=status.HTTP_201_CREATED)
# async def dhan_rice_societies_rate(
#     dhansocietiesrate: DhanRiceSocietiesRateBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_dhan_rice_societies_rate = models.Dhan_rice_societies_rate(
#         **dhansocietiesrate.dict()
#     )
#     db.add(db_dhan_rice_societies_rate)
#     db.commit()


# # # lot number master
# @app.post("/lot-number-master/", status_code=status.HTTP_201_CREATED)
# async def lot_number_master(
#     lotnumbermaster: LotNumberMasterBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_lot_number_master = models.Lot_number_master(**lotnumbermaster.dict())
#     db.add(db_lot_number_master)
#     db.commit()


# # Mohan food paddy
# @app.post("/mohan-food-paddy/", status_code=status.HTTP_201_CREATED)
# async def mohan_food_paddy(
#     mohanfoodpaddy: MohanFoodPaddyBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_mohan_food_paddy = models.Mohan_food_paddy(**mohanfoodpaddy.dict())
#     db.add(db_mohan_food_paddy)
#     db.commit()


# # Transporter master
# @app.post("/transporter-master/", status_code=status.HTTP_201_CREATED)
# async def transporter_master(
#     transportermaster: TransporterMasterBase,
#     token: str = Header(None),
#     db: Session = Depends(get_db),
# ):
#     db_transporter_master = models.Transporter_master(**transportermaster.dict())
#     db.add(db_transporter_master)
#     db.commit()


# @app.get(
#     "/paddy-data/{rice_mill_id}",
#     response_model=DhanAwakDalaliDhan,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def get_data(
#     rice_mill_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     # Fetch data from different tables
#     total_weight = db.query(models.Dalali_dhaan).all()
#     dm_weight = db.query(models.Dhan_Awak).filter_by(rice_mill_id=rice_mill_id).all()
#     weight = db.query(models.Paddy_sale).filter_by(rice_mill_name_id=rice_mill_id).all()
#     miller_purana = (
#         db.query(models.Dhan_Awak).filter_by(rice_mill_id=rice_mill_id).all()
#     )
#     Paddy_deposite_data = (
#         db.query(models.Rice_deposite).filter_by(rice_mill_name_id=rice_mill_id).all()
#     )

#     # payload=g
#     response_data = {
#         "total_weight": [row.total_weight for row in total_weight],
#         "Dhan_data": [DhanAwakBase(**row.__dict__) for row in dm_weight],
#         "Paddy_sale_data": [PaddySaleBase(**row.__dict__) for row in weight],
#         "miller_purana": [DhanAwakBase(**row.__dict__) for row in miller_purana],
#         "Paddy_deposite_data": [
#             RiceDepositeBase(**row.__dict__) for row in Paddy_deposite_data
#         ],
#     }

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return DhanAwakDalaliDhan(**response_data)


# @app.get(
#     "/rice-data/{rice_mill_id}",
#     response_model=inventoryData,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def get_data(
#     rice_mill_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     mill_weight = db.query(models.Rice_Purchase).all()
#     rice_deposide_data = (
#         db.query(models.Rice_deposite).filter_by(rice_mill_name_id=rice_mill_id).all()
#     )
#     broken_data = (
#         db.query(models.broken_jawak).filter_by(rice_mill_name_id=rice_mill_id).all()
#     )
#     bran_data = (
#         db.query(models.bran_jawak).filter_by(rice_mill_name_id=rice_mill_id).all()
#     )
#     nakkhi_data = (
#         db.query(models.nakkhi_jawak).filter_by(rice_mill_name_id=rice_mill_id).all()
#     )
#     husk_data = (
#         db.query(models.husk_jawak).filter_by(rice_mill_name_id=rice_mill_id).all()
#     )

#     response_data = {
#         "mill_weight": [row.mill_weight for row in mill_weight],
#         "rice_deposide_data": [row.__dict__ for row in rice_deposide_data],
#         "broken_data": [row.__dict__ for row in broken_data],
#         "bran_data": [row.__dict__ for row in bran_data],
#         "nakkhi_data": [row.__dict__ for row in nakkhi_data],
#         "husk_data": [row.__dict__ for row in husk_data],
#     }

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return inventoryData(**response_data)


# class BardanaDataDhanAwak(BaseModel):
#     Dhan_Awak_Data: List[DhanAwakBase]


# @app.get(
#     "/bardaha-data/{rice_mill_id}",
#     response_model=BardanaDataDhanAwak,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(api_key_header)],
# )
# async def get_data(
#     rice_mill_id: int, token: str = Header(None), db: Session = Depends(get_db)
# ):
#     # Fetch data from different tables
#     Dhan_Awak_Data = (
#         db.query(models.Dhan_Awak).filter_by(rice_mill_id=rice_mill_id).all()
#     )

#     response_data = {
#         "Dhan_Awak_Data": [DhanAwakBase(**row.__dict__) for row in Dhan_Awak_Data],
#     }

#     payload = get_user_from_token(token)
#     message = f"New action performed by user.\nName: {payload.get('sub')} "
#     send_telegram_message(message)
#     return BardanaDataDhanAwak(**response_data)
