import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import User, QueryHistory, Conversation, ConversationMessage, Geography
from app.routes.auth import create_access_token
from app.utils.auth import get_password_hash

@pytest.fixture
def db_session():
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture
def admin_auth(db_session):
    admin = db_session.query(User).filter_by(role="ADMIN").first()
    if not admin:
        admin = User(
            email="admin_history_test@example.com",
            name="Admin History Test",
            password_hash=get_password_hash("admin123"),
            role="ADMIN"
        )
        db_session.add(admin)
        db_session.commit()
    token = create_access_token({"email": admin.email, "role": admin.role})
    return {"Authorization": f"Bearer {token}"}, admin

@pytest.fixture
def regular_user_auth(db_session):
    user = db_session.query(User).filter_by(email="regular_history_test@example.com").first()
    if not user:
        user = User(
            email="regular_history_test@example.com",
            name="Regular History User",
            password_hash=get_password_hash("pass123"),
            role="USER"
        )
        db_session.add(user)
        db_session.commit()
    token = create_access_token({"email": user.email, "role": user.role})
    return {"Authorization": f"Bearer {token}"}, user

def test_admin_user_history_controls(db_session, admin_auth, regular_user_auth):
    admin_headers, admin = admin_auth
    user_headers, user = regular_user_auth
    client = TestClient(app)

    # 1. Create a geography for testing queries if not exists
    geo = db_session.query(Geography).first()
    if not geo:
        geo = Geography(district_name="TestDistrict", state_name="Andhra Pradesh")
        db_session.add(geo)
        db_session.commit()

    # 2. Add some test query records for the user
    q1 = QueryHistory(
        user_id=user.id,
        geography_id=geo.id,
        query="What is the water level in TestDistrict?",
        response="Water level is 12.5 m bgl."
    )
    q2 = QueryHistory(
        user_id=user.id,
        geography_id=geo.id,
        query="Compare rainfall with last year",
        response="Rainfall increased by 10%."
    )
    db_session.add_all([q1, q2])

    # 3. Add a test conversation and message
    conv = Conversation(
        user_id=user.id,
        conversation_id=f"test-conv-{user.id}",
        last_user_question="Water level discussion"
    )
    db_session.add(conv)
    db_session.commit()

    msg = ConversationMessage(
        conversation_id=conv.conversation_id,
        sender="user",
        text="Hello assistant"
    )
    db_session.add(msg)
    db_session.commit()

    # 4. Test GET /api/admin/users/{user_id}/history
    resp = client.get(f"/api/admin/users/{user.id}/history", headers=admin_headers)
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) >= 2
    query_texts = [item["query"] for item in history]
    assert "What is the water level in TestDistrict?" in query_texts
    assert "Compare rainfall with last year" in query_texts

    # 5. Non-admin should be forbidden
    non_admin_resp = client.get(f"/api/admin/users/{user.id}/history", headers=user_headers)
    assert non_admin_resp.status_code in [401, 403]

    # 6. Test DELETE /api/admin/queries/{query_id} (Delete a single query)
    del_single_resp = client.delete(f"/api/admin/queries/{q1.id}", headers=admin_headers)
    assert del_single_resp.status_code == 200
    assert "deleted successfully" in del_single_resp.json()["message"]

    # Verify q1 is gone
    check_q1 = db_session.query(QueryHistory).filter_by(id=q1.id).first()
    assert check_q1 is None

    # 7. Test filtered query search: GET /api/admin/queries?search=rainfall
    search_resp = client.get("/api/admin/queries?search=rainfall", headers=admin_headers)
    assert search_resp.status_code == 200
    search_results = search_resp.json()
    assert any("rainfall" in r["query"].lower() or "rainfall" in r["response"].lower() for r in search_results)

    # 8. Test DELETE /api/admin/users/{user_id}/history (Clear entire user history)
    clear_user_resp = client.delete(f"/api/admin/users/{user.id}/history", headers=admin_headers)
    assert clear_user_resp.status_code == 200
    assert f"for {user.email}" in clear_user_resp.json()["message"]

    # Verify user's queries are 0 and conversations are cleaned
    user_queries_count = db_session.query(QueryHistory).filter_by(user_id=user.id).count()
    assert user_queries_count == 0
    user_convs_count = db_session.query(Conversation).filter_by(user_id=user.id).count()
    assert user_convs_count == 0

    # 9. Test DELETE /api/admin/queries/clear-all
    # Add one query to clear
    dummy_q = QueryHistory(
        user_id=admin.id,
        geography_id=geo.id,
        query="Admin test query",
        response="Admin test response"
    )
    db_session.add(dummy_q)
    db_session.commit()

    clear_all_resp = client.delete("/api/admin/queries/clear-all", headers=admin_headers)
    assert clear_all_resp.status_code == 200
    assert "purged all" in clear_all_resp.json()["message"].lower()

    total_queries_left = db_session.query(QueryHistory).count()
    assert total_queries_left == 0
