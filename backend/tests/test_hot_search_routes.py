from io import BytesIO

from fastapi import FastAPI
from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes_hot_search import router
from app.db import Base, get_db
from app.models import HotSearchTerm


def _client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    def override_db():
        try:
            yield db
        finally:
            pass

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = override_db
    return TestClient(app), db


def _xlsx_bytes() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["排名", "搜索词主分类", "关键词", "搜索UV指数", "机会指数", "成交金额指数", "销售量指数"])
    sheet.append([1, "儿童裤子", "男童裤子薄款", 1000, 4, 30000, 500])
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_hot_search_config_routes_read_and_update():
    client, _db = _client()

    assert client.get("/api/hot-search/config").json()["enabled_by_default"] is False

    response = client.put("/api/hot-search/config", json={"enabled_by_default": True, "updated_by": "tester"})

    assert response.status_code == 200
    assert response.json()["enabled_by_default"] is True
    assert client.get("/api/hot-search/config").json()["enabled_by_default"] is True


def test_hot_search_import_route_saves_uploaded_source():
    client, db = _client()

    response = client.post(
        "/api/hot-search/import",
        files={
            "file": (
                "hot-search.xlsx",
                _xlsx_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["imported_count"] == 1
    assert db.query(HotSearchTerm).one().keyword == "男童裤子薄款"
