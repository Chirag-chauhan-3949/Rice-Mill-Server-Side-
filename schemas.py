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
    id: Optional[int] = None
    email: str
    password: str
    role: Optional[str] = None


class RoleBase(BaseModel):
    id: Optional[int] = None
    role_name: str


class PermissionsUpdateRequest(BaseModel):
    permissions: Dict[str, Dict[str, bool]]


# Add
class AddRiceMillBase(BaseModel):
    rice_mill_name: str
    gst_number: str
    mill_address: str
    phone_number: int
    rice_mill_capacity: float
    rice_mill_id: Optional[int] = None


# Add Transporter
class TransporterBase(BaseModel):
    transporter_name: str
    transporter_phone_number: int
    transporter_id: Optional[int] = None


# Add Truck
class TruckBase(BaseModel):
    truck_number: str
    transport_id: int
    truck_id: Optional[int] = None


class RiceMillResponse(BaseModel):
    message: str
    data: AddRiceMillBase

    class Config:
        orm_mode = True


# Update / Delete
class UpdateRiceMillBase(BaseModel):
    gst_number: str
    rice_mill_name: str
    mill_address: str
    phone_number: int
    rice_mill_capacity: float


class TruckWithTransporter(BaseModel):
    truck_number: str
    transporter_name: str
    transport_id: int
    truck_id: Optional[int] = None


class SocietyBase(BaseModel):
    society_name: str
    distance_from_mill: int
    google_distance: int
    transporting_rate: int
    actual_distance: int
    society_id: Optional[int] = None


class AgreementBase(BaseModel):
    rice_mill_id: int
    agreement_number: str
    type_of_agreement: str
    lot_from: int
    lot_to: int
    agremennt_id: Optional[int] = None


class RiceMillWithAgreement(BaseModel):
    rice_mill_id: int
    agreement_number: str
    type_of_agreement: str
    lot_from: int
    lot_to: int
    rice_mill_name: str
    agremennt_id: Optional[int] = None


class WareHouseTransporting(BaseModel):
    ware_house_name: str
    ware_house_transporting_rate: int
    hamalirate: int
    ware_house_id: Optional[int] = None


class KochiaBase(BaseModel):
    rice_mill_name_id: int
    kochia_name: str
    kochia_phone_number: int
    kochia_id: Optional[int] = None


class KochiaWithRiceMill(BaseModel):
    rice_mill_name_id: int
    kochia_name: str
    kochia_phone_number: int
    rice_mill_name: str
    kochia_id: Optional[int] = None


class PartyBase(BaseModel):
    party_name: str
    party_phone_number: int
    party_id: Optional[int] = None


class BrokerBase(BaseModel):
    broker_name: str
    broker_phone_number: int
    broker_id: Optional[int] = None


class RiceMillData(BaseModel):
    rice_mill_data: List[AddRiceMillBase]
    agreement_data: List[AgreementBase]
    truck_data: List[TruckBase]
    society_data: List[SocietyBase]


class AddDoBase(BaseModel):
    select_mill_id: int
    date: date
    do_number: str
    select_argeement_id: int
    mota_weight: float
    mota_Bardana: float
    patla_weight: float
    patla_bardana: float
    sarna_weight: float
    sarna_bardana: float
    total_weight: float
    total_bardana: float
    society_name_id: int
    truck_number_id: int
    do_id: Optional[int] = None


class AddDoWithAddRiceMillAgreementSocietyTruck(BaseModel):
    select_mill_id: int
    date: date
    do_number: str
    select_argeement_id: int
    mota_weight: float
    mota_Bardana: float
    patla_weight: float
    patla_bardana: float
    sarna_weight: float
    sarna_bardana: float
    total_weight: float
    total_bardana: float
    society_name_id: int
    truck_number_id: int
    rice_mill_name: str
    agreement_number: str
    society_name: str
    truck_number: str
    do_id: Optional[int] = None
    created_at: Optional[datetime] = None
