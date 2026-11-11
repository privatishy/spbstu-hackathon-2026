import sqlite3
from contextlib import contextmanager
from typing import Optional, Iterable
from models import Equipment, Offer, Supplier, Station

DB_PATH = 'HackatonDB.db'

@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()

                               
def _row_to_equipment(row: sqlite3.Row) -> Equipment:
    return Equipment(
        equipment_id=row["equipment_id"],
        model_name=row["model_name"],
        equipment_type=row["equipment_type"],
        capacity=row["capacity"],
        capacity_unit=row["capacity_unit"],
        min_operating_temperature_c=row["min_operating_temperature_c"],
        installation_days=row["installation_days"],
    )

def _row_to_offer(row: sqlite3.Row) -> Offer:
    return Offer(
        offer_id=row["offer_id"],
        supplier_id=row["supplier_id"],
        equipment_id=row["equipment_id"],
        equipment_type=row["equipment_type"],
        unit_price_rub=row["unit_price_rub"],
        stock_quantity=row["stock_quantity"],
    )

def _row_to_supplier(row: sqlite3.Row) -> Supplier:
    return Supplier(
        supplier_id=row["supplier_id"],
        supplier_name=row["supplier_name"],
        delivery_cost_rub=row["delivery_cost_rub"],
        delivery_days=row["delivery_days"],
    )

def _row_to_station(row: sqlite3.Row) -> Station:
    return Station(
        station_id=row["station_id"],
        station_name=row["station_name"],
        recommended_budget_rub=row["recommended_budget_rub"],
        deadline_days=row["deadline_days"],
        object_id=row["object_id"],
        object_name=row["object_name"],
        optional=(row["optional"] == "yes"),
        equipment_type=row["equipment_type"],
        required_capacity=row["required_capacity"],
        capacity_unit=row["capacity_unit"],
        operating_temperature_c=row["operating_temperature_c"],
        installed_equipment_id=row["installed_equipment_id"] or None,
        available_capacity=row["available_capacity"],
    )

                                         
def get_equipment_by_id(equipment_id: str) -> Optional[Equipment]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT equipment_id, model_name, equipment_type, capacity, "
            "capacity_unit, min_operating_temperature_c, installation_days "
            "FROM equipment WHERE equipment_id = ?",
            (equipment_id,),
        ).fetchone()
    return _row_to_equipment(row) if row else None

def get_all_equipment() -> list[Equipment]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT equipment_id, model_name, equipment_type, capacity, "
            "capacity_unit, min_operating_temperature_c, installation_days "
            "FROM equipment"
        ).fetchall()
    return [_row_to_equipment(r) for r in rows]

def get_offers_by_equipment_type(equipment_type: str) -> list[Offer]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT offer_id, supplier_id, equipment_id, equipment_type, "
            "unit_price_rub, stock_quantity "
            "FROM offers WHERE equipment_type = ?",
            (equipment_type,),
        ).fetchall()
    return [_row_to_offer(r) for r in rows]

def get_supplier_by_id(supplier_id: str) -> Optional[Supplier]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT supplier_id, supplier_name, delivery_cost_rub, delivery_days "
            "FROM suppliers WHERE supplier_id = ?",
            (supplier_id,),
        ).fetchone()
    return _row_to_supplier(row) if row else None

def get_all_stations() -> list[Station]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT station_id, station_name, recommended_budget_rub, deadline_days, "
            "object_id, object_name, optional, equipment_type, required_capacity, "
            "capacity_unit, operating_temperature_c, installed_equipment_id, "
            "available_capacity FROM station_1"
        ).fetchall()
    return [_row_to_station(r) for r in rows]

def get_all_offers() -> list[Offer]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT offer_id, supplier_id, equipment_id, equipment_type, "
            "unit_price_rub, stock_quantity "
            "FROM offers"
        ).fetchall()
    return [_row_to_offer(r) for r in rows]

def get_all_suppliers() -> list[Supplier]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT supplier_id, supplier_name, delivery_cost_rub, delivery_days "
            "FROM suppliers"
        ).fetchall()
    return [_row_to_supplier(r) for r in rows]