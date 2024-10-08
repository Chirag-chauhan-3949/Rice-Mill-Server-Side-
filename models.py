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
    BIGINT,
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
    transporter = relationship("Transporter", back_populates="user")
    trucks = relationship("Truck", back_populates="user")
    society = relationship("Society", back_populates="user")
    # dhanawak = relationship("Dhan_Awak", back_populates="user")
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
    agreement = relationship("Agreement", back_populates="addricemill")
    # dhanawak = relationship("Dhan_Awak", back_populates="addricemill")


class Transporter(Base):
    __tablename__ = "transporter"

    transporter_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transporter_name = Column(String(50))
    transporter_phone_number = Column(BigInteger)
    created_at = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="transporter")
    trucks = relationship("Truck", back_populates="transporter")


class Truck(Base):
    __tablename__ = "trucks"

    truck_id = Column(Integer, primary_key=True, index=True)
    truck_number = Column(VARCHAR(50))
    transport_id = Column(Integer, ForeignKey("transporter.transporter_id"))
    transporter = relationship("Transporter", back_populates="trucks")
    created_at = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="trucks")


class Society(Base):
    __tablename__ = "society"

    society_id = Column(Integer, primary_key=True, index=True)
    society_name = Column(String(50))
    distance_from_mill = Column(Integer)
    google_distance = Column(Integer)
    transporting_rate = Column(Integer)
    actual_distance = Column(Integer)
    user = relationship("User", back_populates="society")
    created_at = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))
    # add_do = relationship("Add_Do", back_populates="society")
    # dhantransporting = relationship("Dhan_transporting", back_populates="society")
    # dhanawak = relationship("Dhan_Awak", back_populates="society")


class Agreement(Base):
    __tablename__ = "agreement"

    agremennt_id = Column(Integer, primary_key=True, index=True)
    rice_mill_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
    agreement_number = Column(VARCHAR(15))
    type_of_agreement = Column(String(50))
    lot_from = Column(Integer)
    lot_to = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    addricemill = relationship("Add_Rice_Mill", back_populates="agreement")
    # add_do = relationship("Add_Do", back_populates="agreement")
    user_id = Column(Integer, ForeignKey("users.id"))


class ware_house_transporting(Base):
    __tablename__ = "warehousetransporting"

    ware_house_id = Column(Integer, primary_key=True, index=True)
    ware_house_name = Column(String(100))
    ware_house_transporting_rate = Column(Integer)
    hamalirate = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    # ricedeposite = relationship("Rice_deposite", back_populates="warehousetransporting")
    user_id = Column(Integer, ForeignKey("users.id"))
