import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.services.prediction_service import WaterLevelPredictionService
from app.routes.auth import create_access_token
from app.models import User

@pytest.fixture
def db_session():
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture
def auth_headers(db_session):
    user = db_session.query(User).first()
    if not user:
        user = User(email="test_pred@example.com", name="Test Pred", password_hash="hash", role="USER")
        db_session.add(user)
        db_session.commit()
    token = create_access_token({"email": user.email, "role": user.role})
    return {"Authorization": f"Bearer {token}"}


def test_water_level_prediction_service(db_session):
    res = WaterLevelPredictionService.predict_district(
        db=db_session,
        district_name="Ananthapuramu",
        years_ahead=5,
        scenario_key="normal"
    )
    assert res is not None
    assert res["district_name"] == "Ananthapuramu"
    assert "baseline" in res
    assert res["baseline"]["depth_to_water_level_m_bgl"] is not None
    assert len(res["projected_series"]) == 5
    assert res["projected_series"][0]["year"] == res["baseline"]["year"] + 1
    assert res["projected_series"][-1]["year"] == res["baseline"]["year"] + 5
    assert len(res["all_scenarios_comparison"]) == 4
    assert len(res["insights"]) >= 3

def test_water_level_prediction_scenarios_sensitivity(db_session):
    normal_res = WaterLevelPredictionService.predict_district(db_session, "Ananthapuramu", years_ahead=5, scenario_key="normal")
    drought_res = WaterLevelPredictionService.predict_district(db_session, "Ananthapuramu", years_ahead=5, scenario_key="drought")
    conservation_res = WaterLevelPredictionService.predict_district(db_session, "Ananthapuramu", years_ahead=5, scenario_key="conservation")

    # In drought, final depth should be deeper (higher value m bgl) than normal
    assert drought_res["projected_series"][-1]["depth_to_water_level_m_bgl"] > normal_res["projected_series"][-1]["depth_to_water_level_m_bgl"]
    # In conservation, final depth should be shallower (lower value m bgl) than normal
    assert conservation_res["projected_series"][-1]["depth_to_water_level_m_bgl"] < normal_res["projected_series"][-1]["depth_to_water_level_m_bgl"]

def test_prediction_api_endpoint(auth_headers):
    client = TestClient(app)
    # 1. Scenarios endpoint
    resp_scen = client.get("/api/prediction/scenarios")
    assert resp_scen.status_code == 200
    scens = resp_scen.json()["scenarios"]
    assert "normal" in scens
    assert "drought" in scens
    assert "conservation" in scens

    # 2. District prediction endpoint
    resp_pred = client.get("/api/prediction/district/Ananthapuramu?years_ahead=4&scenario=drought", headers=auth_headers)
    assert resp_pred.status_code == 200
    data = resp_pred.json()
    assert data["district_name"] == "Ananthapuramu"
    assert len(data["projected_series"]) == 4
    assert data["selected_scenario"]["key"] == "drought"

def test_chatbot_prediction_intent(auth_headers):
    client = TestClient(app)
    # Chat query asking to predict future water level
    chat_payload = {
        "query": "Predict future water level in Kadapa"
    }
    resp = client.post("/api/ai/chat", json=chat_payload, headers=auth_headers)
    assert resp.status_code == 200
    res_json = resp.json()
    assert "🔮 Future Groundwater Level Prediction" in res_json["response"]
    assert "Kadapa" in res_json["response"] or "YSR Kadapa" in res_json["response"]
    assert "Multi-Year Model Projections" in res_json["response"]
