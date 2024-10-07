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


# class Truck(Base):
#     __tablename__ = "trucks"

#     truck_id = Column(Integer, primary_key=True, index=True)
#     truck_number = Column(VARCHAR(50))
#     transport_id = Column(Integer, ForeignKey("transporter.transporter_id"))
#     transporter = relationship("Transporter", back_populates="trucks")
#     created_at = Column(DateTime, default=func.now())
#     add_do = relationship("Add_Do", back_populates="trucks")
#     frk = relationship("Frk", back_populates="trucks")
#     other_awaks = relationship("Other_awak", back_populates="trucks")
#     other_jawak = relationship("Other_jawak", back_populates="trucks")
#     ricedeposite = relationship("Rice_deposite", back_populates="trucks")
#     saudapatrak = relationship("Sauda_patrak", back_populates="trucks")
#     dhantransporting = relationship("Dhan_transporting", back_populates="trucks")
#     dalalidhaan = relationship("Dalali_dhaan", back_populates="trucks")
#     brokenjawak = relationship("broken_jawak", back_populates="trucks")
#     huskjawak = relationship("husk_jawak", back_populates="trucks")
#     nakkhijawak = relationship("nakkhi_jawak", back_populates="trucks")
#     branjawak = relationship("bran_jawak", back_populates="trucks")
#     bhushi = relationship("bhushi", back_populates="trucks")
#     paddysale = relationship("Paddy_sale", back_populates="trucks")
#     ricepurchase = relationship("Rice_Purchase", back_populates="trucks")
#     dhanawak = relationship("Dhan_Awak", back_populates="trucks")
#     # user_id = Column(Integer, ForeignKey("users.id"))


# class Society(Base):
#     __tablename__ = "society"

#     society_id = Column(Integer, primary_key=True, index=True)
#     society_name = Column(String(50))
#     distance_from_mill = Column(Integer)
#     google_distance = Column(Integer)
#     transporting_rate = Column(Integer)
#     actual_distance = Column(Integer)
#     created_at = Column(DateTime, default=func.now())
#     add_do = relationship("Add_Do", back_populates="society")
#     dhantransporting = relationship("Dhan_transporting", back_populates="society")
#     dhanawak = relationship("Dhan_Awak", back_populates="society")
#     # user_id = Column(Integer, ForeignKey("users.id"))


# class Agreement(Base):
#     __tablename__ = "agreement"

#     agremennt_id = Column(Integer, primary_key=True, index=True)
#     rice_mill_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
#     agreement_number = Column(VARCHAR(15))
#     type_of_agreement = Column(String(50))
#     lot_from = Column(Integer)
#     lot_to = Column(Integer)
#     created_at = Column(DateTime, default=func.now())
#     addricemill = relationship("Add_Rice_Mill", back_populates="agreement")
#     add_do = relationship("Add_Do", back_populates="agreement")
#     # user_id = Column(Integer, ForeignKey("users.id"))


# class ware_house_transporting(Base):
#     __tablename__ = "warehousetransporting"

#     ware_house_id = Column(Integer, primary_key=True, index=True)
#     ware_house_name = Column(String(100))
#     ware_house_transporting_rate = Column(Integer)
#     hamalirate = Column(Integer)
#     created_at = Column(DateTime, default=func.now())
#     ricedeposite = relationship("Rice_deposite", back_populates="warehousetransporting")
#     # user_id = Column(Integer, ForeignKey("users.id"))


# class Kochia(Base):
#     __tablename__ = "kochia"

#     kochia_id = Column(Integer, primary_key=True, index=True)
#     rice_mill_name_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
#     kochia_name = Column(String(50))
#     kochia_phone_number = Column(Integer)
#     addricemill = relationship("Add_Rice_Mill", back_populates="kochia")
#     dalalidhaan = relationship("Dalali_dhaan", back_populates="kochia")
#     # user_id = Column(Integer, ForeignKey("users.id"))


# class Party(Base):
#     __tablename__ = "party"

#     party_id = Column(Integer, primary_key=True, index=True)
#     party_name = Column(String(50))
#     party_phone_number = Column(Integer)
#     # user_id = Column(Integer, ForeignKey("users.id"))

#     other_awaks = relationship("Other_awak", back_populates="party")
#     other_jawak = relationship("Other_jawak", back_populates="party")
#     brokenjawak = relationship("broken_jawak", back_populates="party")
#     huskjawak = relationship("husk_jawak", back_populates="party")
#     nakkhijawak = relationship("nakkhi_jawak", back_populates="party")
#     branjawak = relationship("bran_jawak", back_populates="party")
#     bhushi = relationship("bhushi", back_populates="party")
#     paddysale = relationship("Paddy_sale", back_populates="party")
#     ricepurchase = relationship("Rice_Purchase", back_populates="party")


# class brokers(Base):
#     __tablename__ = "brokers"

#     broker_id = Column(Integer, primary_key=True, index=True)
#     broker_name = Column(String(50))
#     broker_phone_number = Column(Integer)
#     brokenjawak = relationship("broken_jawak", back_populates="brokers")
#     huskjawak = relationship("husk_jawak", back_populates="brokers")
#     nakkhijawak = relationship("nakkhi_jawak", back_populates="brokers")
#     branjawak = relationship("bran_jawak", back_populates="brokers")
#     paddysale = relationship("Paddy_sale", back_populates="brokers")
#     ricepurchase = relationship("Rice_Purchase", back_populates="brokers")
#     # user_id = Column(Integer, ForeignKey("users.id"))


# class Add_Do(Base):
#     __tablename__ = "addDo"

#     do_id = Column(Integer, primary_key=True, index=True)
#     select_mill_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
#     date = Column(DATE)
#     do_number = Column(String(15))
#     select_argeement_id = Column(Integer, ForeignKey("agreement.agremennt_id"))
#     mota_weight = Column(Float)
#     mota_Bardana = Column(Float)
#     patla_weight = Column(Float)
#     patla_bardana = Column(Float)
#     sarna_weight = Column(Float)
#     sarna_bardana = Column(Float)
#     total_weight = Column(Float)
#     total_bardana = Column(Float)
#     society_name_id = Column(Integer, ForeignKey("society.society_id"))
#     truck_number_id = Column(Integer, ForeignKey("trucks.truck_id"))
#     created_at = Column(DateTime, default=func.now())
#     addricemill = relationship("Add_Rice_Mill", back_populates="add_do")
#     agreement = relationship("Agreement", back_populates="add_do")
#     society = relationship("Society", back_populates="add_do")
#     trucks = relationship("Truck", back_populates="add_do")
#     dopanding = relationship("Do_panding", back_populates="add_do")
#     dhantransporting = relationship("Dhan_transporting", back_populates="add_do")
#     dhanawak = relationship("Dhan_Awak", back_populates="add_do")
#     # user_id = Column(Integer, ForeignKey("users.id"))


# class Dhan_Awak(Base):
#     __tablename__ = "dhanawak"
#     # user_id = Column(Integer, ForeignKey("users.id"))
#     dhan_awak_id = Column(Integer, primary_key=True, index=True)
#     rst_number = Column(Integer)
#     rice_mill_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
#     date = Column(DATE)
#     do_id = Column(Integer, ForeignKey("addDo.do_id"))
#     society_id = Column(Integer, ForeignKey("society.society_id"))
#     dm_weight = Column(Float)
#     number_of_bags = Column(Float)
#     truck_number_id = Column(Integer, ForeignKey("trucks.truck_id"))
#     transporter_name_id = Column(Integer, ForeignKey("transporter.transporter_id"))
#     transporting_rate = Column(Integer)
#     transporting_total = Column(Integer)
#     jama_jute_22_23 = Column(Integer)
#     ek_bharti_21_22 = Column(Integer)
#     pds = Column(Integer)
#     miller_purana = Column(Float)
#     kisan = Column(Integer)
#     bardana_society = Column(Integer)
#     hdpe_22_23 = Column(Integer)
#     hdpe_21_22 = Column(Integer)
#     hdpe_21_22_one_use = Column(Integer)
#     total_bag_weight = Column(Float)
#     type_of_paddy = Column(String(50))
#     actual_paddy = Column(String(50))
#     mill_weight_quintals = Column(Float)
#     shortage = Column(Float)
#     bags_put_in_hopper = Column(Integer)
#     bags_put_in_stack = Column(Integer)
#     hopper_rice_mill_id = Column(String(100))
#     stack_location = Column(String(50))
#     created_at = Column(DateTime, default=func.now())
#     addricemill = relationship("Add_Rice_Mill", back_populates="dhanawak")
#     add_do = relationship("Add_Do", back_populates="dhanawak")
#     society = relationship("Society", back_populates="dhanawak")
#     trucks = relationship("Truck", back_populates="dhanawak")
#     transporter = relationship("Transporter", back_populates="dhanawak")
#     # paddysale = relationship("Paddy_sale", back_populates="dhanawak")
#     dhantransporting = relationship("Dhan_transporting", back_populates="dhanawak")
#     user = relationship("User", back_populates="dhanawak")


# class Other_awak(Base):
#     __tablename__ = "otherawak"

#     other_awak_id = Column(Integer, primary_key=True, index=True)
#     rst_number = Column(Integer)
#     date = Column(DATE)
#     party_id = Column(Integer, ForeignKey("party.party_id"))
#     truck_number_id = Column(Integer, ForeignKey("trucks.truck_id"))
#     material = Column(String(50))
#     nos = Column(Integer)
#     reason = Column(String(50))
#     weight = Column(Float)
#     rice_mill_name_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
#     created_at = Column(DateTime, default=func.now())
#     party = relationship("Party", back_populates="other_awaks")
#     trucks = relationship("Truck", back_populates="other_awaks")
#     addricemill = relationship("Add_Rice_Mill", back_populates="other_awaks")
#     # user_id = Column(Integer, ForeignKey("users.id"))


# class Rice_deposite(Base):
#     __tablename__ = "ricedeposite"

#     rice_depostie_id = Column(Integer, primary_key=True, index=True)
#     rst_number = Column(Integer)
#     date = Column(DATE)
#     lot_number = Column(Integer)
#     ware_house_id = Column(Integer, ForeignKey("warehousetransporting.ware_house_id"))
#     rice_mill_name_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
#     weight = Column(Integer)
#     truck_number_id = Column(Integer, ForeignKey("trucks.truck_id"))
#     bags = Column(Integer)
#     transporting_total = Column(Integer)
#     transporter_name_id = Column(Integer, ForeignKey("transporter.transporter_id"))
#     transporting_type = Column(String(50))
#     transporting_status = Column(String(50))
#     rate = Column(Integer)
#     variety = Column(String(50))
#     halting = Column(Integer)
#     rrga_wt = Column(Integer)
#     data_2022_23 = Column(Integer)
#     data_2021_22 = Column(Integer)
#     pds = Column(Integer)
#     old = Column(Integer)
#     amount = Column(Integer)
#     status = Column(String(50))
#     hamali = Column(Integer)
#     # user_id = Column(Integer, ForeignKey("users.id"))

#     created_at = Column(DateTime, default=func.now())
#     addricemill = relationship("Add_Rice_Mill", back_populates="ricedeposite")
#     warehousetransporting = relationship(
#         "ware_house_transporting", back_populates="ricedeposite"
#     )
#     trucks = relationship("Truck", back_populates="ricedeposite")
#     transporter = relationship("Transporter", back_populates="ricedeposite")


# class Dalali_dhaan(Base):
#     __tablename__ = "dalalidhaan"

#     dalali_dhaan_id = Column(Integer, primary_key=True, index=True)
#     # rst_number_id = Column(Integer, ForeignKey("dhanawak.dhan_awak_id"))
#     rst_number = Column(Integer)
#     date = Column(DATE)
#     kochia_id = Column(Integer, ForeignKey("kochia.kochia_id"))
#     vehicale_number_id = Column(Integer, ForeignKey("trucks.truck_id"))
#     white_sarna_bags = Column(Integer)
#     white_sarna_weight = Column(Integer)
#     ir_bags = Column(Integer)
#     ir_weight = Column(Integer)
#     rb_gold_bags = Column(Integer)
#     rb_gold_weight = Column(Integer)
#     sarna_bags = Column(Integer)
#     sarna_weight = Column(Integer)
#     sambha_new_bags = Column(Integer)
#     sambha_new_weight = Column(Integer)
#     paddy_type = Column(String(50))
#     total_bags = Column(Integer)
#     total_weight = Column(Integer)
#     hamali = Column(Integer)
#     plastic_bag = Column(Integer)
#     jute_bag = Column(Integer)
#     weight_less_kata_difference = Column(Float)
#     net_weight = Column(Float)
#     rate = Column(Integer)
#     amount = Column(Float)
#     created_at = Column(DateTime, default=func.now())
#     kochia = relationship("Kochia", back_populates="dalalidhaan")
#     trucks = relationship("Truck", back_populates="dalalidhaan")
#     # user_id = Column(Integer, ForeignKey("users.id"))


# class Frk(Base):
#     __tablename__ = "frk"

#     frk_id = Column(Integer, primary_key=True, index=True)
#     date = Column(DATE)
#     party = Column(String(50))
#     bags = Column(Integer)
#     weight = Column(Integer)
#     truck_number_id = Column(Integer, ForeignKey("trucks.truck_id"))
#     rice_mill_name_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
#     bill_number = Column(Integer)
#     rate = Column(Float)
#     batch_number = Column(Integer)
#     created_at = Column(DateTime, default=func.now())
#     addricemill = relationship("Add_Rice_Mill", back_populates="frk")
#     trucks = relationship("Truck", back_populates="frk")
#     # user_id = Column(Integer, ForeignKey("users.id"))


# class Sauda_patrak(Base):
#     __tablename__ = "saudapatrak"

#     sauda_patrak_id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(50))
#     address = Column(String(150))
#     vechicle_number_id = Column(Integer, ForeignKey("trucks.truck_id"))
#     paddy = Column(String(50))
#     bags = Column(Integer)
#     weight = Column(Float)
#     rate = Column(Float)
#     amount = Column(Float)
#     created_at = Column(DateTime, default=func.now())
#     trucks = relationship("Truck", back_populates="saudapatrak")
#     # user_id = Column(Integer, ForeignKey("users.id"))


# class Do_panding(Base):
#     __tablename__ = "dopanding"

#     do_panding_id = Column(Integer, primary_key=True, index=True)
#     rice_mill_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
#     do_number_id = Column(Integer, ForeignKey("addDo.do_id"))
#     date = Column(DATE)
#     mota = Column(VARCHAR(50))
#     patla = Column(VARCHAR(50))
#     sarna = Column(VARCHAR(50))
#     Total = Column(Integer)
#     created_at = Column(DateTime, default=func.now())
#     addricemill = relationship("Add_Rice_Mill", back_populates="dopanding")
#     add_do = relationship("Add_Do", back_populates="dopanding")
#     # user_id = Column(Integer, ForeignKey("users.id"))


# class Dhan_transporting(Base):
#     __tablename__ = "dhantransporting"

#     Dhan_transporting_id = Column(Integer, primary_key=True, index=True)
#     rst_number = Column(Integer)
#     date = Column(DATE)
#     do_number_id = Column(Integer, ForeignKey("addDo.do_id"))
#     society_name_id = Column(Integer, ForeignKey("society.society_id"))
#     rice_mill_name_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
#     dm_weight = Column(Integer)
#     truck_number_id = Column(Integer, ForeignKey("trucks.truck_id"))
#     transporting_rate = Column(Integer)
#     numbers_of_bags = Column(Integer)
#     transporting_total = Column(Integer)
#     transporter_name_id = Column(Integer, ForeignKey("transporter.transporter_id"))
#     status = Column(String(50))
#     total_pending = Column(Integer)
#     total_paid = Column(Integer)
#     created_at = Column(DateTime, default=func.now())
#     # user_id = Column(Integer, ForeignKey("users.id"))

#     dhan_awak_id = Column(
#         Integer, ForeignKey("dhanawak.dhan_awak_id")
#     )  # Foreign key added
#     # dhanawak = relationship("Dhan_Awak", back_populates="dhantransporting")
#     addricemill = relationship("Add_Rice_Mill", back_populates="dhantransporting")
#     society = relationship("Society", back_populates="dhantransporting")
#     add_do = relationship("Add_Do", back_populates="dhantransporting")
#     trucks = relationship("Truck", back_populates="dhantransporting")
#     transporter = relationship("Transporter", back_populates="dhantransporting")
#     dhanawak = relationship("Dhan_Awak", back_populates="dhantransporting")


# class Other_jawak(Base):
#     __tablename__ = "other_jawak"

#     other_jawak_id = Column(Integer, primary_key=True, index=True)
#     rst_number = Column(Integer)
#     date = Column(DATE)
#     party_id = Column(Integer, ForeignKey("party.party_id"))
#     truck_number_id = Column(Integer, ForeignKey("trucks.truck_id"))
#     material = Column(String(50))
#     nos = Column(Integer)
#     reason = Column(String(50))
#     weight = Column(Float)
#     rice_mill_name_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
#     created_at = Column(DateTime, default=func.now())
#     party = relationship("Party", back_populates="other_jawak")
#     trucks = relationship("Truck", back_populates="other_jawak")
#     addricemill = relationship("Add_Rice_Mill", back_populates="other_jawak")


# class broken_jawak(Base):
#     __tablename__ = "brokenjawak"

#     broken_jawak_id = Column(Integer, primary_key=True, index=True)
#     rst_number = Column(Integer)
#     date = Column(DATE)
#     party_id = Column(Integer, ForeignKey("party.party_id"))
#     rice_mill_name_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
#     broker = Column(Integer, ForeignKey("brokers.broker_id"))
#     brokerage_percentage = Column(Float)
#     weight = Column(Float)
#     rate = Column(Integer)
#     number_of_bags = Column(Integer)
#     truck_number_id = Column(Integer, ForeignKey("trucks.truck_id"))
#     total = Column(BIGINT)
#     brokerage = Column(Float)
#     net_recievable = Column(Float)
#     loading_date = Column(DATE)
#     recieved_date = Column(DATE)
#     payment_recieved = Column(Integer)
#     number_of_days = Column(Integer)
#     payment_difference = Column(Float)
#     remarks = Column(String(100))
#     created_at = Column(DateTime, default=func.now())
#     party = relationship("Party", back_populates="brokenjawak")
#     addricemill = relationship("Add_Rice_Mill", back_populates="brokenjawak")
#     brokers = relationship("brokers", back_populates="brokenjawak")
#     trucks = relationship("Truck", back_populates="brokenjawak")


# class husk_jawak(Base):
#     __tablename__ = "huskjawak"

#     husk_jawak_id = Column(Integer, primary_key=True, index=True)
#     rst_number = Column(Integer)
#     date = Column(DATE)
#     party_id = Column(Integer, ForeignKey("party.party_id"))
#     rice_mill_name_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
#     remarks = Column(String(100))
#     broker = Column(Integer, ForeignKey("brokers.broker_id"))
#     brokerage_percentage = Column(Float)
#     weight = Column(Float)
#     rate = Column(Integer)
#     number_of_bags = Column(Integer)
#     truck_number_id = Column(Integer, ForeignKey("trucks.truck_id"))
#     total = Column(BIGINT)
#     brokerage = Column(Float)
#     net_receivable = Column(Float)
#     received_date = Column(DATE)
#     loading_date = Column(DATE)
#     payment_received = Column(Integer)
#     number_of_days = Column(Integer)
#     payment_difference = Column(Float)
#     created_at = Column(DateTime, default=func.now())

#     party = relationship("Party", back_populates="huskjawak")
#     addricemill = relationship("Add_Rice_Mill", back_populates="huskjawak")
#     brokers = relationship("brokers", back_populates="huskjawak")
#     trucks = relationship("Truck", back_populates="huskjawak")


# class nakkhi_jawak(Base):
#     __tablename__ = "nakkhijawak"

#     nakkhi_jawak_id = Column(Integer, primary_key=True, index=True)
#     rst_number = Column(Integer)
#     date = Column(DATE)
#     party_id = Column(Integer, ForeignKey("party.party_id"))
#     rice_mill_name_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
#     broker = Column(Integer, ForeignKey("brokers.broker_id"))
#     brokerage_percent = Column(Integer)
#     weight = Column(Float)
#     rate = Column(Integer)
#     number_of_bags = Column(Integer)
#     truck_number_id = Column(Integer, ForeignKey("trucks.truck_id"))
#     brokerage = Column(Float)
#     total = Column(BIGINT)
#     net_recievable = Column(Float)
#     loading_date = Column(DATE)
#     recieved_date = Column(DATE)
#     payment_recieved = Column(Integer)
#     number_of_days = Column(Integer)
#     payment_difference = Column(Integer)
#     remarks = Column(String(100))
#     created_at = Column(DateTime, default=func.now())

#     party = relationship("Party", back_populates="nakkhijawak")
#     addricemill = relationship("Add_Rice_Mill", back_populates="nakkhijawak")
#     brokers = relationship("brokers", back_populates="nakkhijawak")
#     trucks = relationship("Truck", back_populates="nakkhijawak")


# class bran_jawak(Base):
#     __tablename__ = "branjawak"

#     bran_jawak_id = Column(Integer, primary_key=True, index=True)
#     rst_number = Column(Integer)
#     date = Column(DATE)
#     party_id = Column(Integer, ForeignKey("party.party_id"))
#     rice_mill_name_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
#     broker = Column(Integer, ForeignKey("brokers.broker_id"))
#     brokerage_percentage = Column(Float)
#     weight = Column(Float)
#     rate = Column(Integer)
#     number_of_bags = Column(Integer)
#     truck_number_id = Column(Integer, ForeignKey("trucks.truck_id"))
#     total = Column(Integer)
#     brokerage = Column(Float)
#     net_receivable = Column(Float)
#     payment_received = Column(Integer)
#     payment_difference = Column(Integer)
#     remarks = Column(String(100))
#     oil = Column(Integer)
#     created_at = Column(DateTime, default=func.now())

#     party = relationship("Party", back_populates="branjawak")
#     addricemill = relationship("Add_Rice_Mill", back_populates="branjawak")
#     brokers = relationship("brokers", back_populates="branjawak")
#     trucks = relationship("Truck", back_populates="branjawak")


# class bhushi(Base):
#     __tablename__ = "bhushi"

#     bhushi_id = Column(Integer, primary_key=True, index=True)
#     rst_number = Column(Integer)
#     date = Column(DATE)
#     party_id = Column(Integer, ForeignKey("party.party_id"))
#     rice_mill_name_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
#     number_of_bags = Column(Integer)
#     weight = Column(Float)
#     truck_number_id = Column(Integer, ForeignKey("trucks.truck_id"))
#     rate = Column(Integer)
#     amount = Column(Integer)
#     created_at = Column(DateTime, default=func.now())

#     party = relationship("Party", back_populates="bhushi")
#     addricemill = relationship("Add_Rice_Mill", back_populates="bhushi")
#     trucks = relationship("Truck", back_populates="bhushi")


# class Paddy_sale(Base):
#     __tablename__ = "paddysale"

#     paddy_sale_id = Column(Integer, primary_key=True, index=True)
#     # rst_number_id = Column(Integer, ForeignKey("dhanawak.dhan_awak_id"))
#     rst_number_id = Column(Integer)
#     rice_mill_name_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
#     date = Column(DATE)
#     party_id = Column(Integer, ForeignKey("party.party_id"))
#     broker = Column(Integer, ForeignKey("brokers.broker_id"))
#     loading_form_address = Column(String(50))
#     truck_number_id = Column(Integer, ForeignKey("trucks.truck_id"))
#     paddy_name = Column(String(50))
#     weight = Column(Integer)
#     party_weight = Column(Integer)
#     bags = Column(Integer)
#     rate = Column(Integer)
#     ammount = Column(BIGINT)
#     plastic = Column(Integer)
#     joot_old = Column(Integer)
#     joot_23_24 = Column(Integer)
#     joot_22_23 = Column(Integer)
#     average_bag_wt = Column(Float)
#     created_at = Column(DateTime, default=func.now())

#     # dhanawak = relationship("Dhan_Awak", back_populates="paddysale")
#     party = relationship("Party", back_populates="paddysale")
#     brokers = relationship("brokers", back_populates="paddysale")
#     trucks = relationship("Truck", back_populates="paddysale")
#     addricemill = relationship("Add_Rice_Mill", back_populates="paddysale")


# # ___________________________________________________________


# class Rice_Purchase(Base):
#     __tablename__ = "ricepurchase"

#     rice_purchase_id = Column(Integer, primary_key=True, index=True)
#     rst_number = Column(Integer)
#     date = Column(DATE)
#     broker_id = Column(Integer, ForeignKey("brokers.broker_id"))
#     truck_number_id = Column(Integer, ForeignKey("trucks.truck_id"))
#     bags = Column(Integer)
#     mill_weight = Column(Float)
#     party_weight = Column(Float)
#     bill_to_rice_mill = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
#     party_id = Column(Integer, ForeignKey("party.party_id"))
#     created_at = Column(DateTime, default=func.now())
#     brokers = relationship("brokers", back_populates="ricepurchase")
#     trucks = relationship("Truck", back_populates="ricepurchase")
#     addricemill = relationship("Add_Rice_Mill", back_populates="ricepurchase")
#     party = relationship("Party", back_populates="ricepurchase")


# class CashInCashOut(Base):
#     __tablename__ = "cashincashout"

#     cash_detail = Column(Integer, primary_key=True, index=True)
#     cash = Column(String(50))
#     paddy_purchase = Column(Float)
#     paddy_in = Column(Float)
#     paddy_sale = Column(Float)
#     paddy_processed = Column(Float)
#     paddy_stacked = Column(Float)
#     rice_purchase = Column(Float)
#     rice_depatched = Column(Float)
#     broken_sold = Column(Float)
#     bran_sold = Column(Float)
#     nakkhi_sold = Column(Float)
#     bhusa_sold = Column(Float)
#     transporting_bill = Column(Float)
#     bardana = Column(Float)
#     total = Column(Float)
#     created_at = Column(DateTime, default=func.now())


# # class Society_Name(Base):
# #     __tablename__ = "societyName"

# #     society_id = Column(Integer, primary_key=True, index=True)
# #     society_name = Column(String(50))


# class Lot_number_master(Base):
#     __tablename__ = "lotnumbermaster"

#     lot_number_master_id = Column(Integer, primary_key=True, index=True)
#     rice_mill_name_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
#     lot_number = Column(Integer)
#     created_at = Column(DateTime, default=func.now())


# class Dhan_rice_societies_rate(Base):
#     __tablename__ = "dhanricesocietiesrate"

#     dhan_rice_societies_rate_id = Column(Integer, primary_key=True, index=True)
#     society_name_id = Column(Integer, ForeignKey("society.society_id"))
#     distance = Column(Float)
#     new = Column(Integer)
#     created_at = Column(DateTime, default=func.now())


# class Mohan_food_paddy(Base):
#     __tablename__ = "mohanfoodpaddy"

#     mohan_food_paddy_id = Column(Integer, primary_key=True, index=True)
#     date = Column(DATE)
#     do_number_id = Column(Integer, ForeignKey("addDo.do_id"))
#     samiti = Column(String(50))
#     rice_mill_name_id = Column(Integer, ForeignKey("addricemill.rice_mill_id"))
#     weight = Column(Integer)
#     vehicle_number_id = Column(Integer, ForeignKey("trucks.truck_id"))
#     bags = Column(Integer)
#     transporting_total = Column(Integer)
#     transporter_name_id = Column(Integer, ForeignKey("transporter.transporter_id"))
#     transporter_type = Column(String(50))
#     transporter_status = Column(String(50))
#     rate = Column(Integer)
#     type_1 = Column(String(50))
#     years_22_23 = Column(Integer)
#     years_21_22 = Column(Integer)
#     hdpe_one = Column(Integer)
#     hdpe_new = Column(Integer)
#     purana = Column(Integer)
#     pds = Column(Integer)
#     created_at = Column(DateTime, default=func.now())


# class Transporter_master(Base):
#     __tablename__ = "transportermaster"

#     transporter_master_id = Column(Integer, primary_key=True, index=True)
#     vehicle_number_id = Column(Integer, ForeignKey("trucks.truck_id"))
#     name = Column(String(50))
#     phone_number = Column(BigInteger)
#     date = Column(DATE)
#     transporter_name_id = Column(Integer, ForeignKey("transporter.transporter_id"))
#     advance_payment = Column(Integer)
#     created_at = Column(DateTime, default=func.now())
