"""Admin utilities: database backup and import (restore)."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import DateTime
from sqlalchemy.orm import Session

from app.api.v1.deps import require_admin
from app.db.base import get_db
from app.models import Contact, Product, Service, User
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/admin", tags=["Admin"])

# Order matters: users first so that imported products/services/contacts
# can reference existing ids if needed.
MODELS = [User, Product, Service, Contact]
TABLE_NAMES = {model.__tablename__: model for model in MODELS}


@router.get("/backup")
def backup_database(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    """Export every table as JSON so it can be downloaded and restored later."""
    data = {
        "database": "bookstore",
        "exported_at": datetime.utcnow().isoformat(),
        "tables": {},
    }
    for model in MODELS:
        rows = db.query(model).all()
        data["tables"][model.__tablename__] = [
            {c.name: getattr(row, c.name) for c in model.__table__.columns}
            for row in rows
        ]
    return data


@router.post("/import", response_model=MessageResponse)
def import_database(
    payload: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> MessageResponse:
    """Replace the whole database with the contents of a backup file.

    ⚠️  This DELETES all current data in users/products/services/contacts
    and restores them from the uploaded backup.
    """
    tables = payload.get("tables")
    if not isinstance(tables, dict):
        raise HTTPException(
            status_code=400,
            detail="Invalid backup format: expected an object with a 'tables' key",
        )
    if payload.get("database") != "bookstore":
        raise HTTPException(
            status_code=400,
            detail="Not a Book Store backup file",
        )

    try:
        # 1. Delete all existing rows
        for model in MODELS:
            db.query(model).delete()
        db.commit()

        # 2. Insert rows from the backup (only known tables/columns)
        for name, model in TABLE_NAMES.items():
            rows = tables.get(name) or []
            if not isinstance(rows, list):
                raise HTTPException(status_code=400, detail=f"Invalid rows for table '{name}'")

            columns = {c.name: c for c in model.__table__.columns}
            for row in rows:
                clean = {}
                for key, value in row.items():
                    if key not in columns:
                        continue  # ignore unknown fields
                    col_type = columns[key].type
                    # Re-parse ISO datetime strings into datetime objects
                    if isinstance(col_type, DateTime) and isinstance(value, str):
                        try:
                            value = datetime.fromisoformat(value)
                        except ValueError:
                            value = None
                    clean[key] = value
                db.add(model(**clean))
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:  # noqa: BLE001 - surface a friendly message
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Import failed: {exc}",
        ) from exc

    return MessageResponse(message="Database imported successfully")
