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
