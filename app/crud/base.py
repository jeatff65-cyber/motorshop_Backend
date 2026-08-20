"""Generic CRUD base class for simple models."""
from typing import Any, Dict, List, Optional

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session


class CRUDBase:
    def __init__(self, model):
        self.model = model

    def get(self, db: Session, obj_id: int):
        return db.get(self.model, obj_id)

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        only_active: bool = False,
    ) -> List[Any]:
        query = db.query(self.model)
        if only_active and hasattr(self.model, "is_active"):
            query = query.filter(self.model.is_active.is_(True))
        return query.order_by(self.model.id.desc()).offset(skip).limit(limit).all()

    def count(self, db: Session, *, only_active: bool = False) -> int:
        query = db.query(self.model)
        if only_active and hasattr(self.model, "is_active"):
            query = query.filter(self.model.is_active.is_(True))
        return query.count()

    def create(self, db: Session, *, obj_in):
        obj_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj, obj_in):
        if hasattr(obj_in, "model_dump"):
            update_data: Dict[str, Any] = obj_in.model_dump(exclude_unset=True)
        else:
            update_data = dict(obj_in)
        obj_data = jsonable_encoder(db_obj)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, obj_id: int):
        db_obj = db.get(self.model, obj_id)
        db.delete(db_obj)
        db.commit()
        return db_obj
