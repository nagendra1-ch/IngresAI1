from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class AdminSummary(BaseModel):
    total_users: int
    total_queries: int
    districts_accessed: int
    most_viewed_district: Optional[str] = "None"
    most_viewed_district_views: int = 0
    avg_queries_per_user: float

class AdminQueryLog(BaseModel):
    id: int
    username: str
    email: str
    query: str
    response: str
    district_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DistrictAccessStat(BaseModel):
    district_name: str
    state_name: str
    total_views: int
    unique_users: int
    last_accessed: Optional[datetime] = None

    class Config:
        from_attributes = True

class AdminUserLog(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime
    queries_count: int

    class Config:
        from_attributes = True

class UserRoleUpdate(BaseModel):
    role: str  # "USER" or "ADMIN"

class UserPasswordReset(BaseModel):
    new_password: str

class DataEditorRecord(BaseModel):
    id: int
    geography_id: int
    state_name: str
    district_name: str
    assessment_year: int
    annual_groundwater_recharge_ham: Optional[float] = None
    annual_extractable_groundwater_resource_ham: Optional[float] = None
    annual_groundwater_extraction_ham: Optional[float] = None
    stage_of_groundwater_extraction_percent: Optional[float] = None
    district_assessment_category: Optional[str] = None
    rainfall_mm: Optional[float] = None
    depth_to_water_level_m_bgl: Optional[float] = None

    class Config:
        from_attributes = True

class DataEditorUpdate(BaseModel):
    annual_groundwater_recharge_ham: Optional[float] = None
    annual_extractable_groundwater_resource_ham: Optional[float] = None
    annual_groundwater_extraction_ham: Optional[float] = None
    stage_of_groundwater_extraction_percent: Optional[float] = None
    district_assessment_category: Optional[str] = None
    rainfall_mm: Optional[float] = None
    depth_to_water_level_m_bgl: Optional[float] = None

class DataEditorListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    records: List[DataEditorRecord]
