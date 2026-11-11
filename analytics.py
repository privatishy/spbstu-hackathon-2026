from pathlib import Path
import json
from typing import Optional

from repository import (
    get_all_equipment,
    get_all_offers,
    get_all_suppliers,
    get_all_stations,
)
from models import Equipment, Offer, Supplier, Station


                                                              
        
                                                              
_CONFIG_PATH = Path(__file__).parent / "config.json"
_DEFAULT_CONFIG = {"recommended_budget_rub": 2_600_000, "recovery_deadline_days": 14}


def load_config() -> dict:
    cfg = dict(_DEFAULT_CONFIG)
    if _CONFIG_PATH.exists():
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except (json.JSONDecodeError, OSError) as e:
            cfg["_load_warning"] = f"Не удалось прочитать config.json: {e}"
    return cfg


                                                              
                 
                                                              
def _equipment_index() -> dict[str, Equipment]:
    return {e.equipment_id: e for e in get_all_equipment()}


def _supplier_index() -> dict[str, Supplier]:
    return {s.supplier_id: s for s in get_all_suppliers()}


def _normalize_id(value) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    if s == "" or s.upper() == "NONE":
        return None
    return s


def _check_installed(row: Station, eq_map: dict[str, Equipment]) -> tuple[bool, str]:
    installed_id = _normalize_id(row.installed_equipment_id)
    if installed_id is None:
        return False, "no_equipment"

    eq = eq_map.get(installed_id)
    if eq is None:
        return False, "unknown_installed_model"

                                    
    if eq.min_operating_temperature_c > row.operating_temperature_c:
        return False, "insufficient_temperature"

                                                            
                                                  
    available = row.available_capacity if row.available_capacity is not None else eq.capacity
    if available < row.required_capacity:
        return False, "insufficient_capacity"

    return True, "satisfied"


                                                              
                                               
                                                              
def search_equipment(
    equipment_type: str,
    min_capacity: int,
    operating_temperature_c: int,
) -> dict:
    if not equipment_type or min_capacity is None or operating_temperature_c is None:
        return {"error": "Не заданы обязательные параметры поиска"}

    all_eq = get_all_equipment()
    matches = [
        e for e in all_eq
        if e.equipment_type == equipment_type
        and e.capacity >= min_capacity
        and e.min_operating_temperature_c <= operating_temperature_c
    ]

    return {
        "query": {
            "equipment_type": equipment_type,
            "min_capacity": min_capacity,
            "operating_temperature_c": operating_temperature_c,
        },
        "found": len(matches) > 0,
        "count": len(matches),
        "models": [
            {
                "equipment_id": e.equipment_id,
                "model_name": e.model_name,
                "capacity": e.capacity,
                "capacity_unit": e.capacity_unit,
                "min_operating_temperature_c": e.min_operating_temperature_c,
                "installation_days": e.installation_days,
            }
            for e in matches
        ],
        "message": None if matches else "Модели с указанными характеристиками не найдены",
    }


                                                              
                                              
                                                              
def _valid_offers_for_need(
    need: dict,
    offers: list[Offer],
    eq_map: dict[str, Equipment],
    supplier_map: dict[str, Supplier],
    remaining_stock: dict[str, int],
    deadline_days: int,
) -> list[dict]:
    result: list[dict] = []
    for offer in offers:
        if remaining_stock.get(offer.offer_id, 0) < 1:
            continue
        if offer.equipment_type != need["equipment_type"]:
            continue

        eq = eq_map.get(offer.equipment_id)
        if eq is None:
            continue
        if eq.capacity_unit != need["capacity_unit"]:
            continue
        if eq.capacity < need["required_capacity"]:
            continue
        if eq.min_operating_temperature_c > need["operating_temperature_c"]:
            continue

        supplier = supplier_map.get(offer.supplier_id)
        if supplier is None:
            continue

        ready_days = supplier.delivery_days + eq.installation_days
        if ready_days > deadline_days:
            continue

        result.append({
            "offer": offer,
            "equipment": eq,
            "supplier": supplier,
            "ready_days": ready_days,
        })
    return result


def find_purchase_for_requirement(
    equipment_type: str,
    min_capacity: int,
    operating_temperature_c: int,
    deadline_days: int,
    capacity_unit: Optional[str] = None,
) -> dict:
    if capacity_unit is None:
                                                                  
        units = {
            e.capacity_unit for e in get_all_equipment()
            if e.equipment_type == equipment_type
        }
        if len(units) == 1:
            capacity_unit = next(iter(units))
        elif not units:
            return {"found": False, "message": f"Тип '{equipment_type}' не найден в каталоге"}
        else:
            return {"error": f"Для типа '{equipment_type}' несколько единиц измерения, укажите capacity_unit"}

    need = {
        "equipment_type": equipment_type,
        "required_capacity": min_capacity,
        "operating_temperature_c": operating_temperature_c,
        "capacity_unit": capacity_unit,
    }

    eq_map = _equipment_index()
    supplier_map = _supplier_index()
    offers = get_all_offers()
    remaining_stock = {o.offer_id: o.stock_quantity for o in offers}

                              
    matching_models = {
        e.equipment_id for e in eq_map.values()
        if e.equipment_type == equipment_type
        and e.capacity_unit == capacity_unit
        and e.capacity >= min_capacity
        and e.min_operating_temperature_c <= operating_temperature_c
    }
    if not matching_models:
        return {
            "found": False,
            "query": need,
            "message": "Нет моделей, подходящих по характеристикам",
            "candidates": [],
            "excluded": [],
        }

    valid = _valid_offers_for_need(need, offers, eq_map, supplier_map, remaining_stock, deadline_days)

                                           
    excluded = []
    valid_offer_ids = {v["offer"].offer_id for v in valid}
    for offer in offers:
        if offer.equipment_id not in matching_models:
            continue
        if offer.offer_id in valid_offer_ids:
            continue
        eq = eq_map[offer.equipment_id]
        sup = supplier_map.get(offer.supplier_id)
        reasons = []
        if offer.stock_quantity < 1:
            reasons.append("нет в наличии")
        if sup is None:
            reasons.append("поставщик не найден")
        elif sup.delivery_days + eq.installation_days > deadline_days:
            reasons.append(
                f"срок {sup.delivery_days + eq.installation_days} дн. > дедлайн {deadline_days}"
            )
        excluded.append({
            "offer_id": offer.offer_id,
            "supplier_id": offer.supplier_id,
            "supplier_name": sup.supplier_name if sup else None,
            "unit_price_rub": offer.unit_price_rub,
            "stock_quantity": offer.stock_quantity,
            "reasons": reasons or ["не подходит"],
        })

    candidates = sorted(
        [
            {
                "offer_id": v["offer"].offer_id,
                "equipment_id": v["offer"].equipment_id,
                "model_name": v["equipment"].model_name,
                "supplier_id": v["supplier"].supplier_id,
                "supplier_name": v["supplier"].supplier_name,
                "unit_price_rub": v["offer"].unit_price_rub,
                "delivery_cost_rub": v["supplier"].delivery_cost_rub,
                "total_cost_rub": v["offer"].unit_price_rub + v["supplier"].delivery_cost_rub,
                "ready_days": v["ready_days"],
                "stock_quantity": v["offer"].stock_quantity,
            }
            for v in valid
        ],
        key=lambda c: c["total_cost_rub"],
    )

    return {
        "query": {**need, "deadline_days": deadline_days},
        "found": len(candidates) > 0,
        "best": candidates[0] if candidates else None,
        "candidates": candidates,
        "excluded": excluded,
        "message": None if candidates else "Нет предложений, удовлетворяющих ограничениям",
    }


                                                              
                        
                                                              
def analyze_station() -> dict:
    eq_map = _equipment_index()
    stations = get_all_stations()

    objects: dict[str, dict] = {}
    for row in stations:
        oid = row.object_id
        if oid not in objects:
            objects[oid] = {
                "object_id": oid,
                "object_name": row.object_name,
                "mandatory": not row.optional,                                   
                "needs": [],
            }
        else:
                                                                                  
            if not row.optional:
                objects[oid]["mandatory"] = True

        fits, reason = _check_installed(row, eq_map)
        objects[oid]["needs"].append({
            "station_id": row.station_id,
            "station_name": row.station_name,
            "object_id": row.object_id,
            "object_name": row.object_name,
            "equipment_type": row.equipment_type,
            "required_capacity": row.required_capacity,
            "capacity_unit": row.capacity_unit,
            "operating_temperature_c": row.operating_temperature_c,
            "deadline_days": row.deadline_days,
            "installed_equipment_id": _normalize_id(row.installed_equipment_id),
            "available_capacity": row.available_capacity,
            "status": "satisfied" if fits else "needs_replacement",
            "reason": reason,
        })

    for obj in objects.values():
        obj["satisfied_needs"] = [n for n in obj["needs"] if n["status"] == "satisfied"]
        obj["needs_replacement"] = [n for n in obj["needs"] if n["status"] == "needs_replacement"]
        obj["fully_satisfied"] = len(obj["needs_replacement"]) == 0

    return {
        "objects": list(objects.values()),
        "stats": {
            "total_objects": len(objects),
            "mandatory_objects": sum(1 for o in objects.values() if o["mandatory"]),
            "optional_objects": sum(1 for o in objects.values() if not o["mandatory"]),
            "fully_satisfied_objects": sum(1 for o in objects.values() if o["fully_satisfied"]),
            "total_needs": sum(len(o["needs"]) for o in objects.values()),
            "needs_replacement": sum(len(o["needs_replacement"]) for o in objects.values()),
        },
    }


                                                              
                                         
                                                              
def _try_assign_object(
    obj: dict,
    offers: list[Offer],
    eq_map: dict[str, Equipment],
    supplier_map: dict[str, Supplier],
    remaining_stock: dict[str, int],
    used_suppliers: set[str],
    global_deadline: int,
) -> Optional[list[dict]]:
    if not obj["needs_replacement"]:
        return []                   

    temp_stock = dict(remaining_stock)
    temp_suppliers = set(used_suppliers)
    assignments: list[dict] = []

                                                                                 
    scored = []
    for need in obj["needs_replacement"]:
        effective_deadline = min(need["deadline_days"], global_deadline)
        cands = _valid_offers_for_need(need, offers, eq_map, supplier_map, temp_stock, effective_deadline)
        scored.append((need, cands, effective_deadline))
    scored.sort(key=lambda x: len(x[1]))

    for need, cands, effective_deadline in scored:
                               
        cands = [c for c in cands if temp_stock.get(c["offer"].offer_id, 0) >= 1]
        if not cands:
            return None

        for c in cands:
            if c["supplier"].supplier_id in temp_suppliers:
                c["_marginal"] = c["offer"].unit_price_rub
            else:
                c["_marginal"] = c["offer"].unit_price_rub + c["supplier"].delivery_cost_rub

        best = min(cands, key=lambda c: c["_marginal"])
        assignments.append({
            "need": need,
            "offer": best["offer"],
            "supplier": best["supplier"],
            "equipment": best["equipment"],
            "ready_days": best["ready_days"],
        })
        temp_stock[best["offer"].offer_id] -= 1
        temp_suppliers.add(best["supplier"].supplier_id)

    return assignments


def _estimate_object_cost(obj, offers, eq_map, supplier_map) -> float:
    if not obj["needs_replacement"]:
        return 0.0
    total = 0.0
    for need in obj["needs_replacement"]:
        cands = _valid_offers_for_need(
            need, offers, eq_map, supplier_map,
            remaining_stock={o.offer_id: o.stock_quantity for o in offers},
            deadline_days=need["deadline_days"],
        )
        if not cands:
            return float("inf")
        total += min(c["offer"].unit_price_rub for c in cands)
    return total


def build_recovery_plan(
    budget_rub: Optional[int] = None,
    deadline_days: Optional[int] = None,
) -> dict:
    config = load_config()
    budget = budget_rub if budget_rub is not None else config["recommended_budget_rub"]
    global_deadline = deadline_days if deadline_days is not None else config["recovery_deadline_days"]

    eq_map = _equipment_index()
    supplier_map = _supplier_index()
    offers = get_all_offers()
    analysis = analyze_station()

    remaining_stock = {o.offer_id: o.stock_quantity for o in offers}
    used_suppliers: set[str] = set()
    assignments: list[dict] = []

    mandatory_objs = [o for o in analysis["objects"] if o["mandatory"] and not o["fully_satisfied"]]
    optional_objs = [o for o in analysis["objects"] if not o["mandatory"] and not o["fully_satisfied"]]
    already_done = [o for o in analysis["objects"] if o["fully_satisfied"]]

    mandatory_objs.sort(key=lambda o: _estimate_object_cost(o, offers, eq_map, supplier_map))
    optional_objs.sort(key=lambda o: _estimate_object_cost(o, offers, eq_map, supplier_map))

    restored_mandatory: list[dict] = []
    failed_mandatory: list[dict] = []

                                  
    for obj in mandatory_objs:
        result = _try_assign_object(
            obj, offers, eq_map, supplier_map,
            remaining_stock, used_suppliers, global_deadline,
        )
        if result is None:
            failed_mandatory.append(obj)
            continue
        for a in result:
            assignments.append(a)
            remaining_stock[a["offer"].offer_id] -= 1
            used_suppliers.add(a["supplier"].supplier_id)
        restored_mandatory.append(obj)

    def calc_cost(asg: list[dict], sup_ids: set[str]) -> int:
        unit = sum(a["offer"].unit_price_rub for a in asg)
        delivery = sum(supplier_map[s].delivery_cost_rub for s in sup_ids if s in supplier_map)
        return unit + delivery

    current_cost = calc_cost(assignments, used_suppliers)

                                                                 
    restored_optional: list[dict] = []
    if current_cost <= budget:
        for obj in optional_objs:
            result = _try_assign_object(
                obj, offers, eq_map, supplier_map,
                remaining_stock, used_suppliers, global_deadline,
            )
            if result is None:
                continue
            extra_units = sum(a["offer"].unit_price_rub for a in result)
            extra_suppliers = {a["supplier"].supplier_id for a in result} - used_suppliers
            extra_delivery = sum(
                supplier_map[s].delivery_cost_rub for s in extra_suppliers if s in supplier_map
            )
            if current_cost + extra_units + extra_delivery > budget:
                continue                                                        
            for a in result:
                assignments.append(a)
                remaining_stock[a["offer"].offer_id] -= 1
                used_suppliers.add(a["supplier"].supplier_id)
            restored_optional.append(obj)
            current_cost += extra_units + extra_delivery

    final_cost = calc_cost(assignments, used_suppliers)
    overrun = max(0, final_cost - budget)

                                        
    by_supplier: dict[str, dict] = {}
    for a in assignments:
        sid = a["supplier"].supplier_id
        if sid not in by_supplier:
            by_supplier[sid] = {
                "supplier_id": sid,
                "supplier_name": a["supplier"].supplier_name,
                "delivery_cost_rub": a["supplier"].delivery_cost_rub,
                "delivery_days": a["supplier"].delivery_days,
                "items": [],
                "unit_total_rub": 0,
            }
        by_supplier[sid]["items"].append({
            "offer_id": a["offer"].offer_id,
            "equipment_id": a["offer"].equipment_id,
            "model_name": a["equipment"].model_name,
            "equipment_type": a["offer"].equipment_type,
            "unit_price_rub": a["offer"].unit_price_rub,
            "ready_days": a["ready_days"],
            "for_object_id": a["need"]["object_id"],
            "for_object_name": a["need"]["object_name"],
            "for_need": {
                "equipment_type": a["need"]["equipment_type"],
                "required_capacity": a["need"]["required_capacity"],
                "capacity_unit": a["need"]["capacity_unit"],
                "operating_temperature_c": a["need"]["operating_temperature_c"],
                "deadline_days": a["need"]["deadline_days"],
            },
        })
        by_supplier[sid]["unit_total_rub"] += a["offer"].unit_price_rub

                                       
    unrestored_optional = [
        {"object_id": o["object_id"], "object_name": o["object_name"]}
        for o in optional_objs if o not in restored_optional
    ]

    return {
        "success": len(failed_mandatory) == 0,
        "config": {
            "budget_rub": budget,
            "deadline_days": global_deadline,
        },
        "cost": {
            "unit_total_rub": sum(a["offer"].unit_price_rub for a in assignments),
            "delivery_total_rub": sum(
                supplier_map[s].delivery_cost_rub for s in used_suppliers if s in supplier_map
            ),
            "total_rub": final_cost,
            "overrun_rub": overrun,
            "within_budget": final_cost <= budget,
        },
        "restored_objects": [
            {
                "object_id": o["object_id"],
                "object_name": o["object_name"],
                "mandatory": True,
                "already_satisfied": o["fully_satisfied"],
            }
            for o in (already_done + restored_mandatory)
        ],
        "restored_optional_objects": [
            {"object_id": o["object_id"], "object_name": o["object_name"]}
            for o in restored_optional
        ],
        "failed_mandatory_objects": [
            {
                "object_id": o["object_id"],
                "object_name": o["object_name"],
                "unmet_needs": [
                    {
                        "equipment_type": n["equipment_type"],
                        "required_capacity": n["required_capacity"],
                        "capacity_unit": n["capacity_unit"],
                        "operating_temperature_c": n["operating_temperature_c"],
                        "deadline_days": n["deadline_days"],
                        "reason": n["reason"] + " (нет валидного предложения)",
                    }
                    for n in o["needs_replacement"]
                ],
            }
            for o in failed_mandatory
        ],
        "unrestored_optional_objects": unrestored_optional,
        "purchases_by_supplier": list(by_supplier.values()),
        "assignments": [
            {
                "object_id": a["need"]["object_id"],
                "object_name": a["need"]["object_name"],
                "equipment_type": a["need"]["equipment_type"],
                "required_capacity": a["need"]["required_capacity"],
                "capacity_unit": a["need"]["capacity_unit"],
                "operating_temperature_c": a["need"]["operating_temperature_c"],
                "offer_id": a["offer"].offer_id,
                "equipment_id": a["offer"].equipment_id,
                "model_name": a["equipment"].model_name,
                "supplier_id": a["supplier"].supplier_id,
                "supplier_name": a["supplier"].supplier_name,
                "unit_price_rub": a["offer"].unit_price_rub,
                "ready_days": a["ready_days"],
                "deadline_days": a["need"]["deadline_days"],
            }
            for a in assignments
        ],
        "notes": [
            "Алгоритм жадный: не гарантирует глобальный оптимум.",
            "Порядок объектов влияет на распределение дефицитных остатков.",
            "Необязательные объекты добавляются, только пока не превышен бюджет.",
        ],
    }

