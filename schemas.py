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


class RoleBase(BaseModel):
    role_name: str


class AddNewUserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class AddNewUserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: str

    class Config:
        orm_mode = True
