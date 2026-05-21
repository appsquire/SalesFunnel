from fastapi.testclient import TestClient

from app.main import app


def test_legal_terms_from_legacy():
    with TestClient(app) as client:
        r = client.get("/api/legal/terms")
    assert r.status_code == 200
    data = r.json()
    assert data["format"] == "html"
    assert "Key Summary" in data["body"] or "ENERGY AGREEMENT" in data["body"]
    assert "termscontainer" in data["body"]


def test_legal_disclosure_from_legacy():
    with TestClient(app) as client:
        r = client.get("/api/legal/disclosure")
    assert r.status_code == 200
    data = r.json()
    assert "Disclosure Statement to Consumers" in data["body"]
    assert "marketing contract" in data["body"].lower() or "electricity or gas" in data["body"].lower()


def test_legal_faq_from_legacy():
    with TestClient(app) as client:
        r = client.get("/api/legal/faq")
    assert r.status_code == 200
    assert len(r.json()["body"]) > 500
