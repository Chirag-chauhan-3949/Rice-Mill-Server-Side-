from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, String
from typing import Annotated, List, Optional
from enum import Enum


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


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
