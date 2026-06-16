from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from .schemas import utc_now


class QuadroMemory:
    """SQLite-backed evidence memory for Quadro source packets."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.fts_enabled = False
        self._setup()

    def close(self) -> None:
        self.conn.close()

    def ingest_source_packet(
        self,
        path: Path,
        tags: list[str],
        source_url: str | None = None,
    ) -> str:
        body = path.read_text(encoding="utf-8")
        doc_id = _doc_id(path, body)
        title = _first_heading(body) or path.stem.replace("_", " ").title()
        now = utc_now()
        self.conn.execute(
            """
            insert or replace into documents
            (doc_id, title, source_path, source_url, tags_json, body, ingested_at)
            values (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id,
                title,
                str(path),
                source_url or "",
                json.dumps(tags, sort_keys=True),
                body,
                now,
            ),
        )
        if self.fts_enabled:
            self.conn.execute("delete from documents_fts where doc_id = ?", (doc_id,))
            self.conn.execute(
                """
                insert into documents_fts (doc_id, title, body, tags)
                values (?, ?, ?, ?)
                """,
                (doc_id, title, body, " ".join(tags)),
            )
        self.conn.commit()
        return doc_id

    def ingest_text_document(
        self,
        title: str,
        body: str,
        tags: list[str],
        source_label: str,
    ) -> str:
        clean_title = title.strip() or "Customer Source Document"
        clean_body = body.strip()
        doc_id = f"doc_{hashlib.sha256(f'{clean_title}\n{clean_body}'.encode('utf-8')).hexdigest()[:16]}"
        now = utc_now()
        self.conn.execute(
            """
            insert or replace into documents
            (doc_id, title, source_path, source_url, tags_json, body, ingested_at)
            values (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id,
                clean_title,
                source_label,
                "",
                json.dumps(tags, sort_keys=True),
                clean_body,
                now,
            ),
        )
        if self.fts_enabled:
            self.conn.execute("delete from documents_fts where doc_id = ?", (doc_id,))
            self.conn.execute(
                """
                insert into documents_fts (doc_id, title, body, tags)
                values (?, ?, ?, ?)
                """,
                (doc_id, clean_title, clean_body, " ".join(tags)),
            )
        self.conn.commit()
        return doc_id

    def search(
        self,
        query: str,
        limit: int = 5,
        required_tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        if self.fts_enabled:
            rows = self._search_fts(query, limit, required_tags=required_tags)
            if rows:
                return rows
        return self._search_like(query, limit, required_tags=required_tags)

    def record_checkpoint(self, lane: str, payload: dict[str, Any]) -> None:
        self.conn.execute(
            """
            insert into checkpoints (created_at, lane, payload_json)
            values (?, ?, ?)
            """,
            (utc_now(), lane, json.dumps(payload, sort_keys=True)),
        )
        self.conn.commit()

    def _setup(self) -> None:
        self.conn.execute(
            """
            create table if not exists documents (
                doc_id text primary key,
                title text not null,
                source_path text not null,
                source_url text,
                tags_json text not null,
                body text not null,
                ingested_at text not null
            )
            """
        )
        self.conn.execute(
            """
            create table if not exists checkpoints (
                checkpoint_id integer primary key autoincrement,
                created_at text not null,
                lane text not null,
                payload_json text not null
            )
            """
        )
        try:
            self.conn.execute(
                """
                create virtual table if not exists documents_fts
                using fts5(doc_id unindexed, title, body, tags)
                """
            )
            self.fts_enabled = True
        except sqlite3.OperationalError:
            self.fts_enabled = False
        self.conn.commit()

    def _search_fts(
        self,
        query: str,
        limit: int,
        required_tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        match_query = _fts_query(query)
        if not match_query:
            return []
        raw_limit = _raw_limit(limit, required_tags)
        try:
            rows = self.conn.execute(
                """
                select d.doc_id, d.title, d.source_path, d.source_url,
                       d.tags_json, d.body
                from documents_fts f
                join documents d on d.doc_id = f.doc_id
                where documents_fts match ?
                limit ?
                """,
                (match_query, raw_limit),
            ).fetchall()
        except sqlite3.OperationalError:
            return []
        return _pack_rows(rows, query, limit, required_tags)

    def _search_like(
        self,
        query: str,
        limit: int,
        required_tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        tokens = _tokens(query)
        if not tokens:
            return []
        clauses = " or ".join(["lower(body) like ?" for _ in tokens])
        values = [f"%{token.lower()}%" for token in tokens]
        raw_limit = _raw_limit(limit, required_tags)
        rows = self.conn.execute(
            f"""
            select doc_id, title, source_path, source_url, tags_json, body
            from documents
            where {clauses}
            limit ?
            """,
            (*values, raw_limit),
        ).fetchall()
        return _pack_rows(rows, query, limit, required_tags)


def _doc_id(path: Path, body: str) -> str:
    digest = hashlib.sha256(f"{path.resolve()}\n{body}".encode("utf-8")).hexdigest()
    return f"doc_{digest[:16]}"


def _first_heading(body: str) -> str | None:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def _tokens(query: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_]{3,}", query)


def _fts_query(query: str) -> str:
    return " OR ".join(_tokens(query))


def _pack_row(row: sqlite3.Row, query: str) -> dict[str, Any]:
    body = row["body"]
    return {
        "doc_id": row["doc_id"],
        "title": row["title"],
        "source": row["source_path"],
        "source_url": row["source_url"],
        "tags": json.loads(row["tags_json"]),
        "snippet": _snippet(body, query),
    }


def _pack_rows(
    rows: list[sqlite3.Row],
    query: str,
    limit: int,
    required_tags: list[str] | None,
) -> list[dict[str, Any]]:
    required = {tag for tag in (required_tags or []) if tag}
    packed: list[dict[str, Any]] = []
    for row in rows:
        item = _pack_row(row, query)
        if required and not required.intersection(item["tags"]):
            continue
        packed.append(item)
        if len(packed) >= limit:
            break
    return packed


def _raw_limit(limit: int, required_tags: list[str] | None) -> int:
    if not required_tags:
        return limit
    return max(limit * 8, limit + 12)


def _snippet(body: str, query: str, width: int = 280) -> str:
    lower = body.lower()
    positions = [lower.find(token.lower()) for token in _tokens(query)]
    positions = [position for position in positions if position >= 0]
    start = max(0, min(positions) - 80) if positions else 0
    snippet = body[start : start + width].replace("\n", " ").strip()
    return snippet
