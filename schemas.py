from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Date, String
from typing import Annotated, Dict, List, Optional
from enum import Enum
from datetime import date, datetime


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class AddUserBase(UserCreate):
    role: Optional[str] = "admin"  # Default value is 'admin', but can be overridden

    class Config:
        orm_mode = True


class LoginRequest(BaseModel):
    email: str
    password: str
    role: Optional[str] = None


class RoleBase(BaseModel):
    id: Optional[int] = None
    role_name: str


class PermissionsUpdateRequest(BaseModel):
    permissions: Dict[int, Dict[str, bool]]


class AddRiceMillBase(BaseModel):
    rice_mill_name: str
    gst_number: str
    mill_address: str
    phone_number: int
    rice_mill_capacity: float
    rice_mill_id: Optional[int] = None


class RiceMillResponse(BaseModel):
    message: str
    data: AddRiceMillBase

    class Config:
        orm_mode = True


class UpdateRiceMillBase(BaseModel):
    gst_number: str
    rice_mill_name: str
    mill_address: str
    phone_number: int
    rice_mill_capacity: float


class DhanAwakBase(BaseModel):
    rst_number: int
    rice_mill_id: int
    date: date
    do_id: int
    society_id: int
    dm_weight: float
    number_of_bags: float
    truck_number_id: int
    transporter_name_id: int
    transporting_rate: int
    transporting_total: int
    jama_jute_22_23: int
    ek_bharti_21_22: int
    pds: int
    miller_purana: float
    kisan: int
    bardana_society: int
    hdpe_22_23: int
    hdpe_21_22: int
    hdpe_21_22_one_use: int
    total_bag_weight: float
    type_of_paddy: str
    actual_paddy: str
    mill_weight_quintals: float
    shortage: float
    bags_put_in_hopper: int
    bags_put_in_stack: int
    hopper_rice_mill_id: str
    stack_location: str


class UpdateDhanAwakBase(BaseModel):
    rst_number: int
    rice_mill_id: int
    date: date
    do_id: int
    society_id: int
    dm_weight: float
    number_of_bags: float
    truck_number_id: int
    transporter_name_id: int
    transporting_rate: int
    transporting_total: int
    jama_jute_22_23: int
    ek_bharti_21_22: int
    pds: int
    miller_purana: float
    kisan: int
    bardana_society: int
    hdpe_22_23: int
    hdpe_21_22: int
    hdpe_21_22_one_use: int
    total_bag_weight: float
    type_of_paddy: str
    actual_paddy: str
    mill_weight_quintals: float
    shortage: float
    bags_put_in_hopper: int
    bags_put_in_stack: int
    hopper_rice_mill_id: str
    stack_location: str
