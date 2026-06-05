import logging
import os
import time
from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.bootstrap import assign_legacy_data_to_workspace, ensure_runtime_schema, seed_default_workspace_and_admin
from app.db import Base, SessionLocal, engine
from app.seed import seed_default_rules
from app.services.copy_batch_service import recover_running_batches
from app.services.hot_search_service import seed_default_hot_search_avoid_rules

logger = logging.getLogger(__name__)
_RUNTIME_LOCK_ID = 827364019


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


@contextmanager
def runtime_init_lock():
    if engine.dialect.name != "postgresql":
        yield
        return
    with engine.connect() as connection:
        connection.execute(text("SELECT pg_advisory_lock(:lock_id)"), {"lock_id": _RUNTIME_LOCK_ID})
        connection.commit()
        try:
            yield
        finally:
            connection.execute(text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": _RUNTIME_LOCK_ID})
            connection.commit()


def initialize_runtime(recover_batches: bool = True) -> None:
    wait_for_database(
        max_attempts=int(os.getenv("DB_STARTUP_MAX_ATTEMPTS", "30")),
        delay_seconds=float(os.getenv("DB_STARTUP_DELAY_SECONDS", "2")),
    )
    with runtime_init_lock():
        Base.metadata.create_all(bind=engine)
        ensure_runtime_schema(engine)
        db = SessionLocal()
        try:
            workspace = seed_default_workspace_and_admin(db)
            seed_default_rules(db)
            seed_default_hot_search_avoid_rules(db, workspace.id)
            assign_legacy_data_to_workspace(db, workspace.id)
            if recover_batches:
                recover_running_batches(db)
        finally:
            db.close()
    logger.info("runtime initialized")
