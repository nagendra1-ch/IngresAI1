from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from collections import defaultdict

from app.database import get_db
from app.models import User
from app.routes.auth import get_current_user
from app.routes.districts import get_districts_map
from app.utils.cache import TTLCache

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

_dashboard_cache = TTLCache(default_ttl_seconds=600)  # 10 minutes cache

def get_all_resolved_records(db: Session, current_user: Optional[User] = None):
    """
    Returns resolved records for all districts. Uses the fast in-memory map cache.
    """
    cached = _dashboard_cache.get("all_resolved_records")
    if cached is not None:
        return cached

    user_stub = current_user or type('UserStub', (), {'id': 1})()
    records = get_districts_map(db=db, current_user=user_stub)
    _dashboard_cache.set("all_resolved_records", records)
    return records

@router.get("/summary")
def get_dashboard_summary(
    state_name: Optional[str] = None,
    district_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Computes total national or regional stats (averages of rainfall, recharge, extraction),
    highest/lowest ranking districts, and category counts. Supports optional state/district filters. Cached & optimized.
    """
    cache_key = f"summary_{state_name}_{district_name}"
    cached = _dashboard_cache.get(cache_key)
    if cached is not None:
        return cached

    resolved_records = get_all_resolved_records(db, current_user)

    # Filter by state
    if state_name:
        state_upper = state_name.upper().strip()
        resolved_records = [r for r in resolved_records if r["state_name"].upper().strip() == state_upper]

    # Filter by district
    if district_name:
        dist_upper = district_name.upper().strip()
        resolved_records = [r for r in resolved_records if r["district_name"].upper().strip() == dist_upper]

    total_districts = len(resolved_records)
    total_states = len(set(r["state_name"] for r in resolved_records))

    gw_vals = [r["depth_to_water_level_m_bgl"] for r in resolved_records if r.get("depth_to_water_level_m_bgl") is not None]
    avg_gw = sum(gw_vals) / len(gw_vals) if len(gw_vals) > 0 else 0.0

    rainfall_vals = [r["rainfall_mm"] for r in resolved_records if r.get("rainfall_mm") is not None]
    avg_rainfall = sum(rainfall_vals) / len(rainfall_vals) if len(rainfall_vals) > 0 else 0.0

    recharge_vals = [r["annual_groundwater_recharge_ham"] for r in resolved_records if r.get("annual_groundwater_recharge_ham") is not None]
    total_recharge = sum(recharge_vals)
    avg_recharge = total_recharge / len(recharge_vals) if len(recharge_vals) > 0 else 0.0

    extraction_vals = [r["annual_groundwater_extraction_ham"] for r in resolved_records if r.get("annual_groundwater_extraction_ham") is not None]
    total_extraction = sum(extraction_vals)
    avg_extraction = total_extraction / len(extraction_vals) if len(extraction_vals) > 0 else 0.0

    stage_vals = [r["stage_of_groundwater_extraction_percent"] for r in resolved_records if r.get("stage_of_groundwater_extraction_percent") is not None]
    avg_stage = sum(stage_vals) / len(stage_vals) if len(stage_vals) > 0 else 0.0

    # Rank districts
    ranked_districts = [
        {
            "id": r["id"],
            "district_name": r["district_name"],
            "state_name": r["state_name"],
            "groundwater_level": r["depth_to_water_level_m_bgl"]
        } for r in resolved_records if r.get("depth_to_water_level_m_bgl") is not None
    ]

    ranked = sorted(
        ranked_districts,
        key=lambda x: x["groundwater_level"],
        reverse=True
    )

    highest_gw = ranked[:5]
    lowest_gw = list(reversed(ranked))[:5]

    cat_counts = {}
    for r in resolved_records:
        cat = r.get("assessment_category") or "Unknown"
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    category_distribution = [{"category": k, "count": v} for k, v in cat_counts.items()]

    res = {
        "total_districts": total_districts,
        "total_states": total_states,
        "avg_groundwater_level": round(avg_gw, 2),
        "avg_stage_of_extraction": round(avg_stage, 2),
        "avg_rainfall": round(avg_rainfall, 2),
        "total_recharge": round(total_recharge, 2),
        "avg_recharge": round(avg_recharge, 2),
        "total_extraction": round(total_extraction, 2),
        "avg_extraction": round(avg_extraction, 2),
        "highest_districts": highest_gw,
        "lowest_districts": lowest_gw,
        "category_distribution": category_distribution
    }
    _dashboard_cache.set(cache_key, res)
    return res

@router.get("/state-statistics")
def get_state_statistics(
    state_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Computes averages of groundwater stats grouped by State.
    If state_name is provided, groups by District inside that state.
    """
    cache_key = f"state_stats_{state_name}"
    cached = _dashboard_cache.get(cache_key)
    if cached is not None:
        return cached

    resolved_records = get_all_resolved_records(db, current_user)

    if state_name:
        state_upper = state_name.upper().strip()
        filtered = [r for r in resolved_records if r["state_name"].upper().strip() == state_upper]

        result = []
        for r in sorted(filtered, key=lambda x: x["district_name"]):
            result.append({
                "state_name": r["district_name"],
                "district_name": r["district_name"],
                "avg_groundwater_level": r.get("depth_to_water_level_m_bgl") or 0.0,
                "avg_rainfall": r.get("rainfall_mm") or 0.0,
                "avg_recharge": r.get("annual_groundwater_recharge_ham") or 0.0,
                "avg_extraction": r.get("annual_groundwater_extraction_ham") or 0.0,
                "latitude": r.get("latitude"),
                "longitude": r.get("longitude")
            })
        _dashboard_cache.set(cache_key, result)
        return result

    by_state = defaultdict(list)
    for r in resolved_records:
        by_state[r["state_name"]].append({
            "gw": r.get("depth_to_water_level_m_bgl"),
            "rainfall": r.get("rainfall_mm"),
            "recharge": r.get("annual_groundwater_recharge_ham"),
            "extraction": r.get("annual_groundwater_extraction_ham")
        })

    result = []
    for s_name, items in sorted(by_state.items()):
        gw_vals = [i["gw"] for i in items if i["gw"] is not None]
        rain_vals = [i["rainfall"] for i in items if i["rainfall"] is not None]
        recharge_vals = [i["recharge"] for i in items if i["recharge"] is not None]
        extraction_vals = [i["extraction"] for i in items if i["extraction"] is not None]

        result.append({
            "state_name": s_name,
            "avg_groundwater_level": round(sum(gw_vals) / len(gw_vals), 2) if gw_vals else 0.0,
            "avg_rainfall": round(sum(rain_vals) / len(rain_vals), 2) if rain_vals else 0.0,
            "avg_recharge": round(sum(recharge_vals) / len(recharge_vals), 2) if recharge_vals else 0.0,
            "avg_extraction": round(sum(extraction_vals) / len(extraction_vals), 2) if extraction_vals else 0.0
        })

    _dashboard_cache.set(cache_key, result)
    return result

@router.get("/district-statistics")
def get_district_statistics(
    state_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lists the latest statistics for all districts, optionally filtered by state.
    """
    resolved = get_all_resolved_records(db, current_user)
    if state_name:
        state_upper = state_name.upper().strip()
        resolved = [r for r in resolved if r["state_name"].upper().strip() == state_upper]

    return [
        {
            "id": r["id"],
            "district_name": r["district_name"],
            "state_name": r["state_name"],
            "groundwater_level": r.get("depth_to_water_level_m_bgl"),
            "rainfall": r.get("rainfall_mm"),
            "assessment_category": r.get("assessment_category")
        } for r in resolved
    ]

@router.get("/rainfall")
def get_rainfall_statistics(
    state_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Aggregates state/district level rainfall for visual charts.
    """
    return get_state_statistics(state_name, db, current_user)

@router.get("/groundwater")
def get_groundwater_distribution(
    state_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exposes Safe vs Critical category distributions.
    """
    summary = get_dashboard_summary(state_name, None, db, current_user)
    return summary["category_distribution"]
