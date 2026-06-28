"""SQLite persistence adapter for the platform prototype.

The production target is PostgreSQL, but SQLite gives the project durable,
testable storage immediately while preserving a repository boundary that can be
implemented by Postgres later.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from packages.schemas import CandidateEvent, Report
from services.agents import WorkflowResult


def _json_default(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if is_dataclass(value):
        return asdict(value)
    return str(value)


def _to_json(data: Any) -> str:
    return json.dumps(data, default=_json_default, sort_keys=True)


def _from_json(data: str) -> Any:
    return json.loads(data)


class SQLiteRepository:
    """Durable local repository for events, reports, decisions, and evidence."""

    def __init__(self, path: str | Path = "data/news_intelligence.db") -> None:
        self.path = Path(path)
        if self.path != Path(":memory:"):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(self.path), check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self.initialize()

    def initialize(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                severity TEXT NOT NULL,
                confidence REAL NOT NULL,
                topic_label TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reports (
                report_id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                title TEXT NOT NULL,
                confidence REAL NOT NULL,
                markdown TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(event_id) REFERENCES events(event_id)
            );

            CREATE TABLE IF NOT EXISTS agent_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                confidence REAL NOT NULL,
                requires_human_review INTEGER NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(event_id) REFERENCES events(event_id)
            );

            CREATE TABLE IF NOT EXISTS evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                claim TEXT NOT NULL,
                stance TEXT NOT NULL,
                reliability_score REAL NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(event_id) REFERENCES events(event_id)
            );

            CREATE TABLE IF NOT EXISTS workflow_results (
                event_id TEXT PRIMARY KEY,
                requires_human_review INTEGER NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(event_id) REFERENCES events(event_id)
            );
            """
        )
        self._connection.commit()

    def save_event(self, event: CandidateEvent) -> None:
        payload = asdict(event)
        self._connection.execute(
            """
            INSERT INTO events (
                event_id, title, status, severity, confidence, topic_label,
                payload_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(event_id) DO UPDATE SET
                title = excluded.title,
                status = excluded.status,
                severity = excluded.severity,
                confidence = excluded.confidence,
                topic_label = excluded.topic_label,
                payload_json = excluded.payload_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                event.event_id,
                event.title,
                event.status,
                event.severity,
                event.confidence,
                event.topic.label,
                _to_json(payload),
                event.created_at.isoformat(),
            ),
        )
        self._connection.commit()

    def save_report(self, event_id: str, report: Report) -> None:
        payload = asdict(report)
        self._connection.execute(
            """
            INSERT INTO reports (
                report_id, event_id, title, confidence, markdown, payload_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(report_id) DO UPDATE SET
                title = excluded.title,
                confidence = excluded.confidence,
                markdown = excluded.markdown,
                payload_json = excluded.payload_json
            """,
            (
                report.report_id,
                event_id,
                report.title,
                report.confidence,
                report.markdown,
                _to_json(payload),
                report.created_at.isoformat(),
            ),
        )
        self._connection.commit()

    def save_workflow_result(self, result: WorkflowResult) -> None:
        self.save_event(result.event)
        self.save_report(result.event.event_id, result.report)

        with self._connection:
            self._connection.execute(
                "DELETE FROM agent_decisions WHERE event_id = ?",
                (result.event.event_id,),
            )
            self._connection.execute(
                "DELETE FROM evidence WHERE event_id = ?",
                (result.event.event_id,),
            )

            for decision in result.decisions:
                self._connection.execute(
                    """
                    INSERT INTO agent_decisions (
                        event_id, agent_name, confidence, requires_human_review, payload_json
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        result.event.event_id,
                        decision.agent_name,
                        decision.confidence,
                        int(decision.requires_human_review),
                        _to_json(asdict(decision)),
                    ),
                )

            for item in result.evidence:
                self._connection.execute(
                    """
                    INSERT INTO evidence (
                        event_id, claim, stance, reliability_score, payload_json
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        result.event.event_id,
                        item.claim,
                        item.stance,
                        item.reliability_score,
                        _to_json(asdict(item)),
                    ),
                )

            self._connection.execute(
                """
                INSERT INTO workflow_results (
                    event_id, requires_human_review, payload_json
                )
                VALUES (?, ?, ?)
                ON CONFLICT(event_id) DO UPDATE SET
                    requires_human_review = excluded.requires_human_review,
                    payload_json = excluded.payload_json
                """,
                (
                    result.event.event_id,
                    int(result.requires_human_review),
                    _to_json(asdict(result)),
                ),
            )

    def list_events(self, limit: int = 50) -> list[dict]:
        rows = self._connection.execute(
            """
            SELECT event_id, title, status, severity, confidence, topic_label, created_at, updated_at
            FROM events
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_event(self, event_id: str) -> dict | None:
        row = self._connection.execute(
            "SELECT payload_json FROM events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        return _from_json(row["payload_json"]) if row else None

    def list_reports(self, limit: int = 50) -> list[dict]:
        rows = self._connection.execute(
            """
            SELECT report_id, event_id, title, confidence, created_at
            FROM reports
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_report(self, report_id: str) -> dict | None:
        row = self._connection.execute(
            "SELECT payload_json FROM reports WHERE report_id = ?",
            (report_id,),
        ).fetchone()
        return _from_json(row["payload_json"]) if row else None

    def list_agent_decisions(self, event_id: str) -> list[dict]:
        rows = self._connection.execute(
            """
            SELECT payload_json
            FROM agent_decisions
            WHERE event_id = ?
            ORDER BY id ASC
            """,
            (event_id,),
        ).fetchall()
        return [_from_json(row["payload_json"]) for row in rows]

    def list_evidence(self, event_id: str) -> list[dict]:
        rows = self._connection.execute(
            """
            SELECT payload_json
            FROM evidence
            WHERE event_id = ?
            ORDER BY id ASC
            """,
            (event_id,),
        ).fetchall()
        return [_from_json(row["payload_json"]) for row in rows]

    def close(self) -> None:
        self._connection.close()
