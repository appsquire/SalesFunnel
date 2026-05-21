def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_funnel_config(client):
    r = client.get("/api/config/funnel")
    assert r.status_code == 200
    data = r.json()
    assert data["branding"]["green_charge_per_kwh"] == 0.0185


def test_step1_validation_friendly(client):
    r = client.post(
        "/api/enrollments",
        json={"step": 1, "payload": {}},
    )
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert "field_errors" in detail
    assert detail["field_errors"]["first_name"] == "This field is required."
    assert "pydantic.dev" not in detail["message"].lower()
    assert "string_too_short" not in str(detail).lower()


def test_create_and_patch_enrollment(client):
    r = client.post(
        "/api/enrollments",
        json={
            "step": 1,
            "payload": {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane@example.com",
                "primary_phone": "5875551234",
            },
        },
    )
    assert r.status_code == 200
    body = r.json()
    uuid = body["draft_uuid"]
    assert body["payload"]["first_name"] == "Jane"

    r2 = client.patch(
        f"/api/enrollments/{uuid}",
        json={"step": 2, "payload": {"birthday": "1990-01-15"}, "current_step": 2},
    )
    assert r2.status_code == 200
    assert r2.json()["payload"]["birthday"] == "1990-01-15"
