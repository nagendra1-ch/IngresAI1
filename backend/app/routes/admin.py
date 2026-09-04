from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional

from app.database import get_db
from app.models import (
    User, QueryHistory, ResultAccess, Geography, GWRAAssessment,
    RainfallRecord, GroundwaterObservation, Conversation, ConversationMessage
)
from app.routes.auth import get_admin_user
from app.schemas.admin import (
    AdminSummary,
    AdminQueryLog,
    DistrictAccessStat,
    AdminUserLog,
    UserRoleUpdate,
    UserPasswordReset,
    DataEditorRecord,
    DataEditorUpdate,
    DataEditorListResponse
)
from app.services.excel_service import ExcelService
from app.utils.auth import get_password_hash

router = APIRouter(prefix="/api/admin", tags=["Admin Panel"])

@router.get("/statistics", response_model=AdminSummary)
def get_admin_statistics(db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    """
    Computes overall summary metrics for the Admin Dashboard. Requires ADMIN.
    """
    total_users = db.query(User).count()
    total_queries = db.query(QueryHistory).count()
    
    dist_accessed_query = db.query(func.count(func.distinct(ResultAccess.geography_id))).scalar()
    districts_accessed = dist_accessed_query if dist_accessed_query else 0
    
    # Identify the most viewed district
    most_viewed = db.query(
        ResultAccess.geography_id,
        func.count(ResultAccess.id).label("cnt")
    ).group_by(ResultAccess.geography_id).order_by(func.count(ResultAccess.id).desc()).first()
    
    most_viewed_district = "None"
    most_viewed_district_views = 0
    if most_viewed:
        dist = db.query(Geography).filter_by(id=most_viewed[0]).first()
        if dist:
            most_viewed_district = dist.district_name
            most_viewed_district_views = most_viewed[1]
            
    avg_queries = total_queries / total_users if total_users > 0 else 0.0
    
    return {
        "total_users": total_users,
        "total_queries": total_queries,
        "districts_accessed": districts_accessed,
        "most_viewed_district": most_viewed_district,
        "most_viewed_district_views": most_viewed_district_views,
        "avg_queries_per_user": avg_queries
    }

from sqlalchemy.orm import joinedload

@router.get("/users", response_model=List[AdminUserLog])
def get_admin_users(db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    """
    Exposes user management stats (registration date, activity count). Requires ADMIN.
    """
    users = db.query(User).order_by(User.created_at.desc()).all()
    user_counts = db.query(QueryHistory.user_id, func.count(QueryHistory.id)).group_by(QueryHistory.user_id).all()
    counts_map = dict(user_counts)
    
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "created_at": u.created_at,
            "queries_count": counts_map.get(u.id, 0)
        } for u in users
    ]

@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Promote or demote a user role between 'USER' and 'ADMIN'.
    """
    target_user = db.query(User).filter_by(id=user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    role = payload.role.upper().strip()
    if role not in ["USER", "ADMIN"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'USER' or 'ADMIN'.")
    
    if target_user.id == current_user.id and role != "ADMIN":
        raise HTTPException(status_code=400, detail="Cannot demote your own active administrator account.")
    
    target_user.role = role
    db.commit()
    db.refresh(target_user)
    return {"message": f"User {target_user.email} role updated to {role}", "user_id": target_user.id, "role": target_user.role}

@router.post("/users/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    payload: UserPasswordReset,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Reset a user's password directly from the Admin panel.
    """
    target_user = db.query(User).filter_by(id=user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_pwd = payload.new_password.strip()
    if len(new_pwd) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters long.")
    
    target_user.password_hash = get_password_hash(new_pwd)
    db.commit()
    return {"message": f"Password for {target_user.email} has been successfully reset."}

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Delete a user account and clean up associated records.
    """
    target_user = db.query(User).filter_by(id=user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own active administrator account.")
    
    user_email = target_user.email
    try:
        # Clean up conversations & messages
        user_convs = db.query(Conversation).filter_by(user_id=target_user.id).all()
        for conv in user_convs:
            db.query(ConversationMessage).filter_by(conversation_id=conv.conversation_id).delete(synchronize_session=False)
            db.delete(conv)
        
        # Clean up queries and result accesses
        db.query(QueryHistory).filter_by(user_id=target_user.id).delete(synchronize_session=False)
        db.query(ResultAccess).filter_by(user_id=target_user.id).delete(synchronize_session=False)
        
        # Delete user
        db.delete(target_user)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")

    return {"message": f"User {user_email} deleted successfully."}

@router.get("/users/{user_id}/history", response_model=List[AdminQueryLog])
def get_user_query_history(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Retrieve the entire query history of a specific user. Requires ADMIN.
    """
    target_user = db.query(User).filter_by(id=user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    queries = db.query(QueryHistory).options(
        joinedload(QueryHistory.user),
        joinedload(QueryHistory.geography)
    ).filter_by(user_id=user_id).order_by(QueryHistory.created_at.desc()).all()

    out = []
    for q in queries:
        username = q.user.name if q.user else target_user.name
        email = q.user.email if q.user else target_user.email
        dist_name = q.geography.district_name if q.geography else "N/A"
        out.append({
            "id": q.id,
            "username": username,
            "email": email,
            "query": q.query,
            "response": q.response,
            "district_name": dist_name,
            "created_at": q.created_at
        })
    return out

@router.delete("/users/{user_id}/history")
def clear_user_history(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Purge all query logs and conversation sessions for a specific user. Requires ADMIN.
    """
    target_user = db.query(User).filter_by(id=user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        q_count = db.query(QueryHistory).filter_by(user_id=user_id).delete(synchronize_session=False)
        convs = db.query(Conversation).filter_by(user_id=user_id).all()
        for conv in convs:
            db.query(ConversationMessage).filter_by(conversation_id=conv.conversation_id).delete(synchronize_session=False)
            db.delete(conv)
        db.commit()
        return {"message": f"Successfully cleared {q_count} query logs and conversations for {target_user.email}."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear user history: {str(e)}")

@router.delete("/queries/clear-all")
def clear_all_queries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Bulk purge all system-wide query history logs. Requires ADMIN.
    """
    try:
        deleted_count = db.query(QueryHistory).delete(synchronize_session=False)
        db.commit()
        return {"message": f"Successfully purged all {deleted_count} query history logs."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear query logs: {str(e)}")

@router.delete("/queries/{query_id}")
def delete_admin_query(
    query_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Delete a specific query history log by ID. Requires ADMIN.
    """
    query_rec = db.query(QueryHistory).filter_by(id=query_id).first()
    if not query_rec:
        raise HTTPException(status_code=404, detail="Query record not found")

    db.delete(query_rec)
    db.commit()
    return {"message": f"Query log #{query_id} has been deleted successfully."}

@router.get("/queries", response_model=List[AdminQueryLog])
def get_admin_queries(
    search: Optional[str] = Query(None, description="Search query, email, or district"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    limit: int = Query(250, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Lists query records with joinedload and optional search. Requires ADMIN.
    """
    query = db.query(QueryHistory).options(
        joinedload(QueryHistory.user),
        joinedload(QueryHistory.geography)
    )

    if user_id:
        query = query.filter(QueryHistory.user_id == user_id)

    if search and search.strip():
        s = f"%{search.strip()}%"
        query = query.outerjoin(User, QueryHistory.user_id == User.id)\
                     .outerjoin(Geography, QueryHistory.geography_id == Geography.id)\
                     .filter(or_(
                         QueryHistory.query.ilike(s),
                         QueryHistory.response.ilike(s),
                         User.name.ilike(s),
                         User.email.ilike(s),
                         Geography.district_name.ilike(s)
                     ))

    queries = query.order_by(QueryHistory.created_at.desc()).limit(limit).all()

    out = []
    for q in queries:
        username = q.user.name if q.user else "Unknown"
        email = q.user.email if q.user else "Unknown"
        dist_name = q.geography.district_name if q.geography else "N/A"
        out.append({
            "id": q.id,
            "username": username,
            "email": email,
            "query": q.query,
            "response": q.response,
            "district_name": dist_name,
            "created_at": q.created_at
        })
    return out


@router.get("/access-statistics", response_model=List[DistrictAccessStat])
def get_admin_access_statistics(db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    """
    Calculates view logs per district using a single joined SQL query. Requires ADMIN.
    """
    stats = db.query(
        Geography.district_name,
        Geography.state_name,
        func.count(ResultAccess.id).label("total_views"),
        func.count(func.distinct(ResultAccess.user_id)).label("unique_users"),
        func.max(ResultAccess.accessed_at).label("last_accessed")
    ).join(Geography, ResultAccess.geography_id == Geography.id).group_by(
        Geography.district_name,
        Geography.state_name
    ).order_by(func.count(ResultAccess.id).desc()).all()
    
    return [
        {
            "district_name": s[0],
            "state_name": s[1],
            "total_views": s[2],
            "unique_users": s[3],
            "last_accessed": s[4]
        } for s in stats
    ]


@router.get("/export-excel")
def get_admin_export_excel(db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    """
    Generates a multi-sheet Excel spreadsheet and streams it to the admin browser. Requires ADMIN.
    """
    users = db.query(User).all()
    queries = db.query(QueryHistory).all()
    access_stats = get_admin_access_statistics(db, current_user)
    summary_stats = get_admin_statistics(db, current_user)
    
    excel_buffer = ExcelService.generate_admin_report(users, queries, access_stats, summary_stats)
    
    headers = {
        'Content-Disposition': 'attachment; filename="ingres_ai_admin_report.xlsx"'
    }
    
    return StreamingResponse(
        excel_buffer,
        headers=headers,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =========================================================================
# Groundwater Data Editor Endpoints
# =========================================================================

@router.get("/data-editor/records", response_model=DataEditorListResponse)
def get_data_editor_records(
    search: Optional[str] = Query(None, description="Search by district or state"),
    state: Optional[str] = Query(None, description="Filter by state"),
    category: Optional[str] = Query(None, description="Filter by category"),
    year: Optional[int] = Query(None, description="Filter by year"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Search and retrieve district assessment records with pagination for the Data Editor.
    """
    query = db.query(GWRAAssessment, Geography).join(Geography, GWRAAssessment.geography_id == Geography.id)
    
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(or_(Geography.district_name.ilike(s), Geography.state_name.ilike(s)))
    
    if state and state.lower() != "all":
        query = query.filter(Geography.state_name.ilike(f"%{state.strip()}%"))
        
    if category and category.lower() != "all":
        query = query.filter(GWRAAssessment.district_assessment_category.ilike(f"%{category.strip()}%"))
        
    if year:
        query = query.filter(GWRAAssessment.assessment_year == year)
        
    total = query.count()
    
    # Order by State, District, Year desc
    results = query.order_by(Geography.state_name.asc(), Geography.district_name.asc(), GWRAAssessment.assessment_year.desc())\
                   .offset((page - 1) * page_size).limit(page_size).all()
    
    records = []
    for gwra, geo in results:
        # Fetch rainfall record if available
        rainfall_rec = db.query(RainfallRecord).filter_by(
            geography_id=geo.id,
            rainfall_year=gwra.assessment_year
        ).first()
        rainfall_val = rainfall_rec.rainfall_mm if rainfall_rec else None
        
        # Fetch observation if available
        obs_rec = db.query(GroundwaterObservation).filter_by(
            geography_id=geo.id,
            observation_year=gwra.assessment_year
        ).first()
        depth_val = obs_rec.depth_to_water_level_m_bgl if obs_rec else None
        
        records.append({
            "id": gwra.id,
            "geography_id": geo.id,
            "state_name": geo.state_name,
            "district_name": geo.district_name,
            "assessment_year": gwra.assessment_year,
            "annual_groundwater_recharge_ham": gwra.annual_groundwater_recharge_ham,
            "annual_extractable_groundwater_resource_ham": gwra.annual_extractable_groundwater_resource_ham,
            "annual_groundwater_extraction_ham": gwra.annual_groundwater_extraction_ham,
            "stage_of_groundwater_extraction_percent": gwra.stage_of_groundwater_extraction_percent,
            "district_assessment_category": gwra.district_assessment_category,
            "rainfall_mm": rainfall_val,
            "depth_to_water_level_m_bgl": depth_val
        })
        
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "records": records
    }

@router.put("/data-editor/records/{assessment_id}", response_model=DataEditorRecord)
def update_data_editor_record(
    assessment_id: int,
    payload: DataEditorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Update groundwater metrics, stage of extraction, category, and rainfall for a specific district assessment.
    """
    gwra = db.query(GWRAAssessment).filter_by(id=assessment_id).first()
    if not gwra:
        raise HTTPException(status_code=404, detail="Assessment record not found")
        
    geo = db.query(Geography).filter_by(id=gwra.geography_id).first()
    if not geo:
        raise HTTPException(status_code=404, detail="Geography record not found")
        
    # Update GWRA fields
    if payload.annual_groundwater_recharge_ham is not None:
        gwra.annual_groundwater_recharge_ham = payload.annual_groundwater_recharge_ham
    if payload.annual_extractable_groundwater_resource_ham is not None:
        gwra.annual_extractable_groundwater_resource_ham = payload.annual_extractable_groundwater_resource_ham
    if payload.annual_groundwater_extraction_ham is not None:
        gwra.annual_groundwater_extraction_ham = payload.annual_groundwater_extraction_ham
        
    # Auto recalculate Stage % if needed
    if payload.stage_of_groundwater_extraction_percent is not None:
        gwra.stage_of_groundwater_extraction_percent = payload.stage_of_groundwater_extraction_percent
    elif gwra.annual_groundwater_extraction_ham is not None and gwra.annual_extractable_groundwater_resource_ham and gwra.annual_extractable_groundwater_resource_ham > 0:
        gwra.stage_of_groundwater_extraction_percent = round((gwra.annual_groundwater_extraction_ham / gwra.annual_extractable_groundwater_resource_ham) * 100, 2)
        
    if payload.district_assessment_category:
        gwra.district_assessment_category = payload.district_assessment_category.strip().title()
    elif gwra.stage_of_groundwater_extraction_percent is not None:
        st = gwra.stage_of_groundwater_extraction_percent
        if st <= 70.0:
            gwra.district_assessment_category = "Safe"
        elif st <= 90.0:
            gwra.district_assessment_category = "Semi-Critical"
        elif st <= 100.0:
            gwra.district_assessment_category = "Critical"
        else:
            gwra.district_assessment_category = "Over-Exploited"
            
    # Update or insert Rainfall
    rainfall_val = None
    if payload.rainfall_mm is not None:
        rainfall_rec = db.query(RainfallRecord).filter_by(
            geography_id=geo.id,
            rainfall_year=gwra.assessment_year
        ).first()
        if rainfall_rec:
            rainfall_rec.rainfall_mm = payload.rainfall_mm
        else:
            rainfall_rec = RainfallRecord(
                geography_id=geo.id,
                rainfall_year=gwra.assessment_year,
                rainfall_mm=payload.rainfall_mm,
                rainfall_period="annual"
            )
            db.add(rainfall_rec)
        rainfall_val = payload.rainfall_mm
    else:
        rainfall_rec = db.query(RainfallRecord).filter_by(geography_id=geo.id, rainfall_year=gwra.assessment_year).first()
        if rainfall_rec:
            rainfall_val = rainfall_rec.rainfall_mm
            
    # Update or insert Observation
    depth_val = None
    if payload.depth_to_water_level_m_bgl is not None:
        obs_rec = db.query(GroundwaterObservation).filter_by(
            geography_id=geo.id,
            observation_year=gwra.assessment_year
        ).first()
        if obs_rec:
            obs_rec.depth_to_water_level_m_bgl = payload.depth_to_water_level_m_bgl
        else:
            obs_rec = GroundwaterObservation(
                geography_id=geo.id,
                observation_year=gwra.assessment_year,
                depth_to_water_level_m_bgl=payload.depth_to_water_level_m_bgl,
                monitoring_station=f"{geo.district_name} Central"
            )
            db.add(obs_rec)
        depth_val = payload.depth_to_water_level_m_bgl
    else:
        obs_rec = db.query(GroundwaterObservation).filter_by(geography_id=geo.id, observation_year=gwra.assessment_year).first()
        if obs_rec:
            depth_val = obs_rec.depth_to_water_level_m_bgl

    db.commit()
    db.refresh(gwra)
    
    return {
        "id": gwra.id,
        "geography_id": geo.id,
        "state_name": geo.state_name,
        "district_name": geo.district_name,
        "assessment_year": gwra.assessment_year,
        "annual_groundwater_recharge_ham": gwra.annual_groundwater_recharge_ham,
        "annual_extractable_groundwater_resource_ham": gwra.annual_extractable_groundwater_resource_ham,
        "annual_groundwater_extraction_ham": gwra.annual_groundwater_extraction_ham,
        "stage_of_groundwater_extraction_percent": gwra.stage_of_groundwater_extraction_percent,
        "district_assessment_category": gwra.district_assessment_category,
        "rainfall_mm": rainfall_val,
        "depth_to_water_level_m_bgl": depth_val
    }
