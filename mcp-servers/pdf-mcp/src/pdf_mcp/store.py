"""Content-addressed snapshots and parse results in a new SQLite database."""

import hashlib
import json
import os
import sqlite3
import tempfile
import time
from contextlib import contextmanager
from importlib.metadata import version
from pathlib import Path

from .models import PdfError, checksum, digest

SCHEMA = "pdf-v2.1"


class Store:
    def __init__(self, root=None):
        self.root = (
            Path(root or os.getenv("PDF_MCP_CACHE_DIR", Path.home() / ".cache/pdf-mcp"))
            .expanduser()
            .resolve()
        )
        self.root.mkdir(parents=True, exist_ok=True)
        for name in ("sources-v2", "images-v2", "jobs-v2"):
            (self.root / name).mkdir(exist_ok=True)
        self.database = self.root / "documents-v2.sqlite3"
        self.signature = digest(
            {
                "schema": SCHEMA,
                "code": {
                    name: checksum(Path(__file__).with_name(name))
                    for name in ("structured.py", "native.py", "store.py")
                },
                "libraries": {
                    name: version(name) for name in ("pymupdf", "beautifulsoup4", "lxml")
                },
            }
        )
        with self.db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY, payload TEXT NOT NULL, accessed REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS parses(id TEXT PRIMARY KEY, document_id TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS images(path TEXT PRIMARY KEY, sha256 TEXT NOT NULL);
            """)

    @contextmanager
    def db(self):
        connection = sqlite3.connect(self.database, timeout=20)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @staticmethod
    def atomic_bytes(path, data):
        with tempfile.TemporaryDirectory(dir=path.parent) as temporary:
            staged = Path(temporary) / "content"
            staged.write_bytes(data)
            os.replace(staged, path)

    def save(self, data, payload):
        source_sha = hashlib.sha256(data).hexdigest()
        ident = digest(
            [
                source_sha,
                payload["format"],
                (
                    payload.get("origin", {}).get("final_url")
                    or payload.get("origin", {}).get("local_path")
                )
                if payload["format"] != "pdf"
                else None,
                self.signature,
            ]
        )
        target = self.root / "sources-v2" / (source_sha + "." + payload["format"])
        if not target.exists() or checksum(target) != source_sha:
            self.atomic_bytes(target, data)
        payload = {
            **payload,
            "document_id": ident,
            "sha256": source_sha,
            "path": str(target),
            "schema": SCHEMA,
            "parser_signature": self.signature,
        }
        with self.db() as db:
            db.execute(
                "INSERT INTO documents VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET accessed=excluded.accessed",
                (ident, json.dumps(payload), time.time()),
            )
        return payload

    def get(self, ident):
        with self.db() as db:
            row = db.execute("SELECT payload FROM documents WHERE id=?", (ident,)).fetchone()
            if row:
                db.execute("UPDATE documents SET accessed=? WHERE id=?", (time.time(), ident))
        if not row:
            raise PdfError("DOCUMENT_NOT_FOUND", "Open the document first")
        value = json.loads(row[0])
        path = Path(value["path"])
        if path.is_symlink() or not path.is_file() or checksum(path) != value["sha256"]:
            raise PdfError(
                "CACHE_CHANGED", "Source snapshot is missing or changed; reopen the source"
            )
        return value

    def save_parse(self, document_id, profile, payload):
        ident = digest([document_id, profile, payload])
        value = {**payload, "parse_id": ident, "document_id": document_id, "profile": profile}
        with self.db() as db:
            db.execute(
                "INSERT OR IGNORE INTO parses VALUES(?,?,?)",
                (ident, document_id, json.dumps(value)),
            )
        return value

    def get_parse(self, document_id, ident):
        with self.db() as db:
            row = db.execute(
                "SELECT payload FROM parses WHERE id=? AND document_id=?", (ident, document_id)
            ).fetchone()
        if not row:
            raise PdfError("PARSE_NOT_FOUND", "Parse result does not belong to this document")
        return json.loads(row[0])

    def find_parse(self, document_id, profile):
        with self.db() as db:
            rows = db.execute(
                "SELECT payload FROM parses WHERE document_id=?", (document_id,)
            ).fetchall()
        return next(
            (json.loads(row[0]) for row in rows if json.loads(row[0])["profile"] == profile), None
        )

    def save_image(self, path, data):
        self.atomic_bytes(path, data)
        with self.db() as db:
            db.execute("INSERT OR REPLACE INTO images VALUES(?,?)", (str(path), checksum(path)))

    def image_valid(self, path):
        if path.is_symlink() or not path.is_file():
            return False
        with self.db() as db:
            row = db.execute("SELECT sha256 FROM images WHERE path=?", (str(path),)).fetchone()
        return bool(row and checksum(path) == row[0])

    def stats(self):
        with self.db() as db:
            counts = {
                name: db.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                for name in ("documents", "parses")
            }
        return {
            **counts,
            "cache_dir": str(self.root),
            "database_bytes": self.database.stat().st_size,
        }

    def clear(self, expired_only=True, ttl_hours=24):
        cutoff = time.time() - ttl_hours * 3600
        with self.db() as db:
            rows = db.execute(
                "SELECT id,payload FROM documents WHERE accessed<?"
                if expired_only
                else "SELECT id,payload FROM documents",
                (cutoff,) if expired_only else (),
            ).fetchall()
            for ident, _ in rows:
                db.execute("DELETE FROM parses WHERE document_id=?", (ident,))
                db.execute("DELETE FROM documents WHERE id=?", (ident,))
            remaining = {
                json.loads(r[0])["path"]
                for r in db.execute("SELECT payload FROM documents").fetchall()
            }
        removed = 0
        for _, raw in rows:
            path = Path(json.loads(raw)["path"])
            if str(path) not in remaining and path.parent == self.root / "sources-v2":
                path.unlink(missing_ok=True)
            for image in (self.root / "images-v2").glob(json.loads(raw)["document_id"] + "-*"):
                image.unlink(missing_ok=True)
                with self.db() as db:
                    db.execute("DELETE FROM images WHERE path=?", (str(image),))
                removed += 1
        return {
            "cleared_documents": len(rows),
            "cleared_images": removed,
            "expired_only": expired_only,
        }
