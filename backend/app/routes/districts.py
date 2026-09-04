from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from collections import defaultdict

from app.database import get_db
from app.models import Geography, GeographyAlias, GWRAAssessment, GroundwaterObservation, RainfallRecord, ResultAccess, User
from app.routes.auth import get_current_user
from app.utils.official_fallbacks import get_official_rainfall_fallback, get_official_depth_fallback, get_official_groundwater_fallback
from app.utils.validation import validate_district_data
from app.utils.cache import TTLCache

router = APIRouter(prefix="/api/districts", tags=["Districts"])

# In-memory thread-safe caches for high performance
_district_cache = TTLCache(default_ttl_seconds=600)   # 10 minutes per district detail
_districts_list_cache = TTLCache(default_ttl_seconds=900) # 15 minutes for dropdown selectors
_map_cache = TTLCache(default_ttl_seconds=900)        # 15 minutes for GIS map

def invalidate_district_caches():
    """Invalidate all district-related in-memory caches (e.g. after admin updates)."""
    _district_cache.clear()
    _districts_list_cache.clear()
    _map_cache.clear()

def resolve_district_response(db: Session, geo: Geography):
    """
    Optimized single district resolution.
    Fetches GWRA assessments, observations, and rainfall in batched queries,
    then aggregates in memory in < 1ms.
    """
    cached = _district_cache.get(geo.id)
    if cached is not None:
        return cached

    # 1. Single query for all GWRA assessments for this district
    gwra_all = db.query(GWRAAssessment).filter_by(geography_id=geo.id).order_by(GWRAAssessment.assessment_year.desc()).all()
    gwra = gwra_all[0] if gwra_all else None

    # 2. Single query for all Groundwater Observations for this district across its observation network
    obs_all = db.query(GroundwaterObservation).join(Geography).filter(
        Geography.normalized_state_name == geo.normalized_state_name,
        Geography.normalized_district_name == geo.normalized_district_name
    ).all()
    if not obs_all:
        obs_all = db.query(GroundwaterObservation).filter(GroundwaterObservation.geography_id == geo.id).all()

    # Prefer district-level observations for primary average if present, or all district observations
    dist_obs_all = [o for o in obs_all if o.geography_id == geo.id]
    target_obs = dist_obs_all if dist_obs_all else obs_all

    obs_by_year = defaultdict(list)
    for o in target_obs:
        if o.depth_to_water_level_m_bgl is not None:
            obs_by_year[o.observation_year].append(o)

    # 3. Single query for all Rainfall Records for this district
    rain_all = db.query(RainfallRecord).join(Geography).filter(
        Geography.normalized_state_name == geo.normalized_state_name,
        Geography.normalized_district_name == geo.normalized_district_name
    ).all()
    if not rain_all:
        rain_all = db.query(RainfallRecord).filter(RainfallRecord.geography_id == geo.id).all()

    dist_rain_all = [r for r in rain_all if r.geography_id == geo.id]
    target_rain = dist_rain_all if dist_rain_all else rain_all

    rain_by_year = defaultdict(list)
    for r in target_rain:
        if r.rainfall_mm is not None:
            rain_by_year[r.rainfall_year].append(r)

    # Compute latest depth & indicator % in memory
    all_obs_depths = [o.depth_to_water_level_m_bgl for o in obs_all if o.depth_to_water_level_m_bgl is not None]
    if obs_by_year:
        latest_obs_year = max(obs_by_year.keys())
        latest_obs_list = obs_by_year[latest_obs_year]
        depths = [o.depth_to_water_level_m_bgl for o in latest_obs_list]
        avg_depth = round(sum(depths) / len(depths), 2) if depths else None
        depth_year = latest_obs_year
        depth_src = latest_obs_list[0].source if latest_obs_list else None
        depth_period = latest_obs_list[0].observation_date if latest_obs_list else None
    else:
        avg_depth, depth_year, depth_src, depth_period = None, None, None, None

    # Compute latest rainfall in memory
    avg_rain, rain_year, rain_period_type, rain_month, rain_src = None, None, None, None, None
    if rain_by_year:
        latest_rain_year = max(rain_by_year.keys())
        rains = rain_by_year[latest_rain_year]
        annual_rec = next((r for r in rains if r.rainfall_period and r.rainfall_period.lower() == "annual"), None)
        if annual_rec:
            avg_rain, rain_year, rain_period_type, rain_month, rain_src = (
                annual_rec.rainfall_mm, latest_rain_year, "annual", None, annual_rec.rainfall_source
            )
        else:
            monthly_recs = [r for r in rains if r.rainfall_period and r.rainfall_period.lower() == "monthly"]
            unique_months = {r.rainfall_month.lower().strip() for r in monthly_recs if r.rainfall_month}
            if len(unique_months) == 12:
                avg_rain, rain_year, rain_period_type, rain_month, rain_src = (
                    round(sum(r.rainfall_mm for r in monthly_recs), 1), latest_rain_year, "annual", None, monthly_recs[0].rainfall_source
                )
            elif monthly_recs:
                avg_rain, rain_year, rain_period_type, rain_month, rain_src = (
                    monthly_recs[0].rainfall_mm, latest_rain_year, "monthly", monthly_recs[0].rainfall_month, monthly_recs[0].rainfall_source
                )
            elif rains:
                first_r = rains[0]
                avg_rain, rain_year, rain_period_type, rain_month, rain_src = (
                    first_r.rainfall_mm, latest_rain_year,
                    first_r.rainfall_period.lower() if first_r.rainfall_period else "unknown",
                    first_r.rainfall_month, first_r.rainfall_source
                )

    rain_period = rain_period_type

    # Ensure Depth is not null via historical search or official fallback
    if avg_depth is None:
        if all_obs_depths:
            prev_obs = sorted(obs_all, key=lambda x: x.observation_year or 0, reverse=True)[0]
            avg_depth = prev_obs.depth_to_water_level_m_bgl
            depth_year = prev_obs.observation_year
            depth_src = prev_obs.source or "CGWB (Historical)"
        else:
            avg_depth = get_official_depth_fallback(geo.state_name, geo.district_name)
            depth_year = 2026
            depth_src = "CGWB Fallback (cgwb.gov.in)"

    # Compute Groundwater Level Indicator % (derived from historical reference range or configured standard scale)
    indicator = None
    if avg_depth is not None:
        if len(all_obs_depths) >= 2:
            min_d, max_d = min(all_obs_depths), max(all_obs_depths)
            if max_d > min_d:
                val = ((max_d - avg_depth) / (max_d - min_d)) * 100.0
                indicator = round(max(0.0, min(100.0, val)), 2)
            else:
                indicator = round(max(0.0, min(100.0, ((40.0 - avg_depth) / 40.0) * 100.0)), 2)
        else:
            indicator = round(max(0.0, min(100.0, ((40.0 - avg_depth) / 40.0) * 100.0)), 2)

    # Ensure Rainfall is not null via historical search or official fallback
    if avg_rain is None:
        if rain_all:
            prev_r = sorted(rain_all, key=lambda x: x.rainfall_year or 0, reverse=True)[0]
            avg_rain = prev_r.rainfall_mm
            rain_year = prev_r.rainfall_year
            rain_period = prev_r.rainfall_period.lower() if prev_r.rainfall_period else "annual"
            rain_period_type = rain_period
            rain_src = prev_r.rainfall_source or "IMD (Historical)"
        else:
            fb = get_official_rainfall_fallback(geo.state_name, geo.district_name, depth_year or 2026)
            if fb:
                avg_rain = fb["value"]
                rain_year = depth_year or 2026
                rain_period = fb["period"]
                rain_period_type = "monthly" if "monthly" in fb["period"].lower() else ("annual" if "annual" in fb["period"].lower() else "unknown")
                rain_src = fb["source"]

    recharge = gwra.annual_groundwater_recharge_ham if gwra else None
    extractable = gwra.annual_extractable_groundwater_resource_ham if gwra else None
    extraction = gwra.annual_groundwater_extraction_ham if gwra else None
    stage = gwra.stage_of_groundwater_extraction_percent if gwra else None
    net_avail = gwra.net_groundwater_availability_ham if gwra else None
    category = gwra.district_assessment_category if gwra else None
    gwra_year = gwra.assessment_year if gwra else 2025
    gwra_src = gwra.source_document if gwra else None

    # Apply GWRA fallbacks if missing
    if stage is None or recharge is None or extractable is None or extraction is None:
        if len(gwra_all) > 1:
            prev_gwra = next((g for g in gwra_all if g.stage_of_groundwater_extraction_percent is not None), gwra_all[0])
            recharge = recharge if recharge is not None else prev_gwra.annual_groundwater_recharge_ham
            extractable = extractable if extractable is not None else prev_gwra.annual_extractable_groundwater_resource_ham
            extraction = extraction if extraction is not None else prev_gwra.annual_groundwater_extraction_ham
            stage = stage if stage is not None else prev_gwra.stage_of_groundwater_extraction_percent
            net_avail = net_avail if net_avail is not None else prev_gwra.net_groundwater_availability_ham
            category = category if category is not None else prev_gwra.district_assessment_category
            gwra_year = prev_gwra.assessment_year
            gwra_src = prev_gwra.source_document or "CGWB (Historical)"
        else:
            fb_gw = get_official_groundwater_fallback(geo.state_name, geo.district_name, 2025)
            if fb_gw:
                recharge = recharge if recharge is not None else fb_gw["annual_groundwater_recharge_ham"]
                extractable = extractable if extractable is not None else fb_gw["annual_extractable_groundwater_resource_ham"]
                extraction = extraction if extraction is not None else fb_gw["annual_groundwater_extraction_ham"]
                stage = stage if stage is not None else fb_gw["stage_of_groundwater_extraction_percent"]
                net_avail = net_avail if net_avail is not None else (recharge - extraction if recharge is not None and extraction is not None else 0.0)
                category = category if category is not None else fb_gw["assessment_category"]
                gwra_year = 2025
                gwra_src = fb_gw["source"]

    if stage is None and extraction is not None and extractable is not None and extractable > 0:
        stage = round((extraction / extractable) * 100.0, 2)

    dq = validate_district_data(gwra, avg_depth, avg_rain, geo)

    # In-memory assembly of historical chronological records
    gwra_by_year = {g.assessment_year: g for g in gwra_all}
    all_years = set(gwra_by_year.keys()) | set(obs_by_year.keys()) | set(rain_by_year.keys())
    if not all_years:
        all_years = {gwra_year}

    historical_data = []
    for y in sorted(list(all_years), reverse=True):
        gwra_y = gwra_by_year.get(y)
        obs_y = obs_by_year.get(y, [])
        depths_y = [o.depth_to_water_level_m_bgl for o in obs_y if o.depth_to_water_level_m_bgl is not None]
        avg_depth_y = round(sum(depths_y) / len(depths_y), 2) if depths_y else None

        rains_y = rain_by_year.get(y, [])
        if rains_y:
            annual_y = next((r for r in rains_y if r.rainfall_period and r.rainfall_period.lower() == "annual"), None)
            if annual_y:
                avg_rain_y, r_period_y, r_src_y = annual_y.rainfall_mm, "annual", annual_y.rainfall_source
            else:
                avg_rain_y, r_period_y, r_src_y = round(sum(r.rainfall_mm for r in rains_y) / len(rains_y), 1), "monthly", rains_y[0].rainfall_source
        else:
            avg_rain_y, r_period_y, r_src_y = None, None, None

        rec_y = gwra_y.annual_groundwater_recharge_ham if gwra_y else None
        extable_y = gwra_y.annual_extractable_groundwater_resource_ham if gwra_y else None
        ext_y = gwra_y.annual_groundwater_extraction_ham if gwra_y else None
        stg_y = gwra_y.stage_of_groundwater_extraction_percent if gwra_y else None
        if stg_y is None and ext_y is not None and extable_y is not None and extable_y > 0:
            stg_y = round((ext_y / extable_y) * 100.0, 2)

        historical_data.append({
            "year": y,
            "observation_year": y,
            "depth_to_water_level_m_bgl": avg_depth_y,
            "rainfall_mm": avg_rain_y,
            "rainfall_period": r_period_y,
            "rainfall_period_type": r_period_y,
            "rainfall_month": None,
            "rainfall_year": y,
            "annual_groundwater_recharge_ham": rec_y,
            "annual_extractable_groundwater_resource_ham": extable_y,
            "annual_groundwater_extraction_ham": ext_y,
            "stage_of_groundwater_extraction_percent": stg_y,
            "net_groundwater_availability_ham": gwra_y.net_groundwater_availability_ham if gwra_y else None,
            "assessment_category": gwra_y.district_assessment_category if gwra_y else None,
            "data_source_groundwater": obs_y[0].source if obs_y else None,
            "data_source_rainfall": r_src_y,
            "data_source_gwra": gwra_y.source_document if gwra_y else None
        })

    res = {
        "id": geo.id,
        "district_name": geo.district_name,
        "state_name": geo.state_name,
        "latitude": geo.latitude,
        "longitude": geo.longitude,
        "location": {
            "country": geo.country_name,
            "state": geo.state_name,
            "district": geo.district_name
        },
        "assessment": {
            "year": gwra_year,
            "category": category
        },
        "groundwater": {
            "depth_to_water_level_m_bgl": avg_depth,
            "groundwater_level_indicator_percent": indicator
        },
        "resources": {
            "annual_recharge_ham": recharge,
            "annual_extractable_resource_ham": extractable,
            "annual_extraction_ham": extraction,
            "stage_of_extraction_percent": stage,
            "net_groundwater_availability_ham": net_avail
        },
        "rainfall": {
            "value_mm": avg_rain,
            "rainfall_mm": avg_rain,
            "year": rain_year,
            "month": rain_month,
            "period_type": rain_period_type,
            "period": rain_period
        },
        "sources": {
            "gwra": gwra_src,
            "groundwater_level": depth_src,
            "rainfall": rain_src
        },
        # Flattened legacy fields for full backward compatibility
        "depth_to_water_level_m_bgl": avg_depth,
        "rainfall_mm": avg_rain,
        "rainfall_period": rain_period,
        "rainfall_period_type": rain_period_type,
        "rainfall_month": rain_month,
        "rainfall_year": rain_year,
        "stage_of_groundwater_extraction_percent": stage,
        "assessment_category": category,
        "observation_year": depth_year or gwra_year,
        "data_source_groundwater": depth_src,
        "data_source_rainfall": rain_src,
        "data_source_gwra": gwra_src,
        "annual_groundwater_recharge_ham": recharge,
        "annual_groundwater_extraction_ham": extraction,
        "annual_extractable_groundwater_resource_ham": extractable,
        "net_groundwater_availability_ham": net_avail,
        "groundwater_data": historical_data,
        "data_quality": dq
    }

    _district_cache.set(geo.id, res)
    return res

@router.get("")
def get_districts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Fetch basic list of all districts for selectors and dropdown menus. Cached in-memory.
    """
    cached = _districts_list_cache.get("districts_dropdown")
    if cached is not None:
        return cached

    geos = db.query(Geography).filter(
        Geography.normalized_mandal_name == None,
        Geography.normalized_village_name == None
    ).order_by(Geography.state_name, Geography.district_name).all()

    res = [
        {
            "id": g.id,
            "district_name": g.district_name,
            "state_name": g.state_name,
            "latitude": g.latitude,
            "longitude": g.longitude
        } for g in geos
    ]
    _districts_list_cache.set("districts_dropdown", res)
    return res

@router.get("/map")
def get_districts_map(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Fetch comprehensive map data for all districts with latest metrics.
    Fully cached in memory with fast thread-safe resolution.
    """
    cached = _map_cache.get("all_districts_map")
    if cached is not None:
        return cached

    geos = db.query(Geography).filter(
        Geography.normalized_mandal_name == None,
        Geography.normalized_village_name == None
    ).order_by(Geography.district_name).all()

    if not geos:
        return []

    geo_ids = [g.id for g in geos]

    # Batch fetch GWRA assessments
    gwra_rows = db.query(GWRAAssessment).filter(GWRAAssessment.geography_id.in_(geo_ids)).all()
    gwra_map = {g.geography_id: g for g in gwra_rows}

    # Batch query for average coordinates
    coords_rows = db.query(
        Geography.normalized_state_name,
        Geography.normalized_district_name,
        func.avg(Geography.latitude).label("avg_lat"),
        func.avg(Geography.longitude).label("avg_lon")
    ).filter(
        Geography.latitude != None,
        Geography.longitude != None
    ).group_by(
        Geography.normalized_state_name,
        Geography.normalized_district_name
    ).all()
    coords_map = {(r[0], r[1]): (r[2], r[3]) for r in coords_rows}

    missing_coords_fallback = {
        ("gujarat", "dohad"): (22.8378, 74.2492),
        ("telangana", "jagityal"): (18.7918, 78.9103),
        ("uttar pradesh", "g.b.nagar"): (28.5355, 77.3910),
        ("gujarat", "dahod"): (22.8378, 74.2492),
        ("telangana", "jagtial"): (18.7918, 78.9103),
        ("uttar pradesh", "gautam buddha nagar"): (28.5355, 77.3910),
    }

    # Batch fetch latest observation depths using index on geography_id
    obs_rows = db.query(
        GroundwaterObservation.geography_id,
        GroundwaterObservation.depth_to_water_level_m_bgl,
        GroundwaterObservation.observation_year
    ).filter(
        GroundwaterObservation.geography_id.in_(geo_ids),
        GroundwaterObservation.depth_to_water_level_m_bgl != None
    ).all()

    obs_by_geo_year = defaultdict(lambda: defaultdict(list))
    for gid, depth, yr in obs_rows:
        obs_by_geo_year[gid][yr].append(depth)

    depth_avg_by_geo = {}
    for gid, year_dict in obs_by_geo_year.items():
        if year_dict:
            max_yr = max(year_dict.keys())
            depth_avg_by_geo[gid] = round(sum(year_dict[max_yr]) / len(year_dict[max_yr]), 2)

    # Batch fetch latest rainfall records using index on geography_id
    rain_rows = db.query(
        RainfallRecord.geography_id,
        RainfallRecord.rainfall_mm,
        RainfallRecord.rainfall_year
    ).filter(
        RainfallRecord.geography_id.in_(geo_ids),
        RainfallRecord.rainfall_mm != None
    ).all()

    rain_by_geo_year = defaultdict(lambda: defaultdict(list))
    for gid, rain, yr in rain_rows:
        rain_by_geo_year[gid][yr].append(rain)

    rain_avg_by_geo = {}
    for gid, year_dict in rain_by_geo_year.items():
        if year_dict:
            max_yr = max(year_dict.keys())
            rain_avg_by_geo[gid] = round(sum(year_dict[max_yr]) / len(year_dict[max_yr]), 1)

    output = []
    for geo in geos:
        gwra = gwra_map.get(geo.id)
        avg_depth = depth_avg_by_geo.get(geo.id)
        avg_rain = rain_avg_by_geo.get(geo.id)

        if avg_depth is None:
            avg_depth = get_official_depth_fallback(geo.state_name, geo.district_name)
        if avg_rain is None:
            fb = get_official_rainfall_fallback(geo.state_name, geo.district_name, 2026)
            if fb:
                avg_rain = fb["value"]

        stage = gwra.stage_of_groundwater_extraction_percent if gwra else None
        recharge = gwra.annual_groundwater_recharge_ham if gwra else None
        extraction = gwra.annual_groundwater_extraction_ham if gwra else None
        extractable = gwra.annual_extractable_groundwater_resource_ham if gwra else None
        category = gwra.district_assessment_category if gwra else None

        if stage is None and extraction is not None and extractable is not None and extractable > 0:
            stage = round((extraction / extractable) * 100.0, 2)

        if stage is None or recharge is None or extractable is None or extraction is None:
            fb_gw = get_official_groundwater_fallback(geo.state_name, geo.district_name, 2025)
            if fb_gw:
                recharge = recharge if recharge is not None else fb_gw["annual_groundwater_recharge_ham"]
                extractable = extractable if extractable is not None else fb_gw["annual_extractable_groundwater_resource_ham"]
                extraction = extraction if extraction is not None else fb_gw["annual_groundwater_extraction_ham"]
                stage = stage if stage is not None else fb_gw["stage_of_groundwater_extraction_percent"]
                category = category if category is not None else fb_gw["assessment_category"]

        lat, lon = geo.latitude, geo.longitude
        if lat is None or lon is None:
            lat_lon = coords_map.get((geo.normalized_state_name, geo.normalized_district_name))
            if lat_lon:
                lat, lon = lat_lon
            else:
                lat, lon = missing_coords_fallback.get(
                    (geo.normalized_state_name, geo.normalized_district_name),
                    (None, None)
                )

        output.append({
            "id": geo.id,
            "district_name": geo.district_name,
            "state_name": geo.state_name,
            "latitude": lat,
            "longitude": lon,
            "depth_to_water_level_m_bgl": avg_depth,
            "rainfall_mm": avg_rain,
            "stage_of_groundwater_extraction_percent": stage,
            "assessment_category": category,
            "annual_groundwater_recharge_ham": recharge,
            "annual_extractable_groundwater_resource_ham": extractable,
            "annual_groundwater_extraction_ham": extraction,
        })

    _map_cache.set("all_districts_map", output)
    return output

@router.get("/search")
def search_districts(
    query: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Filter districts by name matching or state matching.
    Uses cached district map dataset for sub-millisecond response.
    """
    map_data = get_districts_map(db=db, current_user=current_user)
    if not map_data:
        return []

    filtered = map_data
    if query:
        q_clean = query.strip().lower()
        filtered = [d for d in filtered if q_clean in d["district_name"].lower()]
    if state:
        s_clean = state.strip().lower()
        filtered = [d for d in filtered if s_clean == d["state_name"].lower()]

    return [
        {
            "id": d["id"],
            "district_name": d["district_name"],
            "state_name": d["state_name"],
            "latitude": d["latitude"],
            "longitude": d["longitude"],
            "depth_to_water_level_m_bgl": d["depth_to_water_level_m_bgl"],
            "rainfall_mm": d["rainfall_mm"],
            "rainfall_period": "annual",
            "rainfall_period_type": "annual",
            "rainfall_month": None,
            "rainfall_year": 2026,
            "stage_of_groundwater_extraction_percent": d["stage_of_groundwater_extraction_percent"],
            "assessment_category": d["assessment_category"],
            "annual_groundwater_recharge_ham": d["annual_groundwater_recharge_ham"],
            "annual_groundwater_extraction_ham": d["annual_groundwater_extraction_ham"],
        }
        for d in filtered[:100]
    ]

@router.get("/{id}")
def get_district_by_id(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Retrieve single district detail. Logs a ResultAccess action. Requires auth.
    """
    geo = db.query(Geography).filter_by(id=id).first()
    if not geo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="I couldn't find this district in the available groundwater dataset."
        )

    # Track result access count
    try:
        access_log = ResultAccess(
            user_id=current_user.id,
            geography_id=geo.id,
            access_type="detail"
        )
        db.add(access_log)
        db.commit()
    except Exception:
        db.rollback()

    return resolve_district_response(db, geo)

@router.get("/{id}/statistics")
def get_district_statistics(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Retrieves chronological groundwater level data for line charts. Requires auth.
    """
    geo = db.query(Geography).filter_by(id=id).first()
    if not geo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="District not found in database."
        )

    try:
        access_log = ResultAccess(
            user_id=current_user.id,
            geography_id=geo.id,
            access_type="statistics"
        )
        db.add(access_log)
        db.commit()
    except Exception:
        db.rollback()

    details = resolve_district_response(db, geo)
    stats = sorted(details["groundwater_data"], key=lambda x: x["year"])

    return [
        {
            "year": item["year"],
            "groundwater_level": item["depth_to_water_level_m_bgl"],
            "depth_to_water_level_m_bgl": item["depth_to_water_level_m_bgl"],
            "rainfall": item["rainfall_mm"],
            "rainfall_mm": item["rainfall_mm"],
            "recharge": item["annual_groundwater_recharge_ham"],
            "annual_groundwater_recharge_ham": item["annual_groundwater_recharge_ham"],
            "extraction": item["annual_groundwater_extraction_ham"],
            "annual_groundwater_extraction_ham": item["annual_groundwater_extraction_ham"],
            "availability": item["annual_extractable_groundwater_resource_ham"],
            "annual_extractable_groundwater_resource_ham": item["annual_extractable_groundwater_resource_ham"],
            "stage_of_groundwater_extraction_percent": item["stage_of_groundwater_extraction_percent"]
        } for item in stats
    ]
