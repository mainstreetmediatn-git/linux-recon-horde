from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable

from .models import Agent, Evidence, MemoryRecord, MissionContract


class SQLiteStore:
    """Durable local persistence for Horde domain records.

    The store intentionally keeps schema and serialization simple so the
    service layer can be replaced later without changing the domain model.
    """

    def __init__(self, path: str | Path = "horde.db") -> None:
        self.path = str(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self) -> None:
        self.conn.close()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            PRAGMA foreign_keys=ON;

            CREATE TABLE IF NOT EXISTS records (
                kind TEXT NOT NULL,
                record_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (kind, record_id)
            );

            CREATE TABLE IF NOT EXISTS audit_events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                subject_id TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                payload TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS engagements (
                engagement_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                authorized INTEGER NOT NULL DEFAULT 0,
                payload TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS environments (
                environment_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    @staticmethod
    def _jsonable(value: Any) -> Any:
        if is_dataclass(value):
            value = asdict(value)
        if isinstance(value, dict):
            return {k: SQLiteStore._jsonable(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [SQLiteStore._jsonable(v) for v in value]
        if hasattr(value, "value"):
            return value.value
        return value

    def _put(self, kind: str, record_id: str, payload: Any) -> None:
        body = json.dumps(self._jsonable(payload), sort_keys=True)
        self.conn.execute(
            """
            INSERT INTO records(kind, record_id, payload)
            VALUES (?, ?, ?)
            ON CONFLICT(kind, record_id)
            DO UPDATE SET payload=excluded.payload, updated_at=CURRENT_TIMESTAMP
            """,
            (kind, record_id, body),
        )
        self.conn.commit()

    def _get(self, kind: str, record_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT payload FROM records WHERE kind=? AND record_id=?",
            (kind, record_id),
        ).fetchone()
        return json.loads(row["payload"]) if row else None

    def _list(self, kind: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT payload FROM records WHERE kind=? ORDER BY updated_at DESC",
            (kind,),
        ).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def save_agent(self, agent: Agent) -> None:
        self._put("agent", agent.agent_id, agent)

    def get_agent(self, agent_id: str) -> dict[str, Any] | None:
        return self._get("agent", agent_id)

    def list_agents(self) -> list[dict[str, Any]]:
        return self._list("agent")

    def save_mission(self, mission: MissionContract) -> None:
        self._put("mission", mission.mission_id, mission)

    def get_mission(self, mission_id: str) -> dict[str, Any] | None:
        return self._get("mission", mission_id)

    def list_missions(self) -> list[dict[str, Any]]:
        return self._list("mission")

    def save_evidence(self, evidence: Evidence) -> None:
        self._put("evidence", evidence.evidence_id, evidence)

    def list_evidence(self) -> list[dict[str, Any]]:
        return self._list("evidence")

    def save_memory(self, memory: MemoryRecord) -> None:
        self._put("memory", memory.memory_id, memory)

    def list_memory(self) -> list[dict[str, Any]]:
        return self._list("memory")

    def append_audit(self, event_type: str, subject_id: str, occurred_at: str, payload: dict[str, Any]) -> int:
        cur = self.conn.execute(
            "INSERT INTO audit_events(event_type, subject_id, occurred_at, payload) VALUES (?, ?, ?, ?)",
            (event_type, subject_id, occurred_at, json.dumps(self._jsonable(payload), sort_keys=True)),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list_audit(self, *, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT seq, event_type, subject_id, occurred_at, payload FROM audit_events ORDER BY seq DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            {
                "seq": row["seq"],
                "event_type": row["event_type"],
                "subject_id": row["subject_id"],
                "occurred_at": row["occurred_at"],
                "payload": json.loads(row["payload"]),
            }
            for row in rows
        ]

    def save_engagement(self, engagement_id: str, name: str, status: str, authorized: bool, payload: dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT INTO engagements(engagement_id, name, status, authorized, payload)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(engagement_id)
            DO UPDATE SET name=excluded.name, status=excluded.status,
                          authorized=excluded.authorized, payload=excluded.payload
            """,
            (engagement_id, name, status, int(authorized), json.dumps(self._jsonable(payload), sort_keys=True)),
        )
        self.conn.commit()

    def get_engagement(self, engagement_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM engagements WHERE engagement_id=?",
            (engagement_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "engagement_id": row["engagement_id"],
            "name": row["name"],
            "status": row["status"],
            "authorized": bool(row["authorized"]),
            "payload": json.loads(row["payload"]),
        }

    def save_environment(self, environment_id: str, name: str, status: str, payload: dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT INTO environments(environment_id, name, status, payload)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(environment_id)
            DO UPDATE SET name=excluded.name, status=excluded.status, payload=excluded.payload
            """,
            (environment_id, name, status, json.dumps(self._jsonable(payload), sort_keys=True)),
        )
        self.conn.commit()

    def list_environments(self) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM environments ORDER BY name").fetchall()
        return [
            {
                "environment_id": row["environment_id"],
                "name": row["name"],
                "status": row["status"],
                "payload": json.loads(row["payload"]),
            }
            for row in rows
        ]

    def checkpoint(self) -> None:
        self.conn.execute("PRAGMA wal_checkpoint(FULL)")
