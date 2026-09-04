"""
Prediction and Scenario Forecasting API Endpoints for IN-GRES AI.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.routes.auth import get_current_user
from app.models import User
from app.services.prediction_service import WaterLevelPredictionService

router = APIRouter(prefix="/api/prediction", tags=["Water Level Prediction & Forecasting"])


@router.get("/scenarios", summary="Get supported prediction climate and conservation scenarios")
def get_scenarios():
    """Returns metadata for all available predictive scenarios."""
    return {
        "status": "success",
        "scenarios": WaterLevelPredictionService.get_supported_scenarios()
    }


@router.get("/district/{district_name}", summary="Predict future groundwater levels and risk trajectory")
def predict_district_water_level(
    district_name: str,
    years_ahead: int = Query(5, ge=1, le=10, description="Forecast horizon in years (1-10)"),
    scenario: str = Query("normal", description="Scenario key: normal, drought, surplus, conservation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Predicts multi-year groundwater levels (m bgl), stage of extraction (%), and GWRA categories
    for the specified district using hydro-statistical trend modeling and climate scenario factors.
    """
    res = WaterLevelPredictionService.predict_district(
        db=db,
        district_name=district_name,
        years_ahead=years_ahead,
        scenario_key=scenario
    )

    if not res:
        raise HTTPException(
            status_code=404,
            detail=f"District '{district_name}' not found in database or insufficient observation data available."
        )

    return res
