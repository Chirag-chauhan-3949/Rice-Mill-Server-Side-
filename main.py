import os
from fastapi import FastAPI, Depends, HTTPException, Request, status, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
import models
from schemas import (
    AddRiceMillBase,
    TransporterBase,
    AddUserBase,
    PermissionsUpdateRequest,
    TruckBase,
    TruckWithTransporter,
    UpdateRiceMillBase,
    RoleBase,
    LoginRequest,
    AddRiceMillBase,
    TransporterBase,
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
import schemas
from models import Add_Rice_Mill, Transporter, Permission, User, Role
from database import engine, Base, get_db
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime

# Get the current time
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://mill.dappfolk.com"],  # Replace with your frontend's URL
    allow_origins=["http://localhost:5173"],  # Replace with your frontend's URL
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
    user = db.query(User).filter(User.email == user.email).first()

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
@app.get(
    "/get-roles-data",
    response_model=List[RoleBase],
    tags=["Get All User Role and Permissions "],
)
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


@app.get("/roles-and-permissions", tags=["User Role and Permissions"])
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


@app.post("/update-permissions", tags=["User Role and Permissions"])
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
@app.post("/add-rice-mill/", response_model=AddRiceMillBase, tags=["Rice Mill"])
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
    "/get-rice-mill/{rice_mill_id}", response_model=AddRiceMillBase, tags=["Rice Mill"]
)
async def get_rice_mill(
    rice_mill_id: int,
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

    return rice_mill


# To get all rice mill data
@app.get(
    "/get-all-rice-mills/", response_model=List[AddRiceMillBase], tags=["Rice Mill"]
)
async def get_all_rice_mills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Retrieve all rice mills
    rice_mills = db.query(Add_Rice_Mill).all()

    return rice_mills


# Update Rice Mill
@app.put(
    "/update-rice-mill/{rice_mill_id}",
    response_model=UpdateRiceMillBase,
    tags=["Rice Mill"],
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
@app.delete("/delete-rice-mill/{rice_mill_id}", response_model=dict, tags=["Rice Mill"])
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
@app.post("/add-transporter/", response_model=TransporterBase, tags=["Transporter"])
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
    tags=["Transporter"],
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
    tags=["Transporter"],
)
async def get_all_transporters(db: Session = Depends(get_db)):
    # Retrieve all transporters
    transporters = db.query(Transporter).all()

    return transporters


@app.put(
    "/update-transporter/{transporter_id}",
    response_model=TransporterBase,
    tags=["Transporter"],
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
    "/delete-transporter/{transporter_id}", response_model=dict, tags=["Transporter"]
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


# create the post route for truck
@app.post(
    "/truck/",
    status_code=status.HTTP_201_CREATED,
    response_model=TruckBase,
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

    message = (
        f"User {current_user.name} added a new truck:\n"
        f"Truck Number: {db_truck.truck_number}\n"
        f"Data: {truck.dict()}"
    )

    send_telegram_message(message)

    return db_truck


# create the get route for truck
@app.get("/get-truck/{truck_id}", response_model=TruckBase, tags=["Truck"])
async def get_truck(truck_id: int, db: Session = Depends(get_db)):
    # Retrieve the Truck by ID
    truck = db.query(models.Truck).filter(models.Truck.truck_id == truck_id).first()

    # Check if the Truck exists
    if not truck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Truck not found",
        )

    return truck


# # create the update route for truck
@app.put("/update-truck/{truck_id}", response_model=TruckBase, tags=["Truck"])
async def update_truck(truck_id: int, Truck: TruckBase, db: Session = Depends(get_db)):
    # Retrieve the Truck by ID
    truck = db.query(models.Truck).filter(models.Truck.truck_id == truck_id).first()

    # Check if the Truck exists
    if not truck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Truck not found",
        )

    # Update the Truck data in another way
    truck.transport_id = Truck.transport_id
    truck.truck_number = Truck.truck_number

    db.commit()
    db.refresh(truck)

    return truck


# # write delete route for truck
@app.delete("/delete-truck/{truck_id}", tags=["Truck"])
async def delete_truck(truck_id: int, db: Session = Depends(get_db)):
    # Retrieve the Truck by ID
    truck = db.query(models.Truck).filter(models.Truck.truck_id == truck_id).first()

    # Check if the Truck exists
    if not truck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Truck not found",
        )

    # Delete the Truck entry
    db.delete(truck)
    db.commit()

    return {"message": "Truck deleted successfully"}


@app.get(
    "/get-all-trucks/",
    response_model=List[TruckWithTransporter],
    status_code=status.HTTP_200_OK,
    tags=["Truck"],
)
async def get_all_truck_data(db: Session = Depends(get_db)):
    trucks = db.query(models.Truck).all()

    # Check if the Truck exists
    if not trucks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Truck not found",
        )

    result = []
    for truck in trucks:
        result.append(
            TruckWithTransporter(
                truck_number=truck.truck_number,
                transporter_name=truck.transporter.transporter_name,
                transport_id=truck.transport_id,
                truck_id=truck.truck_id,
            )
        )
    return result


@app.get(
    "/truck-numbers/",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(api_key_header)],
    tags=["Truck"],
)
async def get_truck_numbers(token: str = Header(None), db: Session = Depends(get_db)):
    db_truck_numbers = db.query(models.Truck.truck_number).distinct().all()
    payload = get_user_from_token(token)
    message = f"New action performed by user.\nName: {payload.get('sub')} "
    send_telegram_message(message)
    return [truck_number[0] for truck_number in db_truck_numbers]


# Add Society
@app.post(
    "/add-society/",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.SocietyBase,
    tags=["Society"],
)
async def add_society(
    addsociety: schemas.SocietyBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_society = (
        db.query(models.Society)
        .filter(models.Society.society_name == addsociety.society_name)
        .first()
    )
    if existing_society:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Society with this name already exists",
        )
    db_society = models.Society(
        **addsociety.dict(),
        user_id=current_user.id,
    )
    db.add(db_society)
    db.commit()
    db.refresh(db_society)

    message = (
        f"User {current_user.name} added a new Society:\n"
        f"Name: {db_society.society_name}\n"
        f"Data: {addsociety.dict()}"
    )
    send_telegram_message(message)
    return db_society


@app.get(
    "/get-all-societies/",
    response_model=List[schemas.SocietyBase],
    status_code=status.HTTP_200_OK,
    tags=["Society"],
)
async def get_all_society_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    societys = db.query(models.Society).all()

    return societys


@app.get(
    "/get-societies/{society_id}",
    response_model=schemas.SocietyBase,
    status_code=status.HTTP_200_OK,
    tags=["Society"],
)
async def get_societies_by_user_id(
    society_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Correctly filter societies by society_id
    societies = (
        db.query(models.Society)
        .filter(models.Society.society_id == society_id)  # Fix comparison here
        .first()
    )

    if not societies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No societies found for society ID {society_id}",  # Use passed id in message
        )

    return societies


@app.put(
    "/update-society/{society_id}",
    response_model=schemas.SocietyBase,
    status_code=status.HTTP_200_OK,
    tags=["Society"],
)
async def update_society_data(
    society_id: int,
    update_addsociety: schemas.SocietyBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Retrieve the society by ID
    society = (
        db.query(models.Society).filter(models.Society.society_id == society_id).first()
    )

    # Check if the society exists
    if not society:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Society not found",
        )

    society.society_name = update_addsociety.society_name
    society.distance_from_mill = update_addsociety.distance_from_mill
    society.google_distance = update_addsociety.google_distance
    society.transporting_rate = update_addsociety.transporting_rate
    society.actual_distance = update_addsociety.actual_distance

    # Commit changes to the database
    db.commit()
    db.refresh(society)

    # Prepare and send the message
    message = (
        f"User {current_user.name} updated the society:\n"
        f"Society Name: {society.society_name}\n"
        f"Data: {update_addsociety.dict()}"
    )
    send_telegram_message(message)

    return society


@app.delete(
    "/delete-society/{society_id}",  # Use the new MessageResponse schema
    status_code=status.HTTP_200_OK,
    tags=["Society"],
)
async def delete_society_data(
    society_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    society = (
        db.query(models.Society).filter(models.Society.society_id == society_id).first()
    )
    if not society:
        raise HTTPException(status_code=404, detail="Society not found")

    db.delete(society)
    db.commit()

    message = f"User {current_user.name} deleted the Society: {society.society_name}"
    send_telegram_message(message)

    return {"message": "Society deleted successfully"}


# Add Agreement
@app.post(
    "/add-agreement/",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.AgreementBase,
    tags=["Agreement"],
)
async def add_agreement(
    addagreement: schemas.AgreementBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_agreement = (
        db.query(models.Agreement)
        .filter(models.Agreement.agreement_number == addagreement.agreement_number)
        .first()
    )
    if existing_agreement:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agreement with this name already exists",
        )
    db_agreement = models.Agreement(
        **addagreement.dict(),
        user_id=current_user.id,
    )
    db.add(db_agreement)
    db.commit()
    db.refresh(db_agreement)

    message = (
        f"User {current_user.name} added a new Agreement:\n"
        f"Rice Mill ID: {db_agreement.rice_mill_id}\n"
        f"Agreement Number: {db_agreement.agreement_number}\n"
        f"Type of Agreement: {db_agreement.type_of_agreement}\n"
        f"Lot Range: {db_agreement.lot_from} - {db_agreement.lot_to}\n"
    )

    send_telegram_message(message)
    return db_agreement


@app.get(
    "/get-all-agreements/",
    response_model=List[schemas.AgreementBase],
    status_code=status.HTTP_200_OK,
    # dependencies=[Depends(api_key_header)],
    tags=["Agreement"],
)
async def get_all_agreements_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agreements = (
        db.query(models.Agreement)
        .options(joinedload(models.Agreement.addricemill))
        .all()
    )

    result = []
    for agreement in agreements:
        result.append(
            schemas.RiceMillWithAgreement(
                rice_mill_id=agreement.rice_mill_id,
                agreement_number=agreement.agreement_number,
                type_of_agreement=agreement.type_of_agreement,
                lot_from=agreement.lot_from,
                lot_to=agreement.lot_to,
                agremennt_id=agreement.agremennt_id,
                rice_mill_name=agreement.addricemill.rice_mill_name,
            )
        )

    return result


@app.post(
    "/ware-house-transporting/",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.WareHouseTransporting,
    tags=["Warehouse"],
)
async def add_ware_house(
    warehouse: schemas.WareHouseTransporting,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_warehouse = (
        db.query(models.ware_house_transporting)
        .filter(
            models.ware_house_transporting.ware_house_name == warehouse.ware_house_name
        )
        .first()
    )
    if existing_warehouse:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ware House with this transporting rate already exists",
        )

    db_add_ware_house = models.ware_house_transporting(
        **warehouse.dict(),
        user_id=current_user.id,
    )
    db.add(db_add_ware_house)
    db.commit()
    db.refresh(db_add_ware_house)

    # Create the message to be sent to Telegram
    message = f"""
    A new warehouse has been added:

    - **Warehouse Name**: {warehouse.ware_house_name}
    - **Transporting Rate**: {warehouse.ware_house_transporting_rate}
    - **Hamali Rate**: {warehouse.hamalirate}
    The warehouse has been successfully registered in the system.
    """

    # Send the message to Telegram
    send_telegram_message(message)

    return db_add_ware_house


@app.get(
    "/get-ware-house-data/",
    response_model=List[schemas.WareHouseTransporting],
    status_code=status.HTTP_200_OK,
    tags=["Warehouse"],
)
async def get_all_ware_house_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ware_house_db = db.query(models.ware_house_transporting).all()

    return ware_house_db
