"""Versioned observations and immutable query snapshots. No title-based merging."""

import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .identity import canonical_ref, normalize_ref


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


class Store:
    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.db_path = self.directory / "records-v2.sqlite3"
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS observations (
                    id TEXT PRIMARY KEY, source TEXT NOT NULL, fetched_at TEXT NOT NULL,
                    record TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS aliases (
                    ref TEXT NOT NULL, observation_id TEXT NOT NULL,
                    PRIMARY KEY(ref, observation_id));
                CREATE TABLE IF NOT EXISTS snapshots (
                    id TEXT PRIMARY KEY, query_id TEXT NOT NULL, created_at TEXT NOT NULL,
                    spec_hash TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS snapshot_spec ON snapshots(spec_hash,created_at);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.db_path, timeout=20)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def save_record(self, record):
        record = dict(record)
        record["identifiers"] = sorted(set(normalize_ref(r) for r in record["identifiers"]))
        record["paper_ref"] = canonical_ref(record["identifiers"])
        record.setdefault("fetched_at", now())
        oid = digest(record)
        with self.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO observations VALUES(?,?,?,?)",
                (oid, record["source"], record["fetched_at"], json.dumps(record)),
            )
            db.executemany(
                "INSERT OR IGNORE INTO aliases VALUES(?,?)",
                [(r, oid) for r in record["identifiers"]],
            )
        return record

    def records(self, ref, version=None):
        # Follow explicit provider-supplied identifiers, not title similarity.
        refs, records = {normalize_ref(ref)}, {}
        while True:
            found = []
            with self.connect() as db:
                for value in refs:
                    found.extend(
                        db.execute(
                            """SELECT o.* FROM observations o JOIN aliases a
                        ON a.observation_id=o.id WHERE a.ref=?""",
                            (value,),
                        ).fetchall()
                    )
            before = len(refs)
            for row in found:
                r = json.loads(row["record"])
                records[row["id"]] = r
                refs.update(r["identifiers"])
            if len(refs) == before:
                break
        observations = records.values()
        if version is not None:
            exact_ref = normalize_ref(ref)
            observations = [
                r
                for r in observations
                if r.get("version") == version and exact_ref in r["identifiers"]
            ]
        return sorted(observations, key=lambda r: r["fetched_at"])

    def paper(self, ref, view="normalized", version=None):
        observations = self.records(ref, version)
        if not observations:
            return None
        refs = sorted({r for o in observations for r in o["identifiers"]})
        result = {"paper_ref": canonical_ref(refs), "identifiers": refs}
        if view == "sources":
            return {**result, "observations": observations}
        if view == "versions":
            return {
                **result,
                "versions": [
                    {
                        "source": o["source"],
                        "version": o.get("version"),
                        "dates": o.get("dates", {}),
                        "identifiers": o["identifiers"],
                        "fetched_at": o["fetched_at"],
                    }
                    for o in observations
                ],
                "limitations": [
                    "Only versions actually observed are listed; shared identifiers are "
                    "provider assertions, not proof of identical text."
                ],
            }
        # Choose whole field observations; never union/deduplicate author names.
        latest = {}
        for o in observations:
            latest[o["source"]] = o
        provenance, conflicts = {}, {}
        for key in (
            "title",
            "authors",
            "year",
            "abstract",
            "snippet",
            "venues",
            "dates",
            "publication_types",
            "categories",
            "language",
            "open_access",
            "version",
        ):
            values = [
                (o["fetched_at"], o["source"], o[key])
                for o in latest.values()
                if o.get(key) is not None and o.get(key) != []
            ]
            if not values:
                result[key] = None
                continue
            _, source, value = max(values, key=lambda v: (v[0], v[1]))
            result[key] = value
            provenance[key] = {"source": source, "fetched_at": latest[source]["fetched_at"]}
            if len({json.dumps(v[2], sort_keys=True) for v in values}) > 1:
                conflicts[key] = [{"source": s, "value": v} for _, s, v in values]
        result["citation_counts"] = [
            {"source": o["source"], "value": o["citation_count"], "fetched_at": o["fetched_at"]}
            for o in latest.values()
            if o.get("citation_count") is not None
        ]
        result["assets"] = [a for o in latest.values() for a in o.get("assets", [])]
        result["field_provenance"] = provenance
        result["conflicts"] = conflicts
        result["fetched_at"] = max(o["fetched_at"] for o in observations)
        return result

    def snapshot(self, payload, query_id=None):
        result = {
            **payload,
            "query_id": query_id or uuid.uuid4().hex,
            "snapshot_id": uuid.uuid4().hex,
            "created_at": now(),
        }
        with self.connect() as db:
            db.execute(
                "INSERT INTO snapshots VALUES(?,?,?,?,?)",
                (
                    result["snapshot_id"],
                    result["query_id"],
                    result["created_at"],
                    digest(result["spec"]),
                    json.dumps(result),
                ),
            )
        return result

    def get_snapshot(self, snapshot_or_query, *, exact=False):
        with self.connect() as db:
            if exact:
                row = db.execute(
                    "SELECT payload FROM snapshots WHERE id=?", (snapshot_or_query,)
                ).fetchone()
            else:
                row = db.execute(
                    "SELECT payload FROM snapshots WHERE id=? OR query_id=? "
                    "ORDER BY created_at DESC, rowid DESC LIMIT 1",
                    (snapshot_or_query, snapshot_or_query),
                ).fetchone()
        if not row:
            raise ValueError("Unknown query/snapshot; query IDs are local to this cache")
        return json.loads(row["payload"])

    def cached_snapshot(self, spec, max_age_seconds=86400):
        with self.connect() as db:
            row = db.execute(
                "SELECT payload FROM snapshots WHERE spec_hash=? "
                "ORDER BY created_at DESC, rowid DESC LIMIT 1",
                (digest(spec),),
            ).fetchone()
        if row:
            obj = json.loads(row["payload"])
            age = (
                datetime.now(timezone.utc) - datetime.fromisoformat(obj["created_at"])
            ).total_seconds()
            if max_age_seconds is None or age < max_age_seconds:
                return obj
        return None
