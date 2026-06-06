from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes_copies import router
from app.auth import AuthContext, require_workspace_write
from app.db import get_db
from app.models import Product, User, Workspace


class FakeDb:
    def get(self, model, value):
        if model is Product and value == 7:
            return Product(id=7, workspace_id=1)
        return None


def _context():
    return AuthContext(
        user=User(id=1, email="tester@example.com", display_name="tester", password_hash="x", is_system_admin=True),
        workspace=Workspace(id=1, name="默认工作空间", slug="default"),
        role="system_admin",
    )


def test_generate_copy_route_passes_hot_search_override(monkeypatch):
    captured = {}

    def fake_generate_copy_for_product(db, product_id, operator_name="system", use_hot_search=None, agent_mode=None):
        captured["product_id"] = product_id
        captured["use_hot_search"] = use_hot_search
        captured["agent_mode"] = agent_mode
        return {"product_id": product_id, "hot_search_enabled": bool(use_hot_search)}

    def override_db():
        yield FakeDb()

    monkeypatch.setattr("app.api.routes_copies.generate_copy_for_product", fake_generate_copy_for_product)
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[require_workspace_write] = _context
    client = TestClient(app)

    response = client.post("/api/products/7/generate-copy", json={"use_hot_search": True})

    assert response.status_code == 200
    assert captured == {"product_id": 7, "use_hot_search": True, "agent_mode": None}
    assert response.json()["hot_search_enabled"] is True
