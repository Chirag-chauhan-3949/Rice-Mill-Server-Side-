from sqlalchemy import (
    JSON,
    Column,
    Integer,
    String,
    DateTime,
    func,
    VARCHAR,
    ForeignKey,
    Float,
    BigInteger,
    DATE,
    Enum,
)
from database import Base
from sqlalchemy.orm import relationship
import enum


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=False)
    role = Column(String(50), default="admin")
    created_at = Column(DateTime, default=func.now())
    role_create = relationship("Role", back_populates="user")
    addricemill = relationship("Add_Rice_Mill", back_populates="user")
    dhanawak = relationship("Dhan_Awak", back_populates="user")
    # add_user = relationship("Add_User", back_populates="user")


class Role(Base):
    __tablename__ = "role_create"
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    user = relationship("User", back_populates="role_create")
    created_at = Column(DateTime, default=func.now())


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, index=True)
    permissions = Column(JSON)


class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"
    token = Column(String(500), primary_key=True)


class Add_Rice_Mill(Base):
    __tablename__ = "addricemill"

    rice_mill_id = Column(Integer, primary_key=True, index=True)
    rice_mill_name = Column(String(50), index=True)
    gst_number = Column(VARCHAR(50))
    mill_address = Column(String(200))
    phone_number = Column(BigInteger)
    rice_mill_capacity = Column(Float)
    created_at = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="addricemill")
    dhanawak = relationship("Dhan_Awak", back_populates="addricemill")


class Dhan_Awak(Base):
    __tablename__ = "dhanawak"

    dhan_awak_id = Column(Integer, primary_key=True, index=True)
    rst_number = Column(Integer)
    rice_mill_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
    date = Column(DATE)
    do_id = Column(Integer)
    society_id = Column(Integer)
    dm_weight = Column(Float)
    number_of_bags = Column(Float)
    truck_number_id = Column(Integer)
    transporter_name_id = Column(Integer)
    transporting_rate = Column(Integer)
    transporting_total = Column(Integer)
    jama_jute_22_23 = Column(Integer)
    ek_bharti_21_22 = Column(Integer)
    pds = Column(Integer)
    miller_purana = Column(Float)
    kisan = Column(Integer)
    bardana_society = Column(Integer)
    hdpe_22_23 = Column(Integer)
    hdpe_21_22 = Column(Integer)
    hdpe_21_22_one_use = Column(Integer)
    total_bag_weight = Column(Float)
    type_of_paddy = Column(String(50))
    actual_paddy = Column(String(50))
    mill_weight_quintals = Column(Float)
    shortage = Column(Float)
    bags_put_in_hopper = Column(Integer)
    bags_put_in_stack = Column(Integer)
    hopper_rice_mill_id = Column(String(100))
    stack_location = Column(String(50))
    created_at = Column(DateTime, default=func.now())
    addricemill = relationship("Add_Rice_Mill", back_populates="dhanawak")
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="dhanawak")
