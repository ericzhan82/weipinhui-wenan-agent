import os
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.api import (
    routes_copies,
    routes_excel,
    routes_health,
    routes_history,
    routes_hot_search,
    routes_learning,
    routes_llm,
    routes_products,
    routes_rules,
    routes_skus,
)
from app.db import Base, SessionLocal, engine
from app.seed import seed_default_rules
from app.services.hot_search_service import seed_default_hot_search_avoid_rules

app = FastAPI(title="Vipshop Kidswear Copy Agent System")


def cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost,http://127.0.0.1,http://localhost:5173,http://127.0.0.1:5173").strip()
    if raw == "*":
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=os.getenv("CORS_ALLOW_CREDENTIALS", "false").lower() == "true",
    allow_methods=["*"],
    allow_headers=["*"],
)


def wait_for_database(max_attempts: int = 30, delay_seconds: float = 2.0) -> None:
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return
        except OperationalError:
            if attempt == max_attempts:
                raise
            time.sleep(delay_seconds)


@app.on_event("startup")
def on_startup() -> None:
    wait_for_database()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_default_rules(db)
        seed_default_hot_search_avoid_rules(db)
    finally:
        db.close()


app.include_router(routes_health.router)
app.include_router(routes_llm.router)
app.include_router(routes_products.router)
app.include_router(routes_skus.router)
app.include_router(routes_copies.router)
app.include_router(routes_rules.router)
app.include_router(routes_history.router)
app.include_router(routes_hot_search.router)
app.include_router(routes_learning.router)
app.include_router(routes_excel.router)
