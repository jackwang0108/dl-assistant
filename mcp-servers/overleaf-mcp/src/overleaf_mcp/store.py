"""Transactional local records; downloads never move the latest compile pointer."""

import json
import os
import sqlite3
import tempfile
import time
import uuid
from contextlib import contextmanager

from .models import OverleafError, checksum, contained, digest, identifier


class Store:
    def __init__(self, config):
        self.root = config.home / "v2" / digest(config.base_url)[:16]
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.database = self.root / "records.sqlite3"
        with self.db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS bindings(project TEXT PRIMARY KEY,payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS compiles(id TEXT PRIMARY KEY,project TEXT NOT NULL,created INTEGER NOT NULL,payload TEXT NOT NULL,pinned INTEGER NOT NULL DEFAULT 0);
                CREATE INDEX IF NOT EXISTS compiles_project ON compiles(project,created);
                CREATE TABLE IF NOT EXISTS active(project TEXT PRIMARY KEY,id TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS snapshots(id TEXT PRIMARY KEY,scope TEXT NOT NULL,payload TEXT NOT NULL);
            """)
        os.chmod(self.database, 0o600)

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.database, timeout=20)
        try:
            with db:
                yield db
        finally:
            db.close()

    def directory(self, project, compile_id, create=True):
        path = contained(self.root, "artifacts", identifier(project), identifier(compile_id))
        if create:
            path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def write(path, data):
        if path.is_symlink():
            raise OverleafError("UNSAFE_PATH", "Artifact is a symlink")
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temp = type(path)(stream.name)
            stream.write(data)
            os.chmod(temp, 0o600)
        os.replace(temp, path)

    def reserve(self, project, source, retry_unknown=False, timeout_seconds=180):
        identifier(project)
        ident = uuid.uuid4().hex
        created = time.time_ns()
        record = {
            "compile_id": ident,
            "project_id": project,
            "created_ns": created,
            "request_deadline_ns": created + int(timeout_seconds * 1_000_000_000),
            "state": "requested",
            "source": source,
            "outputs": {},
            "diagnostics": [],
            "classification": "unknown",
            "response": None,
        }
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            active = db.execute("SELECT id FROM active WHERE project=?", (project,)).fetchone()
            if active:
                previous = json.loads(
                    db.execute("SELECT payload FROM compiles WHERE id=?", (active[0],)).fetchone()[
                        0
                    ]
                )
                if not retry_unknown or previous["state"] != "outcome_unknown":
                    raise OverleafError(
                        "COMPILE_ALREADY_ACTIVE",
                        "Check the existing request before starting another compile",
                        compile_id=active[0],
                        state=previous["state"],
                    )
                record["explicit_retry_of_unknown"] = active[0]
            db.execute(
                "INSERT INTO compiles(id,project,created,payload) VALUES(?,?,?,?)",
                (ident, project, created, json.dumps(record)),
            )
            db.execute("INSERT OR REPLACE INTO active VALUES(?,?)", (project, ident))
        return record

    def save(self, record, release=False):
        with self.db() as db:
            db.execute(
                "UPDATE compiles SET payload=? WHERE id=? AND project=?",
                (json.dumps(record), record["compile_id"], record["project_id"]),
            )
            if release:
                db.execute(
                    "DELETE FROM active WHERE project=? AND id=?",
                    (record["project_id"], record["compile_id"]),
                )

    def get(self, project, compile_id=None):
        identifier(project)
        if compile_id:
            identifier(compile_id)
        with self.db() as db:
            row = (
                db.execute(
                    "SELECT payload,pinned FROM compiles WHERE project=? AND id=?",
                    (project, compile_id),
                ).fetchone()
                if compile_id
                else db.execute(
                    "SELECT payload,pinned FROM compiles WHERE project=? ORDER BY rowid DESC LIMIT 1",
                    (project,),
                ).fetchone()
            )
        if not row:
            raise OverleafError("COMPILE_NOT_FOUND", "No matching local compile record")
        return {**json.loads(row[0]), "pinned": bool(row[1])}

    def patch(self, project, ident, changes, release=False):
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT payload FROM compiles WHERE project=? AND id=?", (project, ident)
            ).fetchone()
            if not row:
                raise OverleafError("COMPILE_NOT_FOUND", "Compile does not exist")
            record = {**json.loads(row[0]), **changes}
            db.execute(
                "UPDATE compiles SET payload=? WHERE project=? AND id=?",
                (json.dumps(record), project, ident),
            )
            if release:
                db.execute("DELETE FROM active WHERE project=? AND id=?", (project, ident))
        return record

    def output(self, project, ident, name, item):
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT payload FROM compiles WHERE project=? AND id=?", (project, ident)
            ).fetchone()
            if not row:
                raise OverleafError("COMPILE_NOT_FOUND", "Compile does not exist")
            record = json.loads(row[0])
            record.setdefault("outputs", {})[name] = item
            db.execute(
                "UPDATE compiles SET payload=? WHERE project=? AND id=?",
                (json.dumps(record), project, ident),
            )
        return record

    def compiles(self, project):
        identifier(project)
        with self.db() as db:
            rows = db.execute(
                "SELECT payload,pinned FROM compiles WHERE project=? ORDER BY rowid DESC",
                (project,),
            ).fetchall()
        return [{**json.loads(r[0]), "pinned": bool(r[1])} for r in rows]

    def binding(self, project, value=None):
        identifier(project)
        with self.db() as db:
            if value is not None:
                db.execute(
                    "INSERT OR REPLACE INTO bindings VALUES(?,?)", (project, json.dumps(value))
                )
            row = db.execute("SELECT payload FROM bindings WHERE project=?", (project,)).fetchone()
        return json.loads(row[0]) if row else None

    def bindings(self):
        with self.db() as db:
            rows = db.execute("SELECT payload FROM bindings ORDER BY project").fetchall()
        return [json.loads(r[0]) for r in rows]

    def pin(self, project, compile_id, pinned=True):
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            if not db.execute(
                "SELECT 1 FROM compiles WHERE project=? AND id=?", (project, compile_id)
            ).fetchone():
                raise OverleafError("COMPILE_NOT_FOUND", "Compile does not exist")
            db.execute(
                "UPDATE compiles SET pinned=? WHERE project=? AND id=?",
                (int(pinned), project, compile_id),
            )
        return {"compile_id": compile_id, "pinned": pinned}

    def snapshot(self, scope, records):
        ident = uuid.uuid4().hex
        with self.db() as db:
            db.execute(
                "INSERT INTO snapshots VALUES(?,?,?)", (ident, digest(scope), json.dumps(records))
            )
        return ident

    def read_snapshot(self, ident, scope):
        identifier(ident)
        with self.db() as db:
            row = db.execute(
                "SELECT payload FROM snapshots WHERE id=? AND scope=?", (ident, digest(scope))
            ).fetchone()
        if not row:
            raise OverleafError("INVALID_CURSOR", "Snapshot does not match this request")
        return json.loads(row[0])

    def verify_output(self, record, name):
        item = record.get("outputs", {}).get(name)
        if not item:
            return None
        path = self.directory(record["project_id"], record["compile_id"], create=False) / name
        if path.is_symlink() or not path.is_file() or checksum(path) != item["sha256"]:
            return None
        return {**item, "path": str(path)}
