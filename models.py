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
    kochia = relationship("Kochia", back_populates="addricemill")
    add_do = relationship("Add_Do", back_populates="addricemill")
    # frk = relationship("Frk", back_populates="addricemill")
    # other_awaks = relationship("Other_awak", back_populates="addricemill")
    # other_jawak = relationship("Other_jawak", back_populates="addricemill")
    # ricedeposite = relationship("Rice_deposite", back_populates="addricemill")
    # dopanding = relationship("Do_panding", back_populates="addricemill")
    # dhantransporting = relationship("Dhan_transporting", back_populates="addricemill")
    # brokenjawak = relationship("broken_jawak", back_populates="addricemill")
    # huskjawak = relationship("husk_jawak", back_populates="addricemill")
    # nakkhijawak = relationship("nakkhi_jawak", back_populates="addricemill")
    # branjawak = relationship("bran_jawak", back_populates="addricemill")
    # bhushi = relationship("bhushi", back_populates="addricemill")
    # paddysale = relationship("Paddy_sale", back_populates="addricemill")
    # ricepurchase = relationship("Rice_Purchase", back_populates="addricemill")
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
    add_do = relationship("Add_Do", back_populates="trucks")
    # frk = relationship("Frk", back_populates="trucks")
    # other_awaks = relationship("Other_awak", back_populates="trucks")
    # other_jawak = relationship("Other_jawak", back_populates="trucks")
    # ricedeposite = relationship("Rice_deposite", back_populates="trucks")
    # saudapatrak = relationship("Sauda_patrak", back_populates="trucks")
    # dhantransporting = relationship("Dhan_transporting", back_populates="trucks")
    # dalalidhaan = relationship("Dalali_dhaan", back_populates="trucks")
    # brokenjawak = relationship("broken_jawak", back_populates="trucks")
    # huskjawak = relationship("husk_jawak", back_populates="trucks")
    # nakkhijawak = relationship("nakkhi_jawak", back_populates="trucks")
    # branjawak = relationship("bran_jawak", back_populates="trucks")
    # bhushi = relationship("bhushi", back_populates="trucks")
    # paddysale = relationship("Paddy_sale", back_populates="trucks")
    # ricepurchase = relationship("Rice_Purchase", back_populates="trucks")
    # dhanawak = relationship("Dhan_Awak", back_populates="trucks")


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
    add_do = relationship("Add_Do", back_populates="society")
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
    user_id = Column(Integer, ForeignKey("users.id"))
    add_do = relationship("Add_Do", back_populates="agreement")


class ware_house_transporting(Base):
    __tablename__ = "warehousetransporting"

    ware_house_id = Column(Integer, primary_key=True, index=True)
    ware_house_name = Column(String(100))
    ware_house_transporting_rate = Column(Integer)
    hamalirate = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    # ricedeposite = relationship("Rice_deposite", back_populates="warehousetransporting")
    user_id = Column(Integer, ForeignKey("users.id"))


class Kochia(Base):
    __tablename__ = "kochia"

    kochia_id = Column(Integer, primary_key=True, index=True)
    rice_mill_name_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
    kochia_name = Column(String(50))
    kochia_phone_number = Column(Integer)
    addricemill = relationship("Add_Rice_Mill", back_populates="kochia")
    # dalalidhaan = relationship("Dalali_dhaan", back_populates="kochia")
    user_id = Column(Integer, ForeignKey("users.id"))


class Party(Base):
    __tablename__ = "party"

    party_id = Column(Integer, primary_key=True, index=True)
    party_name = Column(String(50))
    party_phone_number = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
    # other_awaks = relationship("Other_awak", back_populates="party")
    # other_jawak = relationship("Other_jawak", back_populates="party")
    # brokenjawak = relationship("broken_jawak", back_populates="party")
    # huskjawak = relationship("husk_jawak", back_populates="party")
    # nakkhijawak = relationship("nakkhi_jawak", back_populates="party")
    # branjawak = relationship("bran_jawak", back_populates="party")
    # bhushi = relationship("bhushi", back_populates="party")
    # paddysale = relationship("Paddy_sale", back_populates="party")
    # ricepurchase = relationship("Rice_Purchase", back_populates="party")


class brokers(Base):
    __tablename__ = "brokers"

    broker_id = Column(Integer, primary_key=True, index=True)
    broker_name = Column(String(50))
    broker_phone_number = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
    # brokenjawak = relationship("broken_jawak", back_populates="brokers")
    # huskjawak = relationship("husk_jawak", back_populates="brokers")
    # nakkhijawak = relationship("nakkhi_jawak", back_populates="brokers")
    # branjawak = relationship("bran_jawak", back_populates="brokers")
    # paddysale = relationship("Paddy_sale", back_populates="brokers")
    # ricepurchase = relationship("Rice_Purchase", back_populates="brokers")


class Add_Do(Base):
    __tablename__ = "addDo"

    do_id = Column(Integer, primary_key=True, index=True)
    select_mill_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
    date = Column(DATE)
    do_number = Column(String(15))
    select_argeement_id = Column(Integer, ForeignKey("agreement.agremennt_id"))
    mota_weight = Column(Float)
    mota_Bardana = Column(Float)
    patla_weight = Column(Float)
    patla_bardana = Column(Float)
    sarna_weight = Column(Float)
    sarna_bardana = Column(Float)
    total_weight = Column(Float)
    total_bardana = Column(Float)
    society_name_id = Column(Integer, ForeignKey("society.society_id"))
    truck_number_id = Column(Integer, ForeignKey("trucks.truck_id"))
    created_at = Column(DateTime, default=func.now())
    addricemill = relationship("Add_Rice_Mill", back_populates="add_do")
    agreement = relationship("Agreement", back_populates="add_do")
    society = relationship("Society", back_populates="add_do")
    trucks = relationship("Truck", back_populates="add_do")
    user_id = Column(Integer, ForeignKey("users.id"))
    # dopanding = relationship("Do_panding", back_populates="add_do")
    # dhantransporting = relationship("Dhan_transporting", back_populates="add_do")
    # dhanawak = relationship("Dhan_Awak", back_populates="add_do")
