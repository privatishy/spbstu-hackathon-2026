from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Equipment:
    equipment_id: str
    model_name: str
    equipment_type: str
    capacity: int
    capacity_unit: str
    min_operating_temperature_c: int
    installation_days: int

@dataclass(frozen=True)
class Offer:
    offer_id: str
    supplier_id: str
    equipment_id: str
    equipment_type: str
    unit_price_rub: int
    stock_quantity: int

@dataclass(frozen=True)
class Supplier:
    supplier_id: str
    supplier_name: str
    delivery_cost_rub: int
    delivery_days: int

@dataclass(frozen=True)
class Station:
    station_id: str
    station_name: str
    recommended_budget_rub: int
    deadline_days: int
    object_id: str
    object_name: str
    optional: bool                                          
    equipment_type: str
    required_capacity: int
    capacity_unit: str
    operating_temperature_c: int
    installed_equipment_id: Optional[str]
    available_capacity: Optional[int]