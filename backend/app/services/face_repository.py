import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from bson import ObjectId
from app.db.mongo import db_manager

logger = logging.getLogger("uvicorn.error")


class FaceRepository:
    _active_embeddings_cache: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def invalidate_cache(cls):
        """Clears in-memory active embeddings cache."""
        cls._active_embeddings_cache = None

    @classmethod
    def save_embedding(
        cls,
        student_id: str,
        embedding: List[float],
        model_name: str = "buffalo_s",
        sample_index: int = 1,
    ) -> str:
        """Stores numerical face embedding vector in face_embeddings collection."""
        db = db_manager.db
        if db is None:
            raise RuntimeError("Database connection unavailable")

        now = datetime.now(timezone.utc)
        doc = {
            "student_id": student_id,
            "embedding": embedding,
            "model_name": model_name,
            "embedding_dimension": len(embedding),
            "sample_index": sample_index,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }

        res = db.face_embeddings.insert_one(doc)
        cls.invalidate_cache()
        return str(res.inserted_id)

    @classmethod
    def get_student_embeddings(cls, student_id: str) -> List[Dict[str, Any]]:
        """Retrieves active embedding records for a specific student."""
        db = db_manager.db
        if db is None:
            return []
        query = {"student_id": student_id, "is_active": True}
        docs = list(db.face_embeddings.find(query).sort("created_at", 1))
        for d in docs:
            d["id"] = str(d["_id"])
            del d["_id"]
        return docs

    @classmethod
    def get_all_active_embeddings(cls) -> List[Dict[str, Any]]:
        """Retrieves all active embedding records across all students for recognition matching."""
        if cls._active_embeddings_cache is not None:
            return cls._active_embeddings_cache

        db = db_manager.db
        if db is None:
            return []
        query = {"is_active": True}
        docs = list(db.face_embeddings.find(query))
        result = []
        for d in docs:
            d["id"] = str(d["_id"])
            del d["_id"]
            result.append(d)
        cls._active_embeddings_cache = result
        return result

    @classmethod
    def deactivate_student_embeddings(cls, student_id: str) -> int:
        """Soft-deactivates all registered face embeddings for a student."""
        db = db_manager.db
        if db is None:
            return 0
        now = datetime.now(timezone.utc)
        res = db.face_embeddings.update_many(
            {"student_id": student_id, "is_active": True},
            {"$set": {"is_active": False, "updated_at": now}},
        )
        cls.invalidate_cache()
        return res.modified_count
