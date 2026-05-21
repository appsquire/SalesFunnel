import pytest
from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app


@pytest.fixture
def client():
    init_db()
    with TestClient(app) as c:
        yield c
