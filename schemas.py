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


# class DhanAwakBase(BaseModel):
#     rst_number: int
#     rice_mill_id: int
#     date: date
#     do_id: int
#     society_id: int
#     dm_weight: float
#     number_of_bags: float
#     truck_number_id: int
#     transporter_name_id: int
#     transporting_rate: int
#     transporting_total: int
#     jama_jute_22_23: int
#     ek_bharti_21_22: int
#     pds: int
#     miller_purana: float
#     kisan: int
#     bardana_society: int
#     hdpe_22_23: int
#     hdpe_21_22: int
#     hdpe_21_22_one_use: int
#     total_bag_weight: float
#     type_of_paddy: str
#     actual_paddy: str
#     mill_weight_quintals: float
#     shortage: float
#     bags_put_in_hopper: int
#     bags_put_in_stack: int
#     hopper_rice_mill_id: str
#     stack_location: str


# class UpdateDhanAwakBase(BaseModel):
#     rst_number: int
#     rice_mill_id: int
#     date: date
#     do_id: int
#     society_id: int
#     dm_weight: float
#     number_of_bags: float
#     truck_number_id: int
#     transporter_name_id: int
#     transporting_rate: int
#     transporting_total: int
#     jama_jute_22_23: int
#     ek_bharti_21_22: int
#     pds: int
#     miller_purana: float
#     kisan: int
#     bardana_society: int
#     hdpe_22_23: int
#     hdpe_21_22: int
#     hdpe_21_22_one_use: int
#     total_bag_weight: float
#     type_of_paddy: str
#     actual_paddy: str
#     mill_weight_quintals: float
#     shortage: float
#     bags_put_in_hopper: int
#     bags_put_in_stack: int
#     hopper_rice_mill_id: str
#     stack_location: str


# class TruckWithTransporter(BaseModel):
#     truck_number: str
#     transporter_name: str
#     transport_id: int
#     truck_id: Optional[int] = None


# class SocietyBase(BaseModel):
#     society_name: str
#     distance_from_mill: int
#     google_distance: int
#     transporting_rate: int
#     actual_distance: int
#     society_id: Optional[int] = None


# class AgreementBase(BaseModel):
#     rice_mill_id: int
#     agreement_number: str
#     type_of_agreement: str
#     lot_from: int
#     lot_to: int
#     agremennt_id: Optional[int] = None


# class RiceMillWithAgreement(BaseModel):
#     rice_mill_id: int
#     agreement_number: str
#     type_of_agreement: str
#     lot_from: int
#     lot_to: int
#     rice_mill_name: str
#     agremennt_id: Optional[int] = None


# class WareHouseTransporting(BaseModel):
#     ware_house_name: str
#     ware_house_transporting_rate: int
#     hamalirate: int
#     ware_house_id: Optional[int] = None


# # ___________________________________________________________


# class RiceMillData(BaseModel):
#     rice_mill_data: List[AddRiceMillBase]
#     agreement_data: List[AgreementBase]
#     truck_data: List[TruckBase]
#     society_data: List[SocietyBase]


# class AddDoData(BaseModel):
#     rice_mill_data: List[AddRiceMillBase]
#     agreement_data: List[AgreementBase]


# class SocietyTransportingRate(BaseModel):
#     society_transporting: List[SocietyBase]


# class KochiaBase(BaseModel):
#     rice_mill_name_id: int
#     kochia_name: str
#     kochia_phone_number: int
#     kochia_id: Optional[int] = None


# class KochiaWithRiceMill(BaseModel):
#     rice_mill_name_id: int
#     kochia_name: str
#     kochia_phone_number: int
#     rice_mill_name: str
#     kochia_id: Optional[int] = None


# class PartyBase(BaseModel):
#     party_name: str
#     party_phone_number: int
#     party_id: Optional[int] = None


# class BrokerBase(BaseModel):
#     broker_name: str
#     broker_phone_number: int
#     broker_id: Optional[int] = None


# class AddDoBase(BaseModel):
#     select_mill_id: int
#     date: date
#     do_number: str
#     select_argeement_id: int
#     mota_weight: float
#     mota_Bardana: float
#     patla_weight: float
#     patla_bardana: float
#     sarna_weight: float
#     sarna_bardana: float
#     total_weight: float
#     total_bardana: float
#     society_name_id: int
#     truck_number_id: int
#     do_id: Optional[int] = None


# class AddDoWithAddRiceMillAgreementSocietyTruck(BaseModel):
#     select_mill_id: int
#     date: date
#     do_number: str
#     select_argeement_id: int
#     mota_weight: float
#     mota_Bardana: float
#     patla_weight: float
#     patla_bardana: float
#     sarna_weight: float
#     sarna_bardana: float
#     total_weight: float
#     total_bardana: float
#     society_name_id: int
#     truck_number_id: int
#     rice_mill_name: str
#     agreement_number: str
#     society_name: str
#     truck_number: str
#     do_id: Optional[int] = None
#     created_at: Optional[datetime] = None


# # ___________________________________________________________
# class DhanAwakRiceDoNumber(BaseModel):
#     rice_mill_data: List[AddRiceMillBase]
#     do_number_data: List[AddDoBase]


# class DhanAwakRiceDoSocietyTruckTransporter(BaseModel):
#     rice_mill_data: List[AddRiceMillBase]
#     do_number_data: List[AddDoBase]
#     society_data: List[SocietyBase]
#     truck_data: List[TruckBase]
#     transporter_data: List[TransporterBase]


# class DhanAwakTruckTransporter(BaseModel):
#     truck_data: List[TruckBase]
#     transporter_data: List[TransporterBase]


# class DhanAwakBase(BaseModel):
#     rst_number: int
#     rice_mill_id: int
#     date: date
#     do_id: int
#     society_id: int
#     dm_weight: float
#     number_of_bags: float
#     truck_number_id: int
#     transporter_name_id: int
#     transporting_rate: int
#     transporting_total: int
#     jama_jute_22_23: int
#     ek_bharti_21_22: int
#     pds: int
#     miller_purana: float
#     kisan: int
#     bardana_society: int
#     hdpe_22_23: int
#     hdpe_21_22: int
#     hdpe_21_22_one_use: int
#     total_bag_weight: float
#     type_of_paddy: str
#     actual_paddy: str
#     mill_weight_quintals: float
#     shortage: float
#     bags_put_in_hopper: int
#     bags_put_in_stack: int
#     hopper_rice_mill_id: str
#     stack_location: str
#     dhan_awak_id: Optional[int] = None


# class DhanAwakWithRiceDoSocietyTruckTransport(BaseModel):
#     rst_number: int
#     rice_mill_id: int
#     date: date
#     do_id: int
#     society_id: int
#     dm_weight: int
#     number_of_bags: float
#     truck_number_id: int
#     transporter_name_id: int
#     transporting_rate: int
#     transporting_total: int
#     jama_jute_22_23: int
#     ek_bharti_21_22: int
#     pds: int
#     miller_purana: int
#     kisan: int
#     bardana_society: int
#     hdpe_22_23: int
#     hdpe_21_22: int
#     hdpe_21_22_one_use: int
#     total_bag_weight: float
#     type_of_paddy: str
#     actual_paddy: str
#     mill_weight_quintals: int
#     shortage: float
#     bags_put_in_hopper: int
#     bags_put_in_stack: int
#     hopper_rice_mill_id: str
#     stack_location: str
#     dhan_awak_id: Optional[int] = None
#     rice_mill_name: str
#     do_number: str
#     society_name: str
#     truck_number: str
#     transporter_name: str


# class RiceMillTruckNumberPartyBrokers(BaseModel):
#     rice_mill_data: List[AddRiceMillBase]
#     truck_data: List[TruckBase]
#     party_data: List[PartyBase]
#     brokers_data: List[BrokerBase]


# class OtherAwakBase(BaseModel):
#     rst_number: int
#     date: date
#     rice_mill_name_id: int
#     party_id: int
#     truck_number_id: int
#     material: str
#     nos: int
#     reason: str
#     weight: float
#     other_awak_id: Optional[int] = None


# class OtherAwakWithPartyRiceTruck(BaseModel):
#     rst_number: int
#     date: date
#     rice_mill_name_id: int
#     party_id: int
#     truck_number_id: int
#     material: str
#     nos: int
#     reason: str
#     weight: float
#     party_name: str
#     rice_mill_name: str
#     truck_number: str
#     other_awak_id: Optional[int] = None


# # ___________________________________________________________
# class wareHousetrasportingrate(BaseModel):
#     ware_house_transporting_rate: int
#     hamalirate: int


# class RiceDepositRiceTruckTransport(BaseModel):
#     rice_mill_data: List[AddRiceMillBase]
#     truck_data: List[TruckBase]
#     transporter_data: List[TransporterBase]
#     ware_house_data: List[WareHouseTransporting]


# class RiceDepositeBase(BaseModel):
#     rst_number: int
#     date: date
#     lot_number: int
#     ware_house_id: int
#     rice_mill_name_id: int
#     weight: int
#     truck_number_id: int
#     bags: int
#     transporting_total: int
#     transporter_name_id: int
#     transporting_type: str
#     transporting_status: str
#     rate: int
#     variety: str
#     halting: int
#     rrga_wt: int
#     data_2022_23: int
#     data_2021_22: int
#     pds: int
#     old: int
#     amount: int
#     status: str
#     hamali: int
#     rice_depostie_id: Optional[int] = None


# class RiceDepositWithRiceWareTruckTransporter(BaseModel):
#     rst_number: int
#     date: date
#     lot_number: int
#     ware_house_id: int
#     rice_mill_name_id: int
#     weight: int
#     truck_number_id: int
#     bags: int
#     transporting_total: int
#     transporter_name_id: int
#     transporting_type: str
#     transporting_status: str
#     rate: int
#     variety: str
#     halting: int
#     rrga_wt: int
#     data_2022_23: int
#     data_2021_22: int
#     pds: int
#     old: int
#     amount: int
#     status: str
#     hamali: int
#     rice_mill_name: str
#     truck_number: str
#     ware_house_name: str
#     transporter_name: str
#     rice_depostie_id: Optional[int] = None


# # ___________________________________________________________


# class DalaliDhaanBase(BaseModel):
#     rst_number: int
#     date: date
#     kochia_id: int
#     vehicale_number_id: int
#     white_sarna_bags: int
#     white_sarna_weight: int
#     ir_bags: int
#     ir_weight: int
#     rb_gold_bags: int
#     rb_gold_weight: int
#     sarna_bags: int
#     sarna_weight: int
#     sambha_new_bags: int
#     sambha_new_weight: int
#     paddy_type: str
#     total_bags: int
#     total_weight: int
#     hamali: int
#     plastic_bag: int
#     jute_bag: int
#     weight_less_kata_difference: float
#     net_weight: float
#     rate: int
#     amount: float
#     dalali_dhaan_id: Optional[int] = None


# class DalaliDhaanWithKochia(BaseModel):
#     rst_number: int
#     date: date
#     kochia_id: int
#     vehicale_number_id: int
#     white_sarna_bags: int
#     white_sarna_weight: int
#     ir_bags: int
#     ir_weight: int
#     rb_gold_bags: int
#     rb_gold_weight: int
#     sarna_bags: int
#     sarna_weight: int
#     sambha_new_bags: int
#     sambha_new_weight: int
#     paddy_type: str
#     total_bags: int
#     total_weight: int
#     hamali: int
#     plastic_bag: int
#     jute_bag: int
#     weight_less_kata_difference: float
#     net_weight: float
#     rate: int
#     amount: float
#     kochia_name: str
#     truck_number: str
#     dalali_dhaan_id: Optional[int] = None


# # ___________________________________________________________


# class FrkBase(BaseModel):
#     date: date
#     party: str
#     bags: int
#     weight: int
#     truck_number_id: int
#     rice_mill_name_id: int
#     bill_number: int
#     rate: float
#     batch_number: int
#     frk_id: Optional[int] = None


# class FrkWithRiceTruck(BaseModel):
#     date: date
#     party: str
#     bags: int
#     weight: int
#     truck_number_id: int
#     rice_mill_name_id: int
#     bill_number: int
#     rate: float
#     batch_number: int
#     rice_mill_name: str
#     truck_number: str
#     frk_id: Optional[int] = None


# class SaudaPatrakBase(BaseModel):
#     name: str
#     address: str
#     vechicle_number_id: int
#     paddy: str
#     bags: int
#     weight: float
#     rate: float
#     amount: float
#     sauda_patrak_id: Optional[int] = None


# class SaudaPatrakWithTruckNumber(BaseModel):
#     name: str
#     address: str
#     vechicle_number_id: int
#     paddy: str
#     bags: int
#     weight: float
#     rate: float
#     amount: float
#     truck_number: str
#     sauda_patrak_id: Optional[int] = None


# # ___________________________________________________________


# class DoPendingBase(BaseModel):
#     rice_mill_id: int
#     do_number_id: int
#     date: date
#     mota: str
#     patla: str
#     sarna: str
#     Total: int
#     do_panding_id: Optional[int] = None


# class DoPendingWithRiceAddDo(BaseModel):
#     rice_mill_id: int
#     do_number_id: int
#     date: date
#     mota: str
#     patla: str
#     sarna: str
#     Total: int
#     rice_mill_name: str
#     do_number: str
#     do_panding_id: Optional[int] = None


# # ___________________________________________________________
# class RiceRstSocietyDoTruckTransporter(BaseModel):
#     rice_mill_data: List[AddRiceMillBase]
#     rst_data: List[DhanAwakBase]
#     society_data: List[SocietyBase]
#     do_number_data: List[AddDoBase]
#     truck_data: List[TruckBase]
#     transporter_data: List[TransporterBase]


# class RiceMillRstNumber(BaseModel):
#     rice_mill_data: List[AddRiceMillBase]
#     do_number_data: List[AddDoBase]
#     rst_data: List[DhanAwakBase]


# class DhanTransportingBase(BaseModel):
#     rst_number: int
#     date: date
#     do_number_id: int
#     society_name_id: int
#     rice_mill_name_id: int
#     dm_weight: int
#     truck_number_id: int
#     transporting_rate: int
#     numbers_of_bags: int
#     transporting_total: int
#     transporter_name_id: int
#     status: str
#     total_pending: int
#     total_paid: int
#     Dhan_transporting_id: Optional[int] = None


# class DhanTransportingWithRiceDoTruckTransport(BaseModel):
#     rst_number: int
#     date: date
#     do_number_id: int
#     society_name_id: int
#     rice_mill_name_id: int
#     dm_weight: int
#     truck_number_id: int
#     transporting_rate: int
#     numbers_of_bags: int
#     transporting_total: int
#     transporter_name_id: int
#     status: str
#     total_pending: int
#     total_paid: int
#     rice_mill_name: str
#     society_name: str
#     do_number: str
#     truck_number: str
#     transporter_name: str
#     Dhan_transporting_id: Optional[int] = None


# # ___________________________________________________________
# class OtherJawakBase(BaseModel):
#     rst_number: int
#     date: date
#     party_id: int
#     truck_number_id: int
#     material: str
#     nos: int
#     reason: str
#     weight: float
#     rice_mill_name_id: int
#     other_jawak_id: Optional[int] = None


# class OtherJawakWithPatyTrucksRice(BaseModel):
#     rst_number: int
#     date: date
#     party_id: int
#     truck_number_id: int
#     material: str
#     nos: int
#     reason: str
#     weight: float
#     rice_mill_name_id: int
#     party_name: str
#     rice_mill_name: str
#     truck_number: str
#     other_jawak_id: Optional[int] = None


# class BrokenJawak(BaseModel):
#     rst_number: int
#     date: date
#     party_id: int
#     rice_mill_name_id: int
#     broker: int
#     brokerage_percentage: float
#     weight: float
#     rate: int
#     number_of_bags: int
#     truck_number_id: int
#     total: int
#     brokerage: float
#     net_recievable: float
#     loading_date: date
#     recieved_date: date
#     payment_recieved: int
#     number_of_days: int
#     payment_difference: float
#     remarks: str
#     broken_jawak_id: Optional[int] = None


# class BrokernJawakWithRicePartyBrokerTruck(BaseModel):
#     rst_number: int
#     date: date
#     party_id: int
#     rice_mill_name_id: int
#     broker: int
#     brokerage_percentage: float
#     weight: float
#     rate: int
#     number_of_bags: int
#     truck_number_id: int
#     total: int
#     brokerage: float
#     net_recievable: float
#     loading_date: date
#     recieved_date: date
#     payment_recieved: int
#     number_of_days: int
#     payment_difference: float
#     remarks: str
#     party_name: str
#     rice_mill_name: str
#     broker_name: str
#     truck_number: str
#     broken_jawak_id: Optional[int] = None


# class HuskJawakBase(BaseModel):
#     rst_number: int
#     date: date
#     party_id: int
#     rice_mill_name_id: int
#     remarks: str
#     broker: int
#     brokerage_percentage: float
#     weight: float
#     rate: int
#     number_of_bags: int
#     truck_number_id: int
#     total: int
#     brokerage: float
#     net_receivable: float
#     received_date: date
#     loading_date: date
#     payment_received: int
#     number_of_days: int
#     payment_difference: float
#     husk_jawak_id: Optional[int] = None


# class HuskJawakWithPartyRiceBrokerTruck(BaseModel):
#     rst_number: int
#     date: date
#     party_id: int
#     rice_mill_name_id: int
#     remarks: str
#     broker: int
#     brokerage_percentage: float
#     weight: float
#     rate: int
#     number_of_bags: int
#     truck_number_id: int
#     total: int
#     brokerage: float
#     net_receivable: float
#     received_date: date
#     loading_date: date
#     payment_received: int
#     number_of_days: int
#     payment_difference: float
#     party_name: str
#     rice_mill_name: str
#     broker_name: str
#     truck_number: str
#     husk_jawak_id: Optional[int] = None


# class NakkhiJawakBase(BaseModel):
#     rst_number: int
#     date: date
#     party_id: int
#     rice_mill_name_id: int
#     broker: int
#     brokerage_percent: int
#     weight: float
#     rate: int
#     number_of_bags: int
#     truck_number_id: int
#     brokerage: float
#     total: int
#     net_recievable: float
#     loading_date: date
#     recieved_date: date
#     payment_recieved: int
#     number_of_days: int
#     payment_difference: int
#     remarks: str
#     nakkhi_jawak_id: Optional[int] = None


# class NakkhiWithRicePartyBrokerTruck(BaseModel):
#     rst_number: int
#     date: date
#     party_id: int
#     rice_mill_name_id: int
#     broker: int
#     brokerage_percent: int
#     weight: float
#     rate: int
#     number_of_bags: int
#     truck_number_id: int
#     brokerage: float
#     total: int
#     net_recievable: float
#     loading_date: date
#     recieved_date: date
#     payment_recieved: int
#     number_of_days: int
#     payment_difference: int
#     remarks: str
#     nakkhi_jawak_id: Optional[int] = None
#     party_name: str
#     rice_mill_name: str
#     broker_name: str
#     truck_number: str


# class BranJawakBase(BaseModel):
#     rst_number: int
#     date: date
#     party_id: int
#     rice_mill_name_id: int
#     broker: int
#     brokerage_percentage: float
#     weight: float
#     rate: int
#     number_of_bags: int
#     truck_number_id: int
#     total: int
#     brokerage: float
#     net_receivable: float
#     payment_received: int
#     payment_difference: int
#     remarks: str
#     oil: int
#     bran_jawak_id: Optional[int] = None


# class BranJawakWithRicePatryBrokerTruck(BaseModel):
#     rst_number: int
#     date: date
#     party_id: int
#     rice_mill_name_id: int
#     broker: int
#     brokerage_percentage: float
#     weight: float
#     rate: int
#     number_of_bags: int
#     truck_number_id: int
#     total: int
#     brokerage: float
#     net_receivable: float
#     payment_received: int
#     payment_difference: int
#     remarks: str
#     oil: int
#     bran_jawak_id: Optional[int] = None
#     party_name: str
#     rice_mill_name: str
#     broker_name: str
#     truck_number: str


# class BhushiBase(BaseModel):
#     rst_number: int
#     date: date
#     party_id: int
#     rice_mill_name_id: int
#     number_of_bags: int
#     weight: float
#     truck_number_id: int
#     rate: int
#     amount: int
#     bhushi_id: Optional[int] = None


# class BhushiWithPartyRiceTruck(BaseModel):
#     rst_number: int
#     date: date
#     party_id: int
#     rice_mill_name_id: int
#     number_of_bags: int
#     weight: float
#     truck_number_id: int
#     rate: int
#     amount: int
#     bhushi_id: Optional[int] = None
#     party_name: str
#     rice_mill_name: str
#     truck_number: str


# class PaddySaleBase(BaseModel):
#     rst_number_id: int
#     rice_mill_name_id: int
#     date: date
#     party_id: int
#     broker: int
#     loading_form_address: str
#     truck_number_id: int
#     paddy_name: str
#     weight: int
#     party_weight: int
#     bags: int
#     rate: int
#     ammount: int
#     plastic: int
#     joot_old: int
#     joot_23_24: int
#     joot_22_23: int
#     average_bag_wt: float
#     paddy_sale_id: Optional[int] = None


# class PaddySalesWithDhanawakPartyBrokerTruck(BaseModel):
#     rst_number_id: int
#     rice_mill_name_id: int
#     date: date
#     party_id: int
#     broker: int
#     loading_form_address: str
#     truck_number_id: int
#     paddy_name: str
#     weight: int
#     party_weight: int
#     bags: int
#     rate: int
#     ammount: int
#     plastic: int
#     joot_old: int
#     joot_23_24: int
#     joot_22_23: int
#     average_bag_wt: float
#     paddy_sale_id: Optional[int] = None
#     rst_number: int
#     party_name: str
#     broker_name: str
#     truck_number: str
#     rice_mill_name: str


# class CashInCashOutBase(BaseModel):
#     cash: str
#     paddy_purchase: float
#     paddy_in: float
#     paddy_sale: float
#     paddy_processed: float
#     paddy_stacked: float
#     rice_purchase: float
#     rice_depatched: float
#     broken_sold: float
#     bran_sold: float
#     nakkhi_sold: float
#     bhusa_sold: float
#     transporting_bill: float
#     bardana: float
#     total: float
#     cash_detail: Optional[int] = None


# class DhanAwakDalaliDhan(BaseModel):
#     total_weight: List[int]  # Dalali Dhan
#     Dhan_data: List[DhanAwakBase]  # Dhan Awak
#     Paddy_sale_data: List[PaddySaleBase]  # paddy sale


# class RicePurchaseBase(BaseModel):
#     rst_number: int
#     date: date
#     party_id: int
#     broker_id: int
#     truck_number_id: int
#     bags: int
#     mill_weight: float
#     party_weight: float
#     bill_to_rice_mill: int
#     rice_purchase_id: Optional[int] = None


# class RicePurchaseWithRiceTruckParty(BaseModel):
#     rst_number: int
#     date: date
#     party_id: int
#     broker_id: int
#     truck_number_id: int
#     bags: int
#     mill_weight: float
#     party_weight: float
#     bill_to_rice_mill: int
#     rice_purchase_id: Optional[int] = None
#     party_name: str
#     broker_name: str
#     truck_number: str
#     rice_mill_name: str


# class inventoryData(BaseModel):
#     mill_weight: List[float]
#     rice_deposide_data: List[RiceDepositeBase]
#     broken_data: List[BrokenJawak]
#     bran_data: List[BranJawakBase]
#     nakkhi_data: List[NakkhiJawakBase]
#     husk_data: List[HuskJawakBase]


# # class SocietyBase(BaseModel):
# #     society_name: str
# #     society_id: Optional[int] = None


# class DhanRiceSocietiesRateBase(BaseModel):
#     society_name_id: int
#     distance: float
#     new: int
#     dhan_rice_societies_rate_id: Optional[int] = None


# class LotNumberMasterBase(BaseModel):
#     rice_mill_name_id: int
#     lot_number: int
#     lot_number_master_id: Optional[int] = None


# class MohanFoodPaddyBase(BaseModel):
#     date: date
#     do_number_id: int
#     samiti: str
#     rice_mill_name_id: int
#     weight: int
#     vehicle_number_id: int
#     bags: int
#     transporting_total: int
#     transporter_name_id: int
#     transporter_type: str
#     transporter_status: str
#     rate: int
#     type_1: str
#     years_22_23: int
#     years_21_22: int
#     hdpe_one: int
#     hdpe_new: int
#     purana: int
#     pds: int
#     mohan_food_paddy_id: Optional[int] = None


# class TransporterMasterBase(BaseModel):
#     vehicle_number_id: int
#     name: str
#     phone_number: int
#     date: date
#     transporter_name_id: int
#     advance_payment: int
#     transporter_master_id: Optional[int] = None
