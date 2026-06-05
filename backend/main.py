import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    routes_auth,
    routes_copy_batches,
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
    routes_workspaces,
)
from app.runtime import initialize_runtime

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

@app.on_event("startup")
def on_startup() -> None:
    initialize_runtime(recover_batches=True)


app.include_router(routes_auth.router)
app.include_router(routes_workspaces.router)
app.include_router(routes_health.router)
app.include_router(routes_llm.router)
app.include_router(routes_products.router)
app.include_router(routes_skus.router)
app.include_router(routes_copies.router)
app.include_router(routes_copy_batches.router)
app.include_router(routes_rules.router)
app.include_router(routes_history.router)
app.include_router(routes_hot_search.router)
app.include_router(routes_learning.router)
app.include_router(routes_excel.router)
