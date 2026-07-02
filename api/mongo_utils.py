import os
from typing import Any, Dict, List


class MongoLogStore:
    """Simple MongoDB integration helper for activity and analytics documents."""

    def __init__(self, uri: str | None = None):
        self.uri = uri or os.getenv("MONGO_URI", "mongodb://mongodb:27017/")

    def _get_client(self):
        try:
            from pymongo import MongoClient
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("pymongo is not installed") from exc
        return MongoClient(self.uri)

    def append_activity(self, payload: Dict[str, Any]) -> None:
        try:
            client = self._get_client()
            db = client.get_default_database() if client is not None else None
            if db is None:
                return
            db.activity_logs.insert_one(payload)
        except Exception:
            return

    def append_analytics(self, payload: Dict[str, Any]) -> None:
        try:
            client = self._get_client()
            db = client.get_default_database() if client is not None else None
            if db is None:
                return
            db.learning_analytics.insert_one(payload)
        except Exception:
            return

    def get_analytics_report(self, course_id: int | None = None) -> List[Dict[str, Any]]:
        try:
            client = self._get_client()
            db = client.get_default_database() if client is not None else None
            if db is None:
                return []
            query = {"course_id": course_id} if course_id is not None else {}
            return list(db.learning_analytics.find(query, {"_id": 0}))
        except Exception:
            return []
