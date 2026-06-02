from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes_copies import router
from app.db import get_db


def test_generate_copy_route_passes_hot_search_override(monkeypatch):
    captured = {}

    def fake_generate_copy_for_product(db, product_id, operator_name="system", use_hot_search=None):
        captured["product_id"] = product_id
        captured["use_hot_search"] = use_hot_search
        return {"product_id": product_id, "hot_search_enabled": bool(use_hot_search)}

    def override_db():
        yield object()

    monkeypatch.setattr("app.api.routes_copies.generate_copy_for_product", fake_generate_copy_for_product)
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = override_db
    client = TestClient(app)

    response = client.post("/api/products/7/generate-copy", json={"use_hot_search": True})

    assert response.status_code == 200
    assert captured == {"product_id": 7, "use_hot_search": True}
    assert response.json()["hot_search_enabled"] is True
